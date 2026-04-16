#!/bin/bash
# Patch nginx for W-SOCIAL-001

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/home/windi/nginx-backup-social-$(date +%Y%m%d_%H%M%S).conf"

# Backup
cp "$NGINX_CONF" "$BACKUP"
echo "Backup: $BACKUP"

# Find insertion point after W-LAB-001 END
LINE=$(grep -n "END W-LAB-001" "$NGINX_CONF" | head -1 | cut -d: -f1)

if [ -z "$LINE" ]; then
    echo "ERROR: Could not find W-LAB-001 END marker"
    exit 1
fi

echo "Inserting after line $LINE"

# Create the social block
SOCIAL_BLOCK='
    # ── W-SOCIAL-001: Verified Professional Presence Infrastructure ──────────────
    location /social/ {
        proxy_pass http://127.0.0.1:8133/social/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    # ── END W-SOCIAL-001 ──────────────────────────────────────────────────────────'

# Insert after the line
head -n "$LINE" "$NGINX_CONF" > /tmp/nginx_new.conf
echo "$SOCIAL_BLOCK" >> /tmp/nginx_new.conf
tail -n +"$((LINE + 1))" "$NGINX_CONF" >> /tmp/nginx_new.conf

# Test
nginx -t -c /tmp/nginx_new.conf 2>/dev/null
if [ $? -eq 0 ]; then
    cp /tmp/nginx_new.conf "$NGINX_CONF"
    nginx -t && systemctl reload nginx
    echo "SUCCESS: W-SOCIAL-001 route added"
else
    echo "ERROR: nginx config test failed"
    cat /tmp/nginx_new.conf | grep -A5 "W-SOCIAL-001"
fi
