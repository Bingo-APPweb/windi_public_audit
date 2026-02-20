// test/verifyPdf.test.js — PDF Signature Verification tests
const assert = require("assert");
const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const { verifyPdfSignature } = require("../src/verifyPdfSignature");

console.log("windi-wcaf-toolkit verify-pdf tests\n");

// Create temp directory for test files
const tmpDir = path.join(__dirname, ".tmp");
if (!fs.existsSync(tmpDir)) {
  fs.mkdirSync(tmpDir);
}

// =============================================================================
// Test 1: Generate test keys
// =============================================================================

console.log("1. Generate test RSA keys");

const { privateKey, publicKey } = crypto.generateKeyPairSync("rsa", {
  modulusLength: 2048,
  publicKeyEncoding: { type: "spki", format: "pem" },
  privateKeyEncoding: { type: "pkcs8", format: "pem" }
});

const privKeyPath = path.join(tmpDir, "test_private.pem");
const pubKeyPath = path.join(tmpDir, "test_public.pem");
fs.writeFileSync(privKeyPath, privateKey);
fs.writeFileSync(pubKeyPath, publicKey);

console.log("   ✓ Test keys generated\n");

// =============================================================================
// Test 2: Sign and verify PDF
// =============================================================================

console.log("2. Sign and verify PDF");

// Create test PDF content
const pdfContent = Buffer.from("%PDF-1.4\nTest PDF content for WINDI audit report\n%%EOF");
const pdfPath = path.join(tmpDir, "test_report.pdf");
fs.writeFileSync(pdfPath, pdfContent);

// Sign the PDF
const sign = crypto.createSign("RSA-SHA256");
sign.update(pdfContent);
const signature = sign.sign(privateKey, "base64");

const sigPath = path.join(tmpDir, "test_report.sig");
fs.writeFileSync(sigPath, signature);

// Verify the signature
const result = verifyPdfSignature(pdfPath, sigPath, pubKeyPath);
assert.strictEqual(result.valid, true);
assert.strictEqual(result.pdf_hash.length, 64);

console.log("   ✓ Valid signature verified correctly\n");

// =============================================================================
// Test 3: Detect tampered PDF
// =============================================================================

console.log("3. Detect tampered PDF");

// Create tampered PDF
const tamperedContent = Buffer.from("%PDF-1.4\nTAMPERED content\n%%EOF");
const tamperedPath = path.join(tmpDir, "tampered_report.pdf");
fs.writeFileSync(tamperedPath, tamperedContent);

// Try to verify with original signature
const tamperedResult = verifyPdfSignature(tamperedPath, sigPath, pubKeyPath);
assert.strictEqual(tamperedResult.valid, false);

console.log("   ✓ Tampered PDF detected correctly\n");

// =============================================================================
// Test 4: Detect wrong key
// =============================================================================

console.log("4. Detect wrong key");

// Generate different key pair
const { publicKey: wrongPublicKey } = crypto.generateKeyPairSync("rsa", {
  modulusLength: 2048,
  publicKeyEncoding: { type: "spki", format: "pem" },
  privateKeyEncoding: { type: "pkcs8", format: "pem" }
});

const wrongKeyPath = path.join(tmpDir, "wrong_public.pem");
fs.writeFileSync(wrongKeyPath, wrongPublicKey);

// Try to verify with wrong key
const wrongKeyResult = verifyPdfSignature(pdfPath, sigPath, wrongKeyPath);
assert.strictEqual(wrongKeyResult.valid, false);

console.log("   ✓ Wrong key detected correctly\n");

// =============================================================================
// Test 5: PDF hash is consistent
// =============================================================================

console.log("5. PDF hash consistency");

const result1 = verifyPdfSignature(pdfPath, sigPath, pubKeyPath);
const result2 = verifyPdfSignature(pdfPath, sigPath, pubKeyPath);
assert.strictEqual(result1.pdf_hash, result2.pdf_hash);

console.log("   ✓ PDF hash is deterministic\n");

// =============================================================================
// Test 6: Public anchor hash computation
// =============================================================================

console.log("6. Public anchor hash computation");

const { computeEntryHash, sha256Hex } = require("../src/verifyPublicAnchor");

const anchorEntry = {
  seq: 1,
  ts: "2026-02-08T12:00:00.000Z",
  combined_root_hash: "a".repeat(64),
  prev_entry_hash: "GENESIS"
};

const entryHash = computeEntryHash(anchorEntry);
assert.strictEqual(entryHash.length, 64);

// Same entry → same hash
const entryHash2 = computeEntryHash({ ...anchorEntry });
assert.strictEqual(entryHash, entryHash2);

// entry_hash is excluded
const entryWithHash = { ...anchorEntry, entry_hash: "x".repeat(64) };
const entryHash3 = computeEntryHash(entryWithHash);
assert.strictEqual(entryHash, entryHash3);

console.log("   ✓ Anchor entry hash computation works correctly\n");

// =============================================================================
// Cleanup
// =============================================================================

fs.rmSync(tmpDir, { recursive: true, force: true });

// =============================================================================
// Summary
// =============================================================================

console.log("═══════════════════════════════════════");
console.log("  All 6 tests passed! ✓");
console.log("═══════════════════════════════════════\n");
