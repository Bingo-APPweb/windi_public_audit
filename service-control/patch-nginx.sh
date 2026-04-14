#!/bin/bash
# Patch nginx for W-SERVICE-CONTROL
# Run with: sudo bash patch-nginx.sh

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/tmp/nginx-backup-svc-$(date +%Y%m%d_%H%M%S).conf"

echo "=== W-SERVICE-CONTROL Nginx Patch ==="
echo "Backing up to $BACKUP..."
cp "$NGINX_CONF" "$BACKUP"

# Check if route already exists
if grep -q "svc-control" "$NGINX_CONF"; then
    echo "Route /svc-control/ already exists!"
    exit 0
fi

# Find line number after wcache/api block
LINE=$(grep -n "location /wcache/api/" "$NGINX_CONF" | head -1 | cut -d: -f1)

if [ -z "$LINE" ]; then
    echo "ERROR: Could not find /wcache/api/ location block"
    exit 1
fi

# Insert after the wcache/api block (approximately 10 lines after)
INSERT_LINE=$((LINE + 10))

# Create the new config block
NEW_BLOCK='
    # ═══════════════════════════════════════════════
    # W-SERVICE-CONTROL · Port 8170
    # Sovereign Service Management Panel
    # ═══════════════════════════════════════════════

    location /svc-control/ {
        proxy_pass http://127.0.0.1:8170/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /svc-control/api/ {
        proxy_pass http://127.0.0.1:8170/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location = /svc-control {
        return 301 /svc-control/;
    }
'

# Use sed to insert the block
sed -i "${INSERT_LINE}a\\${NEW_BLOCK}" "$NGINX_CONF"

echo "Testing nginx config..."
nginx -t

if [ $? -eq 0 ]; then
    echo "Reloading nginx..."
    systemctl reload nginx
    echo "=== SUCCESS ==="
    echo "Service Control Panel available at: https://windi-domain.com/svc-control/"
else
    echo "ERROR: nginx config test failed!"
    echo "Restoring backup..."
    cp "$BACKUP" "$NGINX_CONF"
    exit 1
fi
