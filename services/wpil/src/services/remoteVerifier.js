/**
 * Remote Verification Service
 *
 * Calls WINDI Verify Public endpoint to confirm ledger anchor
 *
 * This provides Level 3 verification:
 * - Confirms receipt exists in WINDI Ledger
 * - Validates governance status
 * - Returns ledger metadata
 */

import { logger } from "../utils/logger.js";

// Default WINDI Ledger endpoint (internal)
const DEFAULT_VERIFY_URL = "http://localhost:8101/api/receipts";

/**
 * Verify a receipt against the WINDI Ledger
 *
 * @param {string} receiptId - Receipt ID to verify
 * @param {string} [verifyUrl] - Optional custom verify URL from receipt (ignored in relay mode)
 * @returns {Promise<object>} - Ledger verification result
 */
export async function verifyWithLedger(receiptId, verifyUrl = null) {
  const baseUrl = process.env.WINDI_VERIFY_URL || DEFAULT_VERIFY_URL;

  // In relay mode, always use internal endpoint for reliability
  // External verify_url is informational only
  const url = `${baseUrl}/${encodeURIComponent(receiptId)}`;

  logger.info(`Remote verification: ${receiptId}`, { url });

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000); // 10s timeout

    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Accept": "application/json",
        "User-Agent": "WINDI-WPIL/1.0.0"
      },
      signal: controller.signal
    });

    clearTimeout(timeout);

    if (response.status === 404) {
      return {
        status: "NOT_FOUND",
        receipt_id: receiptId,
        message: "Receipt not found in WINDI Ledger",
        verified_at: new Date().toISOString()
      };
    }

    if (!response.ok) {
      return {
        status: "ERROR",
        receipt_id: receiptId,
        http_status: response.status,
        message: `Remote verification failed: HTTP ${response.status}`,
        verified_at: new Date().toISOString()
      };
    }

    const data = await response.json();

    return {
      status: "CONFIRMED",
      receipt_id: receiptId,
      ledger_data: data,
      verified_at: new Date().toISOString()
    };

  } catch (err) {
    if (err.name === "AbortError") {
      return {
        status: "TIMEOUT",
        receipt_id: receiptId,
        message: "Remote verification timed out",
        verified_at: new Date().toISOString()
      };
    }

    // Network error - ledger unavailable
    logger.warn(`Remote verification failed: ${err.message}`, { receiptId });

    return {
      status: "UNAVAILABLE",
      receipt_id: receiptId,
      message: `Could not reach WINDI Ledger: ${err.message}`,
      verified_at: new Date().toISOString()
    };
  }
}

/**
 * Normalize hash for comparison (remove sha256: prefix if present)
 */
function normalizeHash(hash) {
  if (!hash) return null;
  return hash.replace(/^sha256:/i, "").toLowerCase();
}

/**
 * Compare local receipt with ledger data
 *
 * @param {object} receipt - Local receipt
 * @param {object} ledgerData - Data from ledger (may be wrapped in {ok, receipt})
 * @returns {object} - Comparison result
 */
export function compareLedgerData(receipt, ledgerData) {
  const mismatches = [];

  // Handle wrapped response: {ok: true, receipt: {...}}
  const ledger = ledgerData.receipt || ledgerData;

  // Map receipt fields to ledger fields
  const fieldMap = {
    "content_hash": { receiptField: "content_hash", ledgerField: "content_hash", normalize: normalizeHash },
    "governance_level": { receiptField: "governance_level", ledgerField: "governance_level" },
    "actor": { receiptField: "actor", ledgerField: "actor" },
    "app": { receiptField: "app", ledgerField: "app" }
  };

  for (const [name, config] of Object.entries(fieldMap)) {
    const receiptValue = receipt[config.receiptField];
    const ledgerValue = ledger[config.ledgerField];

    if (receiptValue && ledgerValue) {
      const normalizedReceipt = config.normalize ? config.normalize(receiptValue) : receiptValue;
      const normalizedLedger = config.normalize ? config.normalize(ledgerValue) : ledgerValue;

      if (normalizedReceipt !== normalizedLedger) {
        mismatches.push({
          field: name,
          receipt: receiptValue,
          ledger: ledgerValue
        });
      }
    }
  }

  return {
    match: mismatches.length === 0,
    mismatches
  };
}

export default {
  verifyWithLedger,
  compareLedgerData
};
