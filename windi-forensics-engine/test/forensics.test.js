// test/forensics.test.js
const test = require("node:test");
const assert = require("node:assert/strict");
const { createForensics, EventTypes } = require("../src/index");

test("append + chain verify ok", async () => {
  const fx = createForensics();

  const docId = "INV-2025-0001";

  await fx.appendEvent({
    document_id: docId,
    type: EventTypes.VERIFY_RESULT,
    payload: { verdict: "VALID", integrity: "INTACT", signature: "VALID", trust_level: "HIGH" },
    actor: { system: "verification-api", instance_id: "api-1" }
  });

  await fx.appendEvent({
    document_id: docId,
    type: EventTypes.POLICY_DECISION,
    payload: { decision: "ALLOW", reason_codes: [] },
    actor: { system: "policy-engine", instance_id: "pe-1" }
  });

  const timeline = await fx.getTimeline({ document_id: docId });
  const check = fx.verifyChain(timeline);

  assert.equal(check.ok, true);
  assert.equal(check.problems.length, 0);
});

test("replay reconstructs final state", async () => {
  const fx = createForensics();
  const docId = "INV-2025-0002";

  await fx.appendEvent({
    document_id: docId,
    type: EventTypes.VERIFY_RESULT,
    payload: { verdict: "VALID", integrity: "INTACT", signature: "VALID", trust_level: "MEDIUM" },
    actor: { system: "verification-api", instance_id: "api-1" }
  });

  await fx.appendEvent({
    document_id: docId,
    type: EventTypes.POLICY_DECISION,
    payload: { decision: "HOLD", reason_codes: ["HIGH_VALUE_LOW_TRUST"] },
    actor: { system: "policy-engine", instance_id: "pe-1" }
  });

  await fx.appendEvent({
    document_id: docId,
    type: EventTypes.PAYMENT_ACTION,
    payload: { action: "HOLD", ticket: "RISK-123" },
    actor: { system: "bank-core", instance_id: "core-7" }
  });

  const timeline = await fx.getTimeline({ document_id: docId });
  const state = fx.replay(timeline);

  assert.equal(state.verify.trust_level, "MEDIUM");
  assert.equal(state.policy.decision, "HOLD");
  assert.equal(state.payment.action, "HOLD");
});

test("detect tampering in chain", async () => {
  const fx = createForensics();
  const docId = "INV-2025-0003";

  await fx.appendEvent({
    document_id: docId,
    type: EventTypes.VERIFY_RESULT,
    payload: { verdict: "VALID" },
    actor: { system: "verification-api", instance_id: "api-1" }
  });

  await fx.appendEvent({
    document_id: docId,
    type: EventTypes.POLICY_DECISION,
    payload: { decision: "ALLOW" },
    actor: { system: "policy-engine", instance_id: "pe-1" }
  });

  const timeline = await fx.getTimeline({ document_id: docId });

  // tamper: muda payload sem recalcular hash
  timeline[1].payload.decision = "BLOCK";

  const check = fx.verifyChain(timeline);
  assert.equal(check.ok, false);
  assert.ok(check.problems.some(p => p.code === "HASH_MISMATCH"));
});

test("chain break detection", async () => {
  const fx = createForensics();
  const docId = "INV-2025-0004";

  await fx.appendEvent({
    document_id: docId,
    type: EventTypes.VERIFY_RESULT,
    payload: { verdict: "VALID" },
    actor: { system: "verification-api" }
  });

  await fx.appendEvent({
    document_id: docId,
    type: EventTypes.POLICY_DECISION,
    payload: { decision: "ALLOW" },
    actor: { system: "policy-engine" }
  });

  const timeline = await fx.getTimeline({ document_id: docId });

  // tamper: break the chain by modifying prev_hash
  timeline[1].prev_hash = "FAKE_HASH";

  const check = fx.verifyChain(timeline);
  assert.equal(check.ok, false);
  assert.ok(check.problems.some(p => p.code === "CHAIN_BREAK"));
});
