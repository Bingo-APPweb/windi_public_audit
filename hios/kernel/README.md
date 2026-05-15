# WINDI-HIOS Kernel Ground v0.1

```
STATUS:         DRAFT-SKELETON
NOT SEALED
NOT CANONICAL
PENDING GUARDIAN REVIEW
```

> **"The WINDI-HIOS Kernel is currently defined as a canonical binding map
> and admissibility coordination layer over existing WINDI primitives."**

---

## What This Directory Contains

This is the **review surface** for the WINDI-HIOS Kernel Ground v0.1.

It contains:
- Schema definitions (DRAFT)
- Contract specifications (DRAFT)
- Binding maps to existing WINDI Spine
- Open questions for Architect refinement
- Threat model and failure mode documentation

It does **NOT** contain:
- Sealed constitutional documents
- Executable code
- Tests or examples
- New doctrine

---

## Critical Declaration

**WINDI-HIOS Kernel does NOT substitute:**

| Existing Primitive | Port/Location | Status |
|--------------------|---------------|--------|
| DID Genesis | :8096 | PRESERVED |
| Forensic Ledger | :8101 | PRESERVED |
| CBP (§261) | cognitive-bind-module.sh | PRESERVED |
| PingPong Protocol (§263) | /opt/windi/claudeWeb/ | PRESERVED |
| I9 Human Approval Gate | Constitutional | PRESERVED |
| Three Dragons Protocol | Constitutional | PRESERVED |
| Verify Public | :8145 | PRESERVED |
| W-SITES-001 | :8192 | PRESERVED |

The Kernel **binds to** these primitives. It does not **replace** them.

---

## §266 Status

**§266 is NOT sealed in this step.**

This skeleton only prepares the directory and review surface for:
1. Guardian final review
2. Architect refinement cycle
3. Human Dragon constitutional approval

Only after all three complete will §266 be sealed.

---

## File Index

| File | Purpose | Status |
|------|---------|--------|
| `kernel_manifest.json` | Machine-readable manifest | DRAFT |
| `kernel_contract.md` | Human-readable contract | DRAFT |
| `KERNEL-GROUND-v0.1.md` | Architecture specification | DRAFT |
| `actors.schema.json` | Actor identity schema | DRAFT |
| `authority.schema.json` | Authority/governance schema | DRAFT |
| `context.schema.json` | Context/session schema | DRAFT |
| `admissibility.schema.json` | Admissibility rules schema | DRAFT |
| `execution.schema.json` | Execution envelope schema | DRAFT |
| `proof.schema.json` | Proof/receipt schema | DRAFT |
| `continuity.schema.json` | Continuity chain schema | DRAFT |
| `spine_bindings.md` | Kernel ↔ Spine binding map | DRAFT |
| `threat_model.md` | Security threat model | DRAFT |
| `failure_modes.md` | Failure mode documentation | DRAFT |
| `recovery_protocol.md` | Recovery procedures | DRAFT |
| `mutation_classes.md` | CRITICAL/STANDARD/EPHEMERAL | DRAFT |
| `schema_versioning_policy.md` | Schema evolution policy | DRAFT |
| `OPEN-QUESTIONS.md` | Consolidated open questions | DRAFT |

---

## Receipt Policy (This Step)

| Receipt Type | Permitted |
|--------------|-----------|
| Constitutional receipt | **PROHIBITED** |
| Technical skeleton receipt | PERMITTED if classified as **EPHEMERAL** |
| Constitutional parent linkage | **PROHIBITED** |
| Sealing | **PROHIBITED** |

---

## Next Steps

1. Guardian reviews all files
2. Architect addresses OPEN-QUESTIONS.md
3. Human Dragon approves refinements
4. §266 seals (future session)

---

*WINDI-HIOS Kernel Ground v0.1 · DRAFT-SKELETON*
*Liga IA+H · Kempten, Bavaria · 2026*
