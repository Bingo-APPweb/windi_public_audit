#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# WINDI Desktop D1 — Status Indicator Deployment
# v1.1 — 17 Feb 2026
# "O poder está lá. Mas ele não grita."
#
# Prerequisites: Run from /opt/windi/desktop/
# Creates backup before any changes
# ═══════════════════════════════════════════════════════════════

set -e
DESKTOP_DIR="/opt/windi/desktop"
FRONTEND_DIR="$DESKTOP_DIR/frontend"
SRC_DIR="$FRONTEND_DIR/src"
PATCHES_DIR="$DESKTOP_DIR/patches"
BACKUP_DIR="/opt/windi/backups/pre_status_indicator_$(date +%Y%m%d_%H%M%S)"

echo ""
echo "═══════════════════════════════════════════════════"
echo "  WINDI D1 — Status Indicator Deployment"
echo "  17 Feb 2026 · Foundation v1.1"
echo "═══════════════════════════════════════════════════"
echo ""

# ── 1. BACKUP ───────────────────────────────────────────────
echo "📦 [1/6] Creating backup..."
mkdir -p "$BACKUP_DIR"
cp "$SRC_DIR/App.jsx"                       "$BACKUP_DIR/"
cp "$SRC_DIR/components/GovernancePanel.jsx" "$BACKUP_DIR/"
cp "$SRC_DIR/styles/d1.css"                 "$BACKUP_DIR/"
cp -r "$FRONTEND_DIR/dist"                  "$BACKUP_DIR/dist_backup"
echo "   Backup: $BACKUP_DIR"
echo "   ✅ Backup complete"
echo ""

# ── 2. INSTALL NEW COMPONENT ────────────────────────────────
echo "📄 [2/6] Installing StatusIndicator component..."
cp "$PATCHES_DIR/StatusIndicator.jsx" "$SRC_DIR/components/StatusIndicator.jsx"
echo "   → components/StatusIndicator.jsx"
echo "   ✅ Component installed"
echo ""

# ── 3. PATCH App.jsx ────────────────────────────────────────
echo "🔧 [3/6] Patching App.jsx..."
cp "$PATCHES_DIR/App.jsx" "$SRC_DIR/App.jsx"
echo "   → App.jsx (StatusIndicator + Sign button + R0-R5 strip)"
echo "   ✅ App patched"
echo ""

# ── 4. APPEND CSS ────────────────────────────────────────────
echo "🎨 [4/6] Adding Status Indicator styles to d1.css..."

# Check if already patched (idempotent)
if grep -q "STATUS INDICATOR" "$SRC_DIR/styles/d1.css" 2>/dev/null; then
  echo "   ⚠ Status Indicator CSS already present, skipping append"
else
  echo "" >> "$SRC_DIR/styles/d1.css"
  cat "$PATCHES_DIR/status-indicator.css" >> "$SRC_DIR/styles/d1.css"
  echo "   → d1.css (appended: indicator + R0-R5 palette + Sign upgrade)"
fi
echo "   ✅ CSS updated"
echo ""

# ── 5. BUILD ─────────────────────────────────────────────────
echo "🔨 [5/6] Building frontend..."
cd "$FRONTEND_DIR"

# Check if node_modules exist
if [ ! -d "node_modules" ]; then
  echo "   Installing dependencies first..."
  npm install --silent 2>/dev/null || echo "   ⚠ npm install had warnings (continuing)"
fi

# Build with Vite
npx vite build 2>&1 | tail -5
echo "   ✅ Build complete"
echo ""

# ── 6. VERIFY ────────────────────────────────────────────────
echo "🔍 [6/6] Verifying deployment..."

# Check dist was updated
DIST_TIME=$(stat -c %Y "$FRONTEND_DIR/dist/index.html" 2>/dev/null || echo "0")
NOW=$(date +%s)
DIFF=$((NOW - DIST_TIME))

if [ "$DIFF" -lt 60 ]; then
  echo "   dist/index.html: freshly built (${DIFF}s ago)"
else
  echo "   ⚠ dist/index.html may be stale (${DIFF}s old)"
fi

# Check component exists in build
if grep -q "StatusIndicator\|si-pill\|si-sentinel" "$FRONTEND_DIR/dist/assets/"*.js 2>/dev/null; then
  echo "   StatusIndicator: found in compiled JS"
else
  echo "   ⚠ StatusIndicator not found in compiled JS"
fi

# Check CSS variables
if grep -q "r0-integrity\|r5-critical\|status-protected" "$FRONTEND_DIR/dist/assets/"*.css 2>/dev/null; then
  echo "   R0-R5 palette: found in compiled CSS"
else
  echo "   ⚠ R0-R5 palette not found in compiled CSS"
fi

echo ""
echo "═══════════════════════════════════════════════════"
echo "  ✅ DEPLOYMENT COMPLETE"
echo ""
echo "  Changes:"
echo "   • StatusIndicator component (⚪🟡🟢🔵)"
echo "   • Sentinel LAW badge with 30s heartbeat"
echo "   • R0-R5 governance palette"
echo "   • Sign button (A Porta Dourada) upgraded"
echo "   • Hash peek on hover (Layer 2)"
echo ""
echo "  Backup: $BACKUP_DIR"
echo "  Rollback: cp $BACKUP_DIR/* $SRC_DIR/"
echo "═══════════════════════════════════════════════════"
echo ""
echo "  🐉 AI processes. Human decides. WINDI guarantees."
echo ""
