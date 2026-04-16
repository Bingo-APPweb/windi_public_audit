#!/bin/bash
# §173 DID Simplification Phase 2 — Add /shared/ route
# Execute: sudo bash patch-nginx-shared.sh

set -e

CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/home/windi/nginx-backup-shared-$(date +%Y%m%d_%H%M%S).conf"

echo "=== §173 DID Simplification — Nginx Patch ==="

# Backup
cp "$CONF" "$BACKUP"
echo "✓ Backup: $BACKUP"

# Check if already exists
if grep -q "location /shared/" "$CONF"; then
    echo "✓ Route /shared/ already exists"
    exit 0
fi

# Insert before WINDI PORTAL section
sed -i '/# WINDI PORTAL · Internal Control Center/i\    # ═══════════════════════════════════════════════\n    # §173 DID Simplification — Shared Static Files\n    # ═══════════════════════════════════════════════\n\n    location /shared/ {\n        alias /opt/windi/shared/static/;\n        expires 1d;\n        add_header Cache-Control "public, immutable";\n        add_header X-Content-Type-Options nosniff;\n    }\n\n' "$CONF"

echo "✓ Route added"

# Test
nginx -t
if [ $? -eq 0 ]; then
    systemctl reload nginx
    echo "✓ Nginx reloaded"
    echo ""
    echo "=== Test ==="
    curl -s -o /dev/null -w "GET /shared/windi-did.js → HTTP %{http_code}\n" "https://windi-domain.com/shared/windi-did.js"
else
    echo "✗ Config error, restoring backup"
    cp "$BACKUP" "$CONF"
    exit 1
fi

echo ""
echo "=== Done ==="
