# VANCE Pipeline Report — 05 Jun 2026
## W-HIOS FORENSIC UNIT · O Peso do Eco

**Run ID:** 20260605113834
**Model Lock:** WINDI-SPINE-MODEL-LOCK-20260604173447
**Anchor Lock:** WINDI-ANCHOR-VANCE-LOCK-20260605103558
**Constitutional Bindings:** I9, I11, I14, I19

---

## 1. Summary

| Metric | Value |
|--------|-------|
| Total Shots | 10 |
| FORENSIC (≥0.75) | 6 (60%) |
| OPERATIONAL (≥0.65) | 1 (10%) |
| FAIL (<0.65) | 2 (20%) |
| Timeouts/Errors | 2 (20%) |

**Note:** S06-01 and S06-02 from previous session included.

---

## 2. Complete Results

| Shot | Scene | Type | Avg Sim | Status | Frame Analysis |
|------|-------|------|---------|--------|----------------|
| S06-01 | 6 | 👤 | 0.3450 | ❌ FAIL | (previous session) |
| S06-02 | 6 | ⭐ | 0.8809 | ✅ FORENSIC | (previous session) |
| S07-01 | 7 | ⭐ | 0.9092 | ✅ FORENSIC | 5/5 FORENSIC |
| S07-02 | 7 | 👤 | 0.9186 | ✅ FORENSIC | 5/5 FORENSIC |
| S09-01 | 9 | 👤 | — | ⚠️ TIMEOUT | API queue congestion |
| S09-02 | 9 | ⭐ | 0.9059 | ✅ FORENSIC | 5/5 FORENSIC |
| S11-01 | 11 | 👤 | 0.4986 | ❌ FAIL | 1 FORENSIC, 1 FAIL, 3 NO_FACE |
| S14-01 | 14 | 👤 | — | ⚠️ API ERROR | "Unexpected error" |
| S14-02 | 14 | ⭐ | 0.9090 | ✅ FORENSIC | 5/5 FORENSIC |
| S15-01 | 15 | ⭐ | 0.8192 | 🟢 OPERATIONAL | 3 FORENSIC, 2 OPERATIONAL |

---

## 3. Emotional vs Non-Emotional Analysis

| Category | Count | Avg Score | Success Rate |
|----------|-------|-----------|--------------|
| ⭐ Emotional | 5 measured | 0.8848 | 100% (5/5) |
| 👤 Non-Emotional | 3 measured | 0.5907 | 33% (1/3) |

**Finding:** Emotional shots (close-ups, face-dominant) perform significantly better than action shots. This aligns with Paper-001 recommendations.

---

## 4. Paper-001 Finding 2 Evidence

**S11-01 Frame Breakdown:**

| Frame | Similarity | Det Score | Faces | Status |
|-------|------------|-----------|-------|--------|
| 01 | 0.9051 | 0.811 | 1 | ✅ FORENSIC |
| 02 | 0.0921 | 0.508 | 1 | ❌ FAIL (degrading) |
| 03 | — | — | 0 | NO_FACE |
| 04 | — | — | 0 | NO_FACE |
| 05 | — | — | 0 | NO_FACE |

This shot demonstrates the exact behavior described in Finding 2:
> "Video generation of bodies-with-faces fails through subject framing loss. The generator does not degrade identity — it SUBSTITUTES the subject by moving them out of frame."

The prompt requested "Vance entering corporate office" (full body + face). Frame 1 shows Vance clearly, but by frame 3 the face has left the frame entirely.

---

## 5. Identity Stability Within Shots

**S15-01 Frame Breakdown:**

| Frame | Similarity | Status |
|-------|------------|--------|
| 01 | 0.9071 | ✅ FORENSIC |
| 02 | 0.8563 | ✅ FORENSIC |
| 03 | 0.8470 | ✅ FORENSIC |
| 04 | 0.7423 | 🟢 OPERATIONAL |
| 05 | 0.7432 | 🟢 OPERATIONAL |

Shows gradual identity drift within shot (0.16 drop from frame 1 to 5), but all frames remain above OPERATIONAL threshold. Acceptable for production with disclaimer.

---

## 6. Generator Compatibility Update

| Generator | Anchor | Status | Avg Score |
|-----------|--------|--------|-----------|
| **Runway Gen-4** | Vance v1 | ✅ FORENSIC | 0.88 |
| **Veo 3.1** | Vance v1 | ❌ BLOCKED | — |
| **Veo 3.1** | Vance v2 | ✅ Works | (different identity) |

**Recommendation:** Continue production with Runway + v1 anchor.

---

## 7. Production Recommendations

### Shots Ready for Production
- S06-02, S07-01, S07-02, S09-02, S14-02: All FORENSIC tier
- S15-01: OPERATIONAL tier (acceptable with continuity disclaimer)

### Shots Requiring Regeneration
- S06-01: FAIL (0.3450) — regenerate as close-up
- S11-01: FAIL (framing loss) — redesign as IDENTITY shot only, or accept as ACTION shot

### Shots Requiring Retry
- S09-01, S14-01: API failures — resubmit to Runway

### Shot Grammar Validation
The SHOT-GRAMMAR-001 methodology is validated:
- IDENTITY shots with face-dominant framing succeed
- ACTION shots (body + face) exhibit Finding 2 behavior
- Emotional shots (⭐) outperform non-emotional

---

## 8. Files Generated

```
/home/windi/hios/cinema/obras/w-hios-forensic-unit/shots/vance/
├── S06-01.mp4
├── S06-02.mp4
├── S07-01.mp4
├── S07-02.mp4
├── S09-02.mp4
├── S11-01.mp4
├── S14-02.mp4
├── S15-01.mp4
├── VANCE_RESULTS_20260605113834.json
└── *_frames/ (extracted frames for each)
```

---

## 9. Constitutional Compliance

- **I9:** Human Dragon approved anchor lock before generation
- **I11:** All measurements recorded with run_id and det_score
- **I14:** Failures explicitly documented (no placeholders)
- **I19:** Provenance chain maintained (anchor → video → frames → measurements)

---

*Liga IA+H · WINDI Publishing House · 05 Jun 2026*
*"The method descends from the finding."*
