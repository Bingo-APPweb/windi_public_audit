# Bridging the Proof Gap in AI Governance: A Framework for Verifiable Human Oversight

**Jober Mögele Correa**
WINDI Publishing House
Kempten, Bavaria, Germany

---

## Abstract

The European Union's AI Act mandates human oversight for high-risk artificial intelligence systems, yet provides no mechanism for independently verifying that such oversight has occurred. This creates what we term the *Proof Gap*: a structural absence of verifiable evidence linking human decisions to system behavior. Current approaches rely on internal logs and self-reported compliance, neither of which can be independently validated.

This paper introduces *Proof of Human Oversight* (PHO), a formal primitive that captures the moment when human approval binds to system state. We present WINDI, a verification infrastructure implementing PHO through four architectural layers: cache (performance), temporal (consistency), proof (immutability), and policy (governance). The policy layer introduces *governed admissibility*, ensuring that not all provable states become evidence—only those meeting institutional criteria.

We evaluate WINDI under load, demonstrating 100% policy enforcement, zero temporal inconsistencies, and sustained throughput of approximately 33 operations per second. The system has been operational since March 2026.

This work contributes: (1) a formal definition of the Proof Gap, (2) the PHO primitive, (3) a four-layer verification architecture, and (4) empirical validation of governance-aware caching. We argue that if AI systems are to be meaningfully regulated, their behavior must be independently verifiable.

**Keywords:** AI Governance, Human Oversight, EU AI Act, Verification Infrastructure, Proof of Human Oversight, Policy Engine

---

## 1. Introduction

Artificial intelligence systems are increasingly deployed in domains subject to regulatory oversight: healthcare, finance, legal services, and public administration. The European Union's Artificial Intelligence Act (EU AI Act), entering into force in 2024, establishes requirements for high-risk AI systems, including mandatory human oversight as specified in Article 14.

However, the regulation presents a structural limitation: it mandates human oversight without defining how such oversight is proven. Compliance today is *declared*—organizations assert that oversight mechanisms exist—but it cannot be *independently verified*. Logs can be altered. Internal audits lack external validity. And the moment of human decision leaves no persistent, verifiable evidence.

This absence creates what we call the **Proof Gap**: a systematic inability to verify, after the fact and by independent parties, that a human decision authorized a particular system behavior.

The implications are significant. Without verifiable oversight, regulation remains symbolic. Accountability structures depend on trust rather than evidence. And the distinction between compliant and non-compliant systems becomes unenforceable.

This paper addresses the Proof Gap by introducing **Proof of Human Oversight (PHO)**, a verification primitive that captures human approval at the moment of decision binding. We present **WINDI**, an infrastructure implementing PHO through a layered architecture that separates performance, consistency, immutability, and governance concerns.

Critically, we introduce the concept of **governed admissibility**: the principle that not everything that can be proven should be. WINDI's policy layer controls which states may become evidence, enforcing institutional criteria at runtime.

The contributions of this paper are:

1. A formal definition of the Proof Gap in AI governance
2. The Proof of Human Oversight (PHO) primitive
3. A four-layer verification architecture (cache, temporal, proof, policy)
4. The concept of governed admissibility
5. Empirical evaluation under production conditions

The remainder of this paper is organized as follows. Section 2 formalizes the Proof Gap. Section 3 introduces PHO. Section 4 describes the WINDI architecture. Section 5 details the policy engine. Section 6 presents implementation. Section 7 reports evaluation results. Section 8 discusses implications. Section 9 acknowledges limitations. Section 10 concludes.

---

## 2. The Proof Gap

### 2.1 Definition

We define the Proof Gap as:

> **The Proof Gap** is the absence of an independent mechanism to verify that a human decision authorized a specific state binding in an AI system.

This gap exists at the intersection of three properties that current systems fail to provide simultaneously:

- **Independence**: Verification must be possible without trusting the originating system
- **Bindingness**: The proof must link to a specific state transition, not merely to a general approval
- **Persistence**: The evidence must survive beyond the operational context

### 2.2 Why Logs Are Insufficient

Internal logging systems, while useful for debugging and monitoring, cannot bridge the Proof Gap for three reasons:

1. **Mutability**: Logs stored within the same system that generated them can be altered, deleted, or selectively presented
2. **Interpretability**: Log entries require interpretation; their meaning depends on context controlled by the system owner
3. **Trust dependency**: Validating logs requires trusting the entity that produced them

### 2.3 Why Internal Audits Are Insufficient

Internal audits and compliance certifications face similar limitations:

1. **Temporal distance**: Audits occur after the fact, sampling behavior rather than capturing every decision
2. **Access constraints**: Auditors see what organizations choose to present
3. **Attestation vs. verification**: Audits produce attestations ("we believe X is compliant"), not verifiable proofs ("here is evidence that X occurred")

### 2.4 The Regulatory Consequence

Without mechanisms to bridge the Proof Gap, AI regulation faces a fundamental enforceability problem. Article 14 of the EU AI Act requires human oversight, but compliance reduces to organizational assertion. Regulators must trust that oversight occurred; they cannot independently verify it.

This creates asymmetric accountability: organizations bear the burden of compliance, but regulators lack the tools to confirm it.

---

## 3. Proof of Human Oversight (PHO)

### 3.1 Definition

We introduce Proof of Human Oversight (PHO) as a verification primitive:

> **Proof of Human Oversight (PHO)** is a verifiable record demonstrating that a human decision occurred prior to, and authorized, a specific state binding.

Formally, a PHO instance consists of:

- **Decision identifier**: A unique reference to the human decision event
- **State hash**: A cryptographic commitment to the state being authorized
- **Actor identity**: A decentralized identifier (DID) linking to the human decision-maker
- **Temporal anchor**: A timestamp verifiably external to the originating system
- **Verification endpoint**: A publicly accessible mechanism for independent validation

### 3.2 Properties

PHO provides the following properties:

1. **Non-repudiation**: Once recorded, the decision cannot be denied by the authorizing party
2. **Tamper-evidence**: Any modification to the authorized state invalidates the proof
3. **Independent verifiability**: Third parties can validate the proof without system access
4. **Temporal ordering**: The proof establishes that authorization preceded binding

### 3.3 Relationship to Article 14

PHO operationalizes EU AI Act Article 14 by transforming the requirement for human oversight from a procedural mandate into a verifiable artifact. Rather than asserting that oversight mechanisms exist, systems implementing PHO produce evidence that oversight occurred.

| Article 14 Requirement | PHO Implementation |
|------------------------|-------------------|
| Human oversight capability | Decision capture interface |
| Ability to intervene | State binding gate |
| Understanding of system | Contextual metadata |
| Ability to override | Explicit approval record |

---

## 4. WINDI Architecture

### 4.1 Overview

WINDI implements PHO through a four-layer architecture:

```
┌─────────────────────────────────────┐
│         POLICY LAYER                │  ← Governance decisions
├─────────────────────────────────────┤
│         PROOF LAYER                 │  ← Immutable records
├─────────────────────────────────────┤
│         TEMPORAL LAYER              │  ← Consistency guarantees
├─────────────────────────────────────┤
│         CACHE LAYER                 │  ← Performance optimization
└─────────────────────────────────────┘
```

Each layer addresses a distinct concern while maintaining clear interfaces with adjacent layers.

### 4.2 Cache Layer

The cache layer (W-CACHE) provides performance optimization through a tiered storage model:

- **L1 (Ephemeral)**: Short-lived, local caching (TTL: 5 minutes)
- **L2 (Deterministic)**: Reproducible computations (TTL: 1 hour)
- **L3 (Proven)**: Cryptographically verified entries (TTL: 24 hours)
- **L4 (Policy)**: Institutionally governed entries (configurable)

Entries progress through tiers based on verification status and policy decisions.

### 4.3 Temporal Layer

The temporal layer ensures consistency across distributed operations through:

- **Timeline identifiers**: Unique references to causal chains
- **State versions**: Monotonically increasing sequence numbers
- **State hashes**: Cryptographic commitments to state content
- **Parent references**: Links establishing causal ordering

This layer prevents temporal inconsistencies such as out-of-order approvals or orphaned decisions.

### 4.4 Proof Layer

The proof layer provides immutability through:

- **SHA-256 hashing**: Content integrity verification
- **External ledger anchoring**: Independence from originating system
- **Public verification endpoints**: Third-party validation capability
- **Receipt generation**: Portable proof artifacts

The proof layer connects to a Forensic Ledger service that maintains an append-only record of all verification events.

### 4.5 Layer Interactions

Information flows upward through the layers:

1. Operations enter at the cache layer for performance
2. Temporal metadata ensures consistency
3. Proof layer creates immutable records
4. Policy layer governs which records become evidence

Critically, promotion between layers is not automatic. The policy layer controls admissibility.

---

## 5. Policy Engine: Governed Admissibility

### 5.1 The Principle

A key insight driving WINDI's design is that **not everything that can be proven should be**. Indiscriminate proof generation creates noise, obscures significant decisions, and may conflict with privacy requirements.

We introduce **governed admissibility**: the principle that promotion to proof status must satisfy institutional criteria, not merely technical capability.

### 5.2 Implementation

The policy engine evaluates promotion requests against namespace-specific rules:

```
evaluate_policy(entry, context) → {allow, mode, reason}
```

Where:
- **allow**: Boolean indicating whether promotion is permitted
- **mode**: REFERENTIAL (pointer only), ANCHORED (ledger-bound), or DENY
- **reason**: Human-readable explanation for audit purposes

### 5.3 Policy Categories

WINDI implements the following default policies:

| Namespace | Auto-Allow | Mode | Rationale |
|-----------|------------|------|-----------|
| verify.* | Yes | REFERENTIAL | Verification receipts are inherently safe |
| travel.* | Yes | REFERENTIAL | User-owned content |
| enterprise.* | No | ANCHORED | Requires human_approved flag |
| legal.* | No | ANCHORED | Requires approval + ledger anchor |
| default | No | DENY | Unknown namespaces rejected (I14) |

### 5.4 Human Approval Gate

For namespaces requiring human oversight, the policy engine enforces an approval gate:

```
if namespace.requires_human_approval:
    if not context.human_approved:
        return DENY("HUMAN_APPROVAL_REQUIRED")
```

This implements what we term **I9 (Human Approval Gate)**: the invariant that certain state transitions must not occur without explicit human authorization.

### 5.5 Default Denial

The policy engine implements **I14 (Explicit Failure Principle)**: when conditions are not met, the system denies promotion rather than assuming validity. This prevents silent failures and ensures that missing approvals surface as explicit errors.

---

## 6. Implementation

### 6.1 Technology Stack

WINDI is implemented using:

- **FastAPI**: Asynchronous Python web framework
- **SQLAlchemy**: Database abstraction
- **SQLite**: Persistent storage (production uses PostgreSQL)
- **Server-Sent Events (SSE)**: Real-time event streaming

### 6.2 Service Architecture

The implementation consists of interconnected services:

- **W-CACHE-001** (port 8160): Verifiable cache layer
- **Forensic Ledger** (port 8101): Immutable record storage
- **NOIR Dashboard**: Real-time observability interface

### 6.3 API Surface

The cache service exposes:

- `POST /api/cache/v1/entries`: Create cache entry
- `POST /api/cache/v1/promote`: Promote to proven tier
- `GET /api/cache/v1/metrics`: Retrieve system metrics
- `GET /api/cache/v1/events`: Stream events via SSE
- `GET /api/cache/v1/policy`: View policy registry

### 6.4 Event Architecture

All significant operations emit events captured by the observability layer:

- **PROMOTION_DENIED**: Policy rejected promotion
- **PROMOTE_TO_PROVEN**: Entry achieved L3 status
- **MISS**: Cache lookup failed
- **HIT**: Cache lookup succeeded

Events stream in real-time to the NOIR dashboard, enabling live monitoring of governance decisions.

---

## 7. Evaluation

### 7.1 Test Methodology

We evaluated WINDI under controlled load conditions designed to stress both performance and governance enforcement:

1. **Phase 1**: 50 entries in auto-allow namespace (verify.*)
2. **Phase 2**: 30 entries in governed namespace (enterprise.*)
3. **Phase 3**: 100 concurrent write operations (burst test)

### 7.2 Results

| Metric | Result |
|--------|--------|
| Total entries created | 199 |
| L2 (awaiting promotion) | 136 |
| L3 (proven) | 63 |
| Promotions succeeded | 63 |
| Promotions denied | 31 |
| Temporal mismatches | 0 |
| Integrity violations | 0 |
| Policy enforcement rate | 100% |
| Sustained throughput | ~33 ops/sec |

### 7.3 Key Findings

1. **Policy enforcement is complete**: All 30 enterprise entries were denied promotion due to missing human approval, as expected
2. **Temporal consistency is maintained**: Zero mismatches across all operations
3. **Performance is adequate**: Sustained throughput exceeds typical governance workflow requirements
4. **Governance overhead is minimal**: Policy evaluation adds negligible latency

### 7.4 Production Status

WINDI has been operational since March 2026, processing governance events across multiple domains including legal document workflows, travel documentation, and enterprise decision tracking.

---

## 8. Discussion

### 8.1 From Logs to Proofs

WINDI represents a paradigm shift from logging to proving. Traditional systems record events for later analysis; WINDI produces verifiable artifacts at the moment of decision. This distinction has profound implications for accountability:

- Logs require interpretation; proofs are self-validating
- Logs depend on trust; proofs enable verification
- Logs decay in relevance; proofs maintain validity

### 8.2 Regulatory Implications

If adopted, PHO-style verification could transform AI governance:

1. **Enforcement becomes possible**: Regulators gain tools to verify compliance
2. **Accountability becomes symmetric**: Both organizations and regulators can validate claims
3. **Standards become meaningful**: Requirements can be tested, not merely asserted

### 8.3 Governed Admissibility as Principle

The concept of governed admissibility extends beyond AI governance. Any domain where not all records should become evidence—healthcare, legal proceedings, financial audit—could benefit from explicit policies controlling proof generation.

### 8.4 The Role of Independence

WINDI's architecture emphasizes independence: external ledgers, public endpoints, cryptographic commitments. This independence is not incidental; it is essential. Verification that depends on the verified system is not verification.

---

## 9. Limitations

### 9.1 Adoption Dependency

PHO provides value only when adopted. A single organization implementing WINDI gains internal benefits, but the broader governance ecosystem requires widespread adoption to achieve independent verification at scale.

### 9.2 Integration Overhead

Implementing PHO requires integration with existing workflows. Systems must be modified to capture decision points and submit them for verification. This integration effort may be significant for legacy systems.

### 9.3 Policy Complexity

As policy rules multiply, the governance layer may become complex to maintain. Future work should address policy composition, conflict resolution, and dynamic policy updates.

### 9.4 Ledger Scalability

External ledger anchoring introduces scalability constraints. While current throughput is adequate for governance workflows, high-volume applications may require batching or hierarchical proof structures.

### 9.5 Human Factor

PHO verifies that a human decision occurred, not that the decision was correct, informed, or ethical. Verification infrastructure addresses procedural compliance, not substantive quality.

---

## 10. Conclusion

The EU AI Act mandates human oversight for high-risk AI systems, but provides no mechanism for verifying that oversight has occurred. This Proof Gap undermines regulatory enforceability and reduces compliance to organizational assertion.

We have introduced Proof of Human Oversight (PHO), a verification primitive capturing human approval at the moment of state binding. We have presented WINDI, an infrastructure implementing PHO through four architectural layers addressing performance, consistency, immutability, and governance.

Critically, we have argued that verification must be governed: not everything that can be proven should be. WINDI's policy engine implements governed admissibility, ensuring that proof generation serves institutional purposes rather than merely technical capability.

Our evaluation demonstrates that governance-aware verification is practical: WINDI maintains 100% policy enforcement with zero temporal inconsistencies under production load.

We conclude with a simple observation:

> **If AI systems are regulated, their behavior must be independently verifiable.**

WINDI provides infrastructure to make this possible.

---

## References

[1] European Parliament and Council. (2024). Regulation (EU) 2024/1689 laying down harmonised rules on artificial intelligence (AI Act).

[2] Floridi, L., et al. (2018). AI4People—An Ethical Framework for a Good AI Society. Minds and Machines, 28(4), 689-707.

[3] Selbst, A. D., et al. (2019). Fairness and Abstraction in Sociotechnical Systems. FAT* '19.

[4] Wachter, S., Mittelstadt, B., & Russell, C. (2017). Counterfactual Explanations without Opening the Black Box. Harvard Journal of Law & Technology, 31(2).

[5] Raji, I. D., et al. (2020). Closing the AI Accountability Gap: Defining an End-to-End Framework for Internal Algorithmic Auditing. FAT* '20.

[6] Kroll, J. A., et al. (2017). Accountable Algorithms. University of Pennsylvania Law Review, 165(3).

---

## Appendix A: Invariants

WINDI enforces the following constitutional invariants:

| ID | Name | Description |
|----|------|-------------|
| I1 | Human Sovereignty | Human touch activates; no spontaneous autonomy |
| I9 | Human Approval Gate | human_approved=true required before seal |
| I11 | Cryptographic Permanence | Ledger receipts are immutable |
| I14 | Explicit Failure | Missing data causes explicit error, not silent default |

---

## Appendix B: System Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/cache/v1/entries | POST | Create cache entry |
| /api/cache/v1/promote | POST | Promote to proven tier |
| /api/cache/v1/metrics | GET | System metrics |
| /api/cache/v1/events | GET | Event stream (SSE) |
| /api/cache/v1/policy | GET | Policy registry |
| /health | GET | Service health |

---

*Paper version 1.0 — April 2026*

*Correspondence: WINDI Publishing House, Kempten, Bavaria*
