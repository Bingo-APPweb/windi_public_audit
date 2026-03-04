# Resumo dos 5 Agentes WINDI

**Testados em:** 2026-03-04
**Status Geral:** Todos operacionais

---

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

> Todos seguem o princípio: **planejar → aprovar → executar**.

*"AI processes. Human decides. WINDI guarantees."*
