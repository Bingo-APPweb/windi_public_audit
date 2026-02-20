// src/engine.js
const { Decisions } = require("./schema");

// Regras em ordem (a ordem importa: cedo pode BLOCKar)
const tamperedOrInvalidSig = require("./rules/tamperedOrInvalidSig");
const ibanMismatch = require("./rules/ibanMismatch");
const flagsFromVerification = require("./rules/flagsFromVerification");
const highValueLowTrust = require("./rules/highValueLowTrust");
const issuerUnknown = require("./rules/issuerUnknown");

const RULES = [
  tamperedOrInvalidSig,
  ibanMismatch,
  flagsFromVerification,
  highValueLowTrust,
  issuerUnknown,
];

function worstDecision(a, b) {
  const rank = { ALLOW: 0, HOLD: 1, BLOCK: 2 };
  if (!a) return b;
  if (!b) return a;
  return rank[b] > rank[a] ? b : a;
}

function evaluate({ verification, doc, context, policy }) {
  const applied = [];
  let decision = null;
  let score = 0;

  for (const rule of RULES) {
    const out = rule({ verification, doc, context, policy });
    if (!out) continue;

    applied.push(out);
    decision = worstDecision(decision, out.decision);
    score += Number(out.scoreDelta || 0);

    // Otimização: se já deu BLOCK, não precisa seguir
    if (decision === Decisions.BLOCK) break;
  }

  decision = decision || policy?.default_decision || Decisions.HOLD;
  if (score > 100) score = 100;

  const reason_codes = applied.flatMap(r => r.reasons || []);
  const required_actions = [...new Set(applied.flatMap(r => r.required_actions || []))];

  return {
    decision,
    score,
    reason_codes,
    required_actions,
    applied_rules: applied.map(r => ({
      rule_id: r.rule_id,
      decision: r.decision,
      reasons: r.reasons,
      details: r.details || undefined,
    })),
  };
}

module.exports = { evaluate };
