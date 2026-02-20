-- ═══════════════════════════════════════════════════════════════════
-- WINDI Merkle Anchor Log — Schema (CT-style)
-- ═══════════════════════════════════════════════════════════════════
-- Phase 3B: Merkle Transparency Log
-- Principle: AI processes. Human decides. WINDI guarantees.
-- ═══════════════════════════════════════════════════════════════════

-- ─── Leaves (each anchor = one leaf) ────────────────────────────────
CREATE TABLE IF NOT EXISTS merkle_leaves (
  leaf_index BIGSERIAL PRIMARY KEY,
  ts TIMESTAMPTZ NOT NULL DEFAULT now(),
  node_id TEXT,
  combined_root_hash CHAR(64) NOT NULL,
  leaf_hash CHAR(64) NOT NULL UNIQUE
);

CREATE INDEX IF NOT EXISTS merkle_leaves_combined_idx ON merkle_leaves(combined_root_hash);
CREATE INDEX IF NOT EXISTS merkle_leaves_ts_idx ON merkle_leaves(ts);

-- ─── Signed Tree Heads (STH) ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS merkle_sth (
  id BIGSERIAL PRIMARY KEY,
  tree_size BIGINT NOT NULL,
  ts TIMESTAMPTZ NOT NULL DEFAULT now(),
  root_hash CHAR(64) NOT NULL,
  signature_alg TEXT NOT NULL,
  signature TEXT NOT NULL,
  key_id TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS merkle_sth_tree_size_idx ON merkle_sth(tree_size);

-- ═══════════════════════════════════════════════════════════════════
-- Schema Complete
-- ═══════════════════════════════════════════════════════════════════
