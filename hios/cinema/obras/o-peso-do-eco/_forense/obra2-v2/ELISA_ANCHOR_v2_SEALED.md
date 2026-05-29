# ELISA ANCHOR v2 — SEALED RECEIPT (CORRECTED)

**Receipt ID:** `WINDI-ELISA-ANCHOR-V2-20260529164500`
**Type:** CHARACTER ANCHOR (B1) — SEALED
**Timestamp:** 2026-05-29T16:45:00Z
**Correction:** 2026-05-29T17:XX:00Z (§267 provenance fix)
**Liga IA+H:** Human Dragon (I9 approval) · Guardian (provenance review) · Architect (CCode)

---

## STATUS: SEALED (CORRECTED)

**Correction Note:** Original receipt incorrectly implied embedding came from DALL-E 3 image.
The canonical embedding comes from **Veo 3.1 video frame**, not DALL-E directly.
DALL-E served as reference design input to Veo, not as embedding source.

---

## PROVENANCE CHAIN (CORRECTED)

```
ELO 1: DALL-E 3 (Reference Design)
    ↓ --ref input to Veo
ELO 2: Veo 3.1 (Video Generation)
    ↓ frame extraction
ELO 3: Frame 01 (Embedding Source)
    ↓ InsightFace buffalo_l
ELO 4: Embedding 512-dim (Canonical Anchor)
```

---

## ELO 1 — REFERENCE DESIGN (DALL-E 3)

| Campo | Valor |
|-------|-------|
| **Papel** | Reference design — visual concept para Veo |
| Ficheiro | `elisa_anchor_v2.png` |
| Resolução | 1024×1024 |
| Modelo | DALL-E 3 (gpt-image-2) |
| SHA-256 | `189a637f3384cc7910bf6098ce476bb10d21b4be6985ee6b3a33a71a206c450b` |
| Link | https://windi-domain.com/hios/elisa-v2/elisa_anchor_v2.png |
| **Nota** | Esta imagem NÃO é a fonte do embedding. Foi input `--ref` para Veo. |

---

## ELO 2 — VIDEO GENERATION (Veo 3.1)

| Campo | Valor |
|-------|-------|
| **Papel** | Gerador do vídeo-âncora S01 |
| Ficheiro | `S01_registo_da_vida_v2.mp4` |
| Resolução | 1280×720 @ 24fps |
| Duração | 8.0s |
| Modelo | **Veo 3.1** (veo-3.1-generate-preview) |
| Reference | `elisa_anchor_v2.png` (DALL-E, Elo 1) |
| SHA-256 | `1faef088a0286fad8906b607dcd23f34d0d018ccee240d39aaa1b8a34f9e94a9` |

---

## ELO 3 — EMBEDDING SOURCE (Frame 01)

| Campo | Valor |
|-------|-------|
| **Papel** | Fonte do embedding canónico — frame escolhido pelo Human Dragon (I9) |
| Ficheiro | `elisa_anchor_v2_frame01.png` |
| Origem | Frame 01 extraído de S01 (Veo 3.1) |
| Resolução | 1280×720 |
| SHA-256 | `094b87bf1a8d1f5670f102d17d6f71aa81c89077cba860f558e5109eda9d0266` |
| Link | https://windi-domain.com/hios/elisa-v2/frame_01.png |

---

## ELO 4 — CANONICAL EMBEDDING (B4)

| Campo | Valor |
|-------|-------|
| **Papel** | Embedding canónico — todas as cenas medem contra este vector |
| Ficheiro | `server-b:~/b4-drift-validator/test_frames/elisa.anchor.v2.CURRENT.npy` |
| Método | InsightFace buffalo_l (ArcFace) |
| Dimensão | 512 |
| Fonte | Frame 01 (Elo 3) — **NÃO DALL-E** |
| **Vector Hash** | `sha256:3fdec0faa85d5bd3603032debfdaf9e8cf023acecfd9c647e4a56bf1c05dfcfb` |

---

## ELEMENTOS NARRATIVOS CONFIRMADOS

- [x] Elisa adulta (early twenties)
- [x] Cabelo loiro longo
- [x] Olhos claros/hazel
- [x] Selfie com telemóvel
- [x] **CARRO ESCURO AO FUNDO** (MacGuffin forense)
- [x] Floresta/clearing
- [x] Luz overcast

---

## INVARIANTES

| Invariante | Status |
|------------|--------|
| I1 (Soberania Humana) | ✅ Frame escolhido pelo Human Dragon |
| I9 (Human Approval) | ✅ Aprovação explícita |
| I11 (Permanência) | ✅ Hashes selados, proveniência corrigida |
| I14 (Falha Explícita) | ✅ Embedding verificado (dim=512) |

---

## §267 CORRECTION RECORD

| Campo | Valor |
|-------|-------|
| Erro original | Recibo sugeria embedding vinha de DALL-E 3 |
| Realidade | Embedding vem de Frame 01 (extraído de Veo 3.1) |
| Tipo | Provenance clarification |
| Severidade | MEDIUM — não afecta o embedding, afecta documentação |
| Corrigido por | Guardian (revisão) + Architect (execução) |
| Aprovado por | Human Dragon (I9) |

---

## PRÓXIMOS PASSOS

1. [x] Âncora v2 selada (proveniência corrigida)
2. [x] Gerar S15 com âncora v2 como `--ref`
3. [x] Medir S15 contra embedding canónico → **FORENSIC_PASS (mean=0.8690)**
4. [x] Human Dragon decide (I9) → ACEITE
5. [ ] Repetir para S20, S21, S14, S16

---

*Liga IA+H · WINDI Publishing House · 29 Mai 2026*
*"AI processes. Human decides. WINDI guarantees."*
*🐉 OM SHANTI*
