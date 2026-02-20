#!/bin/bash
# ═══════════════════════════════════════════════════════════
# 🎼 WINDI Maestro Agent — Deployment Script
# Third Pillar: RESOLUTION
# "AI processes. Human decides. WINDI guarantees."
# ═══════════════════════════════════════════════════════════

set -e

AGENT_DIR="/opt/windi/agents/maestro"
REGISTRY="/opt/windi/agents/registry.json"
BACKUP_DIR="/opt/windi/backups/pre_maestro_$(date +%Y%m%d_%H%M%S)"

echo "═══════════════════════════════════════════════════════════"
echo "🎼  WINDI Maestro Agent — Deployment"
echo "═══════════════════════════════════════════════════════════"

# Backup existing registry
echo "💾 Backing up registry..."
mkdir -p "$BACKUP_DIR"
if [ -f "$REGISTRY" ]; then
    cp "$REGISTRY" "$BACKUP_DIR/registry.json.bak"
fi
if [ -d "$AGENT_DIR" ]; then
    cp -r "$AGENT_DIR" "$BACKUP_DIR/maestro.bak"
fi

# Create directory structure
echo "📂 Creating agent directory structure..."
mkdir -p "$AGENT_DIR"/{receipts,resolutions,escalations,reports,state}

# Deploy agent files
echo "📋 Deploying agent files..."
cp agents/maestro/manifest.json "$AGENT_DIR/"
cp agents/maestro/capsule.json "$AGENT_DIR/"
cp agents/maestro/policy.json "$AGENT_DIR/"
cp agents/maestro/maestro_agent.py "$AGENT_DIR/"

# Deploy modules
echo "🧩 Deploying modules..."
mkdir -p "$AGENT_DIR/modules"
cp agents/maestro/modules/__init__.py "$AGENT_DIR/modules/"
cp agents/maestro/modules/decision_router.py "$AGENT_DIR/modules/"
cp agents/maestro/modules/sla_guardian.py "$AGENT_DIR/modules/"
cp agents/maestro/modules/resolution_assembler.py "$AGENT_DIR/modules/"

# Set permissions
echo "🔒 Setting permissions..."
chmod 644 "$AGENT_DIR"/*.json
chmod 755 "$AGENT_DIR"/maestro_agent.py
chmod 755 "$AGENT_DIR"/{receipts,resolutions,escalations,reports,state}

# Update registry
echo "📝 Updating agent registry..."
if [ -f "$REGISTRY" ]; then
    python3 -c "
import json
with open('$REGISTRY') as f:
    reg = json.load(f)

# Add Maestro to agents list
maestro_entry = {
    'agent_id': 'windi://agent/core/maestro',
    'codename': 'Maestro',
    'pillar': 'RESOLUTION',
    'name': 'WINDI Governance Orchestrator',
    'version': '1.0.0',
    'status': 'ACTIVE',
    'execution_mode': 'human-mediated',
    'path': '/opt/windi/agents/maestro',
    'entry_point': 'maestro_agent.py',
    'registered_at': '$(date -u +%Y-%m-%dT%H:%M:%SZ)'
}

# Check if already exists, update or append
agents = reg.get('agents', [])
found = False
for i, a in enumerate(agents):
    if a.get('agent_id') == 'windi://agent/core/maestro':
        agents[i] = maestro_entry
        found = True
        break
if not found:
    agents.append(maestro_entry)

reg['agents'] = agents
reg['version'] = '1.2.0'
reg['updated_at'] = '$(date -u +%Y-%m-%dT%H:%M:%SZ)'
reg['institutional_pillars'] = {
    'CREATION': 'isp-manager',
    'VERIFICATION': 'sentinela',
    'RESOLUTION': 'maestro'
}

with open('$REGISTRY', 'w') as f:
    json.dump(reg, f, indent=2, ensure_ascii=False)
print('  ✅ Registry updated to v1.2.0')
"
else
    echo "  ⚠️  No existing registry found, creating new one..."
    python3 -c "
import json
reg = {
    'registry_version': '1.2.0',
    'updated_at': '$(date -u +%Y-%m-%dT%H:%M:%SZ)',
    'institutional_pillars': {
        'CREATION': 'isp-manager',
        'VERIFICATION': 'sentinela',
        'RESOLUTION': 'maestro'
    },
    'agents': [
        {
            'agent_id': 'windi://agent/core/maestro',
            'codename': 'Maestro',
            'pillar': 'RESOLUTION',
            'name': 'WINDI Governance Orchestrator',
            'version': '1.0.0',
            'status': 'ACTIVE',
            'execution_mode': 'human-mediated',
            'path': '/opt/windi/agents/maestro',
            'entry_point': 'maestro_agent.py',
            'registered_at': '$(date -u +%Y-%m-%dT%H:%M:%SZ)'
        }
    ]
}
with open('$REGISTRY', 'w') as f:
    json.dump(reg, f, indent=2, ensure_ascii=False)
print('  ✅ New registry created v1.2.0')
"
fi

# Verify deployment
echo "🔍 Verifying deployment..."
for f in manifest.json capsule.json policy.json maestro_agent.py; do
    if [ -f "$AGENT_DIR/$f" ]; then
        echo "  ✅ $f"
    else
        echo "  ❌ $f MISSING!"
        exit 1
    fi
done
for f in __init__.py decision_router.py sla_guardian.py resolution_assembler.py; do
    if [ -f "$AGENT_DIR/modules/$f" ]; then
        echo "  ✅ modules/$f"
    else
        echo "  ❌ modules/$f MISSING!"
        exit 1
    fi
done

# Test agent
echo "🧪 Testing agent..."
python3 "$AGENT_DIR/maestro_agent.py" status
if [ $? -eq 0 ]; then
    echo "  ✅ Agent responds"
else
    echo "  ❌ Agent test failed!"
    exit 1
fi

# Show final structure
echo "📂 Final structure:"
find "$AGENT_DIR" -type f | sort

echo "═══════════════════════════════════════════════════════════"
echo "🎼  Deployment complete!"
echo ""
echo "  Quick test commands:"
echo "    python3 $AGENT_DIR/maestro_agent.py status"
echo "    python3 $AGENT_DIR/maestro_agent.py ingest"
echo "    python3 $AGENT_DIR/maestro_agent.py check_sla"
echo "    python3 $AGENT_DIR/maestro_agent.py dashboard"
echo "    python3 $AGENT_DIR/maestro_agent.py report"
echo ""
echo "  Governance Cycle:"
echo "    python3 $AGENT_DIR/maestro_agent.py acknowledge --finding-id <id> --by \"Human Dragon\""
echo "    python3 $AGENT_DIR/maestro_agent.py resolve --finding-id <id> --by \"Human Dragon\" --note \"Fixed\""
echo "    python3 $AGENT_DIR/maestro_agent.py close --finding-id <id> --by \"Human Dragon\""
echo ""
echo "  AI processes. Human decides. WINDI guarantees."
echo "═══════════════════════════════════════════════════════════"
