#!/bin/bash
# ══════════════════════════════════════════════════════════════
# WINDI Governance Nginx Fix — MÉTODO MANUAL SEGURO
# Se o script automático falhar, use este passo a passo.
# ══════════════════════════════════════════════════════════════

echo "🐉 Método Manual — Governance Nginx Route Fix"
echo ""

# Step 1: Pre-flight
echo "═══ STEP 1: Pre-flight ═══"
echo "Governance API alive?"
curl -s http://localhost:8080/api/health | python3 -m json.tool
echo ""

# Step 2: Backup
echo "═══ STEP 2: Backup ═══"
BK="/opt/windi/backups/pre_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BK
sudo cp /etc/nginx/sites-enabled/admin.windia4desk.tech $BK/nginx.conf
echo "Backup: $BK/nginx.conf"
echo ""

# Step 3: Show where to inject
echo "═══ STEP 3: Find injection point ═══"
echo "Look for 'listen 443 ssl' — your block goes BEFORE it:"
grep -n "listen 443 ssl\|location " /etc/nginx/sites-enabled/admin.windia4desk.tech
echo ""

# Step 4: Open editor
echo "═══ STEP 4: Edit nginx config ═══"
echo "Run:"
echo "  sudo nano /etc/nginx/sites-enabled/admin.windia4desk.tech"
echo ""
echo "Paste THIS block BEFORE the 'listen 443 ssl' line,"
echo "OUTSIDE any existing location block:"
echo ""
cat << 'SNIPPET'
    # ── GOVERNANCE API (:8080) ── Three Dragons Core ──────
    location /governance/ {
        proxy_pass http://127.0.0.1:8080/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;

        # CORS for Cockpit/A4Desk integration
        add_header Access-Control-Allow-Origin "https://admin.windia4desk.tech" always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
        if ($request_method = OPTIONS) {
            return 204;
        }
    }
    # ── END GOVERNANCE API ─────────────────────────────────
SNIPPET
echo ""

# Step 5: Test & reload
echo "═══ STEP 5: Test & Reload ═══"
echo "Run:"
echo "  sudo nginx -t"
echo "  sudo systemctl reload nginx"
echo ""

# Step 6: Smoke test
echo "═══ STEP 6: Smoke Test ═══"
echo "Run:"
echo "  curl -s https://admin.windia4desk.tech/governance/api/health | python3 -m json.tool"
echo "  curl -s https://admin.windia4desk.tech/governance/api/status | python3 -m json.tool"
echo "  curl -s https://admin.windia4desk.tech/governance/api/compliance | python3 -m json.tool"
echo "  curl -s https://admin.windia4desk.tech/governance/api/agents/health | python3 -m json.tool"
