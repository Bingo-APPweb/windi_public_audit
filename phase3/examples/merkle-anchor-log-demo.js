#!/usr/bin/env node
/**
 * ═══════════════════════════════════════════════════════════════════
 * WINDI Phase 3B: Merkle Anchor Log Demo
 * ═══════════════════════════════════════════════════════════════════
 * Demonstrates the CT-style Merkle Transparency Log:
 *   1. Adding anchors to the log
 *   2. Getting Signed Tree Head (STH)
 *   3. Verifying inclusion proofs
 *   4. Querying consistency proofs
 *
 * Port: 8074
 * ═══════════════════════════════════════════════════════════════════
 */

const crypto = require('crypto');

const LOG_URL = process.env.LOG_URL || 'http://localhost:8074';

async function main() {
    console.log('═══════════════════════════════════════════════════');
    console.log('  WINDI Merkle Anchor Log Demo (CT-Style)');
    console.log('═══════════════════════════════════════════════════');
    console.log('');
    console.log(`Log URL: ${LOG_URL}`);
    console.log('');

    // ─── 1. Check health ────────────────────────────────────────────
    console.log('─── Step 1: Check Log Health ──────────────────────');
    try {
        const healthRes = await fetch(`${LOG_URL}/health`);
        const health = await healthRes.json();
        console.log(`Status: ${health.status}`);
        console.log(`Log ID: ${health.log_id}`);
        console.log(`Tree Size: ${health.tree_size}`);
        console.log(`Root Hash: ${health.root_hash?.substring(0, 32) || '(empty)'}...`);
    } catch (err) {
        console.log(`Error: ${err.message}`);
        console.log('Make sure the merkle-anchor-log service is running.');
        process.exit(1);
    }
    console.log('');

    // ─── 2. Add anchors ─────────────────────────────────────────────
    console.log('─── Step 2: Add Anchors ───────────────────────────');

    // Generate fake combined_root_hash values (simulating document anchors)
    const anchors = [
        { name: 'contract-2026-001', content: 'Contract hash content v1' },
        { name: 'invoice-12345', content: 'Invoice data hash' },
        { name: 'audit-report-Q1', content: 'Q1 2026 audit report hash' }
    ];

    const results = [];
    for (const anchor of anchors) {
        const combined_root_hash = crypto.createHash('sha256')
            .update(anchor.content + Date.now())
            .digest('hex');

        console.log(`Adding: ${anchor.name}`);
        console.log(`  combined_root_hash: ${combined_root_hash.substring(0, 32)}...`);

        try {
            const addRes = await fetch(`${LOG_URL}/anchors`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    combined_root_hash,
                    node_id: 'demo-node-01',
                    metadata: { document_name: anchor.name, demo: true }
                })
            });

            const result = await addRes.json();

            if (addRes.ok) {
                console.log(`  leaf_index: ${result.leaf_index}`);
                console.log(`  leaf_hash: ${result.leaf_hash.substring(0, 24)}...`);
                console.log(`  tree_size: ${result.tree_size}`);
                results.push({ ...anchor, combined_root_hash, ...result });
            } else {
                console.log(`  Error: ${result.error}`);
            }
        } catch (err) {
            console.log(`  Error: ${err.message}`);
        }
    }
    console.log('');

    // ─── 3. Get Signed Tree Head ────────────────────────────────────
    console.log('─── Step 3: Get Signed Tree Head (STH) ────────────');
    try {
        const sthRes = await fetch(`${LOG_URL}/sth`);
        const sth = await sthRes.json();

        console.log('STH:');
        console.log(`  log_id: ${sth.log_id}`);
        console.log(`  tree_size: ${sth.tree_size}`);
        console.log(`  root_hash: ${sth.root_hash?.substring(0, 32)}...`);
        console.log(`  timestamp: ${sth.timestamp}`);
        console.log(`  signature_alg: ${sth.signature_alg}`);
        console.log(`  signature: ${sth.signature?.substring(0, 32)}...`);
        console.log(`  key_id: ${sth.key_id}`);
    } catch (err) {
        console.log(`Error: ${err.message}`);
    }
    console.log('');

    // ─── 4. Verify an anchor (full verification) ────────────────────
    if (results.length > 0) {
        console.log('─── Step 4: Verify Anchor ─────────────────────────');
        const testAnchor = results[0];
        console.log(`Verifying: ${testAnchor.name}`);
        console.log(`  combined_root_hash: ${testAnchor.combined_root_hash.substring(0, 32)}...`);

        try {
            const verifyRes = await fetch(`${LOG_URL}/verify/${testAnchor.combined_root_hash}`);
            const verify = await verifyRes.json();

            console.log(`  found: ${verify.found}`);
            if (verify.found) {
                console.log(`  verified: ${verify.verified}`);
                console.log(`  leaf.index: ${verify.leaf.index}`);
                console.log(`  leaf.hash: ${verify.leaf.hash.substring(0, 24)}...`);
                console.log(`  leaf.timestamp: ${verify.leaf.timestamp}`);
                console.log('');
                console.log('  Inclusion Proof:');
                console.log(`    tree_size: ${verify.inclusion_proof.tree_size}`);
                console.log(`    root_hash: ${verify.inclusion_proof.root_hash.substring(0, 24)}...`);
                console.log(`    audit_path: [${verify.inclusion_proof.audit_path.length} hashes]`);
                for (let i = 0; i < verify.inclusion_proof.audit_path.length; i++) {
                    console.log(`      [${i}]: ${verify.inclusion_proof.audit_path[i].substring(0, 24)}...`);
                }
            }
        } catch (err) {
            console.log(`Error: ${err.message}`);
        }
        console.log('');
    }

    // ─── 5. Get inclusion proof directly ────────────────────────────
    if (results.length > 0) {
        console.log('─── Step 5: Get Inclusion Proof ───────────────────');
        const leafIndex = results[results.length - 1].leaf_index;
        console.log(`Getting proof for leaf_index: ${leafIndex}`);

        try {
            const proofRes = await fetch(`${LOG_URL}/proof/inclusion?leaf_index=${leafIndex}`);
            const proof = await proofRes.json();

            console.log(`  log_id: ${proof.log_id}`);
            console.log(`  leaf_index: ${proof.leaf_index}`);
            console.log(`  tree_size: ${proof.tree_size}`);
            console.log(`  root_hash: ${proof.root_hash.substring(0, 24)}...`);
            console.log(`  audit_path length: ${proof.audit_path.length}`);
        } catch (err) {
            console.log(`Error: ${err.message}`);
        }
        console.log('');
    }

    // ─── 6. Lookup by combined_root_hash ────────────────────────────
    if (results.length > 0) {
        console.log('─── Step 6: Lookup by Hash ────────────────────────');
        const testHash = results[0].combined_root_hash;
        console.log(`Looking up: ${testHash.substring(0, 32)}...`);

        try {
            const lookupRes = await fetch(`${LOG_URL}/lookup?combined_root_hash=${testHash}`);
            const lookup = await lookupRes.json();

            console.log(`  found: ${lookup.found}`);
            if (lookup.found) {
                console.log(`  leaf_index: ${lookup.leaf_index}`);
                console.log(`  leaf_hash: ${lookup.leaf_hash.substring(0, 24)}...`);
                console.log(`  node_id: ${lookup.node_id}`);
                console.log(`  timestamp: ${lookup.timestamp}`);
            }
        } catch (err) {
            console.log(`Error: ${err.message}`);
        }
        console.log('');
    }

    // ─── 7. List leaves ─────────────────────────────────────────────
    console.log('─── Step 7: List Leaves ───────────────────────────');
    try {
        const leavesRes = await fetch(`${LOG_URL}/leaves?start=0&limit=10`);
        const leaves = await leavesRes.json();

        console.log(`Log ID: ${leaves.log_id}`);
        console.log(`Tree Size: ${leaves.tree_size}`);
        console.log(`Returned: ${leaves.count} leaves`);
        console.log('');
        for (const leaf of leaves.leaves) {
            console.log(`  [${leaf.leaf_index}] ${leaf.leaf_hash.substring(0, 20)}... @ ${leaf.ts}`);
        }
    } catch (err) {
        console.log(`Error: ${err.message}`);
    }
    console.log('');

    // ─── 8. Get public key ──────────────────────────────────────────
    console.log('─── Step 8: Get Log Public Key ────────────────────');
    try {
        const keyRes = await fetch(`${LOG_URL}/pubkey`);
        const key = await keyRes.json();

        console.log(`log_id: ${key.log_id}`);
        console.log(`key_id: ${key.key_id}`);
        console.log(`algorithm: ${key.algorithm}`);
        console.log(`public_key: ${key.public_key.substring(0, 32)}...`);
    } catch (err) {
        console.log(`Error: ${err.message}`);
    }
    console.log('');

    // ─── 9. STH History ─────────────────────────────────────────────
    console.log('─── Step 9: STH History ───────────────────────────');
    try {
        const histRes = await fetch(`${LOG_URL}/sth/history?limit=5`);
        const history = await histRes.json();

        console.log(`Log ID: ${history.log_id}`);
        console.log(`Recent STHs:`);
        for (const sth of history.sths) {
            console.log(`  size=${sth.tree_size} root=${sth.root_hash.substring(0, 16)}... @ ${sth.ts}`);
        }
    } catch (err) {
        console.log(`Error: ${err.message}`);
    }
    console.log('');

    // ─── Summary ────────────────────────────────────────────────────
    console.log('═══════════════════════════════════════════════════');
    console.log('  Demo Complete!');
    console.log('═══════════════════════════════════════════════════');
    console.log('');
    console.log('  The CT-style Merkle Transparency Log provides:');
    console.log('');
    console.log('    - Append-only Merkle tree structure');
    console.log('    - Signed Tree Heads (STH) with Ed25519');
    console.log('    - RFC 6962 compliant inclusion proofs');
    console.log('    - Consistency proofs for log extension');
    console.log('    - Immutable, cryptographically verifiable audit trail');
    console.log('');
    console.log('  This enables:');
    console.log('    - Third-party auditing without log cooperation');
    console.log('    - Detection of log misbehavior');
    console.log('    - Court-admissible evidence chain');
    console.log('    - Proof of non-repudiation');
    console.log('');
    console.log('  AI processes. Human decides. WINDI guarantees.');
    console.log('');
}

main().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
});
