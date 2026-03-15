#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# WINDI Desktop GEN 7 — SWAP TO PRODUCTION
# Authorized: 2026-03-15
# "AI processes. Human decides. WINDI guarantees."
# ═══════════════════════════════════════════════════════════════

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP_DIR="/opt/windi/backups/nginx"
BACKUP_FILE="${BACKUP_DIR}/windi-domain.com.pre-swap.$(date +%Y%m%d%H%M%S)"

echo "═══════════════════════════════════════════════════════════════"
echo "  WINDI Desktop GEN 7 — SWAP TO PRODUCTION"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "  Source: :8119 (GEN 7 staging)"
echo "  Target: /desktop/ (production)"
echo ""

# ─── FASE 1: Backup ───────────────────────────────────────────────
echo "[1/5] Creating nginx backup..."
sudo mkdir -p "$BACKUP_DIR"
sudo cp "$NGINX_CONF" "$BACKUP_FILE"
echo "      ✅ Backup: $BACKUP_FILE"
echo ""

# ─── FASE 2: Swap upstream ────────────────────────────────────────
echo "[2/5] Swapping upstream windi_desktop :8100 → :8119..."
sudo sed -i 's/upstream windi_desktop.*{.*server 127.0.0.1:8100/upstream windi_desktop      { server 127.0.0.1:8119/' "$NGINX_CONF"
echo "      ✅ Upstream updated"
echo ""

# ─── FASE 3: Verify change ────────────────────────────────────────
echo "[3/5] Verifying change..."
grep "upstream windi_desktop" "$NGINX_CONF"
echo ""

# ─── FASE 4: Test nginx ───────────────────────────────────────────
echo "[4/5] Testing nginx configuration..."
if sudo nginx -t; then
    echo "      ✅ nginx test passed"
else
    echo "      ❌ nginx test FAILED — restoring backup"
    sudo cp "$BACKUP_FILE" "$NGINX_CONF"
    echo "      ✅ Backup restored"
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
echo "  Verification — Production Tests"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "Testing https://windi-domain.com/desktop/health..."
sleep 1
curl -s https://windi-domain.com/desktop/health | python3 -m json.tool 2>/dev/null | head -20
echo ""

echo "Testing https://windi-domain.com/desktop/api/dragon/status..."
curl -s https://windi-domain.com/desktop/api/dragon/status | python3 -m json.tool 2>/dev/null
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "  🎉 SWAP COMPLETE — GEN 7 IS NOW PRODUCTION"
echo "  URL: https://windi-domain.com/desktop/"
echo "═══════════════════════════════════════════════════════════════"
