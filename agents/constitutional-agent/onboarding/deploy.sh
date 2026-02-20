#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
#  WINDI Praktikant Onboarding — Deploy to Strato
#  Target: /opt/windi/agents/constitutional-agent/onboarding/
# ═══════════════════════════════════════════════════════════════════════════════

set -e

DEPLOY_DIR="/opt/windi/agents/constitutional-agent/onboarding"
BACKUP_DIR="/opt/windi/backups/onboarding_$(date +%Y%m%d_%H%M%S)"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  WINDI Praktikant Onboarding — Deploy Script                ║"
echo "║  Target: $DEPLOY_DIR"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Backup existing (if any)
if [ -d "$DEPLOY_DIR" ]; then
    echo "📦 Backing up existing onboarding..."
    mkdir -p "$BACKUP_DIR"
    cp -r "$DEPLOY_DIR" "$BACKUP_DIR/"
    echo "   ✓ Backup: $BACKUP_DIR"
fi

# Step 2: Create directory structure
echo "📁 Creating directory structure..."
mkdir -p "$DEPLOY_DIR/reports"
mkdir -p "$DEPLOY_DIR/ledger"

# Step 3: Copy files
echo "📋 Deploying Praktikant Protocol..."
cp praktikant_protocol.py "$DEPLOY_DIR/"
chmod +x "$DEPLOY_DIR/praktikant_protocol.py"
echo "   ✓ praktikant_protocol.py deployed"

# Step 4: Run Phase 1 (Observation)
echo ""
echo "🔍 Running Praktikant Onboarding..."
echo ""
cd "$DEPLOY_DIR"
python3 praktikant_protocol.py

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ DEPLOY COMPLETE"
echo ""
echo "   Files: $DEPLOY_DIR/"
echo "   Reports: $DEPLOY_DIR/reports/"
echo "   Ledger: $DEPLOY_DIR/ledger/"
echo ""
echo "   Next: Review Arrival Report, then:"
echo "   python3 $DEPLOY_DIR/test_babel_integration.py"
echo "═══════════════════════════════════════════════════════════════"
