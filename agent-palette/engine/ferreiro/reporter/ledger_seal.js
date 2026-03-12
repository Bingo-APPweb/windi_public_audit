/**
 * W-FERR-001 — Ledger Seal
 * ========================
 * Integração com Forensic Ledger para registar curas.
 */

(function() {
  'use strict';

  const LEDGER_ENDPOINT = '/api/ledger';

  /**
   * Create seal payload
   */
  function createSealPayload(healResult) {
    return {
      type: 'FERREIRO_HEAL',
      version: '1.0.0',
      timestamp: new Date().toISOString(),
      data: {
        errorId: healResult.errorId,
        service: healResult.service || null,
        action: healResult.action || 'heal',
        success: healResult.success,
        duration: healResult.duration,
        detail: healResult.detail,
        steps: healResult.steps || []
      },
      metadata: {
        agent: 'W-FERR-001',
        autonomous: true,
        level: healResult.level || 1
      }
    };
  }

  /**
   * Calculate hash for seal
   */
  async function calculateHash(payload) {
    const text = JSON.stringify(payload);
    const encoder = new TextEncoder();
    const data = encoder.encode(text);

    // Use SubtleCrypto if available
    if (window.crypto && window.crypto.subtle) {
      const hashBuffer = await window.crypto.subtle.digest('SHA-256', data);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }

    // Fallback: simple hash for demo
    let hash = 0;
    for (let i = 0; i < text.length; i++) {
      const char = text.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return 'fallback-' + Math.abs(hash).toString(16);
  }

  /**
   * Seal heal result to Forensic Ledger
   */
  async function seal(healResult) {
    console.log('[Ferreiro] Sealing to Ledger:', healResult.errorId);

    const payload = createSealPayload(healResult);
    const hash = await calculateHash(payload);

    const sealData = {
      ...payload,
      hash
    };

    try {
      // Get AgentBridge URL if available
      const url = window.AgentBridge
        ? window.AgentBridge.getUrl('ledger', '/seal')
        : LEDGER_ENDPOINT + '/seal';

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Ferreiro-Seal': 'true'
        },
        body: JSON.stringify(sealData)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const result = await response.json();

      return {
        success: true,
        sealId: result.sealId || result.id,
        hash,
        timestamp: payload.timestamp
      };

    } catch (error) {
      console.warn('[Ferreiro] Ledger seal failed:', error.message);

      // Store locally for later sync
      storeLocalSeal(sealData);

      return {
        success: false,
        error: error.message,
        storedLocally: true,
        hash
      };
    }
  }

  /**
   * Store seal locally when Ledger is unavailable
   */
  function storeLocalSeal(sealData) {
    try {
      const key = 'ferreiro_pending_seals';
      const existing = JSON.parse(localStorage.getItem(key) || '[]');
      existing.push(sealData);
      localStorage.setItem(key, JSON.stringify(existing.slice(-100))); // Keep last 100
      console.log('[Ferreiro] Seal stored locally for later sync');
    } catch (e) {
      console.error('[Ferreiro] Failed to store local seal:', e);
    }
  }

  /**
   * Sync pending local seals to Ledger
   */
  async function syncPendingSeals() {
    const key = 'ferreiro_pending_seals';
    const pending = JSON.parse(localStorage.getItem(key) || '[]');

    if (pending.length === 0) return { synced: 0 };

    console.log('[Ferreiro] Syncing', pending.length, 'pending seals...');

    const synced = [];
    const failed = [];

    for (const sealData of pending) {
      try {
        const url = window.AgentBridge
          ? window.AgentBridge.getUrl('ledger', '/seal')
          : LEDGER_ENDPOINT + '/seal';

        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Ferreiro-Seal': 'true',
            'X-Ferreiro-Retry': 'true'
          },
          body: JSON.stringify(sealData)
        });

        if (response.ok) {
          synced.push(sealData);
        } else {
          failed.push(sealData);
        }
      } catch (e) {
        failed.push(sealData);
      }
    }

    // Update local storage with failed ones
    localStorage.setItem(key, JSON.stringify(failed));

    console.log('[Ferreiro] Sync complete:', synced.length, 'synced,', failed.length, 'pending');

    return {
      synced: synced.length,
      pending: failed.length
    };
  }

  /**
   * Get pending seal count
   */
  function getPendingCount() {
    const key = 'ferreiro_pending_seals';
    const pending = JSON.parse(localStorage.getItem(key) || '[]');
    return pending.length;
  }

  // Export
  const FerreiroLedger = {
    seal,
    syncPendingSeals,
    getPendingCount,
    createSealPayload,
    calculateHash
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = FerreiroLedger;
  }

  if (typeof window !== 'undefined') {
    window.FerreiroLedger = FerreiroLedger;
  }

})();
