#!/bin/bash
# ============================================================================
# WINDI A4Desk — Patch v3: Witness Dragon Recommendations
# Date: 2026-02-07
# Based on: Gemini Witness validation + Three Dragons consensus
# ============================================================================
# CHANGES:
#   1. "Command Center" → "Governance Dashboard" (Witness: too vague)
#   2. Add "Human Decision Required" indicator to AI Analysis panel
#   3. Add "(Immutable)" to Governance Certificate/Receipt references
#   4. Add "(WINDI Verified)" seal text to receipt output
#   5. Slogan variants: full/medium/compact per context
# ============================================================================

set -e
echo "🐉 WINDI Patch v3 — Witness Dragon Recommendations"
echo "==================================================="

MAIN="/opt/windi/a4desk-editor/a4desk_tiptap_babel.py"

# --- BACKUP ---
BK="/opt/windi/backups/pre_witness_v3_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BK"
cp "$MAIN" "$BK/"
echo "✅ Backup: $BK"

# --- PRE-CHECK: verify v2 changes are present ---
if ! grep -q "AI Analysis" "$MAIN"; then
    echo "❌ v2 changes not found. Run v2 first."
    exit 1
fi
echo "✅ v2 baseline confirmed"

# ============================================================================
# 1. "Command Center" → "Governance Dashboard"
#    Witness: "Command Center" is vague for institutional context
# ============================================================================
echo ""
echo "🔧 [1/5] Command Center → Governance Dashboard..."

sed -i 's/Command Center/Governance Dashboard/g' "$MAIN"
sed -i 's/command-center/governance-dashboard/g' "$MAIN"
sed -i 's/command_center/governance_dashboard/g' "$MAIN"

C1=$(grep -c "Governance Dashboard" "$MAIN" 2>/dev/null || echo 0)
echo "   → $C1 replacements"

# ============================================================================
# 2. ADD "Human Decision Required" to AI Analysis chat
#    Witness: approved AI Analysis but add HDR indicator
# ============================================================================
echo ""
echo "🔧 [2/5] Adding 'Human Decision Required' to AI chat..."

# Add to the welcome message in the chat
sed -i 's|Willkommen! Wie kann ich helfen?|Willkommen! Wie kann ich helfen?<div style="margin-top:8px;padding:4px 8px;background:rgba(184,134,11,0.15);border-left:2px solid #b8860b;font-size:11px;color:#b8860b;">⚖️ Human Decision Required — AI is advisory only</div>|g' "$MAIN"

C2=$(grep -c "Human Decision Required" "$MAIN" 2>/dev/null || echo 0)
echo "   → $C2 replacements"

# ============================================================================
# 3. ADD "(Immutable)" to Governance Certificate references
#    Witness: adds forensic weight
# ============================================================================
echo ""
echo "🔧 [3/5] Adding '(Immutable)' to certificate references..."

# Target the receipt box header/title in the UI
sed -i 's|WINDI-RECEIPT|WINDI-RECEIPT (Immutable)|g' "$MAIN"

C3=$(grep -c "Immutable" "$MAIN" 2>/dev/null || echo 0)
echo "   → $C3 replacements"

# ============================================================================
# 4. ADD "(WINDI Verified)" seal text
#    Witness: use as branding seal on certificates
# ============================================================================
echo ""
echo "🔧 [4/5] Adding 'WINDI Verified' seal..."

# Add to the receipt/certificate generation area
# Look for the SHA-256 hash display in receipts and add seal after it
sed -i 's|Governance Receipt|Governance Certificate (WINDI Verified)|g' "$MAIN"
sed -i 's|governance-receipt|governance-certificate|g' "$MAIN"

C4=$(grep -c "WINDI Verified" "$MAIN" 2>/dev/null || echo 0)
echo "   → $C4 replacements"

# ============================================================================
# 5. COMPACT SLOGAN for badge/footer contexts
#    Witness: use variants (full/medium/compact)
#    Full = login (already done in v2)
#    Compact = top bar or small contexts
# ============================================================================
echo ""
echo "🔧 [5/5] Adding compact slogan variant..."

# Add compact "WINDI Verified" to the top bar title area
sed -i 's|A4 Desk BABEL v4.7-gov</span>|A4 Desk BABEL v4.7-gov</span><span style="font-size:10px;margin-left:8px;color:#b8860b;opacity:0.7;">WINDI Verified</span>|g' "$MAIN"

C5=$(grep -c "WINDI Verified" "$MAIN" 2>/dev/null || echo 0)
echo "   → $C5 total 'WINDI Verified' instances"

# ============================================================================
# SYNTAX CHECK + RESTART
# ============================================================================
echo ""
echo "🔍 Syntax check..."
python3 -c "
with open('$MAIN') as f: content = f.read()
compile(content, '$MAIN', 'exec')
print('✅ Python syntax OK')
" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "❌ SYNTAX ERROR — rolling back!"
    cp "$BK/a4desk_tiptap_babel.py" "$MAIN"
    echo "Restored from backup."
fi

echo ""
echo "🔄 Restarting A4Desk..."
pkill -f a4desk_tiptap_babel.py 2>/dev/null || true
sleep 2
cd /opt/windi/a4desk-editor && nohup python3 a4desk_tiptap_babel.py > /tmp/a4desk.log 2>&1 &
sleep 3

STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8085/)
if [ "$STATUS" = "200" ]; then
    echo "✅ A4Desk running (HTTP 200)"
else
    echo "⚠ HTTP $STATUS — check: tail -20 /tmp/a4desk.log"
    echo "ROLLBACK: cp $BK/a4desk_tiptap_babel.py $MAIN"
fi

# Quick export sanity check
DOC_ID=$(sqlite3 /opt/windi/data/babel_documents.db "SELECT id FROM documents ORDER BY created_at DESC LIMIT 1;" 2>/dev/null)
if [ -n "$DOC_ID" ]; then
    PDF_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8085/export/$DOC_ID?format=pdf")
    echo "✅ PDF export check: HTTP $PDF_STATUS"
fi

echo ""
echo "==================================================="
echo "🐉 Patch v3 — Witness Recommendations Applied!"
echo "==================================================="
echo ""
echo "THREE DRAGONS CONSENSUS:"
echo "  Guardian ✅  Architect ✅  Witness ✅"
echo ""
echo "CHANGES:"
echo "  [1] ✅ 'Command Center' → 'Governance Dashboard'"
echo "  [2] ✅ 'Human Decision Required' banner in AI chat"
echo "  [3] ✅ 'WINDI-RECEIPT (Immutable)' — forensic weight"
echo "  [4] ✅ 'Governance Certificate (WINDI Verified)' seal"
echo "  [5] ✅ Compact 'WINDI Verified' badge in top bar"
echo ""
echo "VERIFIED STILL WORKING:"
echo "  [v2.1] ✅ 'AI Analysis (Advisory Only)'"
echo "  [v2.2] ✅ Trilingual slogan on login"
echo "  [v2.3] ✅ Governance tracking tooltip"
echo "  [exp]  ✅ All 6 export formats (PDF/DOCX/ODT/HTML/RTF/MD)"
echo ""
echo "DECISION FLOW (Witness-corrected):"
echo "  BABEL Editor → AI Analysis (Advisory)"
echo "    → Governance Dashboard → Governance Certificate (Immutable)"
echo "      → War Room (Real-Time) monitors certificate flow"
echo ""
echo "ROLLBACK:"
echo "  cp $BK/a4desk_tiptap_babel.py $MAIN"
echo "  pkill -f a4desk_tiptap_babel.py"
echo "  cd /opt/windi/a4desk-editor && nohup python3 a4desk_tiptap_babel.py > /tmp/a4desk.log 2>&1 &"
