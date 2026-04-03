#!/bin/bash
# W-VD-CUT-001 — Add nginx route
# Liga IA+H · Kempten, Bavaria · 2026
#
# This script adds the VD-CUT route to nginx config.
# Must be run with sudo.

set -e

NGINX_CONFIG="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP_FILE="/opt/windi/backups/nginx-backup-vdcut-$(date +%Y%m%d_%H%M%S).conf"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "W-VD-CUT-001 — nginx route setup"
echo "================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run with sudo${NC}"
    exit 1
fi

# Backup current config
mkdir -p /opt/windi/backups
cp "$NGINX_CONFIG" "$BACKUP_FILE"
echo "Backup created: $BACKUP_FILE"

# Check if route already exists
if grep -q "vd-cut" "$NGINX_CONFIG"; then
    echo -e "${GREEN}VD-CUT route already exists${NC}"
    exit 0
fi

# Find location to insert (after NOMAD-BOT section)
NOMAD_LINE=$(grep -n "W-NOMAD-001" "$NGINX_CONFIG" | head -1 | cut -d: -f1)

if [ -z "$NOMAD_LINE" ]; then
    echo -e "${RED}Could not find W-NOMAD-001 section in nginx config${NC}"
    echo "Please add the route manually."
    exit 1
fi

# Create the nginx config block
VD_CUT_BLOCK='
    # ═══ W-VD-CUT-001 Video Cut Engine :8128 ═══
    location ^~ /vd-cut/ {
        proxy_pass http://127.0.0.1:8128/vd-cut/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Larger timeouts for video processing
        proxy_read_timeout 300s;
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;

        # Allow larger uploads (250MB)
        client_max_body_size 250M;
    }
'

# Insert after NOMAD-BOT section (find the closing brace after it)
# For now, output what to add manually
echo ""
echo "Add the following block to $NGINX_CONFIG"
echo "(after the W-NOMAD-001 section):"
echo ""
echo "$VD_CUT_BLOCK"
echo ""
echo "Then run:"
echo "  sudo nginx -t && sudo systemctl reload nginx"
echo ""

# Save to file for easy copy
echo "$VD_CUT_BLOCK" > /opt/windi/vd-cut/scripts/nginx-vdcut-block.conf
echo "Config block saved to: /opt/windi/vd-cut/scripts/nginx-vdcut-block.conf"
