// src/printTimeline.js

function printTimeline(bundle) {
  console.log("╔══════════════════════════════════════════════════╗");
  console.log("║              WCAF Event Timeline                 ║");
  console.log("╚══════════════════════════════════════════════════╝\n");

  console.log(`Document ID: ${bundle.document_id || "N/A"}`);
  console.log(`Events: ${bundle.timeline?.length || 0}\n`);

  if (!bundle.timeline || bundle.timeline.length === 0) {
    console.log("No events in timeline.");
    return;
  }

  console.log("─".repeat(70));
  console.log(" #   Timestamp                  Type              Actor");
  console.log("─".repeat(70));

  bundle.timeline.forEach((e, i) => {
    const ts = e.ts?.slice(0, 19).replace("T", " ") || "N/A";
    const type = (e.type || "UNKNOWN").padEnd(18);
    const actor = e.actor?.system || "unknown";

    console.log(` ${String(i).padStart(2)}  ${ts}  ${type} ${actor}`);

    // Show key payload info
    if (e.type === "VERIFY_RESULT" && e.payload) {
      console.log(`     → verdict: ${e.payload.verdict}, trust: ${e.payload.trust_level || "N/A"}`);
    }
    if (e.type === "POLICY_DECISION" && e.payload) {
      console.log(`     → decision: ${e.payload.decision}, policy: ${e.payload.policy_version || "N/A"}`);
    }
    if (e.type === "PAYMENT_ACTION" && e.payload) {
      console.log(`     → action: ${e.payload.action}, ticket: ${e.payload.ticket || "N/A"}`);
    }
  });

  console.log("─".repeat(70));
  console.log("");

  // Show chain info
  const first = bundle.timeline[0];
  const last = bundle.timeline[bundle.timeline.length - 1];

  console.log("Chain Info:");
  console.log(`  Genesis:    ${first.prev_hash}`);
  console.log(`  Head Hash:  ${last.event_hash}`);
  console.log(`  Duration:   ${first.ts} → ${last.ts}`);
}

module.exports = { printTimeline };
