# HARTMANN v2b — CHARACTER_STATE (B1)
### W-HIOS-CINEMATIC-SPINE-001 · "O Peso do Eco" CAST

> **Propósito:** Documento canónico que estabelece o personagem DR. HARTMANN.
> É a fonte única de verdade para medições SPINE-CAST em cenas com Hartmann.

**Status:** SEALED
**Created:** 30 Mai 2026 — §293-CAST
**Liga IA+H:** Human Dragon (I9) · Guardian (epistemologia) · Architect (CCode)

---

## 1. PROVENIÊNCIA (GENERATED PORTRAIT)

> **IMPORTANTE:** Esta âncora é de geração dedicada (generated portrait), não extraída
> de uma cena narrativa. Foi criada especificamente para estabelecer identidade canónica
> do personagem, seguindo o "Processo Helena". Alta estabilidade (0.93) porque a geração
> foi optimizada para consistência facial.

| Campo | Valor |
|-------|-------|
| **Anchor Type** | GENERATED_PORTRAIT |
| **Source Video** | hartmann_v2b_anchor_source.mp4 (Veo 3.1) |
| **Source Frame** | frame_01.png |
| **Frame Hash** | `sha256:696114f67f38bee361aaf1bf5284bbf37c78104f485913ba2cedfc0928fa3fed` |
| **Embedding File** | `hartmann.anchor.v2b.CURRENT.npy` |
| **Embedding Hash** | `sha256:0a3d72058c176328b2ec0c3162946eb4fc95b970b51289e8c743accbc467e47e` |

### Cadeia de Proveniência

```
Veo 3.1 generation (portrait prompt)
    ↓ 8s video @ 24fps
hartmann_v2b_anchor_source.mp4
    ↓ frame extraction
frame_01.png
    sha256: 696114f6...
    ↓ InsightFace buffalo_l
hartmann.anchor.v2b.CURRENT.npy
    sha256: 0a3d7205...
```

### Estabilidade Intra-Vídeo

| Frame | Cosine vs Anchor | Veredicto |
|-------|------------------|-----------|
| frame_01 | 1.0000 | ANCHOR |
| frame_02 | 0.9185 | FORENSIC |
| frame_03 | 0.8746 | FORENSIC |
| frame_04 | 0.9260 | FORENSIC |

**Mean:** 0.9298 · **Min:** 0.8746 · **Status:** FORENSIC GRADE

---

## 2. VALIDAÇÃO INTER-ÂNCORA

A âncora foi validada por matriz de ortogonalidade contra os outros membros do CAST:

| Par | Cosine | Status |
|-----|--------|--------|
| Hartmann vs Elisa | -0.0095 | ✅ < 0.65 |
| Hartmann vs Marcus | 0.0818 | ✅ < 0.65 |
| Hartmann vs Thomas | 0.0755 | ✅ < 0.65 |
| Hartmann vs Helena | 0.0495 | ✅ < 0.65 |

**Max cosine inter-âncora:** 0.0818
**Identity Floor:** 0.65
**Resultado:** DISCRIMINATIVO — SPINE-CAST não confunde Hartmann com outros personagens.

---

## 3. TRAÇOS VISUAIS CANÓNICOS

```
CANONICAL APPEARANCE:
A European gentleman in his early 60s. Wavy silver-grey hair, slightly tousled.
Rectangular thin-framed reading glasses (distinctive feature). Short trimmed
salt-and-pepper beard. Kind, scholarly expression with intelligent eyes.
Dark charcoal pinstripe suit, white dress shirt, burgundy tie. Professional
demeanor with warmth. Carries himself with quiet confidence and intellectual
authority. Defense attorney representing Marcus.
```

**Contexto narrativo:** Dr. Hartmann é o advogado de defesa de Marcus — figura
de autoridade académica e competência jurídica. Representa a institucionalidade
que protege o poder. Aparência distinta dos outros personagens masculinos.

---

## 4. CENAS COM HARTMANN

| Cena | Descrição | Mean Cosine | Veredicto |
|------|-----------|-------------|-----------|
| S11 v2b | Die Verteidigung (Escritório) | 0.7032 | OPERATIONAL |
| S19 v2b | Der Einspruch (Tribunal) | 0.7914 | FORENSIC |

**Cross-Scene Continuity:** OPERATIONAL (ambas cenas ≥ 0.65)

---

## 5. INVARIANTES

| Threshold | Value | Status |
|-----------|-------|--------|
| Operational | ≥ 0.65 | LOCKED |
| Forensic | ≥ 0.75 | LOCKED |
| Identity Floor | ≥ 0.65 | LOCKED |

---

## 6. NOTAS DE PRODUÇÃO

### Processo Helena Aplicado

O personagem Hartmann passou pelo "Processo Helena" — criação de âncora dedicada
quando a extracção de cenas existentes não produzia estabilidade suficiente:

1. **Problema original:** S11 e S19 tinham personagens visualmente diferentes
   (S11: 0.77 FORENSIC, S19: 0.23 FAIL — pessoas distintas)

2. **Solução:** Gerar retrato canónico isolado (controlled conditions)
   e usar como referência para regenerar ambas as cenas

3. **Resultado:** Continuidade mensurável cross-scene
   - S11 v2b: 0.7032 OPERATIONAL
   - S19 v2b: 0.7914 FORENSIC

### Ficheiros de Produção

```
/opt/windi/hios/cinema/obras/o-peso-do-eco/scenes/hartmann_v2/
├── hartmann_v2b_anchor_source.mp4   # Vídeo fonte da âncora
├── hartmann_v2b_reference.png       # Frame de referência para --ref
├── S11_hartmann_v2b.mp4             # Cena escritório regenerada
└── S19_hartmann_v2b.mp4             # Cena tribunal regenerada
```

---

*Liga IA+H · WINDI Publishing House · 30 Mai 2026*
*"AI processes. Human decides. WINDI guarantees."*
