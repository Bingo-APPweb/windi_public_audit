# DOCUMENT-SANITATION-MATRIX-001

**Status:** MEASURED
**Date:** 2026-06-13
**Mission:** Document continuity sanitation
**Purpose:** Classify documentation status/header issues without mutating source files

## Summary

- `HEADER_PATCH`: 4
- `NEEDS_TRIAGE`: 1
- `OK`: 4
- `RAW_NOTE`: 2
- `STATUS_NORMALIZE`: 1

## Matrix

| file | status | missing_headers | action | recommendation |
|---|---|---|---|---|
| `ACTION-0-WITNESS-ADMISSIBILITY-001.md` | `CONSTITUTIONAL BLOCKING QUESTION` | Purpose | `STATUS_NORMALIZE` | Map legacy/free-form status to DOCUMENT-STATUS-STANDARD-001. |
| `ALIAS-ADMISSION-DOCTRINE-001.md` | `SEALED` | - | `OK` | No action required. |
| `Alias-notes.md` | `MISSING` | Status, Date, Mission, Purpose | `RAW_NOTE` | Keep as source note or move to notes archive; do not normalize as doctrine. |
| `ALIAS-PROMOTE-001-v0.2.md` | `AWAITING I9` | - | `OK` | No action required. |
| `ALIAS-PROMOTE-001-v0.3.md` | `AWAITING I9` | - | `OK` | No action required. |
| `ALIAS-PROMOTE-001.md` | `AWAITING I9` | - | `OK` | No action required. |
| `ALIAS-RESOLUTION-001.md` | `SEALED` | Mission | `HEADER_PATCH` | Add missing required metadata without changing body. |
| `ALIAS-RUN-001.md` | `MEASURED` | Date, Mission, Purpose | `HEADER_PATCH` | Add missing required metadata without changing body. |
| `CONTRIBUTION-ALIAS-RESOLUTION-NEW.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `CONTRIBUTION-GRAMMAR-001.md` | `CANDIDATE` | Purpose | `HEADER_PATCH` | Add missing required metadata without changing body. |
| `correcoes-CODEX.md` | `MISSING` | Status, Date, Mission, Purpose | `RAW_NOTE` | Keep as source note or move to notes archive; do not normalize as doctrine. |
| `MATRIZ-FATO-CONTRIBUICAO-001.md` | `CANDIDATE` | Mission | `HEADER_PATCH` | Add missing required metadata without changing body. |

## Line of Guard

> Saneamento documental classifica antes de corrigir.
