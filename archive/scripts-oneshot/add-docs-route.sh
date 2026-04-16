#!/bin/bash
# Add /docs/ route to nginx for WINDI documentation
# Run: sudo bash /home/windi/add-docs-route.sh

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/home/windi/nginx-backup-docs-$(date +%Y%m%d_%H%M%S).conf"

# Backup
cp "$NGINX_CONF" "$BACKUP"
echo "Backup: $BACKUP"

# Check if route already exists
if grep -q "location /docs/" "$NGINX_CONF"; then
    echo "Route /docs/ already exists!"
    exit 0
fi

# Add route after jornal-composer block
sed -i '/add_header X-WINDI-Service "jornal-composer" always;/,/^    }$/!b;/^    }$/a\
\
    # ── WINDI Docs (static) ──────────────────────────────\
    location /docs/ {\
        alias /opt/windi/docs/;\
        index index.html;\
        try_files $uri $uri/ =404;\
        add_header Cache-Control "public, max-age=3600";\
        add_header X-WINDI-Service "windi-docs" always;\
    }' "$NGINX_CONF"

# Test nginx
nginx -t
if [ $? -eq 0 ]; then
    echo "Nginx config OK. Reloading..."
    systemctl reload nginx
    echo "Done! Test: https://windi-domain.com/docs/did/"
else
    echo "Nginx config ERROR! Restoring backup..."
    cp "$BACKUP" "$NGINX_CONF"
    exit 1
fi
