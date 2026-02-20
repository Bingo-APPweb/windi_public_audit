#!/bin/bash
# ================================================================
# 🛡 WINDI Landing Page P/M/G — Deploy Script
# Port: 8107
# Replaces root of windi-domain.com with tier selection
# ================================================================

set -e

echo "🛡 WINDI Landing P/M/G — Deployment"
echo "======================================"

# === 1. Pre-flight ===
echo ""
echo "1️⃣  Pre-flight checks..."

if ss -tlnp | grep -q ":8107 "; then
    echo "⚠️  Port 8107 already in use. Kill? (y/n)"
    read -r KILL
    if [ "$KILL" = "y" ]; then
        PID=$(ss -tlnp | grep ":8107 " | grep -oP 'pid=\K[0-9]+')
        kill "$PID" 2>/dev/null && echo "✅ Killed PID $PID" || true
        sleep 2
    else
        echo "❌ Aborting."
        exit 1
    fi
fi

# === 2. Backup ===
echo ""
echo "2️⃣  Backup (run backup_pre_deploy.sh first if not done)"
BK="/opt/windi/backups/pre_landing_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BK"

# Backup current windi-domain nginx
WINDI_NGINX=$(grep -rl "windi-domain.com" /etc/nginx/sites-enabled/ 2>/dev/null | head -1)
if [ -n "$WINDI_NGINX" ]; then
    sudo cp "$WINDI_NGINX" "$BK/windi-domain-nginx.conf"
    echo "✅ nginx backup: $BK/windi-domain-nginx.conf"
else
    echo "⚠️  Could not find windi-domain.com nginx config"
fi

# === 3. Deploy files ===
echo ""
echo "3️⃣  Deploying Landing files..."
mkdir -p /opt/windi/landing-pmg/static
cp landing_server.py /opt/windi/landing-pmg/
cp static/index.html /opt/windi/landing-pmg/static/
chmod +x /opt/windi/landing-pmg/landing_server.py
echo "✅ Files: /opt/windi/landing-pmg/"

# === 4. systemd ===
echo ""
echo "4️⃣  Installing systemd service..."
sudo cp windi-landing.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable windi-landing.service
sudo systemctl start windi-landing.service
sleep 2

if sudo systemctl is-active --quiet windi-landing.service; then
    echo "✅ Service active!"
    curl -s http://localhost:8107/health | python3 -m json.tool 2>/dev/null
else
    echo "❌ Service failed. Check: journalctl -u windi-landing -n 20"
    exit 1
fi

# === 5. nginx ===
echo ""
echo "5️⃣  Nginx configuration..."
echo ""
echo "   ⚠️  MANUAL STEP REQUIRED"
echo "   ========================"
echo ""
echo "   The root (/) of windi-domain.com needs to point to :8107."
echo "   This requires editing the nginx config carefully."
echo ""
echo "   Current windi-domain.com config: $WINDI_NGINX"
echo ""
echo "   Steps:"
echo "   1. Open: sudo nano $WINDI_NGINX"
echo "   2. Find the current 'location / { ... }' block"
echo "   3. Replace it with the content from nginx_landing_snippet.conf"
echo "   4. KEEP all other locations (/governance, /static/, /records/)"
echo "   5. Test: sudo nginx -t"
echo "   6. Reload: sudo systemctl reload nginx"
echo ""
echo "   Or do it with sed (safer to do manually for root change):"
echo "   cat nginx_landing_snippet.conf"
echo ""

read -p "   Have you updated nginx? (y/skip): " NGINX_DONE

if [ "$NGINX_DONE" = "y" ]; then
    sudo nginx -t
    if [ $? -eq 0 ]; then
        sudo systemctl reload nginx
        echo "✅ Nginx reloaded!"
    else
        echo "❌ Nginx test failed! Restore: sudo cp $BK/windi-domain-nginx.conf $WINDI_NGINX"
        exit 1
    fi
else
    echo "⚠️  Skipped nginx. Service is running on :8107 but not yet proxied."
    echo "   You can test locally: curl http://localhost:8107/"
fi

# === 6. Verify ===
echo ""
echo "6️⃣  Verification..."
echo "   Local: $(curl -s http://localhost:8107/health | python3 -c 'import sys,json; d=json.load(sys.stdin); print(f"✅ {d[\"service\"]}")' 2>/dev/null || echo '❌ Failed')"

if [ "$NGINX_DONE" = "y" ]; then
    echo "   HTTPS: $(curl -s https://windi-domain.com/ | head -c 100 | grep -q 'WINDI' && echo '✅ Landing visible' || echo '⚠️  Check HTTPS')"
fi

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  🛡 WINDI Landing P/M/G DEPLOYED             ║"
echo "║                                              ║"
echo "║  Local:  http://localhost:8107               ║"
echo "║  HTTPS:  https://windi-domain.com            ║"
echo "║  Health: /health                             ║"
echo "║                                              ║"
echo "║  Routes preserved:                           ║"
echo "║    /governance → Dashboard (unchanged)       ║"
echo "║    /vault/     → Forensic Vault (:8106)      ║"
echo "║    /static/    → Audit dashboards            ║"
echo "║    /records/   → Depositions                 ║"
echo "║                                              ║"
echo "║  One system. Three paths. Your scale.        ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "🐉 O mundo agora tem uma porta."
