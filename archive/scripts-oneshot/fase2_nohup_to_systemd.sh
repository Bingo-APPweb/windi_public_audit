#!/bin/bash
# ══════════════════════════════════════════════════════════════
# 🐉 WINDI FASE 2 — nohup → systemd Migration (4 services)
# Date: 15 Feb 2026
# Services: Governance, BABEL, Landing, War Room
# ══════════════════════════════════════════════════════════════

set -e

BACKUP_DIR="/opt/windi/backups/pre_systemd_$(date +%Y%m%d_%H%M%S)"

echo "╔══════════════════════════════════════════════╗"
echo "║  🐉 FASE 2: nohup → systemd (4 services)    ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── PRE-FLIGHT ──────────────────────────────────────────────
echo "📋 Pre-flight checks..."
mkdir -p "$BACKUP_DIR"
mkdir -p /opt/windi/logs

# Verify landing page working directory
LANDING_CWD=$(readlink -f /proc/$(ss -tlnp | grep ":8086 " | grep -oP 'pid=\K[0-9]+' | head -1)/cwd 2>/dev/null || echo "UNKNOWN")
echo "   Landing :8086 working dir: $LANDING_CWD"

# Verify all processes exist
for port in 8080 8085 8086 8090; do
  pid=$(ss -tlnp | grep ":$port " | grep -oP 'pid=\K[0-9]+' | head -1)
  if [ -n "$pid" ]; then
    echo "   ✅ :$port → PID $pid alive"
  else
    echo "   ⚠️  :$port → NO PROCESS (will create service anyway)"
  fi
done

echo ""
echo "Will create 4 systemd services. Continue? (auto-yes in 3s)"
sleep 3

# ══════════════════════════════════════════════════════════════
# SERVICE 1: GOVERNANCE (:8080)
# ══════════════════════════════════════════════════════════════
echo ""
echo "━━━ [1/4] GOVERNANCE API (:8080) ━━━━━━━━━━━━━━━━━━━━━"

if systemctl list-unit-files | grep -q "windi-governance.service"; then
    echo "   ⚠️  windi-governance.service already exists!"
    echo "   Checking status..."
    systemctl is-active windi-governance 2>/dev/null && echo "   Already running via systemd. Skipping." && GOV_SKIP=true
fi

if [ "$GOV_SKIP" != "true" ]; then
    echo "   Creating windi-governance.service..."
    sudo tee /etc/systemd/system/windi-governance.service > /dev/null << 'EOF'
[Unit]
Description=WINDI Governance API v1.0 (:8080)
Documentation=https://admin.windia4desk.tech/governance/api/status
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=windi
Group=windi
WorkingDirectory=/opt/windi/engine
ExecStart=/usr/bin/python3 /opt/windi/engine/windi_governance_api.py
Restart=always
RestartSec=5
StandardOutput=append:/opt/windi/logs/governance.log
StandardError=append:/opt/windi/logs/governance.log

# Security hardening
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/opt/windi

[Install]
WantedBy=multi-user.target
EOF
    echo "   ✅ Unit file created."

    # Kill nohup process
    GOV_PID=$(ss -tlnp | grep ":8080 " | grep -oP 'pid=\K[0-9]+' | head -1)
    if [ -n "$GOV_PID" ]; then
        echo "   Stopping nohup process (PID $GOV_PID)..."
        kill $GOV_PID 2>/dev/null || true
        sleep 2
        # Verify it's dead
        if ss -tlnp | grep -q ":8080 "; then
            echo "   ⚠️  Port 8080 still occupied, force killing..."
            kill -9 $GOV_PID 2>/dev/null || true
            sleep 2
        fi
    fi

    # Start via systemd
    sudo systemctl daemon-reload
    sudo systemctl enable windi-governance.service
    sudo systemctl start windi-governance.service
    sleep 2

    # Verify
    if systemctl is-active --quiet windi-governance; then
        echo "   ✅ GOVERNANCE running via systemd!"
    else
        echo "   ❌ GOVERNANCE failed to start! Checking logs..."
        journalctl -u windi-governance --no-pager -n 10
    fi
fi

# ══════════════════════════════════════════════════════════════
# SERVICE 2: BABEL (:8085)
# ══════════════════════════════════════════════════════════════
echo ""
echo "━━━ [2/4] BABEL EDITOR (:8085) ━━━━━━━━━━━━━━━━━━━━━━━"

if systemctl list-unit-files | grep -q "windi-babel.service"; then
    echo "   ⚠️  windi-babel.service already exists!"
    systemctl is-active windi-babel 2>/dev/null && echo "   Already running via systemd. Skipping." && BABEL_SKIP=true
fi

if [ "$BABEL_SKIP" != "true" ]; then
    echo "   Creating windi-babel.service..."
    sudo tee /etc/systemd/system/windi-babel.service > /dev/null << 'EOF'
[Unit]
Description=WINDI A4 Desk BABEL Editor v4.7.1-gov (:8085)
Documentation=https://admin.windia4desk.tech/babel/api/health
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=windi
Group=windi
WorkingDirectory=/opt/windi/a4desk-editor
ExecStart=/usr/bin/python3 /opt/windi/a4desk-editor/a4desk_tiptap_babel.py
Restart=always
RestartSec=5
StandardOutput=append:/opt/windi/logs/babel.log
StandardError=append:/opt/windi/logs/babel.log

# Security hardening
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/opt/windi

[Install]
WantedBy=multi-user.target
EOF
    echo "   ✅ Unit file created."

    BABEL_PID=$(ss -tlnp | grep ":8085 " | grep -oP 'pid=\K[0-9]+' | head -1)
    if [ -n "$BABEL_PID" ]; then
        echo "   Stopping nohup process (PID $BABEL_PID)..."
        kill $BABEL_PID 2>/dev/null || true
        sleep 2
        if ss -tlnp | grep -q ":8085 "; then
            kill -9 $BABEL_PID 2>/dev/null || true
            sleep 2
        fi
    fi

    sudo systemctl daemon-reload
    sudo systemctl enable windi-babel.service
    sudo systemctl start windi-babel.service
    sleep 2

    if systemctl is-active --quiet windi-babel; then
        echo "   ✅ BABEL running via systemd!"
    else
        echo "   ❌ BABEL failed to start! Checking logs..."
        journalctl -u windi-babel --no-pager -n 10
    fi
fi

# ══════════════════════════════════════════════════════════════
# SERVICE 3: A4DESK LANDING (:8086)
# ══════════════════════════════════════════════════════════════
echo ""
echo "━━━ [3/4] A4DESK LANDING (:8086) ━━━━━━━━━━━━━━━━━━━━━"

# Determine correct working directory
if [ "$LANDING_CWD" != "UNKNOWN" ] && [ -f "$LANDING_CWD/app.py" ]; then
    LANDING_DIR="$LANDING_CWD"
elif [ -f "/opt/windi/a4desk-landing/app.py" ]; then
    LANDING_DIR="/opt/windi/a4desk-landing"
else
    echo "   🔍 Searching for landing app.py..."
    LANDING_DIR=$(find /opt/windi -name "app.py" -path "*/landing*" -exec dirname {} \; 2>/dev/null | head -1)
    if [ -z "$LANDING_DIR" ]; then
        # Fallback: use CWD from process
        LANDING_DIR="$LANDING_CWD"
    fi
fi
echo "   Landing directory resolved: $LANDING_DIR"

if systemctl list-unit-files | grep -q "windi-landing.service"; then
    echo "   ⚠️  windi-landing.service already exists!"
    systemctl is-active windi-landing 2>/dev/null && echo "   Already running via systemd. Skipping." && LAND_SKIP=true
fi

if [ "$LAND_SKIP" != "true" ]; then
    echo "   Creating windi-landing.service..."
    sudo tee /etc/systemd/system/windi-landing.service > /dev/null << EOF
[Unit]
Description=WINDI A4 Desk Landing Page (:8086)
Documentation=https://admin.windia4desk.tech/
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=windi
Group=windi
WorkingDirectory=$LANDING_DIR
ExecStart=/usr/bin/python3 $LANDING_DIR/app.py
Restart=always
RestartSec=5
StandardOutput=append:/opt/windi/logs/landing.log
StandardError=append:/opt/windi/logs/landing.log

# Security hardening
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/opt/windi

[Install]
WantedBy=multi-user.target
EOF
    echo "   ✅ Unit file created (WorkDir: $LANDING_DIR)."

    LAND_PID=$(ss -tlnp | grep ":8086 " | grep -oP 'pid=\K[0-9]+' | head -1)
    if [ -n "$LAND_PID" ]; then
        echo "   Stopping nohup process (PID $LAND_PID)..."
        kill $LAND_PID 2>/dev/null || true
        sleep 2
        if ss -tlnp | grep -q ":8086 "; then
            kill -9 $LAND_PID 2>/dev/null || true
            sleep 2
        fi
    fi

    sudo systemctl daemon-reload
    sudo systemctl enable windi-landing.service
    sudo systemctl start windi-landing.service
    sleep 2

    if systemctl is-active --quiet windi-landing; then
        echo "   ✅ LANDING running via systemd!"
    else
        echo "   ❌ LANDING failed to start! Checking logs..."
        journalctl -u windi-landing --no-pager -n 10
    fi
fi

# ══════════════════════════════════════════════════════════════
# SERVICE 4: WAR ROOM (:8090)
# ══════════════════════════════════════════════════════════════
echo ""
echo "━━━ [4/4] WAR ROOM (:8090) ━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if systemctl list-unit-files | grep -q "windi-warroom.service"; then
    echo "   ⚠️  windi-warroom.service already exists!"
    systemctl is-active windi-warroom 2>/dev/null && echo "   Already running via systemd. Skipping." && WR_SKIP=true
fi

if [ "$WR_SKIP" != "true" ]; then
    echo "   Creating windi-warroom.service..."
    sudo tee /etc/systemd/system/windi-warroom.service > /dev/null << 'EOF'
[Unit]
Description=WINDI War Room Dashboard (:8090)
Documentation=https://admin.windia4desk.tech/war-room/
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=windi
Group=windi
WorkingDirectory=/opt/windi/SDK_v1.1_RFC003/windi-sdk-v1
ExecStart=/usr/bin/node /opt/windi/SDK_v1.1_RFC003/windi-sdk-v1/day-by-day-server.js
Restart=always
RestartSec=5
StandardOutput=append:/opt/windi/logs/warroom.log
StandardError=append:/opt/windi/logs/warroom.log
Environment=NODE_ENV=production
Environment=PORT=8090

# Security hardening
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/opt/windi

[Install]
WantedBy=multi-user.target
EOF
    echo "   ✅ Unit file created."

    WR_PID=$(ss -tlnp | grep ":8090 " | grep -oP 'pid=\K[0-9]+' | head -1)
    if [ -n "$WR_PID" ]; then
        echo "   Stopping nohup process (PID $WR_PID)..."
        kill $WR_PID 2>/dev/null || true
        sleep 2
        if ss -tlnp | grep -q ":8090 "; then
            kill -9 $WR_PID 2>/dev/null || true
            sleep 2
        fi
    fi

    sudo systemctl daemon-reload
    sudo systemctl enable windi-warroom.service
    sudo systemctl start windi-warroom.service
    sleep 2

    if systemctl is-active --quiet windi-warroom; then
        echo "   ✅ WAR ROOM running via systemd!"
    else
        echo "   ❌ WAR ROOM failed to start! Checking logs..."
        journalctl -u windi-warroom --no-pager -n 10
    fi
fi

# ══════════════════════════════════════════════════════════════
# FINAL VERIFICATION
# ══════════════════════════════════════════════════════════════
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  🔥 FINAL VERIFICATION                       ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

echo "=== ALL WINDI SYSTEMD SERVICES ==="
systemctl list-units --type=service --no-pager | grep windi
echo ""

echo "=== PORT STATUS ==="
for port in 8080 8085 8086 8089 8090 8092 8097; do
  pid=$(ss -tlnp | grep ":$port " | grep -oP 'pid=\K[0-9]+' | head -1)
  if [ -n "$pid" ]; then
    echo "  ✅ :$port → PID $pid"
  else
    echo "  ❌ :$port → DOWN"
  fi
done
echo ""

echo "=== SMOKE TEST ==="
sleep 1
curl -s -o /dev/null -w "  Governance :8080   → HTTP %{http_code}\n" http://localhost:8080/api/status --max-time 3
curl -s -o /dev/null -w "  BABEL :8085        → HTTP %{http_code}\n" http://localhost:8085/api/health --max-time 3
curl -s -o /dev/null -w "  Landing :8086      → HTTP %{http_code}\n" http://localhost:8086/ --max-time 3
curl -s -o /dev/null -w "  War Room :8090     → HTTP %{http_code}\n" http://localhost:8090/war-room/ --max-time 3
echo ""

echo "=== REMAINING NOHUP PROCESSES ==="
NOHUP_COUNT=$(ps aux | grep -E "python3|node" | grep -v grep | grep -v "systemd\|journald" | grep -c "nohup" 2>/dev/null || echo "0")
echo "  nohup processes remaining: $NOHUP_COUNT"
echo ""

echo "╔══════════════════════════════════════════════╗"
echo "║  📋 FASE 2 — MIGRATION SUMMARY               ║"
echo "╠══════════════════════════════════════════════╣"
echo "║  Backup dir: $BACKUP_DIR"
echo "║  Governance → systemd: DONE"
echo "║  BABEL      → systemd: DONE"
echo "║  Landing    → systemd: DONE"
echo "║  War Room   → systemd: DONE"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "🐉 Fase 2 complete. All dragons now under systemd control."
echo "   The WINDI system will survive any reboot."
