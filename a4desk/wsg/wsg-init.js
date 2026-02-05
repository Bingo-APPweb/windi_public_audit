/**
 * WINDI Surface Guard (WSG) - Client Initializer
 * v0.1.1 - HARDENED
 * 
 * @version 0.1.1
 */

(function() {
  'use strict';

  const WSG_VERSION = '0.1.1';

  const WSG_CLIENT_CONFIG = {
    serviceWorkerPath: '/wsg/wsg-service-worker.js?v=0.1.1-' + Date.now(),
    domSentinelPath: '/wsg/wsg-dom-sentinel.js',
    scope: '/',
    debug: true,
    showBadge: true,
    onReady: null,
    onError: null,
    onViolation: null
  };

  // ═══════════════════════════════════════════════════════════════
  // SERVICE WORKER REGISTRATION
  // ═══════════════════════════════════════════════════════════════

  async function registerServiceWorker(config) {
    if (!('serviceWorker' in navigator)) {
      console.warn('[WSG] Service Workers not supported');
      return { success: false, reason: 'unsupported' };
    }

    try {
      const registration = await navigator.serviceWorker.register(
        config.serviceWorkerPath,
        { scope: config.scope }
      );

      if (config.debug) {
        console.log('[WSG] Service Worker registered:', registration.scope);
      }

      // Aguardar ativação
      const sw = registration.installing || registration.waiting || registration.active;
      if (sw && sw.state !== 'activated') {
        await new Promise(resolve => {
          sw.addEventListener('statechange', function handler() {
            if (sw.state === 'activated') {
              sw.removeEventListener('statechange', handler);
              resolve();
            }
          });
        });
      }

      // Aguardar controller
      if (!navigator.serviceWorker.controller) {
        await new Promise(resolve => {
          navigator.serviceWorker.addEventListener('controllerchange', resolve, { once: true });
        });
      }

      return { success: true, registration };
    } catch (error) {
      console.error('[WSG] Service Worker registration failed:', error);
      return { success: false, reason: error.message };
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // DOM SENTINEL LOADER
  // ═══════════════════════════════════════════════════════════════

  function loadDOMSentinel(config) {
    return new Promise((resolve, reject) => {
      if (window.WSGSentinel) {
        resolve(window.WSGSentinel);
        return;
      }

      const script = document.createElement('script');
      script.src = config.domSentinelPath;
      script.async = true;

      script.onload = () => {
        if (window.WSGSentinel) {
          if (config.debug) console.log('[WSG] DOM Sentinel loaded');
          resolve(window.WSGSentinel);
        } else {
          reject(new Error('WSGSentinel not found after load'));
        }
      };

      script.onerror = () => reject(new Error('Failed to load DOM Sentinel'));
      document.head.appendChild(script);
    });
  }

  // ═══════════════════════════════════════════════════════════════
  // SERVICE WORKER COMMUNICATION
  // ═══════════════════════════════════════════════════════════════

  function sendToServiceWorker(type, payload = {}) {
    return new Promise((resolve, reject) => {
      if (!navigator.serviceWorker.controller) {
        reject(new Error('No active Service Worker'));
        return;
      }

      const channel = new MessageChannel();
      channel.port1.onmessage = (event) => resolve(event.data);
      navigator.serviceWorker.controller.postMessage({ type, payload }, [channel.port2]);

      setTimeout(() => reject(new Error('Timeout')), 5000);
    });
  }

  // ═══════════════════════════════════════════════════════════════
  // STATUS BADGE
  // ═══════════════════════════════════════════════════════════════

  function createStatusBadge(status) {
    // Remover badge existente
    const existing = document.getElementById('wsg-status-badge');
    if (existing) existing.remove();

    const badge = document.createElement('div');
    badge.id = 'wsg-status-badge';
    
    const icon = status.active ? '🛡️' : '⚠️';
    const text = status.active ? 'WSG Active' : 'WSG Inactive';
    const bg = status.active ? 'rgba(34, 197, 94, 0.95)' : 'rgba(239, 68, 68, 0.95)';

    badge.innerHTML = `<span style="margin-right:6px">${icon}</span>${text}`;
    badge.style.cssText = `
      position: fixed;
      bottom: 12px;
      right: 12px;
      background: ${bg};
      color: white;
      padding: 8px 14px;
      border-radius: 24px;
      font-size: 13px;
      font-family: system-ui, -apple-system, sans-serif;
      font-weight: 500;
      z-index: 2147483646;
      display: flex;
      align-items: center;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(0,0,0,0.25);
      transition: transform 0.15s, box-shadow 0.15s;
    `;

    badge.addEventListener('mouseenter', () => {
      badge.style.transform = 'scale(1.03)';
      badge.style.boxShadow = '0 6px 16px rgba(0,0,0,0.3)';
    });

    badge.addEventListener('mouseleave', () => {
      badge.style.transform = 'scale(1)';
      badge.style.boxShadow = '0 4px 12px rgba(0,0,0,0.25)';
    });

    badge.addEventListener('click', async () => {
      const details = await getWSGStatus();
      const msg = [
        `WINDI Surface Guard v${WSG_VERSION}`,
        `────────────────────────`,
        `Service Worker: ${details.sw ? '✓ Active' : '✗ Inactive'}`,
        `  Build ID: ${details.swBuildId || 'N/A'}`,
        `  Domain: ${details.swDomain || 'N/A'}`,
        `DOM Sentinel: ${details.sentinel ? '✓ Active' : '✗ Inactive'}`,
        `  Mode: ${details.sentinelMode || 'N/A'}`,
        `Protected Elements: ${details.protectedCount || 0}`,
        `Verified Hashes: ${details.verifiedHashCount || 0}`,
        `Violations: ${details.violationCount || 0}`,
        `────────────────────────`,
        `Frontend Constitutional Security Layer`
      ].join('\n');
      
      alert(msg);
    });

    document.body.appendChild(badge);
    return badge;
  }

  // ═══════════════════════════════════════════════════════════════
  // PUBLIC API
  // ═══════════════════════════════════════════════════════════════

  async function getWSGStatus() {
    const status = {
      version: WSG_VERSION,
      sw: false,
      swVersion: null,
      swBuildId: null,
      swDomain: null,
      verifiedHashCount: 0,
      sentinel: false,
      sentinelMode: null,
      protectedCount: 0,
      violationCount: 0
    };

    // Service Worker status
    if (navigator.serviceWorker?.controller) {
      try {
        const swStatus = await sendToServiceWorker('WSG_GET_STATUS');
        status.sw = true;
        status.swVersion = swStatus.version;
        status.swBuildId = swStatus.manifestBuildId;
        status.swDomain = swStatus.currentDomain;
        status.verifiedHashCount = swStatus.verifiedHashCount;
      } catch (e) {
        // SW not responding
      }
    }

    // DOM Sentinel status
    if (window.WSGSentinel) {
      const sentinelStatus = window.WSGSentinel.getStatus();
      status.sentinel = sentinelStatus.initialized;
      status.sentinelMode = sentinelStatus.mode;
      status.protectedCount = sentinelStatus.protectedCount;
      status.violationCount += sentinelStatus.violationCount;
    }

    return status;
  }

  async function initWSG(userConfig = {}) {
    const config = { ...WSG_CLIENT_CONFIG, ...userConfig };

    console.log(`[WSG] 🛡️ Initializing WINDI Surface Guard v${WSG_VERSION} (HARDENED)`);

    const results = {
      serviceWorker: null,
      domSentinel: null,
      errors: []
    };

    // 1. Register Service Worker
    try {
      results.serviceWorker = await registerServiceWorker(config);
    } catch (error) {
      results.errors.push({ component: 'serviceWorker', error });
    }

    // 2. Load DOM Sentinel
    try {
      results.domSentinel = await loadDOMSentinel(config);
    } catch (error) {
      results.errors.push({ component: 'domSentinel', error });
    }

    // 3. Status badge
    const success = results.serviceWorker?.success && results.domSentinel;
    if (config.showBadge !== false) {
      createStatusBadge({ active: success });
    }

    // 4. Callbacks
    if (success && config.onReady) {
      config.onReady(results);
    } else if (!success && config.onError) {
      config.onError(results.errors);
    }

    // 5. Log
    if (config.debug) {
      console.log('[WSG] Initialization complete:', {
        serviceWorker: results.serviceWorker?.success ? 'OK' : 'FAILED',
        domSentinel: results.domSentinel ? 'OK' : 'FAILED',
        errors: results.errors.length
      });
    }

    return results;
  }

  // ═══════════════════════════════════════════════════════════════
  // EXPORT
  // ═══════════════════════════════════════════════════════════════

  window.WSG = {
    version: WSG_VERSION,
    init: initWSG,
    getStatus: getWSGStatus,
    sendMessage: sendToServiceWorker,
    config: WSG_CLIENT_CONFIG,
    
    protect(element, level = 'standard') {
      if (window.WSGSentinel) {
        window.WSGSentinel.protect(element, level);
      }
    },
    
    getViolations() {
      return window.WSGSentinel?.getViolations() || [];
    },
    
    scanOverlays() {
      if (window.WSGSentinel) {
        window.WSGSentinel.scanOverlays();
      }
    },
    
    reloadManifest() {
      return sendToServiceWorker('WSG_RELOAD_MANIFEST');
    }
  };

  // Auto-init
  if (document.currentScript?.dataset.autoInit !== undefined) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => initWSG());
    } else {
      initWSG();
    }
  }

})();
