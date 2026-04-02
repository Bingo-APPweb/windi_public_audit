-- ==============================================================================
-- W-SESSION-001 — Sovereign Session Tables
-- ==============================================================================
-- WINDI Publishing House · Kempten, Bavaria
-- Migration: 001_sovereign_sessions.sql
-- Date: 02 Apr 2026
--
-- Creates tables for sovereign session management.
-- Run with: sqlite3 windi_travel_identity.db < 001_sovereign_sessions.sql
-- ==============================================================================

-- ==============================================================================
-- TABLE: sovereign_sessions
-- ==============================================================================
-- Stores active and revoked sessions.
-- Each session is bound to a DID + device_id pair.
-- Token validation requires both stateless check AND DB lookup for revocation.
-- ==============================================================================

CREATE TABLE IF NOT EXISTS sovereign_sessions (
    -- Identificadores
    session_id      TEXT PRIMARY KEY,              -- UUID unico da sessao
    wallet_id       TEXT NOT NULL,                  -- did:windi:travel:xxx (FK admins.did)

    -- Device binding (APENAS hash, nunca seed)
    device_id       TEXT NOT NULL,                  -- SHA-256 do device fingerprint
    device_name     TEXT,                           -- "Chrome on Windows" (informativo)

    -- Timestamps
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    last_used_at    TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at      TEXT NOT NULL,                  -- Data de expiracao absoluta

    -- Seguranca (sinais secundarios, NAO para autenticacao)
    ip_hash         TEXT,                           -- SHA-256 truncado do IP (sinal)
    user_agent      TEXT,                           -- Para debug/audit (truncado)

    -- Estado de revogacao
    revoked         INTEGER DEFAULT 0,              -- 0=active, 1=revoked
    revoked_at      TEXT,                           -- Quando foi revogada
    revoked_reason  TEXT,                           -- user_request | security | admin | expired

    -- Foreign key
    FOREIGN KEY(wallet_id) REFERENCES admins(did)
);

-- Indices para queries comuns
CREATE INDEX IF NOT EXISTS idx_sovereign_sessions_wallet
    ON sovereign_sessions(wallet_id, revoked);

CREATE INDEX IF NOT EXISTS idx_sovereign_sessions_device
    ON sovereign_sessions(device_id);

CREATE INDEX IF NOT EXISTS idx_sovereign_sessions_expires
    ON sovereign_sessions(expires_at);

CREATE INDEX IF NOT EXISTS idx_sovereign_sessions_active
    ON sovereign_sessions(wallet_id)
    WHERE revoked = 0;


-- ==============================================================================
-- TABLE: device_bindings
-- ==============================================================================
-- Tracks known devices per DID.
-- Used for trust scoring and device management UI.
-- device_id is a hash - device_seed NEVER stored server-side.
-- ==============================================================================

CREATE TABLE IF NOT EXISTS device_bindings (
    -- Identificadores
    binding_id      TEXT PRIMARY KEY,              -- UUID
    wallet_id       TEXT NOT NULL,                  -- did:windi:travel:xxx
    device_id       TEXT NOT NULL,                  -- SHA-256 fingerprint (APENAS hash)

    -- Info (para UI)
    device_name     TEXT,                           -- "iPhone 14", "Chrome on Windows"

    -- Timestamps
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    last_seen_at    TEXT NOT NULL DEFAULT (datetime('now')),

    -- Trust signals (NAO usados para autenticacao, apenas para UI/monitoring)
    consecutive_logins  INTEGER DEFAULT 1,          -- Contador de logins
    trust_level         TEXT DEFAULT 'NEW',         -- NEW | KNOWN | TRUSTED

    -- Estado
    state           TEXT DEFAULT 'ACTIVE',          -- ACTIVE | BLOCKED
    blocked_at      TEXT,
    blocked_reason  TEXT,

    -- Constraints
    UNIQUE(wallet_id, device_id),
    FOREIGN KEY(wallet_id) REFERENCES admins(did)
);

-- Indices
CREATE INDEX IF NOT EXISTS idx_device_bindings_wallet
    ON device_bindings(wallet_id, state);

CREATE INDEX IF NOT EXISTS idx_device_bindings_device
    ON device_bindings(device_id);

CREATE INDEX IF NOT EXISTS idx_device_bindings_active
    ON device_bindings(wallet_id)
    WHERE state = 'ACTIVE';


-- ==============================================================================
-- VIEW: active_sessions
-- ==============================================================================
-- Convenience view for active (non-revoked, non-expired) sessions.
-- ==============================================================================

CREATE VIEW IF NOT EXISTS active_sessions AS
SELECT
    s.session_id,
    s.wallet_id,
    s.device_id,
    s.device_name,
    s.created_at,
    s.last_used_at,
    s.expires_at,
    u.full_name,
    u.email,
    u.state as user_state
FROM sovereign_sessions s
JOIN admins u ON u.did = s.wallet_id
WHERE s.revoked = 0
  AND s.expires_at > datetime('now');


-- ==============================================================================
-- TRIGGER: auto_update_device_trust
-- ==============================================================================
-- Updates trust_level based on consecutive_logins.
-- ==============================================================================

CREATE TRIGGER IF NOT EXISTS trg_update_device_trust
AFTER UPDATE OF consecutive_logins ON device_bindings
FOR EACH ROW
BEGIN
    UPDATE device_bindings
    SET trust_level = CASE
        WHEN NEW.consecutive_logins >= 10 THEN 'TRUSTED'
        WHEN NEW.consecutive_logins >= 3 THEN 'KNOWN'
        ELSE 'NEW'
    END
    WHERE binding_id = NEW.binding_id;
END;


-- ==============================================================================
-- NOTES
-- ==============================================================================
--
-- SECURITY:
-- - device_seed NEVER stored (only device_id hash)
-- - ip_hash is signal only, not for auth
-- - trust_level is informational, not security control
-- - fail-closed: if DB unavailable, deny access
--
-- CLEANUP:
-- - Run periodic cleanup of expired sessions
-- - Example: DELETE FROM sovereign_sessions
--            WHERE expires_at < datetime('now', '-7 days');
--
-- MIGRATION:
-- - This is additive, does not modify existing tables
-- - Legacy travel_sessions table continues to work
-- - Middleware checks sovereign_sessions first, falls back to legacy
--
-- ==============================================================================
