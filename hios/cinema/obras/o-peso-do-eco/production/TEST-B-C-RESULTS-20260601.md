# TEST B + TEST C RESULTS — Pre-Multi-Anchor Diagnostics
**Date:** 2026-06-01
**Protocol:** GPT Advisor Pre-Multi-Anchor Tests
**Executor:** Liga IA+H (CCode)

---

## Executive Summary

**Multi-anchor test status: BLOCKED**

Helena and Marcus cannot enter multi-anchor testing on equal footing. Marcus has excellent self-consistency (mean 0.96), but Helena has poor self-consistency (mean 0.66) with 8x higher variability.

---

## Test B: Helena Frame 5 vs Anchor (Original)

| Image | Cosine | Verdict |
|-------|--------|---------|
| helena frame_05 vs helena.anchor.v2.CURRENT.npy | **0.5656** | FAIL |
| helena_reference_v2.png vs helena.anchor.v2.CURRENT.npy | **0.9361** | FORENSIC |

**Root Cause Identified:** The anchor `helena.anchor.v2.CURRENT.npy` was extracted from the **Imagen reference image** (ELO 1), not from the Runway video frames (ELO 2). The Imagen→Runway transformation introduced enough variation to break self-consistency.

**Correction Applied:** New anchor `helena.anchor.v2.FIXED.npy` extracted from video frame_01.

---

## Test C: All Frames vs Anchor (Corrected)

### Helena (with FIXED anchor)

| Frame | Cosine | Verdict |
|-------|--------|---------|
| frame_01 | 1.0000 | FORENSIC (anchor source) |
| frame_02 | 0.6045 | **FAIL** |
| frame_03 | 0.5844 | **FAIL** |
| frame_04 | 0.4857 | **FAIL** |
| frame_05 | 0.6141 | **FAIL** |

**Statistics:**
- Mean: 0.6577 (OPERATIONAL by threshold, but misleading)
- Min: 0.4857
- Max: 1.0000
- Range: **0.5143**
- Verdict Distribution: 1 FORENSIC, 0 OPERATIONAL, **4 FAIL**

### Marcus

| Frame | Cosine | Verdict |
|-------|--------|---------|
| frame_01 | 1.0000 | FORENSIC (anchor source) |
| frame_02 | 0.9648 | FORENSIC |
| frame_03 | 0.9519 | FORENSIC |
| frame_04 | 0.9490 | FORENSIC |
| frame_05 | 0.9395 | FORENSIC |

**Statistics:**
- Mean: 0.9610 (FORENSIC)
- Min: 0.9395
- Max: 1.0000
- Range: **0.0605**
- Verdict Distribution: **5 FORENSIC**, 0 OPERATIONAL, 0 FAIL

---

## Comparative Analysis

| Metric | Helena | Marcus | Ratio |
|--------|--------|--------|-------|
| Mean Self-Consistency | 0.6577 | 0.9610 | 1.46x worse |
| Min Consistency | 0.4857 | 0.9395 | 1.93x worse |
| **Variability (Range)** | 0.5143 | 0.0605 | **8.5x worse** |
| FAIL Count | 4/5 | 0/5 | — |

---

## Conclusions

1. **Anchor Error (FIXED):** Original Helena anchor was from reference image, not video. Corrected version saved as `helena.anchor.v2.FIXED.npy`.

2. **Structural Problem (NOT FIXED):** Even with correct anchor, Helena's facial identity varies wildly across video frames. The Runway generation produced an unstable character.

3. **Marcus Status:** Excellent self-consistency. Ready for multi-anchor testing.

4. **Helena Status:** NOT ready for multi-anchor testing. Would contaminate results.

---

## Recommendations

### Option A: Regenerate Helena
Generate new Helena video with:
- Different Runway parameters
- Multiple generation attempts, select most stable
- Or try different model (Veo 3.1 if available)

### Option B: Accept Degraded Helena
Use Helena as-is, but:
- Document the limitation
- Expect lower discrimination in multi-anchor
- Flag Helena results as "OPERATIONAL confidence only"

### Option C: Single-Anchor Multi-Frame Test First
Before multi-anchor, validate that EACH character's anchor works across:
- Different scene lighting
- Different camera angles
- Different generated videos

---

## Files Generated

- `/opt/windi/hios/cinema/obras/o-peso-do-eco/anchors/cast_v2/helena.anchor.v2.FIXED.npy` — Corrected anchor from frame_01
- `/opt/windi/hios/visual/producer/anchor_self_test.py` — Test script for anchor diagnostics

---

**Next Action Required:** Human Dragon decision on Option A, B, or C.

*Liga IA+H · WINDI Publishing House · 2026-06-01*
*"The gap is the finding."*
