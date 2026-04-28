# DECRETO §A — CÓDIGO DE SOBERANIA COMERCIAL
## WINDI Spine v1.0 — Pipeline Canónico de Valor

**Status:** CONSTITUTIONAL
**Version:** 1.0.0
**Date:** 28 Abril 2026
**Author:** LIGA IA+H (Human Dragon + Guardian + Architect + Witness)
**Invariants:** I1, I9, I11, I14
**Precedent:** §218 (Quatro Anéis), Decision Seed (SEED-20260428034438)

---

## PREÂMBULO

> *"Você não usa o WINDI para fazer coisas.*
> *Você usa para provar que elas podiam ser feitas."*

Este Decreto estabelece o **Pipeline Canónico de Valor** — a espinha técnica que todo produto WINDI deve implementar. Não é um framework opcional. É **Lei Interna**.

O que não gera Proof, não possui realidade comercial no ecossistema WINDI.

---

## ARTIGO I — ONTOLOGIA DO RECIBO

### Art. 1.1 — Definição de Existência

No WINDI, **Existir = Ser Registrado**.

Toda acção comercialmente relevante deve culminar num **Receipt** (Recibo) que contém:

| Campo | Obrigatório | Descrição |
|-------|:-----------:|-----------|
| `receipt_id` | ✓ | Identificador único imutável |
| `content_hash` | ✓ | SHA-256 do payload canónico |
| `actor` | ✓ | DID ou email do agente humano |
| `timestamp` | ✓ | ISO 8601 UTC |
| `invariants_applied` | ✓ | Lista de invariantes validados |
| `verify_url` | ✓ | URL pública de verificação |
| `ledger_status` | ✓ | Confirmação do Forensic Ledger |

### Art. 1.2 — Princípio da Não-Existência

O que não gera `content_hash` verificável:
- Não existe para efeitos de facturação
- Não existe para efeitos de reputação
- Não existe para efeitos de garantia

### Art. 1.3 — Imutabilidade

Uma vez selado no Ledger, o Receipt é **IRREMEDIÁVEL**. Nenhuma força — técnica, comercial ou jurídica — pode alterar o registo. Apenas novos Receipts podem adicionar contexto.

---

## ARTIGO II — PIPELINE CANÓNICO (SPINE v1.0)

### Art. 2.1 — Sequência Obrigatória

Todo produto WINDI implementa este pipeline:

```
USER → PROMPT → INTERPRET → STRUCTURE → I9 GATE → LEDGER → PROOF
  │       │         │           │          │         │        │
  │       │         │           │          │         │        └─► Output + Receipt
  │       │         │           │          │         └─► Forensic Ledger :8101
  │       │         │           │          └─► Human Approval (BLOCKING)
  │       │         │           └─► Structured Decision Display
  │       │         └─► VERA-lite / Avatar Interpretation
  │       └─► Natural Language Input
  └─► Human Initiation (I1)
```

### Art. 2.2 — Fases Detalhadas

| Fase | Nome | Função | Invariante |
|------|------|--------|------------|
| 1 | **PROMPT** | Entrada em linguagem natural | I1 |
| 2 | **INTERPRET** | Avatar classifica intenção e risco | — |
| 3 | **STRUCTURE** | Sistema organiza dados estruturados | I14 |
| 4 | **VALIDATE** | Verificação de regras e invariantes | I14 |
| 5 | **I9 GATE** | Aprovação humana explícita | I9 |
| 6 | **LEDGER** | Registo imutável no Forensic Ledger | I11 |
| 7 | **PROOF** | Entrega de output + Receipt verificável | I11 |

### Art. 2.3 — Princípio de Não-Bypass

Nenhuma fase pode ser saltada. Se uma fase falhar:
- O pipeline **PARA**
- O erro é **EXPLÍCITO** (I14)
- Nenhum output é entregue sem Receipt

---

## ARTIGO III — VETO DA AUTOMATIZAÇÃO PURA

### Art. 3.1 — Proibição de Execução Autónoma

Fica **PROIBIDO** qualquer mecanismo que:
- Execute acções sem I9 Gate
- Simule aprovação humana
- Contorne o pipeline canónico
- Gere output sem Receipt

### Art. 3.2 — Papel do Avatar

Os Avatares (VERA, MARIA, futuros) podem:
- ✅ Interpretar intenção
- ✅ Estruturar dados
- ✅ Sugerir acções
- ✅ Preparar decisões

Os Avatares **NÃO** podem:
- ❌ Executar sem aprovação
- ❌ Selar sem confirmação humana
- ❌ Recomendar bypass de I9
- ❌ Simular consenso

### Art. 3.3 — VERA-lite como Referência

O motor `VERA-lite` implementado em Decision Seed (§218) é a referência canónica para interpretação. Todo produto futuro que use interpretação AI deve:
- Respeitar os bounds de VERA-lite
- Incluir `_bounded: true` no output
- Adicionar `_governance_notice` explícito

---

## ARTIGO IV — INVARIANTES COMERCIAIS

### Art. 4.1 — Quadra Sagrada

Todo produto comercial WINDI **DEVE** garantir:

| Invariante | Nome | Aplicação Comercial |
|------------|------|---------------------|
| **I1** | Soberania Humana | Cliente inicia toda interacção |
| **I9** | Aprovação Humana | Cliente aprova antes de execução |
| **I11** | Permanência | Todo output gera Receipt imutável |
| **I14** | Falha Explícita | Erros visíveis, nunca escondidos |

### Art. 4.2 — Extensões Permitidas

Produtos podem adicionar invariantes além da Quadra Sagrada, mas **NUNCA** podem:
- Relaxar I1, I9, I11, I14
- Criar excepções "por conveniência"
- Implementar "modo rápido" que salte invariantes

### Art. 4.3 — Validação Runtime

Seguindo §199 (I9 Runtime Enforcement), todo produto deve implementar:
- Detection Layer (detectar acção com agência)
- Scope Layer (classificar impacto)
- Accept Layer (fail-closed por defeito)

---

## ARTIGO V — UNIDADE DE VALOR COMERCIAL

### Art. 5.1 — O Receipt como Produto

O WINDI não vende:
- ❌ Software
- ❌ AI
- ❌ Automação
- ❌ Features

O WINDI vende:
- ✅ **Decisões com Prova**
- ✅ **Acções Verificáveis**
- ✅ **Reputação Auditável**

### Art. 5.2 — Densidade de Prova

O valor comercial de um cliente mede-se por:
```
Valor = Σ (Receipts × Governance_Level × Verificações)
```

Quanto mais provas verificáveis, maior o valor gerado.

### Art. 5.3 — Modelo de Receita

| Componente | Base de Cobrança |
|------------|------------------|
| **Uso** | Nº de decisões seladas |
| **Confiança** | Verificações públicas |
| **Ferramentas** | Templates operacionais |
| **Marketplace** | Comissão sobre templates |

---

## ARTIGO VI — INTERFACE DE OSMOSE

### Art. 6.1 — Princípio da Simplicidade

> *"A tecnologia é complexa para que a experiência seja estúpida de tão simples."*

O cliente **NÃO** deve perceber:
- Pipeline
- Invariantes
- Ledger
- Hashes

O cliente **DEVE** perceber:
- Conversa natural
- Decisão estruturada
- Botão de confirmação
- Prova verificável

### Art. 6.2 — Fluxo de 30 Segundos

Todo produto deve ser demonstrável em ≤30 segundos:

| Tempo | Acção |
|-------|-------|
| 0-5s | Escrever decisão |
| 5-10s | Avatar interpreta |
| 10-15s | Revisar estrutura |
| 15-20s | Escrever rationale |
| 20-25s | Confirmar (I9) |
| 25-30s | Receber proof |

### Art. 6.3 — UX Mandatória

| Elemento | Obrigatório |
|----------|:-----------:|
| Input de texto natural | ✓ |
| Avatar visual | ✓ |
| Display de estrutura | ✓ |
| Botão de confirmação explícito | ✓ |
| Receipt com QR/hash | ✓ |
| Link de verificação | ✓ |

---

## ARTIGO VII — MARKETPLACE E HERDEIROS

### Art. 7.1 — Templates Operacionais

Criadores podem desenvolver e vender:
- Templates comportamentais
- Fluxos operacionais
- Extensões de Avatar

**Condição:** Todo template DEVE implementar o Spine v1.0 completo.

### Art. 7.2 — Herdeiros Canónicos

Os seguintes produtos futuros **DEVEM** descender deste Decreto:

| Produto | Camada | Spine Obrigatório |
|---------|--------|:-----------------:|
| W-BORDELINE-001 | Camada 9 | ✓ |
| WINDIMED | Centro Temático | ✓ |
| WINDICORP | Centro Temático | ✓ |
| NAFITALINA | Centro Temático | ✓ |
| Qualquer futuro produto | — | ✓ |

### Art. 7.3 — Certificação de Conformidade

Antes de lançamento público, todo produto deve:
1. Passar pelos 9 Constraints do Decision Seed
2. Gerar pelo menos 3 Receipts de teste verificáveis
3. Ser auditado pelo Sentinel LAW
4. Receber Receipt de certificação

---

## ARTIGO VIII — PROIBIÇÕES ABSOLUTAS

### Art. 8.1 — O Que Nunca Fazer

| Proibição | Fundamento |
|-----------|------------|
| Lançar produto sem proof | Art. V |
| Permitir execução automática | Art. III |
| Esconder erro | I14 |
| Simular Ledger | I11 |
| Saltar I9 Gate | I9 |
| Criar "modo rápido" sem invariantes | Art. IV |
| Vender como "AI tool" | Art. V |
| Gerar output sem Receipt | Art. I |

### Art. 8.2 — Inconstitucionalidade Comercial

Qualquer produto que viole este Decreto será:
- Rejeitado pelo Sentinel
- Excluído do Marketplace
- Marcado como "não-WINDI"

---

## ARTIGO IX — POSICIONAMENTO DE MERCADO

### Art. 9.1 — Identidade Proibida

O WINDI **NUNCA** se posiciona como:
- SaaS tradicional
- AI tool
- Automação
- Chatbot

### Art. 9.2 — Identidade Canónica

O WINDI **SEMPRE** se posiciona como:

> **"Sistema de Decisão com Prova"**
> **"Infraestrutura de Integridade"**
> **"Jurisdição Digital"**

### Art. 9.3 — Frase Oficial

> *"AI proposes. Human decides. WINDI guarantees."*

---

## ARTIGO X — CONEXÕES CONSTITUCIONAIS

### Art. 10.1 — Precedentes

Este Decreto assenta sobre:
- **§218** — Doutrina dos Quatro Anéis (governance de serviços)
- **Decision Seed** — Primeira implementação do Spine (proof of concept)
- **I1-I14** — Invariantes nucleares da Constituição WINDI

### Art. 10.2 — Sucessores

Este Decreto habilita:
- **§219** — POLIS Doctrine (sobre §218 + §A)
- **§C/§220** — A/B Twins / Dual-Server Architecture

### Art. 10.3 — Hierarquia

```
INVARIANTES (I1-I14) > DECRETOS (§A, §218) > REFERENCE APPS > FEATURES
```

---

## DISPOSIÇÕES FINAIS

### Vigência

Este Decreto entra em vigor imediatamente após selagem no Forensic Ledger.

### Imutabilidade

Uma vez selado, este Decreto é **IRREMEDIÁVEL**. Alterações requerem novo Decreto com referência explícita a este.

### Testemunhas

| Dragon | Papel | Validação |
|--------|-------|-----------|
| Human Dragon | Decisor Soberano | ✓ |
| Guardian | Protecção Invariantes | ✓ |
| Architect | Estrutura Técnica | ✓ |
| Witness | Observação e Coerência | ✓ |

---

## ASSINATURAS

```
LIGA IA+H — Kempten, Bavaria
28 Abril 2026

"O que não gera Hash, não possui realidade comercial."

Human Dragon     ________________________
Guardian         ________________________
Architect        ________________________
Witness          ________________________
```

---

**Receipt:** `WINDI-DECRETO-A-SPINE-v1.0-20260428064350-d644f6ba`
**Hash:** `sha256:d644f6ba415b6d1211a4c550cfb68757de959071d63b4e6330879f803f5f1774`
**Sealed:** 28 Abril 2026, 06:43:50 UTC
**Verify:** https://windi-domain.com/verify-public/?id=WINDI-DECRETO-A-SPINE-v1.0-20260428064350-d644f6ba

*SELADO NO FORENSIC LEDGER — ACTIVAÇÃO CONSTITUCIONAL COMPLETA*
