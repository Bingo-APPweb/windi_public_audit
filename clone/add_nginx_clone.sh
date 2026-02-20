#!/bin/bash
# Add Clone routes to admin.windia4desk.tech nginx config

CONF="/etc/nginx/sites-available/admin.windia4desk.tech"
BK="/opt/windi/backups/nginx_admin_$(date +%Y%m%d_%H%M%S).conf"

echo "=== WINDI Clone — Nginx Setup ==="

# Backup
sudo cp "$CONF" "$BK"
echo "✅ Backup: $BK"

# Check if already configured
if grep -q "Clone Territory" "$CONF"; then
  echo "⚠️  Clone routes already exist!"
  exit 0
fi

# Create the routes block
CLONE_ROUTES='
    # ── WINDI Clone Territory (→ :8095) ──
    location /clone/ {
        proxy_pass http://127.0.0.1:8095/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /clone/museum {
        proxy_pass http://127.0.0.1:8095/museum;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /clone/museum/ {
        proxy_pass http://127.0.0.1:8095/museum/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /clone/health {
        proxy_pass http://127.0.0.1:8095/health;
        proxy_set_header Host $host;
    }

'

# Insert before "listen 443 ssl;"
sudo sed -i "/listen 443 ssl;/i\\$CLONE_ROUTES" "$CONF"

echo "✅ Clone routes added"

# Test and reload
echo ""
echo "Testing nginx config..."
sudo nginx -t
if [ $? -eq 0 ]; then
  sudo systemctl reload nginx
  echo "✅ Nginx reloaded"

  echo ""
  echo "Testing..."
  sleep 1
  curl -s -o /dev/null -w "/clone/health → %{http_code}\n" https://admin.windia4desk.tech/clone/health
  curl -s -o /dev/null -w "/clone/museum → %{http_code}\n" https://admin.windia4desk.tech/clone/museum

  echo ""
  echo "═══════════════════════════════════════"
  echo "✅ DONE!"
  echo ""
  echo "🌐 https://admin.windia4desk.tech/clone/museum"
  echo "═══════════════════════════════════════"
else
  echo "❌ Nginx config error! Restoring backup..."
  sudo cp "$BK" "$CONF"
  sudo nginx -t && sudo systemctl reload nginx
fi
