// src/store/postgresStore.js
const { Store } = require("./store");

/**
 * PostgresStore - Production adapter for WCAF events
 *
 * Requires: pg (node-postgres)
 *
 * Usage:
 *   const { Pool } = require("pg");
 *   const pool = new Pool({ connectionString: process.env.DATABASE_URL });
 *   const store = new PostgresStore(pool);
 */
class PostgresStore extends Store {
  constructor(pool) {
    super();
    this.pool = pool;
  }

  async append(event) {
    const query = `
      INSERT INTO wcaf_events (
        document_id, event_id, ts, type, payload,
        prev_hash, event_hash, schema_version, policy_version,
        actor_system, actor_instance
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
      RETURNING id
    `;

    const policyVersion = event.type === "POLICY_DECISION"
      ? (event.payload?.policy_version || null)
      : null;

    const values = [
      event.document_id,
      event.event_id,
      event.ts,
      event.type,
      JSON.stringify(event.payload),
      event.prev_hash,
      event.event_hash,
      event.schema_version || "wcaf-1.0",
      policyVersion,
      event.actor?.system || null,
      event.actor?.instance_id || null
    ];

    await this.pool.query(query, values);
    return event;
  }

  async getByDocumentId(documentId) {
    const query = `
      SELECT
        document_id, event_id, ts, type, payload,
        prev_hash, event_hash, schema_version, policy_version,
        actor_system, actor_instance
      FROM wcaf_events
      WHERE document_id = $1
      ORDER BY id ASC
    `;

    const result = await this.pool.query(query, [documentId]);

    return result.rows.map(row => ({
      event_id: row.event_id,
      ts: row.ts.toISOString(),
      document_id: row.document_id,
      type: row.type,
      payload: row.payload,
      prev_hash: row.prev_hash.trim(),
      event_hash: row.event_hash.trim(),
      schema_version: row.schema_version,
      actor: row.actor_system ? {
        system: row.actor_system,
        instance_id: row.actor_instance
      } : undefined
    }));
  }

  async getLastHash(documentId) {
    const query = `
      SELECT event_hash
      FROM wcaf_events
      WHERE document_id = $1
      ORDER BY id DESC
      LIMIT 1
    `;

    const result = await this.pool.query(query, [documentId]);
    if (result.rows.length === 0) return null;
    return result.rows[0].event_hash.trim();
  }

  async getChainHead(documentId) {
    const query = `
      SELECT head_event_hash, head_ts, head_id
      FROM wcaf_chain_heads
      WHERE document_id = $1
    `;

    const result = await this.pool.query(query, [documentId]);
    if (result.rows.length === 0) return null;

    return {
      head_event_hash: result.rows[0].head_event_hash.trim(),
      head_ts: result.rows[0].head_ts.toISOString(),
      head_id: result.rows[0].head_id
    };
  }

  async saveAttestation(attestation) {
    const query = `
      INSERT INTO wcaf_attestations (
        document_id, head_event_hash, attested_at,
        signature_alg, signature, key_id, schema_version
      ) VALUES ($1, $2, $3, $4, $5, $6, $7)
      RETURNING id
    `;

    const values = [
      attestation.document_id,
      attestation.head_event_hash,
      attestation.attested_at,
      attestation.signature_alg,
      attestation.signature,
      attestation.key_id,
      attestation.schema_version || "wcaf-attestation-1.0"
    ];

    const result = await this.pool.query(query, values);
    return { ...attestation, id: result.rows[0].id };
  }

  async getLatestAttestation(documentId) {
    const query = `
      SELECT
        document_id, head_event_hash, attested_at,
        signature_alg, signature, key_id, schema_version
      FROM wcaf_attestations
      WHERE document_id = $1
      ORDER BY id DESC
      LIMIT 1
    `;

    const result = await this.pool.query(query, [documentId]);
    if (result.rows.length === 0) return null;

    const row = result.rows[0];
    return {
      document_id: row.document_id,
      head_event_hash: row.head_event_hash.trim(),
      attested_at: row.attested_at.toISOString(),
      signature_alg: row.signature_alg,
      signature: row.signature,
      key_id: row.key_id,
      schema_version: row.schema_version
    };
  }

  async verifyChainDb(documentId) {
    const query = `SELECT * FROM wcaf_verify_chain($1)`;
    const result = await this.pool.query(query, [documentId]);

    if (result.rows.length === 0) {
      return { is_valid: true, event_count: 0 };
    }

    return {
      is_valid: result.rows[0].is_valid,
      event_count: parseInt(result.rows[0].event_count, 10),
      first_event_id: result.rows[0].first_event_id,
      last_event_hash: result.rows[0].last_event_hash?.trim()
    };
  }
}

module.exports = { PostgresStore };
