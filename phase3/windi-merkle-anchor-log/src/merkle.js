/**
 * ═══════════════════════════════════════════════════════════════════
 * WINDI Merkle Anchor Log — Merkle Tree Operations
 * ═══════════════════════════════════════════════════════════════════
 * RFC6962-style Merkle tree root computation
 * ═══════════════════════════════════════════════════════════════════
 */

const { nodeHash } = require("./hash");

/**
 * Build merkle root from leaf hashes (Buffers) using RFC6962-style hashing.
 * Returns Buffer(32). For empty tree, returns Buffer.alloc(32,0).
 */
function merkleRoot(leafHashes) {
  const n = leafHashes.length;
  if (n === 0) return Buffer.alloc(32, 0);

  // copy
  let level = leafHashes.slice();
  while (level.length > 1) {
    const next = [];
    for (let i = 0; i < level.length; i += 2) {
      if (i + 1 === level.length) next.push(level[i]);
      else next.push(nodeHash(level[i], level[i + 1]));
    }
    level = next;
  }
  return level[0];
}

module.exports = { merkleRoot };
