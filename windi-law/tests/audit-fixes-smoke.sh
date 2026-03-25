#!/bin/bash
# ══════════════════════════════════════════════════════════════
# WINDI-LAW Audit Fixes — Smoke Test Suite
# Created: 2026-03-25
# Tests: C1 (SCHLÜSSEL), C2 (WALLET), C3 (contrast), M2 (DID copy)
# Uso: bash /opt/windi/windi-law/tests/audit-fixes-smoke.sh
# ══════════════════════════════════════════════════════════════

FILE="/opt/windi/windi-law/workspace/index.html"
PASS=0
FAIL=0

echo "═══════════════════════════════════════════════════════════"
echo "  WINDI-LAW Audit Fixes — 10 Testes de Contraste + Componentes"
echo "═══════════════════════════════════════════════════════════"
echo ""

# TESTE C1: SCHLÜSSEL panel existe
echo -n "[C1] SCHLÜSSEL panel... "
if grep -q "sb-schluessel" "$FILE" && grep -q "sb-key-hash" "$FILE" && grep -q "Ed25519" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE C2: WALLET panel existe
echo -n "[C2] WALLET panel... "
if grep -q "sb-wallet" "$FILE" && grep -q "sb-pioneer-num" "$FILE" && grep -q "sb-tier" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE C3: KLAR theme contrast fix
echo -n "[C3] KLAR theme contrast... "
if grep -q "\-\-parch:.*#2A2010" "$FILE" && grep -q "\-\-muted:.*#5A4A2A" "$FILE" && grep -q "\-\-dim:.*#7A6850" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE H1: Chips visible in KLAR
echo -n "[H1] Chips visible in KLAR... "
if grep -q "\-\-chip-bg:" "$FILE" && grep -q "\-\-chip-border:" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE H2: Truth buttons KLAR override
echo -n "[H2] Truth buttons KLAR... "
if grep -q '\[data-theme="klar"\] .truth-btn' "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE M1: Statusbar visible KLAR
echo -n "[M1] Statusbar visible KLAR... "
if grep -q '\[data-theme="klar"\] .statusbar' "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE M2: DID tooltip + copy
echo -n "[M2] DID tooltip + copy... "
if grep -q "data-full-did" "$FILE" && grep -q "copyDid" "$FILE" && grep -q "tl-did::after" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE i18n: Identity translations
echo -n "[i18n] Identity translations... "
if grep -q "sbLIdentity" "$FILE" && grep -q "sbSchluesselTitle" "$FILE" && grep -q "sbWalletTitle" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE FALLBACK: Fallback state visible when no session
echo -n "[FB] Fallback state visible... "
if grep -q "sb-ic-pending" "$FILE" && grep -q "sb-connect-btn" "$FILE" && grep -q "nicht verbunden\|não conectado\|not connected" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE STATUS: Status badges in headers
echo -n "[ST] Status badges... "
if grep -q "sb-key-status" "$FILE" && grep -q "sb-wallet-status" "$FILE" && grep -q "sb-ic-status.connected\|sb-ic-status.pending" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  RESULTADO: $PASS/10 PASS · $FAIL FAIL"
echo "═══════════════════════════════════════════════════════════"

echo ""
if [ $FAIL -eq 0 ]; then
    echo "🟢 ALL 10 AUDIT FIXES VERIFIED"
    exit 0
else
    echo "🔴 $FAIL/10 AUDIT FIXES MISSING"
    exit 1
fi
