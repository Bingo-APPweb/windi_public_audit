/**
 * Verification routes
 *
 * @route POST /verify - Verify a receipt
 * @route POST /verify/receipt - Alias for /verify
 * @route POST /verify/batch - Batch verification
 */

import express from "express";
import { verifyReceipt, verifyBatch } from "../services/verificationService.js";
import { logger } from "../utils/logger.js";

const router = express.Router();

/**
 * POST /verify
 * Verify a single WINDI receipt
 *
 * Body: { receipt: {...} } or raw receipt object
 */
router.post("/", async (req, res) => {
  const requestId = `req-${Date.now().toString(36)}`;

  try {
    // Accept both { receipt: {...} } and raw receipt
    const receipt = req.body.receipt || req.body;

    if (!receipt || typeof receipt !== "object") {
      return res.status(400).json({
        verified: false,
        error: "INVALID_INPUT",
        message: "Request body must contain a receipt object",
        request_id: requestId
      });
    }

    logger.info(`Verification request: ${receipt.receipt_id || "unknown"}`, { requestId });

    const result = await verifyReceipt(receipt);
    result.request_id = requestId;

    const statusCode = result.verified ? 200 : 200; // Always 200, result indicates verification status
    res.status(statusCode).json(result);

  } catch (err) {
    logger.error(`Verification error: ${err.message}`, { requestId, stack: err.stack });

    res.status(400).json({
      verified: false,
      error: err.code || "VERIFICATION_ERROR",
      message: err.message,
      request_id: requestId,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * POST /verify/receipt
 * Alias for /verify
 */
router.post("/receipt", async (req, res) => {
  req.url = "/";
  router.handle(req, res);
});

/**
 * POST /verify/batch
 * Verify multiple receipts
 *
 * Body: { receipts: [...] }
 */
router.post("/batch", async (req, res) => {
  const requestId = `batch-${Date.now().toString(36)}`;

  try {
    const { receipts } = req.body;

    if (!Array.isArray(receipts)) {
      return res.status(400).json({
        verified: false,
        error: "INVALID_INPUT",
        message: "Request body must contain a 'receipts' array",
        request_id: requestId
      });
    }

    if (receipts.length === 0) {
      return res.status(400).json({
        verified: false,
        error: "EMPTY_BATCH",
        message: "Receipts array cannot be empty",
        request_id: requestId
      });
    }

    if (receipts.length > 100) {
      return res.status(400).json({
        verified: false,
        error: "BATCH_TOO_LARGE",
        message: "Maximum 100 receipts per batch",
        request_id: requestId
      });
    }

    logger.info(`Batch verification: ${receipts.length} receipts`, { requestId });

    const result = await verifyBatch(receipts);
    result.request_id = requestId;

    res.json(result);

  } catch (err) {
    logger.error(`Batch verification error: ${err.message}`, { requestId, stack: err.stack });

    res.status(400).json({
      verified: false,
      error: err.code || "BATCH_ERROR",
      message: err.message,
      request_id: requestId,
      timestamp: new Date().toISOString()
    });
  }
});

export default router;
