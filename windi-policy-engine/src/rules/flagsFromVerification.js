// src/rules/flagsFromVerification.js
// Converte risk_flags do /verify em decisão (map configurável via policy)
module.exports = function flagsFromVerification({ verification, policy }) {
  const flags = verification?.risk_flags || [];
  if (!flags.length) return null;

  const map = policy?.risk_flag_map || {};
  let worst = null;
  const reasons = [];

  for (const f of flags) {
    reasons.push(`VERIFY_FLAG:${f}`);
    const mapped = map[f]; // "ALLOW"|"HOLD"|"BLOCK"
    if (!mapped) continue;

    // pior decisão vence
    if (!worst) worst = mapped;
    else if (worst === "ALLOW" && (mapped === "HOLD" || mapped === "BLOCK")) worst = mapped;
    else if (worst === "HOLD" && mapped === "BLOCK") worst = mapped;
  }

  if (!worst) return null;

  return {
    rule_id: "flagsFromVerification",
    decision: worst,
    reasons,
    required_actions: worst === "BLOCK" ? ["REJECT_PAYMENT"] : ["MANUAL_REVIEW"],
    scoreDelta: worst === "BLOCK" ? 60 : 20,
  };
};
