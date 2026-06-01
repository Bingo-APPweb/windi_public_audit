# ANCHOR UPGRADE PROTOCOL
## Helena v2 + Marcus v2 — Nivel Elisa v2

**Projeto:** WINDI-HIOS Forensic Ledger Files
**Tipo:** Protocolo de Producao
**Origem:** Human Dragon, 01 Jun 2026
**Objetivo:** Elevar ancoras Helena e Marcus ao padrao multi-elo da Elisa v2

---

## PROBLEMA

As ancoras actuais de Helena e Marcus sao **single-frame** (um so elo):
- Extraidas directamente de cenas ja geradas (S07, S09)
- Sem reference design prvio
- Qualidade dependente do que o gerador produziu naquele dia
- Marcus com problemas de iluminacao conhecidos

A ancora Elisa v2 e **multi-elo** (4 elos):
- Reference design intencional (DALL-E 3)
- Video gerado com --ref controlado
- Frame escolhido pelo Human Dragon
- Embedding de frame optimizado

**Resultado:** Elisa v2 atinge FORENSIC (0.86+), Helena/Marcus ficam abaixo.

---

## SOLUCAO

Recriar Helena v2 e Marcus v2 com o mesmo processo de 4 elos da Elisa v2.

---

## PROCESSO POR PERSONAGEM

### HELENA v2

#### ELO 1 — Reference Design (DALL-E 3)

**Prompt DALL-E 3:**
```
A woman in her early 40s. Strong angular features, high cheekbones, pale
complexion. Blonde hair pulled back in professional updo. Direct, focused
gaze with calm intensity. Fair skin, minimal makeup. Professional detective
aesthetic. Head and shoulders portrait, neutral studio lighting, clean
background. Photorealistic, no stylization.
```

**Ficheiro output:** `helena_reference_v2.png`
**Resolucao:** 1024x1024

#### ELO 2 — Video Generation (Veo 3.1)

**Prompt Veo 3.1 (com --ref helena_reference_v2.png):**
```
A woman in her early 40s. Strong angular features, high cheekbones, pale
complexion. Blonde hair pulled back in professional updo. Direct, focused
gaze with calm intensity.

Standing in a modern office, neutral background. She looks directly at the
camera with a professional, composed expression. Soft diffused lighting,
no harsh shadows. Head and shoulders framing, face fully visible and
well-lit. Static shot, minimal movement. Photorealistic, documentary
realism. 8 seconds.
```

**Ficheiro output:** `helena_anchor_scene_v2.mp4`

#### ELO 3 — Frame Extraction

```bash
ffmpeg -i helena_anchor_scene_v2.mp4 -vf fps=1 helena_v2_frame_%02d.png
```

**Human Dragon (I9):** Escolher frame com rosto mais frontal/nitido.
**Ficheiro output:** `helena_anchor_v2_frame01.png`

#### ELO 4 — Embedding

```bash
# No Server B (85.215.131.0)
python embed_face.py helena_anchor_v2_frame01.png helena.anchor.v2.CURRENT.npy
```

**Ficheiro output:** `helena.anchor.v2.CURRENT.npy`

---

### MARCUS v2

#### ELO 1 — Reference Design (DALL-E 3)

**Prompt DALL-E 3:**
```
A distinguished man in his late 50s to early 60s. Silver-grey hair swept
back. Angular face with prominent cheekbones and strong jawline. Deep-set
eyes with intelligent, measured gaze. Tall, lean build implied. Wearing
dark tailored suit with white dress shirt, no tie. Silver wristwatch
visible. Head and shoulders portrait, neutral studio lighting, clean
background. Photorealistic, no stylization.
```

**Ficheiro output:** `marcus_reference_v2.png`
**Resolucao:** 1024x1024

#### ELO 2 — Video Generation (Veo 3.1)

**Prompt Veo 3.1 (com --ref marcus_reference_v2.png):**
```
A distinguished man in his late 50s to early 60s. Silver-grey hair swept
back. Angular face with prominent cheekbones and strong jawline. Deep-set
eyes with intelligent, measured gaze.

Standing in a modern office, neutral background. He looks directly at the
camera with a calm, composed expression. Soft diffused lighting, no harsh
shadows. Head and shoulders framing, face fully visible and well-lit.
Static shot, minimal movement. Photorealistic, documentary realism.
8 seconds.
```

**Ficheiro output:** `marcus_anchor_scene_v2.mp4`

#### ELO 3 — Frame Extraction

```bash
ffmpeg -i marcus_anchor_scene_v2.mp4 -vf fps=1 marcus_v2_frame_%02d.png
```

**Human Dragon (I9):** Escolher frame com rosto mais frontal/nitido.
**Ficheiro output:** `marcus_anchor_v2_frame01.png`

#### ELO 4 — Embedding

```bash
# No Server B (85.215.131.0)
python embed_face.py marcus_anchor_v2_frame01.png marcus.anchor.v2.CURRENT.npy
```

**Ficheiro output:** `marcus.anchor.v2.CURRENT.npy`

---

## CHECKLIST DE EXECUCAO

### Helena v2
- [ ] **ELO 1:** Gerar reference design DALL-E 3
- [ ] **ELO 2:** Gerar video Veo 3.1 com --ref
- [ ] **ELO 3:** Extrair frames, Human Dragon escolhe (I9)
- [ ] **ELO 4:** Criar embedding no Server B
- [ ] **SEAL:** Recibo `WINDI-HELENA-ANCHOR-V2-...`

### Marcus v2
- [ ] **ELO 1:** Gerar reference design DALL-E 3
- [ ] **ELO 2:** Gerar video Veo 3.1 com --ref
- [ ] **ELO 3:** Extrair frames, Human Dragon escolhe (I9)
- [ ] **ELO 4:** Criar embedding no Server B
- [ ] **SEAL:** Recibo `WINDI-MARCUS-ANCHOR-V2-...`

### Validacao
- [ ] **Ortogonalidade:** Helena v2 vs Marcus v2 < 0.20
- [ ] **Self-consistency:** Helena v2 cosine >= 0.85
- [ ] **Self-consistency:** Marcus v2 cosine >= 0.85

---

## APOS UPGRADE

Com ambas as ancoras ao nivel Elisa v2, retomar o teste multi-anchor:

1. Helena v2 + Marcus v2 no mesmo frame
2. Medir atribuicao (binaria) + sangramento (cosine)
3. 3 corridas para padrao estatistico

---

## NOTAS

- **DALL-E 3** esta disponivel via API OpenAI (nao Gemini)
- **Veo 3.1** requer que os filtros de seguranca aceitem o prompt
- Se Veo filtrar, ajustar prompt para cenario mais neutro
- Iluminacao **difusa e neutra** e critica para embedding de qualidade

---

*Liga IA+H · WINDI Publishing House · 01 Jun 2026*
*"AI processes. Human decides. WINDI guarantees."*
