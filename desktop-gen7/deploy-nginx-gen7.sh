#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# WINDI Desktop GEN 7 — nginx Configuration Script
# Created: 2026-03-15
# "AI processes. Human decides. WINDI guarantees."
# ═══════════════════════════════════════════════════════════════

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP_DIR="/opt/windi/backups/nginx"
BACKUP_FILE="${BACKUP_DIR}/windi-domain.com.bak.$(date +%Y%m%d%H%M%S)"

echo "═══════════════════════════════════════════════════════════════"
echo "  WINDI Desktop GEN 7 — nginx Configuration"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# ─── FASE 1: Backup ───────────────────────────────────────────────
echo "[1/5] Creating backup..."
sudo mkdir -p "$BACKUP_DIR"
sudo cp "$NGINX_CONF" "$BACKUP_FILE"
echo "      ✅ Backup: $BACKUP_FILE"
echo ""

# ─── FASE 2: Add upstream ─────────────────────────────────────────
echo "[2/5] Adding upstream windi_desktop_gen7..."
if grep -q "windi_desktop_gen7" "$NGINX_CONF"; then
    echo "      ⚠️  upstream already exists, skipping"
else
    sudo sed -i '/upstream windi_pioneer.*8120/a upstream windi_desktop_gen7 { server 127.0.0.1:8119 max_fails=3 fail_timeout=30s; keepalive 16; }' "$NGINX_CONF"
    echo "      ✅ upstream windi_desktop_gen7 added"
fi
echo ""

# ─── FASE 3: Add location block ───────────────────────────────────
echo "[3/5] Adding location /desktop-gen7/..."
if grep -q "/desktop-gen7/" "$NGINX_CONF"; then
    echo "      ⚠️  location already exists, skipping"
else
    # Find the line after /desktop/ block closes and insert new location
    sudo sed -i '/location \^~ \/desktop\/ {/,/^    }/ {
        /^    }$/a\
\
    # ── A4 Desk Desktop GEN 7 (:8119 staging) ──────────────────\
    location ^~ /desktop-gen7/ {\
        proxy_pass http://windi_desktop_gen7/;\
        proxy_http_version 1.1;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
    }
    }' "$NGINX_CONF"
    echo "      ✅ location /desktop-gen7/ added"
fi
echo ""

# ─── FASE 4: Test nginx config ────────────────────────────────────
echo "[4/5] Testing nginx configuration..."
echo ""
if sudo nginx -t; then
    echo ""
    echo "      ✅ nginx test passed"
else
    echo ""
    echo "      ❌ nginx test FAILED"
    echo "      Restoring backup..."
    sudo cp "$BACKUP_FILE" "$NGINX_CONF"
    echo "      ✅ Backup restored"
    echo ""
    echo "      Script aborted. Config unchanged."
    exit 1
fi
echo ""

# ─── FASE 5: Reload nginx ─────────────────────────────────────────
echo "[5/5] Reloading nginx..."
sudo systemctl reload nginx
echo "      ✅ nginx reloaded"
echo ""

# ─── Verification ─────────────────────────────────────────────────
echo "═══════════════════════════════════════════════════════════════"
echo "  Verification"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Testing /desktop-gen7/health..."
sleep 1
HEALTH=$(curl -s https://windi-domain.com/desktop-gen7/health 2>/dev/null || echo "FAILED")
echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
echo ""

echo "Testing /desktop-gen7/api/dragon/status..."
DRAGON=$(curl -s https://windi-domain.com/desktop-gen7/api/dragon/status 2>/dev/null || echo "FAILED")
echo "$DRAGON" | python3 -m json.tool 2>/dev/null || echo "$DRAGON"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "  GEN 7 nginx config complete!"
echo "  URL: https://windi-domain.com/desktop-gen7/"
echo "═══════════════════════════════════════════════════════════════"
