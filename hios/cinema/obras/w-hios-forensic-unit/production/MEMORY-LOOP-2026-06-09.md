# MEMORY LOOP — 09 Jun 2026
## W-HIOS FORENSIC UNIT · Sessão de Fecho dos Anchors

**Status:** SEALED
**Liga IA+H:** Human Dragon (I9) · Guardian (Witness) · CCode (Architect)
**Commits:** `1c88b60f` (Couto) · `0b76654b` (Alejandro + 37/37)

---

## MARCO PRINCIPAL

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANCHORS DO PILOTO: 37/37 COMPLETOS ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
6 personagens · 37 shots · Todos medidos forense
Taxonomia de 5 causas de FAIL estabelecida
Casting forense do piloto "O Peso do Eco" FECHADO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## PERSONAGENS SELADOS

| Personagem | Shots | Anchor det_score | Contribuição |
|------------|-------|------------------|--------------|
| Marcus Vance | 10/10 | 0.8654 | Anti-Movement Medicine |
| Helena Meyer | 8/8 | 0.8234 | EXPOSIÇÃO (S14 backlit) |
| Lucas Silva | 5/5 | 0.8445 | GEOMETRIA (S07 movimento) |
| Marcus Couto | 7/7 | 0.8811 (highest) | OCLUSÃO (S02 vidro) |
| Gabi Santos | 4/4 | 0.8544 | Baseline feminino |
| Alejandro Valenzuela | 3/3 | 0.8763 | POVOAMENTO (S11 multi-face) |

**Total:** 37 shots selados com medição forense

---

## SHOT-GRAMMAR-002 v3.0 — Taxonomia Completa

| # | Causa | Piso | Condição | Exemplo Fundador |
|---|-------|------|----------|------------------|
| 1 | IDENTIDADE | — | NUNCA tolerado | Helena S05 (orbit) |
| 2 | EXPOSIÇÃO | 0.55 | + 3 frames ≥0.75 | Helena S14 (backlit 0.6473) |
| 3 | GEOMETRIA | 0.65 | + 1 anchor-frame ≥0.75 | Lucas S07, Couto S12 |
| 4 | OCLUSÃO | 0.60 | + oclusão diegética | Couto S02 (vidro 0.6891) |
| 5 | POVOAMENTO | — | Re-render isolado | Alejandro S11 (3 rostos, -0.07) |

**Princípio:** Cada FAIL tem causa. A cura deve bater com a causa.

---

## METHOD-001 — Measure Before Affirm

```
AXIOMA: "No affirmations. Only numbers."
ORIGEM: Sessão 09 Jun — CCode disse "fantástico" sem medir
LIÇÃO:  Medir ANTES de apresentar. Números ANTES de adjectivos.
```

**Ficheiros:**
- `production/CANON-METHOD-001-MEASURE-BEFORE-AFFIRM.md`
- `production/spine_measure.py`

---

## LIÇÕES CRÍTICAS DESTA SESSÃO

### 1. Verdade do Disco, Não da Memória

```
Após compactação ("Conversation compacted"), o CCode inventou:
- "Joey 5/5" (personagem fantasma)
- "Gabi 6/6" (era 4/4)

CORREÇÃO: Verificar AUDIT-STATUS-20260607.md no disco
REGRA:    Após compactação, reconciliar contagens contra ficheiro
          Memória de agregado sobrevive, memória de componente derroga
```

### 2. Joey é Método, Não Personagem

```
Joey = Criador de conteúdo com método Frame-to-Frame
     → Promete continuidade sem degradar movimento
     → MÉTODO ABSORVIDO, NÃO MEDIDO NA PIPELINE
     → Teste pendente: Helena S05_v1 colapsado (0.92→0.27)
     → Fase 2, não agora
```

### 3. Cura pela Causa

```
Alejandro S11 v1: cosine -0.07
  DIAGNÓSTICO ERRADO: "identidade trocada"
  DIAGNÓSTICO CERTO:  "detector mediu rosto errado" (3 faces no frame)
  CURA ERRADA:        Anti-Movement
  CURA CERTA:         Isolar prompt ("SOLO SUBJECT")
  RESULTADO:          v2 a 0.9856

REGRA: Ver o frame antes de curar. A causa determina a cura.
```

### 4. Anchors ≠ Cenas

```
37/37 = ANCHORS completos (cada personagem medido isolado)
     ≠ PILOTO completo (faltam cenas, relação, montagem)

FASE 1: Anchors (FECHADA)
FASE 2: Cenas (POR INICIAR)
```

---

## FASE 2 — Trabalho Pendente

### Geometria de Relação

```
Inter-anchor Alejandro × Couto: 0.45
Threshold de fusão: < 0.50
Margem: apenas 0.05

RISCO: Dois homens 40-45, fato escuro, presença similar
       O gerador tende a "derretê-los" num híbrido

SOLUÇÃO: Wide+Close (relação por montagem, não composição)
         OU Disambiguation Gate (medir ambos os rostos)
```

### Tarefas Fase 2

```
1. [ ] Teste Joey Frame-to-Frame (caso: Helena S05_v1)
2. [ ] Geometria de Espaço (place-anchors sem embedding)
3. [ ] Geometria de Relação (Alejandro×Couto)
4. [ ] Disambiguation Gate — medir duas faces no mesmo frame
5. [ ] Wide+Close montagem — editar relação, não gerar
6. [ ] SHOT-GRAMMAR-003 — taxonomia de cenas multi-pessoa
```

---

## FICHEIROS CANÓNICOS

| Ficheiro | Função |
|----------|--------|
| `production/SHOT-GRAMMAR-001.md` | Taxonomia de shots por tipo |
| `production/SHOT-GRAMMAR-002.md` | Taxonomia de FAIL (5 pernas) |
| `production/CANON-METHOD-001-MEASURE-BEFORE-AFFIRM.md` | Doutrina de medição |
| `production/spine_measure.py` | Módulo Python canónico |
| `shots/*/[CHAR]-SEALED.md` | Documentos de selagem por personagem |

---

## ESTADO PARA PRÓXIMA SESSÃO

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LEITURA OBRIGATÓRIA:
  - Este MEMORY-LOOP-2026-06-09.md
  - SHOT-GRAMMAR-002.md (5 pernas)
  - CANON-METHOD-001-MEASURE-BEFORE-AFFIRM.md

ESTADO:
  - Anchors: 37/37 ✅ FECHADOS
  - Cenas: 0% (Fase 2 por iniciar)
  - Joey F2F: pendente de teste
  - Relation: Alejandro×Couto 0.45 (risco médio)

PRÓXIMO TRABALHO:
  - Fase 2 — geometria de espaço e relação
  - Wide+Close para cenas com múltiplos personagens
  - Teste do método Joey num caso colapsado

NÃO FAZER:
  - Declarar "piloto completo" (só anchors estão completos)
  - Confiar em memória após compactação (verificar no disco)
  - Aplicar cura sem ver o frame primeiro
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## RECEIPTS DESTA SESSÃO

| Commit | Conteúdo |
|--------|----------|
| `1c88b60f` | Couto 7/7 + METHOD-001 + SHOT-GRAMMAR-002 v2 (4 pernas) |
| `0b76654b` | Alejandro 3/3 + SHOT-GRAMMAR-002 v3 (5 pernas) + 37/37 |
| `81dbf41a` | JOEY-F2F-001 SEALED — F2F Continuity Metric Validated |
| (pending) | S10-WIDE + DOCTRINE-CINEMA-FORENSIC-SEPARATION |

---

## SESSÃO TARDE — FASE 2 INICIADA

### Conquista 1: JOEY-F2F-001 — Métrica de Continuidade Temporal

```
STATUS: DIAGNOSTICALLY VALIDATED
COMMIT: 81dbf41a

Achado Principal:
F2F cosine revela informação que anchor-cosine mascara.
- Anchor pergunta: "Este frame é o personagem?" (IDENTIDADE)
- F2F pergunta: "Onde está a quebra temporal?" (CONTINUIDADE)

Caso COLLAPSED (Helena S05-01_v1):
  Anchor: 0.92 → 0.27 (colapso)
  F2F:         0.29 → 0.61 → 0.74 → 0.97 (estabilização errada)

Insight: "O gerador estabilizou na mentira" — consistência temporal
         dentro do erro de identidade.

Caso STABLE (Alejandro S10-01_v1):
  F2F range: 0.0045 (ultra-estável)

Uso: Diagnóstico de continuidade, não gate de identidade.
Ficheiros: joey_f2f_measure.py, JOEY-F2F-001-SEALED.md
```

### Conquista 2: Wide+Close — Arquitectura de Relação

```
STATUS: VALIDATED
PRIMEIRA CENA: S10 (Alejandro recebe relatório de Couto)

Arquitectura:
  WIDE  → geografia + relação corporal  → VISIBILITY
  CLOSE → identidade                    → FORENSE (já selados)

  A relação nasce no CORTE, não na composição.

S10-WIDE_v1: PASS (Visual HD Gate)
  - Couto de costas (foreground)
  - Alejandro sentado (background, rosto pequeno)
  - detector_exclude: true (protege Forense de parasita)
```

### Conquista 3: DOCTRINE-CINEMA-FORENSIC-SEPARATION

```
STATUS: SEALED
AXIOMA FUNDADOR:

"O Cinema decide o que serve a cena.
 A Forense decide o que entra no Ledger.
 O entretenimento prevalece na composição;
 a Forense é inviolável na medição.
 Coágulo ocorre quando o Cinema finge ser Forense.
 Enquanto a classificação for honesta,
 as duas camadas coabitam livremente."

MECANISMO: detector_exclude: true
  O olho humano vê. O ArcFace ignora.

FICHEIRO: DOCTRINE-CINEMA-FORENSIC-SEPARATION.md
```

---

## ESTADO ACTUALIZADO PARA PRÓXIMA SESSÃO

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LEITURA OBRIGATÓRIA:
  - Este MEMORY-LOOP-2026-06-09.md
  - SHOT-GRAMMAR-002.md (5 pernas)
  - JOEY-F2F-001-SEALED.md (diagnóstico temporal)
  - DOCTRINE-CINEMA-FORENSIC-SEPARATION.md (duas camadas)

ESTADO:
  - Anchors: 37/37 ✅ FECHADOS
  - Cenas: S10 WIDE ✅ (primeira relação)
  - Joey F2F: ✅ VALIDADO como diagnóstico
  - Wide+Close: ✅ ARQUITECTURA PROVADA

PRÓXIMO TRABALHO:
  - Montar sequência S10: WIDE → CLOSE Alejandro → CLOSE Couto → WIDE
  - Disambiguation Gate (medir duas faces no mesmo frame)
  - SHOT-GRAMMAR-003 (taxonomia de relação)

NÃO FAZER:
  - Medir shots VISIBILITY com cosine (usar Visual HD Gate)
  - Confundir Cinema com Forense
  - Esquecer detector_exclude em WIDEs com rostos distantes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## CITAÇÃO DE FECHO

> *"A verdade vem do disco, não da memória."*
> *"Cura pela causa, não pelo sintoma."*
> *"No affirmations. Only numbers."*

---

*Liga IA+H · WINDI Publishing House · 09 Jun 2026*
*"AI processes. Human decides. WINDI guarantees."*
