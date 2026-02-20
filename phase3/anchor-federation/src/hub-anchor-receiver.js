/**
 * ═══════════════════════════════════════════════════════════════════
 * WINDI Phase 3: Hub Anchor Receiver
 * ═══════════════════════════════════════════════════════════════════
 * Purpose: Receive and aggregate transparency anchors from nodes
 * Port: 8072
 * Principle: AI processes. Human decides. WINDI guarantees.
 * ═══════════════════════════════════════════════════════════════════
 */

const express = require('express');
const { Pool } = require('pg');
const nacl = require('tweetnacl');
const naclUtil = require('tweetnacl-util');
const crypto = require('crypto');

const app = express();
app.use(express.json({ limit: '1mb' }));

// ─── Configuration ──────────────────────────────────────────────────
const PORT = process.env.ANCHOR_PORT || 8072;
const DATABASE_URL = process.env.DATABASE_URL || 'postgresql://windi:windi@localhost:5432/windi_hub';
const HUB_SIGNING_KEY = process.env.HUB_SIGNING_KEY;

// ─── Database Pool ──────────────────────────────────────────────────
const pool = new Pool({ connectionString: DATABASE_URL });

// ─── Hub Keypair ────────────────────────────────────────────────────
let hubKeyPair = null;

function initHubKeyPair() {
    if (HUB_SIGNING_KEY) {
        const seed = naclUtil.decodeBase64(HUB_SIGNING_KEY);
        hubKeyPair = nacl.sign.keyPair.fromSeed(seed);
    } else {
        hubKeyPair = nacl.sign.keyPair();
        console.log('Generated ephemeral Hub key (dev mode)');
    }
}

// ─── Utility Functions ──────────────────────────────────────────────

function asyncHandler(fn) {
    return (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
}

function sha256(data) {
    return crypto.createHash('sha256').update(data).digest('hex');
}

function canonicalJSON(obj) {
    return JSON.stringify(obj, Object.keys(obj).sort());
}

function verifySignature(payload, signatureBase64, publicKeyBase64) {
    try {
        const message = naclUtil.decodeUTF8(canonicalJSON(payload));
        const signature = naclUtil.decodeBase64(signatureBase64);
        const publicKey = naclUtil.decodeBase64(publicKeyBase64);
        return nacl.sign.detached.verify(message, signature, publicKey);
    } catch (err) {
        return false;
    }
}

function hubSign(data) {
    const message = naclUtil.decodeUTF8(typeof data === 'string' ? data : canonicalJSON(data));
    const signature = nacl.sign.detached(message, hubKeyPair.secretKey);
    return naclUtil.encodeBase64(signature);
}

// ─── Middleware ─────────────────────────────────────────────────────

app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, X-Node-Id, X-Node-Signature, X-Request-Timestamp');
    if (req.method === 'OPTIONS') return res.sendStatus(204);
    next();
});

/**
 * Authenticate node and verify anchor_publisher role
 */
async function authenticateAnchorPublisher(req, res, next) {
    const nodeId = req.headers['x-node-id'];
    const signature = req.headers['x-node-signature'];
    const timestamp = req.headers['x-request-timestamp'];

    if (!nodeId || !signature || !timestamp) {
        return res.status(401).json({
            error: 'Missing authentication headers'
        });
    }

    // Check timestamp
    const ts = new Date(timestamp).getTime();
    const now = Date.now();
    if (ts < now - 5 * 60 * 1000 || ts > now + 30 * 1000) {
        return res.status(401).json({ error: 'Request timestamp expired' });
    }

    // Fetch node
    const nodeResult = await pool.query(
        'SELECT public_key, status, roles FROM nodes WHERE node_id = $1',
        [nodeId]
    );

    if (nodeResult.rows.length === 0) {
        return res.status(401).json({ error: 'Node not registered' });
    }

    const node = nodeResult.rows[0];

    if (node.status !== 'ACTIVE') {
        return res.status(403).json({ error: 'Node not active' });
    }

    // Check role
    if (!node.roles.includes('anchor_publisher')) {
        return res.status(403).json({
            error: 'Node lacks anchor_publisher role',
            roles: node.roles
        });
    }

    // Verify signature
    const payload = {
        node_id: nodeId,
        timestamp,
        path: req.path
    };

    if (!verifySignature(payload, signature, node.public_key)) {
        return res.status(401).json({ error: 'Invalid signature' });
    }

    req.nodeId = nodeId;
    req.nodePublicKey = node.public_key;
    next();
}

// ─── Routes ─────────────────────────────────────────────────────────

app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        service: 'hub-anchor-receiver',
        version: '1.0.0',
        timestamp: new Date().toISOString()
    });
});

/**
 * POST /anchors
 * Receive an anchor submission from a node
 *
 * Body:
 * {
 *   anchor: {
 *     combined_root_hash: "sha256...",
 *     document_hashes: [...],
 *     timestamp: "ISO8601",
 *     node_id: "node:...",
 *     sequence: 123
 *   },
 *   signature: "base64..."
 * }
 */
app.post('/anchors', authenticateAnchorPublisher, asyncHandler(async (req, res) => {
    const { anchor, signature } = req.body;

    if (!anchor || !signature) {
        return res.status(400).json({
            error: 'Missing anchor or signature'
        });
    }

    // Validate anchor structure
    const requiredFields = ['combined_root_hash', 'timestamp', 'node_id'];
    for (const field of requiredFields) {
        if (!anchor[field]) {
            return res.status(400).json({
                error: `Missing required field: ${field}`
            });
        }
    }

    // Verify anchor.node_id matches authenticated node
    if (anchor.node_id !== req.nodeId) {
        return res.status(400).json({
            error: 'Anchor node_id does not match authenticated node'
        });
    }

    // Verify signature
    if (!verifySignature(anchor, signature, req.nodePublicKey)) {
        return res.status(401).json({ error: 'Invalid anchor signature' });
    }

    // Check for duplicate
    const duplicateCheck = await pool.query(
        'SELECT id FROM transparency_anchors WHERE combined_root_hash = $1 AND node_id = $2',
        [anchor.combined_root_hash, anchor.node_id]
    );

    if (duplicateCheck.rows.length > 0) {
        return res.status(409).json({
            error: 'Anchor already exists',
            anchor_id: duplicateCheck.rows[0].id
        });
    }

    // Insert anchor
    const result = await pool.query(`
        INSERT INTO transparency_anchors (
            node_id, combined_root_hash, document_count, anchor_timestamp,
            node_signature, anchor_data
        ) VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id, sequence_number
    `, [
        anchor.node_id,
        anchor.combined_root_hash,
        anchor.document_hashes?.length || 0,
        anchor.timestamp,
        signature,
        anchor
    ]);

    const anchorId = result.rows[0].id;
    const sequenceNumber = result.rows[0].sequence_number;

    // Create Hub receipt
    const hubReceipt = {
        anchor_id: anchorId,
        sequence_number: sequenceNumber,
        combined_root_hash: anchor.combined_root_hash,
        node_id: anchor.node_id,
        received_at: new Date().toISOString(),
        hub_id: 'windi-hub-primary'
    };

    const hubReceiptSignature = hubSign(hubReceipt);

    // Update anchor with Hub receipt
    await pool.query(`
        UPDATE transparency_anchors SET
            hub_receipt = $2,
            hub_signature = $3,
            hub_received_at = NOW()
        WHERE id = $1
    `, [anchorId, hubReceipt, hubReceiptSignature]);

    res.status(201).json({
        success: true,
        anchor_id: anchorId,
        sequence_number: sequenceNumber,
        hub_receipt: {
            ...hubReceipt,
            hub_signature: hubReceiptSignature
        }
    });
}));

/**
 * GET /anchors
 * List recent anchors
 */
app.get('/anchors', asyncHandler(async (req, res) => {
    const limit = Math.min(parseInt(req.query.limit) || 50, 200);
    const since = req.query.since; // sequence number

    let query = `
        SELECT
            id, node_id, combined_root_hash, document_count,
            anchor_timestamp, sequence_number, hub_received_at
        FROM transparency_anchors
    `;

    const params = [];
    if (since) {
        query += ' WHERE sequence_number > $1';
        params.push(parseInt(since));
    }

    query += ' ORDER BY sequence_number DESC LIMIT $' + (params.length + 1);
    params.push(limit);

    const result = await pool.query(query, params);

    const countResult = await pool.query('SELECT COUNT(*) as total FROM transparency_anchors');

    res.json({
        anchors: result.rows,
        total: parseInt(countResult.rows[0].total),
        timestamp: new Date().toISOString()
    });
}));

/**
 * GET /anchors/:id
 * Get anchor details with Hub receipt
 */
app.get('/anchors/:id', asyncHandler(async (req, res) => {
    const { id } = req.params;

    const result = await pool.query(`
        SELECT * FROM transparency_anchors WHERE id = $1
    `, [id]);

    if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Anchor not found' });
    }

    const anchor = result.rows[0];

    res.json({
        anchor: {
            id: anchor.id,
            node_id: anchor.node_id,
            combined_root_hash: anchor.combined_root_hash,
            document_count: anchor.document_count,
            anchor_timestamp: anchor.anchor_timestamp,
            sequence_number: anchor.sequence_number,
            anchor_data: anchor.anchor_data
        },
        hub_receipt: anchor.hub_receipt,
        hub_signature: anchor.hub_signature,
        verification: {
            node_signature: anchor.node_signature,
            hub_received_at: anchor.hub_received_at
        }
    });
}));

/**
 * GET /anchors/verify/:hash
 * Verify a document hash exists in any anchor
 */
app.get('/anchors/verify/:hash', asyncHandler(async (req, res) => {
    const { hash } = req.params;

    // Search in anchor_data.document_hashes
    const result = await pool.query(`
        SELECT id, node_id, combined_root_hash, anchor_timestamp, sequence_number
        FROM transparency_anchors
        WHERE anchor_data->'document_hashes' ? $1
           OR combined_root_hash = $1
        ORDER BY sequence_number DESC
        LIMIT 10
    `, [hash]);

    if (result.rows.length === 0) {
        return res.status(404).json({
            found: false,
            hash,
            message: 'Hash not found in any anchor'
        });
    }

    res.json({
        found: true,
        hash,
        anchors: result.rows,
        first_anchored: result.rows[result.rows.length - 1].anchor_timestamp
    });
}));

/**
 * GET /anchors/hub-key
 * Get Hub's public key for verifying receipts
 */
app.get('/anchors/hub-key', (req, res) => {
    res.json({
        hub_id: 'windi-hub-primary',
        public_key: naclUtil.encodeBase64(hubKeyPair.publicKey),
        algorithm: 'Ed25519'
    });
});

// ─── Error Handler ──────────────────────────────────────────────────
app.use((err, req, res, next) => {
    console.error('Unhandled error:', err);
    res.status(500).json({ error: 'Internal server error' });
});

// ─── Start Server ───────────────────────────────────────────────────
async function start() {
    try {
        await pool.query('SELECT NOW()');
        console.log('Database connected');

        // Ensure anchors table exists
        await pool.query(`
            CREATE TABLE IF NOT EXISTS transparency_anchors (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                sequence_number BIGSERIAL UNIQUE,
                node_id VARCHAR(255) NOT NULL,
                combined_root_hash VARCHAR(64) NOT NULL,
                document_count INT DEFAULT 0,
                anchor_timestamp TIMESTAMPTZ NOT NULL,
                node_signature TEXT NOT NULL,
                anchor_data JSONB NOT NULL,
                hub_receipt JSONB,
                hub_signature TEXT,
                hub_received_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_anchors_node ON transparency_anchors(node_id);
            CREATE INDEX IF NOT EXISTS idx_anchors_hash ON transparency_anchors(combined_root_hash);
            CREATE INDEX IF NOT EXISTS idx_anchors_sequence ON transparency_anchors(sequence_number DESC);
        `);

        initHubKeyPair();

        app.listen(PORT, '0.0.0.0', () => {
            console.log('');
            console.log('═══════════════════════════════════════════════════');
            console.log('  WINDI Hub Anchor Receiver v1.0.0');
            console.log(`  Port: ${PORT}`);
            console.log('');
            console.log('  Endpoints:');
            console.log('    POST /anchors              (requires node cert)');
            console.log('    GET  /anchors');
            console.log('    GET  /anchors/:id');
            console.log('    GET  /anchors/verify/:hash');
            console.log('    GET  /anchors/hub-key');
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
