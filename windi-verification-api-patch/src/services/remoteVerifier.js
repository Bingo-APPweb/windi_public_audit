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

// Default WINDI Verify Public endpoint
const DEFAULT_VERIFY_URL = "https://windi-domain.com/verify-public/api/verify";

/**
 * Verify a receipt against the WINDI Ledger
 *
 * @param {string} receiptId - Receipt ID to verify
 * @param {string} [verifyUrl] - Optional custom verify URL from receipt
 * @returns {Promise<object>} - Ledger verification result
 */
export async function verifyWithLedger(receiptId, verifyUrl = null) {
  const baseUrl = process.env.WINDI_VERIFY_URL || DEFAULT_VERIFY_URL;

  // Use receipt's verify_url if provided and valid
  let url;
  if (verifyUrl && verifyUrl.startsWith("https://")) {
    url = verifyUrl;
  } else {
    url = `${baseUrl}/${encodeURIComponent(receiptId)}`;
  }

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
 * Compare local receipt with ledger data
 *
 * @param {object} receipt - Local receipt
 * @param {object} ledgerData - Data from ledger
 * @returns {object} - Comparison result
 */
export function compareLedgerData(receipt, ledgerData) {
  const mismatches = [];

  // Fields to compare
  const fieldsToCompare = [
    "content_hash",
    "governance_level",
    "actor",
    "app"
  ];

  for (const field of fieldsToCompare) {
    if (receipt[field] && ledgerData[field]) {
      if (receipt[field] !== ledgerData[field]) {
        mismatches.push({
          field,
          receipt: receipt[field],
          ledger: ledgerData[field]
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
