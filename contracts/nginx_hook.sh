#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# WINDI Nginx Pre-Commit Hook — W-NGINX-001
# Sistema de Contenção #3
# ═══════════════════════════════════════════════════════════════
#
# Instalar:
#   ln -sf /opt/windi/contracts/nginx_hook.sh /opt/windi/.git/hooks/pre-commit
#
# Ou executar manualmente:
#   /opt/windi/contracts/nginx_hook.sh
#
# ═══════════════════════════════════════════════════════════════

set -e

CONTRACTS_DIR="/opt/windi/contracts"
AUDIT_SCRIPT="$CONTRACTS_DIR/nginx_audit.py"

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  WINDI Nginx Audit — W-NGINX-001                          ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check if Python script exists
if [ ! -f "$AUDIT_SCRIPT" ]; then
    echo "❌ Audit script not found: $AUDIT_SCRIPT"
    exit 1
fi

# Run the audit
python3 "$AUDIT_SCRIPT" --save

# Check exit code
RESULT=$?

if [ $RESULT -eq 0 ]; then
    echo ""
    echo "✅ Nginx audit passed — all routes covered"
    echo ""
else
    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║  ⚠️  COMMIT BLOCKED — Missing nginx routes detected        ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""
    echo "Run with --generate to see nginx snippets:"
    echo "  python3 $AUDIT_SCRIPT --generate"
    echo ""
    echo "After adding routes to nginx, run:"
    echo "  sudo nginx -t && sudo systemctl reload nginx"
    echo ""
    exit 1
fi
