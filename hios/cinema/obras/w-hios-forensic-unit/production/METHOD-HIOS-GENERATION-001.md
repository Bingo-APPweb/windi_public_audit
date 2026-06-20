# METHOD-HIOS-GENERATION-001 — Protocolo de Geração Forense

```
doc_type:        method
estatuto:        PRIMEIRO HABITANTE DO ÓRGÃO MÉTODO
órgão:           MÉTODO ("Como meço/gero?")
data:            2026-06-13 · Kempten, Bavaria
versão:          v2.0 · Actualizado 2026-06-17
autor:           Guardian (Human Dragon) + CCode (Strato)
aprovação:       Human Dragon (I9)
invariants:      I9, I11, I14, I19, §268
origem:          ERRATA-002-CONTINUIDADE-PLANO + ACHADO-HELENA-FOREST-20260617
```

> **Órgão MÉTODO responde a:** "Como meço/gero?"
> Este documento é o PRIMEIRO HABITANTE do órgão.

---

## ERRATA v2.0 (17 Jun 2026)

> **§268:** Esta errata ADICIONA conhecimento empírico. Não apaga o contexto original.

### O Que Mudou

A sessão Helena-Forest (17 Jun 2026) testou empiricamente dois métodos de geração:

| Método | Modelo | Endpoint | Resultado |
|--------|--------|----------|-----------|
| Video-Native | gen4_turbo | image_to_video | **INADMISSÍVEL** |
| Joey Method | gen4_image | text_to_image | **ADMISSÍVEL** |

### Dados Empíricos

**Video-Native (gen4_turbo) — mesmo com `referenceImages`:**

| Shot | FORENSE | PASS | BREAK | Runs |
|------|---------|------|-------|------|
| P1 | 0% | 0% | 80% | 5 |
| P5 | 33% | 100% | 67% | 3 |

**Joey Method (gen4_image) — frames estáticos:**

| Shot | FORENSE | PASS | BREAK | Frames |
|------|---------|------|-------|--------|
| P1 | **100%** | **100%** | N/A | 5 |
| P5 | 20% | 80% | N/A | 5 |

### Conclusão

**Para anchor-frames (P1):** Usar Joey Method (gen4_image). Taxa FORENSE: 100%.

**Para shots com movimento:** Video-native é inadmissível para identidade forense. O padrão STABILIZED-WRONG (BREAK em f02→f03) ocorre em 67-80% das runs, mesmo com `referenceImages`.

---

## I. CONTEXTO HISTÓRICO

### Fase 1 (13 Jun 2026) — Problema Original

Revisão visual da cena Gabi-Cozinha revelou:
- 5 frames de P1 não eram um plano contínuo
- Props mudavam entre frames (chávena, telemóvel)
- Geração por 5 imagens independentes sem reference-locking

### Fase 2 (17 Jun 2026) — Teste Video-Native

Tentativa de usar video-native (gen4_turbo) com `referenceImages`:
- Descoberto padrão **STABILIZED-WRONG**: identidade quebra em f02→f03
- O modelo "estabiliza na mentira" — F2F alta, mas Anchor baixo
- `referenceImages` reduz probabilidade mas não elimina BREAK

### Fase 3 (17 Jun 2026) — Joey Method Validado

Teste de gen4_image (frames estáticos):
- P1: 5/5 FORENSE (100%)
- Sem conceito de BREAK (frames independentes)
- **Anchor-frame fiável para autorizar floor**

---

## II. DOIS PROTOCOLOS DE GERAÇÃO

### A) JOEY METHOD — Para Anchor-Frames (RECOMENDADO)

> *"Cada frame é uma fotografia. Não há temporal drift."*

**Usar para:** P1 (anchor-frame), shots estáticos, qualquer frame que precise de ≥0.75 FORENSE.

**API:**
```python
payload = {
    "model": "gen4_image",
    "ratio": "1280:720",
    "referenceImages": [
        {"uri": anchor_base64, "tag": "character"}
    ],
    "promptText": prompt
}

response = requests.post(
    "https://api.dev.runwayml.com/v1/text_to_image",
    headers=headers,
    json=payload
)
```

**Taxa empírica:** 100% FORENSE no P1 (5/5 frames).

**Custo:** ~$0.08 por frame.

### B) VIDEO-NATIVE — Para Continuidade de Props (COM RESSALVAS)

> *"O vídeo garante continuidade de props, mas não de identidade."*

**Usar para:** Shots onde a continuidade de objectos (chávena, telemóvel) é crítica E a identidade pode ser verificada por outros meios.

**API:**
```python
payload = {
    "model": "gen4_turbo",
    "promptImage": anchor_base64,
    "referenceImages": [
        {"uri": anchor_base64, "tag": "character"}
    ],
    "promptText": prompt,
    "duration": 5,
    "ratio": "1280:720"
}

response = requests.post(
    "https://api.dev.runwayml.com/v1/image_to_video",
    headers=headers,
    json=payload
)
```

**ATENÇÃO:** 67-80% das runs mostram BREAK em f02→f03. Não usar para anchor-frames.

**Taxa empírica:** 0% FORENSE fiável no P1.

---

## III. WORKFLOW RECOMENDADO

### Para Cenas com Identidade Forense

```
1. ANCHOR-FRAME via Joey Method (gen4_image)
   - Gerar P1 com referenceImages tag="character"
   - Verificar ≥0.75 FORENSE
   - Este frame AUTORIZA o floor para os restantes

2. SHOTS DE MOVIMENTO — Escolher:

   Opção A: Joey Method (frame-a-frame)
   - Gerar cada keyframe independentemente
   - Sem continuidade de props
   - Identidade fiável (80%+ PASS)

   Opção B: Video-Native (se props críticos)
   - Aceitar risco de BREAK (67-80%)
   - Medir F2F para detectar quebras
   - Re-gerar se BREAK detectado

3. MEDIÇÃO com M1 + M2 + M3

4. SELAR no Ledger após gate I9
```

### Decisão de Método

| Prioridade | Método | Quando |
|------------|--------|--------|
| Identidade ≥0.75 | Joey Method | Anchor-frames, provas forenses |
| Continuidade props | Video-Native | Chávena, telemóvel, objectos |
| Identidade + Props | Híbrido | Anchor via Joey, props via Video |

---

## IV. AS TRÊS MEDIÇÕES — JOEY-F2F-001

| # | Medição | Pergunta | Âncora | Detecta |
|---|---------|----------|--------|---------|
| M1 | **Identidade-âncora** | "Este frame é o personagem?" | Âncora SEALED | Identity drift |
| M2 | **Continuidade-vizinha** | "Frame N coerente com N−1?" | Frame anterior | Temporal breaks |
| M3 | **Reprodutibilidade** | "Frame 005 = Frame 001?" | Primeiro frame | Generation variance |

### M1 — Identidade-Âncora (GATE)

```python
score = cosine_similarity(anchor_embedding, frame_embedding)
# Threshold: SHOT-GRAMMAR-002 (0.55-0.65 conforme tier)
# FORENSE: ≥0.75
```

### M2 — Continuidade-Vizinha (DIAGNÓSTICO)

```python
for i in range(1, len(frames)):
    score = cosine_similarity(frames[i-1].embedding, frames[i].embedding)
    if score < 0.70:
        print("BREAK detectado")  # Identidade trocou
    elif score < 0.85:
        print("JITTER")  # Variância aceitável
    else:
        print("STABLE")  # Continuidade perfeita
```

### M3 — Reprodutibilidade (DIAGNÓSTICO)

```python
score = cosine_similarity(frame_001.embedding, frame_005.embedding)
# Se score < 0.85: alta variância de geração
```

### Agregação

| Medição | Tipo | Threshold | Acção se FAIL |
|---------|------|-----------|---------------|
| M1 | **Gate** | SHOT-GRAMMAR-002 | Re-gerar obrigatório |
| M2 | **Diagnóstico** | 0.70 (BREAK) | Anotar, considerar re-gerar |
| M3 | **Diagnóstico** | 0.85 | Avaliar estabilidade |

---

## V. PADRÃO STABILIZED-WRONG

Descoberto em 17 Jun 2026 durante testes Helena-Forest.

### Definição

O gerador video-native:
1. Usa a referência nos primeiros 1-2 segundos (frames 1-2)
2. **Desacopla-se** da referência em f02→f03
3. Estabiliza num rosto diferente para o resto do vídeo
4. Mantém F2F alta (consistência temporal) após o desacoplamento

### Diagnóstico

```
Frame   Anchor    F2F→next    Estado
f01     0.91      0.96        ✅ Personagem correcto
f02     0.90      0.49        ❌ BREAK LOCALIZADO
f03     0.41      0.96        ❌ Rosto errado, estabilizado
f04     0.42      0.97        ❌ Rosto errado, estabilizado
```

**Assinatura:** F2F alta (>0.90) APÓS o BREAK + Anchor baixo (<0.50).

### Implicação

> *"F2F sozinho pode certificar uma MENTIRA."*

A continuidade temporal NÃO prova identidade. Um gerador que troca de rosto e estabiliza passa o F2F. Só o Anchor apanha que o rosto está errado.

**Promoção Nv3 exige AMBOS os gates:** Anchor ≥ floor E F2F ≥ 0.70.

---

## VI. AXIOMAS DO ÓRGÃO MÉTODO

> *"O SPINE-CAST mede se É a pessoa. Não mede se É o mesmo momento."*

> *"Identidade e continuidade são vectores ortogonais."*

> *"O frame aponta para a âncora no disco. Não a reproduz por prompt."*

> *"Gerar 5 imagens soltas e chamar-lhes plano é o erro que este método corrige."*

> *"A continuidade não se mede depois — constrói-se na geração."*

> *"Um achado de 'impossibilidade' é sempre suspeito até esgotares a configuração."* (Adicionado v2.0)

> *"Antes de selar uma limitação de gerador, esgotar a documentação do gerador."* (Adicionado v2.0)

---

## VII. CHECKLIST PRÉ-GERAÇÃO

Antes de gerar qualquer plano para HIOS:

**Anchor-Frame (P1):**
- [ ] Usar Joey Method (gen4_image)?
- [ ] `referenceImages` com `tag: "character"`?
- [ ] Prompt descritivo (não imperativo)?
- [ ] Target ≥0.75 FORENSE?

**Shots de Movimento:**
- [ ] Decidir: Joey Method ou Video-Native?
- [ ] Se Video-Native: aceitar risco de BREAK (67-80%)?
- [ ] Protocolo de medição inclui M1 + M2 + M3?
- [ ] Estratégia de re-geração se BREAK detectado?

**Geral:**
- [ ] Âncora SEALED disponível?
- [ ] Floor autorizado por anchor-frame ≥0.75?

Se qualquer item falhar → PARAR e corrigir antes de gerar.

---

## VIII. REFERÊNCIA DE API

### Joey Method (gen4_image)

```bash
# Endpoint
POST https://api.dev.runwayml.com/v1/text_to_image

# Headers
Authorization: Bearer {RUNWAY_API_KEY}
X-Runway-Version: 2024-11-06
Content-Type: application/json

# Payload
{
  "model": "gen4_image",
  "ratio": "1280:720",
  "referenceImages": [
    {"uri": "data:image/png;base64,...", "tag": "character"}
  ],
  "promptText": "..."
}
```

### Video-Native (gen4_turbo)

```bash
# Endpoint
POST https://api.dev.runwayml.com/v1/image_to_video

# Payload
{
  "model": "gen4_turbo",
  "promptImage": "data:image/png;base64,...",
  "referenceImages": [
    {"uri": "data:image/png;base64,...", "tag": "character"}
  ],
  "promptText": "...",
  "duration": 5,
  "ratio": "1280:720"
}
```

---

## IX. DADOS EMPÍRICOS (17 Jun 2026)

### Fonte

Sessão Helena-Forest, S08-FOREST_v1, personagem Helena Meyer.

### Video-Native (gen4_turbo)

| Test | Runs | Config | FORENSE | PASS | BREAK |
|------|------|--------|---------|------|-------|
| P1 reliability | 5 | +referenceImages | 0% | 0% | 80% |
| P5 reliability | 3 | +referenceImages | 33% | 100% | 67% |

### Joey Method (gen4_image)

| Test | Runs | Frames | Config | FORENSE | PASS | Nota |
|------|------|--------|--------|---------|------|------|
| P1 joey | 1 | 5 | +referenceImages | **5/5** | **5/5** | min 0.76 |
| P5 joey | 1 | 5 | +referenceImages | 1/5 | 4/5 | **1 frame abaixo floor (0.6145)** |

**ATENÇÃO:** P5 Joey é resultado de 1 run, não taxa. Taxa pendente (5 runs).

### Conclusão Empírica

- Joey Method: **fiável** para anchor-frames (100% FORENSE)
- Video-Native: **não fiável** para identidade (0-33% FORENSE)
- `referenceImages`: **obrigatório** mas não suficiente para video-native

---

*Liga IA+H · WINDI Publishing House · 17 Jun 2026*
*"AI processes. Human decides. WINDI guarantees."*
*Órgão MÉTODO — v2.0 com dados empíricos*

