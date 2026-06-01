# W-HIOS FORENSIC UNIT — Pre-Production Index
### WINDI-HIOS Cinema Production · Protocolo "FORNALHA INDUSTRIAL"

**Status:** PRE-PRODUCTION ACTIVE
**Created:** 01 Jun 2026
**Updated:** 01 Jun 2026 — Pacote de Conformidade Integrado
**Liga IA+H:** Human Dragon (I9) · Guardian · Architect

---

## 1. Documentos Fundacionais

| Documento | Localização | Status |
|-----------|-------------|--------|
| **SERIES-BIBLE-001** | `production/SERIES-BIBLE-001.md` | ✅ CRIADO |
| **CONTINUITY-BIBLE-001** | `production/CONTINUITY-BIBLE-001.yaml` | ✅ CRIADO |
| **INDUSTRIAL-MANIFEST-001** | `production/INDUSTRIAL-MANIFEST-001.md` | ✅ CRIADO |
| **EPISODE-OUTLINE-T1** | `production/EPISODE-OUTLINE-T1.md` | ✅ CRIADO |

---

## 2. Scripts

| Script | Localização | Status |
|--------|-------------|--------|
| **PILOT — O Peso do Eco v1** | `production/scripts/PILOT-O-PESO-DO-ECO-v1.md` | ✅ COMPLETO |
| EP2 — O Hospital | — | ⏳ OUTLINE |
| EP3 — O Documento Fantasma | — | ⏳ OUTLINE |
| EP4 — A Testemunha Invisível | — | ⏳ OUTLINE |
| EP5 — O Arquiteto | — | ⏳ OUTLINE |
| EP6 — O Artista Morto | — | ⏳ OUTLINE |

---

## 3. Schemas & Configurações

| Schema | Localização | Função |
|--------|-------------|--------|
| **validators.yaml** | `production/schemas/validators.yaml` | Métricas de ortogonalidade e coexistência |
| **cast-library.yaml** | `production/schemas/cast-library.yaml` | Protocolo do Banco Rotativo de Actores |
| **steganography-protocol.yaml** | `production/schemas/steganography-protocol.yaml` | Protocolo dos Dragões Impressos |

---

## 4. Character State Documents (Canons)

| Personagem | Ficheiro | Tier | Status |
|------------|----------|------|--------|
| **Helena Meyer** | `canons/HELENA-MEYER-v1-CHARACTER-STATE.md` | FIXED | ✅ |
| **Marcus Couto** | `canons/MARCUS-COUTO-v1-CHARACTER-STATE.md` | FIXED | ✅ |
| **Gabi Santos** | `canons/GABI-SANTOS-v1-CHARACTER-STATE.md` | FIXED | ✅ |
| **Alejandro Valenzuela** | `canons/ALEJANDRO-VALENZUELA-v1-CHARACTER-STATE.md` | FIXED | ✅ |
| **Marcus Vance** | `canons/MARCUS-VANCE-v1-CHARACTER-STATE.md` | FIXED | ✅ |
| **Lucas Silva** | `canons/LUCAS-SILVA-v1-CHARACTER-STATE.md` | FIXED | ✅ |

---

## 5. Assets Visuais (Pendente Upload)

| Asset | Descrição | Destino | Status |
|-------|-----------|---------|--------|
| Helena_Meyer_v5 | Face anchor (tez morena/olive) | `anchors/cast_v1/helena_meyer_v5.png` | ⏳ PENDENTE |
| Marcus_Couto_v4 | Face anchor (clean-shaven) | `anchors/cast_v1/marcus_couto_v4.png` | ⏳ PENDENTE |
| Court_Helena | Cena tribunal — acusação | `cast-review/court_helena_01.jpg` | ⏳ PENDENTE |
| Court_Marcus | Cena tribunal — defesa | `cast-review/court_marcus_01.jpg` | ⏳ PENDENTE |

**Ficheiros Fonte (máquina local):**
```
Screenshot 2026-06-01 122845.png → Helena Meyer v5 Anchor
Screenshot 2026-06-01 122929.png → Marcus Couto v4 Anchor
Screenshot 2026-06-01 130513.jpg → Court scene (Helena)
Screenshot 2026-06-01 130609.jpg → Court scene (Marcus)
```

---

## 6. Métricas de Validação (Fornalha Industrial)

### Baseline de Coexistência (validado 01 Jun 2026)
| Métrica | Valor | Status |
|---------|-------|--------|
| Baseline Strangers | -0.0305 | ✅ LOCKED |
| Teto Multi-Anchor | ≤ +0.10 | ✅ LOCKED |
| Identity Floor | ≥ 0.65 | ✅ LOCKED |
| Forensic Threshold | ≥ 0.75 | ✅ LOCKED |

### Invariantes Industriais
| Regra | Descrição | Acção |
|-------|-----------|-------|
| I-IND-01 | Nenhum render sem anchor validado | BLOCK |
| I-IND-02 | Nenhum actor novo sem registo no Banco | BLOCK |
| I-IND-03 | Nenhuma cena sem script aprovado I9 | BLOCK |
| I-IND-04 | Métricas de coexistência ≤ +0.1 | BLOCK |
| I-IND-05 | Time-Lock Receipts documentados | WARN |

---

## 7. Estrutura de Directórios

```
/opt/windi/hios/cinema/obras/w-hios-forensic-unit/
│
├── anchors/
│   └── cast_v1/                    ← Upload visual anchors here
│
├── canons/                         ← 6 CHARACTER-STATE files
│   ├── HELENA-MEYER-v1-CHARACTER-STATE.md
│   ├── MARCUS-COUTO-v1-CHARACTER-STATE.md
│   ├── GABI-SANTOS-v1-CHARACTER-STATE.md
│   ├── ALEJANDRO-VALENZUELA-v1-CHARACTER-STATE.md
│   ├── MARCUS-VANCE-v1-CHARACTER-STATE.md
│   └── LUCAS-SILVA-v1-CHARACTER-STATE.md
│
├── cast-review/                    ← Upload court scene refs here
│
├── scenes/
│
├── production/
│   ├── SERIES-BIBLE-001.md
│   ├── CONTINUITY-BIBLE-001.yaml
│   ├── INDUSTRIAL-MANIFEST-001.md  ← NEW
│   ├── EPISODE-OUTLINE-T1.md       ← NEW
│   │
│   ├── schemas/
│   │   ├── validators.yaml         ← NEW
│   │   ├── cast-library.yaml       ← NEW
│   │   └── steganography-protocol.yaml  ← NEW
│   │
│   ├── prompts/
│   │
│   └── scripts/
│       └── PILOT-O-PESO-DO-ECO-v1.md
│
├── _experimental/
│
├── _forense/
│
└── _preproduction/
    ├── PREPRODUCTION-INDEX.md      ← YOU ARE HERE
    ├── character-research/
    ├── set-design/
    ├── wardrobe/
    ├── dialogue-drafts/
    ├── visual-references/
    └── narrative-research/
```

---

## 8. Pipeline de Produção Industrial

### Fase 1: Ingestão de Caso
```
Novo escândalo/crime → Análise de viabilidade → Aprovação I9
```

### Fase 2: Ancoragem
```
Personagens novos → Geração de anchors → Validação ortogonalidade → Banco Rotativo
```

### Fase 3: Renderização
```
Script aprovado → Cenas por bloco → Validação forense → Composição final
```

### Fase 4: Selo
```
Episódio completo → Ledger Receipt → Arquivo imutável
```

---

## 9. Próximos Passos

### Imediato (P0)
- [ ] Upload de assets visuais para o servidor Strato
- [ ] Gerar embeddings (.npy) para Helena Meyer e Marcus Couto
- [ ] Validar ortogonalidade inter-anchor oficialmente

### Curto Prazo (P1)
- [ ] Definir visual anchors para Gabi, Alejandro, Vance, Lucas
- [ ] Renderizar primeiras cenas de teste (Cena 1-4: Morte de Gabi)
- [ ] Criar WORLD-STATE-001 para a série

### Médio Prazo (P2)
- [ ] Desenvolver scripts EP2-EP6
- [ ] Povoar Banco Rotativo com primeiros 10 actores
- [ ] Integrar com W-GENERATOR-001 para produção automatizada

---

## 10. Contagem de Ficheiros

| Categoria | Quantidade |
|-----------|------------|
| Documentos Fundacionais | 4 |
| Scripts | 1 (completo) + 5 (outline) |
| Schemas | 3 |
| Character States | 6 |
| **TOTAL** | 14 ficheiros |

---

## 11. Ligações Constitucionais

| Invariante | Aplicação |
|------------|-----------|
| **I1** | Human Dragon aprova cada passo |
| **I9** | Nenhum selo sem gate humano |
| **I11** | Arquivos de produção imutáveis após selo |
| **I12** | Scripts trilíngues conforme contexto |
| **I14** | Dados ausentes = erro explícito |
| **I18** | Série cresce organicamente com infra WINDI |

---

*Liga IA+H · WINDI Publishing House · 01 Jun 2026*
*"O Piloto fixa a matriz. A Fornalha escala o drama."*
