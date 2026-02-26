#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# WINDI SOVEREIGN TEST RUNNER
# "O que separa software de prateleira de um Protocolo de Estado"
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo "  🐉 WINDI SOVEREIGN TEST SUITE"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""

BASE_URL="${BASE_URL:-http://localhost:8108}"

# ─────────────────────────────────────────────────────────────────────────
# 1. Quick Health Check
# ─────────────────────────────────────────────────────────────────────────
echo "┌─────────────────────────────────────────────────────────┐"
echo "│  1. Dragon Server Health                                │"
echo "└─────────────────────────────────────────────────────────┘"

HEALTH=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$BASE_URL/api/dragon/health")
if [ "$HEALTH" = "200" ]; then
    echo "  ✅ Dragon Server: ALIVE"
    curl -s "$BASE_URL/api/dragon/health" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f\"     Dragons: {', '.join(d.get('dragons', []))}\")" 2>/dev/null
else
    echo "  ❌ Dragon Server: DOWN ($HEALTH)"
    echo ""
    echo "  ⚠️  Start the server first: python3 agent_dragon_server.py"
    exit 1
fi
echo ""

# ─────────────────────────────────────────────────────────────────────────
# 2. Endpoint Verification
# ─────────────────────────────────────────────────────────────────────────
echo "┌─────────────────────────────────────────────────────────┐"
echo "│  2. Endpoint Verification                               │"
echo "└─────────────────────────────────────────────────────────┘"

ENDPOINTS=(
    "/api/dragon/health"
    "/sovereignty"
    "/capabilities"
    "/api/dragon/cognitive/hesitation"
)

for EP in "${ENDPOINTS[@]}"; do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "$BASE_URL$EP")
    if [ "$CODE" = "200" ]; then
        printf "  ✅ GET  %-40s %s\n" "$EP" "($CODE)"
    else
        printf "  ❌ GET  %-40s %s\n" "$EP" "($CODE)"
    fi
done
echo ""

# ─────────────────────────────────────────────────────────────────────────
# 3. Chat Response Test
# ─────────────────────────────────────────────────────────────────────────
echo "┌─────────────────────────────────────────────────────────┐"
echo "│  3. Chat Response Test                                  │"
echo "└─────────────────────────────────────────────────────────┘"

START=$(date +%s%N)
CHAT_RESP=$(curl -s -X POST "$BASE_URL/api/dragon/chat" \
    -H "Content-Type: application/json" \
    -d '{"message":"What is your role?","tier":"LOW"}' \
    --max-time 30 -w "\n%{http_code}")
END=$(date +%s%N)
LATENCY=$(( (END - START) / 1000000 ))

HTTP_CODE=$(echo "$CHAT_RESP" | tail -1)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
    echo "  ✅ Chat Response: SUCCESS (${LATENCY}ms)"
else
    echo "  ❌ Chat Response: FAILED ($HTTP_CODE)"
fi
echo ""

# ─────────────────────────────────────────────────────────────────────────
# 4. SGE Analysis Test
# ─────────────────────────────────────────────────────────────────────────
echo "┌─────────────────────────────────────────────────────────┐"
echo "│  4. SGE 6-Layer Analysis Test                           │"
echo "└─────────────────────────────────────────────────────────┘"

SGE_RESP=$(curl -s -X POST "$BASE_URL/api/dragon/sge" \
    -H "Content-Type: application/json" \
    -d '{"text":"Review this compliance document"}' \
    --max-time 10 -w "\n%{http_code}")

SGE_CODE=$(echo "$SGE_RESP" | tail -1)
if [ "$SGE_CODE" = "200" ] || [ "$SGE_CODE" = "201" ]; then
    echo "  ✅ SGE Endpoint: RESPONSIVE"
else
    echo "  ⚠️  SGE Endpoint: $SGE_CODE (may use fallback)"
fi
echo ""

# ─────────────────────────────────────────────────────────────────────────
# 5. Decision Journal Test
# ─────────────────────────────────────────────────────────────────────────
echo "┌─────────────────────────────────────────────────────────┐"
echo "│  5. Decision Journal Test                               │"
echo "└─────────────────────────────────────────────────────────┘"

DEC_RESP=$(curl -s "$BASE_URL/api/dragon/decisions" --max-time 5 -w "\n%{http_code}")
DEC_CODE=$(echo "$DEC_RESP" | tail -1)
if [ "$DEC_CODE" = "200" ]; then
    echo "  ✅ Decision Journal: ACCESSIBLE"
elif [ "$DEC_CODE" = "404" ]; then
    echo "  ⚠️  Decision Journal: No records yet"
else
    echo "  ⚠️  Decision Journal: $DEC_CODE"
fi
echo ""

# ─────────────────────────────────────────────────────────────────────────
# 6. Sovereignty Report
# ─────────────────────────────────────────────────────────────────────────
echo "┌─────────────────────────────────────────────────────────┐"
echo "│  6. Sovereignty Report                                  │"
echo "└─────────────────────────────────────────────────────────┘"

curl -s "$BASE_URL/sovereignty" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    s = d.get('sovereignty', {})
    print(f\"  Local Ratio: {s.get('ratio', 'N/A')}\")
    print(f\"  Local Services: {s.get('local_functions', 'N/A')}\")
    print(f\"  External: {len(d.get('external_services', []))} services\")
    print(f\"  Status: {d.get('status', 'N/A')}\")
except:
    print('  ⚠️  Could not parse sovereignty data')
" 2>/dev/null
echo ""

# ─────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────
echo "═══════════════════════════════════════════════════════════════════════"
echo "  📊 SUMMARY"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""
echo "  To run full E2E tests with Cypress:"
echo "    cd /opt/windi/agent-palette/tests"
echo "    npx cypress run --spec 'cypress/e2e/sovereign-stress.cy.js'"
echo ""
echo "  To run frontend tests in browser console:"
echo "    WINDI_SovereignTest.runAll()"
echo ""
echo "  Keyboard shortcuts:"
echo "    Ctrl+T — Run Sovereign Test"
echo "    Ctrl+H — Health Check"
echo ""
echo "  🐉 \"AI processes. Human decides. WINDI guarantees.\""
echo "═══════════════════════════════════════════════════════════════════════"
echo ""
