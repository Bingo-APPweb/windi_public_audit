# RESEARCH-RECEIPTS-001

**Status:** CANDIDATE  
**Date:** 2026-06-13  
**Mission:** Define research receipt candidates before Ledger integration  
**Purpose:** Specify how research artifacts become hashable evidence candidates  
**Parent:** `CONTINUITY-OPS-001`

## 1. Purpose

Define how research, doctrine, matrices, and measurements become hashable evidence candidates before they are sealed in the Ledger.

## 2. Research Receipt Candidate

A research receipt candidate is not yet a Ledger receipt.

It is a structured record containing:

```text
artifact path
artifact sha256
generated_at
actor/process
source evidence
status
authority boundary
```

## 3. Minimum Fields

| Field | Meaning |
|---|---|
| `receipt_candidate_id` | Stable ID for the candidate |
| `artifact_path` | Path to the document or output |
| `artifact_hash` | SHA-256 of the artifact |
| `generated_at` | Timestamp of hash generation |
| `actor` | Agent/process creating the candidate |
| `source_decision` | I9 or note that no I9 exists |
| `status` | Candidate status |
| `witness_class` | If witness exists, e.g. `AI_REPRODUCIBILITY` |
| `ledger_status` | `not_submitted`, `pending_i9`, `sealed`, `rejected` |

## 4. Lifecycle

```text
document created
  -> hash generated
  -> research receipt candidate
  -> I9 review if mutation/seal requested
  -> Ledger seal only after authority
```

## 5. What Must Not Happen

```text
hash != seal
candidate != receipt
witness != approval
measurement != decision
```

## 6. First Script Target

The first continuity script should generate a read-only report:

```text
path
status
sha256
line_count
missing_headers
```

Later, a second script may produce JSON receipt candidates, but not submit them to the Ledger without I9.

## 7. Line of Guard

> A hash proves content. A receipt requires authority.
