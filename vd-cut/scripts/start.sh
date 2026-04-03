#!/bin/bash
# W-VD-CUT-001 — Start Script
# Liga IA+H · Kempten, Bavaria · 2026

set -e

# Configuration
APP_DIR="/opt/windi/vd-cut"
LOG_DIR="/opt/windi/logs"
PORT=8128

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}W-VD-CUT-001 — WINDI Video Cut Engine${NC}"
echo -e "${GREEN}======================================${NC}"

# Create log directory if needed
mkdir -p "$LOG_DIR"

# Check if FFmpeg is available
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}ERROR: FFmpeg not installed!${NC}"
    echo "Please run: sudo apt-get install ffmpeg"
    exit 1
fi

echo -e "${GREEN}FFmpeg: $(ffmpeg -version | head -1)${NC}"

# Check if already running
if ss -tlnp 2>/dev/null | grep -q ":$PORT"; then
    echo -e "${YELLOW}WARNING: Port $PORT already in use${NC}"
    echo "Use 'pkill -f vd_cut_server' to stop existing instance"
    exit 1
fi

# Navigate to app directory
cd "$APP_DIR"

# Start with nohup (sandbox rule - no systemd)
echo "Starting W-VD-CUT-001 on port $PORT..."

nohup python3 vd_cut_server.py > "$LOG_DIR/vd-cut.log" 2>&1 &

# Wait for startup
sleep 2

# Health check
if curl -s "http://127.0.0.1:$PORT/vd-cut/health" > /dev/null 2>&1; then
    echo -e "${GREEN}W-VD-CUT-001 started successfully on port $PORT${NC}"
    echo -e "Health: http://127.0.0.1:$PORT/vd-cut/health"
    echo -e "Logs: $LOG_DIR/vd-cut.log"
else
    echo -e "${RED}ERROR: W-VD-CUT-001 failed to start${NC}"
    echo "Check logs: tail -f $LOG_DIR/vd-cut.log"
    exit 1
fi
