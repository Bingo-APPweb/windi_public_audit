// src/index.js
const { MemoryStore } = require("./store/memoryStore");
const { PostgresStore } = require("./store/postgresStore");
const { appendEvent } = require("./engine/append");
const { getTimeline } = require("./engine/timeline");
const { verifyChain } = require("./engine/verifyChain");
const { replay } = require("./engine/replay");
const { createAttestation, verifyAttestation } = require("./engine/attestation");
const { createBundle, verifyBundle, exportBundleJson } = require("./engine/bundle");
const { EventTypes } = require("./schema");

/**
 * Creates a forensics engine instance.
 *
 * @param {Object} opts
 * @param {Object} [opts.store] - Store instance (default: MemoryStore)
 * @param {string} [opts.keyId] - Default key ID for attestations
 * @param {string} [opts.privateKey] - Default private key for signing
 * @param {string} [opts.publicKey] - Default public key for verification
 */
function createForensics({ store, keyId, privateKey, publicKey } = {}) {
  const s = store || new MemoryStore();

  return {
    store: s,
    EventTypes,

    // Core operations
    appendEvent: (args) => appendEvent({ store: s, ...args }),
    getTimeline: (args) => getTimeline({ store: s, ...args }),
    verifyChain: (timeline) => verifyChain(timeline),
    replay: (timeline) => replay(timeline),

    // Attestation (institutional signature)
    createAttestation: (args) => createAttestation({
      store: s,
      key_id: keyId,
      privateKey,
      ...args
    }),
    verifyAttestation: (attestation, pubKey) => verifyAttestation(attestation, pubKey || publicKey),

    // Bundle (portable audit export)
    createBundle: (args) => createBundle({
      privateKey,
      keyId,
      ...args
    }),
    verifyBundle: (bundle, pubKey) => verifyBundle(bundle, pubKey || publicKey),
    exportBundleJson: (bundle) => exportBundleJson(bundle),

    // Convenience: full export with attestation
    async exportAuditBundle(document_id) {
      const timeline = await getTimeline({ store: s, document_id });
      if (timeline.length === 0) {
        throw new Error(`No events found for document_id: ${document_id}`);
      }

      let attestation = null;
      if (privateKey && keyId) {
        attestation = await createAttestation({
          store: s,
          document_id,
          key_id: keyId,
          privateKey
        });

        // Save attestation if store supports it
        if (typeof s.saveAttestation === "function") {
          await s.saveAttestation(attestation);
        }
      }

      return createBundle({
        timeline,
        attestation,
        privateKey,
        keyId
      });
    }
  };
}

module.exports = {
  createForensics,
  MemoryStore,
  PostgresStore,
  EventTypes,
  // Direct exports for advanced usage
  createAttestation,
  verifyAttestation,
  createBundle,
  verifyBundle,
  exportBundleJson,
  verifyChain,
  replay
};
