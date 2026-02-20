// src/rules/issuerUnknown.js
module.exports = function issuerUnknown({ verification }) {
  if (!verification) return null;

  const status = verification.issuer_status || "UNKNOWN";
  if (status === "TRUSTED" || status === "REGISTERED") return null;

  return {
    rule_id: "issuerUnknown",
    decision: "HOLD",
    reasons: ["ISSUER_UNKNOWN"],
    required_actions: ["MANUAL_REVIEW"],
    scoreDelta: 25,
    details: { issuer_status: status },
  };
};
