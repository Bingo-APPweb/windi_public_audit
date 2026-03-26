#!/bin/bash
# ══════════════════════════════════════════════════════════════
# WINDI-LAW Workspace v3.1 — Smoke Test Suite
# Conservado: 2026-03-24
# Uso: bash /opt/windi/windi-law/tests/workspace-v31-smoke.sh
# ══════════════════════════════════════════════════════════════

FILE="/opt/windi/windi-law/workspace/index.html"
PASS=0
FAIL=0

echo "═══════════════════════════════════════════════════════════"
echo "  WINDI-LAW Workspace v3.1 — 6 Testes Constitucionais"
echo "═══════════════════════════════════════════════════════════"
echo ""

# TESTE 1: Wallet injection context
echo -n "[1/6] Wallet injection context... "
if grep -q "sessionStorage.*windi_law_wallet" "$FILE" && grep -q "__windiLawWallet" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE 2: DID no header
echo -n "[2/6] DID no header... "
if grep -q "tl-did" "$FILE" && grep -q "tl-status" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE 3: G3 botão visível
echo -n "[3/6] G3 Approval Button... "
if grep -q "g3-approval-zone" "$FILE" && grep -q "approveG3" "$FILE" && grep -q "g3-btn" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE 4: Truth selector separado
echo -n "[4/6] Truth selector separado... "
if grep -q "truth-row" "$FILE" && grep -q "setTruthV31" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE 5: Inspector colapsável
echo -n "[5/6] Inspector colapsável... "
if grep -q "insp-toggle" "$FILE" && grep -q "toggleInspector" "$FILE" && grep -q "inspector.*collapsed" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE 6: Nächster Schritt
echo -n "[6/6] Nächster Schritt... "
if grep -q "rc-k5" "$FILE" && grep -q "rc-v5" "$FILE" && grep -q "v5Ready" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  RESULTADO: $PASS/6 PASS · $FAIL FAIL"
echo "═══════════════════════════════════════════════════════════"

# HTTP smoke test
echo ""
echo "[HTTP] Fail-closed test..."
HTTP=$(curl -s -o /dev/null -w '%{http_code}' https://windi-domain.com/law/workspace/)
if [ "$HTTP" = "302" ]; then
    echo "       /law/workspace/ → $HTTP → /law/gate ✅ (fail-closed)"
else
    echo "       /law/workspace/ → $HTTP ⚠️ (esperado 302)"
fi

echo ""
if [ $FAIL -eq 0 ]; then
    echo "🟢 ALL TESTS PASS"
    exit 0
else
    echo "🔴 $FAIL TESTS FAILED"
    exit 1
fi
