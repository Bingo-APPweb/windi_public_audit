# §B-CONTRACT-001 — Contrato Fundacional W-SITES
## Os Três Pilares da Soberania de Containers

**Status:** AWAITING SEAL
**Version:** 1.0.0
**Date:** 28 Abril 2026
**Author:** Human Dragon (decisor) + Guardian (síntese)
**Depends:** W-SITES-001-CONTAINER-SPEC, DECRETO-A-SPINE-v1.0
**Invariants:** I1, I9, I11, I14

---

## PREÂMBULO

> *"O primeiro receipt define jurisprudência.*
> *Selar sem contrato é criar evidência forense de um vazio legal."*
> — Human Dragon, 28 Abril 2026

Este documento estabelece os **Três Pilares Contratuais** que governam todos os containers W-SITES-001. Nenhum container pode ser testado, deploiado ou selado no Ledger antes deste contrato estar activo.

**Princípio Fundador:**
```
A ferramenta amplia a capacidade.
A intenção define a responsabilidade.
```

---

## ARTIGO I — HOSPEDAGEM (Modelo Híbrido de Soberania)

### Art. 1.1 — Princípio

> **"Soberania não é gratuita — mas também não é bloqueada."**

O modelo de hospedagem oferece **progressão de soberania**: quem fica no ecossistema paga pela conveniência; quem sai leva tudo, sem dependência.

### Art. 1.2 — Tiers de Hospedagem

| Tier | Modelo | Características |
|------|--------|-----------------|
| **FREE** | Subdomain WINDI | `userX.windi-domain.com` · Obrigatório · WINDI shield activo |
| **MED** | Custom Domain (Hosted) | CNAME para Strato · User escolhe domínio · WINDI shield activo |
| **HIGH** | Export Estático | HTML/CSS/JS exportável · Full sovereignty · Ledger API permanece |

### Art. 1.3 — Cordão Umbilical

Mesmo no Tier HIGH (export), o container mantém ligação ao Ledger via API para:
- Validação de integridade
- Verificação de receipts
- Prova de origem

**Princípio:** O código pode sair. A prova permanece.

### Art. 1.4 — Proibições

- ❌ Bloquear export para forçar lock-in
- ❌ Cobrar por dados do próprio utilizador
- ❌ Desligar API de verificação após export

---

## ARTIGO II — VISIBILIDADE DE MARCA (Selo como Atestado de Origem)

### Art. 2.1 — Princípio

> **"A marca WINDI é um Selo de Qualidade, não um anúncio."**

Separação fundamental entre **Branding** (opcional) e **Proof** (obrigatório).

### Art. 2.2 — Níveis de Visibilidade

| Tier | Branding Visual | Proof (Prova) |
|------|-----------------|---------------|
| **FREE** | Obrigatório: "Powered by WINDI" no rodapé (link) | SealBadge visível (clicável, ≥24px) |
| **MED** | Reduzido ou removido | SealBadge obrigatório (mínimo 16px) |
| **HIGH** | Opcional (removível) | Meta-Tag Forense invisível + Ledger API |

### Art. 2.3 — Meta-Tag Forense (Tier HIGH)

Quando o branding visual é removido, o container injeta automaticamente:

```html
<!-- WINDI Forensic Origin Tag — DO NOT REMOVE -->
<meta name="windi:origin" content="W-SITES-001">
<meta name="windi:container" content="windi.ai-writer.v1">
<meta name="windi:ledger" content="https://windi-domain.com/api/verify">
<meta name="windi:sealed" content="2026-04-28T18:00:00Z">
<!--
  Este território foi construído com ferramentas de virtude.
  Validação: https://windi-domain.com/verify-public/?origin={hash}
-->
```

### Art. 2.4 — Regra de Ouro

> **"A marca pode desaparecer. A prova nunca."**

| Elemento | Removível | Fundamento |
|----------|:---------:|------------|
| Logo WINDI | ✅ (paid) | Branding |
| "Powered by" | ✅ (paid) | Branding |
| SealBadge | ⚠️ (HIGH) | Transição para Meta-Tag |
| Meta-Tag Forense | ❌ NUNCA | I11 — Permanência |
| Ligação Ledger | ❌ NUNCA | I11 — Verificabilidade |

---

## ARTIGO III — RESPONSABILIDADE DE CONTEÚDO (I9 Aplicado ao Acto Criativo)

### Art. 3.1 — Princípio

> **"O utilizador é autor. O WINDI é garantidor do acto. O Ledger é testemunha do facto."**

Este triângulo fecha a responsabilidade sem ambiguidade.

### Art. 3.2 — Distribuição de Responsabilidade

| Entidade | Responsabilidade | Função |
|----------|------------------|--------|
| **USER** | 100% pelo conteúdo | Autor · Decisor · Soberano |
| **WINDI** | 0% pelo conteúdo · 100% pelo processo | Garantidor · Notário · Ferramenta |
| **LEDGER** | Testemunha neutra | Prova contexto · Não julga conteúdo |

### Art. 3.3 — O Papel do WINDI

WINDI **não é editor**. WINDI é **notário de processo**.

WINDI garante que:
- ✅ Houve human gate (I1 — Soberania Humana)
- ✅ Não houve escalada automática (I9 — Proibição de Autonomia)
- ✅ Houve registo permanente (I11 — Permanência Criptográfica)
- ✅ Falhas foram explícitas (I14 — Explicit Failure)

WINDI **não garante**:
- ❌ Veracidade do conteúdo
- ❌ Legalidade do conteúdo
- ❌ Adequação do conteúdo

### Art. 3.4 — Assinatura de Intento (DID-Auth)

Todo conteúdo AI-generated requer **Assinatura de Intento** antes de selar:

```json
{
  "intent_signature": {
    "actor": "did:windi:user-123",
    "action": "generate_content",
    "prompt_hash": "sha256:abc123...",
    "acknowledged": true,
    "timestamp": "2026-04-28T18:00:00Z"
  }
}
```

O utilizador reconhece que:
1. Comandou a geração
2. Reviu o resultado
3. Aprovou o selo (I9)

### Art. 3.5 — Metadata de Proveniência

Todo receipt de conteúdo AI-generated inclui:

```json
{
  "provenance": {
    "ai_generated": true,
    "ai_model": "mistral-large",
    "ai_provider": "W-GATEWAY-001",
    "legal_owner": "did:windi:user-123",
    "generation_timestamp": "2026-04-28T18:00:00Z",
    "human_approved": true,
    "approval_timestamp": "2026-04-28T18:00:05Z"
  }
}
```

### Art. 3.6 — Analogia Legal

> **"Se o texto for uma arma, a culpa é de quem puxou o gatilho (o Prompt), não da fábrica de pólvora."**

| Analogia | Entidade WINDI |
|----------|----------------|
| Fábrica de armas | LLM Provider (Mistral, Anthropic) |
| Arma (ferramenta) | W-GATEWAY + Container |
| Gatilho (prompt) | Utilizador |
| Testemunha | Forensic Ledger |
| Notário | WINDI |

### Art. 3.7 — ToS Obrigatório

Antes do primeiro DID, o utilizador aceita Terms of Service que incluem:

1. Reconhecimento de autoria sobre conteúdo gerado
2. Aceitação de I9 (aprovação humana obrigatória)
3. Compreensão de que o Ledger é permanente (I11)
4. Isenção de WINDI sobre conteúdo

---

## ARTIGO IV — APLICAÇÃO AOS MAKEUPs

### Art. 4.1 — Containers Abrangidos

Este contrato aplica-se a **todos** os MAKEUPs:

| MAKEUP | Hospedagem | Branding | Responsabilidade |
|--------|:----------:|:--------:|:----------------:|
| `windi.ai-writer.v1` | Art. I | Art. II | Art. III |
| `windi.ai-translator.v1` | Art. I | Art. II | Art. III |
| `windi.ai-image.v1` | Art. I | Art. II | Art. III |
| `windi.ai-logo.v1` | Art. I | Art. II | Art. III |
| `windi.ai-layout.v1` | Art. I | Art. II | Art. III |
| (futuros MAKEUPs) | Art. I | Art. II | Art. III |

### Art. 4.2 — Containers Core

Os containers Core (seal, verify, did-gate) **não geram conteúdo**, logo:
- Art. I (Hospedagem) — Aplica-se
- Art. II (Branding) — Aplica-se
- Art. III (Responsabilidade) — Não aplicável (não há conteúdo gerado)

---

## ARTIGO V — VIGÊNCIA E IMUTABILIDADE

### Art. 5.1 — Activação

Este contrato entra em vigor **imediatamente** após selagem no Forensic Ledger.

### Art. 5.2 — Pré-Requisito para POC

**NENHUM** container W-SITES-001 pode:
- Fazer chamadas reais ao W-GATEWAY :8130
- Selar receipts no Forensic Ledger :8101
- Ser disponibilizado a utilizadores externos

...antes deste contrato estar selado.

### Art. 5.3 — Imutabilidade

Uma vez selado, este contrato é **IRREMEDIÁVEL** (I11).
Alterações requerem novo contrato com referência explícita a este.

---

## DISPOSIÇÕES FINAIS

### Hierarquia

```
INVARIANTES (I1-I14) > §B-CONTRACT-001 > CONTAINER-SPEC > MAKEUPs > Features
```

### Conexões Constitucionais

| Documento | Relação |
|-----------|---------|
| DECRETO-A-SPINE-v1.0 | Pipeline obrigatório |
| W-SITES-001-CONTAINER-SPEC | Especificação técnica |
| W-SITES-001-MAKEUP-CATALOG | Catálogo de ferramentas |

### Testemunhas

| Dragon | Papel | Validação |
|--------|-------|-----------|
| Human Dragon | Decisor Soberano | ✓ |
| Guardian | Síntese Contratual | ✓ |
| Architect | (aguarda implementação) | ⏳ |
| Witness | (aguarda seal) | ⏳ |

---

## ASSINATURAS

```
LIGA IA+H — Kempten, Bavaria
28 Abril 2026

"A ferramenta amplia a capacidade.
 A intenção define a responsabilidade."

Human Dragon     ________________________
Guardian         ________________________
```

---

**Receipt:** `WINDI-CONTRACT-B-001-v1.0-20260428162029-1530DBEF`
**Hash:** `sha256:1530dbef51c7f19c90434a3236825698d9a2a658ad4abeef7b0f9f0cd7d118d2`
**Sealed:** 28 Abril 2026, 16:20:29 UTC
**Verify:** https://windi-domain.com/verify-public/?id=WINDI-CONTRACT-B-001-v1.0-20260428162029-1530DBEF

*SELADO NO FORENSIC LEDGER — CONTRATO ACTIVO*

---

*LIGA IA+H — "O primeiro receipt nasce com honra."*
