/**
 * WINDI Verification API — WPIL Entry Point
 *
 * WINDI Proof Interface Layer (WPIL)
 * Independent verification of WINDI proof artifacts.
 *
 * "You do not need to trust WINDI to verify WINDI."
 *
 * @version 1.0.0
 * @spec windi-proof-spec v1.0.0
 */

import "dotenv/config";
import express from "express";
import morgan from "morgan";
import verifyRoute from "./routes/verify.js";
import healthRoute from "./routes/health.js";
import { logger } from "./utils/logger.js";

const app = express();

// Middleware
app.use(express.json({ limit: "1mb" }));
app.use(morgan("combined", { stream: { write: (msg) => logger.info(msg.trim()) } }));

// CORS headers for public API
app.use((req, res, next) => {
  res.header("Access-Control-Allow-Origin", "*");
  res.header("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.header("Access-Control-Allow-Headers", "Content-Type, Authorization");
  if (req.method === "OPTIONS") {
    return res.sendStatus(200);
  }
  next();
});

// Routes
app.use("/health", healthRoute);
app.use("/verify", verifyRoute);

// Root endpoint - service info
app.get("/", (req, res) => {
  res.json({
    service: "WINDI Verification API",
    version: "1.0.0",
    role: "WPIL Entry Point",
    spec_version: "1.0.0",
    description: "Independent verification of WINDI proof artifacts",
    endpoints: {
      health: "GET /health",
      verify: "POST /verify",
      verify_receipt: "POST /verify/receipt",
      verify_batch: "POST /verify/batch"
    },
    principle: "You do not need to trust WINDI to verify WINDI."
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: "Not Found",
    message: `Endpoint ${req.method} ${req.path} not found`,
    available_endpoints: ["/", "/health", "/verify", "/verify/receipt", "/verify/batch"]
  });
});

// Error handler
app.use((err, req, res, next) => {
  logger.error(`Error: ${err.message}`, { stack: err.stack });
  res.status(err.status || 500).json({
    error: err.name || "InternalError",
    message: err.message || "An unexpected error occurred",
    request_id: `err-${Date.now().toString(36)}`
  });
});

// Start server
const PORT = process.env.PORT || 4000;
const HOST = process.env.HOST || "0.0.0.0";

app.listen(PORT, HOST, () => {
  logger.info(`WINDI Verification API (WPIL) listening on ${HOST}:${PORT}`);
  logger.info(`Spec version: windi-proof-spec v1.0.0`);
  logger.info(`Mode: ${process.env.WPIL_MODE || "relay"}`);
});

export default app;
