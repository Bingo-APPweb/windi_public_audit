#!/bin/bash
# ================================================================
# 🛡️ WINDI Pre-Deployment Backup
# Run BEFORE any deployment (Vault, Landing, Incisions)
# ================================================================

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BK="/opt/windi/backups/pre_deploy_${TIMESTAMP}"

echo "🛡️ WINDI Pre-Deployment Backup"
echo "================================"
echo "Backup dir: $BK"
echo ""

mkdir -p "$BK"

# === 1. Nginx configs (ALL) ===
echo "1️⃣  Nginx configs..."
sudo cp -r /etc/nginx/sites-enabled/ "$BK/nginx-sites-enabled/"
echo "   ✅ All nginx configs backed up"

# === 2. Current root content of windi-domain.com ===
echo "2️⃣  Current windi-domain.com root..."
# Find what nginx serves for windi-domain.com root
WINDI_NGINX=$(grep -rl "windi-domain.com" /etc/nginx/sites-enabled/ 2>/dev/null | head -1)
if [ -n "$WINDI_NGINX" ]; then
    echo "   Found config: $WINDI_NGINX"
    cp "$WINDI_NGINX" "$BK/windi-domain-nginx.conf"
    # Extract root or proxy_pass for /
    ROOT_DIR=$(grep -A3 'location / ' "$WINDI_NGINX" | grep -oP 'root \K[^;]+' | head -1)
    PROXY=$(grep -A3 'location / ' "$WINDI_NGINX" | grep -oP 'proxy_pass \K[^;]+' | head -1)
    if [ -n "$ROOT_DIR" ]; then
        echo "   Root dir: $ROOT_DIR"
        cp -r "$ROOT_DIR" "$BK/windi-domain-root/" 2>/dev/null || echo "   ⚠️ Could not copy root dir"
    fi
    echo "   Proxy: ${PROXY:-none}"
else
    echo "   ⚠️ No nginx config found for windi-domain.com"
fi

# === 3. Governance dashboard HTML ===
echo "3️⃣  Governance dashboard..."
DASH=$(find /opt/windi -name "*.html" -exec grep -l "WINDI Governance Dashboard" {} \; 2>/dev/null | head -1)
if [ -n "$DASH" ]; then
    cp "$DASH" "$BK/governance_dashboard.html"
    echo "   ✅ Dashboard: $DASH"
else
    echo "   ⚠️ Dashboard HTML not found via search"
fi

# === 4. Forensic Ledger DB snapshot ===
echo "4️⃣  Forensic Ledger DB..."
if [ -f "/opt/windi/data/forensic_ledger.db" ]; then
    sqlite3 /opt/windi/data/forensic_ledger.db ".backup '$BK/forensic_ledger.db'"
    COUNT=$(sqlite3 /opt/windi/data/forensic_ledger.db "SELECT COUNT(*) FROM receipts;" 2>/dev/null)
    echo "   ✅ Ledger: $COUNT receipts"
else
    echo "   ⚠️ Ledger DB not found"
fi

# === 5. Active services snapshot ===
echo "5️⃣  Service snapshot..."
systemctl list-units --type=service | grep windi > "$BK/services.txt" 2>/dev/null
ss -tlnp | grep -E '80[0-9][0-9]' > "$BK/ports.txt" 2>/dev/null
echo "   ✅ Services and ports recorded"

# === 6. Desktop files ===
echo "6️⃣  Desktop D1..."
if [ -d "/opt/windi/desktop" ]; then
    cp -r /opt/windi/desktop/src "$BK/desktop-src/" 2>/dev/null || true
    echo "   ✅ Desktop source backed up"
fi

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  🛡️ Backup Complete                      ║"
echo "║  Location: $BK"
echo "║  Safe to proceed with deployment.        ║"
echo "╚══════════════════════════════════════════╝"
echo ""
ls -la "$BK/"
