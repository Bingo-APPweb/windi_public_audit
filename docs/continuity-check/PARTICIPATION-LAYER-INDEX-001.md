# PARTICIPATION-LAYER-INDEX-001

**Status:** CANDIDATE  
**Date:** 2026-06-13  
**Mission:** Participation Layer orientation index  
**Purpose:** Map Participation Layer artifacts in dependency order  
**Parent:** `CONTINUITY-OPS-001`

## 1. Purpose

Provide a short dependency map for the Participation Layer so future agents can read in order instead of reconstructing the trail from conversation memory.

## 2. Reading Order

| Order | Artifact | Status | Role |
|---:|---|---|---|
| 1 | `CONTRIBUTION-GRAMMAR-001.md` | CANDIDATE | Defines what a verifiable contribution may be |
| 2 | `MATRIZ-FATO-CONTRIBUICAO-001.md` | CANDIDATE | Tests contribution grammar against real receipts |
| 3 | `ACTION-0-WITNESS-ADMISSIBILITY-001.md` | SEALED by process note | Defines witness admissibility in one-human Liga |
| 4 | `ALIAS-RESOLUTION-001.md` | SEALED | Defines actor_original -> canonical_did rules |
| 5 | `ALIAS-RUN-001.md` | MEASURED | Measures alias resolution against real STRATO data |
| 6 | `ALIAS-ADMISSION-DOCTRINE-001.md` | SEALED | Defines Alias Admission as governed identity recognition |
| 7 | `ALIAS-PROMOTE-001-v0.3.md` | AWAITING I9 | Presents line-by-line admission decisions |

Local folder:

```text
docs/ADMISSIBILITY/
```

## 3. Core Chain

```text
Receipt
  -> Observed Actor
  -> Alias Resolution
  -> Alias Admission
  -> Canonical Identity
  -> Contribution Event
  -> Recognition
```

## 4. Guard Rails

```text
Receipt defines the fact.
Alias Admission defines who carries the fact.
Activity vs Contribution comes before counting causal sources.
Recommendation is not decision.
Witness is not approver.
```

## 5. Current Stop Point

The current operational stop point is:

```text
ALIAS-PROMOTE-001-v0.3
Status: AWAITING I9
did_aliases: untouched
Next action: requires explicit I9 approval before STRATO mutation
```

## 6. Open Work

| Item | Need |
|---|---|
| Contribution Event schema | Blocked until identity admission has I9-approved examples |
| ALIAS-RUN-002 | Requires I9-approved alias admissions |
| Research receipts | Need standard before ledger sealing |
| Invariant promotion | Candidate: "Receipt defines the fact. Alias Admission defines who carries the fact." |

## 7. Line of Guard

> A Participation Layer grows by dependency, not by enthusiasm.
