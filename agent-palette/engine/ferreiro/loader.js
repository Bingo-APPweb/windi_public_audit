/**
 * W-FERR-001 — Ferreiro Loader
 * ============================
 * Carrega todos os módulos do Ferreiro em ordem correcta.
 *
 * Uso: <script src="/engine/ferreiro/loader.js"></script>
 */

(function() {
  'use strict';

  const BASE_PATH = '/engine/ferreiro';

  const MODULES = [
    // Probes
    'probes/probe_services.js',
    'probes/probe_manifests.js',
    'probes/probe_code.js',
    'probes/probe_seals.js',

    // Healers
    'healers/heal_zombi.js',
    'healers/heal_alzheimer.js',
    'healers/heal_urls.js',
    'healers/heal_loop.js',
    'healers/heal_manifest.js',

    // Reporter
    'reporter/report.js',
    'reporter/ledger_seal.js',
    'reporter/dashboard.js',

    // Main orchestrator (must be last)
    'ferreiro.js'
  ];

  let loadedCount = 0;
  let failedCount = 0;

  /**
   * Load a single script
   */
  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = `${BASE_PATH}/${src}`;
      script.async = false; // Maintain order

      script.onload = () => {
        loadedCount++;
        console.log(`[Ferreiro] Loaded: ${src} (${loadedCount}/${MODULES.length})`);
        resolve();
      };

      script.onerror = () => {
        failedCount++;
        console.error(`[Ferreiro] Failed to load: ${src}`);
        reject(new Error(`Failed to load ${src}`));
      };

      document.head.appendChild(script);
    });
  }

  /**
   * Load all modules sequentially
   */
  async function loadAll() {
    console.log('[Ferreiro] Loading modules...');

    for (const module of MODULES) {
      try {
        await loadScript(module);
      } catch (error) {
        // Continue loading other modules
        console.warn(`[Ferreiro] Continuing despite error in ${module}`);
      }
    }

    console.log(`[Ferreiro] Load complete: ${loadedCount} loaded, ${failedCount} failed`);

    // Initialize if all critical modules loaded
    if (window.Ferreiro) {
      console.log('[Ferreiro] Initializing...');
      await window.Ferreiro.loadCatalogue();

      // Auto-show dashboard in development
      if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        if (window.FerreiroUI) {
          // Don't auto-show, just init
          console.log('[Ferreiro] Dashboard ready (click anvil to open)');
        }
      }
    }

    // Dispatch ready event
    window.dispatchEvent(new CustomEvent('ferreiro-ready', {
      detail: {
        loaded: loadedCount,
        failed: failedCount,
        version: window.Ferreiro?.VERSION || '0.0.0'
      }
    }));
  }

  // Auto-load on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadAll);
  } else {
    loadAll();
  }

})();
