/**
 * WINDI DragonEngine v2.0 — DragonCore
 * =====================================
 * LLM call wrapper with valid_history injection.
 *
 * KEY FEATURES:
 * - Relative URLs for mobile+desktop compatibility
 * - Proper message format (content: not text:)
 * - History injection for context continuity
 * - Three Dragons routing (Guardian/Architect/Witness)
 *
 * Three Dragons Protocol: AI processes. Human decides. WINDI guarantees.
 * (c) 2026 WINDI Publishing House — Kempten, Bavaria
 */

// Import session management
// In browser: window.getSession is available
// In Node: require('./session/dragon_session')

const DRAGON_TYPES = {
  guardian: {
    name: { de: 'Guardian', en: 'Guardian', pt: 'Guardião' },
    description: 'Protects and guides'
  },
  architect: {
    name: { de: 'Architekt', en: 'Architect', pt: 'Arquiteto' },
    description: 'Designs and structures'
  },
  witness: {
    name: { de: 'Zeuge', en: 'Witness', pt: 'Testemunha' },
    description: 'Observes and records'
  }
};

class DragonCore {
  constructor(options = {}) {
    this.session = options.session || (typeof getSession !== 'undefined' ? getSession() : null);
    this.baseUrl = this._resolveBaseUrl();
    this.defaultTimeout = options.timeout || 30000;
    this.retryCount = options.retryCount || 2;
    this.onStatusChange = options.onStatusChange || (() => {});
  }

  /**
   * Resolve base URL based on environment
   * KEY FIX: No more hardcoded localhost URLs
   */
  _resolveBaseUrl() {
    if (typeof window === 'undefined') {
      // Node.js / server-side
      return process.env.DRAGON_API_URL || 'http://localhost:8108';
    }

    const hostname = window.location.hostname;
    const protocol = window.location.protocol;

    // Local development
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return `${protocol}//localhost:8108`;
    }

    // Production: use relative URLs (nginx proxy handles routing)
    return `${protocol}//${hostname}`;
  }

  /**
   * Get API endpoint path
   * Uses relative paths for mobile compatibility
   */
  _getEndpoint(path) {
    const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';

    // Production: use proxy paths
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
      // Nginx proxies /app/api/dragon to Dragon server
      return `/app/api/dragon${path}`;
    }

    // Local: direct port access
    return `/api/dragon${path}`;
  }

  /**
   * Build full URL for API call
   */
  _buildUrl(path) {
    const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';

    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return `http://localhost:8108/api/dragon${path}`;
    }

    // Production: use current origin with proxy path
    const origin = typeof window !== 'undefined' ? window.location.origin : 'https://windi-domain.com';
    return `${origin}/app/api/dragon${path}`;
  }

  /**
   * Send message to Dragon with proper history
   *
   * @param {string} message - User message
   * @param {Object} options - Additional options
   * @returns {Promise<Object>} Dragon response
   */
  async chat(message, options = {}) {
    const {
      tier = this.session?.metadata?.tier || 'personal',
      lang = this.session?.metadata?.lang || 'de',
      docType = this.session?.metadata?.docType,
      chatType = 'chat',
      intentMode = 'chat',
      includeHistory = true
    } = options;

    // Add user message to session
    if (this.session) {
      this.session.addUserMessage(message);
    }

    // Build request body with valid history
    const body = {
      message: message,
      tier: tier,
      language: lang,
      chatType: chatType,
      intentMode: intentMode
    };

    // Inject valid history for context continuity
    if (includeHistory && this.session) {
      // KEY: Use content field, not text field
      body.history = this.session.getHistoryForBackend(20);
    }

    // Add document type context if available
    if (docType) {
      body.doc_type = docType;
    }

    // Make API call
    const url = this._buildUrl('/chat');
    this.onStatusChange('sending');

    try {
      const response = await this._fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
      });

      const data = await response.json();

      // Add assistant message to session
      if (this.session && data.message) {
        this.session.addAssistantMessage(data.message, {
          source: data.source,
          dragon: data.dragon
        });
      }

      this.onStatusChange('ready');
      return {
        success: true,
        message: data.message,
        dragon: data.dragon || 'guardian',
        source: data.source || 'semantic',
        metadata: data.metadata || {}
      };

    } catch (error) {
      this.onStatusChange('error');
      return {
        success: false,
        error: error.message,
        fallback: this._getFallbackMessage(lang)
      };
    }
  }

  /**
   * Fetch with retry logic
   */
  async _fetch(url, options, retries = this.retryCount) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.defaultTimeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal
      });

      clearTimeout(timeout);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return response;

    } catch (error) {
      clearTimeout(timeout);

      if (retries > 0 && error.name !== 'AbortError') {
        // Wait before retry (exponential backoff)
        await new Promise(r => setTimeout(r, (this.retryCount - retries + 1) * 1000));
        return this._fetch(url, options, retries - 1);
      }

      throw error;
    }
  }

  /**
   * Get fallback message when API fails
   */
  _getFallbackMessage(lang) {
    const messages = {
      de: 'Entschuldigung, ich konnte keine Verbindung herstellen. Bitte versuchen Sie es erneut.',
      en: 'Sorry, I could not connect. Please try again.',
      pt: 'Desculpe, não consegui conectar. Por favor, tente novamente.'
    };
    return messages[lang] || messages.en;
  }

  /**
   * Check Dragon server health
   */
  async checkHealth() {
    const url = this._buildUrl('/health');

    try {
      const response = await this._fetch(url, { method: 'GET' });
      const data = await response.json();
      return {
        healthy: data.status === 'healthy' || data.status === 'ok',
        version: data.version,
        dragons: data.dragons
      };
    } catch (error) {
      return {
        healthy: false,
        error: error.message
      };
    }
  }

  /**
   * Generate document via Dragon
   */
  async generateDocument(docType, fields, options = {}) {
    const url = this._buildUrl('/generate');

    const body = {
      doc_type: docType,
      fields: fields,
      lang: options.lang || this.session?.metadata?.lang || 'de',
      format: options.format || 'json'
    };

    try {
      const response = await this._fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      return await response.json();
    } catch (error) {
      return { error: error.message };
    }
  }

  /**
   * Seal document via Ledger
   */
  async sealDocument(document, options = {}) {
    const ledgerUrl = this._buildLedgerUrl('/seal');

    try {
      const response = await this._fetch(ledgerUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: document,
          wallet_id: options.walletId || this.session?.metadata?.walletId,
          doc_type: options.docType
        })
      });

      return await response.json();
    } catch (error) {
      return { error: error.message };
    }
  }

  /**
   * Build Ledger URL (similar logic to Dragon URL)
   */
  _buildLedgerUrl(path) {
    const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';

    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return `http://localhost:8101${path}`;
    }

    const origin = typeof window !== 'undefined' ? window.location.origin : 'https://windi-domain.com';
    return `${origin}/ledger${path}`;
  }
}

/**
 * Create DragonCore instance with session
 */
function createDragonCore(options = {}) {
  const session = options.session || (typeof getSession !== 'undefined' ? getSession() : null);
  return new DragonCore({ ...options, session });
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { DragonCore, createDragonCore, DRAGON_TYPES };
}

// Export for browser
if (typeof window !== 'undefined') {
  window.DragonCore = DragonCore;
  window.createDragonCore = createDragonCore;
  window.DRAGON_TYPES = DRAGON_TYPES;
}
