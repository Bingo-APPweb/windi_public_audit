// test/engine.test.js
const test = require("node:test");
const assert = require("node:assert/strict");
const { simpleDecision } = require("../src/index");

test("BLOCK when IBAN mismatch", () => {
  const out = simpleDecision({
    verification: { verdict: "VALID", integrity: "INTACT", signature: "VALID", trust_level: "HIGH", issuer_status: "TRUSTED", risk_flags: [] },
    doc: { iban: "DE12 3456 7890 1234 5678 90" },
    context: { expected_iban: "DE00 0000 0000 0000 0000 00", amount: 100 },
  });

  assert.equal(out.decision, "BLOCK");
  assert.ok(out.reason_codes.includes("IBAN_MISMATCH"));
});

test("HOLD when high value and trust != HIGH", () => {
  const out = simpleDecision({
    verification: { verdict: "VALID", integrity: "INTACT", signature: "VALID", trust_level: "MEDIUM", issuer_status: "REGISTERED", risk_flags: [] },
    doc: { iban: "DE001234..." },
    context: { expected_iban: "DE001234...", amount: 50000 },
  });

  assert.equal(out.decision, "HOLD");
  assert.ok(out.reason_codes.includes("HIGH_VALUE_LOW_TRUST"));
});

test("BLOCK when verification says TAMPERED", () => {
  const out = simpleDecision({
    verification: { verdict: "INVALID", integrity: "TAMPERED", signature: "VALID", trust_level: "LOW", issuer_status: "UNKNOWN", risk_flags: ["HASH_MISMATCH"] },
    doc: {},
    context: { amount: 10 },
  });

  assert.equal(out.decision, "BLOCK");
  assert.ok(out.reason_codes.includes("DOC_TAMPERED"));
});

test("ALLOW when everything is valid", () => {
  const out = simpleDecision({
    verification: { verdict: "VALID", integrity: "INTACT", signature: "VALID", trust_level: "HIGH", issuer_status: "TRUSTED", risk_flags: [] },
    doc: { iban: "DE89370400440532013000" },
    context: { expected_iban: "DE89370400440532013000", amount: 500 },
  });

  assert.equal(out.decision, "HOLD"); // default policy is HOLD when no rules match
  assert.equal(out.reason_codes.length, 0);
});

test("HOLD when issuer is unknown", () => {
  const out = simpleDecision({
    verification: { verdict: "VALID", integrity: "INTACT", signature: "VALID", trust_level: "HIGH", issuer_status: "UNKNOWN", risk_flags: [] },
    doc: { iban: "DE89370400440532013000" },
    context: { expected_iban: "DE89370400440532013000", amount: 500 },
  });

  assert.equal(out.decision, "HOLD");
  assert.ok(out.reason_codes.includes("ISSUER_UNKNOWN"));
});

test("BLOCK when risk_flags include HASH_MISMATCH", () => {
  const out = simpleDecision({
    verification: { verdict: "VALID", integrity: "INTACT", signature: "VALID", trust_level: "HIGH", issuer_status: "TRUSTED", risk_flags: ["HASH_MISMATCH"] },
    doc: { iban: "DE89370400440532013000" },
    context: { expected_iban: "DE89370400440532013000", amount: 500 },
  });

  assert.equal(out.decision, "BLOCK");
  assert.ok(out.reason_codes.includes("VERIFY_FLAG:HASH_MISMATCH"));
});
