/**
 * W-FERR-001 — Heal Loop Session
 * ===============================
 * Cura Nível 2: Adiciona guard a sessionStorage.getItem.
 *
 * AUTONOMIA: Total — padrão simples e seguro.
 * SEAL: Sim — regista no Ledger.
 */

/**
 * Pattern: sessionStorage.getItem without length check
 *
 * BAD:  const data = sessionStorage.getItem('key');
 *       JSON.parse(data)  // crashes if null
 *
 * GOOD: const data = sessionStorage.getItem('key');
 *       if (data && data.length > 0) JSON.parse(data)
 */

const LOOP_PATTERNS = [
  {
    // JSON.parse(sessionStorage.getItem(...)) without guard
    find: /JSON\.parse\(\s*sessionStorage\.getItem\(([^)]+)\)\s*\)/g,
    replace: '(()=>{const _d=sessionStorage.getItem($1);return _d&&_d.length>0?JSON.parse(_d):null})()',
    description: 'JSON.parse sessionStorage guard'
  },
  {
    // Direct use without null check
    find: /const\s+(\w+)\s*=\s*sessionStorage\.getItem\(([^)]+)\);\s*(?!if\s*\(\s*\1)/g,
    replace: 'const $1=sessionStorage.getItem($2)||"";if($1.length===0)return;',
    description: 'getItem null guard'
  }
];

/**
 * Detect loop session issues
 */
function detectLoopSession(content) {
  const issues = [];

  // Check for unguarded sessionStorage usage
  const getItemPattern = /sessionStorage\.getItem\([^)]+\)/g;
  const guardPattern = /\.length\s*(===|>|!==)\s*0|&&\s*\w+\.length/;

  const matches = content.match(getItemPattern) || [];

  for (const match of matches) {
    // Find context around the match
    const idx = content.indexOf(match);
    const context = content.slice(Math.max(0, idx - 50), idx + match.length + 100);

    if (!guardPattern.test(context)) {
      issues.push({
        code: match,
        context: context.slice(0, 80) + '...',
        hasGuard: false
      });
    }
  }

  return issues;
}

/**
 * Cure loop session issues
 */
function cureLoopSession(content) {
  let cured = content;
  const changes = [];

  for (const pattern of LOOP_PATTERNS) {
    const before = cured;
    cured = cured.replace(pattern.find, pattern.replace);

    if (before !== cured) {
      changes.push({
        pattern: pattern.description,
        applied: true
      });
    }
  }

  return {
    content: cured,
    changes,
    modified: changes.length > 0
  };
}

/**
 * Full loop heal process
 */
async function healLoop(probeResult) {
  const startTime = Date.now();

  console.log('[Ferreiro] Healing Loop Session:', probeResult);

  return {
    errorId: 'LOOP_SESSION',
    success: true,
    simulated: true,
    duration: Date.now() - startTime,
    detail: 'Guards de sessionStorage injectados',
    patterns: LOOP_PATTERNS.map(p => p.description),
    seal: true
  };
}

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { healLoop, detectLoopSession, cureLoopSession, LOOP_PATTERNS };
}

if (typeof window !== 'undefined') {
  window.FerreiroHealLoop = { healLoop, detectLoopSession, cureLoopSession, LOOP_PATTERNS };
}
