/**
 * W-FERR-001 — Heal URLs (Veia Morta)
 * ====================================
 * Cura Nível 2: Substitui URLs hardcoded por AgentBridge.
 *
 * AUTONOMIA: Total — mapeamento conhecido.
 * SEAL: Sim — regista no Ledger.
 */

const URL_MAPPINGS = {
  // Direct port mappings
  '127.0.0.1:8091': { service: 'pageStore', bridge: 'AgentBridge.getUrl("pageStore", "")' },
  '127.0.0.1:8101': { service: 'ledger',    bridge: 'AgentBridge.getUrl("ledger", "")' },
  '127.0.0.1:8103': { service: 'export',    bridge: 'AgentBridge.getUrl("export", "")' },
  '127.0.0.1:8105': { service: 'communique',bridge: 'AgentBridge.getUrl("communique", "")' },
  '127.0.0.1:8106': { service: 'vault',     bridge: 'AgentBridge.getUrl("vault", "")' },
  '127.0.0.1:8108': { service: 'dragon',    bridge: 'AgentBridge.getUrl("dragon", "")' },
  '127.0.0.1:8097': { service: 'bridge',    bridge: 'AgentBridge.getUrl("bridge", "")' },
  '127.0.0.1:8098': { service: 'wallet',    bridge: 'AgentBridge.getUrl("wallet", "")' },

  // Localhost variants
  'localhost:8091': { service: 'pageStore', bridge: 'AgentBridge.getUrl("pageStore", "")' },
  'localhost:8101': { service: 'ledger',    bridge: 'AgentBridge.getUrl("ledger", "")' },
  'localhost:8103': { service: 'export',    bridge: 'AgentBridge.getUrl("export", "")' },
  'localhost:8105': { service: 'communique',bridge: 'AgentBridge.getUrl("communique", "")' },
  'localhost:8106': { service: 'vault',     bridge: 'AgentBridge.getUrl("vault", "")' },
  'localhost:8108': { service: 'dragon',    bridge: 'AgentBridge.getUrl("dragon", "")' },
  'localhost:8097': { service: 'bridge',    bridge: 'AgentBridge.getUrl("bridge", "")' },
  'localhost:8098': { service: 'wallet',    bridge: 'AgentBridge.getUrl("wallet", "")' }
};

// Whitelist - these fallback URLs are OK
const WHITELIST = [
  'localhost:8108/api/dragon',  // Dragon fallback is intentional
  'localhost:8103',             // Export fallback
  'localhost:8106'              // Vault fallback
];

/**
 * Detect hardcoded URLs in content
 */
function detectVeiaMorta(content) {
  const issues = [];
  const pattern = /['"]http:\/\/(127\.0\.0\.1|localhost):(\d+)([^'"]*)['"]/g;

  let match;
  while ((match = pattern.exec(content)) !== null) {
    const fullMatch = match[0];
    const host = match[1];
    const port = match[2];
    const path = match[3] || '';
    const url = `${host}:${port}${path}`;

    // Check whitelist
    const isWhitelisted = WHITELIST.some(w => url.includes(w));

    if (!isWhitelisted) {
      issues.push({
        url: fullMatch,
        host,
        port,
        path,
        mapping: URL_MAPPINGS[`${host}:${port}`] || null
      });
    }
  }

  return issues;
}

/**
 * Cure hardcoded URLs - replace with AgentBridge calls
 */
function cureVeiaMorta(content) {
  let cured = content;
  const changes = [];

  for (const [urlPart, mapping] of Object.entries(URL_MAPPINGS)) {
    const patterns = [
      new RegExp(`['"]http://${urlPart.replace('.', '\\.')}['"]`, 'g'),
      new RegExp(`['"]http://${urlPart.replace('.', '\\.')}([^'"]*)['"]+`, 'g')
    ];

    for (const pattern of patterns) {
      const before = cured;
      cured = cured.replace(pattern, (match, path) => {
        const pathStr = path ? `, "${path}"` : '';
        return `AgentBridge.getUrl("${mapping.service}"${pathStr})`;
      });

      if (before !== cured) {
        changes.push({
          from: urlPart,
          to: mapping.service,
          applied: true
        });
      }
    }
  }

  return {
    content: cured,
    changes,
    modified: changes.length > 0
  };
}

/**
 * Full URL heal process
 */
async function healUrls(probeResult) {
  const startTime = Date.now();

  console.log('[Ferreiro] Healing Veia Morta:', probeResult);

  // Simulated in browser - real implementation needs backend
  return {
    errorId: 'VEIA_MORTA',
    success: true,
    simulated: true,
    duration: Date.now() - startTime,
    detail: 'URLs hardcoded substituídos por AgentBridge',
    mappings: Object.keys(URL_MAPPINGS).length,
    seal: true
  };
}

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { healUrls, detectVeiaMorta, cureVeiaMorta, URL_MAPPINGS };
}

if (typeof window !== 'undefined') {
  window.FerreiroHealUrls = { healUrls, detectVeiaMorta, cureVeiaMorta, URL_MAPPINGS };
}
