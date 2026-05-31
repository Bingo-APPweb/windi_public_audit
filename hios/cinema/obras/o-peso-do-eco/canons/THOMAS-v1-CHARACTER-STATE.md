# THOMAS v1 — CHARACTER_STATE (B1)
### W-HIOS-CINEMATIC-SPINE-001 · "O Peso do Eco" CAST

> **Propósito:** Documento canónico que estabelece o personagem THOMAS.
> É a fonte única de verdade para medições SPINE-CAST em cenas com Thomas.

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
| **Source Scene** | S04 "A Notícia" |
| **Source Frame** | S04_frame06.png |
| **Frame Hash** | `sha256:7fd7aabaa78e9d9e6d3ade3d007e166618d5932c9af7a6a4b6633626887d05c2` |
| **Embedding File** | `thomas.anchor.v1.CURRENT.npy` |
| **Embedding Hash** | `sha256:ca2cc73608aff8b9940f3f0c7471bbb2e2e3e9105adda1a0cb95acdeee42e615` |

### Cadeia de Proveniência

```
S04_a_noticia.mp4 (Veo 3.1)
    ↓ frame extraction @ 1fps
S04_frame06.png
    sha256: 7fd7aaba...
    ↓ InsightFace buffalo_l
thomas.anchor.v1.CURRENT.npy
    sha256: ca2cc736...
```

---

## 2. VALIDAÇÃO INTER-ÂNCORA

A âncora foi validada por matriz de ortogonalidade contra os outros membros do CAST:

| Par | Cosine | Status |
|-----|--------|--------|
| Thomas vs Marcus | 0.0307 | ✅ < 0.65 |
| Thomas vs Helena | -0.0091 | ✅ < 0.65 |

**Max cosine inter-âncora:** 0.0307
**Identity Floor:** 0.65
**Resultado:** DISCRIMINATIVO — SPINE-CAST não confunde Thomas com outros personagens.

---

## 3. TRAÇOS VISUAIS CANÓNICOS

```
CANONICAL APPEARANCE:
A man in his mid-50s. Curly grey-brown hair, somewhat disheveled. Weathered face
with worried expression, visible stress lines. Medium build. Wears dark green
wool cardigan over light blue collared shirt. Seated in leather armchair, warm
domestic lighting from floor lamp. Expression of shock/distress as he receives
difficult news on the phone. Father figure, devastated by loss.
```

**Contexto narrativo:** Thomas é o pai de Elisa — homem comum destruído pela
tragédia. Contraste com Marcus: vulnerabilidade vs poder.

---

## 4. CENAS COM THOMAS

| Cena | Descrição | Co-presença |
|------|-----------|-------------|
| S04 | A Notícia | Solo |
| S12 | Thomas Desesperado | Solo |

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
