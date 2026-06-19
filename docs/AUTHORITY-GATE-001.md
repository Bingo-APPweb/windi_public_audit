# AUTHORITY-GATE-001

**Status:** CANDIDATE  
**Date:** 2026-06-13  
**Mission:** Preserve authority boundaries in WINDI-HIOS continuity work  
**Purpose:** Prevent recommendation, witness, measurement, and decision from collapsing  
**Parent:** `CONTINUITY-OPS-001`

## 1. Purpose

Prevent analysis, recommendation, measurement, or witness statements from being mistaken for human decision or Ledger seal.

## 2. Four Roles

```text
Conselho: recomenda
Witness: atesta coerencia
I9: decide
STRATO: sela
```

## 3. Role Boundaries

| Role | May Do | Must Not Do |
|---|---|---|
| Council | Analyze, critique, recommend | Decide as I9 |
| Witness | Attest coherence, consistency, reproducibility | Approve or claim judicial independence |
| I9 | Decide, approve, reject, pause | Pretend evidence exists without run |
| STRATO | Seal, persist, hash, measure | Decide what should be sealed |

## 4. Operational Rule

No mutation of identity, contribution, recognition, or Ledger state happens from:

```text
"recommended"
"looks correct"
"if you approve"
"architecturally sound"
"witness coherent"
```

Mutation requires an explicit human decision.

## 5. I9 Form

An I9 decision should be affirmative and specific:

```text
I9: aprovo [specific item].
Ressalva: [if any].
Scope: [what may be changed].
```

Ambiguous statements remain recommendations.

## 6. Witness Form

A witness statement should state its class:

```text
witness_class = AI_REPRODUCIBILITY
```

And its limits:

```text
does not prove independent human review
does not approve
does not replace I9
```

## 7. STRATO Form

A STRATO seal should produce at minimum:

```text
artifact path
sha256
timestamp
actor/process
source decision
```

## 8. Line of Guard

> The system knows how to stop before authority.
