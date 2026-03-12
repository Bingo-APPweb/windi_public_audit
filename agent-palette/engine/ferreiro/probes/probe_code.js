/**
 * W-FERR-001 — Probe Code
 * ========================
 * Verifica problemas de código conhecidos:
 * - ALZHEIMER: text: em vez de content:
 * - VEIA_MORTA: URLs hardcoded
 * - LOOP_SESSION: sessionStorage sem guard
 *
 * NOTA: Em browser, usa fetch para ler ficheiros.
 *       Em Node.js, usa fs.
 */

const CODE_CHECKS = [
  {
    id: 'ALZHEIMER',
    name: 'Dragon Alzheimer',
    description: 'History usa text: em vez de content:',
    file: '/app/',  // Fetches the rendered page
    pattern: /role.*['"]human['"].*text:|\.map\(m=>\(\{role.*text:m\.text/g,
    antiPattern: /role.*['"]human['"].*content:|\.map\(m=>\(\{role.*content:/g,
    severity: 'high'
  },
  {
    id: 'VEIA_MORTA',
    name: 'URL Hardcoded',
    description: 'URLs 127.0.0.1 ou localhost hardcoded',
    file: '/app/',
    pattern: /['"]http:\/\/127\.0\.0\.1:\d+|['"]http:\/\/localhost:\d+/g,
    whitelist: ['localhost:8108/api/dragon', 'localhost:8103', 'localhost:8106'], // Fallbacks OK
    severity: 'medium'
  },
  {
    id: 'LOOP_SESSION',
    name: 'SessionStorage sem Guard',
    description: 'sessionStorage.getItem sem verificar length',
    file: '/app/',
    pattern: /sessionStorage\.getItem\([^)]+\)(?!.*length)/g,
    antiPattern: /\.length\s*===\s*0|\.length\s*>\s*0/g,
    severity: 'low'
  }
];

/**
 * Fetch page content (browser)
 */
async function fetchPageContent(path) {
  try {
    const response = await fetch(path);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.text();
  } catch (error) {
    return null;
  }
}

/**
 * Check single code issue
 */
async function probeCodeIssue(check, content) {
  if (!content) {
    return {
      id: check.id,
      name: check.name,
      status: 'SKIP',
      detail: 'Não foi possível ler o ficheiro'
    };
  }

  const matches = content.match(check.pattern) || [];

  // Filter whitelist if exists
  let filteredMatches = matches;
  if (check.whitelist) {
    filteredMatches = matches.filter(m => {
      return !check.whitelist.some(w => m.includes(w));
    });
  }

  // Check for anti-pattern (fix already applied)
  if (check.antiPattern) {
    const antiMatches = content.match(check.antiPattern) || [];
    if (antiMatches.length > 0 && filteredMatches.length === 0) {
      return {
        id: check.id,
        name: check.name,
        status: 'OK',
        detail: 'Corrigido - padrão correcto encontrado'
      };
    }
  }

  if (filteredMatches.length > 0) {
    return {
      id: check.id,
      name: check.name,
      status: 'ISSUE',
      errorId: check.id,
      count: filteredMatches.length,
      matches: filteredMatches.slice(0, 5), // Max 5 examples
      severity: check.severity,
      detail: `${filteredMatches.length} ocorrência(s) encontrada(s)`
    };
  }

  return {
    id: check.id,
    name: check.name,
    status: 'OK',
    detail: 'Nenhum problema detectado'
  };
}

/**
 * Probe all code issues
 */
async function probeAllCode() {
  // Fetch the main app page
  const content = await fetchPageContent('/app/');

  const results = await Promise.all(
    CODE_CHECKS.map(check => probeCodeIssue(check, content))
  );

  const ok = results.filter(r => r.status === 'OK').length;
  const issues = results.filter(r => r.status === 'ISSUE').length;
  const skip = results.filter(r => r.status === 'SKIP').length;

  return {
    type: 'code',
    timestamp: new Date().toISOString(),
    total: CODE_CHECKS.length,
    ok,
    issues,
    skip,
    score: Math.round((ok / (CODE_CHECKS.length - skip)) * 100) || 0,
    results
  };
}

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { probeCodeIssue, probeAllCode, CODE_CHECKS };
}

if (typeof window !== 'undefined') {
  window.FerreiroProbeCode = { probeCodeIssue, probeAllCode, CODE_CHECKS };
}
