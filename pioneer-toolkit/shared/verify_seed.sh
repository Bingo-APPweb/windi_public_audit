#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════════
# WINDI Pioneer Toolkit — Verificar qualquer Seed ID
# Uso: ./verify_seed.sh SEED-4b5d7eb4...
# ══════════════════════════════════════════════════════════════════════════════

SEED_ID="${1:-}"
BASE="https://windi-domain.com"

if [ -z "$SEED_ID" ]; then
    echo "Uso: ./verify_seed.sh <SEED_ID>"
    echo ""
    echo "Exemplo:"
    echo "  ./verify_seed.sh SEED-4b5d7eb4ebef3dbabddae551"
    exit 1
fi

echo "=== WINDI Verify ==="
echo "Seed: ${SEED_ID}"
echo ""

# Tentar primeiro o verify-public
RESULT=$(curl -s "${BASE}/verify-public/api/verify/${SEED_ID}" 2>/dev/null)

if echo "$RESULT" | grep -q "seed_id\|hash\|status"; then
    echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "$RESULT"
else
    # Fallback para receipts API
    RESULT=$(curl -s "${BASE}/api/receipts/${SEED_ID}" 2>/dev/null)
    echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "$RESULT"
fi

echo ""
echo "Link público:"
echo "   ${BASE}/verify-public/?id=${SEED_ID}"
