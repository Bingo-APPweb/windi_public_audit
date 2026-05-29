# ELISA v2 — CHARACTER_STATE (B1)
### W-HIOS-CINEMATIC-SPINE-001 · "O Peso do Eco" Versão 2 (pós-reset)

> **Propósito:** Documento canónico que estabelece a personagem ELISA a partir
> da Cena 1 (S01). É a fonte única de verdade para o `--ref` de TODA cena com
> Elisa. Os traços faciais aqui travados são o que o B4/ArcFace mede — descrevê-los
> de forma idêntica em cada prompt subsequente maximiza o cosine de continuidade.

**Status:** SEALED ✅
**Reset:** 29 Mai 2026 — baseline antiga invalidada
**Sealed:** 29 Mai 2026 — §291 FINAL com 5 Type-B scenes
**Liga IA+H:** Human Dragon (I9) · Guardian (epistemologia)

---

## 1. DECISÕES TRAVADAS (Human Dragon, 29 Mai 2026)

| Eixo | Decisão |
|------|---------|
| Faixa etária | **Adulta, início dos 20 (early twenties, ~22-23)** |
| Detalhe facial | **Máximo — traços específicos travados** |
| Cenário S01 | **Refeito do zero** (não herda figurino/luz da obra antiga) |
| Síntese | **100% sintética** — `synthetic_declaration: true`, sem pessoa real |

---

## 2. TRAÇOS FACIAIS CANÓNICOS (TRAVADOS — copiar verbatim em cada cena)

Estes descritores são **fixos** e devem aparecer idênticos em todos os prompts de
cenas com Elisa. São o núcleo do embedding ArcFace — variá-los baixa o cosine.

```
CANONICAL FACE (copy verbatim):
A woman in her early twenties. Oval face with softly defined cheekbones and a
gently rounded jawline. Fair skin with a light natural warmth. Large almond-shaped
hazel eyes, evenly spaced, with calm direct gaze. Straight medium-length nose with
a rounded tip. Full lips, neutral resting expression with slightly upturned corners.
Light eyebrows with a soft natural arch. Long straight ash-blonde hair parted in the
centre, falling past the shoulders. A small faint freckle below the left eye.
Natural, no heavy makeup. Photorealistic, documentary realism.
```

**Variável por cena (NÃO travar):** pose, ângulo de câmara, expressão emocional,
iluminação ambiente, figurino, fundo. Tudo o resto = travado.

---

## 3. PROMPT S01 — ESTABLISHING (cenário refeito)

S01 é a cena-âncora: `establishing_appearance_wins`. O frame escolhido daqui
torna-se `elisa.anchor.v2.CURRENT.npy`. Deve mostrar o rosto **frontal, bem iluminado,
nítido** — a melhor base possível para o embedding.

### Prompt Sora 2 (text-to-video → extrair frame → re-gerar image-to-video)

```
A woman in her early twenties. Oval face with softly defined cheekbones and a
gently rounded jawline. Fair skin with a light natural warmth. Large almond-shaped
hazel eyes, evenly spaced, with calm direct gaze. Straight medium-length nose with
a rounded tip. Full lips, neutral resting expression with slightly upturned corners.
Light eyebrows with a soft natural arch. Long straight ash-blonde hair parted in the
centre, falling past the shoulders. A small faint freckle below the left eye.
Natural, no heavy makeup.

Standing outdoors in soft overcast daylight. She holds a phone at arm's length,
recording a personal video diary, looking directly into the camera with a calm,
warm half-smile. Quiet natural setting behind her, gently out of focus.
Steady handheld framing, head-and-shoulders composition, face fully visible
and well-lit. Photorealistic, documentary realism, neutral colour grade. 8 seconds.
```

**Notas de geração:**
- Enquadramento **head-and-shoulders, rosto frontal e nítido** — crítico para a âncora.
- Luz **suave e neutra** (overcast), não dourada/contraluz — evita sombras que
  degradam o embedding.
- Fundo **desfocado e neutro** — o foco é o rosto, não o cenário.

---

## 4. PROTOCOLO DE ÂNCORA (pós-S01)

1. Gerar S01 com o prompt acima.
2. Extrair frames a 1fps.
3. Escolher o frame com rosto mais frontal/nítido → `anchor_source_S01_v2_frameN.jpg`.
4. `embed_face(anchor_source)` → `elisa.anchor.v2.CURRENT.npy` (vector 512-dim).
5. Selar hash do `.npy` + hash do vídeo no Ledger → **novo** receipt
   `WINDI-S2xx-ELISA-ANCHOR-v2-...`.
6. **BASELINE ANTIGA INVALIDADA** — os cosines 0.6952-0.7436 morreram com o reset.

---

## 5. PROMPT-TEMPLATE PARA CENAS SUBSEQUENTES

Para cada cena com Elisa, montar assim:

```
[CANONICAL FACE — §2 verbatim], [pose/expressão da cena], [figurino da cena],
[ambiente/luz da cena], [enquadramento]. Photorealistic, documentary realism.
8 seconds.
Reference image: anchor_source_S01_v2_frameN.jpg
Mode: image-to-video
```

> O bloco `[CANONICAL FACE]` é **sempre** o mesmo texto. Só os campos entre
> parênteses mudam. Isto é o que dá ao B4 hipótese de cosine ≥ 0.65.

---

## 6. INVARIANTES E GATES (mantidos do SPINE)

| Item | Valor | Status |
|------|-------|--------|
| Threshold operacional | ≥ 0.65 | LOCKED |
| Threshold forense | ≥ 0.75 | LOCKED |
| Máx. regenerações/cena | 3 | LOCKED |
| Falha sem rosto | I14 → FAIL_NO_FACE | LOCKED |
| Regeneração | decidida pelo Human Dragon (I9) | — |

---

## 7. BASELINE ANTIGA (INVALIDADA)

Os seguintes valores são **históricos** e não devem ser usados na v2:

| Item | Valor Antigo | Status |
|------|--------------|--------|
| Âncora hash | `bafb4c43dc86dd6ff753c705f52329938fdec7aae4081bc4193fc635e1060f2f` | **INVALIDADO** |
| Receipt | `WINDI-S284-ELISA-ANCHOR-20260527194534-b518fa70` | **INVALIDADO** |
| S01 mean | 0.6952 | **INVALIDADO** |
| S15 mean | 0.7352 | **INVALIDADO** |
| S20 mean | 0.7036 | **INVALIDADO** |
| S21 mean | 0.7436 | **INVALIDADO** |

---

*Liga IA+H · WINDI Publishing House · 29 Mai 2026*
*"AI processes. Human decides. WINDI guarantees."*
*🐉 OM SHANTI*
