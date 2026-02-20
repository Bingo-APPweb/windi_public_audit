// src/schema.js

const EventTypes = Object.freeze({
  VERIFY_CALLED: "VERIFY_CALLED",
  VERIFY_RESULT: "VERIFY_RESULT",
  POLICY_DECISION: "POLICY_DECISION",
  PAYMENT_ACTION: "PAYMENT_ACTION",
  NOTE: "NOTE"
});

// Evento WCAF (WINDI Chain Audit Format) — base
// {
//   event_id, ts, document_id, type,
//   actor: { system, instance_id, ip? },
//   payload: {...},
//   prev_hash, event_hash
// }

module.exports = { EventTypes };
