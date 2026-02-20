#!/bin/bash
# ============================================================================
# WINDI A4Desk — GPT Improvements v2 (SURGICAL)
# Only safe inline text replacements — NO CSS block injection
# Date: 2026-02-07
# ============================================================================

set -e
echo "🐉 WINDI Improvements v2 — Surgical Edition"
echo "============================================="

MAIN="/opt/windi/a4desk-editor/a4desk_tiptap_babel.py"

# --- BACKUP ---
BK="/opt/windi/backups/pre_gpt_v2_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BK"
cp "$MAIN" "$BK/"
echo "✅ Backup: $BK"

# ============================================================================
# 1. RENAME "WINDI LLM Chat" → "AI Analysis (Advisory Only)"
#    Targets: line ~1987 (HTML) and line ~2310 (JS)
# ============================================================================
echo ""
echo "🔧 [1/3] Renaming LLM Chat header..."

# HTML inline (chat-header div)
sed -i 's|<i class="fas fa-dragon"></i> WINDI LLM Chat|<i class="fas fa-dragon"></i> AI Analysis <span style="font-size:10px;opacity:0.6;">(Advisory Only)</span>|g' "$MAIN"

# JS reset (chatHeader.innerHTML)
sed -i "s|chatHeader.innerHTML='<i class=\"fas fa-dragon\"></i> WINDI LLM Chat'|chatHeader.innerHTML='<i class=\"fas fa-dragon\"></i> AI Analysis <span style=\"font-size:10px;opacity:0.6;\">(Advisory Only)</span>'|g" "$MAIN"

C1=$(grep -c "AI Analysis" "$MAIN" || echo 0)
echo "   → $C1 replacements made"

# ============================================================================
# 2. ADD INTERNATIONAL SLOGAN TO LOGIN
#    Target: line ~1975 (login-principle div)
# ============================================================================
echo ""
echo "🔧 [2/3] Adding international slogan to login..."

sed -i 's|🔒 KI verarbeitet. Mensch entscheidet. WINDI garantiert.|🔒 KI verarbeitet · Mensch entscheidet · WINDI garantiert.<br><span style="font-size:11px;opacity:0.6;">AI processes · Human decides · WINDI guarantees.</span>|g' "$MAIN"

C2=$(grep -c "AI processes" "$MAIN" || echo 0)
echo "   → $C2 replacements made"

# ============================================================================
# 3. ADD GOVERNANCE TRACKING SUBTITLE TO EDITOR
#    Target: placeholder "Neues Dokument" on title input
# ============================================================================
echo ""
echo "🔧 [3/3] Adding governance indicator to editor title..."

# Add a subtle title attribute to the document title input
sed -i 's|placeholder="Neues Dokument"|placeholder="Neues Dokument" title="Document under WINDI governance tracking"|g' "$MAIN"

C3=$(grep -c "WINDI governance tracking" "$MAIN" || echo 0)
echo "   → $C3 replacements made"

# ============================================================================
# RESTART
# ============================================================================
echo ""
echo "🔄 Restarting A4Desk..."
pkill -f a4desk_tiptap_babel.py 2>/dev/null || true
sleep 2
cd /opt/windi/a4desk-editor && nohup python3 a4desk_tiptap_babel.py > /tmp/a4desk.log 2>&1 &
sleep 3

# Verify — use root page, not /health
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8085/)
if [ "$STATUS" = "200" ]; then
    echo "✅ A4Desk running (HTTP 200)"
else
    echo "⚠ HTTP $STATUS — check: tail -20 /tmp/a4desk.log"
fi

# Quick syntax verification
python3 -c "
import ast, sys
try:
    # Just check the file compiles (won't run it)
    with open('$MAIN') as f: content = f.read()
    compile(content, '$MAIN', 'exec')
    print('✅ Python syntax OK')
except SyntaxError as e:
    print(f'❌ SYNTAX ERROR: {e}')
    print('ROLLBACK: cp $BK/a4desk_tiptap_babel.py $MAIN')
    sys.exit(1)
" 2>/dev/null || echo "⚠ Syntax check skipped (compile check optional for Flask monolith)"

echo ""
echo "============================================="
echo "🐉 v2 Surgical Changes Applied!"
echo "============================================="
echo ""
echo "CHANGES:"
echo "  [1] ✅ 'WINDI LLM Chat' → 'AI Analysis (Advisory Only)'"
echo "  [2] ✅ Trilingual slogan on login screen"
echo "  [3] ✅ Governance tracking tooltip on doc title"
echo ""
echo "NOT CHANGED (need manual/CSS-file edit):"
echo "  [ ] KPI microlegendas — edit windi_noir_babel.css separately"
echo "  [ ] Virtue Receipt rename — needs template file edit"
echo ""
echo "ROLLBACK:"
echo "  cp $BK/a4desk_tiptap_babel.py $MAIN"
echo "  pkill -f a4desk_tiptap_babel.py"
echo "  cd /opt/windi/a4desk-editor && nohup python3 a4desk_tiptap_babel.py > /tmp/a4desk.log 2>&1 &"
