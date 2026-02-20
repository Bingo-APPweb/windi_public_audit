#!/bin/bash
# ═══════════════════════════════════════════════════════════
# 🐉🛡 WINDI SENTINEL LAW — DEPLOYMENT SCRIPT
# ═══════════════════════════════════════════════════════════
# "The system cannot degrade silently."
# 
# Deploy: scp files to server, then run this script
# Usage: bash deploy_sentinel_law.sh
# ═══════════════════════════════════════════════════════════

# set -e

PORT=8102
SERVICE="windi-sentinel-law"
BASE="/opt/windi/sentinel-law"
NGINX_CONF="/etc/nginx/sites-enabled/admin.windia4desk.tech"

echo "🐉🛡 WINDI SENTINEL LAW — Deployment"
echo "═══════════════════════════════════════"

# ── Step 1: Backup ──
echo ""
echo "📦 Step 1: Backup"
BK="/opt/windi/backups/pre_sentinel_law_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BK"
sudo cp "$NGINX_CONF" "$BK/nginx.conf"
echo "   Backup: $BK"

# ── Step 2: Create directories ──
echo ""
echo "📂 Step 2: Directories"
mkdir -p "$BASE"
mkdir -p /opt/windi/data
mkdir -p /opt/windi/logs
echo "   Created: $BASE"

# ── Step 3: Deploy code ──
echo ""
echo "📄 Step 3: Deploy code"
cp sentinel_law.py "$BASE/sentinel_law.py"
chmod +x "$BASE/sentinel_law.py"
echo "   Deployed: $BASE/sentinel_law.py"

# ── Step 4: Check port availability ──
echo ""
echo "🔍 Step 4: Port check"
if ss -tlnp | grep -q ":${PORT} "; then
    echo "   ⚠️  Port $PORT in use — killing existing process"
    PID=$(ss -tlnp | grep ":${PORT} " | grep -oP 'pid=\K[0-9]+' | head -1)
    if [ -n "$PID" ]; then
        kill "$PID" 2>/dev/null || true
        sleep 2
    fi
fi
echo "   Port $PORT: available"

# ── Step 5: Install systemd service ──
echo ""
echo "⚙️  Step 5: systemd service"
sudo cp windi-sentinel-law.service /etc/systemd/system/${SERVICE}.service
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE}.service
sudo systemctl start ${SERVICE}.service
sleep 3
echo "   Status:"
sudo systemctl status ${SERVICE}.service --no-pager | head -10

# ── Step 6: Verify service ──
echo ""
echo "🏥 Step 6: Health check"
sleep 2
HEALTH=$(curl -s --max-time 5 http://127.0.0.1:${PORT}/health 2>&1)
echo "   $HEALTH" | python3 -m json.tool 2>/dev/null || echo "   $HEALTH"

# ── Step 7: Add nginx proxy ──
echo ""
echo "🌐 Step 7: nginx configuration"

# Find the line number of 'listen 443 ssl'
SSL_LINE=$(grep -n "listen 443 ssl" "$NGINX_CONF" | head -1 | cut -d: -f1)

if [ -z "$SSL_LINE" ]; then
    echo "   ❌ Could not find 'listen 443 ssl' in nginx config"
    echo "   Manual nginx configuration required"
else
    # Check if sentinel-law already configured
    if grep -q "sentinel-law" "$NGINX_CONF"; then
        echo "   ℹ️  sentinel-law already in nginx config — skipping"
    else
        INSERT_LINE=$((SSL_LINE - 2))
        SNIPPET='
    # ── SENTINEL LAW (:8102) ────────────────────────────
    location /sentinel-law/ {
        proxy_pass http://127.0.0.1:8102/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
        add_header Access-Control-Allow-Origin "https://admin.windia4desk.tech" always;
        add_header Access-Control-Allow-Methods "GET, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
        if ($request_method = OPTIONS) {
            return 204;
        }
    }
    # ── END SENTINEL LAW ────────────────────────────────'

        sudo sed -i "${INSERT_LINE}a\\${SNIPPET}" "$NGINX_CONF"
        echo "   Injected nginx snippet at line $INSERT_LINE"

        # Test and reload
        if sudo nginx -t 2>&1; then
            sudo systemctl reload nginx
            echo "   ✅ nginx reloaded"
        else
            echo "   ❌ nginx test failed — restoring backup"
            sudo cp "$BK/nginx.conf" "$NGINX_CONF"
            sudo systemctl reload nginx
            echo "   Restored from backup"
        fi
    fi
fi

# ── Step 8: Full verification ──
echo ""
echo "═══════════════════════════════════════"
echo "🐉🛡 FINAL VERIFICATION"
echo "═══════════════════════════════════════"
echo ""

echo "--- systemd ---"
sudo systemctl is-active ${SERVICE}.service

echo ""
echo "--- localhost health ---"
curl -s --max-time 5 http://127.0.0.1:${PORT}/health | python3 -m json.tool

echo ""
echo "--- HTTPS health ---"
curl -sk --max-time 5 https://admin.windia4desk.tech/sentinel-law/health | python3 -m json.tool 2>/dev/null || echo "(nginx may need manual config)"

echo ""
echo "--- law config ---"
curl -s --max-time 5 http://127.0.0.1:${PORT}/api/law/config | python3 -m json.tool

echo ""
echo "--- trigger first law check ---"
curl -s --max-time 15 http://127.0.0.1:${PORT}/api/law/check | python3 -m json.tool

echo ""
echo "═══════════════════════════════════════"
echo "🐉🛡 SENTINEL LAW DEPLOYED"
echo "═══════════════════════════════════════"
echo ""
echo "Port:      $PORT"
echo "Service:   $SERVICE"
echo "DB:        /opt/windi/data/sentinel_law.db"
echo "Log:       /opt/windi/logs/sentinel_law.log"
echo "Interval:  30 seconds"
echo ""
echo "Endpoints:"
echo "  https://admin.windia4desk.tech/sentinel-law/health"
echo "  https://admin.windia4desk.tech/sentinel-law/api/law/status"
echo "  https://admin.windia4desk.tech/sentinel-law/api/law/check"
echo "  https://admin.windia4desk.tech/sentinel-law/api/law/history"
echo "  https://admin.windia4desk.tech/sentinel-law/api/law/alerts"
echo "  https://admin.windia4desk.tech/sentinel-law/api/law/config"
echo ""
echo "The system cannot degrade silently. 🐉🛡"
