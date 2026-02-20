#!/usr/bin/env node
/**
 * ═══════════════════════════════════════════════════════════════════
 * WINDI Phase 3: Complete Federation Flow Example
 * ═══════════════════════════════════════════════════════════════════
 * Demonstrates:
 *   1. Node registration & attestation
 *   2. Issuer registry sync
 *   3. Anchor publication
 * ═══════════════════════════════════════════════════════════════════
 */

const path = require('path');

// Import our libraries
const { WindiNodeIdentity } = require('../windi-node-identity-client/src/index.js');
const { IssuerSyncClient } = require('../issuer-registry-sync/src/node-sync-client.js');
const { AnchorPublisher } = require('../anchor-federation/src/node-anchor-publisher.js');

// ─── Configuration ──────────────────────────────────────────────────
const HUB_BASE = process.env.HUB_URL || 'http://localhost';
const NODE_ID = process.env.NODE_ID || 'node:example-corp-berlin-01';
const NODE_DOMAIN = process.env.NODE_DOMAIN || 'windi.example-corp.de';
const DATA_DIR = process.env.DATA_DIR || path.join(__dirname, 'data');

async function main() {
    console.log('═══════════════════════════════════════════════════');
    console.log('  WINDI Phase 3: Federation Flow Demo');
    console.log('═══════════════════════════════════════════════════');
    console.log('');
    console.log(`Node ID: ${NODE_ID}`);
    console.log(`Domain:  ${NODE_DOMAIN}`);
    console.log(`Hub:     ${HUB_BASE}`);
    console.log('');

    // ════════════════════════════════════════════════════════════════
    // STEP 1: Node Identity & Registration
    // ════════════════════════════════════════════════════════════════
    console.log('─── Step 1: Node Identity ─────────────────────────');

    const nodeIdentity = new WindiNodeIdentity({
        hubUrl: `${HUB_BASE}:8070`,
        nodeId: NODE_ID,
        domain: NODE_DOMAIN,
        roles: ['verifier', 'anchor_publisher'],
        keyPath: path.join(DATA_DIR, 'node-keypair.json')
    });

    try {
        const regResult = await nodeIdentity.fullRegistrationFlow({
            organization: 'Example Corporation',
            environment: 'demo'
        });
        console.log(`Certificate valid until: ${regResult.certificate.expires_at}`);
    } catch (err) {
        console.error('Registration failed:', err.message);
        if (err.status !== 409) { // Ignore "already registered"
            throw err;
        }
        console.log('Node already registered, continuing...');
    }

    // ════════════════════════════════════════════════════════════════
    // STEP 2: Issuer Registry Sync
    // ════════════════════════════════════════════════════════════════
    console.log('');
    console.log('─── Step 2: Issuer Registry Sync ──────────────────');

    const issuerSync = new IssuerSyncClient({
        hubUrl: `${HUB_BASE}:8071`,
        nodeId: NODE_ID,
        keyPair: nodeIdentity.keyPair,
        cachePath: path.join(DATA_DIR, 'issuer-cache')
    });

    try {
        const syncResult = await issuerSync.sync();
        console.log(`Synced ${syncResult.changes_applied} changes`);
        console.log(`Local cache: ${syncResult.issuer_count} issuers`);

        const trusted = issuerSync.getTrustedIssuers();
        console.log(`Trusted issuers: ${trusted.length}`);
        trusted.slice(0, 3).forEach(i => {
            console.log(`  - ${i.issuer_id}: ${i.display_name}`);
        });
    } catch (err) {
        console.error('Sync failed:', err.message);
    }

    // ════════════════════════════════════════════════════════════════
    // STEP 3: Anchor Publication
    // ════════════════════════════════════════════════════════════════
    console.log('');
    console.log('─── Step 3: Anchor Publication ────────────────────');

    const anchorPublisher = new AnchorPublisher({
        hubUrl: `${HUB_BASE}:8072`,
        nodeId: NODE_ID,
        keyPair: nodeIdentity.keyPair,
        receiptPath: path.join(DATA_DIR, 'anchor-receipts')
    });

    try {
        // Simulate some document hashes to anchor
        const documentHashes = [
            'a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456',
            'b2c3d4e5f67890123456789012345678901abcdef01234567890abcdef012345',
            'c3d4e5f678901234567890123456789012abcdef012345678901abcdef0123456'
        ];

        console.log(`Anchoring ${documentHashes.length} document hashes...`);

        const receipt = await anchorPublisher.anchor(documentHashes, {
            batch_type: 'demo',
            source: 'federation-flow-example'
        });

        console.log(`Anchor published!`);
        console.log(`  Anchor ID:  ${receipt.anchor_id}`);
        console.log(`  Sequence:   ${receipt.sequence_number}`);
        console.log(`  Root Hash:  ${receipt.hub_receipt.combined_root_hash.substring(0, 32)}...`);
    } catch (err) {
        console.error('Anchor publication failed:', err.message);
    }

    // ════════════════════════════════════════════════════════════════
    // Summary
    // ════════════════════════════════════════════════════════════════
    console.log('');
    console.log('═══════════════════════════════════════════════════');
    console.log('  Federation Flow Complete!');
    console.log('═══════════════════════════════════════════════════');
    console.log('');
    console.log('  Node Status:');
    console.log(`    Identity:  ${nodeIdentity.nodeId}`);
    console.log(`    Key:       ${nodeIdentity.getPublicKey().substring(0, 20)}...`);
    console.log('');
    console.log('  Issuer Sync:');
    const status = issuerSync.getStatus();
    console.log(`    Cursor:    ${status.cursor}`);
    console.log(`    Cached:    ${status.issuer_count} issuers`);
    console.log(`    Trusted:   ${status.trusted_count}`);
    console.log('');
    console.log('  Anchoring:');
    const anchorStatus = anchorPublisher.getStatus();
    console.log(`    Sequence:  ${anchorStatus.local_sequence}`);
    console.log('');
    console.log('  AI processes. Human decides. WINDI guarantees.');
}

main().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
});
