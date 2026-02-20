// src/engine/replay.js
const { EventTypes } = require("../schema");

/**
 * replay
 * Reconstroi um "estado" final a partir da timeline.
 * É propositalmente simples: você pode evoluir isso para uma máquina de estados.
 */
function replay(timeline) {
  const state = {
    document_id: timeline[0]?.document_id || null,
    verify: null,
    policy: null,
    payment: null,
    notes: []
  };

  for (const e of timeline) {
    switch (e.type) {
      case EventTypes.VERIFY_RESULT:
        state.verify = e.payload;
        break;
      case EventTypes.POLICY_DECISION:
        state.policy = e.payload;
        break;
      case EventTypes.PAYMENT_ACTION:
        state.payment = e.payload;
        break;
      case EventTypes.NOTE:
        state.notes.push(e.payload);
        break;
      default:
        // ignore
        break;
    }
  }

  return state;
}

module.exports = { replay };
