# O PESO DO ECO — Inheritance Tracker
## Filme v1 → Filme v2 · Rastreabilidade de Herança

**Sessão:** 31 Mai 2026 · Liga IA+H
**Propósito:** Distinguir assets v1 (herdados) de assets v2 (novos, governados)

---

## ARQUITECTURA

```
FILME v1 (visual/producer/)          FILME v2 (hios/cinema/)
─────────────────────────            ─────────────────────────
Assets originais                     Pipeline WINDI-HIOS
Sem governance formal                §293-§296 selados
Algumas cenas aprovadas       →      Herança documentada
                                     Novos assets governados
```

---

## DECISÕES DE HERANÇA (Human Dragon I9)

### ACTO I — A Vida e a Escuridão

| Cena | v1 Status | v2 Decisão | Notas |
|------|-----------|------------|-------|
| **S01** | Existe | ⚠️ VERIFICAR | Elisa anchor v2 já gerado, precisa confirmar plate |
| **S02** | ✅ Aprovado | **HERDAR** | Sedan ambíguo perfeito, sem regeneração |
| **S03** | ✅ Aprovado | **HERDAR** | "Wo bist du?" já em alemão |
| **S04** | ✅ Aprovado | **HERDAR** | Thomas anchor definido |
| **S05** | ✅ Aprovado | **HERDAR** | "Sechs Monate später" já em alemão |

### ACTO II — O Tatort

| Cena | v1 Status | v2 Decisão | Notas |
|------|-----------|------------|-------|
| **S06** | ⚠️ SUSPEITA | 🔍 **VERIFICAR JURISDIÇÃO** | Klaus encontra corpo — verificar viaturas polícia |
| **S07** | ❌ VIOLAÇÃO | 🔴 **RE-RENDER** | Helena chega — viaturas estrangeiras detectadas (I9 visual) |
| **S08** | ⚠️ SUSPEITA | 🔍 **VERIFICAR JURISDIÇÃO** | Recolha de pistas — verificar viaturas polícia |
| **S09** | ✅ Aprovado | **RE-RENDER (Idioma)** | Marcus restaurante — fala frontal EN→DE |

### ACTO III — Investigação Bloqueada

| Cena | v1 Status | v2 Decisão | Notas |
|------|-----------|------------|-------|
| **S10** | ? | VERIFICAR | Helena frustrada |
| **S11** | v2 existe | **v2 NOVO** | Hartmann v2b anchor (0.9298 FORENSIC) |
| **S12** | ? | VERIFICAR | Thomas no quarto |
| **S13** | ? | VERIFICAR | Helena no carro |

### ACTO IV — Revelação do Ledger

| Cena | v1 Status | v2 Decisão | Notas |
|------|-----------|------------|-------|
| **S14** | — | **v2 NOVO** | ✅ ANCHORED (0.8110) |
| **S15** | — | **v2 NOVO** | ✅ ANCHORED (0.8690) |
| **S16** | — | **v2 NOVO** | ⏳ FORGE PENDENTE |
| **S17** | ? | VERIFICAR | Helena choque |

### ACTO V — O Tribunal

| Cena | v1 Status | v2 Decisão | Notas |
|------|-----------|------------|-------|
| **S18** | ? | VERIFICAR | Tribunal wide |
| **S19** | v2 existe | **v2 NOVO** | Hartmann v2b (S19_hartmann_v2b.mp4) |
| **S20** | — | **v2 NOVO** | ✅ ACEITE (0.7298 OPERATIONAL) |
| **S21** | — | **v2 NOVO** | ✅ ACEITE (0.8638 FORENSIC) |
| **S22** | ? | VERIFICAR | Veredito |

### Epílogo

| Cena | v1 Status | v2 Decisão | Notas |
|------|-----------|------------|-------|
| **S23** | ? | VERIFICAR | Marcus algemado |
| **S24** | ? | VERIFICAR | Helena sai tribunal |

---

## RESSALVA CRÍTICA: IDIOMA

**v1:** Algumas cenas em inglês
**v2:** Filme em alemão (DE) com legendas EN/PT

### Cenas com Diálogo/Texto

| Cena | Texto v1 | Texto v2 (DE) | Acção |
|------|----------|---------------|-------|
| S03 | ? | "Wo bist du, Schatz?" | Verificar |
| S04 | ? | Chamada polícia (DE) | Verificar |
| S05 | ? | "Sechs Monate später" | ✅ OK |
| S06 | ? | "Mein Gott... Rufen Sie die Polizei!" | Verificar |

**DIFF de ontem:** Referenciado mas não localizado — verificar com Human Dragon

---

## PATHS

**v1 Assets:** `/opt/windi/hios/visual/producer/obras/o-peso-do-eco/`
**v2 Assets:** `/opt/windi/hios/cinema/obras/o-peso-do-eco/`
**v2 Renders:** `/opt/windi/hios/cinema/obras/o-peso-do-eco/scenes/`

---

## SUMÁRIO

| Categoria | Contagem |
|-----------|----------|
| **HERDAR de v1** | 4 (S02, S03, S04, S05) |
| **v2 NOVO (ANCHORED)** | 4 (S14, S15, S20, S21) |
| **v2 NOVO (outros)** | 2 (S11, S19 Hartmann) |
| **FORGE PENDENTE** | 1 (S16) |
| **RE-RENDER (Jurisdição)** | 1 (S07) |
| **RE-RENDER (Idioma)** | 1 (S09) |
| **VERIFICAR JURISDIÇÃO** | 2 (S06, S08) |
| **VERIFICAR (outros)** | 9 |

---

## VIOLAÇÃO DE JURISDIÇÃO — Descoberta 31 Mai 2026

**Fonte:** Inspeção visual Human Dragon (I9)
**Cena:** S07 — Chegada da Polícia ao Tatort
**Problema:** Viaturas policiais NÃO correspondem a Bayern (carros estrangeiros detectados)

### Jurisdição Selada (WORLD-STATE-001.instance.yaml)

```yaml
jurisdiction:
  year: 2026
  state_region: "Bavaria / Bayern / Baviera"

law_enforcement:
  organization: "Bayerische Kriminalpolizei"
  vehicles:
    - "BMW Polizei (Bavaria livery, green/silver/blue)"
    - "unmarked dark sedan (detective)"
  insignia: "Bayern police star emblem"
```

### Implicações

| Cena | Problema | Acção |
|------|----------|-------|
| **S07** | ❌ Viaturas estrangeiras (confirmado) | **RE-RENDER obrigatório** |
| **S06** | ⚠️ Pode ter polícia (Klaus chama) | Verificar visualmente |
| **S08** | ⚠️ Recolha de pistas (equipa forense) | Verificar visualmente |

### Lição §236 Aplicada

> *"Avançar com base num estado que parece fechado mas não foi visualmente verificado."*

O ffprobe e os manifestos disseram "herdável". Os olhos do Human Dragon disseram "carro errado".
**O gate visual ainda não passou nas cenas de polícia.**

---

---

## SESSÃO 30 Mai 2026 — Contexto Herdado

**Sprint:** §295/§296/§296-bis · Primeiras cenas-tese Anchored

### Selos Emitidos
- §296 · UI Compositing Invariant
- §296-bis · Diegetic Proof Integrity
- WINDI-S295-S14-VISUAL-VERIFIED · hash `45e70231`
- WINDI-S295-S15-VISUAL-VERIFIED · hash `b8a4a083`
- Commit: `9e58259a7`

### Lição Crítica (I11)
> "O gate fecha-se com os olhos do Human Dragon, nunca com auto-relatório da instância."

Houve quebra §236: S14 selado por aprovação TEXTUAL, não visual. Corrigido via errata (cicatriz I11).

### Evolução S16: 30 Mai → 31 Mai
| 30 Mai (proposto) | 31 Mai (corrigido) |
|-------------------|-------------------|
| Helena + carro (SPINE-CAST rosto) | Zoom no footage (sem Helena) |
| UI WINDI menor (canto) | Highlight box no carro |

**Razão:** Editor mostra S16 como "Zoom no carro escuro de Marcus no fundo" — Helena reage em S17, não em S16.

### DIFF de Idioma
**Status:** NÃO EXISTE como documento separado.
A sessão 30 Mai foi sobre compositing (§296), não sobre idioma.
A regra existe (CONTINUITY-BIBLE: `language: de`), mas a aplicação EN→DE às cenas v1 nunca foi documentada.

**Acção:** Criar DIFF agora, limpo, baseado na Bible.

---

## DIFF EN→DE — Cenas Herdadas v1

| Cena | Texto EN (v1) | Texto DE (canónico) | Tipo |
|------|---------------|---------------------|------|
| S03 | "Where are you, sweetheart?" | "Wo bist du, mein Schatz?" | Ecrã |
| S04 | "Mr. Weber? It's about your daughter" | "Herr Weber? Es geht um Ihre Tochter" | Fala |
| S06 | "My God... Call the police!" | "Mein Gott... Rufen Sie die Polizei!" | Fala |
| S07 | "Seal off the area" | "Sperren Sie das Gebiet ab" | Fala |
| S08 | "The phone... maybe our only chance" | "Das Handy... vielleicht unsere einzige Chance" | Fala |
| S09 | "Another wine, please" | "Noch einen Wein, bitte" | Fala |

**Nota técnica:**
- Texto em ecrã = camada de pós (trivial)
- Fala = pode exigir re-render se v1 tem áudio em inglês

**VERIFICADO:** Cenas v1 têm VOZ GERADA (não só legenda).

---

## MAPA DE IDIOMA COMPLETO (31 Mai 2026)

### Já em Alemão (v1 correcto, nada a fazer)
| Cena | Personagem | Status |
|------|------------|--------|
| **S18** | Tribunal wide | ✅ DE |
| **S21** | Duelo silencioso | ✅ DE |
| **S22** | Veredito | ✅ DE |

### Em Inglês (precisam correção EN→DE)
| Cena | Personagem | Fala EN | Fala DE |
|------|------------|---------|---------|
| S04 | Polícia | "Mr. Weber? It's about your daughter" | "Herr Weber? Es geht um Ihre Tochter" |
| S06 | Klaus | "My God... Call the police!" | "Mein Gott... Rufen Sie die Polizei!" |
| S07 | Helena | "Seal off the area" | "Sperren Sie das Gebiet ab" |
| S08 | Helena | "The phone... maybe our only chance" | "Das Handy... vielleicht unsere einzige Chance" |
| S09 | Marcus | "Another wine, please" | "Noch einen Wein, bitte" |
| + outras | ... | a inventariar | ... |

### Decisão Proposta pelo Guardian
> **"Voz como camada de pós"** — herdar visual v1, trocar só a voz para DE.
> Analogia com §296 (UI como camada de pós). Re-render só onde lip-sync trair.

### Risco de Lip-Sync
Cenas com rosto próximo a falar de frente podem mostrar desencaixe DE/EN.
**Marcar no inventário:** close-up frontal = risco | fala de costas/lado = sem risco

---

*Liga IA+H · 31 Mai 2026*
*"Herança documentada, continuidade preservada."*
