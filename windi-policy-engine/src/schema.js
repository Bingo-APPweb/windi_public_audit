// src/schema.js

const Decisions = Object.freeze({
  ALLOW: "ALLOW",
  HOLD: "HOLD",
  BLOCK: "BLOCK",
});

const TrustLevels = Object.freeze({
  LOW: "LOW",
  MEDIUM: "MEDIUM",
  HIGH: "HIGH",
});

module.exports = { Decisions, TrustLevels };
