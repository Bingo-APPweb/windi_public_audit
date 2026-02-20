#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  WINDI Communiqué Composer v1.1 — FULL DEPLOYMENT
#  "AI processes. Human decides. WINDI guarantees."
#
#  This script:
#   1. Creates backup of current state
#   2. Relocates services to CANONICAL paths (per Location Matrix v1.0)
#   3. Installs Composer into Desktop (:8100)
#   4. Creates/updates systemd services
#   5. Updates nginx routes
#   6. Runs smoke tests
#
#  Run on Strato: bash deploy_composer_v11.sh
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  🐉 WINDI Communiqué Composer v1.1 — DEPLOYMENT"
echo "  Location Matrix v1.0 Canonical Alignment"
echo "═══════════════════════════════════════════════════════════"
echo ""

# ── CANONICAL PATHS (Location Matrix v1.0) ────────────────────
DESKTOP_DIR="/opt/windi/desktop"                # :8100
EXPORT_DIR="/opt/windi/export-engine"           # :8103
VIEWER_DIR="/opt/windi/jmpg-viewer"             # :8104
COMMUNIQUE_DIR="/opt/windi/communique"          # :8105
LEDGER_DIR="/opt/windi/forensic-ledger"         # :8101
LOG_DIR="/opt/windi/logs"
DATA_DIR="/opt/windi/data"
BACKUP_BASE="/opt/windi/backups"

# ── OLD PATHS (to relocate) ──────────────────────────────────
OLD_EXPORT="/opt/windi/desktop/export"
OLD_VIEWER="/opt/windi/desktop/jmpg"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_BASE}/pre_composer_${TIMESTAMP}"

# ══════════════════════════════════════════════════════════════
#  STEP 0: PRE-FLIGHT
# ══════════════════════════════════════════════════════════════
echo "▶ [0/7] Pre-flight checks..."

# Verify we're on the right server
if [ ! -d "/opt/windi" ]; then
    echo "❌ /opt/windi not found. Are you on the WINDI Strato server?"
    exit 1
fi

echo "  ✓ Server: $(hostname)"
echo "  ✓ User:   $(whoami)"
echo "  ✓ Date:   $(date -Iseconds)"
echo ""

# ══════════════════════════════════════════════════════════════
#  STEP 1: BACKUP
# ══════════════════════════════════════════════════════════════
echo "▶ [1/7] Creating backup → ${BACKUP_DIR}"

mkdir -p "${BACKUP_DIR}"

# Backup old locations if they exist
[ -d "${OLD_EXPORT}" ] && cp -r "${OLD_EXPORT}" "${BACKUP_DIR}/old_desktop_export/" 2>/dev/null && echo "  ✓ Backed up ${OLD_EXPORT}"
[ -d "${OLD_VIEWER}" ] && cp -r "${OLD_VIEWER}" "${BACKUP_DIR}/old_desktop_jmpg/" 2>/dev/null && echo "  ✓ Backed up ${OLD_VIEWER}"

# Backup canonical locations if they exist
[ -d "${EXPORT_DIR}" ] && cp -r "${EXPORT_DIR}" "${BACKUP_DIR}/export-engine/" 2>/dev/null && echo "  ✓ Backed up ${EXPORT_DIR}"
[ -d "${VIEWER_DIR}" ] && cp -r "${VIEWER_DIR}" "${BACKUP_DIR}/jmpg-viewer/" 2>/dev/null && echo "  ✓ Backed up ${VIEWER_DIR}"
[ -d "${COMMUNIQUE_DIR}" ] && cp -r "${COMMUNIQUE_DIR}" "${BACKUP_DIR}/communique/" 2>/dev/null && echo "  ✓ Backed up ${COMMUNIQUE_DIR}"

# Backup nginx
sudo cp /etc/nginx/sites-enabled/admin.windia4desk.tech "${BACKUP_DIR}/nginx_admin.conf" 2>/dev/null && echo "  ✓ Backed up nginx admin config"
sudo cp /etc/nginx/sites-enabled/windi-domain.com "${BACKUP_DIR}/nginx_windi.conf" 2>/dev/null || true

echo ""

# ══════════════════════════════════════════════════════════════
#  STEP 2: CREATE CANONICAL DIRECTORIES
# ══════════════════════════════════════════════════════════════
echo "▶ [2/7] Creating canonical directory structure..."

mkdir -p "${DESKTOP_DIR}"
mkdir -p "${EXPORT_DIR}"
mkdir -p "${VIEWER_DIR}"
mkdir -p "${COMMUNIQUE_DIR}"
mkdir -p "${LOG_DIR}"
mkdir -p "${DATA_DIR}"

echo "  ✓ ${DESKTOP_DIR}      → Desktop (:8100)"
echo "  ✓ ${EXPORT_DIR}  → Export Engine (:8103)"
echo "  ✓ ${VIEWER_DIR}    → JMPG Viewer (:8104)"
echo "  ✓ ${COMMUNIQUE_DIR}     → Communiqué Engine (:8105)"
echo ""

# ══════════════════════════════════════════════════════════════
#  STEP 3: RELOCATE SERVICES TO CANONICAL PATHS
# ══════════════════════════════════════════════════════════════
echo "▶ [3/7] Relocating services to canonical paths..."

# ── Export Engine: /opt/windi/desktop/export → /opt/windi/export-engine
if [ -d "${OLD_EXPORT}" ] && [ -f "${OLD_EXPORT}/jmpg_export_engine.py" ]; then
    echo "  Moving Export Engine..."
    
    # Stop service if running
    sudo systemctl stop windi-jmpg-export 2>/dev/null || true
    kill $(pgrep -f "jmpg_export_engine.py") 2>/dev/null || true
    sleep 1
    
    # Copy files to canonical location
    cp -f "${OLD_EXPORT}/jmpg_export_engine.py" "${EXPORT_DIR}/"
    cp -f "${OLD_EXPORT}/deploy_jmpg_export.sh" "${EXPORT_DIR}/" 2>/dev/null || true
    cp -f "${OLD_EXPORT}/DESKTOP_INTEGRATION.md" "${EXPORT_DIR}/" 2>/dev/null || true
    
    echo "  ✓ Export Engine → ${EXPORT_DIR}/jmpg_export_engine.py"
else
    echo "  ⚠ Old Export Engine not found at ${OLD_EXPORT}, checking canonical..."
    if [ -f "${EXPORT_DIR}/jmpg_export_engine.py" ]; then
        echo "  ✓ Export Engine already at canonical path"
    else
        echo "  ⚠ Export Engine not found anywhere — will need manual upload"
    fi
fi

# ── JMPG Viewer: /opt/windi/desktop/jmpg → /opt/windi/jmpg-viewer
if [ -d "${OLD_VIEWER}" ] && [ -f "${OLD_VIEWER}/jmpg_server.py" ]; then
    echo "  Moving JMPG Viewer..."
    
    sudo systemctl stop windi-jmpg-viewer 2>/dev/null || true
    kill $(pgrep -f "jmpg_server.py") 2>/dev/null || true
    sleep 1
    
    cp -f "${OLD_VIEWER}/jmpg_server.py" "${VIEWER_DIR}/"
    cp -f "${OLD_VIEWER}"/*.html "${VIEWER_DIR}/" 2>/dev/null || true
    
    echo "  ✓ JMPG Viewer → ${VIEWER_DIR}/jmpg_server.py"
else
    echo "  ⚠ Old JMPG Viewer not found at ${OLD_VIEWER}, checking canonical..."
    if [ -f "${VIEWER_DIR}/jmpg_server.py" ]; then
        echo "  ✓ JMPG Viewer already at canonical path"
    else
        echo "  ⚠ JMPG Viewer not found anywhere — will need manual upload"
    fi
fi

echo ""

# ══════════════════════════════════════════════════════════════
#  STEP 4: INSTALL COMMUNIQUÉ COMPOSER INTO DESKTOP
# ══════════════════════════════════════════════════════════════
echo "▶ [4/7] Installing Communiqué Composer v1.1..."

# The Composer lives inside the Desktop (:8100) as a module
COMPOSER_DIR="${DESKTOP_DIR}/composer"
mkdir -p "${COMPOSER_DIR}"

# Check if the composer JSX was uploaded alongside this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "${SCRIPT_DIR}/DesktopCommuniqueComposerV11.jsx" ]; then
    cp -f "${SCRIPT_DIR}/DesktopCommuniqueComposerV11.jsx" "${COMPOSER_DIR}/"
    echo "  ✓ Composer v1.1 → ${COMPOSER_DIR}/DesktopCommuniqueComposerV11.jsx"
else
    echo "  ⚠ DesktopCommuniqueComposerV11.jsx not found in ${SCRIPT_DIR}"
    echo "    Upload it alongside this script or copy manually."
fi

echo ""

# ══════════════════════════════════════════════════════════════
#  STEP 5: SYSTEMD SERVICES
# ══════════════════════════════════════════════════════════════
echo "▶ [5/7] Setting up systemd services..."

# ── Export Engine (:8103) ──────────────────────────────────────
if [ -f "${EXPORT_DIR}/jmpg_export_engine.py" ]; then
    echo "  Creating windi-export-engine.service..."
    
    sudo tee /etc/systemd/system/windi-export-engine.service > /dev/null << 'EOSVC'
[Unit]
Description=WINDI Export Engine v1.0 (:8103)
Documentation=https://admin.windia4desk.tech/export/health
After=network.target windi-forensic-ledger.service
Wants=network-online.target

[Service]
Type=simple
User=windi
Group=windi
WorkingDirectory=/opt/windi/export-engine
ExecStart=/usr/bin/python3 /opt/windi/export-engine/jmpg_export_engine.py
Restart=always
RestartSec=5
StandardOutput=append:/opt/windi/logs/export-engine.log
StandardError=append:/opt/windi/logs/export-engine.log
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/opt/windi/logs /opt/windi/data /opt/windi/export-engine

[Install]
WantedBy=multi-user.target
EOSVC
    
    echo "  ✓ windi-export-engine.service created"
fi

# ── JMPG Viewer (:8104) ───────────────────────────────────────
if [ -f "${VIEWER_DIR}/jmpg_server.py" ]; then
    echo "  Creating windi-jmpg-viewer.service..."
    
    sudo tee /etc/systemd/system/windi-jmpg-viewer.service > /dev/null << 'EOSVC'
[Unit]
Description=WINDI JMPG Viewer v1.0 (:8104)
Documentation=https://admin.windia4desk.tech/desktop/jmpg/
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=windi
Group=windi
WorkingDirectory=/opt/windi/jmpg-viewer
ExecStart=/usr/bin/python3 /opt/windi/jmpg-viewer/jmpg_server.py
Restart=always
RestartSec=5
StandardOutput=append:/opt/windi/logs/jmpg-viewer.log
StandardError=append:/opt/windi/logs/jmpg-viewer.log
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/opt/windi/logs /opt/windi/jmpg-viewer

[Install]
WantedBy=multi-user.target
EOSVC
    
    echo "  ✓ windi-jmpg-viewer.service created"
fi

# ── Communiqué Engine (:8105) ─────────────────────────────────
# Note: The Communiqué Engine python file should be uploaded separately
# For now, create the service definition ready for when the engine is deployed
echo "  Creating windi-communique.service..."

sudo tee /etc/systemd/system/windi-communique.service > /dev/null << 'EOSVC'
[Unit]
Description=WINDI Communiqué Engine v1.0 (:8105)
Documentation=https://admin.windia4desk.tech/communique/health
After=network.target windi-forensic-ledger.service
Wants=network-online.target

[Service]
Type=simple
User=windi
Group=windi
WorkingDirectory=/opt/windi/communique
ExecStart=/usr/bin/python3 /opt/windi/communique/communique_engine.py
Restart=always
RestartSec=5
StandardOutput=append:/opt/windi/logs/communique.log
StandardError=append:/opt/windi/logs/communique.log
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/opt/windi/logs /opt/windi/data /opt/windi/communique

[Install]
WantedBy=multi-user.target
EOSVC

echo "  ✓ windi-communique.service created"

# ── Reload systemd ─────────────────────────────────────────────
sudo systemctl daemon-reload
echo "  ✓ systemd daemon reloaded"

# ── Enable and start services with files present ──────────────
for svc in windi-export-engine windi-jmpg-viewer; do
    echo "  Enabling ${svc}..."
    sudo systemctl enable "${svc}" 2>/dev/null || true
    
    # Only start if the main script exists
    case "${svc}" in
        windi-export-engine)
            [ -f "${EXPORT_DIR}/jmpg_export_engine.py" ] && sudo systemctl start "${svc}" 2>/dev/null && echo "  ✓ ${svc} STARTED" || echo "  ⚠ ${svc} not started (missing files)"
            ;;
        windi-jmpg-viewer)
            [ -f "${VIEWER_DIR}/jmpg_server.py" ] && sudo systemctl start "${svc}" 2>/dev/null && echo "  ✓ ${svc} STARTED" || echo "  ⚠ ${svc} not started (missing files)"
            ;;
    esac
done

echo ""

# ══════════════════════════════════════════════════════════════
#  STEP 6: NGINX ROUTES — ensure canonical routes exist
# ══════════════════════════════════════════════════════════════
echo "▶ [6/7] Verifying nginx routes..."

NGINX_ADMIN="/etc/nginx/sites-enabled/admin.windia4desk.tech"

# Check if /export/ route exists
if ! grep -q "location /export/" "${NGINX_ADMIN}" 2>/dev/null; then
    echo "  Adding /export/ route → :8103..."
    
    # Find the line number before SSL block
    SSL_LINE=$(grep -n "listen 443 ssl" "${NGINX_ADMIN}" | head -1 | cut -d: -f1)
    
    if [ -n "${SSL_LINE}" ]; then
        INSERT_LINE=$((SSL_LINE - 2))
        sudo sed -i "${INSERT_LINE} a\\
\\
    # ── EXPORT ENGINE (:8103) ─────────────────────────\\
    location /export/ {\\
        proxy_pass http://127.0.0.1:8103/;\\
        proxy_http_version 1.1;\\
        proxy_set_header Host \$host;\\
        proxy_set_header X-Real-IP \$remote_addr;\\
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\\
        proxy_set_header X-Forwarded-Proto \$scheme;\\
        proxy_read_timeout 120s;\\
        proxy_connect_timeout 10s;\\
        add_header Access-Control-Allow-Origin \"https://admin.windia4desk.tech\" always;\\
        add_header Access-Control-Allow-Methods \"GET, POST, OPTIONS\" always;\\
        add_header Access-Control-Allow-Headers \"Content-Type, Authorization\" always;\\
        if (\$request_method = OPTIONS) {\\
            return 204;\\
        }\\
    }\\
    # ── END EXPORT ENGINE ─────────────────────────────" "${NGINX_ADMIN}"
        
        echo "  ✓ /export/ route added"
    fi
else
    echo "  ✓ /export/ route already exists"
fi

# Check if /communique/ route exists
if ! grep -q "location /communique/" "${NGINX_ADMIN}" 2>/dev/null; then
    echo "  Adding /communique/ route → :8105..."
    
    SSL_LINE=$(grep -n "listen 443 ssl" "${NGINX_ADMIN}" | head -1 | cut -d: -f1)
    
    if [ -n "${SSL_LINE}" ]; then
        INSERT_LINE=$((SSL_LINE - 2))
        sudo sed -i "${INSERT_LINE} a\\
\\
    # ── COMMUNIQUÉ ENGINE (:8105) ─────────────────────\\
    location /communique/ {\\
        proxy_pass http://127.0.0.1:8105/;\\
        proxy_http_version 1.1;\\
        proxy_set_header Host \$host;\\
        proxy_set_header X-Real-IP \$remote_addr;\\
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\\
        proxy_set_header X-Forwarded-Proto \$scheme;\\
        proxy_read_timeout 120s;\\
        proxy_connect_timeout 10s;\\
        add_header Access-Control-Allow-Origin \"https://admin.windia4desk.tech\" always;\\
        add_header Access-Control-Allow-Methods \"GET, POST, OPTIONS\" always;\\
        add_header Access-Control-Allow-Headers \"Content-Type, Authorization\" always;\\
        if (\$request_method = OPTIONS) {\\
            return 204;\\
        }\\
    }\\
    # ── END COMMUNIQUÉ ENGINE ─────────────────────────" "${NGINX_ADMIN}"
        
        echo "  ✓ /communique/ route added"
    fi
else
    echo "  ✓ /communique/ route already exists"
fi

# Test nginx
echo "  Testing nginx config..."
if sudo nginx -t 2>&1; then
    echo "  ✓ nginx config OK"
    sudo systemctl reload nginx
    echo "  ✓ nginx reloaded"
else
    echo "  ❌ nginx config FAILED — restoring backup"
    sudo cp "${BACKUP_DIR}/nginx_admin.conf" "${NGINX_ADMIN}"
    sudo systemctl reload nginx
    echo "  ✓ Backup restored"
fi

echo ""

# ══════════════════════════════════════════════════════════════
#  STEP 7: SMOKE TESTS
# ══════════════════════════════════════════════════════════════
echo "▶ [7/7] Running smoke tests..."
echo ""

echo "  ── Port Status ──"
for port in 8100 8101 8102 8103 8104 8105 8106 8107; do
    if ss -tlnp | grep -q ":${port} "; then
        echo "  ✅ :${port} — LISTENING"
    else
        echo "  ⬚  :${port} — not active"
    fi
done
echo ""

echo "  ── Service Status ──"
for svc in windi-export-engine windi-jmpg-viewer windi-communique; do
    STATUS=$(systemctl is-active "${svc}" 2>/dev/null || echo "inactive")
    if [ "${STATUS}" = "active" ]; then
        echo "  ✅ ${svc} — ${STATUS}"
    else
        echo "  ⬚  ${svc} — ${STATUS}"
    fi
done
echo ""

echo "  ── Health Endpoints ──"
curl -s http://localhost:8101/health 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  ✅ Ledger :8101 — {d.get(\"status\",\"?\")}')" 2>/dev/null || echo "  ⬚  Ledger :8101 — not responding"
curl -s http://localhost:8103/health 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  ✅ Export :8103 — {d.get(\"status\",\"?\")}')" 2>/dev/null || echo "  ⬚  Export :8103 — not responding"
curl -s http://localhost:8105/health 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  ✅ Communiqué :8105 — {d.get(\"status\",\"?\")}')" 2>/dev/null || echo "  ⬚  Communiqué :8105 — not responding"
echo ""

echo "  ── Filesystem Verification ──"
echo "  Canonical paths:"
[ -d "${DESKTOP_DIR}" ]    && echo "  ✅ ${DESKTOP_DIR}" || echo "  ⬚  ${DESKTOP_DIR}"
[ -d "${EXPORT_DIR}" ]     && echo "  ✅ ${EXPORT_DIR}" || echo "  ⬚  ${EXPORT_DIR}"
[ -d "${VIEWER_DIR}" ]     && echo "  ✅ ${VIEWER_DIR}" || echo "  ⬚  ${VIEWER_DIR}"
[ -d "${COMMUNIQUE_DIR}" ] && echo "  ✅ ${COMMUNIQUE_DIR}" || echo "  ⬚  ${COMMUNIQUE_DIR}"
echo ""

echo "  Key files:"
[ -f "${EXPORT_DIR}/jmpg_export_engine.py" ]       && echo "  ✅ export-engine/jmpg_export_engine.py" || echo "  ⬚  export-engine/jmpg_export_engine.py"
[ -f "${VIEWER_DIR}/jmpg_server.py" ]              && echo "  ✅ jmpg-viewer/jmpg_server.py" || echo "  ⬚  jmpg-viewer/jmpg_server.py"
[ -f "${DESKTOP_DIR}/composer/DesktopCommuniqueComposerV11.jsx" ] && echo "  ✅ desktop/composer/DesktopCommuniqueComposerV11.jsx" || echo "  ⬚  desktop/composer/DesktopCommuniqueComposerV11.jsx"
echo ""

# ══════════════════════════════════════════════════════════════
#  SUMMARY
# ══════════════════════════════════════════════════════════════
echo "═══════════════════════════════════════════════════════════"
echo "  🐉 DEPLOYMENT COMPLETE"
echo ""
echo "  Backup:  ${BACKUP_DIR}"
echo ""
echo "  Location Matrix Canonical Paths:"
echo "  ┌─────────────────────────────────────────────────────┐"
echo "  │ :8100  Desktop       /opt/windi/desktop/            │"
echo "  │ :8100  └─ Composer   /opt/windi/desktop/composer/   │"
echo "  │ :8103  Export Engine /opt/windi/export-engine/      │"
echo "  │ :8104  JMPG Viewer  /opt/windi/jmpg-viewer/        │"
echo "  │ :8105  Communiqué   /opt/windi/communique/          │"
echo "  │ :8101  Ledger       /opt/windi/forensic-ledger/     │"
echo "  │ :8106  Vault        /opt/windi/forensic-vault/      │"
echo "  └─────────────────────────────────────────────────────┘"
echo ""
echo "  Next steps:"
echo "  □ Upload communique_engine.py to /opt/windi/communique/"
echo "  □ Start: sudo systemctl start windi-communique"
echo "  □ Test:  curl https://admin.windia4desk.tech/communique/health"
echo "  □ Integrate Composer JSX into Desktop React build"
echo ""
echo "  \"AI processes. Human decides. WINDI guarantees.\""
echo "═══════════════════════════════════════════════════════════"
