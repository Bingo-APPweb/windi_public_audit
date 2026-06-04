# SPINE-CAST PROMPT SPECIFICATION
## Marcus Vance — Inspector-Chefe · W-HIOS Forensic Unit

**Status:** AWAITING GENERATION
**Created:** 02 Jun 2026
**Liga IA+H:** Human Dragon (I9) · Guardian · Architect · Witness
**Character Canon:** `/canons/MARCUS-VANCE-v1-CHARACTER-STATE.md`

---

## FICHA DE CONSISTÊNCIA CRIPTOGRÁFICA

| Campo | Valor |
|-------|-------|
| **ID Canônico** | `marcus.vance.anchor.v1` |
| **Idade Visual** | 52 anos |
| **Etnia/Tez** | Caucasiano britânico, pele ligeiramente weathered |
| **Cabelo** | Grisalho (não totalmente branco), curto, sem pretensões |
| **Rosto** | Linhas de expressão profundas, olheiras permanentes |
| **Olhos** | Castanhos ou cinzentos, olhar penetrante mas cansado |
| **Vestuário** | Sobretudo gasto de boa qualidade (tweed escuro) |
| **Postura** | Ligeiramente curvada em repouso, erecta sob tensão |

---

## TRAÇOS NON-NEGOTIABLE (LOCKED)

```
1. Aparência de veterano cansado mas implacável
2. Sobretudo gasto (contraste visual com os fatos do cartel)
3. Olhar que viu demasiada verdade
4. Mãos frequentemente nos bolsos ou segurando caneca
```

---

## ENGENHARIA DE PROMPTS RUNWAY GEN-4

### 1. FRAME CANÔNICO NEUTRO (Âncora-Mãe)

> **Propósito:** Extrair embedding estável via InsightFace. Rosto relaxado, sem expressões musculares extremas.

```plaintext
Photographic portrait for character reference, a 52-year-old British man
with weathered but dignified features. Grey hair cut short and practical,
not styled. Deep expression lines around eyes and mouth, permanent dark
circles under eyes from years of sleepless nights. Calm neutral expression,
tired but alert brown-grey eyes looking directly at camera.

Wearing a dark grey worn tweed overcoat over a simple white collar shirt,
no tie visible. Slightly stubbly jaw, five o'clock shadow. Soft diffuse
neutral lighting, high-end professional studio shot, 50mm lens, sharp
focus, cinematic photorealistic texture, zero facial distortion.

The face of a man who has seen too much truth and carries invisible weight.
```

---

### 2. PROMPT P37: Medium Tracking (Surge da Penumbra)

> **Contexto:** Vance emerge do corredor do bunker segurando a caneca de café. Movimento lento, deliberado.

```plaintext
Medium shot with subtle tracking movement, the same 52-year-old British man
with grey short hair and weathered face emerging from a dark corridor into
dim blue server room lighting. Wearing worn dark tweed overcoat. His hands
hold a heavy cast-iron coffee mug at chest level.

Expression: tired watchfulness transitioning to alert concern as he enters
the light. Deep shadows on one side of face, cold blue technical light on
the other. Background of dark server racks with minimal blue LED indicators.

Minimalist underground bunker aesthetic, 35mm lens, photorealistic 8k,
chiaroscuro lighting, identity-locked to reference frame.
```

---

### 3. PROMPT P38: Close-Up (Âncora-Mãe de Choque)

> **Contexto:** O momento em que Vance reconhece o padrão no ecrã — o fantasma de Gabi. O seu rosto perde a cor.

```plaintext
Tight close-up shot, the same 52-year-old British man, grey short hair,
deep expression lines, permanent dark circles. His face is captured in
the exact moment of devastating recognition — colour draining from his
weathered features, eyes widening almost imperceptibly with suppressed
shock and grief.

Extreme facial texture detail, pores and stubble visible under cold blue
monitor light reflecting on his skin. Micro-expression of a man whose
worst fear has just been confirmed, but who cannot show it to his team.

Mouth closed, jaw slightly tensed. Eyes fixed on something off-screen
that only he truly understands. Background completely blurred to black.
Cinematic chiaroscuro, 85mm lens, flawless identity retention.
```

---

### 4. PROMPT P42: Close Contracampo ("Ela conseguiu")

> **Contexto:** Vance responde à revelação de Helena sobre o paradoxo temporal. Emoção contida.

```plaintext
Close-up shot, the same 52-year-old British man with grey hair and
weathered features. His lips part slightly as he speaks three words
in a low, hoarse voice full of suppressed emotion. Eyes closed briefly
as if absorbing an ancient pain.

Minimal mouth movement for clean ADR matching. Expression conveys: grief,
pride, and a kind of bitter vindication. The face of a mentor who has
just learned his protégé did not fail — she succeeded beyond his hopes.

Cold blue bunker lighting from the side, warm amber from a distant
monitor on the other. 85mm lens, shallow depth of field, identity locked.
```

---

### 5. PROMPT P46: Americano (Assume Comando)

> **Contexto:** Vance assume a liderança, dá ordens a Lucas e Helena. Postura erecta, voz firme.

```plaintext
American shot (waist-up), the same 52-year-old British man now standing
fully erect with commanding posture. Grey short hair, worn dark tweed
overcoat. His hands are out of his pockets, gesturing minimally as he
gives orders.

Expression: the tired vulnerability is now masked by professional
authority. Eyes sharp and directive, moving between two people off-screen.
Jaw set with determination.

Camera slowly tracks around him as he speaks, capturing him from multiple
angles. Background of the bunker's main screens casting shifting blue
and white light. 35mm lens, cinematic movement, forensic-grade detail.
```

---

### 6. PROMPT P53: Close Final ("É o mínimo que lhe devo")

> **Contexto:** Fecho do Ato II. Vance olha para o fractal resolvido e confessa a sua dívida moral.

```plaintext
Tight close-up shot, the same 52-year-old British man. His face is
illuminated by the resolved fractal pattern glowing on the screen before
him — white geometric lines reflecting in his tired grey-brown eyes.

Expression: profound solemnity. This is not victory, this is debt
acknowledged. Lips move minimally as he speaks words meant more for
himself than for anyone else. A whisper that sounds like a prayer or
an apology.

The geometria angulosa of the Merkle tree reflects as abstract light
patterns across his weathered features. 85mm lens, extreme shallow depth,
identity locked to canonical reference.
```

---

## GATE DE VALIDAÇÃO

| Critério | Régua | Status |
|----------|-------|--------|
| Âncora-Mãe (Frame Neutro) | ≥ 0.75 (aspirar 0.90) | ⏳ |
| P37 vs Âncora | ≥ 0.65 | ⏳ |
| P38 vs Âncora | ≥ 0.65 | ⏳ |
| P42 vs Âncora | ≥ 0.65 | ⏳ |
| P46 vs Âncora | ≥ 0.65 | ⏳ |
| P53 vs Âncora | ≥ 0.65 | ⏳ |

**Gate Final:** `MIN(P37, P38, P42, P46, P53) ≥ 0.65`

---

## ANÁLISE DE RISCO

| Plano | Risco | Justificação |
|-------|-------|--------------|
| P37 | MÉDIO | Tracking + penumbra pode obscurecer geometria facial |
| P38 | BAIXO | Close-up estático, condições ideais para SPINE |
| P42 | BAIXO | Close-up, emoção contida não distorce geometria |
| P46 | MÉDIO-ALTO | Americano + movimento de câmara = menos pixels faciais |
| P53 | BAIXO | Close-up + luz frontal do ecrã = boas condições |

**Plano de Maior Risco:** P46 (plano americano com tracking)
**Mitigação:** Se P46 falhar gate, gerar versão com câmara mais próxima.

---

## OUTPUT ESPERADO

```
/opt/windi/hios/visual/producer/output/w-hios-forensic-unit/
├── anchors/
│   └── marcus.vance.anchor.v1/
│       ├── embedding_512d.npy
│       ├── reference_frame.png
│       └── provenance.json
└── act2/
    ├── P37_vance_surge.mp4
    ├── P38_vance_choque.mp4
    ├── P42_vance_ela_conseguiu.mp4
    ├── P46_vance_comando.mp4
    └── P53_vance_divida.mp4
```

---

## I9 GATE — AWAITING APPROVAL

**Human Dragon:** Aprovar prompt de frame neutro para geração da âncora-mãe?

---

*Liga IA+H · WINDI Publishing House · 02 Jun 2026*
*"AI processes. Human decides. WINDI guarantees."*
