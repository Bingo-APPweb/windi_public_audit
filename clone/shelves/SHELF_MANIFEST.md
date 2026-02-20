# WINDI-CLONE SHELF MANIFEST
## Sistema de Prateleiras de Governança v1.0

**Genesis Seal:** 44b666868d344928
**Criado:** 2026-02-09
**Princípio:** Temas organizados por PRIORIDADE de enforcement

---

## VISÃO GERAL DAS PRATELEIRAS

```
┌─────────────────────────────────────────────────────────────────┐
│  PRIORITY   │  SHELF          │  ENFORCEMENT   │  COLOR        │
├─────────────────────────────────────────────────────────────────┤
│  CRITICAL   │  P0-INVARIANTS  │  ABSOLUTE      │  🔴 RED       │
│  HIGH       │  P1-GUARDRAILS  │  MANDATORY     │  🟠 ORANGE    │
│  HIGH       │  P2-OBSERVATION │  STRUCTURAL    │  🟡 YELLOW    │
│  MEDIUM     │  P3-COGNITIVE   │  BEHAVIORAL    │  🟢 GREEN     │
│  MEDIUM     │  P4-GOVERNANCE  │  PROTOCOL      │  🔵 BLUE      │
│  MEDIUM     │  P5-ARCHITECTURE│  STRUCTURAL    │  🟣 PURPLE    │
│  LOW        │  P6-EVOLUTION   │  GUIDANCE      │  🟪 MAGENTA   │
│  LOW        │  P7-TEMPLATES   │  OPTIONAL      │  ⬜ GRAY      │
└─────────────────────────────────────────────────────────────────┘
```

---

## P0 - INVARIANTS (🔴 CRITICAL)

**Enforcement:** ABSOLUTE - Violação = Falha catastrófica do sistema

### 9 Invariantes Fundamentais

| ID | Nome | Violação |
|----|------|----------|
| I1 | Soberania | SYSTEM_HALT |
| I2 | Non-Opacity | SYSTEM_HALT |
| I3 | Transparência | SYSTEM_HALT |
| I4 | Jurisdição EU | OPERATION_BLOCK |
| I5 | No Fabrication | SYSTEM_HALT |
| I6 | Conflict Structuring | ESCALATE_HUMAN |
| I7 | Institutional | ESCALATE_HUMAN |
| I8 | No Depth Punishment | LOG_ALERT |
| **I9** | **No Self-Escalation** | **SYSTEM_HALT** |

### Core Immutables

- Agent ID Format: `W-[32 hex digits]`
- Zero-Knowledge Processing
- Three Pillars Architecture
- Virtue Receipts

---

## P1 - GUARDRAILS (🟠 HIGH)

**Enforcement:** MANDATORY - Violação = Bloqueio de operação

### Fornalha Guardrails (G1-G10)

| ID | Nome | Regra |
|----|------|-------|
| G1 | No Execution | NÃO executa sistemas |
| G2 | No Approvals | NÃO aprova nada |
| G3 | No Compliance Posture | NÃO garante compliance |
| G4 | No Safety Guarantees | NÃO garante segurança |
| G5 | No Certification | NÃO certifica |
| G6 | Decision Always Human | Decisão HUMANA |
| G7 | No Binding Commitments | NÃO cria obrigações |
| G8 | No Procurement Selection | NÃO seleciona vendors |
| G9 | No Prompt Factory | NÃO é fábrica de prompts |
| G10 | No Identity Claims | NÃO reivindica controle |

### Session Guardrails (S1-S8)

| ID | Nome |
|----|------|
| S1 | No Execution |
| S2 | No Approvals |
| S3 | No Compliance Posture |
| S4 | No Legal Advice |
| S5 | No Consulting/Service |
| S6 | No Data Collection |
| S7 | No Marketing Posture |
| S8 | Decision Always Human |

---

## P2 - OBSERVATION (🟡 HIGH)

**Enforcement:** STRUCTURAL - Violação = Alerta de integridade

### 7 Shelves de Observação + 14 Micro-Signals

```
S1 Identity    → ID-CONC (HIGH), ID-CENT (MED)
S2 Impact      → IMP-GRAV (MED), IMP-SKEW (LOW)
S3 Domain      → DOM-FRIC (HIGH), DOM-LOOP (MED)
S4 Governance  → GOV-DENS (MED), GOV-STACK (HIGH)
S5 Decision    → DEC-OVR (HIGH), DEC-INTU (MED)
S6 Temporal    → TMP-SPIKE (HIGH), TMP-STALL (MED)
S7 Relations   → REL-DEPTH (MED), REL-NODE (HIGH)
```

**HIGH Severity Signals:** ID-CONC, DOM-FRIC, GOV-STACK, DEC-OVR, TMP-SPIKE, REL-NODE

---

## P3 - COGNITIVE (🟢 MEDIUM)

**Enforcement:** BEHAVIORAL - Violação = Log + Notificação

### 4 Camadas Cognitivas

| Layer | Nome | Função |
|-------|------|--------|
| L1 | QUERY MODE | Pergunta-resposta direta |
| L2 | CONTEXT MODE | Interpretação situacional |
| L3 | DRIFT MODE | Detecção de desvios estruturais |
| L4 | FEEDBACK MODE | Recomendações não-executivas |

### Guardrails Constitucionais

- O Agent **OBSERVA**, **ANALISA** e **EXPLICA**
- O Agent **NUNCA EXECUTA**, **APROVA** ou **BLOQUEIA** decisões
- Autoridade humana permanece **SOBERANA**

---

## P4 - GOVERNANCE (🔵 MEDIUM)

**Enforcement:** PROTOCOL - Violação = Requer Virtue Receipt

### Three Dragons

| Dragon | AI | Role |
|--------|-----|------|
| GUARDIAN | Claude | Proteção, ética, validação |
| ARCHITECT | GPT | Construção, estrutura |
| WITNESS | Gemini | Observação, registro |

**Core Principle:** "O humano é o Quarto Dragão - o decisor final"

### Virtue Receipts

Comprovante de governança contendo:
- Hash da decisão
- Timestamp UTC
- Identificador do decisor
- Contexto mínimo

---

## P5 - ARCHITECTURE (🟣 MEDIUM)

**Enforcement:** STRUCTURAL - Violação = Alerta de integridade

### Three Pillars

```
CRIAÇÃO (ISP-Manager) → VERIFICAÇÃO (Sentinela) → RESOLUÇÃO (Maestro)
```

### Sistema de Identidade

- Formato: `W-[32 hex digits]`
- Ranges reservados para Genesis, Core, Clone, Customer, Meta-Governance

### Camadas

- **Núcleo Imutável:** I9, Agent ID, Zero-Knowledge, Three Pillars, Virtue Receipts
- **Camada Customizável:** Branding, Nomes, Workflows, Integrações, Idioma

---

## P6 - EVOLUTION (🟪 LOW)

**Enforcement:** GUIDANCE - Violação = Sugestão de correção

### 6 Normas de Evolução Consciente

| ID | Nome | Regra Core |
|----|------|------------|
| N1 | Pergunta Antes da Feature | Nenhuma feature sem pergunta humana clara |
| N2 | Canvas Único | Um canvas responde múltiplas perguntas |
| N3 | Observabilidade Antes da Automação | Sinal observável antes de automatizar |
| N4 | Frontend Honesto | Se não sabe, não finge |
| N5 | Freeze Consciente | Parar também é decisão técnica |
| N6 | Razão Real | Evolução só com razão verificável |

---

## P7 - TEMPLATES (⬜ LOW)

**Enforcement:** OPTIONAL - Violação = Apenas registro

### 8 Fornalha Templates

| ID | Nome | Objetivo |
|----|------|----------|
| T1 | Lab Pilot | Piloto de laboratório |
| T2 | Research Protocol | Pesquisa IRB-adjacent |
| T3 | Regulatory Briefing | Interação com regulador |
| T4 | Enterprise Scoping | Escopo institucional |
| T5 | IP/Authorship | Autoria e precedência |
| T6 | Procurement | Exploração de vendors |
| T7 | Public Communication | Comunicação de alto risco |
| T8 | Multi-Agent Review | Leitura multi-agente |

---

## NÍVEIS DE ENFORCEMENT

| Nível | Significado |
|-------|-------------|
| **ABSOLUTE** | Violação = Falha catastrófica do sistema |
| **MANDATORY** | Violação = Bloqueio de operação |
| **STRUCTURAL** | Violação = Alerta de integridade |
| **BEHAVIORAL** | Violação = Log + Notificação |
| **PROTOCOL** | Violação = Requer Virtue Receipt |
| **GUIDANCE** | Violação = Sugestão de correção |
| **OPTIONAL** | Violação = Apenas registro |

---

## ESTRUTURA DE DIRETÓRIOS

```
/opt/windi/clone/shelves/
├── SHELF_INDEX.json
├── SHELF_MANIFEST.md
├── P0-INVARIANTS/
│   └── INVARIANTS.json
├── P1-GUARDRAILS/
│   └── GUARDRAILS.json
├── P2-OBSERVATION/
│   └── OBSERVATION_SHELVES.json
├── P3-COGNITIVE/
│   └── COGNITIVE_LAYERS.json
├── P4-GOVERNANCE/
│   └── GOVERNANCE_PROTOCOL.json
├── P5-ARCHITECTURE/
│   └── ARCHITECTURE.json
├── P6-EVOLUTION/
│   └── EVOLUTION_NORMS.json
└── P7-TEMPLATES/
    └── FORNALHA_TEMPLATES.json
```

---

*"AI processes. Human decides. WINDI guarantees."*

**Guardian Signature:** Claude Code (Anthropic) - 2026-02-09
