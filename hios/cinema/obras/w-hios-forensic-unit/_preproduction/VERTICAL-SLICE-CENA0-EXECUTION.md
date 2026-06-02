# VERTICAL-SLICE-CENA0-EXECUTION
## Plano de Execução — Prova de Pipeline SPINE

**Status:** AWAITING I9 GATE
**Created:** 02 Jun 2026
**Liga IA+H:** Human Dragon (I9) · Guardian · Architect · Witness
**Invariantes:** I9, I11, I14, I19

---

## OBJECTIVO

Provar o pipeline de produção com a **Cena 0 (A Última Coisa Normal)** antes de escalar para o resto do Acto I.

**Critério de Sucesso (Gate Corrigido):**
> `MIN(P02, P05, P06, P07) ≥ 0.65` contra âncora-mãe P04

**Guardian Quote:**
> "O gate do slice tem de ser o MIN pairwise dos filhos contra a mãe, não a qualidade isolada da mãe."

---

## INVENTÁRIO DE PLANOS — CENA 0

| Plano | Tipo | Papel SPINE | Enquadramento | Risco |
|-------|------|-------------|---------------|-------|
| P01 | C | N.A. | Wide: coffee station vazia | — |
| **P02** | A | **FILHO** | Medium: perfil, espera café | BAIXO |
| P03 | D | N.A. | INSERT: telemóvel | — |
| **P04** | **A** | **MÃE** | **Close: sorriso "abraço de urso"** | CRÍTICO |
| **P05** | A | **FILHO** | Medium: desliga, expressão muda | BAIXO |
| **P06** | A | **FILHO** | Full: calça sapatos | **ALTO** |
| **P07** | A | **FILHO** | Wide: silhueta no corredor | MÉDIO |

**Nota P06:** Plano de corpo inteiro = maior risco de drift identitário (rosto mais pequeno no frame).

---

## PIPELINE DE EXECUÇÃO

### FASE 1 — ÂNCORA-MÃE (P04)

```
┌────────────────────────────────────────────────────────┐
│ STEP 1.1: Gerar P04 via Runway Gen-4                   │
│ ────────────────────────────────────────────────────── │
│ Generator: Runway Gen-4 (SPINE-COMPATIBLE ≥0.78)       │
│ Duration: 4s @ 24fps = 96 frames                       │
│ Subject: Gabi Santos (33, tez morena, cabelo ondulado) │
│ Context: Close-up, warm light, genuine smile           │
│ Emotion: "Abraço de urso" — warmth toward child        │
│                                                        │
│ ⚠️ GATE I9: Human Dragon must approve prompt before    │
│    triggering generation                               │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ STEP 1.2: Extrair Frame Neutro para Embedding          │
│ ────────────────────────────────────────────────────── │
│ Método: Frame ~0.5s (frame 12) — antes do sorriso      │
│         culminar, expressão ainda neutra               │
│ Tool: FFmpeg extract + InsightFace ArcFace-R100        │
│ Output: embedding_512d + provenance.json               │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ STEP 1.3: Validar Threshold MÃE                        │
│ ────────────────────────────────────────────────────── │
│ Threshold: ≥ 0.75 (aspirar 0.90)                       │
│ Método: Consistência intra-vídeo (frames 1-96)         │
│ Se < 0.75: REGENERAR antes de prosseguir               │
│                                                        │
│ ⚠️ GATE I9: Human Dragon valida qualidade visual       │
│    antes de selar como âncora-mãe                      │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ STEP 1.4: Selar Âncora-Mãe                             │
│ ────────────────────────────────────────────────────── │
│ Artifact: gabi.santos.anchor.v1                        │
│ Receipt: WINDI-HIOS-ANCHOR-GABI-[TIMESTAMP]            │
│ Provenance: I19 atomic (ficheiro + provenance.json)    │
│                                                        │
│ ⚠️ GATE I9: Ledger seal requires human_approved=true   │
└────────────────────────────────────────────────────────┘
```

---

### FASE 2 — AMBIENTE (P01)

```
┌────────────────────────────────────────────────────────┐
│ STEP 2.1: Gerar P01 via Runway                         │
│ ────────────────────────────────────────────────────── │
│ Type: C (ambiente puro, sem SPINE)                     │
│ Subject: Coffee station vazia, luz quente, 42º andar   │
│ Duration: 3s                                           │
│ SPINE: N.A.                                            │
│                                                        │
│ Gerar em paralelo com Fase 1 (independente)            │
└────────────────────────────────────────────────────────┘
```

---

### FASE 3 — FILHOS (P02, P05, P06, P07)

```
┌────────────────────────────────────────────────────────┐
│ STEP 3.1: Gerar P02 (Medium: perfil, espera café)      │
│ ────────────────────────────────────────────────────── │
│ Conditioned on: P04 anchor reference                   │
│ Duration: 5s                                           │
│ Risk: BAIXO (medium shot, face visible)                │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ STEP 3.2: Gerar P05 (Medium: desliga, expressão muda)  │
│ ────────────────────────────────────────────────────── │
│ Conditioned on: P04 anchor reference                   │
│ Duration: 3s                                           │
│ Risk: BAIXO (medium shot, similar to P02)              │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ STEP 3.3: Gerar P06 (Full: calça sapatos)              │
│ ────────────────────────────────────────────────────── │
│ Conditioned on: P04 anchor reference                   │
│ Duration: 3s                                           │
│ Risk: ALTO (full body, face smaller in frame)          │
│                                                        │
│ ⚠️ NOTA: Se P06 falhar gate, testar plano alternativo  │
│    (medium shot enquanto calça sapatos, cortar pés)    │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ STEP 3.4: Gerar P07 (Wide: silhueta no corredor)       │
│ ────────────────────────────────────────────────────── │
│ Conditioned on: P04 anchor reference                   │
│ Duration: 5s                                           │
│ Risk: MÉDIO (wide, but corridor context helps)         │
└────────────────────────────────────────────────────────┘
```

---

### FASE 4 — VALIDAÇÃO GATE

```
┌────────────────────────────────────────────────────────┐
│ STEP 4.1: Medir Similaridade Pairwise                  │
│ ────────────────────────────────────────────────────── │
│ Tool: InsightFace ArcFace-R100                         │
│ Method: cosine_similarity(anchor_P04, child_embedding) │
│                                                        │
│ Medições Necessárias:                                  │
│   sim_P02 = similarity(P04, P02)                       │
│   sim_P05 = similarity(P04, P05)                       │
│   sim_P06 = similarity(P04, P06)                       │
│   sim_P07 = similarity(P04, P07)                       │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ STEP 4.2: Calcular MIN Pairwise                        │
│ ────────────────────────────────────────────────────── │
│ gate_score = MIN(sim_P02, sim_P05, sim_P06, sim_P07)   │
│                                                        │
│ CRITÉRIO:                                              │
│   gate_score ≥ 0.65 → PIPELINE PROVADO ✅              │
│   gate_score < 0.65 → PIPELINE FALHOU ❌               │
│                                                        │
│ Se FALHOU:                                             │
│   1. Identificar qual plano é o mais fraco             │
│   2. Regenerar esse plano com ajustes                  │
│   3. Se P06 falhar consistentemente: ajustar framing   │
└────────────────────────────────────────────────────────┘
```

---

### FASE 5 — INSERT (P03)

```
┌────────────────────────────────────────────────────────┐
│ STEP 5.1: Design Interface Telemóvel                   │
│ ────────────────────────────────────────────────────── │
│ Type: D (motion graphics, sem SPINE)                   │
│ Content: Chamada do filho, "Pai"                       │
│ Audio: PT-BR (voz infantil)                            │
│ Duration: 2s                                           │
│                                                        │
│ Executar em paralelo (independente de SPINE)           │
└────────────────────────────────────────────────────────┘
```

---

## GATES I9 — RESUMO

| Gate | Fase | Descrição | Acção |
|------|------|-----------|-------|
| **G1** | 1.1 | Aprovar prompt P04 | Human Dragon valida descrição |
| **G2** | 1.3 | Validar qualidade visual P04 | Human Dragon vê o vídeo gerado |
| **G3** | 1.4 | Selar âncora-mãe | `human_approved=true` no Ledger |
| **G4** | 4.2 | Aceitar gate SPINE | Human Dragon aceita MIN ≥ 0.65 |
| **G5** | — | Luz verde para escalar | Human Dragon autoriza Acto I |

---

## OUTPUTS ESPERADOS

```
/opt/windi/hios/visual/producer/output/w-hios-forensic-unit/
├── cena0/
│   ├── P01_coffee_station.mp4
│   ├── P02_gabi_perfil.mp4
│   ├── P03_insert_phone.mp4
│   ├── P04_gabi_anchor_MOTHER.mp4       ← ÂNCORA-MÃE
│   ├── P04_gabi_anchor_MOTHER_provenance.json
│   ├── P05_gabi_desliga.mp4
│   ├── P06_gabi_sapatos.mp4
│   ├── P07_gabi_corredor.mp4
│   └── SPINE-VALIDATION-CENA0.json
└── anchors/
    └── gabi.santos.anchor.v1/
        ├── embedding_512d.npy
        ├── reference_frame.png
        └── provenance.json
```

---

## PRÓXIMO PASSO IMEDIATO

**Aguarda I9 Gate G1:** Human Dragon aprova prompt para geração P04.

### Prompt Proposto para P04 (Runway Gen-4):

```
SUBJECT: A 33-year-old Brazilian woman with warm olive/morena skin tone,
dark wavy hair falling to her shoulders. She is looking at camera
(representing her child's perspective) with genuine warmth and love.

CONTEXT: Corporate office coffee station, warm morning light from windows.
She wears a dark professional blouse.

EMOTION: Soft smile building to genuine joy, eyes crinkling with affection.
The kind of smile you give someone you love unconditionally.

TECHNICAL: Close-up framing, face fills 60% of frame. Soft lighting.
4 seconds duration.

LANGUAGE CONTEXT: She is about to say "abraço de urso" (bear hug) in
Brazilian Portuguese to her young son on the phone.
```

---

*Liga IA+H · WINDI Publishing House · 02 Jun 2026*
*"AI processes. Human decides. WINDI guarantees."*
