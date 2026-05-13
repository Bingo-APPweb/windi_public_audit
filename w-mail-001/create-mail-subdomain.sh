#!/bin/bash
# Create dedicated server block for mail.windisites.de
# Guardian-approved: Opção C corrigida

set -e

NGINX_CONF="/etc/nginx/sites-enabled/mail.windisites.de"

echo "═══════════════════════════════════════════════════════════════"
echo "Creating dedicated server block: mail.windisites.de"
echo "Guardian-approved: Webmail isolation architecture"
echo "═══════════════════════════════════════════════════════════════"

# Verify certificate exists
if [ ! -f "/etc/letsencrypt/live/mail.windisites.de/fullchain.pem" ]; then
  echo "❌ Certificate not found"
  exit 1
fi

echo "✅ Certificate verified"

# Create server block
echo ""
echo "Creating nginx server block..."

cat > "$NGINX_CONF" <<'EOF'
# ══════════════════════════════════════════════════════════════════
# W-MAIL-001 — SnappyMail WebUI
# Domain: mail.windisites.de
# Architecture: Dedicated subdomain (Guardian Opção C corrigida)
# ══════════════════════════════════════════════════════════════════

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name mail.windisites.de;

    # ── TLS (Let's Encrypt) ──────────────────────────────────────
    ssl_certificate     /etc/letsencrypt/live/mail.windisites.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mail.windisites.de/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # ── Security headers ─────────────────────────────────────────
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options SAMEORIGIN always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;
    add_header X-WINDI-Service "w-mail-001-webui" always;

    # ── Logging ──────────────────────────────────────────────────
    access_log /var/log/nginx/mail_windisites_access.log;
    error_log  /var/log/nginx/mail_windisites_error.log warn;

    # ── Upload limit (email attachments) ─────────────────────────
    client_max_body_size 50m;

    # ── SnappyMail WebUI (port 8200) ─────────────────────────────
    location / {
        proxy_pass http://127.0.0.1:8200/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    # ── Health check ─────────────────────────────────────────────
    location = /health {
        default_type application/json;
        return 200 '{"service":"w-mail-001-webui","domain":"mail.windisites.de","status":"operational"}';
    }
}

# HTTP → HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name mail.windisites.de;

    location / {
        return 301 https://$host$request_uri;
    }
}
EOF

echo "✅ Server block created: $NGINX_CONF"

# Test nginx config
echo ""
echo "Testing nginx configuration..."
nginx -t

if [ $? -ne 0 ]; then
  echo "❌ nginx config invalid"
  rm "$NGINX_CONF"
  exit 1
fi

echo "✅ nginx config valid"

# Reload nginx
echo ""
echo "Reloading nginx..."
systemctl reload nginx
echo "✅ nginx reloaded"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ W-MAIL-001 SnappyMail WebUI LIVE"
echo ""
echo "Access:"
echo "  URL: https://mail.windisites.de/"
echo ""
echo "Credentials:"
echo "  Email: postmaster@windisites.de"
echo "  Password: $(cat /opt/windi/w-mail-001/config/.admin-password 2>/dev/null || echo 'IXEaCYZmpFLnS+yCTfngFqskOIsse1e0SqBhbt+n35M=')"
echo ""
echo "Architecture:"
echo "  HELO/PTR:  mail.windisites.de (Postfix)"
echo "  Webmail:   mail.windisites.de (SnappyMail)"
echo "  Factory:   windisites.de (W-SITES-001)"
echo "  Authority: windi-domain.com (Core Corporate)"
echo ""
echo "Coherence: ✅ Unified mail identity under mail.windisites.de"
echo "═══════════════════════════════════════════════════════════════"
