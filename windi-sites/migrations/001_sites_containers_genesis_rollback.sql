-- ═══════════════════════════════════════════════════════════════════════════
-- W-SITES-001 Migration 001 ROLLBACK: Sites + Containers Genesis
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Strategy: CONSERVATIVE (I11 Compliant)
-- Rationale: Genesis tables are renamed, not dropped.
--            Evidence of structure existence preserved for forensic audit.
--
-- ═══════════════════════════════════════════════════════════════════════════

-- Rename tables (preserve I11 - structure evidence)
ALTER TABLE site_containers RENAME TO site_containers_deprecated_20260503;
ALTER TABLE sites RENAME TO sites_deprecated_20260503;

-- Drop indexes (safe - they're metadata, not evidence)
DROP INDEX IF EXISTS idx_containers_site_type;
DROP INDEX IF EXISTS idx_containers_review;
DROP INDEX IF EXISTS idx_sites_company;
DROP INDEX IF EXISTS idx_sites_subdomain;

-- Remove migration record
DELETE FROM _migrations WHERE version = '001';

-- ═══════════════════════════════════════════════════════════════════════════
-- ROLLBACK COMPLETE
-- Deprecated tables preserved at:
--   - sites_deprecated_20260503
--   - site_containers_deprecated_20260503
-- ═══════════════════════════════════════════════════════════════════════════
