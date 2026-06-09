# MARCUS COUTO — SEALED
## The Caretaker · 7/7 Shots SEALED

**Status:** SEALED
**Date:** 2026-06-09
**Character:** Marcus Couto (O Cuidador)
**Anchor:** `marcus.couto.anchor.v1.png`
**Detection Score:** 0.8811 (highest in pilot)
**Method:** Anti-Movement Medicine + METHOD-001
**Approval:** Human Dragon (I9)

---

## Anchor Quality

```
Anchor:          marcus.couto.anchor.v1.png
Detection Score: 0.8811
Embedding:       512-dim ArcFace (buffalo_l)
Movement Test:   avg=0.8206, min=0.7555 (profile holds)
```

---

## Shot Manifest

| Shot | Scene | Description | Tier | Avg | Min | Threshold | Verdict |
|------|-------|-------------|------|-----|-----|-----------|---------|
| S02-01_v1 | 2 | Corridor - observes Gabi through glass | OCLUSÃO | 0.7943 | 0.6891 | ≥0.60 | PASS |
| S03-01_v1 | 3 | Confrontation - "acabou a auditoria" | FORENSE | 0.9846 | 0.9736 | ≥0.75 | PASS |
| S03-02_v1 | 3 | Physical threat - advances | GEOMETRY | 0.9675 | 0.9480 | ≥0.65 | PASS |
| S10-01_v2 | 10 | Rooftop - reports to Alejandro | FORENSE | 0.8375 | 0.8132 | ≥0.75 | PASS |
| S11-01_v1 | 11 | Confrontation with Interpol | GEOMETRY | 0.9764 | 0.9686 | ≥0.65 | PASS |
| S12-01_v1 | 12 | Window introspection - "cinco anos" | GEOMETRY | 0.9637 | 0.9439 | ≥0.65 | PASS |
| S13-01_v1 | 13 | Tribunal - fear in eyes | FORENSE | 0.9589 | 0.9500 | ≥0.75 | PASS |

**Result:** 7/7 PASS

---

## S02-01_v1 — OCLUSÃO Analysis

```
Frame-by-frame:
  frame_01: 0.9849 (frontal)
  frame_02: 0.8293 (transition)
  frame_03: 0.7426 (glass interference)
  frame_04: 0.7254 (glass + profile)
  frame_05: 0.6891 (maximum occlusion)

Profile: 0.98 → 0.83 → 0.74 → 0.73 → 0.69

Cause: Frosted glass + profile rotation
Classification: FAIL_OCLUSÃO under SHOT-GRAMMAR-002
Admissibility: PASS (≥0.60 floor, identity inequivocal, intentional diegetic element)
```

---

## S10-01 — Version Supersession

| Version | Status | Avg | Issue | Receipt |
|---------|--------|-----|-------|---------|
| v1 | SUPERSEDED | 0.8808 | Cartoon background | — |
| v2 | CANONICAL | 0.8375 | Photorealistic fixed | This document |

**v2 Measurements:**
```
  frame_01: 0.8738 det=0.8958
  frame_02: 0.8378 det=0.8866
  frame_03: 0.8398 det=0.8815
  frame_04: 0.8230 det=0.8675
  frame_05: 0.8132 det=0.8634

Profile: 0.87 → 0.84 → 0.84 → 0.82 → 0.81
VERDICT: FORENSE (min >= 0.75)
```

---

## Anti-Movement Medicine Applied

All shots follow the doctrine:
- **Already in frame** — no entrance movements
- **Near-frontal** — head toward lens
- **Camera locked** — no camera motion
- **Light moves, not subject** — ambient shifts only

---

## Character Profile

```
Name:        Marcus Couto
Role:        Corporate Fixer ("The Caretaker")
Age:         Mid-40s
Build:       Slicked-back grey hair, clean-shaven, angular jaw
Wardrobe:    Dark cashmere overcoat, dark European suit, white shirt
Expression:  Cold bureaucratic courtesy masking emptiness
Arc:         S02 (predator) → S03 (confrontation) → S10 (reporting) → S13 (tribunal fear)
```

---

## Public URLs

All shots available at:
```
https://windi-domain.com/docs/hios-forensic/couto-shots-v1/
├── S02-01_v1.mp4
├── S03-01_v1.mp4
├── S03-02_v1.mp4
├── S10-01_v2.mp4  (canonical, v1 superseded)
├── S11-01_v1.mp4
├── S12-01_v1.mp4
└── S13-01_v1.mp4
```

---

## METHOD-001 Compliance

All measurements performed BEFORE presentation to Human Dragon.
No affirmations. Only numbers.

---

## Approval Chain

```
2026-06-09 09:05  CCode generates 7 shots
2026-06-09 09:10  ArcFace measures all frames
2026-06-09 09:15  S10-01 cartoon background flagged
2026-06-09 09:20  S10-01_v2 re-rendered with photorealistic
2026-06-09 09:25  All measurements presented
2026-06-09 09:30  Human Dragon approves 7/7
2026-06-09 09:35  COUTO-SEALED.md created
```

---

*Liga IA+H · Kempten · 09 Jun 2026*
*"No affirmations. Only numbers."*
