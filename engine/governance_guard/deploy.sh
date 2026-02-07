#!/bin/bash
# ═══════════════════════════════════════════════════════════
#   WINDI Governance Guard — Deployment Script
#   "AI processes. Human decides. WINDI guarantees."
# ═══════════════════════════════════════════════════════════

set -e

echo "⚔️  WINDI Governance Guard v1.0 — Deployment"
echo "═══════════════════════════════════════════════"

WINDI_BASE="/opt/windi"
GUARD_DIR="${WINDI_BASE}/engine"
GUARD_DATA="${WINDI_BASE}/data/guard"
LOG_DIR="/var/log/windi"

# 1. Create directories
echo "📁 Creating directories..."
sudo mkdir -p "${GUARD_DATA}/reports"
sudo mkdir -p "${LOG_DIR}"
sudo chown -R windi:windi "${GUARD_DATA}"
sudo chown -R windi:windi "${LOG_DIR}"

# 2. Backup existing (if any)
if [ -f "${GUARD_DIR}/governance_guard.py" ]; then
    BK="${WINDI_BASE}/backups/guard_pre_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BK"
    cp "${GUARD_DIR}/governance_guard.py" "$BK/"
    echo "💾 Backup saved to ${BK}"
fi

# 3. Deploy Guard
echo "🚀 Deploying governance_guard.py..."
cp governance_guard.py "${GUARD_DIR}/governance_guard.py"
chmod +x "${GUARD_DIR}/governance_guard.py"
chown windi:windi "${GUARD_DIR}/governance_guard.py"

# 4. Install systemd service
echo "⚙️  Installing systemd service..."
sudo cp windi-guard.service /etc/systemd/system/
sudo systemctl daemon-reload

# 5. Quick test — single scan
echo ""
echo "🔍 Running initial scan..."
cd "${GUARD_DIR}"
sudo -u windi python3 governance_guard.py scan

# 6. Ask to enable daemon
echo ""
read -p "🐉 Enable Governance Guard daemon? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo systemctl enable windi-guard
    sudo systemctl start windi-guard
    echo "✅ Governance Guard daemon started!"
    echo "   Status: sudo systemctl status windi-guard"
    echo "   Logs:   sudo journalctl -u windi-guard -f"
    echo "   API:    http://localhost:8091/api/guard/status"
else
    echo "ℹ️  Daemon not started. Run manually:"
    echo "   python3 ${GUARD_DIR}/governance_guard.py daemon --api"
fi

echo ""
echo "═══════════════════════════════════════════════"
echo "⚔️  Governance Guard deployed successfully!"
echo "   \"AI processes. Human decides. WINDI guarantees.\""
echo "═══════════════════════════════════════════════"
