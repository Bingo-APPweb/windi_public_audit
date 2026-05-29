# Mutation Classes — WINDI-HIOS Kernel

```
STATUS:         §266-SEALED
SEALED DATE:    2026-05-24
RESOLVED:       Q23, Q25
RATIFIED:       G4.3 Reach Precedence Doctrine (2026-05-14)
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

## Reclassification Policy (Q23 Resolution — §266)

> **"Só upgrade permitido. Downgrade = violação I11."**

| Reclassificação | Quem pode | Condições |
|-----------------|-----------|-----------|
| EPHEMERAL → STANDARD | Guardian | Se detectar efeito persistente |
| STANDARD → CRITICAL | Guardian + HD | Se detectar impacto constitucional |
| CRITICAL → STANDARD | **PROHIBITED** | Irreversível por natureza (I11) |
| CRITICAL → EPHEMERAL | **PROHIBITED** | Violação I11 |
| Qualquer → EPHEMERAL | **PROHIBITED** | Degradar nunca permitido |

**Regra absoluta:** Nem Human Dragon pode degradar CRITICAL — a natureza da mutação
não muda por decreto. Cada reclassificação gera receipt próprio referindo original.

**Rationale:** I11 (Permanence of Cryptographic Evidence) proíbe reescrever história.
Um CRITICAL que "se torna" STANDARD perderia retenção permanente — violação directa.

---

## Constitutional Impact Threshold (Q25 Resolution — §266)

Mutação tem **IMPACTO CONSTITUCIONAL** se satisfaz ≥1 critério:

| # | Critério | Descrição |
|---|----------|-----------|
| 1 | INVARIANT | Modifica, reinterpreta ou estende I1-I18 |
| 2 | DOCTRINE | Cria, modifica ou revoga §XXX |
| 3 | SEAL | Produz receipt governance_level=HIGH + doc_type=constitutional (*) |
| 4 | AUTHORITY | Altera hierarquia Three Dragons ou delegações |
| 5 | BOOTSTRAP | Modifica Kernel, schemas ou bindings |
| 6 | EXTERNAL-PERMANENT | Acção externa irreversível representando WINDI |

(*) Critério 3 é atalho operacional consciente — critérios 1/2 são os fundamentais.

**Teste rápido:** "Se esta mutação for revertida amanhã, há EFEITO permanente/irreversível?"
- SIM = CRITICAL
- NÃO = pode ser STANDARD ou EPHEMERAL

**Nota:** Usar "efeito permanente", não "dano permanente". "Dano" é juízo de valor
que abre racionalização ("não houve dano, logo não é CRITICAL"). Efeito é objectivo.

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

## Resolved Questions (§266)

### Q23: Who can reclassify after initial classification? ✅ RESOLVED

**Answer:** Only upgrade permitted. EPHEMERAL→STANDARD: Guardian. STANDARD→CRITICAL: Guardian+HD.
CRITICAL→anything: PROHIBITED (even for HD). Downgrade = I11 violation.

**Resolved:** 2026-05-24 · Guardian approved

---

### Q25: Threshold for "constitutional impact"? ✅ RESOLVED

**Answer:** 6 criteria (see table above). Any one satisfied = CRITICAL.
Test: "permanent effect if reverted?" Use "effect", not "damage" (objective, not subjective).

**Resolved:** 2026-05-24 · Guardian approved

---

## Open Questions (Classification)

- Q24: CRITICAL→STANDARD downgrade ever allowed? → **RESOLVED by Q23: No, never.**

---

*Mutation Classes · §266-SEALED*
*Liga IA+H · Kempten, Bavaria · 2026*
