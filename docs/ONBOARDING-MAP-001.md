# ONBOARDING-MAP-001

**Status:** CANDIDATE  
**Date:** 2026-06-13  
**Mission:** Short entry map for WINDI-HIOS agents  
**Purpose:** Orient new agents before they touch the work  
**Parent:** `CONTINUITY-OPS-001`

## 1. Purpose

Give a new agent a minimal map before touching the work.

Rule:

```text
Read the work before touching the work.
```

## 2. Mandatory First Reads

On STRATO:

```text
/home/windi/CLAUDE.md
/home/windi/CLAUDE-HISTORY.md
```

Participation Layer local/STRATO docs:

```text
CONTRIBUTION-GRAMMAR-001.md
PARTICIPATION-LAYER-INDEX-001.md
AUTHORITY-GATE-001.md
DOCUMENT-STATUS-STANDARD-001.md
```

## 3. Core Data Locations

| Area | Path |
|---|---|
| Ledger SQLite | `/opt/windi/data/forensic_ledger.sqlite3` |
| DID Genesis service | `/opt/windi/did-genesis/` |
| DID Genesis DB | `/opt/windi/did-genesis/did_genesis.db` |
| Schemas | `/opt/windi/schemas/`, `/home/windi/windi-proof-spec-v1/schemas/` |
| Cinema work | `/opt/windi/hios/cinema/obras/w-hios-forensic-unit/` |
| W-COST | `/opt/windi/w-cost-001/cost_ledger.db` |
| Published docs | `/home/windi/docs/` |

## 4. Safe First Commands

Read-only orientation:

```bash
hostname && whoami && pwd
find /home/windi/docs -maxdepth 1 -type f | sort
sqlite3 /opt/windi/data/forensic_ledger.sqlite3 '.tables'
sqlite3 /opt/windi/did-genesis/did_genesis.db '.tables'
```

## 5. Do Not Start With

```text
schema mutation
database writes
alias admission
ledger seal
token or reward design
```

unless explicit I9 has already been issued.

## 6. Line of Guard

> A new agent first becomes literate, then useful.
