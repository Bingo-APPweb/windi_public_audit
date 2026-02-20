// src/hash.js
const crypto = require("crypto");

function stableStringify(obj) {
  // stringify determinístico simples (ordena chaves recursivamente)
  // Matches JSON.stringify behavior: skips undefined values
  if (obj === undefined) return undefined;
  if (obj === null) return "null";
  if (typeof obj !== "object") return JSON.stringify(obj);

  if (Array.isArray(obj)) {
    // Arrays: convert undefined to null (JSON.stringify behavior)
    return "[" + obj.map(item => {
      const s = stableStringify(item);
      return s === undefined ? "null" : s;
    }).join(",") + "]";
  }

  const keys = Object.keys(obj).sort();
  const parts = [];
  for (const k of keys) {
    const val = stableStringify(obj[k]);
    // Skip undefined values (JSON.stringify behavior)
    if (val !== undefined) {
      parts.push(JSON.stringify(k) + ":" + val);
    }
  }
  return "{" + parts.join(",") + "}";
}

function sha256Hex(input) {
  return crypto.createHash("sha256").update(input).digest("hex");
}

function computeEventHash(eventCore) {
  // eventCore deve excluir event_hash (obviamente)
  return sha256Hex(stableStringify(eventCore));
}

module.exports = { stableStringify, sha256Hex, computeEventHash };
