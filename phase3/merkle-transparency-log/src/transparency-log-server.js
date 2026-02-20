/**
 * ═══════════════════════════════════════════════════════════════════
 * WINDI Phase 3B: Merkle Transparency Log Server
 * ═══════════════════════════════════════════════════════════════════
 * RFC 6962 inspired transparency log with:
 *   - Signed Tree Heads (STH)
 *   - Inclusion proofs
 *   - Consistency proofs
 * Port: 8073
 * ═══════════════════════════════════════════════════════════════════
 */

const express = require('express');
const { Pool } = require('pg');
const nacl = require('tweetnacl');
const naclUtil = require('tweetnacl-util');
const { MerkleTree, SignedTreeHead } = require('./merkle-tree.js');

const app = express();
app.use(express.json());

// ─── Configuration ──────────────────────────────────────────────────
const PORT = process.env.LOG_PORT || 8073;
const DATABASE_URL = process.env.DATABASE_URL || 'postgresql://windi:windi@localhost:5432/windi_hub';
const LOG_SIGNING_KEY = process.env.LOG_SIGNING_KEY;
const LOG_ID = process.env.LOG_ID || 'windi-transparency-log-01';

// ─── Database Pool ──────────────────────────────────────────────────
const pool = new Pool({ connectionString: DATABASE_URL });

// ─── Signing Key ────────────────────────────────────────────────────
let logKeyPair = null;

function initLogKeyPair() {
    if (LOG_SIGNING_KEY) {
        const seed = naclUtil.decodeBase64(LOG_SIGNING_KEY);
        logKeyPair = nacl.sign.keyPair.fromSeed(seed);
    } else {
        logKeyPair = nacl.sign.keyPair();
        console.log('Generated ephemeral log signing key (dev mode)');
    }
    console.log('Log Public Key:', naclUtil.encodeBase64(logKeyPair.publicKey));
}

function sign(data) {
    const message = naclUtil.decodeUTF8(typeof data === 'string' ? data : JSON.stringify(data));
    const signature = nacl.sign.detached(message, logKeyPair.secretKey);
    return naclUtil.encodeBase64(signature);
}

// ─── Merkle Tree State ──────────────────────────────────────────────
let merkleTree = new MerkleTree();
let latestSTH = null;

// ─── Middleware ─────────────────────────────────────────────────────
function asyncHandler(fn) {
    return (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
}

app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type');
    if (req.method === 'OPTIONS') return res.sendStatus(204);
    next();
});

// ─── Routes ─────────────────────────────────────────────────────────

app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        service: 'transparency-log',
        log_id: LOG_ID,
        tree_size: merkleTree.getSize(),
        version: '1.0.0'
    });
});

/**
 * GET /ct/v1/get-sth
 * Get current Signed Tree Head
 */
app.get('/ct/v1/get-sth', (req, res) => {
    if (!latestSTH) {
        return res.status(404).json({
            error: 'No entries in log yet'
        });
    }
    res.json(latestSTH);
});

/**
 * GET /ct/v1/get-sth-consistency
 * Get consistency proof between two tree sizes
 *
 * Query: ?first=10&second=20
 */
app.get('/ct/v1/get-sth-consistency', asyncHandler(async (req, res) => {
    const first = parseInt(req.query.first);
    const second = parseInt(req.query.second) || merkleTree.getSize();

    if (!first || first <= 0) {
        return res.status(400).json({ error: 'Invalid first parameter' });
    }

    if (second > merkleTree.getSize()) {
        return res.status(400).json({
            error: 'Second size exceeds log size',
            log_size: merkleTree.getSize()
        });
    }

    try {
        const proof = merkleTree.getConsistencyProof(first, second);
        res.json({
            log_id: LOG_ID,
            ...proof
        });
    } catch (err) {
        res.status(400).json({ error: err.message });
    }
}));

/**
 * GET /ct/v1/get-proof-by-hash
 * Get inclusion proof for a hash
 *
 * Query: ?hash=abc123&tree_size=100
 */
app.get('/ct/v1/get-proof-by-hash', asyncHandler(async (req, res) => {
    const { hash, tree_size } = req.query;

    if (!hash) {
        return res.status(400).json({ error: 'Missing hash parameter' });
    }

    // Find leaf index
    const result = await pool.query(
        'SELECT leaf_index FROM transparency_log_entries WHERE leaf_hash = $1',
        [hash]
    );

    if (result.rows.length === 0) {
        return res.status(404).json({
            error: 'Hash not found in log',
            hash
        });
    }

    const leafIndex = result.rows[0].leaf_index;

    try {
        const proof = merkleTree.getInclusionProof(leafIndex);
        res.json({
            log_id: LOG_ID,
            ...proof,
            leaf_hash: hash
        });
    } catch (err) {
        res.status(400).json({ error: err.message });
    }
}));

/**
 * GET /ct/v1/get-entries
 * Get log entries
 *
 * Query: ?start=0&end=100
 */
app.get('/ct/v1/get-entries', asyncHandler(async (req, res) => {
    const start = parseInt(req.query.start) || 0;
    const end = Math.min(parseInt(req.query.end) || start + 100, start + 1000);

    const result = await pool.query(`
        SELECT leaf_index, leaf_hash, entry_data, logged_at
        FROM transparency_log_entries
        WHERE leaf_index >= $1 AND leaf_index < $2
        ORDER BY leaf_index ASC
    `, [start, end]);

    res.json({
        log_id: LOG_ID,
        entries: result.rows,
        start,
        end: Math.min(end, merkleTree.getSize())
    });
}));

/**
 * POST /ct/v1/add-entry
 * Add a new entry to the log
 *
 * Body: { hash: "...", data: {...} }
 */
app.post('/ct/v1/add-entry', asyncHandler(async (req, res) => {
    const { hash, data = {} } = req.body;

    if (!hash || !/^[a-f0-9]{64}$/i.test(hash)) {
        return res.status(400).json({
            error: 'Invalid hash format',
            expected: '64 character hex string (SHA256)'
        });
    }

    // Check for duplicate
    const existing = await pool.query(
        'SELECT leaf_index FROM transparency_log_entries WHERE leaf_hash = $1',
        [hash.toLowerCase()]
    );

    if (existing.rows.length > 0) {
        return res.status(409).json({
            error: 'Hash already in log',
            leaf_index: existing.rows[0].leaf_index
        });
    }

    // Add to Merkle tree
    const leafIndex = merkleTree.addLeaf(hash.toLowerCase());

    // Persist to database
    await pool.query(`
        INSERT INTO transparency_log_entries (leaf_index, leaf_hash, entry_data)
        VALUES ($1, $2, $3)
    `, [leafIndex, hash.toLowerCase(), data]);

    // Update STH
    await updateSTH();

    res.status(201).json({
        success: true,
        leaf_index: leafIndex,
        tree_size: merkleTree.getSize(),
        root_hash: merkleTree.getRootHex(),
        sth: latestSTH
    });
}));

/**
 * POST /ct/v1/add-batch
 * Add multiple entries at once
 *
 * Body: { hashes: ["...", "..."], data: {...} }
 */
app.post('/ct/v1/add-batch', asyncHandler(async (req, res) => {
    const { hashes, data = {} } = req.body;

    if (!Array.isArray(hashes) || hashes.length === 0) {
        return res.status(400).json({ error: 'hashes must be a non-empty array' });
    }

    if (hashes.length > 1000) {
        return res.status(400).json({ error: 'Maximum 1000 hashes per batch' });
    }

    // Validate all hashes
    for (const hash of hashes) {
        if (!/^[a-f0-9]{64}$/i.test(hash)) {
            return res.status(400).json({
                error: 'Invalid hash format',
                hash
            });
        }
    }

    const normalizedHashes = hashes.map(h => h.toLowerCase());

    // Check for duplicates
    const existing = await pool.query(
        'SELECT leaf_hash FROM transparency_log_entries WHERE leaf_hash = ANY($1)',
        [normalizedHashes]
    );

    if (existing.rows.length > 0) {
        return res.status(409).json({
            error: 'Some hashes already in log',
            duplicates: existing.rows.map(r => r.leaf_hash)
        });
    }

    // Add all to Merkle tree
    const startIndex = merkleTree.getSize();
    merkleTree.addLeaves(normalizedHashes);

    // Persist to database
    const values = normalizedHashes.map((hash, i) => `($${i * 3 + 1}, $${i * 3 + 2}, $${i * 3 + 3})`);
    const params = normalizedHashes.flatMap((hash, i) => [startIndex + i, hash, data]);

    await pool.query(`
        INSERT INTO transparency_log_entries (leaf_index, leaf_hash, entry_data)
        VALUES ${values.join(', ')}
    `, params);

    // Update STH
    await updateSTH();

    res.status(201).json({
        success: true,
        start_index: startIndex,
        count: normalizedHashes.length,
        tree_size: merkleTree.getSize(),
        root_hash: merkleTree.getRootHex(),
        sth: latestSTH
    });
}));

/**
 * GET /ct/v1/get-roots
 * Get all historical tree roots (for audit)
 */
app.get('/ct/v1/get-roots', asyncHandler(async (req, res) => {
    const limit = Math.min(parseInt(req.query.limit) || 100, 1000);

    const result = await pool.query(`
        SELECT tree_size, root_hash, timestamp, signature
        FROM transparency_log_sths
        ORDER BY tree_size DESC
        LIMIT $1
    `, [limit]);

    res.json({
        log_id: LOG_ID,
        current_size: merkleTree.getSize(),
        roots: result.rows
    });
}));

/**
 * GET /ct/v1/verify
 * Verify a hash and get inclusion proof
 */
app.get('/ct/v1/verify/:hash', asyncHandler(async (req, res) => {
    const { hash } = req.params;

    const result = await pool.query(
        'SELECT leaf_index, entry_data, logged_at FROM transparency_log_entries WHERE leaf_hash = $1',
        [hash.toLowerCase()]
    );

    if (result.rows.length === 0) {
        return res.json({
            found: false,
            hash,
            log_id: LOG_ID
        });
    }

    const entry = result.rows[0];
    const proof = merkleTree.getInclusionProof(entry.leaf_index);

    // Verify the proof ourselves
    const verified = MerkleTree.verifyInclusionProof(hash.toLowerCase(), proof);

    res.json({
        found: true,
        verified,
        hash,
        log_id: LOG_ID,
        leaf_index: entry.leaf_index,
        logged_at: entry.logged_at,
        entry_data: entry.entry_data,
        inclusion_proof: proof,
        current_sth: latestSTH
    });
}));

/**
 * GET /ct/v1/public-key
 * Get log's public key for signature verification
 */
app.get('/ct/v1/public-key', (req, res) => {
    res.json({
        log_id: LOG_ID,
        public_key: naclUtil.encodeBase64(logKeyPair.publicKey),
        algorithm: 'Ed25519'
    });
});

// ─── Helper Functions ───────────────────────────────────────────────

async function updateSTH() {
    const sth = new SignedTreeHead({
        treeSize: merkleTree.getSize(),
        rootHash: merkleTree.getRootHex(),
        timestamp: Date.now(),
        logId: LOG_ID
    });

    const signature = sign(sth.getSignatureInput());
    latestSTH = sth.toJSON(signature);

    // Persist STH
    await pool.query(`
        INSERT INTO transparency_log_sths (tree_size, root_hash, timestamp, signature)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (tree_size) DO UPDATE SET
            root_hash = EXCLUDED.root_hash,
            timestamp = EXCLUDED.timestamp,
            signature = EXCLUDED.signature
    `, [sth.tree_size, sth.root_hash, sth.timestamp, signature]);
}

async function loadTreeFromDB() {
    console.log('Loading transparency log from database...');

    const result = await pool.query(`
        SELECT leaf_hash FROM transparency_log_entries ORDER BY leaf_index ASC
    `);

    if (result.rows.length > 0) {
        const hashes = result.rows.map(r => r.leaf_hash);
        merkleTree.addLeaves(hashes);
        console.log(`Loaded ${result.rows.length} entries, root: ${merkleTree.getRootHex()?.substring(0, 16)}...`);

        // Load latest STH
        const sthResult = await pool.query(`
            SELECT * FROM transparency_log_sths ORDER BY tree_size DESC LIMIT 1
        `);

        if (sthResult.rows.length > 0) {
            const sth = sthResult.rows[0];
            latestSTH = {
                version: 1,
                log_id: LOG_ID,
                tree_size: sth.tree_size,
                root_hash: sth.root_hash,
                timestamp: parseInt(sth.timestamp),
                timestamp_iso: new Date(parseInt(sth.timestamp)).toISOString(),
                signature: sth.signature
            };
        }
    }
}

// ─── Error Handler ──────────────────────────────────────────────────
app.use((err, req, res, next) => {
    console.error('Error:', err);
    res.status(500).json({ error: 'Internal server error' });
});

// ─── Start Server ───────────────────────────────────────────────────
async function start() {
    try {
        await pool.query('SELECT NOW()');
        console.log('Database connected');

        // Ensure tables exist
        await pool.query(`
            CREATE TABLE IF NOT EXISTS transparency_log_entries (
                id SERIAL PRIMARY KEY,
                leaf_index BIGINT UNIQUE NOT NULL,
                leaf_hash VARCHAR(64) UNIQUE NOT NULL,
                entry_data JSONB DEFAULT '{}',
                logged_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS transparency_log_sths (
                id SERIAL PRIMARY KEY,
                tree_size BIGINT UNIQUE NOT NULL,
                root_hash VARCHAR(64) NOT NULL,
                timestamp BIGINT NOT NULL,
                signature TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_log_entries_hash ON transparency_log_entries(leaf_hash);
            CREATE INDEX IF NOT EXISTS idx_log_entries_index ON transparency_log_entries(leaf_index);
        `);

        initLogKeyPair();
        await loadTreeFromDB();

        app.listen(PORT, '0.0.0.0', () => {
            console.log('');
            console.log('═══════════════════════════════════════════════════');
            console.log('  WINDI Merkle Transparency Log v1.0.0');
            console.log(`  Port: ${PORT}`);
            console.log(`  Log ID: ${LOG_ID}`);
            console.log(`  Tree Size: ${merkleTree.getSize()}`);
            console.log('');
            console.log('  Endpoints (RFC 6962 style):');
            console.log('    GET  /ct/v1/get-sth');
            console.log('    GET  /ct/v1/get-sth-consistency');
            console.log('    GET  /ct/v1/get-proof-by-hash');
            console.log('    GET  /ct/v1/get-entries');
            console.log('    POST /ct/v1/add-entry');
            console.log('    POST /ct/v1/add-batch');
            console.log('    GET  /ct/v1/verify/:hash');
            console.log('');
            console.log('  AI processes. Human decides. WINDI guarantees.');
            console.log('═══════════════════════════════════════════════════');
        });
    } catch (err) {
        console.error('Failed to start:', err);
        process.exit(1);
    }
}

start();
