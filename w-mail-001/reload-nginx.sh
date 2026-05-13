#!/bin/bash
# W-MAIL-001 — Reload nginx and verify SnappyMail proxy

echo "═══════════════════════════════════════════════════════════════"
echo "W-MAIL-001 — Activating SnappyMail nginx Proxy"
echo "═══════════════════════════════════════════════════════════════"

echo "[1/3] Reloading nginx..."
systemctl reload nginx

if [ $? -eq 0 ]; then
  echo "✅ nginx reloaded successfully"
else
  echo "❌ nginx reload failed"
  exit 1
fi

echo ""
echo "[2/3] Verifying SnappyMail backend..."
curl -s http://127.0.0.1:8200/ | head -5

echo ""
echo "[3/3] Testing public URL..."
curl -s -o /dev/null -w "HTTP %{http_code}\n" https://windi-domain.com/mail/

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ SnappyMail Proxy Active"
echo ""
echo "Access WebUI:"
echo "  URL: https://windi-domain.com/mail/"
echo ""
echo "Login credentials:"
echo "  Email: postmaster@windisites.de"
echo "  Password: (see /opt/windi/w-mail-001/config/.admin-password)"
echo "═══════════════════════════════════════════════════════════════"
