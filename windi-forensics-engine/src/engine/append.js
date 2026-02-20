// src/engine/append.js
const crypto = require("crypto");
const { computeEventHash } = require("../hash");

function nowIso() {
  return new Date().toISOString();
}

function newId() {
  return crypto.randomUUID ? crypto.randomUUID() : crypto.randomBytes(16).toString("hex");
}

const SCHEMA_VERSION = "wcaf-1.0";

/**
 * appendEvent
 * - cria evento canonicalizado
 * - linka com prev_hash
 * - calcula event_hash
 * - grava no store
 *
 * @param {Object} opts
 * @param {Object} opts.store - Store instance
 * @param {string} opts.document_id - Document identifier
 * @param {string} opts.type - Event type (VERIFY_RESULT, POLICY_DECISION, etc.)
 * @param {Object} opts.payload - Event payload
 * @param {Object} [opts.actor] - Actor information
 * @param {string} [opts.schema_version] - Override schema version
 */
async function appendEvent({ store, document_id, type, payload, actor, schema_version }) {
  const prev_hash = await store.getLastHash(document_id);

  const core = {
    event_id: newId(),
    ts: nowIso(),
    document_id,
    type,
    actor: actor || { system: "unknown" },
    payload: payload || {},
    prev_hash: prev_hash || "GENESIS",
    schema_version: schema_version || SCHEMA_VERSION
  };

  const event_hash = computeEventHash(core);

  const full = { ...core, event_hash };
  await store.append(full);
  return full;
}

module.exports = { appendEvent };
