#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# WINDI Registration Pipeline — Deployment Script
# ═══════════════════════════════════════════════════════════════════════════════
# Run on Strato server as user 'windi':
#   chmod +x deploy_registration.sh
#   ./deploy_registration.sh
#
# This script:
#   1. Backs up current ID Genesis
#   2. Deploys registration_pipeline.py
#   3. Discovers and patches ID Genesis main app
#   4. Adds nginx /clone/verify route
#   5. Restarts services
#   6. Runs smoke tests
# ═══════════════════════════════════════════════════════════════════════════════

set -e  # Exit on error

GOLD='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'
BOLD='\033[1m'

echo -e "${GOLD}═══════════════════════════════════════════════════${NC}"
echo -e "${GOLD}  WINDI Registration Pipeline — Deploy${NC}"
echo -e "${GOLD}  KI verarbeitet. Mensch entscheidet. WINDI garantiert.${NC}"
echo -e "${GOLD}═══════════════════════════════════════════════════${NC}"
echo ""

# ─── Phase 0: Pre-flight checks ──────────────────────────────
echo -e "${BOLD}[Phase 0] Pre-flight checks${NC}"

# Find ID Genesis directory
ID_GENESIS_DIR=""
for dir in /opt/windi/id-genesis /opt/windi/id_genesis /opt/windi/idgenesis; do
    if [ -d "$dir" ]; then
        ID_GENESIS_DIR="$dir"
        break
    fi
done

# Search for the process if directory not found
if [ -z "$ID_GENESIS_DIR" ]; then
    echo "  Searching for ID Genesis process on port 8096..."
    GENESIS_PID=$(ss -tlnp | grep ':8096' | grep -oP 'pid=\K[0-9]+' | head -1)
    if [ -n "$GENESIS_PID" ]; then
        GENESIS_CMD=$(ps -p $GENESIS_PID -o args= 2>/dev/null)
        echo "  Found process: $GENESIS_CMD"
        # Extract directory from command
        GENESIS_SCRIPT=$(echo "$GENESIS_CMD" | grep -oP '/opt/windi/\S+\.py' | head -1)
        if [ -n "$GENESIS_SCRIPT" ]; then
            ID_GENESIS_DIR=$(dirname "$GENESIS_SCRIPT")
        fi
    fi
fi

if [ -z "$ID_GENESIS_DIR" ]; then
    echo -e "  ${RED}ID Genesis directory not found. Checking common locations...${NC}"
    # List all Python files that might be ID Genesis
    echo "  Files with 'genesis' or 'lead' in name:"
    find /opt/windi -name '*genesis*' -o -name '*lead*' -o -name '*idgen*' 2>/dev/null | grep -v backups | grep -v __pycache__ | head -10
    echo ""
    echo "  Process on port 8096:"
    ss -tlnp | grep ':8096' || echo "  Nothing on 8096"
    echo ""
    echo "  Enter ID Genesis directory path (or 'new' to create fresh):"
    read -r ID_GENESIS_DIR
    if [ "$ID_GENESIS_DIR" = "new" ]; then
        ID_GENESIS_DIR="/opt/windi/id-genesis"
        mkdir -p "$ID_GENESIS_DIR"
        echo -e "  ${GREEN}Created $ID_GENESIS_DIR${NC}"
    fi
fi

echo -e "  ${GREEN}ID Genesis dir: $ID_GENESIS_DIR${NC}"

# Check SMTP config
if [ -f "$ID_GENESIS_DIR/.env" ]; then
    source "$ID_GENESIS_DIR/.env" 2>/dev/null
fi
if [ -f "/etc/windi/secrets.env" ]; then
    source /etc/windi/secrets.env 2>/dev/null
fi

echo ""

# ─── Phase 1: Backup ─────────────────────────────────────────
echo -e "${BOLD}[Phase 1] Backup${NC}"
BK="/opt/windi/backups/pre_reg_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BK"

if [ -d "$ID_GENESIS_DIR" ]; then
    cp -r "$ID_GENESIS_DIR"/*.py "$BK/" 2>/dev/null || true
    cp "$ID_GENESIS_DIR/.env" "$BK/" 2>/dev/null || true
fi
sudo cp /etc/nginx/sites-enabled/admin.windia4desk.tech "$BK/nginx.conf" 2>/dev/null || true
echo -e "  ${GREEN}Backup: $BK${NC}"

# ─── Phase 2: Deploy registration_pipeline.py ─────────────────
echo -e "${BOLD}[Phase 2] Deploy registration_pipeline.py${NC}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/registration_pipeline.py" ]; then
    cp "$SCRIPT_DIR/registration_pipeline.py" "$ID_GENESIS_DIR/"
    echo -e "  ${GREEN}Copied registration_pipeline.py${NC}"
else
    echo -e "  ${RED}registration_pipeline.py not found in $SCRIPT_DIR${NC}"
    echo "  Please place it alongside this script and re-run."
    exit 1
fi

# Ensure directories exist
mkdir -p /opt/windi/data
mkdir -p /opt/windi/logs

# ─── Phase 3: Create/update .env ──────────────────────────────
echo -e "${BOLD}[Phase 3] Configure .env${NC}"

ENV_FILE="$ID_GENESIS_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "  Creating new .env..."
    cat > "$ENV_FILE" << 'ENVEOF'
# WINDI ID Genesis + Registration Pipeline
# ─────────────────────────────────────────

# SMTP — Strato
SMTP_HOST=smtp.strato.de
SMTP_PORT=465
SMTP_USER=info@a4desk.de
SMTP_PASS=DEINE_STRATO_PASSWORT_HIER
SMTP_FROM_NAME=a4Desk by WINDI
SMTP_FROM_EMAIL=noreply@a4desk.de

# Registration
BASE_URL=https://admin.windia4desk.tech
REG_DB_PATH=/opt/windi/data/windi_registration.db

# Service
PORT=8096
ENVEOF
    chmod 600 "$ENV_FILE"
    echo -e "  ${GOLD}⚠ .env created — EDIT SMTP_PASS before starting!${NC}"
    echo -e "  ${GOLD}  nano $ENV_FILE${NC}"
else
    # Check if SMTP vars exist, add if missing
    if ! grep -q "SMTP_HOST" "$ENV_FILE"; then
        echo "" >> "$ENV_FILE"
        echo "# SMTP — Strato (added by registration pipeline)" >> "$ENV_FILE"
        echo "SMTP_HOST=smtp.strato.de" >> "$ENV_FILE"
        echo "SMTP_PORT=465" >> "$ENV_FILE"
        echo "SMTP_USER=info@a4desk.de" >> "$ENV_FILE"
        echo "SMTP_PASS=DEINE_STRATO_PASSWORT_HIER" >> "$ENV_FILE"
        echo "SMTP_FROM_NAME=a4Desk by WINDI" >> "$ENV_FILE"
        echo "SMTP_FROM_EMAIL=noreply@a4desk.de" >> "$ENV_FILE"
        echo "BASE_URL=https://admin.windia4desk.tech" >> "$ENV_FILE"
        echo "REG_DB_PATH=/opt/windi/data/windi_registration.db" >> "$ENV_FILE"
        echo -e "  ${GOLD}⚠ SMTP vars added to .env — EDIT SMTP_PASS!${NC}"
    else
        echo -e "  ${GREEN}SMTP config already in .env${NC}"
    fi
fi

# ─── Phase 4: Discover and patch ID Genesis main app ──────────
echo -e "${BOLD}[Phase 4] Integrate with ID Genesis${NC}"

# Find the main FastAPI app file
MAIN_APP=""
for f in "$ID_GENESIS_DIR"/main.py "$ID_GENESIS_DIR"/app.py "$ID_GENESIS_DIR"/server.py "$ID_GENESIS_DIR"/id_genesis.py "$ID_GENESIS_DIR"/idgenesis.py; do
    if [ -f "$f" ]; then
        MAIN_APP="$f"
        break
    fi
done

if [ -z "$MAIN_APP" ]; then
    # Search for FastAPI app in any .py file
    MAIN_APP=$(grep -rl "FastAPI\|app = " "$ID_GENESIS_DIR"/*.py 2>/dev/null | grep -v registration_pipeline | head -1)
fi

if [ -n "$MAIN_APP" ] && [ -f "$MAIN_APP" ]; then
    echo "  Found main app: $MAIN_APP"
    
    # Check if already integrated
    if grep -q "registration_pipeline" "$MAIN_APP"; then
        echo -e "  ${GREEN}Already integrated!${NC}"
    else
        echo "  Patching to include registration_pipeline router..."
        
        # Find the import section and add our import
        # Strategy: add import after the last 'from' or 'import' line
        LAST_IMPORT_LINE=$(grep -n "^from \|^import " "$MAIN_APP" | tail -1 | cut -d: -f1)
        
        if [ -n "$LAST_IMPORT_LINE" ]; then
            sed -i "${LAST_IMPORT_LINE}a\\
# ── Registration Pipeline (WINDI Email + WALLET) ──\\
try:\\
    from registration_pipeline import router as reg_router\\
    _REG_AVAILABLE = True\\
except ImportError:\\
    _REG_AVAILABLE = False" "$MAIN_APP"
            
            # Find where routers are included or app is created
            # Look for app.include_router or app = FastAPI
            APP_LINE=$(grep -n "app.include_router\|app = FastAPI\|app=FastAPI" "$MAIN_APP" | tail -1 | cut -d: -f1)
            
            if [ -n "$APP_LINE" ]; then
                sed -i "${APP_LINE}a\\
\\
# ── Registration Pipeline Router ──\\
if _REG_AVAILABLE:\\
    app.include_router(reg_router)\\
    print('[ID Genesis] Registration Pipeline loaded')" "$MAIN_APP"
            fi
            
            echo -e "  ${GREEN}Patched $MAIN_APP${NC}"
        else
            echo -e "  ${RED}Could not find import section. Manual integration needed.${NC}"
            echo "  Add these lines to $MAIN_APP:"
            echo "    from registration_pipeline import router as reg_router"
            echo "    app.include_router(reg_router)"
        fi
    fi
else
    echo -e "  ${GOLD}No main app found — creating standalone launcher${NC}"
    
    cat > "$ID_GENESIS_DIR/main.py" << 'APPEOF'
#!/usr/bin/env python3
"""
WINDI ID Genesis + Registration Pipeline
Port: 8096
"""
import os
from dotenv import load_dotenv

# Load .env
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="WINDI ID Genesis",
    version="1.0.0",
    description="Lead capture, email verification, and WALLET creation"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://admin.windia4desk.tech", "https://master.windia4desk.tech"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Registration Pipeline Router ──
from registration_pipeline import router as reg_router
app.include_router(reg_router)

@app.get("/health")
async def health():
    return {
        "service": "WINDI ID Genesis + Registration Pipeline",
        "version": "1.0.0",
        "status": "healthy",
        "smtp_configured": bool(os.environ.get("SMTP_PASS", "")),
        "principle": "KI verarbeitet. Mensch entscheidet. WINDI garantiert."
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8096"))
    uvicorn.run(app, host="0.0.0.0", port=port)
APPEOF
    echo -e "  ${GREEN}Created standalone main.py${NC}"
fi

# ─── Phase 5: Nginx — Add /clone/verify route ────────────────
echo -e "${BOLD}[Phase 5] Nginx — Add /clone/verify route${NC}"

NGINX_CONF="/etc/nginx/sites-enabled/admin.windia4desk.tech"

if sudo grep -q "clone/verify" "$NGINX_CONF"; then
    echo -e "  ${GREEN}/clone/verify route already exists${NC}"
else
    echo "  Adding /clone/verify route..."
    
    # Find the line with "listen 443 ssl" to insert before it
    SSL_LINE=$(grep -n "listen 443 ssl" "$NGINX_CONF" | head -1 | cut -d: -f1)
    
    if [ -n "$SSL_LINE" ]; then
        # Insert 2 lines before SSL directive
        INSERT_LINE=$((SSL_LINE - 1))
        
        sudo sed -i "${INSERT_LINE}i\\
\\
    # ── Registration Pipeline: Email Verification (8096) ──\\
    location = /clone/verify {\\
        proxy_pass http://127.0.0.1:8096/api/verify;\\
        proxy_http_version 1.1;\\
        proxy_set_header Host \$host;\\
        proxy_set_header X-Real-IP \$remote_addr;\\
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\\
        proxy_set_header X-Forwarded-Proto \$scheme;\\
    }\\
\\
    # ── Registration Stats & Wallets (8096) ──\\
    location /clone/api/leads/ {\\
        proxy_pass http://127.0.0.1:8096/api/leads/;\\
        proxy_http_version 1.1;\\
        proxy_set_header Host \$host;\\
        proxy_set_header X-Real-IP \$remote_addr;\\
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\\
        proxy_set_header X-Forwarded-Proto \$scheme;\\
    }\\
\\
    location /clone/api/wallets {\\
        proxy_pass http://127.0.0.1:8096/api/wallets;\\
        proxy_http_version 1.1;\\
        proxy_set_header Host \$host;\\
        proxy_set_header X-Real-IP \$remote_addr;\\
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\\
        proxy_set_header X-Forwarded-Proto \$scheme;\\
    }\\
\\
    location /clone/api/wallet/ {\\
        proxy_pass http://127.0.0.1:8096/api/wallet/;\\
        proxy_http_version 1.1;\\
        proxy_set_header Host \$host;\\
        proxy_set_header X-Real-IP \$remote_addr;\\
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\\
        proxy_set_header X-Forwarded-Proto \$scheme;\\
    }" "$NGINX_CONF"
        
        echo -e "  ${GREEN}Nginx routes added${NC}"
    else
        echo -e "  ${RED}Could not find SSL line in nginx config${NC}"
        echo "  Manual addition needed."
    fi
    
    # Test nginx
    echo "  Testing nginx config..."
    if sudo nginx -t 2>&1; then
        echo -e "  ${GREEN}nginx config OK${NC}"
        sudo systemctl reload nginx
        echo -e "  ${GREEN}nginx reloaded${NC}"
    else
        echo -e "  ${RED}nginx config ERROR — restoring backup${NC}"
        sudo cp "$BK/nginx.conf" "$NGINX_CONF"
        sudo nginx -t && sudo systemctl reload nginx
        echo "  Backup restored."
    fi
fi

# ─── Phase 6: Install dependencies ───────────────────────────
echo -e "${BOLD}[Phase 6] Dependencies${NC}"

# Check for python-dotenv (needed for .env loading)
python3 -c "import dotenv" 2>/dev/null || {
    echo "  Installing python-dotenv..."
    pip3 install python-dotenv --break-system-packages -q
}

# Check for pydantic (needed for FastAPI models) 
python3 -c "import pydantic" 2>/dev/null || {
    echo "  Installing pydantic..."
    pip3 install pydantic --break-system-packages -q
}

echo -e "  ${GREEN}Dependencies OK${NC}"

# ─── Phase 7: Restart ID Genesis ─────────────────────────────
echo -e "${BOLD}[Phase 7] Restart ID Genesis${NC}"

# Check if systemd service exists
if systemctl list-unit-files | grep -q "windi-idgenesis\|windi-id-genesis"; then
    SERVICE_NAME=$(systemctl list-unit-files | grep -oP 'windi-id.?genesis\S*' | head -1)
    echo "  Restarting systemd: $SERVICE_NAME"
    sudo systemctl restart "$SERVICE_NAME"
else
    # Check for nohup process
    GENESIS_PID=$(ss -tlnp | grep ':8096' | grep -oP 'pid=\K[0-9]+' | head -1)
    if [ -n "$GENESIS_PID" ]; then
        echo "  Stopping nohup process (PID: $GENESIS_PID)..."
        kill "$GENESIS_PID" 2>/dev/null
        sleep 2
    fi
    
    echo "  Starting ID Genesis with registration pipeline..."
    cd "$ID_GENESIS_DIR"
    
    # Source .env for the process
    set -a
    source .env 2>/dev/null
    set +a
    
    nohup python3 main.py > /opt/windi/logs/id-genesis.log 2>&1 &
    echo "  PID: $!"
    sleep 3
    
    # Verify it started
    if ss -tlnp | grep -q ':8096'; then
        echo -e "  ${GREEN}ID Genesis running on :8096${NC}"
    else
        echo -e "  ${RED}Failed to start! Check logs:${NC}"
        echo "  tail -20 /opt/windi/logs/id-genesis.log"
        tail -10 /opt/windi/logs/id-genesis.log 2>/dev/null
    fi
fi

# ─── Phase 8: Smoke Tests ────────────────────────────────────
echo -e "${BOLD}[Phase 8] Smoke Tests${NC}"
echo ""

sleep 2

# Test 1: Health
echo -n "  [1] Health (/health).................. "
HEALTH=$(curl -s http://localhost:8096/health 2>/dev/null)
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
    echo "      $HEALTH"
fi

# Test 2: Lead capture
echo -n "  [2] Lead capture (POST /api/leads).... "
LEAD=$(curl -s -X POST http://localhost:8096/api/leads \
    -H "Content-Type: application/json" \
    -d '{"name":"Deploy Test","email":"deploy-test@example.com","company":"","interest":"test","lang":"de"}' 2>/dev/null)
if echo "$LEAD" | grep -q "lead_id"; then
    LEAD_ID=$(echo "$LEAD" | python3 -c "import sys,json; print(json.load(sys.stdin).get('lead_id',''))" 2>/dev/null)
    VSENT=$(echo "$LEAD" | python3 -c "import sys,json; print(json.load(sys.stdin).get('verification_sent','N/A'))" 2>/dev/null)
    echo -e "${GREEN}✅${NC} ($LEAD_ID, smtp=$VSENT)"
else
    echo -e "${RED}❌${NC}"
    echo "      $LEAD"
fi

# Test 3: Verify endpoint
echo -n "  [3] Verify endpoint (GET /api/verify). "
VERIFY=$(curl -so /dev/null -w "%{http_code}" "http://localhost:8096/api/verify?token=test_invalid" 2>/dev/null)
if [ "$VERIFY" = "200" ]; then
    echo -e "${GREEN}✅${NC} (returns HTML error page as expected)"
else
    echo -e "${RED}❌${NC} (HTTP $VERIFY)"
fi

# Test 4: Stats
echo -n "  [4] Stats (/api/leads/stats).......... "
STATS=$(curl -s "http://localhost:8096/api/leads/stats" 2>/dev/null)
if echo "$STATS" | grep -q "total_leads"; then
    TOTAL=$(echo "$STATS" | python3 -c "import sys,json; print(json.load(sys.stdin).get('stats',{}).get('total_leads',0))" 2>/dev/null)
    echo -e "${GREEN}✅${NC} ($TOTAL leads)"
else
    echo -e "${RED}❌${NC}"
fi

# Test 5: Wallets
echo -n "  [5] Wallets (/api/wallets)............ "
WALLETS=$(curl -so /dev/null -w "%{http_code}" "http://localhost:8096/api/wallets" 2>/dev/null)
if [ "$WALLETS" = "200" ]; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC} (HTTP $WALLETS)"
fi

# Test 6: Nginx routing
echo -n "  [6] Nginx /clone/leads (HTTPS)........ "
NGINX_LEAD=$(curl -so /dev/null -w "%{http_code}" -X POST "https://admin.windia4desk.tech/clone/leads" \
    -H "Content-Type: application/json" \
    -d '{"name":"Nginx Test","email":"nginx@test.de"}' 2>/dev/null)
if [ "$NGINX_LEAD" = "200" ]; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC} (HTTP $NGINX_LEAD)"
fi

echo -n "  [7] Nginx /clone/verify (HTTPS)....... "
NGINX_VERIFY=$(curl -so /dev/null -w "%{http_code}" "https://admin.windia4desk.tech/clone/verify?token=test" 2>/dev/null)
if [ "$NGINX_VERIFY" = "200" ]; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC} (HTTP $NGINX_VERIFY)"
fi

echo ""

# ─── Summary ─────────────────────────────────────────────────
echo -e "${GOLD}═══════════════════════════════════════════════════${NC}"
echo -e "${GOLD}  DEPLOYMENT COMPLETE${NC}"
echo -e "${GOLD}═══════════════════════════════════════════════════${NC}"
echo ""
echo "  Files deployed:"
echo "    $ID_GENESIS_DIR/registration_pipeline.py"
echo "    $ID_GENESIS_DIR/main.py (if created)"
echo "    $ID_GENESIS_DIR/.env"
echo ""
echo "  Nginx routes:"
echo "    /clone/leads      → 8096/api/leads      (POST: lead capture + SMTP)"
echo "    /clone/verify     → 8096/api/verify      (GET:  email verification)"
echo "    /clone/api/leads/ → 8096/api/leads/      (GET:  stats)"
echo "    /clone/api/wallets→ 8096/api/wallets     (GET:  wallet list)"
echo ""
echo "  Database:"
echo "    /opt/windi/data/windi_registration.db"
echo ""
echo "  Logs:"
echo "    /opt/windi/logs/id-genesis.log"
echo "    /opt/windi/logs/registration.log"
echo ""
echo "  Backup:"
echo "    $BK"
echo ""

# Check SMTP
if grep -q "DEINE_STRATO_PASSWORT" "$ENV_FILE" 2>/dev/null; then
    echo -e "  ${GOLD}⚠  ATENÇÃO: SMTP_PASS ainda não configurado!${NC}"
    echo -e "  ${GOLD}   Edite: nano $ENV_FILE${NC}"
    echo -e "  ${GOLD}   Troque DEINE_STRATO_PASSWORT_HIER pela senha real${NC}"
    echo -e "  ${GOLD}   Depois reinicie: kill \$(pgrep -f 'main.py.*8096') && cd $ID_GENESIS_DIR && nohup python3 main.py > /opt/windi/logs/id-genesis.log 2>&1 &${NC}"
    echo ""
fi

echo -e "  ${BOLD}Flow completo:${NC}"
echo "    Landing 'Jetzt starten' → POST /clone/leads"
echo "    → Captura lead + Envia email verificação"
echo "    → Usuário clica link no email"
echo "    → GET /clone/verify?token=xxx"
echo "    → WALLET criado (WDI-H ou WDI-C)"
echo "    → Welcome email com WALLET-ID"
echo "    → Acesso ao a4Desk Desktop"
echo ""
echo -e "${GREEN}  🐉 O organismo agora tem voz. 🐉${NC}"
