/**
 * WINDI Dispatch Route
 * POST /api/dispatch — sends governance briefing to authorized recipient
 * GET  /api/dispatch/status — returns last dispatch status
 */

const express = require("express");
const { dispatchGovernanceBriefing } = require("./windi-dispatcher");

const router = express.Router();

// In-memory dispatch log (last N dispatches)
const dispatchLog = [];
const MAX_LOG = 50;

function logDispatch(entry) {
  dispatchLog.unshift({ ...entry, timestamp: new Date().toISOString() });
  if (dispatchLog.length > MAX_LOG) dispatchLog.length = MAX_LOG;
}

// POST /api/dispatch
// Body: { "recipient": "email@example.com" }
router.post("/dispatch", async (req, res) => {
  try {
    const { recipient } = req.body || {};
    if (!recipient) {
      return res.status(400).json({
        success: false,
        error: "recipient required",
        hint: 'Send { "recipient": "email@example.com" }',
      });
    }

    const result = await dispatchGovernanceBriefing(recipient);
    logDispatch({ ...result, error: null });

    res.json({ success: true, result });
  } catch (e) {
    const errorMsg = String(e.message || e);
    logDispatch({ success: false, error: errorMsg, recipient: req.body?.recipient });

    const status = errorMsg.includes("BLOCKED") ? 403 : 500;
    res.status(status).json({ success: false, error: errorMsg });
  }
});

// POST /api/dispatch/all — sends to ALL whitelisted recipients
router.post("/dispatch/all", async (req, res) => {
  try {
    const recipients = (process.env.WINDI_RECIPIENTS || "")
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    if (!recipients.length) {
      return res.status(400).json({
        success: false,
        error: "No recipients in WINDI_RECIPIENTS whitelist",
      });
    }

    const results = [];
    for (const r of recipients) {
      try {
        const result = await dispatchGovernanceBriefing(r);
        results.push(result);
        logDispatch({ ...result, error: null });
      } catch (e) {
        results.push({ success: false, recipient: r, error: e.message });
        logDispatch({ success: false, error: e.message, recipient: r });
      }
    }

    const sent = results.filter((r) => r.success).length;
    res.json({
      success: sent > 0,
      total: recipients.length,
      sent,
      failed: recipients.length - sent,
      results,
    });
  } catch (e) {
    res.status(500).json({ success: false, error: String(e.message || e) });
  }
});

// GET /api/dispatch/status — last dispatches
router.get("/dispatch/status", (req, res) => {
  res.json({
    success: true,
    totalDispatched: dispatchLog.length,
    recent: dispatchLog.slice(0, 10),
  });
});

module.exports = router;
