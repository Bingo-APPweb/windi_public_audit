#!/bin/bash
# ══════════════════════════════════════════════════════════════
# WINDI Nginx Patch — VPR + Verify Public v1
# Date: 2026-03-19
# Author: Gêmeo (G1 READ + G3 PROPOSE → Human APPROVED)
# Purpose: Add VPR pages + restore verify-public v1 route
# ══════════════════════════════════════════════════════════════

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/home/windi/nginx-backup-vpr-$(date +%Y%m%d_%H%M%S).conf"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "WINDI Patch: VPR + Verify Public v1"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Backup
echo "[1/4] Creating backup → $BACKUP"
sudo cp "$NGINX_CONF" "$BACKUP"

# 2. Check if locations already exist
if grep -q "verify-public/vpr/" "$NGINX_CONF"; then
    echo "[!] /verify-public/vpr/ already exists. Aborting."
    exit 1
fi

# 3. Insert VPR + Verify v1 locations BEFORE the existing /verify-public/viewer/ block
# This ensures correct nginx matching order (most specific first)
echo "[2/4] Inserting VPR + Verify v1 locations..."

sudo sed -i '/# ── JMPG Viewer v2.2 (static) ────────────────────────/i\
    # ── VPR Pages (Personal Verify Pages) ────────────────────\
    # Serves static HTML for verified individuals (e.g., /verify-public/vpr/jober/)\
    location ^~ /verify-public/vpr/ {\
        alias /opt/windi/verify-public/vpr/;\
        index index.html;\
        try_files $uri $uri/ =404;\
        add_header Cache-Control "public, max-age=3600";\
        add_header X-WINDI-Service "vpr-pages" always;\
    }\
\
    # ── Verify Public v1 Internal (:8114) ────────────────────\
    # Internal verification tool — coexists with viewer and vpr\
    location /verify-public/ {\
        proxy_pass http://127.0.0.1:8114/;\
        proxy_http_version 1.1;\
        add_header X-WINDI-Service "verify-v1" always;\
    }\
' "$NGINX_CONF"

# 4. Test nginx config
echo "[3/4] Testing nginx configuration..."
sudo nginx -t

# 5. Reload
echo "[4/4] Reloading nginx..."
sudo systemctl reload nginx

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ PATCH APPLIED"
echo ""
echo "New locations:"
echo "  /verify-public/vpr/   → static VPR pages"
echo "  /verify-public/       → :8114 (verify v1 internal)"
echo "  /verify-public/viewer/→ JMPG viewer (unchanged)"
echo ""
echo "Test URLs:"
echo "  curl -I https://windi-domain.com/verify-public/vpr/jober/"
echo "  curl -I https://windi-domain.com/verify-public/"
echo ""
echo "Backup saved: $BACKUP"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
