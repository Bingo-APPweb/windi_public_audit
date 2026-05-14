# Spine Bindings — Kernel ↔ WINDI Spine

```
STATUS:         DRAFT-SKELETON
NOT SEALED
NOT CANONICAL
PENDING GUARDIAN REVIEW
```

---

## Purpose

This document maps each Kernel concern to its **existing WINDI primitive**.

The Kernel does NOT duplicate the Spine. It BINDS to it.

---

## Binding Table

| Kernel Concern | Existing WINDI Primitive | Binding Status | Open Questions |
|----------------|--------------------------|----------------|----------------|
| **Identity** | DID Genesis :8096 / actor registry | BOUND | Q2, Q3: Agent actors, session vs persistent |
| **Proof** | Forensic Ledger :8101 `/api/receipts` | BOUND | Q12, Q13: Merkle aggregation, EPHEMERAL retention |
| **Continuity** | CBP §261 + PingPong §263 + INDEX | BOUND | Q14, Q15: Lineage depth, orphan cleanup |
| **Authority** | I9 + Human Dragon + Three Dragons | BOUND | Q4, Q5: HD unavailability, Guardian blocking |
| **Admissibility** | I9 Gate + Guardian Review | BOUND | Q8, Q9: Expiration window, re-admission |
| **Execution** | Construtor / service-specific execution | BOUND | Q10, Q11: Timeout, partial rollback |
| **Drift** | W-LEXICON / future §265 metrics | PENDING | §265 not yet sealed |
| **Spine Integrity** | §244 Three Pillars + Invariants I1-I9 | **OPEN** | **Q1: How does the Kernel verify that I1-I9 themselves did not drift?** |

---

## Q1 Resolution: Spine Integrity Verification

> **Q1: How does the Kernel verify that I1-I9 themselves did not drift?**
>
> **STATUS: RESOLVED** — 2026-05-14 · Architect proposal

### Drift Type Classification

| Type | Descrição | Severidade |
|------|-----------|------------|
| **Lexical** | Palavra alterada sem mudar semântica | LOW |
| **Semantic** | Significado do invariante alterado | CRITICAL |
| **Application** | Invariante aplicado de forma diferente | HIGH |
| **Scope** | Invariante expandido/contraído sem selo | CRITICAL |

### Canonical Source Hierarchy

```
1. CLAUDE.md § Constituição Nuclear (fonte primária)
2. Receipts §XXX que selaram cada invariante (prova de origem)
3. CLAUDE-HISTORY.md (contexto de decisão)
```

### Verification Triggers

| Gatilho | Verificação | Acção se Drift |
|---------|-------------|----------------|
| **Session Start** | Hash I1-I17 vs último CBP | Warning no CBP output |
| **CRITICAL Mutation** | Full Spine check | Bloqueia mutação |
| **Weekly Cron** | Background audit | Alerta Guardian + HD |

### Signature Rules (Dual Witness)

```
STANDARD mutations:
  → Guardian assina sozinho (auditável)

CRITICAL mutations:
  → Guardian assina primeiro
  → Human Dragon contra-assina
  → Ambas assinaturas no receipt
```

### SPINE-LOCK Rule

> Se Guardian detecta drift E HD não está disponível → sistema entra em **SPINE-LOCK** (apenas leitura, zero mutações CRITICAL).

### Implementation

Schema: `spine_integrity.schema.json`
Script: `spine_integrity_check.sh` (pending implementation)

---

## Binding Details

### Identity → DID Genesis :8096

```
Kernel calls:   GET /api/genesis/verify/{did}
Returns:        Actor identity, tier, verification status
Uses:           actors.schema.json
```

### Proof → Forensic Ledger :8101

```
Kernel calls:   POST /api/receipts (seal)
                GET /api/receipts/{id} (verify)
Returns:        Receipt ID, content_hash, timestamp
Uses:           proof.schema.json
```

### Continuity → CBP + PingPong

```
Kernel reads:   /opt/windi/claudeWeb/INDEX.md
                cognitive-bind-module.sh output
Writes:         CLAUDE-HISTORY.md entries
                claudeWeb/ chapters
Uses:           continuity.schema.json
```

### Authority → Three Dragons

```
Guardian:       Reviews, blocks, approves
Architect:      Proposes, designs
Witness:        Observes, validates
Construtor:     Executes
Human Dragon:   Final decision (I9)
Uses:           authority.schema.json
```

### Admissibility → I9 Gate

```
Check:          Is I9 required for this action?
Gate:           human_approved=true before seal
Expiration:     Approval is ephemeral (per §199)
Uses:           admissibility.schema.json
```

### Execution → Service Layer

```
Construtor:     Executes kernel-gated operations
Services:       W-SITES, W-MAIL, etc. execute domain ops
Kernel:         Coordinates, does not execute
Uses:           execution.schema.json
```

### Drift → W-LEXICON (pending §265)

```
Future:         §265 Drift Monitor Metrics
Measures:       Structural density, hyperdefensive patterns, semantic distance
Status:         PENDING - not bound yet
```

### Spine Integrity → I1-I9 + Three Pillars

```
Reference:      §244 (Soberania, Acessibilidade, Memória)
Invariants:     I1-I9 as defined in CLAUDE.md
Verification:   OPEN QUESTION (Q1)
```

---

## Non-Duplication Guarantee

The Kernel MUST NOT:
- Create its own identity system (use DID Genesis)
- Create its own receipt system (use Forensic Ledger)
- Create its own continuity system (use CBP + PingPong)
- Override Three Dragons authority
- Bypass I9 human approval gate

If the Kernel duplicates, it violates its own definition as a "binding map".

---

*Spine Bindings · DRAFT-SKELETON*
*Liga IA+H · Kempten, Bavaria · 2026*
