#!/bin/bash
# §134 W-JMPG-001 — Nginx Patch
# Run with: sudo bash /opt/windi/comm/patch-nginx-jmpg.sh

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/opt/windi/comm/nginx-backup-jmpg-$(date +%Y%m%d_%H%M%S).conf"

echo "=== §134 W-JMPG-001 — Nginx Patch ==="
echo ""

# Backup
cp "$NGINX_CONF" "$BACKUP"
echo "Backup: $BACKUP"

# Check if already patched
if grep -q "location /comm/" "$NGINX_CONF"; then
    echo "Already patched — /comm/ location exists"
    exit 0
fi

# Find insertion point (before vd-cut or after nomad-upload)
LINE=$(grep -n "# ═══ VD-CUT" "$NGINX_CONF" | head -1 | cut -d: -f1)

if [ -z "$LINE" ]; then
    LINE=$(grep -n "location /vd-cut/" "$NGINX_CONF" | head -1 | cut -d: -f1)
fi

if [ -z "$LINE" ]; then
    echo "Could not find insertion point"
    exit 1
fi

# Insert the new location blocks
sed -i "${LINE}i\\
\\
    # ═══ W-JMPG-001 COMM Service ═══\\
    location /comm/jmpg/ {\\
        alias /opt/windi/media/comm/jmpg/;\\
        expires 7d;\\
        add_header Cache-Control \"public, immutable\";\\
        add_header X-WINDI-Service \"jmpg-static\" always;\\
    }\\
\\
    location /comm/ {\\
        proxy_pass http://127.0.0.1:8132/comm/;\\
        proxy_http_version 1.1;\\
        proxy_set_header Host \$host;\\
        proxy_set_header X-Real-IP \$remote_addr;\\
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\\
        proxy_set_header X-Forwarded-Proto \$scheme;\\
        add_header X-WINDI-Service \"jmpg-api\" always;\\
    }\\
" "$NGINX_CONF"

echo "Location /comm/ added"

# Test nginx
echo ""
echo "Testing nginx config..."
nginx -t

if [ $? -eq 0 ]; then
    echo ""
    echo "nginx -t passed"
    echo ""
    echo "To apply: sudo systemctl reload nginx"
    echo "To start service: sudo systemctl enable --now windi-jmpg"
else
    echo ""
    echo "nginx -t failed — restoring backup"
    cp "$BACKUP" "$NGINX_CONF"
fi
