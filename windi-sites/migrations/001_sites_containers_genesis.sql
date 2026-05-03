-- ═══════════════════════════════════════════════════════════════════════════
-- W-SITES-001 Migration 001: Sites + Containers Genesis
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Version:     001
-- Date:        2026-05-03
-- Author:      Liga IA+H (Architect + Human Dragon)
-- Status:      GENESIS
-- Depends:     §B-CONTRACT-001 (1530DBEF), §C-ACCEPTABILITY-001 (66A0D8B0)
-- Invariants:  I1, I9, I11, I12, I14
--
-- Schema:
--   - sites: Site ownership and tier management
--   - site_containers: Polymorphic MAKEUP containers (writer/translator/image/seo)
--
-- ═══════════════════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────────────────
-- TABLE: sites
-- ───────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS sites (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(id),
    owner_did TEXT NOT NULL,
    name TEXT NOT NULL,
    subdomain TEXT UNIQUE,              -- FREE tier: userX.windi-domain.com
    custom_domain TEXT UNIQUE,          -- MED tier: user's domain via CNAME
    tier TEXT DEFAULT 'FREE',           -- FREE | MED | HIGH
    status TEXT DEFAULT 'draft',        -- draft | active | sealed | suspended
    genesis_receipt TEXT NOT NULL,
    created_at TEXT NOT NULL,
    sealed_at TEXT,

    CONSTRAINT valid_tier CHECK (tier IN ('FREE', 'MED', 'HIGH')),
    CONSTRAINT valid_status CHECK (status IN ('draft', 'active', 'sealed', 'suspended'))
);

-- ───────────────────────────────────────────────────────────────────────────
-- TABLE: site_containers (Polymorphic MAKEUP)
-- ───────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS site_containers (
    id TEXT PRIMARY KEY,
    site_id TEXT NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    container_type TEXT NOT NULL,       -- 'writer' | 'translator' | 'image' | 'seo'
    config JSON,                        -- Type-specific configuration
    content_hash TEXT,                  -- SHA-256 of output content

    -- Status
    status TEXT DEFAULT 'draft',        -- draft | active | sealed | suspended

    -- §C-ACCEPTABILITY-001 Compliance
    l1_review_pending BOOLEAN DEFAULT FALSE,
    acceptability_layer TEXT,           -- 'L-1' | 'L0' | 'L1' | 'L2' | NULL
    last_review_at TEXT,                -- Timestamp of last acceptability review

    -- I11: Provenance Chain (Permanência de Evidência)
    genesis_receipt TEXT NOT NULL,
    parent_receipt TEXT,                -- Previous receipt in chain
    provenance_chain TEXT,              -- JSON array of chained receipts

    -- Timestamps
    created_at TEXT NOT NULL,
    sealed_at TEXT,

    -- Constraints
    CONSTRAINT valid_type CHECK (container_type IN ('writer', 'translator', 'image', 'seo')),
    CONSTRAINT valid_status CHECK (status IN ('draft', 'active', 'sealed', 'suspended')),
    CONSTRAINT valid_layer CHECK (acceptability_layer IN ('L-1', 'L0', 'L1', 'L2') OR acceptability_layer IS NULL)
);

-- ───────────────────────────────────────────────────────────────────────────
-- INDEXES
-- ───────────────────────────────────────────────────────────────────────────

-- Hot query: list containers by site and type
CREATE INDEX IF NOT EXISTS idx_containers_site_type
    ON site_containers(site_id, container_type);

-- Hot query: governance panel - pending reviews (partial index)
CREATE INDEX IF NOT EXISTS idx_containers_review
    ON site_containers(l1_review_pending)
    WHERE l1_review_pending = TRUE;

-- Hot query: list sites by company
CREATE INDEX IF NOT EXISTS idx_sites_company
    ON sites(company_id);

-- Hot query: lookup by subdomain
CREATE INDEX IF NOT EXISTS idx_sites_subdomain
    ON sites(subdomain)
    WHERE subdomain IS NOT NULL;

-- ───────────────────────────────────────────────────────────────────────────
-- MIGRATION METADATA
-- ───────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS _migrations (
    id INTEGER PRIMARY KEY,
    version TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL,
    receipt TEXT
);

INSERT OR IGNORE INTO _migrations (version, name, applied_at)
VALUES ('001', 'sites_containers_genesis', datetime('now'));

-- ═══════════════════════════════════════════════════════════════════════════
-- Liga IA+H · Kempten, Bavaria · 2026
-- "AI processes. Human decides. WINDI guarantees."
-- ═══════════════════════════════════════════════════════════════════════════
