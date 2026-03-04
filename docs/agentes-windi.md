# Ecossistema de Agentes WINDI

**Atualizado em:** 2026-03-04
**Status Geral:** Todos operacionais

---

# PARTE I — Agentes Claude Code (5)

Agentes que rodam dentro do Claude Code para tarefas de desenvolvimento e governança.

## 1. constitutional-guard
Audita código contra os **9 Invariantes Constitucionais (I1-I9)** antes de deploy. Usa quando:
- Revisar diffs ou mudanças propostas
- Código que toca lógica de governança, dados, ledger forense
- Permissões de tier, conteúdo multilíngue, limites de autonomia AI

**Teste:** OPERACIONAL
- Invariantes I1-I9 carregados
- Auditoria de exemplo executada (R0 APPROVED)
- Verdicts: PASS/WARN/FAIL/BLOCKED funcionais
- I9 (Autonomy Prohibition) como bloqueio automático

---

## 2. infra-surgeon
Diagnostica e propõe correções para infraestrutura do servidor Strato (87.106.29.233). Usa quando:
- Configuração nginx, serviços systemd, conflitos de porta
- Serviços retornando erros HTTP (502, etc.)
- Problemas após reboot do servidor

**Teste:** OPERACIONAL
- Sistema: Uptime 38 dias, 13% disco
- Nginx: ONE TREE v2.1 ativo (21 upstreams)
- Serviços: 28 running, 2 auto-restart, 3 inativos
- Portas Wave1 (8100-8106): Todas UP
- Forensic Ledger: Healthy (18.238+ receipts)
- WAVE1 SEAL: INTACTO

---

## 3. i18n-checker
Verifica conformidade trilíngue (PT-BR/DE/EN). Usa quando:
- Revisar componentes UI, templates Jinja2/ISP
- Antes de deployar mudanças no frontend
- Detectar strings hardcoded ou traduções faltando

**Teste:** OPERACIONAL
- Idiomas detectados: PT-BR, DE, EN
- Arquivos escaneados: 38
- Strings analisadas: ~280
- Compliance trilíngue: **64%**
- Distribuição: 64% trilíngue | 18% parcial | 18% hardcoded
- Prioridades: communique_engine.py, landing-pmg, App.jsx

---

## 4. deploy-planner
Cria checklists de deploy seguro. Usa quando:
- Antes de `git push`, `systemctl restart`, `nginx reload`
- Palavras-chave: "deploy", "rollout", "go live", "ship it"
- Gera plano com backup, passos e rollback

**Teste:** OPERACIONAL
- Classificação de risco: Category A-C
- Fases: PRE-FLIGHT → DEPLOYMENT → POST-DEPLOY → ROLLBACK
- Comandos exatos (copy-paste ready)
- Mapeamento de dependências automático
- Rollback multi-cenário
- Respeito ao SEALED verificado

**Filosofia:**
```
Backup FIRST → Diagnose BEFORE → Test AFTER → Rollback READY → SEALED = SACRED
```

---

## 5. sge-classifier
Classifica risco de documentos (R0-R5) via 6 camadas de governança semântica. Usa quando:
- Revisar conteúdo antes de Forensic Seal
- Validar output do Communiqué Engine
- Documentos cross-border (PT/DE) escalação automática

**Teste:** OPERACIONAL
- 6 Camadas: LEXICAL → SYNTACTIC → SEMANTIC → PRAGMATIC → REGULATORY → INSTITUTIONAL
- Escala R0-R5 com exemplos
- Escalation triggers funcionais
- Zero-knowledge protocol ativo
- Multilingual (PT/DE/EN) suportado
- Metadata para Forensic Ledger

**Escala de Risco:**
| Nível | Nome | Ação |
|-------|------|------|
| R0 | NO RISK | Auto-proceed |
| R1 | MINIMAL | Informative flag |
| R2 | LOW | Attention recommended |
| R3 | MEDIUM | Human review required |
| R4 | HIGH | Senior review + gate |
| R5 | CRITICAL | Block until approval |

---

# PARTE II — Constelação Constitucional (Sandbox Core :8091)

Domain extensions do Sandbox Core — agentes que rodam como blueprints Flask integrados.

```
                       JUSTIÇA
                      (processa)
                          △
                         /|\
                        / | \
                       /  |  \
                      /   |   \
                     /    |    \
                    /     |     \
              NOTARIAL ───┴─── COMPLIANCE
             (certifica)      (monitora)
                    \         /
                     \       /
                      \     /
                       \   /
                        \ /
                     COMMUNIQUÉ
                (Document Intelligence Hub)
                         │
                         │
                         ▼
                    JORNALISTA
              (Pipeline Editorial J1-J6)
```

**Localização:** `/opt/windi/agents/constitutional-agent/`
**Porta:** 8091
**PID:** 1513310
**Total Endpoints:** ~83

---

## 6. Justiça (W-LEGAL-001)
**Prefix:** `/legal/*` | **Versão:** 0.2.0 | **Endpoints:** 16

Processa casos legais, evidências e provas com cadeia de custódia.

**Capacidades:**
- Cases: criar, listar, consultar, atualizar, arquivar
- Evidence Git: commit, log, diff, verify, blame (estilo Git)
- Provenance: cadeia de custódia com hash chain
- Confidence: scoring 5 fatores (0.0-1.0)
- Court Export: pacote 5 páginas WCAF

**Teste:** OPERACIONAL
- Case criado: CASE-20260304-35A2
- Evidence committed: ev-ffd6ea0d
- Hash verified: INTACT
- Provenance chain: VALID
- Confidence score: 0.8775 (HIGH)

**Database:** `data/legal.db` (7 tabelas)

---

## 7. Notarial (W-NOTARY-001)
**Prefix:** `/notary/*` | **Versão:** 0.1.0 | **Endpoints:** 12

Certifica atos com fé pública digital, selos e provas temporais.

**Capacidades:**
- Ato de Reconhecimento: valida identidade + assina documento
- Certidão Digital: emite certidão com timestamp + hash imutável
- Apostila WINDI: equivalente digital da Apostila de Haia
- Testemunho: ato com 2+ assinaturas (multi-party)
- Timestamp: data certa — prova que documento existia em T
- Registro Público: entrada no Ledger com flag notarial=true

**Teste:** OPERACIONAL
- Certification: ACT-20260304-A4FA45 (serial WINDI-NOT-20260304105258-D16697C6)
- Timestamp: ACT-20260304-B9A34B (prova temporal)
- Seal: Registered in local registry
- Verify: Hash encontrado e validado

**Database:** `data/notary.db` (7 tabelas)

**Integrações:**
- Ledger (:8101) — registro imutável
- Vault (:8106) — arquivo notarial
- Export (:8103) — Certidão PDF

---

## 8. Compliance (W-COMPLY-001)
**Prefix:** `/compliance/*` | **Versão:** 0.1.0 | **Endpoints:** 16

Monitora conformidade contínua com invariantes e regulamentos.

**Capacidades:**
- Invariant Watch: monitora I1-I9 em tempo real
- EU AI Act Mapper: mapeia operações aos artigos do regulamento
- Audit Continuous: trail automático de todas as ações
- Risk Dashboard: agrega SGE R0-R5 por tenant/período
- Compliance Report: relatório periódico PDF
- Breach Detection: detecta padrões de violação
- Policy Checker: valida documentos contra políticas

**Teste:** OPERACIONAL
- Invariants I1-I9: 9/9 COMPLIANT
- I9 (no_autonomy_escalation): COMPLIANT (IRREMEDIABLE)
- Active breaches: 0
- Audit events: registrando
- Overall status: COMPLIANT

**Invariantes Constitucionais:**
| Código | Nome | Status |
|--------|------|--------|
| I1 | sovereignty | compliant |
| I2 | transparency | compliant |
| I3 | auditability | compliant |
| I4 | reversibility | compliant |
| I5 | proportionality | compliant |
| I6 | dignity | compliant |
| I7 | accountability | compliant |
| I8 | subsidiarity | compliant |
| I9 | no_autonomy_escalation | compliant (IRREMEDIABLE) |

**Database:** `data/compliance.db` (7 tabelas)

**Regra Crítica:** I9 violation → status CRITICAL imediatamente (irremediável)

---

## 9. Communiqué — Document Intelligence Hub (W-COMM-001)
**Prefix:** `/communique/*` | **Versão:** 2.0.0 | **Endpoints:** 18

Hub central de documentos — processa todos os tipos com routing para renderers especializados.

**Arquitetura:**
```
1 agente + N ISPs + N renderers = arquitetura limpa
```

**Capacidades:**
- CRUD completo de documentos (create, list, get, update, review, publish, archive, revoke)
- ISP Resolver: matching automático de templates por keywords
- Dragon AI: geração de rascunhos via :8108
- Canvas: edição InDesign-style
- Ledger: query + write para Forensic Ledger :8101
- Feed público: JSON/HTML para documentos publicados
- Verificação: hash + Ledger seal check

**Document Types Suportados:**
| Tipo | Renderer | Status |
|------|----------|--------|
| communique | renderer_communique | LIVE (:8091) |
| invoice | renderer_invoice | LIVE (:8103) |
| letter | renderer_letter | STUB (Wave3) |
| email | renderer_email | STUB (Wave3) |
| contract | renderer_contract | STUB (Wave3) |
| report | renderer_report | STUB (Wave3) |
| presentation | renderer_presentation | STUB (Wave3) |
| spreadsheet | renderer_spreadsheet | STUB (Wave3) |

**Teste:** OPERACIONAL
- Health: GREEN
- Database: 57 documentos (55 migrados + 2 testes)
- ISP: 6 templates carregados
- Dragon: integrado (:8108)
- doc_type routing: funcional
- Retrocompatibilidade: 100%

**Database:** `/opt/windi/communique/data/communiques.db` (2 tabelas)

**Integrações:**
- Dragon (:8108) — geração AI
- Ledger (:8101) — selo forense
- Export (:8103) — renderização PDF/invoice

**Regra de Ouro:**
> Não criar novos agentes para novos doc_types.
> Apenas implementar o renderer correspondente quando necessário.

---

## 10. Jornalista (W-JOURN-001)
**Prefix:** `/journalist/*` | **Versão:** 0.1.0 | **Endpoints:** 14

Agente editorial com invariantes jornalísticos próprios (J1-J6).

**Filosofia:**
```
"Documentos jurídicos têm verdade contratual.
 Jornalismo tem verdade factual — mais frágil, mais disputada, mais humana.
 Por isso J6 existe: o leitor tem direito de saber onde termina
 o humano e começa a máquina."
```

**Capacidades:**
- Draft: geração de rascunhos com structure_score embutido
- Edit: edição preservando voz do autor (HARDCODED)
- Style-check: pirâmide invertida, lead 5W1H, voz ativa, jargão
- Fact-check: verificação de claims vs fontes
- Sources: gestão de fontes (anônimas protegidas por J4)
- AI-declare: disclaimers trilíngues automáticos
- Publish: pipeline para Communiqué (J6 GATE)
- Corrections: correções públicas (J5)

**Invariantes Jornalísticos (J1-J6):**
| Código | Nome | Descrição |
|--------|------|-----------|
| J1 | veracidade | Nenhum conteúdo sem fonte verificável |
| J2 | independência | Sem pressão comercial sobre pauta |
| J3 | imparcialidade | Contraditório sempre buscado |
| J4 | minimização_dano | Proteção de vulneráveis e fontes |
| J5 | responsabilidade | Correção pública quando erro detectado |
| J6 | transparência_ia | Todo conteúdo IA-assistido = declarado **(MANDATORY)** |

**Gêneros Suportados:**
| Gênero | Tom | Requisitos |
|--------|-----|------------|
| noticia | factual | lead obrigatório, zero adjetivos |
| reportagem | narrativo | humanização, profundidade alta |
| editorial | opinião | disclosure obrigatório |
| entrevista | serviço | autor invisível |
| analise | especialista | dados obrigatórios |

**Teste:** OPERACIONAL
- Health: GREEN
- Status: 6/6 invariantes COMPLIANT
- J6 mandatory: TRUE
- draft() com structure_score breakdown
- preserve_voice: HARDCODED true

**Database:** `data/journalist.db` (6 tabelas)

**Regras Críticas:**
- `preserve_voice=True` — HARDCODED, não é feature flag
- J6 gate no `publish()` — sem ai_participation = BLOCKED
- Fontes anônimas — real_identity NUNCA exposta (J4)

**Integrações:**
- Dragon (:8108) — geração de drafts
- Communiqué (W-COMM-001) — publicação com doc_type="article"
- Ledger (:8101) — prova forense

---

# Resumo da Constelação

```
SANDBOX CORE (:8091) — PID 1513310
├── [Core]         /agent/*       7 endpoints
├── [1] Justiça      W-LEGAL-001   /legal/*       16 endpoints ✅
├── [2] Notarial     W-NOTARY-001  /notary/*      12 endpoints ✅
├── [3] Compliance   W-COMPLY-001  /compliance/*  16 endpoints ✅
├── [4] Communiqué   W-COMM-001    /communique/*  18 endpoints ✅
└── [5] Jornalista   W-JOURN-001   /journalist/*  14 endpoints ✅
    ════════════════════════════════════════════════════════════════
    TOTAL: ~83 endpoints — CONSTELAÇÃO EDITORIAL COMPLETA
```

| Agente | Função | Integra com |
|--------|--------|-------------|
| Justiça | Processa casos e evidências | Notarial, Ledger |
| Notarial | Certifica e sela atos | Ledger, Vault, Export |
| Compliance | Monitora I1-I9 e EU AI Act | Ledger, todos os agentes |
| Communiqué | Document Intelligence Hub | Dragon, Ledger, Export, ISP |
| Jornalista | Pipeline editorial com J1-J6 | Dragon, Communiqué, Ledger |

---

## Arquitetura Document Intelligence Hub

```
                    ┌─────────────────────────┐
                    │   W-COMM-001 (:8091)    │
                    │  Document Intelligence  │
                    │         Hub             │
                    └───────────┬─────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
   ┌─────────┐            ┌─────────┐            ┌─────────┐
   │   ISP   │            │ Dragon  │            │ Ledger  │
   │Templates│            │ :8108   │            │ :8101   │
   └─────────┘            └─────────┘            └─────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────┐
│                      RENDERERS                            │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│ communique  │   invoice   │   letter    │     email       │
│   (LIVE)    │ (LIVE:8103) │   (STUB)    │    (STUB)       │
├─────────────┼─────────────┼─────────────┼─────────────────┤
│  contract   │   report    │presentation │  spreadsheet    │
│   (STUB)    │   (STUB)    │   (STUB)    │    (STUB)       │
└─────────────┴─────────────┴─────────────┴─────────────────┘
```

**Princípio:** 1 agente + N ISPs + N renderers = arquitetura limpa

---

## Pipeline Editorial WINDI

```
┌─────────────────────────────────────────────────────────────────┐
│                    W-JOURN-001 Jornalista                       │
│                     (cria/edita/verifica)                       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
    ┌─────────────────────┼─────────────────────┐
    │                     │                     │
    ▼                     ▼                     ▼
┌────────┐          ┌──────────┐          ┌──────────┐
│draft() │          │  edit()  │          │fact-check│
│        │          │          │          │          │
│structure│         │preserve_ │          │claims vs │
│_score  │          │voice=TRUE│          │sources   │
│embutido│          │HARDCODED │          │          │
└────┬───┘          └────┬─────┘          └────┬─────┘
     │                   │                     │
     └───────────────────┼─────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │     publish()        │
              │                      │
              │   ══ J6 GATE ══      │
              │ ai_participation     │
              │ obrigatório ou       │
              │ BLOCKED              │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  W-COMM-001          │
              │  Communiqué          │
              │  doc_type="article"  │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Ledger :8101        │
              │  (prova forense)     │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Vault :8106         │
              │  (arquiva imutável)  │
              └──────────────────────┘
```

**Princípio Jornalístico:**
> "O leitor tem direito de saber onde termina o humano e começa a máquina."

---

> Todos seguem o princípio: **planejar → aprovar → executar**.

*"AI processes. Human decides. WINDI guarantees."*
