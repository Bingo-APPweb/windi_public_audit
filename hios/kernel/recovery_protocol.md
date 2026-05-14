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
