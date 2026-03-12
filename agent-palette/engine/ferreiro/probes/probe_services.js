/**
 * W-FERR-001 — Probe Services
 * ============================
 * Verifica saúde de todos os serviços WINDI.
 *
 * Retorna: { id, status, latency, error?, detail? }
 */

const TIMEOUT_MS = 5000;

// Detect environment
const isLocal = typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

const SERVICES = [
  { id: 'dragon',     port: 8108, path: '/api/dragon/health', healthPath: '/dragon/health',       critical: true,  name: 'Dragon Server',     enabled: true },
  { id: 'ledger',     port: 8101, path: '/health',            healthPath: '/ledger/health',       critical: true,  name: 'Forensic Ledger',   enabled: true },
  { id: 'export',     port: 8103, path: '/health',            healthPath: '/export/health',       critical: false, name: 'Export Engine',     enabled: true },
  { id: 'vault',      port: 8106, path: '/health',            healthPath: '/vault/health',        critical: false, name: 'Vault',             enabled: true },
  { id: 'communique', port: 8105, path: '/health',            healthPath: '/communique/health',   critical: false, name: 'Communiqué',        enabled: true },
  { id: 'wallet',     port: 8098, path: '/health',            healthPath: '/sentinel/health',     critical: false, name: 'Wallet',            enabled: true },
  { id: 'bridge',     port: 8097, path: '/health',            healthPath: '/bridge/health',       critical: false, name: 'Bridge',            enabled: true },
  { id: 'pageStore',  port: 8091, path: '/health',            healthPath: '/pagestore/health',    critical: false, name: 'Page Store',        enabled: false }, // nginx route pendente
  { id: 'pioneer',    port: 8120, path: '/pioneer/health',    healthPath: '/pioneer/health',      critical: false, name: 'Pioneer Landing',   enabled: false }  // serviço não deployado
];

/**
 * Check single service health
 */
async function probeService(service) {
  const start = Date.now();
  // Use relative URL in production (nginx proxy), localhost in dev
  const url = isLocal
    ? `http://127.0.0.1:${service.port}${service.path}`
    : service.healthPath;

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
  const activeServices = SERVICES.filter(s => s.enabled !== false);
  const results = await Promise.all(activeServices.map(probeService));

  const ok = results.filter(r => r.status === 'OK').length;
  const down = results.filter(r => r.status === 'DOWN').length;
  const error = results.filter(r => r.status === 'ERROR').length;

  return {
    type: 'services',
    timestamp: new Date().toISOString(),
    total: activeServices.length,
    ok,
    down,
    error,
    score: Math.round((ok / activeServices.length) * 100),
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
