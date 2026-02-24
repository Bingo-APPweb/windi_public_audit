#!/bin/bash
# WINDI Webhook Service Installer
# Run with: sudo ./install-service.sh

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  WINDI Webhook Service Installer                               ║"
echo "║  Port: 8095 · Paperless Bridge · Three Dragons Protocol        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root: sudo ./install-service.sh"
    exit 1
fi

TSIL_DIR="/opt/windi/tsil"
SERVICE_FILE="$TSIL_DIR/windi-webhook.service"
SYSTEMD_DIR="/etc/systemd/system"

# Ensure directories exist
mkdir -p "$TSIL_DIR/logs"
mkdir -p "/opt/windi/vault/signed"
chown -R windi:windi "$TSIL_DIR/logs" "/opt/windi/vault"

# Ensure .env exists
if [ ! -f "$TSIL_DIR/.env" ]; then
    echo "⚠️  Creating .env with new HMAC secret..."
    HMAC_SECRET=$(openssl rand -hex 32)
    cat > "$TSIL_DIR/.env" << EOF
# WINDI Paperless Webhook Security
# Generated: $(date -Iseconds)
WINDI_PAPERLESS_WEBHOOK_SECRET=$HMAC_SECRET
WINDI_SIGNING_PROVIDER=paperless
WINDI_PAPERLESS_WORKSPACE_ID=1
EOF
    chmod 600 "$TSIL_DIR/.env"
    chown windi:windi "$TSIL_DIR/.env"
    echo "✓ Created $TSIL_DIR/.env"
fi

# Stop existing service if running
systemctl stop windi-webhook 2>/dev/null || true
pkill -f "schnittstelle.*webhook" 2>/dev/null || true

# Copy service file
cp "$SERVICE_FILE" "$SYSTEMD_DIR/windi-webhook.service"
echo "✓ Copied service file to $SYSTEMD_DIR"

# Reload systemd
systemctl daemon-reload
echo "✓ Reloaded systemd"

# Enable service
systemctl enable windi-webhook
echo "✓ Enabled windi-webhook service"

# Start service
systemctl start windi-webhook
sleep 2

# Check status
if systemctl is-active --quiet windi-webhook; then
    echo "✓ Service started successfully"
    echo
    echo "Service Status:"
    systemctl status windi-webhook --no-pager | head -15
    echo
    echo "Health Check:"
    curl -s http://localhost:8095/webhook/paperless/health | python3 -m json.tool 2>/dev/null || echo "Waiting for service..."
else
    echo "❌ Service failed to start"
    journalctl -u windi-webhook --no-pager -n 20
    exit 1
fi

echo
echo "═══════════════════════════════════════════════════════════════════"
echo "✅ WINDI Webhook Service installed and running"
echo
echo "Commands:"
echo "  systemctl status windi-webhook   — Check status"
echo "  systemctl restart windi-webhook  — Restart service"
echo "  journalctl -u windi-webhook -f   — Follow logs"
echo "  curl localhost:8095/webhook/paperless/health  — Health check"
echo "═══════════════════════════════════════════════════════════════════"
