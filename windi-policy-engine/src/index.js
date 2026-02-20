// src/index.js
const fs = require("fs");
const path = require("path");
const { evaluate } = require("./engine");

function loadDefaultPolicy() {
  const p = path.join(__dirname, "policies", "default.policy.json");
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

/**
 * simpleDecision
 * Entrada mínima e portátil pra ligar SDK -> Verification API -> Policy Engine
 */
function simpleDecision(input) {
  const policy = input.policy || loadDefaultPolicy();
  return evaluate({ ...input, policy });
}

module.exports = { simpleDecision, evaluate };
