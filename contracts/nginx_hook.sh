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

# ═══════════════════════════════════════════════════════════════
# WINDI-LAW Feature Lock Check
# ═══════════════════════════════════════════════════════════════
FEATURE_LOCK_SCRIPT="/opt/windi/windi-law/tests/feature-lock-check.sh"

if [ -f "$FEATURE_LOCK_SCRIPT" ]; then
    echo ""
    "$FEATURE_LOCK_SCRIPT"
    FEATURE_RESULT=$?

    if [ $FEATURE_RESULT -ne 0 ]; then
        echo ""
        echo "╔═══════════════════════════════════════════════════════════╗"
        echo "║  ⚠️  COMMIT BLOCKED — Feature Lock violation               ║"
        echo "╚═══════════════════════════════════════════════════════════╝"
        echo ""
        echo "Check /opt/windi/windi-law/FEATURE_LOCK.md"
        echo "Restore missing features from git history."
        echo ""
        exit 1
    fi
fi

exit 0
