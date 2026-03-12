/**
 * W-FERR-001 — Probe Services
 * ============================
 * Verifica saúde de todos os serviços WINDI.
 *
 * Retorna: { id, status, latency, error?, detail? }
 */

const TIMEOUT_MS = 5000;

const SERVICES = [
  { id: 'dragon',     port: 8108, path: '/api/dragon/health', critical: true,  name: 'Dragon Server' },
  { id: 'ledger',     port: 8101, path: '/health',            critical: true,  name: 'Forensic Ledger' },
  { id: 'export',     port: 8103, path: '/health',            critical: false, name: 'Export Engine' },
  { id: 'vault',      port: 8106, path: '/health',            critical: false, name: 'Vault' },
  { id: 'communique', port: 8105, path: '/health',            critical: false, name: 'Communiqué' },
  { id: 'wallet',     port: 8098, path: '/health',            critical: false, name: 'Wallet' },
  { id: 'bridge',     port: 8097, path: '/health',            critical: false, name: 'Bridge' },
  { id: 'pageStore',  port: 8091, path: '/health',            critical: false, name: 'Page Store' },
  { id: 'pioneer',    port: 8120, path: '/pioneer/health',    critical: false, name: 'Pioneer Landing' }
];

/**
 * Check single service health
 */
async function probeService(service) {
  const start = Date.now();
  const url = `http://127.0.0.1:${service.port}${service.path}`;

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);

    const response = await fetch(url, {
      method: 'GET',
      signal: controller.signal
    });

    clearTimeout(timeout);
    const latency = Date.now() - start;

    if (!response.ok) {
      return {
        id: service.id,
        name: service.name,
        port: service.port,
        status: 'ERROR',
        latency,
        errorId: 'PORTA_MORTA',
        detail: `HTTP ${response.status}`,
        critical: service.critical
      };
    }

    const data = await response.json().catch(() => ({}));

    return {
      id: service.id,
      name: service.name,
      port: service.port,
      status: 'OK',
      latency,
      version: data.version || null,
      detail: data.status || 'healthy',
      critical: service.critical
    };

  } catch (error) {
    const latency = Date.now() - start;

    // Determine error type
    let errorId = 'PORTA_MORTA';
    let detail = error.message;

    if (error.name === 'AbortError') {
      detail = 'Timeout após ' + TIMEOUT_MS + 'ms';
      errorId = 'ZOMBI'; // Pode ser processo zombi
    } else if (error.code === 'ECONNREFUSED') {
      detail = 'Conexão recusada - serviço morto';
    }

    // Critical services get level 4
    if (service.critical && service.id === 'ledger') {
      errorId = 'LEDGER_MORTO';
    }

    return {
      id: service.id,
      name: service.name,
      port: service.port,
      status: 'DOWN',
      latency,
      errorId,
      detail,
      critical: service.critical
    };
  }
}

/**
 * Probe all services
 */
async function probeAllServices() {
  const results = await Promise.all(SERVICES.map(probeService));

  const ok = results.filter(r => r.status === 'OK').length;
  const down = results.filter(r => r.status === 'DOWN').length;
  const error = results.filter(r => r.status === 'ERROR').length;

  return {
    type: 'services',
    timestamp: new Date().toISOString(),
    total: SERVICES.length,
    ok,
    down,
    error,
    score: Math.round((ok / SERVICES.length) * 100),
    results
  };
}

/**
 * Get service by ID
 */
function getService(id) {
  return SERVICES.find(s => s.id === id) || null;
}

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { probeService, probeAllServices, getService, SERVICES };
}

if (typeof window !== 'undefined') {
  window.FerreiroProbServices = { probeService, probeAllServices, getService, SERVICES };
}
