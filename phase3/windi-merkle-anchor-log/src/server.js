/**
 * ═══════════════════════════════════════════════════════════════════
 * WINDI Merkle Anchor Log — Server (CT-style)
 * ═══════════════════════════════════════════════════════════════════
 * Public append-only Merkle Transparency Log for combined_root_hash anchors
 * Port: 4051 (default)
 *
 * Endpoints:
 *   POST /anchors           - Append anchor
 *   GET  /sth               - Get Signed Tree Head
 *   GET  /lookup            - Find by combined_root_hash
 *   GET  /proof/inclusion   - Get inclusion proof
 *   GET  /proof/consistency - Get consistency proof
 *   GET  /hub/public-key    - Get log's public key
 *
 * Principle: AI processes. Human decides. WINDI guarantees.
 * ═══════════════════════════════════════════════════════════════════
 */

const express = require("express");
const { pool } = require("./db");
const { stableStringify } = require("./canonical");
const { leafHash, hex } = require("./hash");
const { merkleRoot } = require("./merkle");
const { inclusionProof, consistencyProof } = require("./proofs");
const { signSTH } = require("./signer");

const app = express();
app.use(express.json({ limit: "2mb" }));

const PORT = Number(process.env.PORT || 4051);

// ─── CORS ─────────────────────────────────────────────────────────
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.sendStatus(204);
  next();
});

// ─── Helpers ──────────────────────────────────────────────────────
async function getLeavesUpTo(treeSize) {
  const { rows } = await pool.query(
    `SELECT leaf_index, leaf_hash, combined_root_hash, node_id, ts
     FROM merkle_leaves
     WHERE leaf_index <= $1
     ORDER BY leaf_index ASC`,
    [treeSize]
  );
  return rows;
}

async function getLeafCount() {
  const { rows } = await pool.query(`SELECT COUNT(*)::bigint AS c FROM merkle_leaves`);
  return Number(rows[0].c);
}

async function getLatestSTH() {
  const { rows } = await pool.query(
    `SELECT tree_size, ts, root_hash, signature_alg, signature, key_id
     FROM merkle_sth
     ORDER BY tree_size DESC
     LIMIT 1`
  );
  return rows[0] || null;
}

async function upsertSTH(treeSize, rootHashHex) {
  const sthPayload = {
    tree_size: treeSize,
    timestamp: new Date().toISOString(),
    root_hash: rootHashHex
  };
  const sig = signSTH(sthPayload);

  const { rows } = await pool.query(
    `INSERT INTO merkle_sth (tree_size, root_hash, signature_alg, signature, key_id)
     VALUES ($1,$2,$3,$4,$5)
     ON CONFLICT (tree_size) DO UPDATE
     SET root_hash=EXCLUDED.root_hash,
         signature_alg=EXCLUDED.signature_alg,
         signature=EXCLUDED.signature,
         key_id=EXCLUDED.key_id,
         ts=now()
     RETURNING tree_size, ts, root_hash, signature_alg, signature, key_id`,
    [treeSize, rootHashHex, sig.signature_alg, sig.signature, sig.key_id]
  );

  return rows[0];
}

// ─── Routes ───────────────────────────────────────────────────────

app.get("/health", (_req, res) => res.json({
  ok: true,
  service: "windi-merkle-anchor-log",
  port: PORT
}));

/**
 * POST /anchors
 * body: { combined_root_hash: "<64hex>", node_id?: "node:..." }
 */
app.post("/anchors", async (req, res) => {
  const { combined_root_hash, node_id } = req.body || {};
  if (!combined_root_hash || !/^[0-9a-f]{64}$/i.test(combined_root_hash)) {
    return res.status(400).json({ error: "invalid_combined_root_hash" });
  }

  // Create leaf payload for hashing (canonical JSON)
  const ts = new Date().toISOString();
  const leafPayload = {
    combined_root_hash: combined_root_hash.toLowerCase(),
    node_id: node_id || null,
    ts
  };
  const leafPayloadJson = stableStringify(leafPayload);
  const lh = leafHash(leafPayloadJson);
  const leaf_hash_hex = hex(lh);

  try {
    const { rows } = await pool.query(
      `INSERT INTO merkle_leaves (ts, node_id, combined_root_hash, leaf_hash)
       VALUES ($1,$2,$3,$4)
       RETURNING leaf_index, ts, node_id, combined_root_hash, leaf_hash`,
      [ts, node_id || null, combined_root_hash.toLowerCase(), leaf_hash_hex]
    );

    const leaf = rows[0];

    // Build STH for current tree_size = count
    const treeSize = await getLeafCount();

    // Load all leaf hashes up to treeSize (MVP)
    const leaves = await getLeavesUpTo(treeSize);
    const leafHashes = leaves.map(r => Buffer.from(r.leaf_hash, "hex"));

    const root = merkleRoot(leafHashes);
    const rootHex = hex(root);

    const sth = await upsertSTH(treeSize, rootHex);

    res.status(201).json({
      leaf_index: Number(leaf.leaf_index) - 1, // 0-based index for proofs
      leaf_hash: leaf.leaf_hash,
      leaf_payload: leafPayload,
      sth
    });
  } catch (e) {
    const msg = String(e?.message || e);
    if (msg.includes("duplicate key") || msg.includes("unique")) {
      return res.status(409).json({ error: "duplicate_leaf" });
    }
    console.error("POST /anchors error:", e);
    res.status(500).json({ error: "internal_error", message: msg });
  }
});

/**
 * GET /sth
 * Get current Signed Tree Head
 */
app.get("/sth", async (_req, res) => {
  const sth = await getLatestSTH();
  if (!sth) return res.status(404).json({ error: "no_sth" });
  res.json(sth);
});

/**
 * GET /lookup?combined_root_hash=...
 * Find leaf by combined_root_hash
 */
app.get("/lookup", async (req, res) => {
  const h = String(req.query.combined_root_hash || "").toLowerCase();
  if (!/^[0-9a-f]{64}$/.test(h)) return res.status(400).json({ error: "invalid_hash" });

  const { rows } = await pool.query(
    `SELECT leaf_index, leaf_hash, ts, node_id
     FROM merkle_leaves
     WHERE combined_root_hash=$1
     ORDER BY leaf_index ASC
     LIMIT 1`,
    [h]
  );

  if (!rows.length) return res.json({ found: false });
  res.json({
    found: true,
    leaf_index: Number(rows[0].leaf_index) - 1, // 0-based
    leaf_hash: rows[0].leaf_hash,
    ts: rows[0].ts,
    node_id: rows[0].node_id
  });
});

/**
 * GET /proof/inclusion?leaf_index=42&tree_size=12345
 * Returns audit_path (hex hashes)
 */
app.get("/proof/inclusion", async (req, res) => {
  const leafIndex = Number(req.query.leaf_index);
  const treeSize = Number(req.query.tree_size);
  if (!Number.isInteger(leafIndex) || leafIndex < 0) {
    return res.status(400).json({ error: "invalid_leaf_index" });
  }
  if (!Number.isInteger(treeSize) || treeSize < 1) {
    return res.status(400).json({ error: "invalid_tree_size" });
  }

  try {
    const leaves = await getLeavesUpTo(treeSize);
    if (leaves.length < treeSize) {
      return res.status(400).json({ error: "tree_size_too_large" });
    }

    const leafHashes = leaves.map(r => Buffer.from(r.leaf_hash, "hex"));
    const path = inclusionProof(leafHashes, leafIndex, treeSize);

    res.json({
      leaf_index: leafIndex,
      tree_size: treeSize,
      audit_path: path.map(b => b.toString("hex"))
    });
  } catch (e) {
    res.status(400).json({ error: e.message });
  }
});

/**
 * GET /proof/consistency?old_size=8000&new_size=12345
 */
app.get("/proof/consistency", async (req, res) => {
  const oldSize = Number(req.query.old_size);
  const newSize = Number(req.query.new_size);
  if (!Number.isInteger(oldSize) || oldSize < 1) {
    return res.status(400).json({ error: "invalid_old_size" });
  }
  if (!Number.isInteger(newSize) || newSize < 1) {
    return res.status(400).json({ error: "invalid_new_size" });
  }
  if (oldSize > newSize) {
    return res.status(400).json({ error: "old_gt_new" });
  }

  try {
    const leaves = await getLeavesUpTo(newSize);
    if (leaves.length < newSize) {
      return res.status(400).json({ error: "new_size_too_large" });
    }

    const leafHashes = leaves.map(r => Buffer.from(r.leaf_hash, "hex"));
    const path = consistencyProof(leafHashes, oldSize, newSize);

    res.json({
      old_size: oldSize,
      new_size: newSize,
      consistency_path: path.map(b => b.toString("hex"))
    });
  } catch (e) {
    res.status(400).json({ error: e.message });
  }
});

/**
 * GET /hub/public-key
 * Expose the log operator public key
 */
app.get("/hub/public-key", (_req, res) => {
  const pub = process.env.LOG_PUBLIC_KEY_PEM || null;
  res.json({
    key_id: process.env.LOG_KEY_ID || "hub-log-2026",
    public_key_pem: pub
  });
});

/**
 * GET /leaves
 * List leaves (pagination)
 */
app.get("/leaves", async (req, res) => {
  const start = parseInt(req.query.start) || 0;
  const limit = Math.min(parseInt(req.query.limit) || 100, 1000);

  const { rows } = await pool.query(`
    SELECT leaf_index, leaf_hash, combined_root_hash, node_id, ts
    FROM merkle_leaves
    WHERE leaf_index > $1
    ORDER BY leaf_index ASC
    LIMIT $2
  `, [start, limit]);

  const count = await getLeafCount();

  res.json({
    tree_size: count,
    start,
    count: rows.length,
    leaves: rows.map(r => ({
      ...r,
      leaf_index: Number(r.leaf_index) - 1 // 0-based
    }))
  });
});

// ─── Error Handler ────────────────────────────────────────────────
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({ error: 'internal_server_error' });
});

// ─── Startup ──────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log('');
  console.log('═══════════════════════════════════════════════════');
  console.log('  WINDI Merkle Anchor Log (CT-style)');
  console.log(`  Port: ${PORT}`);
  console.log(`  Key ID: ${process.env.LOG_KEY_ID || 'hub-log-2026'}`);
  console.log('');
  console.log('  Endpoints:');
  console.log('    POST /anchors');
  console.log('    GET  /sth');
  console.log('    GET  /lookup');
  console.log('    GET  /proof/inclusion');
  console.log('    GET  /proof/consistency');
  console.log('    GET  /leaves');
  console.log('    GET  /hub/public-key');
  console.log('');
  console.log('  AI processes. Human decides. WINDI guarantees.');
  console.log('═══════════════════════════════════════════════════');
});
