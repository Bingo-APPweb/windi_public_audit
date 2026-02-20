# 🐉 WINDI Ecosystem — Organizational Map & Deployment Plan
# Updated: 18 Feb 2026

## 🌐 Domain Architecture

```
windi-domain.com                     admin.windia4desk.tech
┌────────────────────────┐           ┌──────────────────────────────┐
│  /              → LANDING PAGE     │  /         → A4 Desk Landing │
│                   P/M/G Triagem    │               (:8086)        │
│                   ★ NEW ★          │                              │
│                                    │  /desktop/ → D1 Desktop     │
│  /personal/     → WINDI Personal   │               (:8100)        │
│                   ★ FUTURE ★       │                              │
│                                    │  /communique/ → Engine       │
│  /governance    → Dashboard G      │               (:8105)        │
│                   (já existe)      │                              │
│                                    │  /vault/   → Forensic Vault │
│  /governance/hub → Agent Hub       │               (:8106) ★ NEW ★│
│                                    │                              │
│  /vault/        → Forensic Vault   │  /war-room/ → War Room      │
│                   (:8106) ★ NEW ★  │               (:8090)        │
│                                    │                              │
│  /static/       → Audit dashboards │  /bridge/  → Command Bridge │
│                                    │               (:8097)        │
│  /records/      → Depositions      │                              │
│                                    │  /clone/   → Clone UI       │
│                                    │               (:8092)        │
└────────────────────────────────────┘──────────────────────────────┘
                    ↕ Same server: 87.106.29.233 ↕
```

## 🏗️ Port Map (Complete — Feb 2026)

| Port | Service | Status | Tier |
|------|---------|--------|------|
| 8080 | Governance API | ✅ | G |
| 8081 | Trust Bus | ✅ | G |
| 8083 | SGE Engine | ✅ | G |
| 8085 | A4 Desk BABEL | ✅ | M/G |
| 8086 | A4 Desk Landing | ✅ | ALL |
| 8089 | Cortex | ✅ | G |
| 8090 | War Room | ✅ | G |
| 8092 | Clone UI | ✅ | G |
| 8094 | Forensic API | ✅ | G |
| 8097 | Command Bridge | ✅ | G |
| 8098 | Sentinel | ✅ | G |
| 8099 | Wallet | ✅ | ALL |
| 8100 | Desktop D1 | ✅ | ALL |
| 8101 | Forensic Ledger | ✅ | ALL |
| 8102 | Sentinel LAW | ✅ | G |
| 8103 | Export Engine M3 | ✅ | ALL |
| 8104 | JMPG Viewer | ✅ | ALL |
| 8105 | Communiqué Engine | ✅ | M/G |
| 8106 | Forensic Vault | ★ NEW | M/G |
| 8107 | Landing P/M/G | ★ NEW | ALL |

## 📁 File Organization on Server

```
/opt/windi/
├── landing-pmg/           ★ NEW — P/M/G landing page
│   ├── landing_server.py  ★ Port 8107
│   └── static/
│       └── index.html     ★ The landing page
│
├── forensic-vault/        ★ NEW — Audit room
│   ├── forensic_vault.py  ★ Port 8106
│   └── ...
│
├── desktop/               Desktop D1 (:8100)
├── a4desk-editor/         BABEL (:8085)
├── a4desk-landing/        Landing (:8086)
├── engine/                Core governance
├── data/                  SQLite DBs
│   └── forensic_ledger.db
├── war-room/              War Room (:8090)
├── bridge/                Command Bridge (:8097)
├── clone/                 Clone (:8092)
├── isp/                   ISP Profiles (17)
├── logs/                  Centralized logs
├── backups/               Pre-change backups
└── docs/                  Architecture docs
```

## 🔐 Nginx Config Required (windi-domain.com)

```nginx
# ROOT — P/M/G Landing (NEW)
location / {
    proxy_pass http://127.0.0.1:8107/;
    # ...standard proxy headers...
}

# VAULT (NEW)
location /vault/ {
    proxy_pass http://127.0.0.1:8106/;
    # ...standard proxy headers + CORS...
}

# GOVERNANCE (existing — preserve)
location /governance { ... }

# STATIC (existing — preserve)
location /static/ { ... }

# RECORDS (existing — preserve)
location /records/ { ... }
```

## ⚠️ IMPORTANT: Current Root

Whatever currently serves `windi-domain.com/` needs to be:
1. IDENTIFIED (check nginx: `grep -A5 'location / ' /etc/nginx/sites-enabled/*windi*`)
2. BACKED UP
3. Either MOVED to a sub-path or REPLACED by the new landing

## 📋 Deployment Order

```
STEP 1: BACKUP
  □ cp nginx config
  □ cp current root HTML/service
  □ snapshot databases

STEP 2: DEPLOY VAULT (:8106)
  □ mkdir /opt/windi/forensic-vault
  □ deploy files
  □ systemd enable + start
  □ nginx proxy /vault/
  □ smoke test

STEP 3: DEPLOY LANDING (:8107)
  □ mkdir /opt/windi/landing-pmg
  □ deploy files
  □ systemd enable + start
  □ nginx: move current root to /old/ or /legacy/
  □ nginx: set / → :8107
  □ smoke test

STEP 4: INCISIONS (governance dashboard)
  □ sidebar link
  □ agent constellation card
  □ health check row

STEP 5: VERIFY ALL
  □ windi-domain.com → landing P/M/G
  □ windi-domain.com/governance → dashboard (unchanged)
  □ windi-domain.com/vault/ → Forensic Vault
  □ admin.windia4desk.tech/vault/ → Forensic Vault
  □ admin.windia4desk.tech/desktop/ → Desktop D1
```
