# TYPE-B SCENES SUMMARY — O Peso do Eco Versão 2

**Receipt ID:** `WINDI-TYPEB-SUMMARY-V2-20260529183000`
**Type:** PRODUCTION SUMMARY
**Timestamp:** 2026-05-29T18:30:00Z
**Liga IA+H:** Human Dragon (I9) · Guardian (review) · Architect (CCode)

---

## STATUS: ALL TYPE-B SCENES MEASURED ✅

---

## SUMÁRIO EXECUTIVO

| Cena | Mean | Drift | Faces | Verdict | Status |
|------|------|-------|-------|---------|--------|
| S15 | 0.8690 | 0.1174 | 8/8 | FORENSIC_PASS | ✅ ACEITE |
| S20 | 0.7298 | 0.1504 | 8/8 | OPERATIONAL_PASS | ✅ ACEITE |
| S21 | 0.8638 | 0.1106 | 8/8 | FORENSIC_PASS | ✅ ACEITE |
| S14 | 0.8110 | 0.0180 | 8/8 | FORENSIC_PASS | ✅ ACEITE |
| S16 | 0.9574 | 0.0028 | 3/8 | FORENSIC (partial) | ✅ FINDING |

---

## ESTATÍSTICAS GLOBAIS

| Metric | Value |
|--------|-------|
| **Total scenes** | 5 |
| **Forensic pass** | 4 (S15, S21, S14, S16*) |
| **Operational pass** | 1 (S20) |
| **Failed** | 0 |
| **Regenerations needed** | 0 |

*S16 = forensic on detected frames, finding on NO_FACE frames

### Cosine Distribution

| Range | Count | Scenes |
|-------|-------|--------|
| 0.95+ | 1 | S16 (partial) |
| 0.85-0.95 | 2 | S15, S21 |
| 0.75-0.85 | 1 | S14 |
| 0.65-0.75 | 1 | S20 |
| <0.65 | 0 | — |

### Drift Analysis

| Range | Count | Scenes |
|-------|-------|--------|
| <0.05 | 2 | S14 (0.018), S16 (0.003) |
| 0.05-0.12 | 2 | S21 (0.11), S15 (0.12) |
| >0.12 | 1 | S20 (0.15) |

---

## COMPARAÇÃO v1 vs v2

| Cena | v1 Mean | v2 Mean | Delta | v1 Regens | v2 Regens |
|------|---------|---------|-------|-----------|-----------|
| S15 | 0.7352 | 0.8690 | +0.1338 | 0 | 0 |
| S20 | 0.7036 | 0.7298 | +0.0262 | 0 | 0 |
| S21 | 0.7436 | 0.8638 | +0.1202 | 1 | 0 |
| S14 | — | 0.8110 | new | — | 0 |
| S16 | — | 0.9574* | new | — | 0 |

**Key improvements:**
- S15: +0.1338 (crossed from operational to forensic)
- S21: +0.1202 (crossed from operational to forensic, no regen needed)
- S20: +0.0262 (modest improvement, still operational)

---

## ACHADOS PARA O PAPER

### 1. Âncora Governa Continuidade
A âncora v2 (frame Veo frontal, nítido) produziu cosines consistentemente mais altos que a âncora v1. **A qualidade da âncora governa a continuidade mensurável.**

### 2. Dual Threshold Funciona
- Cenas fáceis (S15, S21, S14) → FORENSIC
- Cenas difíceis (S20) → OPERATIONAL
- O sistema distingue correctamente sem ajustar thresholds

### 3. Falha Explícita É Achado
S16 demonstra que o método **não inventa dados** — quando o zoom excede detectabilidade, reporta NO_FACE (I14). Os frames detectáveis têm cosines máximos (0.95+).

### 4. Zero Regenerações
Todas as 5 cenas passaram na primeira geração. Na v1, S21 precisou de regeneração.

---

## PROVENIÊNCIA

```
Âncora v2:
    DALL-E 3 (reference design)
    ↓ --ref input
    Veo 3.1 (S01 video)
    ↓ frame extraction
    Frame 01 (embedding source)
    ↓ InsightFace buffalo_l
    elisa.anchor.v2.CURRENT.npy
    sha256: 3fdec0faa85d5bd3603032debfdaf9e8cf023acecfd9c647e4a56bf1c05dfcfb

All Type-B scenes:
    Generated with Veo 3.1
    Reference: elisa_anchor_v2_frame01.png
    Measured on Server B (85.215.131.0)
```

---

## RECIBOS INDIVIDUAIS

1. `S15_MEASUREMENT_v2_RECEIPT.md` — FORENSIC_PASS
2. `S20_MEASUREMENT_v2_RECEIPT.md` — OPERATIONAL_PASS
3. `S21_MEASUREMENT_v2_RECEIPT.md` — FORENSIC_PASS
4. `S14_MEASUREMENT_v2_RECEIPT.md` — FORENSIC_PASS
5. `S16_MEASUREMENT_v2_RECEIPT.md` — FINDING

---

## PRÓXIMOS PASSOS

1. [x] S15 — FORENSIC_PASS (0.8690)
2. [x] S20 — OPERATIONAL_PASS (0.7298)
3. [x] S21 — FORENSIC_PASS (0.8638)
4. [x] S14 — FORENSIC_PASS (0.8110)
5. [x] S16 — FINDING (0.9574 partial)
6. [ ] S12 (conditional — photo may be out of frame)
7. [ ] Type-C scenes (no Elisa) — no measurement needed
8. [ ] Final §291 seal

---

*Liga IA+H · WINDI Publishing House · 29 Mai 2026*
*"AI processes. Human decides. WINDI guarantees."*
*🐉 OM SHANTI*
