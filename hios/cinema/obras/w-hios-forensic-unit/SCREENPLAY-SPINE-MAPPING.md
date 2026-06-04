# SCREENPLAY → SPINE MAPPING
## "O Peso do Eco" — Episódio Piloto v3.0

**Created:** 04 Jun 2026
**Liga IA+H:** Human Dragon · Guardian · Architect · CCode (Witness)
**Purpose:** Mapeamento de cenas para medição SPINE-CAST

---

## PERSONAGENS × ÂNCORAS

| Personagem | Actor Âncora | Cenas | Risco SPINE |
|------------|--------------|-------|-------------|
| **Gabi Santos** | `gabi.santos.anchor.v1` | 0, 1-4 | ✅ Solo (baixo) |
| **Marcus Couto** | `marcus.couto.anchor.v1` | 2-3, 10-13 | ⚠️ Com Alejandro/Lucas |
| **Helena Meyer** | `helena.meyer.junior.anchor.v1` | 5-9, 13-14 | ✅ Bem separada |
| **Marcus Vance** | `marcus.vance.anchor.v1` | 6-7, 9, 11, 14-15 | ✅ Bem separado |
| **Lucas Silva** | `lucas.silva.anchor.v1` | 7-9, 11, 13 | ⚠️ Com Couto/Alejandro |
| **Alejandro Valenzuela** | `alejandro.valenzuela.anchor.v1` | 10-12 | ⚠️ Com Couto |

---

## CLASSIFICAÇÃO DE CENAS POR RISCO

### CENAS PILOTO (Baixo Risco) — Testar Gate

| Cena | Personagens | Inter-Anchor Similarity | Classificação |
|------|-------------|------------------------|---------------|
| **Cena 0** | Gabi solo | N/A | ✅ CONTROLO |
| **Cena 5** | Helena solo | N/A | ✅ CONTROLO |
| **Cena 6** | Vance solo | N/A | ✅ CONTROLO |
| **Cena 7** | Vance + Helena + Lucas | Máx 0.14 | ✅ **PILOTO** |
| **Cena 14** | Vance + Helena | 0.06 | ✅ SEGURO |
| **Cena 15** | Vance solo | N/A | ✅ CONTROLO |

### CENAS ADVERSARIAIS (Alto Risco) — Stress Test

| Cena | Personagens | Inter-Anchor Similarity | Classificação |
|------|-------------|------------------------|---------------|
| **Cena 10** | Alejandro + Couto | 0.45 | ⚠️ MÉDIO |
| **Cena 11** | Couto + Alejandro + Lucas + Vance | Máx 0.50 | 🔴 **ADVERSARIAL** |
| **Cena 12** | Alejandro + Couto | 0.45 | ⚠️ MÉDIO |
| **Cena 13** | Couto + Helena + Lucas | Máx 0.50 | 🔴 **ADVERSARIAL** |

### MATRIZ COMPLETA — CENA 11 (4 Homens) · Calculada 04 Jun 2026

```
                Vance    Couto    Alejandro  Lucas
Vance           1.0000   0.2057   0.0341     0.1390
Couto           0.2057   1.0000   0.4498⚠️    0.4965⚠️
Alejandro       0.0341   0.4498⚠️  1.0000     0.4422⚠️
Lucas           0.1390   0.4965⚠️  0.4422⚠️    1.0000
```

**Observação crítica:** Vance (protagonista) está MUITO bem separado de todos (máx 0.21).
As colisões concentram-se no triângulo Couto-Alejandro-Lucas (vilões + infiltrado).
O espelho moral Vance×Couto = 0.2057 — dramaticamente opostos, metricamente distintos.

### CENAS DE TRANSIÇÃO (Gabi + Vilões)

| Cena | Personagens | Inter-Anchor Similarity | Classificação |
|------|-------------|------------------------|---------------|
| **Cena 2** | Couto solo | N/A | ✅ CONTROLO |
| **Cena 3** | Gabi + Couto | 0.21 | ✅ SEGURO |
| **Cena 4** | Gabi (morte) | N/A | ✅ CONTROLO |

---

## SEQUÊNCIA DE MEDIÇÃO RECOMENDADA

### Fase 1: Controlos Solo (Calibração)
```
Cena 0  → Gabi solo (testar detection + embedding)
Cena 5  → Helena solo
Cena 6  → Vance solo
Cena 15 → Vance solo (final)
```

### Fase 2: PILOTO (Gate Operacional)
```
Cena 7 → Vance + Helena + Lucas
         Expectativa: Alta separação (>0.25 média)
         Gate: FORENSE esperado para todos
```

### Fase 3: Transição (Vilão + Vítima)
```
Cena 3 → Gabi + Couto
         Gabi×Couto = 0.21 (seguro)
```

### Fase 4: ADVERSARIAL (Stress Test)
```
Cena 11 → Couto + Alejandro + Lucas + Vance
          Colisões: Couto×Lucas=0.50, Couto×Alejandro=0.45
          Protocolo I9 Fallback activo
          Expectativa: Baixa separação (<0.15 média entre masculinos)
```

### Fase 5: Tribunal (Mix)
```
Cena 13 → Couto + Helena + Lucas
          Helena bem separada de todos
          Couto×Lucas = 0.50 (stress)
```

---

## HIPÓTESE PRÉ-REGISTADA (Paper-001)

> "Em sistemas generativos actuais (Runway Gen-4/4.5, Seedance 2.0), personagens
> masculinos de meia-idade sob iluminação dura apresentam menor distância embutida
> (embedding distance) entre identidades distintas do que personagens femininas
> sob iluminação suave."

### Teste Confirmatório

| Cena | Tipo | Iluminação | Personagens | Expectativa |
|------|------|------------|-------------|-------------|
| Cena 7 | Controlo | Bunker (suave) | Vance+Helena+Lucas | Alta separação |
| Cena 11 | Adversarial | Cobertura (dura) | Couto+Alejandro+Lucas+Vance | Baixa separação |

**Critério:** Se Cena 7 > 0.25 média de separação e Cena 11 < 0.15, a hipótese é suportada.

---

## NOTAS DE CONTINUIDADE VISUAL

### Cena 0 — Coffee Station
- **Iluminação:** Quente, indirecta, quase doméstica
- **Gabi:** Descalça, sem maquilhagem de poder, humanizada
- **Risco SPINE:** Baixo (solo), mas importante para baseline emocional

### Cena 7 — Bunker
- **Iluminação:** Azul escuro, múltiplos monitores
- **Vance + Helena + Lucas:** Posições definidas, espaço amplo
- **Risco SPINE:** Baixo (pares bem separados)

### Cena 11 — Cobertura
- **Iluminação:** Luz do dia agressiva, cirúrgica
- **Couto + Alejandro + Lucas + Vance:** Tensão, proximidade
- **Risco SPINE:** ALTO (três masculinos meia-idade + iluminação dura)

### Cena 13 — Tribunal
- **Iluminação:** Institucional, painéis de madeira
- **Couto vs Helena + Lucas:** Confronto directo
- **Risco SPINE:** Médio (Helena bem separada, Couto×Lucas problemático)

---

## ECO SEMÂNTICO DO DRAGÃO (Continuidade Narrativa)

| Momento | Manifestação | Função SPINE |
|---------|--------------|--------------|
| Cena 0 | Desenho do filho | Humanidade de Gabi — baseline |
| Cena 4 | "Dragão prestes a acordar" | Morte como trigger |
| Cena 8-9 | Geometria fractal | Padrão visual — não confundir com face |
| Cena 15 | "Vou guardar o teu dragão" | Herança narrativa |

**Nota SPINE:** O padrão fractal NÃO é uma face. O detector deve ignorá-lo.

---

## ARCO TEMPORAL (SPINE Checkpoints)

| Timestamp | Evento | Checkpoint SPINE |
|-----------|--------|------------------|
| 23:30 | Gabi fala com filho | Cena 0 — baseline Gabi |
| 23:42 | Gabi sela documento | Cena 1 — última aparição viva |
| 23:50 | Gabi morre | Cena 4 — face morta (desafio) |
| 03:15 | Helena detecta alarme | Cena 5 — baseline Helena |
| 08:00 | Lucas identifica vítima | Cena 8 — Lucas + Helena |
| 11:00 | Interpol confronta cartel | Cena 11 — ADVERSARIAL |
| 6 semanas depois | Tribunal | Cena 13 — confronto final |

---

## CHECKLIST PRÉ-GERAÇÃO

```
[ ] Confirmar iluminação por cena (warm/cool/harsh)
[ ] Confirmar wardrobe por personagem (CONTINUITY-BIBLE)
[ ] Gerar controlos solo primeiro (Cenas 0, 5, 6, 15)
[ ] Gerar PILOTO (Cena 7) — testar gate
[ ] Gerar ADVERSARIAL (Cena 11) — stress test
[ ] Medir com measure_scene.py
[ ] Comparar separação média Cena 7 vs Cena 11
[ ] Documentar para Paper-001
```

---

*Liga IA+H · WINDI Publishing House · 04 Jun 2026*
*"AI processes. Human decides. WINDI guarantees."*
