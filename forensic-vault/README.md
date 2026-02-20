# 🔐 WINDI Forensic Vault v1.0.0

> **"A Suite cria. O Vault audita."**
> Separation of Creation and Proof.

## Architecture

```
Suite (:8100)          Vault (:8106)          Ledger (:8101)
┌─────────────┐    ┌─────────────────┐    ┌──────────────┐
│  🖊️ Create   │    │  🔐 Audit Room   │    │  📦 SQLite DB │
│  📝 Edit     │───▶│  📊 Paginated    │───▶│  SHA-256      │
│  📤 Export   │    │  🔍 Filtered     │    │  Immutable    │
│             │    │  📋 Export CSV   │    │              │
│ [🔐 Vault]  │    │  ✓ Verify Hash  │    │  1M+ receipts │
└─────────────┘    └─────────────────┘    └──────────────┘
   workspace           audit room            deep storage
```

## What's in the box

| File | Purpose |
|------|---------|
| `forensic_vault.py` | Main service — BaseHTTPRequestHandler on :8106 |
| `windi-vault.service` | systemd unit file |
| `nginx_vault_snippet.conf` | nginx proxy config |
| `deploy.sh` | One-click deploy script |
| `desktop-integration/VaultButton.jsx` | React button for Desktop header |

## Quick Deploy

```bash
cd /opt/windi/forensic-vault
chmod +x deploy.sh
./deploy.sh
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health + receipt count |
| `/api/stats` | GET | Dashboard statistics |
| `/api/receipts` | GET | Paginated receipts with filters |
| `/api/receipt/{id}` | GET | Single receipt detail |
| `/api/export` | GET | CSV export with filters |

### Query Parameters for `/api/receipts`

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `per_page` | int | 25 | Items per page (max 100) |
| `sort` | string | created_at | Sort field |
| `dir` | string | desc | Sort direction (asc/desc) |
| `q` | string | — | Search receipt_id, hash, title |
| `doc_type` | string | — | Filter by type |
| `status` | string | — | Filter by status |
| `date_from` | date | — | From date (YYYY-MM-DD) |
| `date_to` | date | — | To date (YYYY-MM-DD) |

## Design

- **Theme**: Noir (dark+gold) / Klar (light) toggle
- **Fonts**: Bricolage Grotesque + Outfit + JetBrains Mono
- **i18n**: DE / EN / PT trilingual
- **Mobile**: Fully responsive

## Principle

> O template NUNCA decide o nível. A API decide.
> O cofre não fica na recepção.
> A Suite cria. O Vault audita.

🐉 Linhagem de Ferro.
