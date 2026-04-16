#!/bin/bash
# §129 NOMAD Upload PWA — Nginx Patch
# Run with: sudo bash /home/windi/patch-nginx-nomad-pwa.sh

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/home/windi/nginx-backup-nomad-pwa-$(date +%Y%m%d_%H%M%S).conf"

echo "=== §129 NOMAD Upload PWA — Nginx Patch ==="
echo ""

# Backup
cp "$NGINX_CONF" "$BACKUP"
echo "✓ Backup: $BACKUP"

# Check if already patched
if grep -q "nomad-upload" "$NGINX_CONF"; then
    echo "⚠ Already patched — /nomad-upload/ location exists"
    exit 0
fi

# Find the line number after mobile section
LINE=$(grep -n "# ── A4 Desk BABEL Editor" "$NGINX_CONF" | head -1 | cut -d: -f1)

if [ -z "$LINE" ]; then
    echo "✗ Could not find insertion point"
    exit 1
fi

# Insert the new location block before A4 Desk
sed -i "${LINE}i\\
    # ═══ NOMAD Upload PWA (static) ═══\\
    location /nomad-upload/ {\\
        alias /opt/windi/nomad-pwa/;\\
        try_files \$uri \$uri/ /nomad-upload/index.html;\\
        add_header Cache-Control \"no-cache\";\\
        add_header X-Frame-Options \"SAMEORIGIN\";\\
        add_header X-WINDI-Service \"nomad-upload-pwa\" always;\\
    }\\
" "$NGINX_CONF"

echo "✓ Location /nomad-upload/ added"

# Test nginx
echo ""
echo "Testing nginx config..."
nginx -t

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ nginx -t passed"
    echo ""
    echo "To apply: sudo systemctl reload nginx"
    echo "URL: https://windi-domain.com/nomad-upload/"
else
    echo ""
    echo "✗ nginx -t failed — restoring backup"
    cp "$BACKUP" "$NGINX_CONF"
fi
