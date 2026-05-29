# S20 v2 MEASUREMENT RECEIPT — O Peso do Eco Versão 2

**Receipt ID:** `WINDI-S20-MEASUREMENT-V2-20260529180500`
**Type:** SCENE MEASUREMENT (B4 DRIFT_VALIDATOR)
**Timestamp:** 2026-05-29T18:05:00Z
**Liga IA+H:** Human Dragon (I9) · Guardian (review) · Architect (CCode)

---

## STATUS: OPERATIONAL_PASS (degraded)

---

## CENA MEDIDA

| Campo | Valor |
|-------|-------|
| **Cena** | S20 — O Dispositivo |
| **Descrição** | Video of Elisa shown in tribunal courtroom |
| **Tipo** | Type B (Elisa in secondary frame — video-in-video) |
| **Vídeo** | `S20_o_dispositivo_v2.mp4` |
| **Frames** | 8 (1fps extraction) |
| **Modelo** | Veo 3.1 |
| **Reference** | `elisa_anchor_v2_frame01.png` |

---

## MEDIÇÃO CONTRA ÂNCORA v2

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| **Mean cosine** | **0.7298** | ≥0.75 | ⚠️ BELOW FORENSIC |
| Min cosine | 0.6751 | ≥0.65 | ✅ |
| Max cosine | 0.8255 | — | — |
| Drift | 0.1504 | — | moderate |
| Faces detected | 8/8 | — | 100% |

### Per-Frame Breakdown

| Frame | Cosine | Verdict |
|-------|--------|---------|
| frame_01 | 0.6751 | OPERATIONAL_PASS |
| frame_02 | 0.7297 | OPERATIONAL_PASS |
| frame_03 | 0.8255 | **FORENSIC_PASS** |
| frame_04 | 0.7126 | OPERATIONAL_PASS |
| frame_05 | 0.8092 | **FORENSIC_PASS** |
| frame_06 | 0.7091 | OPERATIONAL_PASS |
| frame_07 | 0.6920 | OPERATIONAL_PASS |
| frame_08 | 0.6851 | OPERATIONAL_PASS |

---

## COMPARAÇÃO COM BASELINE ANTIGA (INVALIDADA)

| Versão | Mean Cosine | Status |
|--------|-------------|--------|
| S20 v1 (antiga) | 0.7036 | OPERATIONAL |
| **S20 v2** | **0.7298** | OPERATIONAL |
| Delta | **+0.0262** | modest improvement |

---

## ANÁLISE

S20 é uma cena de **vídeo-in-vídeo** — Elisa aparece num ecrã de laptop dentro de uma sala de tribunal. Condições de medição mais difíceis:
- Degradação de resolução (vídeo dentro de vídeo)
- Iluminação ambiente diferente (tribunal vs outdoor)
- Possíveis artefactos de compressão

O resultado de 0.7298 é **consistente com as expectativas**:
- Passa o gate operacional (≥0.65) com margem
- Não atinge o gate forense (≥0.75)
- 2 dos 8 frames atingem forense individualmente

**Conclusão metodológica:** O threshold operacional de 0.65 existe precisamente para cenas como esta, onde a degradação é esperada mas a identidade se mantém verificável.

---

## PROVENIÊNCIA

```
Âncora v2 (embedding source):
    elisa_anchor_v2_frame01.png (Frame 01 de S01 Veo 3.1)
    ↓ InsightFace buffalo_l
    elisa.anchor.v2.CURRENT.npy
    sha256: 3fdec0faa85d5bd3603032debfdaf9e8cf023acecfd9c647e4a56bf1c05dfcfb

S20 v2 (medido):
    S20_o_dispositivo_v2.mp4 (Veo 3.1 com --ref anchor frame)
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

**S20 (O Dispositivo):** ACEITE ao nível operacional.

Cena mais difícil (vídeo-in-vídeo, tribunal) mostra degradação esperada mas mantém identidade verificável. Todos os frames passam operacional; 2/8 atingem forense.

**Decisão I9:** Aceitar como OPERATIONAL ou regenerar (até 3) para tentar forensic?

---

## INVARIANTES

| Invariante | Status |
|------------|--------|
| I1 (Soberania Humana) | ✅ Medição iniciada por Human Dragon |
| I9 (Human Approval) | ⏳ Aguarda decisão (aceitar/regenerar) |
| I11 (Permanência) | ✅ Receipt selado |
| I14 (Falha Explícita) | ✅ 8/8 faces detectadas |

---

## PRÓXIMOS PASSOS

1. [x] S15 medido — FORENSIC_PASS (0.8690)
2. [x] S20 medido — OPERATIONAL_PASS (0.7298)
3. [ ] S21 (Duelo Silencioso) — gerar e medir
4. [ ] S14 (MATCH FOUND) — gerar e medir
5. [ ] S16 (Zoom on video) — gerar e medir
6. [ ] Selar §291-FINAL quando todas Type-B cenas medidas

---

*Liga IA+H · WINDI Publishing House · 29 Mai 2026*
*"AI processes. Human decides. WINDI guarantees."*
*🐉 OM SHANTI*
