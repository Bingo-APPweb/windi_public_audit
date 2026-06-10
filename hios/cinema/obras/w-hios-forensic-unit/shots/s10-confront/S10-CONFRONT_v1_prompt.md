# S10-CONFRONT_v1 — Disambiguation Gate Stress Test
## W-HIOS FORENSIC UNIT · Phase 2

**Status:** PENDING GENERATION
**Created:** 10 Jun 2026
**Liga IA+H:** Human Dragon (I9 authorized) · CCode (Architect)
**Doctrine:** DOCTRINE-HIOS-ATTESTATION-001 · G-ATT-1

---

## PURPOSE

This is the **first disambiguation test** of the SPINE-CAST pipeline.

- **Par tested:** Alejandro × Couto (0.4498 inter-anchor — tightest pair)
- **Goal:** Prove attribution works when two distinct faces share same frame
- **Gate:** Both faces must attribute correctly to their anchor with margin

---

## PROMPT (Anti-Movement Medicine Applied)

```
Medium shot, corporate boardroom. Two men in dark suits.

LEFT SIDE OF FRAME — ALEJANDRO VALENZUELA:
43-year-old European-Latin executive with sharp angular facial features.
Dark hair cleanly styled short with subtle gel. Piercing intelligent dark
brown eyes. Smooth clean-shaven skin. Wearing charcoal grey Italian suit
with crisp white shirt. He is ALREADY SEATED at the table, facing camera
in 3/4 profile. Head stays toward lens. He does NOT move — only his eyes
shift slightly. Face 70%+ visible.

RIGHT SIDE OF FRAME — MARCUS COUTO:
45-year-old European corporate man with impeccably slicked-back grey hair.
Sharp chiseled jawline, perfectly clean-shaven face. Cold piercing dark
brown eyes. Arrogant neutral expression. Wearing high-end black cashmere
overcoat over corporate suit. He is ALREADY STANDING behind the table,
facing camera in near-frontal view. He does NOT move — only the ambient
light shifts. Face 70%+ visible.

Both faces clearly visible and measurable. Power dynamic: Alejandro seated
(principal), Couto standing (subordinate reporting). Corporate thriller.

Camera LOCKED. No orbit. No angle change. Flat professional lighting.
Cinematic 4K.
```

---

## ANTI-MOVEMENT MEDICINE CHECKLIST

- [x] "Already in frame, does not enter"
- [x] "Camera locked, no orbit, no angle change"
- [x] "Near-frontal, head stays toward lens"
- [x] "He does NOT move"
- [x] "Face always 70%+ visible"
- [x] "Only eyes/light shifts, not body"

---

## EXPECTED MEASUREMENT

| Face | Expected Anchor | Required | Separation from Other |
|------|-----------------|----------|----------------------|
| Left | Alejandro | ≥0.65 | <0.50 to Couto |
| Right | Couto | ≥0.65 | <0.50 to Alejandro |

**Gate PASS criteria:**
1. Each face matches its anchor ≥0.65
2. Each face separation from other anchor <0.50
3. Margin (best - second) ≥0.15

---

## GENERATION PARAMETERS

- **Generator:** Runway Gen-4 Turbo (10s)
- **Aspect:** 16:9 (1280x768)
- **Duration:** 5 seconds
- **Seed:** Random

---

*Liga IA+H · WINDI Publishing House · 10 Jun 2026*
*"Hoje começam a provar que duas pessoas continuam distintas quando partilham o mesmo mundo."*
