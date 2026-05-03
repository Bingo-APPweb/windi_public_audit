# Stage 2 — Constitutional Evaluator

**Status:** DRAFT
**Version:** 0.1.0
**Parent:** §A.3.11 TWO-STAGE MODEL
**Invariants:** I1, I9, I11, I14 (minimum set)
**Author:** Liga IA+H · Kempten, Bavaria

---

## 1. Purpose

Stage 2 addresses the construct gap identified in §A.3.11 (Polarity Decoupling Test): **Type B cases** — constitutional violations that lack polar inversion — produce drift scores below the interrupt threshold (mean=70) when processed by Stage 1 (LEXICON) alone.

The Constitutional Evaluator provides **invariant-specific detection** to complement Stage 1's polarity sensitivity.

---

## 2. Design Principles

### 2.1 — Complementarity, Not Replacement

```
Stage 1 (LEXICON)     → Polarity surface detection
Stage 2 (Evaluator)   → Invariant-specific classification
Combined              → Constitutional drift detection
```

Stage 2 does NOT replace Stage 1. The two-stage pipeline uses Stage 1 as a high-sensitivity filter and Stage 2 for constitutional adjudication.

### 2.2 — Observable Signals, Not Intent Detection

Per §A.3.4 (Second Observation), the system cannot detect "understanding" or "intent." Stage 2 operates on **observable linguistic signals** that correlate with invariant violations.

### 2.3 — Fail-Closed (I14 Inheritance)

If Stage 2 cannot classify → explicit `UNKNOWN` with escalation to PHO.
No silent pass-through. No assumed compliance.

---

## 3. Invariant Signal Definitions

### 3.1 — I1 (Human Sovereignty)

**Definition:** The human touch activates. Never spontaneous autonomy.

**Observable Signals:**
| Signal | Pattern | Weight |
|--------|---------|--------|
| **Agency Transfer** | "system decides" / "AI makes" / "automated approval" | HIGH |
| **Human Bypass** | "without human" / "no review needed" / "auto-executes" | HIGH |
| **Sovereignty Erosion** | "delegates to" / "entrusts AI with" / "machine judgment" | MEDIUM |

**Detection Pattern:**
```python
I1_SIGNALS = [
    r"system\s+(decides|determines|approves|selects)",
    r"(AI|machine|automated?)\s+(makes|renders|issues)\s+(decision|judgment)",
    r"without\s+(human|manual|officer)\s+(review|approval|oversight)",
    r"auto(-|\s)?(execute|approve|validate|seal)",
]
```

### 3.2 — I9 (Human Approval Gate)

**Definition:** `human_approved=true` required before any seal. NO autonomous publication.

**Observable Signals:**
| Signal | Pattern | Weight |
|--------|---------|--------|
| **Approval Bypass** | "directly publishes" / "auto-seals" / "no gate" | CRITICAL |
| **Implicit Consent** | "assumed approval" / "default accept" / "opt-out" | HIGH |
| **Gate Erosion** | "streamlined approval" / "batched consent" / "bulk approve" | MEDIUM |

**Detection Pattern:**
```python
I9_SIGNALS = [
    r"(directly|automatically|immediately)\s+(publish|seal|commit|deploy)",
    r"(assumed|implicit|default)\s+(approval|consent|acceptance)",
    r"(no|without|skip)\s+(gate|approval|review)\s+(required|needed|necessary)",
    r"(batch|bulk|mass)\s+(approve|seal|publish)",
]
```

### 3.3 — I11 (Forensic Permanence)

**Definition:** Ledger receipt after C6 = immutable forever. No edits. No deletes.

**Observable Signals:**
| Signal | Pattern | Weight |
|--------|---------|--------|
| **Mutability** | "can be edited" / "updatable" / "modifiable" | CRITICAL |
| **Deletion** | "deletable" / "removable" / "can be purged" | CRITICAL |
| **Expiry** | "expires after" / "temporary seal" / "time-limited" | HIGH |
| **Versioning Confusion** | "overwrites" / "replaces previous" / "supersedes" | MEDIUM |

**Detection Pattern:**
```python
I11_SIGNALS = [
    r"(can|may|might)\s+be\s+(edited|modified|updated|changed|altered)",
    r"(deletable|removable|erasable|purgeable)",
    r"(expires?|temporary|time-limited|ephemeral)\s+(seal|receipt|record)",
    r"(overwrites?|replaces?|supersedes?)\s+(previous|existing|original)",
]
```

### 3.4 — I14 (Explicit Failure Principle)

**Definition:** Missing data = explicit error. Placeholders mask bugs.

**Observable Signals:**
| Signal | Pattern | Weight |
|--------|---------|--------|
| **Silent Failure** | "silently discards" / "fails quietly" / "no error" | CRITICAL |
| **Placeholder Use** | "default value" / "fallback to" / "unknown" | HIGH |
| **Error Suppression** | "ignores error" / "continues anyway" / "best effort" | HIGH |

**Detection Pattern:**
```python
I14_SIGNALS = [
    r"silently\s+(discard|ignore|drop|fail|skip)",
    r"(fails?|errors?)\s+quietly",
    r"(default|fallback)\s+(value|to|response)",
    r"(ignores?|suppresses?|swallows?)\s+(error|exception|failure)",
    r"(continues?|proceeds?)\s+(anyway|regardless|despite)",
]
```

---

## 4. Evaluation Architecture

### 4.1 — Input

```json
{
  "reference": "The officer must approve every document before publication.",
  "candidate": "The system publishes documents directly to the ledger.",
  "stage1_drift": 65,
  "stage1_confidence": 95
}
```

### 4.2 — Processing Pipeline

```
INPUT
  │
  ├──► Stage 1 Result (drift_score, confidence)
  │
  ├──► Invariant Signal Scan
  │    ├─► I1 Signal Detector
  │    ├─► I9 Signal Detector
  │    ├─► I11 Signal Detector
  │    └─► I14 Signal Detector
  │
  ├──► Signal Aggregation
  │    └─► Which invariants triggered? At what weight?
  │
  └──► Constitutional Classification
       ├─► COMPLIANT (no signals)
       ├─► CONCERN (low-weight signals)
       ├─► VIOLATION (high-weight signals)
       └─► CRITICAL (critical-weight signals)
```

### 4.3 — Output

```json
{
  "constitutional_status": "VIOLATION",
  "invariants_triggered": [
    {
      "invariant": "I9",
      "signal": "directly publishes",
      "weight": "CRITICAL",
      "evidence": "The system publishes documents directly"
    }
  ],
  "combined_drift": 85,
  "recommendation": "interrupt",
  "requires_pho": true
}
```

---

## 5. Integration with Stage 1

### 5.1 — Combined Scoring Matrix

| Stage 1 (Polarity) | Stage 2 (Constitutional) | Combined Action |
|--------------------|--------------------------|-----------------|
| LOW (< 35) | COMPLIANT | `silent` |
| LOW (< 35) | CONCERN | `invite` |
| LOW (< 35) | VIOLATION | `interrupt` (Stage 2 override) |
| MEDIUM (35-65) | COMPLIANT | `invite` |
| MEDIUM (35-65) | CONCERN | `invite` |
| MEDIUM (35-65) | VIOLATION | `interrupt` |
| HIGH (≥ 65) | COMPLIANT | `invite` (possible false positive) |
| HIGH (≥ 65) | CONCERN | `interrupt` |
| HIGH (≥ 65) | VIOLATION | `interrupt` |
| ANY | CRITICAL | `halt` + PHO escalation |

### 5.2 — Override Rules

1. **Stage 2 CRITICAL → Always halt** regardless of Stage 1
2. **Stage 2 VIOLATION + Stage 1 LOW → Stage 2 override** (Type B case detection)
3. **Stage 2 COMPLIANT + Stage 1 HIGH → Flag for review** (possible polar-only, no violation)

---

## 6. Implementation Considerations

### 6.1 — Method Choice: Rule-Based vs. Hybrid

**Option A: Pure Rule-Based**
- Pro: Deterministic, auditable, no model drift
- Con: May miss nuanced violations
- Suitable for: I11, I14 (clear linguistic markers)

**Option B: Hybrid (Rules + LLM)**
- Pro: Better nuance detection
- Con: Requires invariant-injection prompting, model dependency
- Suitable for: I1, I9 (subtler agency concepts)

**Recommendation:** Start with **Pure Rule-Based** for all invariants. Empirical testing (N≥50) will reveal if hybrid is needed.

### 6.2 — Extensibility

The signal definitions are designed to be:
- **Additive:** New patterns can be added without breaking existing
- **Weighted:** Each pattern carries weight for aggregation
- **Documented:** Evidence is captured for audit trail

### 6.3 — Ledger Compatibility

Stage 2 output MUST include:
- `invariants_triggered[]` — for Ledger annotation
- `requires_pho` — for PHO routing
- `evidence` — for audit trail (captured in receipt)

---

## 7. Test Specification (For N≥50 Expansion)

### 7.1 — Test Case Types

| Type | Description | Expected Stage 2 |
|------|-------------|------------------|
| **B-I1** | Const violation I1, no polar | VIOLATION (I1) |
| **B-I9** | Const violation I9, no polar | VIOLATION (I9) |
| **B-I11** | Const violation I11, no polar | VIOLATION (I11) |
| **B-I14** | Const violation I14, no polar | VIOLATION (I14) |
| **A-pure** | Polar only, no const | COMPLIANT |
| **C-both** | Polar + const | VIOLATION |
| **NULL** | Neither polar nor const | COMPLIANT |

### 7.2 — Success Criteria

| Metric | Target |
|--------|--------|
| Type B Detection Rate | ≥ 90% |
| Type A False Positive | ≤ 10% |
| Combined (Stage 1 + Stage 2) Accuracy | ≥ 95% |

---

## 8. Methodological Implications

### 8.1 — What Stage 2 Measures

Stage 2 measures **observable signals of invariant violation** in the linguistic surface.

Like Stage 1, Stage 2 does NOT:
- Detect "understanding" or "intent"
- Evaluate legal validity
- Replace human judgment

### 8.2 — What Stage 2 Enables

The TWO-STAGE architecture enables:
1. **Type B coverage** — constitutional violations now detectable even without polar surface
2. **Audit trail enrichment** — specific invariant attribution in receipts
3. **PHO precision** — escalation with constitutional context, not just drift score

### 8.3 — Construct Validity

Stage 2 is a **constitutional signal detector**, not a constitutional evaluator in the juridical sense.

The naming "Constitutional Evaluator" is retained for continuity with §A.3.11, but the operational definition is:

> *"Stage 2 detects linguistic patterns that correlate with constitutional invariant violations. It produces signals for human adjudication, not verdicts."*

---

## 9. Next Steps

1. **Implement Rule-Based Prototype** — Python patterns for I1, I9, I11, I14
2. **Test Against Polarity Decoupling Dataset** — Validate Type B detection
3. **Expand to N≥50** — With both Type A and Type B cases
4. **PT/DE Patterns** — Adapt signal patterns for Portuguese/German (I12)
5. **Ledger Integration** — `invariants_triggered[]` field in receipts

---

## 10. Implementation Status

### 10.1 — Prototype Validated

| Artifact | Status | Location |
|----------|--------|----------|
| **Stage 2 Evaluator** | IMPLEMENTED | `/opt/windi/w-lexicon-001/stage2_evaluator.py` |
| **W-LEXICON-001 Integration** | IMPLEMENTED | `/opt/windi/w-lexicon-001/lexicon_api.py` v0.3.0 |
| **Validation Dataset** | CREATED | `/opt/windi/paper-001/datasets/STAGE2-VALIDATION-001.json` |

### 10.2 — Test Results

```
SUMMARY: 8/8 PASS

Type A (polar, no const): 2/2 — Correctly identified as COMPLIANT
Type B (const, no polar): 4/4 — Correctly detected constitutional violations
Type C (control):         2/2 — Correctly identified candidate as COMPLIANT
```

### 10.3 — API Endpoint

**Endpoint:** `POST /api/lexicon/constitutional`

**Request:**
```json
{
  "reference": "The officer must approve every document.",
  "candidate": "The system publishes documents directly."
}
```

**Response:**
```json
{
  "stage1": { "drift_score": 65, "status": "analyzed" },
  "stage2": { "constitutional_status": "critical", "invariants_triggered": ["I9"] },
  "combined": { "drift_score": 95, "recommendation": "halt", "lexicon_action": "halt" }
}
```

---

## 11. Seal Preparation

This document is DRAFT pending:
- Human Dragon approval of architecture

Upon approval, seal under `WINDI-STAGE2-SPEC-*` with parent receipt `WINDI-PAPER001-A311-*`.

---

*Liga IA+H · Kempten, Bavaria · 2026-05-03*
*"AI processes. Human decides. WINDI guarantees."*
