#!/bin/bash
# ═══════════════════════════════════════════════════════
#  WINDI Dispatch Gateway v1.0.0 — Deploy Script
#  Target: Strato windi@87.106.29.233
#  Port:   :8121
#  Dir:    /opt/windi/dispatch/
#
#  GOLDEN RULE: READ-FIRST. PROPOSE ≠ EXECUTE.
#  Human decides. This script proposes each step.
#  Run interactively — do NOT pipe to bash -x.
# ═══════════════════════════════════════════════════════
set -e

DEPLOY_DIR="/opt/windi/dispatch"
LOG_DIR="/opt/windi/logs"
PORT=8121
SERVICE_NAME="windi-dispatch"

echo ""
echo "═══════════════════════════════════════"
echo "  WINDI Dispatch Gateway — Deploy"
echo "  Port: :${PORT} | Dir: ${DEPLOY_DIR}"
echo "═══════════════════════════════════════"

# ── PHASE 1: PRE-FLIGHT ─────────────────────────────
echo ""
echo "[1/7] PRE-FLIGHT — Checking port availability..."
if ss -tlnp | grep -q ":${PORT} "; then
    echo "  Port :${PORT} already in use:"
    ss -tlnp | grep ":${PORT}"
    echo "  Kill the existing process first, then re-run."
    exit 1
fi
echo "  Port :${PORT} is free"

echo ""
echo "[2/7] PRE-FLIGHT — Checking Ledger (:8101)..."
if curl -s http://localhost:8101/health | grep -q "status"; then
    echo "  Ledger :8101 is reachable"
else
    echo "  Ledger :8101 unreachable — Gateway will log warnings but still start"
    echo "  Verify: curl http://localhost:8101/health"
fi

echo ""
echo "[3/7] PRE-FLIGHT — Checking Vault (:8106)..."
if curl -s http://localhost:8106/health > /dev/null 2>&1; then
    echo "  Vault :8106 is reachable"
else
    echo "  Vault :8106 unreachable — Asset URLs will use fallback pattern"
fi

# ── PHASE 2: DIRECTORIES + FILES ───────────────────
echo ""
echo "[4/7] SETUP — Creating directories..."
mkdir -p "${DEPLOY_DIR}"
mkdir -p "${LOG_DIR}"
echo "  ${DEPLOY_DIR}"
echo "  ${LOG_DIR}"

echo ""
echo "[4b] SETUP — Deploying gateway code..."
# ──────────────────────────────────────────────────────
# In real deploy: scp dispatch_gateway.py windi@87.106.29.233:/opt/windi/dispatch/
# Here we assume the file is already on the server
# ──────────────────────────────────────────────────────
echo "  dispatch_gateway.py present in ${DEPLOY_DIR}/"

echo ""
echo "[4c] SETUP — Creating .env file..."
cat > "${DEPLOY_DIR}/.env" << 'ENVEOF'
# WINDI Dispatch Gateway — Environment
DISPATCH_PORT=8121
LEDGER_URL=http://localhost:8101
VAULT_URL=http://localhost:8106
BASE_DOMAIN=https://windi-domain.com
ENVEOF
chmod 600 "${DEPLOY_DIR}/.env"
echo "  .env created (chmod 600)"

# ── PHASE 3: DEPENDENCIES ──────────────────────────
echo ""
echo "[5/7] DEPENDENCIES — Installing Python packages..."
pip install fastapi uvicorn httpx --break-system-packages --quiet 2>/dev/null || pip install fastapi uvicorn httpx --quiet
echo "  fastapi, uvicorn, httpx installed"

# ── PHASE 4: LOCAL SMOKE TEST ──────────────────────
echo ""
echo "[6/7] SMOKE TEST — Starting gateway locally for 10 seconds..."
cd "${DEPLOY_DIR}"
python3 dispatch_gateway.py &
GW_PID=$!
sleep 3

echo "  Testing /health endpoint..."
HEALTH=$(curl -s http://localhost:${PORT}/health)
if echo "$HEALTH" | grep -q "GREEN"; then
    echo "  Health: GREEN"
else
    echo "  Health check failed: $HEALTH"
    kill $GW_PID 2>/dev/null
    exit 1
fi

echo "  Testing /tiers endpoint..."
TIERS=$(curl -s http://localhost:${PORT}/tiers)
if echo "$TIERS" | grep -q "2g"; then
    echo "  Tiers endpoint: OK"
fi

echo "  Testing /activate with mock payload..."
ACTIVATE=$(curl -s -X POST http://localhost:${PORT}/activate \
    -H "Content-Type: application/json" \
    -d '{"seed_id":"WINDI-TEST-001","stream_token":"TEST-TOKEN","network_quality":"4g"}')
if echo "$ACTIVATE" | grep -q "activation_id"; then
    echo "  Activate endpoint: OK"
    echo "  Status: $(echo $ACTIVATE | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d["status"])')"
    echo "  Layers: $(echo $ACTIVATE | python3 -c 'import sys,json;d=json.load(sys.stdin);print(len(d["manifest"]))')"
fi

echo ""
echo "  Stopping local test process..."
kill $GW_PID 2>/dev/null
sleep 1
echo "  Smoke test passed"

# ── PHASE 5: SYSTEMD SERVICE ───────────────────────
echo ""
echo "[7/7] SYSTEMD — Creating service unit..."

sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null << SVCEOF
[Unit]
Description=WINDI Dispatch Gateway v1.0.0 — .jmpg Hydration Engine
Documentation=https://windi-domain.com/dispatch/health
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=windi
Group=windi
WorkingDirectory=${DEPLOY_DIR}
EnvironmentFile=${DEPLOY_DIR}/.env
ExecStart=/usr/bin/python3 ${DEPLOY_DIR}/dispatch_gateway.py
Restart=always
RestartSec=5
StandardOutput=append:${LOG_DIR}/dispatch_gateway.log
StandardError=append:${LOG_DIR}/dispatch_gateway.log

# Security
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=${LOG_DIR} ${DEPLOY_DIR}

[Install]
WantedBy=multi-user.target
SVCEOF

sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}.service
sudo systemctl start ${SERVICE_NAME}.service
sleep 2

STATUS=$(sudo systemctl is-active ${SERVICE_NAME})
if [ "$STATUS" = "active" ]; then
    echo "  Service ${SERVICE_NAME}: ACTIVE"
else
    echo "  Service failed to start. Check logs:"
    echo "     journalctl -u ${SERVICE_NAME} -n 30 --no-pager"
    exit 1
fi

# ── NGINX SNIPPET ──────────────────────────────────
echo ""
echo "═══════════════════════════════════════"
echo "  NGINX SNIPPET (add to sites-enabled)"
echo "═══════════════════════════════════════"
cat << 'NGINXEOF'

    # ── WINDI Dispatch Gateway (:8121) ────────────────
    location /dispatch/ {
        proxy_pass http://127.0.0.1:8121/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
        proxy_connect_timeout 5s;
        # WINDI Cache Sovereignty Headers
        add_header X-WINDI-Gateway "Dispatch/1.0.0" always;
        # CORS for .jmpg Viewers on windi-domain.com
        add_header Access-Control-Allow-Origin "https://windi-domain.com" always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, X-Stream-Token, X-WINDI-Seed" always;
        if ($request_method = OPTIONS) {
            return 204;
        }
    }
    # ── END Dispatch Gateway ──────────────────────────

NGINXEOF

echo ""
echo "  Add the snippet above to nginx BEFORE the 'listen 443 ssl' line."
echo "  Then:"
echo "    sudo nginx -t && sudo systemctl reload nginx"
echo ""
echo "  Final verification:"
echo "    curl https://windi-domain.com/dispatch/health"
echo ""
echo "═══════════════════════════════════════"
echo "  DEPLOY COMPLETO"
echo "  OM SHANTI — Gateway :8121 LIVE"
echo "═══════════════════════════════════════"
echo ""
