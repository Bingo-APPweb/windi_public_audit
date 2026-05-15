#!/bin/bash
# W-MAIL-001 — Let's Encrypt Certificate Installation
# Run with: sudo bash /opt/windi/w-mail-001/install-cert.sh

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "W-MAIL-001 — Let's Encrypt Certificate Request"
echo "Domain: mail.windisites.de"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check if certificate already exists
if [ -d "/etc/letsencrypt/live/mail.windisites.de" ]; then
  echo "✅ Certificate already exists at /etc/letsencrypt/live/mail.windisites.de"
  echo ""
  echo "Certificate details:"
  certbot certificates -d mail.windisites.de
  exit 0
fi

# Request new certificate
echo "[1/3] Stopping nginx..."
systemctl stop nginx

echo "[2/3] Requesting certificate from Let's Encrypt..."
certbot certonly \
  --standalone \
  -d mail.windisites.de \
  --non-interactive \
  --agree-tos \
  --email postmaster@windisites.de \
  --preferred-challenges http

if [ $? -eq 0 ]; then
  echo "✅ Certificate obtained successfully"
else
  echo "❌ Certificate request failed"
  systemctl start nginx
  exit 1
fi

echo "[3/3] Starting nginx..."
systemctl start nginx

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ Certificate Installation Complete"
echo ""
echo "Certificate location:"
echo "  Fullchain: /etc/letsencrypt/live/mail.windisites.de/fullchain.pem"
echo "  Private:   /etc/letsencrypt/live/mail.windisites.de/privkey.pem"
echo ""
echo "Validity:"
certbot certificates -d mail.windisites.de | grep -E "(Expiry|Domains)"
echo "═══════════════════════════════════════════════════════════════"
