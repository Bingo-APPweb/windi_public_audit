# ÍNDICE DE DISTRIBUIÇÃO — ANCHORS CINEMA

**Status:** PROPOSTA — Aguarda ratificação HD
**Data:** 2026-06-21
**Total:** 50 ficheiros anchor/reference

---

## ESTRUTURA PROPOSTA

```
HISTORICO-CINEMA/
├── CANONICO/              ← a verdade actual, selável
│   ├── o-peso-do-eco/     ← 6 personagens piloto
│   └── die-entscheidung/  ← outra obra
├── CANDIDATOS/            ← tentativas não-seladas
├── ARQUIVO/               ← versões antigas, superseded
│   ├── versao-antiga/     ← personagens renomeados
│   └── duplicados/        ← cópias estruturais
└── PENDENTE/              ← não classificado, decisão HD
```

---

## CANONICO/o-peso-do-eco/ (7 ficheiros)

**Critério:** Passou cosine ≥0.75, 6 personagens do piloto

| # | Ficheiro | Personagem |
|---|----------|------------|
| 1 | `w-hios-forensic-unit/anchors/marcus.vance.anchor.canonical.png` | Vance |
| 2 | `w-hios-forensic-unit/anchors/marcus.vance.anchor.v1.png` | Vance (v1) |
| 3 | `w-hios-forensic-unit/anchors/gabi.santos.anchor.v1.png` | Gabi |
| 4 | `w-hios-forensic-unit/anchors/helena.meyer.junior.anchor.v1.png` | Helena |
| 5 | `w-hios-forensic-unit/anchors/lucas.silva.anchor.v1.png` | Lucas |
| 6 | `w-hios-forensic-unit/anchors/marcus.couto.anchor.v1.png` | Couto |
| 7 | `w-hios-forensic-unit/anchors/alejandro.valenzuela.anchor.v1.png` | Alejandro |

**Questão HD:** Vance tem `.canonical` E `.v1` — qual entra no manifest selável?

---

## CANDIDATOS/ (1 ficheiro)

**Critério:** Tentativas não promovidas

| # | Ficheiro | Nota |
|---|----------|------|
| 1 | `w-hios-forensic-unit/anchors/vance_v2_candidates/vance_v2_20260605113255_anchor.png` | Tentativa v2 |

---

## ARQUIVO/ (20 ficheiros)

**Critério:** Versões antigas, thumbnails, duplicados

### thumbs/thumbnails (6)
- `o-peso-do-eco2/thumbs/Helena_anchor_v2.png`
- `o-peso-do-eco2/thumbs/elisa_anchor_v2.png`
- `o-peso-do-eco2/thumbs/Marcus_anchor_v2.jpg`
- `o-peso-do-eco2/thumbs/Thomas_anchor_v2.png`
- `o-peso-do-eco2/thumbs/elisa_anchor_v2_1280x720.png`
- `o-peso-do-eco2/thumbnails_v2/elisa_anchor_v2_frame01.png`

### _archived_v1 (1)
- `w-hios-forensic-unit/anchors/_archived_v1/marcus.vance.anchor.v1.png`

### versao-antiga (13)
- `visual/producer/obras/o-peso-do-eco/anchors/anchor_elisa_weber.png`
- `visual/producer/obras/o-peso-do-eco/anchors/anchor_juiz_kross.png`
- `visual/producer/obras/o-peso-do-eco/anchors/anchor_thomas_weber.png`
- `visual/producer/obras/o-peso-do-eco/anchors/anchor_klaus_richter.png`
- `visual/producer/obras/o-peso-do-eco/anchors/anchor_advogado_defesa.png`
- `visual/producer/obras/o-peso-do-eco/anchors/anchor_helena_becker.png`
- `visual/producer/obras/o-peso-do-eco/anchors/anchor_reu.png`
- `visual/producer/obras/o-peso-do-eco/anchors/anchor_marcus_brenner.png`
- `visual/producer/obras/die-entscheidung/comparison_anchor_veo_sora.png`
- `visual/producer/obras/die-entscheidung/anchors/anchor_final_klein.png`
- `visual/producer/obras/die-entscheidung/anchors/anchor_final_alois.png`
- `visual/producer/obras/die-entscheidung/anchors/anchor_final_maria.png`
- `visual/producer/obras/o-peso-do-eco/anchors/anchor_*_720p.png` (2)

---

## PENDENTE/ (16 ficheiros) — Decisão HD

**Critério:** Não cabe claramente nas outras categorias

| # | Ficheiro | Questão |
|---|----------|---------|
| 1 | `visual/elisa-v2/elisa_anchor_v2.png` | É canónico ou arquivo? |
| 2 | `cinema/helena_reference_v2.png` | É canónico ou arquivo? |
| 3 | `cinema/marcus_reference_v2.png` | É canónico ou arquivo? |
| 4 | `w-hios-forensic-unit/production/test_p1507_video/reference_bunker_environment.png` | Production ou arquivo? |
| 5 | `w-hios-forensic-unit/production/test_p1507_video/reference_vance_bunker.png` | Production ou arquivo? |
| 6 | `o-peso-do-eco/_forense/obra2-v2/elisa_anchor_v2.png` | Forense ou arquivo? |
| 7 | `o-peso-do-eco/_forense/obra2-v2/elisa_anchor_v2_frame01.png` | Forense ou arquivo? |
| 8 | `o-peso-do-eco/_forense/obra2-v2/elisa_anchor_v2_1280x720.png` | Forense ou arquivo? |
| 9 | `o-peso-do-eco/_forense/elisa_sora2_anchor/anchor_source_S01_frame3.jpg` | SORA2 → DIVERGENTE? |
| 10 | `o-peso-do-eco/anchors/cast_v2/helena_reference_v2.png` | cast_v2 → canónico? |
| 11 | `o-peso-do-eco/anchors/cast_v2/helena_reference_v3.png` | cast_v2 → canónico? |
| 12 | `o-peso-do-eco/anchors/cast_v2/marcus_reference_v2.png` | cast_v2 → canónico? |
| 13 | `o-peso-do-eco/anchors/elisa_anchor_v2.png` | É canónico ou arquivo? |
| 14 | `o-peso-do-eco/scenes/hartmann_v2/hartmann_v2_reference.png` | Cena específica |
| 15 | `o-peso-do-eco/scenes/hartmann_v2/hartmann_v2b_reference.png` | Cena específica |
| 16 | `w-hios-forensic-unit/anchors/anchors/*.png` (6 duplicados) | Duplicados estruturais |

---

## DUPLICADOS ESTRUTURAIS (6 ficheiros)

Existem em `anchors/anchors/` (subdir duplicado):

- `anchors/anchors/alejandro.valenzuela.anchor.v1.png`
- `anchors/anchors/gabi.santos.anchor.v1.png`
- `anchors/anchors/helena.meyer.junior.anchor.v1.png`
- `anchors/anchors/lucas.silva.anchor.v1.png`
- `anchors/anchors/marcus.couto.anchor.v1.png`
- `anchors/anchors/marcus.vance.anchor.v1.png`

**Questão:** São cópias idênticas dos canónicos? Verificar hash.

---

## RESUMO

| Prateleira | Ficheiros | Estado |
|------------|-----------|--------|
| CANONICO | 7 | Quase confirmado (questão Vance) |
| CANDIDATOS | 1 | Confirmado |
| ARQUIVO | 20 | Confirmado |
| PENDENTE | 16 | Aguarda decisão HD |
| DUPLICADOS | 6 | Verificar se idênticos |
| **TOTAL** | 50 | — |

---

## PRÓXIMOS PASSOS

1. HD confirma classificação dos 16 PENDENTE
2. HD confirma qual Vance é canónico (.canonical vs .v1)
3. CCode verifica se duplicados são idênticos (hash)
4. Após confirmação, CCode gera manifest de CANONICO
5. Seal manifest com `audit-bundle`

---

*"Na dúvida, classifica — não elimines."*
