#!/bin/bash
# W-BRIDGE-001 Nginx Patch v2
# Adds /watch/ location to proxy to bridge service on :8143
# All endpoints now under /watch/ (stream, direct, etc.)

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/home/windi/nginx-backup-bridge-$(date +%Y%m%d_%H%M%S).conf"

echo "=== W-BRIDGE-001 Nginx Patch v2 ==="

# Backup
sudo cp "$NGINX_CONF" "$BACKUP"
echo "✅ Backup: $BACKUP"

# Check if /watch/ already exists
if grep -q "location /watch/" "$NGINX_CONF"; then
    echo "⚠️  /watch/ location already exists"
    exit 0
fi

# Find the line with location /udb/ and add /watch/ before it
sudo sed -i '/location \/udb\//i\
    # W-BRIDGE-001 — BIG-BRIDGE Gateway (§143)\
    # Watch page + HLS streaming + direct video\
    location /watch/ {\
        proxy_pass http://127.0.0.1:8143/watch/;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        proxy_buffering off;\
        add_header X-WINDI-Service "W-BRIDGE-001" always;\
    }\
' "$NGINX_CONF"

# Test nginx config
echo ""
echo "=== Testing nginx config ==="
sudo nginx -t

if [ $? -eq 0 ]; then
    echo ""
    echo "=== Reloading nginx ==="
    sudo systemctl reload nginx
    echo ""
    echo "=== SUCCESS ==="
    echo "Watch page: https://windi-domain.com/watch/{receipt_id}"
    echo "Stream:     https://windi-domain.com/watch/stream/{id}/playlist.m3u8"
    echo "Direct:     https://windi-domain.com/watch/direct/{id}"
else
    echo ""
    echo "=== NGINX CONFIG ERROR ==="
    echo "Restoring backup..."
    sudo cp "$BACKUP" "$NGINX_CONF"
    exit 1
fi
