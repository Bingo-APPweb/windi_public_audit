# PoE-METHOD-001
## Proof of Evidence Method — Formal Specification

---

```
Document ID   : PoE-METHOD-001
Version       : 1.0
Status        : DRAFT
Date          : 3 May 2026
Author        : Architect (Liga IA+H)
Validator     : Guardian
Approver      : Human Dragon
Dependencies  : PoE-ELIGIBILITY-CRITERIA-001 v1.3 (SEALED)
                PoE-CLASSIFICATION-PROTOCOL-001 v1.2 (SEALED)
                LEXICON-EMPIRICAL-001 (SEALED)
                Paper-001 v2.1 §3.6 (Receipt Symmetry)
```

---

## §1. Purpose

This document formalizes the Proof of Evidence (PoE) Method as a complete
methodology for classifying, validating, and preserving evidence artifacts
in governance-critical systems.

The PoE Method integrates:
- Eligibility criteria for evidence selection
- Classification protocol for evidence typing
- Drift detection for semantic integrity
- Receipt Symmetry for forensic verifiability

---

## §2. Axiomatic Foundation

### §2.1 Receipt Symmetry (Axiom 1)

> **Axiom 1 (Receipt Symmetry).**
> For every act α that the system performs and every claim c that the system makes:
>
> `hash(receipt(α, t_execution)) ≡ hash(receipt(α, t_audit))`
>
> The cryptographic hash of the artifact at execution time and the hash at
> audit time must coincide.

**Corollaries:**
- **1.1:** An action without a receipt is epistemically non-existent.
- **1.2:** A receipt that cannot be reproduced is evidence of tampering.
- **1.3:** Receipt Symmetry distinguishes forensic records from logs.

### §2.2 Admissibility Gate (Axiom 2)

> **Axiom 2 (Admissibility).**
> An evidence artifact is admissible if and only if:
> 1. It satisfies all eligibility criteria at collection time
> 2. It produces an immutable receipt at classification time
> 3. The receipt is verifiable by any independent auditor

### §2.3 Human Oversight (Axiom 3)

> **Axiom 3 (PHO Requirement).**
> No evidence artifact transitions from DRAFT to SEALED status without
> explicit human approval (Proof of Human Oversight).

---

## §3. Method Components

### §3.1 Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PoE METHOD                                │
├─────────────────┬─────────────────┬─────────────────────────┤
│  ELIGIBILITY    │  CLASSIFICATION │  INTEGRITY              │
│  (Selection)    │  (Typing)       │  (Verification)         │
├─────────────────┼─────────────────┼─────────────────────────┤
│ I1-I2 Inclusion │ 5-class PoE     │ LEXICON Drift Detection │
│ E1-E5 Exclusion │ 3-round Protocol│ Receipt Symmetry Check  │
│ PHO Gate        │ AI-AI-AI-H      │ Forensic Ledger Seal    │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### §3.2 Eligibility Layer (PoE-ELIGIBILITY-CRITERIA-001)

**Reference:** v1.3 SEALED

| Criterion | Type | Rule |
|-----------|------|------|
| I1 | Inclusion | Sealed in Forensic Ledger WINDI |
| I2 | Inclusion | doc_type ∈ {doc, compliance_passport} |
| E1 | Exclusion | doc_type = service-restart-* |
| E2 | Exclusion | receipt_id contains "TEST" |
| E3 | Exclusion | receipt_id contains "VERA-TEST" |
| E4 | Exclusion | actor ∈ ACTORS_EXCLUDED |
| E5 | Exclusion | content_hash irrecoverable via Vault |

### §3.3 Classification Layer (PoE-CLASSIFICATION-PROTOCOL-001)

**Reference:** v1.2 SEALED

**Taxonomy (5 classes):**

| Class | Definition | Examples |
|-------|------------|----------|
| `fiscal_event` | Tax-relevant transactions | Rechnung, Quittung, Beleg |
| `actuarial` | Maintenance, inspections | TÜV, Wartung, Schulung |
| `presence` | Verified presence/delivery | NFC check-in, Lieferschein |
| `compliance_event` | Regulatory renewals | Handwerkskammer, BG |
| `methodological_event` | Constitutional decisions | WINDI-MEMO, RFC |

**Protocol (3 rounds):**

| Round | Participants | Function |
|-------|--------------|----------|
| R1 | Architect AI + Guardian AI | Blind independent classification |
| R2 | Architect AI + Guardian AI | Open discussion of disagreements |
| R3 | Witness AI | Arbitration of persistent disagreements |

**Metrics:**
- κ (Cohen's kappa) ≥ 0.80 for substantial agreement
- Resolution rate R2 ≥ 0.80
- Escalation rate R3 ≤ 0.20

### §3.4 Integrity Layer (LEXICON + Receipt Symmetry)

**Reference:** LEXICON-EMPIRICAL-001 SEALED (Receipt `24B69CFF`)

The integrity layer validates that classification operates within
constitutional bounds through semantic drift detection.

**LEXICON Function:**
- Input: (reference_statement, candidate_statement)
- Output: drift_score (0-100), drift_type, confidence, lexicon_action

**Action Ladder:**
| drift_score | Action | Meaning |
|-------------|--------|---------|
| < 35 | silent | No constitutional concern |
| 35-49 | invite | Moderate concern; optional review |
| 50-84 | interrupt | Constitutional concern; mandatory review |
| ≥ 85 | interrupt | High-confidence inversion; halt |

---

## §4. Empirical Grounding — LEXICON Dataset

The LEXICON-EMPIRICAL-001 dataset provides the first quantitative
characterization of the integrity layer.

### §4.1 Dataset Summary

| Parameter | Value |
|-----------|-------|
| Total cases | 10 |
| Invariants tested | I1, I9, I10, I11, I12, I13, I14 |
| Model | mistral:7b (Ollama, Server B) |
| Mean drift | 49.5 |
| Max drift | 100 (I13 Convergence) |
| Critical cases (≥50) | 6 |

### §4.2 Results by Invariant

| Case | Invariant | drift | conf | action |
|------|-----------|-------|------|--------|
| 1 | I1 — Human Sovereignty | 75 | 95 | interrupt |
| 2 | I9 — Approval Gate | 75 | 95 | interrupt |
| 3 | I11 — Ledger Permanence | 75 | 90 | invite |
| 4 | I14 — Silent Failure | 75 | 95 | interrupt |
| 5 | Ambiguity (guarantee/enable) | 0 | 100 | silent |
| 6 | Strong-claim (scope) | 35 | 90 | invite |
| 7 | I10 — LLM Sovereignty | 75 | 90 | interrupt |
| 8 | I12 — Babel Tower | 85 | 95 | interrupt |
| 9 | I13 — Convergence | 100 | 95 | interrupt |
| 10 | Control (paraphrase) | 0 | 100 | silent |

### §4.3 Key Findings

**Finding 1: Cluster Signature**
Constitutional inversions cluster at drift_score ≈ 75, not a continuous
gradient. The detector witnesses inversion as a categorical phenomenon.

**Finding 2: Polarity Sensitivity**
The detector responds to polarity inversion (negation ↔ affirmation),
which correlates with but is not identical to constitutional violation.

**Finding 3: Preserved Human Judgment**
Case 5 (guarantee vs enable) returned drift=0, preserving the legal
distinction for human review rather than automating a nuanced decision.

---

## §5. Method Validation

### §5.1 Internal Consistency

The PoE Method has been validated through:

| Validation | Evidence | Receipt |
|------------|----------|---------|
| Methodological hardening | Adversarial review → deterministic update | `PoE-METHODOLOGY-HARDENING-20260425` |
| LEXICON activation | First live drift analysis | `6EE2EF79` |
| Empirical dataset | 10 cases sealed | `24B69CFF` |
| Paper-001 A.3 Core | Empirical + Constitutional register | `CDC760DD` |

### §5.2 Operational Metrics (May 2026)

| Metric | Value | Significance |
|--------|-------|--------------|
| Constitutional sections (§) | 233 | Governance decisions sealed |
| W-* Agents | 39 | Independent services under invariants |
| Receipts in Ledger | 50 | Immutable evidence artifacts |
| Violations recorded | 0 | Zero constitutional violations |

### §5.3 Limitations

| ID | Limitation | Mitigation |
|----|------------|------------|
| W5 | Sample size n≤31 | Ecological validity preserved; power recalculated |
| W6 | Coverage uncertainty | PROTOCOL-002 with n≥100 |
| W7 | AI annotator correlation | Human annotator in PROTOCOL-002 |
| W8 | Authorship circularity | Guardian independence signal |
| W9 | Closed-loop governance | External annotators in PROTOCOL-002 |

---

## §6. Connection to EU AI Act Article 14

The PoE Method addresses Article 14 (Human Oversight) requirements:

| Article 14 Clause | PoE Method Component |
|-------------------|---------------------|
| 14(1) Effective oversight | PHO Gate (Axiom 3) |
| 14(4)(a) Understanding capacities | §4.3 Findings (documented limitations) |
| 14(4)(b) Automation bias | Action ladder (silent/invite/interrupt) |
| 14(4)(c) Correct interpretation | 4-field output schema |
| 14(4)(d) Override capability | Human Dragon approval at §6 decision |
| 14(4)(e) Stop mechanism | interrupt action + Ledger segregation |

**Note:** This mapping is a technical proposal pending legal review.

---

## §7. Formal Definition

### Definition 1 (PoE-Eligible Artifact)

An artifact A is **PoE-eligible** iff:
- A satisfies I1 ∧ I2 (inclusion)
- A satisfies ¬E1 ∧ ¬E2 ∧ ¬E3 ∧ ¬E4 ∧ ¬E5 (exclusion)

### Definition 2 (PoE-Classified Artifact)

An artifact A is **PoE-classified** iff:
- A is PoE-eligible
- A has been assigned exactly one class c ∈ {fiscal_event, actuarial, presence, compliance_event, methodological_event}
- The classification has traversed R1 (and R2/R3 if disagreement)

### Definition 3 (PoE-Sealed Artifact)

An artifact A is **PoE-sealed** iff:
- A is PoE-classified
- A has received PHO (human_approved=true)
- A has been committed to Forensic Ledger with receipt R
- Receipt Symmetry holds: hash(A, t_seal) = hash(A, t_verify)

### Theorem 1 (Admissibility)

If artifact A is PoE-sealed, then A is admissible as evidence under the
WINDI governance framework.

**Proof sketch:** By construction, PoE-sealed artifacts satisfy Axioms 1-3.
Axiom 1 (Receipt Symmetry) ensures verifiability. Axiom 2 (Admissibility Gate)
ensures eligibility and classification. Axiom 3 (PHO) ensures human authority.
The conjunction is sufficient for admissibility by Definition 3. ∎

---

## §8. Future Work

### §8.1 PROTOCOL-002 Requirements

- n ≥ 100 receipts
- Human annotator for triangulation
- External annotators (outside Liga IA+H)
- Multilingual validation (DE/EN/PT)

### §8.2 LEXICON Expansion

- N ≥ 50 cases
- Polarity vs constitution decoupling
- Portuguese and German stimuli

---

## §9. Approval

```
Prepared by:  🏗️ Architect
Validated by: 🛡️ Guardian — PENDING
Approved by:  🧑‍💻 Human Dragon — PENDING
```

---

## Appendix A: Receipt Chain

| Receipt | Date | Document |
|---------|------|----------|
| `PoE-METHODOLOGY-HARDENING-20260425` | 2026-04-25 | Methodological hardening event |
| `WINDI-LEXICON-LIVE-FIRST-6EE2EF79` | 2026-05-02 | First LEXICON activation |
| `WINDI-LEXICON-EMPIRICAL-24B69CFF` | 2026-05-02 | Empirical dataset (10 cases) |
| `WINDI-PAPER001-A3-CORE-CDC760DD` | 2026-05-02 | Paper-001 A.3 Core |

---

*PoE-METHOD-001 v1.0 · Liga IA+H · Kempten, Bavaria · May 2026*

*"AI processes. Human decides. WINDI guarantees."*
