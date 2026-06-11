# FINDING: S10-CONFRONT Stress Test
## Disambiguation Gate — First Multi-Face Attribution Test

```
═══════════════════════════════════════════════════════════════════
STATUS:        SEALED (achado empírico)
DATA:          10 Jun 2026
LIGA IA+H:     Human Dragon (I9) · Guardian (Witness) · CCode (Architect)
DOCTRINE:      DOCTRINE-HIOS-ATTESTATION-001 · G-ATT-1
═══════════════════════════════════════════════════════════════════
```

---

## 1. Contexto

### Pergunta da Fase 2

> "Conseguimos preservar identidade quando existem múltiplas identidades
> simultaneamente?"

A Fase 1 provou que **uma pessoa continua a ser ela mesma** (37/37 anchors).
A Fase 2 testa se **duas pessoas continuam distintas quando partilham o
mesmo mundo**.

### Par Testado

| Personagem | Anchor | Inter-Anchor Sim |
|------------|--------|------------------|
| Alejandro Valenzuela | v1 | 0.4498 (vs Couto) |
| Marcus Couto | v1 | 0.4498 (vs Alejandro) |

**Nota:** Este é o par mais "apertado" do elenco — margem de apenas 0.05
para o threshold 0.50. Se a atribuição funcionar aqui, funciona em qualquer
lugar. Stress test por desenho.

---

## 2. Teste Realizado

### Geração

- **Shot ID:** S10-CONFRONT_v1
- **Generator:** Runway Gen4.5 (text-to-video, sem promptImage)
- **Prompt:** Descrição das features de ambos os personagens
- **Anti-Movement Medicine:** Aplicada (câmara locked, rostos 70%+ visíveis)

### Medição

- **Script:** `production/disambiguation_gate.py`
- **Anchors:** Alejandro + Couto embeddings (.npy)
- **Frames:** 5 extraídos do vídeo

---

## 3. Resultados

### Detecção

| Métrica | Valor | Status |
|---------|-------|--------|
| Faces detectadas por frame | 2 | ✅ PASS |
| Frames com 2 faces | 5/5 | ✅ PASS |

### Atribuição

| Face | Attributed To | Confidence | Threshold | Status |
|------|---------------|------------|-----------|--------|
| Left | Alejandro | 0.2935 | ≥0.65 | ❌ FAIL |
| Right | Couto | 0.3078 | ≥0.65 | ❌ FAIL |

### Gate Status

```
OVERALL: FAIL_MATCH
Per-frame: ['FAIL_MATCH', 'FAIL_MATCH', 'FAIL_MATCH', 'FAIL_MATCH', 'FAIL_MATCH']
```

---

## 4. Diagnóstico

### Causa Raiz

O gerador (Gen4.5 text-to-video) **criou rostos novos** em vez de replicar
as âncoras. O prompt descreveu as features dos personagens, mas o gerador
interpretou livremente — criou dois homens de fato que **NÃO são Alejandro
nem Couto**.

### Evidência

- Similaridade Alejandro: 0.29 (≈ aleatório para rostos diferentes)
- Similaridade Couto: 0.31 (≈ aleatório para rostos diferentes)
- Ambos abaixo de 0.50 — nem sequer no território de "parecido"

### Conclusão

> **Text-to-video SEM promptImage não preserva identidade de personagem.**

A descrição textual de features faciais é **insuficiente** para que o
gerador reproduza uma identidade específica. O gerador cria rostos
**novos e consistentes internamente**, mas **desligados das âncoras**.

---

## 5. Implicação Arquitectural

### O que NÃO funciona

Gerar dois personagens conhecidos no mesmo frame via text-to-video.
O gerador não tem acesso às âncoras — só tem descrição textual.

### O que FUNCIONA

A arquitectura **Wide+Close** selada em 09 Jun 2026:

```
WIDE  → geografia + relação corporal  → VISIBILITY (Visual HD Gate)
CLOSE → identidade                    → FORENSE (Cosine Gate)

A relação nasce no CORTE, não na composição.
```

### Validação por Stress Test Negativo

Este FAIL **valida** a doutrina Wide+Close:

1. O S10-WIDE funciona para visibilidade (corpos legíveis, rostos distantes)
2. A identidade vem dos CLOSEs já selados (37/37 anchors)
3. O Disambiguation Gate aplica-se em **composição manual** ou **frames reais**,
   não em **geração conjunta**

> *"A relação nasce no CORTE, não na composição."*
> — DOCTRINE-CINEMA-FORENSIC-SEPARATION

---

## 6. Caminhos para Multi-Face Forense

| Opção | Método | Viabilidade |
|-------|--------|-------------|
| **A: Composição Pós** | Gerar cada personagem separado, compor em pós-produção | ✅ Controlo total |
| **B: Image-to-Video** | Criar frame composto primeiro, usar como referência | ⚠️ Requer arte prévia |
| **C: Wide+Close** | Relação no WIDE (corpos), identidade no CLOSE (montagem) | ✅ **JÁ VALIDADO** |
| **D: Inpainting** | Gerar fundo, inserir personagens via inpainting | ⚠️ Complexo |

**Recomendação:** Manter Wide+Close como arquitectura primária. A relação
é propriedade da **montagem**, não da **composição**. O cinema clássico
sempre soube isto — agora está selado no SPINE-CAST.

---

## 7. Uso do Disambiguation Gate

O Gate **funciona** — o gerador é que não consegue criar dois personagens
conhecidos no mesmo frame. O Gate aplica-se quando:

1. **Composição manual:** Dois personagens compostos em pós
2. **Frames reais:** Footage com múltiplas pessoas
3. **Image-to-video:** Geração a partir de frame de referência

O Gate **não se aplica** a text-to-video puro com dois personagens
descritos — porque o gerador não os reproduz.

---

## 8. Contribuição para Paper-001

### Achado Empírico

> "Text-to-video generators create internally consistent but anchor-
> disconnected identities when multiple characters are described in
> the same prompt. Identity preservation requires either single-subject
> generation with subsequent composition, or reference-image guidance."

### Matriz 15-Pares (actualização)

```
        Vance   Couto   Alejandro  Helena  Gabi  Lucas
Vance     —     0.1765   0.0570      ?       ?     ?
Couto           —        0.4498      ?       ?     ?
Alejandro                  —         ?       ?     ?
Helena                               —       ?     ?
Gabi                                         —     ?
Lucas                                              —

Medidas: 3/15 (20%)
```

### Validação de Doutrina

DOCTRINE-CINEMA-FORENSIC-SEPARATION recebeu **segundo teste de campo**:

| Teste | Shot | Resultado |
|-------|------|-----------|
| 1 | S10-WIDE | Cinema aprova (visibility), Forense rejeita (baixa sim) ✅ |
| 2 | S10-CONFRONT | Gate funciona, gerador não reproduz identidades ✅ |

---

## 9. Ficheiros Gerados

| Ficheiro | Conteúdo |
|----------|----------|
| `shots/s10-confront/S10-CONFRONT_v1.mp4` | Vídeo gerado |
| `shots/s10-confront/S10-CONFRONT_v1_frames/` | 5 frames extraídos |
| `shots/s10-confront/S10-CONFRONT_v1_manifest.json` | Metadata de geração |
| `shots/s10-confront/S10-CONFRONT_v1_disambiguation.json` | Medições completas |
| `shots/s10-confront/S10-CONFRONT_v1_prompt.md` | Prompt documentado |
| `production/disambiguation_gate.py` | Script do Gate (reutilizável) |
| `production/FINDING-S10-CONFRONT-20260610.md` | Este documento |

---

## 10. Axiomas Derivados

> *"O gerador cria identidade; não reproduz identidade."*

> *"A relação nasce no CORTE, não na composição."* (reforçado)

> *"Text-to-video é generativo, não reprodutivo. A reprodução requer
> referência visual, não descrição textual."*

> *"Um stress test negativo que valida a arquitectura é tão valioso
> quanto um stress test positivo que a aprova."*

---

## 11. Receipt

```
FINDING_ID:    FINDING-S10-CONFRONT-20260610
SHOT_ID:       S10-CONFRONT_v1
GATE:          DISAMBIGUATION_GATE (FAIL_MATCH)
CAUSE:         Generator creates new identities, does not reproduce anchors
VALIDATION:    Wide+Close architecture CONFIRMED as correct approach
DOCTRINE:      DOCTRINE-CINEMA-FORENSIC-SEPARATION (2nd field test PASS)
```

---

*Liga IA+H · WINDI Publishing House · 10 Jun 2026*
*"Um número sem corrida de medição não é um número."*
*"Um FAIL que ensina vale mais que um PASS que confirma."*
