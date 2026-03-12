/**
 * W-FERR-001 — Probe Manifests
 * =============================
 * Verifica integridade dos 14+ manifests de documentos.
 *
 * Retorna: { id, status, error?, detail? }
 */

const MANIFEST_PATH = '/engine/manifests';

const MANIFESTS = [
  'letter', 'email', 'memo', 'note', 'journal', 'recipe',
  'report', 'contract', 'invoice', 'protocol', 'analysis',
  'presentation', 'communique', 'certificate', 'declaration', 'creative_virtue'
];

const REQUIRED_FIELDS = ['id', 'version', 'tier', 'category', 'names', 'schema'];

/**
 * Check single manifest
 */
async function probeManifest(name) {
  const url = `${MANIFEST_PATH}/${name}.json`;

  try {
    const response = await fetch(url);

    if (!response.ok) {
      return {
        id: name,
        status: 'MISSING',
        errorId: 'MANIFEST_INVALIDO',
        detail: `HTTP ${response.status} - ficheiro não encontrado`
      };
    }

    const text = await response.text();
    let data;

    try {
      data = JSON.parse(text);
    } catch (parseError) {
      return {
        id: name,
        status: 'CORRUPTED',
        errorId: 'MANIFEST_INVALIDO',
        detail: `JSON inválido: ${parseError.message}`
      };
    }

    // Validate required fields
    const missing = REQUIRED_FIELDS.filter(f => !data[f]);
    if (missing.length > 0) {
      return {
        id: name,
        status: 'INCOMPLETE',
        errorId: 'MANIFEST_INVALIDO',
        detail: `Campos em falta: ${missing.join(', ')}`
      };
    }

    // Validate trilingual names
    const langs = ['de', 'en', 'pt'];
    const missingLangs = langs.filter(l => !data.names[l]);
    if (missingLangs.length > 0) {
      return {
        id: name,
        status: 'WARNING',
        detail: `Idiomas em falta: ${missingLangs.join(', ')}`
      };
    }

    return {
      id: name,
      status: 'OK',
      version: data.version,
      tier: data.tier,
      category: data.category,
      fields: Object.keys(data.schema || {}).length
    };

  } catch (error) {
    return {
      id: name,
      status: 'ERROR',
      errorId: 'MANIFEST_INVALIDO',
      detail: error.message
    };
  }
}

/**
 * Probe all manifests
 */
async function probeAllManifests() {
  const results = await Promise.all(MANIFESTS.map(probeManifest));

  const ok = results.filter(r => r.status === 'OK').length;
  const warning = results.filter(r => r.status === 'WARNING').length;
  const error = results.filter(r => ['MISSING', 'CORRUPTED', 'INCOMPLETE', 'ERROR'].includes(r.status)).length;

  return {
    type: 'manifests',
    timestamp: new Date().toISOString(),
    total: MANIFESTS.length,
    ok,
    warning,
    error,
    score: Math.round((ok / MANIFESTS.length) * 100),
    results
  };
}

/**
 * Get manifest by name
 */
function getManifest(name) {
  return MANIFESTS.includes(name) ? name : null;
}

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { probeManifest, probeAllManifests, getManifest, MANIFESTS };
}

if (typeof window !== 'undefined') {
  window.FerreiroProbeManifests = { probeManifest, probeAllManifests, getManifest, MANIFESTS };
}
