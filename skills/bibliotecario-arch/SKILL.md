# W-LIB-001 Bibliotecario — Architectural Knowledge Skill

> **Skill ID**: bibliotecario-arch
> **Version**: 1.0.0
> **Category**: constitutional
> **Created**: 2026-03-10
> **Author**: Human Dragon + AI Dragon

## Purpose

This skill documents the architectural design of the W-LIB-001 Bibliotecario agent — the guardian of constitutional knowledge in the WINDI ecosystem. Use this skill when agents or humans need to understand how knowledge flows through the constellation.

---

## 1. Constellation Overview

```
                           ┌─────────────────────────────────────┐
                           │         HUMAN DRAGON                │
                           │    (Veto Absoluto / I1 + I9)        │
                           └──────────────┬──────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                    ╔═══════════════════════════════════╗                    │
│                    ║   W-LIB-001 BIBLIOTECARIO         ║                    │
│                    ║   "Guardian of Knowledge"         ║                    │
│                    ║   :8091/library                   ║                    │
│                    ╚═══════════════════════════════════╝                    │
│                                    │                                        │
│         ┌──────────────────────────┼──────────────────────────┐             │
│         │                          │                          │             │
│         ▼                          ▼                          ▼             │
│  ┌─────────────┐           ┌─────────────┐           ┌─────────────┐        │
│  │ INVARIANTS  │           │ PRINCIPLES  │           │   WISDOM    │        │
│  │   (I1-I11)  │           │ (GP-001-008)│           │   BLOCKS    │        │
│  │ IRREMEDIAVEL│           │  Governance │           │  (Sealed)   │        │
│  └─────────────┘           └─────────────┘           └─────────────┘        │
│                                                                             │
│                         SANDBOX-CORE :8091                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Context Request Flow (Agent → Bibliotecario)

When any agent needs to act, it SHOULD first request constitutional context:

```
┌───────────────┐                    ┌───────────────┐
│  W-LEGAL-001  │                    │  W-LIB-001    │
│    Legal      │                    │  Bibliotecario│
└───────┬───────┘                    └───────┬───────┘
        │                                    │
        │  POST /library/context             │
        │  {                                 │
        │    "requesting_agent": "W-LEGAL",  │
        │    "action_type": "DECISION",      │
        │    "include": "invariants,wisdom"  │
        │  }                                 │
        │ ──────────────────────────────────►│
        │                                    │
        │                                    │ ┌─────────────────────┐
        │                                    │ │ Builds package:     │
        │                                    │ │ • I1, I6, I9        │
        │                                    │ │ • GP-001, GP-008    │
        │                                    │ │ • Critical Reminders│
        │                                    │ └─────────────────────┘
        │                                    │
        │  {                                 │
        │    "governance_principle": "AI...",│
        │    "sections": {                   │
        │      "invariants": {...},          │
        │      "principles": {...}           │
        │    },                              │
        │    "critical_reminders": [...]     │
        │  }                                 │
        │ ◄──────────────────────────────────│
        │                                    │
        ▼                                    │
┌───────────────┐                            │
│ Legal now     │                            │
│ knows limits  │                            │
│ before acting │                            │
└───────────────┘                            │
```

---

## 3. Distribution to All Constellation Agents

```
                              W-LIB-001
                            ┌─────────────┐
                            │ BIBLIOTECARIO│
                            │             │
                            │ 11 Invariants│
                            │ 8 Principles │
                            │ 5 Wisdom     │
                            │ 9 Agents     │
                            └──────┬──────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           │                       │                       │
     ┌─────┴─────┐           ┌─────┴─────┐           ┌─────┴─────┐
     │ /context  │           │/grove-brief│          │/invariants│
     │ (on       │           │ (pre-      │           │(direct    │
     │ demand)   │           │ debate)    │           │ query)    │
     └─────┬─────┘           └─────┬─────┘           └─────┬─────┘
           │                       │                       │
           ▼                       ▼                       ▼
    ┌──────────────────────────────────────────────────────────────┐
    │                                                              │
    │   Legal     Notary     Comply    Communique                  │
    │                                                              │
    │   Journalist  Auditor   Accounting   Architect               │
    │                                                              │
    │   Grove Arena   WICK   VPR   META   VIRTUE                   │
    │                                                              │
    └──────────────────────────────────────────────────────────────┘
```

---

## 4. Grove Arena — Constitutional Briefing Injection

Before any Grove debate starts, all participants receive a constitutional briefing:

```
┌─────────────────────────────────────────────────────────────────────┐
│                      GROVE ARENA                                    │
│                    Structured Debate                                │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               │ BEFORE debate starts
                               ▼
                    ┌─────────────────────┐
                    │ POST /grove-brief   │
                    │ {                   │
                    │   topic: "...",     │
                    │   participants: []  │
                    │ }                   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ╔═════════════════════╗
                    ║    BIBLIOTECARIO    ║
                    ╚══════════╤══════════╝
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ governance_     │  │ binding_        │  │ debate_rules    │
│ anchor          │  │ invariants      │  │                 │
│                 │  │                 │  │ 1. Reference I  │
│ "AI processes.  │  │ I9: Autonomy    │  │ 2. Explainable  │
│  Human decides. │  │     Prohibition │  │ 3. Human veto   │
│  WINDI          │  │                 │  │ 4. Record dissent│
│  guarantees."   │  │ I6: Transparency│  │ 5. 2/3 consensus│
│                 │  │                 │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │    BRIEFING INJECTED INTO     │
              │    ALL PARTICIPANTS           │
              │    BEFORE SPEAKING            │
              └────────────────────────────────┘
```

---

## 5. Constitutional Knowledge Hierarchy

```
                    ╔═════════════════════════════════════╗
                    ║           LEVEL 0 — IMMUTABLE       ║
                    ║   "Hardcoded in Source Code"        ║
                    ╚═════════════════════════════════════╝
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
        ▼                             ▼                             ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│  INVARIANTS   │           │  PRINCIPLES   │           │THREE DRAGONS  │
│    (11)       │           │    (8)        │           │   PROTOCOL    │
│               │           │               │           │               │
│ I1  Sovereignty│          │ GP-001 Core   │           │  Guardian     │
│ I2  Forensic  │           │ GP-002 Dragons│           │  Architect    │
│ I3  Trilingual│           │ GP-003 Foren. │           │  Witness      │
│ I4  Privacy   │           │ GP-004 Grace  │           │               │
│ I5  Service   │           │ GP-005 Git    │           │ Human > Code  │
│ I6  Transpare.│           │ GP-006 Read   │           │    > AI       │
│ I7  Isolation │           │ GP-007 Loop   │           │               │
│ I8  Audit     │           │ GP-008 Tree   │           └───────────────┘
│ I9  AUTONOMY  │           │               │
│ I10 SGE       │           └───────────────┘
│ I11 Constel.  │
│               │
│ IRREMEDIAVEL  │
└───────────────┘

                    ╔═════════════════════════════════════╗
                    ║         LEVEL 1 — SEALED            ║
                    ║   "Ledger Receipt + Hash"           ║
                    ╚═════════════════════════════════════╝
                                      │
                                      ▼
                           ┌───────────────────┐
                           │   WISDOM BLOCKS   │
                           │       (5)         │
                           │                   │
                           │ WB-001 Birth      │
                           │ WB-002 Tree       │
                           │ WB-003 Constel.   │
                           │ WB-004 3 Dragons  │
                           │ WB-005 SGE        │
                           │                   │
                           │ Maturity: N4-N5   │
                           └───────────────────┘

                    ╔═════════════════════════════════════╗
                    ║        LEVEL 2 — EXTENSIBLE         ║
                    ║   "Human Dragon can add"            ║
                    ╚═════════════════════════════════════╝
                                      │
                                      ▼
                           ┌───────────────────┐
                           │ KNOWLEDGE ENTRIES │
                           │                   │
                           │ POST /knowledge   │
                           │ human_approved:   │
                           │    true (I9 gate) │
                           │                   │
                           │ Persisted in      │
                           │ JSON/SQLite       │
                           └───────────────────┘
```

---

## 6. Knowledge Lifecycle with I9 Gate

```
    ┌─────────────────────────────────────────────────────────────┐
    │                                                             │
    │  HUMAN DRAGON                                               │
    │  (Only source of new knowledge)                             │
    │                                                             │
    └──────────────────────────┬──────────────────────────────────┘
                               │
                               │ POST /library/knowledge
                               │ { human_approved: true }
                               │
                               ▼
                    ┌─────────────────────┐
                    │   I9 GATE CHECK     │
                    │                     │
                    │  human_approved?    │
                    │  ┌───┐     ┌───┐    │
                    │  │YES│     │ NO│    │
                    │  └─┬─┘     └─┬─┘    │
                    └────┼────────┼───────┘
                         │        │
                         │        └──────► 403 BLOCKED
                         │                 "I9: AI proposes,
                         │                  Human decides"
                         ▼
              ┌─────────────────────┐
              │   KNOWLEDGE STORE   │
              │                     │
              │  library_knowledge  │
              │      .json          │
              │                     │
              │  ID: KE-xxxxxxxx    │
              │  content_hash: ...  │
              │  approved_by:       │
              │    "Human Dragon"   │
              └──────────┬──────────┘
                         │
                         │ Available to
                         │ entire constellation
                         ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                                                             │
    │   GET /library/knowledge                                    │
    │   GET /library/context?include=knowledge                    │
    │                                                             │
    │   All agents access updated knowledge                       │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
```

---

## 7. Complete Integration Map

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║                        WINDI CONSTITUTIONAL ECOSYSTEM                         ║
║                                                                               ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │                          BIBLIOTECARIO                                  │  ║
║  │                         (Central Knowledge)                             │  ║
║  └───────────────────────────────────┬─────────────────────────────────────┘  ║
║                                      │                                        ║
║     ┌────────────────────────────────┼────────────────────────────────┐       ║
║     │                                │                                │       ║
║     ▼                                ▼                                ▼       ║
║  ┌──────────┐                 ┌──────────┐                     ┌──────────┐   ║
║  │ DOMAIN   │                 │ DEBATE   │                     │ EVIDENCE │   ║
║  │ AGENTS   │                 │ SYSTEM   │                     │ CHAIN    │   ║
║  │          │                 │          │                     │          │   ║
║  │  Legal   │◄───context────►│  Grove   │◄────grove-brief────►│  Ledger  │   ║
║  │  Notary  │                 │  Arena   │                     │  Vault   │   ║
║  │  Comply  │                 │          │                     │  Audit   │   ║
║  │  Comm.   │                 │ Debates  │                     │          │   ║
║  │  Journ.  │                 │ use I    │                     │ Virtue   │   ║
║  │  Acct.   │                 │ context  │                     │ Receipts │   ║
║  │          │                 │          │                     │          │   ║
║  └──────────┘                 └──────────┘                     └──────────┘   ║
║       │                            │                                │         ║
║       │                            │                                │         ║
║       └────────────────────────────┼────────────────────────────────┘         ║
║                                    │                                          ║
║                                    ▼                                          ║
║                         ┌────────────────────┐                                ║
║                         │   HUMAN DRAGON     │                                ║
║                         │   (Final Decision) │                                ║
║                         │                    │                                ║
║                         │ "AI processes.     │                                ║
║                         │  Human decides.    │                                ║
║                         │  WINDI guarantees."│                                ║
║                         └────────────────────┘                                ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 8. API Endpoints Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/library/health` | GET | Health check |
| `/library/context` | POST | Get constitutional context for an agent |
| `/library/grove-brief` | POST | Get debate briefing for Grove Arena |
| `/library/invariants` | GET | List all 11 invariants |
| `/library/principles` | GET | List all 8 governance principles |
| `/library/agents` | GET | List all constellation agents |
| `/library/wisdom` | GET | List sealed wisdom blocks |
| `/library/knowledge` | GET | List extensible knowledge |
| `/library/knowledge` | POST | Add knowledge (I9 gated) |

---

## 9. Action Type Reminders

The Bibliotecario provides context-specific reminders based on action type:

| Action Type | Key Reminders |
|-------------|---------------|
| `EXPORT` | I2 (Forensic), I3 (Trilingual) |
| `DECISION` | I9 (Autonomy), I6 (Transparency) |
| `COMMUNICATION` | I3 (Trilingual), GP-006 |
| `DATA_PROCESSING` | I4 (Privacy), I8 (Audit) |
| `GENERAL` | GP-001, I9 |

---

## 10. Integration Code Example

```python
import requests

def get_constitutional_context(agent_id: str, action_type: str) -> dict:
    """Request constitutional context before acting."""
    response = requests.post(
        "http://localhost:8091/library/context",
        json={
            "requesting_agent": agent_id,
            "action_type": action_type,
            "include": "invariants,principles",
            "lang": "en"
        }
    )
    return response.json()

# Usage in any agent
context = get_constitutional_context("W-LEGAL-001", "DECISION")
print(f"Principle: {context['governance_principle']}")
print(f"Reminders: {context['critical_reminders']}")
```

---

## Summary

The Bibliotecario acts as the **single source of constitutional truth**. Before any agent acts, it can (and should) request context. Knowledge always flows from the center (Bibliotecario) to the periphery (specialized agents), ensuring that **the entire constellation operates under the same 11 invariants**.

**Principle**: "O Bibliotecario nao cria — ele preserva, organiza e ilumina."

---

*Sealed: 2026-03-10 | W-LIB-001 v1.0.0 | OM SHANTI*
