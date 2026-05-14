# Recovery Protocol — WINDI-HIOS Kernel

```
STATUS:         DRAFT-SKELETON
NOT SEALED
NOT CANONICAL
PENDING GUARDIAN REVIEW
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

**⚠️ STATUS: BLOCKED on Q1 resolution**

> Cannot define recovery procedure for drift we cannot yet detect.
> R5 becomes implementable only after Q1 ("How does the Kernel verify
> that I1-I9 themselves did not drift?") has a concrete answer.

```
1. Halt all CRITICAL operations
2. Alert Human Dragon immediately
3. Guardian reviews drift
4. Human Dragon decides:
   a) Drift acceptable → document, continue
   b) Drift unacceptable → constitutional session
5. Generate recovery receipt (CRITICAL)
```

**Dependency:** Q1 (CRITICAL) must be resolved first.

### R6. Chain Integrity Recovery (Orphan Receipt)

```
1. Create receipt with orphan flag
2. Document missing parent
3. Flag for audit
4. Continue operations
5. Audit resolves orphan later
```

### R7. Ledger Outage Buffer Protocol

**⚠️ STATUS: DRAFT-SKELETON — Requires Q31 resolution**

> When Forensic Ledger :8101 is unavailable, the Kernel enters "Sovereign Pause".
> This protocol defines how to buffer receipts locally without violating
> the "Forensic Ledger is single source of truth" principle.

```
1. Detect Ledger :8101 DOWN (F2 failure mode)
2. Enter LEDGER_OUTAGE state
3. For incoming receipts:
   a) CRITICAL: BLOCK — prefer system halt to buffer
   b) STANDARD/EPHEMERAL: Buffer locally with constraints
4. Buffer constraints:
   a) Each entry signed by actor + Guardian witness
   b) Buffer TTL: 24h maximum (Q31 pending)
   c) Entries marked: buffered_during_outage: true
5. When Ledger returns:
   a) Verify Ledger health endpoint
   b) Flush buffer in chronological order
   c) Each entry marked: recovered_from_buffer: true
   d) Generate recovery receipt (STANDARD)
6. If buffer TTL expires before Ledger returns:
   a) Escalate to Human Dragon
   b) Buffer entries become orphan candidates
```

**Dependencies:**
- Q19: Automatic vs manual recovery triggers
- Q20: Failure notification channels
- Q31: Buffer TTL, signature requirements, and CRITICAL exclusion policy

**Constitutional Constraint:**
Buffer is NOT a parallel Ledger. It is a signed write-ahead log with strict TTL.
If misdesigned, violates I11 (single source of forensic truth).

---

## Recovery Receipt Format

```json
{
  "receipt_type": "recovery",
  "mutation_class": "STANDARD|CRITICAL",
  "failure_mode": "F1-F8",
  "recovery_procedure": "R1-R6",
  "recovered_by": "actor_id",
  "human_dragon_notified": true|false,
  "timestamp": "ISO8601"
}
```

---

## Open Questions (Recovery)

- Q21: Recovery receipt chain separate from main chain?
- Q22: Maximum auto-recovery attempts before escalation?

---

*Recovery Protocol · DRAFT-SKELETON*
*Liga IA+H · Kempten, Bavaria · 2026*
