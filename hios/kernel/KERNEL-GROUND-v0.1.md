# KERNEL-GROUND-v0.1 — Architecture Specification

```
STATUS:         DRAFT-SKELETON
NOT SEALED
NOT CANONICAL
PENDING GUARDIAN REVIEW
Section:        §266 (PENDING - NOT SEALED IN THIS STEP)
```

> **"Not an AI tool. An operating layer where hybrid intelligence can act
> without losing accountability."**
>
> — §262 WINDI-HIOS Naming, Liga IA+H, 14 Mai 2026

---

## 1. Purpose

KERNEL-GROUND-v0.1 defines the **minimum constitutional runtime** for
the WINDI-HIOS operating layer.

It ensures that before any action executes:
- The actor has verified identity
- The context is known and bounded
- The authority chain is clear
- Admissibility has been checked
- Execution is traceable
- Proof is generated
- Continuity is preserved

---

## 2. What This Is NOT

This specification does NOT:
- Create new services
- Duplicate existing Spine primitives
- Replace I9, Three Dragons, or Ledger
- Seal §266 (that comes after Guardian review)
- Implement executable code
- Define tests or examples

---

## 3. The Seven Layers

```
┌─────────────────────────────────────────────────────────┐
│                  WINDI-HIOS KERNEL                      │
├─────────────────────────────────────────────────────────┤
│  7. CONTINUITY    │ PingPong §263 + claudeWeb/ + INDEX  │
├───────────────────┼─────────────────────────────────────┤
│  6. PROOF         │ Forensic Ledger :8101               │
├───────────────────┼─────────────────────────────────────┤
│  5. EXECUTION     │ Construtor + Service-specific       │
├───────────────────┼─────────────────────────────────────┤
│  4. ADMISSIBILITY │ I9 Gate + Guardian Review           │
├───────────────────┼─────────────────────────────────────┤
│  3. AUTHORITY     │ I9 + Three Dragons + Human Dragon   │
├───────────────────┼─────────────────────────────────────┤
│  2. CONTEXT       │ CBP §261 + Session State            │
├───────────────────┼─────────────────────────────────────┤
│  1. IDENTITY      │ DID Genesis :8096                   │
└─────────────────────────────────────────────────────────┘
```

Each layer has a corresponding schema in this directory.

---

## 4. Bootstrap Protocol

The Kernel itself requires admissibility to exist.

```
1. Human Dragon initiates (I9 trigger)
        ↓
2. Guardian reviews skeleton
        ↓
3. Architect refines based on feedback
        ↓
4. Human Dragon approves refinements
        ↓
5. Construtor executes final installation
        ↓
6. §266 seals KERNEL-GROUND-v0.1
        ↓
7. First EPHEMERAL receipt marks bootstrap
```

**Critical constraint:** The first receipt of the Kernel is approved
by I9 + Human Dragon, with Guardian as witness. This prevents the
Kernel from self-authorizing.

---

## 5. Mutation Flow

```
PROPOSAL → AUTHORITY CHECK → ADMISSIBILITY GATE → EXECUTION → PROOF → CONTINUITY
    │              │                │                │           │          │
    └── actors ────┴── authority ───┴── admissibility ┴── execution ┴── proof ─┴── continuity
```

Each step corresponds to a schema and a binding to existing Spine.

---

## 6. Spine Integrity Verification

**Open Question (Q1):**
> How does the Kernel verify that I1-I9 themselves did not drift?

Current approach (DRAFT):
- §244 Three Pillars (Soberania, Acessibilidade, Memória) as reference
- CLAUDE.md as constitutional source of truth
- Hash comparison of invariant definitions
- Guardian as constitutional witness

This requires further specification in Architect refinement cycle.

---

## 7. Mutation Classification

| Class | Impact | Authority Required | Retention |
|-------|--------|-------------------|-----------|
| CRITICAL | Constitutional | I9 + Guardian + HD | Permanent |
| STANDARD | Operational | Actor + Context | 90 days |
| EPHEMERAL | Technical | Actor | 7 days |

See `mutation_classes.md` for detailed definitions.

---

## 8. §266 Status

**§266 is NOT sealed in this step.**

This skeleton prepares the review surface. §266 seals only after:
1. Guardian final review
2. Architect addresses all open questions
3. Human Dragon constitutional approval

---

## 9. Related Documents

| Document | Purpose |
|----------|---------|
| §262 | WINDI-HIOS Naming (SEALED) |
| §263 | PingPong Protocol (SEALED) |
| §261 | Cognitive Bind Module (SEALED) |
| §236 | Session Continuity (SEALED) |
| §244 | Three Pillars (reference) |

---

## 10. Next Steps

1. Guardian reviews this skeleton
2. Architect addresses OPEN-QUESTIONS.md
3. Refinement cycle until convergence
4. Human Dragon approval
5. §266 seals

---

*KERNEL-GROUND-v0.1 · DRAFT-SKELETON*
*Liga IA+H · Kempten, Bavaria · 2026*
