#!/bin/bash
# Patch nginx for W-SERVICE-CONTROL - v3 (correct placement)
# Run with: sudo bash patch-nginx-v3.sh

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/tmp/nginx-backup-svc-$(date +%Y%m%d_%H%M%S).conf"

echo "=== W-SERVICE-CONTROL Nginx Patch v3 ==="

# First, restore from most recent backup if svc-control exists incorrectly
if grep -q "svc-control" "$NGINX_CONF"; then
    echo "Removing incorrectly placed svc-control block..."
    # Remove the bad block (lines containing svc-control and surrounding)
    grep -v "svc-control" "$NGINX_CONF" | grep -v "W-SERVICE-CONTROL" | grep -v "Sovereign Service Management" > "${NGINX_CONF}.clean"
    mv "${NGINX_CONF}.clean" "$NGINX_CONF"
fi

echo "Backing up to $BACKUP..."
cp "$NGINX_CONF" "$BACKUP"

# Find line BEFORE "location /canvas/" - this is the correct insertion point
CANVAS_LINE=$(grep -n "location /canvas/" "$NGINX_CONF" | head -1 | cut -d: -f1)

if [ -z "$CANVAS_LINE" ]; then
    echo "ERROR: Could not find /canvas/ location"
    exit 1
fi

# Insert BEFORE canvas (2 lines before to account for comments)
INSERT_LINE=$((CANVAS_LINE - 1))

echo "Inserting at line $INSERT_LINE (before /canvas/ at line $CANVAS_LINE)..."

# Create temp file with the patch
{
    head -n "$INSERT_LINE" "$NGINX_CONF"
    cat << 'BLOCK'

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
    nginx -t
    exit 1
fi
