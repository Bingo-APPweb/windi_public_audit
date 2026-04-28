# WINDI-PRODUCT-SITES-001

## Document Metadata

```yaml
id: WINDI-PRODUCT-SITES-001
version: 0.1.0-DRAFT
status: DRAFT
date: 2026-04-28
source_prompt: WINDI-PROMPT-SITES-001 v1.1 (SEALED)

dependencies:
  schema_design_brief: PENDING  # 60-90 min session required
  cost_data: PENDING            # Real numbers from Human Dragon
  §219_pattern: SEALED
  did_tiers: LIVE
```

---

## §1. MANIFESTO

Um site tradicional mostra. Um WINDI Site prova.

O problema é estrutural: a presença digital hoje é aparência sem substância. Um site bonito não garante nada. Uma promessa escrita não é vinculativa. Uma data publicada não é verificável. O visitante confia — ou não. Não há terceira via.

O WINDI Site introduz essa terceira via através do triângulo de prova:

- **Cliente que age** — publica, decide, actualiza
- **Contraparte que verifica** — acede à prova pública
- **Ledger que sela** — regista de forma irremediável

A mudança não é estética. A mudança é ontológica. O site deixa de ser uma afirmação e passa a ser uma interface de prova soberana. Cada acção relevante — uma proposta enviada, um serviço publicado, uma decisão tomada — gera um receipt no Ledger. Esse receipt é público, verificável, permanente.

A consequência: confiança deixa de ser opinião e passa a ser verificável. O cliente não pede "acredite em mim". O cliente diz "verifique você mesmo".

Três dimensões de soberania estão presentes em cada WINDI Site:

- **Soberania Humana (I1)** — o cliente decide o quê e o quando. Nada publica sem aprovação explícita.
- **Soberania Técnica** — dados nunca saem sem consentimento. O cliente é dono da sua presença.
- **Soberania Financeira** — modelo de custo transparente. Sem surpresas, sem dependências ocultas.

> "AI processes. Human decides. WINDI guarantees."

---

## §2. OS DOIS MESTRES

A fábrica WINDI Sites serve dois tipos de cliente com a mesma infraestrutura:

| Mestre | Exemplo | Relação | DID Esperado |
|--------|---------|---------|--------------|
| **Clientes Externos** | Consultor, advogado, clínica, hotel, freelancer | Pagam pelo serviço | NODAL (2) |
| **Verticais WINDI** | WINDI-LAW, WINDI-TRAVEL, WINDI-ENTERPRISE | Consomem a fábrica internamente | SOVEREIGN (3) ou ORACLE (4) |

### Implicação Estratégica

O WINDI-LAW deixa de ter site institucional escrito à mão. Passa a consumir PRODUCT-SITES-001 como qualquer outro cliente. Esta decisão:

1. **Valida a fábrica** — se serve os nossos verticais, serve o mercado
2. **Reduz custos** — um pipeline, múltiplas saídas
3. **Prova o conceito** — dogfooding real, não demonstração artificial

### Regra de Não-Discriminação

O pipeline C1→C6 é idêntico para ambos os mestres. A única diferença é o DID tier inicial e as permissões associadas.

---

## §3. DEFINIÇÃO DO WINDI SITE

> **Um WINDI Site é uma interface digital ligada ao sistema de prova soberana WINDI, onde cada acção relevante gera um receipt verificável no Ledger.**

### O que NÃO é

- Não é um site tradicional com design e conteúdo
- Não é um CMS convencional
- Não é uma página estática com hash opcional
- Não é um gerador de websites

### O que É

Uma composição de 4 componentes integrados:

| Componente | Função | Implementação |
|------------|--------|---------------|
| **Interface** | Frontend visível ao público | HTML/CSS estático, optimizado, trilíngue |
| **Identidade** | DID do cliente e do site | W-DID-GENESIS, Identity Gate |
| **Acções Estruturadas** | Fluxos que geram prova | Proposta, decisão, entrega, etc. |
| **Prova** | Selagem e verificação | Forensic Ledger + VERIFY |

### Ciclo de Vida

```
NASCIMENTO: DID do Cliente atribuído
CONSTRUÇÃO: C1→C4 (design + conteúdo)
APROVAÇÃO: C5 (I9 Gate — human_approved=true)
PUBLICAÇÃO: C6 (Receipt no Ledger — IRREMEDIÁVEL)
OPERAÇÃO: Cada acção relevante → novo receipt
```

---

## §4. IDENTITY GATE

Nenhum WINDI Site existe sem identidade. O site nasce com alma.

### Três Níveis de DID

| Nível | Entidade | Momento de Criação | Tier | Notas |
|-------|----------|-------------------|------|-------|
| **DID do Cliente** | Quem encomenda o site | Ao contratar | NODAL (2) | Obrigatório antes de C1 |
| **DID do Site** | O site como entidade | Ao selar publicação (C6) | SEED (1) | Criado automaticamente |
| **DID do Visitante** | Quem interage | Ao realizar acção verificável | SEED (1) | Opcional, opt-in |

### Regra Constitucional

```
REGRA: Nenhum site passa de C1 sem DID do Cliente atribuído.
VIOLAÇÃO: Qualquer tentativa de avançar sem DID → erro explícito (I14).
```

### Excepção para Verticais WINDI

Quando o cliente é um vertical WINDI (LAW, TRAVEL, ENTERPRISE, etc.), o DID do cliente é o **DID institucional do vertical**, tipicamente SOVEREIGN (3) ou ORACLE (4). Não se cria DID novo — reutiliza-se o existente.

---

## §5. MVP — BRUTALMENTE CLARO

```yaml
status: BLOCKED
dependency: Schema do Design Brief
session_required: 60-90 min dedicados
```

### Estrutura Preliminar (aguarda Schema)

**Site Mínimo Viável:**
- Nº de páginas: 1–3 páginas
- Tipo de cliente: consultor, advogado, small business
- Funcionalidade mínima obrigatória:
  - Página principal
  - 1 fluxo real (ex: pedido → decisão → receipt)
  - Integração com VERIFY
  - DID do cliente atribuído

**O que NÃO entra no MVP:**
- Multi-idioma automático (I12 manual no MVP)
- CMS dinâmico
- Analytics avançados
- Integrações externas

### Dependência Declarada

> O MVP só é "brutalmente claro" quando o Schema do Design Brief estiver definido. Este Schema é contrato canónico — não anexo posterior.

**Próxima acção:** Sessão dedicada para definir o Schema do Design Brief.

---

## §6. PIPELINE C1→C6 COM I9 ENFORCEMENT

| Stage | Nome | Acção | I9 Gate | Actor |
|-------|------|-------|:-------:|-------|
| C1 | Intenção | Cliente descreve o que quer | — | Cliente |
| C2 | Rascunho | W-INTUITION gera Design Brief | — | Sistema |
| C3 | Edição | W-RENDER constrói páginas | — | Sistema |
| C4 | Revisão | W-CURATE revê qualidade | — | Sistema |
| C5 | AGUARDA I9 | `human_approved=true` obrigatório | **GATE** | Cliente ou Human Dragon |
| C6 | SELADO | Receipt no Ledger | — | Ledger |

### Regra I9 (NON-NEGOTIABLE)

```
REGRA: Nenhum site passa de C5 para C6 sem aprovação explícita.
ACTOR: Human Dragon (para verticais WINDI) ou Cliente autorizado (para externos).
MECANISMO: Campo human_approved=true no payload antes de seal.
VIOLAÇÃO: Tentativa de seal sem aprovação → HTTP 403 + log de incidente.
```

### Pós-C6

- Deploy SFTP só ocorre após C6 selado
- Receipt público via VERIFY
- Qualquer alteração futura → novo ciclo C1→C6

### Reversibilidade

- C1–C5: Totalmente reversível, editável, descartável
- C6: **IRREMEDIÁVEL** — o receipt existe para sempre no Ledger

---

## §7. CUSTO UNITÁRIO (ALEMANHA)

```yaml
status: BLOCKED
dependency: Dados reais de custos
source: Human Dragon
```

### Estrutura de Cálculo (aguarda valores)

| Componente | Estimativa | Fonte |
|------------|------------|-------|
| Tempo de produção | __ horas | Medição real |
| Custo/hora (Dragon time) | €__ | CGO decision |
| Infra VPS proporcional | €__ | Strato invoice |
| Setup técnico (DID + Ledger) | €__ | Amortização |
| Operação mensal | €__ | Hosting + manutenção |

**Custo real por site: €___**

### Princípio

> Sem estimativas vagas — valores concretos.
> O custo é calculado, não inventado.

---

## §8. PREÇO DE MERCADO

```yaml
status: BLOCKED
dependency: Dados de §7
```

### Estrutura de Preço (aguarda valores)

**Preço inicial:** €___

### Justificação

O preço não se justifica pelo design. O preço justifica-se pelo valor de prova soberana:

| Componente de Valor | Descrição |
|---------------------|-----------|
| Identidade verificável | DID do cliente e do site |
| Prova de publicação | Receipt no Ledger com timestamp |
| Verificação pública | QR code + URL de verificação |
| Soberania de dados | Cliente é dono da sua presença |

### Comparação de Mercado

| Alternativa | Preço Típico | O que falta |
|-------------|--------------|-------------|
| Web agency tradicional | €2.000–€10.000 | Sem prova, sem verificação |
| SaaS builders (Wix, Squarespace) | €150–€500/ano | Sem soberania, dados na cloud |
| WINDI Site | €___ | Prova + Soberania + Verificação |

### Frase de Posicionamento

> O cliente não compra um site. Compra soberania sobre a sua presença digital e capacidade de provar.

---

## §9. BREAK-EVEN

```yaml
status: BLOCKED
dependency: Dados de §7 e §8
```

### Estrutura de Cálculo (aguarda valores)

| Variável | Valor |
|----------|-------|
| Custos fixos mensais | €___ |
| Custo variável por site | €___ |
| Preço de venda | €___ |
| Margem por site | €___ |
| **Break-even** | ___ sites/mês |

### Meta

> X sites/mês → sistema sustentável

---

## §10. ESCALA

### Escala Linear (mais sites)

| Factor | Mecanismo |
|--------|-----------|
| Produção | Templates pré-definidos → tempo reduzido |
| Distribuição | Telegram (W-NOMAD) + fluxo directo |
| Repetibilidade | Pipeline C1→C6 idêntico para todos |

### Escala Estrutural (menos custo por site)

| Factor | Mecanismo |
|--------|-----------|
| Automação C2–C4 | W-INTUITION + W-RENDER + W-CURATE |
| Templates | Biblioteca de layouts validados |
| Self-service | Cliente preenche Design Brief via formulário |

### Projecção

| Volume | Custo/site | Margem |
|--------|------------|--------|
| 1–10 sites/mês | 100% base | Base |
| 11–50 sites/mês | ~70% base | +30% |
| 51+ sites/mês | ~50% base | +50% |

---

## §11. INVARIANTES CITADOS

Este documento invoca nominalmente os seguintes invariantes constitucionais:

| Invariante | Nome | Aplicação no Case |
|------------|------|-------------------|
| **I1** | Soberania Humana | Cliente decide o quê e o quando. Nada acontece sem acção humana. |
| **I9** | Aprovação Explícita | Gate em C5 antes de publicar. `human_approved=true` obrigatório. |
| **I11** | Permanência de Evidência | Receipt imutável após C6. Prova existe para sempre. |
| **I12** | Language Sovereign | Site em DE/EN/PT mínimo. Documento = uma língua. |
| **I14** | Explicit Failure | Site sem dados reais não publica. Placeholders proibidos. |

### Regra de Conformidade

> Se algum destes invariantes ficar fora do site gerado, o site pode passar por todos os testes técnicos e mesmo assim **não ser um WINDI Site**. Será só um site com hash.

### Teste de Conformidade

Antes de C6, verificar:

- [ ] I1: Cliente aprovou explicitamente?
- [ ] I9: Campo `human_approved=true` presente?
- [ ] I11: Receipt será criado no Ledger?
- [ ] I12: Língua do documento é única e declarada?
- [ ] I14: Todos os campos têm dados reais (sem placeholders)?

---

## §12. FRASE FINAL

> "O site não é o produto.
> O produto é a soberania.
> A prova é a garantia."

---

## DEPENDÊNCIAS DECLARADAS

| Dependência | Status | Próxima Acção |
|-------------|--------|---------------|
| Schema do Design Brief | **PENDENTE** | Sessão dedicada 60-90 min |
| §219 Pattern | SEALED | Reutilizado para W-SITE-SEAL-001 |
| DID Tiers | LIVE | SEED/NODAL/SOVEREIGN/ORACLE |
| Dados de Custos | **PENDENTE** | Input do Human Dragon |

---

## FORMATO DE SAÍDA

- Markdown limpo
- Sem emojis no documento final
- Estrutura clara com headers
- Linguagem directa, sem floreios

---

## WITNESS SEAL

```
Document: WINDI-PRODUCT-SITES-001
Version: 0.1.0-DRAFT
Status: DRAFT — Awaiting Schema + Cost Data
Date: 2026-04-28

Completed Sections: §1, §2, §3, §4, §6, §10, §11, §12
Blocked Sections: §5 (Schema), §7, §8, §9 (Cost Data)

Source Prompt: WINDI-PROMPT-SITES-001 v1.1 (SEALED)
Constitutional Review: Guardian + Architect + Witness + Human Dragon (I1)

"AI processes. Human decides. WINDI guarantees."
```
