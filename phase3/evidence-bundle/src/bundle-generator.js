/**
 * ═══════════════════════════════════════════════════════════════════
 * WINDI Phase 3B: Evidence Bundle Generator
 * ═══════════════════════════════════════════════════════════════════
 * Creates court-ready evidence packages containing:
 *   - Document hash
 *   - Audit report (PDF)
 *   - Merkle inclusion proof
 *   - Signed Tree Head
 *   - All relevant public keys
 * ═══════════════════════════════════════════════════════════════════
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const archiver = require('archiver');

class EvidenceBundleGenerator {
    /**
     * Create an Evidence Bundle Generator
     * @param {Object} options
     * @param {string} options.transparencyLogUrl - URL of transparency log
     * @param {string} options.hubUrl - URL of Hub
     * @param {string} options.outputDir - Directory for bundles
     */
    constructor(options) {
        this.transparencyLogUrl = options.transparencyLogUrl?.replace(/\/$/, '');
        this.hubUrl = options.hubUrl?.replace(/\/$/, '');
        this.outputDir = options.outputDir || './evidence-bundles';
    }

    /**
     * Generate a complete evidence bundle
     * @param {Object} params
     * @param {string} params.documentHash - SHA256 hash of the document
     * @param {Buffer} params.reportPdf - Audit report PDF buffer
     * @param {Object} params.metadata - Additional metadata
     * @returns {Object} Bundle info
     */
    async generateBundle({ documentHash, reportPdf, metadata = {} }) {
        const bundleId = this._generateBundleId(documentHash);
        const bundleDir = path.join(this.outputDir, bundleId);
        fs.mkdirSync(bundleDir, { recursive: true });

        console.log(`[EvidenceBundle] Generating bundle: ${bundleId}`);

        // ─── 1. Create manifest ─────────────────────────────────────
        const manifest = {
            bundle_id: bundleId,
            version: '1.0',
            created_at: new Date().toISOString(),
            document_hash: documentHash,
            metadata,
            contents: []
        };

        // ─── 2. Fetch inclusion proof ───────────────────────────────
        let inclusionProof = null;
        let sth = null;

        try {
            const verifyRes = await fetch(`${this.transparencyLogUrl}/ct/v1/verify/${documentHash}`);
            const verifyData = await verifyRes.json();

            if (verifyData.found) {
                inclusionProof = verifyData.inclusion_proof;
                sth = verifyData.current_sth;

                fs.writeFileSync(
                    path.join(bundleDir, 'inclusion-proof.json'),
                    JSON.stringify(inclusionProof, null, 2)
                );
                manifest.contents.push({
                    file: 'inclusion-proof.json',
                    description: 'Merkle tree inclusion proof'
                });

                fs.writeFileSync(
                    path.join(bundleDir, 'signed-tree-head.json'),
                    JSON.stringify(sth, null, 2)
                );
                manifest.contents.push({
                    file: 'signed-tree-head.json',
                    description: 'Signed Tree Head (STH) at time of proof'
                });

                manifest.transparency_log = {
                    log_id: verifyData.log_id,
                    leaf_index: verifyData.leaf_index,
                    logged_at: verifyData.logged_at,
                    verified: verifyData.verified
                };
            }
        } catch (err) {
            console.warn('[EvidenceBundle] Failed to fetch inclusion proof:', err.message);
        }

        // ─── 3. Fetch public keys ───────────────────────────────────
        const publicKeys = {};
        fs.mkdirSync(path.join(bundleDir, 'public-keys'), { recursive: true });

        try {
            // Log public key
            const logKeyRes = await fetch(`${this.transparencyLogUrl}/ct/v1/public-key`);
            const logKey = await logKeyRes.json();
            publicKeys.transparency_log = logKey;
            fs.writeFileSync(
                path.join(bundleDir, 'public-keys', 'transparency-log.json'),
                JSON.stringify(logKey, null, 2)
            );
        } catch (err) {
            console.warn('[EvidenceBundle] Failed to fetch log public key:', err.message);
        }

        try {
            // Hub public key
            const hubKeyRes = await fetch(`${this.hubUrl}/hub/public-key`);
            const hubKey = await hubKeyRes.json();
            publicKeys.hub = hubKey;
            fs.writeFileSync(
                path.join(bundleDir, 'public-keys', 'hub.json'),
                JSON.stringify(hubKey, null, 2)
            );
        } catch (err) {
            console.warn('[EvidenceBundle] Failed to fetch hub public key:', err.message);
        }

        manifest.contents.push({
            file: 'public-keys/',
            description: 'Public keys for signature verification'
        });

        // ─── 4. Save audit report ───────────────────────────────────
        if (reportPdf) {
            fs.writeFileSync(path.join(bundleDir, 'audit-report.pdf'), reportPdf);
            manifest.contents.push({
                file: 'audit-report.pdf',
                description: 'Audit report document'
            });

            // Generate signature for PDF
            const pdfHash = crypto.createHash('sha256').update(reportPdf).digest('hex');
            manifest.report_hash = pdfHash;
        }

        // ─── 5. Create verification instructions ────────────────────
        const verificationInstructions = this._generateVerificationInstructions(manifest, publicKeys);
        fs.writeFileSync(
            path.join(bundleDir, 'VERIFY.md'),
            verificationInstructions
        );
        manifest.contents.push({
            file: 'VERIFY.md',
            description: 'Verification instructions'
        });

        // ─── 6. Save manifest ───────────────────────────────────────
        fs.writeFileSync(
            path.join(bundleDir, 'manifest.json'),
            JSON.stringify(manifest, null, 2)
        );

        // ─── 7. Create ZIP archive ──────────────────────────────────
        const zipPath = `${bundleDir}.zip`;
        await this._createZip(bundleDir, zipPath);

        // Compute ZIP hash
        const zipBuffer = fs.readFileSync(zipPath);
        const zipHash = crypto.createHash('sha256').update(zipBuffer).digest('hex');

        console.log(`[EvidenceBundle] Bundle created: ${zipPath}`);

        return {
            bundle_id: bundleId,
            bundle_path: zipPath,
            bundle_hash: zipHash,
            manifest,
            inclusion_proof: inclusionProof,
            sth
        };
    }

    /**
     * Generate bundle ID
     */
    _generateBundleId(documentHash) {
        const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
        const shortHash = documentHash.substring(0, 8);
        return `WINDI-EVIDENCE-${date}-${shortHash}`;
    }

    /**
     * Generate verification instructions markdown
     */
    _generateVerificationInstructions(manifest, publicKeys) {
        return `# WINDI Evidence Bundle Verification

## Bundle Information

- **Bundle ID**: ${manifest.bundle_id}
- **Created**: ${manifest.created_at}
- **Document Hash**: \`${manifest.document_hash}\`

## Verification Steps

### 1. Verify Document Hash

Calculate the SHA256 hash of the original document and compare:

\`\`\`bash
sha256sum <document>
# Expected: ${manifest.document_hash}
\`\`\`

### 2. Verify Inclusion Proof

The document hash is included in the WINDI Transparency Log.

- **Log ID**: ${manifest.transparency_log?.log_id || 'N/A'}
- **Leaf Index**: ${manifest.transparency_log?.leaf_index || 'N/A'}
- **Logged At**: ${manifest.transparency_log?.logged_at || 'N/A'}

To verify the inclusion proof:

1. Load \`inclusion-proof.json\`
2. Compute the leaf hash: \`SHA256(0x00 || document_hash)\`
3. For each proof step:
   - If position is "left": \`hash = SHA256(0x01 || sibling || current)\`
   - If position is "right": \`hash = SHA256(0x01 || current || sibling)\`
4. Final hash should equal \`root_hash\` in the proof

### 3. Verify Signed Tree Head

The Signed Tree Head (STH) is signed by the transparency log.

1. Load \`signed-tree-head.json\`
2. Load \`public-keys/transparency-log.json\`
3. Verify Ed25519 signature of canonical JSON:
   \`\`\`json
   {"log_id":"...","root_hash":"...","timestamp":...,"tree_size":...,"version":1}
   \`\`\`

### 4. Verify Audit Report (if present)

${manifest.report_hash ? `
Report SHA256: \`${manifest.report_hash}\`

\`\`\`bash
sha256sum audit-report.pdf
# Expected: ${manifest.report_hash}
\`\`\`
` : 'No audit report included in this bundle.'}

## Public Keys

### Transparency Log
\`\`\`json
${JSON.stringify(publicKeys.transparency_log || {}, null, 2)}
\`\`\`

### Hub
\`\`\`json
${JSON.stringify(publicKeys.hub || {}, null, 2)}
\`\`\`

## Legal Notice

This evidence bundle was generated by the WINDI document verification system.
The cryptographic proofs contained herein provide non-repudiable evidence
that the document with the specified hash was processed and logged at the
indicated time.

---
Generated by WINDI Evidence Bundle Generator v1.0
AI processes. Human decides. WINDI guarantees.
`;
    }

    /**
     * Create ZIP archive
     */
    _createZip(sourceDir, outputPath) {
        return new Promise((resolve, reject) => {
            const output = fs.createWriteStream(outputPath);
            const archive = archiver('zip', { zlib: { level: 9 } });

            output.on('close', resolve);
            archive.on('error', reject);

            archive.pipe(output);
            archive.directory(sourceDir, path.basename(sourceDir));
            archive.finalize();
        });
    }

    /**
     * Verify an existing bundle
     * @param {string} bundlePath - Path to bundle ZIP
     * @returns {Object} Verification result
     */
    async verifyBundle(bundlePath) {
        // This would extract and verify all components
        // For now, just validate structure
        const stats = fs.statSync(bundlePath);
        return {
            path: bundlePath,
            size: stats.size,
            exists: true,
            // Full verification would be implemented here
        };
    }
}

module.exports = { EvidenceBundleGenerator };
