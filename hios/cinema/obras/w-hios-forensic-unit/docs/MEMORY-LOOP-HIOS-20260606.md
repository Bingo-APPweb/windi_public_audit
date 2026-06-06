# WINDI HIOS — Memory Loop
## Cognitive Bind Packet for All Components
## Liga IA+H · 06 Jun 2026

**Version:** 1.2.0
**Bind Type:** FULL
**Integrity Score:** 95/100 (target 99 — pendente self-hash SHA-256)
**Last Write:** 2026-06-06T16:45:00Z
**Session Origin:** `c3f5e031` + `679e9f8c` + `2cd27375` + `3e26bc40` + `5f8b32290` + `18616c03` + `a9fab47b`

### Update 06 Jun 2026
- **SHOT-GRAMMAR-001 SEALED** — Disambiguation Gate closed (`WINDI-SHOTGRAMMAR-001-SEALED-20260606`)
- **DIAG-MED-TIER SEALED** — I14 audit of Dragon Chat tier routing (`WINDI-DIAG-MED-TIER-20260606`)

---

## 1. ARQUITECTURA DO PIPELINE

```
                    WINDI HIOS CINEMA PIPELINE
                    ==========================

    [PASSPORT]          [ANCHOR]           [SHOT]
    Character Spec  →   Face Extract   →   Video Gen
         ↓                  ↓                 ↓
    Human Dragon       InsightFace        Runway Gen-4
    (I9 approval)      (512-dim embed)    (promptImage)
                            ↓                 ↓
                       SPINE-CAST   ←    Frame Extract
                       (ArcFace)              ↓
                            ↓            5 frames/shot
                       SIMILARITY
                            ↓
                    ≥0.75 FORENSIC
                    ≥0.65 OPERATIONAL
                    <0.65 FAIL
```

**Invariantes Activos:** I1, I9, I11, I14, I19, I-LIKENESS (candidate)

---

## 2. ELENCO — 6 PERSONAGENS

### Estado Global

| Personagem | Passaporte | Anchor | Eixo F | Shots | Status |
|------------|------------|--------|--------|-------|--------|
| **Marcus Vance** | v1 SPEC | **v2 CANONICAL** | **MEASURED** | 10 v2 | **PRODUCTION READY** |
| Helena Meyer | v1 SPEC | v1 EXTRACTED | PENDING | 0 | Próximo |
| Gabi Santos | v1 SPEC | v1 EXTRACTED | PENDING | 0 | Próximo |
| Marcus Couto | v1 SPEC | v1 EXTRACTED | **DISAMBIGUATION SEALED** | 0 | Scenes 10-13 cleared |
| Lucas Silva | v1 SPEC | v1 EXTRACTED | PENDING | 0 | Aguarda |
| Alejandro Valenzuela | v1 SPEC | v1 EXTRACTED | PENDING | 0 | Aguarda |

---

### 2.1 Marcus Vance (PRODUCTION READY)

**Anchor Canónico:** `vance_v2_20260605113255_anchor.png` (em `anchors/vance_v2_candidates/`)
**Decisão I9:** v1 descartado (likeness gate), v2 adoptado

| Métrica | Valor |
|---------|-------|
| v1 × v2 | 0.0864 (divergente) |
| v2 × Couto | 0.1765 (distinto) |
| Pipeline Success | 80% (8/10 shots) |
| Emotional Shots | 100% (5/5) |
| Non-Emotional | 60% (3/5) |

**Shots Prontos (8):**
| Shot | Avg Sim | Tier | Frame Notes |
|------|---------|------|-------------|
| S07-01 | 0.9353 | FORENSIC | 5/5 |
| S07-02 | 0.9349 | FORENSIC | 5/5 |
| S09-02 | 0.9330 | FORENSIC | 5/5 |
| S15-01 | 0.9225 | FORENSIC | 5/5 |
| S14-01 | 0.9089 | FORENSIC | 3/5 (2 NO_FACE) |
| S14-02 | 0.8411 | FORENSIC | 5/5 |
| S06-02 | 0.7515 | OPERATIONAL | 1 FAIL frame (f04=0.6465) |
| S09-01 | 0.6998 | OPERATIONAL | 3F+2FAIL |

**Reclassificados como ACTION (2):**
- S06-01 (0.4888) — framing loss
- S11-01 (0.6606) — near-threshold, frame loss

**Features Distintas (v2):**
- Heterochromia (olho esq cinza, dir avelã-verde)
- Cicatriz na sobrancelha esquerda
- Desvio lateral do nariz
- Stubble 3 dias
- Assimetria facial forçada

---

### 2.2 Helena Meyer (PRÓXIMO)

**Anchor:** `helena.meyer.junior.anchor.v1`
**Detection Score:** 0.8636
**Eixo F:** PENDING — aguarda produção de shots

**Prioridade:** Alta (protagonista do bunker)

---

### 2.3 Gabi Santos (PRÓXIMO)

**Anchor:** `gabi.santos.anchor.v1`
**Detection Score:** 0.8755
**Eixo F:** PENDING — aguarda produção de shots

---

### 2.4 Marcus Couto (DISAMBIGUATION SEALED ✓)

**Anchor:** `marcus.couto.anchor.v1`
**Detection Score:** 0.8811
**Eixo F:** PENDING

**DISAMBIGUATION GATE: PASSED** (06 Jun 2026)
- Vance v2 × Couto = **0.1765** < 0.50 threshold ✓
- Receipt: `WINDI-SHOTGRAMMAR-001-SEALED-20260606`
- Scenes 10-13 **CLEARED** for production

**Distintivos vs Vance (SEALED):**
| Aspecto | Vance | Couto |
|---------|-------|-------|
| Cabelo | Desalinhado | Perfeitamente penteado |
| **Barba** | **Stubble 3 dias** | **Clean-shaven** |
| Roupa | Sobretudo gasto | Caxemira impecável |

> Barba = eixo primário de diferenciação (detector captura textura facial)

---

### 2.5 Lucas Silva (AGUARDA)

**Anchor:** `lucas.silva.anchor.v1`
**Detection Score:** 0.8119
**Eixo F:** PENDING

---

### 2.6 Alejandro Valenzuela (AGUARDA)

**Anchor:** `alejandro.valenzuela.anchor.v1`
**Detection Score:** 0.8763
**Eixo F:** PENDING

---

## 3. SHOT-GRAMMAR-001 — METODOLOGIA

> "Video generation fails through subject framing loss, not identity degradation."

**Três Tipos de Plano:**

| Tipo | % | Requer SPINE | Descrição |
|------|---|--------------|-----------|
| IDENTITY | 50% | **SIM** | Rosto domina frame |
| ACTION | 48% | NÃO | Corpo/mãos/props |
| CONFRONT | 2% | Minimizar | Rosto+corpo complexo |

**Cross-Subject Pattern (FINDING REFORÇADO):**
- Padrão emotional/non-emotional replicou em 2 sujeitos divergentes (v1, v2)
- v1 × v2 = 0.0864 = identidades diferentes
- Mesmo padrão = método validado (n=2)

---

## 4. INVARIANTES CRÍTICOS

| ID | Nome | Aplicação HIOS |
|----|------|----------------|
| I9 | Human Approval Gate | Anchor só é canónico após I9 decision |
| I11 | Permanência Criptográfica | Shots selados são imutáveis |
| I14 | Explicit Failure | Scores reais, nunca placeholders |
| I19 | Proveniência Inseparável | Anchor sem provenance.json = inválido |
| I-LIKENESS (candidate) | Likeness Gate | Filtros de terceiros = governance gates |

---

## 5. THRESHOLDS FORENSES

| Score | Status | Uso |
|-------|--------|-----|
| ≥0.75 | FORENSIC | Produção final, selo possível |
| ≥0.65 | OPERATIONAL | Uso interno, revisão recomendada |
| <0.65 | FAIL | Reclassificar como ACTION ou regenerar |

---

## 6. FICHEIROS CRÍTICOS

### Repositório Principal
```
/home/windi/hios/cinema/obras/w-hios-forensic-unit/
├── anchors/
│   ├── marcus.vance.anchor.canonical.png           ← CANONICAL (v2)
│   ├── marcus.vance.anchor.canonical.embedding.npy
│   ├── marcus.vance.anchor.canonical.provenance.json
│   ├── marcus.couto.anchor.v1.*
│   ├── helena.meyer.junior.anchor.v1.*
│   ├── gabi.santos.anchor.v1.*
│   ├── lucas.silva.anchor.v1.*
│   └── alejandro.valenzuela.anchor.v1.*
├── shots/
│   └── vance/
│       ├── VANCE_V2_RESULTS_20260605163404.json
│       └── S*_v2.mp4 (10 videos)
└── docs/
    ├── VANCE-V2-FINAL-REPORT-20260605.md
    ├── COUNCIL-DECISION-V2-CANONICAL-20260605.md
    ├── ERRATA-SHOTGRAMMAR-S4-bis-20260605.md
    └── MEMORY-LOOP-HIOS-20260606.md (este ficheiro)
```

### Preproduction
```
/opt/windi/hios/cinema/obras/w-hios-forensic-unit/_preproduction/
├── SPINE-PASSPORTS-MASTER.md
└── SPINE-CAST-VANCE-PROMPTS.md
```

---

## 7. PRÓXIMOS PASSOS (PRIORIDADE)

1. ~~**[HOUSEKEEPING]** Promover v2 anchor para canonical~~ ✅ **DONE** (`marcus.vance.anchor.canonical.*`)
2. **[PRODUCTION]** Helena anchor → 10 IDENTITY shots → measure
3. **[PRODUCTION]** Gabi anchor → 10 IDENTITY shots → measure
4. ~~**[DISAMBIGUATION]** Re-medir Couto × Vance v2~~ ✅ **DONE** (0.1765 < 0.50, SEALED 06 Jun)
5. **[INFRA]** Fix nginx mime-type para `/docs/hios-forensic/*.md`

---

## 8. COMANDOS ÚTEIS

```bash
# Medir shot contra anchor
/opt/windi/venv-poe/bin/python3 scripts/measure_scene.py \
  --anchor anchors/vance_v2_candidates/vance_v2_20260605113255_anchor.png \
  --video shots/vance/S07-01_v2.mp4

# Ver resultados JSON
cat shots/vance/VANCE_V2_RESULTS_20260605163404.json | jq '.results[] | {shot_id, avg: .summary.avg_similarity, status: .summary.status}'

# Extrair embedding de novo anchor
/opt/windi/venv-poe/bin/python3 -c "
from insightface.app import FaceAnalysis
import cv2, numpy as np
app = FaceAnalysis(name='buffalo_l')
app.prepare(ctx_id=-1, det_size=(640,640))
img = cv2.imread('path/to/anchor.png')
faces = app.get(img)
if faces:
    np.save('anchor.embedding.npy', faces[0].normed_embedding)
"
```

---

## 9. AXIOMAS SELADOS

> "A filter that blocks is not an obstacle to circumvent — it's a gate to respect."
> — Guardian + Human Dragon, 05 Jun 2026

> "A number without a measurement run is not a number."
> — Paper-001 Axiom

> "The method descends from the finding."
> — SHOT-GRAMMAR-001 derivation

> "O débito que sangrava parou de sangrar — não porque o curámos, mas porque o nomeámos."
> — Human Dragon, 06 Jun 2026 (DIAG-MED-TIER)

> "git stash, nunca rm -f. Um fluxo que apaga artefactos forenses para resolver conflito de git contradiz a doutrina que o sistema protege."
> — Guardian, 06 Jun 2026 (post-ERRATA-MED-503)

---

## 10. COMMITS RELEVANTES

| Hash | Descrição |
|------|-----------|
| `c3f5e031` | fix(vance-v2): apply Guardian's 3 corrections |
| `679e9f8c` | docs: add 05 Jun milestone |
| `f5a4d192` | Paper-001 Errata + SHOT-GRAMMAR-001 |
| `21e59079` | feat(cinema): SHOT-GRAMMAR-001 completo |
| `2cd27375` | seal(cinema): SHOT-GRAMMAR-001 Disambiguation Gate closed |
| `3e26bc40` | seal(governance): DIAG-MED-TIER diagnostic — I14 audit |
| `5f8b32290` | fix(engine): I14 gate for MED tier — Errata §240-241 |
| `18616c03` | docs(errata): MED tier I14 gate — §240-241 correction |
| `a9fab47b` | docs(hios): Memory Loop v1.2.0 — ERRATA-MED-503 + axiom |

---

## 11. CROSS-SYSTEM REFERENCES

### DIAG-MED-TIER + ERRATA-MED-503 (Infra WINDI)

**Diagnóstico (manhã):**
- W-SITES: MED implementado, I14 conforme (503 se sem chave Mistral)
- Dragon Chat :8112: MED NÃO implementado (viola I14, usa Claude para tudo)

**Correcção (tarde):**
- Dragon Chat agora retorna 503 quando MED pedido sem Mistral
- Padrão alinhado com W-SITES
- Receipt: `WINDI-ERRATA-MED-503-20260606`

**Débito técnico (nomeado, não corrigido):**
- MISTRAL_API_KEY lida uma vez no import (linha 119)
- Se chave configurada sem reiniciar serviço, gate continua 503
- Acção futura: quando Mistral entrar (500+ users), confirmar releitura em runtime
- **Débito:** Dragon Chat → 503 em MED (errata §240-241, sessão própria)

**Receipts desta sessão:**
- `WINDI-SHOTGRAMMAR-001-SEALED-20260606` — Disambiguation Gate
- `WINDI-DIAG-MED-TIER-20260606` — I14 Diagnostic
- `WINDI-ERRATA-MED-503-20260606` — Runtime Correction

**Docs:**
- `/home/windi/docs/DIAG-MED-TIER-20260606.md`
- `/home/windi/docs/ERRATA-MED-503-20260606.md`

---

*Liga IA+H · WINDI Publishing House · 06 Jun 2026*
*"A Opção A é a única soberana."*
