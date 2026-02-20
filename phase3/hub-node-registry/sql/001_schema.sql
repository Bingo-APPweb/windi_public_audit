-- ═══════════════════════════════════════════════════════════════════
-- WINDI Phase 3: Hub Node Registry Schema
-- ═══════════════════════════════════════════════════════════════════
-- Purpose: Store node identities, public keys, and attestation history
-- Database: PostgreSQL 14+
-- ═══════════════════════════════════════════════════════════════════

-- Extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── Node Status Enum ───────────────────────────────────────────────
CREATE TYPE node_status AS ENUM ('PENDING', 'ACTIVE', 'SUSPENDED', 'REVOKED');

-- ─── Node Role Enum ─────────────────────────────────────────────────
CREATE TYPE node_role AS ENUM (
    'verifier',
    'anchor_publisher',
    'issuer',
    'auditor',
    'governance_observer'
);

-- ─── Nodes Table ────────────────────────────────────────────────────
CREATE TABLE nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id VARCHAR(255) UNIQUE NOT NULL,  -- Format: node:<org>-<location>-<instance>
    domain VARCHAR(255) NOT NULL,
    public_key TEXT NOT NULL,              -- Base64-encoded Ed25519 public key
    public_key_fingerprint VARCHAR(64) NOT NULL, -- SHA256 of public key
    roles node_role[] NOT NULL DEFAULT '{}',
    status node_status NOT NULL DEFAULT 'PENDING',
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    activated_at TIMESTAMPTZ,
    suspended_at TIMESTAMPTZ,
    last_attestation_at TIMESTAMPTZ,

    -- Hub certificate
    certificate JSONB,                     -- Signed node certificate from Hub
    certificate_issued_at TIMESTAMPTZ,
    certificate_expires_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT valid_node_id CHECK (node_id ~ '^node:[a-z0-9-]+-[a-z0-9-]+-[0-9]+$')
);

-- ─── Attestation History Table ──────────────────────────────────────
CREATE TABLE attestation_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id VARCHAR(255) NOT NULL REFERENCES nodes(node_id) ON DELETE CASCADE,

    -- Attestation payload
    payload JSONB NOT NULL,
    payload_hash VARCHAR(64) NOT NULL,     -- SHA256 of canonical JSON payload
    signature TEXT NOT NULL,               -- Base64-encoded Ed25519 signature

    -- Verification
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    verified_at TIMESTAMPTZ,
    verification_error TEXT,

    -- Replay protection
    attestation_timestamp TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Hub response
    hub_response JSONB,
    certificate_issued BOOLEAN DEFAULT FALSE,

    -- Constraints
    CONSTRAINT unique_payload_hash UNIQUE (node_id, payload_hash)
);

-- ─── Node Events Table ──────────────────────────────────────────────
CREATE TABLE node_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id VARCHAR(255) NOT NULL REFERENCES nodes(node_id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,       -- REGISTERED, ATTESTED, ACTIVATED, SUSPENDED, etc.
    event_data JSONB DEFAULT '{}',
    actor VARCHAR(255),                    -- Who triggered the event
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── Hub Signing Keys Table ─────────────────────────────────────────
-- Stores Hub's own keypairs for signing certificates
CREATE TABLE hub_signing_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_id VARCHAR(64) UNIQUE NOT NULL,    -- Short identifier for the key
    public_key TEXT NOT NULL,              -- Base64-encoded Ed25519 public key
    private_key_encrypted TEXT,            -- Encrypted private key (optional, for managed keys)
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, ROTATED, REVOKED
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    rotated_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ
);

-- ─── Indexes ────────────────────────────────────────────────────────
CREATE INDEX idx_nodes_status ON nodes(status);
CREATE INDEX idx_nodes_domain ON nodes(domain);
CREATE INDEX idx_nodes_roles ON nodes USING GIN(roles);
CREATE INDEX idx_nodes_registered_at ON nodes(registered_at DESC);

CREATE INDEX idx_attestation_node_id ON attestation_history(node_id);
CREATE INDEX idx_attestation_timestamp ON attestation_history(attestation_timestamp DESC);
CREATE INDEX idx_attestation_received ON attestation_history(received_at DESC);

CREATE INDEX idx_events_node_id ON node_events(node_id);
CREATE INDEX idx_events_type ON node_events(event_type);
CREATE INDEX idx_events_created ON node_events(created_at DESC);

-- ─── Functions ──────────────────────────────────────────────────────

-- Function to check attestation freshness (5 minute window)
CREATE OR REPLACE FUNCTION is_attestation_fresh(ts TIMESTAMPTZ)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN ts >= NOW() - INTERVAL '5 minutes' AND ts <= NOW() + INTERVAL '30 seconds';
END;
$$ LANGUAGE plpgsql;

-- Function to log node events
CREATE OR REPLACE FUNCTION log_node_event(
    p_node_id VARCHAR(255),
    p_event_type VARCHAR(50),
    p_event_data JSONB DEFAULT '{}',
    p_actor VARCHAR(255) DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    event_id UUID;
BEGIN
    INSERT INTO node_events (node_id, event_type, event_data, actor)
    VALUES (p_node_id, p_event_type, p_event_data, p_actor)
    RETURNING id INTO event_id;
    RETURN event_id;
END;
$$ LANGUAGE plpgsql;

-- ─── Initial Hub Signing Key ────────────────────────────────────────
-- Note: In production, generate this securely and store private key externally
INSERT INTO hub_signing_keys (key_id, public_key, status)
VALUES (
    'hub-primary-2026',
    'PLACEHOLDER_GENERATE_ON_FIRST_RUN',
    'PENDING'
);

-- ═══════════════════════════════════════════════════════════════════
-- WINDI Phase 3 Schema Complete
-- AI processes. Human decides. WINDI guarantees.
-- ═══════════════════════════════════════════════════════════════════
