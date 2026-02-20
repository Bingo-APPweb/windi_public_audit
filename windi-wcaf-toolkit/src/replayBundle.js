// src/replayBundle.js
const { replay } = require("windi-forensics-engine");

function replayBundle(bundle) {
  console.log("╔══════════════════════════════════════════════════╗");
  console.log("║           WCAF State Reconstruction              ║");
  console.log("╚══════════════════════════════════════════════════╝\n");

  if (!bundle.timeline || bundle.timeline.length === 0) {
    console.log("No events to replay.");
    return;
  }

  const state = replay(bundle.timeline);

  console.log(`Document ID: ${state.document_id || bundle.document_id}\n`);

  // Verification state
  console.log("┌─ Verification ─────────────────────────────────────┐");
  if (state.verify) {
    console.log(`│  Verdict:     ${state.verify.verdict || "N/A"}`);
    console.log(`│  Integrity:   ${state.verify.integrity || "N/A"}`);
    console.log(`│  Trust Level: ${state.verify.trust_level || "N/A"}`);
    console.log(`│  Signature:   ${state.verify.signature || "N/A"}`);
  } else {
    console.log("│  (No verification event)");
  }
  console.log("└────────────────────────────────────────────────────┘\n");

  // Policy state
  console.log("┌─ Policy Decision ──────────────────────────────────┐");
  if (state.policy) {
    console.log(`│  Decision:    ${state.policy.decision || "N/A"}`);
    console.log(`│  Version:     ${state.policy.policy_version || "N/A"}`);
    if (state.policy.reason_codes?.length) {
      console.log(`│  Reasons:     ${state.policy.reason_codes.join(", ")}`);
    }
  } else {
    console.log("│  (No policy decision event)");
  }
  console.log("└────────────────────────────────────────────────────┘\n");

  // Payment state
  console.log("┌─ Payment Action ───────────────────────────────────┐");
  if (state.payment) {
    console.log(`│  Action:      ${state.payment.action || "N/A"}`);
    console.log(`│  Ticket:      ${state.payment.ticket || "N/A"}`);
    if (state.payment.executed_at) {
      console.log(`│  Executed:    ${state.payment.executed_at}`);
    }
  } else {
    console.log("│  (No payment action event)");
  }
  console.log("└────────────────────────────────────────────────────┘\n");

  // Notes
  if (state.notes && state.notes.length > 0) {
    console.log("┌─ Notes ───────────────────────────────────────────┐");
    state.notes.forEach((note, i) => {
      console.log(`│  ${i + 1}. ${JSON.stringify(note)}`);
    });
    console.log("└────────────────────────────────────────────────────┘\n");
  }

  // Final decision summary
  console.log("═══════════════════════════════════════════════════════");
  const decision = state.policy?.decision || "UNKNOWN";
  const action = state.payment?.action || "PENDING";

  if (decision === "ALLOW" && action === "EXECUTED") {
    console.log("  FINAL STATE: ✅ PAYMENT EXECUTED");
  } else if (decision === "BLOCK" || action === "REJECTED") {
    console.log("  FINAL STATE: ❌ PAYMENT BLOCKED");
  } else if (decision === "HOLD" || action === "HOLD") {
    console.log("  FINAL STATE: ⏸️  PAYMENT ON HOLD");
  } else {
    console.log("  FINAL STATE: ⚠️  PENDING RESOLUTION");
  }
  console.log("═══════════════════════════════════════════════════════");
}

module.exports = { replayBundle };
