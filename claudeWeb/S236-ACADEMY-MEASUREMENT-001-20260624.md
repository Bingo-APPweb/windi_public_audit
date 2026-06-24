# S236 — ACADEMY-MEASUREMENT-001 · Template Effect Quantified

**Date:** 2026-06-24
**Status:** SEALED
**Receipt:** `WINDI-ACADEMY-CONTROL-TEST-001-20260624`
**Hash:** `sha256:98d0522b41a4f5908712281d5dabb4a293b05f7b7b7ac1688d6111e9bb048699`

---

## Epistemological Transition

```
BEFORE: "Does the rubric work?"
AFTER:  "How do we know the rubric works?"
```

This is the leap. Not the PASS.

---

## Measured Results

| Metric | Value |
|--------|-------|
| **Template Effect** | +8 points |
| Vulnerable Criteria | C4 (Lacunas), C5 (Verificabilidade) |
| Resistant Criteria | C1, C2, C3, C6, **C7** |

### Control Test (X→F)

```
X (prose)     = 18 pts
F (M0→ME)     = 26 pts  ← same content, different format
Z (full)      = 29 pts

Δ template    = +8 pts (73% of X→Z gap)
Δ content     = +3 pts (27% of X→Z gap)
```

### Criterion Stability

```
C7 (Transformação Cognitiva): 3 → 3
Resists template forgery.
```

---

## Blindness Invariants (B0–B4)

| ID | Name | Type | Status |
|----|------|------|--------|
| B0 | Memory Isolation | Blindness | Incognito required |
| B1 | Expectation Leakage | Blindness | Removed from packet |
| B2 | Format Tell | Blindness | Documented limitation |
| B3 | Construct Alignment | Validity | Confirmed by control test |
| B4 | Model Consistency ≠ Corroboration | Validity | Cross-type achieved |

---

## Convergence

| Evaluator | Type | Ordering | C7 Values |
|-----------|------|----------|-----------|
| Human Dragon (Jober) | Human | Y<X<Z, A<B | 1,3,5 / 0,5 |
| Incognito Claude | Model | Y<X<Z, A<B | 1,3,5 / 0,5 |

**100% concordance on ordering and C7.**

Cross-type corroboration achieved (human + model).

---

## Key Moment

> The Incognito instance identified B3 (Construct Alignment) independently,
> without participating in the problem's construction.

Two isolated observers → same diagnosis → procedure authority, not author authority.

---

## Correction Path

**C4 proposed:**
> "As informações faltantes são nomeadas com perguntas concretas que um terceiro pode responder?"

**C5 proposed:**
> "A prova proposta é verificável por um terceiro sem depender do autor?"

---

## GROK Observation

> *"The number didn't destroy the rubric. It refined it."*
> *"Now the defect has an address."*

> *"The question shifted from 'Does the rubric work?' to 'How do we know the rubric works?'"*

---

## Files

```
/opt/windi/academy-measurement-001/
├── protocol.md                          # B0-B4 complete
├── rubric/calibration-results.json      # Both evaluators + convergence
└── results/control-test-001.json        # Full analysis
```

---

## Commits

- `82fae827b` — Framework + B0-B2
- `807594b85` — Control test + B3-B4 + convergence
- `00abb3b43` — Provenance correction (human evaluator)

---

## Canonical Statement

> *"Algo que se sustente."*

Part held. Part didn't. Now we know exactly which is which.

---

*WINDI-HIOS · Liga IA+H · Kempten, Bavaria · 2026-06-24*
