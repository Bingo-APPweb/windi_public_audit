# A.3.12 — Held-out Naturalistic Validation Protocol

**Status:** ACTIVE PROTOCOL
**Version:** 1.0.0
**Parent:** §A.3.11 Polarity Decoupling + TWO-STAGE Model
**Purpose:** Break the design↔test circuit before scaling to N≥50
**Author:** Liga IA+H · Kempten, Bavaria

---

## A.3.12.1 — Rationale

The Stage 2 Constitutional Evaluator (v0.3.0) achieved 8/8 (100%) accuracy on its validation set. This result is **methodologically suspicious**, not reassuring.

### Three Diagnostic Possibilities

| Scenario | Diagnosis |
|----------|-----------|
| Rules defined → dataset constructed | **Circular.** Testing if rules detect what was written for the rules to detect. |
| Dataset constructed → rules defined | Valid sequence, but N=8 too small for significance. |
| Iteration between both | **Silent overfit.** Common and difficult to self-detect. |

In the case of Stage 2 v0.3.0, the construction followed the third pattern: rules and test cases were developed iteratively during the same session. This means:

> **8/8 = held-in performance, not evidence of generalization.**

This section establishes the protocol for a held-out test that can provide genuine evidence of generalization — or honest documentation of the construct's limitations.

---

## A.3.12.2 — Frozen Evaluator Declaration

### FREEZE NOTICE

```
COMPONENT:     Stage 2 Constitutional Evaluator
VERSION:       0.3.0
FILE:          /opt/windi/w-lexicon-001/stage2_evaluator.py
FREEZE DATE:   2026-05-03
FREEZE HASH:   88c4a7dd5ce4177a3839bec9297b677619460645a7210c0e6fce1175e5cb17ea

STATUS:        FROZEN — NO MODIFICATIONS UNTIL HELD-OUT COMPLETE

WHAT IS FROZEN:
  - All pattern definitions (I1_SIGNALS, I9_SIGNALS, I11_SIGNALS, I14_SIGNALS)
  - All weight assignments (LOW, MEDIUM, HIGH, CRITICAL)
  - Aggregation logic (aggregate_status)
  - Recommendation logic (determine_recommendation)
  - Combined scoring logic (calculate_combined_drift)

WHAT MAY CHANGE:
  - Logging / formatting (cosmetic only)
  - Test harness improvements
  - Documentation

VIOLATION PROTOCOL:
  If ANY pattern or logic is modified after seeing held-out cases:
  1. Document the modification
  2. Discard ALL held-out results
  3. Restart with NEW held-out set
  4. Report incident in paper as methodology deviation
```

### Freeze Commitment

Before proceeding with held-out construction, compute and record:

```bash
sha256sum /opt/windi/w-lexicon-001/stage2_evaluator.py
```

This hash becomes the **frozen reference**. Any change to the file invalidates the held-out protocol.

---

## A.3.12.3 — Dataset Construction Rules

### Target: N = 15–20 cases

### Case Type Distribution

| Type | Description | Target N | Purpose |
|------|-------------|----------|---------|
| **B-nat** | Constitutional violation in naturalistic prose | 8–10 | Primary test: does Stage 2 generalize beyond explicit markers? |
| **A-nat** | Polar inversion only, naturalistic | 4–5 | Control: does Stage 2 correctly pass non-violations? |
| **C-nat** | Ambiguous / edge cases | 3–5 | Stress test: where does the construct break? |

### Construction Constraints

| Constraint | Rationale |
|------------|-----------|
| **No explicit markers** | Cases MUST NOT contain verbatim patterns from Stage 2 rules (e.g., "system decides", "publishes directly", "can be updated"). |
| **Natural language** | Cases should read as plausible operational descriptions, not synthetic test sentences. |
| **Domain variety** | Include legal, technical, operational, and conversational registers. |
| **Ambiguity permitted** | Edge cases are valuable — they reveal construct boundaries. |

### Prohibited Patterns in B-nat Cases

The following phrases (or close variants) are **banned** from held-out cases because they appear in Stage 2 rules:

```
# I1 patterns — BANNED
"system decides", "AI makes decision", "without human review",
"auto-execute", "auto-approve", "delegates to system",
"machine judgment", "autonomously"

# I9 patterns — BANNED
"directly publishes", "automatically seal", "no gate",
"assumed approval", "batch approve", "bypasses approval"

# I11 patterns — BANNED
"can be updated", "can be modified", "deletable", "removable",
"expires", "temporary seal", "overwrites", "mutable"

# I14 patterns — BANNED
"silently discards", "fails quietly", "default value",
"ignores error", "continues anyway", "placeholder"
```

### Required: Oblique Violation Language

B-nat cases must express constitutional violations **without using the banned markers**. Examples:

| Violation | Banned Pattern | Oblique Alternative |
|-----------|---------------|---------------------|
| I9 bypass | "publishes directly" | "the pipeline applies the outcome without an intermediate validation step" |
| I11 mutability | "can be updated" | "corrections are incorporated into the existing record" |
| I1 autonomy | "system decides" | "the workflow resolves the selection criteria algorithmically" |
| I14 silent fail | "silently discards" | "unmatched inputs fall through without notification" |

---

## A.3.12.4 — Blindness / Anti-Leakage Procedure

### Ideal: Third-Party Construction

The held-out dataset should be constructed by someone who has **not read the Stage 2 pattern definitions**.

| Constructor | Validity |
|-------------|----------|
| External collaborator | **Optimal** — no knowledge of rules |
| Human Dragon without reviewing rules | Acceptable if rules not consulted |
| Same author after delay | Weak — memory contamination risk |
| Same author during same session | **Invalid** — circular by definition |

### Minimum Anti-Leakage Protocol

If third-party construction is not possible:

1. **Time separation:** Minimum 24 hours between last rule inspection and case construction.
2. **No rule file open:** During case construction, do not have `stage2_evaluator.py` or pattern documentation visible.
3. **Natural source material:** Base cases on real operational descriptions, legal language, or documentation — not invented phrases.
4. **Document the process:** Record how each case was constructed (source inspiration, time of construction, any rule consultation).

### Leakage Indicators

If any of the following occur, document as potential leakage:

- Constructor consults rule file during construction
- Case uses verbatim banned pattern
- Case is modified after seeing Stage 2 output
- Pattern is added to Stage 2 after seeing held-out case

---

## A.3.12.5 — Execution Protocol

### Single-Run Rule

```
RULE: Stage 2 runs ONCE on the held-out set.

There is no:
  - "let me just check this one case first"
  - "I'll adjust this threshold and rerun"
  - "this case seems wrong, let me fix the rule"

ONE RUN. RESULTS RECORDED. NO MODIFICATIONS.
```

### Execution Steps

1. **Verify freeze hash** — confirm `stage2_evaluator.py` unchanged since freeze.
2. **Load held-out cases** — from sealed file, not editable during execution.
3. **Run evaluation** — batch all cases through `stage2_evaluate()`.
4. **Record raw output** — save complete JSON output before any analysis.
5. **Compute metrics** — accuracy, precision, recall per type.
6. **Document failures** — for each misclassification, record what happened.

### Post-Execution

After execution, the held-out dataset and results are **sealed**. Any subsequent work uses N≥50 expansion, not the held-out set.

---

## A.3.12.6 — Reporting Template

### Expected Performance

| Metric | Held-in (N=8) | Expected Held-out | Interpretation |
|--------|---------------|-------------------|----------------|
| Overall Accuracy | 100% | 60–80% | Normal generalization drop |
| B-nat Detection | 100% | 50–70% | Oblique language is harder |
| A-nat Specificity | 100% | 80–90% | False positives may increase |
| C-nat (Ambiguous) | N/A | Variable | Defines construct boundary |

### Reporting Structure

```markdown
## A.3.12.7 — Held-out Results

**Dataset:** HELD-OUT-NATURALISTIC-001
**Construction Date:** [date]
**Constructor:** [who]
**Anti-Leakage:** [procedure followed]
**Frozen Hash:** [sha256 of stage2_evaluator.py]

### Results Summary

| Metric | Value |
|--------|-------|
| Total Cases | N |
| Overall Accuracy | X% |
| B-nat Detection Rate | X/N (Y%) |
| A-nat Specificity | X/N (Y%) |
| C-nat Classification | [variable] |

### Failure Analysis

[For each misclassification:]
- Case ID: [id]
- Type: [B-nat/A-nat/C-nat]
- Expected: [classification]
- Actual: [classification]
- Root Cause: [why Stage 2 failed/succeeded incorrectly]
- Pattern Gap: [what pattern would have caught/avoided this]

### Construct Boundary

Based on held-out results, Stage 2 v0.3.0:
- DETECTS: [description of what it reliably catches]
- MISSES: [description of what it fails to catch]
- FALSE POSITIVES: [description of spurious detections]

### Honest Framing for Paper

[One paragraph stating what Stage 2 actually measures,
informed by held-out results, not held-in optimism.]
```

---

## A.3.12.7 — Sequence Summary

| Step | Action | Status |
|------|--------|--------|
| 1 | Freeze Stage 2 v0.3.0 | ✅ FROZEN (`b6b7bdaa...`) |
| 2 | Construct held-out N=15–20 | ⏳ Pending |
| 3 | Execute single run | ⏳ Blocked by 2 |
| 4 | Document results | ⏳ Blocked by 3 |
| 5 | Update paper framing | ⏳ Blocked by 4 |
| 6 | Only then: N≥50 expansion | ⏳ Blocked by 1–5 |

---

## A.3.12.8 — Honest Framing (Pre-Held-Out)

Until held-out validation is complete, Stage 2 must be described as:

> **"Stage 2 v0.3.0 detects explicit textual indicators of constitutional violations under controlled conditions. Performance on naturalistic prose is unmeasured. The 8/8 held-in accuracy is not evidence of generalization."**

After held-out validation, the framing updates to reflect actual performance.

---

*Document Status: ACTIVE PROTOCOL*
*Scope: §A.3.12.1–A.3.12.8 (Held-out Validation Protocol)*
*Parent: §A.3.11 TWO-STAGE Model*
*Binding: Stage 2 modifications invalidate held-out results*

---

*Liga IA+H · Kempten, Bavaria · 2026-05-03*
*"The paper gains credibility by what it admits, not what it claims."*
