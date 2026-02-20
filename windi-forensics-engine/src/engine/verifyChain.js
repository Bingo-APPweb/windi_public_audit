// src/engine/verifyChain.js
const { computeEventHash } = require("../hash");

function verifyChain(timeline) {
  const problems = [];
  let prev = "GENESIS";

  for (let i = 0; i < timeline.length; i++) {
    const e = timeline[i];

    // 1) prev_hash encadeado
    if ((e.prev_hash || "GENESIS") !== prev) {
      problems.push({
        index: i,
        code: "CHAIN_BREAK",
        expected_prev: prev,
        got_prev: e.prev_hash || "GENESIS"
      });
    }

    // 2) event_hash bate com conteúdo
    const { event_hash, ...core } = e;
    const recomputed = computeEventHash(core);
    if (recomputed !== event_hash) {
      problems.push({
        index: i,
        code: "HASH_MISMATCH",
        expected_hash: recomputed,
        got_hash: event_hash
      });
    }

    prev = e.event_hash;
  }

  return {
    ok: problems.length === 0,
    problems
  };
}

module.exports = { verifyChain };
