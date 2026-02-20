#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# WINDI Communiqué Engine — Deploy Script
# Run on Strato server as user 'windi'
# ═══════════════════════════════════════════════════════════════

set -e

echo "═══════════════════════════════════════════════════════════"
echo "  🛡️  WINDI Communiqué Engine — Deploy"
echo "  Port: 8105"
echo "  Target: /opt/windi/communique/"
echo "═══════════════════════════════════════════════════════════"

BASE_DIR="/opt/windi/communique"

# 1. Create directory structure
echo "[1/7] Creating directory structure..."
mkdir -p "$BASE_DIR"/{data,templates,static,published,backups}

# 2. Copy Python files
echo "[2/7] Copying engine files..."
cp -v communique_engine.py "$BASE_DIR/"
cp -v communique_db.py "$BASE_DIR/"
cp -v communique_publisher.py "$BASE_DIR/"
cp -v communique_renderer.py "$BASE_DIR/"

# 3. Set permissions
echo "[3/7] Setting permissions..."
chmod 755 "$BASE_DIR"/communique_engine.py
chown -R windi:windi "$BASE_DIR"

# 4. Install systemd service
echo "[4/7] Installing systemd service..."
sudo cp -v windi-communique.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable windi-communique

# 5. Check port availability
echo "[5/7] Checking port 8105..."
if ss -tlnp | grep -q ":8105 "; then
    echo "⚠️  WARNING: Port 8105 already in use!"
    ss -tlnp | grep ":8105 "
    echo "Please resolve conflict before starting."
else
    echo "✅ Port 8105 is free."
fi

# 6. Start service
echo "[6/7] Starting windi-communique..."
sudo systemctl start windi-communique
sleep 2

# 7. Health check
echo "[7/7] Health check..."
HEALTH=$(curl -s http://127.0.0.1:8105/health 2>/dev/null || echo "FAILED")
echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Deploy complete!"
echo ""
echo "  Next steps:"
echo "  1. Add nginx config (see nginx-communique.conf)"
echo "  2. sudo nginx -t && sudo systemctl reload nginx"
echo "  3. Test: curl http://127.0.0.1:8105/health"
echo "  4. Create inaugural communiqué via API"
echo "═══════════════════════════════════════════════════════════"
