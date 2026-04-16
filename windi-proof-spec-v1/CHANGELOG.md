# Changelog

All notable changes to the WINDI Proof Specification will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-04-16

### Added

- **Canonical stable version** for WINDI proof interoperability
- `receipt.schema.json` — Canonical receipt structure with required fields:
  - `spec_version` (locked to "1.0.0")
  - `receipt_id` (unique identifier)
  - `issued_at` (ISO 8601 timestamp)
  - `actor` (DID or sovereign identifier)
  - `app` (originating WINDI module)
  - `content_hash` (SHA-256, 64 hex chars)
  - `hash_algorithm` (SHA-256 only in v1.0.0)
  - `governance_level` (FREE/MED/HIGH)
  - `verify_url` (HTTPS public verification endpoint)
- `proofset.schema.json` — Collection/envelope for multiple proofs
- `verification-result.schema.json` — Structured verification response
- **Canonicalization specification** (`specs/canonicalization.md`):
  - UTF-8 encoding
  - Lexicographic key ordering
  - No whitespace
  - Array order preserved
  - Number normalization
  - String escaping rules
  - Transient field exclusion (`source_payload`)
- **Hashing specification** (`specs/hashing.md`):
  - SHA-256 as sole algorithm
  - 64 lowercase hex output format
  - Reference implementations (JS, Python, Go, Rust)
- **Verification model** (`specs/verification-model.md`):
  - Level 1: Schema validation
  - Level 2: Hash verification
  - Level 3: Remote ledger confirmation
  - Offline verification support
- **Invariants mapping** (`specs/invariants-mapping.md`):
  - I9 — Human Approval Gate
  - I11 — Evidence Permanence
  - I14 — Presence / Origin context
- **Examples**:
  - `receipt-minimal.json` — Minimum valid receipt
  - `receipt-high-governance.json` — Full HIGH governance receipt
- **Test vectors** for interoperability validation

### Changed

- Repositioned from technical draft to **canonical specification**
- Made `verify_url` **mandatory** (previously optional)
- Separated `receipt` schema from `proofset` schema

### Security

- Added SECURITY.md for responsible disclosure

### Notes

This release establishes WINDI Proof Spec as the official interoperability contract for proof receipts across the WINDI ecosystem.

The key principle:

> **"You do not need to trust WINDI to verify WINDI."**

---

## [0.x.x] - Pre-release

Early development versions. Not suitable for production use.

---

*WINDI Proof Spec — Canonical schema for independently verifiable proof artifacts.*
