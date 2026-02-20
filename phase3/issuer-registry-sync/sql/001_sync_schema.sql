-- ═══════════════════════════════════════════════════════════════════
-- WINDI Phase 3: Issuer Registry Sync Schema
-- ═══════════════════════════════════════════════════════════════════
-- Purpose: Track issuer registry changes for delta-based sync
-- Enables: Hub → Node synchronization of TRUSTED/REVOKED issuers
-- ═══════════════════════════════════════════════════════════════════

-- Extension for UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── Issuer Trust Status Enum ───────────────────────────────────────
CREATE TYPE issuer_trust_status AS ENUM (
    'UNKNOWN',      -- Not yet evaluated
    'PENDING',      -- Under review
    'TRUSTED',      -- Approved by governance
    'REVOKED',      -- Trust revoked
    'SUSPENDED'     -- Temporarily suspended
);

-- ─── Issuers Table (Master Registry) ────────────────────────────────
CREATE TABLE issuers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    issuer_id VARCHAR(255) UNIQUE NOT NULL,       -- e.g., "did:windi:bafin"
    display_name VARCHAR(255) NOT NULL,
    jurisdiction VARCHAR(10) NOT NULL,            -- ISO 3166-1 alpha-2

    -- Trust status
    trust_status issuer_trust_status NOT NULL DEFAULT 'UNKNOWN',
    trust_reason TEXT,                            -- Why trusted/revoked
    trust_evidence JSONB DEFAULT '{}',            -- Supporting documents/links

    -- Cryptographic identity
    public_keys JSONB NOT NULL DEFAULT '[]',      -- Array of {key_id, algorithm, public_key, valid_from, valid_until}
    active_key_id VARCHAR(64),                    -- Currently active key

    -- Governance
    governance_level VARCHAR(20) DEFAULT 'LOW',   -- HIGH/MEDIUM/LOW
    approved_by VARCHAR(255),                     -- Node/user that approved
    approval_quorum INT DEFAULT 1,                -- Required approvals

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    trusted_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,

    -- Sync tracking
    version BIGINT NOT NULL DEFAULT 1,            -- Increments on every change
    sync_cursor BIGINT GENERATED ALWAYS AS IDENTITY
);

-- ─── Issuer Changelog (Delta Feed) ──────────────────────────────────
-- Every change to an issuer creates a changelog entry for sync
CREATE TABLE issuer_changelog (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cursor_id BIGSERIAL UNIQUE,                   -- Monotonic cursor for sync

    -- Change details
    issuer_id VARCHAR(255) NOT NULL,
    change_type VARCHAR(20) NOT NULL,             -- CREATED, UPDATED, TRUST_CHANGED, KEY_ROTATED, DELETED
    old_value JSONB,                              -- Previous state (for UPDATED)
    new_value JSONB NOT NULL,                     -- Current state

    -- Change metadata
    changed_by VARCHAR(255),                      -- Node ID or user
    change_reason TEXT,

    -- Timestamp
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- For filtering
    trust_status issuer_trust_status,
    affects_trust BOOLEAN DEFAULT FALSE           -- True if trust_status changed
);

-- ─── Sync Cursors (Track node sync state) ───────────────────────────
CREATE TABLE sync_cursors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id VARCHAR(255) UNIQUE NOT NULL,

    -- Last synced position
    last_cursor BIGINT NOT NULL DEFAULT 0,
    last_sync_at TIMESTAMPTZ,

    -- Sync stats
    total_syncs INT DEFAULT 0,
    total_changes_received INT DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── Issuer Key History ─────────────────────────────────────────────
CREATE TABLE issuer_key_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    issuer_id VARCHAR(255) NOT NULL REFERENCES issuers(issuer_id) ON DELETE CASCADE,
    key_id VARCHAR(64) NOT NULL,
    algorithm VARCHAR(20) NOT NULL,               -- Ed25519, RSA-2048, etc.
    public_key TEXT NOT NULL,

    -- Validity
    valid_from TIMESTAMPTZ NOT NULL,
    valid_until TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    revocation_reason TEXT,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(issuer_id, key_id)
);

-- ─── Indexes ────────────────────────────────────────────────────────
CREATE INDEX idx_issuers_trust_status ON issuers(trust_status);
CREATE INDEX idx_issuers_jurisdiction ON issuers(jurisdiction);
CREATE INDEX idx_issuers_updated ON issuers(updated_at DESC);
CREATE INDEX idx_issuers_version ON issuers(version);

CREATE INDEX idx_changelog_cursor ON issuer_changelog(cursor_id);
CREATE INDEX idx_changelog_issuer ON issuer_changelog(issuer_id);
CREATE INDEX idx_changelog_changed_at ON issuer_changelog(changed_at DESC);
CREATE INDEX idx_changelog_trust ON issuer_changelog(affects_trust) WHERE affects_trust = TRUE;

CREATE INDEX idx_sync_cursors_node ON sync_cursors(node_id);

-- ─── Trigger: Auto-update timestamp ─────────────────────────────────
CREATE OR REPLACE FUNCTION update_issuer_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    NEW.version = OLD.version + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_issuer_timestamp
    BEFORE UPDATE ON issuers
    FOR EACH ROW
    EXECUTE FUNCTION update_issuer_timestamp();

-- ─── Trigger: Create changelog entry on issuer change ───────────────
CREATE OR REPLACE FUNCTION create_issuer_changelog()
RETURNS TRIGGER AS $$
DECLARE
    change_type VARCHAR(20);
    affects_trust BOOLEAN := FALSE;
BEGIN
    IF TG_OP = 'INSERT' THEN
        change_type := 'CREATED';
        INSERT INTO issuer_changelog (issuer_id, change_type, new_value, trust_status, affects_trust)
        VALUES (NEW.issuer_id, change_type, to_jsonb(NEW), NEW.trust_status, TRUE);

    ELSIF TG_OP = 'UPDATE' THEN
        -- Determine change type
        IF OLD.trust_status != NEW.trust_status THEN
            change_type := 'TRUST_CHANGED';
            affects_trust := TRUE;
        ELSIF OLD.active_key_id != NEW.active_key_id THEN
            change_type := 'KEY_ROTATED';
        ELSE
            change_type := 'UPDATED';
        END IF;

        INSERT INTO issuer_changelog (issuer_id, change_type, old_value, new_value, trust_status, affects_trust)
        VALUES (NEW.issuer_id, change_type, to_jsonb(OLD), to_jsonb(NEW), NEW.trust_status, affects_trust);

    ELSIF TG_OP = 'DELETE' THEN
        change_type := 'DELETED';
        INSERT INTO issuer_changelog (issuer_id, change_type, old_value, new_value, trust_status, affects_trust)
        VALUES (OLD.issuer_id, change_type, to_jsonb(OLD), '{}', OLD.trust_status, TRUE);
    END IF;

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_issuer_changelog
    AFTER INSERT OR UPDATE OR DELETE ON issuers
    FOR EACH ROW
    EXECUTE FUNCTION create_issuer_changelog();

-- ─── Function: Get changes since cursor ─────────────────────────────
CREATE OR REPLACE FUNCTION get_issuer_changes(
    p_since_cursor BIGINT,
    p_limit INT DEFAULT 100,
    p_trust_only BOOLEAN DEFAULT FALSE
)
RETURNS TABLE (
    cursor_id BIGINT,
    issuer_id VARCHAR(255),
    change_type VARCHAR(20),
    new_value JSONB,
    trust_status issuer_trust_status,
    changed_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.cursor_id,
        c.issuer_id,
        c.change_type,
        c.new_value,
        c.trust_status,
        c.changed_at
    FROM issuer_changelog c
    WHERE c.cursor_id > p_since_cursor
      AND (NOT p_trust_only OR c.affects_trust = TRUE)
    ORDER BY c.cursor_id ASC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ─── Seed: Example issuers ──────────────────────────────────────────
INSERT INTO issuers (issuer_id, display_name, jurisdiction, trust_status, governance_level, public_keys, active_key_id, trust_reason)
VALUES
    ('did:windi:bafin', 'BaFin - Bundesanstalt für Finanzdienstleistungsaufsicht', 'DE', 'TRUSTED', 'HIGH',
     '[{"key_id": "bafin-key-2026", "algorithm": "Ed25519", "public_key": "placeholder", "valid_from": "2026-01-01"}]',
     'bafin-key-2026', 'German Federal Financial Supervisory Authority'),

    ('did:windi:ecb', 'European Central Bank', 'EU', 'TRUSTED', 'HIGH',
     '[{"key_id": "ecb-key-2026", "algorithm": "Ed25519", "public_key": "placeholder", "valid_from": "2026-01-01"}]',
     'ecb-key-2026', 'Central bank for the Eurozone'),

    ('did:windi:bundesregierung', 'Bundesregierung Deutschland', 'DE', 'TRUSTED', 'MEDIUM',
     '[{"key_id": "bundes-key-2026", "algorithm": "Ed25519", "public_key": "placeholder", "valid_from": "2026-01-01"}]',
     'bundes-key-2026', 'German Federal Government');

-- ═══════════════════════════════════════════════════════════════════
-- WINDI Phase 3 Issuer Sync Schema Complete
-- AI processes. Human decides. WINDI guarantees.
-- ═══════════════════════════════════════════════════════════════════
