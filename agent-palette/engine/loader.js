/**
 * WINDI DragonEngine v2.0 — Loader Script
 * ========================================
 *
 * Include this script to load all DragonEngine components.
 *
 * Usage in HTML:
 *   <script src="/engine/loader.js"></script>
 *   <script>
 *     // Wait for engine to be ready
 *     document.addEventListener('DragonEngineReady', async () => {
 *       const engine = await initDragonEngine();
 *       const response = await engine.chat('Hello Dragon!');
 *       console.log(response);
 *     });
 *   </script>
 *
 * Three Dragons Protocol: AI processes. Human decides. WINDI guarantees.
 * (c) 2026 WINDI Publishing House — Kempten, Bavaria
 */

(function() {
  'use strict';

  const ENGINE_BASE = '/engine';
  const COMPONENTS = [
    { path: '/session/dragon_session.js', name: 'SessionCore' },
    { path: '/core/dragon_engine_core.js', name: 'DragonCore' },
    { path: '/bridge/agent_bridge.js', name: 'AgentBridge' },
    { path: '/manifests/index.js', name: 'ManifestRegistry' },
    { path: '/index.js', name: 'DragonEngine' }
  ];

  let loadedCount = 0;
  const totalComponents = COMPONENTS.length;

  function getBasePath() {
    // Try to detect base path from current script
    const scripts = document.getElementsByTagName('script');
    for (const script of scripts) {
      if (script.src && script.src.includes('loader.js')) {
        const url = new URL(script.src);
        return url.pathname.replace('/loader.js', '');
      }
    }
    return ENGINE_BASE;
  }

  function loadScript(src, name) {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = src;
      script.async = false; // Load in order

      script.onload = () => {
        loadedCount++;
        console.log(`[DragonEngine] ${name} loaded (${loadedCount}/${totalComponents})`);
        resolve();
      };

      script.onerror = () => {
        console.error(`[DragonEngine] Failed to load ${name} from ${src}`);
        reject(new Error(`Failed to load ${name}`));
      };

      document.head.appendChild(script);
    });
  }

  async function loadAllComponents() {
    const basePath = getBasePath();
    console.log(`[DragonEngine] Loading from ${basePath}...`);

    for (const component of COMPONENTS) {
      try {
        await loadScript(basePath + component.path, component.name);
      } catch (e) {
        console.error(`[DragonEngine] Load failed:`, e);
        // Continue loading other components
      }
    }

    // Dispatch ready event
    const event = new CustomEvent('DragonEngineReady', {
      detail: {
        version: window.DragonEngine?.version || '2.0.0',
        loaded: loadedCount,
        total: totalComponents
      }
    });
    document.dispatchEvent(event);

    console.log(`[DragonEngine] Ready! ${loadedCount}/${totalComponents} components loaded.`);
  }

  // Start loading when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadAllComponents);
  } else {
    loadAllComponents();
  }

})();
