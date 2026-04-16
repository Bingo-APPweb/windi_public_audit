#!/bin/bash
# Patch nginx for W-FEDIVERSE-001 (:8142)

echo "=== W-FEDIVERSE-001 Nginx Patch ==="

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/home/windi/nginx-backup-fediverse-$(date +%Y%m%d_%H%M%S).conf"

# Backup
cp "$NGINX_CONF" "$BACKUP"
echo "✅ Backup: $BACKUP"

# Check if already exists
if grep -q "location /fediverse/" "$NGINX_CONF"; then
    echo "⚠️ /fediverse/ route already exists"
    exit 0
fi

# Find insertion point (after /udb/ block)
LINE=$(grep -n "location.*\/udb\/" "$NGINX_CONF" | head -1 | cut -d: -f1)

if [ -z "$LINE" ]; then
    echo "❌ Could not find /udb/ location"
    exit 1
fi

# Find the closing brace of the /udb/ block (approximately 12 lines after)
INSERT_LINE=$((LINE + 12))

# Create the new location block
FEDIVERSE_BLOCK='
    # ── W-FEDIVERSE-001 Glass Embassy (:8142) ──────────────────
    location /fediverse/ {
        proxy_pass http://127.0.0.1:8142/fediverse/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
'

# Insert the block
sed -i "${INSERT_LINE}a\\${FEDIVERSE_BLOCK}" "$NGINX_CONF"

echo ""
echo "=== Testing nginx config ==="
nginx -t

if [ $? -eq 0 ]; then
    echo ""
    echo "=== Reloading nginx ==="
    systemctl reload nginx
    echo "✅ W-FEDIVERSE-001 route added successfully"
else
    echo ""
    echo "=== NGINX CONFIG ERROR ==="
    echo "Restoring backup..."
    cp "$BACKUP" "$NGINX_CONF"
    exit 1
fi
