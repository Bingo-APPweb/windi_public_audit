/**
 * ═══════════════════════════════════════════════════════════════════
 * WINDI Phase 3: Node Issuer Sync Client
 * ═══════════════════════════════════════════════════════════════════
 * Purpose: Sync issuer registry from Hub to local node cache
 * Principle: AI processes. Human decides. WINDI guarantees.
 * ═══════════════════════════════════════════════════════════════════
 */

const nacl = require('tweetnacl');
const naclUtil = require('tweetnacl-util');
const fs = require('fs');
const path = require('path');

class IssuerSyncClient {
    /**
     * Create an Issuer Sync Client
     * @param {Object} options
     * @param {string} options.hubUrl - Hub sync server URL
     * @param {string} options.nodeId - This node's ID
     * @param {Object} options.keyPair - Node's Ed25519 keypair {publicKey, secretKey}
     * @param {string} options.cachePath - Path to store local issuer cache
     */
    constructor(options) {
        this.hubUrl = options.hubUrl?.replace(/\/$/, '');
        this.nodeId = options.nodeId;
        this.keyPair = options.keyPair;
        this.cachePath = options.cachePath || './issuer-cache';

        // Local state
        this.cursor = 0;
        this.issuers = new Map(); // issuer_id -> issuer data
        this.lastSyncAt = null;

        // Load cache if exists
        this._loadCache();
    }

    /**
     * Create authentication headers for Hub requests
     */
    _createAuthHeaders(path) {
        const timestamp = new Date().toISOString();
        const payload = {
            node_id: this.nodeId,
            timestamp,
            path
        };

        const message = naclUtil.decodeUTF8(JSON.stringify(payload, Object.keys(payload).sort()));
        const signature = nacl.sign.detached(message, this.keyPair.secretKey);

        return {
            'Content-Type': 'application/json',
            'X-Node-Id': this.nodeId,
            'X-Node-Signature': naclUtil.encodeBase64(signature),
            'X-Request-Timestamp': timestamp
        };
    }

    /**
     * Make authenticated request to Hub
     */
    async _request(method, path, body = null) {
        const url = `${this.hubUrl}${path}`;
        const options = {
            method,
            headers: this._createAuthHeaders(path)
        };

        if (body) {
            options.body = JSON.stringify(body);
        }

        const response = await fetch(url, options);
        const data = await response.json();

        if (!response.ok) {
            const error = new Error(data.error || `HTTP ${response.status}`);
            error.response = data;
            error.status = response.status;
            throw error;
        }

        return data;
    }

    /**
     * Load cache from disk
     */
    _loadCache() {
        const cacheFile = path.join(this.cachePath, 'issuer-cache.json');

        if (fs.existsSync(cacheFile)) {
            try {
                const data = JSON.parse(fs.readFileSync(cacheFile, 'utf8'));
                this.cursor = data.cursor || 0;
                this.lastSyncAt = data.lastSyncAt;

                for (const [id, issuer] of Object.entries(data.issuers || {})) {
                    this.issuers.set(id, issuer);
                }

                console.log(`[IssuerSync] Loaded cache: ${this.issuers.size} issuers, cursor=${this.cursor}`);
            } catch (err) {
                console.warn('[IssuerSync] Failed to load cache:', err.message);
            }
        }
    }

    /**
     * Save cache to disk
     */
    _saveCache() {
        const cacheFile = path.join(this.cachePath, 'issuer-cache.json');
        fs.mkdirSync(this.cachePath, { recursive: true });

        const data = {
            cursor: this.cursor,
            lastSyncAt: this.lastSyncAt,
            issuers: Object.fromEntries(this.issuers)
        };

        fs.writeFileSync(cacheFile, JSON.stringify(data, null, 2));
    }

    /**
     * Sync issuers from Hub
     * @param {Object} options
     * @param {boolean} options.trustOnly - Only sync trust-affecting changes
     * @param {number} options.limit - Max changes per request
     * @returns {Object} Sync result
     */
    async sync(options = {}) {
        const { trustOnly = false, limit = 100 } = options;

        console.log(`[IssuerSync] Starting sync from cursor=${this.cursor}`);

        let totalChanges = 0;
        let hasMore = true;

        while (hasMore) {
            const queryParams = new URLSearchParams({
                since: this.cursor.toString(),
                limit: limit.toString(),
                trust_only: trustOnly.toString()
            });

            const result = await this._request('GET', `/sync/issuers?${queryParams}`);

            for (const change of result.changes) {
                this._applyChange(change);
                totalChanges++;
            }

            this.cursor = result.next_cursor;
            hasMore = result.has_more;

            if (result.changes.length > 0) {
                console.log(`[IssuerSync] Applied ${result.changes.length} changes, cursor=${this.cursor}`);
            }
        }

        this.lastSyncAt = new Date().toISOString();
        this._saveCache();

        console.log(`[IssuerSync] Sync complete: ${totalChanges} changes applied`);

        return {
            changes_applied: totalChanges,
            cursor: this.cursor,
            issuer_count: this.issuers.size,
            synced_at: this.lastSyncAt
        };
    }

    /**
     * Apply a single change to local cache
     */
    _applyChange(change) {
        const { issuer_id, change_type, issuer } = change;

        switch (change_type) {
            case 'CREATED':
            case 'UPDATED':
            case 'TRUST_CHANGED':
            case 'KEY_ROTATED':
                this.issuers.set(issuer_id, {
                    ...issuer,
                    _synced_at: new Date().toISOString(),
                    _change_type: change_type
                });
                break;

            case 'DELETED':
                this.issuers.delete(issuer_id);
                break;

            default:
                console.warn(`[IssuerSync] Unknown change type: ${change_type}`);
        }
    }

    /**
     * Get current sync cursor from Hub
     */
    async getCursorInfo() {
        return this._request('GET', '/sync/cursor');
    }

    /**
     * Get specific issuer from Hub
     */
    async getIssuer(issuerId) {
        return this._request('GET', `/sync/issuers/${encodeURIComponent(issuerId)}`);
    }

    /**
     * Check if issuer is trusted (from local cache)
     */
    isTrusted(issuerId) {
        const issuer = this.issuers.get(issuerId);
        return issuer?.trust_status === 'TRUSTED';
    }

    /**
     * Get issuer from local cache
     */
    getLocalIssuer(issuerId) {
        return this.issuers.get(issuerId);
    }

    /**
     * Get all trusted issuers from local cache
     */
    getTrustedIssuers() {
        const trusted = [];
        for (const [id, issuer] of this.issuers) {
            if (issuer.trust_status === 'TRUSTED') {
                trusted.push({ issuer_id: id, ...issuer });
            }
        }
        return trusted;
    }

    /**
     * Get all revoked issuers from local cache
     */
    getRevokedIssuers() {
        const revoked = [];
        for (const [id, issuer] of this.issuers) {
            if (issuer.trust_status === 'REVOKED') {
                revoked.push({ issuer_id: id, ...issuer });
            }
        }
        return revoked;
    }

    /**
     * Get sync status
     */
    getStatus() {
        return {
            node_id: this.nodeId,
            hub_url: this.hubUrl,
            cursor: this.cursor,
            issuer_count: this.issuers.size,
            trusted_count: this.getTrustedIssuers().length,
            revoked_count: this.getRevokedIssuers().length,
            last_sync_at: this.lastSyncAt,
            cache_path: this.cachePath
        };
    }

    /**
     * Full sync - reset cursor and sync everything
     */
    async fullSync() {
        console.log('[IssuerSync] Starting full sync...');
        this.cursor = 0;
        this.issuers.clear();
        return this.sync();
    }

    /**
     * Start periodic sync
     * @param {number} intervalMs - Sync interval in milliseconds
     * @returns {Object} Timer handle
     */
    startPeriodicSync(intervalMs = 60000) {
        console.log(`[IssuerSync] Starting periodic sync every ${intervalMs / 1000}s`);

        const timer = setInterval(async () => {
            try {
                await this.sync();
            } catch (err) {
                console.error('[IssuerSync] Periodic sync failed:', err.message);
            }
        }, intervalMs);

        // Initial sync
        this.sync().catch(err => {
            console.error('[IssuerSync] Initial sync failed:', err.message);
        });

        return {
            stop: () => {
                clearInterval(timer);
                console.log('[IssuerSync] Periodic sync stopped');
            }
        };
    }
}

module.exports = { IssuerSyncClient };
