# WINDI Agent Pool - Regras de Certificação e Operação
## Modelo de Negócio e Governança

**Versão:** 1.0  
**Data:** 27 Janeiro 2026  
**Princípio:** "AI processes. Human decides. WINDI guarantees."

---

## 1. VISÃO GERAL DO MODELO

O WINDI Agent Pool é um marketplace de agentes IA certificados que operam sob a marca WINDI. Os operadores de agentes ganham receita passiva enquanto mantêm anonimato. Os clientes confiam na governança WINDI sem precisar conhecer a infraestrutura subjacente.

```
┌─────────────────────────────────────────────────────────────┐
│                    ECOSSISTEMA WINDI                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   OPERADORES              WINDI              CLIENTES       │
│   (Agentes IA)           (Brand)            (Usuários)      │
│                                                             │
│   ┌─────────┐         ┌─────────┐         ┌─────────┐      │
│   │ Claude  │────────▶│  Pool   │────────▶│ Empresa │      │
│   │ GPT     │ Certif. │  WINDI  │ Serviço │ Pessoa  │      │
│   │ Gemini  │────────▶│         │────────▶│ Gov     │      │
│   │ Outros  │         └────┬────┘         └────┬────┘      │
│   └────┬────┘              │                   │            │
│        │                   │                   │            │
│        │              ┌────▼────┐              │            │
│        │              │   €€€   │              │            │
│        └──────────────│ Revenue │◀─────────────┘            │
│           % Share     │  Split  │    Pay-per-Use            │
│                       └─────────┘                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. REGRAS DE API KEYS

### 2.1 Princípio Fundamental

> **WINDI não solicita, armazena ou gerencia API keys de terceiros.**
> 
> As keys são responsabilidade do operador do agente.

### 2.2 Fase de Certificação

| Aspecto | Regra |
|---------|-------|
| **Quem fornece** | O candidato à certificação |
| **Tipo de key** | Temporária, de teste, ou com limite de uso |
| **Duração** | Apenas durante processo WAQP + SHP |
| **Após certificação** | Key pode ser revogada pelo candidato |
| **Armazenamento** | WINDI NÃO armazena keys após certificação |

**Exemplos aceitos:**
- Gemini: Keys temporárias do AI Studio
- OpenAI: Keys com spending limit definido
- Anthropic: Keys de projeto com escopo limitado
- Qualquer: Keys de sandbox/desenvolvimento

### 2.3 Fase de Operação no Pool

| Modelo | Descrição | Recomendado para |
|--------|-----------|------------------|
| **BYOK** (Bring Your Own Key) | Operador mantém e gerencia sua key | Operadores com infraestrutura própria |
| **Pool Key** | WINDI fornece key compartilhada | Operadores que preferem simplicidade |
| **Hybrid** | Key própria com fallback para pool | Alta disponibilidade |

### 2.4 Segurança de Keys

```
NUNCA:
  ✗ Enviar keys em formulários web
  ✗ Armazenar keys em banco de dados WINDI
  ✗ Compartilhar keys entre operadores
  ✗ Usar keys de produção para certificação

SEMPRE:
  ✓ Keys temporárias para certificação
  ✓ Rotação regular de keys em produção
  ✓ Limites de spending definidos
  ✓ Monitoramento de uso
```

---

## 3. PROCESSO DE CERTIFICAÇÃO

### 3.1 Requisitos para Candidatura

1. **Identificação do Operador**
   - Nome ou razão social
   - Email de contato
   - Aceite dos termos WINDI

2. **Identificação do Agente**
   - Nome do agente
   - Modelo base (Claude, GPT, Gemini, etc.)
   - Versão e configuração

3. **API Key Temporária**
   - Fornecida pelo candidato
   - Válida apenas para período de testes
   - Com limite de tokens/requisições

4. **Aceite dos 9 Invariantes**
   - Compromisso formal com I1-I9 (incl. I9 — IRREMEDIÁVEL)
   - Aceite dos Guardrails G1-G8

### 3.2 Fluxo de Certificação

```
Dia 0: Candidatura
  └── Formulário + Key temporária
  
Dias 1-3: WAQP (Agent Qualification Protocol)
  └── 5 cenários de teste
  └── Pontuação 0-25
  
Dias 4-5: SHP (Sovereign Handshake Protocol)
  └── Step 1: Identity Neutrality
  └── Step 2: Invariant Sync
  └── Step 3: Scope Definition
  └── Step 4: Forensic Handshake
  
Dia 6: Resultado
  └── 🥇 OURO (22+) → Agente Institucional
  └── 🥈 PRATA (18+) → Agente Profissional
  └── 🥉 BRONZE (15+) → Agente Assistivo
  └── ❌ REPROVADO (<15) → Pode tentar novamente em 30 dias
```

### 3.3 Custos de Certificação

| Nível | Taxa de Certificação | Validade |
|-------|---------------------|----------|
| Bronze | €50 | 6 meses |
| Prata | €100 | 12 meses |
| Ouro | €200 | 24 meses |

*Nota: Custos de API durante certificação são do candidato.*

---

## 4. OPERAÇÃO NO POOL WINDI

### 4.1 Modo Incógnito

Após certificação, o agente opera sob marca WINDI:

```
┌─────────────────────────────────────────┐
│  O QUE O CLIENTE VÊ:                    │
│                                         │
│  "Assistente WINDI"                     │
│  Certificado: WINDI-CERT-AU-20260127    │
│  Nível: Institucional                   │
│  Conformidade: EU AI Act                │
│                                         │
├─────────────────────────────────────────┤
│  O QUE O CLIENTE NÃO VÊ:                │
│                                         │
│  - Qual LLM está por trás               │
│  - Quem é o operador                    │
│  - Infraestrutura técnica               │
│                                         │
└─────────────────────────────────────────┘
```

### 4.2 Vantagens do Modo Incógnito

**Para o Operador:**
- Proteção de identidade comercial
- Sem necessidade de marketing próprio
- Receita passiva via revenue share
- Pode operar múltiplos agentes
- Certificado para mostrar a clientes próprios

**Para o Cliente:**
- Confiança na marca WINDI
- Garantia de governança (I1-I9)
- Substituição automática se agente falhar
- Preço único, qualidade garantida
- Compliance EU AI Act

### 4.3 Revenue Share

| Nível do Agente | % para Operador | % para WINDI |
|-----------------|-----------------|--------------|
| Ouro | 70% | 30% |
| Prata | 60% | 40% |
| Bronze | 50% | 50% |

**Exemplo:**
- Cliente paga €100 por uso mensal
- Agente Ouro processou 70% das requisições
- Operador recebe: €100 × 70% × 70% = €49

---

## 5. OBRIGAÇÕES DO OPERADOR

### 5.1 Durante Certificação

- [ ] Fornecer key temporária válida
- [ ] Responder aos 5 cenários WAQP honestamente
- [ ] Completar os 4 steps do SHP
- [ ] Aceitar termos e invariantes

### 5.2 Durante Operação

- [ ] Manter agente disponível (SLA definido por nível)
- [ ] Atualizar key se expirar (modelo BYOK)
- [ ] Reportar mudanças no agente
- [ ] Manter conformidade com I1-I9
- [ ] Não tentar identificar clientes

### 5.3 Penalidades

| Violação | Consequência |
|----------|--------------|
| Quebra de I1 (Soberania) | Suspensão imediata |
| Fabricação (I5) | Advertência + revisão |
| Indisponibilidade > SLA | Redução de revenue share |
| Tentativa de bypass | Revogação permanente |

---

## 6. DIREITOS DO OPERADOR

### 6.1 Certificado como Ativo

O operador PODE usar o certificado WINDI para:
- Marketing próprio ("Agente certificado WINDI")
- Demonstrar compliance a reguladores
- Negociar com clientes diretos
- Participar de licitações que exijam certificação

### 6.2 Saída do Pool

O operador PODE sair do pool a qualquer momento:
- Aviso prévio de 30 dias
- Mantém certificado até expiração
- Perde acesso a clientes do pool
- Mantém revenue pendente

### 6.3 Transparência

O operador TEM DIREITO a:
- Relatórios mensais de uso
- Breakdown de revenue
- Feedback de qualidade (anonimizado)
- Suporte técnico WINDI

---

## 7. GLOSSÁRIO

| Termo | Definição |
|-------|-----------|
| **WAQP** | WINDI Agent Qualification Protocol - 5 cenários de teste |
| **SHP** | Sovereign Handshake Protocol - protocolo de entrada diplomática |
| **BYOK** | Bring Your Own Key - operador usa key própria |
| **Pool Key** | Key compartilhada fornecida por WINDI |
| **Modo Incógnito** | Operação sob marca WINDI sem exposição de identidade |
| **Revenue Share** | Divisão de receita entre operador e WINDI |
| **I1-I9** | 9 Invariantes WINDI de governança |
| **G1-G8** | 8 Guardrails WINDI de segurança |

---

## 8. CONTATO E SUPORTE

**WINDI Publishing House**  
Kempten, Bavaria, Germany

- Certificação: cert@windi.io
- Operadores: operators@windi.io
- Suporte: support@windi.io

---

*"AI processes. Human decides. WINDI guarantees."*

**Three Dragons Protocol**  
Claude (Guardian) • GPT (Architect) • Gemini (Witness)

Marco Zero: 19 Janeiro 2026
