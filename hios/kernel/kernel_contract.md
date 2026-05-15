# WINDI-HIOS Kernel Contract

```
STATUS:         DRAFT-SKELETON
NOT SEALED
NOT CANONICAL
PENDING GUARDIAN REVIEW
```

---

## 1. Definition

The WINDI-HIOS Kernel is a **canonical binding map and admissibility
coordination layer** over existing WINDI primitives.

It is NOT:
- A new execution engine
- A replacement for existing services
- An autonomous decision system

It IS:
- A coordination layer that ensures every action has identity, context,
  admissibility, and proof
- A binding map that connects Kernel concerns to existing Spine primitives
- An admissibility gate that prevents unauthorized mutations

---

## 2. The Seven Layers

| # | Layer | Binding | Schema |
|---|-------|---------|--------|
| 1 | Identity | DID Genesis :8096 | actors.schema.json |
| 2 | Context | CBP §261 + Session | context.schema.json |
| 3 | Authority | I9 + Three Dragons | authority.schema.json |
| 4 | Admissibility | I9 Gate + Guardian | admissibility.schema.json |
| 5 | Execution | Construtor + Services | execution.schema.json |
| 6 | Proof | Forensic Ledger :8101 | proof.schema.json |
| 7 | Continuity | PingPong §263 + INDEX | continuity.schema.json |

---

## 3. Spine Bindings (NOT Duplications)

The Kernel does not create new systems. It binds to existing ones:

| Kernel Concern | Existing Primitive | Binding Status |
|----------------|-------------------|----------------|
| Identity | DID Genesis :8096 / actor registry | BOUND |
| Proof | Forensic Ledger :8101 /api/receipts | BOUND |
| Continuity | CBP §261 + PingPong §263 + INDEX | BOUND |
| Authority | I9 + Human Dragon + Three Dragons | BOUND |
| Admissibility | I9 Gate + Guardian Review | BOUND |
| Execution | Construtor / service-specific | BOUND |
| Drift | W-LEXICON / future §265 metrics | PENDING |
| Spine Integrity | §244 Three Pillars + I1-I9 | OPEN |

---

## 4. Bootstrap Protocol

The Kernel's own installation requires admissibility.

**Bootstrap Sequence:**
1. Human Dragon initiates Kernel installation (I9 trigger)
2. Guardian reviews skeleton (this step)
3. Architect refines based on Guardian feedback
4. Human Dragon approves refined version
5. Construtor executes final installation
6. §266 seals Kernel Ground v0.1
7. First EPHEMERAL receipt marks bootstrap complete

**First receipt authority:** Human Dragon + Guardian witness
**Receipt classification:** EPHEMERAL (not constitutional until §266 seals)

---

## 5. Mutation Classification

| Class | Description | Requires | Retention |
|-------|-------------|----------|-----------|
| **CRITICAL** | Constitutional changes, doctrine, seals | I9 + Guardian + Human Dragon | Permanent |
| **STANDARD** | Normal operations with audit trail | Actor identity + context | 90 days min |
| **EPHEMERAL** | Technical ops, no constitutional impact | Actor identity | 7 days / session |

---

## 6. Fast-Path Declaration

Not all operations are kernel-gated. The following are **user-space**
(no Kernel mediation required):

- Read-only queries to existing services
- Session-scoped ephemeral state
- UI rendering and client-side operations
- Cache reads (L2/L3 in W-CACHE-001)

**Kernel-gated operations:**
- Any mutation that creates receipts
- Any action requiring I9 approval
- Any cross-service coordination
- Any state change affecting Spine integrity

---

## 7. Schema Versioning Policy

- **Format:** Semantic versioning (MAJOR.MINOR.PATCH)
- **Sealed schemas:** Immutable (new schema for breaking changes)
- **Migration:** Explicit migration path required for MAJOR version bumps
- **Backwards compatibility:** Required for MINOR/PATCH within same MAJOR

See `schema_versioning_policy.md` for details.

---

## 8. Open Questions

See `OPEN-QUESTIONS.md` for consolidated list of unresolved questions.

Critical open question:
> **"How does the Kernel verify that I1-I9 themselves did not drift?"**

---

## 9. Threat Model Reference

See `threat_model.md` for:
- Attack vectors
- Trust boundaries
- Mitigation strategies

See `failure_modes.md` for:
- Component failure scenarios
- Cascade effects
- Recovery procedures

---

## 10. Contract Status

| Aspect | Status |
|--------|--------|
| Definition | DRAFT |
| Layer bindings | DRAFT |
| Bootstrap protocol | DRAFT |
| Mutation classes | DRAFT |
| Schema versioning | DRAFT |
| §266 seal | PENDING |

This contract becomes canonical only after §266 seals.

---

*WINDI-HIOS Kernel Contract · DRAFT-SKELETON*
*Liga IA+H · Kempten, Bavaria · 2026*
