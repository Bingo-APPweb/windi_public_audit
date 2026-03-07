#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# WINDI Distribution Engine — Deploy Script
# ═══════════════════════════════════════════════════════════════════════════════

set -e

GOLD='\033[0;33m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GOLD}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GOLD}  WINDI Distribution Engine — Deploy                           ${NC}"
echo -e "${GOLD}═══════════════════════════════════════════════════════════════${NC}"

# 1. Copy systemd service
echo -e "\n${GREEN}[1/5]${NC} Installing systemd service..."
sudo cp /opt/windi/distribution-engine/windi-distribution-engine.service /etc/systemd/system/

# 2. Add nginx route
echo -e "${GREEN}[2/5]${NC} Adding nginx route..."

# Check if route already exists
if grep -q "location /distribute/" /etc/nginx/sites-enabled/windi-domain.com; then
    echo "  → Route already exists, skipping..."
else
    # Find line number after /builder/ block closes
    LINE=$(grep -n "proxy_connect_timeout 10s;" /etc/nginx/sites-enabled/windi-domain.com | grep -A1 "builder" | tail -1 | cut -d: -f1)

    # If that doesn't work, find it another way
    if [ -z "$LINE" ]; then
        LINE=$(awk '/location \/builder\//,/^[[:space:]]*\}/' /etc/nginx/sites-enabled/windi-domain.com | wc -l)
        LINE=$((241 + LINE))
    fi

    # Insert the nginx block using sed
    sudo sed -i '/location \/builder\//,/proxy_connect_timeout 10s;/{
        /proxy_connect_timeout 10s;/a\
      }\
\
      # ── Distribution Engine (:8116) — Publishing House ────────\
      location /distribute/ {\
          proxy_pass http://127.0.0.1:8116/distribute/;\
          proxy_http_version 1.1;\
          proxy_set_header Host $host;\
          proxy_set_header X-Real-IP $remote_addr;\
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
          proxy_set_header X-Forwarded-Proto $scheme;\
          proxy_read_timeout 60s;\
          proxy_connect_timeout 10s;
    }' /etc/nginx/sites-enabled/windi-domain.com

    echo "  → Route added"
fi

# 3. Test nginx
echo -e "${GREEN}[3/5]${NC} Testing nginx configuration..."
sudo nginx -t

# 4. Reload nginx
echo -e "${GREEN}[4/5]${NC} Reloading nginx..."
sudo systemctl reload nginx

# 5. Start Distribution Engine
echo -e "${GREEN}[5/5]${NC} Starting Distribution Engine..."
sudo systemctl daemon-reload
sudo systemctl enable windi-distribution-engine
sudo systemctl restart windi-distribution-engine

# Wait and check
sleep 2
echo -e "\n${GOLD}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Status:${NC}"
sudo systemctl status windi-distribution-engine --no-pager -l | head -15

echo -e "\n${GREEN}Health Check:${NC}"
curl -s http://localhost:8116/health | python3 -m json.tool 2>/dev/null || echo "Waiting for service..."

echo -e "\n${GOLD}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Distribution Engine deployed on :8116${NC}"
echo -e "${GREEN}✓ Route: https://windi-domain.com/distribute/${NC}"
echo -e "${GOLD}═══════════════════════════════════════════════════════════════${NC}"
