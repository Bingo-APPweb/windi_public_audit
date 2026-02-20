#!/usr/bin/env node
/**
 * ═══════════════════════════════════════════════════════════════════
 * WINDI Node Registration Example
 * ═══════════════════════════════════════════════════════════════════
 * Usage: node register-node.js
 *
 * This example demonstrates the full registration flow for a WINDI Node.
 * ═══════════════════════════════════════════════════════════════════
 */

const path = require('path');
const { WindiNodeIdentity } = require('../windi-node-identity-client/src/index.js');

async function main() {
    // ─── Configuration ──────────────────────────────────────────────
    const config = {
        hubUrl: process.env.HUB_URL || 'http://localhost:8070',
        nodeId: process.env.NODE_ID || 'node:example-org-munich-01',
        domain: process.env.NODE_DOMAIN || 'windi.example-org.de',
        roles: ['verifier', 'anchor_publisher'],
        keyPath: path.join(__dirname, 'keys', 'node-keypair.json')
    };

    console.log('═══════════════════════════════════════════════════');
    console.log('  WINDI Node Registration Example');
    console.log('═══════════════════════════════════════════════════');
    console.log('');
    console.log('Configuration:');
    console.log(`  Hub URL:  ${config.hubUrl}`);
    console.log(`  Node ID:  ${config.nodeId}`);
    console.log(`  Domain:   ${config.domain}`);
    console.log(`  Roles:    ${config.roles.join(', ')}`);
    console.log(`  Key Path: ${config.keyPath}`);
    console.log('');

    // ─── Create Client ──────────────────────────────────────────────
    const node = new WindiNodeIdentity(config);

    try {
        // ─── Full Registration Flow ─────────────────────────────────
        const result = await node.fullRegistrationFlow({
            organization: 'Example Organization',
            contact: 'admin@example-org.de',
            environment: 'production'
        });

        console.log('');
        console.log('═══════════════════════════════════════════════════');
        console.log('  Registration Complete!');
        console.log('═══════════════════════════════════════════════════');
        console.log('');
        console.log('Certificate:');
        console.log(JSON.stringify(result.certificate, null, 2));
        console.log('');
        console.log('Next Steps:');
        console.log('  1. Store the certificate securely');
        console.log('  2. Include it in federation requests');
        console.log('  3. Renew before expiration');
        console.log('');

        // ─── Verify Certificate ─────────────────────────────────────
        console.log('Verifying certificate...');
        const hubKey = await node.getHubPublicKey();
        const valid = node.verifyCertificate(result.certificate, hubKey.public_key);
        console.log(`Certificate valid: ${valid}`);

    } catch (err) {
        console.error('');
        console.error('Registration failed:', err.message);
        if (err.response) {
            console.error('Details:', JSON.stringify(err.response, null, 2));
        }
        process.exit(1);
    }
}

main();
