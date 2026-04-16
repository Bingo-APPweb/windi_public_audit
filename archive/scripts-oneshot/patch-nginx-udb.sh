#!/bin/bash
# Patch nginx for W-UDB-001 Dashboard
# Run with: sudo bash patch-nginx-udb.sh

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/home/windi/nginx-backup-udb-$(date +%Y%m%d_%H%M%S).conf"

echo "=== W-UDB-001 Nginx Patch ==="
echo "Backing up to: $BACKUP"
cp "$NGINX_CONF" "$BACKUP"

# Insert UDB location block after VD-MASS
sed -i '/# ═══ END W-VD-MASS-001 ═══/a\
\
      # ═══ W-UDB-001 Unified Dashboard :8140 ═══\
      location /udb/ {\
          proxy_pass http://127.0.0.1:8140/;\
          proxy_http_version 1.1;\
          proxy_set_header Host $host;\
          proxy_set_header X-Real-IP $remote_addr;\
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
          proxy_set_header X-Forwarded-Proto $scheme;\
          proxy_read_timeout 300s;\
          proxy_connect_timeout 10s;\
          # SSE support\
          proxy_buffering off;\
          proxy_cache off;\
      }\
      # ═══ END W-UDB-001 ═══' "$NGINX_CONF"

echo "Testing nginx config..."
nginx -t

if [ $? -eq 0 ]; then
    echo "Reloading nginx..."
    systemctl reload nginx
    echo "=== SUCCESS ==="
    echo "UDB available at: https://windi-domain.com/udb/"
else
    echo "=== CONFIG ERROR - Restoring backup ==="
    cp "$BACKUP" "$NGINX_CONF"
    exit 1
fi
