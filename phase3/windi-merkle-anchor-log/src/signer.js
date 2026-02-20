const fs = require("fs");
const crypto = require("crypto");
const { stableStringify } = require("./canonical");

/**
 * Signs STH payload with Ed25519 private key PEM.
 * Env:
 *  - LOG_SIGNING_KEY_PATH
 *  - LOG_KEY_ID
 */
function signSTH(sthPayload) {
  const keyPath = process.env.LOG_SIGNING_KEY_PATH;
  if (!keyPath) throw new Error("LOG_SIGNING_KEY_PATH missing");
  const privateKeyPem = fs.readFileSync(keyPath, "utf8");

  const msg = Buffer.from(stableStringify(sthPayload), "utf8");
  const signature = crypto.sign(null, msg, privateKeyPem); // Ed25519 uses null algorithm

  return {
    signature_alg: "Ed25519",
    signature: signature.toString("base64"),
    key_id: process.env.LOG_KEY_ID || "hub-log-2026"
  };
}

module.exports = { signSTH };
