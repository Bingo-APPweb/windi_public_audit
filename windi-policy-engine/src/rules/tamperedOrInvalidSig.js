// src/rules/tamperedOrInvalidSig.js
module.exports = function tamperedOrInvalidSig({ verification }) {
  const reasons = [];
  let decision = null;
  let scoreDelta = 0;

  if (!verification) return null;

  if (verification.integrity === "TAMPERED") {
    reasons.push("DOC_TAMPERED");
    decision = "BLOCK";
    scoreDelta += 90;
  }

  if (verification.signature === "INVALID") {
    reasons.push("SIGNATURE_INVALID");
    decision = "BLOCK";
    scoreDelta += 80;
  }

  if (verification.verdict === "INVALID") {
    reasons.push("VERIFICATION_INVALID");
    decision = decision || "BLOCK";
    scoreDelta += 60;
  }

  if (!reasons.length) return null;

  return {
    rule_id: "tamperedOrInvalidSig",
    decision,
    reasons,
    required_actions: ["REJECT_PAYMENT"],
    scoreDelta,
  };
};
