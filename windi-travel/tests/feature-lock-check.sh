#!/bin/bash
# ══════════════════════════════════════════════════════════════
# WINDI-LAW Feature Lock Check v1.0
# Verifies all SEALED features exist before commit
# ══════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
PROMPT_AREA="$BASE_DIR/prompt-area/index.html"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  WINDI-LAW Feature Lock Check v1.0                        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

FAILED=0
PASSED=0

check_marker() {
    local feature="$1"
    local file="$2"
    local marker="$3"

    if grep -q "$marker" "$file" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $feature"
        ((PASSED++))
    else
        echo -e "  ${RED}✗${NC} $feature — marker '$marker' NOT FOUND"
        ((FAILED++))
    fi
}

echo "Checking prompt-area/index.html..."
echo ""

# Feature 1: Media Bar
check_marker "Media Bar (cmd-media-bar)" "$PROMPT_AREA" "cmd-media-bar"
check_marker "Media Bar (handleMedia)" "$PROMPT_AREA" "function handleMedia"
check_marker "Media Bar (attachedFiles)" "$PROMPT_AREA" "var attachedFiles"

# Feature 2: SHA-256 client-side
check_marker "SHA-256 (hashFile)" "$PROMPT_AREA" "async function hashFile"
check_marker "SHA-256 (crypto.subtle)" "$PROMPT_AREA" "crypto.subtle.digest"

# Feature 3: Identity SCHLÜSSEL
check_marker "SCHLÜSSEL (sb-schluessel)" "$PROMPT_AREA" "sb-schluessel"
check_marker "SCHLÜSSEL (copyFingerprint)" "$PROMPT_AREA" "function copyFingerprint"

# Feature 4: Identity WALLET
check_marker "WALLET (sb-wallet)" "$PROMPT_AREA" "sb-wallet"
check_marker "WALLET (sb-pioneer-num)" "$PROMPT_AREA" "sb-pioneer-num"

# Feature 5: ab-seal + Modal I9
check_marker "ab-seal (openSealModal)" "$PROMPT_AREA" "function openSealModal"
check_marker "ab-seal (confirmSeal)" "$PROMPT_AREA" "async function confirmSeal"
check_marker "ab-seal (modal-i9)" "$PROMPT_AREA" "modal-i9"

# Feature 6: ab-verify
check_marker "ab-verify (verifyReceipt)" "$PROMPT_AREA" "async function verifyReceipt"

# Feature 7: ab-chain
check_marker "ab-chain (showChain)" "$PROMPT_AREA" "async function showChain"

# Feature 8: CIA badges
check_marker "CIA (updateCIA)" "$PROMPT_AREA" "function updateCIA"
check_marker "CIA (cia-i9)" "$PROMPT_AREA" "cia-i9"

# Feature 9: QR SVG
check_marker "QR (generateQRSVG)" "$PROMPT_AREA" "function generateQRSVG"
check_marker "QR (showQRCode)" "$PROMPT_AREA" "function showQRCode"

# Feature 10: Wallet Gate Link
check_marker "Wallet Gate (createWallet)" "$PROMPT_AREA" "createWallet"

# Feature 11: i18n
check_marker "i18n (LANG)" "$PROMPT_AREA" "var LANG"
check_marker "i18n (setLang)" "$PROMPT_AREA" "function setLang"

# Feature 12: Theme
check_marker "Theme (toggleTheme)" "$PROMPT_AREA" "function toggleTheme"
check_marker "Theme (data-theme)" "$PROMPT_AREA" "data-theme"

echo ""
echo "════════════════════════════════════════════════════════════"
echo -e "Results: ${GREEN}$PASSED passed${NC}, ${RED}$FAILED failed${NC}"
echo "════════════════════════════════════════════════════════════"

if [ $FAILED -gt 0 ]; then
    echo ""
    echo -e "${RED}FEATURE LOCK VIOLATION${NC}"
    echo "One or more SEALED features are missing."
    echo "Check FEATURE_LOCK.md and restore from git history."
    echo ""
    exit 1
else
    echo ""
    echo -e "${GREEN}ALL FEATURES VERIFIED${NC}"
    echo "Safe to commit."
    echo ""
    exit 0
fi
