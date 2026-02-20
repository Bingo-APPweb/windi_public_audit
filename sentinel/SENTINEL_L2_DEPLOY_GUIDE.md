# WINDI SENTINEL — Deployment Guide
## Fix Cirúrgico + Nível 2: Protocolo de Intervenção Humana

---

## PASSO 1: Fix Cirúrgico (5 minutos)

Upload `sentinel_fix_10de10.py` para o servidor e execute:

```bash
# 1. Upload do fix para o servidor
scp sentinel_fix_10de10.py windi@87.106.29.233:/opt/windi/sentinel/

# 2. Conectar ao servidor
ssh windi@87.106.29.233

# 3. Executar o fix
cd /opt/windi/sentinel
python3 sentinel_fix_10de10.py

# 4. Restart do Sentinel
sudo systemctl restart windi-sentinel

# 5. Aguardar um ciclo (60s) e verificar
sleep 65
tail -20 /opt/windi/logs/sentinel.log

# 6. Verificar status via API
curl -s http://localhost:8098/api/status | python3 -m json.tool
```

**Resultado esperado:** 10/10 healthy (ou 9/10 se forensic não estiver deployado ainda)

---

## PASSO 2: Deploy do Sentinel Level 2 (10 minutos)

```bash
# 1. Upload
scp sentinel_level2.py windi@87.106.29.233:/opt/windi/sentinel/

# 2. No servidor — teste standalone
cd /opt/windi/sentinel
python3 sentinel_level2.py

# 3. Verificar que criou os arquivos
ls -la /opt/windi/data/sentinel_proposals.json
cat /opt/windi/logs/sentinel_actions.log
```

---

## PASSO 3: Integrar no Sentinel Daemon

Editar `/opt/windi/sentinel/windi_sentinel.py` e adicionar após cada ciclo de check:

```python
# No topo do arquivo, adicionar import:
from sentinel_level2 import sentinel_check_hook

# No loop principal, após processar os checks:
for name, result in check_results.items():
    sentinel_check_hook(name, result, state)
```

---

## PASSO 4: Registrar endpoints na Sentinel Bridge

Se o Sentinel Bridge (porta 8098) usa Flask, adicionar:

```python
from sentinel_level2 import register_sentinel_l2_routes
engine = register_sentinel_l2_routes(app)
```

Endpoints disponíveis:
- `GET  /sentinel/proposals` — Lista pendentes
- `GET  /sentinel/proposals/history` — Histórico
- `POST /sentinel/proposals/:id/authorize` — Autorizar
- `POST /sentinel/proposals/:id/veto` — Vetar
- `GET  /sentinel/proposals/:id` — Detalhes

---

## PASSO 5: Dashboard React

O arquivo `sentinel_l2_dashboard.jsx` pode ser integrado como nova aba no Wallet ("O Espelho") ou deployado standalone.

---

## Arquitetura dos 3 Níveis

```
NÍVEL 1 (ATUAL): Observar
  Sentinel → detecta → loga → reporta
  Humano consulta quando quer

NÍVEL 2 (ESTE DEPLOY): Propor + Veto
  Sentinel → detecta → cria Proposta → Dashboard
  Humano → Autoriza ou Veta → Sentinel executa (ou não)
  Forensic → grava Receipt de cada decisão

NÍVEL 3 (FUTURO): Auto-heal limitado
  Sentinel → detecta → verifica PRE_AUTHORIZATION_RULES
  Se pré-autorizado → executa sozinho + gera Receipt
  Se não → cria Proposta → Dashboard (volta ao Nível 2)
  I9: Sentinel NUNCA pode reiniciar a si mesmo
```

---

## Regras de Autorização (PRE_AUTHORIZATION_RULES)

| Ação | Serviço | Autorização |
|------|---------|-------------|
| Restart | cortex, clone, warroom, landing, wallet | Pré-autorizado |
| Restart | governance, babel, bridge | Aprovação humana |
| Restart | gateway | Confirmado + passphrase |
| Restart | sentinel | PROIBIDO (I9) |
| Stop | qualquer | Confirmado + passphrase |
| Nginx reload | — | Confirmado + passphrase |
| Custom command | — | PROIBIDO |

---

*"Sentinel propõe. Humano autoriza. WINDI garante."*
