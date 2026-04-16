#!/bin/bash
# §137 — Deploy Streaming (WINDI-LAW)
# Execute: sudo bash /home/windi/deploy-streaming.sh

set -e

echo "════════════════════════════════════════════════════════════"
echo "§137 — DEPLOY STREAMING (Demo VC Berlin)"
echo "════════════════════════════════════════════════════════════"

# 1. Nginx patch
echo ""
echo "[1/3] Patching nginx for SSE..."
bash /home/windi/patch-nginx-streaming.sh

# 2. Restart WINDI-LAW
echo ""
echo "[2/3] Restarting windi-law..."
systemctl restart windi-law
sleep 3
systemctl status windi-law | head -8

# 3. Smoke test
echo ""
echo "[3/3] Smoke test..."
curl -s -N --max-time 10 -X POST "http://127.0.0.1:8122/ai-draft/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Was ist DSGVO?",
    "doc_type": "analyse",
    "jurisdiction": "DE",
    "lang": "DE",
    "context": "Smoke test",
    "tier": "HIGH",
    "did": "SMOKE",
    "wallet_id": "SMOKE"
  }' 2>&1 | head -20

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ §137 Streaming deployed!"
echo "Test: curl -N https://windi-domain.com/law/ai-draft/stream"
echo "════════════════════════════════════════════════════════════"
