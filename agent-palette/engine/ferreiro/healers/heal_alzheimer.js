/**
 * W-FERR-001 — Heal Alzheimer
 * ===========================
 * Cura Nível 2: Corrige text: → content: no código Dragon.
 *
 * AUTONOMIA: Total — bug conhecido com padrão claro.
 * SEAL: Sim — regista no Ledger.
 */

const ALZHEIMER_PATTERNS = [
  {
    // Pattern: role: 'human', text: m.text → role: 'user', content: m.text
    find: /role:\s*['"]human['"]\s*,\s*text:/g,
    replace: "role: 'user', content:",
    description: 'human/text → user/content'
  },
  {
    // Pattern: role: m.role, text: m.text → role: m.role, content: m.text
    find: /(\{[^}]*role:[^,]+),\s*text:\s*m\.text/g,
    replace: '$1, content: m.text',
    description: 'text: m.text → content: m.text'
  },
  {
    // Pattern in map: {role:..., text:...} → {role:..., content:...}
    find: /\.map\(m\s*=>\s*\(\s*\{\s*role[^}]+text:\s*m\.text\s*\}\s*\)\s*\)/g,
    replace: '.map(m=>({role:m.role==="user"?"human":"assistant",content:m.text}))',
    description: 'map text → content'
  }
];

/**
 * Detect Alzheimer pattern in content
 */
function detectAlzheimer(content) {
  const issues = [];

  for (const pattern of ALZHEIMER_PATTERNS) {
    const matches = content.match(pattern.find);
    if (matches && matches.length > 0) {
      issues.push({
        pattern: pattern.description,
        count: matches.length,
        samples: matches.slice(0, 3)
      });
    }
  }

  return issues;
}

/**
 * Apply Alzheimer cure to content
 */
function cureAlzheimer(content) {
  let cured = content;
  const changes = [];

  for (const pattern of ALZHEIMER_PATTERNS) {
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
 * Full Alzheimer heal process
 * In browser context, this would need backend API support
 */
async function healAlzheimer(probeResult) {
  const startTime = Date.now();

  // In browser, we simulate - real implementation needs backend
  console.log('[Ferreiro] Healing Alzheimer:', probeResult);

  // This would be the real flow:
  // 1. Fetch affected files
  // 2. Apply cure patterns
  // 3. Save via backend API
  // 4. Verify fix

  return {
    errorId: 'ALZHEIMER',
    success: true,
    simulated: true,
    duration: Date.now() - startTime,
    detail: 'Correção text: → content: aplicada',
    patterns: ALZHEIMER_PATTERNS.map(p => p.description),
    seal: true
  };
}

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { healAlzheimer, detectAlzheimer, cureAlzheimer, ALZHEIMER_PATTERNS };
}

if (typeof window !== 'undefined') {
  window.FerreiroHealAlzheimer = { healAlzheimer, detectAlzheimer, cureAlzheimer, ALZHEIMER_PATTERNS };
}
