/**
 * windi-tree.js — DECRETO-001 Living Tree Implementation
 * Canonical module for WINDI organ interconnection
 *
 * USAGE:
 *   <script src="/static/windi-tree.js"></script>
 *   <script>
 *     WindiTree.init();
 *     // Later: WindiTree.goToOrigin();
 *   </script>
 *
 * Liga IA+H · 12 Abril 2026
 */

const WindiTree = (function() {
  'use strict';

  // ═══════════════════════════════════════════════════════════════════
  // DECREE-001 — Organ Map
  // ═══════════════════════════════════════════════════════════════════

  const ORGANS = {
    '/enterprise/':    { name: 'W-Enterprise',    port: 8150, tier: 'organ',      icon: '⬡' },
    '/law/':           { name: 'WINDI-LAW',       port: 8122, tier: 'organ',      icon: '⚖' },
    '/travel/':        { name: 'WINDI Travel',    port: 8126, tier: 'organ',      icon: '🌍' },
    '/wallet/':        { name: 'WINDI Wallet',    port: 8099, tier: 'root',       icon: '🪪' },
    '/sec/dashboard/': { name: 'W-SEC-001',       port: 8144, tier: 'root',       icon: '🛡' },
    '/verify-public/': { name: 'Verify Public',   port: 8145, tier: 'leaf',       icon: '✓' },
    '/dev-api/':       { name: 'W-DEV-API',       port: 8200, tier: 'leaf',       icon: '⚡' },
    '/desktop/':       { name: 'GEN7 (LEGACY)',   port: 8119, tier: 'deprecated', icon: '⚠' },
  };

  const STORAGE_KEY = 'windi_origin';
  const DEFAULT_ORIGIN = '/enterprise/';

  // ═══════════════════════════════════════════════════════════════════
  // Article 2 — Origin Detection
  // ═══════════════════════════════════════════════════════════════════

  function detectOrigin() {
    // 1. URL param ?return=
    const params = new URLSearchParams(window.location.search);
    const returnParam = params.get('return');
    if (returnParam && returnParam.startsWith('/')) {
      // Validate it's a known organ
      if (isValidOrgan(returnParam)) {
        return returnParam;
      }
    }

    // 2. sessionStorage
    const stored = sessionStorage.getItem(STORAGE_KEY);
    if (stored && isValidOrgan(stored)) {
      return stored;
    }

    // 3. Referrer
    try {
      const ref = document.referrer;
      if (ref && ref.includes('windi-domain.com')) {
        const path = new URL(ref).pathname;
        for (const [route, info] of Object.entries(ORGANS)) {
          if (path.startsWith(route) && info.tier !== 'deprecated') {
            return route;
          }
        }
      }
    } catch (e) {
      // Ignore referrer parsing errors
    }

    // 4. Default — never deprecated organs
    return DEFAULT_ORIGIN;
  }

  function isValidOrgan(path) {
    for (const [route, info] of Object.entries(ORGANS)) {
      if (path.startsWith(route) && info.tier !== 'deprecated') {
        return true;
      }
    }
    return false;
  }

  function storeOrigin() {
    const origin = detectOrigin();
    sessionStorage.setItem(STORAGE_KEY, origin);
    console.log('[WindiTree] Origin stored:', origin);
    return origin;
  }

  function getOrigin() {
    return sessionStorage.getItem(STORAGE_KEY) || DEFAULT_ORIGIN;
  }

  function goToOrigin() {
    const origin = getOrigin();
    console.log('[WindiTree] Returning to origin:', origin);
    window.location.href = origin;
  }

  // ═══════════════════════════════════════════════════════════════════
  // Article 3 — Navigation Helpers
  // ═══════════════════════════════════════════════════════════════════

  function getCurrentOrgan() {
    const path = window.location.pathname;
    for (const [route, info] of Object.entries(ORGANS)) {
      if (path.startsWith(route)) {
        return { route, ...info };
      }
    }
    return null;
  }

  function getOtherOrgans() {
    const current = getCurrentOrgan();
    return Object.entries(ORGANS)
      .filter(([route, info]) => {
        return info.tier !== 'deprecated' && route !== current?.route;
      })
      .map(([route, info]) => ({ route, ...info }));
  }

  function buildReturnUrl(targetRoute) {
    const current = getCurrentOrgan();
    if (!current) return targetRoute;
    return `${targetRoute}?return=${encodeURIComponent(current.route)}`;
  }

  // ═══════════════════════════════════════════════════════════════════
  // Article 4 — DID Flow Helpers
  // ═══════════════════════════════════════════════════════════════════

  function getDID() {
    // Check multiple storage locations
    return sessionStorage.getItem('windi_did')
        || sessionStorage.getItem('windi_enterprise_did')
        || sessionStorage.getItem('windi_desktop_wallet')
        || localStorage.getItem('windi_did');
  }

  function setDID(did) {
    if (!did || !did.startsWith('did:windi:')) {
      console.warn('[WindiTree] Invalid DID format');
      return false;
    }
    sessionStorage.setItem('windi_did', did);
    console.log('[WindiTree] DID stored:', did.substring(0, 25) + '...');
    return true;
  }

  function clearDID() {
    sessionStorage.removeItem('windi_did');
    sessionStorage.removeItem('windi_enterprise_did');
    sessionStorage.removeItem('windi_desktop_wallet');
    console.log('[WindiTree] DID cleared');
  }

  // ═══════════════════════════════════════════════════════════════════
  // Initialization
  // ═══════════════════════════════════════════════════════════════════

  function init(options = {}) {
    // Store origin on page load
    const origin = storeOrigin();

    // Log tree status
    const current = getCurrentOrgan();
    console.log('[WindiTree] DECREE-001 Active');
    console.log('[WindiTree] Current organ:', current?.name || 'Unknown');
    console.log('[WindiTree] Origin:', origin);
    console.log('[WindiTree] DID:', getDID() ? 'Present' : 'None');

    // Dispatch event for other scripts
    window.dispatchEvent(new CustomEvent('windi-tree-ready', {
      detail: { origin, current, did: getDID() }
    }));

    return { origin, current };
  }

  // ═══════════════════════════════════════════════════════════════════
  // Public API
  // ═══════════════════════════════════════════════════════════════════

  return {
    // Constants
    ORGANS,
    VERSION: '1.0.0',
    DECREE: 'DECREE-001-LIVING-TREE',

    // Origin (Article 2)
    init,
    detectOrigin,
    storeOrigin,
    getOrigin,
    goToOrigin,

    // Navigation (Article 3)
    getCurrentOrgan,
    getOtherOrgans,
    buildReturnUrl,

    // DID Flow (Article 4)
    getDID,
    setDID,
    clearDID,
  };
})();

// Auto-init if not in module context
if (typeof module === 'undefined') {
  document.addEventListener('DOMContentLoaded', () => WindiTree.init());
}
