/**
 * ═══════════════════════════════════════════════════════════════════
 * WINDI Phase 3: Hub Issuer Registry Sync Server
 * ═══════════════════════════════════════════════════════════════════
 * Purpose: Serve issuer registry deltas to authenticated nodes
 * Port: 8071 (or integrated into hub-node-registry)
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
const PORT = process.env.SYNC_PORT || 8071;
const DATABASE_URL = process.env.DATABASE_URL || 'postgresql://windi:windi@localhost:5432/windi_hub';
const REQUIRE_NODE_AUTH = process.env.REQUIRE_NODE_AUTH !== 'false';

// ─── Database Pool ──────────────────────────────────────────────────
const pool = new Pool({ connectionString: DATABASE_URL });

// ─── Utility Functions ──────────────────────────────────────────────

function asyncHandler(fn) {
    return (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
}

function canonicalJSON(obj) {
    return JSON.stringify(obj, Object.keys(obj).sort());
}

function verifyNodeSignature(payload, signatureBase64, publicKeyBase64) {
    try {
        const message = naclUtil.decodeUTF8(canonicalJSON(payload));
        const signature = naclUtil.decodeBase64(signatureBase64);
        const publicKey = naclUtil.decodeBase64(publicKeyBase64);
        return nacl.sign.detached.verify(message, signature, publicKey);
    } catch (err) {
        return false;
    }
}

// ─── Middleware ─────────────────────────────────────────────────────

// CORS
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, X-Node-Id, X-Node-Signature, X-Request-Timestamp');
    if (req.method === 'OPTIONS') return res.sendStatus(204);
    next();
});

/**
 * Node Authentication Middleware
 * Verifies that the request comes from an authenticated ACTIVE node
 *
 * Required headers:
 *   X-Node-Id: node:deutschebank-frankfurt-01
 *   X-Node-Signature: base64 signature of {node_id, timestamp, path}
 *   X-Request-Timestamp: ISO8601 timestamp
 */
async function authenticateNode(req, res, next) {
    if (!REQUIRE_NODE_AUTH) {
        req.nodeId = 'anonymous';
        return next();
    }

    const nodeId = req.headers['x-node-id'];
    const signature = req.headers['x-node-signature'];
    const timestamp = req.headers['x-request-timestamp'];

    if (!nodeId || !signature || !timestamp) {
        return res.status(401).json({
            error: 'Missing authentication headers',
            required: ['X-Node-Id', 'X-Node-Signature', 'X-Request-Timestamp']
        });
    }

    // Check timestamp freshness (5 minute window)
    const ts = new Date(timestamp).getTime();
    const now = Date.now();
    if (ts < now - 5 * 60 * 1000 || ts > now + 30 * 1000) {
        return res.status(401).json({
            error: 'Request timestamp expired or invalid',
            server_time: new Date().toISOString()
        });
    }

    // Fetch node from registry
    const nodeResult = await pool.query(
        'SELECT public_key, status FROM nodes WHERE node_id = $1',
        [nodeId]
    );

    if (nodeResult.rows.length === 0) {
        return res.status(401).json({ error: 'Node not registered', node_id: nodeId });
    }

    const node = nodeResult.rows[0];

    if (node.status !== 'ACTIVE') {
        return res.status(403).json({
            error: 'Node not active',
            status: node.status
        });
    }

    // Verify signature
    const payload = {
        node_id: nodeId,
        timestamp,
        path: req.path
    };

    if (!verifyNodeSignature(payload, signature, node.public_key)) {
        return res.status(401).json({ error: 'Invalid signature' });
    }

    req.nodeId = nodeId;
    next();
}

// ─── Routes ─────────────────────────────────────────────────────────

/**
 * GET /health
 * Health check
 */
app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        service: 'hub-issuer-sync',
        version: '1.0.0',
        timestamp: new Date().toISOString()
    });
});

/**
 * GET /sync/issuers
 * Delta-based issuer registry sync
 *
 * Query params:
 *   since: cursor position (default: 0)
 *   limit: max changes to return (default: 100, max: 500)
 *   trust_only: only return trust-affecting changes (default: false)
 *
 * Response:
 * {
 *   changes: [...],
 *   next_cursor: 123,
 *   has_more: false,
 *   sync_timestamp: "ISO8601"
 * }
 */
app.get('/sync/issuers', authenticateNode, asyncHandler(async (req, res) => {
    const since = parseInt(req.query.since) || 0;
    const limit = Math.min(parseInt(req.query.limit) || 100, 500);
    const trustOnly = req.query.trust_only === 'true';

    // Get changes
    const result = await pool.query(`
        SELECT cursor_id, issuer_id, change_type, new_value, trust_status, changed_at
        FROM issuer_changelog
        WHERE cursor_id > $1
          AND ($3 = FALSE OR affects_trust = TRUE)
        ORDER BY cursor_id ASC
        LIMIT $2
    `, [since, limit + 1, trustOnly]); // Fetch one extra to check has_more

    const changes = result.rows.slice(0, limit);
    const hasMore = result.rows.length > limit;
    const nextCursor = changes.length > 0 ? changes[changes.length - 1].cursor_id : since;

    // Update node's sync cursor
    if (req.nodeId !== 'anonymous') {
        await pool.query(`
            INSERT INTO sync_cursors (node_id, last_cursor, last_sync_at, total_syncs, total_changes_received)
            VALUES ($1, $2, NOW(), 1, $3)
            ON CONFLICT (node_id) DO UPDATE SET
                last_cursor = GREATEST(sync_cursors.last_cursor, $2),
                last_sync_at = NOW(),
                total_syncs = sync_cursors.total_syncs + 1,
                total_changes_received = sync_cursors.total_changes_received + $3,
                updated_at = NOW()
        `, [req.nodeId, nextCursor, changes.length]);
    }

    res.json({
        since_cursor: since,
        next_cursor: nextCursor,
        changes: changes.map(c => ({
            cursor: c.cursor_id,
            issuer_id: c.issuer_id,
            change_type: c.change_type,
            issuer: c.new_value,
            trust_status: c.trust_status,
            changed_at: c.changed_at
        })),
        count: changes.length,
        has_more: hasMore,
        sync_timestamp: new Date().toISOString(),
        node_id: req.nodeId
    });
}));

/**
 * GET /sync/issuers/:issuer_id
 * Get specific issuer details
 */
app.get('/sync/issuers/:issuer_id', authenticateNode, asyncHandler(async (req, res) => {
    const { issuer_id } = req.params;

    const result = await pool.query(`
        SELECT * FROM issuers WHERE issuer_id = $1
    `, [issuer_id]);

    if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Issuer not found', issuer_id });
    }

    const issuer = result.rows[0];

    // Get key history
    const keysResult = await pool.query(`
        SELECT key_id, algorithm, public_key, valid_from, valid_until, revoked_at
        FROM issuer_key_history
        WHERE issuer_id = $1
        ORDER BY valid_from DESC
    `, [issuer_id]);

    res.json({
        issuer,
        key_history: keysResult.rows,
        fetched_at: new Date().toISOString()
    });
}));

/**
 * GET /sync/cursor
 * Get current max cursor (for initial sync planning)
 */
app.get('/sync/cursor', authenticateNode, asyncHandler(async (req, res) => {
    const result = await pool.query(`
        SELECT
            MAX(cursor_id) as max_cursor,
            COUNT(*) as total_changes,
            MAX(changed_at) as last_change_at
        FROM issuer_changelog
    `);

    const issuerCount = await pool.query(`
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE trust_status = 'TRUSTED') as trusted,
            COUNT(*) FILTER (WHERE trust_status = 'REVOKED') as revoked
        FROM issuers
    `);

    res.json({
        max_cursor: parseInt(result.rows[0].max_cursor) || 0,
        total_changes: parseInt(result.rows[0].total_changes) || 0,
        last_change_at: result.rows[0].last_change_at,
        issuers: {
            total: parseInt(issuerCount.rows[0].total),
            trusted: parseInt(issuerCount.rows[0].trusted),
            revoked: parseInt(issuerCount.rows[0].revoked)
        },
        timestamp: new Date().toISOString()
    });
}));

/**
 * GET /sync/status/:node_id
 * Get a node's sync status (Hub admin use)
 */
app.get('/sync/status/:node_id', asyncHandler(async (req, res) => {
    const { node_id } = req.params;

    const result = await pool.query(`
        SELECT * FROM sync_cursors WHERE node_id = $1
    `, [node_id]);

    if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Node sync status not found', node_id });
    }

    // Get current max cursor
    const maxCursor = await pool.query('SELECT MAX(cursor_id) as max FROM issuer_changelog');
    const max = parseInt(maxCursor.rows[0].max) || 0;
    const nodeCursor = result.rows[0].last_cursor;

    res.json({
        node_id,
        sync_status: result.rows[0],
        behind_by: max - nodeCursor,
        is_current: nodeCursor >= max
    });
}));

/**
 * GET /sync/nodes
 * List all nodes' sync status
 */
app.get('/sync/nodes', asyncHandler(async (req, res) => {
    const result = await pool.query(`
        SELECT
            sc.node_id,
            sc.last_cursor,
            sc.last_sync_at,
            sc.total_syncs,
            sc.total_changes_received,
            n.status as node_status
        FROM sync_cursors sc
        LEFT JOIN nodes n ON sc.node_id = n.node_id
        ORDER BY sc.last_sync_at DESC
    `);

    // Get current max cursor
    const maxCursor = await pool.query('SELECT MAX(cursor_id) as max FROM issuer_changelog');
    const max = parseInt(maxCursor.rows[0].max) || 0;

    res.json({
        max_cursor: max,
        nodes: result.rows.map(n => ({
            ...n,
            behind_by: max - n.last_cursor,
            is_current: n.last_cursor >= max
        })),
        timestamp: new Date().toISOString()
    });
}));

// ─── Admin Routes (for managing issuers) ────────────────────────────

/**
 * POST /admin/issuers
 * Create or update an issuer (Hub admin only)
 */
app.post('/admin/issuers', asyncHandler(async (req, res) => {
    const {
        issuer_id,
        display_name,
        jurisdiction,
        trust_status = 'UNKNOWN',
        governance_level = 'LOW',
        public_keys = [],
        active_key_id,
        trust_reason,
        metadata = {}
    } = req.body;

    if (!issuer_id || !display_name || !jurisdiction) {
        return res.status(400).json({
            error: 'Missing required fields',
            required: ['issuer_id', 'display_name', 'jurisdiction']
        });
    }

    const result = await pool.query(`
        INSERT INTO issuers (
            issuer_id, display_name, jurisdiction, trust_status,
            governance_level, public_keys, active_key_id, trust_reason, metadata
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (issuer_id) DO UPDATE SET
            display_name = EXCLUDED.display_name,
            jurisdiction = EXCLUDED.jurisdiction,
            trust_status = EXCLUDED.trust_status,
            governance_level = EXCLUDED.governance_level,
            public_keys = EXCLUDED.public_keys,
            active_key_id = EXCLUDED.active_key_id,
            trust_reason = EXCLUDED.trust_reason,
            metadata = EXCLUDED.metadata
        RETURNING *
    `, [issuer_id, display_name, jurisdiction, trust_status, governance_level,
        JSON.stringify(public_keys), active_key_id, trust_reason, metadata]);

    res.status(201).json({
        success: true,
        issuer: result.rows[0]
    });
}));

/**
 * PATCH /admin/issuers/:issuer_id/trust
 * Update issuer trust status
 */
app.patch('/admin/issuers/:issuer_id/trust', asyncHandler(async (req, res) => {
    const { issuer_id } = req.params;
    const { trust_status, trust_reason, approved_by } = req.body;

    if (!['UNKNOWN', 'PENDING', 'TRUSTED', 'REVOKED', 'SUSPENDED'].includes(trust_status)) {
        return res.status(400).json({
            error: 'Invalid trust_status',
            valid: ['UNKNOWN', 'PENDING', 'TRUSTED', 'REVOKED', 'SUSPENDED']
        });
    }

    const timestampField = trust_status === 'TRUSTED' ? 'trusted_at'
                         : trust_status === 'REVOKED' ? 'revoked_at' : null;

    let query = `
        UPDATE issuers SET
            trust_status = $2,
            trust_reason = COALESCE($3, trust_reason),
            approved_by = COALESCE($4, approved_by)
    `;

    if (timestampField) {
        query += `, ${timestampField} = NOW()`;
    }

    query += ` WHERE issuer_id = $1 RETURNING *`;

    const result = await pool.query(query, [issuer_id, trust_status, trust_reason, approved_by]);

    if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Issuer not found', issuer_id });
    }

    res.json({
        success: true,
        issuer: result.rows[0],
        change: {
            trust_status,
            trust_reason,
            changed_at: new Date().toISOString()
        }
    });
}));

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

        app.listen(PORT, '0.0.0.0', () => {
            console.log('');
            console.log('═══════════════════════════════════════════════════');
            console.log('  WINDI Hub Issuer Sync Server v1.0.0');
            console.log(`  Port: ${PORT}`);
            console.log(`  Auth Required: ${REQUIRE_NODE_AUTH}`);
            console.log('');
            console.log('  Endpoints:');
            console.log('    GET  /sync/issuers?since=<cursor>');
            console.log('    GET  /sync/issuers/:issuer_id');
            console.log('    GET  /sync/cursor');
            console.log('    GET  /sync/status/:node_id');
            console.log('    GET  /sync/nodes');
            console.log('');
            console.log('  Admin:');
            console.log('    POST  /admin/issuers');
            console.log('    PATCH /admin/issuers/:id/trust');
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
