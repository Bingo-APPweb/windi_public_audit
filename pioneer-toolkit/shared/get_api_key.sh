#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════════
# WINDI Pioneer Toolkit — Obter API Key em 30 segundos
# Uso: ./get_api_key.sh "Nome da Empresa" SEED|NODAL|SOVEREIGN
# ══════════════════════════════════════════════════════════════════════════════

NOME="${1:-Pioneer}"
TIER="${2:-SEED}"
BASE="https://windi-domain.com"

echo "=== WINDI API Key · Pioneer Program ==="
echo "Nome: ${NOME}"
echo "Tier: ${TIER}"
echo ""

RESULT=$(curl -s -X POST "${BASE}/api-keys/create" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"${NOME}\",
    \"tier\": \"${TIER}\",
    \"description\": \"Pioneer Program — ${NOME}\"
  }")

echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "$RESULT"

echo ""
echo "IMPORTANTE: Guarde a api_key retornada."
echo "            Ela não pode ser recuperada depois."
echo ""
echo "Para usar nos scripts:"
echo "  export WINDI_API_KEY=wnd_live_xxx"
