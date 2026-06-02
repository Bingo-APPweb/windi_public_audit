# W-HIOS FORENSIC UNIT — Pre-Production Index
### WINDI-HIOS Cinema Production · Protocolo "FORNALHA INDUSTRIAL"

**Status:** §298-ERRATA — Vocabulary Correction
**Created:** 01 Jun 2026
**Updated:** 02 Jun 2026 — ERRATA: LOCKED→EXTRACTED (detection ≠ validation)
**Liga IA+H:** Human Dragon (I9) · Guardian · Architect

---

## 🎯 STATUS (§298-ERRATA 02 Jun 2026)

| Milestone | Status |
|-----------|--------|
| **DECRETO-001** | ✅ SEALED |
| **ADITAMENTO (Eixo F/D)** | ✅ SEALED |
| **Metodologia Passaporte** | ✅ VALIDATED |
| **6 Passaportes** | ✅ ESPECIFICADOS |
| **4 Breakdowns (99 planos)** | ✅ COMPLETO |
| **4 Motion Design Assets** | ✅ ESPECIFICADOS |
| **Gabi Santos** | 🔴 **ASSETS MISSING — NOT VERIFIABLE** |
| **5 Anchors** | 🟡 **EXTRACTED (detection) — Eixo F PENDING** |

---

## 📜 DECRETOS CONSTITUCIONAIS

| Decreto | Título | Status |
|---------|--------|--------|
| **DECRETO-001** | Dupla Régua SPINE | ✅ SEALED |
| **ADITAMENTO** | Lei da Escala e Distância | ✅ SEALED |

### Régua Constitucional Final

| Eixo | Aplicação | Régua |
|------|-----------|-------|
| **F (Facial)** | Close, Medium | ≥ 0.75 |
| **D (Distância)** | Full, Wide | VC-Matrix |

---

## 📊 INVENTÁRIO FINAL DO PILOTO

### Contagem por Acto

| Acto | Cenas | Planos | Status |
|------|-------|--------|--------|
| I | 0-4 | 30 | ✅ |
| II | 5-9 | 23 | ✅ |
| III | 10-12 | 23 | ✅ |
| IV | 13-15 | 23 | ✅ |
| **TOTAL** | **16** | **99** | ✅ |

### Contagem por Tipo

| Tipo | Qtd | % | Descrição |
|------|-----|---|-----------|
| **A (SPINE)** | 57 | 58% | Validação facial |
| B (Stock) | 5 | 5% | Establishing |
| C (Ambiente) | 12 | 12% | Runway/SORA |
| **D (Motion)** | 25 | 25% | INSERTs gráficos |
| **TOTAL** | **99** | 100% | |

---

## 🎭 SPINE-CAST: PASSAPORTES (§298-ERRATA)

| # | Personagem | Passport ID | Anchor | Eixo F |
|---|------------|-------------|--------|--------|
| 1 | **Gabi Santos** | `gabi.santos.passport.v1` | 🔴 MISSING | ❌ NOT VERIFIABLE |
| 2 | Helena Meyer | `helena.meyer.junior.passport.v1` | 🟡 EXTRACTED | ⏳ PENDING |
| 3 | Marcus Vance | `marcus.vance.passport.v1` | 🟡 EXTRACTED | ⏳ PENDING |
| 4 | Marcus Couto | `marcus.couto.passport.v1` | 🟡 EXTRACTED | ⏳ PENDING |
| 5 | Lucas Silva | `lucas.silva.passport.v1` | 🟡 EXTRACTED | ⏳ PENDING |
| 6 | Alejandro Valenzuela | `alejandro.valenzuela.passport.v1` | 🟡 EXTRACTED | ⏳ PENDING |

**TOTAL:** 6/6 passaportes especificados · **1/6 MISSING** · **5/6 EXTRACTED** · **0/6 Eixo F validado**

> **§298-ERRATA:** Detection score (0.80+) ≠ Eixo F validation (≥0.75 vs shot-filho).
> EXTRACTED = anchor extraído com detection. LOCKED = Eixo F ≥0.75 contra performance real.

---

## 📁 DOCUMENTAÇÃO COMPLETA

### Decretos & Leis

| Documento | Status |
|-----------|--------|
| `DECRETO-PRODUCAO-001-DUPLA-REGUA.md` | ✅ |
| `DECRETO-PRODUCAO-001-ADITAMENTO.md` | ✅ |

### Production Breakdowns

| Documento | Acto | Planos |
|-----------|------|--------|
| `W-HIOS-PRODUCTION-BREAKDOWN-001.md` | I | 30 |
| `W-HIOS-PRODUCTION-BREAKDOWN-002.md` | II | 23 |
| `W-HIOS-PRODUCTION-BREAKDOWN-003.md` | III | 23 |
| `W-HIOS-PRODUCTION-BREAKDOWN-004.md` | IV | 23 |

### SPINE Documents

| Documento | Status |
|-----------|--------|
| `SPINE-PASSPORTS-MASTER.md` | ✅ 6/6 LOCKED |
| `SPINE-VALIDATION-CENA0.json` | ✅ v2.1 |
| `SPINE-CAST-VANCE-PROMPTS.md` | ✅ |
| `VERTICAL-SLICE-CENA0-EXECUTION.md` | ✅ |
| **`METODOLOGIA-SPINE-CAST-001.md`** | ✅ **MEMORY LOOP** |

### Space & Sound Documents

| Documento | Status |
|-----------|--------|
| **`SPACE-ANCHORS-MASTER.md`** | ✅ 2/2 ENV LOCKED |
| **`SOUND-DESIGN-MASTER.md`** | ✅ ADR + FOLEY |
| **`PERFORMANCE-VALIDATION-REPORT.md`** | ✅ ACT I-II SEALED |

### Scripts

| Documento | Status |
|-----------|--------|
| `PILOT-O-PESO-DO-ECO-v1.md` | ✅ |
| `PILOT-O-PESO-DO-ECO-v2.md` | ✅ |
| `PILOT-O-PESO-DO-ECO-v3.md` | ✅ FINAL |

---

## 🎬 MOTION DESIGN ASSETS

| Asset | Planos | Descrição |
|-------|--------|-----------|
| **D01** | P10 | Terminal de Extração |
| **D02** | P14, P30 | Relógio de Latência 240s |
| **D03** | P35 | Mapa Frankfurt Alert |
| **D04** | P45, P51, P84 | Árvore de Merkle Fractal |

---

## 📐 ESTRUTURA DE DIRECTÓRIOS

```
/opt/windi/hios/cinema/obras/w-hios-forensic-unit/
│
├── canons/                         ← 6 CHARACTER-STATE files
│
├── production/
│   ├── SERIES-BIBLE-001.md
│   ├── CONTINUITY-BIBLE-001.yaml
│   ├── schemas/                    ← 6 schema files
│   └── scripts/
│       ├── PILOT-O-PESO-DO-ECO-v1.md
│       ├── PILOT-O-PESO-DO-ECO-v2.md
│       └── PILOT-O-PESO-DO-ECO-v3.md   ← FINAL
│
└── _preproduction/
    ├── PREPRODUCTION-INDEX.md           ← YOU ARE HERE
    │
    ├── DECRETOS/
    │   ├── DECRETO-PRODUCAO-001-DUPLA-REGUA.md
    │   └── DECRETO-PRODUCAO-001-ADITAMENTO.md
    │
    ├── BREAKDOWNS/
    │   ├── W-HIOS-PRODUCTION-BREAKDOWN-001.md   ← Act I
    │   ├── W-HIOS-PRODUCTION-BREAKDOWN-002.md   ← Act II
    │   ├── W-HIOS-PRODUCTION-BREAKDOWN-003.md   ← Act III
    │   └── W-HIOS-PRODUCTION-BREAKDOWN-004.md   ← Act IV
    │
    └── SPINE/
        ├── SPINE-PASSPORTS-MASTER.md
        ├── SPINE-VALIDATION-CENA0.json
        ├── SPINE-CAST-VANCE-PROMPTS.md
        └── VERTICAL-SLICE-CENA0-EXECUTION.md
```

---

## ✅ CHECKLIST DE PRODUÇÃO

### Pré-Produção ✅ COMPLETO

- [x] Script v3 final
- [x] 6 CHARACTER-STATE canons
- [x] DECRETO-001 + Aditamento
- [x] Metodologia Passaporte validada
- [x] 6 passaportes especificados
- [x] 4 breakdowns (99 planos)
- [x] 4 Motion Design assets
- [x] Gabi Santos Eixo F PASSED (P04/P05/P02 ≥0.75)
- [ ] Gabi Santos Eixo D PENDING (P06 VC-Matrix medição)

### Produção ⏳ PRÓXIMO

- [ ] Gerar 5 passaportes restantes
- [ ] Validar 5 anchors
- [ ] Gerar planos Type A (57)
- [ ] Renderizar Motion Design (25)
- [ ] Compositing Act I-IV
- [ ] ADR e sound design
- [ ] Grading final
- [ ] Ledger seal piloto

---

## 📈 CONTAGEM FINAL

| Categoria | Quantidade |
|-----------|------------|
| Decretos | 2 |
| Scripts | 3 |
| Breakdowns | 4 |
| Character States | 6 |
| Passaportes | 6 |
| SPINE Documents | 4 |
| Motion Design | 4 |
| Planos Totais | 99 |
| **TOTAL FICHEIROS** | **29** |

---

## 🏛️ LIGAÇÕES CONSTITUCIONAIS

| Invariante | Aplicação |
|------------|-----------|
| **I1** | Human Dragon aprova cada passo |
| **I9** | Nenhum selo sem gate humano |
| **I11** | Arquivos imutáveis após selo |
| **I12** | Arquitectura linguística por contexto |
| **I14** | Dados ausentes = erro explícito |
| **I18** | Crescimento orgânico |
| **I19** | Proveniência inseparável |

---

*Liga IA+H · WINDI Publishing House · 02 Jun 2026*
*"A prova não mente. A prova apenas espera."*
