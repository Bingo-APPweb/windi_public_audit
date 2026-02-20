-- WINDI Forensics Engine — WCAF Schema v1.0
-- Append-only audit trail with institutional attestation

-- =============================================================================
-- TABLE: wcaf_events (Append-Only Forensic Log)
-- =============================================================================

CREATE TABLE wcaf_events (
    id              BIGSERIAL PRIMARY KEY,
    document_id     TEXT        NOT NULL,
    event_id        UUID        NOT NULL,
    ts              TIMESTAMPTZ NOT NULL DEFAULT now(),

    type            TEXT        NOT NULL, -- VERIFY_RESULT | POLICY_DECISION | PAYMENT_ACTION | NOTE

    payload         JSONB       NOT NULL,

    prev_hash       CHAR(64)    NOT NULL,
    event_hash      CHAR(64)    NOT NULL,

    schema_version  TEXT        NOT NULL DEFAULT 'wcaf-1.0',
    policy_version  TEXT,       -- only for POLICY_DECISION events

    actor_system    TEXT,
    actor_instance  TEXT,

    CONSTRAINT wcaf_events_event_id_unique UNIQUE (event_id)
);

-- Prevent UPDATE and DELETE (append-only guarantee)
CREATE RULE wcaf_no_update AS ON UPDATE TO wcaf_events DO INSTEAD NOTHING;
CREATE RULE wcaf_no_delete AS ON DELETE TO wcaf_events DO INSTEAD NOTHING;

-- Performance indexes
CREATE INDEX wcaf_events_document_idx ON wcaf_events(document_id);
CREATE INDEX wcaf_events_ts_idx       ON wcaf_events(ts);
CREATE INDEX wcaf_events_hash_idx     ON wcaf_events(event_hash);
CREATE INDEX wcaf_events_type_idx     ON wcaf_events(type);

-- =============================================================================
-- TABLE: wcaf_attestations (Institutional Signatures)
-- =============================================================================

CREATE TABLE wcaf_attestations (
    id              BIGSERIAL PRIMARY KEY,
    document_id     TEXT        NOT NULL,
    head_event_hash CHAR(64)    NOT NULL,
    attested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),

    signature_alg   TEXT        NOT NULL, -- RSA-PSS-SHA256, Ed25519, etc.
    signature       TEXT        NOT NULL, -- base64 encoded

    key_id          TEXT        NOT NULL, -- institutional key identifier

    schema_version  TEXT        NOT NULL DEFAULT 'wcaf-attestation-1.0'
);

CREATE INDEX wcaf_attestations_document_idx ON wcaf_attestations(document_id);
CREATE INDEX wcaf_attestations_hash_idx     ON wcaf_attestations(head_event_hash);

-- =============================================================================
-- VIEW: wcaf_chain_heads (Latest event per document)
-- =============================================================================

CREATE VIEW wcaf_chain_heads AS
SELECT DISTINCT ON (document_id)
    document_id,
    event_hash AS head_event_hash,
    ts AS head_ts,
    id AS head_id
FROM wcaf_events
ORDER BY document_id, id DESC;

-- =============================================================================
-- FUNCTION: wcaf_verify_chain (Server-side chain verification)
-- =============================================================================

CREATE OR REPLACE FUNCTION wcaf_verify_chain(p_document_id TEXT)
RETURNS TABLE (
    is_valid BOOLEAN,
    event_count BIGINT,
    first_event_id UUID,
    last_event_hash CHAR(64)
) AS $$
DECLARE
    v_prev_hash CHAR(64) := 'GENESIS';
    v_count BIGINT := 0;
    v_first_id UUID;
    v_last_hash CHAR(64);
    v_valid BOOLEAN := TRUE;
    r RECORD;
BEGIN
    FOR r IN
        SELECT event_id, prev_hash, event_hash
        FROM wcaf_events
        WHERE document_id = p_document_id
        ORDER BY id ASC
    LOOP
        v_count := v_count + 1;

        IF v_count = 1 THEN
            v_first_id := r.event_id;
        END IF;

        -- Check chain continuity
        IF r.prev_hash != v_prev_hash AND NOT (v_count = 1 AND r.prev_hash = 'GENESIS') THEN
            v_valid := FALSE;
        END IF;

        v_prev_hash := r.event_hash;
        v_last_hash := r.event_hash;
    END LOOP;

    RETURN QUERY SELECT v_valid, v_count, v_first_id, v_last_hash;
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE wcaf_events IS 'WINDI Chain Audit Format - Append-only event log';
COMMENT ON TABLE wcaf_attestations IS 'Institutional signatures over chain heads';
