# VANCE V2 — Anti-Likeness Analysis
## W-HIOS FORENSIC UNIT · 05 Jun 2026

**Status:** DOCUMENTED
**Constitutional Bindings:** I9, I11, I14, I19
**Triggered By:** Veo 3.1 celebrity filter blocking v1 anchor

---

## 1. Background

During TEST-SPINE-003 (Veo 3.1 integration test), the Marcus Vance v1 anchor was blocked by Google's celebrity likeness filter:

```
❌ BLOCKED: ['Public figure']
```

Per Guardian's constitutional guidance, this was treated as a **Likeness Gate** — not a bug to circumvent, but a legitimate governance check requiring proper resolution.

---

## 2. Guardian Anti-Likeness Prompt

Guardian (Gemini) designed a divergent prompt explicitly engineered to:
1. Pass celebrity filters
2. Create a visually distinct character
3. Maintain narrative function (Interpol inspector)

**Divergence Features:**
- Heterochromia (left eye steel-grey, right eye hazel-green)
- Lateral nose deviation (aquiline with mid-bridge bump)
- Asymmetric jawline
- Eyebrow scar (1.5cm, left side)
- 3-day stubble (salt-and-pepper)
- Harsh side-lighting to obscure symmetry
- Messy swept-back hair (not slicked)

---

## 3. Generation Result

| Field | Value |
|-------|-------|
| Generator | Veo 3.1 (text-to-video) |
| Model | veo-3.1-generate-preview |
| Method | Pure text-to-video (no image input) |
| Duration | 81 seconds |
| Filter Status | ✅ PASSED |

**Output:**
- Video: `vance_v2_20260605113255.mp4`
- Anchor: `vance_v2_20260605113255_anchor.png`
- Provenance: `vance_v2_20260605113255.provenance.json`

---

## 4. Identity Analysis (ArcFace buffalo_l)

| Comparison | Similarity | Interpretation |
|------------|------------|----------------|
| **Vance v2 × Couto** | 0.1765 | ✅ Different characters (better than v1 baseline 0.2057) |
| **Vance v1 × v2** | 0.0864 | ⚠️ Different identity (only 8.6% match) |

**Detection Score:** 0.7766 (good confidence)

---

## 5. Verdict

The Guardian's anti-likeness prompt successfully created a character that:
- ✅ Passes Veo celebrity filter
- ✅ Discriminates well from Couto (0.1765)
- ❌ Is NOT the same identity as Vance v1 (0.0864 << 0.65)

**Implication:** Vance v2 cannot be used as a replacement anchor for SPINE-CAST continuity with v1. The divergence features changed the face geometry too much.

---

## 6. Production Decision

| Generator | Anchor | Status |
|-----------|--------|--------|
| **Runway Gen-4** | Vance v1 | ✅ Primary (FORENSIC ~0.78 avg) |
| **Veo 3.1** | Vance v1 | ❌ Blocked by celebrity filter |
| **Veo 3.1** | Vance v2 | ✅ Works, but different identity |

**Recommendation:** Continue O Peso do Eco production using **Runway + v1 anchor** exclusively. Veo is not SPINE-compatible for this character until:

1. A new anchor is generated that both:
   - Passes Veo's celebrity filter
   - Maintains ≥0.65 similarity to v1

2. Or Paper-001 methodology is extended to accept "narrative continuity" without biometric continuity

---

## 7. Constitutional Implications

This incident established a new invariant candidate:

> **I-LIKENESS (proposed):** Third-party content filters constitute governance gates, not obstacles. Circumvention that preserves surface appearance while evading detection is constitutionally equivalent to forgery.

The Guardian's approach (explicit divergence) is the correct constitutional response — accept the filter's verdict and redesign the asset, rather than adversarially fooling the filter.

---

## 8. Files

| File | Location |
|------|----------|
| V2 Video | `anchors/vance_v2_candidates/vance_v2_20260605113255.mp4` |
| V2 Anchor | `anchors/vance_v2_candidates/vance_v2_20260605113255_anchor.png` |
| V2 Embedding | `anchors/vance_v2_candidates/vance_v2_20260605113255_anchor.embedding.npy` |
| V2 Provenance | `anchors/vance_v2_candidates/vance_v2_20260605113255.provenance.json` |

---

*Liga IA+H · WINDI Publishing House · 05 Jun 2026*
*"The filter was right. The divergence was necessary."*
