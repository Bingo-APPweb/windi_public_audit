#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# W-LAB-001 — Nginx Route Patch
# Date: 2026-04-14
# Adds: /lab/ route → 127.0.0.1:8151
# ═══════════════════════════════════════════════════════════════

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP_DIR="/opt/windi/w-lab-001"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "═══════════════════════════════════════════════════"
echo "W-LAB-001 Nginx Patch"
echo "═══════════════════════════════════════════════════"

# 1. Check if route already exists
if grep -q "location /lab/" "$NGINX_CONF"; then
    echo "✅ Route /lab/ already exists. Nothing to do."
    exit 0
fi

# 2. Backup
echo "📦 Creating backup..."
cp "$NGINX_CONF" "$BACKUP_DIR/nginx-backup-lab-$TIMESTAMP.conf"
echo "   Saved: $BACKUP_DIR/nginx-backup-lab-$TIMESTAMP.conf"

# 3. Find insertion point (after /enterprise/ blocks, before /dispatch/)
echo "🔧 Adding /lab/ route..."

# Insert the W-LAB route block after /enterprise/api/ location block
sed -i '/location \/enterprise\/api\//,/^    }/ {
    /^    }/ a\
\
    # ── W-LAB-001: Governance Training Laboratory ──────────────────────────────\
    location /lab/ {\
        proxy_pass http://127.0.0.1:8151/;\
        proxy_http_version 1.1;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
    }\
    location /lab/api/ {\
        proxy_pass http://127.0.0.1:8151/api/;\
        proxy_http_version 1.1;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
    }\
    # ── END W-LAB-001 ──────────────────────────────────────────────────────────
}' "$NGINX_CONF"

# 4. Test config
echo "🧪 Testing nginx configuration..."
nginx -t

# 5. Reload
echo "🔄 Reloading nginx..."
systemctl reload nginx

# 6. Verify
echo ""
echo "═══════════════════════════════════════════════════"
echo "✅ W-LAB-001 route added successfully!"
echo ""
echo "URLs:"
echo "   Dashboard: https://windi-domain.com/lab/"
echo "   API:       https://windi-domain.com/lab/api/..."
echo "═══════════════════════════════════════════════════"
