---
name: windi-agent-palette
description: >
  Deploy, update, and maintain the WINDI Agent Palette — the constitutional document
  intelligence terminal. Use when the user mentions palette, agent palette, agent suite,
  palette deploy, palette update, palette theme, KLAR, NOIR, constitutional terminal,
  palette UI, or any task involving the Agent Palette on Strato server.
  Also use for: palette version updates, theme changes, UI fixes, SealBadge modifications,
  GovPanel changes, identity text updates, Three Dragons Protocol display changes,
  and palette health checks.
---

# WINDI Agent Palette — Deployment & Maintenance Guide

## Service Overview

| Key | Value |
|-----|-------|
| **Service** | Agent Palette (Constitutional Document Terminal) |
| **Port** | 8108 |
| **Server** | Python3 BaseHTTPServer |
| **Process** | `python3 /opt/windi/agent-palette/agent_palette_server.py` |
| **nginx** | `admin.windia4desk.tech/palette/` → `proxy_pass http://127.0.0.1:8108/` |
| **UI File** | `/opt/windi/agent-palette/ui/index.html` |
| **Current Version** | v0.6.0-K (KLAR Edition) |
| **systemd** | Not yet — runs via nohup |

## File Structure

```
/opt/windi/agent-palette/
├── agent_palette_server.py    # Python HTTP server (reads UI_FILE)
├── index.html                 # NOT used — legacy location
└── ui/
    └── index.html             # ← ACTIVE UI FILE (this is what gets served)
```

**CRITICAL:** The server reads from `ui/index.html`, NOT from root `index.html`.
The server variable is: `UI_FILE = BASE_DIR / "ui" / "index.html"`

## Deploy Procedure (UI Update)

### Step 1: Upload new file to server
User does from local machine:
```bash
scp <local-file.html> windi@87.106.29.233:~/
```

### Step 2: Backup current version
```bash
cp /opt/windi/agent-palette/ui/index.html /opt/windi/agent-palette/ui/index.html.$(date +%Y%m%d_%H%M).bak
```

### Step 3: Deploy
```bash
cp ~/<uploaded-file.html> /opt/windi/agent-palette/ui/index.html
```

### Step 4: Verify (no restart needed — server reads file per request)
```bash
curl -s http://localhost:8108/ | grep -o 'v[0-9].[0-9].[0-9]-[A-Z]'
```

### Step 5: Verify via HTTPS
```bash
curl -s https://admin.windia4desk.tech/palette/ | grep -o 'v[0-9].[0-9].[0-9]-[A-Z]'
```

**NOTE:** No service restart needed. The Python server reads `ui/index.html` fresh on each request.

## Server Management

### Check if running
```bash
ss -tlnp | grep 8108
```

### Find PID
```bash
ps aux | grep palette | grep -v grep
```

### Restart (if needed)
```bash
# Kill existing
kill $(ss -tlnp | grep 8108 | grep -oP 'pid=\K\d+')
sleep 1

# Start fresh
cd /opt/windi/agent-palette
nohup python3 agent_palette_server.py > /dev/null 2>&1 &

# Verify
sleep 1 && ss -tlnp | grep 8108
```

## Theme System (v0.6.0-K)

### Dual Theme: KLAR (default) + NOIR (toggle)

| Property | KLAR (Pergaminho) | NOIR |
|----------|-------------------|------|
| bg | `#F5F0E0` | `#0E0E14` |
| card | `#FDFBF5` | `#16161F` |
| hover | `#EDE8D8` | `#1C1C28` |
| input | `#FDFBF5` | `#12121A` |
| border | `#DDD6C2` | `#26263A` |
| gold | `#8B6914` | `#D4A843` |
| text | `#2C2924` | `#E2E2EA` |
| dim | `#6B6560` | `#7A7A96` |

**Design Principle:** "Governança silenciosa — a proteção está na arquitetura, não na interface."

### IMPORTANT: KLAR bg must NOT be #F8F7F4 (too close to Claude/Anthropic brand).
Current approved color: `#F5F0E0` (Pergaminho/warm parchment).

## Constitutional Architecture (Invisible but Active)

All governance checks run silently — user sees only results:

- **9 Invariants** (I1-I9) — validated on every response via `validateInvariants()`
- **8 Stability Layers** (S1-S8) — active in processing pipeline
- **Layer 7 Communication Semantics** — `applyLayer7()` post-filter
- **SealBadge** — compact "✓ Sealed" badge (replaces verbose Pipeline component)
- **GovPanel** — collapsed by default (🛡️ icon), expandable for experts

## Brand Rules

### NEVER mention third-party AI brand names in the UI:
- ❌ Claude, GPT, Gemini, OpenAI, Anthropic, Google
- ✅ Guardian, Architect, Witness

### Three Dragons Protocol (public-facing):
```
🛡️ Guardian — Protection & Ethics
🏗️ Architect — Structure & Build
👁️ Witness — Observation & Validation
```

### Verification command (must return 0):
```bash
curl -s https://admin.windia4desk.tech/palette/ | grep -c "Claude\|GPT\|Gemini\|OpenAI\|Anthropic"
```

## Smoke Test Checklist

```bash
# 1. Service running?
ss -tlnp | grep 8108

# 2. Correct version?
curl -s http://localhost:8108/ | grep -o 'v[0-9].[0-9].[0-9]-[A-Z]' | head -1

# 3. HTTPS accessible?
curl -s -o /dev/null -w "%{http_code}" https://admin.windia4desk.tech/palette/

# 4. No brand leaks?
curl -s https://admin.windia4desk.tech/palette/ | grep -c "Claude\|GPT\|Gemini"

# 5. Themes present?
curl -s https://admin.windia4desk.tech/palette/ | grep -c "KLAR\|NOIR"

# 6. Constitutional checks present?
curl -s https://admin.windia4desk.tech/palette/ | grep -c "INVARIANTS\|STABILITY_LAYERS\|validateInvariants"
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v0.5.0-C | 2025-02-20 | Constitutional Terminal, I1-I9, S1-S8, L7, NOIR only |
| v0.6.0-K | 2025-02-20 | KLAR theme (default), silent governance, SealBadge, GovPanel collapsed, brand names removed, pergaminho background |

## nginx Config Reference

```nginx
# In /etc/nginx/sites-enabled/admin.windia4desk.tech
location /palette/ {
    proxy_pass http://127.0.0.1:8108/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```
