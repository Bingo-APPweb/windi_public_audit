/**
 * ═══════════════════════════════════════════════════════════════════
 * WINDI Phase 3: Node Anchor Publisher
 * ═══════════════════════════════════════════════════════════════════
 * Purpose: Publish transparency anchors from node to Hub
 * Principle: AI processes. Human decides. WINDI guarantees.
 * ═══════════════════════════════════════════════════════════════════
 */

const nacl = require('tweetnacl');
const naclUtil = require('tweetnacl-util');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

class AnchorPublisher {
    /**
     * Create an Anchor Publisher
     * @param {Object} options
     * @param {string} options.hubUrl - Hub anchor receiver URL
     * @param {string} options.nodeId - This node's ID
     * @param {Object} options.keyPair - Node's Ed25519 keypair
     * @param {string} options.receiptPath - Path to store anchor receipts
     */
    constructor(options) {
        this.hubUrl = options.hubUrl?.replace(/\/$/, '');
        this.nodeId = options.nodeId;
        this.keyPair = options.keyPair;
        this.receiptPath = options.receiptPath || './anchor-receipts';

        // Local sequence tracking
        this.localSequence = this._loadSequence();
    }

    /**
     * Load local sequence number
     */
    _loadSequence() {
        const seqFile = path.join(this.receiptPath, 'sequence.json');
        if (fs.existsSync(seqFile)) {
            try {
                const data = JSON.parse(fs.readFileSync(seqFile, 'utf8'));
                return data.sequence || 0;
            } catch {
                return 0;
            }
        }
        return 0;
    }

    /**
     * Save local sequence number
     */
    _saveSequence() {
        fs.mkdirSync(this.receiptPath, { recursive: true });
        const seqFile = path.join(this.receiptPath, 'sequence.json');
        fs.writeFileSync(seqFile, JSON.stringify({ sequence: this.localSequence }));
    }

    /**
     * Compute SHA256 hash
     */
    sha256(data) {
        return crypto.createHash('sha256').update(data).digest('hex');
    }

    /**
     * Canonical JSON
     */
    canonicalJSON(obj) {
        return JSON.stringify(obj, Object.keys(obj).sort());
    }

    /**
     * Sign data with node key
     */
    sign(data) {
        const message = naclUtil.decodeUTF8(
            typeof data === 'string' ? data : this.canonicalJSON(data)
        );
        const signature = nacl.sign.detached(message, this.keyPair.secretKey);
        return naclUtil.encodeBase64(signature);
    }

    /**
     * Create auth headers for Hub
     */
    _createAuthHeaders(requestPath) {
        const timestamp = new Date().toISOString();
        const payload = {
            node_id: this.nodeId,
            timestamp,
            path: requestPath
        };

        const signature = this.sign(payload);

        return {
            'Content-Type': 'application/json',
            'X-Node-Id': this.nodeId,
            'X-Node-Signature': signature,
            'X-Request-Timestamp': timestamp
        };
    }

    /**
     * Make authenticated request to Hub
     */
    async _request(method, requestPath, body = null) {
        const url = `${this.hubUrl}${requestPath}`;
        const options = {
            method,
            headers: this._createAuthHeaders(requestPath)
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
     * Create an anchor for a set of document hashes
     * @param {string[]} documentHashes - Array of document hashes
     * @param {Object} metadata - Optional metadata
     * @returns {Object} Anchor object (not yet published)
     */
    createAnchor(documentHashes, metadata = {}) {
        // Compute combined root hash (Merkle-like aggregation)
        const sortedHashes = [...documentHashes].sort();
        const combined = sortedHashes.join('');
        const combinedRootHash = this.sha256(combined);

        this.localSequence++;

        const anchor = {
            combined_root_hash: combinedRootHash,
            document_hashes: sortedHashes,
            document_count: sortedHashes.length,
            timestamp: new Date().toISOString(),
            node_id: this.nodeId,
            sequence: this.localSequence,
            metadata
        };

        return anchor;
    }

    /**
     * Publish an anchor to the Hub
     * @param {Object} anchor - Anchor object from createAnchor()
     * @returns {Object} Hub receipt
     */
    async publishAnchor(anchor) {
        console.log(`[AnchorPublisher] Publishing anchor: ${anchor.combined_root_hash.substring(0, 16)}...`);

        // Sign the anchor
        const signature = this.sign(anchor);

        // Publish to Hub
        const result = await this._request('POST', '/anchors', {
            anchor,
            signature
        });

        // Save receipt locally
        this._saveReceipt(anchor, result);
        this._saveSequence();

        console.log(`[AnchorPublisher] Published. Hub sequence: ${result.sequence_number}`);

        return result;
    }

    /**
     * Create and publish an anchor in one step
     * @param {string[]} documentHashes - Array of document hashes
     * @param {Object} metadata - Optional metadata
     * @returns {Object} Hub receipt
     */
    async anchor(documentHashes, metadata = {}) {
        const anchorObj = this.createAnchor(documentHashes, metadata);
        return this.publishAnchor(anchorObj);
    }

    /**
     * Save receipt to disk
     */
    _saveReceipt(anchor, hubResult) {
        fs.mkdirSync(this.receiptPath, { recursive: true });

        const receipt = {
            anchor,
            hub_receipt: hubResult.hub_receipt,
            published_at: new Date().toISOString()
        };

        const filename = `anchor-${hubResult.sequence_number}-${anchor.combined_root_hash.substring(0, 8)}.json`;
        const filepath = path.join(this.receiptPath, filename);

        fs.writeFileSync(filepath, JSON.stringify(receipt, null, 2));
        console.log(`[AnchorPublisher] Receipt saved: ${filename}`);
    }

    /**
     * Verify a document hash is anchored
     * @param {string} hash - Document hash
     * @returns {Object} Verification result
     */
    async verifyHash(hash) {
        return this._request('GET', `/anchors/verify/${hash}`);
    }

    /**
     * Get Hub's public key
     */
    async getHubKey() {
        return this._request('GET', '/anchors/hub-key');
    }

    /**
     * List recent anchors from Hub
     * @param {number} limit - Max anchors to return
     */
    async listAnchors(limit = 50) {
        return this._request('GET', `/anchors?limit=${limit}`);
    }

    /**
     * Get anchor by ID
     * @param {string} anchorId - Anchor UUID
     */
    async getAnchor(anchorId) {
        return this._request('GET', `/anchors/${anchorId}`);
    }

    /**
     * Verify Hub receipt signature
     * @param {Object} receipt - Hub receipt
     * @param {string} hubPublicKey - Hub's public key in base64
     */
    verifyHubReceipt(receipt, hubPublicKey) {
        try {
            const { hub_signature, ...payload } = receipt;
            const message = naclUtil.decodeUTF8(this.canonicalJSON(payload));
            const signature = naclUtil.decodeBase64(hub_signature);
            const publicKey = naclUtil.decodeBase64(hubPublicKey);
            return nacl.sign.detached.verify(message, signature, publicKey);
        } catch (err) {
            console.error('[AnchorPublisher] Receipt verification error:', err.message);
            return false;
        }
    }

    /**
     * Get publisher status
     */
    getStatus() {
        return {
            node_id: this.nodeId,
            hub_url: this.hubUrl,
            local_sequence: this.localSequence,
            receipt_path: this.receiptPath
        };
    }
}

module.exports = { AnchorPublisher };
