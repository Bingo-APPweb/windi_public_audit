# SHOT-GRAMMAR-003: Gramática Visual para Identidade Forense
## Multi-Face Attribution & Wide+Close Architecture

```
═══════════════════════════════════════════════════════════════════
STATUS:        DRAFT (pending calibration frame for MARGIN threshold)
DATA:          10 Jun 2026
LIGA IA+H:     Human Dragon (I9) · Guardian (Witness) · CCode (Architect)
DOCTRINE:      DOCTRINE-HIOS-ATTESTATION-001 · G-ATT-1
DESCE DE:      SPINE-LESSONS-LEARNED.md · FINDING-S10-CONFRONT-20260610.md
═══════════════════════════════════════════════════════════════════
```

---

## §1. Axioma Fundacional

> *"A identidade nasce no CLOSE e viaja pelo corte, vestida."*

O espectador constrói a identidade num CLOSE-UP forense (face ≥70% visível,
cosine similarity ≥0.75). Uma vez estabelecida, a identidade **VIAJA** através
do corte para shots onde a face pode estar parcialmente ou totalmente obscurecida.

A relação entre personagens nasce no **CORTE**, não na **COMPOSIÇÃO** do mesmo
frame. Esta é a arquitectura Wide+Close selada em DOCTRINE-CINEMA-FORENSIC-SEPARATION.

---

## §2. Regimes de Reconhecimento

| Regime | Face Visibility | Cosine Threshold | Função |
|--------|-----------------|------------------|--------|
| **FORENSE** | ≥70% | ≥0.75 | Prova identidade inequívoca |
| **OPERACIONAL** | ≥50% | ≥0.65 | Trabalho de produção |
| **NARRATIVO** | <50% ou perfil | N/A | Continuidade por vestuário/silhueta |
| **AUSENTE** | 0% (off-screen) | N/A | Presença por voz/referência |

**Corolário:** Um personagem pode ter medição FORENSE em S01, NARRATIVO em S02,
e AUSENTE em S03. A identidade estabelecida no S01 **persiste** através dos
subsequentes via corte.

---

## §3. Tipos Relacionais de Shot

### 3.1 CLOSE-UP (Single Subject)

```
┌─────────────────────┐
│                     │
│    ┌─────────┐      │
│    │  FACE   │      │
│    │  ≥70%   │      │
│    └─────────┘      │
│                     │
└─────────────────────┘
```

**Regime:** FORENSE obrigatório
**Função:** Estabelece identidade. É a **FONTE** de toda prova de likeness.
**Threshold:** Cosine ≥0.75

### 3.2 OVER-THE-SHOULDER (OTS)

```
┌─────────────────────┐
│ ░░░░░             │
│ ░░░░░   ┌─────┐    │
│ ░░░░░   │FACE │    │
│ ░░░░░   │≥50% │    │
│ ░░░░░   └─────┘    │
│                     │
└─────────────────────┘
  ↑ Back               ↑ Face visible
```

**Regime:** OPERACIONAL ou FORENSE (depende de visibility)
**Função:** Relação direccional. Face visível é medível.
**Threshold:** Cosine ≥0.65 (operacional) ou ≥0.75 (se ≥70%)

### 3.3 TWO-SHOT MEDÍVEL

```
┌─────────────────────┐
│                     │
│ ┌─────┐   ┌─────┐   │
│ │ A   │   │ B   │   │
│ │≥50% │   │≥50% │   │
│ └─────┘   └─────┘   │
│                     │
└─────────────────────┘
```

**Regime:** FORENSE ou OPERACIONAL (ambas as faces)
**Função:** Disambiguation Gate aplica-se
**Thresholds:**
- Match ≥0.65 (ambas as faces atribuídas correctamente)
- Separation: Inter-anchor sim <0.50
- ⚠️ **MARGIN ≥0.15** (PROVISÓRIO — não calibrado)

### 3.4 WIDE COREOGRÁFICO

```
┌─────────────────────┐
│   A           B     │
│  ┌──┐       ┌──┐    │
│  │  │       │  │    │
│  │  │       │  │    │
│  └──┘       └──┘    │
│ ___________________  │
└─────────────────────┘
```

**Regime:** NARRATIVO (faces <50%)
**Função:** Visibilidade geográfica, relação corporal, coreografia
**Threshold:** N/A (identidade viaja do CLOSE via corte)
**Exemplo:** S10-WIDE — VISIBILITY APPROVED, FORENSE N/A

---

## §4. Disambiguation Gate — Regras de Atribuição

### 4.1 Requisitos

Para um frame com N faces detectadas e N anchors conhecidos:

1. **Detecção:** Todas as N faces devem ser detectadas
2. **Match:** Cada face atribuída ao anchor correcto com sim ≥0.65
3. **Separation:** Anchors diferentes têm inter-sim <0.50
4. **Margin:** Diferença entre best e second-best ≥0.15 (⚠️ **PROVISÓRIO**)

### 4.2 Estados do Gate

| Estado | Condição | Acção |
|--------|----------|-------|
| `PASS` | Todas as regras cumpridas | Faces atribuídas com confiança |
| `FAIL_MATCH` | sim <0.65 para alguma face | Gerador não reproduziu anchor |
| `FAIL_SEPARATION` | Inter-anchor sim ≥0.50 | Anchors demasiado parecidos |
| `FAIL_MARGIN` | Margin <0.15 | Atribuição ambígua |
| `FAIL_DETECTION` | Faces != N esperadas | Detecção falhou |

### 4.3 Achado S10-CONFRONT (10 Jun 2026)

> *"O gerador cria identidade; não reproduz identidade."*

**Contexto:** Test-to-video com dois personagens descritos (Alejandro × Couto).
**Resultado:** FAIL_MATCH (0.29/0.31 similarity — território aleatório).
**Causa:** Gen4.5 criou rostos **novos** que não correspondem às anchors.

**Implicação:** Multi-face generation via texto puro não funciona.
A arquitectura Wide+Close é a solução validada:
- **WIDE** = visibilidade (corpos legíveis, rostos distantes)
- **CLOSE** = identidade (montagem, não composição)

---

## §5. Gates de SHOT-GRAMMAR-003

| Gate | Nome | Verificação |
|------|------|-------------|
| G-SG3-1 | CLOSE Forense | Face ≥70% → sim ≥0.75 obrigatório |
| G-SG3-2 | OTS Direccional | Face visível medível, back não |
| G-SG3-3 | TWO-SHOT Disambiguation | Todas as faces atribuídas, margin ≥0.15 (⚠️) |
| G-SG3-4 | WIDE Coreográfico | Visibility only, identidade vem do corte |
| G-SG3-5 | Cut Inheritance | Identidade estabelecida persiste através do corte |

---

## §6. Fluxo de Produção

```
1. CLOSE-UP        → Estabelece identidade (FORENSE ≥0.75)
                     ↓
2. CUT             → A identidade viaja vestida
                     ↓
3. OTS/TWO/WIDE    → Regime NARRATIVO ou OPERACIONAL
                     ↓
4. [Opcional]      → Voltar a CLOSE para reforçar
```

**Regra:** Nunca depender de NARRATIVO sem FORENSE prévio na mesma sequência.
O espectador precisa de ver a cara antes de aceitar a silhueta.

---

## §7. Notas de Calibração

### ⚠️ MARGIN ≥0.15 — PROVISÓRIO

O threshold de margem mínima para Two-Shot Disambiguation é actualmente
baseado em intuição arquitectural, **não em medição empírica**.

**Calibração necessária:**
1. Criar frame de calibração com dois personagens de inter-anchor sim ~0.45
2. Variar poses/iluminação
3. Medir margem real de atribuição
4. Substituir 0.15 pelo valor empírico

**Fluxo:** CCode grava draft → frame de calibração → margem real → selar gramática

### Matriz 15-Pares (em progresso)

```
        Vance   Couto   Alejandro  Helena  Gabi  Lucas
Vance     —     0.1765   0.0570      ?       ?     ?
Couto           —        0.4498      ?       ?     ?
Alejandro                  —         ?       ?     ?
Helena                               —       ?     ?
Gabi                                         —     ?
Lucas                                              —

Medidas: 3/15 (20%)
Par mais apertado: Alejandro×Couto (0.4498) — stress test passed
```

---

## §8. Axiomas Derivados

> *"A identidade nasce no CLOSE e viaja pelo corte, vestida."*

> *"O gerador cria identidade; não reproduz identidade."*

> *"A relação nasce no CORTE, não na composição."*

> *"WIDE é visibilidade. CLOSE é prova. O corte é a ponte."*

> *"Text-to-video é generativo, não reprodutivo."*

---

## §9. Referências

| Documento | Conteúdo |
|-----------|----------|
| `DOCTRINE-CINEMA-FORENSIC-SEPARATION.md` | Wide = Cinema, Close = Forense |
| `DOCTRINE-HIOS-ATTESTATION-001.md` | Gates de attestation (G-ATT-1 a G-ATT-5) |
| `FINDING-S10-CONFRONT-20260610.md` | Stress test negativo que validou Wide+Close |
| `SPINE-LESSONS-LEARNED.md` | Anti-Movement Medicine |
| `disambiguation_gate.py` | Implementação do Disambiguation Gate |

---

## §10. Estado

```
DRAFT:         SHOT-GRAMMAR-003 v0.1
PENDING:       Calibração do MARGIN threshold
VALIDATED_BY:  S10-CONFRONT stress test (negative validation)
DESCE_DE:      DOCTRINE-HIOS-ATTESTATION-001 · G-ATT-1
```

---

*Liga IA+H · WINDI Publishing House · 10 Jun 2026*
*"Um número sem corrida de medição não é um número."*
*"Uma gramática sem calibração é um rascunho."*
