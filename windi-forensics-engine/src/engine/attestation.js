// src/engine/attestation.js
const crypto = require("crypto");
const { stableStringify, sha256Hex } = require("../hash");

/**
 * Creates an institutional attestation for the current chain head.
 *
 * @param {Object} opts
 * @param {Object} opts.store - Store instance (must support getLastHash)
 * @param {string} opts.document_id - Document to attest
 * @param {string} opts.key_id - Institutional key identifier
 * @param {string} opts.privateKey - PEM-encoded private key (RSA or Ed25519)
 * @param {string} [opts.algorithm] - Signature algorithm (default: RSA-SHA256)
 */
async function createAttestation({ store, document_id, key_id, privateKey, algorithm = "RSA-SHA256" }) {
  const head_event_hash = await store.getLastHash(document_id);

  if (!head_event_hash) {
    throw new Error(`No events found for document_id: ${document_id}`);
  }

  const attested_at = new Date().toISOString();

  // Payload to sign
  const attestPayload = {
    document_id,
    head_event_hash,
    attested_at,
    schema_version: "wcaf-attestation-1.0"
  };

  // Canonicalize and hash
  const canonical = stableStringify(attestPayload);
  const payloadHash = sha256Hex(canonical);

  // Sign
  let signature;
  let signature_alg;

  if (algorithm === "Ed25519" || algorithm.toLowerCase().includes("ed25519")) {
    signature_alg = "Ed25519";
    const sign = crypto.sign(null, Buffer.from(payloadHash), privateKey);
    signature = sign.toString("base64");
  } else {
    // Default RSA-SHA256
    signature_alg = "RSA-SHA256";
    const sign = crypto.createSign("SHA256");
    sign.update(payloadHash);
    signature = sign.sign(privateKey, "base64");
  }

  return {
    document_id,
    head_event_hash,
    attested_at,
    signature_alg,
    signature,
    key_id,
    schema_version: "wcaf-attestation-1.0"
  };
}

/**
 * Verifies an attestation signature.
 *
 * @param {Object} attestation - Attestation object
 * @param {string} publicKey - PEM-encoded public key
 * @returns {boolean} - True if signature is valid
 */
function verifyAttestation(attestation, publicKey) {
  const { signature, signature_alg, ...rest } = attestation;

  // Reconstruct payload (excluding signature fields)
  const attestPayload = {
    document_id: rest.document_id,
    head_event_hash: rest.head_event_hash,
    attested_at: rest.attested_at,
    schema_version: rest.schema_version
  };

  const canonical = stableStringify(attestPayload);
  const payloadHash = sha256Hex(canonical);

  try {
    if (signature_alg === "Ed25519") {
      return crypto.verify(
        null,
        Buffer.from(payloadHash),
        publicKey,
        Buffer.from(signature, "base64")
      );
    } else {
      // RSA-SHA256
      const verify = crypto.createVerify("SHA256");
      verify.update(payloadHash);
      return verify.verify(publicKey, signature, "base64");
    }
  } catch (err) {
    return false;
  }
}

module.exports = { createAttestation, verifyAttestation };
