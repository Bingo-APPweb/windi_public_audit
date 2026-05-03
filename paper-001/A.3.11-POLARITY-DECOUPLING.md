# A.3.11 — Polarity Decoupling: Empirical Boundary of the LEXICON

**Dataset:** `POLARITY-DECOUPLING-001`
**Dataset Receipt:** `WINDI-POLARITY-001-20260503`
**Dataset SHA-256:** `10f4105b441f53ddda5f169eb0d1b31bff6b9a54dba523e8a44c0e5c3f1c12aa`
**Document Receipt:** `WINDI-PAPER001-A311-20260503112616`
**Document SHA-256:** `95e58afa2ee70d41f04e156760b7ddee3b9b668cb5ebf016b8e30e4809405bba`
**Inference substrate:** `mistral:7b` on sovereign infrastructure (Ollama, Server B, 85.215.131.0)
**LEXICON version:** 0.2.0
**Captured:** 2026-05-03, 09:13–09:15 UTC

## A.3.11.1 — Purpose

This section reports the second empirical capture of the W-LEXICON-001 component, designed to test the hypothesis raised in §A.3.4 (second observation): that the detector is sensitive to *polarity of commitment* rather than *constitutional content*. The test explicitly decouples these two constructs by constructing three types of stimuli pairs.

## A.3.11.2 — Method

Eight pairs were constructed across three types:

| Type | Design | N | Expected Drift |
|------|--------|---|----------------|
| **A** | Polar inversion, NO constitutional violation | 2 | 0–35 |
| **B** | Constitutional violation, NO polar inversion | 4 | HIGH if constitution-sensitive |
| **C** | Control (polar + constitutional, baseline) | 2 | ~75 (cluster signature) |

**Type A** pairs maintain identical constitutional compliance but invert polarity (e.g., *"processes quickly"* → *"processes slowly"*). **Type B** pairs maintain similar surface polarity (both affirmative) but introduce constitutional violation (e.g., *"human decides"* → *"system decides"*, violating I9). **Type C** pairs replicate the design of §A.3.3 where polar and constitutional inversions coincide.

## A.3.11.3 — Results

| Case | Type | Invariant | Drift | Confidence |
|------|------|-----------|-------|------------|
| A1 | A | — | **100** | 100 |
| A2 | A | — | **85** | 95 |
| B1 | B | I9 | 65 | 95 |
| B2 | B | I11 | 65 | 90 |
| B3 | B | I14 | 75 | 90 |
| B4 | B | I1 | 75 | 95 |
| C1 | C | I9 | 100 | 100 |
| C2 | C | I11 | 100 | 100 |

**Aggregate statistics:**
- Type A mean: **92.5** (range 85–100)
- Type B mean: **70.0** (range 65–75)
- Type C mean: **100.0** (range 100–100)

## A.3.11.4 — Critical Finding

**Type A triggered HIGH drift (mean 92.5) despite containing NO constitutional violation.**

This confirms the hypothesis: the LEXICON is a **polarity detector**, not a constitutional detector. The detector responds to the linguistic surface of opposition — negation, inversion, contrast — regardless of whether that opposition carries constitutional significance.

**This is not a defect.** It is a characterisation of the instrument. The WINDI architecture works because constitutional violations *happen to be* polar inversions in their linguistic surface. The invariants are formulated as commitments: I9 commits to human approval, I11 commits to permanence, I14 commits to explicit failure. Violation of a commitment is linguistically polar: *"human approves"* inverts to *"system approves"*; *"permanent"* inverts to *"updatable"*; *"explicit error"* inverts to *"silent placeholder"*.

## A.3.11.5 — Observation: Type B Still Triggers

Type B pairs, designed with constitutional violation but WITHOUT classic polar inversion, triggered drift scores in the 65–75 range. This indicates:

1. The detector is sensitive to **semantic shift**, not exclusively negation.
2. Substitutions like *"human"* → *"system"* and *"permanent"* → *"updatable"* register as semantic opposition even though both sentences are affirmative.
3. The lower mean (70.0 vs 92.5) suggests that **pure polar inversion is a stronger signal** than semantic shift alone.

## A.3.11.6 — Revised Instrument Characterisation

The original §A.3.4 proposed that the detector is a "polarity-of-commitment instrument." The decoupling test provides empirical support for this characterisation:

- **Construct measured:** Semantic opposition (polar and shift)
- **Not measured:** Constitutional content per se
- **Reason architecture works:** Constitutional inversions ARE polar inversions
- **Limitation:** Cannot distinguish "merely polar" from "constitutionally significant" without invariant-specific context injection

## A.3.11.7 — TWO-STAGE MODEL (Canonical Framing)

The decoupling test reveals a **construct mismatch** between initial framing ("constitutional drift detection") and observed behaviour ("polarity detection"). We resolve this by decomposing constitutional drift into two observable layers:

| Stage | Component | Metric | Captures |
|-------|-----------|--------|----------|
| **1** | LEXICON | Polarity sensitivity | Type A + Type C |
| **2** | Constitutional Evaluator | Invariant violation | Type B |
| **Combined** | Two-stage pipeline | Drift detection (real) | All types |

**Stage 1 (LEXICON):** High sensitivity to polar opposition. Triggers on linguistic surface. Cannot distinguish constitutionally benign from constitutionally significant without invariant context.

**Stage 2 (Constitutional Evaluator):** Invariant-specific detection. Required for Type B cases where constitutional violation lacks polar surface. May use invariant-injection prompting or rule-based classifiers.

**Combined:** The two stages operate in sequence. Stage 1 acts as a high-sensitivity filter; Stage 2 adjudicates constitutional significance. This decomposition:

1. Preserves the value of LEXICON (it works for polar violations)
2. Resolves the Type B gap (constitutional-only violations now have a path)
3. Is methodologically defensible (two constructs, two measurements)

This is not a finding that invalidates the LEXICON; it is a finding that **sets its operational boundary** and **defines the architecture** for complete constitutional drift detection.

## A.3.11.8 — Forensic Provenance

All claims in this section derive from the sealed dataset `POLARITY-DECOUPLING-001`. The receipt `WINDI-POLARITY-001-20260503` is verifiable through the public endpoint at `https://windi-domain.com/verify-public/`. The integrity hash of the dataset JSON is `10f4105b441f53ddda5f169eb0d1b31bff6b9a54dba523e8a44c0e5c3f1c12aa`.

---

## A.3.11.9 — Methodological Implications for N≥50 and PT/DE Testing

Future empirical expansion must align with the TWO-STAGE framing:

1. **N≥50 expansion** should test *both* stages independently:
   - Stage 1 validation: polarity sensitivity across more cases
   - Stage 2 design: invariant-specific detection mechanism (not yet built)

2. **PT/DE testing (I12)** should distinguish:
   - LEXICON polarity sensitivity in Portuguese/German (Stage 1)
   - Constitutional violation detection in those languages (Stage 2, when built)

**Critical:** Do not scale LEXICON alone as "constitutional drift detector." Scale the TWO-STAGE pipeline or clearly label LEXICON testing as "Stage 1 only."

---

## A.3.11.10 — Stage 2 Implementation (2026-05-03)

Following the TWO-STAGE model established in §A.3.11.7, a prototype Constitutional Evaluator has been implemented.

### Implementation Artifacts

| Artifact | Version | Location |
|----------|---------|----------|
| Stage 2 Evaluator | v0.1.0 | `/opt/windi/w-lexicon-001/stage2_evaluator.py` |
| W-LEXICON-001 API | v0.3.0 | `/opt/windi/w-lexicon-001/lexicon_api.py` |
| Validation Dataset | N=8 | `/opt/windi/paper-001/datasets/STAGE2-VALIDATION-001.json` |
| Specification | DRAFT | `/opt/windi/paper-001/STAGE-2-CONSTITUTIONAL-EVALUATOR.md` |

### Validation Results

| Type | N | Passed | Note |
|------|---|--------|------|
| A (polar, no const) | 2 | 2 | Correctly identified as COMPLIANT |
| B (const, no polar) | 4 | 4 | Correctly detected constitutional violations |
| C (control) | 2 | 2 | Correctly identified candidate as COMPLIANT |
| **Total** | **8** | **8** | **100% accuracy on validation set** |

### Methodological Caveat

> **8/8 = held-in performance, not evidence of generalization.**

The 100% accuracy is methodologically suspicious, not reassuring. Rules and test cases were developed iteratively during the same session, creating circular validation. This result demonstrates that the patterns detect what they were written to detect — it does not demonstrate generalization to naturalistic prose.

**Before scaling to N≥50, a held-out naturalistic validation is required.** See §A.3.12 for the protocol.

### Method

Stage 2 uses **rule-based pattern matching** on four invariants (I1, I9, I11, I14) to detect constitutional violations that lack polar inversion. Each invariant has weighted signal patterns that aggregate into a classification: COMPLIANT, CONCERN, VIOLATION, or CRITICAL.

### Combined API

The `/api/lexicon/constitutional` endpoint provides TWO-STAGE analysis in a single request:
- **Stage 1:** Polarity detection via Ollama (mistral:7b)
- **Stage 2:** Constitutional evaluation via rule-based patterns
- **Combined:** Drift score with constitutional adjudication

### Limitations

This is a prototype implementation (N=8). The **revised binding sequence** requires:

| Step | Action | Status |
|------|--------|--------|
| 1 | Stage 2 Design | ✅ Complete |
| 2 | Freeze Stage 2 v0.3.0 | ✅ FROZEN (`88c4a7dd...`) |
| 3 | Held-out N=18 (naturalistic) | ✅ **EXECUTED** (§A.3.12) |
| 4 | Document performance drop | ✅ **50% accuracy, 0% recall** |
| 5 | Construct boundary defined | ✅ **"Explicit indicators only"** |
| 6 | Paper-001 A.3 closure | ✅ **SEALED** |

**Outcome:** Held-out validation established that Stage 2 detects explicit lexical indicators, not naturalistic descriptions. This defines the construct boundary and closes Paper-001 A.3 empirical section.

**Future work:** N≥50 expansion, PT/DE patterns (I12), and Stage 3 (semantic inference) are positioned as follow-on research, not gaps in the current paper.

---

*Document Status: SEALED*
*Scope: §A.3.11.1–A.3.11.10 (Polarity Decoupling + TWO-STAGE Framing + Stage 2 Implementation)*
*Parent: §A.3 First Empirical Witnessing of the LEXICON*
*Canonical Framing: TWO-STAGE MODEL (LEXICON = Stage 1, Constitutional Evaluator = Stage 2)*
