// test/verifyAnchor.test.js — Public Anchor Verification tests
const assert = require("assert");
const { computeEntryHash, verifyChainIntegrity } = require("../src/verifyAnchor");

console.log("windi-wcaf-toolkit verify-anchor tests\n");

// =============================================================================
// Test 1: Entry hash computation
// =============================================================================

console.log("1. Entry hash computation");

const entry1 = {
  seq: 1,
  ts: "2026-02-08T12:00:00.000Z",
  combined_root_hash: "a".repeat(64),
  prev_entry_hash: "GENESIS"
};

const hash1 = computeEntryHash(entry1);
assert.strictEqual(hash1.length, 64);

// Same entry → same hash
const hash2 = computeEntryHash({ ...entry1 });
assert.strictEqual(hash1, hash2);

// Different entry → different hash
const entry2 = { ...entry1, seq: 2 };
const hash3 = computeEntryHash(entry2);
assert.notStrictEqual(hash1, hash3);

// entry_hash field is excluded
const entryWithHash = { ...entry1, entry_hash: "x".repeat(64) };
const hash4 = computeEntryHash(entryWithHash);
assert.strictEqual(hash1, hash4);

console.log("   ✓ Entry hash is deterministic and excludes entry_hash field\n");

// =============================================================================
// Test 2: Chain verification - valid chain
// =============================================================================

console.log("2. Chain verification - valid chain");

const chain = [];

const e1 = {
  seq: 1,
  ts: "2026-02-08T12:00:00.000Z",
  combined_root_hash: "a".repeat(64),
  prev_entry_hash: "GENESIS"
};
e1.entry_hash = computeEntryHash(e1);
chain.push(e1);

const e2 = {
  seq: 2,
  ts: "2026-02-08T13:00:00.000Z",
  combined_root_hash: "b".repeat(64),
  prev_entry_hash: e1.entry_hash
};
e2.entry_hash = computeEntryHash(e2);
chain.push(e2);

const e3 = {
  seq: 3,
  ts: "2026-02-08T14:00:00.000Z",
  combined_root_hash: "c".repeat(64),
  prev_entry_hash: e2.entry_hash
};
e3.entry_hash = computeEntryHash(e3);
chain.push(e3);

const validResult = verifyChainIntegrity(chain);
assert.strictEqual(validResult.valid, true);
assert.strictEqual(validResult.entries, 3);
assert.strictEqual(validResult.head_hash, e3.entry_hash);

console.log("   ✓ Valid chain passes verification\n");

// =============================================================================
// Test 3: Chain verification - tampered entry
// =============================================================================

console.log("3. Chain verification - tampered entry");

const tamperedChain = JSON.parse(JSON.stringify(chain));
tamperedChain[1].combined_root_hash = "x".repeat(64); // Tamper

const tamperedResult = verifyChainIntegrity(tamperedChain);
assert.strictEqual(tamperedResult.valid, false);
assert.strictEqual(tamperedResult.index, 1);

console.log("   ✓ Tampered chain detected\n");

// =============================================================================
// Test 4: Chain verification - broken link
// =============================================================================

console.log("4. Chain verification - broken link");

const brokenChain = JSON.parse(JSON.stringify(chain));
brokenChain[2].prev_entry_hash = "wrong"; // Break link

const brokenResult = verifyChainIntegrity(brokenChain);
assert.strictEqual(brokenResult.valid, false);
assert.strictEqual(brokenResult.index, 2);

console.log("   ✓ Broken chain link detected\n");

// =============================================================================
// Test 5: Empty chain
// =============================================================================

console.log("5. Empty chain");

const emptyResult = verifyChainIntegrity([]);
assert.strictEqual(emptyResult.valid, false);
assert.strictEqual(emptyResult.error, "Empty log");

console.log("   ✓ Empty chain rejected\n");

// =============================================================================
// Summary
// =============================================================================

console.log("═══════════════════════════════════════");
console.log("  All 5 tests passed! ✓");
console.log("═══════════════════════════════════════\n");
