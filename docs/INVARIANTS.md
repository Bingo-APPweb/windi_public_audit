# WINDI Constitutional Invariants

**Version:** 1.0.0
**Updated:** 2026-05-12 (§250 Lei VII)
**Location:** /opt/windi/docs/INVARIANTS.md

---

## Invariant Categories

| Category | Meaning | Consequence of Violation |
|----------|---------|--------------------------|
| **IRREMEDIABLE** | Violation destroys WINDI instantly | Irreversible loss of sovereignty |
| **STRUCTURAL** | Violation corrodes slowly | Remediable by return-to-origin seal |

---

## Active Invariants

### I1 — Human Sovereignty
**Status:** IRREMEDIABLE

> The human touch activates. Never spontaneous autonomy.

All WINDI operations require human initiation. No system component may act without human trigger.

---

### I2 — Process Transparency
**Status:** Active

> Pipeline visible when requested.

GovPanel must expose the full processing pipeline to users upon request.

---

### I3 — Reversibility
**Status:** Active (until C5)

> Drafts always editable until C5. After C6 = IRREMEDIABLE.

Documents can be modified during stages C1-C5. After C6 seal, content is immutable.

---

### I6 — Conflict Exposure
**Status:** Active

> Grove Arena must show Tri-Divergence explicitly.

When Three Dragons disagree, all positions must be visible. ALL_DIFFER escalates to Human Dragon (I9).

---

### I9 — Prohibition of Autonomy Escalation
**Status:** IRREMEDIABLE

> `human_approved=true` mandatory before any seal.

No system component may:
- Auto-publish
- Auto-seal
- Execute without human approval

**Pipeline:** SGV illuminates → System suggests → **Human decides** → Ledger seals

---

### I10 — LLM Sovereignty
**Status:** Active

> Graceful fallback if external LLM unavailable.

System must continue functioning if Anthropic/OpenAI/Mistral APIs are unavailable.

---

### I11 — Permanence of Cryptographic Evidence
**Status:** IRREMEDIABLE

> Ledger receipt after C6 = immutable forever.

Once sealed, receipts cannot be modified or deleted. Hash integrity is permanent.

---

### I12 — Language Sovereign Principle
**Status:** IRREMEDIABLE

> Conversation=Universal, Document=Sovereign. Babel Tower=IRREMEDIABLE.

- Conversation: Respond in user's language
- Document: Generate in wallet/toggle language
- One document = one language
- Mixing languages in single document is constitutional violation

---

### I13 — Convergence with Sovereignty
**Status:** IRREMEDIABLE

> Every Dragon converges to structure/decision/artifact. Reflexive loop prohibited.

AI must produce concrete output. Endless reflection without action is violation.

---

### I14 — Explicit Failure Principle
**Status:** IRREMEDIABLE

> Missing data = explicit error. Placeholders mask bugs.

**Prohibited:** "unknown", "N/A", "?", "---", str(dict), "", None silencioso
**Correct:** `response["name"]` → KeyError → immediate diagnosis

---

### I16 — Creator Cartographic Sovereignty
**Status:** IRREMEDIABLE

> Map belongs to creator. GPS never sold. Publication = opt-in.

User coordinates never leave device. Zone detection computed locally. No server-side tracking.

---

### I17 — Session/Identity Separation
**Status:** Active

> Session proves presence. Identity proves agency.

| Concept | Mechanism | Function |
|---------|-----------|----------|
| Session | `windi_did_session` (HttpOnly cookie) | Proves active presence |
| Identity | `windi_did` (localStorage) | Represents agency in frontend |

Frontend never creates identity — only reflects backend.

---

### I18 — Organic Constitutional Growth
**Status:** STRUCTURAL (NEW - §250 Lei VII)

> The ecosystem can expand through multiple simultaneous fronts.

A new front is constitutionally WINDI if:
- **(a)** Reuses Spine (DID Genesis, Forensic Ledger, Receipts)
- **(b)** Preserves I1–I9 and §248 Foundation model
- **(c)** Has explicit human approval (I9)

**Violations:**
- Artificial market pressure
- Compulsory acceleration
- Hypergrowth
- Premature front amputation
- Forced convergence by external urgency

**Remediation:** Return-to-organic-growth seal

---

## Fiscal Invariant

### C6 — Fiscal Invariant
**Status:** IRREMEDIABLE

> AI prepares. Human approves. ELSTER sends. Never autonomous.

Tax documents require human approval before submission. No auto-filing.

---

## Twin Invariants (G1-G6)

### G1 — READ BEFORE TOUCH
`git log` + `git diff` + `ss -tlnp` before any modification.

### G2 — ONE DOMAIN PER SESSION
One session = one repository = one domain.

### G3 — PROPOSE ≠ EXECUTE
Change >10 lines → `git diff --stat` → await "confirm".

### G4 — COMMITS ARE CONTRACTS
Precise message, never "fix misc".

### G5 — SEALED PORTS SACRED
:8101, :8102, :8106, :8114 untouchable.

### G6 — CANVAS COMMITS PROTECTED
List + justify + approve before altering.

---

## Hierarchy

```
I1-I11 (IRREMEDIABLE) > G1-G6 > T1 > Golden Rules > Frontend Invariants > Session Instructions
```

---

## Reference Documents

| § | Document | Invariant |
|---|----------|-----------|
| §117 | I9 Human Approval Gate | I9 |
| §146 | I14 Placeholder Prohibition | I14 |
| §194 | I17 Session/Identity Separation | I17 |
| §247 | Lei IV Nomenclatura Canónica | — |
| §248 | Lei V Foundation Direction | — |
| §249 | Lei VI Three Dragons Sequence | I9 |
| §250 | Lei VII Organic Growth | I18 |

---

*WINDI Three Dragons Protocol*
*Liga IA+H — Kempten, Bavaria — 2026*
