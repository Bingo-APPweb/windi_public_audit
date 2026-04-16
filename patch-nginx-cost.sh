#!/bin/bash
# W-COST-001 — Add nginx route
# Run: sudo bash patch-nginx-cost.sh

set -e

CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/home/windi/nginx-backup-cost-$(date +%Y%m%d_%H%M%S).conf"

echo "=== W-COST-001 Nginx Patch ==="

cp "$CONF" "$BACKUP"
echo "✓ Backup: $BACKUP"

if grep -q "location /cost/" "$CONF"; then
    echo "✓ Route /cost/ already exists"
    exit 0
fi

# Insert before /wcache/
sed -i '/location \/wcache\//i\    # W-COST-001 — Cost Intelligence Layer\n    location /cost/ {\n        proxy_pass http://127.0.0.1:8152/;\n        proxy_set_header Host $host;\n        proxy_set_header X-Real-IP $remote_addr;\n    }\n' "$CONF"

echo "✓ Route added"

nginx -t && systemctl reload nginx
echo "✓ Nginx reloaded"
echo ""
echo "Test: https://windi-domain.com/cost/"
