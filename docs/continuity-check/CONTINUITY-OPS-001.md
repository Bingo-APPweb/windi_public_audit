# CONTINUITY-OPS-001

**Status:** CANDIDATE  
**Date:** 2026-06-13  
**Mission:** WINDI-HIOS Operational Continuity Layer  
**Purpose:** Organize five operational continuity areas for WINDI-HIOS  
**Steward:** Codex, provisional operational manager  
**Authority Boundary:** Codex organizes continuity; I9 remains human.

## 1. Purpose

Organize five operational continuity areas so WINDI-HIOS can onboard agents, preserve doctrine, verify document state, generate research receipts, and prevent recommendations from becoming decisions.

This mission does not change constitutional authority.

```text
Conselho: recomenda
Witness: atesta coerencia
I9: decide
STRATO: sela
```

## 2. Scope

| Area | Artifact | Purpose |
|---|---|---|
| 1. Entry maps | `ONBOARDING-MAP-001.md` | Give new agents a short map of where the living system is |
| 2. Document statuses | `DOCUMENT-STATUS-STANDARD-001.md` | Normalize CANDIDATE, SEALED, MEASURED, AWAITING I9, SUPERSEDED |
| 3. Participation index | `PARTICIPATION-LAYER-INDEX-001.md` | Link the Participation Layer documents in dependency order |
| 4. Research receipts | `RESEARCH-RECEIPTS-001.md` | Define how research outputs become hashable, attributable evidence |
| 5. Authority gate | `AUTHORITY-GATE-001.md` | Preserve recommendation != decision and witness != approver |

## 3. Operating Rule

Continuity scripts must verify and report. They must not silently decide, promote, seal, or mutate constitutional state.

```text
scripts may inspect
scripts may hash
scripts may produce reports
scripts may propose next steps
scripts must not cross I9
```

## 4. Phase Plan

### Phase 1 — Documentation Spine

Create the five artifacts above with enough structure that a new agent can orient without oral memory.

### Phase 2 — Minimum Standards

Define required metadata, status vocabulary, authority boundaries, and dependency links.

### Phase 3 — Continuity Scripts

Create read-only scripts that can:

- list continuity docs;
- check known status values;
- compute hashes;
- report missing required headers;
- prepare research receipt candidates.

### Phase 4 — STRATO Publication

Publish artifacts to `/home/windi/docs/` and scripts to `/home/windi/docs/` or a future controlled scripts directory.

### Phase 5 — Ledger Integration

Only after I9 review, connect the output to Ledger receipts. Until then, hashes and reports are evidence candidates, not sealed facts.

## 5. Deliverables v0.1

| Deliverable | Status |
|---|---|
| `CONTINUITY-OPS-001.md` | this document |
| `ONBOARDING-MAP-001.md` | planned |
| `DOCUMENT-STATUS-STANDARD-001.md` | planned |
| `PARTICIPATION-LAYER-INDEX-001.md` | planned |
| `RESEARCH-RECEIPTS-001.md` | planned |
| `AUTHORITY-GATE-001.md` | planned |
| `scripts/continuity_check.py` | created |
| `scripts/document_sanitation_matrix.py` | created |
| `scripts/participation_index_check.py` | created |
| `scripts/research_receipt_candidates.py` | created |
| `scripts/authority_gate_check.py` | created |
| `scripts/header_patch_proposals.py` | created |

## 5.1 First Measurements

Local continuity check:

```text
files_checked: 18
files_with_header_or_status_issues: 8
```

STRATO continuity check:

```text
files_checked: 83
files_with_header_or_status_issues: 74
```

Interpretation:

```text
The new continuity artifacts follow the standard.
The wider historical docs need triage before normalization.
```

Generated proposal artifacts:

| Artifact | Purpose |
|---|---|
| `DOCUMENT-SANITATION-MATRIX-001.md/json` | Local sanitation classification |
| `DOCUMENT-SANITATION-MATRIX-STRATO-001.md/json` | STRATO sanitation classification |
| `HEADER-PATCH-PROPOSALS-001.md` | Metadata-only patch proposals for local HEADER_PATCH items |

## 6. Line of Guard

> Organizar a continuidade sem assumir a soberania.
