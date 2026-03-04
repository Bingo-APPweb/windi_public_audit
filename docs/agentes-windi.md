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

# PARTE II — Triângulo Constitucional (Sandbox Core :8091)

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
```

**Localização:** `/opt/windi/agents/constitutional-agent/`
**Porta:** 8091
**PID:** 1506896
**Total Endpoints:** 51

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

# Resumo da Constelação

```
SANDBOX CORE (:8091) — PID 1506896
├── [Core]       /agent/*       7 endpoints
├── [1] Justiça    W-LEGAL-001   /legal/*       16 endpoints ✅
├── [2] Notarial   W-NOTARY-001  /notary/*      12 endpoints ✅
└── [3] Compliance W-COMPLY-001  /compliance/*  16 endpoints ✅
    ═══════════════════════════════════════════════════════════
    TOTAL: 51 endpoints — TRIÂNGULO CONSTITUCIONAL VIVO
```

| Agente | Função | Integra com |
|--------|--------|-------------|
| Justiça | Processa casos e evidências | Notarial, Ledger |
| Notarial | Certifica e sela atos | Ledger, Vault, Export |
| Compliance | Monitora I1-I9 e EU AI Act | Ledger, todos os agentes |

---

> Todos seguem o princípio: **planejar → aprovar → executar**.

*"AI processes. Human decides. WINDI guarantees."*
