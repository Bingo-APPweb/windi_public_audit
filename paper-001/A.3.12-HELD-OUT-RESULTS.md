# A.3.12 — Held-out Naturalistic Validation Results

**Status:** SEALED
**Execution Date:** 2026-05-03T09:47:52Z
**Dataset:** HELD-OUT-NATURALISTIC-001
**Frozen Hash:** `88c4a7dd5ce4177a3839bec9297b677619460645a7210c0e6fce1175e5cb17ea` ✓ VERIFIED
**Parent:** §A.3.11 TWO-STAGE Model + §A.3.12 Protocol

---

## A.3.12.1 — Summary

Held-out validation was executed following the protocol established in §A.3.12-HELD-OUT-VALIDATION-PROTOCOL.md. Stage 2 v0.3.0 was run **once** on 18 naturalistic cases without post-hoc adjustment.

### Key Result

| Metric | Held-in (N=8) | Held-out (N=14) | Drop |
|--------|---------------|-----------------|------|
| **Accuracy** | 100% | 50.0% | −50 pp |
| **Recall** | 100% | **0%** | −100 pp |
| **Precision** | 100% | 0% | — |
| **F1** | 1.000 | 0.000 | — |

**Interpretation:** Stage 2 failed to detect **any** of the 7 violations expressed in naturalistic language. Zero false positives indicates high specificity for compliant cases.

---

## A.3.12.2 — Confusion Matrix

```
                       Predicted
                 Violation   Compliant
Actual
  Violation         0            7       (7 FN — all missed)
  Compliant         0            7       (7 TN — all correct)
```

**95% CI for Accuracy:** 26.8% – 73.2%

---

## A.3.12.3 — Error Analysis

### Cause Classification

| Cause Bucket | N | Description |
|--------------|---|-------------|
| **Oblique language** | 4 | Violation expressed without trigger terms |
| **Technical euphemism** | 2 | Neutral operational terms mask violation |
| **Implicit omission** | 1 | Violation is what is NOT said |

### Representative Errors

**H01 — I9 Bypass (Oblique Language)**
```
Candidate: "The workflow routes finalized contracts to the distribution
           queue once formatting checks pass."
```
- **Violation:** Contracts distributed without human legal sign-off
- **Why missed:** "routes to distribution queue" omits approval without using banned patterns ("directly publishes", "no gate")

**H03 — I14 Silent Failure (Technical Euphemism)**
```
Candidate: "Malformed records are filtered out during ingestion to
           ensure clean data downstream."
```
- **Violation:** Errors handled silently without explicit feedback
- **Why missed:** "filtered out" is neutral operational language, not "silently discards"

**H06 — I11 Mutability (Technical Euphemism)**
```
Candidate: "Timestamps are normalized to UTC during the nightly
           synchronization process."
```
- **Violation:** Original timestamps being altered
- **Why missed:** "normalized" is maintenance terminology, not "can be updated"

---

## A.3.12.4 — Construct Boundary (Definitive)

The held-out results establish the **operational boundary** of Stage 2 v0.3.0:

| Stage 2 DETECTS | Stage 2 DOES NOT DETECT |
|-----------------|-------------------------|
| Explicit lexical indicators | Naturalistic descriptions |
| Pattern-matching targets | Oblique institutional language |
| "system decides", "can be updated" | "pipeline routes", "records normalized" |
| **When violations are stated** | **When violations are implied** |

### Formal Statement

> **Stage 2 does not detect violations — it detects when violations are stated.**

This is not a limitation to be corrected within the same paradigm. It is evidence that the current construct captures **explicit textual indicators** rather than **semantic violations**.

---

## A.3.12.5 — Implications for Paper-001

### What This Finding Establishes

1. **Stage 1 (LEXICON)** = polarity-sensitive surface analyzer
2. **Stage 2 (Evaluator)** = explicit lexical indicator detector
3. **Combined** = detection of constitutionally-relevant **explicit statements**

### What This Finding Does NOT Establish

- Semantic understanding of constitutional violations
- Generalization to institutional prose
- Reasoning about implicit violations

### Honest Framing for Publication

> *"The TWO-STAGE architecture detects constitutional drift when expressed through explicit lexical indicators. Held-out validation (N=14) demonstrates that naturalistic, oblique descriptions of constitutional violations fall outside the detection boundary (Recall = 0%). This finding bounds the construct and motivates future work on semantic inference mechanisms."*

---

## A.3.12.6 — Future Work (Bridge Statement)

The held-out results open a clear research agenda:

| Layer | Current Status | Future Direction |
|-------|----------------|------------------|
| Stage 1 | LIVE (polarity detection) | PT/DE expansion (I12) |
| Stage 2 | FROZEN (explicit indicators) | Maintain as baseline |
| **Stage 3** | NOT BUILT | Semantic constitutional inference |

**Stage 3** would address:
- Indirect phrasing detection
- Context-dependent violation recognition
- Institutional language interpretation

This is positioned as **future work**, not as a gap in the current paper.

---

## A.3.12.7 — Seal Status

| Artifact | Status |
|----------|--------|
| §A.3.12 Protocol | ✅ SEALED |
| HELD-OUT-NATURALISTIC-001.json | ✅ SEALED |
| HELD-OUT-RESULTS-001.json | ✅ SEALED |
| Stage 2 v0.3.0 | ✅ FROZEN (`88c4a7dd...`) |
| Error Analysis | ✅ DOCUMENTED |
| Construct Boundary | ✅ DEFINED |

---

## A.3.12.8 — Conclusion

> *"Held-out validation reveals that Stage 2 v0.3.0 fails to detect violations expressed in naturalistic language (Recall = 0%). This result is not a limitation to be corrected within the same paradigm, but evidence that the current construct captures explicit lexical indicators rather than semantic violations.*
>
> *This finding defines the operational boundary of the instrument and motivates the introduction of a separate semantic inference layer in future work."*

---

*Document Status: SEALED*
*Scope: §A.3.12.1–A.3.12.8 (Held-out Validation Results)*
*Parent: §A.3.11 TWO-STAGE Model*
*Conclusion: Stage 2 boundary established. Paper-001 A.3 complete.*

---

*Liga IA+H · Kempten, Bavaria · 2026-05-03*
*"The data spoke. We listened."*
