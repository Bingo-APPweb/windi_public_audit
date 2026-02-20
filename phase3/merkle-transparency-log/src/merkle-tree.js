/**
 * ═══════════════════════════════════════════════════════════════════
 * WINDI Phase 3B: Merkle Tree Implementation
 * ═══════════════════════════════════════════════════════════════════
 * RFC 6962 compliant Merkle Tree for transparency log
 * Provides: inclusion proofs, consistency proofs, signed tree heads
 * ═══════════════════════════════════════════════════════════════════
 */

const crypto = require('crypto');

// Domain separation prefixes (RFC 6962)
const LEAF_PREFIX = Buffer.from([0x00]);
const NODE_PREFIX = Buffer.from([0x01]);

class MerkleTree {
    constructor() {
        this.leaves = [];
        this.levels = [];
    }

    /**
     * Hash a leaf (with domain separation)
     */
    static hashLeaf(data) {
        const hash = crypto.createHash('sha256');
        hash.update(LEAF_PREFIX);
        hash.update(typeof data === 'string' ? Buffer.from(data, 'hex') : data);
        return hash.digest();
    }

    /**
     * Hash two nodes together (with domain separation)
     */
    static hashNodes(left, right) {
        const hash = crypto.createHash('sha256');
        hash.update(NODE_PREFIX);
        hash.update(left);
        hash.update(right);
        return hash.digest();
    }

    /**
     * Add a leaf to the tree
     * @param {string|Buffer} data - Leaf data (typically a document hash)
     * @returns {number} Leaf index
     */
    addLeaf(data) {
        const leafHash = MerkleTree.hashLeaf(data);
        this.leaves.push(leafHash);
        this._rebuild();
        return this.leaves.length - 1;
    }

    /**
     * Add multiple leaves at once
     * @param {Array} items - Array of leaf data
     * @returns {number[]} Array of leaf indices
     */
    addLeaves(items) {
        const startIndex = this.leaves.length;
        for (const item of items) {
            this.leaves.push(MerkleTree.hashLeaf(item));
        }
        this._rebuild();
        return items.map((_, i) => startIndex + i);
    }

    /**
     * Rebuild the tree from leaves
     */
    _rebuild() {
        if (this.leaves.length === 0) {
            this.levels = [];
            return;
        }

        this.levels = [[...this.leaves]];

        while (this.levels[this.levels.length - 1].length > 1) {
            const currentLevel = this.levels[this.levels.length - 1];
            const nextLevel = [];

            for (let i = 0; i < currentLevel.length; i += 2) {
                if (i + 1 < currentLevel.length) {
                    nextLevel.push(MerkleTree.hashNodes(currentLevel[i], currentLevel[i + 1]));
                } else {
                    // Odd number of nodes - promote the last one
                    nextLevel.push(currentLevel[i]);
                }
            }

            this.levels.push(nextLevel);
        }
    }

    /**
     * Get the root hash
     * @returns {Buffer|null}
     */
    getRoot() {
        if (this.levels.length === 0) return null;
        return this.levels[this.levels.length - 1][0];
    }

    /**
     * Get root hash as hex string
     * @returns {string|null}
     */
    getRootHex() {
        const root = this.getRoot();
        return root ? root.toString('hex') : null;
    }

    /**
     * Get tree size (number of leaves)
     * @returns {number}
     */
    getSize() {
        return this.leaves.length;
    }

    /**
     * Generate inclusion proof for a leaf
     * @param {number} index - Leaf index
     * @returns {Object} Inclusion proof
     */
    getInclusionProof(index) {
        if (index < 0 || index >= this.leaves.length) {
            throw new Error(`Invalid leaf index: ${index}`);
        }

        const proof = [];
        let currentIndex = index;

        for (let level = 0; level < this.levels.length - 1; level++) {
            const levelNodes = this.levels[level];
            const isRight = currentIndex % 2 === 1;
            const siblingIndex = isRight ? currentIndex - 1 : currentIndex + 1;

            if (siblingIndex < levelNodes.length) {
                proof.push({
                    hash: levelNodes[siblingIndex].toString('hex'),
                    position: isRight ? 'left' : 'right'
                });
            }

            currentIndex = Math.floor(currentIndex / 2);
        }

        return {
            leaf_index: index,
            tree_size: this.leaves.length,
            root_hash: this.getRootHex(),
            proof
        };
    }

    /**
     * Verify an inclusion proof
     * @param {string} leafHash - The leaf hash (hex)
     * @param {Object} proof - Inclusion proof object
     * @returns {boolean}
     */
    static verifyInclusionProof(leafHash, proof) {
        let currentHash = MerkleTree.hashLeaf(leafHash);

        for (const step of proof.proof) {
            const siblingHash = Buffer.from(step.hash, 'hex');
            if (step.position === 'left') {
                currentHash = MerkleTree.hashNodes(siblingHash, currentHash);
            } else {
                currentHash = MerkleTree.hashNodes(currentHash, siblingHash);
            }
        }

        return currentHash.toString('hex') === proof.root_hash;
    }

    /**
     * Generate consistency proof between two tree sizes
     * Proves that the tree at size1 is a prefix of tree at size2
     * @param {number} size1 - First tree size
     * @param {number} size2 - Second tree size (current)
     * @returns {Object} Consistency proof
     */
    getConsistencyProof(size1, size2 = this.leaves.length) {
        if (size1 <= 0 || size1 > size2 || size2 > this.leaves.length) {
            throw new Error(`Invalid sizes: ${size1}, ${size2}`);
        }

        // Build tree at size1
        const tree1 = new MerkleTree();
        tree1.leaves = this.leaves.slice(0, size1);
        tree1._rebuild();

        const proof = [];

        // Simple consistency proof (collect hashes needed to reconstruct)
        // This is a simplified implementation
        let m = size1;
        let n = size2;

        while (m < n) {
            const subtreeSize = 1 << Math.floor(Math.log2(n - m));
            const subtreeStart = m;
            const subtreeEnd = Math.min(m + subtreeSize, n);

            // Get subtree root
            const subtree = new MerkleTree();
            subtree.leaves = this.leaves.slice(subtreeStart, subtreeEnd);
            subtree._rebuild();

            if (subtree.getRoot()) {
                proof.push({
                    hash: subtree.getRootHex(),
                    range: [subtreeStart, subtreeEnd]
                });
            }

            m = subtreeEnd;
        }

        return {
            size1,
            size2,
            root1: tree1.getRootHex(),
            root2: this.getRootHex(),
            proof
        };
    }

    /**
     * Export tree state for persistence
     * @returns {Object}
     */
    export() {
        return {
            leaves: this.leaves.map(l => l.toString('hex')),
            size: this.leaves.length,
            root: this.getRootHex()
        };
    }

    /**
     * Import tree state
     * @param {Object} state
     */
    static import(state) {
        const tree = new MerkleTree();
        tree.leaves = state.leaves.map(h => Buffer.from(h, 'hex'));
        tree._rebuild();
        return tree;
    }
}

/**
 * Signed Tree Head (STH) - represents a snapshot of the tree
 */
class SignedTreeHead {
    /**
     * Create a Signed Tree Head
     * @param {Object} options
     * @param {number} options.treeSize - Number of leaves
     * @param {string} options.rootHash - Root hash (hex)
     * @param {number} options.timestamp - Unix timestamp (ms)
     * @param {string} options.logId - Log identifier
     */
    constructor({ treeSize, rootHash, timestamp, logId }) {
        this.version = 1;
        this.log_id = logId;
        this.tree_size = treeSize;
        this.root_hash = rootHash;
        this.timestamp = timestamp || Date.now();
    }

    /**
     * Get the data to be signed
     * @returns {string} Canonical JSON
     */
    getSignatureInput() {
        const obj = {
            log_id: this.log_id,
            root_hash: this.root_hash,
            timestamp: this.timestamp,
            tree_size: this.tree_size,
            version: this.version
        };
        return JSON.stringify(obj, Object.keys(obj).sort());
    }

    /**
     * Convert to JSON with signature
     * @param {string} signature - Base64 signature
     * @returns {Object}
     */
    toJSON(signature) {
        return {
            version: this.version,
            log_id: this.log_id,
            tree_size: this.tree_size,
            root_hash: this.root_hash,
            timestamp: this.timestamp,
            timestamp_iso: new Date(this.timestamp).toISOString(),
            signature
        };
    }
}

module.exports = { MerkleTree, SignedTreeHead };
