# Admissibility at Execution Time
## A Verifiable Governance Model for AI Systems Based on Cryptographic Receipts and Human Oversight

---

**Submitted for External Review**
**Date:** April 25, 2026
**Version:** 1.0 (Review Draft)
**Classification:** Pre-publication / Confidential Review

---

## Abstract

Current AI governance frameworks emphasize validation, auditability, and post-hoc accountability. However, they do not guarantee that system actions are admissible at the moment of execution. This gap allows systems to produce outcomes without provable authorization under the governing conditions active at runtime.

This paper introduces a governance model centered on admissibility at execution time, where every action must be justified by verifiable authority before it becomes real. The model is implemented through a set of non-overridable invariants, a Proof of Human Oversight (PHO) mechanism, and a cryptographic forensic ledger that records execution receipts as immutable evidence.

We present an empirical methodological hardening event triggered by external adversarial review, in which identified epistemic and procedural fissures were formally integrated into the system through deterministic updates. The transformation is captured and sealed as a verifiable receipt, establishing a reproducible chain of governance evolution.

The results demonstrate that governance can be operationalized as a runtime enforcement property rather than a retrospective assessment. This approach enables systems to evolve under adversarial pressure while preserving verifiability, offering a new foundation for trustworthy AI in high-stakes environments.

**Keywords:** AI governance, runtime enforcement, human oversight, cryptographic evidence, admissibility, EU AI Act

---

## 1. Introduction

The rapid deployment of AI systems in decision-critical environments has exposed a fundamental limitation in current governance approaches. Existing frameworks focus on whether systems are well-designed, tested, or auditable, but do not address a more immediate and decisive question:

> **Was the system allowed to act at the moment it acted?**

This distinction separates two fundamentally different concerns:

1. whether a system can generate valid outputs
2. whether it is authorized to execute those outputs under current conditions

Most governance architectures implicitly collapse these layers. Validation ensures that a system can behave correctly, while auditability ensures that its behavior can be reconstructed after the fact. Neither guarantees that an action was admissible at the exact moment of execution.

Recent discussions in AI governance have highlighted related tensions between decision ownership and system authority. As noted by Demarius J. Lawson, validation does not resolve who is accountable for outcomes. Similarly, John M. Willis emphasizes the need for runtime governance mechanisms that constrain system behavior at execution time. However, existing approaches remain largely descriptive or control-plane oriented, lacking a unified mechanism that ties authorization, execution, and evidence into a single verifiable structure.

This paper proposes a different approach: **admissibility as a first-class runtime property**.

In this model, an action is not considered valid because it can be explained or audited later. It is valid only if it can be proven, at the moment of execution, that:

1. the action is authorized under the governing rules
2. the authorization is non-overridable
3. the authorization is recorded as immutable evidence

To operationalize this, we introduce a system architecture based on:

- constitutional invariants that cannot be bypassed
- a Proof of Human Oversight (PHO) requirement for critical actions
- a cryptographic forensic ledger that records execution receipts

The central claim of this paper is that **governance must be resolved at execution time, not inferred afterward**.

To support this claim, we present an empirical case: a methodological hardening event triggered by external adversarial review. During this event, structural weaknesses in the system's epistemology and methodology were exposed and subsequently integrated into the framework through deterministic updates. The transformation was sealed as a cryptographic receipt, creating a verifiable record of governance evolution.

---

## 2. Conceptual Distinction: Validation, Ownership, and Admissibility

Contemporary AI governance frameworks rely on three conceptual anchors: validation, accountability, and control. While each addresses a relevant aspect of system behavior, they are frequently conflated in practice.

### 2.1 Validation: Capability Without Authority

Validation determines whether a system behaves as intended under predefined conditions. It is inherently **pre-execution** or **test-bound**. It establishes that a system *can* operate within acceptable parameters, but does not constrain whether it *should* act in a specific instance.

A system can therefore be fully validated and still produce an inadmissible action if runtime conditions invalidate its authority to act.

### 2.2 Ownership: Responsibility Without Constraint

Ownership addresses the attribution of consequences. It becomes relevant after an action has been executed. Ownership is therefore **post-execution**. It assigns responsibility but does not enforce constraints at the moment of decision.

### 2.3 Admissibility: Authority at Execution Time

Admissibility is defined here as:

> **The property that an action is authorized under the governing conditions at the exact moment of execution.**

Unlike validation and ownership, admissibility is:

- **runtime-bound** (evaluated at execution time)
- **state-dependent** (based on current conditions, not prior tests)
- **binary** (an action is either admissible or not)

### 2.4 Failure Mode in Existing Systems

Most deployed systems collapse validation, ownership, and admissibility into a single operational layer:

1. A system is validated and deployed
2. It generates an action under changing runtime conditions
3. The action executes without explicit admissibility verification
4. Ownership is assigned after the fact

The result is a system that can explain its behavior but cannot prove that it was authorized to act.

### 2.5 Requirement: Admissibility as a First-Class Property

To resolve this gap, admissibility must be elevated to a **first-class property of system design**:

1. Every execution must be preceded by an admissibility decision
2. This decision must be non-overridable under defined invariants
3. The decision must produce verifiable evidence at the moment of execution

---

## 3. The Governance Model

The governance model operationalizes admissibility as a runtime property by binding authorization, execution, and evidence into a single, non-separable process.

### 3.1 Architectural Overview

The system is structured as a layered execution pipeline:

```
USER → INTENT → COUNSEL → DOMAIN → LEDGER → VERIFY
```

Each stage refines a proposed action, but execution is not finalized until it is committed to the ledger. **An action becomes real only if it produces a valid receipt at commit time.**

### 3.2 Constitutional Invariants

At the core of the model is a set of constitutional invariants — system-level constraints that cannot be bypassed, overridden, or deferred.

| ID | Name | Function |
|----|------|----------|
| I6 | Conflict Exposure | The system must surface internal contradictions. Suppression is not permitted. |
| I9 | Prohibition of Autonomy Escalation | The system cannot elevate its own authority. Higher authority requires explicit human approval. |
| I11 | Permanence of Cryptographic Evidence | All execution-relevant events must produce immutable, hash-linked evidence. |
| I14 | Explicit Failure Principle | When conditions for valid execution are not met, the system must fail explicitly. |

### 3.3 Proof of Human Oversight (PHO)

For actions requiring human authority, the model introduces mandatory Proof of Human Oversight (PHO). An action requiring human approval must satisfy:

1. **Identity** — a valid human actor is identified
2. **Intent** — the action is explicitly approved
3. **Presence** — the approval occurs within the active execution context

PHO ensures that human authority is not inferred or assumed, but proven at the moment of decision.

### 3.4 Forensic Ledger as Execution Gate

The forensic ledger serves three simultaneous roles:

1. **commit layer** — finalizes execution
2. **evidence layer** — records immutable proof
3. **verification anchor** — enables independent validation

Each executed action produces a receipt including unique identifier, actor, action metadata, cryptographic hash, references to prior states, and governance attributes.

**An action that does not produce a valid receipt is considered non-existent from a system perspective.**

### 3.5 Admissibility Resolution at Commit Time

An action is admissible if and only if:

1. it satisfies all applicable invariants
2. required PHO conditions are fulfilled
3. it produces a valid, immutable receipt

There is no intermediate state in which an action executes without proof.

### 3.6 Non-Overridability

A critical property is that admissibility enforcement is non-overridable:

- Invariants cannot be disabled at runtime
- PHO cannot be bypassed for actions that require it
- Ledger commitment cannot be skipped or deferred

**System integrity is defined not by compliance with policies, but by inability to violate admissibility conditions.**

---

## 4. Empirical Case: Methodological Hardening Event

This section presents a verifiable methodological hardening event triggered by external adversarial review, anchored in a sealed cryptographic receipt enabling independent verification.

### 4.1 Context and Trigger

On April 25, 2026, the system underwent an external adversarial review conducted in a structured session. The review was explicitly critical and aimed at identifying epistemic and methodological weaknesses.

Focus areas included:
- classification consistency
- methodological circularity
- statistical validity
- reproducibility constraints

The review resulted in the identification of multiple structural fissures.

### 4.2 Identified Fissures

| Fissure | Description |
|---------|-------------|
| **Authorship Circularity (W8)** | Classification logic risked reinforcing its own assumptions without sufficient external grounding. |
| **Closed-Loop Governance (W9)** | Governance mechanisms were internally consistent but insufficiently open to external challenge. |
| **Irrecoverability Gap** | Absence of formal criterion for excluding irrecoverable cases weakened statistical integrity. |

### 4.3 Deterministic Integration of Corrections

All fissures were addressed through deterministic updates:

| Change | Description |
|--------|-------------|
| W8 | Explicit acknowledgment and structural mitigation of circular reasoning risks |
| W9 | Repositioning to incorporate external critique as valid input condition |
| E5 | Formal exclusion rule with 10% quantitative threshold |
| §4.4 | Statistical power recalculation (κ, PABAK, confidence intervals) |
| §4.6 | Transparent procedure for irrecoverability criterion |
| §5.4 | Vault reproducibility commitment |
| §6 | Lexicographic precedence for ambiguous outcomes |

Document versions updated:
- Eligibility Criteria: v1.2 → v1.3
- Classification Protocol: v1.1 → v1.2

### 4.4 Receipt as Verifiable Evidence

The transformation was sealed as a cryptographic receipt:

| Field | Value |
|-------|-------|
| Receipt ID | `PoE-METHODOLOGY-HARDENING-20260425` |
| Timestamp | April 25, 2026 (UTC) |
| Governance Level | HIGH |

The receipt establishes a verifiable chain linking predecessor and successor documents with corresponding SHA-256 hashes.

**The receipt is publicly accessible and independently verifiable.**

### 4.5 Admissibility Enforcement During the Event

| Invariant | Operation |
|-----------|-----------|
| I6 | Fissures explicitly surfaced and recorded |
| I14 | Limitations acknowledged and formalized |
| I9 | All modifications required explicit human approval |
| I11 | Transformation sealed as immutable proof |

**The system adapted only through admissible transformations, each requiring authorization and producing evidence.**

### 4.6 Properties of the Event

| Property | Description |
|----------|-------------|
| **Causality** | Trigger explicitly linked to resulting changes |
| **Determinism** | All updates formally specified and version-controlled |
| **Verifiability** | Entire transformation anchored in accessible receipt |
| **Non-Bypassability** | Changes required satisfying invariant constraints and PHO |
| **Reproducibility** | Explicit commitments to reconstructability |

---

## 5. Analysis

### 5.1 From Compliance to Admissibility Enforcement

Key distinction:
- **Compliance asks:** Did the system follow the rules?
- **Admissibility asks:** Was the system allowed to act at that moment?

This shifts governance from a descriptive layer to an operational gate.

### 5.2 Evidence as a First-Class Output

In the observed event:
- evidence is produced atomically with execution
- evidence is cryptographically bound to the action
- absence of evidence implies non-existence of execution

> **An action is only real if it is provable.**

### 5.3 Governance Under Adversarial Pressure

The system did not adapt heuristically. It adapted through structured, admissible transformations.

> **Systems can evolve under adversarial conditions without losing structural integrity, provided that evolution itself is governed by admissibility constraints.**

### 5.4 Determinism and Non-Bypassability

The empirical event confirms that:
- corrections could not be applied without satisfying invariants
- execution paths without admissibility proof do not exist

> **Rules that cannot be violated are more relevant than rules that can be audited.**

### 5.5 Coupling of Authorization, Execution, and Evidence

The model collapses authorization, execution, and evidence into a single operation:

> **authorization → execution → evidence are no longer separable processes**

### 5.6 Reproducibility as a Governance Property

The inclusion of versioned transitions, hash-linked documents, and vault-based reconstructability extends reproducibility from experimental outcomes to governance evolution itself.

### 5.7 Limitations

| Limitation | Description |
|------------|-------------|
| Infrastructure centralization | Verification depends on limited endpoints |
| Early-stage empirical base | Analysis based on single documented event |
| Operational dependency | Availability affects practical auditability |

### 5.8 Synthesis

The empirical event supports:

1. Admissibility can be enforced at execution time through deterministic constraints
2. Evidence can be made inseparable from execution
3. Systems can evolve under adversarial pressure without violating governance rules
4. Authorization, execution, and evidence can be unified into a single verifiable process

---

## 6. Implications and Conclusion

### 6.1 Implications for AI Governance Frameworks

The model suggests an additional requirement beyond current standards:

> **Systems must prove, at the moment of execution, that they are allowed to act.**

For regulatory contexts requiring human oversight (e.g., EU AI Act):
- human oversight cannot be treated as procedural requirement
- it must be implemented as verifiable condition of execution

### 6.2 Implications for System Design

| Requirement | Description |
|-------------|-------------|
| Execution gating | Actions contingent on runtime authorization |
| Non-overridable constraints | Invariants that cannot be bypassed |
| Atomic evidence generation | Cryptographic proof at completion |
| Deterministic failure modes | Explicit failure when conditions not met |

### 6.3 Implications for Scientific and Industrial Practice

Systems can provide publicly verifiable records of:
- what changed
- why it changed
- under which conditions change was authorized

Supporting independent verification and cross-institutional trust.

### 6.4 Future Work

| Direction | Description |
|-----------|-------------|
| Distributed verification | Reducing centralized dependency |
| Broader empirical validation | Multiple domains and events |
| Formal specification | Machine-verifiable definitions |
| Standards integration | Alignment with existing frameworks |

### 6.5 Conclusion

This paper introduced a governance model in which admissibility is enforced at execution time through invariants, human oversight, and cryptographic evidence.

The central claim:

> **An action is only valid if it can be proven, at the moment of execution, that it was authorized.**

The empirical event demonstrates that:

1. governance can operate as a runtime enforcement mechanism
2. systems can evolve under adversarial pressure without violating constraints
3. execution and evidence can be unified into a single verifiable process

This shifts governance from retrospective assessment to deterministic control of what is allowed to become real.

**In high-stakes environments, where consequences are immediate and irreversible, this distinction defines whether systems can be trusted not only to perform, but to act within provable bounds of authority.**

---

## Verification Appendix

The empirical case can be independently verified:

**Receipt ID:** `PoE-METHODOLOGY-HARDENING-20260425`

**Public Verification URL:**
https://windi-domain.com/verify-public/?id=PoE-METHODOLOGY-HARDENING-20260425

**Document Hash Chain:**

| Document | Version | SHA-256 |
|----------|---------|---------|
| Eligibility Criteria | v1.2 → v1.3 | `57a84cc0...` → `51acf3cd...` |
| Classification Protocol | v1.1 → v1.2 | `2c704e66...` → `e7755c03...` |

---

## Review Request

**Reviewer guidance:**

This draft is submitted for critical evaluation. Specific feedback requested on:

1. **Conceptual clarity** — Is the distinction between validation, ownership, and admissibility sufficiently clear and useful?

2. **Empirical validity** — Does the documented event constitute sufficient evidence for the claims made?

3. **Architectural soundness** — Are there gaps in the governance model as described?

4. **Practical applicability** — How might this model apply to other AI governance contexts?

5. **Limitations** — Are there unstated limitations or risks in the approach?

**Contact:** [To be provided]

**Confidentiality:** This draft is shared for review purposes only. Please do not circulate without permission.

---

*Pre-publication Draft · April 2026*
