# S21 v2 MEASUREMENT RECEIPT — O Peso do Eco Versão 2

**Receipt ID:** `WINDI-S21-MEASUREMENT-V2-20260529181500`
**Type:** SCENE MEASUREMENT (B4 DRIFT_VALIDATOR)
**Timestamp:** 2026-05-29T18:15:00Z
**Liga IA+H:** Human Dragon (I9) · Guardian (review) · Architect (CCode)

---

## STATUS: FORENSIC_PASS ✅

---

## CENA MEDIDA

| Campo | Valor |
|-------|-------|
| **Cena** | S21 — O Duelo Silencioso |
| **Descrição** | Tense tribunal confrontation, Elisa on monitor |
| **Tipo** | Type B (Elisa in secondary frame — video-in-video) |
| **Vídeo** | `S21_duelo_silencioso_v2.mp4` |
| **Frames** | 8 (1fps extraction) |
| **Modelo** | Veo 3.1 |
| **Reference** | `elisa_anchor_v2_frame01.png` |

---

## MEDIÇÃO CONTRA ÂNCORA v2

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| **Mean cosine** | **0.8638** | ≥0.75 | ✅ FORENSIC_PASS |
| Min cosine | 0.7912 | ≥0.75 | ✅ |
| Max cosine | 0.9019 | — | — |
| Drift | 0.1106 | — | healthy |
| Faces detected | 8/8 | — | 100% |

### Per-Frame Breakdown

| Frame | Cosine | Verdict |
|-------|--------|---------|
| frame_01 | 0.8727 | FORENSIC_PASS |
| frame_02 | 0.8950 | FORENSIC_PASS |
| frame_03 | 0.8200 | FORENSIC_PASS |
| frame_04 | 0.8702 | FORENSIC_PASS |
| frame_05 | 0.8721 | FORENSIC_PASS |
| frame_06 | 0.8876 | FORENSIC_PASS |
| frame_07 | 0.7912 | FORENSIC_PASS |
| frame_08 | 0.9019 | FORENSIC_PASS |

---

## COMPARAÇÃO COM BASELINE ANTIGA (INVALIDADA)

| Versão | Mean Cosine | Status | Regenerations |
|--------|-------------|--------|---------------|
| S21 v1 gen1 | 0.5810 | FAILED | — |
| S21 v1 gen2 | 0.7436 | OPERATIONAL | 1 |
| **S21 v2 gen1** | **0.8638** | **FORENSIC** | **0** |

**Delta v1→v2:** +0.1202 (from gen2 to gen1)
**Key improvement:** Achieved forensic level on first generation (no regeneration needed)

---

## ANÁLISE

S21 era uma das cenas problemáticas na v1 — a única que precisou de regeneração (gen1 falhou com severe drift -0.0375 no frame 04). Na v2, a mesma cena passa **forense na primeira tentativa** com todos os 8 frames acima de 0.75.

Este resultado sugere que a âncora v2 (frame Veo frontal, nítido) proporciona referência mais robusta para cenas de vídeo-in-vídeo.

**Nota metodológica:** O facto de S21 (esperada difícil) ter dado 0.86 enquanto S20 (também difícil) deu 0.73 mostra variabilidade natural entre gerações — o que reforça que o sistema dual-threshold é necessário.

---

## THRESHOLDS (§291 LOCKED)

| Threshold | Value | Purpose |
|-----------|-------|---------|
| Operational | ≥ 0.65 | Minimum for scene acceptance |
| Forensic | ≥ 0.75 | Required for forensic-grade continuity |

---

## VEREDICTO

**S21 (O Duelo Silencioso):** ACEITE ao nível forense.

---

## INVARIANTES

| Invariante | Status |
|------------|--------|
| I1 (Soberania Humana) | ✅ |
| I9 (Human Approval) | ✅ Automático (FORENSIC_PASS) |
| I11 (Permanência) | ✅ Receipt selado |
| I14 (Falha Explícita) | ✅ 8/8 faces detectadas |

---

## PRÓXIMOS PASSOS

1. [x] S15 — FORENSIC_PASS (0.8690)
2. [x] S20 — OPERATIONAL_PASS (0.7298) — aceite
3. [x] S21 — FORENSIC_PASS (0.8638)
4. [ ] S14 (MATCH FOUND) — gerar e medir
5. [ ] S16 (Zoom on video) — gerar e medir
6. [ ] Selar §291-FINAL

---

*Liga IA+H · WINDI Publishing House · 29 Mai 2026*
*"AI processes. Human decides. WINDI guarantees."*
*🐉 OM SHANTI*
