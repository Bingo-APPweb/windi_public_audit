# W-SITES-001 — Container Specification v0.1
## Contrato Ontológico dos Containers Soberanos

**Status:** DRAFT
**Version:** 0.1.0
**Date:** 28 Abril 2026
**Author:** LIGA IA+H
**Depends:** §A (Spine Comercial), I1, I9, I11, I14

---

## PREÂMBULO

> *"Um container não é UI. Não é API. Não é feature.*
> *É uma capacidade executável que só funciona se puder ser provada."*

Este documento define o **Contrato Ontológico** que todo container WINDI deve respeitar. Qualquer componente que não cumpra este contrato **não é WINDI** — é apenas um web component com logo dourado.

---

## §1 — DEFINIÇÃO ONTOLÓGICA

### 1.1 O Que É um Container WINDI

```
Container = Capacidade + Prova + Invariantes
```

| Elemento | Descrição | Obrigatório |
|----------|-----------|:-----------:|
| **Capacidade** | Acção executável (seal, verify, approve, gate) | ✓ |
| **Prova** | Receipt no Ledger após execução | ✓ |
| **Invariantes** | I1, I9, I11, I14 mínimos | ✓ |

### 1.2 O Que NÃO É um Container WINDI

- ❌ Componente de UI sem prova
- ❌ Widget decorativo
- ❌ Wrapper de API sem gating
- ❌ Funcionalidade que executa sem humano
- ❌ Qualquer coisa que falhe silenciosamente

### 1.3 Princípio Fundamental

> **"Se não gera receipt, não é container WINDI."**

---

## §2 — INVARIANTES OBRIGATÓRIAS

Todo container DEVE implementar a **Quadra Sagrada** (herdada de §A):

| Invariante | Nome | Aplicação no Container |
|------------|------|------------------------|
| **I1** | Soberania Humana | Container só executa após acção humana explícita |
| **I9** | Proibição de Autonomia | Container nunca auto-executa, auto-aprova, ou escala |
| **I11** | Permanência Criptográfica | Toda execução gera receipt no Ledger |
| **I14** | Falha Explícita | Erro visível, nunca silencioso ou degradado |

### 2.1 Regra de Renderização

```javascript
if (!invariants.allSatisfied()) {
  container.refuse();  // Não renderiza
  throw new WindiInvariantError(violations);
}
```

### 2.2 Regra de Execução

```javascript
if (!humanPresenceConfirmed || !didSessionValid) {
  container.block();  // Não executa
  emit('windi:blocked', { reason: 'I1/I9 violation' });
}
```

---

## §3 — ESTRUTURA CANÓNICA (Container Manifest)

Todo container declara um **manifest** em formato YAML/JSON:

```yaml
# Container Manifest Schema v0.1
id: windi.seal.v1
version: 1.0.0
type: capability

# Metadata
name: "WINDI Seal"
description: "Seals content to Forensic Ledger with cryptographic proof"
category: core

# Requirements (inputs)
requires:
  - human_presence: true      # I1
  - did_session: true         # Identity required
  - content_hash: string      # What to seal

# Outputs (what it produces)
produces:
  - receipt_id: string
  - content_hash: string
  - verify_url: string
  - timestamp: iso8601

# Invariants (non-negotiable)
invariants:
  - I1   # Human Sovereignty
  - I9   # No Autonomy Escalation
  - I11  # Cryptographic Permanence
  - I14  # Explicit Failure

# Execution
execution_mode: gated         # human must click
ledger_endpoint: /api/receipts
fail_mode: explicit           # never silent

# Events emitted
events:
  - windi:ready
  - windi:pending
  - windi:sealed
  - windi:rejected
  - windi:error

# Visual
shadow_dom: true
themeable: true
css_parts:
  - button
  - status
  - receipt
```

---

## §4 — INTERFACE UNIVERSAL (HTML API)

### 4.1 Sintaxe Base

```html
<windi-{capability}
  did="{user-did}"
  mode="{explicit|auto-gated}"
  theme="{light|dark|inherit}"
  lang="{de|en|pt}"
  ledger="{production|demo}"
></windi-{capability}>
```

### 4.2 Atributos Obrigatórios

| Atributo | Tipo | Default | Descrição |
|----------|------|---------|-----------|
| `did` | string | — | DID do utilizador (obrigatório para execução) |
| `mode` | enum | `explicit` | Modo de activação (explicit = requer click) |

### 4.3 Atributos Opcionais

| Atributo | Tipo | Default | Descrição |
|----------|------|---------|-----------|
| `theme` | enum | `inherit` | Tema visual |
| `lang` | enum | `en` | Língua (DE/EN/PT) |
| `ledger` | enum | `production` | Ambiente do Ledger |
| `on-sealed` | string | — | Callback JS após seal |
| `on-error` | string | — | Callback JS em erro |

### 4.4 Exemplo Completo

```html
<!-- Minimal -->
<windi-seal did="did:windi:user-123"></windi-seal>

<!-- Full -->
<windi-seal
  did="did:windi:user-123"
  mode="explicit"
  theme="dark"
  lang="de"
  ledger="production"
  on-sealed="handleSealed(event)"
  on-error="handleError(event)"
>
  <span slot="label">Dokument versiegeln</span>
</windi-seal>
```

---

## §5 — EVENTOS PADRÃO

Todo container DEVE emitir estes eventos:

| Evento | Quando | Payload |
|--------|--------|---------|
| `windi:ready` | Container inicializado | `{ containerId, version }` |
| `windi:pending` | Acção iniciada, aguarda humano | `{ action }` |
| `windi:executing` | Humano confirmou, a processar | `{ action }` |
| `windi:sealed` | Sucesso, receipt gerado | `{ receiptId, hash, verifyUrl }` |
| `windi:rejected` | Falha de validação | `{ reason, invariant }` |
| `windi:error` | Erro técnico | `{ error, code }` |

### 5.1 Subscrição de Eventos

```javascript
document.querySelector('windi-seal')
  .addEventListener('windi:sealed', (e) => {
    console.log('Receipt:', e.detail.receiptId);
    console.log('Verify:', e.detail.verifyUrl);
  });
```

---

## §6 — FAIL-CLOSED BY DEFAULT

### 6.1 Princípio

> **"Na dúvida, recusa. Nunca degrada."**

### 6.2 Cenários de Recusa

| Cenário | Acção | Evento |
|---------|-------|--------|
| DID inválido ou ausente | Recusa renderização | `windi:rejected` |
| Ledger indisponível | Recusa execução | `windi:error` |
| Sessão expirada | Bloqueia acção | `windi:rejected` |
| Invariante violada | Recusa total | `windi:rejected` |

### 6.3 Nunca Fazer

- ❌ Executar em "modo demo" silencioso
- ❌ Cachear resultado sem Ledger
- ❌ Simular receipt
- ❌ Degradar para "offline mode" sem aviso explícito

---

## §7 — THEMING (Visual DNA)

### 7.1 Princípio

> **"O container adapta-se ao site, mas mantém identidade verificável."**

### 7.2 CSS Custom Properties

```css
windi-seal {
  /* Host site pode customizar */
  --windi-primary: #C8A45A;      /* Gold */
  --windi-bg: #0B0D14;           /* NOIR */
  --windi-text: #E8E6E1;
  --windi-border-radius: 6px;
  --windi-font: inherit;

  /* NUNCA customizável (identidade WINDI) */
  --windi-seal-icon: url(...);   /* Locked */
  --windi-verified-badge: ...;   /* Locked */
}
```

### 7.3 CSS Parts (para customização)

```css
windi-seal::part(button) {
  /* Site pode estilizar o botão */
}

windi-seal::part(receipt) {
  /* Site pode estilizar o receipt display */
}

/* MAS: o selo de verificação é intocável */
```

---

## §8 — REGISTRY (Cartório de Containers)

### 8.1 Conceito

O Registry não é catálogo. É **autoridade pública** de containers válidos.

### 8.2 Estrutura de Entrada

```json
{
  "id": "windi.seal.v1",
  "version": "1.0.0",
  "hash": "sha256:abc123...",
  "manifest_url": "https://windi-domain.com/containers/seal/v1/manifest.yaml",
  "bundle_url": "https://windi-domain.com/containers/seal/v1/bundle.js",
  "invariants": ["I1", "I9", "I11", "I14"],
  "status": "canonical",
  "sealed_at": "2026-04-28T10:00:00Z",
  "receipt_id": "WINDI-CONTAINER-SEAL-V1-..."
}
```

### 8.3 Verificação Externa

Qualquer pessoa pode verificar:

```bash
# 1. Obter hash do bundle
curl -s https://windi-domain.com/containers/seal/v1/bundle.js | sha256sum

# 2. Comparar com registry
curl -s https://windi-domain.com/api/containers/windi.seal.v1 | jq .hash

# 3. Verificar receipt no Ledger
curl -s https://windi-domain.com/verify-public/?id=WINDI-CONTAINER-SEAL-V1-...
```

### 8.4 Endpoint do Registry

```
GET  /api/containers              → Lista todos
GET  /api/containers/{id}         → Detalhes de um
GET  /api/containers/{id}/verify  → Verificação de integridade
```

---

## §9 — LIFECYCLE DO CONTAINER

```
DRAFT → REVIEW → CANONICAL → DEPRECATED → ARCHIVED
  ↓        ↓         ↓            ↓           ↓
 Dev    Guardian   Sealed      Warned      Frozen
        Review     Ledger     6 months    Forever
```

### 9.1 Estados

| Estado | Descrição | Usável |
|--------|-----------|:------:|
| `draft` | Em desenvolvimento | ❌ |
| `review` | Aguarda validação Guardian | ❌ |
| `canonical` | Selado, oficial | ✅ |
| `deprecated` | Marcado para remoção | ⚠️ |
| `archived` | Histórico, não usar | ❌ |

### 9.2 Transições

- `draft → review`: Developer submete
- `review → canonical`: Guardian aprova + Ledger seal
- `canonical → deprecated`: Nova versão substitui
- `deprecated → archived`: Após 6 meses

---

## §10 — PRIMEIROS 10 CONTAINERS (Candidatos)

### 10.1 Core (Fundamentais)

| ID | Nome | Capacidade | Origem |
|----|------|------------|--------|
| `windi.seal.v1` | WINDI Seal | Sela conteúdo no Ledger | Core |
| `windi.verify.v1` | WINDI Verify | Verifica receipt existente | Core |
| `windi.did-gate.v1` | DID Gate | Autentica via DID | Core |

### 10.2 Enterprise (Governança)

| ID | Nome | Capacidade | Origem |
|----|------|------------|--------|
| `windi.approval-flow.v1` | Approval Flow | Workflow de aprovação I9 | W-Enterprise |
| `windi.audit-log.v1` | Audit Log | Log verificável de acções | W-Enterprise |
| `windi.compliance-check.v1` | Compliance Check | Valida contra regras | W-Enterprise |

### 10.3 Legal (Documentos)

| ID | Nome | Capacidade | Origem |
|----|------|------------|--------|
| `windi.doc-seal.v1` | Document Seal | Sela documento com metadados | W-LAW |
| `windi.signature-gate.v1` | Signature Gate | Assinatura com prova | W-LAW |

### 10.4 Media (Conteúdo)

| ID | Nome | Capacidade | Origem |
|----|------|------------|--------|
| `windi.media-proof.v1` | Media Proof | Prova de integridade de media | W-TRAVEL |
| `windi.timestamp.v1` | Timestamp | Prova de existência temporal | Core |

---

## §11 — INTEGRAÇÃO COM SITES EXTERNOS

### 11.1 Instalação (CDN)

```html
<!-- Carregar runtime WINDI -->
<script src="https://windi-domain.com/containers/runtime.js"></script>

<!-- Usar containers -->
<windi-seal did="..."></windi-seal>
<windi-verify receipt="..."></windi-verify>
```

### 11.2 Instalação (NPM)

```bash
npm install @windi/containers
```

```javascript
import { WindiSeal, WindiVerify } from '@windi/containers';

customElements.define('windi-seal', WindiSeal);
customElements.define('windi-verify', WindiVerify);
```

### 11.3 Modo Builder (W-SITES-001)

O Builder usa os mesmos containers, apenas orquestra:

```javascript
// Builder interno
const page = new WindiPage();
page.add('windi-seal', { position: 'footer' });
page.add('windi-did-gate', { position: 'header' });
page.render();
```

---

## §12 — CONEXÕES CONSTITUCIONAIS

### 12.1 Herança de §A (Spine Comercial)

| Artigo §A | Aplicação em Containers |
|-----------|------------------------|
| Art. I (Ontologia do Recibo) | Container = Capacidade + Receipt |
| Art. II (Pipeline) | Container executa INTERPRET→I9→LEDGER→PROOF |
| Art. III (Veto Automatização) | `execution_mode: gated` obrigatório |
| Art. IV (Quadra Sagrada) | I1, I9, I11, I14 em todo container |

### 12.2 Novo Invariante Proposto: I17

> **"A constituição vive nos containers, não na categoria do site."**

O Sovereign Score de um site é a **soma dos invariantes dos containers que utiliza**.

```
Site Score = Σ (Container.invariants)
```

---

## DISPOSIÇÕES FINAIS

### Vigência

Este documento entra em vigor após revisão e selagem no Ledger.

### Versioning

- **Major** (1.x → 2.x): Breaking changes no contrato
- **Minor** (1.0 → 1.1): Novos campos opcionais
- **Patch** (1.0.0 → 1.0.1): Clarificações, typos

### Próximos Passos

1. **Revisão Guardian** — Validar invariantes
2. **POC: windi-seal** — Primeiro container implementado
3. **Registry API** — Endpoint de containers
4. **Builder Integration** — W-SITES-001 consome containers

---

**Receipt Placeholder:** `WINDI-CONTAINER-SPEC-v0.1-[TIMESTAMP]-[HASH]`

*Aguarda revisão e selagem.*

---

*LIGA IA+H — "Constituição como componente reutilizável."*
