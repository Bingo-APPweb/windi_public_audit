#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# WINDI M3 Export Engine — Deployment Script
# ═══════════════════════════════════════════════════════════════
# Run on Strato server: bash deploy_m3.sh
# Prerequisites: Python 3.11+, pip
#
# Port: 8103 (new service)
# Service: windi-export.service
# ═══════════════════════════════════════════════════════════════

set -e

echo "🐉 WINDI M3 Export Engine — Deployment"
echo "======================================="

# ── 1. Pre-flight checks ──
echo ""
echo "1️⃣  Pre-flight checks..."

# Check port availability
if ss -tlnp | grep -q ':8103 '; then
    echo "⚠️  Port 8103 already in use:"
    ss -tlnp | grep ':8103'
    echo "Kill existing process? (y/n)"
    read -r KILL_EXISTING
    if [ "$KILL_EXISTING" = "y" ]; then
        PID=$(ss -tlnp | grep ':8103' | grep -oP 'pid=\K[0-9]+')
        kill "$PID" 2>/dev/null && echo "Killed PID $PID" || true
        sleep 2
    else
        echo "Abort."
        exit 1
    fi
fi
echo "✅ Port 8103 available"

# ── 2. Create directory ──
echo ""
echo "2️⃣  Setting up directory..."
EXPORT_DIR="/opt/windi/export-engine"
mkdir -p "$EXPORT_DIR"
mkdir -p /opt/windi/logs

# ── 3. Install dependencies ──
echo ""
echo "3️⃣  Installing dependencies..."
pip3 install reportlab qrcode pillow fastapi uvicorn --break-system-packages -q 2>/dev/null || \
pip3 install reportlab qrcode pillow fastapi uvicorn -q

# ── 4. Deploy files ──
echo ""
echo "4️⃣  Deploying files..."
# Copy the engine files (assumes they're in current directory)
cp windi_export_engine.py "$EXPORT_DIR/"
cp d1_export_endpoint.py "$EXPORT_DIR/"
echo "✅ Files deployed to $EXPORT_DIR"

# ── 5. Create .env ──
echo ""
echo "5️⃣  Creating .env..."
cat > "$EXPORT_DIR/.env" << 'ENVEOF'
WINDI_EXPORT_PORT=8103
WINDI_EXPORT_HOST=0.0.0.0
WINDI_LOG_LEVEL=info
ENVEOF
chmod 600 "$EXPORT_DIR/.env"
echo "✅ .env created"

# ── 6. Create systemd service ──
echo ""
echo "6️⃣  Creating systemd service..."
sudo tee /etc/systemd/system/windi-export.service << 'SVCEOF'
[Unit]
Description=WINDI M3 Export Engine v1.0.0
Documentation=https://admin.windia4desk.tech/desktop/api/export/health
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=windi
Group=windi
WorkingDirectory=/opt/windi/export-engine
EnvironmentFile=/opt/windi/export-engine/.env
ExecStart=/usr/bin/python3 -m uvicorn d1_export_endpoint:app --host 0.0.0.0 --port 8103
Restart=always
RestartSec=5
StandardOutput=append:/opt/windi/logs/export-engine.log
StandardError=append:/opt/windi/logs/export-engine.log

# Security hardening
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/opt/windi/logs /opt/windi/export-engine

[Install]
WantedBy=multi-user.target
SVCEOF

# ── 7. Enable and start ──
echo ""
echo "7️⃣  Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable windi-export.service
sudo systemctl start windi-export.service
sleep 3

# ── 8. Verify ──
echo ""
echo "8️⃣  Verifying..."
sudo systemctl status windi-export.service --no-pager | head -15

echo ""
echo "Health check:"
curl -s http://localhost:8103/api/export/health | python3 -m json.tool 2>/dev/null || echo "⚠️ Health check pending..."

# ── 9. Nginx snippet ──
echo ""
echo "9️⃣  Nginx snippet (add to admin.windia4desk.tech config):"
echo ""
cat << 'NGINX'
    # ── M3 Export Engine (:8103) ────────────────────────
    location /desktop/api/export/ {
        proxy_pass http://127.0.0.1:8103/api/export/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
        add_header Access-Control-Allow-Origin "https://admin.windia4desk.tech" always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
        if ($request_method = OPTIONS) {
            return 204;
        }
    }
    # ── END M3 Export Engine ──────────────────────────────
NGINX

echo ""
echo "═══════════════════════════════════════════════════"
echo "🐉 M3 Export Engine deployed!"
echo "  Local:  http://localhost:8103/api/export/health"
echo "  Public: https://admin.windia4desk.tech/desktop/api/export/health"
echo "═══════════════════════════════════════════════════"
echo ""
echo "📋 Remaining steps:"
echo "  1. Add nginx snippet above to admin.windia4desk.tech config"
echo "  2. sudo nginx -t && sudo systemctl reload nginx"
echo "  3. Integrate ExportPdfButton.jsx into D1 frontend"
echo "  4. Update WINDI Ports documentation (8103=export-engine)"
