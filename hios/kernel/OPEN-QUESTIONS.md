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
| Q1 | spine_bindings.md | **How does the Kernel verify that I1-I9 themselves did not drift?** | **CRITICAL** | **RESOLVED** |
| Q2 | actors.schema.json | How to handle agent actors without persistent DID? | high | open |
| Q3 | actors.schema.json | Session-scoped vs persistent actor identity? | high | open |
| Q4 | authority.schema.json | **What happens when Human Dragon is unavailable?** | **CRITICAL** | **RESOLVED** |
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

| Priority | Count | Open | Proposed | Resolved |
|----------|-------|------|----------|----------|
| CRITICAL | 2 | 0 | 0 | **2** |
| high | 10 | 10 | 0 | 0 |
| medium | 13 | 13 | 0 | 0 |
| low | 6 | 6 | 0 | 0 |

**Total:** 31 questions · **29 open** · **0 proposed** · **2 resolved (Q1, Q4)**

**§266 STATUS:** CRITICAL questions resolved. Etapa 1 A-Progressivo COMPLETE.
- Q1 (Genesis) → RESOLVED via Genesis Ceremony v2 · Ratified 2026-05-14
- Q4 (HD Unavailability) → RESOLVED via Matriz Reversibilidade v2 · Ratified 2026-05-14
- Genesis Ceremony execution pending (scheduled as deliberate act)

---

## CRITICAL Questions — RESOLVED

### Q1: Spine Integrity Verification ✅ RESOLVED

> **How does the Kernel verify that I1-I9 themselves did not drift?**

**Status:** RESOLVED · 2026-05-14 · HD Ratification
**Schema:** `spine_integrity.schema.json` (RATIFIED)
**Doc:** `spine_bindings.md` (RATIFIED)

**Architect Proposal Summary:**

| Sub-Q | Answer |
|-------|--------|
| Q1.a Drift types | lexical (LOW), semantic (CRITICAL), application (HIGH), scope (CRITICAL) |
| Q1.b Canonical source | CLAUDE.md (primary) → Receipts (origin) → CLAUDE-HISTORY (context) |
| Q1.c Verification triggers | session_start, critical_mutation, weekly_cron |
| Q1.d Signatures | STANDARD: Guardian alone · CRITICAL: Guardian + HD dual witness |

**Guardian Review — 4 Refinements Required:**

| # | Issue | Guardian Observation |
|---|-------|---------------------|
| G1.1 | **Lexical LOW is dangerous** | Em texto constitucional "deve"→"pode" muda tudo. Eliminar LOW ou redefinir como "requires semantic review" |
| G1.2 | **Genesis Problem** | Qual receipt original selou I1-I9 com hash? Se não existe, bootstrap requer assinatura HD presencial |
| G1.3 | **Hash só detecta texto** | Drift de aplicação não detectado por sha256. Falta auditoria de aplicação (declarar como gap v0.1) |
| G1.4 | **Watchdog do watchdog** | Se cron comprometido, ninguém nota. Falta heartbeat invertido: ausência de receipt 8 dias = suspeita |

---

### Q4: Human Dragon Unavailability ✅ RESOLVED

> **What happens when Human Dragon is unavailable?**

**Status:** RESOLVED · 2026-05-14 · HD Ratification
**Schema:** `authority.schema.json` (RATIFIED)

**Architect Proposal Summary:**

| State | Threshold | Capabilities |
|-------|-----------|--------------|
| **HD-ACTIVE** | HD responded < 24h | Full operations |
| **HD-GRACE** | 24h-72h absent | STANDARD: Guardian+Architect · CRITICAL: queued |
| **HD-LOCK** | >72h absent | Read-only · Zero mutations |

**Principle:** *"Preferir bloqueio a violação de I9."*

**Guardian Review — 5 Refinements Required:**

| # | Issue | Guardian Observation |
|---|-------|---------------------|
| G4.1 | **24h/72h arbitrários** | Sem justificação. Declarar como parâmetros configuráveis com racional documentado |
| G4.2 | **Guardian+Architect em GRACE viola I9?** | Amarrar explicitamente a I9. Cláusula: STANDARD com acção externa irreversível → CRITICAL |
| G4.3 | **Falta eixo reversibilidade** | STANDARD irreversível (email, receipt) deve ir para fila CRITICAL em GRACE |
| G4.4 | **Sessões em curso em HD-LOCK** | O que acontece a Construtor a meio de execução? Aborto? Finalização? Receipt parcial? |
| G4.5 | **Q16/Q17 subdimensionados** | Q17 (HD comprometido) requer árbitro externo. Quem? Registar ex ante |

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
