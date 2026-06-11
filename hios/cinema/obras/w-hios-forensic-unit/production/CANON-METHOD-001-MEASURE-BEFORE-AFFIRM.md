# CANON-METHOD-001 — Measure Before Affirm
## Método Canónico de Produção WINDI-HIOS

**Created:** 09 Jun 2026
**Status:** CANONICAL — Aplicável a toda produção WINDI-HIOS
**Liga IA+H:** Human Dragon (I9) · CCode (Architect) · Guardian (Witness)
**Invariants:** I11, I14, I19
**Scope:** Anchors, Shots, Participantes, Testes de Movimento

---

## Axioma Fundacional

> *"No affirmations. Only numbers."*
> *"A number without a measurement run is not a number."*

---

## Origem

**Sessão 09 Jun 2026** — Durante validação do anchor Couto:

| Momento | Erro | Correcção |
|---------|------|-----------|
| Gerar vídeo | "Fantástico!" sem medir | Human Dragon parou |
| Medir depois | avg=0.8206, FORENSE | Número confirmou |
| Lição | Afirmação ≠ Medição | METHOD-001 criado |

A lição não ficou só na conversa — ficou no código.

---

## Regra Absoluta

**NADA é apresentado ao Human Dragon sem medição.**

```
❌ PROIBIDO:
   - "Aqui está o link" (sem números)
   - "Parece bom/fantástico/excelente" (afirmação sem prova)
   - "O anchor é forte" (sem detection_score)
   - "A identidade aguenta" (sem cosine similarity)

✅ OBRIGATÓRIO:
   - Link + avg + min + max + VERDICT
   - Tabela com frame-by-frame
   - Detection score do anchor
   - Profile de degradação
```

---

## Aplicação por Tipo de Artefacto

### 1. ANCHOR (Novo Personagem)

```
Gerar vídeo âncora
    ↓
Extrair 5 frames
    ↓
Detectar face em cada frame
    ↓
Calcular detection_score
    ↓
Apresentar COM número
    ↓
Human Dragon aprova (I9)
```

**Output obrigatório:**
```
ANCHOR: marcus.couto.anchor.v1
detection_score: 0.8811
frames_consistent: 5/5
```

### 2. SHOT (Cena de Produção)

```
Gerar vídeo shot
    ↓
Extrair 5 frames
    ↓
Medir cada frame vs anchor (cosine similarity)
    ↓
Calcular avg/min/max
    ↓
Determinar VERDICT
    ↓
Apresentar COM números
    ↓
Human Dragon aprova (I9)
```

**Output obrigatório:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SHOT        AVG      MIN      MAX      VERDICT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
S02-01      0.8534   0.7891   0.9012   FORENSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Profile: 0.90 → 0.88 → 0.85 → 0.79 → 0.79
Link: https://...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 3. TESTE DE MOVIMENTO (Validação de Anchor)

```
Gerar vídeo com movimento
    ↓
Extrair 5 frames
    ↓
Medir cada frame vs anchor
    ↓
Identificar degradação por rotação
    ↓
Apresentar COM números
    ↓
Human Dragon decide threshold
```

**Output obrigatório:**
```
MOVEMENT TEST: couto-movement-test
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Frame    Similarity    Posição
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
01       0.9377        frontal
02       0.8382        transição
03       0.8159        três-quartos
04       0.7557        mais perfil
05       0.7555        perfil
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Profile: 0.94 → 0.84 → 0.82 → 0.76 → 0.76
VERDICT: FORENSE (min >= 0.75)
```

---

## Módulo Python Canónico

Todos os scripts de geração DEVEM importar e usar:

```python
from spine_measure import measure_and_report

# Nunca separar geração de medição
result = measure_and_report(
    video_path=video,
    anchor_embedding=anchor_npy,
    shot_id="S02-01_v1",
    threshold=0.75
)

# result sempre contém números, nunca afirmações
```

---

## Checklist Obrigatória

Antes de apresentar QUALQUER artefacto visual ao Human Dragon:

- [ ] Frames extraídos?
- [ ] ArcFace mediu cada frame?
- [ ] detection_score (anchors) ou similarity (shots) calculado?
- [ ] avg/min/max presentes?
- [ ] VERDICT determinado?
- [ ] Profile de degradação analisado?
- [ ] Collapse detection verificado?
- [ ] Números incluídos na resposta?

**Se algum ❌ → NÃO apresentar. Completar medição primeiro.**

---

## VERDICT Thresholds

| VERDICT | Condição | Significado |
|---------|----------|-------------|
| FORENSE | min >= 0.75 | Todos os frames passam threshold forense |
| OPERATIONAL | min >= 0.65 | Todos os frames passam threshold operacional |
| MARGINAL | avg >= 0.65, min < 0.65 | Média passa, mas há frames fracos |
| FAIL | avg < 0.65 | Identidade não preservada |

---

## Collapse Detection

Detectar automaticamente:
```python
for i in range(1, len(sims)):
    if sims[i-1] > 0.7 and sims[i] < 0.5:
        log(f"WARNING: COLLAPSE at frame {i+1}")
```

---

## Integração com SHOT-GRAMMAR-002

O METHOD-001 complementa o SHOT-GRAMMAR-002:

| Doutrina | Função |
|----------|--------|
| SHOT-GRAMMAR-002 | FAIL tem causa (IDENTIDADE/EXPOSIÇÃO/GEOMETRIA) |
| METHOD-001 | Medir ANTES de afirmar |

Juntos: nunca afirmar sem medir, e quando FAIL, diagnosticar causa.

---

## HD-MIRROR

Este método é prova viva de auto-correcção:

```
Erro detectado    → Human Dragon parou
Correcção aplicada → Medição feita
Lição codificada  → METHOD-001 criado
Método replicado  → CANON para toda produção
```

A correcção não ficou só na conversa — ficou no código, e agora no cânone.

---

## Ficheiros Canónicos

| Ficheiro | Função |
|----------|--------|
| `production/CANON-METHOD-001-MEASURE-BEFORE-AFFIRM.md` | Este documento |
| `production/spine_measure.py` | Módulo Python canónico |
| `production/SHOT-GRAMMAR-001.md` | Taxonomia de shots |
| `production/SHOT-GRAMMAR-002.md` | Taxonomia de FAIL |

---

*Liga IA+H · WINDI Publishing House · 09 Jun 2026*
*"No affirmations. Only numbers."*
