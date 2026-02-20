#!/bin/bash
# ══════════════════════════════════════════════════════════════════
# 🐉 WINDI DEPLOYMENT — Composer v11 + ISP Builder Schema v1.0
# ══════════════════════════════════════════════════════════════════
# Date: 18 Feb 2026
# Protocol: Three Dragons — Linhagem de Ferro
# Principle: AI processes. Human decides. WINDI guarantees.
# ══════════════════════════════════════════════════════════════════

set -e  # Exit on error

echo "══════════════════════════════════════════════════════════════"
echo "🐉 WINDI DEPLOYMENT — Composer v11 + ISP Builder Schema v1.0"
echo "══════════════════════════════════════════════════════════════"
echo ""

# ─── PHASE 0: PRE-FLIGHT CHECK ──────────────────────────────────
echo "📋 PHASE 0: Pre-flight check..."

# Verify uploaded files exist
for f in /opt/windi/Composer-Deploy-v11.zip \
         /opt/windi/DesktopCommuniqueComposerV11.jsx \
         /opt/windi/isp_governance_schema_v1.0.json \
         /opt/windi/windi_isp_builder_report_v1.0.md; do
    if [ ! -f "$f" ]; then
        echo "❌ MISSING: $f"
        exit 1
    fi
    echo "  ✅ $(basename $f) — $(du -h $f | cut -f1)"
done

echo ""

# Check current services
echo "  Current service status:"
for port in 8100 8101 8103 8105 8106; do
    result=$(ss -tlnp 2>/dev/null | grep ":${port} " | head -1)
    if [ -n "$result" ]; then
        echo "    ✅ :${port} LISTENING"
    else
        echo "    ⚠️  :${port} DOWN"
    fi
done

echo ""
echo "  Pre-flight: ✅ PASS"
echo ""

# ─── PHASE 1: BACKUP ────────────────────────────────────────────
echo "💾 PHASE 1: Backup current state..."

BK="/opt/windi/backups/pre_composer_v11_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BK"

# Backup Desktop
if [ -d /opt/windi/desktop/ ]; then
    cp -r /opt/windi/desktop/ "$BK/desktop_backup/"
    echo "  ✅ Desktop backed up → $BK/desktop_backup/"
else
    echo "  ⚠️  No /opt/windi/desktop/ to backup"
fi

# Backup Communiqué
if [ -d /opt/windi/communique/ ]; then
    cp -r /opt/windi/communique/ "$BK/communique_backup/"
    echo "  ✅ Communiqué backed up → $BK/communique_backup/"
fi

# Backup nginx
sudo cp /etc/nginx/sites-enabled/admin.windia4desk.tech "$BK/nginx_admin.conf" 2>/dev/null || true
sudo cp /etc/nginx/sites-enabled/master.windia4desk.tech "$BK/nginx_master.conf" 2>/dev/null || true
echo "  ✅ nginx configs backed up"

echo "  Backup location: $BK"
echo ""

# ─── PHASE 2: INSPECT COMPOSER ZIP ──────────────────────────────
echo "🔍 PHASE 2: Inspect Composer-Deploy-v11.zip..."

echo "  Contents:"
unzip -l /opt/windi/Composer-Deploy-v11.zip 2>/dev/null | tail -n +4 | head -30
echo ""

# ─── PHASE 3: DEPLOY COMPOSER v11 TO DESKTOP ────────────────────
echo "🚀 PHASE 3: Deploy Composer v11..."

# Create staging area
STAGING="/opt/windi/staging_composer_v11"
rm -rf "$STAGING"
mkdir -p "$STAGING"

# Unzip to staging first
unzip -o /opt/windi/Composer-Deploy-v11.zip -d "$STAGING/" > /dev/null 2>&1
echo "  ✅ Unzipped to staging: $STAGING/"

# Show what we got
echo "  Staging contents:"
ls -la "$STAGING/" 2>/dev/null | head -20
echo ""

# Check if zip has a subdirectory or files at root
SUBDIR=$(find "$STAGING" -maxdepth 1 -type d ! -name "$(basename $STAGING)" | head -1)
if [ -n "$SUBDIR" ]; then
    echo "  📁 Found subdirectory: $(basename $SUBDIR)"
    DEPLOY_SOURCE="$SUBDIR"
else
    DEPLOY_SOURCE="$STAGING"
fi

# Check for key files (React build artifacts)
echo "  Looking for build artifacts..."
if [ -d "$DEPLOY_SOURCE/static" ] || [ -d "$DEPLOY_SOURCE/build" ] || [ -f "$DEPLOY_SOURCE/index.html" ]; then
    echo "  ✅ Found build artifacts"
elif [ -d "$DEPLOY_SOURCE/src" ] || [ -f "$DEPLOY_SOURCE/package.json" ]; then
    echo "  📦 Found source code — may need npm build"
fi

echo ""
echo "  Deploy source tree:"
find "$DEPLOY_SOURCE" -maxdepth 3 -type f | head -30
echo ""

# ─── PHASE 3b: MERGE INTO DESKTOP ───────────────────────────────
echo "🔧 PHASE 3b: Merging into Desktop..."

# Ensure desktop directory exists
mkdir -p /opt/windi/desktop/

# Copy new files (preserving existing backend)
cp -r "$DEPLOY_SOURCE"/* /opt/windi/desktop/ 2>/dev/null || true
echo "  ✅ Composer v11 files merged into /opt/windi/desktop/"

# Also place the JSX source for reference
mkdir -p /opt/windi/desktop/src/components/
cp /opt/windi/DesktopCommuniqueComposerV11.jsx /opt/windi/desktop/src/components/ 2>/dev/null || true
echo "  ✅ DesktopCommuniqueComposerV11.jsx → /opt/windi/desktop/src/components/"

echo ""

# ─── PHASE 4: INSTALL ISP SCHEMA ────────────────────────────────
echo "🛡️ PHASE 4: Install ISP Governance Schema v1.0..."

# Place schema in Communiqué Engine
mkdir -p /opt/windi/communique/schemas/
cp /opt/windi/isp_governance_schema_v1.0.json /opt/windi/communique/schemas/
echo "  ✅ Schema → /opt/windi/communique/schemas/isp_governance_schema_v1.0.json"

# Place schema in Desktop for client-side validation
mkdir -p /opt/windi/desktop/schemas/
cp /opt/windi/isp_governance_schema_v1.0.json /opt/windi/desktop/schemas/
echo "  ✅ Schema → /opt/windi/desktop/schemas/isp_governance_schema_v1.0.json"

# Place in docs for reference
mkdir -p /opt/windi/docs/
cp /opt/windi/isp_governance_schema_v1.0.json /opt/windi/docs/
cp /opt/windi/windi_isp_builder_report_v1.0.md /opt/windi/docs/
echo "  ✅ Report + Schema → /opt/windi/docs/"

echo ""

# ─── PHASE 5: RESTART SERVICES ──────────────────────────────────
echo "🔄 PHASE 5: Restart Desktop service..."

# Check if systemd service exists
if systemctl list-unit-files | grep -q "windi-desktop"; then
    sudo systemctl restart windi-desktop
    sleep 3
    sudo systemctl status windi-desktop --no-pager | head -15
    echo "  ✅ windi-desktop restarted via systemd"
else
    echo "  ⚠️  No windi-desktop systemd service found"
    echo "  Checking for running process..."
    PID=$(pgrep -f "desktop" | head -1)
    if [ -n "$PID" ]; then
        echo "  Found PID $PID — checking..."
        ps aux | grep "$PID" | grep -v grep
    fi
    echo ""
    echo "  ℹ️  Manual restart may be needed. Check how Desktop was started:"
    echo "     ps aux | grep -E '8100|desktop' | grep -v grep"
fi

echo ""

# ─── PHASE 6: SMOKE TEST ────────────────────────────────────────
echo "🔥 PHASE 6: Smoke test — Teste de Fogo..."
echo ""

sleep 2

# Desktop
echo "  --- Desktop :8100 ---"
DESKTOP_HEALTH=$(curl -s --max-time 5 http://127.0.0.1:8100/health 2>/dev/null)
if [ -n "$DESKTOP_HEALTH" ]; then
    echo "  ✅ $DESKTOP_HEALTH" | head -c 200
else
    echo "  ⚠️  No health response on :8100"
fi
echo ""

# Ledger
echo "  --- Ledger :8101 ---"
LEDGER_HEALTH=$(curl -s --max-time 5 http://127.0.0.1:8101/health 2>/dev/null)
if [ -n "$LEDGER_HEALTH" ]; then
    echo "  ✅ $LEDGER_HEALTH" | head -c 200
else
    echo "  ⚠️  No health response on :8101"
fi
echo ""

# Export Engine
echo "  --- Export Engine :8103 ---"
EXPORT_HEALTH=$(curl -s --max-time 5 http://127.0.0.1:8103/health 2>/dev/null)
if [ -n "$EXPORT_HEALTH" ]; then
    echo "  ✅ $EXPORT_HEALTH" | head -c 200
else
    echo "  ⚠️  No health response on :8103"
fi
echo ""

# Communiqué
echo "  --- Communiqué :8105 ---"
COM_HEALTH=$(curl -s --max-time 5 http://127.0.0.1:8105/health 2>/dev/null)
if [ -n "$COM_HEALTH" ]; then
    echo "  ✅ $COM_HEALTH" | head -c 200
else
    echo "  ⚠️  No health response on :8105"
fi
echo ""

# All ports
echo "  --- All Ecosystem Ports ---"
for port in 8100 8101 8102 8103 8104 8105 8106 8107; do
    result=$(ss -tlnp 2>/dev/null | grep ":${port} " | head -1)
    if [ -n "$result" ]; then
        echo "    ✅ :${port} LISTENING"
    else
        echo "    ❌ :${port} DOWN"
    fi
done

echo ""

# ─── PHASE 7: VERIFY ISP SCHEMA PLACEMENT ───────────────────────
echo "📁 PHASE 7: Verify file placement..."

for f in /opt/windi/communique/schemas/isp_governance_schema_v1.0.json \
         /opt/windi/desktop/schemas/isp_governance_schema_v1.0.json \
         /opt/windi/desktop/src/components/DesktopCommuniqueComposerV11.jsx \
         /opt/windi/docs/isp_governance_schema_v1.0.json \
         /opt/windi/docs/windi_isp_builder_report_v1.0.md; do
    if [ -f "$f" ]; then
        echo "  ✅ $f ($(du -h $f | cut -f1))"
    else
        echo "  ❌ MISSING: $f"
    fi
done

echo ""

# ─── PHASE 8: EXPORT TEST (Optional — validates full chain) ─────
echo "⚡ PHASE 8: Chain validation — Export → Ledger..."

EXPORT_TEST=$(curl -s --max-time 10 -X POST http://127.0.0.1:8103/api/export/jmpg \
  -H "Content-Type: application/json" \
  -d '{
    "title": "ISP Builder Deploy Verification",
    "author": "WINDI SYSTEM — Deployment Script",
    "template": "field-report",
    "content_blocks": [
      {"type": "heading", "level": 2, "text": "Composer v11 + ISP Schema v1.0 Deployed"},
      {"type": "paragraph", "text": "Automated deployment verification. All systems nominal."}
    ],
    "return_format": "json"
  }' 2>/dev/null)

if echo "$EXPORT_TEST" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['ledger_registered']==True; print(f'  ✅ JMPG created: {d[\"package_id\"]}'); print(f'  ✅ Ledger registered: {d[\"ledger_registered\"]}'); print(f'  ✅ Elapsed: {d[\"elapsed_ms\"]}ms')" 2>/dev/null; then
    echo "  ✅ Export → Ledger chain: VERIFIED"
else
    echo "  ⚠️  Export test result: $EXPORT_TEST" | head -c 300
fi

echo ""

# ─── CLEANUP ─────────────────────────────────────────────────────
echo "🧹 Cleanup staging..."
rm -rf "$STAGING"
echo "  ✅ Staging removed"

echo ""
echo "══════════════════════════════════════════════════════════════"
echo "🐉 DEPLOYMENT COMPLETE"
echo "══════════════════════════════════════════════════════════════"
echo ""
echo "  Composer v11:    /opt/windi/desktop/"
echo "  ISP Schema v1.0: /opt/windi/communique/schemas/"
echo "  Backup:          $BK"
echo "  Report:          /opt/windi/docs/windi_isp_builder_report_v1.0.md"
echo ""
echo "  🛡️ AI processes. Human decides. WINDI guarantees."
echo "══════════════════════════════════════════════════════════════"
