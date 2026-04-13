#!/bin/bash
# ═══════════════════════════════════════════════
# W-CACHE-001 · DEPLOY SCRIPT
# Verifiable Cache Layer for Regulated Systems
# ═══════════════════════════════════════════════

set -e

echo "🚀 Deploying W-CACHE-001..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

BASE_DIR="/opt/windi/w-cache-001"
VENV_DIR="$BASE_DIR/venv"
DATA_DIR="$BASE_DIR/data"
LOG_DIR="/var/log/windi"

# 1. Create directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p "$DATA_DIR"
mkdir -p "$LOG_DIR"

# 2. Create virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
fi

# 3. Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$BASE_DIR/requirements.txt"

# 4. Set permissions
echo -e "${YELLOW}Setting permissions...${NC}"
chown -R windi:windi "$BASE_DIR"
chown -R windi:windi "$LOG_DIR"

# 5. Install systemd service
echo -e "${YELLOW}Installing systemd service...${NC}"
cp "$BASE_DIR/wcache.service" /etc/systemd/system/wcache.service
systemctl daemon-reload

# 6. Start service
echo -e "${YELLOW}Starting service...${NC}"
systemctl enable wcache.service
systemctl restart wcache.service

# 7. Wait and verify
sleep 3
if systemctl is-active --quiet wcache.service; then
    echo -e "${GREEN}✅ W-CACHE-001 deployed successfully!${NC}"
    echo ""
    echo "Service: wcache.service"
    echo "Port: 8160"
    echo "API: http://localhost:8160/api/cache/v1"
    echo "Docs: http://localhost:8160/docs"
    echo ""

    # Quick health check
    curl -s http://localhost:8160/health | python3 -m json.tool
else
    echo "❌ Service failed to start"
    systemctl status wcache.service
    exit 1
fi
