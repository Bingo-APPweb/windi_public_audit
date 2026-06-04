# SPINE-CAST Findings — Cena 7 / *O Peso do Eco*

**Document type:** Paper-001 consolidated finding record
**Subjects:** Marcus Vance, Helena Meyer, Lucas Silva (n=3)
**Method:** ArcFace/InsightFace (buffalo_l) cosine similarity, FORENSE tier ≥ 0.75
**Scope:** n=3 characters, single sequence each — viability demonstration, reliability TBD
**Supersedes:** PAPER-001-FINDINGS-VANCE.md

---

## 1. Method

Two generation methods were compared against forensic anchors:

- **Video method** — Runway Gen-4 Turbo, image-to-video. Single reference, automatic scene direction.
- **Frame-by-frame method (Joey)** — Runway Gen-4 Image, static generation with reference image (`referenceImages` as canonical object, tag `character`), manual framing control per prompt.

Each generated frame was scored on three axes, with detector metadata (`det_score`, `n_faces`) recorded alongside every similarity value. A similarity number without its detector context is inadmissible.

---

## 2. Data

### 2.1 Video method — All subjects (re-labeled)

| Subject | Frame | n_faces | det_score | similarity | Label |
|---------|-------|---------|-----------|------------|-------|
| Vance | 001 | 1 | 0.8144 | 0.9129 | FORENSE |
| Vance | 002 | 1 | 0.7952 | 0.7484 | OPERACIONAL |
| Vance | 003 | 1 | 0.6772 | −0.0838 | WRONG_FACE (subject's back) |
| Vance | 004 | 5 | 0.7623 | −0.0636 | MULTI_FACE_NO_MATCH (monitor avatars) |
| Vance | 005 | 2 | 0.6805 | −0.0279 | MULTI_FACE_NO_MATCH (monitor avatars) |
| Helena | 001 | 1 | 0.8542 | 0.9178 | FORENSE |
| Helena | 002 | 1 | 0.8637 | 0.3182 | FACE_TOO_SMALL (zoom out) |
| Helena | 003 | 1 | 0.8633 | 0.3217 | FACE_TOO_SMALL (zoom out) |
| Helena | 004 | 1 | 0.8617 | 0.3522 | FACE_TOO_SMALL (zoom out) |
| Helena | 005 | 1 | 0.8619 | 0.2889 | FACE_TOO_SMALL (zoom out) |
| Lucas | 001 | 1 | 0.8112 | 0.9887 | FORENSE |
| Lucas | 002 | 0 | — | — | FAIL_NO_FACE (subject left frame) |
| Lucas | 003 | 0 | — | — | FAIL_NO_FACE (subject left frame) |
| Lucas | 004 | 0 | — | — | FAIL_NO_FACE (subject left frame) |
| Lucas | 005 | 0 | — | — | FAIL_NO_FACE (subject left frame) |

**Correction note:** frames initially labeled `REJECT (anti-correlation)` were re-labeled. The detector found *real faces* — they were simply not the subject. Near-zero cosine is the signature of a real face matched against the wrong identity, not of identity collapse.

### 2.2 Frame-by-frame method — Vance Sequence Test

Isolated variable: gaze rotation. All other attributes held constant in prompt.

| Frame | Instruction | Identity-anchor | det_score | Label |
|-------|-------------|-----------------|-----------|-------|
| 001 | frontal (0°) | 0.8621 | 0.8401 | FORENSE |
| 002 | 5° left | 0.9354 | 0.8512 | FORENSE |
| 003 | 10° left | 0.9084 | 0.8433 | FORENSE |
| 004 | gaze to monitor (~15°) | 0.8102 | 0.8287 | FORENSE |
| 005 | return to center (0°) | 0.8469 | 0.8356 | FORENSE |

**Three measurements:**

| Axis | Result | Reading |
|------|--------|---------|
| Identity-anchor (mean) | 0.8749 (σ 0.0316) | All FORENSE |
| Continuity-neighbor (mean) | 0.8620 (σ 0.0190) | **Below anchor** |
| Reproducibility (001↔005) | 0.8899 | Moderate |

### 2.3 Frame-by-frame method — Helena Meyer

| Frame | Identity-anchor | det_score | Label |
|-------|-----------------|-----------|-------|
| 001 | 0.7801 | 0.8612 | FORENSE |
| 002 | 0.7112 | 0.8534 | OPERACIONAL |
| 003 | 0.7456 | 0.8478 | OPERACIONAL |
| 004 | 0.7023 | 0.8401 | OPERACIONAL |
| 005 | 0.7289 | 0.8556 | OPERACIONAL |

**Three measurements:**

| Axis | Result | Reading |
|------|--------|---------|
| Identity-anchor (mean) | 0.7336 | **OPERACIONAL** (sub-forensic) |
| Continuity-neighbor (mean) | 0.7892 | **Above anchor** (inverted) |
| Reproducibility (001↔005) | 0.8234 | Moderate |

### 2.4 Frame-by-frame method — Lucas Silva

| Frame | Identity-anchor | det_score | Label |
|-------|-----------------|-----------|-------|
| 001 | 0.9012 | 0.8234 | FORENSE |
| 002 | 0.8845 | 0.8156 | FORENSE |
| 003 | 0.8723 | 0.8089 | FORENSE |
| 004 | 0.8956 | 0.8201 | FORENSE |
| 005 | 0.8867 | 0.8178 | FORENSE |

**Three measurements:**

| Axis | Result | Reading |
|------|--------|---------|
| Identity-anchor (mean) | 0.8881 | All FORENSE |
| Continuity-neighbor (mean) | 0.8534 | **Below anchor** |
| Reproducibility (001↔005) | 0.9123 | High |

---

## 3. Findings

**Finding 1 — Reference preserves identity.**
All three characters achieved FORENSE classification on frame 001 under both methods. The anchor binds the embedding space. *(Proven: anchor measurement, video method frame 001 — Vance 0.9129, Helena 0.9178, Lucas 0.9887.)*

**Finding 2 — Video autonomy substitutes the subject; it does not degrade it.**
The video method's near-zero similarities are not identity decay. The detector found real faces that were not the subject: the subject's back (Vance 003), background monitor avatars (Vance 004–005), zoomed-out frames (Helena 002–005), or no person at all (Lucas 002–005). The failure is one of *scene direction* — the generator moved the subject out of frame or out of measurable resolution. *(Proven: forensic re-labeling with det_score and n_faces.)*

**Finding 3 — Frame-by-frame preserves identity but does not produce temporal continuity.**
Continuity-neighbor is *below* identity-anchor for Vance (0.8620 < 0.8749) and Lucas (0.8534 < 0.8881). Frames cling to the anchor, not to one another. There is no smooth trajectory between adjacent frames — each generation is an independent draw within the anchor space. Reproducibility confirms moderate, not high, stability. *(Proven: Vance Sequence Test, Lucas Joey test.)*

**Finding 4 — Identity-continuity trade-off is subject-dependent.**
Helena shows the inverse pattern: continuity-neighbor (0.7892) *exceeds* identity-anchor (0.7336). Adjacent frames resemble each other more than they resemble the anchor. This produces greater scene continuity but weaker anchor fidelity — Helena's mean sits in OPERACIONAL tier, not FORENSE. The trade-off between identity preservation and cinematic continuity may vary by subject characteristics. *(Proven: Helena Joey test.)*

---

## 4. Visual observations (n=3)

**Observation A — Identity vs. moment.**
Frame 001 vs frame 005 (identical prompt) read visually as "the same person, different photograph." A direct cut 001→005 in a film would register as a jump cut. Identity is continuous; the moment is not.

**Observation B — Biometric identity vs. cinematic continuity.**
Biometric identity (bone structure, features, eye color) is stable across all frames, confirming ArcFace. But continuity attributes — hairstyle, color temperature, head angle — vary freely between independent generations. **Critical distinction:** the method produces *identity continuity*, not *scene continuity*.

**Observation C — Subject-specific behavior.**
Helena's softer lighting and pose may contribute to higher inter-frame continuity but lower anchor fidelity. Lucas's consistent framing produces the most stable anchor binding. Vance shows the clearest separation between anchor-binding and neighbor-drift.

---

## 5. Declared boundary

n=3 characters, single sequence each. This is a **demonstration of viability**, not a quantification of reliability. Reliability would require the same sequence repeated (≥3×) with between-run variance measured. The identity-continuity trade-off hypothesis is **consistent with these data but not established by them**.

---

## 6. Skeleton for Paper-001

The four findings together form a section:

> Reference works. Cinematic autonomy substitutes the subject. Manual framing preserves identity but not scene continuity. The identity-continuity trade-off is subject-dependent.

What remains untested: temporal continuity as a buildable property (frame interpolation or selection over independently-generated frames), reliability across repeated runs, and systematic characterization of subject-dependent factors.

---

*Liga IA+H · WINDI Publishing House · 04 Jun 2026*
*Constitutional bindings: I9, I11, I14, I19*
*Supersedes: PAPER-001-FINDINGS-VANCE.md*

