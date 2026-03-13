/**
 * W-SAFETY-FLASH-ALERT — Canvas Gen 7
 * WINDI Publishing House · Kempten, Bavaria · 2026-03-13
 *
 * Flash Alert Stack: SafetyInterrogator + LedgerVerifier + FlashAlertSheet
 *
 * Philosophy: OFFLINE FIRST → SYNC WHEN POSSIBLE → NEVER BLOCK WITHOUT PROOF
 *
 * The .jmpg Gen 7 carries a safety_level in APP1 segment representing
 * the forensic safety state of a document in real-time.
 *
 * Example: Tourist opens .jmpg of mountain trail. National Park closed
 * the trail 2h ago due to avalanche risk. Flash Alert intercepts with
 * institutional authority — even without network.
 *
 * This component is the Sister Witness in action: transforms passive
 * data into active sentinel.
 */

// ═══════════════════════════════════════════════════════════════════════════════
// MODULE 1 — SafetyInterrogator
// Extracts safety metadata from APP1 segment of .jmpg
// ═══════════════════════════════════════════════════════════════════════════════

class SafetyInterrogator {

  async interrogate(fileBlob) {
    try {
      const buffer = await fileBlob.arrayBuffer();
      const view = new DataView(buffer);

      // Verify JPEG magic bytes: FF D8
      if (view.getUint16(0) !== 0xFFD8) {
        return { error: 'NOT_JMPG', safety_level: 'unknown' };
      }

      // Walk JFIF segments looking for APP1 (FF E1)
      let offset = 2;
      while (offset < view.byteLength - 4) {
        const marker = view.getUint16(offset);

        // Check for valid marker
        if ((marker & 0xFF00) !== 0xFF00) break;

        // Start of Scan — end of metadata
        if (marker === 0xFFDA) break;

        const length = view.getUint16(offset + 2);

        if (marker === 0xFFE1) {
          // APP1 found — extract JSON string
          const segmentBytes = new Uint8Array(buffer, offset + 4, length - 2);
          const text = new TextDecoder('utf-8', { fatal: false }).decode(segmentBytes);

          // Look for WINDI_META block within APP1
          const windiStart = text.indexOf('WINDI_META:');
          if (windiStart !== -1) {
            const jsonStr = text.slice(windiStart + 11).split('\x00')[0];
            try {
              const meta = JSON.parse(jsonStr);
              return this._normalise(meta);
            } catch {
              return { error: 'PARSE_ERROR', safety_level: 'unknown' };
            }
          }

          // Alternative: look for WINDI_SAFETY block
          const safetyStart = text.indexOf('WINDI_SAFETY:');
          if (safetyStart !== -1) {
            const jsonStr = text.slice(safetyStart + 13).split('\x00')[0];
            try {
              const meta = JSON.parse(jsonStr);
              return this._normalise(meta);
            } catch {
              return { error: 'PARSE_ERROR', safety_level: 'unknown' };
            }
          }
        }

        // Advance to next segment
        offset += 2 + length;
      }

      // File without WINDI_META — not a .jmpg with safety
      return { error: 'NO_WINDI_META', safety_level: 'none' };

    } catch (err) {
      console.error('[SafetyInterrogator] Error:', err);
      return { error: 'READ_ERROR', safety_level: 'unknown' };
    }
  }

  _normalise(raw) {
    return {
      receipt_id:        raw.receipt_id        || raw.id || null,
      safety_level:      (raw.safety_level || raw.safetyLevel || 'green').toLowerCase(),
      valid_from:        raw.valid_from        || raw.validFrom || raw.created_at || null,
      issuing_authority: raw.issuing_authority || raw.issuingAuthority || raw.authority || 'Autoridade Desconhecida',
      subject:           raw.subject           || raw.title || 'Documento sem título',
      supersedes:        raw.supersedes        || null,
      governance_level:  raw.governance_level  || raw.governanceLevel || 'LOW'
    };
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// MODULE 2 — LedgerVerifier
// Verifies with Ledger when network available; uses cache when offline
// Strategy: OFFLINE FIRST
// ═══════════════════════════════════════════════════════════════════════════════

class LedgerVerifier {

  constructor() {
    this.CACHE_TTL_MS = 6 * 60 * 60 * 1000; // 6 hours
    this.LEDGER_BASE  = 'https://windi-domain.com/verify-public';
    this.TIMEOUT_MS   = 5000; // 5s timeout for weak signal
  }

  async verify(receipt_id) {
    if (!receipt_id) return { status: 'no_id', source: 'none' };

    // 1. Check local cache
    const cached = this._readCache(receipt_id);
    if (cached) return { ...cached, source: 'cache' };

    // 2. Try online (timeout 5s — tourist in mountain)
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), this.TIMEOUT_MS);

      const res = await fetch(`${this.LEDGER_BASE}/?id=${encodeURIComponent(receipt_id)}`, {
        signal: controller.signal,
        headers: { 'Accept': 'application/json' }
      });
      clearTimeout(timeout);

      if (!res.ok) return { status: 'ledger_error', source: 'online', code: res.status };

      const data = await res.json();
      const receipt = data.receipt || data;

      const result = {
        status:             'verified',
        online_safety_level: receipt.safety_level || receipt.safetyLevel || null,
        superseded_by:      receipt.superseded_by || receipt.supersededBy || null,
        closed_at:          receipt.closed_at     || receipt.closedAt || null,
        online_authority:   receipt.issuing_authority || receipt.authority || null,
        verified_at:        new Date().toISOString(),
        source:             'online'
      };

      this._writeCache(receipt_id, result);
      return result;

    } catch (err) {
      // No network or timeout
      return {
        status:  'offline',
        source:  'none',
        message: 'Sem ligação ao Ledger. A usar dados do ficheiro.'
      };
    }
  }

  _readCache(id) {
    try {
      const raw = localStorage.getItem(`windi_safety_cache_${id}`);
      if (!raw) return null;
      const entry = JSON.parse(raw);
      if (Date.now() - new Date(entry.verified_at).getTime() > this.CACHE_TTL_MS) {
        localStorage.removeItem(`windi_safety_cache_${id}`);
        return null;
      }
      return entry;
    } catch { return null; }
  }

  _writeCache(id, data) {
    try {
      localStorage.setItem(`windi_safety_cache_${id}`, JSON.stringify(data));
    } catch { /* storage full — ignore silently */ }
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// MODULE 3 — FlashAlertSheet (UI)
// G3 Bottom Sheet reacting to modules 1+2 results
// ═══════════════════════════════════════════════════════════════════════════════

class FlashAlertSheet {

  constructor(canvasContainer) {
    this.container = canvasContainer || document.body;
    this.sheet = null;
    this.propagateBtn = null;
    this._inject();
  }

  // Main entry point
  async evaluate(fileBlob) {
    const interrogator = new SafetyInterrogator();
    const verifier     = new LedgerVerifier();

    // Show "checking..." state
    this._showChecking();

    // Interrogate file
    const meta = await interrogator.interrogate(fileBlob);

    if (meta.error === 'NO_WINDI_META' || meta.error === 'NOT_JMPG') {
      this._dismiss();
      return { level: 'none', blocked: false }; // Normal file without safety — don't interfere
    }

    // Verify with Ledger (offline-first)
    const ledger = await verifier.verify(meta.receipt_id);

    // Determine final safety_level
    // Rule: Online Ledger prevails over embedded data if more restrictive
    const finalLevel = this._resolveLevel(meta, ledger);

    // Check freshness (> 30 days = yellow minimum)
    const freshnessAlert = this._checkFreshness(meta.valid_from);

    // Render alert
    this._render(finalLevel, meta, ledger, freshnessAlert);

    return { level: finalLevel, blocked: finalLevel === 'red', meta, ledger };
  }

  _resolveLevel(meta, ledger) {
    const levels = { 'green': 0, 'yellow': 1, 'red': 2, 'unknown': 1 };
    const embedded = meta.safety_level || 'green';
    const online   = ledger.online_safety_level || embedded;

    // Use the more restrictive of the two
    return levels[online] >= levels[embedded] ? online : embedded;
  }

  _checkFreshness(valid_from) {
    if (!valid_from) return false;
    const ageMs  = Date.now() - new Date(valid_from).getTime();
    const ageDays = ageMs / (1000 * 60 * 60 * 24);
    return ageDays > 30 ? Math.floor(ageDays) : false;
  }

  _inject() {
    // Sheet container (starts hidden)
    this.sheet = document.createElement('div');
    this.sheet.id = 'windi-flash-alert';
    this.sheet.innerHTML = this._template();
    this.sheet.style.cssText = `
      position: fixed;
      bottom: 0; left: 0; right: 0;
      z-index: 9999;
      transform: translateY(100%);
      transition: transform 0.35s cubic-bezier(0.32, 0.72, 0, 1);
      font-family: 'Bricolage Grotesque', 'Segoe UI', sans-serif;
    `;
    document.body.appendChild(this.sheet);
  }

  _template() {
    return `
      <style>
        #windi-flash-alert {
          --alert-green:   #2A7D4F;
          --alert-yellow:  #E6A817;
          --alert-red:     #D63B3B;
          --alert-unknown: #8B8B8B;
          --bg-klar:       #F5F0E0;
          --bg-noir:       #1A1A1A;
          --text-primary:  #1A1A1A;
          --mono:          'JetBrains Mono', monospace;
        }
        .wfa-sheet {
          background: var(--bg-klar);
          border-radius: 16px 16px 0 0;
          box-shadow: 0 -8px 40px rgba(0,0,0,0.18);
          padding: 0 0 env(safe-area-inset-bottom, 0);
          max-height: 80vh;
          overflow-y: auto;
        }
        .wfa-handle {
          width: 40px; height: 4px;
          background: rgba(0,0,0,0.15);
          border-radius: 2px;
          margin: 12px auto 0;
        }
        .wfa-header {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 16px 20px 12px;
          border-bottom: 1px solid rgba(0,0,0,0.08);
        }
        .wfa-icon {
          width: 40px; height: 40px;
          border-radius: 10px;
          display: flex; align-items: center; justify-content: center;
          font-size: 20px;
          flex-shrink: 0;
        }
        .wfa-title { font-size: 16px; font-weight: 700; line-height: 1.2; }
        .wfa-subtitle {
          font-size: 12px;
          font-family: var(--mono);
          opacity: 0.6;
          margin-top: 2px;
        }
        .wfa-body { padding: 16px 20px; }
        .wfa-message { font-size: 15px; line-height: 1.5; margin-bottom: 12px; }
        .wfa-meta {
          background: rgba(0,0,0,0.04);
          border-radius: 8px;
          padding: 10px 12px;
          font-family: var(--mono);
          font-size: 11px;
          line-height: 1.8;
          color: rgba(0,0,0,0.6);
          white-space: pre-line;
        }
        .wfa-actions {
          display: flex; gap: 10px;
          padding: 0 20px 20px;
        }
        .wfa-btn {
          flex: 1;
          min-height: 48px;  /* ≥44px touch target */
          border-radius: 12px;
          border: none;
          font-family: 'Bricolage Grotesque', sans-serif;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: opacity 0.15s, transform 0.1s;
          -webkit-tap-highlight-color: transparent;
        }
        .wfa-btn:active { transform: scale(0.97); }
        .wfa-btn-primary { color: white; }
        .wfa-btn-secondary {
          background: rgba(0,0,0,0.06);
          color: var(--text-primary);
        }
        .wfa-source-badge {
          display: inline-flex; align-items: center; gap: 4px;
          font-size: 10px; font-family: var(--mono);
          padding: 2px 8px; border-radius: 4px;
          background: rgba(0,0,0,0.06);
          margin-bottom: 8px;
        }
        .wfa-source-badge.online { background: rgba(42,125,79,0.12); color: var(--alert-green); }
        .wfa-source-badge.cache  { background: rgba(230,168,23,0.12); color: var(--alert-yellow); }
        .wfa-source-badge.offline{ background: rgba(0,0,0,0.08); color: #888; }

        /* CHECKING state */
        .wfa-checking {
          padding: 20px;
          display: flex; align-items: center; gap: 12px;
          font-size: 13px; color: rgba(0,0,0,0.5);
          font-family: var(--mono);
        }
        .wfa-spinner {
          width: 16px; height: 16px;
          border: 2px solid rgba(0,0,0,0.1);
          border-top-color: rgba(0,0,0,0.4);
          border-radius: 50%;
          animation: wfa-spin 0.8s linear infinite;
        }
        @keyframes wfa-spin { to { transform: rotate(360deg); } }

        /* NOIR mode */
        @media (prefers-color-scheme: dark) {
          #windi-flash-alert { --bg-klar: #1E1E1E; --text-primary: #F5F0E0; }
          .wfa-meta { background: rgba(255,255,255,0.06); color: rgba(255,255,255,0.5); }
          .wfa-btn-secondary { background: rgba(255,255,255,0.08); color: var(--text-primary); }
          .wfa-handle { background: rgba(255,255,255,0.2); }
          .wfa-checking { color: rgba(255,255,255,0.5); }
          .wfa-spinner { border-color: rgba(255,255,255,0.1); border-top-color: rgba(255,255,255,0.4); }
        }
      </style>
      <div class="wfa-sheet" id="wfa-inner">
        <div class="wfa-handle"></div>
        <div id="wfa-content"><!-- filled dynamically --></div>
      </div>
    `;
  }

  _showChecking() {
    const content = document.getElementById('wfa-content');
    if (!content) return;
    content.innerHTML = `
      <div class="wfa-checking">
        <div class="wfa-spinner"></div>
        Verificando integridade do documento...
      </div>
    `;
    this._slideUp();
  }

  _render(level, meta, ledger, freshnessAlert) {
    if (level === 'green' && !freshnessAlert && ledger.source !== 'offline') {
      this._dismiss();
      return;
    }

    const configs = {
      red: {
        icon: '🚨',
        bg: '#D63B3B',
        title: 'Área Fechada — Risco Confirmado',
        message: `Esta trilha foi <strong>fechada oficialmente</strong> por
                  <em>${meta.issuing_authority}</em>
                  ${ledger.closed_at ? ` há ${this._timeAgo(ledger.closed_at)}` : ''}.
                  O acesso está bloqueado por razões de segurança.`
      },
      yellow: {
        icon: '⚠️',
        bg: '#E6A817',
        title: freshnessAlert ? `Informação com ${freshnessAlert} dias` : 'Verificação Recomendada',
        message: freshnessAlert
          ? `Os dados desta trilha têm <strong>${freshnessAlert} dias</strong>.
             Verifique o estado actual antes de prosseguir.`
          : `O estado desta trilha requer verificação.
             Confirme com a autoridade emissora antes de avançar.`
      },
      unknown: {
        icon: '❓',
        bg: '#8B8B8B',
        title: 'Metadados Não Verificáveis',
        message: 'Não foi possível verificar o estado de segurança deste documento. Proceda com cautela.'
      }
    };

    const cfg = configs[level] || configs.unknown;
    const sourceBadge = this._sourceBadge(ledger.source);

    const content = document.getElementById('wfa-content');
    content.innerHTML = `
      <div class="wfa-header">
        <div class="wfa-icon" style="background:${cfg.bg}20; color:${cfg.bg}">
          ${cfg.icon}
        </div>
        <div>
          <div class="wfa-title" style="color:${cfg.bg}">${cfg.title}</div>
          <div class="wfa-subtitle">${meta.receipt_id || 'ID não disponível'}</div>
        </div>
      </div>
      <div class="wfa-body">
        ${sourceBadge}
        <div class="wfa-message">${cfg.message}</div>
        <div class="wfa-meta">Autoridade: ${meta.issuing_authority}${meta.valid_from ? `\nVálido desde: ${new Date(meta.valid_from).toLocaleDateString('pt-PT')}` : ''}${ledger.closed_at ? `\nFechado em: ${new Date(ledger.closed_at).toLocaleString('pt-PT')}` : ''}${ledger.source === 'none' ? '\n⚡ Dado local — sem verificação online' : ''}</div>
      </div>
      <div class="wfa-actions">
        <button class="wfa-btn wfa-btn-primary"
                style="background:${cfg.bg}"
                onclick="window.open('https://windi-domain.com/verify-public/?id=${encodeURIComponent(meta.receipt_id || '')}', '_blank')">
          Ver no Ledger
        </button>
        ${level !== 'red' ? `
          <button class="wfa-btn wfa-btn-secondary"
                  onclick="document.getElementById('windi-flash-alert')._dismiss?.()">
            Continuar mesmo assim
          </button>
        ` : ''}
      </div>
    `;

    // Block propagation button if RED
    if (level === 'red') {
      this._blockPropagation(cfg.bg);
    }

    this._slideUp();

    // Expose dismiss method on element for inline button
    document.getElementById('windi-flash-alert')._dismiss = () => this._dismiss();
  }

  _sourceBadge(source) {
    const labels = {
      online:  ['🟢', 'Verificado online',  'online'],
      cache:   ['🟡', 'Cache local (< 6h)', 'cache'],
      none:    ['⚡', 'Offline — dado local', 'offline'],
      default: ['⚡', 'Offline — dado local', 'offline']
    };
    const [icon, label, cls] = labels[source] || labels.default;
    return `<span class="wfa-source-badge ${cls}">${icon} ${label}</span>`;
  }

  _blockPropagation(color) {
    // Find the "Propagate" button by data-attribute or common patterns
    const propBtn = document.querySelector('[data-action="propagate"]')
                 || document.querySelector('[data-action="seal"]')
                 || document.querySelector('[data-action="export"]');
    if (!propBtn) return;

    this.propagateBtn = {
      element:          propBtn,
      originalBg:       propBtn.style.background,
      originalTitle:    propBtn.title,
      originalDisabled: propBtn.disabled,
      originalOpacity:  propBtn.style.opacity,
      originalCursor:   propBtn.style.cursor
    };

    propBtn.disabled = true;
    propBtn.style.opacity = '0.4';
    propBtn.style.cursor  = 'not-allowed';
    propBtn.title = '⚠️ Propagação bloqueada — documento com safety_level: red';

    // Visual badge over button
    const badge = document.createElement('span');
    badge.id = 'windi-propagate-blocked';
    badge.style.cssText = `
      position: absolute;
      top: -6px; right: -6px;
      background: ${color};
      color: white;
      font-size: 10px;
      font-weight: 700;
      padding: 2px 5px;
      border-radius: 4px;
      pointer-events: none;
      font-family: 'JetBrains Mono', monospace;
      z-index: 10;
    `;
    badge.textContent = 'BLOQ.';

    if (getComputedStyle(propBtn).position === 'static') {
      propBtn.style.position = 'relative';
    }
    propBtn.appendChild(badge);
  }

  _unblockPropagation() {
    if (!this.propagateBtn) return;
    const { element, originalBg, originalTitle, originalDisabled, originalOpacity, originalCursor } = this.propagateBtn;
    element.disabled        = originalDisabled;
    element.style.opacity   = originalOpacity || '';
    element.style.cursor    = originalCursor || '';
    element.title           = originalTitle || '';
    element.style.background = originalBg || '';
    document.getElementById('windi-propagate-blocked')?.remove();
    this.propagateBtn = null;
  }

  _slideUp() {
    this.sheet.style.transform = 'translateY(0)';
  }

  _dismiss() {
    this.sheet.style.transform = 'translateY(100%)';
    this._unblockPropagation();
  }

  _timeAgo(isoString) {
    const ms    = Date.now() - new Date(isoString).getTime();
    const mins  = Math.floor(ms / 60000);
    const hours = Math.floor(mins / 60);
    const days  = Math.floor(hours / 24);
    if (days > 0)  return `${days} dia${days > 1 ? 's' : ''}`;
    if (hours > 0) return `${hours} hora${hours > 1 ? 's' : ''}`;
    return `${mins} minuto${mins > 1 ? 's' : ''}`;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// MODULE 4 — Global Integration
// Auto-hook into WINDI Canvas events
// ═══════════════════════════════════════════════════════════════════════════════

(function() {
  'use strict';

  // Initialize FlashAlertSheet when DOM ready
  let flashAlert = null;

  const init = () => {
    const container = document.getElementById('canvas-container') || document.body;
    flashAlert = new FlashAlertSheet(container);

    // Expose globally for manual use
    window.WindiFlashAlert = flashAlert;
    window.SafetyInterrogator = SafetyInterrogator;
    window.LedgerVerifier = LedgerVerifier;

    console.log('[WindiFlashAlert] Safety Flash Alert v1.0.0 initialized');

    // Hook into WINDI EventBus if available
    if (window.WINDI?.EventBus) {
      // Listen for document load events
      window.WINDI.EventBus.on('windi:document:loaded', async (e) => {
        if (e.file && e.file instanceof Blob) {
          await flashAlert.evaluate(e.file);
        }
      });

      // Listen for file drops
      window.WINDI.EventBus.on('windi:file:dropped', async (e) => {
        if (e.file && e.file.name?.endsWith('.jmpg')) {
          await flashAlert.evaluate(e.file);
        }
      });
    }

    // Hook into native file inputs with .jmpg files
    document.addEventListener('change', async (e) => {
      if (e.target.type === 'file' && e.target.files?.[0]) {
        const file = e.target.files[0];
        if (file.name?.toLowerCase().endsWith('.jmpg') ||
            file.type === 'application/vnd.windi.jmpg') {
          await flashAlert.evaluate(file);
        }
      }
    }, true);
  };

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
