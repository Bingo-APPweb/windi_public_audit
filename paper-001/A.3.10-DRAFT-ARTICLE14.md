# A.3.10 — Proposed Mapping to Article 14 of the EU AI Act

**Status:** DRAFT — Not sealed. Pending legal review.
**Parent Document:** A.3-EMPIRICAL-CONSTITUTIONAL.md
**Created:** 2026-05-02

---

> **IMPORTANT:** This section is maintained separately from the sealed A.3 Core (§A.3.1–A.3.9) because it contains regulatory interpretation that requires legal validation before permanent sealing. The empirical and constitutional content in §A.3.1–A.3.9 is independently verifiable; this section is a proposal.

---

The empirical findings of §A.3.3–§A.3.7 and the constitutional reading of §A.3.9 converge on a regulatory question that this subsection addresses directly. We propose that the architecture under examination — LEXICON, Forensic Ledger, Liga IA+H, Three Dragons Protocol — constitutes a candidate implementation of the human oversight requirements set out in Article 14 of Regulation (EU) 2024/1689 (the "AI Act"). The mapping is presented as a **technical proposal for legal review**, not as a certification of conformity. Formal validation by qualified counsel in EU AI Act compliance is required before any operational reliance on this mapping.

**Article 14(1) — General requirement of human oversight.**
The Article requires that high-risk AI systems be designed and developed to be effectively overseen by natural persons during the period in which they are in use. The Liga IA+H instantiates this requirement by constitutional design: the human node is not an external supervisor superimposed on the system but a structural component without which the system does not produce admissible output. Receipt Symmetry (§A.3.9) is the property that makes this oversight verifiable after the fact.

**Article 14(4)(a) — Properly understanding the relevant capacities and limitations.**
The Article requires that overseers be enabled to understand what the system can and cannot do. §A.3.4 provides the first empirical characterisation of LEXICON capacities (cluster signature in the 65–85 band, saturation at 100) and limitations (zero response on jurisdictional ambiguity, polarity sensitivity that does not equate to constitutional sensitivity). §A.3.7 enumerates three explicit limitations of the current capture. This documentation pattern is proposed as the WINDI standard for every component in the constellation.

**Article 14(4)(b) — Remaining aware of automation bias.**
The Article requires that overseers be enabled to remain aware of the tendency to over-rely on automated output. The LEXICON action ladder (§A.3.6) is constructed to resist automation bias in two ways: the `silent` action requires no human attention only below an explicit threshold, and the `interrupt` action mandates human adjudication regardless of operator preference. Case 5 is the canonical instance — the system's silence on a legally material question is the architecture's way of refusing to absorb a decision that requires human judgment.

**Article 14(4)(c) — Correctly interpreting the system's output.**
The Article requires that overseers be enabled to correctly interpret what the system produces. Every LEXICON output carries four interpretable fields (`drift_score`, `drift_type`, `confidence`, `lexicon_action`) and a forensic `request_hash` that anchors the output to a specific moment of inference. Interpretation is therefore not opaque; it is bounded by a documented schema and verifiable against the Ledger.

**Article 14(4)(d) — Deciding not to use the system or otherwise overriding its output.**
The Article requires that overseers be enabled to decline or override system output. The Three Dragons Protocol (§A.3.9) places the Human Dragon as the sole authorising channel between the artificial nodes. Override is not an exception path; it is the default control flow. No artificial node deploys, seals, or publishes without human authorisation traversing the chain.

**Article 14(4)(e) — Intervening or interrupting through a "stop" button or similar procedure.**
The Article requires that overseers be enabled to halt the system safely. The `interrupt` action in the LEXICON ladder, the sealed nature of the Forensic Ledger, and the segregation of inference (Server B) from orchestration (Server A) are infrastructural realisations of this requirement. The system can be halted at the inference layer without compromising the integrity of records already sealed.

---

## Reservation

The mapping above is a technical proposal authored by the system designers. It identifies how each clause of Article 14 is intended to be addressed by specific architectural features. It does not constitute legal advice, does not certify conformity, and does not substitute for the conformity assessment procedures that the AI Act prescribes for high-risk systems. Operators considering the WINDI architecture as a basis for AI Act compliance must obtain independent legal review. The authors invite such review and commit to publishing material clarifications that arise from it.

---

## Why this matters for the paper as a whole

This subsection completes the argumentative arc of A.3. The empirical register established what the LEXICON does; the constitutional register established why the architecture does it that way; the regulatory register now establishes what the architecture answers in the legal frame the operators face. The three registers are not redundant. They are three independent lines of evidence that the same system is empirically observable, constitutionally coherent, and regulatorily addressable. We submit that a system that is observable but not coherent, or coherent but not addressable, would not meet the standard the AI Act sets. The proposal is that this one does, subject to the reservation above.

---

## Review Checklist (for legal counsel)

- [ ] Verify Article 14 clause citations against official EU AI Act text
- [ ] Assess whether "Liga IA+H" framing meets "natural person" requirement
- [ ] Review Case 5 interpretation for automation bias defense
- [ ] Confirm Three Dragons Protocol satisfies override requirements
- [ ] Evaluate if Forensic Ledger qualifies as "stop" mechanism under 14(4)(e)
- [ ] Advise on any modifications needed before sealing

---

*This document will be integrated into A.3 and sealed only after legal review.*
