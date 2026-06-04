# SPINE-CAST Findings — Cena 7 / *O Peso do Eco*

**Document type:** Paper-001 finding record
**Subject:** Marcus Vance (anchor `marcus.vance.anchor.v1.png`)
**Method:** ArcFace/InsightFace (buffalo_l) cosine similarity, FORENSE tier ≥ 0.75
**Scope:** n=1 character, single sequence — viability demonstration, reliability TBD

---

## 1. Method

Two generation methods were compared against a single forensic anchor:

- **Video method** — Runway Gen-4 Turbo, image-to-video. Single reference, automatic scene direction.
- **Frame-by-frame method (Joey)** — Runway Gen-4 Image, static generation with reference image (`referenceImages` as canonical object, tag `character`), manual framing control per prompt.

Each generated frame was scored on three axes, with detector metadata (`det_score`, `n_faces`) recorded alongside every similarity value. A similarity number without its detector context is inadmissible.

---

## 2. Data

### 2.1 Video method (re-labeled)

| Frame | n_faces | det_score | similarity | Label |
|-------|---------|-----------|------------|-------|
| 001 | 1 | 0.8144 | 0.9129 | FORENSE |
| 002 | 1 | 0.7952 | 0.7484 | OPERACIONAL |
| 003 | 1 | 0.6772 | −0.0838 | WRONG_FACE (subject's back) |
| 004 | 5 | 0.7623 | −0.0636 | MULTI_FACE_NO_MATCH (monitor avatars) |
| 005 | 2 | 0.6805 | −0.0279 | MULTI_FACE_NO_MATCH (monitor avatars) |

**Correction note:** frames 003–005 were initially labeled `REJECT (anti-correlation)`. This was a misreading of the mechanism. The detector found *real faces* — they were simply not the subject (the subject's back; avatars on background monitors). Near-zero cosine is the signature of a real face matched against the wrong identity, not of identity collapse. Re-labeled `WRONG_FACE` / `MULTI_FACE_NO_MATCH`.

### 2.2 Frame-by-frame method — Sequence Test

Isolated variable: gaze rotation. All other attributes held constant in prompt.

| Frame | Instruction | Identity-anchor | Label |
|-------|-------------|-----------------|-------|
| 001 | frontal (0°) | 0.8621 | FORENSE |
| 002 | 5° left | 0.9354 | FORENSE |
| 003 | 10° left | 0.9084 | FORENSE |
| 004 | gaze to monitor (~15°) | 0.8102 | FORENSE |
| 005 | return to center (0°) | 0.8469 | FORENSE |

**Three measurements:**

| Axis | Result | Reading |
|------|--------|---------|
| Identity-anchor (mean) | 0.8749 (σ 0.0316) | All FORENSE |
| Continuity-neighbor (mean) | 0.8620 (σ 0.0190) | **Below anchor** |
| Reproducibility (001↔005) | 0.8899 | Moderate |

---

## 3. Findings

**Finding 1 — Reference preserves identity.**
Both methods produce a FORENSE-tier subject at frame 001. The anchor binds the embedding space. *(Proven: anchor measurement, both methods, frame 001.)*

**Finding 2 — Video autonomy substitutes the subject; it does not degrade it.**
The video method's near-zero similarities are not identity decay. The detector found real faces that were not the subject: the subject's back (frame 003), background monitor avatars (frames 004–005). The failure is one of *scene direction* — the generator moved the subject out of frame and filled the frame with other faces. *(Proven: forensic re-labeling, WRONG_FACE + MULTI_FACE_NO_MATCH.)*

**Finding 3 — Frame-by-frame preserves identity but does not produce temporal continuity.**
Continuity-neighbor (0.8620) is *below* identity-anchor (0.8749). Frames cling to the anchor, not to one another. There is no smooth trajectory between adjacent frames — each generation is an independent draw within the anchor space. Reproducibility of 0.89 between two same-prompt frames (001, 005) confirms moderate, not high, stability. *(Proven: Sequence Test.)*

---

## 4. Visual observations (n=1)

**Observation A — Identity vs. moment.**
Frame 001 vs frame 005 (identical prompt) read visually as "the same person, different photograph." A direct cut 001→005 in a film would register as a jump cut. Identity is continuous; the moment is not.

**Observation B — Biometric identity vs. cinematic continuity.**
Biometric identity (bone structure, features, eye color) is stable across all frames, confirming ArcFace. But continuity attributes — hairstyle, color temperature, head angle — vary freely between independent generations. The hair sits looser in one frame, slicked back in another; skin tone shifts warm / neutral / cold-blue with lighting. **Critical distinction:** the method produces *identity continuity*, not *scene continuity*. A reviewer must not read "continuity" as face when the data only guarantees it for the face and explicitly denies it for the scene.

The blue-bunker frame is the strongest stress evidence: a total lighting change (dark moody → blue with monitors) — the same conditions under which the video method substituted the subject — left identity comfortably FORENSE under the Joey method. Identity absorbed the aesthetic shock. Scene attributes did not.

---

## 5. Declared boundary

n=1 character, single sequence. This is a **demonstration of viability**, not a quantification of reliability. Reliability would require the same sequence repeated (≥3×) with between-run variance measured. The competing-objectives hypothesis — *identity preservation and cinematic autonomy are in tension in current generators* — is consistent with these data but not established by them.

---

## 6. Skeleton for Paper-001

The three findings together form a section:

> Reference works. Cinematic autonomy substitutes the subject. Manual framing preserves identity but not scene continuity.

What remains untested: temporal continuity as a buildable property (frame interpolation or selection over independently-generated frames), and reliability across repeated runs and across characters (Helena — `FACE_TOO_SMALL` test; Lucas — `FAIL_NO_FACE` test).

---

*Liga IA+H · WINDI Publishing House · 04 Jun 2026*
*Constitutional bindings: I9, I11, I14, I19*
