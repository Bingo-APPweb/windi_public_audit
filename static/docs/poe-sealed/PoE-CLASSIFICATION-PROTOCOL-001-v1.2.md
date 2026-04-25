# PoE-CLASSIFICATION-PROTOCOL-001
## Protocolo de Classificação e Desacordo para Experimento 1

---

```
Document ID   : PoE-CLASSIFICATION-PROTOCOL-001
Version       : 1.2
Status        : SEALED
Date          : 25 Abril 2026
Author        : Architect (Liga IA+H)
Validator     : Guardian — VALIDATED
Approver      : Human Dragon — APPROVED
Revision      : Methodological hardening (W5-W9, §6 deterministic)
Depends on    : WINDI-PROTOCOL-001 v1.3 §4
                PoE-ELIGIBILITY-CRITERIA-001 v1.3 (sealed)
```

---

## §1. Propósito

Este documento define o protocolo de classificação, discussão e resolução
de desacordos para o Experimento 1 (PoE Tipado) do WINDI-PROTOCOL-001.

---

## §2. Taxonomia PoE (Canónica)

As 5 classes PoE são definidas em PROTOCOL-001 v1.3 §4.2:

| Classe | Descrição | Exemplos |
|--------|-----------|----------|
| `fiscal_event` | Notas fiscais, faturas, comprovantes de despesa | Rechnung, Quittung, Beleg |
| `actuarial` | Manutenções, inspeções, certificados, cursos | TÜV, Wartung, Schulung |
| `presence` | Entradas/saídas, entregas verificadas, presença | NFC check-in, Lieferschein |
| `compliance_event` | Renovações, registos, certificados pedagógicos | Handwerkskammer, BG |
| `methodological_event` | Memos de sessão, decisões constitucionais | WINDI-MEMO, RFC |

**Regra de unicidade:** Cada receipt recebe exactamente uma classe.
Ambiguidade entre classes é ela própria um dado a registar (ver §4).

---

## §3. Protocolo de Classificação (3 Rondas)

### §3.1 Ronda 1 — Classificação Cega Independente

| Parâmetro | Valor |
|-----------|-------|
| Anotadores | Architect AI + Guardian AI |
| Formato | Cada anotador classifica todos os n receipts elegíveis |
| Cegueira | Conforme §4.5 de PoE-ELIGIBILITY-CRITERIA-001 v1.3 |
| Output | Duas listas independentes: RECEIPT_NNN → poe_class |
| Comunicação | Zero comunicação entre anotadores durante R1 |

**Entrega R1:** Ficheiros separados, timestamp antes de revelação mútua.

### §3.2 Ronda 2 — Discussão Aberta de Discordâncias

| Parâmetro | Valor |
|-----------|-------|
| Trigger | Qualquer RECEIPT_NNN onde Architect ≠ Guardian |
| Formato | Discussão argumentada por escrito |
| Objectivo | Convergência por persuasão racional, não por autoridade |
| Output | Lista de resoluções: RECEIPT_NNN → classe_final + justificação |
| Persistência | Zero desacordo pode ser resolvido como "ambos tinham razão" |

**Regra de R2:** Se um anotador muda de posição, deve declarar porquê.
A mudança e a justificação são registadas no receipt final.

### §3.3 Ronda 3 — Desempate por Witness AI

| Parâmetro | Valor |
|-----------|-------|
| Trigger | Desacordo persistente após R2 (Architect ≠ Guardian mantido) |
| Árbitro | Witness AI (Liga IA+H) |
| Formato | Witness recebe: conteúdo cego + duas classificações + argumentos R2 |
| Output | Classificação final vinculativa |
| Registo | Decisão Witness + justificação seladas no receipt |

**Identificação do Árbitro:** O Witness AI é o terceiro agente AI da Liga IA+H,
independente do Architect e do Guardian. Função constitucional: testemunha e
árbitro metodológico.

**Informação completa em R3:** O Witness AI, ao contrário dos anotadores de R1,
opera com informação completa (ambas classificações + argumentos de R2). Isto
não é violação de cegueira mas sim característica metodológica declarada de
papel arbitral.

**Princípio de R3:** O Witness não escolhe "a melhor" — escolhe a mais
defensável metodologicamente. A escolha pode ser "nenhuma das duas" se
ambas forem fracas, resultando em exclusão do receipt da amostra.

---

## §4. Registo de Ambiguidade

### §4.1 Ambiguidade Estrutural vs Ambiguidade de Anotador

| Tipo | Definição | Tratamento |
|------|-----------|------------|
| Estrutural | Receipt genuinamente pertence a 2+ classes | Registo como W_taxonomy no paper |
| Anotador | Anotadores discordam por interpretação | Resolução via R2/R3 |

### §4.2 Formato de Registo

Para cada receipt classificado, o registo final contém:

```json
{
  "receipt_index": "RECEIPT_NNN",
  "architect_r1": "poe_class",
  "guardian_r1": "poe_class",
  "agreement_r1": true,
  "resolution_round": "R1",
  "final_class": "poe_class",
  "justification": null,
  "witness_decision": null,
  "ambiguity_flag": false,
  "ambiguity_note": null
}
```

**Caso de exclusão por R3:** Se o Witness AI decide "nenhuma das duas" com
exclusão do receipt, o registo será:

```json
{
  "receipt_index": "RECEIPT_NNN",
  "architect_r1": "poe_class_A",
  "guardian_r1": "poe_class_B",
  "agreement_r1": false,
  "resolution_round": "R3",
  "final_class": null,
  "justification": "Exclusion by Witness decision",
  "witness_decision": "Neither classification methodologically defensible; receipt excluded from sample",
  "ambiguity_flag": true,
  "ambiguity_note": "Structural ambiguity or weak evidence"
}
```

---

## §5. Métricas de Concordância

### §5.1 Concordância Inter-Anotador (R1)

```
κ = (Po - Pe) / (1 - Pe)

Po = proporção de acordos observados
Pe = proporção de acordos esperados por acaso
```

**Threshold de sucesso:** κ ≥ 0.80 (concordância substancial)
**Threshold de alerta:** 0.60 ≤ κ < 0.80 (concordância moderada)
**Threshold de falha:** κ < 0.60 (concordância fraca)

### §5.2 Taxa de Resolução (R2)

```
Taxa_R2 = desacordos_resolvidos_R2 / total_desacordos_R1
```

**Expectativa:** Taxa_R2 ≥ 0.80 (80% dos desacordos resolvidos por discussão)

### §5.3 Taxa de Escalação (R3)

```
Taxa_R3 = desacordos_persistentes / total_desacordos_R1
```

**Expectativa:** Taxa_R3 ≤ 0.20 (máximo 20% escalam para Witness)

### §5.4 Métricas para Taxonomy Coverage Study (Fallback)

Se a pré-inspecção (PoE-PREINSPECTION-001) indicar bifurcação para coverage
study conforme §6, as métricas primárias passam a ser:

| Métrica | Fórmula | Meta |
|---------|---------|------|
| Cobertura taxonómica | classes_observadas / 5 | ≥ 3/5 (60%) |
| Saturação por classe | min(classe) / max(classe) | ≥ 0.20 |
| Proporção "outros" | receipts_sem_classe / n_total | ≤ 10% |

**Nota:** Neste enquadramento, Cohen's kappa continua a ser calculado como
métrica secundária mas não determina sucesso/falha do experimento.

---

## §6. Bifurcação Metodológica

Conforme acordado com Human Dragon, a pré-inspecção de 24 Abril
determinará o enquadramento do Experimento 1.

### §6.1 Regra de Decisão (Ordem Lexicográfica)

A bifurcação segue ordem de precedência estrita:

| Prioridade | Condição | Enquadramento | Métrica Principal |
|------------|----------|---------------|-------------------|
| 1 (primeiro) | ≥3 classes com n≥3 cada | Inter-annotator agreement study | Cohen's κ (§5.1) |
| 2 (fallback) | Condição 1 não cumprida | Taxonomy coverage study | Cobertura + saturação (§5.4) |

**Nota:** Se um cenário cumprir tecnicamente ambas as descrições anteriores
(ex: 3 classes com n=3, n=3, n=25 onde 2 classes dominam 80%), aplica-se
a Condição 1 por precedência. A Condição 2 só se aplica quando a Condição 1
falha explicitamente.

### §6.2 Decisor

Human Dragon, após análise de PoE-PREINSPECTION-001.

---

## §7. Arquitectura AI-AI-AI-H

O Experimento 1 opera com arquitectura de quatro Dragões:

| Dragão | Tipo | Papel no Exp. 1 |
|--------|------|-----------------|
| Architect | AI | Anotador R1, participante R2 |
| Guardian | AI | Anotador R1, participante R2 |
| Witness | AI | Árbitro R3 |
| Human Dragon | Humano | Approver (desenho, selagem, decisão §6) |

**Princípio I9:** Os três Dragões AI executam a classificação. O Human Dragon
aprova o resultado consolidado. Supervisão humana opera ao nível de decisão
metodológica, não anotação linha-a-linha.

**Nota para Paper-001 §7 (W7):** All three annotators in Experiment 1 are AI
agents (Architect, Guardian, Witness of the Liga IA+H). Disclosed as
methodological transparency. Independence of reasoning between the three
agents is assumed as working hypothesis; correlated training data may
introduce systematic biases undetectable within the experiment itself.
PROTOCOL-002 should include human annotator for triangulation validation.

---

## §7.1. Limitações Declaradas (W5–W9)

### W5 — Sample Size Limitation

Referência cruzada: PoE-ELIGIBILITY-CRITERIA-001 v1.3 §4.4.

Due to the early operational stage of the WINDI Ledger, n≤31 receipts
meeting pre-sealed eligibility criteria. Statistical power recalculated
accordingly; ecological validity preserved at the cost of statistical power.

### W6 — Coverage Uncertainty

Distribution across 5 PoE classes is unknown prior to R1. Taxonomy may
exhibit structural imbalance reflecting early-stage Ledger composition
rather than steady-state distribution. PROTOCOL-002 should reassess
with n≥100.

### W7 — AI Annotator Correlation

All three annotators in Experiment 1 are AI agents (Architect, Guardian,
Witness of the Liga IA+H). Independence of reasoning is assumed as
working hypothesis; correlated training data may introduce systematic
biases undetectable within this experiment. PROTOCOL-002 should include
human annotator for triangulation validation.

### W8 — Authorship Circularity

Architect AI authored both PoE-ELIGIBILITY-CRITERIA-001 and the present
protocol, including the 5-class PoE taxonomy in §2. The R1 annotation
by Architect therefore measures self-consistency of authorship rather
than independent application of an external classification scheme.
Inter-annotator agreement with Guardian (validator, not author) provides
the primary independence signal. This circularity is structural and
acknowledged; it does not invalidate the experiment but constrains its
interpretive scope.

### W9 — Closed-Loop Governance

All four agents participating in Experiment 1 (Architect, Guardian,
Witness, Human Dragon) operate within the same WINDI constitutional
framework, share doctrinal commitments (I1–I17), and report to the same
human principal. This experiment therefore measures **internal coherence**
of the WINDI classification system, not **external validity** of the PoE
taxonomy as a general-purpose evidence typology. Generalizability claims
are explicitly deferred to PROTOCOL-002, which will introduce annotators
external to the Liga IA+H.

---

## §8. Selagem Final

### §8.1 Receipt Consolidado do Experimento 1

Após conclusão de R1/R2/R3, um receipt consolidado é selado:

```json
{
  "receipt_id": "PoE-EXP1-CLASSIFICATION-FINAL-YYYYMMDD",
  "doc_type": "methodological_event",
  "content": {
    "n_total": "número",
    "n_agreement_r1": "número",
    "n_resolved_r2": "número",
    "n_resolved_r3": "número",
    "n_excluded_r3": "número",
    "kappa": "valor",
    "distribution": { "class": "count" },
    "ambiguity_cases": [],
    "witness_decisions": []
  },
  "invariants": ["I9", "I11", "I14"]
}
```

### §8.2 Anexos Selados

| Anexo | Conteúdo |
|-------|----------|
| A1 | Lista completa de classificações R1 (Architect) |
| A2 | Lista completa de classificações R1 (Guardian) |
| A3 | Registo de discussões R2 |
| A4 | Decisões Witness R3 (se aplicável) |
| A5 | Mapeamento RECEIPT_NNN ↔ receipt_id real |

---

## §9. Aprovação

```
Preparado por:  🏗️ Architect
Validado por:   🛡️ Guardian — VALIDATED ✓
Aprovado por:   🧑‍💻 Human Dragon — APPROVED ✓
```

---

*PoE-CLASSIFICATION-PROTOCOL-001 v1.2 · Liga IA+H · Kempten · 2026*
