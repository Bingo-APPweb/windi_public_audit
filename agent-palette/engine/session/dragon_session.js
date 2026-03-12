/**
 * WINDI DragonEngine v2.0 — SessionCore
 * ======================================
 * Session management with proper message structure.
 *
 * KEY FIX: Uses `content:` instead of `text:` for Claude API compatibility.
 *
 * Three Dragons Protocol: AI processes. Human decides. WINDI guarantees.
 * (c) 2026 WINDI Publishing House — Kempten, Bavaria
 */

const STORAGE_KEY = 'windi_dragon_session_v2';
const MAX_HISTORY = 50;
const SESSION_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes

/**
 * Message structure compatible with Claude API
 * @typedef {Object} DragonMessage
 * @property {string} role - 'user' | 'assistant' | 'system'
 * @property {string} content - Message content (NOT 'text')
 * @property {number} timestamp - Unix timestamp
 * @property {string} [source] - 'local' | 'semantic' | 'institutional'
 * @property {string} [dragon] - 'guardian' | 'architect' | 'witness'
 */

class DragonSession {
  constructor(sessionId = null) {
    this.sessionId = sessionId || this._generateSessionId();
    this.history = [];
    this.metadata = {
      created: Date.now(),
      lastActivity: Date.now(),
      tier: 'personal',
      lang: 'de',
      docType: null,
      walletId: null
    };
    this._load();
  }

  /**
   * Generate unique session ID
   */
  _generateSessionId() {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substring(2, 8);
    return `ds_${timestamp}_${random}`;
  }

  /**
   * Load session from storage (with guard for empty/invalid data)
   */
  _load() {
    if (typeof sessionStorage === 'undefined') return;

    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (!raw || raw.length < 3) return; // Guard: empty or invalid

      const data = JSON.parse(raw);
      if (data.sessionId === this.sessionId && data.history) {
        // Validate and migrate old format (text → content)
        this.history = data.history.map(msg => this._normalizeMessage(msg));
        this.metadata = { ...this.metadata, ...data.metadata };
      }
    } catch (e) {
      console.warn('[DragonSession] Load failed:', e.message);
      this.history = [];
    }
  }

  /**
   * Normalize message to use `content:` instead of `text:`
   * KEY FIX for Claude API compatibility
   */
  _normalizeMessage(msg) {
    return {
      role: msg.role === 'human' ? 'user' : (msg.role === 'bot' ? 'assistant' : msg.role),
      content: msg.content || msg.text || '', // Migrate text → content
      timestamp: msg.timestamp || Date.now(),
      source: msg.source,
      dragon: msg.dragon
    };
  }

  /**
   * Save session to storage
   */
  _save() {
    if (typeof sessionStorage === 'undefined') return;

    try {
      const data = {
        sessionId: this.sessionId,
        history: this.history.slice(-MAX_HISTORY),
        metadata: this.metadata
      };
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } catch (e) {
      console.warn('[DragonSession] Save failed:', e.message);
    }
  }

  /**
   * Add user message to history
   */
  addUserMessage(content) {
    const msg = {
      role: 'user',
      content: content,
      timestamp: Date.now()
    };
    this.history.push(msg);
    this.metadata.lastActivity = Date.now();
    this._save();
    return msg;
  }

  /**
   * Add assistant (Dragon) message to history
   */
  addAssistantMessage(content, options = {}) {
    const msg = {
      role: 'assistant',
      content: content,
      timestamp: Date.now(),
      source: options.source || 'semantic',
      dragon: options.dragon || 'guardian'
    };
    this.history.push(msg);
    this.metadata.lastActivity = Date.now();
    this._save();
    return msg;
  }

  /**
   * Get valid history for API call
   * Returns messages in Claude API format
   */
  getValidHistory(limit = 20) {
    const recentHistory = this.history.slice(-limit);

    // Filter and format for Claude API
    return recentHistory
      .filter(msg => msg.role === 'user' || msg.role === 'assistant')
      .map(msg => ({
        role: msg.role,
        content: msg.content
      }));
  }

  /**
   * Get history for backend (with role mapping)
   * Backend expects: role='human' for user, role='assistant' for bot
   */
  getHistoryForBackend(limit = 20) {
    const recentHistory = this.history.slice(-limit);

    return recentHistory
      .filter(msg => msg.role === 'user' || msg.role === 'assistant')
      .map(msg => ({
        role: msg.role === 'user' ? 'human' : 'assistant',
        content: msg.content // KEY: Use content, not text
      }));
  }

  /**
   * Set document context
   */
  setDocType(docType) {
    this.metadata.docType = docType;
    this._save();
  }

  /**
   * Set wallet/user context
   */
  setWallet(walletId, tier = 'personal') {
    this.metadata.walletId = walletId;
    this.metadata.tier = tier;
    this._save();
  }

  /**
   * Set language
   */
  setLang(lang) {
    this.metadata.lang = lang;
    this._save();
  }

  /**
   * Check if session is stale
   */
  isStale() {
    return (Date.now() - this.metadata.lastActivity) > SESSION_TIMEOUT_MS;
  }

  /**
   * Clear session history
   */
  clear() {
    this.history = [];
    this.metadata.lastActivity = Date.now();
    this._save();
  }

  /**
   * Get session summary for debugging
   */
  getSummary() {
    return {
      sessionId: this.sessionId,
      messageCount: this.history.length,
      lastActivity: new Date(this.metadata.lastActivity).toISOString(),
      tier: this.metadata.tier,
      docType: this.metadata.docType,
      isStale: this.isStale()
    };
  }
}

// Singleton instance
let _sessionInstance = null;

/**
 * Get or create session instance
 */
function getSession(sessionId = null) {
  if (!_sessionInstance || (sessionId && _sessionInstance.sessionId !== sessionId)) {
    _sessionInstance = new DragonSession(sessionId);
  }
  return _sessionInstance;
}

/**
 * Reset session (for logout or clear)
 */
function resetSession() {
  _sessionInstance = null;
  if (typeof sessionStorage !== 'undefined') {
    sessionStorage.removeItem(STORAGE_KEY);
  }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { DragonSession, getSession, resetSession };
}

// Export for browser
if (typeof window !== 'undefined') {
  window.DragonSession = DragonSession;
  window.getSession = getSession;
  window.resetSession = resetSession;
}
