// test/bundle.test.js
const test = require("node:test");
const assert = require("node:assert/strict");
const crypto = require("crypto");
const { createForensics, EventTypes, verifyBundle } = require("../src/index");

// Generate test RSA key pair
const { publicKey, privateKey } = crypto.generateKeyPairSync("rsa", {
  modulusLength: 2048,
  publicKeyEncoding: { type: "spki", format: "pem" },
  privateKeyEncoding: { type: "pkcs8", format: "pem" }
});

test("create bundle without signature", async () => {
  const fx = createForensics();
  const docId = "BUNDLE-TEST-001";

  await fx.appendEvent({
    document_id: docId,
    type: EventTypes.VERIFY_RESULT,
    payload: { verdict: "VALID", trust_level: "HIGH" },
    actor: { system: "verification-api" }
  });

  await fx.appendEvent({
    document_id: docId,
    type: EventTypes.POLICY_DECISION,
    payload: { decision: "ALLOW", policy_version: "bank-v1" },
    actor: { system: "policy-engine" }
  });

  const timeline = await fx.getTimeline({ document_id: docId });
  const bundle = fx.createBundle({ timeline });

  assert.equal(bundle.bundle_version, "wcaf-bundle-1.0");
  assert.equal(bundle.document_id, docId);
  assert.equal(bundle.timeline.length, 2);
  assert.equal(bundle.chain_verification.verified, true);
  assert.equal(bundle.chain_verification.event_count, 2);
  assert.ok(!bundle.bundle_signature); // No signature without key
});

test("create and verify signed bundle", async () => {
  const fx = createForensics({
    keyId: "bundle-key-2026",
    privateKey,
    publicKey
  });

  const docId = "BUNDLE-TEST-002";

  await fx.appendEvent({
    document_id: docId,
    type: EventTypes.VERIFY_RESULT,
    payload: { verdict: "VALID" },
    actor: { system: "test" }
  });

  const timeline = await fx.getTimeline({ document_id: docId });
  const bundle = fx.createBundle({ timeline });

  assert.ok(bundle.bundle_signature);
  assert.equal(bundle.bundle_signature.alg, "RSA-SHA256");
  assert.equal(bundle.bundle_signature.key_id, "bundle-key-2026");

  // Verify bundle
  const result = fx.verifyBundle(bundle);
  assert.equal(result.ok, true);
  assert.equal(result.chain_verified, true);
  assert.equal(result.bundle_signature_verified, true);
});

test("exportAuditBundle creates full bundle with attestation", async () => {
  const fx = createForensics({
    keyId: "audit-key-2026",
    privateKey,
    publicKey
  });

  const docId = "BUNDLE-TEST-003";

  await fx.appendEvent({
    document_id: docId,
    type: EventTypes.VERIFY_RESULT,
    payload: { verdict: "VALID", integrity: "INTACT" },
    actor: { system: "verification-api", instance_id: "api-1" }
  });

  await fx.appendEvent({
    document_id: docId,
    type: EventTypes.POLICY_DECISION,
    payload: { decision: "HOLD", reason_codes: ["HIGH_VALUE"], policy_version: "corp-v2" },
    actor: { system: "policy-engine", instance_id: "pe-1" }
  });

  await fx.appendEvent({
    document_id: docId,
    type: EventTypes.PAYMENT_ACTION,
    payload: { action: "HOLD", ticket: "RISK-456" },
    actor: { system: "bank-core", instance_id: "core-3" }
  });

  // Export full audit bundle
  const bundle = await fx.exportAuditBundle(docId);

  assert.equal(bundle.bundle_version, "wcaf-bundle-1.0");
  assert.equal(bundle.document_id, docId);
  assert.equal(bundle.timeline.length, 3);
  assert.equal(bundle.chain_verification.verified, true);

  // Has attestation
  assert.ok(bundle.attestation);
  assert.equal(bundle.attestation.key_id, "audit-key-2026");

  // Has bundle signature
  assert.ok(bundle.bundle_signature);

  // Verify the bundle
  const result = fx.verifyBundle(bundle);
  assert.equal(result.ok, true);
  assert.equal(result.attestation_present, true);
});

test("bundle detects tampered timeline", async () => {
  const fx = createForensics();
  const docId = "BUNDLE-TEST-004";

  await fx.appendEvent({
    document_id: docId,
    type: EventTypes.VERIFY_RESULT,
    payload: { verdict: "VALID" },
    actor: { system: "test" }
  });

  await fx.appendEvent({
    document_id: docId,
    type: EventTypes.POLICY_DECISION,
    payload: { decision: "ALLOW" },
    actor: { system: "test" }
  });

  const timeline = await fx.getTimeline({ document_id: docId });

  // Tamper with the timeline
  timeline[1].payload.decision = "BLOCK";

  const bundle = fx.createBundle({ timeline });

  // Chain should be marked as not verified
  assert.equal(bundle.chain_verification.verified, false);
  assert.ok(bundle.chain_verification.problems.length > 0);
});

test("exportBundleJson produces valid JSON", async () => {
  const fx = createForensics();
  const docId = "BUNDLE-TEST-005";

  await fx.appendEvent({
    document_id: docId,
    type: EventTypes.VERIFY_RESULT,
    payload: { verdict: "VALID" },
    actor: { system: "test" }
  });

  const timeline = await fx.getTimeline({ document_id: docId });
  const bundle = fx.createBundle({ timeline });
  const json = fx.exportBundleJson(bundle);

  // Should be valid JSON
  const parsed = JSON.parse(json);
  assert.equal(parsed.bundle_version, "wcaf-bundle-1.0");
});
