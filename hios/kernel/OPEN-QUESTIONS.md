# OPEN-QUESTIONS — WINDI-HIOS Kernel

```
STATUS:         DRAFT-SKELETON
NOT SEALED
NOT CANONICAL
PENDING GUARDIAN REVIEW
```

---

## Purpose

Consolidated list of all open questions requiring Architect refinement
before §266 can seal.

---

## Question Index

| ID | Source File | Question | Priority | Status |
|----|-------------|----------|----------|--------|
| Q1 | spine_bindings.md | **How does the Kernel verify that I1-I9 themselves did not drift?** | **CRITICAL** | open |
| Q2 | actors.schema.json | How to handle agent actors without persistent DID? | high | open |
| Q3 | actors.schema.json | Session-scoped vs persistent actor identity? | high | open |
| Q4 | authority.schema.json | **What happens when Human Dragon is unavailable?** | **CRITICAL** | open |
| Q5 | authority.schema.json | Can Guardian block indefinitely without escalation? | medium | open |
| Q6 | context.schema.json | How to handle stale context (session > 24h)? | medium | open |
| Q7 | context.schema.json | Context inheritance across PingPong cycles? | medium | open |
| Q8 | admissibility.schema.json | Admissibility expiration window? | high | open |
| Q9 | admissibility.schema.json | Re-admission after denial - what changes? | medium | open |
| Q10 | execution.schema.json | Execution timeout policy? | medium | open |
| Q11 | execution.schema.json | Partial execution rollback strategy? | high | open |
| Q12 | proof.schema.json | Merkle aggregation for high-volume STANDARD receipts? | medium | open |
| Q13 | proof.schema.json | EPHEMERAL receipt retention policy enforcement? | low | open |
| Q14 | continuity.schema.json | Maximum session lineage depth? | low | open |
| Q15 | continuity.schema.json | Orphan session cleanup policy? | low | open |
| Q16 | threat_model.md | How to detect malicious Guardian? | medium | open |
| Q17 | threat_model.md | Recovery from compromised Human Dragon session? | high | open |
| Q18 | threat_model.md | Multi-party approval for CRITICAL mutations? | medium | open |
| Q19 | failure_modes.md | Automatic vs manual recovery triggers? | medium | open |
| Q20 | failure_modes.md | Failure notification channels? | low | open |
| Q21 | recovery_protocol.md | Recovery receipt chain separate from main chain? | medium | open |
| Q22 | recovery_protocol.md | Maximum auto-recovery attempts before escalation? | low | open |
| Q23 | mutation_classes.md | Who can reclassify after initial classification? | high | open |
| Q24 | mutation_classes.md | CRITICAL→STANDARD downgrade ever allowed? | medium | open |
| Q25 | mutation_classes.md | Threshold for "constitutional impact"? | high | open |
| Q26 | schema_versioning_policy.md | Schema registry location? | low | open |
| Q27 | schema_versioning_policy.md | Automated migration tooling? | low | open |
| Q28 | schema_versioning_policy.md | Multi-version coexistence period? | medium | open |
| Q29 | kernel_manifest.json | How does Kernel detect at runtime that a service is using an outdated schema version? | high | open |
| Q30 | context.schema.json | Minimum CBP version Kernel context layer requires? | medium | open |
| Q31 | recovery_protocol.md | Buffer TTL, signature requirements, and CRITICAL exclusion policy for R7? | high | open |

---

## Priority Distribution

| Priority | Count | Percentage |
|----------|-------|------------|
| CRITICAL | 2 | 6% |
| high | 10 | 32% |
| medium | 13 | 42% |
| low | 6 | 19% |

**Total:** 31 questions (28 original + 3 Guardian additions)

---

## CRITICAL Questions (Must Resolve Before §266)

### Q1: Spine Integrity Verification

> **How does the Kernel verify that I1-I9 themselves did not drift?**

**Source:** spine_bindings.md

**Current Thinking:**
1. CLAUDE.md as constitutional source of truth
2. Hash invariant definitions at session start
3. Compare against known-good hash from last sealed §
4. Guardian as constitutional witness
5. If drift → escalate to Human Dragon

**Why Critical:**
Without this, the Kernel can become a binding map over a drifted Spine.
The map would be accurate to a wrong territory.

**Next Step:**
Architect decomposes into Q1.a–Q1.d (per Guardian Obs 1), then proposes.

**Suggested Decomposition:**
- Q1.a: What constitutes "drift" of an invariant? (word change, semantic change, application change?)
- Q1.b: Who is the canonical source? CLAUDE.md? §244? Both with reconciliation hash?
- Q1.c: Verification frequency? Each session? Each CRITICAL mutation?
- Q1.d: Who signs the "Spine did not drift" declaration? Guardian? HD? Both?

---

### Q4: Human Dragon Unavailability (Elevated to CRITICAL)

> **What happens when Human Dragon is unavailable?**

**Source:** authority.schema.json

**Why Critical (Guardian elevation):**
Q4 touches I9 directly. If I9 = Prohibition of Autonomy Escalation, and HD is
the only one who can authorize CRITICAL mutations, then HD unavailability =
system blocked by design. This may be correct (prefer blocking to violation),
or may need temporary delegation mechanism (Guardian + Architect as joint
signatories).

**Related Questions:**
- Q16: How to detect malicious Guardian?
- Q17: Recovery from compromised Human Dragon session?

**Next Step:**
Architect addresses Q4 + Q17 + Q16 as a cluster (failure of arbiters themselves).

---

## Process

1. Architect addresses questions in priority order
2. Guardian reviews each answer
3. Human Dragon approves refinements
4. Questions move from `open` to `resolved`
5. When all CRITICAL/high resolved → §266 can seal

---

## Resolution Format

When a question is resolved:

```markdown
| Q1 | spine_bindings.md | How verify I1-I9 drift? | CRITICAL | **resolved** |

### Q1 Resolution

**Answer:** [concrete mechanism]
**Approved by:** Guardian + Human Dragon
**Date:** YYYY-MM-DD
**Incorporated in:** [file updated]
```

---

*OPEN-QUESTIONS · DRAFT-SKELETON*
*Liga IA+H · Kempten, Bavaria · 2026*
