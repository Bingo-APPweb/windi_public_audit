# INFRASTRUCTURE-PROVENANCE-001 — O Mapa Suíço

```yaml
doc_type:        infrastructure_map
gate_id:         INFRASTRUCTURE-PROVENANCE-001
status:          ACTIVE
priority:        P0
created:         2026-06-18
author:          CODEX + Human Dragon
purpose:         O sistema deve explicar-se a si mesmo
invariants:      I1, I9, I11, I14
```

---

## PRINCÍPIO FUNDADOR

> **"Se o servidor sofrer um apagão e o sistema não voltar sozinho, o valuation cai a zero."**
> — Human Dragon, 18 Jun 2026

Este documento é a memória institucional do WINDI Proofmail. Qualquer engenheiro, auditor ou investidor deve conseguir reconstruir o sistema apenas lendo este ficheiro.

---

## 1. ARQUITECTURA DO DUTO FORENSE

```
┌─────────────────────────────────────────────────────────────────┐
│                        STRATO VPS                               │
│                    87.106.29.233                                │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ W-SITES-001 (:8192)                                     │   │
│  │ /opt/windi/windi-sites/identity-gate/                   │   │
│  │ systemd: windi-sites.service                            │   │
│  │ Função: Identity Gate + Email Trigger                   │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                         │ POST /api/verify-email/{id}          │
│                         ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ W-MAIL-001 (Docker: windi-mailserver)                   │   │
│  │ Portas: :25, :587, :465, :993, :8895                    │   │
│  │ /opt/windi/w-mail-001/                                  │   │
│  │                                                         │   │
│  │   ┌─────────────────────────────────────────────────┐   │   │
│  │   │ DACP Milter (:8890 interno)                     │   │   │
│  │   │ /tmp/docker-mailserver/dacp-milter/             │   │   │
│  │   │ supervisord: [program:dacp-milter]              │   │   │
│  │   │ Wrapper: start-milter.sh                        │   │   │
│  │   │ Função: Intercept + Hash + Seal                 │   │   │
│  │   └──────────────────────┬──────────────────────────┘   │   │
│  └──────────────────────────┼──────────────────────────────┘   │
│                             │ POST /api/receipts               │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Forensic Ledger (:8101)                                 │   │
│  │ /opt/windi/forensic-ledger/                             │   │
│  │ systemd: windi-ledger.service                           │   │
│  │ DB: /opt/windi/data/forensic_ledger.sqlite3             │   │
│  │ Função: Immutable Receipt Storage                       │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │ GET /api/receipts/{id}           │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Verify Public (:8114)                                   │   │
│  │ /opt/windi/verify-public/                               │   │
│  │ systemd: windi-verify-public.service                    │   │
│  │ Função: Public Verification Interface                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. INVENTÁRIO DE SERVIÇOS

### 2.1 Serviços systemd (Host)

| Serviço | Porta | Caminho | Estado |
|---------|-------|---------|--------|
| `windi-sites.service` | :8192 | `/opt/windi/windi-sites/identity-gate/` | enabled |
| `windi-ledger.service` | :8101 | `/opt/windi/forensic-ledger/` | enabled |
| `windi-verify-public.service` | :8114 | `/opt/windi/verify-public/` | enabled |

### 2.2 Serviços Docker

| Container | Portas | Compose | Estado |
|-----------|--------|---------|--------|
| `windi-mailserver` | :25,:587,:465,:993,:8895 | `/opt/windi/w-mail-001/docker-compose.yml` | restart: unless-stopped |
| `windi-snappymail` | :8888 | `/opt/windi/w-mail-001/docker-compose.yml` | restart: unless-stopped |

### 2.3 Supervisord (Dentro do Container)

| Programa | Porta Interna | Config | Estado |
|----------|---------------|--------|--------|
| `dacp-milter` | :8890 | `/etc/supervisor/conf.d/dacp-milter.conf` | autostart=true |

---

## 3. FICHEIROS CRÍTICOS

### 3.1 W-SITES-001

```
/opt/windi/windi-sites/identity-gate/
├── identity_gate.py          # Main application
├── requirements.txt          # Dependencies
└── .env                      # SMTP credentials (NOT in git)
```

**Variáveis de ambiente críticas:**
- `SMTP_HOST`: mail.windisites.de
- `SMTP_PORT`: 587
- `SMTP_USER`: noreply@windisites.de
- `SMTP_PASS`: [SEALED]
- `LEDGER_URL`: http://localhost:8101

### 3.2 W-MAIL-001

```
/opt/windi/w-mail-001/
├── docker-compose.yml                    # Container orchestration
├── config/
│   ├── user-patches.sh                   # Startup script (installs pymilter)
│   ├── supervisor/
│   │   └── dacp-milter.conf              # Supervisor config (MOUNTED)
│   ├── dacp-milter/
│   │   ├── dacp_milter.py                # Main milter
│   │   ├── ledger_client.py              # Ledger integration
│   │   ├── start-milter.sh               # Wrapper (waits for pymilter)
│   │   └── *.py                          # Supporting modules
│   └── opendkim/keys/windisites.de/
│       ├── rsa.txt                       # DKIM public key
│       └── rsa.private                   # DKIM private key
├── mail-data/                            # Mailboxes
├── mail-state/                           # Persistent state
└── mail-logs/                            # Container logs
```

**Volume Mounts (docker-compose.yml):**
```yaml
volumes:
  - ./mail-data/:/var/mail/
  - ./mail-state/:/var/mail-state/
  - ./mail-logs/:/var/log/mail/
  - ./config/:/tmp/docker-mailserver/
  - ./config/supervisor/dacp-milter.conf:/etc/supervisor/conf.d/dacp-milter.conf:ro
  - /etc/letsencrypt:/etc/letsencrypt:ro
```

### 3.3 Forensic Ledger

```
/opt/windi/forensic-ledger/
├── app/
│   └── main.py                           # API server
├── requirements.txt
└── .env

/opt/windi/data/
└── forensic_ledger.sqlite3               # THE DATABASE (CRITICAL)
```

### 3.4 Verify Public

```
/opt/windi/verify-public/
├── app/
│   ├── main.py                           # API server
│   └── verify_engine.py                  # Verification logic
└── requirements.txt
```

---

## 4. ORDEM DE ARRANQUE

A ordem correcta após reboot do servidor:

```
1. systemd basic.target
   │
2. docker.service
   │
3. windi-ledger.service        # PRIMEIRO - outros dependem dele
   │
4. windi-mailserver (docker)   # SEGUNDO - depende do Ledger
   │   └── supervisord
   │       └── dacp-milter     # Arranca via wrapper após pymilter instalado
   │
5. windi-sites.service         # TERCEIRO - depende do Mail
   │
6. windi-verify-public.service # ÚLTIMO - apenas leitura
```

**Dependências nos ficheiros systemd:**

```ini
# windi-ledger.service
[Unit]
After=network.target

# windi-sites.service
[Unit]
After=network.target docker.service

# windi-verify-public.service
[Unit]
After=network.target windi-ledger.service
```

---

## 5. HASHES DOS FICHEIROS CRÍTICOS

**Data:** 2026-06-18

| Ficheiro | SHA256 |
|----------|--------|
| `dacp_milter.py` | `1617f4f59adc276171cb75e910716ee5453982ef4bbff0d1e6e275017f042c9b` |
| `ledger_client.py` | `59eb486561dd7e8e75f1effed3bd7ea817e10d20b80e3ea02c5f5b9a99ddfe43` |
| `identity_gate.py` | `f9b99e2a68272dde2dd520d69881370f8cdaa8fee31bc24f817e2d46fa95242c` |
| `start-milter.sh` | (novo - calcular) |
| `dacp-milter.conf` | (novo - calcular) |

---

## 6. FIXES APLICADOS HOJE (2026-06-18)

### Fix 1: DACP Survivability Hardening

**Problema:** Milter não sobrevivia a restart do container.

**Solução:**
1. Criado `config/supervisor/dacp-milter.conf` — supervisor config
2. Criado `config/dacp-milter/start-milter.sh` — wrapper que espera pymilter
3. Modificado `docker-compose.yml` — mount do supervisor config
4. Modificado `config/user-patches.sh` — delega arranque ao supervisor

**Gate:** `DACP-SURVIVABILITY-HARDENING-001` → PASS

### Fix 2: Ledger Client URL

**Problema:** Milter usava URL incorrecta para o Ledger.

**Solução:** `ledger_client.py` actualizado para usar `https://windi-domain.com` (proxy nginx).

---

## 7. COMANDOS DE DIAGNÓSTICO

```bash
# Estado geral
systemctl status windi-ledger windi-sites windi-verify-public
docker ps --filter "name=windi"

# Portas activas
ss -tlnp | grep -E ':(8101|8114|8192|25|587|993|8895)'

# Milter no container
docker exec windi-mailserver supervisorctl status dacp-milter
docker exec windi-mailserver ss -tlnp | grep 8890

# Health checks
curl -s http://localhost:8101/health | jq .status
curl -s http://localhost:8114/health | jq .status
curl -s http://localhost:8192/health | jq .status
docker exec windi-mailserver curl -s http://localhost:8895/health | jq .status

# Teste de duto completo
/opt/windi/w-mail-001/scripts/test-proofmail.sh
```

---

## 8. BACKUPS CRÍTICOS

| O Quê | Localização | Frequência |
|-------|-------------|------------|
| Ledger DB | `/opt/windi/data/forensic_ledger.sqlite3` | Diário (cron) |
| DKIM Keys | `/opt/windi/w-mail-001/config/opendkim/keys/` | Manual |
| Mail Data | `/opt/windi/w-mail-001/mail-data/` | Diário (cron) |
| Certificates | `/etc/letsencrypt/` | Auto-renovação |

---

## 9. CONTACTOS DE EMERGÊNCIA

| Função | Contacto |
|--------|----------|
| **I1 Decisor** | Human Dragon (Jober Mögele Correa) |
| **Infra** | CODEX (CCode CLI) |
| **Hosting** | Strato VPS (87.106.29.233) |

---

## 10. FRASE DE GUARDA

> **"O WINDI deve explicar-se a si mesmo. Este documento é essa explicação."**

---

*Liga IA+H · INFRASTRUCTURE-PROVENANCE-001 · 18 Jun 2026*
