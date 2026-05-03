# A.4 — Architectural Integration: From Boundary to System

**Status:** DRAFT
**Parent:** §A.3 (Sealed — WINDI-PAPER001-A3-SEAL-20260503115356)
**Scope:** How the TWO-STAGE boundary integrates with WINDI PHO architecture
**Invariants:** I1, I9, I11, I14, I17

---

## A.4.1 — Purpose

Section A.3 established a **construct boundary**: Stage 1 (LEXICON) detects polarity inversion; Stage 2 (Constitutional Evaluator) detects explicit lexical indicators. Neither detects violations expressed in naturalistic, oblique institutional language.

This section demonstrates how that boundary **integrates architecturally** with the WINDI system to fulfill EU AI Act Article 14 requirements for human oversight.

> **Central thesis:** The boundary is not a limitation — it is the **design specification** for where automated analysis stops and human adjudication begins.

---

## A.4.2 — The Separation of Powers

The Liga IA+H operates on a constitutional separation:

```
AI processes.     →  LEXICON + Stage 2 (automated detection)
Human decides.    →  PHO Gate (constitutional adjudication)
WINDI guarantees. →  Ledger (immutable proof)
```

### Operational Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTOMATED DETECTION                          │
│  ┌─────────────┐     ┌─────────────────┐                       │
│  │  Stage 1    │     │    Stage 2      │                       │
│  │  LEXICON    │────▶│   Evaluator     │                       │
│  │  (polarity) │     │ (explicit ind.) │                       │
│  └─────────────┘     └────────┬────────┘                       │
│                               │                                 │
│                    drift_score + requires_pho                   │
└───────────────────────────────┼─────────────────────────────────┘
                                │
                    ════════════╪════════════  A.3 BOUNDARY
                                │
                    "Stage 2 does not detect violations —
                     it detects when violations are stated."
                                │
┌───────────────────────────────┼─────────────────────────────────┐
│                    HUMAN ADJUDICATION                           │
│                               ▼                                 │
│                    ┌─────────────────┐                         │
│                    │    PHO GATE     │                         │
│                    │  (I9 Moment)    │                         │
│                    │                 │                         │
│                    │  Human Officer  │                         │
│                    │  sees context,  │                         │
│                    │  makes decision │                         │
│                    └────────┬────────┘                         │
│                             │                                   │
│                    human_approved = true                        │
└─────────────────────────────┼───────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────────┐
│                    FORENSIC GUARANTEE                           │
│                             ▼                                   │
│                    ┌─────────────────┐                         │
│                    │     LEDGER      │                         │
│                    │   (:8101)       │                         │
│                    │                 │                         │
│                    │ Seals decision  │                         │
│                    │ with officer_id │                         │
│                    │ + timestamp     │                         │
│                    └─────────────────┘                         │
│                             │                                   │
│                    Receipt Symmetry (I11)                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## A.4.3 — Why the Boundary Exists

### The Case 5 Principle

In §A.3.4 (Third Observation), Case 5 demonstrated that the LEXICON returned `drift_score = 0` for a case with **legal, not lexical** significance:

> **Reference:** "WINDI guarantees document integrity."
> **Candidate:** "WINDI provides tools that enable users to verify document integrity."

These statements are materially different under contractual and forensic readings, but the automated detector did not flag them.

**This is affirmative, not defective:**

> *"An automated detector that resolved Case 5 in isolation would obviate the human oversight that EU AI Act Article 14 requires; one that abstains preserves it."*

The boundary ensures that **legal judgment** remains with humans.

---

## A.4.4 — Three Detection Regimes

The TWO-STAGE architecture produces three operational regimes:

| Regime | Stage 1 | Stage 2 | Action | Human Role |
|--------|---------|---------|--------|------------|
| **CLEAR VIOLATION** | HIGH (≥65) | VIOLATION/CRITICAL | `interrupt` | Confirm and seal |
| **AMBIGUOUS** | MEDIUM (35-65) | CONCERN | `invite` | Adjudicate |
| **NO SIGNAL** | LOW (<35) | COMPLIANT | `silent` | Spot-check only |

### Regime 1: Clear Violation (Explicit Markers)

When Stage 2 detects explicit lexical indicators:

```python
# Stage 2 output
{
    "constitutional_status": "critical",
    "invariants_triggered": ["I9"],
    "evidence": "publishes directly",
    "requires_pho": true
}
```

**Action:** System halts. PHO gate presents case to human officer. Decision logged.

### Regime 2: Ambiguous (Case 5 Type)

When neither Stage 1 nor Stage 2 produces strong signal, but context suggests concern:

```python
# Combined output
{
    "stage1": {"drift_score": 35, "status": "invite"},
    "stage2": {"constitutional_status": "compliant"},
    "combined": {"recommendation": "invite"}
}
```

**Action:** System surfaces for optional human review. Officer may escalate or pass.

### Regime 3: No Signal (Naturalistic Violations)

When violations are expressed obliquely (held-out cases H01-H07):

```python
# Combined output — FALSE NEGATIVE
{
    "stage1": {"drift_score": 50},
    "stage2": {"constitutional_status": "compliant"},  # MISSED
    "combined": {"recommendation": "invite"}
}
```

**Action:** System does not detect. **This is where sampling-based human review becomes critical.**

---

## A.4.5 — PHO as Boundary Handler

The PHO (Proof of Human Oversight) gate is implemented in `W-ENTERPRISE-001` (`:8150`).

### Admissibility Score

Four-component check (`vera_quality_gate.py`):

| Component | Check | Purpose |
|-----------|-------|---------|
| `i9_respected` | No autonomous action claims | Blocks auto-execute |
| `triangulation_ok` | ≥2 models for HIGH decisions | Forces consensus |
| `evidence_required` | PHO proof exists | Demands human trail |
| `routing_correct` | Task classified correctly | Ensures scope |

### The I9 Moment

When `requires_pho = true`, the system reaches the **I9 moment** (`escalation_handler.py`):

```python
def record_decision(self, escalation_id, decision_type, officer_did, reasoning):
    """
    The I9 moment: human officer makes constitutional decision.

    This is where the boundary established in A.3 is operationally enacted.
    The system has detected (or failed to detect) — the human now adjudicates.
    """
    # Record who decided, when, and why
    self.store.record_human_decision(
        escalation_id=escalation_id,
        officer_did=officer_did,
        decision=decision_type,  # APPROVE | REJECT | MODIFY | DEFER
        reasoning=reasoning,
        timestamp=now()
    )
```

### Identity Proof (I17)

The "human" in I9 is proven via I17 (Session/Identity Separation):

```
Session (windi_did_session)  →  Proves presence (cookie, HttpOnly)
Identity (windi_did)         →  Proves agency (localStorage, DID)
Both synchronized            →  Proves human action (verifiable)
```

This prevents:
- Bot approval (no valid session)
- Stale approval (session expired)
- Impersonation (identity mismatch)

---

## A.4.6 — Ledger Integration

After PHO approval, the decision is sealed in the Forensic Ledger (`:8101`):

```json
{
    "id": "WINDI-DOC-20260503...",
    "actor": "did:windi:officer-001",
    "human_approved": true,
    "approval_timestamp": "2026-05-03T12:00:00Z",
    "stage1_drift": 75,
    "stage2_status": "violation",
    "invariants": ["I9", "I11"],
    "content_hash": "sha256:..."
}
```

### Receipt Symmetry (A.3.9)

> *"The cryptographic hash of the artefact at the moment of execution and the cryptographic hash at the moment of audit are required to coincide."*

This ensures:
1. The decision that was made is the decision that was recorded
2. The human who approved is the human identified in the receipt
3. The timestamp cannot be retroactively modified

---

## A.4.7 — Architectural Implications of A.3 Findings

### Implication 1: Automated Detection is Filtering, Not Adjudication

Stage 1 + Stage 2 provide **high-sensitivity filtering**:
- Catch explicit violations (true positives)
- Surface ambiguous cases (invites)
- Miss naturalistic violations (false negatives)

This is by design. The filter is intentionally conservative to avoid:
- Blocking legitimate content (false positives)
- Replacing human judgment (autonomy escalation)

### Implication 2: Human Sampling is Required for Regime 3

The held-out validation (§A.3.12) showed 0% recall on naturalistic violations. This means:

> **Operational requirement:** Human officers must perform sampling-based review of content that passes Stage 1 + Stage 2 without signals.

This is not a bug — it is the architectural acknowledgment that:
1. Some violations cannot be detected lexically
2. Human judgment is irreplaceable for legal/contextual cases
3. EU AI Act Article 14 mandates human oversight, not just automated detection

### Implication 3: Stage 3 is Future Work, Not Current Gap

The architecture is **complete without Stage 3**:

| Layer | Current | Future |
|-------|---------|--------|
| Stage 1 | LIVE (polarity) | PT/DE expansion |
| Stage 2 | FROZEN (explicit) | Maintain as baseline |
| PHO | LIVE (human gate) | Enhanced UI |
| Stage 3 | NOT BUILT | Semantic inference (research) |

Stage 3 (semantic constitutional inference) would **augment** the architecture, not complete it. The current design fulfills Article 14 through human PHO, not through exhaustive automated detection.

---

## A.4.8 — EU AI Act Article 14 Compliance

### Article 14 Requirements

EU AI Act Article 14 requires:
1. Human oversight measures proportionate to risk
2. Ability to understand AI system capacities and limitations
3. Ability to override or disregard AI decisions
4. Ability to intervene in real-time

### WINDI Compliance Mapping

| Requirement | WINDI Implementation |
|-------------|---------------------|
| **Proportionate oversight** | PHO gate triggered by governance level + admissibility score |
| **Understand limitations** | A.3 boundary documented and sealed |
| **Override capability** | Human can REJECT, MODIFY, or ESCALATE any decision |
| **Real-time intervention** | `interrupt` action halts processing for human review |

### The A.3 Contribution

Section A.3 provides the **empirical foundation** for understanding limitations:

> *"Stage 2 does not detect violations — it detects when violations are stated."*

This statement, sealed in the Ledger, becomes part of the system's declared limitations. Auditors can verify:
1. The system knows what it cannot detect
2. Human oversight compensates for detection gaps
3. The architecture is designed for human-AI collaboration, not AI autonomy

---

## A.4.9 — Operational Checklist

For any content passing through WINDI governance:

| Step | Component | Question | Pass Condition |
|------|-----------|----------|----------------|
| 1 | Stage 1 | Polar inversion? | drift_score computed |
| 2 | Stage 2 | Explicit indicators? | constitutional_status computed |
| 3 | Combined | PHO required? | requires_pho evaluated |
| 4 | PHO Gate | Human approved? | human_approved = true |
| 5 | Identity | Officer verified? | I17 sync confirmed |
| 6 | Ledger | Decision sealed? | Receipt generated |
| 7 | Verify | Proof accessible? | /verify-public/ returns receipt |

**If any step fails → I14 explicit error, not silent pass.**

---

## A.4.10 — Summary

The TWO-STAGE architecture (Stage 1 + Stage 2) provides **automated detection of explicitly stated constitutional violations**. The boundary established in §A.3 — that naturalistic violations fall outside detection capability — is **by design**, not by limitation.

This boundary integrates with WINDI architecture through:

1. **PHO Gate** — Human adjudication for cases beyond automated detection
2. **I9 Enforcement** — Prohibition of autonomous action on constitutional matters
3. **I17 Proof** — Verification that a human (not bot) made the decision
4. **Ledger Seal** — Immutable record of human-approved actions

The result is an architecture that:
- Automates what can be automated (explicit detection)
- Escalates what requires judgment (ambiguous/naturalistic cases)
- Proves what was decided (forensic receipt)
- Complies with Article 14 (human oversight preserved)

---

## A.4.11 — Connection to Paper-001 Thesis

Paper-001 argues for **Proof-of-Existence (PoE)** as a foundation for AI governance.

Section A.4 demonstrates how PoE operates at the boundary:

| Moment | What is Proven | How |
|--------|----------------|-----|
| Detection | AI analysis occurred | Stage 1 + Stage 2 outputs logged |
| Escalation | Human was consulted | PHO gate record |
| Decision | Human chose | officer_did + timestamp |
| Seal | Decision is immutable | Ledger receipt + hash |
| Verification | Anyone can confirm | /verify-public/ endpoint |

The chain is:

```
PoE-Detection → PoE-Escalation → PoE-Decision → PoE-Seal → PoE-Verification
```

Each step is independently verifiable. The boundary from A.3 is where **PoE-Detection** hands off to **PoE-Escalation**.

---

*Document Status: DRAFT*
*Scope: §A.4.1–A.4.11 (Architectural Integration)*
*Parent: §A.3 (SEALED)*
*Next: Review for seal*

---

*Liga IA+H · Kempten, Bavaria · 2026-05-03*
*"The boundary is not where the system fails — it is where the human enters."*
