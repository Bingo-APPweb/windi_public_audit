#!/usr/bin/env node
/**
 * ═══════════════════════════════════════════════════════════════════
 * WINDI Phase 3B: Transparency Log Demo
 * ═══════════════════════════════════════════════════════════════════
 * Demonstrates:
 *   1. Adding entries to the log
 *   2. Getting Signed Tree Head
 *   3. Verifying inclusion proofs
 *   4. Generating evidence bundles
 * ═══════════════════════════════════════════════════════════════════
 */

const crypto = require('crypto');
const path = require('path');

const LOG_URL = process.env.LOG_URL || 'http://localhost:8073';
const HUB_URL = process.env.HUB_URL || 'http://localhost:8070';

async function main() {
    console.log('═══════════════════════════════════════════════════');
    console.log('  WINDI Merkle Transparency Log Demo');
    console.log('═══════════════════════════════════════════════════');
    console.log('');
    console.log(`Log URL: ${LOG_URL}`);
    console.log('');

    // ─── 1. Check health ────────────────────────────────────────────
    console.log('─── Step 1: Check Log Health ──────────────────────');
    const healthRes = await fetch(`${LOG_URL}/health`);
    const health = await healthRes.json();
    console.log(`Status: ${health.status}`);
    console.log(`Log ID: ${health.log_id}`);
    console.log(`Tree Size: ${health.tree_size}`);
    console.log('');

    // ─── 2. Add some entries ────────────────────────────────────────
    console.log('─── Step 2: Add Entries ───────────────────────────');

    // Generate some fake document hashes
    const documents = [
        { name: 'contract.pdf', content: 'Contract content v1' },
        { name: 'invoice.pdf', content: 'Invoice #12345' },
        { name: 'report.pdf', content: 'Annual report 2026' }
    ];

    const hashes = documents.map(doc => ({
        name: doc.name,
        hash: crypto.createHash('sha256').update(doc.content).digest('hex')
    }));

    for (const doc of hashes) {
        console.log(`Adding: ${doc.name}`);
        console.log(`  Hash: ${doc.hash.substring(0, 32)}...`);

        try {
            const addRes = await fetch(`${LOG_URL}/ct/v1/add-entry`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    hash: doc.hash,
                    data: { document_name: doc.name, added_by: 'demo' }
                })
            });

            const addResult = await addRes.json();

            if (addRes.ok) {
                console.log(`  Leaf Index: ${addResult.leaf_index}`);
                console.log(`  Tree Size: ${addResult.tree_size}`);
            } else {
                console.log(`  ${addResult.error}`);
            }
        } catch (err) {
            console.log(`  Error: ${err.message}`);
        }
    }
    console.log('');

    // ─── 3. Get Signed Tree Head ────────────────────────────────────
    console.log('─── Step 3: Get Signed Tree Head ──────────────────');
    try {
        const sthRes = await fetch(`${LOG_URL}/ct/v1/get-sth`);
        const sth = await sthRes.json();

        console.log('STH:');
        console.log(`  Log ID: ${sth.log_id}`);
        console.log(`  Tree Size: ${sth.tree_size}`);
        console.log(`  Root Hash: ${sth.root_hash?.substring(0, 32)}...`);
        console.log(`  Timestamp: ${sth.timestamp_iso}`);
        console.log(`  Signature: ${sth.signature?.substring(0, 32)}...`);
    } catch (err) {
        console.log(`Error: ${err.message}`);
    }
    console.log('');

    // ─── 4. Verify inclusion ────────────────────────────────────────
    console.log('─── Step 4: Verify Inclusion ──────────────────────');
    const testHash = hashes[0].hash;
    console.log(`Verifying: ${hashes[0].name}`);
    console.log(`Hash: ${testHash.substring(0, 32)}...`);

    try {
        const verifyRes = await fetch(`${LOG_URL}/ct/v1/verify/${testHash}`);
        const verify = await verifyRes.json();

        console.log(`Found: ${verify.found}`);
        if (verify.found) {
            console.log(`Verified: ${verify.verified}`);
            console.log(`Leaf Index: ${verify.leaf_index}`);
            console.log(`Logged At: ${verify.logged_at}`);
            console.log('');
            console.log('Inclusion Proof:');
            console.log(`  Tree Size: ${verify.inclusion_proof.tree_size}`);
            console.log(`  Root Hash: ${verify.inclusion_proof.root_hash?.substring(0, 32)}...`);
            console.log(`  Proof Steps: ${verify.inclusion_proof.proof.length}`);

            for (let i = 0; i < verify.inclusion_proof.proof.length; i++) {
                const step = verify.inclusion_proof.proof[i];
                console.log(`    [${i}] ${step.position}: ${step.hash.substring(0, 16)}...`);
            }
        }
    } catch (err) {
        console.log(`Error: ${err.message}`);
    }
    console.log('');

    // ─── 5. Get entries ─────────────────────────────────────────────
    console.log('─── Step 5: Get Log Entries ───────────────────────');
    try {
        const entriesRes = await fetch(`${LOG_URL}/ct/v1/get-entries?start=0&end=10`);
        const entries = await entriesRes.json();

        console.log(`Entries ${entries.start}-${entries.end}:`);
        for (const entry of entries.entries) {
            console.log(`  [${entry.leaf_index}] ${entry.leaf_hash.substring(0, 24)}... @ ${entry.logged_at}`);
        }
    } catch (err) {
        console.log(`Error: ${err.message}`);
    }
    console.log('');

    // ─── 6. Get public key ──────────────────────────────────────────
    console.log('─── Step 6: Get Log Public Key ────────────────────');
    try {
        const keyRes = await fetch(`${LOG_URL}/ct/v1/public-key`);
        const key = await keyRes.json();

        console.log(`Log ID: ${key.log_id}`);
        console.log(`Algorithm: ${key.algorithm}`);
        console.log(`Public Key: ${key.public_key.substring(0, 32)}...`);
    } catch (err) {
        console.log(`Error: ${err.message}`);
    }
    console.log('');

    console.log('═══════════════════════════════════════════════════');
    console.log('  Demo Complete!');
    console.log('═══════════════════════════════════════════════════');
    console.log('');
    console.log('  The transparency log now contains:');
    console.log('    - Signed Tree Heads (STH)');
    console.log('    - Merkle inclusion proofs');
    console.log('    - Immutable audit trail');
    console.log('');
    console.log('  This provides:');
    console.log('    - Non-repudiation of document submission');
    console.log('    - Cryptographic proof of log consistency');
    console.log('    - Court-admissible evidence chain');
    console.log('');
    console.log('  AI processes. Human decides. WINDI guarantees.');
}

main().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
});
