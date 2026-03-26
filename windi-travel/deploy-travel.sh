#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# WINDI Travel Deploy Script v1.0.0
# Port: 8126
# Liga IA+H · Kempten · 2026
# ═══════════════════════════════════════════════════════════════

set -e

echo "═══════════════════════════════════════════════════════════"
echo "WINDI Travel — Deploy Script"
echo "═══════════════════════════════════════════════════════════"

# 1. Create logs directory
echo "[1/5] Creating logs directory..."
mkdir -p /opt/windi/logs

# 2. Copy systemd service
echo "[2/5] Installing systemd service..."
sudo cp /opt/windi/windi-travel/identity-gate/windi-travel.service /etc/systemd/system/
sudo systemctl daemon-reload

# 3. Add nginx config
echo "[3/5] Adding nginx configuration..."
NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
NGINX_BACKUP="/opt/windi/backups/nginx-windi-domain-$(date +%Y%m%d_%H%M%S).conf"

# Backup
sudo cp "$NGINX_CONF" "$NGINX_BACKUP"
echo "    Backup: $NGINX_BACKUP"

# Check if /travel/ already exists
if grep -q "location.*\/travel\/" "$NGINX_CONF"; then
    echo "    /travel/ already configured — skipping"
else
    # Add /travel/ block after /law/ block
    # Find line number of /law/ block and add after
    TRAVEL_BLOCK='
    # ═══ WINDI TRAVEL :8126 ═══
    location ^~ /travel/ {
        proxy_pass http://127.0.0.1:8126/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
'
    # Find the line with "location ^~ /law/" and add TRAVEL_BLOCK after its closing brace
    sudo sed -i '/location \^~ \/law\//,/^[[:space:]]*}$/{ /^[[:space:]]*}$/a\
    # ═══ WINDI TRAVEL :8126 ═══\
    location ^~ /travel/ {\
        proxy_pass http://127.0.0.1:8126/;\
        proxy_http_version 1.1;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
    }
}' "$NGINX_CONF"
    echo "    /travel/ block added"
fi

# 4. Test nginx
echo "[4/5] Testing nginx configuration..."
sudo nginx -t

# 5. Start services
echo "[5/5] Starting services..."
sudo systemctl enable windi-travel
sudo systemctl start windi-travel
sudo systemctl reload nginx

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "DEPLOY COMPLETE"
echo "═══════════════════════════════════════════════════════════"
echo "Service:  systemctl status windi-travel"
echo "Logs:     tail -f /opt/windi/logs/windi-travel.log"
echo "Gate:     https://windi-domain.com/travel/gate"
echo "═══════════════════════════════════════════════════════════"
