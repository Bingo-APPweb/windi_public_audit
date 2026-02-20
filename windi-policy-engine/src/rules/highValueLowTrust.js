// src/rules/highValueLowTrust.js
const { TrustLevels } = require("../schema");

module.exports = function highValueLowTrust({ verification, context, policy }) {
  const amount = Number(context?.amount || 0);
  const threshold = Number(policy?.high_value_threshold || 10000);

  if (!verification) return null;
  if (!amount || amount < threshold) return null;

  if (verification.trust_level === TrustLevels.HIGH) return null;

  // Se for alto valor e trust não for HIGH -> HOLD (padrão seguro)
  return {
    rule_id: "highValueLowTrust",
    decision: "HOLD",
    reasons: ["HIGH_VALUE_LOW_TRUST"],
    required_actions: ["MANUAL_REVIEW"],
    scoreDelta: 40,
    details: { amount, threshold, trust_level: verification.trust_level },
  };
};
