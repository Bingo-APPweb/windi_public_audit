# S14 v2 MEASUREMENT RECEIPT — O Peso do Eco Versão 2

**Receipt ID:** `WINDI-S14-MEASUREMENT-V2-20260529182000`
**Type:** SCENE MEASUREMENT (B4 DRIFT_VALIDATOR)
**Timestamp:** 2026-05-29T18:20:00Z
**Liga IA+H:** Human Dragon (I9) · Guardian (review) · Architect (CCode)

---

## STATUS: FORENSIC_PASS ✅

---

## CENA MEDIDA

| Campo | Valor |
|-------|-------|
| **Cena** | S14 — MATCH FOUND |
| **Descrição** | Forensic recognition screen showing identity match |
| **Tipo** | Type B (Elisa on forensic display) |
| **Vídeo** | `S14_match_found_v2.mp4` |
| **Frames** | 8 (1fps extraction) |
| **Modelo** | Veo 3.1 |
| **Reference** | `elisa_anchor_v2_frame01.png` |

---

## MEDIÇÃO CONTRA ÂNCORA v2

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| **Mean cosine** | **0.8110** | ≥0.75 | ✅ FORENSIC_PASS |
| Min cosine | 0.8019 | ≥0.75 | ✅ |
| Max cosine | 0.8199 | — | — |
| **Drift** | **0.0180** | — | **LOWEST** |
| Faces detected | 8/8 | — | 100% |

### Per-Frame Breakdown

| Frame | Cosine | Verdict |
|-------|--------|---------|
| frame_01 | 0.8071 | FORENSIC_PASS |
| frame_02 | 0.8019 | FORENSIC_PASS |
| frame_03 | 0.8019 | FORENSIC_PASS |
| frame_04 | 0.8147 | FORENSIC_PASS |
| frame_05 | 0.8166 | FORENSIC_PASS |
| frame_06 | 0.8143 | FORENSIC_PASS |
| frame_07 | 0.8120 | FORENSIC_PASS |
| frame_08 | 0.8199 | FORENSIC_PASS |

---

## ANÁLISE

S14 apresenta o **drift mais baixo** de todas as cenas medidas (0.0180). A identidade mantém-se extremamente estável ao longo dos 8 segundos — todos os cosines entre 0.80-0.82.

**Nota metodológica:** A cena "MATCH FOUND" mostra a Elisa num ecrã de análise forense, possivelmente com a imagem mais estática/frontal. Isto explica a estabilidade excepcional.

---

## VEREDICTO

**S14 (MATCH FOUND):** ACEITE ao nível forense.

---

*Liga IA+H · WINDI Publishing House · 29 Mai 2026*
