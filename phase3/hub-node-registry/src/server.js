/**
 * ═══════════════════════════════════════════════════════════════════
 * WINDI Phase 3: Hub Node Registry Service
 * ═══════════════════════════════════════════════════════════════════
 * Purpose: Register and attest WINDI Nodes for federation
 * Port: 8070
 * Principle: AI processes. Human decides. WINDI guarantees.
 * ═══════════════════════════════════════════════════════════════════
 */

const express = require('express');
const { Pool } = require('pg');
const nacl = require('tweetnacl');
const naclUtil = require('tweetnacl-util');
const crypto = require('crypto');

const app = express();
app.use(express.json());

// ─── Configuration ──────────────────────────────────────────────────
const PORT = process.env.PORT || 8070;
const DATABASE_URL = process.env.DATABASE_URL || 'postgresql://windi:windi@localhost:5432/windi_hub';
const HUB_SIGNING_KEY = process.env.HUB_SIGNING_KEY; // Base64 encoded Ed25519 seed
const ATTESTATION_WINDOW_MS = 5 * 60 * 1000; // 5 minutes

// ─── Database Pool ──────────────────────────────────────────────────
const pool = new Pool({ connectionString: DATABASE_URL });

// ─── Hub Keypair ────────────────────────────────────────────────────
let hubKeyPair = null;

function initHubKeyPair() {
    if (HUB_SIGNING_KEY) {
        const seed = naclUtil.decodeBase64(HUB_SIGNING_KEY);
        hubKeyPair = nacl.sign.keyPair.fromSeed(seed);
        console.log('Hub signing key loaded from environment');
    } else {
        hubKeyPair = nacl.sign.keyPair();
        console.log('Generated new Hub signing key (ephemeral - for development only)');
        console.log('Hub Public Key:', naclUtil.encodeBase64(hubKeyPair.publicKey));
    }
}

// ─── Utility Functions ──────────────────────────────────────────────

/**
 * Compute SHA256 hash of data
 */
function sha256(data) {
    return crypto.createHash('sha256').update(data).digest('hex');
}

/**
 * Compute fingerprint of public key
 */
function keyFingerprint(publicKeyBase64) {
    return sha256(publicKeyBase64).substring(0, 16);
}

/**
 * Canonicalize JSON for signing (sorted keys, no whitespace)
 */
function canonicalJSON(obj) {
    return JSON.stringify(obj, Object.keys(obj).sort());
}

/**
 * Verify Ed25519 signature
 */
function verifySignature(payload, signatureBase64, publicKeyBase64) {
    try {
        const message = naclUtil.decodeUTF8(canonicalJSON(payload));
        const signature = naclUtil.decodeBase64(signatureBase64);
        const publicKey = naclUtil.decodeBase64(publicKeyBase64);
        return nacl.sign.detached.verify(message, signature, publicKey);
    } catch (err) {
        console.error('Signature verification error:', err.message);
        return false;
    }
}

/**
 * Sign data with Hub key
 */
function hubSign(data) {
    const message = naclUtil.decodeUTF8(typeof data === 'string' ? data : canonicalJSON(data));
    const signature = nacl.sign.detached(message, hubKeyPair.secretKey);
    return naclUtil.encodeBase64(signature);
}

/**
 * Check if timestamp is within acceptable window
 */
function isTimestampFresh(timestamp) {
    const ts = new Date(timestamp).getTime();
    const now = Date.now();
    return ts >= now - ATTESTATION_WINDOW_MS && ts <= now + 30000; // Allow 30s clock drift
}

/**
 * Validate node_id format
 */
function isValidNodeId(nodeId) {
    return /^node:[a-z0-9-]+-[a-z0-9-]+-[0-9]+$/.test(nodeId);
}

// ─── Middleware ─────────────────────────────────────────────────────

function asyncHandler(fn) {
    return (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
}

// CORS
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    if (req.method === 'OPTIONS') return res.sendStatus(204);
    next();
});

// ─── Routes ─────────────────────────────────────────────────────────

/**
 * GET /health
 * Health check endpoint
 */
app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        service: 'hub-node-registry',
        version: '1.0.0',
        timestamp: new Date().toISOString()
    });
});

/**
 * GET /hub/public-key
 * Get Hub's public key for verification
 */
app.get('/hub/public-key', (req, res) => {
    res.json({
        key_id: 'hub-primary',
        public_key: naclUtil.encodeBase64(hubKeyPair.publicKey),
        algorithm: 'Ed25519',
        issued_at: new Date().toISOString()
    });
});

/**
 * POST /nodes/register
 * Register a new WINDI Node
 *
 * Body:
 * {
 *   node_id: "node:deutschebank-frankfurt-01",
 *   domain: "windi.deutschebank.de",
 *   public_key: "base64...",
 *   roles: ["verifier", "anchor_publisher"],
 *   metadata: { ... }
 * }
 */
app.post('/nodes/register', asyncHandler(async (req, res) => {
    const { node_id, domain, public_key, roles = [], metadata = {} } = req.body;

    // Validation
    if (!node_id || !domain || !public_key) {
        return res.status(400).json({
            error: 'Missing required fields',
            required: ['node_id', 'domain', 'public_key']
        });
    }

    if (!isValidNodeId(node_id)) {
        return res.status(400).json({
            error: 'Invalid node_id format',
            expected: 'node:<org>-<location>-<instance>',
            example: 'node:deutschebank-frankfurt-01'
        });
    }

    // Validate public key format (try to decode it)
    try {
        const decoded = naclUtil.decodeBase64(public_key);
        if (decoded.length !== 32) {
            throw new Error('Invalid key length');
        }
    } catch (err) {
        return res.status(400).json({
            error: 'Invalid public_key format',
            expected: 'Base64-encoded Ed25519 public key (32 bytes)'
        });
    }

    // Validate roles
    const validRoles = ['verifier', 'anchor_publisher', 'issuer', 'auditor', 'governance_observer'];
    const invalidRoles = roles.filter(r => !validRoles.includes(r));
    if (invalidRoles.length > 0) {
        return res.status(400).json({
            error: 'Invalid roles',
            invalid: invalidRoles,
            valid: validRoles
        });
    }

    const fingerprint = keyFingerprint(public_key);

    try {
        // Check if node already exists
        const existing = await pool.query(
            'SELECT node_id, status FROM nodes WHERE node_id = $1',
            [node_id]
        );

        if (existing.rows.length > 0) {
            return res.status(409).json({
                error: 'Node already registered',
                node_id,
                status: existing.rows[0].status
            });
        }

        // Insert new node
        const result = await pool.query(`
            INSERT INTO nodes (node_id, domain, public_key, public_key_fingerprint, roles, metadata)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, node_id, status, registered_at
        `, [node_id, domain, public_key, fingerprint, roles, metadata]);

        // Log event
        await pool.query(
            `SELECT log_node_event($1, 'REGISTERED', $2, 'hub-api')`,
            [node_id, JSON.stringify({ domain, roles })]
        );

        res.status(201).json({
            success: true,
            node: {
                id: result.rows[0].id,
                node_id: result.rows[0].node_id,
                status: result.rows[0].status,
                public_key_fingerprint: fingerprint,
                registered_at: result.rows[0].registered_at
            },
            next_step: 'POST /nodes/attest with signed attestation payload'
        });

    } catch (err) {
        console.error('Registration error:', err);
        res.status(500).json({ error: 'Registration failed', message: err.message });
    }
}));

/**
 * POST /nodes/attest
 * Submit attestation to activate node and receive certificate
 *
 * Body:
 * {
 *   node_id: "node:deutschebank-frankfurt-01",
 *   attestation: {
 *     node_id: "...",
 *     domain: "...",
 *     roles: [...],
 *     timestamp: "ISO8601"
 *   },
 *   signature: "base64..."
 * }
 */
app.post('/nodes/attest', asyncHandler(async (req, res) => {
    const { node_id, attestation, signature } = req.body;

    // Validation
    if (!node_id || !attestation || !signature) {
        return res.status(400).json({
            error: 'Missing required fields',
            required: ['node_id', 'attestation', 'signature']
        });
    }

    // Fetch node
    const nodeResult = await pool.query(
        'SELECT * FROM nodes WHERE node_id = $1',
        [node_id]
    );

    if (nodeResult.rows.length === 0) {
        return res.status(404).json({
            error: 'Node not found',
            node_id,
            hint: 'Register first via POST /nodes/register'
        });
    }

    const node = nodeResult.rows[0];

    // Check node status
    if (node.status === 'REVOKED') {
        return res.status(403).json({
            error: 'Node has been revoked',
            node_id
        });
    }

    // Verify attestation payload matches node
    if (attestation.node_id !== node_id) {
        return res.status(400).json({
            error: 'Attestation node_id mismatch',
            expected: node_id,
            received: attestation.node_id
        });
    }

    // Check timestamp freshness (replay protection)
    if (!attestation.timestamp || !isTimestampFresh(attestation.timestamp)) {
        return res.status(400).json({
            error: 'Attestation timestamp invalid or expired',
            timestamp: attestation.timestamp,
            window: '5 minutes',
            server_time: new Date().toISOString()
        });
    }

    // Compute payload hash for replay protection
    const payloadHash = sha256(canonicalJSON(attestation));

    // Check for replay
    const replayCheck = await pool.query(
        'SELECT id FROM attestation_history WHERE node_id = $1 AND payload_hash = $2',
        [node_id, payloadHash]
    );

    if (replayCheck.rows.length > 0) {
        return res.status(409).json({
            error: 'Attestation replay detected',
            payload_hash: payloadHash
        });
    }

    // Verify signature
    const signatureValid = verifySignature(attestation, signature, node.public_key);

    // Record attestation attempt
    await pool.query(`
        INSERT INTO attestation_history
        (node_id, payload, payload_hash, signature, attestation_timestamp, verified, verified_at, verification_error)
        VALUES ($1, $2, $3, $4, $5, $6, NOW(), $7)
    `, [
        node_id,
        attestation,
        payloadHash,
        signature,
        attestation.timestamp,
        signatureValid,
        signatureValid ? null : 'Signature verification failed'
    ]);

    if (!signatureValid) {
        await pool.query(
            `SELECT log_node_event($1, 'ATTESTATION_FAILED', $2, 'hub-api')`,
            [node_id, JSON.stringify({ reason: 'invalid_signature' })]
        );

        return res.status(401).json({
            error: 'Signature verification failed',
            node_id,
            hint: 'Ensure you are signing the canonical JSON of the attestation payload'
        });
    }

    // Generate node certificate
    const certificate = {
        version: '1.0',
        node_id,
        domain: node.domain,
        public_key: node.public_key,
        public_key_fingerprint: node.public_key_fingerprint,
        roles: node.roles,
        status: 'ACTIVE',
        issued_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(), // 1 year
        issuer: {
            hub_id: 'windi-hub-primary',
            public_key: naclUtil.encodeBase64(hubKeyPair.publicKey)
        }
    };

    // Sign certificate
    const certificateSignature = hubSign(certificate);
    const signedCertificate = {
        ...certificate,
        hub_signature: certificateSignature
    };

    // Update node status and certificate
    await pool.query(`
        UPDATE nodes SET
            status = 'ACTIVE',
            activated_at = NOW(),
            last_attestation_at = NOW(),
            certificate = $2,
            certificate_issued_at = NOW(),
            certificate_expires_at = $3
        WHERE node_id = $1
    `, [node_id, signedCertificate, certificate.expires_at]);

    // Update attestation record
    await pool.query(`
        UPDATE attestation_history
        SET hub_response = $2, certificate_issued = TRUE
        WHERE node_id = $1 AND payload_hash = $3
    `, [node_id, signedCertificate, payloadHash]);

    // Log event
    await pool.query(
        `SELECT log_node_event($1, 'ACTIVATED', $2, 'hub-api')`,
        [node_id, JSON.stringify({ certificate_expires: certificate.expires_at })]
    );

    res.json({
        success: true,
        message: 'Node attested and activated',
        certificate: signedCertificate
    });
}));

/**
 * GET /nodes/:node_id
 * Get node details
 */
app.get('/nodes/:node_id', asyncHandler(async (req, res) => {
    const { node_id } = req.params;

    const result = await pool.query(`
        SELECT
            node_id, domain, public_key_fingerprint, roles, status, metadata,
            registered_at, activated_at, last_attestation_at,
            certificate_issued_at, certificate_expires_at
        FROM nodes WHERE node_id = $1
    `, [node_id]);

    if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Node not found', node_id });
    }

    const node = result.rows[0];

    // Get attestation count
    const attestCount = await pool.query(
        'SELECT COUNT(*) as count FROM attestation_history WHERE node_id = $1 AND verified = TRUE',
        [node_id]
    );

    res.json({
        node,
        attestation_count: parseInt(attestCount.rows[0].count),
        links: {
            certificate: node.status === 'ACTIVE' ? `/nodes/${node_id}/certificate` : null,
            events: `/nodes/${node_id}/events`
        }
    });
}));

/**
 * GET /nodes/:node_id/certificate
 * Get node's current certificate
 */
app.get('/nodes/:node_id/certificate', asyncHandler(async (req, res) => {
    const { node_id } = req.params;

    const result = await pool.query(
        'SELECT certificate FROM nodes WHERE node_id = $1 AND status = $2',
        [node_id, 'ACTIVE']
    );

    if (result.rows.length === 0 || !result.rows[0].certificate) {
        return res.status(404).json({
            error: 'Certificate not found',
            node_id,
            hint: 'Node may not be active or attested'
        });
    }

    res.json(result.rows[0].certificate);
}));

/**
 * GET /nodes/:node_id/events
 * Get node event history
 */
app.get('/nodes/:node_id/events', asyncHandler(async (req, res) => {
    const { node_id } = req.params;
    const limit = Math.min(parseInt(req.query.limit) || 50, 100);

    const result = await pool.query(`
        SELECT event_type, event_data, actor, created_at
        FROM node_events
        WHERE node_id = $1
        ORDER BY created_at DESC
        LIMIT $2
    `, [node_id, limit]);

    res.json({
        node_id,
        total: result.rows.length,
        events: result.rows
    });
}));

/**
 * GET /nodes
 * List all nodes
 */
app.get('/nodes', asyncHandler(async (req, res) => {
    const { status, role, limit = 50 } = req.query;
    const maxLimit = Math.min(parseInt(limit), 200);

    let query = `
        SELECT node_id, domain, public_key_fingerprint, roles, status,
               registered_at, activated_at, last_attestation_at
        FROM nodes
    `;
    const params = [];
    const conditions = [];

    if (status) {
        conditions.push(`status = $${params.length + 1}`);
        params.push(status.toUpperCase());
    }

    if (role) {
        conditions.push(`$${params.length + 1} = ANY(roles)`);
        params.push(role);
    }

    if (conditions.length > 0) {
        query += ' WHERE ' + conditions.join(' AND ');
    }

    query += ` ORDER BY registered_at DESC LIMIT $${params.length + 1}`;
    params.push(maxLimit);

    const result = await pool.query(query, params);

    // Get totals
    const totals = await pool.query(`
        SELECT
            COUNT(*) FILTER (WHERE status = 'PENDING') as pending,
            COUNT(*) FILTER (WHERE status = 'ACTIVE') as active,
            COUNT(*) FILTER (WHERE status = 'SUSPENDED') as suspended,
            COUNT(*) as total
        FROM nodes
    `);

    res.json({
        nodes: result.rows,
        totals: totals.rows[0],
        filters: { status, role, limit: maxLimit }
    });
}));

// ─── Error Handler ──────────────────────────────────────────────────
app.use((err, req, res, next) => {
    console.error('Unhandled error:', err);
    res.status(500).json({
        error: 'Internal server error',
        message: process.env.NODE_ENV === 'development' ? err.message : undefined
    });
});

// ─── Start Server ───────────────────────────────────────────────────
async function start() {
    try {
        // Test database connection
        await pool.query('SELECT NOW()');
        console.log('Database connected');

        // Initialize Hub keypair
        initHubKeyPair();

        app.listen(PORT, '0.0.0.0', () => {
            console.log('');
            console.log('═══════════════════════════════════════════════════');
            console.log('  WINDI Hub Node Registry v1.0.0');
            console.log(`  Port: ${PORT}`);
            console.log('  Endpoints:');
            console.log('    GET  /health');
            console.log('    GET  /hub/public-key');
            console.log('    POST /nodes/register');
            console.log('    POST /nodes/attest');
            console.log('    GET  /nodes/:node_id');
            console.log('    GET  /nodes/:node_id/certificate');
            console.log('    GET  /nodes');
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
