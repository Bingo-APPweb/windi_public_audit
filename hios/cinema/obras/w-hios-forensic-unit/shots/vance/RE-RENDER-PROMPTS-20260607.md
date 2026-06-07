# RE-RENDER PROMPTS — Vance v2 Corrections

**Data:** 07 Jun 2026
**Auditor:** Human Dragon
**Revisão:** Guardian (GPT) + CCode (Opus 4.5)
**Gerador:** Runway Gen-4
**Anchor:** `marcus.vance.anchor.canonical.png`

---

## SELO CONSTITUCIONAL — Ficção Universal / Forense Jurisdicionada

> **"Universal na ficção ≠ ambíguo na forense."**

| Domínio | Regra |
|---------|-------|
| **Cenário diegético** | Qualquer-cidade, qualquer-lugar. História universal. |
| **Pipeline SPINE-CAST** | Rigor de sempre. Threshold 0.65/0.75. Sem relaxamento. |

A universalidade é propriedade do **cenário narrativo**, não do **pipeline de validação**.
Skyline genérica é escolha estética, não permissão para relaxar SPINE.

**Decisão HD:** 07 Jun 2026 · OM SHANTI 🐉

---

## Características Canónicas do Vance (OBRIGATÓRIO)

```
- Idade: 50s
- Cabelo: Salt-and-pepper (cinza-prateado), comprido até ombros, rabo de cavalo solto
- Barba: Curta, grisalha, bem aparada
- Rosto: Vincado, weathered, olhos azul-cinza penetrantes
- Cicatriz: Pequena marca vermelha na testa (lado esquerdo)
- Vestuário: Casaco de lã escuro, camisa clara, pin prateado na lapela
- Expressão: Contemplativa, peso emocional, nunca sorrindo
```

---

## PROMPT 1: S06-01 — "Vance Revealed by Light"

**Problema original:** SPINE fail (0.49) — identity drift nos frames finais
**Causa:** Iluminação contrastada + "emerges from shadow" interpretado como movimento
**Fix Guardian:** "Light moves, not Vance" — remove tensão semântica

### Prompt Corrigido (v2)

```
Marcus Vance, 50s man with salt-pepper hair in loose ponytail, short grey beard,
weathered face with small red mark on left forehead, blue-grey eyes.

Dark wool coat with silver pin on lapel. White shirt underneath.

SCENE: Vance stands completely still as soft light gradually reveals his face.
Camera locked on face throughout. LIGHT MOVES, NOT VANCE.
Lighting transitions slowly from rim light to soft frontal fill.
Vance does not turn, does not move — only the illumination changes.

CRITICAL FOR SPINE: Face always 70%+ visible. No extreme shadows.
Eyes visible throughout. Maintain consistent facial features entire shot.

Cinematic, 4K, 24fps, shallow depth of field.
Mood: Contemplative revelation, weight of knowledge emerging into clarity.
```

### Notas Técnicas
- Vance estático, luz move
- Evitar interpretação de "emergência" como rotação facial
- Transição de luz suave, não abrupta

---

## PROMPT 2: S11-01 — "Vance Enters Confrontation"

**Problema original:** SPINE fail (0.66 — borderline) — identity drift em frames 3-5
**Causa:** Iluminação "cirúrgica" demasiado dura
**Fix:** Luz difusa, não harsh direct sun

### Prompt Corrigido (v2)

```
Marcus Vance, 50s man with salt-pepper hair in loose ponytail, short grey beard,
weathered face with small red mark on left forehead, blue-grey eyes.

Dark wool coat with silver pin on lapel.

SCENE: Vance enters a tense confrontation space. Modern rooftop terrace, daylight.
Camera follows him entering frame from left, settling on medium close-up.
He surveys the scene with controlled intensity.

LIGHTING: Bright daylight but DIFFUSED — overcast sky, not harsh direct sun.
Avoid harsh shadows on face. Soft fill from environment.

CRITICAL FOR SPINE: Face must remain consistently lit throughout.
No dramatic shadow changes. Maintain 80%+ face visibility at all times.

Cinematic, 4K, 24fps.
Mood: Controlled tension, predator entering territory.
Location: Modern rooftop terrace, generic European city — no specific landmarks.
```

### Notas Técnicas
- Luz difusa (dia nublado), não "cirúrgica"
- Sem landmarks específicos (doutrina universal)
- Rosto consistentemente iluminado

---

## PROMPT 3: S14-01 — "Vance at Window, Any City"

**Problema original:** Skyline NYC (jurisdição americana)
**SPINE:** OK (0.91 FORENSIC) — manter estilo visual
**Decisão HD:** História universal — skyline genérica intencional

### Prompt Corrigido (v2)

```
Marcus Vance, 50s man with salt-pepper hair in loose ponytail, short grey beard,
weathered face with small red mark on left forehead, blue-grey eyes.

Dark wool coat with silver pin on lapel.

SCENE: Vance stands at floor-to-ceiling window, looking out pensively.
Camera captures him in profile/three-quarter view against the cityscape.

VIEW THROUGH WINDOW: Generic modern city skyline at dusk.
Deliberately non-specific — NO recognizable landmarks.
Modern glass and steel buildings, could be any major city.
NOT American art-deco. No Empire State silhouettes. No obvious US markers.
Cool blue tones, STRONG SOFT FOCUS on skyline.

LIGHTING: Golden hour, warm light on Vance's face from window.
Cool blue tones on the city outside. Vance sharp, skyline deliberately blurred.

Cinematic, 4K, 24fps, shallow depth of field — face sharp, city atmospheric.
Mood: Solitary reflection, weight of responsibility. Any-city, anywhere.
```

### Notas Técnicas
- Skyline em soft focus forte = "lê" como qualquer cidade
- Guard-rail negativo: NOT American art-deco (evitar recorrência)
- Sem Frankfurt, sem landmarks — escolha estética, não remendo
- SPINE já OK, manter consistência

---

## Checklist Pré-Geração

```
[ ] Upload anchor: marcus.vance.anchor.canonical.png
[ ] Configurar Runway Gen-4 (não Gen-3)
[ ] Duração: 5 segundos cada
[ ] Resolução: 1280x720 ou 1920x1080
[ ] Gerar S06-01 primeiro (fix semântico)
[ ] Gerar S11-01 segundo (fix iluminação)
[ ] Gerar S14-01 terceiro (fix skyline)
[ ] Validar SPINE com measure_scene.py após cada geração
[ ] Threshold: ≥0.65 operacional, ≥0.75 forense
```

---

## Validação Pós-Geração (OBRIGATÓRIO)

> **"A number without a measurement run is not a number."**

```bash
# Após gerar cada vídeo — NÃO marcar como resolvido antes disto:
cd /opt/windi/hios/cinema/obras/w-hios-forensic-unit
python measure_scene.py --video shots/vance/S06-01_v3.mp4 --anchor anchors/marcus.vance.anchor.canonical.png
python measure_scene.py --video shots/vance/S11-01_v3.mp4 --anchor anchors/marcus.vance.anchor.canonical.png
python measure_scene.py --video shots/vance/S14-01_v3.mp4 --anchor anchors/marcus.vance.anchor.canonical.png
```

**Critério de sucesso:**
- S06-01: ≥0.65 (era 0.49) — threshold operacional padrão
- S11-01: ≥0.70 (era 0.66) — **threshold de aceitação elevado** (ver nota abaixo)
- S14-01: ≥0.75 (manter FORENSIC, era 0.91)

---

## NOTA CONSTITUCIONAL — Threshold Operacional vs Threshold de Aceitação

> **"O threshold operacional é do sistema; o threshold de aceitação pode ser do shot."**

| Conceito | Valor | Função |
|----------|-------|--------|
| **Threshold Operacional** | 0.65 | Chão canónico do sistema. Não muda. |
| **Threshold de Aceitação** | Variável | Decisão HD por shot, pode ser > operacional |

**S11-01 — Justificação para ≥0.70:**
- Shot adversarial de alta tensão dramática (Cena 11 = confronto)
- v2 a 0.66 passou o chão por uma unha — margem insuficiente
- 0.70 dá margem de 4 centésimas acima do rejeitado
- NÃO é 0.75 porque FORENSIC é patamar de qualidade, não exigência narrativa

**Precedente:** Cenas futuras de alta tensão herdam este raciocínio sem nova deliberação.

**Decisão HD:** 07 Jun 2026 · Recomendação Guardian aceite

---

## Histórico de Revisões

| Versão | Data | Autor | Alteração |
|--------|------|-------|-----------|
| v1 | 07 Jun 10:45 | CCode | Prompts iniciais |
| v2 | 07 Jun 11:15 | Guardian + CCode | Fix S06-01 semântico, doutrina universal, remoção Frankfurt |
| v3 | 07 Jun 11:14 | CCode | Prompts curtos (fix INTERNAL.BAD_OUTPUT) |
| v4 | 07 Jun 11:30 | Guardian + CCode | Anti-movement medicine (already in frame, near-frontal) |
| **SEAL** | 07 Jun 11:35 | HD + Guardian | **3/3 APROVADOS** — ver nota obsolescência abaixo |

---

## NOTA DE OBSOLESCÊNCIA — Guard-Rail "NOT American Art-Deco"

> **Guard-rail tornou-se obsoleto sob doutrina universal (decisão HD 07 Jun 2026).**

| Guard-Rail Original | Doutrina Antiga | Doutrina Nova |
|---------------------|-----------------|---------------|
| "NOT American art-deco" | Frankfurt obrigatório | Universal (any-city) |
| "No Empire State silhouettes" | Jurisdição alemã | Não-reconhecível |

**S14-01_v4** contém silhueta art-deco em soft focus. Sob doutrina antiga, seria violação.
Sob **doutrina universal**, exigência reduz-se a: **não-reconhecível como cidade real específica**.

**Avaliação HD:** Skyline em soft focus lê como "cidade genérica grande" — **ACEITE**.

**Critério vigente:** Universal na ficção = qualquer-lugar. SPINE rigoroso = 0.8868 FORENSIC.

*§268 aplicado: corrigir o entendimento sem reescrever a história.*

---

## RESULTADO FINAL — 3/3 SELADOS

| Shot | Versão | Score | Threshold | Margin | Status |
|------|--------|-------|-----------|--------|--------|
| S06-01 | v3 | 0.7995 | ≥0.65 | +0.15 | ✅ **SELADO** |
| S11-01 | v4 | 0.8312 | ≥0.70 | +0.13 | ✅ **SELADO** |
| S14-01 | v4 | 0.8868 | ≥0.75 | +0.14 | ✅ **SELADO** |

**Perfil saudável confirmado em todos:** Degradação suave que estabiliza.

---

*Liga IA+H · W-HIOS FORENSIC UNIT · 07 Jun 2026*
*"AI processes. Human decides. WINDI guarantees."*
*OM SHANTI 🐉*
