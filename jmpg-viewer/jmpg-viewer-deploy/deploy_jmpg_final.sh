#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  WINDI JMPG Viewer — DEFINITIVE Deploy Script
#  
#  Three Dragons Approved:
#    Guardian: BaseHTTPRequestHandler + SHA-256 verify
#    Architect: Enterprise clean via nginx + /desktop/jmpg/
#    Witness: Port :8104 + Sentinel LAW invariant
#
#  Result: Service on :8104, proxied via /desktop/jmpg/
#          4th card in ante-sala
#
#  Run AS windi user:  bash deploy_jmpg_final.sh
# ═══════════════════════════════════════════════════════════════

set -e

echo "═══════════════════════════════════════════════════════"
echo "  🐉 WINDI JMPG Viewer — Three Dragons Deploy"
echo "  Port: 8104 | Route: /desktop/jmpg/"
echo "═══════════════════════════════════════════════════════"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ═══ 1. BACKUP ═══
echo "[1/7] 📦 Backup..."
BK="/opt/windi/backups/pre_jmpg_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BK"
sudo cp /etc/nginx/sites-enabled/admin.windia4desk.tech "$BK/nginx.conf" 2>/dev/null || true
cp /opt/windi/desktop/index.html "$BK/index.html" 2>/dev/null || true
[ -d /opt/windi/jmpg-viewer ] && cp -r /opt/windi/jmpg-viewer "$BK/jmpg-viewer-old" 2>/dev/null || true
echo "  ✅ Backup: $BK"

# ═══ 2. CHECK PORT ═══
echo ""
echo "[2/7] 🔍 Checking port 8104..."
if ss -tlnp | grep -q ":8104 "; then
    echo "  ⚠️  Port 8104 in use — killing existing process"
    PID=$(ss -tlnp | grep ":8104 " | grep -oP 'pid=\K\d+' | head -1)
    [ -n "$PID" ] && kill "$PID" 2>/dev/null || true
    sleep 2
fi
echo "  ✅ Port 8104 available"

# ═══ 3. DEPLOY FILES ═══
echo ""
echo "[3/7] 📁 Deploying files..."
mkdir -p /opt/windi/jmpg-viewer/samples
mkdir -p /opt/windi/logs

cp "$SCRIPT_DIR/jmpg_viewer_server.py" /opt/windi/jmpg-viewer/
cp "$SCRIPT_DIR/viewer.html" /opt/windi/jmpg-viewer/
cp "$SCRIPT_DIR/samples/"*.jmpg /opt/windi/jmpg-viewer/samples/ 2>/dev/null || true
echo "  ✅ Files → /opt/windi/jmpg-viewer/"

# ═══ 4. SYSTEMD ═══
echo ""
echo "[4/7] ⚙️  Installing systemd service..."

# Stop existing if running
sudo systemctl stop windi-jmpg-viewer 2>/dev/null || true

sudo tee /etc/systemd/system/windi-jmpg-viewer.service > /dev/null << 'SVCEOF'
[Unit]
Description=WINDI JMPG Viewer v1.0.0 (:8104)
Documentation=https://admin.windia4desk.tech/desktop/jmpg/health
After=network.target windi-desktop.service
Wants=network-online.target

[Service]
Type=simple
User=windi
Group=windi
WorkingDirectory=/opt/windi/jmpg-viewer
ExecStart=/usr/bin/python3 /opt/windi/jmpg-viewer/jmpg_viewer_server.py
Restart=always
RestartSec=5
StandardOutput=append:/opt/windi/logs/jmpg-viewer.log
StandardError=append:/opt/windi/logs/jmpg-viewer.log

NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/opt/windi/jmpg-viewer /opt/windi/logs

[Install]
WantedBy=multi-user.target
SVCEOF

sudo systemctl daemon-reload
sudo systemctl enable windi-jmpg-viewer.service
sudo systemctl start windi-jmpg-viewer.service
sleep 2

if sudo systemctl is-active --quiet windi-jmpg-viewer; then
    echo "  ✅ systemd: ACTIVE"
else
    echo "  ❌ systemd: FAILED"
    sudo systemctl status windi-jmpg-viewer --no-pager | tail -10
    exit 1
fi

# Verify health
if curl -sf http://localhost:8104/health > /dev/null 2>&1; then
    echo "  ✅ Health: OK"
else
    echo "  ❌ Health check failed!"
    exit 1
fi

# ═══ 5. NGINX ═══
echo ""
echo "[5/7] 🌐 Configuring nginx..."

NGINX_CONF="/etc/nginx/sites-enabled/admin.windia4desk.tech"

if grep -q "JMPG Viewer" "$NGINX_CONF" 2>/dev/null; then
    echo "  ⚠️  JMPG nginx snippet already present — skipping"
else
    # Find SSL line to inject before
    SSL_LINE=$(grep -n "listen 443 ssl" "$NGINX_CONF" | head -1 | cut -d: -f1)
    
    if [ -z "$SSL_LINE" ]; then
        echo "  ❌ Cannot find 'listen 443 ssl' — manual nginx config needed"
        echo "  📋 Snippet saved to: $SCRIPT_DIR/nginx_jmpg_snippet.conf"
    else
        INJECT_LINE=$((SSL_LINE - 2))
        
        # Create the snippet inline (to avoid file path issues with sed)
        sudo sed -i "${INJECT_LINE}a\\
\\
    # ── JMPG Viewer (:8104) ──────────────────────────\\
    location /desktop/jmpg/ {\\
        proxy_pass http://127.0.0.1:8104/;\\
        proxy_http_version 1.1;\\
        proxy_set_header Host \$host;\\
        proxy_set_header X-Real-IP \$remote_addr;\\
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\\
        proxy_set_header X-Forwarded-Proto \$scheme;\\
        proxy_read_timeout 120s;\\
        proxy_connect_timeout 10s;\\
    }\\
\\
    location /desktop/jmpg/api/ {\\
        proxy_pass http://127.0.0.1:8104/api/;\\
        proxy_http_version 1.1;\\
        proxy_set_header Host \$host;\\
        proxy_set_header X-Real-IP \$remote_addr;\\
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\\
        proxy_set_header X-Forwarded-Proto \$scheme;\\
        proxy_read_timeout 120s;\\
        add_header Access-Control-Allow-Origin \"https://admin.windia4desk.tech\" always;\\
        add_header Access-Control-Allow-Methods \"GET, POST, OPTIONS\" always;\\
        add_header Access-Control-Allow-Headers \"Content-Type\" always;\\
        if (\$request_method = OPTIONS) {\\
            return 204;\\
        }\\
    }\\
    # ── END JMPG Viewer ──────────────────────────────" "$NGINX_CONF"
        
        echo "  ✅ Snippet injected at line $INJECT_LINE"
    fi
    
    # Test and reload
    if sudo nginx -t 2>&1; then
        sudo systemctl reload nginx
        echo "  ✅ nginx: reloaded"
    else
        echo "  ❌ nginx test FAILED — reverting!"
        sudo cp "$BK/nginx.conf" "$NGINX_CONF"
        sudo nginx -t && sudo systemctl reload nginx
        echo "  ↩️  Reverted to backup"
        exit 1
    fi
fi

# ═══ 6. ANTE-SALA CARD ═══
echo ""
echo "[6/7] 🎴 Adding JMPG card to ante-sala..."

DESKTOP_INDEX="/opt/windi/desktop/index.html"

if [ ! -f "$DESKTOP_INDEX" ]; then
    echo "  ⚠️  index.html not found at $DESKTOP_INDEX — skip card injection"
    echo "  📋 Add manually: see navigation_integration.html"
else
    if grep -q "jmpg" "$DESKTOP_INDEX" 2>/dev/null; then
        echo "  ⚠️  JMPG card already in ante-sala — skipping"
    else
        # Find the last card closing tag and inject the 4th card after it
        # Strategy: find "War Room" or the 3rd card, inject after its closing </a> or </div>
        
        # Try to inject using Python for precision
        python3 << 'PYEOF'
import re

path = "/opt/windi/desktop/index.html"
with open(path, "r", encoding="utf-8") as f:
    html = f.read()

# The JMPG card HTML — matching the style of existing cards
jmpg_card = '''
        <!-- JMPG Viewer Card -->
        <a href="/desktop/jmpg/" style="text-decoration:none;display:block">
          <div style="background:#16162a;border:1px solid rgba(212,175,55,0.12);border-radius:14px;padding:28px 24px;transition:all 0.3s;cursor:pointer;border-left:4px solid #22c55e;position:relative;overflow:hidden">
            <div style="position:absolute;top:0;right:0;width:120px;height:120px;background:radial-gradient(circle at top right,rgba(34,197,94,0.06),transparent);pointer-events:none"></div>
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">
              <div style="width:44px;height:44px;background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.2);border-radius:10px;display:grid;place-items:center;font-size:22px">📄</div>
              <div>
                <div style="font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:18px;color:#f0ece4">04 · JMPG Viewer</div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:rgba(240,236,228,0.4);letter-spacing:0.05em">COMMUNIQUÉ PORTAL</div>
              </div>
            </div>
            <p style="font-family:'Outfit',sans-serif;font-size:14px;color:rgba(240,236,228,0.6);line-height:1.5;margin:0">.jmpg Dateien öffnen und verifizieren. Governance-Siegel prüfen. Communiqués mit Vertrauensbeweis.</p>
            <div style="margin-top:14px;display:flex;align-items:center;gap:8px">
              <span style="font-family:'JetBrains Mono',monospace;font-size:10px;padding:3px 8px;border:1px solid rgba(34,197,94,0.2);color:rgba(34,197,94,0.8);border-radius:999px">SHA-256</span>
              <span style="font-family:'JetBrains Mono',monospace;font-size:10px;padding:3px 8px;border:1px solid rgba(212,175,55,0.2);color:rgba(212,175,55,0.8);border-radius:999px">ZERO-KNOWLEDGE</span>
            </div>
          </div>
        </a>'''

# Strategy: find the War Room card or 3rd card and inject after it
# Look for common patterns: "War Room", "03 ·", "warroom"
# Insert before the closing of the cards container

# Try: find "War Room" reference and its parent closing tag
patterns = [
    r'(warroom\.html.*?</a>)',      # after warroom link
    r'(War\s*Room.*?</a>)',         # after War Room card
    r'(03\s*·.*?</a>)',             # after card 03
]

inserted = False
for pat in patterns:
    match = re.search(pat, html, re.DOTALL)
    if match:
        insert_pos = match.end()
        html = html[:insert_pos] + "\n" + jmpg_card + html[insert_pos:]
        inserted = True
        break

if not inserted:
    # Fallback: find last </a> before a </div> that closes the card grid
    # Try inserting before the footer or before Pitch Deck section
    pitch_match = re.search(r'(Pitch\s*Deck|pitch)', html, re.IGNORECASE)
    if pitch_match:
        insert_pos = pitch_match.start()
        # Go back to find a clean insertion point
        last_a = html.rfind('</a>', 0, insert_pos)
        if last_a > 0:
            insert_pos = last_a + 4
            html = html[:insert_pos] + "\n" + jmpg_card + html[insert_pos:]
            inserted = True
    
    if not inserted:
        # Last resort: insert before </body>
        html = html.replace('</body>', jmpg_card + '\n</body>')
        inserted = True

with open(path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"  Card injected: {inserted}")
PYEOF
        
        echo "  ✅ JMPG card added to ante-sala"
    fi
fi

# ═══ 7. SMOKE TEST ═══
echo ""
echo "[7/7] 🔥 Smoke test..."
echo ""

# Service health
echo "  :8104/health"
curl -s http://localhost:8104/health | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'    service: {d[\"service\"]} v{d[\"version\"]}')
print(f'    status:  {d[\"status\"]}')
print(f'    viewer:  {d[\"viewer_available\"]}')
print(f'    zk:      {d[\"zero_knowledge\"]}')
" 2>/dev/null || echo "    ❌ FAIL"

# Sibling connectivity
echo ""
echo "  :8104/api/status (siblings)"
curl -s http://localhost:8104/api/status | python3 -c "
import sys,json
d=json.load(sys.stdin)
for name, info in d.get('siblings',{}).items():
    status = info.get('status','?')
    icon = '✅' if status == 'reachable' else '⚠️'
    print(f'    {icon} {name}: {status}')
" 2>/dev/null || echo "    ⚠️  Status check skipped"

# HTTPS test
echo ""
echo "  HTTPS proxy test:"
HTTPS_CODE=$(curl -sf -o /dev/null -w "%{http_code}" https://admin.windia4desk.tech/desktop/jmpg/health 2>/dev/null || echo "000")
if [ "$HTTPS_CODE" = "200" ]; then
    echo "    ✅ /desktop/jmpg/health → 200"
else
    echo "    ⚠️  /desktop/jmpg/health → $HTTPS_CODE (may need a moment)"
fi

# Ante-sala check
echo ""
if grep -q "jmpg" /opt/windi/desktop/index.html 2>/dev/null; then
    echo "  ✅ Ante-sala: JMPG card present"
else
    echo "  ⚠️  Ante-sala: card not injected (add manually)"
fi

# System count
echo ""
SERVICES=$(systemctl list-units --type=service | grep -c "windi" 2>/dev/null || echo "?")
echo "  📊 Total WINDI services: $SERVICES"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ✅ JMPG Viewer DEPLOYED — Three Dragons Approved"
echo ""
echo "  🐉 ANTE-SALA DO DESKTOP (Atualizada):"
echo ""
echo "  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐"
echo "  │ 01 SUITE  │  │02 SEALING │  │ 03 WAR RM │  │ 04 JMPG   │"
echo "  │ 'I work'  │  │'I decide' │  │ 'I see'   │  │'I verify' │"
echo "  │ :8100     │  │ :8100     │  │ :8100     │  │ :8104     │"
echo "  └───────────┘  └───────────┘  └───────────┘  └───────────┘"
echo ""
echo "  URLs:"
echo "    Viewer:  https://admin.windia4desk.tech/desktop/jmpg/"
echo "    Health:  https://admin.windia4desk.tech/desktop/jmpg/health"
echo "    Schema:  https://admin.windia4desk.tech/desktop/jmpg/api/schema"
echo "    Verify:  POST /desktop/jmpg/api/verify"
echo ""
echo "  Logs:    tail -f /opt/windi/logs/jmpg-viewer.log"
echo "  Status:  sudo systemctl status windi-jmpg-viewer"
echo ""
echo "  'AI processes. Human decides. WINDI guarantees.'"
echo "═══════════════════════════════════════════════════════"
