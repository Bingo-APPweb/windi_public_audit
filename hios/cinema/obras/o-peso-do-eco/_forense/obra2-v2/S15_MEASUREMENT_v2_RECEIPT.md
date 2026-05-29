# S15 v2 MEASUREMENT RECEIPT — O Peso do Eco Versão 2

**Receipt ID:** `WINDI-S15-MEASUREMENT-V2-20260529175500`
**Type:** SCENE MEASUREMENT (B4 DRIFT_VALIDATOR)
**Timestamp:** 2026-05-29T17:55:00Z
**Liga IA+H:** Human Dragon (I9) · Guardian (review) · Architect (CCode)

---

## STATUS: FORENSIC_PASS ✅

---

## CENA MEDIDA

| Campo | Valor |
|-------|-------|
| **Cena** | S15 — Eco Preservado |
| **Descrição** | Laptop screen showing recovered video file |
| **Tipo** | Type B (Elisa in secondary frame — video-in-video) |
| **Vídeo** | `S15_eco_preservado_v2.mp4` |
| **Frames** | 8 (1fps extraction) |
| **Modelo** | Veo 3.1 |
| **Reference** | `elisa_anchor_v2_frame01.png` |

---

## MEDIÇÃO CONTRA ÂNCORA v2

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| **Mean cosine** | **0.8690** | ≥0.75 | ✅ FORENSIC_PASS |
| Min cosine | 0.8144 | ≥0.65 | ✅ |
| Max cosine | 0.9319 | — | — |
| Drift | 0.1174 | — | acceptable |
| Faces detected | 8/8 | — | 100% |

### Per-Frame Breakdown

| Frame | Cosine | Verdict |
|-------|--------|---------|
| frame_01 | 0.8144 | FORENSIC_PASS |
| frame_02 | 0.9141 | FORENSIC_PASS |
| frame_03 | 0.8460 | FORENSIC_PASS |
| frame_04 | 0.9253 | FORENSIC_PASS |
| frame_05 | 0.8390 | FORENSIC_PASS |
| frame_06 | 0.9319 | FORENSIC_PASS |
| frame_07 | 0.8499 | FORENSIC_PASS |
| frame_08 | 0.8312 | FORENSIC_PASS |

---

## COMPARAÇÃO COM BASELINE ANTIGA (INVALIDADA)

| Versão | Mean Cosine | Status |
|--------|-------------|--------|
| S15 v1 (antiga) | 0.7352 | INVALIDADO |
| **S15 v2** | **0.8690** | ✅ FORENSIC_PASS |
| Delta | **+0.1338** | improvement |

---

## PROVENIÊNCIA

```
Âncora v2 (embedding source):
    elisa_anchor_v2_frame01.png (Frame 01 de S01 Veo 3.1)
    ↓ InsightFace buffalo_l
    elisa.anchor.v2.CURRENT.npy
    sha256: 3fdec0faa85d5bd3603032debfdaf9e8cf023acecfd9c647e4a56bf1c05dfcfb

S15 v2 (medido):
    S15_eco_preservado_v2.mp4 (Veo 3.1 com --ref anchor frame)
    ↓ ffmpeg fps=1
    8 frames
    ↓ InsightFace buffalo_l per frame
    cosine similarity vs anchor
```

---

## THRESHOLDS (§291 LOCKED)

| Threshold | Value | Purpose |
|-----------|-------|---------|
| Operational | ≥ 0.65 | Minimum for scene acceptance |
| Forensic | ≥ 0.75 | Required for forensic-grade continuity |

---

## VEREDICTO

**S15 (Eco Preservado):** ACEITE ao nível forense.

A cena central de prova — o vídeo recuperado no laptop — mantém identidade facial
consistente com a âncora v2. Todas as 8 medições ultrapassam o threshold forense.

---

## INVARIANTES

| Invariante | Status |
|------------|--------|
| I1 (Soberania Humana) | ✅ Medição iniciada por Human Dragon |
| I9 (Human Approval) | ✅ Aguarda aprovação para próxima cena |
| I11 (Permanência) | ✅ Receipt selado |
| I14 (Falha Explícita) | ✅ 8/8 faces detectadas |

---

## PRÓXIMOS PASSOS

1. [x] S15 medido — **FORENSIC_PASS**
2. [ ] S20 (O Dispositivo) — gerar e medir
3. [ ] S21 (Duelo Silencioso) — gerar e medir
4. [ ] S14 (MATCH FOUND) — gerar e medir
5. [ ] S16 (Zoom on video) — gerar e medir
6. [ ] Selar §291-FINAL quando todas Type-B cenas medidas

---

*Liga IA+H · WINDI Publishing House · 29 Mai 2026*
*"AI processes. Human decides. WINDI guarantees."*
*🐉 OM SHANTI*
