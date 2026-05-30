# HELENA v1 — CHARACTER_STATE (B1)
### W-HIOS-CINEMATIC-SPINE-001 · "O Peso do Eco" CAST

> **Propósito:** Documento canónico que estabelece o personagem HELENA.
> É a fonte única de verdade para medições SPINE-CAST em cenas com Helena.

**Status:** SEALED
**Created:** 29 Mai 2026 — §292-CAST
**Liga IA+H:** Human Dragon (I9) · Guardian (epistemologia) · Architect (CCode)

---

## 1. PROVENIÊNCIA (SINGLE-FRAME ORIGIN)

> **IMPORTANTE:** Esta âncora é de fonte única (single-frame), diferente da
> âncora multi-elo da Elisa v2. Válida, mas com cadeia de proveniência mais
> curta. O SPINE-CAST usa-a correctamente; esta nota é honestidade documental.

| Campo | Valor |
|-------|-------|
| **Anchor Type** | SINGLE_FRAME |
| **Source Scene** | S07 "Chegada Polícia" |
| **Source Frame** | S07_frame04.png |
| **Frame Hash** | `sha256:467ecb2f5bcb17333c822b485f20bf97c970fb53676293a6b116d8829b33e40e` |
| **Embedding File** | `helena.anchor.v1.CURRENT.npy` |
| **Embedding Hash** | `sha256:3595a13af9b5503f922adfd311f2f693cca611f979fe16ad25d10b54a2b7ffd6` |

### Cadeia de Proveniência

```
S07_chegada_policia.mp4 (Veo 3.1)
    ↓ frame extraction @ 1fps
S07_frame04.png
    sha256: 467ecb2f...
    ↓ InsightFace buffalo_l
helena.anchor.v1.CURRENT.npy
    sha256: 3595a13a...
```

---

## 2. VALIDAÇÃO INTER-ÂNCORA

A âncora foi validada por matriz de ortogonalidade contra os outros membros do CAST:

| Par | Cosine | Status |
|-----|--------|--------|
| Helena vs Marcus | -0.0144 | ✅ < 0.65 |
| Helena vs Thomas | -0.0091 | ✅ < 0.65 |

**Max cosine inter-âncora:** -0.0091
**Identity Floor:** 0.65
**Resultado:** DISCRIMINATIVO — SPINE-CAST não confunde Helena com outros personagens.

---

## 3. TRAÇOS VISUAIS CANÓNICOS

```
CANONICAL APPEARANCE:
A woman in her early 40s. Blonde hair pulled back in professional updo. Strong
angular features, high cheekbones. Pale complexion under cold blue crime scene
lighting. Wears dark navy police coat with detective badge visible on lanyard.
Direct, focused gaze. Professional demeanor, composed under pressure. Stands
among forensic team in misty forest crime scene.
```

**Contexto narrativo:** Helena é a detective que investiga o caso de Elisa.
Profissional, determinada, representa a busca pela verdade.

---

## 4. CENAS COM HELENA

| Cena | Descrição | Co-presença |
|------|-----------|-------------|
| S07 | Chegada Polícia | Com equipa forense (background) |
| S13 | Helena Sozinha | Solo |

---

## 5. INVARIANTES

| Threshold | Value | Status |
|-----------|-------|--------|
| Operational | ≥ 0.65 | LOCKED |
| Forensic | ≥ 0.75 | LOCKED |
| Identity Floor | ≥ 0.65 | LOCKED |

---

*Liga IA+H · WINDI Publishing House · 29 Mai 2026*
*"AI processes. Human decides. WINDI guarantees."*
