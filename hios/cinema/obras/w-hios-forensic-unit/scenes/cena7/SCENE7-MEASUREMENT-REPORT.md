# SCENE 7 — SPINE-CAST MEASUREMENT REPORT
## W-HIOS FORENSIC UNIT · O Peso do Eco

**Measured:** 2026-06-04T18:12:00Z
**Scene Type:** PILOT (Low Risk)
**Generator:** Runway Gen-4 Turbo
**Constitutional Bindings:** I9, I11, I14, I19

---

## RECEIPT DECLARATIONS

| Receipt | ID | Purpose |
|---------|-----|---------|
| Threshold | `WINDI-SPINE-THRESHOLD-20260604150425` | 0.65/0.75 locked |
| Model Lock | `WINDI-SPINE-MODEL-LOCK-20260604173447` | w600k_r50.onnx hash |

---

## CAST

| Character | Anchor | Expected Role |
|-----------|--------|---------------|
| Marcus Vance | `marcus.vance.anchor.v1` | Protagonist |
| Helena Meyer | `helena.meyer.junior.anchor.v1` | Forensic Analyst |
| Lucas Silva | `lucas.silva.anchor.v1` | Tech Specialist |

---

## MEASUREMENT RESULTS

### Summary Statistics (RE-ETIQUETADO 04 Jun 2026)

| Metric | Value | Notes |
|--------|-------|-------|
| Total Frames | 15 | 5 per character |
| FORENSE (≥0.75) | 3 (20%) | All frame 001 |
| OPERACIONAL (≥0.65) | 1 (7%) | vance_002 |
| FACE_TOO_SMALL | 4 (27%) | helena_002-005 (zoom out) |
| WRONG_FACE | 1 (7%) | vance_003 (back of head) |
| MULTI_FACE_NO_MATCH | 2 (13%) | vance_004-005 (avatar faces) |
| FAIL_NO_FACE | 4 (27%) | lucas_002-005 (subject absent) |

**VERDICT:** Video generation SUBSTITUTES subject, does not degrade identity

**CORRECTION (04 Jun 2026):** Original labels UNIDENTIFIED/REJECT were misleading.
Re-labeling with det_score and n_faces revealed the true mechanism:
- The detector FOUND faces (det_score 0.68-0.76)
- But they were WRONG faces: backs of heads, monitor avatars
- Negative similarity = different person, not measurement failure

### Frame-by-Frame Analysis

#### Helena Meyer

| Frame | Similarity | Classification | Notes |
|-------|------------|----------------|-------|
| helena_001 | **0.9178** | ✅ FORENSE | Excellent match |
| helena_002 | <0.65 | ⚠️ FACE_TOO_SMALL | Camera zoomed out, face ~20px |
| helena_003 | <0.65 | ⚠️ FACE_TOO_SMALL | Full body shot, face too small |
| helena_004 | <0.65 | ⚠️ FACE_TOO_SMALL | Continued zoom out |
| helena_005 | <0.65 | ⚠️ FACE_TOO_SMALL | Continued zoom out |

**Pattern:** Strong initial seeding (0.92), camera zoom out destroyed facial resolution.
**Mechanism:** Not identity drift — framing failure. ArcFace needs minimum face size.

#### Lucas Silva

| Frame | Similarity | Classification | Notes |
|-------|------------|----------------|-------|
| lucas_001 | **0.9887** | ✅ FORENSE | Exceptional match |
| lucas_002 | — | ⚠️ FAIL_NO_FACE | Subject left frame |
| lucas_003 | — | ⚠️ FAIL_NO_FACE | Camera zoomed to monitors |
| lucas_004 | — | ⚠️ FAIL_NO_FACE | No person visible |
| lucas_005 | — | ⚠️ FAIL_NO_FACE | No person visible |

**Pattern:** Perfect initial seeding (0.99), generator removed subject from frame.

#### Marcus Vance (RE-ETIQUETADO com det_score e n_faces)

| Frame | n_faces | det_score | Similarity | Classification | Notes |
|-------|---------|-----------|------------|----------------|-------|
| vance_001 | 1 | 0.8144 | **0.9129** | ✅ FORENSE | Strong match |
| vance_002 | 1 | 0.7952 | 0.7484 | ✅ OPERACIONAL | Visual artifacts bleeding |
| vance_003 | 1 | 0.6772 | -0.0838 | ❌ WRONG_FACE | Back of head detected |
| vance_004 | **5** | 0.7623 | -0.0636 | ❌ MULTI_FACE_NO_MATCH | Avatar faces on monitors |
| vance_005 | **2** | 0.6805 | -0.0279 | ❌ MULTI_FACE_NO_MATCH | Avatar faces on monitors |

**Pattern:** Good initial frames (0.91→0.75), then SUBJECT SUBSTITUTION.
**Mechanism:** Generator turned subject around (003) then filled monitors with avatars (004-005).
The detector FOUND faces — they just weren't Vance. Negative similarity = different person.

---

## KEY FINDINGS

### Finding 1: Reference Seeding Works

All three characters achieved **FORENSE classification** on frame 001:
- Helena: 0.9178
- Lucas: 0.9887 (exceptional)
- Vance: 0.9129

**Conclusion:** The anchor reference image correctly seeds the first frame.

### Finding 2: Video Autonomy SUBSTITUTES Subject (Corrected)

By frame 002-003, all characters experienced FRAMING FAILURE, not identity drift:
1. **FACE_TOO_SMALL** (Helena: camera zoomed out, face too small for ArcFace)
2. **FAIL_NO_FACE** (Lucas: subject removed from frame by generator)
3. **WRONG_FACE + MULTI_FACE** (Vance: turned around, monitors filled with avatars)

**Conclusion (corrected):** In these three samples (n=1 each), Runway Gen-4 Turbo
failed to maintain the subject in frame beyond the first second. The generator
does not "lose" identity — it SUBSTITUTES the subject with other visual elements
(backs, avatars, empty monitors). This is a scene direction failure, not identity
collapse.

### Finding 3: Failure is SUBSTITUTION, Not Degradation

The generator does not gradually degrade identity — it makes scene direction choices
that remove the subject from measurable position:
- **Framing change** (Helena: zoom out destroyed facial resolution)
- **Subject removal** (Lucas: camera focused on monitors, person gone)
- **Orientation change + avatar fill** (Vance: turned around, monitors got avatars)

**Key insight:** The detector found faces in 11/15 frames. The failure is not
"no face found" — it's "wrong face found" or "face too small to measure".

---

## PAPER-001 HYPOTHESIS ASSESSMENT

**Hypothesis (pre-registered):**
> "Em sistemas generativos actuais, personagens masculinos de meia-idade sob iluminação dura apresentam menor distância embutida entre identidades distintas do que personagens femininas sob iluminação suave."

**Scene 7 Status:** Cannot test inter-character collision because temporal continuity failed.

**Revised Finding:** Before testing inter-character collision, generators must first achieve intra-character continuity. Scene 7 failed this prerequisite.

---

## RECOMMENDATIONS

1. **Re-generate with shorter duration (1s)** to test if continuity improves with fewer frames
2. **Test static image generation** before video to isolate the continuity problem
3. **Compare with other generators** (SORA tested in previous session: also failed SPINE)
4. **Consider frame-interpolation approach**: generate multiple single-frame images and interpolate

---

## RAW DATA (RE-ETIQUETADO)

Full measurement JSON: `scene7_measurement.json`

```
Total frames measured: 15
  FORENSE:           3  (all frame 001)
  OPERACIONAL:       1  (vance_002)
  FACE_TOO_SMALL:    4  (helena_002-005)
  WRONG_FACE:        1  (vance_003 — back of head)
  MULTI_FACE_NO_MATCH: 2  (vance_004-005 — avatars)
  FAIL_NO_FACE:      4  (lucas_002-005)
```

**Correction history:**
- Original labels (cfe0e1e0): UNIDENTIFIED, REJECT
- Corrected labels (this version): FACE_TOO_SMALL, WRONG_FACE, MULTI_FACE_NO_MATCH
- Reason: Original labels masked the true mechanism (substitution, not degradation)

---

*Liga IA+H · WINDI Publishing House · 04 Jun 2026*
*"The gap is the finding."*
