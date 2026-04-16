/**
 * Verification Service
 *
 * Core verification logic implementing windi-proof-spec v1.0.0
 *
 * Three-level verification:
 * - Level 1: Schema validation
 * - Level 2: Hash verification
 * - Level 3: Remote ledger confirmation
 */

import { validateReceipt } from "../validation/schemaValidator.js";
import { verifyHash } from "./canonicalizer.js";
import { verifyWithLedger, compareLedgerData } from "./remoteVerifier.js";
import { logger } from "../utils/logger.js";

/**
 * Verify a single receipt
 *
 * @param {object} receipt - WINDI receipt to verify
 * @returns {Promise<object>} - Verification result per verification-result.schema.json
 */
export async function verifyReceipt(receipt) {
  const startTime = Date.now();
  const receiptId = receipt.receipt_id || "unknown";

  const result = {
    verified: false,
    receipt_id: receiptId,
    timestamp: new Date().toISOString(),
    levels: {
      schema: "SKIPPED",
      hash: "SKIPPED",
      ledger: "SKIPPED"
    },
    governance_status: null,
    warnings: [],
    errors: []
  };

  // ============================================================
  // LEVEL 1: Schema Validation
  // ============================================================
  try {
    const schemaResult = validateReceipt(receipt);

    if (schemaResult.valid) {
      result.levels.schema = "VALID";
    } else {
      result.levels.schema = "INVALID";
      result.errors.push({
        code: "SCHEMA_INVALID",
        message: "Receipt does not match windi-proof-spec v1.0.0 schema",
        details: schemaResult.errors
      });

      // Cannot continue without valid schema
      result.duration_ms = Date.now() - startTime;
      return result;
    }
  } catch (err) {
    result.levels.schema = "INVALID";
    result.errors.push({
      code: "SCHEMA_ERROR",
      message: err.message
    });
    result.duration_ms = Date.now() - startTime;
    return result;
  }

  // ============================================================
  // LEVEL 2: Hash Verification
  // ============================================================
  try {
    const hashResult = await verifyHash(receipt);

    if (hashResult.error) {
      result.levels.hash = "MISMATCH";
      result.errors.push({
        code: "HASH_INVALID",
        message: hashResult.error,
        field: "content_hash"
      });
    } else if (hashResult.match) {
      result.levels.hash = "MATCH";
      result.hashes = {
        expected: hashResult.expected,
        computed: hashResult.computed,
        note: hashResult.note
      };
    } else {
      result.levels.hash = "MISMATCH";
      result.errors.push({
        code: "HASH_MISMATCH",
        message: "Content hash does not match",
        expected: hashResult.expected,
        computed: hashResult.computed
      });
    }
  } catch (err) {
    result.levels.hash = "MISMATCH";
    result.errors.push({
      code: "HASH_ERROR",
      message: err.message
    });
  }

  // ============================================================
  // Extract Governance Status
  // ============================================================
  result.governance_status = {
    level: receipt.governance_level || null,
    human_approved: receipt.human_approved,
    policy_decision: receipt.policy_decision || null,
    invariants: receipt.invariants || []
  };

  // Check I9 compliance for HIGH governance
  if (receipt.governance_level === "HIGH") {
    if (receipt.human_approved === undefined) {
      result.warnings.push({
        code: "I9_MISSING",
        message: "HIGH governance receipt missing human_approved field",
        field: "human_approved"
      });
    } else if (receipt.human_approved === false) {
      result.warnings.push({
        code: "I9_PENDING",
        message: "Receipt is pending human approval (I9 gate)",
        field: "human_approved"
      });
    }
  }

  // ============================================================
  // LEVEL 3: Remote Ledger Verification
  // ============================================================
  const skipRemote = process.env.WPIL_SKIP_REMOTE === "true";

  if (skipRemote) {
    result.levels.ledger = "SKIPPED";
    result.warnings.push({
      code: "REMOTE_SKIPPED",
      message: "Remote verification skipped (WPIL_SKIP_REMOTE=true)"
    });
  } else {
    try {
      const ledgerResult = await verifyWithLedger(receiptId, receipt.verify_url);

      switch (ledgerResult.status) {
        case "CONFIRMED":
          // Compare local receipt with ledger
          if (ledgerResult.ledger_data) {
            const comparison = compareLedgerData(receipt, ledgerResult.ledger_data);
            if (comparison.match) {
              result.levels.ledger = "CONFIRMED";
            } else {
              result.levels.ledger = "MISMATCH";
              result.errors.push({
                code: "LEDGER_MISMATCH",
                message: "Receipt does not match ledger data",
                mismatches: comparison.mismatches
              });
            }
          } else {
            result.levels.ledger = "CONFIRMED";
          }
          result.verify_url_checked = receipt.verify_url || ledgerResult.url;
          break;

        case "NOT_FOUND":
          result.levels.ledger = "NOT_FOUND";
          result.warnings.push({
            code: "NOT_IN_LEDGER",
            message: "Receipt not found in WINDI Ledger"
          });
          break;

        case "UNAVAILABLE":
        case "TIMEOUT":
          result.levels.ledger = "UNAVAILABLE";
          result.warnings.push({
            code: "LEDGER_UNAVAILABLE",
            message: ledgerResult.message
          });
          break;

        default:
          result.levels.ledger = "UNAVAILABLE";
          result.warnings.push({
            code: "LEDGER_ERROR",
            message: ledgerResult.message || "Unknown ledger error"
          });
      }
    } catch (err) {
      result.levels.ledger = "UNAVAILABLE";
      result.warnings.push({
        code: "LEDGER_ERROR",
        message: err.message
      });
    }
  }

  // ============================================================
  // Final Verdict
  // ============================================================
  const schemaOk = result.levels.schema === "VALID";
  const hashOk = result.levels.hash === "MATCH";
  const ledgerOk = result.levels.ledger === "CONFIRMED" ||
                   result.levels.ledger === "SKIPPED" ||
                   result.levels.ledger === "UNAVAILABLE" ||
                   result.levels.ledger === "NOT_FOUND"; // NOT_FOUND is a warning, not error

  result.verified = schemaOk && hashOk && result.errors.length === 0;

  // Add verifier info
  result.verifier = {
    name: "WINDI Verification API",
    version: "1.0.0",
    spec_version: "1.0.0",
    role: "WPIL"
  };

  result.duration_ms = Date.now() - startTime;

  logger.info(`Verification complete: ${receiptId}`, {
    verified: result.verified,
    levels: result.levels,
    duration_ms: result.duration_ms
  });

  return result;
}

/**
 * Verify multiple receipts in batch
 *
 * @param {object[]} receipts - Array of receipts
 * @returns {Promise<object>} - Batch verification result
 */
export async function verifyBatch(receipts) {
  const startTime = Date.now();

  const results = await Promise.all(
    receipts.map((receipt) => verifyReceipt(receipt))
  );

  const summary = {
    total: results.length,
    verified: results.filter((r) => r.verified).length,
    failed: results.filter((r) => !r.verified).length,
    by_governance_level: {
      FREE: results.filter((r) => r.governance_status?.level === "FREE").length,
      MED: results.filter((r) => r.governance_status?.level === "MED").length,
      HIGH: results.filter((r) => r.governance_status?.level === "HIGH").length
    }
  };

  return {
    verified: summary.failed === 0,
    timestamp: new Date().toISOString(),
    summary,
    results,
    duration_ms: Date.now() - startTime,
    verifier: {
      name: "WINDI Verification API",
      version: "1.0.0",
      spec_version: "1.0.0",
      role: "WPIL"
    }
  };
}

export default {
  verifyReceipt,
  verifyBatch
};
