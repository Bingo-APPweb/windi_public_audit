#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  WINDI JMPG Viewer — Deploy Script
#  Target: Strato (87.106.29.233)
#  Port: 8104
#  Location: /opt/windi/jmpg-viewer/
#  URL: https://admin.windia4desk.tech/jmpg/
#
#  Run AS windi user:  bash deploy_jmpg_viewer.sh
# ═══════════════════════════════════════════════════════════════

set -e

echo "═══════════════════════════════════════════════"
echo "  WINDI JMPG Viewer — Deployment"
echo "  Port: 8104"
echo "═══════════════════════════════════════════════"

# ── 1. Pre-flight checks ──
echo ""
echo "[1/8] Pre-flight checks..."

# Check port availability
if ss -tlnp | grep -q ":8104 "; then
    echo "⚠️  Port 8104 already in use:"
    ss -tlnp | grep ":8104 "
    echo "Kill existing process? (y/n)"
    read -r KILL
    if [ "$KILL" = "y" ]; then
        PID=$(ss -tlnp | grep ":8104 " | grep -oP 'pid=\K\d+')
        kill "$PID" 2>/dev/null && echo "Killed PID $PID" || true
        sleep 2
    else
        echo "Aborted."
        exit 1
    fi
fi

echo "✅ Port 8104 available"

# ── 2. Backup ──
echo ""
echo "[2/8] Creating backup..."
BK="/opt/windi/backups/pre_jmpg_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BK"
sudo cp /etc/nginx/sites-enabled/admin.windia4desk.tech "$BK/nginx.conf" 2>/dev/null || true
if [ -d /opt/windi/jmpg-viewer ]; then
    cp -r /opt/windi/jmpg-viewer "$BK/jmpg-viewer-old"
fi
echo "✅ Backup: $BK"

# ── 3. Create service directory ──
echo ""
echo "[3/8] Setting up /opt/windi/jmpg-viewer/..."
mkdir -p /opt/windi/jmpg-viewer/samples
mkdir -p /opt/windi/logs

# ── 4. Deploy files ──
echo ""
echo "[4/8] Deploying files..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp "$SCRIPT_DIR/jmpg_viewer_server.py" /opt/windi/jmpg-viewer/
cp "$SCRIPT_DIR/viewer.html" /opt/windi/jmpg-viewer/
cp "$SCRIPT_DIR/samples/"*.jmpg /opt/windi/jmpg-viewer/samples/ 2>/dev/null || true
echo "✅ Files deployed"

# ── 5. Test locally ──
echo ""
echo "[5/8] Testing server startup..."
python3 /opt/windi/jmpg-viewer/jmpg_viewer_server.py &
TEST_PID=$!
sleep 2

if curl -sf http://localhost:8104/health > /dev/null 2>&1; then
    echo "✅ Server responds on :8104"
    HEALTH=$(curl -s http://localhost:8104/health)
    echo "   $HEALTH"
else
    echo "❌ Server failed to start!"
    kill $TEST_PID 2>/dev/null
    exit 1
fi
kill $TEST_PID 2>/dev/null
sleep 1

# ── 6. Install systemd service ──
echo ""
echo "[6/8] Installing systemd service..."
sudo cp "$SCRIPT_DIR/windi-jmpg-viewer.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable windi-jmpg-viewer.service
sudo systemctl start windi-jmpg-viewer.service
sleep 2

if sudo systemctl is-active --quiet windi-jmpg-viewer; then
    echo "✅ systemd service: ACTIVE"
else
    echo "❌ systemd service failed!"
    sudo systemctl status windi-jmpg-viewer --no-pager
    exit 1
fi

# ── 7. Inject nginx config ──
echo ""
echo "[7/8] Configuring nginx..."

# Check if already injected
if grep -q "JMPG Viewer" /etc/nginx/sites-enabled/admin.windia4desk.tech 2>/dev/null; then
    echo "⚠️  nginx snippet already present — skipping injection"
else
    # Find the SSL line to inject before
    SSL_LINE=$(grep -n "listen 443 ssl" /etc/nginx/sites-enabled/admin.windia4desk.tech | head -1 | cut -d: -f1)
    
    if [ -z "$SSL_LINE" ]; then
        echo "❌ Cannot find 'listen 443 ssl' in nginx config!"
        echo "   Please manually add the snippet from nginx_jmpg_snippet.conf"
    else
        # Inject 2 lines before SSL directive
        INJECT_LINE=$((SSL_LINE - 2))
        
        # Read snippet and inject
        SNIPPET=$(cat "$SCRIPT_DIR/nginx_jmpg_snippet.conf")
        
        sudo sed -i "${INJECT_LINE}r ${SCRIPT_DIR}/nginx_jmpg_snippet.conf" \
            /etc/nginx/sites-enabled/admin.windia4desk.tech
        
        echo "✅ nginx snippet injected at line $INJECT_LINE"
    fi
    
    # Test nginx
    if sudo nginx -t 2>&1; then
        sudo systemctl reload nginx
        echo "✅ nginx reloaded"
    else
        echo "❌ nginx test FAILED — reverting!"
        sudo cp "$BK/nginx.conf" /etc/nginx/sites-enabled/admin.windia4desk.tech
        sudo nginx -t && sudo systemctl reload nginx
        echo "   Reverted to backup"
        exit 1
    fi
fi

# ── 8. Smoke test ──
echo ""
echo "[8/8] Smoke test..."
echo ""

# Local tests
echo "  localhost:8104/health:"
curl -s http://localhost:8104/health | python3 -m json.tool 2>/dev/null || echo "  ❌ FAIL"

echo ""
echo "  localhost:8104/api/status:"
curl -s http://localhost:8104/api/status | python3 -m json.tool 2>/dev/null || echo "  ❌ FAIL"

# HTTPS test (may take a moment for nginx proxy)
echo ""
echo "  HTTPS test:"
curl -sf https://admin.windia4desk.tech/jmpg/health 2>/dev/null && echo "  ✅ HTTPS OK" || echo "  ⚠️  HTTPS not yet reachable (check nginx)"

echo ""
echo "═══════════════════════════════════════════════"
echo "  ✅ JMPG Viewer DEPLOYED"
echo ""
echo "  Service:  windi-jmpg-viewer (systemd)"
echo "  Port:     8104"
echo "  Local:    http://localhost:8104/"
echo "  HTTPS:    https://admin.windia4desk.tech/jmpg/"
echo "  Health:   https://admin.windia4desk.tech/jmpg/health"
echo "  Schema:   https://admin.windia4desk.tech/jmpg/api/schema"
echo "  Verify:   POST https://admin.windia4desk.tech/jmpg/api/verify"
echo ""
echo "  Logs:     tail -f /opt/windi/logs/jmpg-viewer.log"
echo "  Status:   sudo systemctl status windi-jmpg-viewer"
echo "═══════════════════════════════════════════════"
