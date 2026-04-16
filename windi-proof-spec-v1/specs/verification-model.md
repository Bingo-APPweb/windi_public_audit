# Verification Model

**WINDI Proof Spec v1.0.0**

This document defines how WINDI proof artifacts are verified, both locally and remotely.

---

## Verification Principle

> **"You do not need to trust WINDI to verify WINDI."**

Verification is designed to be:
- **Deterministic** — Same input, same result
- **Independent** — No WINDI access required for local verification
- **Transparent** — Rules are public
- **Auditable** — Every step can be inspected

---

## Verification Levels

### Level 1: Local Schema Validation

Verify receipt structure matches `receipt.schema.json`.

**Checks:**
- All required fields present
- Field types correct
- Field values within constraints
- `spec_version` matches expected version

**Result:** `VALID_SCHEMA` or `INVALID_SCHEMA`

### Level 2: Local Hash Verification

Recompute hash and compare with `content_hash`.

**Process:**
1. Parse receipt
2. Remove `source_payload` (transient)
3. Canonicalize remaining fields
4. Compute SHA-256
5. Compare with `content_hash`

**Result:** `HASH_MATCH` or `HASH_MISMATCH`

### Level 3: Remote Ledger Confirmation

Query public verification endpoint to confirm Ledger anchor.

**Process:**
1. Extract `verify_url` from receipt
2. HTTP GET to `verify_url`
3. Compare response with receipt

**Result:** `LEDGER_CONFIRMED` or `LEDGER_NOT_FOUND` or `LEDGER_MISMATCH`

---

## Verification Flow

```
┌─────────────────────────────────────────────────────────┐
│                    INPUT: Receipt                       │
└─────────────────────────┬───────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│  LEVEL 1: Schema Validation                             │
│  - Required fields present?                             │
│  - Types correct?                                       │
│  - spec_version = "1.0.0"?                              │
└─────────────────────────┬───────────────────────────────┘
                          │
            ┌─────────────┴─────────────┐
            │                           │
         INVALID                      VALID
            │                           │
            ▼                           ▼
    ┌───────────────┐   ┌─────────────────────────────────┐
    │ FAIL: SCHEMA  │   │  LEVEL 2: Hash Verification     │
    └───────────────┘   │  - Canonicalize receipt         │
                        │  - Compute SHA-256              │
                        │  - Compare with content_hash    │
                        └─────────────────────────────────┘
                                        │
                          ┌─────────────┴─────────────┐
                          │                           │
                       MISMATCH                     MATCH
                          │                           │
                          ▼                           ▼
                  ┌───────────────┐   ┌─────────────────────────────────┐
                  │ FAIL: HASH    │   │  LEVEL 3: Remote Confirmation   │
                  └───────────────┘   │  - GET verify_url               │
                                      │  - Compare response             │
                                      └─────────────────────────────────┘
                                                      │
                                        ┌─────────────┴─────────────┐
                                        │             │             │
                                    NOT_FOUND      MISMATCH      CONFIRMED
                                        │             │             │
                                        ▼             ▼             ▼
                                ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
                                │ WARN: NOT   │ │ FAIL: LEDGER│ │   PASS      │
                                │ IN LEDGER   │ │ MISMATCH    │ │ VERIFIED    │
                                └─────────────┘ └─────────────┘ └─────────────┘
```

---

## Verification Result Schema

```json
{
  "verified": true,
  "receipt_id": "WINDI-DSF-20260410094726-289EE95D",
  "timestamp": "2026-04-10T10:00:00Z",
  "levels": {
    "schema": "VALID",
    "hash": "MATCH",
    "ledger": "CONFIRMED"
  },
  "governance_status": {
    "level": "HIGH",
    "human_approved": true,
    "policy_decision": "ALLOW"
  },
  "warnings": [],
  "errors": []
}
```

---

## Governance Verification

Beyond cryptographic integrity, verification includes governance status.

### Governance Level Checks

| Level | Required Checks |
|-------|-----------------|
| `FREE` | Schema + Hash |
| `MED` | Schema + Hash + Ledger recommended |
| `HIGH` | Schema + Hash + Ledger + `human_approved=true` |

### Human Approval (I9)

For `governance_level: "HIGH"`:
- If `human_approved: true` → Receipt is SEALED
- If `human_approved: false` → Receipt is PENDING
- If `human_approved` missing → Verification WARNING

### Policy Decision

| Decision | Meaning |
|----------|---------|
| `ALLOW` | Approved and sealed |
| `HOLD` | Awaiting human review |
| `BLOCK` | Rejected |

---

## Remote Verification Endpoint

The `verify_url` field must point to a public HTTPS endpoint.

### Expected Behavior

**Request:**
```
GET https://windi-domain.com/verify/WINDI-DSF-20260410094726-289EE95D
Accept: application/json
```

**Response (found):**
```json
{
  "status": "verified",
  "receipt_id": "WINDI-DSF-20260410094726-289EE95D",
  "content_hash": "9d4e1e23bd5b727046a9e3b4b7db57bd8d6ee684d5a63e7d8f6a3d1c1f1f9abc",
  "sealed_at": "2026-04-10T09:47:26Z",
  "governance_level": "HIGH"
}
```

**Response (not found):**
```json
{
  "status": "not_found",
  "receipt_id": "WINDI-DSF-20260410094726-289EE95D"
}
```

---

## Offline Verification

When remote endpoint is unavailable:

1. **Level 1 + 2** can proceed (schema + hash)
2. **Level 3** skipped with warning
3. Overall result: `VERIFIED_LOCAL` (not `VERIFIED_FULL`)

This supports air-gapped and offline-first scenarios.

---

## Trust Model

### What You Trust

| Trust | Source |
|-------|--------|
| Spec correctness | This repository (public) |
| Canonicalization | Deterministic algorithm |
| Hash algorithm | SHA-256 (standard) |
| Ledger integrity | Remote endpoint (optional) |

### What You Don't Trust

| No Trust Needed | Reason |
|-----------------|--------|
| WINDI backend | Hash is recomputable |
| Receipt issuer | Content hash is verifiable |
| Network | Local verification possible |

---

## Error Handling

### Schema Errors

```json
{
  "verified": false,
  "levels": { "schema": "INVALID" },
  "errors": [
    { "field": "content_hash", "error": "missing required field" }
  ]
}
```

### Hash Mismatch

```json
{
  "verified": false,
  "levels": { "schema": "VALID", "hash": "MISMATCH" },
  "errors": [
    {
      "type": "hash_mismatch",
      "expected": "9d4e1e23...",
      "computed": "a1b2c3d4..."
    }
  ]
}
```

### Ledger Mismatch

```json
{
  "verified": false,
  "levels": { "schema": "VALID", "hash": "MATCH", "ledger": "MISMATCH" },
  "errors": [
    {
      "type": "ledger_mismatch",
      "field": "governance_level",
      "receipt": "HIGH",
      "ledger": "MED"
    }
  ]
}
```

---

## Implementation Checklist

- [ ] Parse receipt as JSON
- [ ] Validate against `receipt.schema.json`
- [ ] Remove `source_payload` field
- [ ] Sort keys lexicographically
- [ ] Serialize without whitespace
- [ ] Compute SHA-256
- [ ] Compare with `content_hash`
- [ ] Optionally fetch `verify_url`
- [ ] Check `human_approved` for HIGH governance
- [ ] Return structured verification result

---

## References

- Schema: `schemas/receipt.schema.json`
- Canonicalization: `specs/canonicalization.md`
- Hashing: `specs/hashing.md`
- Invariants: `specs/invariants-mapping.md`

---

*WINDI Proof Spec v1.0.0 — Verification Model*
