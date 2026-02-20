#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# WINDI Phase 3: Quick Setup Script
# ═══════════════════════════════════════════════════════════════════

set -e

echo "═══════════════════════════════════════════════════"
echo "  WINDI Phase 3: Hub Node Registry Setup"
echo "═══════════════════════════════════════════════════"
echo ""

cd /opt/windi/phase3

# ─── Install Dependencies ────────────────────────────────────────────
echo "1. Installing hub-node-registry dependencies..."
cd hub-node-registry
npm install
cd ..

echo ""
echo "2. Installing windi-node-identity-client dependencies..."
cd windi-node-identity-client
npm install
cd ..

echo ""
echo "3. Creating examples/keys directory..."
mkdir -p examples/keys

# ─── Generate Hub Signing Key ────────────────────────────────────────
echo ""
echo "4. Generating Hub signing key..."
HUB_KEY=$(node -e "
const nacl = require('./hub-node-registry/node_modules/tweetnacl');
const util = require('./hub-node-registry/node_modules/tweetnacl-util');
const seed = nacl.randomBytes(32);
console.log(util.encodeBase64(seed));
")
echo "   Hub Signing Key (save this securely):"
echo "   HUB_SIGNING_KEY=${HUB_KEY}"
echo ""

# ─── Create .env File ────────────────────────────────────────────────
echo "5. Creating .env file..."
cat > .env << EOF
# WINDI Phase 3 Environment
DATABASE_URL=postgresql://windi:windi@localhost:5432/windi_hub
HUB_SIGNING_KEY=${HUB_KEY}
PORT=8070
EOF
echo "   Created .env"

echo ""
echo "═══════════════════════════════════════════════════"
echo "  Setup Complete!"
echo "═══════════════════════════════════════════════════"
echo ""
echo "  To start with Docker:"
echo "    cd /opt/windi/phase3"
echo "    docker-compose up -d"
echo ""
echo "  To start manually (requires PostgreSQL):"
echo "    cd /opt/windi/phase3/hub-node-registry"
echo "    source ../.env"
echo "    npm start"
echo ""
echo "  To register a test node:"
echo "    cd /opt/windi/phase3/examples"
echo "    node register-node.js"
echo ""
echo "  AI processes. Human decides. WINDI guarantees."
