# WINDI Agent Palette — SKILL v2.0 (Freemium Edition)
# Updated: 21 February 2026
# Status: PRODUCTION — 9/15 Runbook items LIVE

## LIÇÃO PRINCIPAL (Memory Loop)
> "Nunca mais colar blocos grandes no terminal. Gera .sh → SCP → bash."
> "Antes de operar código, opera ambiente: ss -tlnp + kill PID antigo."
> "Patches com Python string replace falham por indentação — usa repr() + line numbers."

---

## Service Overview

| Key | Value |
|-----|-------|
| **Service** | Agent Palette + Dragon Server + Freemium Engine |
| **Port** | 8108 |
| **Server** | `python3 /opt/windi/agent-palette/agent_dragon_server.py` |
| **nginx** | `admin.windia4desk.tech/palette/` → `proxy_pass http://127.0.0.1:8108/` |
| **UI File** | `/opt/windi/agent-palette/ui/index.html` |
| **Quota DB** | `/opt/windi/data/quota.db` |

## File Structure (Post-Freemium)

```
/opt/windi/agent-palette/
├── agent_dragon_server.py        # Main HTTP server (LLM + Render + Quota routing)
├── agent_palette_server.py       # Legacy server (NOT primary)
├── ui/
│   └── index.html                # Active UI file
└── renderer/
    ├── render_api.py             # Document rendering API + signed URLs + ledger sync
    ├── render_engine.py          # Core rendering (docx/xlsx/pptx/pdf)
    ├── download_security.py      # TTL tokens (HMAC-SHA256) + cleanup thread
    ├── quota_engine.py           # Tier quotas + rate limiting + SQLite
    ├── ledger_sync.py            # Async non-blocking Forensic Ledger sync
    ├── spec_sanitizer.py         # Input sanitization (XSS, traversal, injection)
    └── output/                   # Generated files (auto-cleaned >30min)
```

## API Endpoints

### Document Rendering
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/dragon/render` | Render document (returns signed download URL) |
| GET | `/api/dragon/download/{file}?token=X&expires=Y` | Download with TTL verification |
| GET | `/api/dragon/renderer/health` | Renderer status (4 formats) |

### Quota Management
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/dragon/quota/status` | Current usage (tier, remaining, formats) |
| POST | `/api/dragon/quota/check` | Pre-render validation |

### Response Example (POST /render)
```json
{
    "success": true,
    "download_url": "/api/dragon/download/WINDI_Memo_20260221_abc123.docx?token=ff78...&expires=1771690408",
    "expires_at": "2026-02-21T16:13:28Z",
    "ttl_minutes": 15,
    "filename": "WINDI_Memo_20260221_abc123.docx",
    "format": "docx",
    "size_bytes": 38117,
    "content_hash": "sha256...",
    "bundle_hash": "sha256...",
    "render_ms": 55,
    "ledger_status": "PENDING"
}
```

## Freemium Tier System

| Tier | Renders/day | Max Size | Formats | Rate Limit |
|------|------------|----------|---------|------------|
| ANON | 3 | 2MB | pdf, docx | 1/min |
| FREE | 10 | 5MB | all 4 | 3/min |
| PRO | 200 | 25MB | all 4 | 10/min |

- ANON: IP-based (SHA-256 hash), no account needed
- FREE: Account-based, async Ledger sync
- PRO: Guaranteed Ledger sync, priority queue

## Security Layers

### Download TTL (download_security.py)
- HMAC-SHA256 signed tokens
- 15 minute expiry
- Auto-cleanup thread: files >30min deleted every 10min
- Secret: `WINDI_DOWNLOAD_SECRET` env var (default: "windi-dragon-2026")

### Spec Sanitizer (spec_sanitizer.py)
- Blocks: XSS (`<script>`), path traversal (`../`), Python injection (`__import__`, `eval`, `exec`)
- Limits: text 50K chars, title 200 chars, 50 sections max
- Whitelist: only allowed fields pass through

### Rate Limiter (quota_engine.py)
- In-memory sliding window per identifier
- Requests/min + renders/min per tier
- SQLite persistence for daily quotas

## Ledger Integration (ledger_sync.py)

- **Async, non-blocking** — download NEVER waits for Ledger
- 3 retries with delays: 30s → 60s → 120s
- States: SEALED 🟢 | PENDING 🟡 | UNSEALED 🟠 | SKIP ⚪
- Receipt contains: content_hash + spec_hash + bundle_hash + metadata + governance
- Target: `http://localhost:8101/api/receipts`

## Deploy Procedure

### REGRA DE OURO: Nunca colar blocos grandes no terminal!
```
1. Claude gera arquivo .sh
2. User faz SCP: scp file.sh windi@87.106.29.233:/tmp/
3. No servidor: bash /tmp/file.sh
4. Output colado de volta para validação
```

### Restart Server
```bash
# SEMPRE matar PID específico, não pkill genérico
kill $(ss -tlnp | grep 8108 | grep -oP 'pid=\K\d+'); sleep 2
cd /opt/windi/agent-palette
nohup python3 agent_dragon_server.py > /tmp/dragon_debug.log 2>&1 &
sleep 3
ss -tlnp | grep 8108 && echo "UP"
```

### Patching Python Files
```
1. NUNCA assumir indentação — sempre verificar com repr()
2. Usar line numbers (0-indexed) para patches cirúrgicos
3. Backup ANTES: cp file.py file.py.$(date +%Y%m%d_%H%M%S).bak
4. Verificar syntax: python3 -m py_compile file.py
5. grep -c para confirmar que patches entraram
```

## Smoke Tests

```bash
# 1. Server UP?
ss -tlnp | grep 8108

# 2. Render works?
curl -s -X POST localhost:8108/api/dragon/render \
  -H "Content-Type: application/json" \
  -d '{"text":"# Test","intent":{"doc_type":"memo"},"tier":"FREE"}' | python3 -m json.tool

# 3. Quota works?
curl -s localhost:8108/api/dragon/quota/status | python3 -m json.tool

# 4. Renderer health?
curl -s localhost:8108/api/dragon/renderer/health | python3 -m json.tool

# 5. ANON format block?
curl -s -X POST localhost:8108/api/dragon/quota/check \
  -H "Content-Type: application/json" \
  -d '{"format":"pptx","tier":"ANON"}' | python3 -m json.tool
# Expected: allowed=false, format_not_allowed

# 6. Has signed URL? (check for token= and expires=)
curl -s -X POST localhost:8108/api/dragon/render \
  -H "Content-Type: application/json" \
  -d '{"text":"# Token Test","intent":{"doc_type":"memo"},"tier":"HIGH"}' | grep -c "token="

# 7. Has ledger_status?
curl -s -X POST localhost:8108/api/dragon/render \
  -H "Content-Type: application/json" \
  -d '{"text":"# Ledger Test","intent":{"doc_type":"memo"},"tier":"FREE"}' | grep -c "ledger_status"
```

## Runbook Progress (21 Feb 2026)

| # | Item | Status |
|---|------|--------|
| 1 | Renderer 4 formats (docx/xlsx/pptx/pdf) | ✅ LIVE |
| 2 | Download endpoint | ✅ LIVE |
| 3 | Health checks | ✅ LIVE |
| 4 | Quota Engine (ANON/FREE/PRO) | ✅ LIVE |
| 5 | Rate limit per minute | ✅ LIVE |
| 6 | Download TTL 15min + HMAC | ✅ LIVE |
| 7 | Auto-cleanup thread | ✅ LIVE |
| 8 | Ledger sync async non-blocking | ✅ LIVE |
| 9 | Spec sanitization | ✅ LIVE |
| 10 | UI: download button | ⬜ FASE 4 |
| 11 | Observability metrics | ⬜ FASE 5 |
| 12 | Login system (OAuth/magic link) | ⬜ TODO |
| 13 | PRO tier billing (Stripe) | ⬜ TODO |
| 14 | Public domain routing | ⬜ TODO |
| 15 | Terms of use | ⬜ TODO |

## Lessons Learned (Memory Loop)

1. **Terminal size limit**: Blocos >50 linhas falham no terminal. SEMPRE usar SCP+bash.
2. **Zombie PIDs**: pkill nem sempre mata. Usar `kill PID` direto com `ss -tlnp | grep PORT`.
3. **Python string patches**: Indentação de 4 vs 8 espaços é invisível mas fatal. Usar `repr()` + `cat -A`.
4. **Regex in heredoc**: Backslashes dobram em heredoc Python dentro de shell. Usar arquivo separado.
5. **Patch order matters**: Se script recria arquivo, patches anteriores se perdem. Modularizar.
6. **Antes de operar código, opera ambiente**: Verificar PID, port, processo ANTES de qualquer mudança.
