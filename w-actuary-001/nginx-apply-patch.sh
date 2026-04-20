#!/bin/bash
# W-ACTUARY-001 nginx precise patch
# Run with: sudo bash /opt/windi/w-actuary-001/nginx-apply-patch.sh

set -e

NGINX_CONF="/etc/nginx/sites-available/windi-domain.com"
BACKUP="$NGINX_CONF.bak.$(date +%Y%m%d%H%M%S)"

echo "🔧 W-ACTUARY-001 nginx precise patch"
echo "──────────────────────────────"

# Create backup
cp "$NGINX_CONF" "$BACKUP"
echo "✓ Backup: $BACKUP"

# Step 1: Remove broken lines 388-417 and replace with correct /api/receipts/ block
echo "Step 1: Fixing /api/receipts/ block..."
sed -i '388,417d' "$NGINX_CONF"
sed -i '387a\
    # ── Forensic Ledger Receipts API ──────────────────────────\
    location ^~ /api/receipts/ {\
        proxy_pass http://windi_ledger/api/receipts/;\
        proxy_http_version 1.1;\
    }' "$NGINX_CONF"

# Step 2: Add actuary location before "location / {" catch-all
echo "Step 2: Adding /actuary/ location..."
# Find line number of "location / {" that proxies to windi_landing
LINE=$(grep -n "location / {" "$NGINX_CONF" | grep -v "return 301" | head -1 | cut -d: -f1)
if [ -n "$LINE" ]; then
    sed -i "${LINE}i\\
\\
    # ── W-Actuary-001 (:8015) — Verifiable Actuarial Intelligence ─────\\
    location ^~ /actuary/ {\\
        proxy_pass http://windi_actuary/;\\
        proxy_http_version 1.1;\\
    }" "$NGINX_CONF"
    echo "✓ Inserted at line $LINE"
fi

# Step 3: Test configuration
echo "Step 3: Testing nginx..."
nginx -t

# Step 4: Reload
echo "Step 4: Reloading nginx..."
systemctl reload nginx

echo "──────────────────────────────"
echo "✓ Patch applied successfully"
echo ""
echo "Test: curl -s https://windi-domain.com/actuary/health | jq"
