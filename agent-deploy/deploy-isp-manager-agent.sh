#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# WINDI ISP Manager Agent — Deployment Script
# AI processes. Human decides. WINDI guarantees.
# ═══════════════════════════════════════════════════════════════

set -e

echo "═══════════════════════════════════════════════════════════"
echo "🏛️  WINDI ISP Manager Agent — Deployment"
echo "═══════════════════════════════════════════════════════════"

WINDI_BASE="/opt/windi"
AGENTS_BASE="$WINDI_BASE/agents"
ISP_MANAGER="$AGENTS_BASE/isp-manager"
BACKUP_DIR="$WINDI_BASE/backups"

# Step 1: Backup existing agents dir if present
if [ -d "$AGENTS_BASE" ]; then
    BACKUP_NAME="agents_backup_$(date +%Y%m%d_%H%M%S)"
    echo "📦 Backing up existing agents to $BACKUP_DIR/$BACKUP_NAME"
    mkdir -p "$BACKUP_DIR"
    cp -r "$AGENTS_BASE" "$BACKUP_DIR/$BACKUP_NAME"
fi

# Step 2: Create directory structure
echo "📂 Creating agent directory structure..."
mkdir -p "$AGENTS_BASE"
mkdir -p "$ISP_MANAGER"/{scanners,rules,receipts,tests,drafts,alerts,reports}

# Step 3: Copy files
echo "📋 Deploying agent files..."
cp registry.json "$AGENTS_BASE/registry.json"
cp agents/isp-manager/manifest.json "$ISP_MANAGER/manifest.json"
cp agents/isp-manager/capsule.json "$ISP_MANAGER/capsule.json"
cp agents/isp-manager/policy.json "$ISP_MANAGER/policy.json"
cp agents/isp-manager/isp_manager_agent.py "$ISP_MANAGER/isp_manager_agent.py"

# Step 4: Set permissions
echo "🔒 Setting permissions..."
chown -R windi:windi "$AGENTS_BASE"
chmod -R 755 "$AGENTS_BASE"
chmod 644 "$AGENTS_BASE/registry.json"
chmod 644 "$ISP_MANAGER"/*.json
chmod 755 "$ISP_MANAGER/isp_manager_agent.py"

# Step 5: Verify deployment
echo ""
echo "🔍 Verifying deployment..."
echo ""

if [ -f "$AGENTS_BASE/registry.json" ]; then
    echo "  ✅ registry.json"
else
    echo "  ❌ registry.json MISSING"
fi

for f in manifest.json capsule.json policy.json isp_manager_agent.py; do
    if [ -f "$ISP_MANAGER/$f" ]; then
        echo "  ✅ isp-manager/$f"
    else
        echo "  ❌ isp-manager/$f MISSING"
    fi
done

# Step 6: Test agent
echo ""
echo "🧪 Testing agent..."
cd "$ISP_MANAGER"
python3 isp_manager_agent.py status --json 2>/dev/null && echo "  ✅ Agent responds" || echo "  ⚠️  Agent test needs review"

# Step 7: Show structure
echo ""
echo "📂 Final structure:"
find "$AGENTS_BASE" -maxdepth 3 -type f | sort | head -20

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "🏛️  Deployment complete!"
echo ""
echo "  Quick test commands:"
echo "    python3 $ISP_MANAGER/isp_manager_agent.py status"
echo "    python3 $ISP_MANAGER/isp_manager_agent.py audit"
echo "    python3 $ISP_MANAGER/isp_manager_agent.py health_report"
echo "    python3 $ISP_MANAGER/isp_manager_agent.py validate --isp-id deutsche-bahn"
echo "    python3 $ISP_MANAGER/isp_manager_agent.py drift_check"
echo ""
echo "  AI processes. Human decides. WINDI guarantees."
echo "═══════════════════════════════════════════════════════════"
