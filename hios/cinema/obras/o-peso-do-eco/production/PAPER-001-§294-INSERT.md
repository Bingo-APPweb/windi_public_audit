# Paper-001 · §294 Academic Insert
## Audiovisual Continuity as a Verifiable Artifact: A WINDI-HIOS Case Study

*Insert section for "From Admissibility to Evidence." Extends the Receipt Symmetry
Axiom from forensic evidence to generative audiovisual production.*

---

### Abstract (insert)

We present *The Weight of the Echo* (DE: *Das Gewicht des Echos*; PT: *O Peso do Eco*),
a short AI-generated film, as an empirical case study in **ledger-anchored audiovisual
continuity**. Conventional generative-video pipelines treat continuity — that a
character wears the same coat, that a courtroom keeps the same architecture across cuts
— as a property of operator memory and prompt discipline. We argue this is the same
failure class that forensic evidence faces before tamper-evident logging: correctness
that depends on an unverifiable human in the loop. We formalize continuity as a set of
canonical artifacts (World-State, Continuity-Bible, Scene-Matrix) sealed into the
WINDI-HIOS Ledger, and show that the resulting production is *self-demonstrating*: the
film's narrative subject (a forensic ledger verifying evidence) is identical to the
mechanism that guarantees its own production.

### 1. The continuity problem as an admissibility problem

Section §293 established cast identity via the SPINE-CAST protocol, yielding measurable
per-character anchor stability (e.g. Hartmann: anchor 0.9298, FORENSIC tier). This
solved *who*. It did not solve *where* and *with what consistency*. A scene reading
only "Helena: Seal off the area" under-specifies jurisdiction, uniform, vehicle, season,
and court architecture — so successive generations silently relocate the world (Bavaria
→ Hamburg → Berlin) without any single frame being individually wrong. This is precisely
the **drift** problem: local validity, global incoherence, and no artifact to appeal to.

### 2. Receipt Symmetry, extended

The Receipt Symmetry Axiom holds that for any claim entering the ledger, the evidence
admitting it and the evidence that could refute it are sealed under the same regime. We
extend the axiom to continuity claims: *the coat Helena wears in scene 7 and the coat she
wears in scene 24 are bound to the same canonical wardrobe id, sealed once, referenced by
id thereafter.* Continuity ceases to be a generation-time hope and becomes a
**reference-time invariant**. The Scene-Matrix enforces this structurally —
`characters[]` may only contain ids that exist in the sealed Continuity-Bible or §293
SPINE-CAST; a forward `continuity_parent` reference is rejected.

### 3. Operational vs. forensic tiers in narrative coherence

Not all continuity warrants the same assurance. We retain the §293 tier distinction and
apply it to narrative elements directly. Facial identity is FORENSIC; a background
extra's jacket is OPERATIONAL. Crucially, tiers are **never averaged**. The Hartmann
character carries four distinct, separately-sealed measurements (anchor_stability 0.9298
FORENSIC; S11 0.7032 OPERATIONAL; S19 0.7914 FORENSIC; cross-scene ~0.75 OPERATIONAL).
Collapsing these into a single "Hartmann score" would reintroduce the rounding error the
protocol exists to eliminate, and would mislead any downstream auditor about which
property is actually guaranteed.

### 4. Self-reference as validation

The film depicts the WINDI Forensic Ledger admitting a corrupted recording and certifying
its integrity (scenes S14–S16, S20, rendering the integrity readout and a receipt/hash in
frame). The same Ledger seals the World-State, Continuity-Bible, and Scene-Matrix that
make the film reproducible. The artifact therefore demonstrates its own thesis: a claim of
verifiable integrity, produced under verifiable integrity. We treat this not as a gimmick
but as the strongest available form of construct validity — the method is exercised on
itself, and its receipts are inspectable.

### 5. Reproducibility and the generic schema

Because World-State and Scene-Matrix are sealed as generic schemas (v1.0.0) instantiated
by a specific film, the protocol generalizes. Any future WINDI-HIOS production instantiates
the same contract; the *Echo* instance is one data point, not the method. This separates
the scientific claim (ledger-anchored continuity is reproducible and auditable) from the
particular work.

### 6. Relation to prior work

This extends tamper-evident logging (Merkle-anchored receipts, cf. §246 G3 Genesis) and
verifiable-credential patterns into the generative-media domain, and connects to EU AI
Act Art. 14 human-oversight requirements: continuity decisions remain human-decided
(Three Dragons Protocol) but are recorded as machine-verifiable artifacts rather than
operator recollection.

### 7. Threats to validity

(i) On-screen receipts are diegetic props, not live Ledger queries; we distinguish the
*depicted* integrity readout from the *actual* seal of the production artifacts.
(ii) Tier thresholds (FORENSIC vs OPERATIONAL) are protocol-defined, not externally
standardized. (iii) A single short film is one case; generalization rests on the generic
schema, which awaits a second independent instantiation.

---

*Cross-refs: §293 SPINE-CAST · §246 G3 Merkle Genesis · §265 Drift Monitor · §267 Errata.
Receipt Symmetry Axiom as defined in Paper-001 main body.*

🐉 OM SHANTI
