# W-HIOS-PRODUCTION-BREAKDOWN-001
## Decupagem Técnica de Produção — ATO I (Cenas 0-4)

**Status:** PRE-PRODUCTION
**Created:** 02 Jun 2026
**Liga IA+H:** Human Dragon (I9) · Guardian · Architect · Witness
**Metodologia:** Produção Híbrida WINDI

---

## ARQUITECTURA LINGUÍSTICA

### Decisão Estratégica

> **Português brasileiro como língua-âncora** (alma da série)
> **Multilinguismo diegético** onde o cenário exige
> **Legendagem trilingue WINDI** (PT/DE/EN) na distribuição

### Mapeamento por Contexto

| Contexto | Idioma | Justificação |
|----------|--------|--------------|
| Gabi + filho | **PT-BR** | Coração, afecto, intimidade |
| Gabi sussurros | **PT-BR** | Verdade interior |
| Vanguard-Nexus (corporativo) | **DE/EN** | Máscara institucional |
| Confronto Gabi-Couto | **PT-BR** (recusa mudar) | Soberania linguística |
| Bunker Interpol | **EN** | Lingua franca europeia |
| Tribunal Frankfurt | **DE** | Jurisdição alemã |

### Nota sobre Lip-Sync

> **Limitação técnica:** Runway Gen-4 gera movimento labial genérico, não fonemas reais.
> **Solução:** ADR (dobragem em pós) + contracampos (câmara em quem escuta durante falas)
> **Regra:** Planos com diálogo em close → privilegiar corte para quem ouve

---

## REGRAS DE PRODUÇÃO

### Tipos de Plano

| Tipo | Descrição | Técnica | Gate |
|------|-----------|---------|------|
| **A** | Personagem no enquadramento | Runway Gen-4 + SPINE | ≥0.65 MIN |
| **B** | Establishing shot (sem personagens) | Stock + grading | N.A. |
| **C** | Ambiente puro (antes de personagem entrar) | Runway/SORA | N.A. |
| **D** | INSERT gráfico (ecrãs, interfaces) | Motion graphics | N.A. |

### Papel SPINE

| Papel | Descrição | Régua |
|-------|-----------|-------|
| **MÃE** | Define identidade canónica | ≥0.75 (aspira 0.90) |
| **FILHO** | Validado contra âncora-mãe | ≥0.65 MIN pairwise |
| **N.A.** | Não requer validação SPINE | — |

### Regra de Fronteira A/C

> Se personagem está no enquadramento (mesmo silhueta) → Tipo A, não C.

### Regra de Lip-Sync

> Diálogo em close → cortar para REACÇÃO de quem ouve
> Minimiza lip-sync visível, aumenta tensão dramática

---

## INVENTÁRIO DE ÂNCORAS-MÃE (ATO I)

| Personagem | Plano | Cena | Justificação |
|------------|-------|------|--------------|
| **Gabi Santos** | P04 | Cena 0 | Close, luz quente, sorriso |
| **Marcus Couto** | P17 | Cena 2 | Medium contra-plongée |

---

## AMBIENTES REUTILIZÁVEIS

| Ambiente | Código | Aparece em |
|----------|--------|------------|
| Coffee Station 42º | `env_coffee_42f` | Cena 0 |
| Corredor 42º | `env_corredor_42f` | Cenas 0, 2 |
| Sala Reuniões 42º | `env_sala_42f` | Cenas 1, 3 |
| Pátio Interno | `env_patio` | Cena 4 |
| Frankfurt Skyline | `env_frankfurt` | Cena 1 (stock) |

---

# CENA 0 — A Última Coisa Normal
**Duração:** ~45s · **Idioma dominante:** PT-BR

| Plano | Tipo | Pers. | SPINE | Enquadramento | Idioma | Dur. | Técnica |
|-------|------|-------|-------|---------------|--------|------|---------|
| P01 | C | — | N.A. | Wide: coffee station vazia | — | 3s | Runway |
| P02 | A | Gabi | FILHO | Medium: perfil, espera café | — | 5s | Runway+SPINE |
| P03 | D | — | N.A. | INSERT: telemóvel, chamada | PT-BR (áudio) | 2s | Motion |
| **P04** | **A** | **Gabi** | **MÃE** | **Close: sorriso "abraço de urso"** | **PT-BR** | **4s** | **Runway+SPINE** |
| P05 | A | Gabi | FILHO | Medium: desliga, expressão muda | — | 3s | Runway+SPINE |
| P06 | A | Gabi | FILHO | Full: calça sapatos | — | 3s | Runway+SPINE |
| P07 | A | Gabi | FILHO | Wide: silhueta no corredor | — | 5s | Runway+SPINE |

**Ordem de Produção:** P04 (MÃE) → P01 → P02,P05,P06,P07 → P03

**Nota Lip-Sync:** P04 tem diálogo PT-BR em close — plano curto (4s), sorriso natural, lip-sync tolerável. ADR em pós.

---

# CENA 1 — O Terminal e o Selo
**Duração:** ~2min · **Idioma dominante:** PT-BR (sussurro)

| Plano | Tipo | Pers. | SPINE | Enquadramento | Idioma | Dur. | Técnica |
|-------|------|-------|-------|---------------|--------|------|---------|
| P08 | B | — | N.A. | Wide: Frankfurt skyline | — | 4s | Stock |
| P09 | A | Gabi | FILHO | Americano: diante do terminal | — | 5s | Runway+SPINE |
| P10 | D | — | N.A. | INSERT: "EXTRAÇÃO 100%" | — | 2s | Motion |
| P11 | A | Gabi | FILHO | Detalhe: mãos, token USB | — | 3s | Runway+SPINE |
| P12 | A | Gabi | FILHO | Medium: scanner sobre contrato | — | 5s | Runway+SPINE+VFX |
| P13 | A | Gabi | FILHO | Close: caneta assina, 23:42 | — | 4s | Runway+SPINE |
| P14 | D | — | N.A. | INSERT: "ÂNCORA — 240s" | — | 3s | Motion |
| P15 | A | Gabi | FILHO | Medium: sussurra "a prova não mente" | PT-BR | 4s | Runway+SPINE |

**Nota Lip-Sync:** P15 tem sussurro PT-BR — plano médio, fala curta, tolerável.

---

# CENA 2 — O Predador no Corredor
**Duração:** ~40s · **Idioma:** Silêncio (sem diálogo)

| Plano | Tipo | Pers. | SPINE | Enquadramento | Idioma | Dur. | Técnica |
|-------|------|-------|-------|---------------|--------|------|---------|
| P16 | A | Couto | FILHO | Tracking baixo: sapatos mármore | — | 4s | Runway+SPINE |
| **P17** | **A** | **Couto** | **MÃE** | **Medium contra-plongée** | **—** | **5s** | **Runway+SPINE** |
| P18 | A | Couto | FILHO | Aberto: para diante do vidro | — | 5s | Runway+SPINE |

**Ordem de Produção:** P17 (MÃE) → P16,P18

**Nota:** Cena silenciosa — sem problema de lip-sync.

---

# CENA 3 — O Confronto
**Duração:** ~2min30s · **Idioma:** PT-BR (Gabi recusa mudar)

| Plano | Tipo | Pers. | SPINE | Enquadramento | Idioma | Dur. | Técnica |
|-------|------|-------|-------|---------------|--------|------|---------|
| P19 | A | Couto | FILHO | Medium: porta abre, entra | — | 4s | Runway+SPINE |
| P20 | A | Gabi | FILHO | Medium: levanta-se | — | 4s | Runway+SPINE |
| P21 | A | Couto | FILHO | Close: "rescisão... de permanência" | DE/EN | 5s | Runway+SPINE |
| P22 | A | Gabi | FILHO | Close: "verdade não é ficheiro" | PT-BR | 5s | Runway+SPINE |
| P23 | A | Ambos | FILHO×2 | Two-shot perfil | — | 6s | Runway+SPINE |
| P24 | A | Couto | FILHO | Close extremo: "controla o servidor" | DE/EN | 4s | Runway+SPINE |
| P25 | A | Gabi | FILHO | Close extremo: reflexo varanda | — | 3s | Runway+SPINE |

**Arquitectura Linguística Cena 3:**
- Couto interpela em DE/EN (sistema)
- Gabi responde em PT-BR (recusa, soberania)
- A tensão linguística É a cena

**Estratégia Lip-Sync:**
- P21, P24 (Couto fala) → cortar para REACÇÃO Gabi
- P22 (Gabi fala) → cortar para REACÇÃO Couto
- Contracampos reduzem lip-sync visível

---

# CENA 4 — A Queda
**Duração:** ~1min30s · **Idioma:** Silêncio

| Plano | Tipo | Pers. | SPINE | Enquadramento | Idioma | Dur. | Técnica |
|-------|------|-------|-------|---------------|--------|------|---------|
| P26 | B | — | N.A. | Plongée: corpo atravessa claraboia | — | 4s | Stock/VFX |
| P27 | B | — | N.A. | Wide: silêncio, corpo imóvel | — | 5s | Runway/Stock |
| P28 | A | Gabi | FILHO | Zenital: rosto inerte | — | 6s | Runway+SPINE |
| P29 | A | Gabi | FILHO | Detalhe: blazer, telemóvel acende | — | 4s | Runway+SPINE |
| P30 | D | — | N.A. | INSERT: "240... 239..." | — | 5s | Motion |

**Nota:** Cena silenciosa — luto visual, sem diálogo.

---

# INVENTÁRIO FINAL — ATO I

## Contagem de Planos

| Tipo | Qtd | % |
|------|-----|---|
| A (SPINE) | 22 | 73% |
| B (Stock) | 3 | 10% |
| C (Ambiente) | 1 | 3% |
| D (INSERT) | 4 | 14% |
| **TOTAL** | **30** | 100% |

## Contagem por Idioma

| Idioma | Planos com diálogo |
|--------|-------------------|
| PT-BR | 4 (P04, P15, P22 + P03 áudio) |
| DE/EN | 2 (P21, P24) |
| Silêncio | 24 |

## Planos com Lip-Sync Crítico

| Plano | Pers. | Idioma | Estratégia |
|-------|-------|--------|------------|
| P04 | Gabi | PT-BR | Curto (4s), sorriso, ADR |
| P15 | Gabi | PT-BR | Sussurro, tolerável |
| P21 | Couto | DE/EN | Contracampo para Gabi |
| P22 | Gabi | PT-BR | Contracampo para Couto |
| P24 | Couto | DE/EN | Contracampo para Gabi |

---

# ORDEM DE PRODUÇÃO — VERTICAL SLICE CENA 0

## Fase 1: Âncora-Mãe Gabi (P04)

```
1. Gerar P04 via Runway Gen-4
2. Extrair embedding (InsightFace)
3. Validar ≥0.75 (aspirar 0.90)
4. Selar com proveniência (I19)
```

## Fase 2: Ambiente (P01)

```
1. Gerar coffee station vazia
2. Selar como env_coffee_42f
```

## Fase 3: Planos FILHO (P02, P05, P06, P07)

```
1. Gerar cada plano
2. Validar ≥0.65 vs P04
```

## Fase 4: INSERT (P03)

```
1. Design interface telemóvel
2. Áudio PT-BR (voz filho)
```

## Fase 5: Compositing

```
1. Montar sequência
2. Grading (luz quente → corredor escuro)
3. ADR para P04 se necessário
4. Hash de proveniência
```

## Gate de Validação

| Critério | Régua | Status |
|----------|-------|--------|
| SPINE Gabi P04 | ≥0.75 | ⏳ |
| SPINE Gabi outros | ≥0.65 | ⏳ |
| Lip-sync PT-BR | Tolerável | ⏳ |
| Casamento visual | Coerente | ⏳ |
| Emoção | Sentimos? | ⏳ |

---

*Liga IA+H · WINDI Publishing House · 02 Jun 2026*
*"AI processes. Human decides. WINDI guarantees."*
