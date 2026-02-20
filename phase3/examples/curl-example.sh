#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# WINDI Node Registration — cURL Example
# ═══════════════════════════════════════════════════════════════════
# This script demonstrates the registration flow using curl
# For production, use the Node.js client library
# ═══════════════════════════════════════════════════════════════════

HUB_URL="${HUB_URL:-http://localhost:8070}"
NODE_ID="node:example-bank-frankfurt-01"
DOMAIN="windi.example-bank.de"

echo "═══════════════════════════════════════════════════"
echo "  WINDI Node Registration — cURL Example"
echo "═══════════════════════════════════════════════════"
echo ""
echo "Hub URL: ${HUB_URL}"
echo "Node ID: ${NODE_ID}"
echo ""

# ─── Step 1: Check Hub Health ────────────────────────────────────────
echo "1. Checking Hub health..."
curl -s "${HUB_URL}/health" | jq .
echo ""

# ─── Step 2: Get Hub Public Key ──────────────────────────────────────
echo "2. Getting Hub public key..."
curl -s "${HUB_URL}/hub/public-key" | jq .
echo ""

# ─── Step 3: Generate Keypair ────────────────────────────────────────
# In production, use the Node.js client. This is for demonstration only.
echo "3. Generating Ed25519 keypair..."
echo "   (In production, use: node register-node.js)"
echo ""

# For this example, we'll use a pre-generated test keypair
# DO NOT USE THESE KEYS IN PRODUCTION
TEST_PUBLIC_KEY="VGVzdFB1YmxpY0tleUZvckRlbW9uc3RyYXRpb24xMjM="
TEST_SECRET_KEY="VGVzdFNlY3JldEtleUZvckRlbW9uc3RyYXRpb24xMjM0NTY3ODkwMTIzNDU2Nzg5MDEyMzQ1Njc4OTA="

echo "   Public Key: ${TEST_PUBLIC_KEY:0:20}..."
echo ""

# ─── Step 4: Register Node ───────────────────────────────────────────
echo "4. Registering node with Hub..."
REGISTER_RESPONSE=$(curl -s -X POST "${HUB_URL}/nodes/register" \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "'"${NODE_ID}"'",
    "domain": "'"${DOMAIN}"'",
    "public_key": "'"${TEST_PUBLIC_KEY}"'",
    "roles": ["verifier", "anchor_publisher"],
    "metadata": {
      "organization": "Example Bank AG",
      "contact": "it-security@example-bank.de"
    }
  }')

echo "${REGISTER_RESPONSE}" | jq .
echo ""

# ─── Step 5: Create and Sign Attestation ─────────────────────────────
echo "5. Creating attestation..."
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "   Timestamp: ${TIMESTAMP}"
echo ""

# The attestation payload (must be signed by the node's secret key)
ATTESTATION='{
  "domain": "'"${DOMAIN}"'",
  "node_id": "'"${NODE_ID}"'",
  "roles": ["verifier", "anchor_publisher"],
  "timestamp": "'"${TIMESTAMP}"'"
}'

echo "   Attestation payload:"
echo "${ATTESTATION}" | jq .
echo ""

echo "   NOTE: In production, sign this payload with Ed25519 using the secret key"
echo "   The signature must be Base64-encoded"
echo ""

# ─── Step 6: Submit Attestation ──────────────────────────────────────
echo "6. Submitting attestation..."
echo "   (This would require a valid signature - skipping in curl demo)"
echo ""

# Example request structure:
# curl -s -X POST "${HUB_URL}/nodes/attest" \
#   -H "Content-Type: application/json" \
#   -d '{
#     "node_id": "'"${NODE_ID}"'",
#     "attestation": '"${ATTESTATION}"',
#     "signature": "BASE64_SIGNATURE_HERE"
#   }'

# ─── Step 7: List Nodes ──────────────────────────────────────────────
echo "7. Listing registered nodes..."
curl -s "${HUB_URL}/nodes" | jq .
echo ""

# ─── Step 8: Get Node Details ────────────────────────────────────────
echo "8. Getting node details..."
curl -s "${HUB_URL}/nodes/${NODE_ID}" | jq .
echo ""

echo "═══════════════════════════════════════════════════"
echo "  Example Complete"
echo "═══════════════════════════════════════════════════"
echo ""
echo "For full registration with signing, use:"
echo "  cd /opt/windi/phase3/examples"
echo "  node register-node.js"
echo ""
echo "AI processes. Human decides. WINDI guarantees."
