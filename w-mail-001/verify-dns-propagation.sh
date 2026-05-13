#!/bin/bash
# W-MAIL-001 — Verify DNS Propagation (5 critical records)

echo "═══════════════════════════════════════════════════════════════"
echo "W-MAIL-001 — DNS Propagation Verification"
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "═══════════════════════════════════════════════════════════════"
echo ""

PASS=0
FAIL=0

# 1. SPF
echo "[1/5] SPF Record..."
SPF=$(dig windisites.de TXT +short | grep -i "v=spf1")
if [ -n "$SPF" ]; then
  echo "✅ SPF: $SPF"
  ((PASS++))
else
  echo "❌ SPF: NOT FOUND"
  ((FAIL++))
fi
echo ""

# 2. DMARC
echo "[2/5] DMARC Record..."
DMARC=$(dig _dmarc.windisites.de TXT +short)
if [ -n "$DMARC" ]; then
  echo "✅ DMARC: $DMARC"
  ((PASS++))
else
  echo "❌ DMARC: NOT FOUND"
  ((FAIL++))
fi
echo ""

# 3. DKIM Ed25519
echo "[3/5] DKIM Ed25519..."
ED25519=$(dig ed25519._domainkey.windisites.de TXT +short)
if echo "$ED25519" | grep -q "k=ed25519"; then
  echo "✅ Ed25519: $(echo $ED25519 | tr -d '\"')"
  ((PASS++))
else
  echo "❌ Ed25519: NOT FOUND or INCORRECT"
  echo "   Got: $ED25519"
  ((FAIL++))
fi
echo ""

# 4. DKIM RSA
echo "[4/5] DKIM RSA..."
RSA=$(dig rsa._domainkey.windisites.de TXT +short | tr -d '\n' | tr -d ' ')
if echo "$RSA" | grep -q "k=rsa"; then
  echo "✅ RSA: v=DKIM1; k=rsa; p=MIIBIjAN... ($(echo $RSA | wc -c) chars)"
  ((PASS++))
else
  echo "❌ RSA: NOT FOUND or INCORRECT"
  echo "   Got: $(echo $RSA | head -c 100)..."
  ((FAIL++))
fi
echo ""

# 5. MX
echo "[5/5] MX Record..."
MX=$(dig windisites.de MX +short)
if echo "$MX" | grep -q "mail.windisites.de"; then
  echo "✅ MX: $MX"
  ((PASS++))
else
  echo "❌ MX: NOT FOUND"
  ((FAIL++))
fi
echo ""

# Summary
echo "═══════════════════════════════════════════════════════════════"
echo "Results: $PASS/5 passed, $FAIL/5 failed"
echo "═══════════════════════════════════════════════════════════════"

if [ $PASS -eq 5 ]; then
  echo ""
  echo "✅ ALL DNS RECORDS PROPAGATED"
  echo ""
  echo "NEXT STEP: Loopback Smoke Test"
  echo ""
  echo "Run:"
  echo "  bash /opt/windi/w-mail-001/loopback-test.sh"
  echo ""
  exit 0
else
  echo ""
  echo "⏳ Propagation incomplete. Wait 5-10 min and run again:"
  echo "  bash /opt/windi/w-mail-001/verify-dns-propagation.sh"
  echo ""
  exit 1
fi
