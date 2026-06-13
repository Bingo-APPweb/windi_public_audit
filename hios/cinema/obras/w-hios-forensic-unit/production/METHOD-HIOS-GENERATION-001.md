# METHOD-HIOS-GENERATION-001 — Protocolo de Geração Video-Native

```
doc_type:        method
estatuto:        PRIMEIRO HABITANTE DO ÓRGÃO MÉTODO
órgão:           MÉTODO ("Como meço/gero?")
data:            2026-06-13 · Kempten, Bavaria
autor:           Guardian (Human Dragon) + CCode (Strato)
aprovação:       Human Dragon (I9)
invariants:      I9, I11, I14, I19, §268
origem:          ERRATA-002-CONTINUIDADE-PLANO (correcção que gerou este método)
```

> **Órgão MÉTODO responde a:** "Como meço/gero?"
> Este documento é o PRIMEIRO HABITANTE do órgão.

---

## I. CONTEXTO — O QUE FALHOU

Em 13 Jun 2026, revisão visual frame-a-frame da cena Gabi-Cozinha revelou:
- 5 frames de P1 não eram um plano contínuo
- Chávena mudava de cor, saltos trocavam de lado, telemóvel saltava
- Geração por 5 imagens independentes, não video-native

**Causa raiz:** Usámos Runway Gen-4 Image (5 prompts soltos) em vez de Runway Gen-4 Video com reference-locking.

**Documentação que já existia e não aplicámos:**
- MEMORY-LOOP-SOVEREIGN.md §V: "1. Gerar vídeo via Runway API"
- MEMORY-LOOP-20260612 R3: "Continuidade de props é eixo invisível ao SPINE"

---

## II. PROTOCOLO DE GERAÇÃO — VIDEO-NATIVE + REFERENCE-LOCKING

### Princípio MAPA-não-FONTE

> *"O frame aponta para a âncora no disco. Não a reproduz por prompt."*

O frame gerado não "é" o personagem por sorte do prompt — ele **referencia** a âncora SEALED como `image_1`, e o disco (a âncora selada) testemunha.

### Três Referências Obrigatórias

| Slot | Conteúdo | Função |
|------|----------|--------|
| `image_1` | Âncora SEALED do personagem | Identity lock |
| `image_2` | Referência de cena/cenário | Scene anchoring |
| `image_3` | (opcional) Prop crítico | Object continuity |

### Gramática de Prompt (Runway Gen-4)

**OBRIGATÓRIO:**
```
- Descritivo, não imperativo ("She stands" não "Make her stand")
- Sujeito genérico para movimento ("The subject turns" não "Gabi turns")
- Sem elementos conversacionais ("Can you..." proibido)
- Descrever como elementos aparecem, não comandar adição
```

**EXEMPLO CORRECTO:**
```
A 33-year-old Brazilian woman with warm olive skin stands in a kitchen,
near-frontal. She watches coffee drip into a ceramic cup. Expression
tired but calm. Eyes forward. Camera locked. Only the light breathes.
```

### Workflow Video-Native

```
1. GERAR VÍDEO via Runway Gen-4 Video (não Image)
   - image_1 = âncora SEALED do personagem
   - image_2 = referência de cenário
   - Prompt descritivo (gramática acima)

2. EXTRAIR KEYFRAMES do vídeo
   - ffmpeg -i video.mp4 -vf "select='eq(n\,0)+eq(n\,24)+eq(n\,48)+eq(n\,72)+eq(n\,96)'" -vsync 0 frame_%02d.png
   - Keyframes são o MESMO MOMENTO (continuidade garantida pelo generator)

3. MEDIR com as 3 medições (ver §III)

4. SELAR no Ledger após gate I9
```

---

## III. AS TRÊS MEDIÇÕES — JOEY-F2F-001 COMPLETO

| # | Medição | Pergunta | Âncora | Detecta |
|---|---------|----------|--------|---------|
| M1 | **Identidade-âncora** | "Este frame é o personagem?" | Âncora SEALED | Identity drift |
| M2 | **Continuidade-vizinha** | "Frame N coerente com N−1?" | Frame anterior | Temporal breaks |
| M3 | **Reprodutibilidade** | "Frame 005 = Frame 001?" | Primeiro frame | Generation variance |

### M1 — Identidade-Âncora (JÁ USÁVAMOS)

```python
# Cada frame vs âncora SEALED
score = cosine_similarity(anchor_embedding, frame_embedding)
# Threshold: SHOT-GRAMMAR-002 (0.55-0.65 conforme tier)
```

### M2 — Continuidade-Vizinha (FALTAVA)

```python
# Frame N vs Frame N-1
for i in range(1, len(frames)):
    score = cosine_similarity(frames[i-1].embedding, frames[i].embedding)
    # Se score < 0.90: possível quebra temporal
    # Diagnóstico, não gate (pode haver corte intencional)
```

### M3 — Reprodutibilidade (FALTAVA)

```python
# Frame 005 vs Frame 001 (mesma pose, chamadas diferentes)
score = cosine_similarity(frame_001.embedding, frame_005.embedding)
# Se score < 0.85: alta variância de geração
# Indica generator instável para este prompt
```

### Agregação

| Medição | Tipo | Threshold | Acção se FAIL |
|---------|------|-----------|---------------|
| M1 | **Gate** | SHOT-GRAMMAR-002 | Re-gerar obrigatório |
| M2 | **Diagnóstico** | 0.90 | Anotar quebras |
| M3 | **Diagnóstico** | 0.85 | Avaliar estabilidade |

---

## IV. INTEGRAÇÃO — CONTAINER PRODUKTION/

O Container `produktion/` criado em 13 Jun 2026 vive **dentro** deste Órgão MÉTODO.

### Hierarquia

```
ÓRGÃO MÉTODO (Este documento)
    │
    ├── METHOD-HIOS-GENERATION-001.md (protocolo de geração)
    │
    └── /produktion/ (Container de execução)
            ├── CINEMA-PRODUKTION-BASE-001.md (3 níveis)
            ├── REGISTO-CENA-*.md (registos de cena)
            ├── PROTOCOLO-RUN-*.md (protocolos de medição)
            ├── PROMPTS-*.md (prompts de geração)
            └── <personagem>/
                    ├── RESULTADOS-*.md
                    └── ERRATA-*.md
```

### O Container NÃO é Paralelo

O Container `produktion/` não substitui este documento — **executa-o**. Este documento define o "como"; o Container regista cada execução individual.

---

## V. AXIOMAS DO ÓRGÃO MÉTODO

> *"O SPINE-CAST mede se É a pessoa. Não mede se É o mesmo momento."*

> *"Identidade e continuidade são vectores ortogonais."*

> *"O frame aponta para a âncora no disco. Não a reproduz por prompt."*

> *"Gerar 5 imagens soltas e chamar-lhes plano é o erro que este método corrige."*

> *"A continuidade não se mede depois — constrói-se na geração."*

---

## VI. CHECKLIST PRÉ-GERAÇÃO

Antes de gerar qualquer plano para HIOS:

- [ ] Âncora SEALED do personagem disponível como `image_1`?
- [ ] Referência de cenário disponível como `image_2`?
- [ ] Prompt segue gramática descritiva (não imperativa)?
- [ ] Generator configurado para VIDEO (não Image)?
- [ ] Workflow inclui extracção de keyframes do vídeo?
- [ ] Protocolo de medição inclui M1 + M2 + M3?

Se qualquer item falhar → PARAR e corrigir antes de gerar.

---

## VII. VERIFICAÇÃO

```bash
# Hash deste documento (para receipt)
sha256sum production/METHOD-HIOS-GENERATION-001.md

# Confirmar que Container produktion/ existe
ls -la /opt/windi/hios/cinema/produktion/
```

---

*Liga IA+H · WINDI Publishing House · 13 Jun 2026*
*"AI processes. Human decides. WINDI guarantees."*
*Órgão MÉTODO — Primeiro Habitante*
