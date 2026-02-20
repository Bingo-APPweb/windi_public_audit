#!/bin/bash
# ═══════════════════════════════════════════════════════════
# WINDI Clone 1 — Governance Enhancement Deploy
# ═══════════════════════════════════════════════════════════
# Uso: Coloque editor_enhanced.html no servidor e rode este script.
#
# scp editor_enhanced.html windi@87.106.29.233:/tmp/
# ssh windi@87.106.29.233
# bash /tmp/deploy_enhance.sh
# ═══════════════════════════════════════════════════════════

set -e

CLONE_DIR="/opt/windi/clone-app/static"
BACKUP_DIR="/opt/windi/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SOURCE="/tmp/editor_enhanced.html"

echo "🐉 WINDI Clone 1 — Governance Enhancement Deploy"
echo "================================================="

# 1. Check source file
if [ ! -f "$SOURCE" ]; then
  echo "❌ Arquivo $SOURCE não encontrado!"
  echo "   Primeiro faça: scp editor_enhanced.html windi@87.106.29.233:/tmp/"
  exit 1
fi
echo "✅ Source file found: $(wc -c < $SOURCE) bytes"

# 2. Backup
mkdir -p "$BACKUP_DIR"
if [ -f "$CLONE_DIR/editor.html" ]; then
  cp "$CLONE_DIR/editor.html" "$BACKUP_DIR/editor_pre_enhance_${TIMESTAMP}.html"
  echo "✅ Backup: $BACKUP_DIR/editor_pre_enhance_${TIMESTAMP}.html"
else
  echo "⚠️  No existing editor.html found — fresh install"
fi

# 3. Deploy
cp "$SOURCE" "$CLONE_DIR/editor.html"
echo "✅ Deployed to $CLONE_DIR/editor.html"

# 4. Verify
echo ""
echo "=== Verification ==="
for term in "windi-welcome" "windi-seal-receipt" "windi-audit-panel" "windi-gov-badge" "windi-inst-footer" "WE.init"; do
  if grep -q "$term" "$CLONE_DIR/editor.html"; then
    echo "  ✅ $term"
  else
    echo "  ❌ $term MISSING!"
  fi
done

# 5. Test via curl (no restart needed — static files)
echo ""
echo "=== Live Test ==="
if curl -s http://localhost:8095/ | grep -q "windi-welcome"; then
  echo "  ✅ Clone serving enhanced editor"
else
  echo "  ⚠️  Clone may need restart:"
  echo "     pkill -f clone_server.py"
  echo "     cd /opt/windi/clone-app && nohup python3 clone_server.py > /tmp/clone.log 2>&1 &"
fi

echo ""
echo "🐉 Deploy complete! Open: http://87.106.29.233:8095/"
echo "   Or: https://admin.windia4desk.tech/clone/"
echo ""
echo "5 Features injected:"
echo "  🛡️ F1: Welcome State (6-card governance grid)"
echo "  📋 F2: Seal Receipt Banner (SHA-256 + Virtue Receipt)"
echo "  📜 F3: Audit Trail Panel (Pro mode sidebar)"
echo "  🟢 F4: Governance Badge (SGE score LED)"
echo "  🏛️ F5: Institutional Footer (WINDI Publishing House)"
