# PROMPTS — GABI COZINHA (P1/P3/P5)
## W-HIOS FORENSIC UNIT · O Peso do Eco · Cena Cozinha

```
doc_type:        generation_prompts
cena:            COZINHA · INTERIOR · MADRUGADA — Gabi & Filhote
identidade:      Gabi Santos (âncora SEALED 4/4 · média 0.86)
generator:       Runway Gen-4 (SPINE-compatible)
protocol:        WINDI-PROTOCOLO-RUN-SPINE-GABI-001-20260613
data:            2026-06-13 · Kempten, Bavaria
operador:        Human Dragon · Jober Mögele Correa
```

---

## Axiomas Anti-Movement Medicine

> "Already in frame. Near-frontal. Camera locked. Light moves, not subject."

> "O sorriso a formar-se vive no corte, não no frame."

---

## Anchor Visual (Base Canónica)

```
33-year-old Brazilian woman, warm olive/morena skin tone, dark wavy
hair falling to shoulders. Intense dark eyes. Symmetrical face.
```

---

## Wardrobe & Props (Cena Cozinha)

| Item | Descrição |
|------|-----------|
| **Roupa** | Dark professional blouse, barefoot |
| **Sapatos** | High heels placed beside counter (not worn) |
| **Cabelo** | Solto, ondulado, natural |
| **Props** | Permanent marker pen behind ear |
| **Telemóvel** | Modified phone, screen glowing |
| **Café** | Artisanal ceramic cup, coffee machine |

---

## P1 — ÂNCORA FRONTAL (72 frames · 3s)

**Função SPINE:** Âncora de identidade. Paga frontalidade de P3 e P5.
**Expressão:** Rosto neutro, cansado. PRÉ-sorriso.
**Tier:** GEOMETRIA (floor 0.65)

### Prompt P1

```
A 33-year-old Brazilian woman with warm olive skin and dark wavy hair
to her shoulders. She is already standing in a kitchen, near-frontal,
watching coffee drip into a ceramic cup. Expression tired but calm.
Eyes forward, neutral. Soft warm kitchen lighting from above.

She is barefoot. High heels placed beside the counter. A pen tucked
behind her ear. Phone on the table nearby, screen glowing faintly.

Camera locked. She is completely still. Only the light breathes.
Intimate, human, photorealistic. 50mm lens. Sharp focus on face.
```

**Checklist:**
- [x] Already in frame
- [x] Near-frontal
- [x] Camera locked
- [x] Light moves, not subject
- [x] No smile (PRÉ-sorriso)
- [x] Barefoot + heels visible

---

## P3 — SORRISO JÁ POUSADO (96 frames · 4s)

**Função SPINE:** Transição viveu no corte. Sorriso já completo.
**Expressão:** Sorriso genuíno, desarmado, humanidade profunda.
**Tier:** EXPOSIÇÃO (floor 0.55)

### Prompt P3

```
A 33-year-old Brazilian woman with warm olive skin and dark wavy hair
to her shoulders. She is already in a kitchen, near-frontal, holding
a ceramic coffee cup. Her expression is a genuine warm smile — full,
already formed, radiating maternal affection. Eyes bright with love.

Soft warm kitchen lighting from above. Subtle glow from phone screen
on table as fill light — not the key, just an accent. The tiredness
from before has vanished.

Camera locked. She is completely still. Only the light breathes.
Intimate, human, photorealistic. 50mm lens. Sharp focus on face.
```

**CRITICAL:** O sorriso JÁ está pousado. Não é transição. Não é "smile forming".
O corte entre P1 e P3 é onde o sorriso se formou — fora do frame.

**Checklist:**
- [x] Already in frame
- [x] Near-frontal
- [x] Camera locked
- [x] Smile ALREADY formed (não "forming")
- [x] Phone glow as FILL, not key
- [x] Eyes bright, maternal affection

---

## P5 — ERGUER TELEMÓVEL (120 frames · 5s)

**Função SPINE:** Frontalidade preservada. Telemóvel sobe ao olhar.
**Expressão:** Ternura, "abraço de urso", despedida amorosa.
**Tier:** GEOMETRIA (floor 0.65)

### Prompt P5

```
A 33-year-old Brazilian woman with warm olive skin and dark wavy hair
to her shoulders. She is already in a kitchen, near-frontal, holding
her phone at eye level. She looks at the phone screen with tender love.
Expression of gentle farewell — "embrace of a bear" warmth.

The phone is raised to her face, not her face lowered to the phone.
Her posture remains upright, head toward lens. Soft warm kitchen
lighting from above. Phone screen adds subtle warm glow to her face.

Camera locked. She is completely still. Only the light breathes.
Intimate, human, photorealistic. 50mm lens. Sharp focus on face.
```

**CRITICAL:** O telemóvel SOBE à altura do olhar. O rosto NÃO desce.
Isto preserva frontalidade (GEOMETRIA protegida pela âncora P1).

**Checklist:**
- [x] Already in frame
- [x] Near-frontal
- [x] Camera locked
- [x] Phone RAISED to face (not face lowered)
- [x] Tender farewell expression
- [x] Same axis as P1 and P3

---

## Sequência de Geração

| Ordem | Plano | Prioridade | Motivo |
|-------|-------|------------|--------|
| 1 | **P1** | ⭐⭐⭐ | Âncora — define identidade da cena |
| 2 | **P3** | ⭐⭐ | Valida transição-no-corte |
| 3 | **P5** | ⭐⭐ | Valida frontalidade preservada |

**Regra:** Medir P1 primeiro. Se FAIL, não gerar P3/P5 (âncora inválida).

---

## Medição (após geração)

```bash
# Extrair frames
ffmpeg -i P1.mp4 -vf fps=24 P1_frames/frame_%02d.png
ffmpeg -i P3.mp4 -vf fps=24 P3_frames/frame_%02d.png
ffmpeg -i P5.mp4 -vf fps=24 P5_frames/frame_%02d.png

# Medir contra âncora-mãe (Run α)
python measure_scene.py --anchor gabi.santos.anchor.v1.png --frames P1_frames/ --run alpha
python measure_scene.py --anchor gabi.santos.anchor.v1.png --frames P3_frames/ --run alpha
python measure_scene.py --anchor gabi.santos.anchor.v1.png --frames P5_frames/ --run alpha

# Medir F2F intra-cena (Run β) — P3 e P5 contra P1
python measure_scene.py --anchor P1_frames/frame_01.png --frames P3_frames/ --run beta
python measure_scene.py --anchor P1_frames/frame_01.png --frames P5_frames/ --run beta
```

---

## Critérios (do protocolo selado)

| Critério | Valor |
|----------|-------|
| Amostragem | Frame a frame (288 total) |
| Comparação | α (âncora-mãe) + β (F2F) |
| Agregação | Mínimo severo (1 frame abaixo = FAIL) |
| Política FAIL | Blocking (reblocar, não regenerar) |

---

*Liga IA+H · WINDI Publishing House · 13 Jun 2026*
*"Already in frame. Near-frontal. Camera locked. Light moves, not subject."*
