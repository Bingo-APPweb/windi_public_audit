#!/bin/bash
# ══════════════════════════════════════════════════════════════
# WINDI-LAW Media Bar — Smoke Test Suite
# Created: 2026-03-25
# Tests: Media buttons, file inputs, attachment preview, i18n
# Uso: bash /opt/windi/windi-law/tests/media-bar-smoke.sh
# ══════════════════════════════════════════════════════════════

FILE="/opt/windi/windi-law/prompt-area/index.html"
PASS=0
FAIL=0

echo "═══════════════════════════════════════════════════════════"
echo "  WINDI-LAW Media Bar — 12 Smoke Tests"
echo "═══════════════════════════════════════════════════════════"
echo ""

# TESTE M1: Media bar container exists
echo -n "[M1] Media bar container... "
if grep -q "cmd-media-bar" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE M2: 4 media buttons exist
echo -n "[M2] 4 media buttons (📎🖼📄🎥)... "
if grep -q "mb-any" "$FILE" && grep -q "mb-img" "$FILE" && grep -q "mb-doc" "$FILE" && grep -q "mb-vid" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE M3: Hidden file inputs exist
echo -n "[M3] Hidden file inputs (mf-*)... "
if grep -q "mf-any" "$FILE" && grep -q "mf-img" "$FILE" && grep -q "mf-doc" "$FILE" && grep -q "mf-vid" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE M4: File accept attributes
echo -n "[M4] Accept attributes... "
if grep -q 'accept="image/\*"' "$FILE" && grep -q 'accept="video/\*"' "$FILE" && grep -q 'accept=".pdf,.docx,.xlsx,.txt"' "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE M5: Attachment preview container
echo -n "[M5] Attachment preview row... "
if grep -q "att-preview" "$FILE" && grep -q "attachment-preview" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE M6: SHA-256 hashFile function
echo -n "[M6] SHA-256 hashFile function... "
if grep -q "async function hashFile" "$FILE" && grep -q "crypto.subtle.digest" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE M7: File limits defined
echo -n "[M7] FILE_LIMITS defined... "
if grep -q "FILE_LIMITS" "$FILE" && grep -q "25 \* 1024 \* 1024" "$FILE" && grep -q "100 \* 1024 \* 1024" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE M8: handleMedia function
echo -n "[M8] handleMedia function... "
if grep -q "async function handleMedia" "$FILE" && grep -q "attachedFiles\[id\]" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE M9: i18n DE tooltips
echo -n "[M9] i18n DE tooltips... "
if grep -q "mbAny:'Anhang'" "$FILE" && grep -q "mbImg:'Bild'" "$FILE" && grep -q "mbDoc:'Dokument'" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE M10: i18n PT tooltips
echo -n "[M10] i18n PT tooltips... "
if grep -q "mbAny:'Anexo'" "$FILE" && grep -q "mbImg:'Imagem'" "$FILE" && grep -q "mbVid:'Vídeo'" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE M11: i18n EN tooltips
echo -n "[M11] i18n EN tooltips... "
if grep -q "mbAny:'Attachment'" "$FILE" && grep -q "mbImg:'Image'" "$FILE" && grep -q "mbDoc:'Document'" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE M12: KLAR theme media buttons
echo -n "[M12] KLAR theme styles... "
if grep -q '\[data-theme="klar"\] .cmd-media-btn' "$FILE" && grep -q '\[data-theme="klar"\] .attachment-preview' "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  RESULTADO: $PASS/12 PASS · $FAIL FAIL"
echo "═══════════════════════════════════════════════════════════"

# ══════════════════════════════════════════════════════════════
# IDENTITY SECTION TESTS
# ══════════════════════════════════════════════════════════════

# TESTE I1: Identity section in sidebar
echo -n "[I1] Identity section in sidebar... "
if grep -q "sb-identity-section" "$FILE" && grep -q "sb-identity-label" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE I2: Connected state container
echo -n "[I2] Connected state container... "
if grep -q "sb-id-connected" "$FILE" && grep -q "sb-id-tier" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE I3: Disconnected state with Gate link
echo -n "[I3] Disconnected state + Gate link... "
if grep -q "sb-id-disconnected" "$FILE" && grep -q "sb-gate-btn" "$FILE" && grep -q "/law/gate" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE I4: Header Gate link
echo -n "[I4] Header Gate link... "
if grep -q "header-gate-link" "$FILE" && grep -q "header-gate-text" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE I5: initSession function
echo -n "[I5] initSession function... "
if grep -q "function initSession" "$FILE" && grep -q "windi_law_wallet" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE I6: i18n identity strings DE
echo -n "[I6] i18n identity DE... "
if grep -q "sbIdentity:'Identität'" "$FILE" && grep -q "sbIdDisconnected:'Nicht verbunden'" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE I7: i18n identity strings PT
echo -n "[I7] i18n identity PT... "
if grep -q "sbIdentity:'Identidade'" "$FILE" && grep -q "sbIdDisconnected:'Não conectado'" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

# TESTE I8: i18n identity strings EN
echo -n "[I8] i18n identity EN... "
if grep -q "sbIdentity:'Identity'" "$FILE" && grep -q "sbIdDisconnected:'Not connected'" "$FILE"; then
    echo "✅ PASS"
    PASS=$((PASS+1))
else
    echo "❌ FAIL"
    FAIL=$((FAIL+1))
fi

TOTAL=$((12 + 8))
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  RESULTADO: $PASS/$TOTAL PASS · $FAIL FAIL"
echo "═══════════════════════════════════════════════════════════"

echo ""
if [ $FAIL -eq 0 ]; then
    echo "🟢 ALL $TOTAL MEDIA BAR + IDENTITY TESTS VERIFIED"
    exit 0
else
    echo "🔴 $FAIL/$TOTAL TESTS FAILED"
    exit 1
fi
