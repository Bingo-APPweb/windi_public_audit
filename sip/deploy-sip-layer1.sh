#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# WINDI SIP Layer 1 — Deployment Script for Strato
# AI processes. Human decides. WINDI guarantees.
# ═══════════════════════════════════════════════════════════════

set -e

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║   🔐 WINDI SIP Layer 1 — Deployment                   ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

WINDI_BASE="/opt/windi"
SIP_DIR="$WINDI_BASE/sip"

# Step 1: Create SIP directory
echo "📂 Creating SIP directory..."
mkdir -p "$SIP_DIR"

# Step 2: Copy files
echo "📋 Deploying SIP Layer 1 files..."
cp sip_layer1.py "$SIP_DIR/sip_layer1.py"
cp test_sip_layer1.py "$SIP_DIR/test_sip_layer1.py"

# Step 3: Set permissions (critical for security!)
echo "🔒 Setting strict permissions..."
chown -R windi:windi "$SIP_DIR"
chmod 700 "$SIP_DIR"                    # Directory: owner only
chmod 755 "$SIP_DIR/sip_layer1.py"      # Script: executable
chmod 755 "$SIP_DIR/test_sip_layer1.py" # Test: executable

# Step 4: Run tests on Strato
echo ""
echo "🧪 Running test suite on Strato..."
echo ""
python3 "$SIP_DIR/test_sip_layer1.py"
TEST_RESULT=$?

if [ $TEST_RESULT -ne 0 ]; then
    echo ""
    echo "❌ TESTES FALHARAM! Deploy abortado."
    echo "   Revise os erros antes de configurar a identidade."
    exit 1
fi

# Step 5: Verify
echo ""
echo "🔍 Verificando deployment..."
echo ""

if [ -f "$SIP_DIR/sip_layer1.py" ]; then
    echo "  ✅ sip_layer1.py instalado"
else
    echo "  ❌ sip_layer1.py MISSING"
    exit 1
fi

if [ -f "$SIP_DIR/test_sip_layer1.py" ]; then
    echo "  ✅ test_sip_layer1.py instalado"
else
    echo "  ❌ test_sip_layer1.py MISSING"
    exit 1
fi

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║   ✅ SIP Layer 1 — Deploy completo!                    ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""
echo "  PRÓXIMO PASSO (EXECUTE PESSOALMENTE):"
echo ""
echo "    python3 $SIP_DIR/sip_layer1.py setup"
echo ""
echo "  Isso vai pedir:"
echo "  1. Sua PASSPHRASE SOBERANA (frase secreta)"
echo "  2. Sua PASSPHRASE DE COERÇÃO (frase de emergência)"
echo ""
echo "  ⚠️  FAÇA ISSO EM TERMINAL PRIVADO!"
echo "  ⚠️  NÃO compartilhe a tela durante o setup!"
echo "  ⚠️  MEMORIZE as frases — elas NÃO são salvas!"
echo ""
echo "  Outros comandos:"
echo "    python3 $SIP_DIR/sip_layer1.py status   → Ver status"
echo "    python3 $SIP_DIR/sip_layer1.py verify   → Autenticar"
echo "    python3 $SIP_DIR/sip_layer1.py audit    → Ver ledger"
echo ""
echo "  🐉 O circuito está fechado. Criptograficamente."
echo ""
