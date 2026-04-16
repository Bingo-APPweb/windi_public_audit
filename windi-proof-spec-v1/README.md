# WINDI Proof Spec

**Canonical specification for independently verifiable WINDI proof artifacts.**

![WINDI Canonical Specification](https://img.shields.io/badge/WINDI-Canonical%20Specification-black)
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Status](https://img.shields.io/badge/status-stable-green)
![License](https://img.shields.io/badge/license-Apache%202.0-blue)

---

## Status

**CANONICAL / STABLE**

## Version

**v1.0.0**

---

## Purpose

This repository defines the canonical schema, canonicalization rules, hashing requirements, and interoperability vectors for WINDI proof receipts and proofsets.

WINDI (Worldwide Infrastructure for Non-repudiable Document Integrity) enables organizations to create, verify, and audit document governance decisions with cryptographic proof.

---

## Why It Exists

> **"You do not need to trust WINDI to verify WINDI."**

This specification allows any third party to independently verify WINDI proof artifacts without access to or trust in the originating system. The rules are public. The verification is deterministic. The evidence is permanent.

---

## Core Guarantees

| Guarantee | Description |
|-----------|-------------|
| **Deterministic Canonicalization** | Identical input always produces identical hash |
| **SHA-256 Evidence Hashing** | Single algorithm, no ambiguity |
| **Public Verification Linkage** | Every receipt links to public verify endpoint |
| **Ledger-Aligned Structure** | Compatible with WINDI Forensic Ledger |
| **Independent Consumption** | Third parties verify without WINDI access |

---

## Invariants Mapping

This specification aligns with WINDI Constitutional Invariants:

| Invariant | Name | Relevance |
|-----------|------|-----------|
| **I9** | Human Approval Gate | `human_approved` field reflects explicit human decision |
| **I11** | Evidence Permanence | Hash-only verification, `verify_url` + `ledger_anchor_id` |
| **I14** | Presence / Origin | Optional context for session/witness provenance |

See [`specs/invariants-mapping.md`](specs/invariants-mapping.md) for detailed mapping.

---

## Main Artifacts

| File | Purpose |
|------|---------|
| `schemas/receipt.schema.json` | Canonical receipt structure |
| `schemas/proofset.schema.json` | Collection/envelope of multiple proofs |
| `schemas/verification-result.schema.json` | Verification response structure |
| `specs/canonicalization.md` | Deterministic serialization rules |
| `specs/hashing.md` | SHA-256 application requirements |
| `specs/verification-model.md` | How verification works |
| `specs/invariants-mapping.md` | WINDI invariants alignment |
| `test-vectors/` | Interoperability test cases |
| `examples/` | Sample receipts and proofsets |

---

## Directory Structure

```
windi-proof-spec/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── VERSION
├── schemas/
│   ├── receipt.schema.json
│   ├── proofset.schema.json
│   └── verification-result.schema.json
├── specs/
│   ├── canonicalization.md
│   ├── hashing.md
│   ├── verification-model.md
│   └── invariants-mapping.md
├── examples/
│   ├── receipt-minimal.json
│   ├── receipt-high-governance.json
│   └── proofset-minimal.json
├── test-vectors/
│   ├── canonicalization-vectors.json
│   ├── hashing-vectors.json
│   └── interoperability-vectors.json
└── badges/
    └── canonical-spec.md
```

---

## Minimal Receipt Example

```json
{
  "spec_version": "1.0.0",
  "receipt_id": "WINDI-DSF-20260410094726-289EE95D",
  "issued_at": "2026-04-10T09:47:26Z",
  "actor": "did:windi:dragon-001",
  "app": "windi-law",
  "doc_name": "risk_assessment_0426.pdf",
  "doc_type": "risk_assessment",
  "content_hash": "9d4e1e23bd5b727046a9e3b4b7db57bd8d6ee684d5a63e7d8f6a3d1c1f1f9abc",
  "hash_algorithm": "SHA-256",
  "governance_level": "HIGH",
  "verify_url": "https://windi-domain.com/verify/WINDI-DSF-20260410094726-289EE95D",
  "human_approved": true,
  "invariants": ["I9", "I11"]
}
```

---

## Required Fields

Every valid receipt MUST include:

| Field | Type | Description |
|-------|------|-------------|
| `spec_version` | string | Must be `"1.0.0"` |
| `receipt_id` | string | Unique identifier (min 8 chars) |
| `issued_at` | string | ISO 8601 datetime |
| `actor` | string | DID or sovereign actor identifier |
| `app` | string | Originating WINDI module |
| `content_hash` | string | SHA-256 hex (64 chars) |
| `hash_algorithm` | string | Must be `"SHA-256"` |
| `governance_level` | string | `FREE`, `MED`, or `HIGH` |
| `verify_url` | string | HTTPS URL to public verification |

---

## Verification Flow

```
┌─────────────────┐
│  Receive Proof  │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Parse receipt   │
│ per schema      │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Canonicalize    │
│ payload         │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Recompute hash  │
│ (SHA-256)       │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Compare with    │
│ content_hash    │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Optionally:     │
│ GET verify_url  │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Verification    │
│ Result          │
└─────────────────┘
```

---

## Ecosystem Integration

This specification is consumed by:

| Component | Role |
|-----------|------|
| `windi-reader-sdk` | Client library for parsing and local verification |
| `windi-verification-api` | API service for remote verification |
| `windi-policy-engine` | Decision layer using verification results |
| `windi-forensics-engine` | Audit trail and replay |
| `windi-wcaf-toolkit` | Auditor tools for compliance export |

---

## License

Apache 2.0 — See [LICENSE](LICENSE)

---

## Security

See [SECURITY.md](SECURITY.md) for responsible disclosure.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

---

**WINDI Proof Spec v1.0.0** — *Canonical schema for independently verifiable proof artifacts.*

> "AI processes. Human decides. WINDI guarantees."
