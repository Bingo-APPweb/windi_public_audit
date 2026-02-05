#!/usr/bin/env node
/**
 * WINDI Dispatcher — Cron Runner
 * ===============================
 * Sends governance briefing to all whitelisted recipients.
 *
 * Crontab (09:00 CET, weekdays):
 *   0 9 * * 1-5 cd /opt/windi/dispatcher && node run.js >> /var/log/windi-dispatch.log 2>&1
 *
 * Or use TZ=Europe/Berlin for clarity:
 *   TZ=Europe/Berlin 0 9 * * 1-5 cd /opt/windi/dispatcher && node run.js
 */

require("dotenv").config();
const { dispatchGovernanceBriefing } = require("./windi-dispatcher");

const RECIPIENTS = (process.env.WINDI_RECIPIENTS || "")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);

(async () => {
  const runId = `RUN-${Date.now()}`;
  console.log(`\n${"=".repeat(60)}`);
  console.log(`[WINDI DISPATCH] ${runId}`);
  console.log(`[WINDI DISPATCH] Time: ${new Date().toISOString()}`);
  console.log(`[WINDI DISPATCH] Recipients: ${RECIPIENTS.length}`);
  console.log(`${"=".repeat(60)}`);

  if (!RECIPIENTS.length) {
    console.error("[WINDI DISPATCH] ERROR: No recipients in WINDI_RECIPIENTS. Aborting.");
    process.exit(1);
  }

  let sent = 0;
  let failed = 0;

  for (const recipient of RECIPIENTS) {
    try {
      const result = await dispatchGovernanceBriefing(recipient);
      console.log(`[WINDI DISPATCH] ✅ ${recipient} — ${result.messageId} (${result.elapsedMs}ms)`);
      sent++;
    } catch (err) {
      console.error(`[WINDI DISPATCH] ❌ ${recipient} — ${err.message}`);
      failed++;
    }
  }

  console.log(`\n[WINDI DISPATCH] COMPLETE: ${sent} sent, ${failed} failed`);
  console.log(`${"=".repeat(60)}\n`);

  process.exit(failed > 0 ? 1 : 0);
})();
