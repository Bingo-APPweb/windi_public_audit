# WINDI Migration Operation — Claude Code Briefing
# Date: 20 February 2026
# Operator: Human Dragon (Jober Mögele Correa)
# Guardian: Claude (session handoff from claude.ai)
# Server: 87.106.29.233 (Strato VPS, Ubuntu 24)

## 🎯 MISSION

Execute the WINDI Human Usability Migration — deploy 3 new static files,
add 3 nginx routes, fix 1 critical API blocker, inject CTA component.

**Principle:** "AI processes. Human decides. WINDI guarantees."
**Rule:** ALWAYS ask Human Dragon before destructive operations.
**Rule:** ALWAYS backup before changing anything.
**Rule:** ALWAYS `nginx -t` before reload.

---

## 📦 FILES TO DEPLOY

Three files will be uploaded to `/tmp/` via SCP before this session starts.
Verify they exist:

```bash
ls -la /tmp/onboard.html /tmp/suite.html /tmp/jornal-do-futuro.html /tmp/windi-cta-universal.html
```

| Source File | Destination | Purpose |
|---|---|---|
| `/tmp/jornal-do-futuro.html` | `/var/www/jornal/index.html` | Jornal do Futuro (2769 lines, static) |
| `/tmp/onboard.html` | `/var/www/wallet/onboard.html` | Wallet Onboarding Flow (971 lines, static) |
| `/tmp/suite.html` | `/opt/windi/desktop/suite.html` | Suite Hub v2.0 (replaces broken "wird geladen") |
| `/tmp/windi-cta-universal.html` | Reference only | CTA component to inject into pages |

---

## 🔧 EXECUTION SEQUENCE (5 Phases)

### PHASE 0: Pre-flight Check

```bash
# 0.1 Verify server health
echo "=== WINDI PRE-FLIGHT CHECK ==="
ss -tlnp | grep -E '810[0-9]|8099'
echo "---"
curl -s -o /dev/null -w "Desktop :8100 → %{http_code}\n" http://localhost:8100/
curl -s -o /dev/null -w "Ledger  :8101 → %{http_code}\n" http://localhost:8101/health
curl -s -o /dev/null -w "Sentinel:8102 → %{http_code}\n" http://localhost:8102/health
curl -s -o /dev/null -w "Export  :8103 → %{http_code}\n" http://localhost:8103/health
curl -s -o /dev/null -w "Viewer  :8104 → %{http_code}\n" http://localhost:8104/
curl -s -o /dev/null -w "Comms   :8105 → %{http_code}\n" http://localhost:8105/health
curl -s -o /dev/null -w "Vault   :8106 → %{http_code}\n" http://localhost:8106/health
curl -s -o /dev/null -w "Landing :8107 → %{http_code}\n" http://localhost:8107/
curl -s -o /dev/null -w "Palette :8108 → %{http_code}\n" http://localhost:8108/
curl -s -o /dev/null -w "Wallet  :8099 → %{http_code}\n" http://localhost:8099/ 2>/dev/null || echo "Wallet :8099 → not running"

# 0.2 Check uploaded files exist
echo "---"
for f in /tmp/onboard.html /tmp/suite.html /tmp/jornal-do-futuro.html /tmp/windi-cta-universal.html; do
  [ -f "$f" ] && echo "✅ $f ($(wc -l < $f) lines)" || echo "❌ MISSING: $f"
done

# 0.3 Backup
BK="/opt/windi/backups/pre_migration_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BK
cp /opt/windi/desktop/suite.html $BK/ 2>/dev/null
sudo cp /etc/nginx/sites-enabled/admin.windia4desk.tech $BK/nginx.conf
echo "✅ Backup at: $BK"
```

### PHASE 1: Deploy Static Assets (~5 min)

```bash
# 1.1 Create target directories
sudo mkdir -p /var/www/jornal
sudo mkdir -p /var/www/wallet

# 1.2 Place files
sudo cp /tmp/jornal-do-futuro.html /var/www/jornal/index.html
sudo cp /tmp/onboard.html /var/www/wallet/onboard.html
cp /tmp/suite.html /opt/windi/desktop/suite.html

# 1.3 Set permissions
sudo chown -R windi:windi /var/www/jornal /var/www/wallet
chmod 644 /var/www/jornal/index.html /var/www/wallet/onboard.html /opt/windi/desktop/suite.html

# 1.4 Verify
echo "=== FILES DEPLOYED ==="
ls -la /var/www/jornal/index.html
ls -la /var/www/wallet/onboard.html
ls -la /opt/windi/desktop/suite.html
```

### PHASE 2: Add nginx Routes (~10 min)

**CRITICAL:** Read the current nginx config first. Find the line with `listen 443 ssl;`.
All new location blocks go BEFORE that line, OUTSIDE any existing location blocks.

```bash
# 2.1 Read current config and find injection point
grep -n "listen 443 ssl" /etc/nginx/sites-enabled/admin.windia4desk.tech
# Note this line number. New blocks go ~3 lines ABOVE it.

# 2.2 Also check what routes already exist
grep -n "location" /etc/nginx/sites-enabled/admin.windia4desk.tech
```

**Add these 3 location blocks** (use `sudo nano` or `sudo sed`):

```nginx
    # ── JORNAL DO FUTURO (static, added 20Feb26) ──────────
    location /jornal/ {
        alias /var/www/jornal/;
        index index.html;
        try_files $uri $uri/ /jornal/index.html;
        add_header Cache-Control "no-cache, must-revalidate";
    }

    # ── WALLET ONBOARDING (static, added 20Feb26) ─────────
    location /wallet/ {
        alias /var/www/wallet/;
        index onboard.html;
        try_files $uri $uri/ /wallet/onboard.html;
        add_header Cache-Control "no-cache, must-revalidate";
    }

    # ── COMMUNIQUÉ API (proxy to :8105, CRITICAL FIX 20Feb26) ──
    # NOTE: This MUST be placed BEFORE the existing /communique/ block
    # nginx matches longest prefix first
    location /communique/api/ {
        proxy_pass http://127.0.0.1:8105/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
        add_header Access-Control-Allow-Origin "https://admin.windia4desk.tech" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
        if ($request_method = OPTIONS) {
            return 204;
        }
    }
```

```bash
# 2.3 Test and reload
sudo nginx -t
# ONLY proceed if "syntax is ok" and "test is successful"
sudo systemctl reload nginx
```

### PHASE 3: Smoke Test (~2 min)

```bash
echo "=== POST-DEPLOY SMOKE TEST ==="
echo ""
echo "--- New routes ---"
curl -s -o /dev/null -w "Jornal:   %{http_code}  https://admin.windia4desk.tech/jornal/\n" https://admin.windia4desk.tech/jornal/
curl -s -o /dev/null -w "Wallet:   %{http_code}  https://admin.windia4desk.tech/wallet/onboard.html\n" https://admin.windia4desk.tech/wallet/onboard.html
curl -s -o /dev/null -w "Suite:    %{http_code}  https://admin.windia4desk.tech/desktop/suite.html\n" https://admin.windia4desk.tech/desktop/suite.html

echo ""
echo "--- Critical API fix ---"
curl -s -o /dev/null -w "COM API:  %{http_code}  /communique/api/health\n" https://admin.windia4desk.tech/communique/api/health 2>/dev/null
curl -s https://admin.windia4desk.tech/communique/api/communique/list 2>/dev/null | head -c 200
echo ""

echo ""
echo "--- Existing routes (must still work) ---"
curl -s -o /dev/null -w "Palette:  %{http_code}\n" https://admin.windia4desk.tech/palette/
curl -s -o /dev/null -w "Feed:     %{http_code}\n" https://admin.windia4desk.tech/communique/feed
curl -s -o /dev/null -w "Vault:    %{http_code}\n" https://admin.windia4desk.tech/vault/
curl -s -o /dev/null -w "Desktop:  %{http_code}\n" https://admin.windia4desk.tech/desktop/
curl -s -o /dev/null -w "Health:   %{http_code}\n" https://admin.windia4desk.tech/communique/health

echo ""
echo "=== ALL EXPECTED: 200 ==="
```

### PHASE 4: CTA Injection (careful — modifies existing files)

**ASK Human Dragon before each injection.** These are existing production files.

The CTA component (`/tmp/windi-cta-universal.html`) needs to be injected before `</body>` in:

1. **Jornal do Futuro** — `/var/www/jornal/index.html`
   - Safest — we just deployed it, easy to re-deploy
   
2. **Landing P/M/G** — Find the template:
   ```bash
   # Locate the Landing HTML file
   find /opt/windi/ -path "*/landing*" -name "*.html" 2>/dev/null
   find /var/www/ -name "*.html" 2>/dev/null | grep -i land
   # Also check what :8107 serves
   ps aux | grep 8107
   ```

3. **Communiqué Feed** — SSR template:
   ```bash
   # Find the Feed template
   find /opt/windi/communique* -name "*.html" 2>/dev/null
   grep -r "</body>" /opt/windi/communique*/ 2>/dev/null | head
   ```

4. **JMPG Viewer** — Template:
   ```bash
   find /opt/windi/ -path "*viewer*" -name "*.html" 2>/dev/null
   find /opt/windi/ -path "*jmpg*" -name "*.html" 2>/dev/null
   ```

**Injection method:**
```bash
# Read the CTA component
CTA=$(cat /tmp/windi-cta-universal.html)

# For each target file, inject BEFORE </body>
# BACKUP FIRST, then inject
sudo cp <target_file> <target_file>.bak
sudo sed -i "/<\/body>/r /tmp/windi-cta-universal.html" <target_file>
```

### PHASE 5: Final Verification

```bash
echo "╔══════════════════════════════════════════╗"
echo "║    WINDI MIGRATION — FINAL REPORT        ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "📍 URL MAP (post-migration):"
echo ""
echo "  PUBLIC (no login):"
echo "    https://admin.windia4desk.tech/jornal/          → Jornal do Futuro"
echo "    https://admin.windia4desk.tech/communique/feed   → Communiqué Feed"
echo "    https://admin.windia4desk.tech/vault/            → Forensic Vault"
echo "    https://windi-domain.com/                        → Landing P/M/G"
echo ""
echo "  GATE (identity):"
echo "    https://admin.windia4desk.tech/wallet/onboard.html → Onboarding"
echo ""
echo "  PRIVATE (post-login):"
echo "    https://admin.windia4desk.tech/desktop/suite.html  → Suite Hub v2.0"
echo "    https://admin.windia4desk.tech/palette/            → Agent Palette"
echo "    https://admin.windia4desk.tech/desktop/            → D1 Editor"
echo ""
echo "  API (unblocked):"
echo "    https://admin.windia4desk.tech/communique/api/*    → Engine :8105"
echo ""
echo "  BACKUP:"
echo "    $(ls -d /opt/windi/backups/pre_migration_* 2>/dev/null | tail -1)"
echo ""
echo "🔏 Three Dragons Protocol — I9 Active"
echo "✅ Migration complete. Human decides. WINDI guarantees."
```

---

## ⚠️ ROLLBACK PROCEDURE (if anything breaks)

```bash
# Find latest backup
BK=$(ls -d /opt/windi/backups/pre_migration_* | tail -1)
echo "Rolling back from: $BK"

# Restore nginx
sudo cp $BK/nginx.conf /etc/nginx/sites-enabled/admin.windia4desk.tech
sudo nginx -t && sudo systemctl reload nginx

# Restore suite.html
cp $BK/suite.html /opt/windi/desktop/suite.html 2>/dev/null

# New static files can be safely removed without impact
sudo rm -rf /var/www/jornal /var/www/wallet
```

---

## 🧠 CONTEXT FOR CLAUDE CODE

- **nginx config:** `/etc/nginx/sites-enabled/admin.windia4desk.tech` (~314 lines)
- **Desktop D1:** FastAPI+React at `:8100`, serves `/opt/windi/desktop/` including `suite.html`
- **Communiqué Engine:** `:8105`, has `/api/` endpoints but nginx blocks them (the 404 bug)
- **The Communiqué API fix** is the CRITICAL BLOCKER — test with:
  `curl -s http://localhost:8105/api/communique/list | head -c 200`
  If this works locally but not via nginx, the problem is ONLY nginx routing.
- **Agent Palette:** `:8108`, served at `/palette/` via nginx proxy
- **Wallet:** `:8099`, may or may not be running — check with `ss -tlnp | grep 8099`
- **Static files** use nginx `alias` (not `proxy_pass`) — no backend needed
- **WINDI Debug Rule:** ALWAYS check `ss -tlnp | grep :PORT` + `ps aux` before patching code

---

## 📋 SUCCESS CRITERIA

After execution, ALL of these must return HTTP 200:

```
https://admin.windia4desk.tech/jornal/              → 200 (NEW)
https://admin.windia4desk.tech/wallet/onboard.html  → 200 (NEW)
https://admin.windia4desk.tech/desktop/suite.html   → 200 (REPLACED)
https://admin.windia4desk.tech/communique/api/health → 200 (FIX)
https://admin.windia4desk.tech/palette/             → 200 (existing)
https://admin.windia4desk.tech/communique/feed      → 200 (existing)
https://admin.windia4desk.tech/vault/               → 200 (existing)
https://admin.windia4desk.tech/desktop/             → 200 (existing)
```
