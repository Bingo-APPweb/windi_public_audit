# MARCUS v1 — CHARACTER_STATE (B1)
### W-HIOS-CINEMATIC-SPINE-001 · "O Peso do Eco" CAST

> **Propósito:** Documento canónico que estabelece o personagem MARCUS.
> É a fonte única de verdade para medições SPINE-CAST em cenas com Marcus.

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
| **Source Scene** | S09 "Marcus Intocável" |
| **Source Frame** | frame_06.jpg |
| **Frame Hash** | `sha256:ab916efcaefdb4541a710bc499943c80ab5b66032939cd7a5273603fa0a3cdad` |
| **Embedding File** | `marcus.anchor.v1.CURRENT.npy` |
| **Embedding Hash** | `sha256:b1e021f72ac604def5a99e325b9267a1750004ab45d412bb7748ca6a0754218f` |

### Cadeia de Proveniência

```
S09_marcus_intocavel.mp4 (Veo 3.1)
    ↓ frame extraction @ 1fps
frame_06.jpg
    sha256: ab916efc...
    ↓ InsightFace buffalo_l
marcus.anchor.v1.CURRENT.npy
    sha256: b1e021f7...
```

---

## 2. VALIDAÇÃO INTER-ÂNCORA

A âncora foi validada por matriz de ortogonalidade contra os outros membros do CAST:

| Par | Cosine | Status |
|-----|--------|--------|
| Marcus vs Thomas | 0.0307 | ✅ < 0.65 |
| Marcus vs Helena | -0.0144 | ✅ < 0.65 |

**Max cosine inter-âncora:** 0.0307
**Identity Floor:** 0.65
**Resultado:** DISCRIMINATIVO — SPINE-CAST não confunde Marcus com outros personagens.

---

## 3. TRAÇOS VISUAIS CANÓNICOS

```
CANONICAL APPEARANCE:
A man in his late 50s to early 60s. Distinguished silver-grey hair swept back.
Angular face with prominent cheekbones and strong jawline. Deep-set eyes with
calculating gaze. Tall, lean build. Impeccably dressed in dark tailored suit
with white dress shirt, no tie. Silver wristwatch. Carries himself with quiet
authority and controlled menace. Restaurant lighting, warm amber tones.
```

**Contexto narrativo:** Marcus é o antagonista — empresário poderoso, suspeito
no desaparecimento de Elisa. Aparência imaculada contrasta com natureza predatória.

---

## 4. CENAS COM MARCUS

| Cena | Descrição | Co-presença |
|------|-----------|-------------|
| S09 | Marcus Intocável | Solo |
| S21 | Duelo Silencioso | Marcus + Elisa |

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
