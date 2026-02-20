#!/bin/bash
# ╔══════════════════════════════════════════════════════════════════╗
# ║  WINDI SENTINEL — Deployment Script v1.0.0                      ║
# ║  Bloco E: Shield of the Dragon                                  ║
# ║                                                                  ║
# ║  This script deploys the Sentinel monitoring system:             ║
# ║  1. Creates directory structure                                  ║
# ║  2. Places files                                                 ║
# ║  3. Creates systemd service                                      ║
# ║  4. Runs initial test check                                      ║
# ║  5. Activates daemon                                             ║
# ║                                                                  ║
# ║  Run as: bash deploy_sentinel.sh                                 ║
# ║  (will use sudo for systemd operations)                          ║
# ╚══════════════════════════════════════════════════════════════════╝

set -euo pipefail

# ── Configuration ──
WINDI_BASE="/opt/windi"
SENTINEL_DIR="${WINDI_BASE}/sentinel"
SERVICE_NAME="windi-sentinel"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║  WINDI SENTINEL — Deployment                                    ║"
echo "║  Erguendo o Escudo do Dragão...                                 ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# ── Step 1: Pre-flight checks ──
echo "── Step 1: Pre-flight checks ──"

if [ ! -d "$WINDI_BASE" ]; then
    echo "  ❌ WINDI base directory not found: $WINDI_BASE"
    exit 1
fi
echo "  ✅ WINDI base: $WINDI_BASE"

if ! command -v python3 &> /dev/null; then
    echo "  ❌ python3 not found"
    exit 1
fi
echo "  ✅ Python3: $(python3 --version 2>&1)"

if ! command -v systemctl &> /dev/null; then
    echo "  ❌ systemctl not found"
    exit 1
fi
echo "  ✅ systemd available"

# Check if sentinel already running
if systemctl is-active --quiet ${SERVICE_NAME}.service 2>/dev/null; then
    echo "  ⚠️  Sentinel already running. Stopping for upgrade..."
    sudo systemctl stop ${SERVICE_NAME}.service
    sleep 2
fi

echo ""

# ── Step 2: Create directory structure ──
echo "── Step 2: Directory structure ──"

mkdir -p "${SENTINEL_DIR}"
mkdir -p "${WINDI_BASE}/logs"
mkdir -p "${WINDI_BASE}/data"
echo "  ✅ ${SENTINEL_DIR}"
echo "  ✅ ${WINDI_BASE}/logs"
echo "  ✅ ${WINDI_BASE}/data"
echo ""

# ── Step 3: Deploy files ──
echo "── Step 3: Deploy files ──"

# Copy sentinel script
if [ -f "${SCRIPT_DIR}/windi_sentinel.py" ]; then
    cp "${SCRIPT_DIR}/windi_sentinel.py" "${SENTINEL_DIR}/windi_sentinel.py"
    echo "  ✅ windi_sentinel.py deployed"
else
    # If running from a different location, check current dir
    if [ -f "./windi_sentinel.py" ]; then
        cp "./windi_sentinel.py" "${SENTINEL_DIR}/windi_sentinel.py"
        echo "  ✅ windi_sentinel.py deployed (from cwd)"
    else
        echo "  ❌ windi_sentinel.py not found in ${SCRIPT_DIR} or $(pwd)"
        exit 1
    fi
fi

# Copy .env
if [ -f "${SCRIPT_DIR}/.env" ]; then
    cp "${SCRIPT_DIR}/.env" "${SENTINEL_DIR}/.env"
    echo "  ✅ .env deployed"
elif [ -f "./.env" ]; then
    cp "./.env" "${SENTINEL_DIR}/.env"
    echo "  ✅ .env deployed (from cwd)"
else
    # Create default .env
    cat > "${SENTINEL_DIR}/.env" << 'ENVEOF'
WINDI_BASE=/opt/windi
SENTINEL_INTERVAL=60
SENTINEL_TIMEOUT=8
SENTINEL_WARN=2
SENTINEL_ALERT=5
SENTINEL_CRIT=10
ENVEOF
    echo "  ✅ .env created (defaults)"
fi

chmod 600 "${SENTINEL_DIR}/.env"
echo ""

# ── Step 4: Create systemd service ──
echo "── Step 4: systemd service ──"

sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null << 'EOF'
[Unit]
Description=WINDI Sentinel v1.0.0 — Shield of the Dragon
Documentation=https://admin.windia4desk.tech/sentinel/health
After=network.target
Wants=network-online.target

# Start after core services are up
After=windi-governance.service windi-bridge.service windi-brain.service
Wants=windi-governance.service

[Service]
Type=simple
User=windi
Group=windi
WorkingDirectory=/opt/windi/sentinel
EnvironmentFile=/opt/windi/sentinel/.env
ExecStart=/usr/bin/python3 /opt/windi/sentinel/windi_sentinel.py serve
Restart=always
RestartSec=15

# Sentinel restarts slower — it's an observer, not a responder
StartLimitIntervalSec=300
StartLimitBurst=5

# Logging
StandardOutput=append:/opt/windi/logs/sentinel.log
StandardError=append:/opt/windi/logs/sentinel.log

# Security hardening
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/opt/windi/data /opt/windi/logs /opt/windi/sentinel

[Install]
WantedBy=multi-user.target
EOF

echo "  ✅ ${SERVICE_NAME}.service created"

sudo systemctl daemon-reload
echo "  ✅ systemd reloaded"
echo ""

# ── Step 5: Initial test check ──
echo "── Step 5: Initial test check ──"
echo ""

cd "${SENTINEL_DIR}"
python3 windi_sentinel.py check
RESULT=$?

echo ""
if [ $RESULT -eq 0 ]; then
    echo "  ✅ Initial check: ALL HEALTHY"
else
    echo "  ⚠️  Initial check: Some services degraded (non-blocking)"
fi
echo ""

# ── Step 6: Activate daemon ──
echo "── Step 6: Activate daemon ──"

sudo systemctl enable ${SERVICE_NAME}.service
echo "  ✅ Enabled (auto-start on boot)"

sudo systemctl start ${SERVICE_NAME}.service
sleep 3

if systemctl is-active --quiet ${SERVICE_NAME}.service; then
    echo "  ✅ Sentinel is ACTIVE"
else
    echo "  ⚠️  Sentinel may not have started cleanly. Checking..."
    sudo systemctl status ${SERVICE_NAME}.service --no-pager -l
fi

echo ""

# ── Step 7: Verify ──
echo "── Step 7: Verification ──"

echo "  systemd status:"
systemctl is-active ${SERVICE_NAME}.service && echo "    ✅ active" || echo "    ❌ not active"
systemctl is-enabled ${SERVICE_NAME}.service && echo "    ✅ enabled" || echo "    ❌ not enabled"

echo ""
echo "  Log tail:"
sleep 2
tail -5 "${WINDI_BASE}/logs/sentinel.log" 2>/dev/null | while read line; do
    echo "    $line"
done

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║  🛡️  WINDI SENTINEL — DEPLOYED & ACTIVE  🛡️                    ║"
echo "║                                                                ║"
echo "║  The shield is raised. The dragon watches.                     ║"
echo "║                                                                ║"
echo "║  Commands:                                                     ║"
echo "║    Status:   python3 sentinel/windi_sentinel.py status         ║"
echo "║    Check:    python3 sentinel/windi_sentinel.py check          ║"
echo "║    Logs:     tail -f /opt/windi/logs/sentinel.log              ║"
echo "║    Service:  sudo systemctl status windi-sentinel              ║"
echo "║    Stop:     sudo systemctl stop windi-sentinel                ║"
echo "║    Restart:  sudo systemctl restart windi-sentinel             ║"
echo "║                                                                ║"
echo "║  Thresholds:                                                   ║"
echo "║    🟡 DEGRADED:  1 consecutive failure                         ║"
echo "║    🟠 WARNING:   2 consecutive failures                        ║"
echo "║    🔴 ALERT:     5 consecutive failures                        ║"
echo "║    ⚫ CRITICAL: 10 consecutive failures                        ║"
echo "║                                                                ║"
echo "║  Interval: 60 seconds between cycles                          ║"
echo "║                                                                ║"
echo "║  AI processes. Human decides. WINDI guarantees.                ║"
echo "║  The Sentinel guarantees the guarantor.  🐉🛡️                  ║"
echo "║                                                                ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
