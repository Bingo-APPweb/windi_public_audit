#!/bin/bash
# ============================================================================
# WINDI WALLET — Deploy Script v1.0.0
# Executar no Strato: bash /opt/windi/deploy_wallet.sh
# Three Dragons Protocol: AI processes. Human decides. WINDI guarantees.
# ============================================================================

set -e  # Parar em qualquer erro

echo "=============================================="
echo "🐉 WINDI WALLET — Deploy no Strato"
echo "=============================================="
echo ""

# ─── CORES ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
fail() { echo -e "${RED}❌ $1${NC}"; }

# ============================================================================
# FASE 1: BACKUP (sempre antes de mudar qualquer coisa)
# ============================================================================
echo "── FASE 1: Backup ──────────────────────────────"

BK="/opt/windi/backups/pre_wallet_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BK"

# Backup da Governance API (vamos modificar)
if [ -f /opt/windi/engine/windi_governance_api.py ]; then
    cp /opt/windi/engine/windi_governance_api.py "$BK/"
    ok "Governance API backed up"
else
    warn "Governance API not found at expected path"
fi

# Backup do nginx
sudo cp /etc/nginx/sites-enabled/admin.windia4desk.tech "$BK/nginx.conf" 2>/dev/null || true

echo "Backup dir: $BK"
ok "Backup complete"
echo ""

# ============================================================================
# FASE 2: DESCOMPACTAR
# ============================================================================
echo "── FASE 2: Descompactar Wallet ─────────────────"

if [ -f /opt/windi/Wallet-Bridge.zip ]; then
    # Criar diretório wallet
    mkdir -p /opt/windi/wallet

    # Descompactar
    cd /opt/windi
    unzip -o Wallet-Bridge.zip -d /opt/windi/wallet_temp/

    # Verificar estrutura (pode ter subpasta)
    if [ -d /opt/windi/wallet_temp/wallet ]; then
        cp -r /opt/windi/wallet_temp/wallet/* /opt/windi/wallet/
    elif [ -f /opt/windi/wallet_temp/wallet_provisioning.py ]; then
        cp -r /opt/windi/wallet_temp/* /opt/windi/wallet/
    else
        # Listar para diagnóstico
        echo "Conteúdo do zip:"
        find /opt/windi/wallet_temp/ -type f
        cp -r /opt/windi/wallet_temp/* /opt/windi/wallet/
    fi

    # Limpar temp
    rm -rf /opt/windi/wallet_temp
    ok "Wallet files extracted"
else
    fail "Wallet-Bridge.zip not found in /opt/windi/"
    exit 1
fi

# Verificar arquivos essenciais
echo ""
echo "Arquivos do WALLET:"
ls -la /opt/windi/wallet/*.py 2>/dev/null || warn "No .py files found"
ls -la /opt/windi/wallet/ddl/ 2>/dev/null || warn "No ddl/ directory"
ls -la /opt/windi/wallet/*.md 2>/dev/null || warn "No .md files"

# Verificar que wallet_provisioning.py existe
if [ -f /opt/windi/wallet/wallet_provisioning.py ]; then
    ok "wallet_provisioning.py found"
else
    fail "wallet_provisioning.py NOT FOUND — checking subdirectories..."
    find /opt/windi/wallet/ -name "wallet_provisioning.py" -type f
    exit 1
fi

if [ -f /opt/windi/wallet/wallet_bridge.py ]; then
    ok "wallet_bridge.py found"
else
    warn "wallet_bridge.py not found (optional for Mode C)"
fi

echo ""

# ============================================================================
# FASE 3: CRIAR DIRETÓRIOS
# ============================================================================
echo "── FASE 3: Criar diretórios ────────────────────"

mkdir -p /opt/windi/data
mkdir -p /opt/windi/logs
mkdir -p /opt/windi/tsil/wallet_keys
chmod 700 /opt/windi/tsil/wallet_keys
mkdir -p /opt/windi/backups/forensic_pending

ok "Directories created"
echo "  /opt/windi/data/          (wallet.db viverá aqui)"
echo "  /opt/windi/tsil/wallet_keys/ (chaves privadas, 700)"
echo "  /opt/windi/backups/forensic_pending/ (fallback forense)"
echo ""

# ============================================================================
# FASE 4: INSTALAR DEPENDÊNCIAS
# ============================================================================
echo "── FASE 4: Dependências ────────────────────────"

# uuid-utils para UUIDv7 (tem fallback para UUID4)
pip install uuid-utils --break-system-packages 2>/dev/null && \
    ok "uuid-utils installed" || warn "uuid-utils failed (will use UUID4 fallback)"

# PyNaCl para Ed25519 real (tem fallback para dev)
pip install pynacl --break-system-packages 2>/dev/null && \
    ok "PyNaCl installed" || warn "PyNaCl failed (will use fallback key gen)"

# requests (provavelmente já existe)
pip install requests --break-system-packages 2>/dev/null && \
    ok "requests installed" || warn "requests might already be installed"

echo ""

# ============================================================================
# FASE 5: TESTE STANDALONE
# ============================================================================
echo "── FASE 5: Teste Standalone ────────────────────"

cd /opt/windi/wallet

WALLET_DB_PATH=/opt/windi/data/wallet_test.db \
FORENSIC_API_URL=http://localhost:8094 \
FORENSIC_FALLBACK_DIR=/opt/windi/backups/forensic_pending \
WALLET_LOG_PATH=/opt/windi/logs/wallet_test.log \
python3 wallet_provisioning.py 2>&1

TEST_EXIT=$?
if [ $TEST_EXIT -eq 0 ]; then
    ok "Standalone test passed"
else
    fail "Standalone test failed (exit code: $TEST_EXIT)"
    echo "Check: /opt/windi/logs/wallet_test.log"
fi

# Limpar teste
rm -f /opt/windi/data/wallet_test.db
rm -f /opt/windi/logs/wallet_test.log

echo ""

# ============================================================================
# FASE 6: DIAGNÓSTICO DA GOVERNANCE API
# ============================================================================
echo "── FASE 6: Diagnóstico Governance API ──────────"

# Verificar se está rodando
GOV_PID=$(pgrep -f "windi_governance_api" || echo "")
if [ -n "$GOV_PID" ]; then
    ok "Governance API running (PID: $GOV_PID)"
else
    warn "Governance API not running"
fi

# Verificar porta 8080
ss -tlnp | grep :8080 && ok "Port 8080 active" || warn "Port 8080 not active"

# Verificar saúde
HTTP=$(curl -so /dev/null -w "%{http_code}" http://localhost:8080/api/status 2>/dev/null)
echo "Governance API /api/status: HTTP $HTTP"

# Encontrar arquivo principal
echo ""
echo "Governance API files:"
find /opt/windi/engine -name "windi_governance_api.py" -type f 2>/dev/null
find /opt/windi/engine -name "*.py" -type f | head -10

echo ""

# ============================================================================
# FASE 7: INTEGRAR BLUEPRINT (MANUAL — REQUER REVISÃO HUMANA)
# ============================================================================
echo "── FASE 7: Integração (INSTRUÇÕES) ─────────────"
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  I9: HUMAN APPROVAL REQUIRED                        ║"
echo "║  As próximas ações requerem decisão humana.         ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "Para integrar o WALLET na Governance API, execute:"
echo ""
echo "  1. Abra o arquivo da Governance API:"
echo "     nano /opt/windi/engine/windi_governance_api.py"
echo ""
echo "  2. Adicione ANTES de app.run() (ou no final das rotas):"
echo ""
echo "     # ─── WALLET MODULE ───────────────────────────────"
echo "     import sys"
echo "     sys.path.insert(0, '/opt/windi/wallet')"
echo "     from wallet_provisioning import create_wallet_blueprint"
echo "     app.register_blueprint(create_wallet_blueprint())"
echo "     from wallet_bridge import create_bridge_blueprint"
echo "     app.register_blueprint(create_bridge_blueprint())"
echo "     # ─── END WALLET ──────────────────────────────────"
echo ""
echo "  3. Salve e reinicie:"
echo "     pkill -f windi_governance_api.py"
echo "     cd /opt/windi/engine"
echo "     nohup python3 windi_governance_api.py > /opt/windi/logs/governance.log 2>&1 &"
echo "     sleep 3"
echo ""
echo "  4. Verifique:"
echo "     curl -s http://localhost:8080/api/wallet/health | python3 -m json.tool"
echo ""

# ============================================================================
# FASE 8: VERIFICAÇÃO FINAL
# ============================================================================
echo "── FASE 8: Verificação Final ───────────────────"
echo ""
echo "Após integrar (Fase 7), execute estes testes:"
echo ""
echo "  # Health check"
echo "  curl -s http://localhost:8080/api/wallet/health | python3 -m json.tool"
echo ""
echo "  # Provisionar primeiro wallet real"
echo '  curl -s -X POST http://localhost:8080/api/wallet/provision \'
echo '    -H "Content-Type: application/json" \'
echo '    -d '"'"'{'
echo '      "lead_id": "LEAD-20260215-151736",'
echo '      "email": "jober@a4desk.de",'
echo '      "display_name": "Jober Mögele Correa",'
echo '      "kind": "PJ",'
echo '      "org": {"name": "WINDI Publishing House", "domain": "a4desk.de"},'
echo '      "role": "admin",'
echo '      "approved_by": "admin:jober"'
echo '    }'"'"' | python3 -m json.tool'
echo ""
echo "  # Verificar via email"
echo '  curl -s "http://localhost:8080/api/wallet/me?email=jober@a4desk.de" | python3 -m json.tool'
echo ""
echo "  # Stats"
echo "  curl -s http://localhost:8080/api/wallet/stats | python3 -m json.tool"
echo ""

# ============================================================================
# RESUMO
# ============================================================================
echo "=============================================="
echo "🐉 WALLET Deploy — Resumo"
echo "=============================================="
echo ""
echo "Completado automaticamente:"
echo "  ✅ Backup criado em: $BK"
echo "  ✅ Arquivos descompactados em /opt/windi/wallet/"
echo "  ✅ Diretórios criados (data, logs, keys)"
echo "  ✅ Dependências instaladas"
echo "  ✅ Teste standalone executado"
echo ""
echo "Requer ação humana (I9):"
echo "  ⏳ Integrar Blueprint na Governance API (Fase 7)"
echo "  ⏳ Verificar endpoints (Fase 8)"
echo ""
echo "Próximo após verificação:"
echo "  → Conectar Lead Admin Approve → wallet_bridge"
echo "  → Testar pipeline completo"
echo ""
echo "O coração está pronto para bater no corpo real. 🐉"
