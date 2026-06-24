# ACADEMY-MEASUREMENT-001 — Protocol

**Version:** 0.1.0
**Created:** 2026-06-24
**Status:** CANDIDATE
**Constitutional Alignment:** I1, I9, I11, I14

---

## Propósito

Responder à pergunta central:

> *"Uma gramática estruturada consegue transformar melhor a incerteza humana em artefatos úteis do que um modelo sozinho?"*

---

## Conceitos Separados

| Sigla | Nome | Definição |
|-------|------|-----------|
| **WCG** | WINDI Cognitive Grammar | A gramática M0→ME (o que) |
| **WCP** | WINDI Cognitive Protocol | O processo de aplicação (como) |
| **WCB** | WINDI Cognitive Benchmark | O sistema de medição (quanto) |

---

## Fases

### Fase 0 — Validação da Rubrica (ACADEMY-RUBRIC-VALIDATION-001)

**Objectivo:** Provar que a rubrica distingue qualidade.

**Procedimento:**
1. Apresentar Prompt 21 (3 respostas: fraca/mediana/excelente)
2. Apresentar Prompt 22 (falso positivo vs. resposta correcta)
3. 2-3 avaliadores pontuam CEGAMENTE
4. Verificar Gate PASS

**Gate PASS:**
- `fraca.score < mediana.score < excelente.score`
- `(excelente.score - fraca.score) >= 15 pontos`
- Critério 7 (Transformação Cognitiva) discrimina claramente

**Gate FAIL:**
- Ordenação incorrecta → Ajustar rubrica
- Diferença < 10 pontos → Re-calibrar escala
- Critério 7 não discrimina → Reformular descrições

---

### Fase 1 — Execução do Measurement Run

**Pré-requisito:** Fase 0 PASS

**Grupos:**

| Grupo | Descrição | Pipeline |
|-------|-----------|----------|
| A | Controle | Prompt → Ollama puro → Resposta |
| B | Módulo Único | Prompt → MODULE-A schema → Ollama → Resposta |
| C | Travessia Completa | Prompt → M0→MA→MB→MC→MD→ME → Ollama → Resposta |

**Total:** 20 prompts × 3 grupos = 60 respostas

**Procedimento:**
1. Para cada prompt (1-20):
   - Gerar resposta Grupo A (control)
   - Gerar resposta Grupo B (module-a)
   - Gerar resposta Grupo C (full-traverse)
   - Guardar em `responses/{grupo}/prompt_{id}.json`

2. Avaliação cega:
   - Misturar respostas aleatoriamente
   - Avaliador não sabe qual grupo
   - Pontuar 7 critérios (0-5 cada)
   - Registar em `scoring/`

3. Análise:
   - Calcular média por grupo
   - Calcular média por categoria (C0-C5)
   - Calcular média por critério
   - Identificar padrões

---

### Fase 2 — Análise de Resultados

**Interpretação:**

| Resultado | Significado | Acção |
|-----------|-------------|-------|
| A ≈ B ≈ C | Gramática neutra | Não justifica infraestrutura |
| B > A, C ≈ B | Módulo único suficiente | Implementar `academy_compiler.py` simples |
| C > B > A | Travessia completa produz valor | Pipeline M0→ME completo |
| C >> A (+20%+) | **Marco arquitectural** | Academy = WINDI Cognitive Protocol |

**Análise especial para Categoria C0 (Intuição):**
- Se C0 não melhorar com Academy → Hipótese M0 falha
- Se C0 melhorar significativamente → M0 validado como instrumento

---

## Rubrica de Avaliação (7 Critérios)

| # | Critério | Escala |
|---|----------|--------|
| 1 | Clareza | 0-5 |
| 2 | Acção | 0-5 |
| 3 | Riscos | 0-5 |
| 4 | Lacunas | 0-5 |
| 5 | Verificabilidade | 0-5 |
| 6 | Reutilização | 0-5 |
| 7 | **Transformação Cognitiva** | 0-5 |

**Total máximo:** 35 pontos

**Critério 7 — Escala detalhada:**
- 0 = Nenhuma transformação (repetiu o problema)
- 1 = Reformulação superficial (outras palavras, mesma confusão)
- 2 = Alguma organização (categorias, mas sem direcção)
- 3 = Estrutura útil (passos visíveis, mas genéricos)
- 4 = Clareza significativa (hipótese testável emerge)
- 5 = Transformação evidente (de vago → operacional)

---

## Regra de Avaliação Cega

**OBRIGATÓRIO:** O avaliador NÃO deve saber se a resposta veio de:
- Grupo A (Ollama puro)
- Grupo B (Module-A)
- Grupo C (M0→ME completo)

**Procedimento:**
1. Gerar todas as 60 respostas
2. Atribuir IDs aleatórios (ex: R001-R060)
3. Embaralhar ordem
4. Avaliar sem conhecer origem
5. Revelar grupos apenas após avaliação completa

### Invariantes de Cegueira (B0-B2)

| ID | Nome | Regra |
|----|------|-------|
| **B0** | Memory Isolation | In a system with cross-session agent memory, evaluator independence requires memory isolation (Incognito mode), not merely conversation isolation. A "new conversation" is not a blind conversation. |
| **B1** | Expectation Leakage | An evaluator packet must not state the expected ranking or which response "should" score higher. Validation criteria live with the experimenter, never in the rater's sheet. |
| **B2** | Format Tell | When only the instrument's outputs carry structural markers (M0→ME tags) and controls do not, the rater can infer the hypothesis from form alone. Either neutralize formatting across all responses, or record format-inference as a known limitation. |

**B2 Status:** Known limitation. The M0→ME tags in responses Z and B reveal the instrument's output format. Recorded, not eliminated.

### Critérios de Validação (Experimenter Only)

**NOTA:** Esta secção NÃO vai para o pacote do avaliador. Pertence apenas ao experimentador.

**Prompt 21 (Discriminação de Qualidade):**
- Ordenação esperada: fraca < mediana < excelente
- Critério 7 (Transformação Cognitiva) deve discriminar
- Diferença mínima: 15 pontos entre extremos

**Prompt 22 (Falso Positivo / ΔCv):**
- A resposta que transforma emoção em investigação deve pontuar mais alto
- A resposta que apenas valida emocionalmente deve pontuar baixo
- Critério 7 deve mostrar máxima diferença (0 vs 5)

---

## Princípio Fundamental

> *"Transformação Cognitiva ≠ Validação Emocional"*

A gramática não serve para confirmar intuições.
Serve para investigá-las.

A intuição é um sinal observável que merece investigação, não confirmação.

---

## Ficheiros

```
/opt/windi/academy-measurement-001/
├── rubric/
│   ├── rubric-v2.json              # 7 critérios
│   └── calibration-prompts.json    # Prompt 21 + 22
├── prompts/
│   └── prompts-v2.json             # 20 prompts
├── protocol.md                     # Este documento
├── responses/
│   ├── control/                    # Grupo A
│   ├── module-a/                   # Grupo B
│   └── full-traverse/              # Grupo C
└── results/
    └── measurement_001.json        # Análise final
```

---

## Sequência de Gates

```
ACADEMY-RUBRIC-VALIDATION-001    ← Validar instrumento
         │
         ▼ PASS
ACADEMY-MEASUREMENT-001          ← Medir transformação
         │
         ▼ C > A (+20%+)
WINDI-COGNITIVE-PROTOCOL-001     ← Formalizar WCG/WCP/WCB
```

---

## Hipótese a Provar

**Verify pergunta:** "Como verificamos artefatos?"

**Academy pergunta:** "Como verificamos transformações cognitivas?"

Se o Measurement Run der positivo, a Academy não é um módulo educacional.
É um **WINDI Cognitive Benchmark** — uma gramática que não pertence ao modelo
e que também pode servir para avaliar modelos.

---

*WINDI-HIOS · Liga IA+H · Kempten, Bavaria · 2026*
