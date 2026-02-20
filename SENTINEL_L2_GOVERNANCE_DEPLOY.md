# WINDI SENTINEL L2 — Deploy na Governance API
## "O Sentinel não precisa de casa nova. A Governance JÁ É a casa dele."

---

## Arquitetura Correta

```
                    ┌──────────────────────────────┐
                    │   GOVERNANCE API (:8080)      │
                    │                              │
                    │   /api/status          ✅    │
                    │   /api/submissions     ✅    │
                    │   /api/dashboard       ✅    │
                    │   /api/integrity       ✅    │
                    │   /api/compliance      ✅    │
                    │   /api/health          ✅    │
                    │                              │
                    │   /api/sentinel/status  🆕   │  ← Estado + propostas
                    │   /api/sentinel/proposals 🆕 │  ← Pendentes
                    │   /api/sentinel/authorize 🆕 │  ← Humano autoriza
                    │   /api/sentinel/veto    🆕   │  ← Humano veta
                    │   /api/sentinel/rules   🆕   │  ← Transparência I9
                    │   /api/sentinel/history 🆕   │  ← Auditoria
                    │   /api/sentinel/heal    🆕   │  ← Trigger manual
                    │                              │
                    └──────────┬───────────────────┘
                               │
                    ┌──────────▼───────────────────┐
                    │   SENTINEL DAEMON (:8098)     │
                    │   Monitora todos os serviços  │
                    │   Gera propostas → Engine L2  │
                    └──────────────────────────────┘
```

O Sentinel Daemon (porta 8098) continua observando.
Quando detecta anomalia, cria proposta via `sentinel_level2.py`.
A Governance API (porta 8080) expõe as propostas para o humano decidir.

**Um portão. Uma família. Uma API.**

---

## Deploy em 4 Passos

### PASSO 1: Upload dos arquivos (no seu terminal local)

```bash
# Copiar os 3 arquivos para o servidor
scp sentinel_fix_10de10.py windi@87.106.29.233:/opt/windi/sentinel/
scp sentinel_level2.py windi@87.106.29.233:/opt/windi/engine/
scp sentinel_governance_patch.py windi@87.106.29.233:/opt/windi/engine/
```

### PASSO 2: Fix cirúrgico do Sentinel Daemon (no servidor)

```bash
ssh windi@87.106.29.233

# Corrigir health check + expandir radar
cd /opt/windi/sentinel
python3 sentinel_fix_10de10.py

# Restart do daemon
sudo systemctl restart windi-sentinel
sleep 65
tail -15 /opt/windi/logs/sentinel.log
```

**Resultado esperado:** 10/10 healthy (ou 9/10 se forensic inativo)

### PASSO 3: Patch da Governance API (no servidor)

```bash
cd /opt/windi/engine

# Teste standalone do motor L2
python3 sentinel_level2.py

# Aplicar patch na Governance API
python3 sentinel_governance_patch.py

# Restart da Governance API
# Se roda via nohup:
kill $(pgrep -f windi_governance_api) 2>/dev/null
sleep 2
nohup python3 windi_governance_api.py > /opt/windi/logs/governance.log 2>&1 &
sleep 3

# Verificar
curl -s http://localhost:8080/api/sentinel/status | python3 -m json.tool
curl -s http://localhost:8080/api/sentinel/rules | python3 -m json.tool
```

### PASSO 4: Verificar via HTTPS (público)

```bash
# Status completo
curl -s https://admin.windia4desk.tech/governance/api/sentinel/status | python3 -m json.tool

# Regras de autorização
curl -s https://admin.windia4desk.tech/governance/api/sentinel/rules | python3 -m json.tool

# Propostas pendentes (se houver)
curl -s https://admin.windia4desk.tech/governance/api/sentinel/proposals | python3 -m json.tool
```

---

## Como o Fluxo Funciona

```
1. Sentinel Daemon detecta: windi-forensic (:8094) down há 60 ciclos
   │
2. Daemon chama: sentinel_check_hook("windi-forensic", result, state)
   │
3. ProposalEngine cria: SEN-20260215-0001
   │   action: RESTART_SERVICE
   │   impact: MEDIUM
   │   auth: HUMAN_EXPLICIT
   │
4. Proposta aparece em:
   │   GET /api/sentinel/proposals
   │   Dashboard Wallet (React)
   │
5. Human Dragon decide:
   │
   ├── POST /api/sentinel/authorize
   │   {"proposal_id": "SEN-20260215-0001"}
   │   → Sentinel executa: sudo systemctl restart windi-forensic
   │   → Gera SEN-RECEIPT-a7f3c91e
   │
   └── POST /api/sentinel/veto
       {"proposal_id": "SEN-20260215-0001", "reason": "Não é prioridade agora"}
       → Proposta arquivada com razão do veto
```

---

## Regras de Autorização (Invariante I9)

| Impacto   | Serviços                              | Autorização          |
|-----------|---------------------------------------|----------------------|
| BAIXO     | cortex, clone, warroom, landing, wallet | Pré-autorizado (N3) |
| MÉDIO     | governance, babel, bridge              | Aprovação humana     |
| ALTO      | gateway, nginx reload, stop serviço    | Confirmado + frase   |
| PROIBIDO  | sentinel (auto-restart), custom cmd    | NUNCA                |

**Regra de Ouro:** O Sentinel NUNCA pode reiniciar a si mesmo.

---

## Mapa de Endpoints Completo pós-Patch

```
Governance API (:8080)
├── /api/status           → Estado do engine + ISPs
├── /api/submissions      → Submissions ao engine
├── /api/dashboard        → Dados do dashboard
├── /api/integrity        → Verificação de integridade
├── /api/compliance       → Estado de compliance
├── /api/health           → Health check da API
│
├── /api/sentinel/status     → 🆕 Estado Sentinel + daemon + propostas
├── /api/sentinel/proposals  → 🆕 Propostas pendentes
├── /api/sentinel/history    → 🆕 Histórico de decisões
├── /api/sentinel/authorize  → 🆕 Humano autoriza
├── /api/sentinel/veto       → 🆕 Humano veta
├── /api/sentinel/rules      → 🆕 Regras I9 (transparência)
└── /api/sentinel/heal       → 🆕 Trigger manual (N3)
```

---

*"KI verarbeitet. Mensch entscheidet. WINDI garantiert."*
