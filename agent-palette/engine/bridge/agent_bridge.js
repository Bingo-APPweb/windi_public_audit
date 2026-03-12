/**
 * WINDI DragonEngine v2.0 — AgentBridge
 * ======================================
 * Unified endpoint resolver for mobile and desktop.
 *
 * KEY FIX: No more hardcoded 127.0.0.1 or localhost URLs.
 * Uses relative paths that nginx proxies to correct ports.
 *
 * Service Map:
 *   /app/api/dragon → Dragon Server (8108)
 *   /ledger         → Ledger API (8101)
 *   /export         → Export Engine (8103)
 *   /vault          → Vault Service (8106)
 *   /communique     → Communiqué Engine (8105)
 *   /bridge         → Command Bridge (8097)
 *   /wallet         → Wallet Service (8098)
 *   /id-genesis     → ID Genesis (8096)
 *
 * Three Dragons Protocol: AI processes. Human decides. WINDI guarantees.
 * (c) 2026 WINDI Publishing House — Kempten, Bavaria
 */

const SERVICE_PORTS = {
  dragon:       8108,
  ledger:       8101,
  export:       8103,
  vault:        8106,
  communique:   8105,
  bridge:       8097,
  wallet:       8098,
  idGenesis:    8096,
  schnittstelle: 8095,
  cortex:       8889,
  sentinelLaw:  8102,
  pageStore:    8091,
  whatsapp:     8111
};

const SERVICE_PATHS = {
  dragon:       '/app/api/dragon',
  ledger:       '/ledger',
  export:       '/export',
  vault:        '/vault',
  communique:   '/communique',
  bridge:       '/bridge',
  wallet:       '/wallet',
  idGenesis:    '/id-genesis',
  schnittstelle: '/schnittstelle',
  cortex:       '/cortex',
  sentinelLaw:  '/sentinel-law',
  pageStore:    '/page-store',
  whatsapp:     '/whatsapp'
};

class AgentBridge {
  constructor() {
    this.isLocal = this._detectLocalEnvironment();
    this.origin = this._getOrigin();
    this.healthCache = {};
    this.healthCacheTTL = 30000; // 30 seconds
  }

  /**
   * Detect if running in local development
   */
  _detectLocalEnvironment() {
    if (typeof window === 'undefined') {
      return process.env.NODE_ENV !== 'production';
    }

    const hostname = window.location.hostname;
    return hostname === 'localhost' || hostname === '127.0.0.1';
  }

  /**
   * Get origin URL
   */
  _getOrigin() {
    if (typeof window === 'undefined') {
      return process.env.WINDI_ORIGIN || 'https://windi-domain.com';
    }
    return window.location.origin;
  }

  /**
   * Get endpoint URL for a service
   *
   * @param {string} service - Service name (dragon, ledger, export, etc.)
   * @param {string} path - API path (e.g., '/chat', '/health')
   * @returns {string} Full URL
   */
  getUrl(service, path = '') {
    const port = SERVICE_PORTS[service];
    const proxyPath = SERVICE_PATHS[service];

    if (!port) {
      console.warn(`[AgentBridge] Unknown service: ${service}`);
      return null;
    }

    // Local development: direct port access
    if (this.isLocal) {
      return `http://localhost:${port}${path}`;
    }

    // Production: use nginx proxy paths
    return `${this.origin}${proxyPath}${path}`;
  }

  /**
   * Get Dragon API URL
   */
  getDragonUrl(path = '') {
    return this.getUrl('dragon', path);
  }

  /**
   * Get Ledger API URL
   */
  getLedgerUrl(path = '') {
    return this.getUrl('ledger', path);
  }

  /**
   * Get Export Engine URL
   */
  getExportUrl(path = '') {
    return this.getUrl('export', path);
  }

  /**
   * Get Vault URL
   */
  getVaultUrl(path = '') {
    return this.getUrl('vault', path);
  }

  /**
   * Get Communiqué URL
   */
  getCommuniqueUrl(path = '') {
    return this.getUrl('communique', path);
  }

  /**
   * Get Wallet URL
   */
  getWalletUrl(path = '') {
    return this.getUrl('wallet', path);
  }

  /**
   * Get all health endpoints
   */
  getHealthEndpoints() {
    const endpoints = {};

    for (const service of Object.keys(SERVICE_PORTS)) {
      endpoints[service] = this.getUrl(service, '/health');
    }

    return endpoints;
  }

  /**
   * Check health of a service with caching
   */
  async checkHealth(service) {
    const now = Date.now();
    const cached = this.healthCache[service];

    // Return cached if valid
    if (cached && (now - cached.timestamp) < this.healthCacheTTL) {
      return cached.data;
    }

    const url = this.getUrl(service, '/health');

    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 5000);

      const response = await fetch(url, {
        method: 'GET',
        signal: controller.signal
      });

      clearTimeout(timeout);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      const result = {
        status: 'healthy',
        service: service,
        data: data
      };

      // Cache the result
      this.healthCache[service] = { data: result, timestamp: now };
      return result;

    } catch (error) {
      const result = {
        status: 'unhealthy',
        service: service,
        error: error.message
      };

      // Cache failure too (shorter TTL)
      this.healthCache[service] = { data: result, timestamp: now - (this.healthCacheTTL / 2) };
      return result;
    }
  }

  /**
   * Check health of all services
   */
  async checkAllHealth() {
    const services = Object.keys(SERVICE_PORTS);
    const results = {};

    await Promise.all(
      services.map(async (service) => {
        results[service] = await this.checkHealth(service);
      })
    );

    return results;
  }

  /**
   * Make authenticated request to a service
   */
  async request(service, path, options = {}) {
    const url = this.getUrl(service, path);

    const defaultOptions = {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    };

    const mergedOptions = { ...defaultOptions, ...options };

    // Add admin key if provided
    if (options.adminKey) {
      mergedOptions.headers['X-WINDI-Admin-Key'] = options.adminKey;
      delete mergedOptions.adminKey;
    }

    // Stringify body if object
    if (mergedOptions.body && typeof mergedOptions.body === 'object') {
      mergedOptions.body = JSON.stringify(mergedOptions.body);
    }

    try {
      const response = await fetch(url, mergedOptions);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }

      return await response.text();

    } catch (error) {
      console.error(`[AgentBridge] Request failed: ${service}${path}`, error);
      throw error;
    }
  }

  /**
   * Seal document via Ledger
   */
  async sealDocument(content, options = {}) {
    return this.request('ledger', '/seal', {
      method: 'POST',
      body: {
        content: content,
        wallet_id: options.walletId,
        doc_type: options.docType,
        title: options.title
      }
    });
  }

  /**
   * Export document
   */
  async exportDocument(format, content, options = {}) {
    return this.request('export', `/export/${format}`, {
      method: 'POST',
      body: {
        content: content,
        title: options.title,
        receipt_id: options.receiptId,
        lang: options.lang
      }
    });
  }

  /**
   * Store page in PageStore
   */
  async storePage(options = {}) {
    return this.request('pageStore', '/page/generate', {
      method: 'POST',
      body: {
        intent: options.content,
        title: options.title,
        doc_type: options.docType,
        wallet_id: options.walletId,
        receipt_id: options.receiptId,
        lang: options.lang,
        fields: options.fields
      }
    });
  }

  /**
   * Get environment info for debugging
   */
  getEnvironmentInfo() {
    return {
      isLocal: this.isLocal,
      origin: this.origin,
      services: Object.keys(SERVICE_PORTS),
      servicePaths: SERVICE_PATHS
    };
  }
}

// Singleton instance
let _bridgeInstance = null;

/**
 * Get or create bridge instance
 */
function getBridge() {
  if (!_bridgeInstance) {
    _bridgeInstance = new AgentBridge();
  }
  return _bridgeInstance;
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { AgentBridge, getBridge, SERVICE_PORTS, SERVICE_PATHS };
}

// Export for browser
if (typeof window !== 'undefined') {
  window.AgentBridge = AgentBridge;
  window.getBridge = getBridge;
  window.SERVICE_PORTS = SERVICE_PORTS;
  window.SERVICE_PATHS = SERVICE_PATHS;
}
