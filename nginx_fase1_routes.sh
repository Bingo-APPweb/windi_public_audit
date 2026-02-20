#!/bin/bash
# ══════════════════════════════════════════════════════════════
# 🐉 WINDI FASE 1 — Nginx Route Injection (Governance + BABEL)
# Date: 15 Feb 2026
# Purpose: Add missing /governance/ and /babel/ routes to nginx
# ══════════════════════════════════════════════════════════════

set -e  # Exit on any error

NGINX_CONF="/etc/nginx/sites-enabled/admin.windia4desk.tech"
BACKUP_DIR="/opt/windi/backups/pre_$(date +%Y%m%d_%H%M%S)"

echo "╔══════════════════════════════════════════════╗"
echo "║  🐉 FASE 1: Nginx Route Injection            ║"
echo "╚══════════════════════════════════════════════╝"

# ── STEP 1: Backup ──────────────────────────────────────────
echo ""
echo "📦 Step 1: Creating backup..."
mkdir -p "$BACKUP_DIR"
sudo cp "$NGINX_CONF" "$BACKUP_DIR/nginx.conf.bak"
echo "   ✅ Backup saved to: $BACKUP_DIR/nginx.conf.bak"

# ── STEP 2: Find injection point ────────────────────────────
echo ""
echo "🔍 Step 2: Finding injection point..."
SSL_LINE=$(grep -n "listen 443 ssl" "$NGINX_CONF" | head -1 | cut -d: -f1)
echo "   SSL directive found at line: $SSL_LINE"

if [ -z "$SSL_LINE" ]; then
    echo "   ❌ FATAL: Could not find 'listen 443 ssl' in config!"
    echo "   Aborting. Config unchanged."
    exit 1
fi

# Inject BEFORE the SSL line (2 lines above to be safe)
INJECT_LINE=$((SSL_LINE - 2))
echo "   Will inject at line: $INJECT_LINE"

# ── STEP 3: Check if routes already exist ────────────────────
echo ""
echo "🔍 Step 3: Checking for existing routes..."
if grep -q "location /governance/" "$NGINX_CONF"; then
    echo "   ⚠️  /governance/ route already exists! Skipping."
    GOV_EXISTS=true
else
    echo "   ℹ️  /governance/ route NOT found — will add."
    GOV_EXISTS=false
fi

if grep -q "location /babel/" "$NGINX_CONF"; then
    echo "   ⚠️  /babel/ route already exists! Skipping."
    BABEL_EXISTS=true
else
    echo "   ℹ️  /babel/ route NOT found — will add."
    BABEL_EXISTS=false
fi

# ── STEP 4: Inject Governance route ─────────────────────────
if [ "$GOV_EXISTS" = false ]; then
    echo ""
    echo "🔧 Step 4a: Injecting Governance API route (:8080)..."
    sudo sed -i "${INJECT_LINE}a\\
\\
    # ── GOVERNANCE API (:8080) ────────────────────────────\\
    location /governance/ {\\
        proxy_pass http://127.0.0.1:8080/;\\
        proxy_http_version 1.1;\\
        proxy_set_header Host \$host;\\
        proxy_set_header X-Real-IP \$remote_addr;\\
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\\
        proxy_set_header X-Forwarded-Proto \$scheme;\\
        proxy_read_timeout 120s;\\
        proxy_connect_timeout 10s;\\
        add_header Access-Control-Allow-Origin \"https://admin.windia4desk.tech\" always;\\
        add_header Access-Control-Allow-Methods \"GET, POST, OPTIONS\" always;\\
        add_header Access-Control-Allow-Headers \"Content-Type, Authorization\" always;\\
        if (\$request_method = OPTIONS) {\\
            return 204;\\
        }\\
    }\\
    # ── END GOVERNANCE API ────────────────────────────────" "$NGINX_CONF"
    echo "   ✅ Governance route injected."
fi

# ── STEP 5: Inject BABEL route ──────────────────────────────
# Re-find SSL line (it shifted after governance injection)
SSL_LINE=$(grep -n "listen 443 ssl" "$NGINX_CONF" | head -1 | cut -d: -f1)
INJECT_LINE=$((SSL_LINE - 2))

if [ "$BABEL_EXISTS" = false ]; then
    echo ""
    echo "🔧 Step 4b: Injecting BABEL Editor route (:8085)..."
    sudo sed -i "${INJECT_LINE}a\\
\\
    # ── BABEL EDITOR / HUB (:8085) ───────────────────────\\
    location /babel/ {\\
        proxy_pass http://127.0.0.1:8085/;\\
        proxy_http_version 1.1;\\
        proxy_set_header Host \$host;\\
        proxy_set_header X-Real-IP \$remote_addr;\\
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\\
        proxy_set_header X-Forwarded-Proto \$scheme;\\
        proxy_read_timeout 120s;\\
        proxy_connect_timeout 10s;\\
        add_header Access-Control-Allow-Origin \"https://admin.windia4desk.tech\" always;\\
        add_header Access-Control-Allow-Methods \"GET, POST, OPTIONS\" always;\\
        add_header Access-Control-Allow-Headers \"Content-Type, Authorization\" always;\\
        if (\$request_method = OPTIONS) {\\
            return 204;\\
        }\\
    }\\
    # ── END BABEL EDITOR ─────────────────────────────────" "$NGINX_CONF"
    echo "   ✅ BABEL route injected."
fi

# ── STEP 5: Test nginx config ────────────────────────────────
echo ""
echo "🧪 Step 5: Testing nginx configuration..."
if sudo nginx -t 2>&1; then
    echo "   ✅ nginx config is valid!"
else
    echo "   ❌ NGINX TEST FAILED!"
    echo "   Rolling back from backup..."
    sudo cp "$BACKUP_DIR/nginx.conf.bak" "$NGINX_CONF"
    sudo nginx -t
    echo "   ✅ Rollback complete. Config restored."
    exit 1
fi

# ── STEP 6: Reload nginx ────────────────────────────────────
echo ""
echo "🔄 Step 6: Reloading nginx..."
sudo systemctl reload nginx
echo "   ✅ nginx reloaded."

# ── STEP 7: Smoke test ──────────────────────────────────────
echo ""
echo "🔥 Step 7: Smoke testing new routes..."
sleep 1

echo "   Testing /governance/health..."
GOV_RESP=$(curl -s -o /tmp/gov_test.txt -w "%{http_code}" --max-time 5 http://localhost:8080/health 2>/dev/null)
echo "   → Governance direct :8080 → HTTP $GOV_RESP"
cat /tmp/gov_test.txt 2>/dev/null | head -1
echo ""

echo "   Testing /babel/health..."
BABEL_RESP=$(curl -s -o /tmp/babel_test.txt -w "%{http_code}" --max-time 5 http://localhost:8085/health 2>/dev/null)
echo "   → BABEL direct :8085 → HTTP $BABEL_RESP"
cat /tmp/babel_test.txt 2>/dev/null | head -1
echo ""

echo "   Testing via nginx..."
GOV_NGINX=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 https://admin.windia4desk.tech/governance/health 2>/dev/null)
echo "   → /governance/health via nginx → HTTP $GOV_NGINX"

BABEL_NGINX=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 https://admin.windia4desk.tech/babel/health 2>/dev/null)
echo "   → /babel/health via nginx → HTTP $BABEL_NGINX"

# ── SUMMARY ──────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  📋 FASE 1 — SUMMARY                         ║"
echo "╠══════════════════════════════════════════════╣"
echo "║  Backup: $BACKUP_DIR"
echo "║  Governance route: $([ "$GOV_EXISTS" = true ] && echo 'ALREADY EXISTED' || echo 'ADDED')"
echo "║  BABEL route:      $([ "$BABEL_EXISTS" = true ] && echo 'ALREADY EXISTED' || echo 'ADDED')"
echo "║  nginx test:       PASSED"
echo "║  nginx reload:     DONE"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "🐉 Fase 1 complete. Dragon routes are open."
