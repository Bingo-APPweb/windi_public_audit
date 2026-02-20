// test/attestation.test.js
const test = require("node:test");
const assert = require("node:assert/strict");
const crypto = require("crypto");
const { createForensics, EventTypes } = require("../src/index");

// Generate test RSA key pair
const { publicKey, privateKey } = crypto.generateKeyPairSync("rsa", {
  modulusLength: 2048,
  publicKeyEncoding: { type: "spki", format: "pem" },
  privateKeyEncoding: { type: "pkcs8", format: "pem" }
});

test("create and verify attestation", async () => {
  const fx = createForensics({
    keyId: "test-key-2026",
    privateKey,
    publicKey
  });

  const docId = "ATT-TEST-001";

  await fx.appendEvent({
    document_id: docId,
    type: EventTypes.VERIFY_RESULT,
    payload: { verdict: "VALID", trust_level: "HIGH" },
    actor: { system: "test" }
  });

  await fx.appendEvent({
    document_id: docId,
    type: EventTypes.POLICY_DECISION,
    payload: { decision: "ALLOW", policy_version: "test-v1" },
    actor: { system: "test" }
  });

  // Create attestation
  const attestation = await fx.createAttestation({ document_id: docId });

  assert.ok(attestation.head_event_hash);
  assert.equal(attestation.key_id, "test-key-2026");
  assert.equal(attestation.signature_alg, "RSA-SHA256");
  assert.ok(attestation.signature);
  assert.equal(attestation.schema_version, "wcaf-attestation-1.0");

  // Verify attestation
  const isValid = fx.verifyAttestation(attestation);
  assert.equal(isValid, true);
});

test("attestation fails verification with wrong key", async () => {
  const fx = createForensics({
    keyId: "test-key-2026",
    privateKey
  });

  const docId = "ATT-TEST-002";

  await fx.appendEvent({
    document_id: docId,
    type: EventTypes.VERIFY_RESULT,
    payload: { verdict: "VALID" },
    actor: { system: "test" }
  });

  const attestation = await fx.createAttestation({ document_id: docId });

  // Generate a different key pair
  const { publicKey: wrongKey } = crypto.generateKeyPairSync("rsa", {
    modulusLength: 2048,
    publicKeyEncoding: { type: "spki", format: "pem" },
    privateKeyEncoding: { type: "pkcs8", format: "pem" }
  });

  // Verify with wrong key should fail
  const isValid = fx.verifyAttestation(attestation, wrongKey);
  assert.equal(isValid, false);
});

test("attestation fails if timeline is empty", async () => {
  const fx = createForensics({
    keyId: "test-key-2026",
    privateKey
  });

  await assert.rejects(
    async () => fx.createAttestation({ document_id: "NONEXISTENT" }),
    /No events found/
  );
});
