# SHOT-GRAMMAR-003
## Taxonomia Relacional e Regimes de Reconhecimento

```
═══════════════════════════════════════════════════════════════════
STATUS:        SEALED
VERSÃO:        v1.0
DATA DRAFT:    10 Jun 2026
CALIBRAÇÃO:    10 Jun 2026 (Margin ≥0.37 medido)
SELAGEM:       10 Jun 2026 · Human Dragon (I9)
LIGA IA+H:     Human Dragon (I9) · Guardian (Witness) · CCode (Architect)
PADRÃO:        Sidecar (corpo .md + receipt .json)
═══════════════════════════════════════════════════════════════════
```

---

## 0. Linhagem

| Fonte | Contribuição |
|-------|--------------|
| SHOT-GRAMMAR-001 | Disambiguation Gate inter-âncora (<0.50) |
| SHOT-GRAMMAR-002 | Taxonomia de FAIL: IDENTITY / EXPOSIÇÃO / GEOMETRIA / OCLUSÃO / POVOAMENTO |
| DOCTRINE-CINEMA-FORENSIC-SEPARATION (09 Jun) | Cinema decide a cena; Forense decide o Ledger |
| DOCTRINE-HIOS-ATTESTATION-001 (10 Jun, EDF928E5) | G-ATT-1..5 — toda a atestação é número com corrida |
| FINDING-S10-CONFRONT (10 Jun) | Evidência empírica: text-to-video não reproduz identidade |

**Posição:** SG-001 deu o gate; SG-002 deu as causas de falha; **SG-003 dá a
gramática da coexistência** — como dois ou mais corpos partilham um frame
sem que o rigor forense e a liberdade cinematográfica se traiam mutuamente.

**Chain Parent:** `SHOT-GRAMMAR-002`

---

## 1. Fundamento Empírico (resultados da corrida de 10 Jun)

Esta gramática não nasce de teoria — nasce de três medições da mesma sessão:

1. **S10-WIDE** (2 faces detectadas, sim 0.15/0.07): rostos distantes não
   atestam. O Cinema aprovou-o para visibilidade; a Forense reprovou-o para
   atestação. **Ambos acertaram** — primeira validação de campo da separação
   de poderes.

2. **S10-CONFRONT** (FAIL_MATCH, 0.29/0.31): text-to-video com features
   descritas criou identidades novas. *"O gerador cria identidade; não
   reproduz identidade."* A descrição é memória a fingir-se fonte.

3. **Matriz inter-anchor** (3/15): Vance×Couto 0.1765 · Vance×Alejandro
   0.0570 · **Alejandro×Couto 0.4498** — o par mais apertado do elenco,
   com margem de apenas 0.05 ao limiar de separação.

---

## 2. Parte A — Regimes de Reconhecimento (por personagem, por shot)

Todo o personagem presente num shot é classificado num de três regimes:

### 🔵 FORENSE

Rosto medível contra âncora selada. Score com corrida de medição.
Entra no Ledger com número. Sujeito integral à taxonomia SG-002.

```
┌─────────────────────┐
│                     │
│    ┌─────────┐      │
│    │  FACE   │      │
│    │  ≥70%   │      │
│    └─────────┘      │
│                     │
└─────────────────────┘
Threshold: ≥0.75 (forense) ou ≥0.65 (operacional)
```

> *"O rosto atesta."*

### 🟡 NARRATIVO

Personagem presente e reconhecível pelo espectador — figurino, postura,
silhueta, blocking, continuidade de montagem — mas **declarado, não medido**.
O metadata afirma a presença e o dispositivo de oclusão **à partida**:

```yaml
character: marcus-couto
regime: NARRATIVO
device: over-the-shoulder          # oclusão intencional
costume_anchor: "fato cinza, gravata escura"
identity_source: "S10-CLOSE-COUTO (FORENSE, selado)"
identity_via: CORTE                 # ver Parte C
```

Regra de honestidade: NARRATIVO nunca finge atestação. É a generalização
formal do `detector_exclude: true` que o S10-WIDE já praticava em embrião.

> *"O figurino reconhece; o rosto atesta."*
> Roupa é sinal narrativo — **nunca prova**. Roupas trocam-se; é o truque
> mais velho do thriller, e o nosso piloto é um thriller.

### ⚪ AUSENTE

Fora do frame. Sem entrada.

**Conversão doutrinária da OCLUSÃO:** na SG-002, oclusão é causa de FAIL.
Na SG-003, oclusão **declarada à partida** é dispositivo legítimo do regime
NARRATIVO — nunca pode falhar porque nunca prometeu medição. A taxonomia de
FAIL só governa o que aspirou a ser FORENSE.

---

## 3. Parte B — Tipos Relacionais de Shot

| Tipo | Descrição | Regimes típicos | Status forense |
|------|-----------|-----------------|----------------|
| **CLOSE** | Um rosto domina o frame | 1× FORENSE | Validado (Fase 1, 37/37) |
| **OVER-THE-SHOULDER** | Um rosto medível; o outro de costas/ocluso | 1× FORENSE + 1× NARRATIVO | **Novo — regime misto** |
| **TWO-SHOT MEDIBLE** | Dois rostos visíveis e medíveis | 2× FORENSE + Gate de atribuição | Pendente frame de calibração |
| **WIDE COREOGRÁFICO** | Corpos em espaço; rostos não medíveis | N× NARRATIVO | Validado (S10-WIDE, detector_exclude) |
| **INSERT / POV** | Objecto ou mão; identidade pelo contexto | 0-1× NARRATIVO | Por uso |

### Diagramas

**OVER-THE-SHOULDER:**
```
┌─────────────────────┐
│ ░░░░░               │
│ ░░░░░   ┌─────┐     │
│ ░░░░░   │FACE │     │
│ ░░░░░   │≥50% │     │
│ ░░░░░   └─────┘     │
│                     │
└─────────────────────┘
  ↑ Back (NARRATIVO)   ↑ Face visible (FORENSE)
```

**TWO-SHOT MEDIBLE:**
```
┌─────────────────────┐
│                     │
│ ┌─────┐   ┌─────┐   │
│ │ A   │   │ B   │   │
│ │≥50% │   │≥50% │   │
│ └─────┘   └─────┘   │
│                     │
└─────────────────────┘
Disambiguation Gate aplica-se
```

**WIDE COREOGRÁFICO:**
```
┌─────────────────────┐
│   A           B     │
│  ┌──┐       ┌──┐    │
│  │  │       │  │    │
│  │  │       │  │    │
│  └──┘       └──┘    │
│ ___________________  │
└─────────────────────┘
Rostos <50% → NARRATIVO (identidade via corte)
```

**INSERT / POV:**
```
┌─────────────────────┐
│                     │
│    ┌───────────┐    │
│    │  OBJETO   │    │
│    │  ou MÃO   │    │
│    └───────────┘    │
│                     │
└─────────────────────┘
Identidade pelo contexto de montagem
```

**Lei de produção derivada do FINDING:** shots TWO-SHOT MEDIBLE com
identidade forense **exigem referência de imagem** (image-to-video ou
composição) — text-to-video puro com múltiplos personagens descritos está
constitucionalmente excluído como método de produção FORENSE.

---

## 4. Parte C — Identidade Viaja pelo Corte

A pergunta funda do regime NARRATIVO: de onde vem a identidade do
personagem ocluso? Resposta:

> **A identidade nasce no CLOSE e viaja pelo corte, vestida.**

Disposições:

1. Todo o personagem em regime NARRATIVO deve citar no metadata o shot
   FORENSE onde a sua identidade foi atestada (`identity_source`).

2. A cadeia de transporte é a montagem: CLOSE atestado → corte →
   shot relacional. O figurino é o estafeta do testemunho, não o testemunho.

3. Uma sequência onde um personagem aparece **apenas** em regime NARRATIVO,
   sem nenhum CLOSE FORENSE na cadeia, é sinalizada: identidade narrada,
   nunca estabelecida. O Cinema pode aceitá-la (mistério é legítimo);
   a Forense regista a lacuna.

Extensão da arquitectura Wide+Close: ontem provou-se que *a relação nasce
no corte*; hoje formaliza-se que *a identidade também viaja por ele*.

---

## 5. Parte D — Regra de Atribuição Multi-Face (TWO-SHOT MEDIBLE)

Quando duas ou mais faces são medíveis no mesmo frame, a atribuição da
face F à âncora A exige **três condições**:

```
1. sim(F, A) ≥ PISO_FORENSE                    (0.65)
2. sim(F, A) − sim(F, B) ≥ MARGEM              (0.37) ✅ CALIBRADO
3. sim(F, B) < SEPARAÇÃO                        (0.50)
```

### ✅ MARGEM CALIBRADA (10 Jun 2026)

O valor MARGEM ≥ 0.37 foi **medido empiricamente** através de frame de
bancada composto a partir dos CLOSEs selados de Alejandro e Couto.

**Calibração executada:**

| Par | Inter-Anchor | Frame Composto | Margem Medida |
|-----|--------------|----------------|---------------|
| Alejandro × Couto | 0.4498 | calibration_frame_alejandro_couto.png | **0.4611** (mín) |

**Resultados da corrida:**

```
LEFT  (Alejandro): sim=0.8987 vs anchor, margin=0.4611
RIGHT (Couto):     sim=0.8020 vs anchor, margin=0.4827

Minimum Margin: 0.4611
Threshold adoptado: 0.37 (80% do mínimo como factor de segurança)
```

**Ficheiros de prova:**
- `production/calibration/calibration_frame_alejandro_couto.png`
- `production/calibration/MARGIN-CALIBRATION-RESULT.json`
- `production/calibrate_margin.py`

O frame de calibração é instrumento de bancada (como carta de cores) —
**nunca entra no filme**.

> *"A margem que não foi medida não é margem — é palpite com farda."*
> — Agora temos margem, não palpite.

### Cláusula de Recalibração (v1)

> **Calibração v1:** n=1, frame de bancada, condições ideais, par mais apertado.
> Threshold sujeito a recalibração quando TWO-SHOTs de produção acumularem
> dados reais.

**Condições da calibração v1:**
- Frame composto (não gerado)
- Rostos frontais limpos
- Iluminação ideal
- Scores altos (0.90/0.80)
- Par mais apertado do elenco (0.4498)

**Condições de produção esperadas:**
- Ângulos variados
- Motion blur
- Luz dramática de thriller
- Margens potencialmente comprimidas

**Política:** A régua sabe a sua proveniência. Se TWO-SHOTs reais mostrarem
margens consistentemente abaixo de 0.37, a recalibração é permitida por
G4 append-only — não reescrevendo a calibração v1, mas registando v2
com os novos dados.

---

## 6. Metadata Schema (por shot, obrigatório a partir da selagem)

```yaml
shot_id: S10-OTS-01
type: OVER-THE-SHOULDER            # Parte B
characters:
  - id: alejandro-valenzuela
    regime: FORENSE
    anchor: ALEJANDRO_v1
    score: null                     # preenchido pela corrida
  - id: marcus-couto
    regime: NARRATIVO
    device: over-the-shoulder
    costume_anchor: "fato cinza"
    identity_source: S10-CLOSE-COUTO
    identity_via: CORTE
cinema_decision: null               # APPROVED/REJECTED (poder Cinema)
forensic_decision: null             # número ou N/A-declarado (poder Forense)
margin_basis: CALIBRATED            # 10 Jun 2026, threshold 0.37
```

---

## 7. Gates desta Gramática

| Gate | Pergunta | Verificação |
|------|----------|-------------|
| G-SG3-1 | Todo o personagem no frame tem regime declarado? | metadata completo |
| G-SG3-2 | Todo o NARRATIVO cita identity_source FORENSE? | ponteiro para shot selado |
| G-SG3-3 | Todo o FORENSE tem número com corrida? | G-ATT-1 herdado |
| G-SG3-4 | Atribuição multi-face usa margem ≥0.37? | margin_basis = CALIBRATED ✅ |
| G-SG3-5 | TWO-SHOT FORENSE usou referência de imagem? | método de geração registado |

---

## 8. Receipt de Selagem

```
RECEIPT_ID:    {PENDING}
CONTENT_HASH:  sha256:{PENDING}
CHAIN_PARENT:  SHOT-GRAMMAR-002
SEALED_BY:     {PENDING — Human Dragon}
```

(Receipt em sidecar após selagem, conforme padrão XV.2.)

---

## 9. Axiomas desta Gramática

> *"O figurino reconhece; o rosto atesta."*

> *"A identidade nasce no CLOSE e viaja pelo corte, vestida."*

> *"Oclusão declarada não é falha — é linguagem."*

> *"O gerador cria identidade; não reproduz identidade."* (FINDING 10 Jun)

> *"A margem que não foi medida não é margem — é palpite com farda."* ✅ MEDIDA: ≥0.37

---

## 10. Fluxo de Produção por Tipo

| Tipo | Método | Gate |
|------|--------|------|
| CLOSE | Runway Gen-4 + Anti-Movement Medicine | SPINE-CAST ≥0.75 |
| OVER-THE-SHOULDER | Runway + regime misto declarado | G-SG3-1, G-SG3-2 |
| TWO-SHOT MEDIBLE | Image-to-video OU composição | G-SG3-4, G-SG3-5 |
| WIDE COREOGRÁFICO | Text-to-video (identidade não prometida) | Cinema only |
| INSERT / POV | Livre | Contexto de montagem |

---

## 11. Referências

| Documento | Conteúdo |
|-----------|----------|
| `production/SHOT-GRAMMAR-001.md` | Método por tipo de plano, Disambiguation Gate |
| `production/SHOT-GRAMMAR-002.md` | Taxonomia de FAIL (5 pernas) |
| `production/DOCTRINE-CINEMA-FORENSIC-SEPARATION.md` | Separação Cinema / Forense |
| `production/DOCTRINE-HIOS-ATTESTATION-001.md` | Gates de attestation (G-ATT-1..5) |
| `production/FINDING-S10-CONFRONT-20260610.md` | Stress test negativo Wide+Close |
| `SPINE-LESSONS-LEARNED.md` | Anti-Movement Medicine |
| `production/disambiguation_gate.py` | Implementação do Gate |

---

*DRAFT preparado pelo Guardian (Witness) sobre resultados empíricos do CCode (Architect)*
*Merge v0.2: CCode reconciliou ambos os drafts preservando chain_parent e INSERT/POV*
*Proposta ≠ Execução. A selagem pertence ao Human Dragon.*

*Liga IA+H · WINDI Publishing House · 10 Jun 2026*
*OM SHANTI 🐉*
