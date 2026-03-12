/**
 * W-FERR-001 — Probe Seals
 * ========================
 * Monitora integridade das operações de seal.
 * Detecta documentos selados localmente que não chegaram ao Ledger.
 *
 * Níveis de Autonomia:
 * - Level 2: Registar falhas no Ledger (Cura com Registo)
 * - Level 3: Alertar Human Dragon para seals críticos falhados
 *
 * Retorna: { orphans, ledgerCount, localCount, syncRate, issues[] }
 */

const TIMEOUT_MS = 5000;

// Detect environment
const isLocal = typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

/**
 * Get local receipts from wallet (localStorage)
 */
function getLocalReceipts() {
  if (typeof window === 'undefined' || typeof localStorage === 'undefined') {
    return [];
  }

  try {
    const walletStr = localStorage.getItem('windi_wallet');
    if (!walletStr) return [];

    const wallet = JSON.parse(walletStr);
    return wallet.receipts || [];
  } catch (e) {
    console.warn('[Ferreiro/Seals] Error reading local receipts:', e);
    return [];
  }
}

/**
 * Check if a receipt exists in the Ledger
 */
async function checkLedgerReceipt(receiptId) {
  const url = isLocal
    ? `http://127.0.0.1:8101/api/receipts/${receiptId}`
    : `/api/ledger/api/receipts/${receiptId}`;

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);

    const response = await fetch(url, {
      method: 'GET',
      signal: controller.signal
    });

    clearTimeout(timeout);

    if (!response.ok) {
      return { exists: false, error: `HTTP ${response.status}` };
    }

    const data = await response.json();
    return {
      exists: data.ok === true,
      receipt: data.receipt || null
    };

  } catch (error) {
    return {
      exists: false,
      error: error.name === 'AbortError' ? 'Timeout' : error.message
    };
  }
}

/**
 * Get recent Ledger receipts count
 */
async function getLedgerStats() {
  const url = isLocal
    ? 'http://127.0.0.1:8101/health'
    : '/api/ledger/health';

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);

    const response = await fetch(url, {
      method: 'GET',
      signal: controller.signal
    });

    clearTimeout(timeout);

    if (!response.ok) {
      return { ok: false, error: `HTTP ${response.status}` };
    }

    const data = await response.json();
    return {
      ok: true,
      totalReceipts: data.receipts || 0,
      status: data.status
    };

  } catch (error) {
    return {
      ok: false,
      error: error.name === 'AbortError' ? 'Timeout' : error.message
    };
  }
}

/**
 * Probe all seals - detect orphans
 */
async function probeSeals() {
  const issues = [];
  const start = Date.now();

  // 1. Get local receipts
  const localReceipts = getLocalReceipts();
  const localCount = localReceipts.length;

  // 2. Get Ledger stats
  const ledgerStats = await getLedgerStats();

  if (!ledgerStats.ok) {
    issues.push({
      id: 'LEDGER_UNREACHABLE',
      severity: 'critical',
      level: 4, // Alert Human Dragon
      message: 'Forensic Ledger unreachable - cannot verify seals',
      detail: ledgerStats.error,
      action: 'CHECK_LEDGER_SERVICE'
    });

    return {
      type: 'seals',
      timestamp: new Date().toISOString(),
      localCount,
      ledgerReachable: false,
      orphans: [],
      issues,
      score: 0,
      latency: Date.now() - start
    };
  }

  // 3. Check each local receipt against Ledger
  const orphans = [];
  const vrReceipts = localReceipts.filter(r => r.id && r.id.startsWith('VR-'));

  // Only check VR-* receipts (locally generated)
  for (const receipt of vrReceipts.slice(0, 10)) { // Limit to 10 to avoid overload
    const check = await checkLedgerReceipt(receipt.id);

    if (!check.exists) {
      orphans.push({
        id: receipt.id,
        title: receipt.title || 'Unknown',
        timestamp: receipt.ts,
        error: check.error || 'Not found in Ledger'
      });
    }
  }

  // 4. Generate issues for orphans
  if (orphans.length > 0) {
    issues.push({
      id: 'ORPHAN_SEALS',
      severity: orphans.length > 3 ? 'warning' : 'info',
      level: 2, // Cura com Registo
      message: `${orphans.length} local seal(s) not found in Ledger`,
      detail: orphans.map(o => o.id).join(', '),
      orphanCount: orphans.length,
      action: 'RESYNC_SEALS'
    });
  }

  // 5. Calculate sync rate
  const checkedCount = vrReceipts.slice(0, 10).length;
  const syncedCount = checkedCount - orphans.length;
  const syncRate = checkedCount > 0 ? Math.round((syncedCount / checkedCount) * 100) : 100;

  // 6. Score calculation
  let score = 100;
  if (!ledgerStats.ok) score = 0;
  else if (orphans.length > 5) score = 50;
  else if (orphans.length > 0) score = 80;

  return {
    type: 'seals',
    timestamp: new Date().toISOString(),
    localCount,
    ledgerCount: ledgerStats.totalReceipts,
    ledgerReachable: true,
    checkedCount,
    orphans,
    orphanCount: orphans.length,
    syncRate,
    issues,
    score,
    latency: Date.now() - start
  };
}

/**
 * Attempt to re-sync an orphan seal to the Ledger
 * Level 2 Autonomy: AI acts + Ledger seal
 */
async function healOrphanSeal(receiptId) {
  // Get local receipt data
  const localReceipts = getLocalReceipts();
  const receipt = localReceipts.find(r => r.id === receiptId);

  if (!receipt) {
    return {
      success: false,
      error: 'Receipt not found in local storage'
    };
  }

  // Try to register in Ledger via anchor endpoint
  const url = isLocal
    ? 'http://127.0.0.1:8108/api/anchor/anchor'
    : '/api/anchor/anchor';

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        receipt_id: receipt.id,
        combined_hash: receipt.ch || receipt.bh || 'unknown',
        doc_type: receipt.type || 'doc',
        entry_data: {
          title: receipt.title || 'Recovered Document',
          actor: 'ferreiro-heal',
          wallet: receipt.wallet_id
        }
      })
    });

    const data = await response.json();

    if (response.ok && data.ok) {
      return {
        success: true,
        receiptId: receipt.id,
        message: 'Seal recovered and registered in Ledger',
        ledgerResponse: data
      };
    } else {
      return {
        success: false,
        error: data.error || 'Unknown error',
        details: data
      };
    }

  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Heal all orphan seals (Level 2 autonomy)
 */
async function healAllOrphans() {
  const probe = await probeSeals();
  const results = [];

  for (const orphan of probe.orphans) {
    const result = await healOrphanSeal(orphan.id);
    results.push({
      id: orphan.id,
      ...result
    });

    // Small delay to avoid overwhelming the server
    await new Promise(r => setTimeout(r, 200));
  }

  const healed = results.filter(r => r.success).length;
  const failed = results.filter(r => !r.success).length;

  return {
    type: 'seal_heal',
    timestamp: new Date().toISOString(),
    total: probe.orphans.length,
    healed,
    failed,
    results,
    message: `Healed ${healed}/${probe.orphans.length} orphan seals`
  };
}

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { probeSeals, healOrphanSeal, healAllOrphans, getLocalReceipts };
}

if (typeof window !== 'undefined') {
  window.FerreiroProbSeals = { probeSeals, healOrphanSeal, healAllOrphans, getLocalReceipts };
}
