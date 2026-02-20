// src/engine/bundle.js
const crypto = require("crypto");
const { stableStringify, sha256Hex } = require("../hash");
const { verifyChain } = require("./verifyChain");

/**
 * Creates a portable WCAF bundle for external audit.
 *
 * @param {Object} opts
 * @param {Array} opts.timeline - Array of events
 * @param {Object} [opts.attestation] - Optional attestation object
 * @param {string} [opts.privateKey] - Optional key to sign the bundle
 * @param {string} [opts.keyId] - Key identifier for bundle signature
 */
function createBundle({ timeline, attestation, privateKey, keyId }) {
  if (!timeline || timeline.length === 0) {
    throw new Error("Timeline is empty");
  }

  const document_id = timeline[0].document_id;
  const chainCheck = verifyChain(timeline);
  const head_event_hash = timeline[timeline.length - 1].event_hash;

  const bundle = {
    bundle_version: "wcaf-bundle-1.0",
    document_id,
    created_at: new Date().toISOString(),

    timeline: timeline.map(e => ({
      event_id: e.event_id,
      ts: e.ts,
      document_id: e.document_id,
      type: e.type,
      actor: e.actor,
      payload: e.payload,
      prev_hash: e.prev_hash,
      event_hash: e.event_hash,
      schema_version: e.schema_version || "wcaf-1.0"
    })),

    chain_verification: {
      verified: chainCheck.ok,
      problems: chainCheck.problems.length > 0 ? chainCheck.problems : undefined,
      head_event_hash,
      event_count: timeline.length
    }
  };

  // Include attestation if provided
  if (attestation) {
    bundle.attestation = {
      attested_at: attestation.attested_at,
      head_event_hash: attestation.head_event_hash,
      signature_alg: attestation.signature_alg,
      signature: attestation.signature,
      key_id: attestation.key_id,
      schema_version: attestation.schema_version
    };
  }

  // Sign the entire bundle if private key provided
  if (privateKey && keyId) {
    const bundleForSigning = { ...bundle };
    const canonical = stableStringify(bundleForSigning);
    const bundleHash = sha256Hex(canonical);

    const sign = crypto.createSign("SHA256");
    sign.update(bundleHash);
    const signature = sign.sign(privateKey, "base64");

    bundle.bundle_signature = {
      alg: "RSA-SHA256",
      key_id: keyId,
      signature,
      signed_hash: bundleHash
    };
  }

  return bundle;
}

/**
 * Verifies a WCAF bundle signature and chain integrity.
 *
 * @param {Object} bundle - WCAF bundle
 * @param {string} [publicKey] - Public key for signature verification
 * @returns {Object} - Verification result
 */
function verifyBundle(bundle, publicKey) {
  const result = {
    bundle_version_ok: bundle.bundle_version === "wcaf-bundle-1.0",
    chain_verified: false,
    bundle_signature_verified: null,
    attestation_present: !!bundle.attestation,
    problems: []
  };

  // Verify chain
  if (bundle.timeline && bundle.timeline.length > 0) {
    const chainCheck = verifyChain(bundle.timeline);
    result.chain_verified = chainCheck.ok;
    if (!chainCheck.ok) {
      result.problems.push(...chainCheck.problems);
    }
  }

  // Verify bundle signature if present and public key provided
  if (bundle.bundle_signature && publicKey) {
    try {
      const { bundle_signature, ...bundleWithoutSig } = bundle;
      const canonical = stableStringify(bundleWithoutSig);
      const bundleHash = sha256Hex(canonical);

      // Check hash matches
      if (bundleHash !== bundle_signature.signed_hash) {
        result.bundle_signature_verified = false;
        result.problems.push({ code: "BUNDLE_HASH_MISMATCH" });
      } else {
        const verify = crypto.createVerify("SHA256");
        verify.update(bundleHash);
        result.bundle_signature_verified = verify.verify(
          publicKey,
          bundle_signature.signature,
          "base64"
        );
      }
    } catch (err) {
      result.bundle_signature_verified = false;
      result.problems.push({ code: "SIGNATURE_ERROR", message: err.message });
    }
  }

  result.ok = result.bundle_version_ok &&
              result.chain_verified &&
              (result.bundle_signature_verified !== false);

  return result;
}

/**
 * Exports bundle as JSON string (formatted for readability).
 */
function exportBundleJson(bundle) {
  return JSON.stringify(bundle, null, 2);
}

module.exports = { createBundle, verifyBundle, exportBundleJson };
