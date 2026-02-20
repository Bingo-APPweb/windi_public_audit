#!/bin/bash
# ============================================================================
# WINDI Wallet → Desktop Link Update
# ============================================================================
# Adds "Abrir Desktop" button to the existing Wallet page (port 8099)
# Run AFTER deploy.sh
# ============================================================================

set -e

GOLD='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GOLD}[Wallet Update]${NC} Adding Desktop link to Wallet..."

# Find the Wallet HTML file
# Common locations based on WINDI infrastructure
WALLET_DIRS=(
    "/opt/windi/wallet"
    "/opt/windi/a4desk-landing"
    "/opt/windi/a4desk-editor"
)

WALLET_FILE=""
for dir in "${WALLET_DIRS[@]}"; do
    for f in "$dir/index.html" "$dir/wallet.html" "$dir/templates/index.html"; do
        if [ -f "$f" ]; then
            WALLET_FILE="$f"
            break 2
        fi
    done
done

if [ -z "$WALLET_FILE" ]; then
    echo -e "${RED}  Could not auto-detect Wallet HTML file.${NC}"
    echo ""
    echo -e "  ${GOLD}Manual integration needed:${NC}"
    echo ""
    echo "  Add this HTML snippet to your Wallet page where appropriate:"
    echo ""
    cat << 'HTML_SNIPPET'
<!-- WINDI Desktop Link — Add to Wallet page -->
<a href="/desktop/"
   style="
     display: inline-flex;
     align-items: center;
     gap: 10px;
     padding: 14px 28px;
     background: linear-gradient(135deg, #C9A84C 0%, #A8893D 100%);
     color: #0A0C14;
     text-decoration: none;
     border-radius: 12px;
     font-family: 'Bricolage Grotesque', 'Outfit', sans-serif;
     font-weight: 700;
     font-size: 15px;
     letter-spacing: 0.3px;
     transition: all 0.2s ease;
     box-shadow: 0 4px 16px rgba(201,168,76,0.2);
   "
   onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 8px 24px rgba(201,168,76,0.3)'"
   onmouseout="this.style.transform='translateY(0)';this.style.boxShadow='0 4px 16px rgba(201,168,76,0.2)'"
>
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
    <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
    <line x1="8" y1="21" x2="16" y2="21"></line>
    <line x1="12" y1="17" x2="12" y2="21"></line>
  </svg>
  Desktop öffnen
</a>

<!-- Optional: Subtitle beneath the button -->
<p style="
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: #8B7A3D;
  margin-top: 8px;
  letter-spacing: 0.3px;
">
  Suite · Sealing · War Room
</p>
HTML_SNIPPET
    echo ""
    echo -e "  ${GOLD}Or for a minimal text link:${NC}"
    echo '  <a href="/desktop/" style="color:#C9A84C">Desktop öffnen →</a>'
    echo ""
    exit 0
fi

echo -e "${GREEN}  Found Wallet: $WALLET_FILE${NC}"
echo ""
echo -e "  ${GOLD}Please add the Desktop link to this file manually.${NC}"
echo -e "  File: $WALLET_FILE"
echo ""
echo -e "  Minimal insertion:"
echo '  <a href="/desktop/" class="desktop-link">Desktop öffnen →</a>'
echo ""
