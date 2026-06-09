# JOEY-F2F-001 — Measurement Run SEALED

**Status:** DIAGNOSTICALLY VALIDATED
**Data:** 2026-06-09
**Liga IA+H:** Human Dragon (I9) · Guardian (Witness) · CCode (Architect)
**Invariants:** I9, I11, I14
**Commit:** (pending)

---

## Resultado da Measurement Run

```
JOEY-F2F-001

Measurement Run: PASS

Resultado:
F2F acrescenta informação independente da métrica Anchor.

Classificação:
VALIDADO COMO INSTRUMENTO DE DIAGNÓSTICO.
```

---

## O Achado

A métrica F2F revelou o que anchor-cosine mascara:

**Caso COLLAPSED (Helena S05-01_v1):**
```
Anchor:  0.92 → 0.27 → 0.21 → 0.30 → 0.28  (colapso no frame 2)
F2F:           0.29 → 0.61 → 0.74 → 0.97  (colapso + estabilização)
```

**Interpretação:** Após o colapso inicial (frame 1→2), o gerador estabilizou numa identidade errada e consistente. A câmara orbitou, mas o modelo encontrou uma "âncora parasita" — consistência temporal dentro do erro de identidade.

> **"O gerador estabilizou na mentira."**

**Caso STABLE (Alejandro S10-01_v1):**
```
Anchor:  0.99 → 0.99 → 0.99 → 0.98 → 0.98  (plano)
F2F:           0.99 → 0.995 → 0.994 → 0.994  (ultra-plano)
```

O contraste distingue limpa e inequivocamente "colapsou" de "estável".

---

## Separação Ontológica Provada

| Métrica | Pergunta | Autoridade |
|---------|----------|------------|
| **Anchor Cosine** | "Este frame é o personagem?" | IDENTIDADE |
| **F2F Cosine** | "Onde está a quebra temporal?" | CONTINUIDADE |

**São perguntas ortogonais.** Um shot pode passar anchor em todos os frames mas ter micro-jitter em F2F. Um shot pode ter F2F alta mas estar estabilizado na identidade errada (caso Helena).

---

## Limites Formais

| Limite | Descrição |
|--------|-----------|
| **Não substitui Anchor** | F2F alta não autoriza selagem se anchor falhar |
| **Não participa de gates** | Gate de identidade continua a ser anchor-cosine |
| **Não autoriza selagem** | Ferramenta de diagnóstico, não de aprovação |

---

## Uso Autorizado (Fase 2)

```
1. Localizar transições problemáticas (onde ocorreu a quebra)
2. Distinguir colapso de estabilização errada
3. Investigar micro-jitter
4. Apoiar classificação de causa em SHOT-GRAMMAR-002
5. Auditoria temporal de cenas com movimento
```

---

## Crédito e Nomenclatura

| Item | Valor |
|------|-------|
| **Nome formal** | `F2F-CONTINUITY-METRIC` |
| **Origem** | Ferramenta WINDI, inspirada conceptualmente pelo método Joey |
| **Joey como medicina** | **PENDENTE** — teste separado quando gerarmos shot de movimento pelo pipeline Joey |

> A métrica F2F provou valor. A medicina-Joey (impedir colapso em movimento) continua por provar.

---

## Métricas de Referência

### COLLAPSE (Helena S05-01_v1)

| Métrica | Valor |
|---------|-------|
| Anchor min | 0.2068 |
| Anchor range | 0.7099 |
| F2F min | 0.2921 |
| F2F range | 0.6736 |
| Max delta | 0.3208 |
| Worst transition | frame_01 → frame_02 |
| Classification | **COLLAPSE** |

### STABLE (Alejandro S10-01_v1)

| Métrica | Valor |
|---------|-------|
| Anchor min | 0.9845 |
| Anchor range | 0.0093 |
| F2F min | 0.9907 |
| F2F range | 0.0045 |
| Max delta | 0.0045 |
| Worst transition | frame_01 → frame_02 |
| Classification | **STABLE** |

---

## Próxima Etapa

```
JOEY-F2F-002
Caso: MICRO-JITTER
Objetivo: Testar se F2F detecta instabilidade que anchor mascara
         (shot que passa anchor mas parece visualmente instável)
```

---

## Ficheiros Canónicos

| Ficheiro | Função |
|----------|--------|
| `production/joey_f2f_measure.py` | Script de medição F2F |
| `shots/helena/S05-01_v1_COLLAPSED_joey_f2f.json` | Resultado caso colapsado |
| `shots/alejandro/S10-01_v1_STABLE_joey_f2f.json` | Resultado caso estável |
| `production/JOEY-F2F-001-SEALED.md` | Este documento |

---

## Axioma Selado

> **"Continuidade e identidade são vetores ortogonais. Um shot perfeitamente contínuo pode ser continuamente errado."**

> **"F2F não substitui anchor. F2F complementa anchor ao localizar o instante da costura."**

---

*Liga IA+H · Kempten · 09 Jun 2026*
*"A engenharia derrotou a pirite mais uma vez."*
