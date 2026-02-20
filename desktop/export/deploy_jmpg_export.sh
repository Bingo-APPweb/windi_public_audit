#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# WINDI JMPG Export Engine — Deploy Script
# Run on Strato: bash deploy_jmpg_export.sh
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

echo "═══════════════════════════════════════════════════════════"
echo "  🐉 WINDI JMPG Export Engine v1.0.0 — DEPLOY"
echo "  Port: 8103 | Spec: JMPG-1.0"
echo "═══════════════════════════════════════════════════════════"

# ── 0. Pre-flight ─────────────────────────────────────────────
echo ""
echo "▶ [0/7] Pre-flight check..."

# Check if port 8103 is in use
if ss -tlnp | grep -q ":8103 "; then
    echo "⚠  Port 8103 is in use:"
    ss -tlnp | grep ":8103 "
    echo ""
    echo "Stopping existing process..."
    # Try systemd first
    sudo systemctl stop windi-jmpg-export 2>/dev/null || true
    # Kill any remaining process
    fuser -k 8103/tcp 2>/dev/null || true
    sleep 2
    echo "✅ Port 8103 freed."
fi

# ── 1. Backup ─────────────────────────────────────────────────
echo ""
echo "▶ [1/7] Creating backup..."
BK="/opt/windi/backups/pre_jmpg_export_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BK"
sudo cp /etc/nginx/sites-enabled/admin.windia4desk.tech "$BK/nginx.conf" 2>/dev/null || true
if [ -d /opt/windi/desktop/export ]; then
    cp -r /opt/windi/desktop/export "$BK/export_backup" 2>/dev/null || true
fi
echo "✅ Backup: $BK"

# ── 2. Create directories ────────────────────────────────────
echo ""
echo "▶ [2/7] Creating directories..."
mkdir -p /opt/windi/desktop/export
mkdir -p /opt/windi/desktop/export/media_cache
mkdir -p /opt/windi/logs
echo "✅ Directories ready."

# ── 3. Deploy engine ─────────────────────────────────────────
echo ""
echo "▶ [3/7] Deploying JMPG Export Engine..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp "$SCRIPT_DIR/jmpg_export_engine.py" /opt/windi/desktop/export/jmpg_export_engine.py
chmod +x /opt/windi/desktop/export/jmpg_export_engine.py
echo "✅ Engine deployed to /opt/windi/desktop/export/"

# ── 4. Install systemd service ────────────────────────────────
echo ""
echo "▶ [4/7] Installing systemd service..."
sudo cp "$SCRIPT_DIR/windi-jmpg-export.service" /etc/systemd/system/windi-jmpg-export.service
sudo systemctl daemon-reload
sudo systemctl enable windi-jmpg-export
sudo systemctl start windi-jmpg-export
sleep 2

# Verify
STATUS=$(sudo systemctl is-active windi-jmpg-export)
if [ "$STATUS" = "active" ]; then
    echo "✅ Service active!"
else
    echo "❌ Service not active. Checking logs..."
    journalctl -u windi-jmpg-export --no-pager -n 20
    exit 1
fi

# ── 5. Health check ───────────────────────────────────────────
echo ""
echo "▶ [5/7] Health check..."
sleep 1
HEALTH=$(curl -s http://localhost:8103/health)
echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
echo "✅ Health check passed."

# ── 6. NGINX routing ─────────────────────────────────────────
echo ""
echo "▶ [6/7] Configuring NGINX..."

NGINX_CONF="/etc/nginx/sites-enabled/admin.windia4desk.tech"

# Check if export route already exists
if grep -q "jmpg-export" "$NGINX_CONF" 2>/dev/null; then
    echo "⚠  NGINX export route already exists. Skipping."
else
    # Find the line number for SSL block
    SSL_LINE=$(grep -n "listen 443 ssl" "$NGINX_CONF" | head -1 | cut -d: -f1)
    
    if [ -z "$SSL_LINE" ]; then
        echo "❌ Could not find 'listen 443 ssl' in nginx config."
        echo "   Please add the following manually:"
        cat << 'NGINX_SNIPPET'

    # ── JMPG Export Engine (:8103) ─────────────────────────
    location /export/ {
        proxy_pass http://127.0.0.1:8103/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
        add_header Access-Control-Allow-Origin "https://admin.windia4desk.tech" always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
        if ($request_method = OPTIONS) {
            return 204;
        }
        client_max_body_size 50M;
    }
    # ── END JMPG Export Engine ─────────────────────────────

NGINX_SNIPPET
    else
        INSERT_LINE=$((SSL_LINE - 2))
        echo "   Inserting at line $INSERT_LINE (before SSL block at line $SSL_LINE)"

        # Create temp file with the snippet
        SNIPPET_FILE=$(mktemp)
        cat > "$SNIPPET_FILE" << 'NGINX_BLOCK'

    # ── JMPG Export Engine (:8103) ─────────────────────────
    location /export/ {
        proxy_pass http://127.0.0.1:8103/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
        add_header Access-Control-Allow-Origin "https://admin.windia4desk.tech" always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
        if ($request_method = OPTIONS) {
            return 204;
        }
        client_max_body_size 50M;
    }
    # ── END JMPG Export Engine ─────────────────────────────
NGINX_BLOCK

        sudo sed -i "${INSERT_LINE}r ${SNIPPET_FILE}" "$NGINX_CONF"
        rm -f "$SNIPPET_FILE"

        # Test nginx config
        if sudo nginx -t 2>&1; then
            sudo systemctl reload nginx
            echo "✅ NGINX configured and reloaded."
        else
            echo "❌ NGINX config error! Restoring backup..."
            sudo cp "$BK/nginx.conf" "$NGINX_CONF"
            sudo systemctl reload nginx
            echo "   Backup restored. Please add the route manually."
        fi
    fi
fi

# ── 7. Smoke test ─────────────────────────────────────────────
echo ""
echo "▶ [7/7] Smoke test — creating test .jmpg..."

RESULT=$(curl -s -X POST http://localhost:8103/api/export/jmpg \
    -H "Content-Type: application/json" \
    -d '{
        "title": "Deploy Test Communiqué",
        "author": "WINDI Guardian",
        "template": "generic",
        "content_blocks": [
            {
                "type": "heading",
                "level": 1,
                "text": "JMPG Export Engine — Operational"
            },
            {
                "type": "paragraph",
                "text": "This is the first .jmpg ever created by the WINDI Export Pipeline. The factory is alive."
            },
            {
                "type": "paragraph",
                "text": "AI processes. Human decides. WINDI guarantees."
            }
        ],
        "metadata": {
            "doc_type": "COMMUNIQUE",
            "impact_level": "LOW",
            "department_code": "SYSTEM",
            "language": "en",
            "tags": ["deploy-test", "first-jmpg"]
        },
        "return_format": "json"
    }')

echo "$RESULT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    if d.get('success'):
        print(f'✅ FIRST .jmpg CREATED!')
        print(f'   Package ID:  {d[\"package_id\"]}')
        print(f'   Content hash: {d[\"content_hash\"][:32]}...')
        print(f'   Manifest hash: {d[\"manifest_hash\"][:32]}...')
        print(f'   Receipt ID:  {d.get(\"receipt_id\", \"N/A\")}')
        print(f'   Ledger:      {\"✅ REGISTERED\" if d.get(\"ledger_registered\") else \"⚠ NOT REGISTERED\"}')
        print(f'   Size:        {d[\"size_bytes\"]} bytes')
        print(f'   Time:        {d[\"elapsed_ms\"]}ms')
    else:
        print(f'⚠ Test returned: {json.dumps(d, indent=2)}')
except:
    print(f'Raw response: {sys.stdin.read()}')
" 2>/dev/null || echo "   Raw: $RESULT"

# ── DONE ──────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  🐉 JMPG Export Engine v1.0.0 — DEPLOYED!"
echo ""
echo "  Endpoints:"
echo "    Health:    https://admin.windia4desk.tech/export/health"
echo "    Spec:      https://admin.windia4desk.tech/export/api/export/spec"
echo "    Templates: https://admin.windia4desk.tech/export/api/export/templates"
echo "    Export:    POST https://admin.windia4desk.tech/export/api/export/jmpg"
echo "    Preview:   POST https://admin.windia4desk.tech/export/api/export/jmpg/preview"
echo ""
echo "  Service:     sudo systemctl status windi-jmpg-export"
echo "  Logs:        tail -f /opt/windi/logs/jmpg-export.log"
echo "  Backup:      $BK"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  🛡️ A fábrica está viva. O WINDI agora PRODUZ mídia confiável."
echo ""
