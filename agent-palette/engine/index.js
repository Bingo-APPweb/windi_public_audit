/**
 * WINDI DragonEngine v2.0 — Main Entry Point
 * ==========================================
 *
 * Unified engine for document intelligence across mobile and desktop.
 *
 * Architecture:
 *   Layer 1: SessionCore (dragon_session.js) — History with `content:` field
 *   Layer 2: DragonCore (dragon_engine_core.js) — LLM call with valid_history
 *   Layer 3: DocManifests (manifests/*.json) — 14 document type definitions
 *   Layer 4: AgentBridge (agent_bridge.js) — Relative URLs for mobile+desktop
 *
 * KEY FIXES:
 *   - `text:` → `content:` for Claude API compatibility
 *   - `127.0.0.1` hardcoded → relative URLs via AgentBridge
 *   - sessionStorage without guard → length check in SessionCore
 *   - valid_history properly injected in DragonCore
 *
 * Three Dragons Protocol: AI processes. Human decides. WINDI guarantees.
 * (c) 2026 WINDI Publishing House — Kempten, Bavaria
 */

const ENGINE_VERSION = '2.0.0';
const ENGINE_NAME = 'DragonEngine';

// Lazy-load components to support both browser and Node.js
let _sessionModule = null;
let _coreModule = null;
let _bridgeModule = null;
let _manifestModule = null;

/**
 * Initialize DragonEngine
 * @param {Object} options - Configuration options
 * @returns {Object} Engine instance with all components
 */
async function initDragonEngine(options = {}) {
  const {
    sessionId = null,
    manifestBasePath = '/engine/manifests',
    autoLoadManifests = true
  } = options;

  // Initialize session
  const session = typeof getSession !== 'undefined'
    ? getSession(sessionId)
    : null;

  // Initialize bridge
  const bridge = typeof getBridge !== 'undefined'
    ? getBridge()
    : null;

  // Initialize core with session and bridge
  const core = typeof createDragonCore !== 'undefined'
    ? createDragonCore({ session })
    : null;

  // Initialize manifest registry
  const manifests = typeof getManifestRegistry !== 'undefined'
    ? getManifestRegistry()
    : null;

  // Load manifests if requested
  if (autoLoadManifests && manifests && !manifests.loaded) {
    await manifests.load(manifestBasePath);
  }

  return {
    version: ENGINE_VERSION,
    name: ENGINE_NAME,
    session,
    core,
    bridge,
    manifests,

    // Convenience methods
    chat: async (message, opts) => core?.chat(message, opts),
    getUrl: (service, path) => bridge?.getUrl(service, path),
    getDocType: (id) => manifests?.get(id),
    setDocType: (type) => session?.setDocType(type),
    setLang: (lang) => session?.setLang(lang),
    clearSession: () => session?.clear(),

    // Health check
    checkHealth: async () => {
      if (!bridge) return { healthy: false, error: 'Bridge not initialized' };
      return bridge.checkHealth('dragon');
    },

    // Debug info
    getDebugInfo: () => ({
      version: ENGINE_VERSION,
      session: session?.getSummary(),
      bridge: bridge?.getEnvironmentInfo(),
      manifests: manifests?.getSummary()
    })
  };
}

/**
 * Quick initialization for common use cases
 */
function quickInit(options = {}) {
  // Get existing instances
  const session = typeof getSession !== 'undefined' ? getSession() : null;
  const bridge = typeof getBridge !== 'undefined' ? getBridge() : null;
  const core = typeof createDragonCore !== 'undefined' ? createDragonCore({ session }) : null;

  return {
    session,
    bridge,
    core,
    chat: (msg, opts) => core?.chat(msg, opts),
    getUrl: (svc, path) => bridge?.getUrl(svc, path)
  };
}

/**
 * Migrate old history format to new format
 * Converts `text:` to `content:` and `human/bot` to `user/assistant`
 */
function migrateHistory(oldHistory) {
  if (!Array.isArray(oldHistory)) return [];

  return oldHistory.map(msg => ({
    role: msg.role === 'human' ? 'user' : (msg.role === 'bot' ? 'assistant' : msg.role),
    content: msg.content || msg.text || '',
    timestamp: msg.timestamp || Date.now()
  }));
}

/**
 * Build API-compatible history from session
 */
function buildApiHistory(session, limit = 20) {
  if (!session) return [];

  return session.getValidHistory(limit);
}

// Export engine metadata
const DragonEngine = {
  version: ENGINE_VERSION,
  name: ENGINE_NAME,
  init: initDragonEngine,
  quickInit,
  migrateHistory,
  buildApiHistory
};

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = DragonEngine;
}

// Export for browser
if (typeof window !== 'undefined') {
  window.DragonEngine = DragonEngine;

  // Also expose init directly for convenience
  window.initDragonEngine = initDragonEngine;
  window.quickInitDragon = quickInit;

  // Auto-log availability
  console.log(`[DragonEngine] v${ENGINE_VERSION} loaded — "AI processes. Human decides. WINDI guarantees."`);
}
