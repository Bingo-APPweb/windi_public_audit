/**
 * Health endpoint - Living Tree compatible
 *
 * @route GET /health
 */

import express from "express";

const router = express.Router();

const startTime = Date.now();

router.get("/", (req, res) => {
  const uptime = Math.floor((Date.now() - startTime) / 1000);

  res.json({
    status: "healthy",
    service: "windi-verification-api",
    role: "WPIL",
    version: "1.0.0",
    spec_version: "1.0.0",
    mode: process.env.WPIL_MODE || "relay",
    uptime_seconds: uptime,
    capabilities: {
      local_verification: true,
      remote_verification: true,
      batch_verification: true,
      schema_validation: true,
      hash_recomputation: true
    },
    invariants: ["I9", "I11", "I14"],
    verify_endpoint: process.env.WINDI_VERIFY_URL || "https://windi-domain.com/verify-public/",
    timestamp: new Date().toISOString()
  });
});

export default router;
