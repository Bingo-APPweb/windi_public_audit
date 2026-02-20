#!/bin/bash
# ============================================================================
# WINDI Desktop — Deployment Script
# ============================================================================
# Server: Strato VPS (87.106.29.233)
# Domain: admin.windia4desk.tech
# Path:   /desktop/
# Port:   8100
# Access: Public
# ============================================================================
#
# Wallet (/) → Desktop (/desktop/) → Suite · Sealing · War Room
#
# AI processes. Human decides. WINDI guarantees.
#
# Usage:
#   1. Upload: scp -r windi-suite-deploy/ windi@87.106.29.233:/opt/windi/
#   2. SSH:    ssh windi@87.106.29.233
#   3. Run:    bash /opt/windi/windi-suite-deploy/deploy.sh
# ============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
GOLD='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${GOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GOLD}║          WINDI Desktop — Deployment                  ║${NC}"
echo -e "${GOLD}║    Wallet → Desktop → Suite · Sealing · War Room    ║${NC}"
echo -e "${GOLD}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

DEPLOY_DIR="/opt/windi/windi-suite-deploy"
TARGET_DIR="/opt/windi/desktop"
PORT=8100
NGINX_CONF="/etc/nginx/sites-enabled/admin.windia4desk.tech"
SERVICE_NAME="windi-desktop"

# ── Step 1: Pre-flight ──
echo -e "${GOLD}[1/9]${NC} Pre-flight checks..."

if [ ! -d "$DEPLOY_DIR/html" ]; then
    echo -e "${RED}ERROR: $DEPLOY_DIR/html not found.${NC}"
    echo "Upload the windi-suite-deploy folder to /opt/windi/ first."
    exit 1
fi

for f in index.html suite.html sealing.html warroom.html; do
    if [ ! -f "$DEPLOY_DIR/html/$f" ]; then
        echo -e "${RED}ERROR: $f not found in $DEPLOY_DIR/html/${NC}"
        exit 1
    fi
done

if ss -tlnp | grep -q ":${PORT} "; then
    echo -e "${GOLD}  Port ${PORT} in use — stopping existing service...${NC}"
    sudo systemctl stop ${SERVICE_NAME} 2>/dev/null || true
    sleep 2
fi

echo -e "${GREEN}  ✓ Pre-flight OK${NC}"

# ── Step 2: Backup ──
echo -e "${GOLD}[2/9]${NC} Creating backup..."

BK="/opt/windi/backups/pre_desktop_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BK"
sudo cp "$NGINX_CONF" "$BK/nginx.conf" 2>/dev/null || true
if [ -d "$TARGET_DIR" ]; then
    cp -r "$TARGET_DIR" "$BK/desktop_old"
fi
echo -e "${GREEN}  ✓ Backup: $BK${NC}"

# ── Step 3: Deploy files ──
echo -e "${GOLD}[3/9]${NC} Deploying files..."

mkdir -p "$TARGET_DIR"
mkdir -p "$TARGET_DIR/pitch"
mkdir -p /opt/windi/logs

cp "$DEPLOY_DIR/html/index.html"   "$TARGET_DIR/"
cp "$DEPLOY_DIR/html/suite.html"   "$TARGET_DIR/"
cp "$DEPLOY_DIR/html/sealing.html" "$TARGET_DIR/"
cp "$DEPLOY_DIR/html/warroom.html" "$TARGET_DIR/"

if [ -f "$DEPLOY_DIR/pitch/WINDI_Suite_Pitch_Deck.pptx" ]; then
    cp "$DEPLOY_DIR/pitch/WINDI_Suite_Pitch_Deck.pptx" "$TARGET_DIR/pitch/"
    echo -e "${GREEN}  ✓ Pitch deck deployed${NC}"
fi

echo -e "${GREEN}  ✓ $(ls $TARGET_DIR/*.html | wc -l) HTML files deployed to $TARGET_DIR/${NC}"

# ── Step 4: Create server ──
echo -e "${GOLD}[4/9]${NC} Creating HTTP server..."

cat > "$TARGET_DIR/serve.py" << 'PYEOF'
#!/usr/bin/env python3
"""WINDI Desktop — Static Server with Health Endpoint"""
import http.server
import socketserver
import os
import sys
import json
from datetime import datetime

PORT = int(os.environ.get("PORT", 8100))
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class DesktopHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            health = {
                "service": "windi-desktop",
                "status": "operational",
                "version": "1.0.0",
                "port": PORT,
                "path": "/desktop/",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "pages": {
                    "landing": "index.html",
                    "suite": "suite.html",
                    "sealing": "sealing.html",
                    "warroom": "warroom.html"
                },
                "wallet_integration": True,
                "principle": "AI processes. Human decides. WINDI guarantees."
            }
            self.wfile.write(json.dumps(health, indent=2).encode())
            return
        super().do_GET()

    def log_message(self, format, *args):
        sys.stdout.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {args[0]}\n")
        sys.stdout.flush()

if __name__ == "__main__":
    with socketserver.TCPServer(("0.0.0.0", PORT), DesktopHandler) as httpd:
        print(f"WINDI Desktop serving on port {PORT}")
        print(f"Directory: {DIRECTORY}")
        print(f"Health: http://localhost:{PORT}/health")
        httpd.serve_forever()
PYEOF

chmod +x "$TARGET_DIR/serve.py"
echo -e "${GREEN}  ✓ Server script created${NC}"

# ── Step 5: systemd service ──
echo -e "${GOLD}[5/9]${NC} Creating systemd service..."

sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null << EOF
[Unit]
Description=WINDI Desktop v1.0.0
Documentation=https://admin.windia4desk.tech/desktop/health
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=windi
Group=windi
WorkingDirectory=$TARGET_DIR
Environment=PORT=$PORT
ExecStart=/usr/bin/python3 $TARGET_DIR/serve.py
Restart=always
RestartSec=5
StandardOutput=append:/opt/windi/logs/desktop.log
StandardError=append:/opt/windi/logs/desktop.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}.service
sudo systemctl restart ${SERVICE_NAME}.service
sleep 2

if sudo systemctl is-active --quiet ${SERVICE_NAME}; then
    echo -e "${GREEN}  ✓ ${SERVICE_NAME} active on port ${PORT}${NC}"
else
    echo -e "${RED}  ✗ Service failed to start!${NC}"
    sudo journalctl -u ${SERVICE_NAME} --no-pager -n 10
    exit 1
fi

# ── Step 6: nginx /desktop/ proxy ──
echo -e "${GOLD}[6/9]${NC} Configuring nginx..."

if grep -q "location /desktop/" "$NGINX_CONF"; then
    echo -e "${CYAN}  /desktop/ already exists in nginx — skipping injection${NC}"
else
    SSL_LINE=$(grep -n "listen 443 ssl" "$NGINX_CONF" | head -1 | cut -d: -f1)

    if [ -z "$SSL_LINE" ]; then
        echo -e "${RED}  Could not find 'listen 443 ssl' — manual injection needed${NC}"
        echo ""
        echo "    Add this block inside the server {} block:"
        echo ""
        echo '    # ── WINDI Desktop (:8100) ──────────────────────'
        echo '    location /desktop/ {'
        echo '        proxy_pass http://127.0.0.1:8100/;'
        echo '        proxy_http_version 1.1;'
        echo '        proxy_set_header Host $host;'
        echo '        proxy_set_header X-Real-IP $remote_addr;'
        echo '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;'
        echo '        proxy_set_header X-Forwarded-Proto $scheme;'
        echo '        proxy_read_timeout 120s;'
        echo '        proxy_connect_timeout 10s;'
        echo '    }'
        echo '    # ── END WINDI Desktop ──────────────────────────'
    else
        INJECT_LINE=$((SSL_LINE - 2))

        sudo sed -i "${INJECT_LINE}a\\
\\
    # ── WINDI Desktop (:8100) ──────────────────────\\
    location /desktop/ {\\
        proxy_pass http://127.0.0.1:8100/;\\
        proxy_http_version 1.1;\\
        proxy_set_header Host \$host;\\
        proxy_set_header X-Real-IP \$remote_addr;\\
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\\
        proxy_set_header X-Forwarded-Proto \$scheme;\\
        proxy_read_timeout 120s;\\
        proxy_connect_timeout 10s;\\
    }\\
    # ── END WINDI Desktop ──────────────────────────" "$NGINX_CONF"

        echo -e "${GREEN}  ✓ /desktop/ location injected${NC}"
    fi

    if sudo nginx -t 2>&1 | grep -q "successful"; then
        sudo systemctl reload nginx
        echo -e "${GREEN}  ✓ nginx reloaded${NC}"
    else
        echo -e "${RED}  ✗ nginx test failed — restoring backup...${NC}"
        sudo cp "$BK/nginx.conf" "$NGINX_CONF"
        sudo nginx -t && sudo systemctl reload nginx
        echo -e "${GOLD}  Backup restored. Add location manually.${NC}"
    fi
fi

# ── Step 7: Health checks ──
echo -e "${GOLD}[7/9]${NC} Health checks..."

HEALTH=$(curl -s http://localhost:${PORT}/health 2>/dev/null)
if echo "$HEALTH" | grep -q "operational"; then
    echo -e "${GREEN}  ✓ /health → operational${NC}"
else
    echo -e "${RED}  ✗ /health failed${NC}"
fi

for page in index.html suite.html sealing.html warroom.html; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${PORT}/${page} 2>/dev/null)
    if [ "$STATUS" = "200" ]; then
        echo -e "${GREEN}  ✓ ${page} → ${STATUS}${NC}"
    else
        echo -e "${RED}  ✗ ${page} → ${STATUS}${NC}"
    fi
done

# ── Step 8: Wallet update reminder ──
echo -e "${GOLD}[8/9]${NC} Wallet integration..."
echo ""
echo -e "  ${CYAN}NEXT STEP: Update the Wallet page to link to Desktop${NC}"
echo -e "  The Wallet (port 8099) needs a button/link pointing to /desktop/"
echo -e "  This will complete the flow: Wallet → Desktop → Suite/Sealing/WarRoom"
echo ""

# ── Step 9: Summary ──
echo -e "${GOLD}[9/9]${NC} Deployment complete!"
echo ""
echo -e "${GOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GOLD}║              WINDI DESKTOP — LIVE                    ║${NC}"
echo -e "${GOLD}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${GREEN}Service:${NC}   ${SERVICE_NAME} (systemd, auto-restart)"
echo -e "  ${GREEN}Port:${NC}      ${PORT}"
echo -e "  ${GREEN}Directory:${NC} ${TARGET_DIR}/"
echo -e "  ${GREEN}Access:${NC}    Public"
echo ""
echo -e "  ${GOLD}FLOW:${NC}"
echo -e "    Wallet    → https://admin.windia4desk.tech/"
echo -e "      ↓"
echo -e "    Desktop   → https://admin.windia4desk.tech/desktop/"
echo -e "      ├── Suite    → /desktop/suite.html"
echo -e "      ├── Sealing  → /desktop/sealing.html"
echo -e "      ├── War Room → /desktop/warroom.html"
echo -e "      └── Pitch    → /desktop/pitch/WINDI_Suite_Pitch_Deck.pptx"
echo ""
echo -e "  ${GOLD}Health:${NC}    https://admin.windia4desk.tech/desktop/health"
echo ""
echo -e "  ${GOLD}Commands:${NC}"
echo -e "    sudo systemctl status ${SERVICE_NAME}"
echo -e "    sudo systemctl restart ${SERVICE_NAME}"
echo -e "    tail -f /opt/windi/logs/desktop.log"
echo ""
echo -e "  ${GOLD}AI processes. Human decides. WINDI guarantees.${NC}"
echo ""
