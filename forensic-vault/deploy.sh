#!/bin/bash
# ================================================================
# WINDI Forensic Vault v1.0.0 — Deploy Script
# Port: 8106
# "AI processes. Human decides. WINDI guarantees."
# ================================================================

set -e

echo "🔐 WINDI Forensic Vault — Deployment"
echo "======================================"

# === 1. Pre-flight checks ===
echo ""
echo "1️⃣  Pre-flight checks..."

# Check port availability
if ss -tlnp | grep -q ":8106 "; then
    echo "⚠️  Port 8106 is already in use!"
    ss -tlnp | grep ":8106 "
    echo "Kill existing process? (y/n)"
    read -r KILL
    if [ "$KILL" = "y" ]; then
        PID=$(ss -tlnp | grep ":8106 " | grep -oP 'pid=\K[0-9]+')
        kill "$PID" 2>/dev/null && echo "✅ Killed PID $PID" || echo "⚠️  Could not kill PID"
        sleep 2
    else
        echo "❌ Aborting. Free port 8106 first."
        exit 1
    fi
fi

# Check Ledger DB
LEDGER_DB="/opt/windi/data/forensic_ledger.db"
if [ -f "$LEDGER_DB" ]; then
    RECEIPT_COUNT=$(sqlite3 "$LEDGER_DB" "SELECT COUNT(*) FROM receipts;" 2>/dev/null || echo "?")
    echo "✅ Ledger DB found: $RECEIPT_COUNT receipts"
else
    echo "⚠️  Ledger DB not found at $LEDGER_DB"
    echo "   Vault will start but queries will fail until DB exists."
fi

# === 2. Backup ===
echo ""
echo "2️⃣  Creating backup..."
BK="/opt/windi/backups/pre_vault_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BK"
sudo cp /etc/nginx/sites-enabled/admin.windia4desk.tech "$BK/nginx.conf"
echo "✅ Backup: $BK"

# === 3. Deploy files ===
echo ""
echo "3️⃣  Deploying Forensic Vault files..."
mkdir -p /opt/windi/forensic-vault
cp forensic_vault.py /opt/windi/forensic-vault/
chmod +x /opt/windi/forensic-vault/forensic_vault.py
echo "✅ Files deployed to /opt/windi/forensic-vault/"

# === 4. Create systemd service ===
echo ""
echo "4️⃣  Installing systemd service..."
sudo cp windi-vault.service /etc/systemd/system/windi-vault.service
sudo systemctl daemon-reload
sudo systemctl enable windi-vault.service
sudo systemctl start windi-vault.service
sleep 2

# Verify
if sudo systemctl is-active --quiet windi-vault.service; then
    echo "✅ Service active!"
else
    echo "❌ Service failed to start. Check logs:"
    echo "   journalctl -u windi-vault -n 20 --no-pager"
    exit 1
fi

# Health check
HEALTH=$(curl -s http://localhost:8106/health 2>/dev/null)
echo "   Health: $HEALTH"

# === 5. Inject nginx proxy ===
echo ""
echo "5️⃣  Configuring nginx proxy..."

# Find the SSL line number
SSL_LINE=$(grep -n "listen 443 ssl" /etc/nginx/sites-enabled/admin.windia4desk.tech | head -1 | cut -d: -f1)
if [ -z "$SSL_LINE" ]; then
    echo "❌ Could not find SSL line in nginx config!"
    exit 1
fi

# Check if vault is already configured
if grep -q "FORENSIC VAULT" /etc/nginx/sites-enabled/admin.windia4desk.tech; then
    echo "⚠️  Vault already in nginx config — skipping injection"
else
    # Inject before SSL line
    INJECT_LINE=$((SSL_LINE - 1))
    sudo sed -i "${INJECT_LINE}r nginx_vault_snippet.conf" /etc/nginx/sites-enabled/admin.windia4desk.tech
    echo "✅ Injected at line $INJECT_LINE"
fi

# Test nginx
echo "   Testing nginx..."
sudo nginx -t
if [ $? -eq 0 ]; then
    sudo systemctl reload nginx
    echo "✅ Nginx reloaded!"
else
    echo "❌ Nginx test failed! Restoring backup..."
    sudo cp "$BK/nginx.conf" /etc/nginx/sites-enabled/admin.windia4desk.tech
    sudo nginx -t && sudo systemctl reload nginx
    echo "   Backup restored."
    exit 1
fi

# === 6. Final verification ===
echo ""
echo "6️⃣  Final verification..."
echo ""

# Internal
echo "   Internal:  $(curl -s http://localhost:8106/health | python3 -c 'import sys,json; d=json.load(sys.stdin); print(f"✅ {d.get(\"service\")} — {d.get(\"receipts\", 0)} receipts")' 2>/dev/null || echo "❌ Failed")"

# External
echo "   External:  $(curl -s https://admin.windia4desk.tech/vault/health | python3 -c 'import sys,json; d=json.load(sys.stdin); print(f"✅ {d.get(\"service\")} via HTTPS")' 2>/dev/null || echo "⚠️  HTTPS not yet reachable (may need DNS propagation)")"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  🔐 WINDI Forensic Vault v1.0.0 DEPLOYED    ║"
echo "║                                              ║"
echo "║  Local:  http://localhost:8106               ║"
echo "║  HTTPS:  https://admin.windia4desk.tech/vault║"
echo "║  Health: /vault/health                       ║"
echo "║  API:    /vault/api/receipts                 ║"
echo "║  API:    /vault/api/stats                    ║"
echo "║  API:    /vault/api/receipt/{id}             ║"
echo "║  API:    /vault/api/export?format=csv        ║"
echo "║                                              ║"
echo "║  The Suite creates. The Vault audits.        ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "🐉 Linhagem de Ferro. O Cofre está selado."
