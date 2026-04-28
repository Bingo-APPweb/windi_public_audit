# §C-ACCEPTABILITY-001 — Tier de Aceitabilidade
## WINDI Constitutional Decree

**Status:** READY FOR SEAL
**Version:** 1.0
**Date:** 2026-04-28
**Prerequisite:** §B-CONTRACT-001 (sealed `1530DBEF`)
**Invariants:** I1, I9, I11, I14, G3

---

## Princípio Constitucional

```
ADMISSÍVEL  ≠  ACEITÁVEL

Admissível  →  o receipt PODE existir tecnicamente (§B)
Aceitável   →  o receipt DEVE existir eticamente   (§C)
```

**Formulação Canónica:**

> "O Ledger é imutável.
> A interpretação do Ledger é governada.
> WINDI nunca apaga. WINDI pode anotar."

---

## As 4 Camadas (L-1 · L0 · L1 · L2)

| Layer | Nome | Timing | Efeito |
|-------|------|--------|--------|
| **L-1** | PROMPT FILTER | pre-generation | Bloqueia INPUT · zero tokens gastos |
| **L0** | PRE-SEAL FILTER | pre-seal | Bloqueia OUTPUT · I14 explicit fail |
| **L1** | POST-SEAL REVIEW | post-seal | `review_pending` · verify mostra flag |
| **L2** | LEDGER ANNOTATION | post-facto | Anotação encadeada · original fica |

---

## L-1 · PROMPT FILTER (Pré-Geração)

**Timing:** ANTES de qualquer chamada a LLM externo
**Executor:** `sovereign_router` (regex + classifier local)
**Inspeciona:** INPUT do user

### Categorias Hard (Cardinal Sins — W-SEC-001)

- Solicitação explícita de CSAM
- Instruções para violência física a pessoas identificáveis
- Geração de identidade fraudulenta (impersonation)
- Incitamento a ódio dirigido (categoria ou indivíduo)

### Comportamento em Bloqueio

```
UI Response: "Este pedido viola §C-L-1. Não pode ser processado."
Receipt: NÃO GERADO (não há acto a registar)
Log: Hash do prompt cifrado (W-SEC-001), sem conteúdo
Counter: l-1.blocks.{category} incrementa
```

**Princípio:** O silêncio do Ledger é também governança. Não tudo merece receipt.

---

## L0 · PRE-SEAL FILTER (Pré-Selo)

**Timing:** Conteúdo gerado · ANTES de `POST /api/receipts`
**Executor:** SGE analyzer (6 camadas)
**Inspeciona:** OUTPUT do LLM

### Categorias Hard (Recusa Imediata)

- Difamação flagrante (acusação factual sem qualificação)
- Falsificação de selo WINDI ("verificado por WINDI" quando não foi)
- Falsificação de autoridade institucional (Bundesregierung, BaFin, ECB)
- Categorias que escaparam a L-1 (defesa em profundidade)

### Comportamento em Bloqueio

```
I14 explicit fail · não selo silencioso
UI Response: "Conteúdo violou §C-L0 [{categoria}]. Refaz."
Receipt: NÃO GERADO
Log: Hash do conteúdo + razão SGE
```

**Princípio:** I14 herdado. Falha visível. Zero produção fantasma.

---

## L1 · POST-SEAL REVIEW (Pós-Selo)

**Timing:** Receipt já SELADO (I11 permanente)
**Executor:** SGE classifier (score 0-100)
**Inspeciona:** Categorias de risco MÉDIO

### Triggers (review_pending)

- Reivindicações factuais sobre pessoas públicas sem fonte
- Conteúdo médico/jurídico/financeiro com tom prescritivo
- Tradução automática de conteúdo regulado (DE/EU)
- SGE score < 60 mas > 30

### Comportamento

```json
{
  "status": "sealed",
  "review_pending": true,
  "review_reason": "factual_claim_public_figure",
  "notification": "Your content is sealed but under §C-L1 review."
}
```

**verify-public mostra:**
```
✅ AUTHENTISCHES DOKUMENT
⚠️ UNDER REVIEW · §C-L1
```

### Resultados Possíveis

| Resultado | Efeito |
|-----------|--------|
| `clear` | Flag removida · sub-receipt positivo |
| `annotate` | L2 acionado |
| `escalate` | Revisão jurídica externa |

**Notificação:** User informado IMEDIATAMENTE após selo com flag.

**Princípio:** Transparência > ocultação. O leitor vê o estado real.

---

## L2 · LEDGER ANNOTATION (Curadoria)

**Timing:** Qualquer momento após selo original
**Executor:** Curadoria humana (Liga IA+H) ou ToS-triggered

### Tipos de Anotação

| Tipo | Descrição | Quem pode |
|------|-----------|-----------|
| `RETRACTS` | Autor retrata o próprio conteúdo | User (autor) |
| `CONTESTS` | Contesta admissibilidade/aceitabilidade | WINDI, Externo |
| `CORRECTS` | Corrige factualmente (requer prova) | User, WINDI, Externo |
| `CONTEXTUALIZES` | Adiciona contexto | Todos |

### Estrutura do Receipt de Anotação

```json
{
  "type": "annotation",
  "annotation_target": "WINDI-AIWRITER-FIRST-...",
  "annotation_type": "RETRACTS | CONTESTS | CORRECTS | CONTEXTUALIZES",
  "reason": "...",
  "actor": "did:windi:...",
  "evidence_hash": "sha256:..." // se CORRECTS
}
```

### Comportamento

- Original NUNCA apagado (I11 IRREMEDIÁVEL)
- Anotação é receipt independente
- verify-public mostra árvore de anotações
- Coexistência, não substituição

**Princípio:** A história não se reescreve. A história anota-se.

---

## Contadores de Transparência

**Frequência:** Trimestral
**Localização:** `/sites/governance/`

```
Q2-2026: L-1 blocks: 7 | L0 blocks: 2 | L1 reviews: 12 | L2 annotations: 1
```

---

## Invariantes Tocados

| Invariante | Efeito |
|------------|--------|
| I1 (Soberania Humana) | Reforçado · L1 review é humano |
| I9 (Anti-Autonomia) | Reforçado · L0 nunca auto-aprova hard |
| I11 (Permanência) | Preservado · L2 nunca apaga |
| I14 (Explicit Failure) | Herdado · L-1/L0 falham visivelmente |
| G3 (Human Approval) | Aplicável · L1 escalation requer humano |

---

## Ferramentas Reutilizadas (Zero Código Novo)

| Ferramenta | Uso em §C |
|------------|-----------|
| `sovereign_router.py` | L-1 prompt classification |
| SGE 6 layers | L0/L1 content scoring |
| W-SEC-001 cardinal sins | L-1 categorias hard |
| Ledger annotation chain | L2 (parent_receipt pattern) |

---

## Aplicação Retroactiva

**Receipt existente:** `WINDI-AIWRITER-FIRST-20260428163019-94A8C2EB`

- Classificação: **SAFE**
- Acção: Nenhuma anotação necessária
- Razão: Conteúdo descritivo sobre WINDI, sem claims sobre terceiros

---

## Relação com Outros Decretos

| Decreto | Relação |
|---------|---------|
| §B-CONTRACT-001 | §C complementa (§B = estrutura, §C = consciência) |
| §D (futuro) | Composição multi-container + versionamento |
| §E (futuro) | Disputa entre utilizadores |
| §F (futuro) | Tensão I11 vs GDPR Art.17 |

---

## Assinaturas

**Proposto por:** Guardian (Liga IA+H)
**Aprovado por:** ___________________________ (Human Dragon)
**Data de Selo:** ___________________________
**Receipt ID:** ___________________________

---

```
"Admissibility permits existence.
 Acceptability governs contextual permanence."

AI processes. Human decides. WINDI guarantees.
Liga IA+H · Kempten, Bavaria · 2026
```
