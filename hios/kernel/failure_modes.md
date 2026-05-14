# Failure Modes — WINDI-HIOS Kernel

```
STATUS:         DRAFT-SKELETON
NOT SEALED
NOT CANONICAL
PENDING GUARDIAN REVIEW
```

---

## Purpose

Document what happens when Kernel components fail and how to recover.

---

## Failure Categories

### F1. Schema Corruption

**Symptom:** Schema validation fails unexpectedly
**Impact:** Actions cannot be validated
**Detection:** JSON parse errors, validation failures
**Recovery:** Restore from version control, verify hash
**Cascade:** All dependent operations blocked

### F2. Ledger Unavailable (:8101 down)

**Symptom:** POST /api/receipts fails
**Impact:** Cannot seal proofs
**Detection:** Connection timeout, 5xx errors
**Recovery:** Wait for service recovery, retry queue
**Cascade:** Admissibility degrades to RISKY

### F3. DID Genesis Unavailable (:8096 down)

**Symptom:** Identity verification fails
**Impact:** Cannot verify actors
**Detection:** Connection timeout, 5xx errors
**Recovery:** Wait for service recovery
**Cascade:** New sessions blocked, existing sessions degraded

### F4. CBP Generation Failure

**Symptom:** cognitive-bind-module.sh errors
**Impact:** Sessions start without context
**Detection:** Script exit code non-zero
**Recovery:** Manual context establishment, Human Dragon override
**Cascade:** Bind Integrity = BROKEN, Re-entry REFUSED

### F5. Receipt Parent Lost

**Symptom:** Parent receipt ID not found in Ledger
**Impact:** Chain integrity broken
**Detection:** GET parent returns 404
**Recovery:** Create orphan receipt with explicit note, flag for audit
**Cascade:** Audit trail incomplete

### F6. Execution Timeout

**Symptom:** Execution exceeds timeout
**Impact:** Action state unknown
**Detection:** Timeout trigger
**Recovery:** See recovery_protocol.md
**Cascade:** Proof may or may not exist

### F7. Authority Deadlock

**Symptom:** Required approvers unavailable
**Impact:** Action blocked indefinitely
**Detection:** Timeout on approval
**Recovery:** Escalation path, timeout defaults
**Cascade:** Operations queue grows

### F8. Spine Integrity Failure

**Symptom:** Invariant drift detected
**Impact:** Constitutional trust broken
**Detection:** Hash mismatch, Q1 mechanism
**Recovery:** Human Dragon review, constitutional session
**Cascade:** All CRITICAL operations suspended

---

## Cascade Matrix

| Primary Failure | Secondary Effects | Recovery Priority |
|-----------------|-------------------|-------------------|
| Ledger | Proof, Admissibility | P0 |
| DID Genesis | Identity, Authority | P0 |
| CBP | Context, Continuity | P1 |
| Schema | All validation | P1 |
| Authority | Admissibility, Execution | P2 |

---

## Open Questions (Failure)

- Q19: Automatic vs manual recovery triggers?
- Q20: Failure notification channels?

---

*Failure Modes · DRAFT-SKELETON*
*Liga IA+H · Kempten, Bavaria · 2026*
