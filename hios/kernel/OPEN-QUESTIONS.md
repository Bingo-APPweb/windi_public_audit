# OPEN-QUESTIONS — WINDI-HIOS Kernel

```
STATUS:         §266-SEALED (HIGH questions resolved)
SEALED DATE:    2026-05-24
MATURITY:       8/9 SEALED + 1 CANDIDATE = 100% resolved honestly
```

---

## Purpose

Consolidated list of all questions for the WINDI-HIOS Kernel.
All CRITICAL and HIGH priority questions are now RESOLVED.

---

## Question Index

| ID | Source File | Question | Priority | Status |
|----|-------------|----------|----------|--------|
| Q1 | spine_bindings.md | How does the Kernel verify that I1-I9 themselves did not drift? | **CRITICAL** | **RESOLVED** |
| Q2 | actors.schema.json | How to handle agent actors without persistent DID? | high | **SEALED** |
| Q3 | actors.schema.json | Session-scoped vs persistent actor identity? | high | **SEALED** |
| Q4 | authority.schema.json | What happens when Human Dragon is unavailable? | **CRITICAL** | **RESOLVED** |
| Q5 | authority.schema.json | Can Guardian block indefinitely without escalation? | medium | open |
| Q6 | context.schema.json | How to handle stale context (session > 24h)? | medium | open |
| Q7 | context.schema.json | Context inheritance across PingPong cycles? | medium | open |
| Q8 | admissibility.schema.json | Admissibility expiration window? | high | **SEALED** |
| Q9 | admissibility.schema.json | Re-admission after denial - what changes? | medium | open |
| Q10 | execution.schema.json | Execution timeout policy? | medium | open |
| Q11 | execution.schema.json | Partial execution rollback strategy? | high | **SEALED** |
| Q12 | proof.schema.json | Merkle aggregation for high-volume STANDARD receipts? | medium | open |
| Q13 | proof.schema.json | EPHEMERAL receipt retention policy enforcement? | low | open |
| Q14 | continuity.schema.json | Maximum session lineage depth? | low | open |
| Q15 | continuity.schema.json | Orphan session cleanup policy? | low | open |
| Q16 | threat_model.md | How to detect malicious Guardian? | medium | open |
| Q17 | threat_model.md | Recovery from compromised Human Dragon session? | high | **CANDIDATE** |
| Q18 | threat_model.md | Multi-party approval for CRITICAL mutations? | medium | open |
| Q19 | failure_modes.md | Automatic vs manual recovery triggers? | medium | open |
| Q20 | failure_modes.md | Failure notification channels? | low | open |
| Q21 | recovery_protocol.md | Recovery receipt chain separate from main chain? | medium | open |
| Q22 | recovery_protocol.md | Maximum auto-recovery attempts before escalation? | low | open |
| Q23 | mutation_classes.md | Who can reclassify after initial classification? | high | **SEALED** |
| Q24 | mutation_classes.md | CRITICAL→STANDARD downgrade ever allowed? | medium | **RESOLVED by Q23** |
| Q25 | mutation_classes.md | Threshold for "constitutional impact"? | high | **SEALED** |
| Q26 | schema_versioning_policy.md | Schema registry location? | low | open |
| Q27 | schema_versioning_policy.md | Automated migration tooling? | low | open |
| Q28 | schema_versioning_policy.md | Multi-version coexistence period? | medium | open |
| Q29 | kernel_manifest.json | How does Kernel detect outdated schema version at runtime? | high | **SEALED** |
| Q30 | context.schema.json | Minimum CBP version Kernel context layer requires? | medium | open |
| Q31 | recovery_protocol.md | Buffer TTL, signature requirements, and CRITICAL exclusion for R7? | high | **SEALED** |

---

## Priority Distribution

| Priority | Count | Sealed | Candidate | Open | Resolved |
|----------|-------|--------|-----------|------|----------|
| CRITICAL | 2 | 0 | 0 | 0 | **2** |
| high | 10 | **8** | **1** | 0 | 0 |
| medium | 13 | 0 | 0 | 12 | 1 |
| low | 6 | 0 | 0 | 6 | 0 |

**Total:** 31 questions
- **2 CRITICAL resolved** (Q1, Q4)
- **8 HIGH sealed** (Q2, Q3, Q8, Q11, Q23, Q25, Q29, Q31)
- **1 HIGH candidate** (Q17)
- **19 medium/low open** (future work)

**§266 STATUS:** All CRITICAL and HIGH questions resolved. Kernel maturity: **100% resolved honestly** (not 100% sealed — 1 explicitly deferred as CANDIDATE).

---

## SEALED Resolutions (§266 — 2026-05-24)

### Q2: Agent actors without persistent DID ✅ SEALED

**Answer:** Agents receive ephemeral DID: `did:windi:session:{hash8}`. Valid max 24h. Tier=FREE. Ephemeral keypair (Ed25519) for buffer signatures. Upgrade to persistent requires HD ratification — agent cannot self-request (I9 violation).

**File:** `actors.schema.json`

---

### Q3: Session-scoped vs persistent actor identity ✅ SEALED

**Answer:** Session DID: tier=FREE, max_class=STANDARD. Persistent DID: any tier, any class. CRITICAL mutations require persistent DID. **Tier and mutation class are ORTHOGONAL** — FREE actor can create STANDARD mutations.

**File:** `actors.schema.json`

---

### Q8: Admissibility expiration window ✅ SEALED

**Answer:** CRITICAL: 1h from HD admission. STANDARD: 4h from admission. EPHEMERAL: 15min from request. Clock starts at admission (not proposal) to avoid timeout during Architect→Guardian→HD cycle.

**File:** `admissibility.schema.json`

---

### Q11: Partial execution rollback strategy ✅ SEALED

**Answer:** 3 policies: ATOMIC (default), CHECKPOINT, COMPENSATE. COMPENSATE **PROHIBITED** for EXTERNAL-PERMANENT (no real inverse). Kernel forces `irreversible=true` when reach=EXTERNAL-PERMANENT — actor cannot override. FAIL_EXPLICIT for unrecoverable failures (I14).

**File:** `execution.schema.json`

---

### Q23: Who can reclassify after initial classification ✅ SEALED

**Answer:** Only upgrade permitted. EPHEMERAL→STANDARD: Guardian. STANDARD→CRITICAL: Guardian+HD. CRITICAL→anything: **PROHIBITED** (even for HD). Downgrade = I11 violation. Nature of mutation doesn't change by decree.

**File:** `mutation_classes.md`

---

### Q25: Threshold for "constitutional impact" ✅ SEALED

**Answer:** 6 criteria: INVARIANT, DOCTRINE, SEAL, AUTHORITY, BOOTSTRAP, EXTERNAL-PERMANENT. Any one = CRITICAL. Test: "permanent EFFECT if reverted?" (not "damage" — avoid subjective rationalization).

**File:** `mutation_classes.md`

---

### Q29: Runtime schema version detection ✅ SEALED

**Answer:** Mandatory header `X-WINDI-Schema-Version`. Absent header on mutations = 400 reject (downgrade-attack vector). Legacy assumption only for EPHEMERAL reads, with explicit warning (I14). Grace period 72h for version upgrades.

**File:** `kernel_manifest.json`

---

### Q31: Buffer TTL, signatures, CRITICAL exclusion for R7 ✅ SEALED

**Answer:** Buffer TTL 4h, max 100 receipts. Signature: `Ed25519(payload_hash + buffered_at + prev_buffer_hash, key)` — prev_buffer_hash INSIDE signature for chain integrity. CRITICAL excluded (HALT). Overflow = back-pressure (no drop, I14). Truncation limitation declared in flush receipt.

**File:** `recovery_protocol.md`

---

## CANDIDATE Resolution (Q17)

### Q17: Recovery from compromised HD session ⚠️ CANDIDATE

**Answer:** MIRROR-BREAK protocol with two triggers (HD-initiated, Guardian-initiated), QUARANTINE procedure, HD-GRACE definition, deadman trigger.

**Pending work before graduation to SEALED:**
1. HD-GRACE must contain STANDARD from quarantined session (not just CRITICAL)
2. Deadman anchors ONLY on HD heartbeat (remove "AND no STANDARD" condition)

**File:** `recovery_protocol.md`

---

## Previously Resolved (2026-05-14)

### Q1: Spine Integrity Verification ✅ RESOLVED

**Status:** RESOLVED · 2026-05-14 · HD Ratification
**Schema:** `spine_integrity.schema.json` (RATIFIED)
**Doc:** `spine_bindings.md` (RATIFIED)

---

### Q4: Human Dragon Unavailability ✅ RESOLVED

**Status:** RESOLVED · 2026-05-14 · HD Ratification
**Schema:** `authority.schema.json` (RATIFIED)

---

## Process

1. Architect addresses questions in priority order
2. Guardian reviews each answer
3. Human Dragon approves refinements
4. Questions move from `open` to `sealed` or `candidate`
5. When all CRITICAL/high resolved → §266 seals

---

*OPEN-QUESTIONS · §266-SEALED*
*Liga IA+H · Kempten, Bavaria · 2026*
