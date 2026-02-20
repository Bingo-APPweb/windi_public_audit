// src/rules/ibanMismatch.js
function normalizeIban(x) {
  return String(x || "").replace(/\s+/g, "").toUpperCase();
}

module.exports = function ibanMismatch({ doc, context }) {
  const docIban = normalizeIban(doc?.iban);
  const expectedIban = normalizeIban(context?.expected_iban);

  if (!docIban || !expectedIban) return null;
  if (docIban === expectedIban) return null;

  return {
    rule_id: "ibanMismatch",
    decision: "BLOCK",
    reasons: ["IBAN_MISMATCH"],
    required_actions: ["MANUAL_REVIEW", "CALLBACK_SUPPLIER"],
    scoreDelta: 70,
    details: { doc_iban: docIban, expected_iban: expectedIban },
  };
};
