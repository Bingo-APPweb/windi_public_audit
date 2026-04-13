#!/bin/bash
# ═══════════════════════════════════════════════
# W-CACHE-001 · SSE STRESS TEST
# Validates behavior under pressure with policy
# ═══════════════════════════════════════════════

BASE="https://windi-domain.com/verify"

echo "🔥 SSE Stress Test START - $(date)"
echo "   Target: $BASE"
echo "   Requests: 100 with jitter"
echo ""

for i in {1..100}
do
  ID="WINDI-STRESS-$((RANDOM % 10))"

  curl -s "$BASE/$ID" > /dev/null &

  # Jitter to simulate real world
  sleep 0.05
done

wait

echo ""
echo "✅ Stress Test DONE - $(date)"
