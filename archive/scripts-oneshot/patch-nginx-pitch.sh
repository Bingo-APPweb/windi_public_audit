#!/bin/bash
# Patch nginx for /pitch/ route
# Run with: sudo bash /home/windi/patch-nginx-pitch.sh

set -e
NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/home/windi/nginx-backup-pitch-$(date +%Y%m%d_%H%M%S).conf"

echo "=== WINDI Pitch Route Patch ==="
echo "Backup: $BACKUP"
cp "$NGINX_CONF" "$BACKUP"

# Check if /pitch/ already exists
if grep -q "location /pitch/" "$NGINX_CONF"; then
    echo "ERROR: /pitch/ route already exists!"
    exit 1
fi

# Insert pitch route after /docs/ block
sed -i '/add_header X-WINDI-Service "windi-docs" always;/,/^[[:space:]]*}/ {
    /^[[:space:]]*}/ a\
\
    # ── Pitch Dashboard for VCs (/pitch/) ──────────────────\
    location /pitch/ {\
        alias /opt/windi/pitch/;\
        index index.html;\
        try_files $uri $uri/ /pitch/index.html;\
        add_header X-WINDI-Service "pitch-dashboard" always;\
    }
}' "$NGINX_CONF"

echo "--- Testing nginx config ---"
nginx -t

if [ $? -eq 0 ]; then
    echo "--- Reloading nginx ---"
    systemctl reload nginx
    echo ""
    echo "=== DONE ==="
    echo "Test: curl -s -o /dev/null -w '%{http_code}' https://windi-domain.com/pitch/"
else
    echo "ERROR: nginx config test failed!"
    echo "Restoring backup..."
    cp "$BACKUP" "$NGINX_CONF"
    exit 1
fi
