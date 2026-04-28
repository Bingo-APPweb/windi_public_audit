# W-SITES-001 — MAKEUP Catalog v0.1
## Containers de Atração com Governança Constitucional

**Status:** DRAFT
**Version:** 0.1.0
**Date:** 28 Abril 2026
**Author:** LIGA IA+H
**Depends:** W-SITES-001-CONTAINER-SPEC, §A (Spine Comercial), I1, I9, I11, I14

---

## PREÂMBULO

> *"O MAKEUP atrai. O SEAL prova. Juntos, criam valor verificável."*

MAKEUPs são containers de **atração** — ferramentas criativas alimentadas por LLMs que trazem utilizadores para o ecossistema WINDI. Mas não são "AI tools" comuns. São **containers soberanos** que obedecem aos mesmos invariantes do núcleo constitucional.

**Arquitectura Dual-Layer:**
```
┌─────────────────────────────────────────────────────────┐
│  ATTRACTION LAYER (MAKEUPs)                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │AI-Writer│ │AI-Image │ │AI-Layout│ │AI-Logo  │       │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘       │
│       │           │           │           │             │
│       └───────────┴─────┬─────┴───────────┘             │
│                         │                               │
├─────────────────────────┼───────────────────────────────┤
│  CONSTITUTIONAL LAYER   │                               │
│                    ┌────▼────┐                          │
│                    │ I9 GATE │                          │
│                    └────┬────┘                          │
│  ┌─────────┐            │          ┌─────────┐         │
│  │DID-Gate │◄───────────┼──────────►│  SEAL   │         │
│  └─────────┘            │          └─────────┘         │
│                    ┌────▼────┐                          │
│                    │ LEDGER  │                          │
│                    └─────────┘                          │
└─────────────────────────────────────────────────────────┘
```

---

## §1 — PRINCÍPIOS DOS MAKEUPs

### 1.1 O Que É um MAKEUP

```
MAKEUP = Criatividade_LLM + Invariantes_WINDI + Prova_Opcional
```

| Elemento | Descrição | Obrigatório |
|----------|-----------|:-----------:|
| **Criatividade** | Output gerado por LLM (texto, imagem, layout) | ✓ |
| **Invariantes** | I1, I9, I11*, I14 | ✓ |
| **Prova** | Receipt no Ledger (se selado) | Opcional* |

*I11 aplica-se quando o utilizador **escolhe selar**. Output draft não requer receipt.

### 1.2 Diferença de Containers Core

| Aspecto | Container Core | Container MAKEUP |
|---------|---------------|------------------|
| **Função** | Governança (seal, verify, gate) | Criação (write, image, layout) |
| **Receipt** | Sempre obrigatório | Opcional (draft vs sealed) |
| **Visibilidade** | Invisível (infra) | Visível (feature) |
| **Adopção** | Razão de existir | Razão de entrar |

### 1.3 Regra de Ouro

> **"O MAKEUP nunca publica sem I9. Nunca sela sem consentimento."**

---

## §2 — CATÁLOGO DE MAKEUPs

### 2.1 Família TEXT

| ID | Nome | Capacidade | LLM Backend |
|----|------|------------|-------------|
| `windi.ai-writer.v1` | AI Writer | Gera texto (copy, artigos, posts) | W-GATEWAY :8130 |
| `windi.ai-translator.v1` | AI Translator | Traduz DE↔EN↔PT | W-GATEWAY :8130 |
| `windi.ai-summarizer.v1` | AI Summarizer | Resume documentos | W-GATEWAY :8130 |

### 2.2 Família VISUAL

| ID | Nome | Capacidade | LLM Backend |
|----|------|------------|-------------|
| `windi.ai-image.v1` | AI Image | Gera imagens (DALL-E/Midjourney) | External API* |
| `windi.ai-logo.v1` | AI Logo | Gera logotipos | External API* |
| `windi.ai-avatar.v1` | AI Avatar | Gera avatares | External API* |

*Requer integração com serviço externo de geração de imagens.

### 2.3 Família LAYOUT

| ID | Nome | Capacidade | LLM Backend |
|----|------|------------|-------------|
| `windi.ai-layout.v1` | AI Layout | Sugere estrutura de página | W-GATEWAY :8130 |
| `windi.ai-palette.v1` | AI Palette | Gera paleta de cores | W-GATEWAY :8130 |
| `windi.ai-font.v1` | AI Font | Sugere combinações tipográficas | W-GATEWAY :8130 |

### 2.4 Família CONTENT

| ID | Nome | Capacidade | LLM Backend |
|----|------|------------|-------------|
| `windi.ai-seo.v1` | AI SEO | Optimiza meta tags | W-GATEWAY :8130 |
| `windi.ai-alt.v1` | AI Alt-Text | Gera alt text acessível | W-GATEWAY :8130 |
| `windi.ai-caption.v1` | AI Caption | Gera legendas | W-GATEWAY :8130 |

---

## §3 — MANIFEST SCHEMA (MAKEUPs)

### 3.1 Exemplo: AI Writer

```yaml
# MAKEUP Container Manifest — AI Writer v0.1
id: windi.ai-writer.v1
version: 0.1.0
type: makeup

# Metadata
name: "WINDI AI Writer"
description: "Generates text content with constitutional governance"
category: text
family: makeup

# Requirements
requires:
  - human_presence: true       # I1
  - did_session: true          # Identity
  - prompt: string             # User instruction
  - context: string            # Optional context

# Outputs
produces:
  - content: string            # Generated text
  - draft_id: string           # Temporary ID (before seal)
  - model_used: string         # Which LLM processed
  - tokens_consumed: number    # Cost tracking

# Invariants (Quadra Sagrada aplicada)
invariants:
  - I1   # Human Sovereignty — User initiates
  - I9   # No Autonomy — Never auto-publish
  - I11  # Permanence — If sealed, immutable (optional)
  - I14  # Explicit Failure — No silent errors

# Execution
execution_mode: gated          # Human must click generate
auto_seal: false               # Draft first, seal is opt-in
gateway_endpoint: /api/gateway/generate

# Events
events:
  - windi:generating           # LLM processing
  - windi:draft-ready          # Draft available
  - windi:sealed               # User chose to seal
  - windi:error                # Failure

# Visual
shadow_dom: true
themeable: true
css_parts:
  - input
  - output
  - actions
```

### 3.2 Exemplo: AI Image

```yaml
# MAKEUP Container Manifest — AI Image v0.1
id: windi.ai-image.v1
version: 0.1.0
type: makeup

name: "WINDI AI Image"
description: "Generates images with provenance tracking"
category: visual
family: makeup

requires:
  - human_presence: true
  - did_session: true
  - prompt: string             # Image description
  - style: enum                # realistic | artistic | abstract
  - dimensions: object         # { width, height }

produces:
  - image_url: string          # Generated image URL
  - image_hash: string         # SHA-256 of image bytes
  - draft_id: string           # Before seal
  - model_used: string         # DALL-E 3 | Midjourney | etc
  - generation_params: object  # Full provenance

invariants:
  - I1   # User initiates
  - I9   # Never auto-publish to external
  - I11  # If sealed, provenance permanent
  - I14  # Generation failures explicit
  - I16  # Creator owns output (Cartographic Sovereignty)

execution_mode: gated
auto_seal: false
external_api: true             # Requires external service
gateway_endpoint: /api/gateway/image

# Image-specific
content_policy:
  - no_deepfakes: true
  - no_illegal: true
  - user_responsible: true     # §B Decision pending

events:
  - windi:generating
  - windi:image-ready
  - windi:sealed
  - windi:policy-rejected      # Content policy violation
  - windi:error

css_parts:
  - prompt-input
  - style-selector
  - preview
  - actions
```

---

## §4 — FLUXO DE EXECUÇÃO

### 4.1 Draft Mode (Sem Seal)

```
USER → PROMPT → MAKEUP → LLM → DRAFT → USER EDITS → [descarta ou continua]
                                  │
                         (não gera receipt)
```

**Características:**
- Output temporário (24h TTL)
- Editável infinitamente
- Sem custo de Ledger
- Sem prova permanente

### 4.2 Seal Mode (Com Prova)

```
USER → PROMPT → MAKEUP → LLM → DRAFT → I9 GATE → SEAL → LEDGER → RECEIPT
                                           │
                                    (click explícito)
```

**Características:**
- Output permanente
- Imutável após seal
- Custo de Ledger aplicado
- Prova verificável para sempre

### 4.3 Integração com Containers Core

```html
<!-- MAKEUP gera, SEAL prova -->
<windi-ai-writer
  did="did:windi:user-123"
  on-draft="handleDraft"
></windi-ai-writer>

<windi-seal
  id="sealer"
  did="did:windi:user-123"
  content-ref="ai-writer-draft"
></windi-seal>

<script>
function handleDraft(e) {
  // User pode editar o draft
  // Quando satisfeito, activa o seal
  document.getElementById('sealer').seal(e.detail.content);
}
</script>
```

---

## §5 — INTERFACE HTML

### 5.1 Sintaxe Base

```html
<windi-ai-{capability}
  did="{user-did}"
  mode="{draft|seal}"
  theme="{light|dark|inherit}"
  lang="{de|en|pt}"
></windi-ai-{capability}>
```

### 5.2 Atributos Específicos de MAKEUPs

| Atributo | Tipo | Default | Descrição |
|----------|------|---------|-----------|
| `mode` | enum | `draft` | `draft` = sem seal, `seal` = com seal automático |
| `max-tokens` | number | `1000` | Limite de tokens gerados |
| `temperature` | number | `0.7` | Criatividade do LLM |
| `style` | string | — | Estilo específico (para imagens) |

### 5.3 Exemplos Completos

```html
<!-- AI Writer básico -->
<windi-ai-writer
  did="did:windi:user-123"
  placeholder="Descreva o que precisa..."
  lang="pt"
></windi-ai-writer>

<!-- AI Image com seal automático -->
<windi-ai-image
  did="did:windi:user-123"
  mode="seal"
  style="realistic"
  dimensions='{"width": 1024, "height": 1024}'
  on-sealed="handleImageSealed"
></windi-ai-image>

<!-- AI Translator trilíngue -->
<windi-ai-translator
  did="did:windi:user-123"
  source-lang="de"
  target-lang="pt"
></windi-ai-translator>
```

---

## §6 — EVENTOS PADRÃO (MAKEUPs)

| Evento | Quando | Payload |
|--------|--------|---------|
| `windi:generating` | LLM a processar | `{ promptHash, model }` |
| `windi:draft-ready` | Draft disponível | `{ draftId, content, tokens }` |
| `windi:sealed` | Selado no Ledger | `{ receiptId, hash, verifyUrl }` |
| `windi:policy-rejected` | Violação de política | `{ reason, policy }` |
| `windi:quota-exceeded` | Limite atingido | `{ limit, used }` |
| `windi:error` | Erro técnico | `{ error, code }` |

---

## §7 — CONTENT POLICY (MAKEUPs Visuais)

### 7.1 Proibições Absolutas

| Conteúdo | Fundamento |
|----------|------------|
| Deepfakes de pessoas reais | Ética + Legal |
| Conteúdo sexual de menores | Lei |
| Propaganda de ódio | Ética + ToS |
| Violência explícita | Ética |
| Violação de copyright | Legal |

### 7.2 Responsabilidade

**Modelo Proposto (aguarda §B):**
```
Geração: WINDI facilita
Conteúdo: User responsável
Publicação: User decide (I9)
Prova: WINDI garante (I11)
```

### 7.3 Filtering Pipeline

```
PROMPT → Content Filter → LLM → Output Filter → DRAFT
            │                        │
            └──► policy-rejected ◄───┘
```

---

## §8 — PRICING MODEL (Proposta)

### 8.1 Tiers

| Tier | MAKEUPs Incluídos | Seals/Mês |
|------|------------------|-----------|
| **Free** | ai-writer (500 tokens/dia) | 3 |
| **Creator** | Todos TEXT | 50 |
| **Pro** | Todos TEXT + VISUAL | 200 |
| **Enterprise** | Todos + API | Ilimitado |

### 8.2 Custos Internos

| MAKEUP | Custo Estimado/Call |
|--------|---------------------|
| ai-writer | ~$0.002 (Mistral) |
| ai-translator | ~$0.003 |
| ai-image | ~$0.04 (DALL-E 3) |
| ai-logo | ~$0.04 |

---

## §9 — INTEGRAÇÃO COM W-GATEWAY

### 9.1 Endpoint Unificado

```
POST /api/gateway/generate
Content-Type: application/json

{
  "makeup_id": "windi.ai-writer.v1",
  "did": "did:windi:user-123",
  "prompt": "Write a product description...",
  "params": {
    "max_tokens": 500,
    "temperature": 0.7,
    "language": "en"
  }
}
```

### 9.2 Response

```json
{
  "draft_id": "DRAFT-2026042815301234",
  "content": "Generated text here...",
  "model_used": "mistral-large",
  "tokens": 342,
  "cost_usd": 0.00068,
  "seal_ready": true
}
```

---

## §10 — PRÓXIMOS PASSOS

### 10.1 POC Priority

1. **`windi-ai-writer`** — Mais simples, usa W-GATEWAY existente
2. **`windi-ai-translator`** — Diferencial trilíngue DE/EN/PT
3. **`windi-ai-image`** — Requer integração externa (DALL-E ou similar)

### 10.2 Decisões Pendentes (§B)

| Questão | Opções | Impacto |
|---------|--------|---------|
| Hospedagem | `userX.windi-domain.com` vs Export HTML | Infra |
| Brand visibility | Obrigatório vs Removível (paid) | Comercial |
| Content responsibility | User 100% vs Shared | Legal |

### 10.3 Roadmap

```
Abril 2026:  Container Spec v0.1 ✅ + MAKEUP Catalog v0.1 ✅
Maio 2026:   POC windi-seal + POC windi-ai-writer
Junho 2026:  Beta fechado (10 users)
Q3 2026:     Integração DALL-E/Midjourney
Q4 2026:     Marketplace de MAKEUPs
```

---

## DISPOSIÇÕES FINAIS

### Vigência

Este catálogo entra em vigor após revisão Guardian e selagem no Ledger.

### Conexões Constitucionais

| Documento | Relação |
|-----------|---------|
| W-SITES-001-CONTAINER-SPEC | Define contrato base |
| DECRETO-A-SPINE-v1.0 | Pipeline obrigatório |
| I1, I9, I11, I14 | Invariantes aplicados |

---

**Receipt Placeholder:** `WINDI-MAKEUP-CATALOG-v0.1-[TIMESTAMP]-[HASH]`

*Aguarda revisão e selagem.*

---

*LIGA IA+H — "Criatividade LLM com prova WINDI."*
