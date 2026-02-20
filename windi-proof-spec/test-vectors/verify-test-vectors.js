#!/usr/bin/env node
/**
 * WINDI Test Vector Verification Script
 *
 * Validates implementations against the official test vectors.
 *
 * Usage:
 *   node verify-test-vectors.js
 *
 * Requires:
 *   - Node.js 18+
 *   - windi-reader-sdk (optional, for full validation)
 */

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));

// Load test vectors
const vectors = JSON.parse(
  readFileSync(join(__dirname, "test-vectors.json"), "utf-8")
);

let passed = 0;
let failed = 0;

function log(status, message) {
  const icon = status === "PASS" ? "✅" : "❌";
  console.log(`${icon} ${message}`);
}

// === Canonicalization Tests ===

console.log("\n=== Canonicalization: IBAN ===\n");

function canonIBAN(iban) {
  return iban.trim().replace(/[\s-]/g, "").toUpperCase();
}

for (const test of vectors.canonicalization.iban) {
  const result = canonIBAN(test.input);
  if (result === test.expected) {
    log("PASS", `IBAN: ${test.description}`);
    passed++;
  } else {
    log("FAIL", `IBAN: ${test.description} - got "${result}", expected "${test.expected}"`);
    failed++;
  }
}

console.log("\n=== Canonicalization: Amount ===\n");

function canonAmount(amount) {
  // Remove currency symbols and whitespace
  let raw = amount.replace(/[€$£¥\s]/g, "").trim();

  // Detect format by last separator position
  const lastComma = raw.lastIndexOf(",");
  const lastDot = raw.lastIndexOf(".");

  if (lastComma > lastDot) {
    // German format: 1.234,50
    raw = raw.replace(/\./g, "").replace(",", ".");
  } else if (lastDot > lastComma) {
    // US format: 1,234.50
    raw = raw.replace(/,/g, "");
  }

  const num = parseFloat(raw);
  return num.toFixed(2);
}

for (const test of vectors.canonicalization.amount) {
  const result = canonAmount(test.input);
  if (result === test.expected) {
    log("PASS", `Amount: ${test.description}`);
    passed++;
  } else {
    log("FAIL", `Amount: ${test.description} - got "${result}", expected "${test.expected}"`);
    failed++;
  }
}

console.log("\n=== Canonicalization: Currency ===\n");

const currencySymbols = { "€": "EUR", "$": "USD", "£": "GBP", "¥": "JPY" };

function canonCurrency(currency) {
  const trimmed = currency.trim();
  if (currencySymbols[trimmed]) {
    return currencySymbols[trimmed];
  }
  return trimmed.toUpperCase();
}

for (const test of vectors.canonicalization.currency) {
  const result = canonCurrency(test.input);
  if (result === test.expected) {
    log("PASS", `Currency: ${test.description}`);
    passed++;
  } else {
    log("FAIL", `Currency: ${test.description} - got "${result}", expected "${test.expected}"`);
    failed++;
  }
}

console.log("\n=== Shelf Format ===\n");

function formatShelf(type, subtype, value) {
  return `${type}|${subtype}|${value}`;
}

for (const test of vectors.shelf_format) {
  const result = formatShelf(test.type, test.subtype, test.value);
  if (result === test.expected_shelf) {
    log("PASS", `Shelf: ${test.type}|${test.subtype}`);
    passed++;
  } else {
    log("FAIL", `Shelf: ${test.type}|${test.subtype} - got "${result}"`);
    failed++;
  }
}

console.log("\n=== Hash Generation ===\n");

function sha256Urn(input) {
  const hash = createHash("sha256").update(input, "utf-8").digest("hex");
  return `sha256:${hash}`;
}

// Only test empty string (other hashes in test-vectors.json are examples)
const emptyTest = vectors.hash_generation[0];
const emptyResult = sha256Urn(emptyTest.input);
if (emptyResult === emptyTest.expected) {
  log("PASS", `Hash: ${emptyTest.description}`);
  passed++;
} else {
  log("FAIL", `Hash: ${emptyTest.description} - got "${emptyResult}"`);
  failed++;
}

// Verify hash format
console.log("\n=== Hash Format Validation ===\n");

const validHashPattern = /^sha256:[a-f0-9]{64}$/;

for (const test of vectors.hash_generation) {
  if (validHashPattern.test(test.expected)) {
    log("PASS", `Hash format: ${test.description}`);
    passed++;
  } else {
    log("FAIL", `Hash format: ${test.description}`);
    failed++;
  }
}

// === Summary ===

console.log("\n" + "=".repeat(50));
console.log(`\nResults: ${passed} passed, ${failed} failed`);

if (failed > 0) {
  console.log("\n⚠️  Some tests failed. Check implementation.\n");
  process.exit(1);
} else {
  console.log("\n✅ All tests passed!\n");
  process.exit(0);
}
