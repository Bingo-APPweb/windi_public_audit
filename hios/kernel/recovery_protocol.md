# Recovery Protocol — WINDI-HIOS Kernel

```
STATUS:         §266-SEALED (partial)
SEALED DATE:    2026-05-24
SEALED:         Q31 (R7 Buffer Protocol)
CANDIDATE:      Q17 (R8 MIRROR-BREAK) — pending HD-GRACE containment + deadman graduation
```

---

## Purpose

Define procedures for recovering from Kernel failure states.

---

## General Principles

1. **Human Dragon is ultimate recovery authority**
2. **Never auto-recover CRITICAL mutations**
3. **Always generate recovery receipt**
4. **Document recovery in CLAUDE-HISTORY.md**

---

## Recovery Procedures

### R1. Service Recovery (Ledger, DID Genesis)

```
1. Detect service down (monitoring)
2. Attempt restart (systemd or nohup)
3. Verify health endpoint
4. Clear retry queue
5. Generate recovery receipt (EPHEMERAL)
```

### R2. Schema Recovery

```
1. Identify corrupted schema
2. Restore from git (known-good commit)
3. Verify hash matches canonical
4. Re-validate pending operations
5. Generate recovery receipt (STANDARD)
```

### R3. Execution Timeout Recovery

```
1. Check actual execution state
2. If completed: generate proof
3. If failed: mark as failed, notify
4. If unknown: escalate to Human Dragon
5. Generate recovery receipt (STANDARD)
```

### R4. Authority Deadlock Recovery

```
1. Identify blocked approvers
2. Activate escalation path
3. If all escalation fails: timeout with explicit denial
4. Never auto-approve
5. Generate recovery receipt (STANDARD)
```

### R5. Spine Integrity Recovery

**STATUS: IMPLEMENTABLE (Q1 resolved 2026-05-14)**

```
1. Halt all CRITICAL operations
2. Alert Human Dragon immediately
3. Guardian reviews drift
4. Human Dragon decides:
   a) Drift acceptable → document, continue
   b) Drift unacceptable → constitutional session
5. Generate recovery receipt (CRITICAL)
```

### R6. Chain Integrity Recovery (Orphan Receipt)

```
1. Create receipt with orphan flag
2. Document missing parent
3. Flag for audit
4. Continue operations
5. Audit resolves orphan later
```

---

## R7. Ledger Outage Buffer Protocol (Q31 Resolution — §266 SEALED)

> When Forensic Ledger :8101 is unavailable, the Kernel enters "Sovereign Pause".
> This protocol defines how to buffer receipts locally without violating
> the "Forensic Ledger is single source of truth" principle.

### Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Buffer TTL | 4 hours | Reasonable time for Ledger restore |
| Max buffer size | 100 receipts | Prevents flood during outage |
| Clock | Ledger timestamp (canonical) | When flush occurs |

### Signature Requirements (CRITICAL — Trindade Imutabilidade)

Each buffered receipt MUST include:

```json
{
  "payload_hash": "sha256(receipt_payload)",
  "buffered_at": "ISO8601",
  "prev_buffer_hash": "sha256 of previous buffer entry",
  "actor_signature": "Ed25519(payload_hash + buffered_at + prev_buffer_hash, actor_private_key)"
}
```

**The signature MUST cover `prev_buffer_hash`** — this is the chain integrity guarantee.
Without it, an attacker during outage could reorder/insert entries while each individual
signature remains valid. With the hash inside the signature, reordering breaks verification.

**Buffer[0].prev_buffer_hash** = `"GENESIS-OUTAGE-{outage_id}"`

### Ephemeral DID Keypair (Q2 linkage)

Session DIDs (did:windi:session:*) are minted with ephemeral Ed25519 keypair.
- Generated at session start
- Discarded at session end
- Enables STANDARD receipts in buffer even for session actors

### CRITICAL Exclusion

- Mutações **CRITICAL NÃO entram no buffer**
- CRITICAL durante outage = **HALT** (wait for Ledger)
- Razão: I9 requires immediate confirmation, not deferred

### Overflow Policy (Buffer Full)

- **Back-pressure:** HALT also STANDARD until buffer has space
- **Drop = PROHIBITED** (I14 violation — silent loss)
- System announces: `"Buffer at capacity. Waiting for Ledger recovery."`

### Flush Protocol

When Ledger returns:
1. Verify Ledger health endpoint (3 successful pings)
2. Validate mini-Merkle chain integrity:
   - Each signature valid for declared actor
   - `prev_buffer_hash` chain unbroken
   - No insertions/deletions/reorderings
3. Flush in FIFO order
4. Each flushed receipt includes:
   - `buffered_at`: when originally buffered
   - `flushed_at`: when written to Ledger
   - `outage_id`: identifier for this outage period
   - `buffer_position`: 0-indexed position in buffer

### Truncation Detection Limitation (I14 Declaration)

Receipt de flush MUST include:

```json
{
  "gap_detection_limited": true,
  "limitation_note": "Integrity verified for buffered chain. Truncation detection limited during outage window — no external anchor available."
}
```

**Rationale:** Removal of tail entries during outage is undetectable (inherent limitation, not defect). Per I14, known limitation must be surfaced, not hidden.

### Constitutional Constraint

Buffer is NOT a parallel Ledger. It is a signed write-ahead log with strict TTL.
If misdesigned, violates I11 (single source of forensic truth).

---

## R8. MIRROR-BREAK Protocol (Q17 — CANDIDATE)

```
STATUS:         CANDIDATE (not sealed)
PENDING WORK:   1) HD-GRACE contains STANDARD from quarantined session
                2) Deadman graduation (heartbeat-only trigger)
```

> Recovery from compromised Human Dragon session.
> Defined in response to Q17: "What if the HD session itself is compromised?"

### Trigger 1: HD-initiated

```
HD declares: "I suspect compromise on session X"
→ All CRITICAL mutations from session X → QUARANTINE
```

### Trigger 2: Guardian-initiated (independent)

Guardian observes anomalous CRITICAL pattern:
- 3+ CRITICAL in <1h without justifying context
- CRITICAL with inconsistent actor_signature
- CRITICAL contradicting recent Spine

**Action:** Guardian initiates QUARANTINE pending HD confirmation.
If HD does not respond in 24h → HD-GRACE activates.

### QUARANTINE Procedure

1. All CRITICAL mutations from suspect session → QUARANTINE state
2. Guardian reviews each quarantined mutation
3. HD confirms: **RATIFY** (keep) or **REVOKE** (errata)
4. REVOKE generates ERRATA receipt (not DELETE) per HD-MIRROR §267/I11

### HD-GRACE Definition (CANDIDATE — pending containment fix)

**Activated when:** HD does not respond 24h after Guardian QUARANTINE

**Behaviour (current):**
- Quarantine PERSISTS (fail-safe, not fail-open)
- CRITICAL in quarantine = blocked until HD returns
- STANDARD new = permitted (Guardian supervises)

**PENDING FIX (not yet sealed):**
- STANDARD from quarantined session should ALSO be contained
- Only actors OUTSIDE quarantined session operate normally
- Rationale: Attacker controlling session degrades to STANDARD to bypass

### Guardian Compromised

Detection: Architect or Witness report anomaly to HD
HD declares: "Guardian compromised"
→ SYSTEM HALT immediate
→ Recovery: HD designates new Guardian instance (I9 presencial)

### Deadman Trigger (CANDIDATE — pending graduation)

**Condition (corrected):** Absence of HD heartbeat for 7 days
- **Independent** of system activity
- Does NOT require "AND no STANDARD receipts"
- Rationale: Attacker produces receipts — "no STANDARD" would be false

**Action:** HD-LOCK automatic + external alert (pre-configured email)

### HD-MIRROR Linkage (§267/I11)

REVOKE generates receipt type ERRATA (not DELETE).
Reference: `/opt/windi/docs/PROOF-SELF-CORRECTION-WITHOUT-REWRITE.md`
Principle: "Corrigir sem reescrever" — error remains visible, correction also visible.

---

## Recovery Receipt Format

```json
{
  "receipt_type": "recovery",
  "mutation_class": "STANDARD|CRITICAL",
  "failure_mode": "F1-F8",
  "recovery_procedure": "R1-R8",
  "recovered_by": "actor_id",
  "human_dragon_notified": true,
  "timestamp": "ISO8601"
}
```

---

## Open Questions (Recovery)

- Q21: Recovery receipt chain separate from main chain?
- Q22: Maximum auto-recovery attempts before escalation?

---

*Recovery Protocol · §266-SEALED (Q31) + CANDIDATE (Q17)*
*Liga IA+H · Kempten, Bavaria · 2026*
