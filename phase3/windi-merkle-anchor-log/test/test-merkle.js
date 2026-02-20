#!/usr/bin/env node
/**
 * ═══════════════════════════════════════════════════════════════════
 * WINDI Merkle Anchor Log — Unit Tests
 * ═══════════════════════════════════════════════════════════════════
 * Tests for merkle tree operations and proof verification
 * ═══════════════════════════════════════════════════════════════════
 */

const { stableStringify } = require('../src/canonical.js');
const { leafHash, nodeHash, hex } = require('../src/hash.js');
const { merkleRoot } = require('../src/merkle.js');
const { inclusionProof, consistencyProof, hashSubtree, largestPowerOfTwoLessThan } = require('../src/proofs.js');

let passed = 0;
let failed = 0;

function assert(condition, message) {
    if (condition) {
        passed++;
        console.log(`  ✓ ${message}`);
    } else {
        failed++;
        console.log(`  ✗ ${message}`);
    }
}

function section(name) {
    console.log(`\n─── ${name} ───`);
}

// ─── Test stableStringify (canonical JSON) ─────────────────────────
section('stableStringify');

const obj1 = { b: 2, a: 1 };
const obj2 = { a: 1, b: 2 };
assert(stableStringify(obj1) === stableStringify(obj2), 'Key order normalized');
assert(stableStringify(obj1) === '{"a":1,"b":2}', 'Produces canonical form');

const nested = { z: { b: 2, a: 1 }, y: [3, 2, 1] };
const nestedResult = stableStringify(nested);
assert(nestedResult.includes('"y":[3,2,1]'), 'Arrays preserved');
assert(nestedResult.indexOf('"y"') < nestedResult.indexOf('"z"'), 'Keys sorted');

// ─── Test leafHash ─────────────────────────────────────────────────
section('leafHash');

const lh1 = leafHash('test');
assert(lh1.length === 32, 'Returns 32-byte Buffer');
assert(hex(lh1).length === 64, 'Hex is 64 chars');

const lh2 = leafHash('test');
assert(hex(lh1) === hex(lh2), 'Same input produces same hash');

const lh3 = leafHash('different');
assert(hex(lh1) !== hex(lh3), 'Different input produces different hash');

// ─── Test nodeHash ─────────────────────────────────────────────────
section('nodeHash');

const nh = nodeHash(lh1, lh3);
assert(nh.length === 32, 'Node hash is 32 bytes');
assert(hex(nh) !== hex(lh1), 'Node hash differs from inputs');

const reverseNh = nodeHash(lh3, lh1);
assert(hex(nh) !== hex(reverseNh), 'Order matters for node hashing');

// ─── Test largestPowerOfTwoLessThan ────────────────────────────────
section('largestPowerOfTwoLessThan');

assert(largestPowerOfTwoLessThan(2) === 1, 'k(2) = 1');
assert(largestPowerOfTwoLessThan(3) === 2, 'k(3) = 2');
assert(largestPowerOfTwoLessThan(4) === 2, 'k(4) = 2');
assert(largestPowerOfTwoLessThan(5) === 4, 'k(5) = 4');
assert(largestPowerOfTwoLessThan(8) === 4, 'k(8) = 4');
assert(largestPowerOfTwoLessThan(9) === 8, 'k(9) = 8');

// ─── Test merkleRoot ───────────────────────────────────────────────
section('merkleRoot');

const leaf1 = leafHash('leaf1');
const leaf2 = leafHash('leaf2');
const leaf3 = leafHash('leaf3');
const leaf4 = leafHash('leaf4');

const root1 = merkleRoot([leaf1]);
assert(hex(root1) === hex(leaf1), 'Single leaf root is the leaf');

const root2 = merkleRoot([leaf1, leaf2]);
const expected2 = nodeHash(leaf1, leaf2);
assert(hex(root2) === hex(expected2), 'Two leaves: root = H(leaf1, leaf2)');

const root4 = merkleRoot([leaf1, leaf2, leaf3, leaf4]);
const left = nodeHash(leaf1, leaf2);
const right = nodeHash(leaf3, leaf4);
const expected4 = nodeHash(left, right);
assert(hex(root4) === hex(expected4), 'Four leaves: correct root');

const emptyRoot = merkleRoot([]);
assert(emptyRoot.length === 32, 'Empty tree returns 32-byte zero buffer');

// ─── Test hashSubtree ──────────────────────────────────────────────
section('hashSubtree');

const leaves = [leaf1, leaf2, leaf3, leaf4];
const fullSubtree = hashSubtree(leaves, 0, 4);
assert(hex(fullSubtree) === hex(root4), 'hashSubtree(0,4) = root');

const leftSubtree = hashSubtree(leaves, 0, 2);
assert(hex(leftSubtree) === hex(left), 'hashSubtree(0,2) = left child');

const rightSubtree = hashSubtree(leaves, 2, 2);
assert(hex(rightSubtree) === hex(right), 'hashSubtree(2,2) = right child');

// ─── Test inclusionProof ───────────────────────────────────────────
section('inclusionProof');

// With 4 leaves, proof for leaf 0 should have 2 elements
const proof0 = inclusionProof(leaves, 0, 4);
assert(proof0.length === 2, 'Leaf 0 has 2-step proof');

// Verify proof manually
// To verify leaf0: hash with sibling (leaf1), then hash with right subtree
let current = leaf1; // first sibling is leaf1 (index 1)
assert(hex(proof0[0]) === hex(nodeHash(leaf3, leaf4)), 'First proof element is right subtree');
assert(hex(proof0[1]) === hex(leaf2), 'Second proof element is leaf2');

// Proof for leaf 1
const proof1 = inclusionProof(leaves, 1, 4);
assert(proof1.length === 2, 'Leaf 1 has 2-step proof');

// Proof for leaf 3
const proof3 = inclusionProof(leaves, 3, 4);
assert(proof3.length === 2, 'Leaf 3 has 2-step proof');

// ─── Test consistencyProof ─────────────────────────────────────────
section('consistencyProof');

// Consistency proof from size 2 to size 4
const cProof24 = consistencyProof(leaves, 2, 4);
assert(cProof24.length > 0, 'Consistency proof has elements');

// Consistency proof from size 1 to size 4
const cProof14 = consistencyProof(leaves, 1, 4);
assert(cProof14.length > 0, 'Consistency proof 1->4 has elements');

// Same size should return single element (the root)
const cProof44 = consistencyProof(leaves, 4, 4);
assert(cProof44.length === 1, 'Same size returns single element');
assert(hex(cProof44[0]) === hex(root4), 'Same size returns root');

// ─── Test proof structure ──────────────────────────────────────────
section('Proof Structure');

// Verify proof structure is correct
// For leaf 0 in 4-leaf tree: path should be [right_subtree, sibling]
assert(hex(proof0[0]) === hex(right), 'Proof[0] contains right subtree hash');
assert(hex(proof0[1]) === hex(leaf2), 'Proof[1] contains direct sibling');

// For leaf 3: path should be [left_subtree, sibling]
assert(hex(proof3[0]) === hex(left), 'Proof3[0] contains left subtree hash');
assert(hex(proof3[1]) === hex(leaf3), 'Proof3[1] contains direct sibling (leaf3)');

// Proof for leaf 2
const proof2 = inclusionProof(leaves, 2, 4);
assert(proof2.length === 2, 'Leaf 2 has 2-step proof');
assert(hex(proof2[0]) === hex(left), 'Proof2[0] contains left subtree');
assert(hex(proof2[1]) === hex(leaf4), 'Proof2[1] contains sibling leaf4');

// All proofs for 4-leaf tree should have depth 2
assert(proof0.length === 2 && proof1.length === 2 && proof2.length === 2 && proof3.length === 2,
    'All proofs in balanced tree have same depth');

// ─── Test with odd number of leaves ────────────────────────────────
section('Odd Tree Size');

const leaf5 = leafHash('leaf5');
const leaves5 = [leaf1, leaf2, leaf3, leaf4, leaf5];
const root5 = merkleRoot(leaves5);

const proof5_4 = inclusionProof(leaves5, 4, 5);
assert(proof5_4.length > 0, 'Leaf 4 in 5-tree has proof');

// For leaf 4 in 5-leaf tree, proof is just 1 step (sibling is root of first 4)
// Because: k=4 for n=5, so leaf 4 is the only element in right subtree
assert(proof5_4.length === 1, 'Leaf 4 proof has 1 step (sibling is full left subtree)');

// Test that root can be computed from 5 leaves
const expected5 = nodeHash(
    nodeHash(nodeHash(leaf1, leaf2), nodeHash(leaf3, leaf4)),
    leaf5
);
assert(hex(root5) === hex(expected5), '5-leaf root is correct');

// ─── Summary ───────────────────────────────────────────────────────
console.log('\n═══════════════════════════════════════════════════');
console.log(`  Tests: ${passed + failed}`);
console.log(`  Passed: ${passed}`);
console.log(`  Failed: ${failed}`);
console.log('═══════════════════════════════════════════════════\n');

process.exit(failed > 0 ? 1 : 0);
