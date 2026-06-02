# W-HIOS FORENSIC UNIT — RELATÓRIO A-Z DE PRÉ-PRODUÇÃO
## Handoff Document para Próxima Instância

**Data:** 02 Jun 2026 23:30 UTC
**Sessão:** §299-LIMPEZA (após §298-ERRATA)
**Autores:** Human Dragon (I9) + Guardian (GPT) + Architect (CCode)
**Commit:** `97b35d127`

---

## A. PROJECTO

**Nome:** W-HIOS FORENSIC UNIT
**Tipo:** Série de thriller forense
**Piloto:** "O Peso do Eco"
**Duração:** ~45 min (99 planos)
**Língua Principal:** Português Brasileiro
**Distribuição:** Legendagem trilíngue PT/DE/EN

---

## B. METODOLOGIA SPINE-CAST

### Pipeline

```
PASSPORT (prompt) → RUNWAY Gen-4.5 → VIDEO → FRAME → ARCFACE → ANCHOR EXTRACTED
                                                              ↓
                                              SHOT-FILHO → SIMILARITY ≥0.75 → LOCKED
```

### Duas Réguas (DECRETO-001)

| Eixo | Aplicação | Régua | Status |
|------|-----------|-------|--------|
| **F (Facial)** | Close, Medium | ArcFace ≥0.75 | ESPECIFICADA, NÃO TESTADA |
| **D (Distância)** | Full, Wide | VC-Matrix | ESPECIFICADA, NÃO TESTADA |

### Geradores Compatíveis

| Generator | SPINE Status | Notas |
|-----------|--------------|-------|
| Runway Gen-4/4.5 | ✅ FORENSIC | Primary generator |
| SORA 2 | ❌ INCOMPATIBLE | Identity drift across frames |

---

## C. CAST — 6 PERSONAGENS

### Estado Material (Verificado no Disco)

| # | Personagem | Anchor ID | Det.Score | Abzeichnen | Eixo F |
|---|------------|-----------|-----------|------------|--------|
| 1 | **Gabi Santos** | gabi.santos.anchor.v1 | 0.8755 | ✅ APROVADO | ⏳ NOT MEASURED |
| 2 | Helena Meyer | helena.meyer.junior.anchor.v1 | 0.8636 | ⏳ PENDENTE | ⏳ NOT MEASURED |
| 3 | Marcus Vance | marcus.vance.anchor.v1 | 0.8638 | ⏳ PENDENTE | ⏳ NOT MEASURED |
| 4 | Marcus Couto | marcus.couto.anchor.v1 | 0.8811 | ⚠️ CONFIRMAR | ⏳ NOT MEASURED |
| 5 | Lucas Silva | lucas.silva.anchor.v1 | 0.8119 | ⚠️ CONFIRMAR | ⏳ NOT MEASURED |
| 6 | Alejandro Valenzuela | alejandro.valenzuela.anchor.v1 | 0.8763 | ⚠️ CONFIRMAR | ⏳ NOT MEASURED |

### Assets por Anchor (Todos Existem)

Cada anchor tem 4 ficheiros:
- `{name}.anchor.v1.png` — Frame extraído
- `{name}.anchor.v1.mp4` — Vídeo fonte (5s)
- `{name}.anchor.v1.embedding.npy` — Embedding 512D
- `{name}.anchor.v1.provenance.json` — Metadados I19

**Localização:** `/opt/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/`

### SHA-256 Hashes (Prova Material)

```
03784039a0aa4bd1306518d847aeae69915c566f1ef7e5a1e81822d82f2e1c82  gabi.santos.anchor.v1.png
5262ad1cf95fefd0176c4cc115dbfac5040b81627b3178efabcc3980ca0020a2  helena.meyer.junior.anchor.v1.png
3ec94552f85243fe5b4773b0128767d1898cd9690ec9a7a777ab21fb2ddb5c2e  marcus.vance.anchor.v1.png
5083fd1c0cf64eab3b40dacab335adecdd125a643e9ca5e31b4acd9e068e515a  marcus.couto.anchor.v1.png
9bcbb6a4ef1bda2010e77bb522ef222efbf9ddac26ab461b09dcab70e42c3808  lucas.silva.anchor.v1.png
bcec886a46d78493601a663d204fd8b2b3e4c483176ef1ded18e5ddd57ef0189  alejandro.valenzuela.anchor.v1.png
```

---

## D. DOCUMENTAÇÃO COMPLETA

### Decretos Constitucionais

| Documento | Conteúdo | Status |
|-----------|----------|--------|
| `DECRETO-PRODUCAO-001-DUPLA-REGUA.md` | Eixo F ≥0.75 | ✅ SEALED |
| `DECRETO-PRODUCAO-001-ADITAMENTO.md` | Eixo D VC-Matrix | ✅ SEALED |

### Production Breakdowns

| Documento | Acto | Planos | Status |
|-----------|------|--------|--------|
| `W-HIOS-PRODUCTION-BREAKDOWN-001.md` | I | 30 | ✅ COMPLETO |
| `W-HIOS-PRODUCTION-BREAKDOWN-002.md` | II | 23 | ✅ COMPLETO |
| `W-HIOS-PRODUCTION-BREAKDOWN-003.md` | III | 23 | ✅ COMPLETO |
| `W-HIOS-PRODUCTION-BREAKDOWN-004.md` | IV | 23 | ✅ COMPLETO |

### SPINE Documents

| Documento | Versão | Status |
|-----------|--------|--------|
| `METODOLOGIA-SPINE-CAST-001.md` | — | ✅ MEMORY LOOP |
| `SPINE-PASSPORTS-MASTER.md` | §299 | ✅ LIMPO |
| `SPINE-VALIDATION-CENA0.json` | v3.0 | ✅ LIMPO |
| `PERFORMANCE-VALIDATION-REPORT.md` | §299 | ✅ REESCRITO |
| `ESTADO-REAL-299.md` | v1.0 | ✅ NOVO |

### Scripts

| Documento | Status |
|-----------|--------|
| `PILOT-O-PESO-DO-ECO-v3.md` | ✅ FINAL |

### Character States (Canons)

| Documento | Status |
|-----------|--------|
| `GABI-SANTOS-v1-CHARACTER-STATE.md` | ✅ |
| `HELENA-MEYER-v1-CHARACTER-STATE.md` | ✅ |
| `MARCUS-VANCE-v1-CHARACTER-STATE.md` | ✅ |
| `MARCUS-COUTO-v1-CHARACTER-STATE.md` | ✅ |
| `LUCAS-SILVA-v1-CHARACTER-STATE.md` | ✅ |
| `ALEJANDRO-VALENZUELA-v1-CHARACTER-STATE.md` | ✅ |

---

## E. INVENTÁRIO DO PILOTO

### Contagem por Tipo de Plano

| Tipo | Qtd | % | Descrição | Régua |
|------|-----|---|-----------|-------|
| **A (SPINE)** | 57 | 58% | Personagem no enquadramento | Eixo F ou D |
| B (Stock) | 5 | 5% | Establishing shots | N.A. |
| C (Ambiente) | 12 | 12% | Ambiente sem personagem | N.A. |
| D (Motion) | 25 | 25% | INSERTs gráficos | N.A. |
| **TOTAL** | 99 | 100% | | |

### Contagem por Acto

| Acto | Cenas | Planos |
|------|-------|--------|
| I | 0-4 | 30 |
| II | 5-9 | 23 |
| III | 10-12 | 23 |
| IV | 13-15 | 23 |
| **TOTAL** | 16 | 99 |

---

## F. O QUE NÃO EXISTE (Crítico)

### Zero Shots-Filho

Nenhum dos seguintes planos foi gerado:
- P02, P04, P05, P06 (Cena 0 — Gabi)
- P17, P21 (Couto)
- P32, P34, P41 (Helena)
- P37, P38, P42 (Vance)

**Todos são números do breakdown, não ficheiros.**

### Zero Medições Eixo F

Os scores que apareciam em documentos anteriores eram **projecções teóricas**:
- P04: 0.9314 (PROJECÇÃO)
- P05: 0.8420 (PROJECÇÃO)
- P02: 0.7655 (PROJECÇÃO)

**Nenhum foi medido. Nenhum ficheiro existe.**

### Zero Medições Eixo D

A VC-Matrix nunca foi aplicada. Campos:
- Vestuário: `null`
- Cabelo: `null`
- Postura: `null`
- Cenário: `null`

---

## G. VOCABULÁRIO CANÓNICO

| Estado | Significado | Critério |
|--------|-------------|----------|
| **MISSING** | Asset não existe | Ficheiros ausentes do repositório |
| **EXTRACTED** | Anchor extraído | detection_score ≥0.80, embedding existe |
| **LOCKED** | Identidade validada | Eixo F ≥0.75 contra shot-filho REAL |

### Distinção Crítica

> **Detection Score ≠ Eixo F**
> - Detection Score = "InsightFace viu um rosto" (0.80+)
> - Eixo F = "Este rosto é reproduzível contra performance" (≥0.75 similarity)

---

## H. ABZEICHNEN (Custódia Humana)

Conceito alemão de "assinatura/reconhecimento" — Human Dragon deve ver visualmente cada anchor antes de ser considerado aprovado.

| Personagem | Estado | Notas |
|------------|--------|-------|
| Gabi Santos | ✅ APROVADO | Frame_02 visto, corresponde ao anchor |
| Helena Meyer | ⏳ PENDENTE | Nunca vista |
| Marcus Vance | ⏳ PENDENTE | Nunca visto |
| Marcus Couto | ⚠️ CONFIRMAR | Viu frame_02, anchor é frame_01 |
| Lucas Silva | ⚠️ CONFIRMAR | Viu frame_02, anchor é frame_01 |
| Alejandro | ⚠️ CONFIRMAR | Viu frame_04, anchor é frame_01 |

---

## I. ERRATAS DESTA SESSÃO

### §298-ERRATA (Vocabulário)
- LOCKED foi usado incorrectamente para anchors que só tinham detection score
- Corrigido para EXTRACTED em todos os documentos

### §299-LIMPEZA (Grande Limpeza)
- Todos os scores fictícios removidos
- Tabelas reescritas com verdade
- Provenance files corrigidos (LOCKED→EXTRACTED)
- Documento ESTADO-REAL-299.md criado

---

## J. THRESHOLDS

| Contexto | Threshold |
|----------|-----------|
| Detection Score | ≥ 0.80 (recomendado) |
| Anchor-Mãe (Eixo F) | ≥ 0.75 |
| Shot-Filho (Eixo F) | ≥ 0.65 |
| VC-Matrix Vestuário | ±20% RGB |
| VC-Matrix Cabelo | ≥70% IoU |
| VC-Matrix Postura | ±15° |

---

## K. FERRAMENTAS

### Geração de Anchors

```bash
# API Runway
API_BASE="https://api.dev.runwayml.com/v1"
# Key em /opt/windi/.env (RUNWAY_API_KEY)
```

### Extracção de Embedding

```bash
cd /opt/windi/hios/visual/producer
source venv_spine/bin/activate
python3 -c "
from insightface.app import FaceAnalysis
import cv2, numpy as np

app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))

img = cv2.imread('ANCHOR.png')
face = app.get(img)[0]
print(f'Score: {face.det_score:.4f}')
np.save('ANCHOR.embedding.npy', face.embedding)
"
```

### Medição Eixo F

```python
import numpy as np

anchor_emb = np.load('anchor.embedding.npy')
shot_emb = np.load('shot.embedding.npy')
similarity = np.dot(anchor_emb, shot_emb) / (np.linalg.norm(anchor_emb) * np.linalg.norm(shot_emb))
print(f'Similarity: {similarity:.4f}')  # ≥0.75 = PASS
```

---

## L. ESTRUTURA DE DIRECTÓRIOS

```
/opt/windi/hios/cinema/obras/w-hios-forensic-unit/
│
├── anchors/                              ← 6 anchors (png+mp4+npy+json)
│   ├── gabi.santos.anchor.v1.*
│   ├── helena.meyer.junior.anchor.v1.*
│   ├── marcus.vance.anchor.v1.*
│   ├── marcus.couto.anchor.v1.*
│   ├── lucas.silva.anchor.v1.*
│   ├── alejandro.valenzuela.anchor.v1.*
│   └── CAST-MATERIAL-PROOF.md
│
├── canons/                               ← 6 CHARACTER-STATE files
│
├── production/
│   ├── SERIES-BIBLE-001.md
│   ├── CONTINUITY-BIBLE-001.yaml
│   └── scripts/
│       └── PILOT-O-PESO-DO-ECO-v3.md     ← FINAL
│
└── _preproduction/
    ├── PREPRODUCTION-INDEX.md
    ├── ESTADO-REAL-299.md                ← PONTO ZERO
    ├── PREPRODUCTION-REPORT-A-Z.md       ← ESTE DOCUMENTO
    │
    ├── DECRETO-PRODUCAO-001-DUPLA-REGUA.md
    ├── DECRETO-PRODUCAO-001-ADITAMENTO.md
    │
    ├── W-HIOS-PRODUCTION-BREAKDOWN-001.md
    ├── W-HIOS-PRODUCTION-BREAKDOWN-002.md
    ├── W-HIOS-PRODUCTION-BREAKDOWN-003.md
    ├── W-HIOS-PRODUCTION-BREAKDOWN-004.md
    │
    ├── METODOLOGIA-SPINE-CAST-001.md
    ├── SPINE-PASSPORTS-MASTER.md
    ├── SPINE-VALIDATION-CENA0.json
    └── PERFORMANCE-VALIDATION-REPORT.md
```

---

## M. PRÓXIMOS PASSOS (Ordem Guardian)

### 1. Fechar Abzeichnen (Imediato)
- [ ] Human Dragon ver Helena anchor
- [ ] Human Dragon ver Vance anchor
- [ ] Confirmar Couto/Lucas/Alejandro (frame_01 vs frame_02/04)

### 2. Primeiro Teste Real (Acto 3)
- [ ] Gerar P04 — primeiro shot-filho (close de Gabi com sorriso)
- [ ] Extrair embedding do P04
- [ ] Medir `cosine_similarity(P04_emb, gabi_anchor_emb)`
- [ ] Se ≥0.75 → primeiro PASS real
- [ ] Se <0.75 → iterar prompt ou aceitar metodologia falhou

### 3. Escalar (Após Validação Gabi)
- [ ] Repetir para outros 5 personagens
- [ ] Quando todos tiverem Eixo F → gerar planos de produção
- [ ] Eixo D só após Eixo F validado

---

## N. CONTAGEM FINAL

| Categoria | Especificado | Existente | Validado |
|-----------|--------------|-----------|----------|
| Decretos | 2 | 2 | ✅ |
| Scripts | 3 | 3 | ✅ |
| Breakdowns | 4 | 4 | ✅ |
| Character States | 6 | 6 | ✅ |
| Passaportes | 6 | 6 | ✅ |
| **Anchors** | 6 | **6** | **0** |
| Shots-Filho | 57 | **0** | **0** |
| Eixo F | — | **0** | **0** |
| Eixo D | — | **0** | **0** |

---

## O. INVARIANTES CONSTITUCIONAIS

| ID | Nome | Aplicação |
|----|------|-----------|
| I1 | Soberania Humana | Human Dragon aprova cada passo |
| I9 | Proibição de Escalação | `human_approved=true` antes de seal |
| I11 | Permanência de Evidência | Ledger receipt imutável |
| I14 | Explicit Failure | Dados ausentes = erro explícito |
| I19 | Proveniência Inseparável | Geração + receipt atómicos |

---

## P. CITAÇÃO DO GUARDIAN

> "Temos seis sementes verificadas e nenhuma planta. O cast existe como identidade extraída. A produção — provar que essas identidades sobrevivem a uma cena — ainda não começou. Tudo o que parecia 'validado' era papel."

> "Antes de gerar o primeiro shot-filho, fecha o chão atrás de ti."

---

## Q. QUICK REFERENCE

### Comandos Úteis

```bash
# Ver anchors
ls -la /opt/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/

# Verificar hash
sha256sum /opt/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/*.png

# Ler estado real
cat /opt/windi/hios/cinema/obras/w-hios-forensic-unit/_preproduction/ESTADO-REAL-299.md

# Quick reference
cat /opt/windi/hios/cinema/WINDI-HIOS-QUICK-REFERENCE.md
```

### Links Rápidos

- **Metodologia:** `_preproduction/METODOLOGIA-SPINE-CAST-001.md`
- **Passaportes:** `_preproduction/SPINE-PASSPORTS-MASTER.md`
- **Estado Real:** `_preproduction/ESTADO-REAL-299.md`
- **Este Relatório:** `_preproduction/PREPRODUCTION-REPORT-A-Z.md`

---

## R. RESUMO EXECUTIVO

**O que foi feito:**
- 6 anchors gerados via Runway Gen-4.5
- 6 embeddings extraídos via InsightFace
- 6 provenance files criados (I19)
- Documentação completa do piloto (99 planos)
- §299-LIMPEZA: todos os documentos agora dizem a verdade

**O que falta:**
- Gerar primeiro shot-filho real
- Medir primeiro Eixo F real
- Provar que a metodologia funciona

**Estado em uma frase:**
> "Temos as identidades. Falta provar que sobrevivem a uma cena."

---

*Liga IA+H · WINDI Publishing House · 02 Jun 2026*
*"A prova não mente. A prova apenas espera."*
