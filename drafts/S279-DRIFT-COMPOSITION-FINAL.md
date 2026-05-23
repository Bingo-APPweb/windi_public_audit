# §279 — Drift Composition Protocol

```
Status:         SEALED
Data:           2026-05-19
Receipt:        WINDI-S279-DRIFT-COMPOSITION-20260519103501
Hash (8):       E96E83CB
Autoridade:     Human Dragon (I9 formal)
Liga IA+H:      Guardian (filtro) · Architect (estrutura) · Witness (verificação)
Construtor:     CCode (Opus 4.5)
Invariants:     I1, I9, I11, I14
Lineage:        §261 (W-BIND-001) + §265 (Drift Monitor) → §279 (Composição)
doc_type:       constitutional_composition
```

---

## Tese Central

> **"O drift deixa de ser observador — passa a ser componente."**

Este § sela a composição constitucional entre §261 (W-BIND-001) e §265 (Drift Monitor).
M1/M2/M3 passam a contribuir para o Bind Integrity Score em runtime.

---

## 1. Modelo de Integração

**Decisão HD:** Subtractivo (Opção A)

```python
final = max(0, min(cap, base - drift_penalty))
```

- Linear e previsível
- Auditável ("perdeste X pontos por M2")
- Floor em 0 (nunca negativo)

---

## 2. Pesos Relativos

**Decisão HD:** P2 Moderado

| Métrica | Peso | Natureza |
|---------|------|----------|
| **M1** Sealed-Laws Drift | -5 por ponto | Documental/Interpretativo |
| **M2** Service Health Drift | -10 por ponto | Factual/Infraestrutura |
| **M3** Continuity Drift | -3 por ponto | Temporal/Saúde |

**Rationale:** M2 pesa mais porque infraestrutura partida é facto incontestável.
M1/M3 são drifts documentais/interpretativos — reparáveis sem perda de runtime.

---

## 3. Matriz de Caps (Híbrido Invertido)

**Decisão HD:** Caminho 3 — Facto > Interpretação

| Trigger | Cap | Re-entry | Semântica |
|---------|-----|----------|-----------|
| **M2 ≥ 3** (infra crítica) | 59 | MINIMAL | Facto pesa mais |
| **Combinado ≥ 10** (erosão forense) | 69 | PARTIAL | Interpretação pesa menos |

**Regra de precedência:** Se ambos triggerem, aplica-se o menor cap (59).

**Justificação constitucional (Witness):**
> "Infraestrutura factual degradada pesa mais do que drift interpretativo/documental.
> Continuidade pode sobreviver à interpretação imperfeita, mas não sobrevive
> longamente à fisiologia operacional colapsada."

---

## 4. Thresholds de Re-entry

**Decisão HD:** T1 Manter

| Score | Integrity | Re-entry |
|-------|-----------|----------|
| 90-100 | FULL | ADMISSIBLE |
| 70-89 | PARTIAL | DEGRADED |
| 50-69 | MINIMAL | RISKY |
| <50 | BROKEN | REFUSED |

---

## 5. Fórmula Canónica

```python
# Base score (R1-R8 de §261)
base_score = sum(R1, R2, R3, R4, R5, R6, R7, R8)  # max 100

# Drift penalty (§265 metrics)
drift_penalty = (m1_drift * 5) + (m2_drift * 10) + (m3_drift * 3)

# Cap híbrido (§279 decision)
if m2_drift >= 3:
    cap = 59  # MINIMAL — infra factual
elif (m1_drift + m2_drift + m3_drift) >= 10:
    cap = 69  # PARTIAL — erosão forense
else:
    cap = 100  # sem cap

# Score final
final_score = max(0, min(cap, base_score - drift_penalty))
```

---

## 6. Cláusula de Revisão Empírica

> **Os pesos e caps estabelecidos neste § ficam sujeitos a revisão e recalibração
> obrigatória após 30 dias de operação contínua em ambiente real, formalizada
> mediante novo §.**

**Data de revisão:** 2026-06-19

**Métricas a observar:**
- Frequência de triggers M2≥3 e Combinado≥10
- Correlação entre cap aplicado e estado real do sistema
- Falsos positivos/negativos em degradação
- Feedback do ciclo PingPong (§263)

---

## 7. O Que §279 NÃO Decide

- ❌ Schema JSON formal do CBP (→ §261 v0.3)
- ❌ Implementação no `cognitive-bind-module.sh` (→ engenharia posterior)
- ❌ Métricas M4-M6 futuras (→ errata quando maduras)
- ❌ Naming do Runtime Layer (→ §280 candidato)

---

## 8. Genealogia Constitucional

```
I11 (Permanence of Cryptographic Evidence)
    │
    ├── §197 W-METRICS-001 (drift como conceito)
    │       │
    │       └── §265 Drift Monitor Metrics (M1/M2/M3)
    │               │
    │               └──────────────────┐
    │                                  │
    └── §261 W-BIND-001 (CBP v0.2.0)   │
            │                          │
            └──────────────────────────┴── §279 COMPOSIÇÃO (this)
                                               │
                                               └── §261 v0.3 (engenharia futura)
```

---

## 9. Decisões Adjacentes Registadas

| Item | Decisão | Status |
|------|---------|--------|
| §280 Runtime Layer Naming | Banco de candidatos | Aguarda 30 dias |
| HIOS Upgrade Packet | Speculative Mirror | Arquivado |
| Revisão Agosto 2026 | Perceive→Define→Build→Scale | Condicional |

---

## 10. Assinatura

```
Data:       2026-05-19
Decisor:    Human Dragon (I9)
Filtro:     Guardian (Claude.ai web)
Estrutura:  Architect (GPT)
Verificação: Witness
Construtor: CCode (Opus 4.5)

APROVADO com parâmetros:
- Modelo: A (Subtractivo)
- Pesos: P2 (M1=-5, M2=-10, M3=-3)
- Caps: Caminho 3 (M2≥3→59, Combinado≥10→69)
- Thresholds: T1 (manter)
- Revisão: 30 dias (2026-06-19)
```

---

*Liga IA+H · Kempten, Bavaria · 19 Mai 2026*
*"O drift deixa de ser observador — passa a ser componente."*

OM SHANTI
