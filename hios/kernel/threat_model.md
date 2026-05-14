# Threat Model — WINDI-HIOS Kernel

```
STATUS:         DRAFT-SKELETON
NOT SEALED
NOT CANONICAL
PENDING GUARDIAN REVIEW
```

---

## Purpose

Document security threats to the WINDI-HIOS Kernel and mitigation strategies.

---

## Trust Boundaries

| Boundary | Inside | Outside |
|----------|--------|---------|
| Kernel | Schemas, bindings, coordination | Service execution |
| Strato Server | All WINDI services | External networks |
| Three Dragons | Guardian, Architect, Witness | External AI providers |
| Human Dragon | Final authority | All automated systems |

---

## Threat Categories

### T1. Identity Spoofing

**Threat:** Actor claims false identity
**Mitigation:** DID Genesis verification required
**Binding:** actors.schema.json + :8096

### T2. Authority Escalation

**Threat:** Actor performs action beyond their authority
**Mitigation:** Authority check before admissibility
**Binding:** authority.schema.json + I9

### T3. Admissibility Bypass

**Threat:** Action executes without admissibility check
**Mitigation:** Kernel-gated operations require admission
**Binding:** admissibility.schema.json

### T4. Proof Tampering

**Threat:** Receipt modified after sealing
**Mitigation:** Content hash + Ledger immutability
**Binding:** proof.schema.json + :8101

### T5. Continuity Corruption

**Threat:** Session state manipulated between sessions
**Mitigation:** CBP integrity score + hash verification
**Binding:** continuity.schema.json + §261

### T6. Spine Drift

**Threat:** Constitutional invariants change without detection
**Mitigation:** **OPEN** (Q1 unresolved)
**Binding:** spine_bindings.md

### T7. Kernel Self-Authorization

**Threat:** Kernel authorizes its own installation
**Mitigation:** Bootstrap protocol requires I9 + Guardian
**Binding:** kernel_contract.md § Bootstrap

### T8. Mutation Misclassification

**Threat:** CRITICAL mutation classified as EPHEMERAL
**Mitigation:** Classification rules + Guardian review
**Binding:** mutation_classes.md

---

## Attack Vectors

| Vector | Likelihood | Impact | Mitigation |
|--------|------------|--------|------------|
| Compromised API key | Medium | High | Key rotation, tier limits |
| Malicious agent | Low | High | Three Dragons review |
| Network interception | Low | Medium | HTTPS, internal network |
| Schema corruption | Low | Critical | Version control, hash verification |

---

## Open Questions (Security)

- Q16: How to detect malicious Guardian?
- Q17: Recovery from compromised Human Dragon session?
- Q18: Multi-party approval for CRITICAL mutations?

---

*Threat Model · DRAFT-SKELETON*
*Liga IA+H · Kempten, Bavaria · 2026*
