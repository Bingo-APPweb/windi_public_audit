/**
 * ═══════════════════════════════════════════════════════════════════
 * WINDI Node Identity Client
 * ═══════════════════════════════════════════════════════════════════
 * Purpose: Client library for WINDI Nodes to register and attest with Hub
 * Principle: AI processes. Human decides. WINDI guarantees.
 * ═══════════════════════════════════════════════════════════════════
 */

const nacl = require('tweetnacl');
const naclUtil = require('tweetnacl-util');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

class WindiNodeIdentity {
    /**
     * Create a new WINDI Node Identity client
     * @param {Object} options
     * @param {string} options.hubUrl - URL of the Hub Node Registry (e.g., "http://hub.windi.local:8070")
     * @param {string} options.nodeId - Node identifier (e.g., "node:deutschebank-frankfurt-01")
     * @param {string} options.domain - Node domain (e.g., "windi.deutschebank.de")
     * @param {string[]} options.roles - Node roles (e.g., ["verifier", "anchor_publisher"])
     * @param {string} [options.keyPath] - Path to store/load keypair
     */
    constructor(options) {
        this.hubUrl = options.hubUrl?.replace(/\/$/, '');
        this.nodeId = options.nodeId;
        this.domain = options.domain;
        this.roles = options.roles || [];
        this.keyPath = options.keyPath;
        this.keyPair = null;
        this.certificate = null;
    }

    /**
     * Generate a new Ed25519 keypair for this node
     * @param {boolean} [persist=true] - Whether to save to keyPath
     * @returns {Object} { publicKey, secretKey } in base64
     */
    generateKeyPair(persist = true) {
        this.keyPair = nacl.sign.keyPair();

        const keys = {
            publicKey: naclUtil.encodeBase64(this.keyPair.publicKey),
            secretKey: naclUtil.encodeBase64(this.keyPair.secretKey)
        };

        if (persist && this.keyPath) {
            const keyData = {
                node_id: this.nodeId,
                public_key: keys.publicKey,
                secret_key: keys.secretKey,
                generated_at: new Date().toISOString()
            };
            fs.mkdirSync(path.dirname(this.keyPath), { recursive: true });
            fs.writeFileSync(this.keyPath, JSON.stringify(keyData, null, 2), { mode: 0o600 });
            console.log(`Keypair saved to ${this.keyPath}`);
        }

        return keys;
    }

    /**
     * Load existing keypair from keyPath
     * @returns {Object} { publicKey, secretKey } in base64
     */
    loadKeyPair() {
        if (!this.keyPath || !fs.existsSync(this.keyPath)) {
            throw new Error(`Keypair file not found: ${this.keyPath}`);
        }

        const keyData = JSON.parse(fs.readFileSync(this.keyPath, 'utf8'));
        this.keyPair = {
            publicKey: naclUtil.decodeBase64(keyData.public_key),
            secretKey: naclUtil.decodeBase64(keyData.secret_key)
        };

        return {
            publicKey: keyData.public_key,
            secretKey: keyData.secret_key
        };
    }

    /**
     * Get public key in base64 format
     * @returns {string}
     */
    getPublicKey() {
        if (!this.keyPair) {
            throw new Error('No keypair loaded. Call generateKeyPair() or loadKeyPair() first.');
        }
        return naclUtil.encodeBase64(this.keyPair.publicKey);
    }

    /**
     * Canonicalize JSON for signing (sorted keys, no whitespace)
     * @param {Object} obj
     * @returns {string}
     */
    canonicalJSON(obj) {
        return JSON.stringify(obj, Object.keys(obj).sort());
    }

    /**
     * Sign data with node's secret key
     * @param {Object|string} data
     * @returns {string} Base64-encoded signature
     */
    sign(data) {
        if (!this.keyPair) {
            throw new Error('No keypair loaded.');
        }
        const message = naclUtil.decodeUTF8(
            typeof data === 'string' ? data : this.canonicalJSON(data)
        );
        const signature = nacl.sign.detached(message, this.keyPair.secretKey);
        return naclUtil.encodeBase64(signature);
    }

    /**
     * Create an attestation payload
     * @param {Object} [extra] - Additional fields to include
     * @returns {Object} Attestation payload ready for signing
     */
    createAttestation(extra = {}) {
        return {
            node_id: this.nodeId,
            domain: this.domain,
            roles: this.roles,
            timestamp: new Date().toISOString(),
            ...extra
        };
    }

    /**
     * Create a signed attestation
     * @param {Object} [extra] - Additional fields to include
     * @returns {Object} { attestation, signature }
     */
    createSignedAttestation(extra = {}) {
        const attestation = this.createAttestation(extra);
        const signature = this.sign(attestation);
        return { attestation, signature };
    }

    /**
     * HTTP request helper
     * @private
     */
    async _request(method, path, body = null) {
        const url = `${this.hubUrl}${path}`;
        const options = {
            method,
            headers: { 'Content-Type': 'application/json' }
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
     * Register this node with the Hub
     * @param {Object} [metadata] - Optional metadata to include
     * @returns {Object} Registration result
     */
    async registerWithHub(metadata = {}) {
        if (!this.keyPair) {
            throw new Error('No keypair loaded. Call generateKeyPair() or loadKeyPair() first.');
        }

        return this._request('POST', '/nodes/register', {
            node_id: this.nodeId,
            domain: this.domain,
            public_key: this.getPublicKey(),
            roles: this.roles,
            metadata
        });
    }

    /**
     * Submit attestation to Hub and receive certificate
     * @returns {Object} Certificate from Hub
     */
    async attestWithHub() {
        const { attestation, signature } = this.createSignedAttestation();

        const result = await this._request('POST', '/nodes/attest', {
            node_id: this.nodeId,
            attestation,
            signature
        });

        if (result.certificate) {
            this.certificate = result.certificate;

            // Optionally save certificate
            if (this.keyPath) {
                const certPath = this.keyPath.replace(/\.json$/, '.cert.json');
                fs.writeFileSync(certPath, JSON.stringify(this.certificate, null, 2));
                console.log(`Certificate saved to ${certPath}`);
            }
        }

        return result;
    }

    /**
     * Fetch node's certificate from Hub
     * @returns {Object} Certificate
     */
    async fetchNodeCertificate() {
        const result = await this._request('GET', `/nodes/${this.nodeId}/certificate`);
        this.certificate = result;
        return result;
    }

    /**
     * Get node status from Hub
     * @returns {Object} Node status
     */
    async getNodeStatus() {
        return this._request('GET', `/nodes/${this.nodeId}`);
    }

    /**
     * Get Hub's public key (for verifying certificates)
     * @returns {Object} Hub public key info
     */
    async getHubPublicKey() {
        return this._request('GET', '/hub/public-key');
    }

    /**
     * Verify a certificate was signed by the Hub
     * @param {Object} certificate - Certificate to verify
     * @param {string} hubPublicKey - Hub's public key in base64
     * @returns {boolean}
     */
    verifyCertificate(certificate, hubPublicKey) {
        try {
            const { hub_signature, ...payload } = certificate;
            const message = naclUtil.decodeUTF8(this.canonicalJSON(payload));
            const signature = naclUtil.decodeBase64(hub_signature);
            const publicKey = naclUtil.decodeBase64(hubPublicKey);
            return nacl.sign.detached.verify(message, signature, publicKey);
        } catch (err) {
            console.error('Certificate verification error:', err.message);
            return false;
        }
    }

    /**
     * Full registration flow: generate keys, register, attest
     * @param {Object} [metadata] - Optional metadata
     * @returns {Object} { registration, certificate }
     */
    async fullRegistrationFlow(metadata = {}) {
        console.log(`\n[WINDI Node] Starting registration for ${this.nodeId}`);

        // Step 1: Generate or load keypair
        if (this.keyPath && fs.existsSync(this.keyPath)) {
            console.log('[WINDI Node] Loading existing keypair...');
            this.loadKeyPair();
        } else {
            console.log('[WINDI Node] Generating new keypair...');
            this.generateKeyPair();
        }
        console.log(`[WINDI Node] Public Key: ${this.getPublicKey().substring(0, 20)}...`);

        // Step 2: Register with Hub
        console.log('[WINDI Node] Registering with Hub...');
        let registration;
        try {
            registration = await this.registerWithHub(metadata);
            console.log(`[WINDI Node] Registration successful. Status: ${registration.node?.status}`);
        } catch (err) {
            if (err.status === 409) {
                console.log('[WINDI Node] Already registered, proceeding to attestation...');
                registration = { already_registered: true };
            } else {
                throw err;
            }
        }

        // Step 3: Attest and get certificate
        console.log('[WINDI Node] Submitting attestation...');
        const attestResult = await this.attestWithHub();
        console.log(`[WINDI Node] Attestation successful. Certificate expires: ${attestResult.certificate?.expires_at}`);

        return {
            registration,
            certificate: attestResult.certificate
        };
    }
}

module.exports = { WindiNodeIdentity };
