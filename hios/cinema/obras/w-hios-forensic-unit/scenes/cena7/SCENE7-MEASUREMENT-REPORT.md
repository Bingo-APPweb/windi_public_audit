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

### Summary Statistics

| Metric | Value |
|--------|-------|
| Total Frames | 15 |
| FORENSE (≥0.75) | 3 (20%) |
| OPERACIONAL (≥0.65) | 1 (7%) |
| UNIDENTIFIED | 7 (47%) |
| FAIL_NO_FACE | 4 (26%) |

**VERDICT:** OPERACIONAL (some faces need review)

### Frame-by-Frame Analysis

#### Helena Meyer

| Frame | Similarity | Classification | Notes |
|-------|------------|----------------|-------|
| helena_001 | **0.9178** | ✅ FORENSE | Excellent match |
| helena_002 | <0.65 | ❌ UNIDENTIFIED | Face geometry distorted |
| helena_003 | <0.65 | ❌ UNIDENTIFIED | Continued drift |
| helena_004 | <0.65 | ❌ UNIDENTIFIED | Continued drift |
| helena_005 | <0.65 | ❌ UNIDENTIFIED | Continued drift |

**Pattern:** Strong initial seeding (0.92), complete collapse by frame 2.

#### Lucas Silva

| Frame | Similarity | Classification | Notes |
|-------|------------|----------------|-------|
| lucas_001 | **0.9887** | ✅ FORENSE | Exceptional match |
| lucas_002 | — | ⚠️ FAIL_NO_FACE | Subject left frame |
| lucas_003 | — | ⚠️ FAIL_NO_FACE | Camera zoomed to monitors |
| lucas_004 | — | ⚠️ FAIL_NO_FACE | No person visible |
| lucas_005 | — | ⚠️ FAIL_NO_FACE | No person visible |

**Pattern:** Perfect initial seeding (0.99), generator removed subject from frame.

#### Marcus Vance

| Frame | Similarity | Classification | Notes |
|-------|------------|----------------|-------|
| vance_001 | **0.9129** | ✅ FORENSE | Strong match |
| vance_002 | 0.7484 | ✅ OPERACIONAL | Acceptable but declining |
| vance_003 | <0.65 | ❌ UNIDENTIFIED | Subject turned around (back of head) |
| vance_004 | <0.65 | ❌ UNIDENTIFIED | Multiple hallucinated faces |
| vance_005 | <0.65 | ❌ UNIDENTIFIED | Continued drift |

**Pattern:** Good initial frames (0.91→0.75), catastrophic drift as subject turns around.

---

## KEY FINDINGS

### Finding 1: Reference Seeding Works

All three characters achieved **FORENSE classification** on frame 001:
- Helena: 0.9178
- Lucas: 0.9887 (exceptional)
- Vance: 0.9129

**Conclusion:** The anchor reference image correctly seeds the first frame.

### Finding 2: Temporal Continuity Fails

By frame 002-003, all characters either:
1. **Drifted below IDENTITY_FLOOR** (Helena: 0.92→UNIDENTIFIED)
2. **Left the frame entirely** (Lucas: person removed by generator)
3. **Changed orientation** (Vance: turned to face away from camera)

**Conclusion:** Runway Gen-4 does NOT maintain identity across video frames.

### Finding 3: Drift is Catastrophic, Not Gradual

The identity collapse is not subtle degradation but transformative changes:
- Face geometry distortion (Helena frame 002)
- Subject removal (Lucas frames 002-005)
- Orientation change (Vance frame 003 shows back of head)

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

## RAW DATA

Full measurement JSON: `scene7_measurement.json`

```
Total frames measured: 15
  FORENSE:      3
  OPERACIONAL:  1
  REJECT:       0
  FAIL_NO_FACE: 4
```

---

*Liga IA+H · WINDI Publishing House · 04 Jun 2026*
*"The gap is the finding."*
