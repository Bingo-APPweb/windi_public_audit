#!/bin/bash
# W-MAIL-001 — Loopback Smoke Test (postmaster → postmaster)

echo "═══════════════════════════════════════════════════════════════"
echo "W-MAIL-001 — Loopback Smoke Test"
echo "Testing: postmaster@windisites.de → postmaster@windisites.de"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Send test email
echo "[1/3] Sending test email..."
echo "Subject: W-MAIL-001 Dual DKIM Test
From: postmaster@windisites.de
To: postmaster@windisites.de

This is a loopback test for W-MAIL-001 dual DKIM signing.

Expected headers:
- DKIM-Signature with s=ed25519; d=windisites.de
- DKIM-Signature with s=rsa; d=windisites.de

Genesis Day 1 — $(date -u +%Y-%m-%dT%H:%M:%SZ)
" | sudo docker exec -i windi-mailserver sendmail -f postmaster@windisites.de postmaster@windisites.de

echo "✅ Email sent"
echo ""

# Wait for delivery
echo "[2/3] Waiting 10 seconds for delivery..."
sleep 10

# Check for email
echo "[3/3] Checking mailbox..."
EMAIL_FILE=$(sudo docker exec windi-mailserver find /var/mail/windisites.de/postmaster/new/ -type f 2>/dev/null | head -1)

if [ -z "$EMAIL_FILE" ]; then
  echo "❌ No email found in mailbox"
  echo ""
  echo "Debug:"
  echo "  sudo docker exec windi-mailserver ls -la /var/mail/windisites.de/postmaster/new/"
  echo "  sudo docker exec windi-mailserver tail -50 /var/log/mail.log"
  exit 1
fi

echo "✅ Email received: $EMAIL_FILE"
echo ""

# Extract DKIM headers
echo "═══════════════════════════════════════════════════════════════"
echo "DKIM Signatures Found:"
echo "═══════════════════════════════════════════════════════════════"

sudo docker exec windi-mailserver cat "$EMAIL_FILE" | grep -A3 "DKIM-Signature:" | head -20

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Verification:"
echo "═══════════════════════════════════════════════════════════════"

ED25519_SIG=$(sudo docker exec windi-mailserver cat "$EMAIL_FILE" | grep "DKIM-Signature:" | grep "s=ed25519")
RSA_SIG=$(sudo docker exec windi-mailserver cat "$EMAIL_FILE" | grep "DKIM-Signature:" | grep "s=rsa")

if [ -n "$ED25519_SIG" ]; then
  echo "✅ Ed25519 signature present (s=ed25519; d=windisites.de)"
else
  echo "❌ Ed25519 signature MISSING"
fi

if [ -n "$RSA_SIG" ]; then
  echo "✅ RSA signature present (s=rsa; d=windisites.de)"
else
  echo "❌ RSA signature MISSING"
fi

echo ""

if [ -n "$ED25519_SIG" ] && [ -n "$RSA_SIG" ]; then
  echo "═══════════════════════════════════════════════════════════════"
  echo "✅ DUAL DKIM SIGNING VALIDATED"
  echo "═══════════════════════════════════════════════════════════════"
  echo ""
  echo "NEXT STEP: mail-tester.com"
  echo ""
  echo "1. Go to: https://www.mail-tester.com/"
  echo "2. Copy the generated test email address"
  echo "3. Send email via SnappyMail (https://mail.windisites.de/)"
  echo "4. Check score (target ≥8.0/10)"
  echo ""
  echo "If score ≥8.0 → GO for external Gmail test"
  echo "If score <8.0 → Call Guardian for review"
  exit 0
else
  echo "═══════════════════════════════════════════════════════════════"
  echo "❌ DUAL DKIM INCOMPLETE"
  echo "═══════════════════════════════════════════════════════════════"
  echo ""
  echo "Debug commands:"
  echo "  sudo docker exec windi-mailserver cat $EMAIL_FILE | head -50"
  echo "  sudo docker exec windi-mailserver tail -100 /var/log/mail.log | grep -i dkim"
  exit 1
fi
