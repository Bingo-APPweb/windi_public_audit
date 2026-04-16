# Invariants Mapping

**WINDI Proof Spec v1.0.0**

This document defines how WINDI Constitutional Invariants map to proof receipt fields and verification behavior.

---

## Overview

WINDI operates under a constitutional framework of invariants — non-negotiable rules that govern system behavior. Proof receipts must reflect compliance with these invariants to be institutionally valid.

---

## Primary Invariants

### I9 — Human Approval Gate

> **"I9 não vive na entrada. I9 vive na saída."**
> (I9 doesn't live at the input. I9 lives at the output.)

**Principle:** No autonomous AI action can seal a decision. Human approval is mandatory before any governance artifact becomes permanent.

**Receipt Mapping:**

| Field | Relevance |
|-------|-----------|
| `human_approved` | `true` indicates explicit human approval |
| `policy_decision` | `HOLD` indicates awaiting human review |
| `governance_level` | `HIGH` requires `human_approved=true` before sealing |
| `invariants` | Must include `"I9"` when human approval was enforced |

**Verification Rule:**

When `governance_level` is `HIGH`:
- If `human_approved` is `false` or missing → receipt is PENDING, not SEALED
- If `human_approved` is `true` → receipt reflects completed I9 gate passage

**Anti-pattern:**
```
❌ governance_level: "HIGH", human_approved: missing  → ambiguous
✅ governance_level: "HIGH", human_approved: true     → valid sealed receipt
✅ governance_level: "HIGH", human_approved: false    → valid pending receipt
```

---

### I11 — Evidence Permanence

> **"Permanência de Evidência Criptográfica"**
> (Cryptographic Evidence Permanence)

**Principle:** Once sealed in the Ledger, evidence is immutable forever. Receipts are hash-only — they never require the original content for verification.

**Receipt Mapping:**

| Field | Relevance |
|-------|-----------|
| `content_hash` | SHA-256 of canonicalized content (evidence fingerprint) |
| `hash_algorithm` | Must be `SHA-256` in v1.0.0 |
| `verify_url` | Public endpoint for independent verification |
| `ledger_anchor_id` | Links to immutable Ledger entry |
| `invariants` | Must include `"I11"` when evidence permanence applies |

**Verification Rule:**

- `content_hash` is sufficient for verification
- Original document is NOT required
- `verify_url` must resolve to public verification endpoint
- `ledger_anchor_id` enables audit trail lookup

**Anti-pattern:**
```
❌ Verification requires original file upload  → violates I11
✅ Verification uses only content_hash         → compliant
```

---

### I14 — Presence / Origin Context

> **"Explicit Failure Principle"**
> (Dados ausentes = erro explícito)

**Principle:** When presence, session, or origin context is relevant, it must be explicitly declared. Placeholders or missing data are forbidden — absence is an explicit error, not a silent default.

**Receipt Mapping:**

| Field | Relevance |
|-------|-----------|
| `actor` | DID or sovereign identity (origin) |
| `app` | Originating module (session context) |
| `issued_at` | Timestamp (temporal presence) |
| `invariants` | Include `"I14"` when presence/origin is evidentially relevant |

**Verification Rule:**

- `actor` must be a valid identifier, never placeholder
- `app` must identify the actual originating system
- `issued_at` must be actual timestamp, never generated/guessed

**Anti-pattern:**
```
❌ actor: "unknown"           → violates I14
❌ actor: "N/A"               → violates I14
❌ app: "default"             → violates I14
✅ actor: "did:windi:dragon-001"  → compliant
✅ app: "windi-law"               → compliant
```

---

## Secondary Invariants

These invariants may appear in receipts depending on context:

### I1 — Human Sovereignty

Human activation required. System never acts autonomously.

**Receipt indicator:** `actor` field identifies human or human-delegated DID.

### I2 — Process Transparency

Pipeline is visible when requested.

**Receipt indicator:** `source_payload` may contain process metadata.

### I3 — Reversibility

Drafts are editable until sealing.

**Receipt indicator:** `policy_decision: "HOLD"` indicates reversible state.

### I6 — Conflict Exposure

Divergent positions must be explicit.

**Receipt indicator:** May appear in multi-party proofsets.

### I10 — LLM Sovereignty

Graceful fallback when external LLM unavailable.

**Receipt indicator:** Infrastructure concern, rarely in receipts.

### I12 — Language Sovereign Principle

Conversation is universal, document is sovereign.

**Receipt indicator:** `doc_type` or `source_payload` may indicate language.

### I13 — Convergence with Sovereignty

Every process converges to structure/decision/artifact.

**Receipt indicator:** `policy_decision` shows final convergent state.

---

## Invariants Array Usage

The `invariants` field is an array listing which invariants were actively enforced for this receipt.

**Example:**
```json
{
  "invariants": ["I9", "I11"]
}
```

This indicates:
- I9: Human approval was required and obtained
- I11: Evidence was sealed with cryptographic permanence

**Rules:**
- Only include invariants that were actually enforced
- Do not include all possible invariants
- Order does not matter (uniqueItems enforced)

---

## Governance Level → Invariant Defaults

| Level | Default Invariants | Notes |
|-------|-------------------|-------|
| `FREE` | `["I11"]` | Evidence permanence only |
| `MED` | `["I11"]` | Evidence permanence, I9 optional |
| `HIGH` | `["I9", "I11"]` | Human approval + evidence permanence required |

---

## Verification Checklist

When verifying a receipt, check:

1. **I11 Compliance**
   - [ ] `content_hash` is valid SHA-256 (64 hex chars)
   - [ ] `hash_algorithm` is `SHA-256`
   - [ ] `verify_url` is HTTPS and resolves

2. **I9 Compliance** (when `governance_level` is `HIGH`)
   - [ ] `human_approved` is explicitly `true` or `false`
   - [ ] If `human_approved: true`, receipt is SEALED
   - [ ] If `human_approved: false`, receipt is PENDING

3. **I14 Compliance**
   - [ ] `actor` is not a placeholder
   - [ ] `app` is not a placeholder
   - [ ] `issued_at` is valid ISO 8601 timestamp

---

## References

- WINDI Constitutional Framework: `CLAUDE.md`
- Living Tree Architecture: `DECRETO-001`
- Verify Public: `https://windi-domain.com/verify-public/`

---

*WINDI Proof Spec v1.0.0 — Invariants Mapping*
