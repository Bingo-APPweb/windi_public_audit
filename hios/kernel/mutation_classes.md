# Mutation Classes — WINDI-HIOS Kernel

```
STATUS:         DRAFT-REFINED
NOT SEALED (pending §266)
PARTIALLY RATIFIED (G4.3 Reach Precedence Doctrine)
HD Ratification: 2026-05-14
```

---

## Purpose

Define the three classes of mutations and their governance requirements.

---

## The Three Classes

### CRITICAL

**Definition:** Constitutional changes, doctrine, seals, invariant modifications

**Examples:**
- Sealing a new § section
- Modifying invariants I1-I9
- Creating new constitutional receipts
- Bootstrap operations
- Spine integrity changes

**Authority Required:**
- I9 Human Dragon approval: **MANDATORY**
- Guardian review: **MANDATORY**
- Architect proposal: **MANDATORY**

**Receipt Type:** constitutional

**Retention:** Permanent (never deleted)

**Escalation:** Cannot timeout; blocks until Human Dragon decides

---

### STANDARD

**Definition:** Normal operations with audit trail, operational receipts

**Examples:**
- Creating user content
- Service operations (W-SITES, W-MAIL)
- Session state changes
- Normal Ledger receipts
- PingPong chapter deposits

**Authority Required:**
- Actor identity: **MANDATORY**
- Context verification: **MANDATORY**
- I9: Only if action scope escalates
- Guardian: Available but not blocking

**Receipt Type:** operational

**Retention:** 90 days minimum

**Escalation:** Timeout after 24h → escalate to Guardian

---

### EPHEMERAL

**Definition:** Technical operations with no constitutional impact

**Examples:**
- Cache reads/writes
- Session-scoped state
- Skeleton receipts (like this installation)
- Health checks
- Read-only queries

**Authority Required:**
- Actor identity: **MANDATORY**
- Context: Optional

**Receipt Type:** ephemeral (or no receipt)

**Retention:** 7 days or session-scoped

**Escalation:** Auto-timeout, no escalation

---

## Classification Decision Tree

```
Is the action constitutional?
  YES → CRITICAL
  NO  ↓

Does it create persistent state?
  YES → STANDARD
  NO  ↓

Is it session-scoped or transient?
  YES → EPHEMERAL
  NO  → STANDARD (default safe)
```

---

## Reach Precedence Doctrine (G4.3 Ratified 2026-05-14)

> **"A dimensão `reach: external` tem precedência sobre a classificação de impacto declarada."**

Operação inicialmente classificada como EPHEMERAL ou STANDARD com efeito externo irreversível
é tratada como classe superior para efeitos de autoridade e auditoria, independentemente da
retenção técnica do registo.

**Regra operacional:**
- `reach: internal` → mantém classificação original
- `reach: external` + `reversibility: irreversible` → escalona automaticamente

**Durante HD-GRACE:**
- STANDARD-I-EXTERNAL → reclassificado como CRITICAL (queued)
- EPHEMERAL-I-EXTERNAL → reclassificado como STANDARD-I-EXTERNAL → CRITICAL (queued)

**Razão constitucional:** Consequência externa supera auto-classificação interna. O sistema
classifica pela natureza do efeito no mundo, não pela intenção declarada do actor.

**Janela de reversibilidade:** T+5 minutos medidos pelo timestamp do receipt no Ledger
(clock canónico do sistema). Após T+5, a mutação é considerada irreversível.

---

## Misclassification Risks

| Actual | Classified As | Risk |
|--------|---------------|------|
| CRITICAL | STANDARD | Constitutional bypass |
| CRITICAL | EPHEMERAL | No permanent record |
| STANDARD | EPHEMERAL | Lost audit trail |
| EPHEMERAL | CRITICAL | Over-governance, slowdown |
| EXTERNAL | INTERNAL | Sovereignty breach (G4.3) |

**Mitigation:** Guardian review for reclassification requests + automatic reach detection

---

## First EPHEMERAL Receipt (Bootstrap)

This skeleton installation generates the first EPHEMERAL receipt:
- Classification: EPHEMERAL
- No constitutional parent
- No sealing
- Marks bootstrap surface preparation

This tests the EPHEMERAL class in practice.

---

## Open Questions (Classification)

- Q23: Who can reclassify after initial classification?
- Q24: CRITICAL→STANDARD downgrade ever allowed?
- Q25: Threshold for "constitutional impact"?

---

*Mutation Classes · DRAFT-SKELETON*
*Liga IA+H · Kempten, Bavaria · 2026*
