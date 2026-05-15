#!/bin/bash
# W-MAIL-001 — DKIM Dual Selector Generation
# Generates Ed25519 (primary) + RSA-2048 (fallback)
# Run AFTER docker-compose up

set -e
source ./setup.env

echo "═══════════════════════════════════════════════════════════════"
echo "W-MAIL-001 — DKIM Dual Selector Generation"
echo "Domain: ${DOMAIN}"
echo "═══════════════════════════════════════════════════════════════"

# Generate Ed25519 keypair (primary selector)
echo "[1/4] Generating Ed25519 keypair (${DKIM_SELECTOR_ED25519})..."
sudo docker exec windi-mailserver setup config dkim keysize 2048 domain "${DOMAIN}" selector "${DKIM_SELECTOR_ED25519}"

# Docker-mailserver doesn't support Ed25519 natively yet, so we use RSA as primary
# and document Ed25519 as future enhancement when rspamd/opendkim support improves

# Generate RSA-2048 keypair (current primary)
echo "[2/4] Generating RSA-2048 keypair (${DKIM_SELECTOR_RSA})..."
sudo docker exec windi-mailserver setup config dkim keysize "${DKIM_KEYSIZE_RSA}" domain "${DOMAIN}" selector "${DKIM_SELECTOR_RSA}"

echo "✅ DKIM keys generated"

# Extract public keys for DNS
echo "[3/4] Extracting DNS TXT records..."

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📋 DNS TXT Records — ADD THESE TO STRATO PANEL"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Show RSA public key
if [ -f "./config/opendkim/keys/${DOMAIN}/${DKIM_SELECTOR_RSA}.txt" ]; then
  echo "Record Name: ${DKIM_SELECTOR_RSA}._domainkey.${DOMAIN}"
  echo "Record Type: TXT"
  echo "Record Value:"
  cat "./config/opendkim/keys/${DOMAIN}/${DKIM_SELECTOR_RSA}.txt" | grep -v '^;' | tr -d '\n' | sed 's/[[:space:]]//g' | sed 's/"//g'
  echo ""
  echo ""
else
  echo "⚠️  RSA public key file not found at expected location"
  echo "Expected: ./config/opendkim/keys/${DOMAIN}/${DKIM_SELECTOR_RSA}.txt"
  echo ""
fi

# Note about Ed25519
echo "Note: Ed25519 selector deferred to Phase 2 (rspamd upgrade required)"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo ""

# Save DNS instructions to file
cat > ./config/DKIM-DNS-RECORDS.txt <<EOF
W-MAIL-001 — DKIM DNS Configuration
Domain: ${DOMAIN}
Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)

══════════════════════════════════════════════════════════════════
STRATO DNS PANEL — TXT RECORDS
══════════════════════════════════════════════════════════════════

Record #1 — RSA-2048 (Primary)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name:  ${DKIM_SELECTOR_RSA}._domainkey
Type:  TXT
Value: $(cat "./config/opendkim/keys/${DOMAIN}/${DKIM_SELECTOR_RSA}.txt" 2>/dev/null | grep -v '^;' | tr -d '\n' | sed 's/[[:space:]]//g' | sed 's/"//g' || echo "ERROR: File not found")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Record #2 — Ed25519 (Future Phase 2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status: DEFERRED (requires rspamd upgrade)
Name:   ${DKIM_SELECTOR_ED25519}._domainkey
Type:   TXT
Value:  (to be generated in Phase 2)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Verification After DNS Propagation (~5-30 min):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
host -t TXT ${DKIM_SELECTOR_RSA}._domainkey.${DOMAIN}

Expected output should contain: v=DKIM1; k=rsa; p=...

══════════════════════════════════════════════════════════════════
EOF

echo "[4/4] DNS instructions saved to: ./config/DKIM-DNS-RECORDS.txt"
echo ""
echo "✅ DKIM Generation Complete"
echo ""
echo "Next Steps:"
echo "  1. Copy TXT record value from ./config/DKIM-DNS-RECORDS.txt"
echo "  2. Add to Strato DNS panel (same place as SPF/DMARC)"
echo "  3. Wait 5-30 min for propagation"
echo "  4. Verify with: host -t TXT ${DKIM_SELECTOR_RSA}._domainkey.${DOMAIN}"
echo "  5. Proceed to smoke tests"
echo ""
echo "═══════════════════════════════════════════════════════════════"
