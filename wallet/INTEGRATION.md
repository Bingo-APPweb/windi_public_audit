# WALLET Auto-Provision — Guia de Integração
## Conectando Lead Admin → WALLET → A4Desk

**Objetivo:** Quando o botão APPROVE é clicado no Lead Admin,
o WALLET é criado automaticamente. O humano nunca precisa intervir manualmente.

---

## O Pipeline Completo

```
Landing Page     →  Lead criado       (já funciona)
Lead Admin       →  Humano aprova     (já funciona)
  ↓ [NOVO]
wallet_bridge    →  Detecta aprovação
  ↓
Governance API   →  /api/wallet/provision
  ↓
Forensic Ledger  →  WALLET_PROVISIONED registrado
  ↓
A4Desk Builder   →  Renderiza PF ou PJ automaticamente
```

---

## 3 Modos de Integração (escolha UM)

### Modo A: Hook Direto (⭐ Recomendado)

Adicionar 5 linhas no código do Lead Admin quando o botão Approve é clicado.

**No arquivo do Lead Admin** (provavelmente `/opt/windi/id-genesis/app.py`
ou similar):

```python
# PASSO 1: No topo do arquivo, adicionar imports
import sys
sys.path.insert(0, '/opt/windi/wallet')
from wallet_bridge import on_lead_approved

# PASSO 2: Dentro da função que trata APPROVE, DEPOIS de mudar status:
# (Localizar com: grep -n "APPROVED\|approve\|status" app.py)

    # ... código existente que muda status para APPROVED ...

    # ─── AUTO-PROVISION WALLET ────────────────────────
    wallet = on_lead_approved({
        "lead_id": lead_id,
        "name": name,
        "email": email,
        "company": company,
        "interest": interest,
        "approved_by": "admin:jober",
    })
    if wallet and wallet.get("status") == "ok":
        # Opcional: salvar wallet_id no lead
        # db.execute("UPDATE leads SET wallet_id=? WHERE lead_id=?",
        #            (wallet["wallet_id"], lead_id))
        pass
    # ─── END AUTO-PROVISION ───────────────────────────
```

### Modo B: Webhook (se Lead Admin não pode importar módulo)

O Lead Admin faz um POST HTTP para a Governance API após aprovar.

**No Lead Admin:**
```python
import requests

# Após aprovar o lead:
requests.post(
    "http://localhost:8080/api/wallet/bridge/approve",
    json={
        "lead_id": lead_id,
        "name": name,
        "email": email,
        "company": company,
        "interest": interest,
    },
    timeout=10,
)
```

**Na Governance API** (adicionar ao lado do wallet Blueprint):
```python
from wallet_bridge import create_bridge_blueprint
app.register_blueprint(create_bridge_blueprint())
```

### Modo C: Watcher (sem modificar Lead Admin)

Processo independente que observa o DB de leads e provisiona automaticamente.

```bash
# Executar como serviço:
cd /opt/windi/wallet
python3 wallet_bridge.py watch --interval 30

# Ou provisionar todos de uma vez:
python3 wallet_bridge.py provision-all
```

**systemd service (opcional):**
```ini
[Unit]
Description=WINDI Wallet Watcher v1.0.0
After=network.target

[Service]
Type=simple
User=windi
Group=windi
WorkingDirectory=/opt/windi/wallet
ExecStart=/usr/bin/python3 /opt/windi/wallet/wallet_bridge.py watch --interval 60
Restart=always
RestartSec=10
StandardOutput=append:/opt/windi/logs/wallet_bridge.log
StandardError=append:/opt/windi/logs/wallet_bridge.log

[Install]
WantedBy=multi-user.target
```

---

## Preparação no Servidor (Antes de Integrar)

```bash
# 1. Copiar arquivos
cp wallet_bridge.py /opt/windi/wallet/
cp wallet_provisioning.py /opt/windi/wallet/

# 2. Garantir que Governance API tem o Blueprint do WALLET
# (ver DEPLOY.md para detalhes)

# 3. Verificar que WALLET está respondendo
curl -s http://localhost:8080/api/wallet/health

# 4. Identificar estrutura do Lead Admin
# Encontrar o DB:
find /opt/windi -name "*.db" | xargs -I{} sqlite3 {} ".tables" 2>/dev/null
# Encontrar a função de approve:
grep -rn "APPROVED\|approve\|status" /opt/windi/id-genesis/ 2>/dev/null
grep -rn "APPROVED\|approve\|status" /opt/windi/a4desk-landing/ 2>/dev/null
```

---

## Mapeamento de Dados: Lead → WALLET

| Campo Lead Admin    | Campo WALLET          | Transformação        |
|--------------------|-----------------------|----------------------|
| lead_id            | lead_id               | Direto               |
| name               | display_name          | Direto               |
| email              | email                 | Direto               |
| company            | org.name + kind=PJ    | "-" → PF, outro → PJ|
| interest           | role                  | governance→admin, pro→manager, free→operator |
| email domain       | org.domain            | Auto-extraído se não genérico |
| approved_by        | created_by            | "admin:jober"        |

---

## Detecção Automática PF vs PJ

O bridge decide automaticamente:

| company no Lead      | Resultado        |
|----------------------|------------------|
| `-` ou vazio          | PF (soberano)    |
| `WINDI Publishing`   | PJ + domain auto |
| `Test GmbH`          | PJ               |
| `WINDI SYSTEM`       | PJ + domain auto |

E-mails genéricos (gmail, yahoo, web.de) não geram domínio de org.

---

## Verificação Pós-Integração

```bash
# 1. Aprovar um lead no admin
# (usar o browser em admin.windia4desk.tech)

# 2. Verificar que o wallet foi criado
curl -s http://localhost:8080/api/wallet/stats | python3 -m json.tool

# 3. Buscar pelo email
curl -s "http://localhost:8080/api/wallet/me?email=EMAIL_DO_LEAD" | python3 -m json.tool

# 4. Verificar ledger
curl -s http://localhost:8080/api/wallet/stats | python3 -m json.tool

# 5. Logs
tail -20 /opt/windi/logs/wallet.log
tail -20 /opt/windi/logs/wallet_bridge.log
```

---

## Diagrama do Fluxo

```
  ┌─────────────────┐
  │   Landing Page   │  ← Humano se registra
  │    (:8086)       │
  └────────┬────────┘
           │ POST /api/leads
           ▼
  ┌─────────────────┐
  │   Lead Admin     │  ← Admin vê leads pendentes
  │  (ID Genesis)    │
  │    (:8096)       │
  └────────┬────────┘
           │ Botão APPROVE (I9: Human decides)
           ▼
  ┌─────────────────┐
  │  wallet_bridge   │  ← NOVO: converte lead → wallet payload
  │   (hook/webhook) │
  └────────┬────────┘
           │ POST /api/wallet/provision
           ▼
  ┌─────────────────┐
  │  Governance API  │  ← Cria identidade soberana
  │    (:8080)       │
  │  wallet module   │
  └────────┬────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
  ┌──────┐  ┌────────┐
  │Wallet│  │Forensic│  ← Registra WALLET_PROVISIONED
  │  DB  │  │ Ledger │
  │(.db) │  │(:8094) │
  └──────┘  └────────┘
           │
           ▼
  ┌─────────────────┐
  │   A4Desk BABEL   │  ← Renderiza PF/PJ automaticamente
  │    (:8085)       │
  │  via /wallet/me  │
  └─────────────────┘
```

---

*"Primeiro existir. Depois respirar. Depois se ver. Depois evoluir."* 🐉
