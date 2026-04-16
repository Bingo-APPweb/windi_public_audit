/**
 * Schema Validator
 *
 * Validates receipts against windi-proof-spec v1.0.0 schemas
 */

import Ajv from "ajv";
import addFormats from "ajv-formats";

// Embedded receipt schema from windi-proof-spec v1.0.0
// Note: Using draft-07 for Ajv compatibility
const receiptSchema = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://github.com/Bingo-APPweb/windi-proof-spec/schemas/receipt.schema.json",
  "title": "WINDI Receipt",
  "description": "Canonical independently verifiable WINDI proof receipt. Version 1.0.0.",
  "type": "object",
  "required": [
    "spec_version",
    "receipt_id",
    "issued_at",
    "actor",
    "app",
    "content_hash",
    "hash_algorithm",
    "governance_level",
    "verify_url"
  ],
  "properties": {
    "spec_version": {
      "type": "string",
      "const": "1.0.0"
    },
    "receipt_id": {
      "type": "string",
      "minLength": 8
    },
    "issued_at": {
      "type": "string",
      "format": "date-time"
    },
    "actor": {
      "type": "string"
    },
    "app": {
      "type": "string"
    },
    "doc_name": {
      "type": "string"
    },
    "doc_type": {
      "type": "string"
    },
    "content_hash": {
      "type": "string",
      "pattern": "^[A-Fa-f0-9]{64}$"
    },
    "hash_algorithm": {
      "type": "string",
      "enum": ["SHA-256"]
    },
    "governance_level": {
      "type": "string",
      "enum": ["FREE", "MED", "HIGH"]
    },
    "sge_score": {
      "type": "number",
      "minimum": 0,
      "maximum": 100
    },
    "verify_url": {
      "type": "string",
      "format": "uri",
      "pattern": "^https://"
    },
    "ledger_anchor_id": {
      "type": "string"
    },
    "human_approved": {
      "type": "boolean"
    },
    "policy_decision": {
      "type": "string",
      "enum": ["ALLOW", "HOLD", "BLOCK"]
    },
    "invariants": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["I1", "I2", "I3", "I6", "I9", "I10", "I11", "I12", "I13", "I14"]
      },
      "uniqueItems": true
    },
    "source_payload": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "additionalProperties": false
};

// Initialize Ajv with draft-2020-12 support
const ajv = new Ajv({
  strict: false,
  allErrors: true
});
addFormats(ajv);

// Compile schema
const validateReceiptSchema = ajv.compile(receiptSchema);

/**
 * Validate a receipt against windi-proof-spec v1.0.0 schema
 *
 * @param {object} receipt - Receipt to validate
 * @returns {{valid: boolean, errors: object[]|null}}
 */
export function validateReceipt(receipt) {
  const valid = validateReceiptSchema(receipt);

  if (valid) {
    return { valid: true, errors: null };
  }

  // Format errors for clarity
  const errors = validateReceiptSchema.errors.map((err) => ({
    field: err.instancePath || err.params?.missingProperty || "root",
    message: err.message,
    keyword: err.keyword,
    params: err.params
  }));

  return { valid: false, errors };
}

/**
 * Check if a receipt has required fields (quick check without full validation)
 *
 * @param {object} receipt - Receipt to check
 * @returns {{valid: boolean, missing: string[]}}
 */
export function checkRequiredFields(receipt) {
  const required = [
    "spec_version",
    "receipt_id",
    "issued_at",
    "actor",
    "app",
    "content_hash",
    "hash_algorithm",
    "governance_level",
    "verify_url"
  ];

  const missing = required.filter((field) => !receipt[field]);

  return {
    valid: missing.length === 0,
    missing
  };
}

/**
 * Validate content_hash format
 *
 * @param {string} hash - Hash to validate
 * @returns {boolean}
 */
export function isValidHashFormat(hash) {
  if (typeof hash !== "string") return false;
  return /^[a-fA-F0-9]{64}$/.test(hash);
}

/**
 * Validate verify_url format
 *
 * @param {string} url - URL to validate
 * @returns {boolean}
 */
export function isValidVerifyUrl(url) {
  if (typeof url !== "string") return false;
  try {
    const parsed = new URL(url);
    return parsed.protocol === "https:";
  } catch {
    return false;
  }
}

export default {
  validateReceipt,
  checkRequiredFields,
  isValidHashFormat,
  isValidVerifyUrl
};
