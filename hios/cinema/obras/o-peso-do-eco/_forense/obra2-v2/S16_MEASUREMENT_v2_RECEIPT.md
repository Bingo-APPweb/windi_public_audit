# S16 v2 MEASUREMENT RECEIPT — O Peso do Eco Versão 2

**Receipt ID:** `WINDI-S16-MEASUREMENT-V2-20260529182500`
**Type:** SCENE MEASUREMENT (B4 DRIFT_VALIDATOR) — **FINDING**
**Timestamp:** 2026-05-29T18:25:00Z
**Liga IA+H:** Human Dragon (I9) · Guardian (review) · Architect (CCode)

---

## STATUS: FORENSIC_PASS (partial) — FINDING FOR PAPER

---

## CENA MEDIDA

| Campo | Valor |
|-------|-------|
| **Cena** | S16 — ZOOM ON VIDEO |
| **Descrição** | Extreme close-up zoom into video of Elisa |
| **Tipo** | Type B (extreme degradation test) |
| **Vídeo** | `S16_zoom_v2.mp4` |
| **Frames** | 8 (1fps extraction) |
| **Modelo** | Veo 3.1 |
| **Reference** | `elisa_anchor_v2_frame01.png` |

---

## MEDIÇÃO CONTRA ÂNCORA v2

| Metric | Value | Note |
|--------|-------|------|
| **Faces detected** | **3/8** | 37.5% |
| NO_FACE frames | 5/8 | zoom too extreme |
| Mean (detected) | **0.9574** | **HIGHEST IN EXPERIMENT** |
| Min (detected) | 0.9562 | |
| Max (detected) | 0.9591 | |
| Drift (detected) | **0.0028** | **LOWEST IN EXPERIMENT** |

### Per-Frame Breakdown

| Frame | Cosine | Verdict | Note |
|-------|--------|---------|------|
| frame_01 | 0.9562 | FORENSIC_PASS | moderate zoom |
| frame_02 | 0.9570 | FORENSIC_PASS | moderate zoom |
| frame_03 | 0.9591 | FORENSIC_PASS | moderate zoom |
| frame_04 | — | NO_FACE | extreme zoom |
| frame_05 | — | NO_FACE | extreme zoom |
| frame_06 | — | NO_FACE | extreme zoom |
| frame_07 | — | NO_FACE | extreme zoom |
| frame_08 | — | NO_FACE | extreme zoom |

---

## FINDING PARA O PAPER

Esta cena é **o achado metodológico mais importante** do experimento:

### 1. Onde o Método Funciona (frames 01-03)
- Zoom moderado → cosines mais altos do experimento (0.95+)
- Drift quase zero (0.0028)
- Identity verification é **extremamente robusta** quando a face é detectável

### 2. Onde o Método Verga (frames 04-08)
- Zoom extremo → face detector falha
- O método **não inventa dados** — reporta NO_FACE honestamente
- Isto é I14 (Explicit Failure) a funcionar correctamente

### 3. Tese do Paper
> "Reference-anchored generative systems achieve near-forensic identity persistence
> under moderate degradation, but fail explicitly (NO_FACE) rather than silently
> when degradation exceeds detection thresholds. The gap between verification
> and failure is the finding — not a flaw to hide."

---

## VEREDICTO

**S16 (ZOOM ON VIDEO):** ACEITE como finding.

- 3/8 frames medidos: FORENSIC_PASS (0.95+)
- 5/8 frames: NO_FACE (I14 honesto)
- **Não é regeneração necessária** — o resultado É o achado

---

## COMPARAÇÃO COM OUTRAS CENAS

| Cena | Mean | Drift | Faces | Type |
|------|------|-------|-------|------|
| S15 | 0.8690 | 0.1174 | 8/8 | video-proof |
| S20 | 0.7298 | 0.1504 | 8/8 | tribunal v-in-v |
| S21 | 0.8638 | 0.1106 | 8/8 | tribunal v-in-v |
| S14 | 0.8110 | 0.0180 | 8/8 | forensic display |
| **S16** | **0.9574** | **0.0028** | **3/8** | **extreme zoom** |

S16 mostra o padrão: **quanto mais próximo/nítido, maior o cosine** — até ao ponto onde a proximidade destrói a detectabilidade.

---

## INVARIANTES

| Invariante | Status |
|------------|--------|
| I14 (Explicit Failure) | ✅ NO_FACE reportado honestamente |
| I9 (Human Approval) | ✅ Aceite como finding |
| I11 (Permanência) | ✅ Receipt selado |

---

*Liga IA+H · WINDI Publishing House · 29 Mai 2026*
*"The gap is the finding."*
*🐉 OM SHANTI*
