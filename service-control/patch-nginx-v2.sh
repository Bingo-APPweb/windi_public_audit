#!/bin/bash
# Patch nginx for W-SERVICE-CONTROL - v2 (simpler approach)
# Run with: sudo bash patch-nginx-v2.sh

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/tmp/nginx-backup-svc-$(date +%Y%m%d_%H%M%S).conf"
PATCH_FILE="/tmp/svc-control-block.conf"

echo "=== W-SERVICE-CONTROL Nginx Patch v2 ==="
echo "Backing up to $BACKUP..."
cp "$NGINX_CONF" "$BACKUP"

# Check if route already exists
if grep -q "svc-control" "$NGINX_CONF"; then
    echo "Route /svc-control/ already exists!"
    exit 0
fi

# Create patch block file
cat > "$PATCH_FILE" << 'BLOCK'

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
BLOCK

# Find the line with "location = /wcache/noir" and insert after its block
# We'll insert before the next major section (after wcache block)
LINE=$(grep -n "location = /wcache/noir" "$NGINX_CONF" | head -1 | cut -d: -f1)

if [ -z "$LINE" ]; then
    # Try alternative: after /wcache/ block
    LINE=$(grep -n "location /wcache/" "$NGINX_CONF" | head -1 | cut -d: -f1)
fi

if [ -z "$LINE" ]; then
    echo "ERROR: Could not find wcache location block"
    echo "Manual insertion required. Add this block to nginx config:"
    cat "$PATCH_FILE"
    exit 1
fi

# Insert 15 lines after the found location (should be after the closing brace)
INSERT_LINE=$((LINE + 15))

# Use head/tail approach instead of sed
{
    head -n "$INSERT_LINE" "$NGINX_CONF"
    cat "$PATCH_FILE"
    tail -n +$((INSERT_LINE + 1)) "$NGINX_CONF"
} > "${NGINX_CONF}.new"

mv "${NGINX_CONF}.new" "$NGINX_CONF"

echo "Testing nginx config..."
nginx -t

if [ $? -eq 0 ]; then
    echo "Reloading nginx..."
    systemctl reload nginx
    echo ""
    echo "=== SUCCESS ==="
    echo "Service Control Panel: https://windi-domain.com/svc-control/"
else
    echo "ERROR: nginx config test failed!"
    echo "Restoring backup..."
    cp "$BACKUP" "$NGINX_CONF"
    exit 1
fi

rm -f "$PATCH_FILE"
