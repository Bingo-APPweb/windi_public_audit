#!/bin/bash
# ══════════════════════════════════════════════════════════════
# WINDI Governance API — Nginx Route Fix
# Bloco A1.5: Abrir artérias HTTPS para Core Constitucional
# Date: 2026-02-15
# Three Dragons Protocol: Guardian prescribes, Human decides
# ══════════════════════════════════════════════════════════════

set -e  # Abort on any error

NGINX_CONF="/etc/nginx/sites-enabled/admin.windia4desk.tech"
BACKUP_DIR="/opt/windi/backups/pre_$(date +%Y%m%d_%H%M%S)"

echo "🐉 WINDI Governance Nginx Fix — Starting"
echo "═══════════════════════════════════════════"

# ── STEP 1: Pre-flight checks ───────────────────────────────
echo ""
echo "▸ Step 1: Pre-flight checks"

echo "  Checking Governance API on :8080..."
GOV_HEALTH=$(curl -s http://localhost:8080/api/health 2>/dev/null)
if echo "$GOV_HEALTH" | grep -q '"status"'; then
    echo "  ✅ Governance API alive on :8080"
    echo "  $GOV_HEALTH"
else
    echo "  ❌ Governance API NOT responding on :8080!"
    echo "  Run: sudo systemctl status windi-governance"
    exit 1
fi

echo ""
echo "  Checking nginx is running..."
if sudo nginx -t 2>&1 | grep -q "successful"; then
    echo "  ✅ Nginx config currently valid"
else
    echo "  ❌ Nginx config already has errors! Fix those first."
    sudo nginx -t
    exit 1
fi

# ── STEP 2: Backup ──────────────────────────────────────────
echo ""
echo "▸ Step 2: Backup current config"
mkdir -p "$BACKUP_DIR"
sudo cp "$NGINX_CONF" "$BACKUP_DIR/nginx_admin.conf"
echo "  ✅ Backup saved: $BACKUP_DIR/nginx_admin.conf"

# ── STEP 3: Check if governance location already exists ─────
echo ""
echo "▸ Step 3: Checking for existing governance location..."
if grep -q "location /governance/" "$NGINX_CONF"; then
    echo "  ⚠️  A /governance/ location already exists!"
    grep -n "governance" "$NGINX_CONF"
    echo "  Review manually before proceeding."
    exit 1
fi
echo "  ✅ No existing governance block — safe to add"

# ── STEP 4: Find injection point ────────────────────────────
echo ""
echo "▸ Step 4: Finding injection point..."

# We need to inject BEFORE 'listen 443 ssl' and OUTSIDE any other location block
SSL_LINE=$(grep -n "listen 443 ssl" "$NGINX_CONF" | head -1 | cut -d: -f1)

if [ -z "$SSL_LINE" ]; then
    echo "  ❌ Could not find 'listen 443 ssl' in config!"
    exit 1
fi

# Insert 2 lines before SSL directive
INJECT_LINE=$((SSL_LINE - 2))
echo "  ✅ SSL at line $SSL_LINE, will inject at line $INJECT_LINE"

# ── STEP 5: Inject governance location block ─────────────────
echo ""
echo "▸ Step 5: Injecting governance location block..."

# Using heredoc with sed for clean injection
GOVERNANCE_BLOCK='    # ── GOVERNANCE API (:8080) ── Three Dragons Core ──────\
    location /governance/ {\
        proxy_pass http://127.0.0.1:8080/;\
        proxy_http_version 1.1;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        proxy_read_timeout 120s;\
        proxy_connect_timeout 10s;\
        \
        # CORS for Cockpit/A4Desk integration\
        add_header Access-Control-Allow-Origin "https://admin.windia4desk.tech" always;\
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;\
        add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;\
        if ($request_method = OPTIONS) {\
            return 204;\
        }\
    }\
    # ── END GOVERNANCE API ─────────────────────────────────\
'

sudo sed -i "${INJECT_LINE}a\\
${GOVERNANCE_BLOCK}" "$NGINX_CONF"

echo "  ✅ Governance block injected"

# ── STEP 6: Validate nginx config ────────────────────────────
echo ""
echo "▸ Step 6: Validating nginx config..."
if sudo nginx -t 2>&1; then
    echo "  ✅ Nginx config VALID"
else
    echo "  ❌ Nginx config INVALID! Rolling back..."
    sudo cp "$BACKUP_DIR/nginx_admin.conf" "$NGINX_CONF"
    echo "  ✅ Rollback complete. Original config restored."
    exit 1
fi

# ── STEP 7: Reload nginx ─────────────────────────────────────
echo ""
echo "▸ Step 7: Reloading nginx (zero-downtime)..."
sudo systemctl reload nginx
echo "  ✅ Nginx reloaded"

# ── STEP 8: Smoke test ───────────────────────────────────────
echo ""
echo "▸ Step 8: Smoke test — External endpoints"
echo ""

echo "  Testing /governance/api/health..."
RESULT=$(curl -s http://localhost/governance/api/health 2>/dev/null)
if echo "$RESULT" | grep -q '"status"'; then
    echo "  ✅ /governance/api/health → $RESULT"
else
    echo "  ⚠️  Local test: $RESULT"
    echo "  (May need to test via HTTPS externally)"
fi

echo ""
echo "  Testing /governance/api/status..."
curl -s http://localhost/governance/api/status 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "  (Test externally)"

echo ""
echo "  Testing /governance/api/compliance..."
curl -s http://localhost/governance/api/compliance 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "  (Test externally)"

echo ""
echo "  Testing /governance/api/agents/health..."
curl -s http://localhost/governance/api/agents/health 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "  (Test externally)"

# ── STEP 9: Verify root still works ──────────────────────────
echo ""
echo "▸ Step 9: Verify root (landing page) still works..."
ROOT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null)
echo "  Root / → HTTP $ROOT_STATUS"
if [ "$ROOT_STATUS" = "200" ]; then
    echo "  ✅ Landing page unaffected"
else
    echo "  ⚠️  Check landing page"
fi

# ── DONE ──────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════"
echo "🐉🔥 WINDI Governance Route — COMPLETE"
echo "═══════════════════════════════════════════"
echo ""
echo "External URLs now available:"
echo "  https://admin.windia4desk.tech/governance/api/health"
echo "  https://admin.windia4desk.tech/governance/api/status"
echo "  https://admin.windia4desk.tech/governance/api/compliance"
echo "  https://admin.windia4desk.tech/governance/api/agents/health"
echo ""
echo "Backup: $BACKUP_DIR/nginx_admin.conf"
echo ""
echo "🐉 The arteries are open. The Constitution speaks to the world."
echo "   AI processes. Human decides. WINDI guarantees."
