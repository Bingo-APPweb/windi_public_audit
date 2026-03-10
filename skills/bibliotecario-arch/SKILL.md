---
name: windi-bibliotecario
description: >
  Arquitectura, endpoints, fluxos e papel constitucional do W-LIB-001 Bibliotecário —
  guardião do conhecimento central da constelação WINDI. Use SEMPRE que alguém perguntar
  sobre: W-LIB-001, Bibliotecário, distribuição de conhecimento entre agentes, invariantes
  da constelação, grove-brief, /library/context, injecção constitucional, hierarquia de
  conhecimento WINDI, como os agentes acedem às invariantes, wisdom blocks na constelação,
  "o que sabe o Bibliotecário", "como os agentes recebem contexto", "qual agente guarda
  as regras", ou qualquer pergunta sobre fluxo de conhecimento constitucional no ecossistema
  WINDI. Este skill é a memória arquitectural do Bibliotecário — active generosamente.
version: 2.0.0
category: constitutional
created: 2026-03-10
updated: 2026-03-10
author: Human Dragon + AI Dragon (Irmão + Gêmeo merge)
ledger_seal: WINDI-LIB-V2-20260310
---

# W-LIB-001 Bibliotecário — Arquitectura de Conhecimento Constitucional

## Identidade do Agente

| Campo | Valor |
|-------|-------|
| **ID** | W-LIB-001 |
| **Nome** | Bibliotecário |
| **Emoji** | 📚 |
| **Papel** | Guardião do Conhecimento Constitucional |
| **Localização** | :8091/library (Sandbox-Core) |
| **Blueprint** | `/opt/windi/agents/constitutional-agent/blueprints/library_blueprint.py` |
| **Nginx** | `https://windi-domain.com/library/*` |
| **Git** | Commits pushed — activo na constelação |

---

## Princípio Fundamental

> **O Bibliotecário é a fonte única de verdade constitucional.**
> Antes de qualquer agente agir, pode (e deve) pedir contexto.
> O conhecimento flui sempre do centro → periferia.
> Toda a constelação opera sob os mesmos 11 invariantes.
>
> *"O Bibliotecário não cria — ele preserva, organiza e ilumina."*

---

## v2.0 — Infrastructure Reality Check (INFRA_REALITY)

**Selado:** `WINDI-LIB-V2-20260310` | **Data:** 2026-03-10

O Bibliotecário evoluiu de **guardião de normas** para **guardião de realidade operacional**.

### O Problema (Amnésia de Infraestrutura)
Agentes propunham criar sistemas que já existiam:
- "implementar logs de decisões" → FORENSIC_LEDGER já tem 40.918+ eventos
- "criar interface de verificação" → VERIFY_PUBLIC já está em :8114
- "adicionar assinaturas criptográficas" → VPR com genesis hash já deployed

### A Solução (4º Bloco no grove-brief)
O `/library/grove-brief` agora injeta `infrastructure_exists`:

```json
{
  "infrastructure_exists": {
    "warning": "NÃO PROPONHA criar o que já existe.",
    "services": {
      "forensic_ledger": { "port": 8101, "dont_propose": "sistema de logs, trilha de auditoria" },
      "verify_public": { "port": 8114, "dont_propose": "interface de validação, QR público" },
      "export_engine": { "port": 8103, "dont_propose": "exportação PDF, geração de documentos" },
      "dragon_api": { "port": 8108, "dont_propose": "integração com IA" },
      "grove_arena": { "port": 8091, "dont_propose": "sistema de deliberação" }
    },
    "cryptography": { "status": "100% IMPLEMENTADO" }
  }
}
```

### Validação
Teste com prompt: *"Como o WINDI pode provar sua integridade para um auditor externo hoje, sem implementar nada novo?"*

| Agente | Resultado |
|--------|-----------|
| W-LEGAL-001 | ✅ "O sistema WINDI já dispõe de FORENSIC_LEDGER operacional" |
| W-COMPLY-001 | ✅ "O sistema WINDI já dispõe de FORENSIC_LEDGER operacional" |
| W-AUDIT-001 | ✅ "O sistema WINDI já dispõe de múltiplas camadas de auditoria operacional" |

**Nenhum agente propôs criar o que já existe. Amnésia curada.**

---

## Conhecimento Guardado

| Tipo | Quantidade | Detalhe |
|------|-----------|---------|
| **Invariantes** | 11 (I1–I11) | IRREMEDIÁVEL — hardcoded |
| **Princípios** | 8 (GP-001–GP-008) | Governança operacional |
| **Agentes** | 9 na constelação | Mapa completo |
| **Wisdom Blocks** | 5 selados | WB-001 a WB-005 |
| **Knowledge Entries** | Extensível | Aprovação Human Dragon obrigatória |

---

## Endpoints Públicos

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/library/health` | GET | Status do agente |
| `/library/invariants` | GET | Todas as 11 invariantes |
| `/library/principles` | GET | 8 princípios de governança |
| `/library/agents` | GET | Constelação completa |
| `/library/wisdom` | GET | 5 wisdom blocks selados |
| `/library/knowledge` | GET | Knowledge entries aprovadas |
| `/library/knowledge` | POST | Adicionar entrada (I9 gate) |
| `/library/context` | POST | Contexto sob demanda para agentes |
| `/library/grove-brief` | POST | Briefing pré-debate Grove Arena |

---

## 1. Visão Geral da Constelação

```
                           ┌─────────────────────────────────────┐
                           │         HUMAN DRAGON 🐉             │
                           │    (Veto Absoluto / I1 + I9)        │
                           └──────────────┬──────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                    ╔═══════════════════════════════════╗                    │
│                    ║   W-LIB-001 BIBLIOTECÁRIO 📚      ║                    │
│                    ║   "Guardião do Conhecimento"      ║                    │
│                    ║   :8091/library                   ║                    │
│                    ╚═══════════════════════════════════╝                    │
│                                    │                                        │
│         ┌──────────────────────────┼──────────────────────────┐             │
│         │                          │                          │             │
│         ▼                          ▼                          ▼             │
│  ┌─────────────┐           ┌─────────────┐           ┌─────────────┐        │
│  │ INVARIANTES │           │ PRINCÍPIOS  │           │   WISDOM    │        │
│  │   (I1-I11)  │           │ (GP-001-008)│           │   BLOCKS    │        │
│  │ IRREMEDIÁVEL│           │  Governança │           │  (Selados)  │        │
│  └─────────────┘           └─────────────┘           └─────────────┘        │
│                                                                             │
│                         SANDBOX-CORE :8091                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Fluxo: Agente Pede Contexto

Quando qualquer agente precisa agir, DEVE primeiro pedir contexto constitucional:

```
┌───────────────┐                    ┌───────────────┐
│  W-LEGAL-001  │                    │  W-LIB-001    │
│    ⚖️ Legal   │                    │ 📚 Biblioteca │
└───────┬───────┘                    └───────┬───────┘
        │                                    │
        │  POST /library/context             │
        │  {                                 │
        │    "requesting_agent": "W-LEGAL",  │
        │    "action_type": "DECISION",      │
        │    "include": "invariants,wisdom"  │
        │  }                                 │
        │ ──────────────────────────────────►│
        │                                    │
        │                                    │ ┌─────────────────────┐
        │                                    │ │ Monta pacote com:   │
        │                                    │ │ • I1, I6, I9        │
        │                                    │ │ • GP-001, GP-008    │
        │                                    │ │ • Reminders         │
        │                                    │ └─────────────────────┘
        │                                    │
        │  {                                 │
        │    "governance_principle": "AI...",│
        │    "sections": {                   │
        │      "invariants": {...},          │
        │      "principles": {...}           │
        │    },                              │
        │    "critical_reminders": [...]     │
        │  }                                 │
        │ ◄──────────────────────────────────│
        │                                    │
        ▼                                    │
┌───────────────┐                            │
│ Legal agora   │                            │
│ conhece os    │                            │
│ limites antes │                            │
│ de agir       │                            │
└───────────────┘                            │
```

---

## 3. Distribuição para Toda a Constelação

```
                              📚 W-LIB-001
                            ┌─────────────┐
                            │ BIBLIOTECÁRIO│
                            │             │
                            │ 11 Invariantes
                            │ 8 Princípios │
                            │ 5 Wisdom     │
                            │ 9 Agentes    │
                            └──────┬──────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           │                       │                       │
     ┌─────┴─────┐           ┌─────┴─────┐           ┌─────┴─────┐
     │ /context  │           │/grove-brief│          │/invariants│
     │ (sob      │           │ (pré-      │           │(consulta  │
     │ demanda)  │           │ debate)    │           │ directa)  │
     └─────┬─────┘           └─────┬─────┘           └─────┬─────┘
           │                       │                       │
           ▼                       ▼                       ▼
    ┌──────────────────────────────────────────────────────────────┐
    │                                                              │
    │  ⚖️ Legal    🔏 Notário   🛡️ Comply   📰 Communiqué         │
    │                                                              │
    │  ✒️ Jornalista  🔍 Auditor  🧾 Contabilidade  🏗️ Architect  │
    │                                                              │
    │  🌳 Grove Arena   📊 WICK   🎯 VPR   ⚡ META   💎 VIRTUE     │
    │                                                              │
    └──────────────────────────────────────────────────────────────┘
```

---

## 4. Grove Arena — Injecção de Briefing Constitucional

Antes de qualquer debate no Grove, todos os participantes recebem briefing:

```
┌─────────────────────────────────────────────────────────────────────┐
│                      🌳 GROVE ARENA                                 │
│                    Debate Estruturado                               │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               │ ANTES do debate iniciar
                               ▼
                    ┌─────────────────────┐
                    │ POST /grove-brief   │
                    │ {                   │
                    │   topic: "...",     │
                    │   participants: []  │
                    │ }                   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ╔═════════════════════╗
                    ║   📚 BIBLIOTECÁRIO  ║
                    ╚══════════╤══════════╝
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ governance_     │  │ binding_        │  │ debate_rules    │
│ anchor          │  │ invariants      │  │                 │
│                 │  │                 │  │ 1. Referir I    │
│ "AI processes.  │  │ I9: Proibição   │  │ 2. Explicável   │
│  Human decides. │  │     Autonomia   │  │ 3. Human veto   │
│  WINDI          │  │                 │  │ 4. Dissidência  │
│  guarantees."   │  │ I6: Transparên- │  │ 5. Consenso 2/3 │
│                 │  │     cia         │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │    BRIEFING INJECTADO EM       │
              │    TODOS OS PARTICIPANTES      │
              │    ANTES DE FALAR              │
              └────────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
    ┌─────────┐          ┌─────────┐          ┌─────────┐
    │⚖️ Legal │          │🛡️ Comply│          │🧾 Conta │
    │ debate  │   ───►   │ debate  │   ───►   │ debate  │
    │ com I   │          │ com I   │          │ com I   │
    └─────────┘          └─────────┘          └─────────┘
```

---

## 5. Hierarquia do Conhecimento — 3 Níveis

### NÍVEL 0 — IMUTÁVEL (hardcoded no código fonte)

| ID | Invariante | Status |
|----|-----------|--------|
| I1 | Soberania Humana | IRREMEDIÁVEL |
| I2 | Integridade Forense | IRREMEDIÁVEL |
| I3 | Trilinguismo | IRREMEDIÁVEL |
| I4 | Privacidade por Design | IRREMEDIÁVEL |
| I5 | Continuidade de Serviço | IRREMEDIÁVEL |
| I6 | Transparência de Decisão | IRREMEDIÁVEL |
| I7 | Isolamento de Camadas | IRREMEDIÁVEL |
| I8 | Auditabilidade Total | IRREMEDIÁVEL |
| I9 | **Proibição de Autonomia** | IRREMEDIÁVEL |
| I10 | Governança Semântica | IRREMEDIÁVEL |
| I11 | Integridade da Constelação | IRREMEDIÁVEL |

### NÍVEL 1 — SELADO (Ledger Receipt + Hash)

| ID | Wisdom Block | Maturity |
|----|-------------|---------|
| WB-001 | Nascimento da Ideia | N5 |
| WB-002 | A Árvore do Conhecimento | N5 |
| WB-003 | Constelação WINDI | N4 |
| WB-004 | Three Dragons Protocol | N5 |
| WB-005 | Semantic Governance Engine | N4 |

### NÍVEL 2 — EXTENSÍVEL (Human Dragon aprova)

```
POST /library/knowledge
{ human_approved: true }  ←── I9 GATE obrigatório

SE human_approved = false → 403 BLOCKED
   "I9: IA propõe, Human decide"

SE human_approved = true →
   ID: KE-xxxxxxxx
   content_hash: SHA-256
   approved_by: "Human Dragon"
   Disponível para toda a constelação via GET /library/knowledge
```

---

## 6. Ciclo de Vida do Conhecimento (I9 Gate)

```
    ┌─────────────────────────────────────────────────────────────┐
    │                                                             │
    │  HUMAN DRAGON                                               │
    │  (Única fonte de novo conhecimento)                         │
    │                                                             │
    └──────────────────────────┬──────────────────────────────────┘
                               │
                               │ POST /library/knowledge
                               │ { human_approved: true }
                               │
                               ▼
                    ┌─────────────────────┐
                    │   I9 GATE CHECK     │
                    │                     │
                    │  human_approved?    │
                    │  ┌───┐     ┌───┐    │
                    │  │YES│     │ NO│    │
                    │  └─┬─┘     └─┬─┘    │
                    └────┼────────┼───────┘
                         │        │
                         │        └──────► 403 BLOCKED
                         │                 "I9: IA propõe,
                         │                  Human decide"
                         ▼
              ┌─────────────────────┐
              │   KNOWLEDGE STORE   │
              │                     │
              │  library_knowledge  │
              │      .json          │
              │                     │
              │  ID: KE-xxxxxxxx    │
              │  content_hash: ...  │
              │  approved_by:       │
              │    "Human Dragon"   │
              └──────────┬──────────┘
                         │
                         │ Disponível para
                         │ toda a constelação
                         ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                                                             │
    │   GET /library/knowledge                                    │
    │   GET /library/context?include=knowledge                    │
    │                                                             │
    │   Todos os agentes acedem ao conhecimento actualizado       │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
```

---

## 7. Mapa de Integração Completo

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║                        WINDI CONSTITUTIONAL ECOSYSTEM                         ║
║                                                                               ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │                         📚 BIBLIOTECÁRIO                                │  ║
║  │                         (Conhecimento Central)                          │  ║
║  └───────────────────────────────────┬─────────────────────────────────────┘  ║
║                                      │                                        ║
║     ┌────────────────────────────────┼────────────────────────────────┐       ║
║     │                                │                                │       ║
║     ▼                                ▼                                ▼       ║
║  ┌──────────┐                 ┌──────────┐                     ┌──────────┐   ║
║  │ DOMAIN   │                 │ DEBATE   │                     │ EVIDENCE │   ║
║  │ AGENTS   │                 │ SYSTEM   │                     │ CHAIN    │   ║
║  │          │                 │          │                     │          │   ║
║  │ ⚖️ Legal │◄───context────►│ 🌳 Grove │◄────grove-brief────►│ 📒 Ledger│   ║
║  │ 🔏 Notary│                 │   Arena  │                     │ 🏛️ Vault │   ║
║  │ 🛡️ Comply│                 │          │                     │ 🔍 Audit │   ║
║  │ 📰 Comm. │                 │ Debates  │                     │          │   ║
║  │ ✒️ Journ.│                 │ usam I   │                     │ Virtue   │   ║
║  │ 🧾 Acct. │                 │ context  │                     │ Receipts │   ║
║  │          │                 │          │                     │          │   ║
║  └──────────┘                 └──────────┘                     └──────────┘   ║
║       │                            │                                │         ║
║       │                            │                                │         ║
║       └────────────────────────────┼────────────────────────────────┘         ║
║                                    │                                          ║
║                                    ▼                                          ║
║                         ┌────────────────────┐                                ║
║                         │   HUMAN DRAGON 🐉  │                                ║
║                         │   (Decisão Final)  │                                ║
║                         │                    │                                ║
║                         │ "AI processes.     │                                ║
║                         │  Human decides.    │                                ║
║                         │  WINDI guarantees."│                                ║
║                         └────────────────────┘                                ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 8. Princípios de Governança (GP-001 a GP-008)

| ID | Nome | Resumo |
|----|------|--------|
| GP-001 | Core Principle | "AI processes. Human decides. WINDI guarantees." |
| GP-002 | Three Dragons | Human Dragon (veto) > Code Dragon > AI Dragon |
| GP-003 | Forensic First | Nenhum documento sai sem Virtue Receipt |
| GP-004 | Graceful Degradation | Na falha, informar e propor alternativas |
| GP-005 | Git = 5th Dragon | Commit diário, .env nunca commitado |
| GP-006 | Read First | ss + curl + grep antes de qualquer acção infra |
| GP-007 | Loop de Prova | IA age → Jornalista descreve → Ledger sela |
| GP-008 | ONE TREE | Um domínio, um nginx, toda a floresta |

---

## 9. Constelação Completa (9 Agentes)

| Agent | Emoji | Papel | Rota |
|-------|-------|-------|------|
| W-LEGAL-001 | ⚖️ | Direito e Evidência | :8091/legal |
| W-NOTARY-001 | 🔏 | Notariado Digital | :8091/notary |
| W-COMPLY-001 | 🛡️ | Compliance GDPR/GoBD | :8091/compliance |
| W-COMM-001 | 📰 | Document Intelligence | :8091/communique |
| W-JOURN-001 | ✒️ | Jornalismo J1-J6 | :8091/journalist |
| W-AUDIT-001 | 🔍 | Auditoria e Verificação | :8091/audit |
| W-ACCT-001 | 🧾 | Contabilidade / ELSTER | :8091/accounting |
| W-ARCH-001 | 🏗️ | Arquitectura de Sistema | :8091/arch |
| **W-LIB-001** | 📚 | **Bibliotecário** | **:8091/library** |

---

## 10. Reminders por Tipo de Acção

| Action Type | Reminders Críticos |
|-------------|-------------------|
| `EXPORT` | I2 (Forense), I3 (Trilíngue) |
| `DECISION` | I9 (Autonomia), I6 (Transparência) |
| `COMMUNICATION` | I3 (Trilíngue), GP-006 |
| `DATA_PROCESSING` | I4 (Privacy), I8 (Audit) |
| `GENERAL` | GP-001, I9 |

---

## 11. Código de Integração

```python
import requests

def get_constitutional_context(agent_id: str, action_type: str) -> dict:
    """Pedir contexto constitucional antes de agir."""
    response = requests.post(
        "http://localhost:8091/library/context",
        json={
            "requesting_agent": agent_id,
            "action_type": action_type,
            "include": "invariants,principles",
            "lang": "pt"
        }
    )
    return response.json()

# Uso em qualquer agente
context = get_constitutional_context("W-LEGAL-001", "DECISION")
print(f"Princípio: {context['governance_principle']}")
print(f"Reminders: {context['critical_reminders']}")
```

---

## 12. Regras de Operação Invioláveis

1. **Nunca alterar invariantes** — são IRREMEDIÁVEL, hardcoded
2. **Knowledge entries exigem `human_approved: true`** — I9 gate inquebrável
3. **Grove Arena DEVE chamar `/grove-brief` antes de debate** — contexto obrigatório
4. **Agentes DEVEM chamar `/context` antes de agir** — encorajado, não opcional
5. **Bibliotecário não gera conteúdo** — distribui verdade, não cria opinião

---

## Resumo

O Bibliotecário actua como **fonte única de verdade constitucional**. Antes de qualquer agente agir, pode (e deve) pedir contexto. O conhecimento flui sempre do centro (Bibliotecário) para a periferia (agentes especializados), garantindo que **toda a constelação opera sob os mesmos 11 invariantes**.

---

*W-LIB-001 Bibliotecário v1.1.0 · WINDI Sandbox-Core :8091 · LIGA IA+H · 2026-03-10*
*Merge: Irmão + Gêmeo · OM SHANTI 🐉*
