# DOCUMENT-STATUS-STANDARD-001

**Status:** CANDIDATE  
**Date:** 2026-06-13  
**Mission:** Normalize WINDI-HIOS document lifecycle states  
**Purpose:** Define standard status vocabulary and required metadata  
**Parent:** `CONTINUITY-OPS-001`

## 1. Purpose

Define a minimal status vocabulary for WINDI-HIOS research, doctrine, measurement, and authority documents.

## 2. Required Header

Every continuity artifact should include:

```text
Status:
Date:
Mission:
Purpose:
```

Recommended when applicable:

```text
Parent:
Depends on:
Supersedes:
Blocks:
I9 Decision:
Authority Boundary:
```

## 3. Status Values

| Status | Meaning | Authority |
|---|---|---|
| `DRAFT` | Rough working note, not yet structured | Author |
| `CANDIDATE` | Structured proposal ready for review | Author / Council |
| `AWAITING I9` | Decision prepared; no mutation allowed | Human I9 |
| `SEALED` | Human-approved doctrine or decision | Human I9 + evidence |
| `MEASURED` | Result of a real run against data | Run evidence |
| `SUPERSEDED` | Replaced by later artifact; not deleted | Superseding artifact |
| `REJECTED` | Reviewed and explicitly not accepted | Human I9 or stated authority |
| `BLOCKED` | Cannot proceed until named condition is resolved | Stated blocker |

## 4. Rules

1. `CANDIDATE` is never equivalent to `SEALED`.
2. `MEASURED` is never equivalent to `APPROVED`.
3. `AWAITING I9` must not mutate state.
4. `SUPERSEDED` preserves history; it does not erase.
5. A document may be coherent and still lack authority.

## 5. Examples from Participation Layer

| Artifact | Correct Status |
|---|---|
| `ALIAS-RUN-001.md` | `MEASURED` |
| `ALIAS-PROMOTE-001-v0.3.md` | `AWAITING I9` |
| `ALIAS-ADMISSION-DOCTRINE-001.md` | `SEALED` |
| `CONTRIBUTION-GRAMMAR-001.md` | `CANDIDATE` |

## 6. Scriptable Checks

A continuity script may check:

- known status values;
- required metadata presence;
- whether `AWAITING I9` documents contain unchecked decision boxes;
- whether `SUPERSEDED` documents name the successor.

The script may report. It may not promote.

## 7. Sanitation Workflow

Document sanitation follows this order:

```text
measure
  -> classify
  -> propose
  -> review
  -> patch only after authority
```

Classes:

| Class | Meaning | Default Action |
|---|---|---|
| `OK` | Already follows the standard | Leave unchanged |
| `HEADER_PATCH` | Known status, missing metadata | Propose metadata-only patch |
| `STATUS_NORMALIZE` | Legacy/free-form status | Needs status mapping review |
| `NEEDS_TRIAGE` | Missing status and metadata | Classify before patching |
| `RAW_NOTE` | Conversation/note source | Preserve or archive; do not normalize as doctrine |

Header patch proposals are not automatic edits.

```text
proposal != patch
patch != seal
```

## 8. Line of Guard

> Status is not decoration. Status is authority state.
