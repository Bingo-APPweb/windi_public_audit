#!/bin/bash
# §173 DID Simplification — Add nginx route for /shared/
# Run as root: sudo bash patch_nginx_shared.sh

NGINX_CONF="/etc/nginx/sites-available/windi"
BACKUP="/tmp/nginx-backup-shared-$(date +%Y%m%d_%H%M%S).conf"

# Backup
cp "$NGINX_CONF" "$BACKUP"
echo "Backup: $BACKUP"

# Check if route already exists
if grep -q "location /shared/" "$NGINX_CONF"; then
    echo "Route /shared/ already exists"
    exit 0
fi

# Find line to insert after (before first location block)
LINE=$(grep -n "location" "$NGINX_CONF" | head -1 | cut -d: -f1)

# Create the new location block
ROUTE='
    # §173 DID Simplification — Shared static files
    location /shared/ {
        alias /opt/windi/shared/static/;
        expires 1d;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options nosniff;
    }
'

# Insert the route
sed -i "${LINE}i\\${ROUTE}" "$NGINX_CONF"

# Test nginx
nginx -t
if [ $? -eq 0 ]; then
    systemctl reload nginx
    echo "✅ Route /shared/ added and nginx reloaded"
else
    echo "❌ nginx config error, restoring backup"
    cp "$BACKUP" "$NGINX_CONF"
    exit 1
fi
