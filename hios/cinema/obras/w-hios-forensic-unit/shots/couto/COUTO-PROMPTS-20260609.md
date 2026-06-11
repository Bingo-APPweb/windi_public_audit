# MARCUS COUTO — SPINE-CAST Prompts
## 7 Shots | Episode: O Peso do Eco (Pilot)

**Created:** 09 Jun 2026
**Liga IA+H:** Human Dragon (I9) · CCode (Opus 4.5)
**Invariants:** I1, I9, I11, I14, I19
**Generator:** Runway Gen-4 Turbo (image-to-video)
**Anchor:** `marcus.couto.anchor.v1.png`

---

## Anti-Movement Medicine Applied

> *"Already in frame. Near-frontal. Camera locked. Light moves, not subject."*

**Rules:**
- ✅ Eyes scanning, blinking, focus shifting
- ✅ Micro-expression (jaw tension, lip compression)
- ✅ Visible breathing (shoulders, chest)
- ✅ Ambient light movement (shadows, reflections)
- ❌ Head turn / looking off-camera
- ❌ Weight shift / posture change
- ❌ Walking / stepping

---

## SHOT S02-01 — Corridor Predator

**Scene:** 2 | **Type:** PREDATOR | **Threshold:** ≥0.65

**Setting:** Dark marble corridor, 42nd floor, night. Frosted glass door visible. Minimal NOIR lighting.

**Prompt:**
```
A man in his mid-40s with slicked-back grey hair, clean-shaven, sharp angular jaw, wearing a dark cashmere overcoat over white shirt and black tie. He stands still in a dark corporate corridor at night, near-frontal framing, head perfectly still. His calculating dark eyes scan methodically left to right, watching through frosted glass. Predatory patience. Micro-expression: lips slightly compressed. Ambient office lights flicker subtly on his face. Breathing visible in chest. Camera locked. Cinematic 4K, shallow depth of field.
```

---

## SHOT S03-01 — Confrontation Entrance

**Scene:** 3 | **Type:** CLOSE-UP | **Threshold:** ≥0.75

**Setting:** Glass-walled meeting room. Soft overhead lighting. Frankfurt skyline visible through windows.

**Prompt:**
```
Close-up portrait of a man in his mid-40s with slicked-back grey hair, completely clean-shaven, pronounced angular jaw, cold calculating dark eyes. Wearing dark cashmere overcoat, white shirt, black tie. Expression already formed: cold bureaucratic courtesy masking total emptiness. Near-frontal, head locked still. Eyes fixed forward with predatory stillness. Subtle ambient light from office windows plays across his face. Visible micro-tension in jaw muscles. Camera locked. Cinematic 4K, dramatic corporate lighting.
```

---

## SHOT S03-02 — Physical Threat

**Scene:** 3 | **Type:** ACTION | **Threshold:** ≥0.65

**Setting:** Same meeting room. Character has already stepped forward — capture the stillness after movement.

**Prompt:**
```
Medium shot of a man in his mid-40s with slicked-back grey hair, clean-shaven, angular jaw, wearing dark cashmere overcoat over white shirt. He stands perfectly still after having stepped forward, body already in threatening proximity position. Near-frontal framing, head locked. Expression: cold intimidation already formed. Dark calculating eyes fixed on target. Ambient light shifts subtly across his face from window reflections. Visible breathing in shoulders. Camera locked, stable. Cinematic 4K, tense corporate thriller lighting.
```

---

## SHOT S10-01 — Rooftop Report

**Scene:** 10 | **Type:** NEUTRAL | **Threshold:** ≥0.65

**Setting:** 42nd floor penthouse, aggressive daylight through massive windows. Frankfurt skyline. Corporate luxury.

**Prompt:**
```
Medium shot of a man in his mid-40s with slicked-back grey hair, completely clean-shaven, sharp angular jaw, wearing a perfectly tailored dark European suit, white shirt. He holds a corporate tablet in both hands, already positioned. Near-frontal framing, head and body perfectly still. Eyes scan the tablet with methodical precision. Expression: efficient, emotionless corporate facade. Harsh daylight from floor-to-ceiling windows creates dramatic shadows. Frankfurt skyline visible behind. Camera locked. Cinematic 4K, corporate thriller aesthetic.
```

---

## SHOT S11-01 — Confrontation with Interpol

**Scene:** 11 | **Type:** CONFRONTATION | **Threshold:** ≥0.65

**Setting:** Same penthouse. Facing off against visitors. Defensive posture already established.

**Prompt:**
```
Medium close-up of a man in his mid-40s with slicked-back grey hair, clean-shaven, angular jaw, cold dark eyes. Wearing dark suit, white shirt. He stands in a challenging posture, body already positioned forward, near-frontal framing. Head locked perfectly still. Expression already formed: controlled aggression beneath bureaucratic mask. Eyes fixed with predatory focus. Harsh daylight creates dramatic shadows across his face. Subtle jaw muscle tension visible. Breathing visible in chest. Camera locked. Cinematic 4K, tense standoff lighting.
```

---

## SHOT S12-01 — Window Introspection

**Scene:** 12 | **Type:** INTROSPECTION | **Threshold:** ≥0.75

**Setting:** Same penthouse, looking out window. Moment of doubt after Interpol departure.

**Prompt:**
```
Profile-to-three-quarter shot of a man in his mid-40s with slicked-back grey hair, completely clean-shaven, angular jaw. Wearing dark suit. He stands at floor-to-ceiling window, already positioned, gazing out at Frankfurt skyline below. Head perfectly still, locked in contemplation. Expression already formed: subtle crack in the mask, hint of concern in the eyes. Natural daylight illuminates his profile. Subtle reflection visible in glass. Breathing visible in shoulders. Camera locked. Cinematic 4K, contemplative corporate thriller lighting.
```

---

## SHOT S13-01 — Tribunal Fear

**Scene:** 13 | **Type:** EMOTIONAL | **Threshold:** ≥0.75

**Setting:** German federal courtroom. Classic wood panels. Institutional lighting.

**Prompt:**
```
Close-up portrait of a man in his mid-40s with slicked-back grey hair, completely clean-shaven, pronounced angular jaw. Wearing impeccable dark suit, white shirt. Seated in courtroom, near-frontal framing, head perfectly still. Expression already formed: attempt at composure failing, fear visible in the dark eyes. The mask cracking. Micro-expression: subtle tension around mouth, eyes slightly wider than normal. Warm institutional lighting from wood-paneled courtroom. Camera locked. Cinematic 4K, dramatic courtroom lighting.
```

---

## GENERATION SEQUENCE

1. **First batch (v1):** All 7 shots
2. **Measure:** Using `measure_scene.py` with anchor
3. **Evaluate:** Apply SHOT-GRAMMAR-002 (FAIL has cause)
4. **Re-render:** Any FAIL_IDENTIDADE shots only

---

## THRESHOLDS

| Type | Operational | Forensic | HD Exception |
|------|-------------|----------|--------------|
| CLOSE-UP | ≥0.65 | ≥0.75 | ≥0.70 |
| EMOTIONAL | ≥0.65 | ≥0.75 | ≥0.70 |
| ACTION | ≥0.55 | ≥0.65 | — |
| NEUTRAL | ≥0.65 | ≥0.75 | — |
| CONFRONTATION | ≥0.55 | ≥0.65 | — |

---

## CONTINUITY CHECKLIST

- [x] Grey hair, slicked back
- [x] CLEAN-SHAVEN (no beard, no mustache) — CRITICAL
- [x] Angular jaw, calculating dark eyes
- [x] Dark cashmere overcoat OR dark European suit
- [x] White shirt
- [x] Expression: cold bureaucratic courtesy

---

*Liga IA+H · WINDI Publishing House · 09 Jun 2026*
*"AI processes. Human decides. WINDI guarantees."*
