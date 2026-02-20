# WINDI Registration Pipeline — Deployment Guide

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    admin.windia4desk.tech                        │
│                         (nginx)                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   /clone/              a4Desk Landing (static HTML)              │
│       │                "Wissen, bevor Sie unterschreiben"         │
│       │                                                          │
│       ▼  "Jetzt starten →"                                       │
│   /clone/leads  ──────►  ID Genesis (:8096)                      │
│       │                  ┌─────────────────────┐                 │
│       │                  │ POST /api/leads      │                 │
│       │                  │  1. Valida dados     │                 │
│       │                  │  2. Salva no SQLite  │                 │
│       │                  │  3. Gera token 48h   │                 │
│       │                  │  4. SMTP → Strato    │                 │
│       │                  └────────┬────────────┘                 │
│       │                           │                               │
│       │                    ┌──────▼──────┐                       │
│       │                    │  📧 E-MAIL   │                       │
│       │                    │  Verificação │                       │
│       │                    │  Noir+Gold   │                       │
│       │                    │  DE/EN/PT    │                       │
│       │                    └──────┬──────┘                       │
│       │                           │                               │
│       │                    User clica link                        │
│       │                           │                               │
│   /clone/verify?token=xxx ───────►│                               │
│                          ┌────────▼────────────┐                 │
│                          │ GET /api/verify      │                 │
│                          │  1. Valida token     │                 │
│                          │  2. Cria WALLET      │                 │
│                          │     WDI-H (Human)    │                 │
│                          │     WDI-C (Company)  │                 │
│                          │  3. Welcome email    │                 │
│                          │  4. Página sucesso   │                 │
│                          └────────┬────────────┘                 │
│                                   │                               │
│   /clone/app/  ◄──────────────────┘                              │
│       │                  a4Desk Desktop (:8092)                   │
│       │                  Editor + Governance                      │
│       │                                                          │
│   /clone/api/leads/stats    Estatísticas de registro             │
│   /clone/api/wallets        Lista de WALLETs                     │
│   /clone/api/wallet/{id}    Detalhes do WALLET                   │
└──────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- 12 aliases @a4desk.de configurados no Strato ✅
- Postfach info@a4desk.de ativo (53 GB, Catchall) ✅
- ID Genesis rodando na porta 8096 ✅
- nginx proxy /clone/leads → 8096 ✅

## Files

| File | Location (server) | Purpose |
|------|-------------------|---------|
| `registration_pipeline.py` | `/opt/windi/id-genesis/` | FastAPI router: leads, verify, wallets |
| `deploy_registration.sh` | (run once, then delete) | Automated deployment script |
| `.env` | `/opt/windi/id-genesis/` | SMTP credentials + config |

## Quick Deploy (3 commands)

```bash
# 1. Upload files to server
scp registration_pipeline.py deploy_registration.sh windi@87.106.29.233:/opt/windi/id-genesis/

# 2. SSH in and configure SMTP password
ssh windi@87.106.29.233
nano /opt/windi/id-genesis/.env   # set SMTP_PASS

# 3. Run deploy
cd /opt/windi/id-genesis
chmod +x deploy_registration.sh
./deploy_registration.sh
```

## Manual Deploy (step by step)

### Step 1: Upload

```bash
# From your local machine:
scp registration_pipeline.py windi@87.106.29.233:/opt/windi/id-genesis/
```

### Step 2: Configure .env

```bash
ssh windi@87.106.29.233
nano /opt/windi/id-genesis/.env
```

Required variables:
```
SMTP_HOST=smtp.strato.de
SMTP_PORT=465
SMTP_USER=info@a4desk.de
SMTP_PASS=<senha real do Strato Postfach>
SMTP_FROM_NAME=a4Desk by WINDI
SMTP_FROM_EMAIL=noreply@a4desk.de
BASE_URL=https://admin.windia4desk.tech
REG_DB_PATH=/opt/windi/data/windi_registration.db
```

### Step 3: Integrate with ID Genesis

Add to the ID Genesis main app:

```python
from registration_pipeline import router as reg_router
app.include_router(reg_router)
```

### Step 4: Nginx — Add verify route

```bash
sudo nano /etc/nginx/sites-enabled/admin.windia4desk.tech
```

Add BEFORE `listen 443 ssl;`:

```nginx
    # ── Registration Pipeline: Email Verification (8096) ──
    location = /clone/verify {
        proxy_pass http://127.0.0.1:8096/api/verify;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # ── Registration Stats & Wallets (8096) ──
    location /clone/api/leads/ {
        proxy_pass http://127.0.0.1:8096/api/leads/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /clone/api/wallets {
        proxy_pass http://127.0.0.1:8096/api/wallets;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /clone/api/wallet/ {
        proxy_pass http://127.0.0.1:8096/api/wallet/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
```

Test and reload:
```bash
sudo nginx -t && sudo systemctl reload nginx
```

### Step 5: Restart ID Genesis

```bash
# Kill current process
kill $(pgrep -f 'id.genesis\|8096') 2>/dev/null
sleep 2

# Start with .env loaded
cd /opt/windi/id-genesis
set -a; source .env; set +a
nohup python3 main.py > /opt/windi/logs/id-genesis.log 2>&1 &
```

### Step 6: Smoke Tests

```bash
# Health
curl -s http://localhost:8096/health | python3 -m json.tool

# Lead capture
curl -s -X POST http://localhost:8096/api/leads \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@example.com","lang":"de"}'

# Verify (should return error page for invalid token)
curl -s "http://localhost:8096/api/verify?token=invalid_test" | head -5

# Stats
curl -s http://localhost:8096/api/leads/stats | python3 -m json.tool

# Wallets
curl -s http://localhost:8096/api/wallets | python3 -m json.tool

# Via nginx
curl -s -X POST https://admin.windia4desk.tech/clone/leads \
  -H "Content-Type: application/json" \
  -d '{"name":"Nginx Test","email":"nginx@test.de","lang":"de"}'

curl -s "https://admin.windia4desk.tech/clone/verify?token=test" | head -5
```

## Email Flow

### Email 1: Verificação (após registro)

- **De:** noreply@a4desk.de
- **Para:** email do usuário
- **Template:** Noir+Gold, trilíngue (DE/EN/PT)
- **CTA:** "E-Mail bestätigen →"
- **Validade:** 48 horas
- **Detecção automática:** Human (sem empresa) vs Company (com empresa)

### Email 2: Welcome (após verificação)

- **De:** noreply@a4desk.de
- **Para:** email do usuário
- **Template:** Noir+Gold com WALLET-ID em destaque
- **CTA:** "Zum a4Desk →"
- **Conteúdo:** WALLET-ID + features + link para desktop

## WALLET System

### Tipos

| Tipo | Prefixo | Detecção |
|------|---------|----------|
| Human | `WDI-H-YYYYMMDD-xxxx` | Campo "company" vazio |
| Company | `WDI-C-YYYYMMDD-xxxx` | Campo "company" preenchido |

### Endpoints

| Endpoint | Method | Função |
|----------|--------|--------|
| `/clone/leads` | POST | Captura lead + envia verificação |
| `/clone/verify` | GET | Valida token + cria WALLET |
| `/clone/api/leads/stats` | GET | Estatísticas de registro |
| `/clone/api/wallets` | GET | Lista WALLETs |
| `/clone/api/wallet/{id}` | GET | Detalhes de um WALLET |

## Database

Location: `/opt/windi/data/windi_registration.db`

### Tables

- **leads** — All lead captures (name, email, company, status, wallet_id)
- **verification_tokens** — Secure tokens (48h expiry, one-time use)
- **wallets** — Created WALLETs (human/company, status, virtue_receipts count)
- **email_log** — Audit trail of all emails sent (with SHA-256 hash)

## Email Mapping

| Alias | Usado por | Função |
|-------|-----------|--------|
| noreply@a4desk.de | Registration Pipeline | Verificação + Welcome |
| info@a4desk.de | Landing pages, Impressum | Contato público |
| cgo@a4desk.de | Footer, alerts | Chief Governance Officer |
| governance@a4desk.de | secrets.env | SMTP_FROM institucional |
| support@a4desk.de | BABEL editor | Tickets de suporte |
| security@a4desk.de | Bridge, WSG | Alertas de segurança |
| jober@a4desk.de | WINDI_RECIPIENTS | Recebe relatórios |

## Troubleshooting

| Problema | Causa | Solução |
|----------|-------|---------|
| "verification_sent: false" | SMTP_PASS vazio ou errado | Editar .env, reiniciar |
| Email não chega | Strato SMTP bloqueado | Testar no webmail, verificar porta 465 |
| 502 no /clone/verify | ID Genesis caiu | `ss -tlnp \| grep 8096`, reiniciar |
| Token expired | > 48h entre registro e clique | Registrar novamente |
| WALLET já existe | Email duplicado | Lead já verificado, fazer login |
