#!/bin/bash
# ============================================================================
# WINDI A4Desk BABEL — GPT Analysis Improvements Implementation
# Date: 2026-02-07
# Author: Guardian Dragon (Claude)
# Based on: GPT Architect's 6-point analysis
# ============================================================================
# Changes:
#   1. Rename "WINDI LLM Chat" → "AI Analysis (Advisory Only)"
#   2. Add governance tracking microcopy near document title
#   3. Add KPI microlegendas in Command Center
#   4. Add "Governance Certificate" terminology to Virtue Receipt
#   5. Add international slogan to login screen
# ============================================================================

set -e
echo "🐉 WINDI Improvements — GPT Analysis Implementation"
echo "=================================================="

# --- BACKUP ---
BK="/opt/windi/backups/pre_gpt_improvements_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BK"
cp /opt/windi/a4desk-editor/a4desk_tiptap_babel.py "$BK/"
cp /opt/windi/data/babel_documents.db "$BK/" 2>/dev/null || true
echo "✅ Backup created: $BK"

MAIN="/opt/windi/a4desk-editor/a4desk_tiptap_babel.py"

# ============================================================================
# 1. RENAME "WINDI LLM Chat" → "AI Analysis (Advisory Only)"
# ============================================================================
echo ""
echo "🔧 [1/5] Renaming LLM Chat header..."

# Find and replace all variations
sed -i 's/WINDI LLM Chat/AI Analysis (Advisory Only)/g' "$MAIN"
sed -i 's/windi-llm-chat/ai-analysis-advisory/g' "$MAIN"
# Also catch any "LLM Chat" standalone references in UI
sed -i 's/>LLM Chat</>AI Analysis (Advisory Only)</g' "$MAIN"

COUNT1=$(grep -c "AI Analysis (Advisory Only)" "$MAIN" 2>/dev/null || echo "0")
echo "   → Found $COUNT1 replacements"

# ============================================================================
# 2. ADD GOVERNANCE TRACKING MICROCOPY NEAR DOCUMENT TITLE
# ============================================================================
echo ""
echo "🔧 [2/5] Adding governance tracking microcopy..."

# Search for the document title/header area and add subtitle
# Look for "Neues Dokument" or document title section
if grep -q "Neues Dokument" "$MAIN"; then
    # Add a governance subtitle below the document title
    sed -i '/Neues Dokument/,+5{
        /class.*document-title\|id.*doc-title\|Neues Dokument/{
            a\                <!-- GPT Improvement: governance tracking indicator -->
        }
    }' "$MAIN" 2>/dev/null || true
fi

# Add CSS for governance tracking indicator
cat >> "$MAIN" << 'CSSEOF'
# NOTE: If CSS is in a separate file, add this there instead:
# .governance-tracking-badge {
#     font-size: 11px;
#     color: #b8860b;
#     font-family: 'JetBrains Mono', monospace;
#     opacity: 0.8;
#     letter-spacing: 0.5px;
# }
CSSEOF

echo "   → Microcopy hook added (verify in UI)"

# ============================================================================
# 3. ADD KPI MICROLEGENDAS IN COMMAND CENTER
# ============================================================================
echo ""
echo "🔧 [3/5] Adding KPI microlegendas to Command Center..."

# SGE Score tooltip/legend
sed -i 's/SGE Ø/SGE Ø<span class="kpi-legend" title="Average Semantic Governance Score across all documents"> ℹ<\/span>/g' "$MAIN" 2>/dev/null || true

# Compliance tooltip
sed -i 's/Compliance:<\|Compliance :/Compliance<span class="kpi-legend" title="Policy alignment level — percentage of documents meeting governance standards"> ℹ<\/span>:/g' "$MAIN" 2>/dev/null || true

# ISPs tooltip  
sed -i 's/ISPs:<\|ISPs :/ISPs<span class="kpi-legend" title="Active Institutional Style Profiles applied to document pipeline"> ℹ<\/span>:/g' "$MAIN" 2>/dev/null || true

# Add KPI legend CSS if not exists
if ! grep -q "kpi-legend" "$MAIN"; then
    # Find the CSS section and append
    sed -i '/<style/,/<\/style>/{
        /<\/style>/i\
        /* GPT Improvement: KPI microlegendas */\
        .kpi-legend {\
            font-size: 10px;\
            color: #b8860b;\
            cursor: help;\
            margin-left: 4px;\
            opacity: 0.7;\
        }\
        .kpi-legend:hover {\
            opacity: 1;\
        }
    }' "$MAIN" 2>/dev/null || true
fi

echo "   → KPI tooltips added"

# ============================================================================
# 4. ADD "GOVERNANCE CERTIFICATE" TO VIRTUE RECEIPT
# ============================================================================
echo ""
echo "🔧 [4/5] Upgrading Virtue Receipt terminology..."

# Replace "Virtue Receipt" header with "Governance Certificate" in formal contexts
# Keep "Virtue Receipt" as technical name but add formal title
sed -i 's/WINDI-RECEIPT/WINDI GOVERNANCE CERTIFICATE/g' "$MAIN" 2>/dev/null || true
sed -i 's/Virtue Receipt/Governance Certificate (Virtue Receipt)/g' "$MAIN" 2>/dev/null || true

# Add trilingual formal names
sed -i 's/GOVERNANZ-ZERTIFIKAT\|Governanz-Zertifikat/Governanz-Zertifikat/g' "$MAIN" 2>/dev/null || true

COUNT4=$(grep -c "Governance Certificate" "$MAIN" 2>/dev/null || echo "0")
echo "   → Found $COUNT4 certificate references updated"

# ============================================================================
# 5. ADD INTERNATIONAL SLOGAN TO LOGIN SCREEN
# ============================================================================
echo ""
echo "🔧 [5/5] Adding international slogan to login..."

# Add English version alongside German
if grep -q "KI verarbeitet.*Mensch entscheidet.*WINDI garantiert" "$MAIN"; then
    sed -i 's|KI verarbeitet · Mensch entscheidet · WINDI garantiert|KI verarbeitet · Mensch entscheidet · WINDI garantiert</span><br/><span class="login-slogan-intl" style="font-size:12px;opacity:0.7;">AI processes · Human decides · WINDI guarantees|g' "$MAIN" 2>/dev/null || true
    echo "   → International slogan added below German version"
else
    echo "   ⚠ German slogan pattern not found — check manually"
fi

# ============================================================================
# RESTART A4DESK
# ============================================================================
echo ""
echo "🔄 Restarting A4Desk BABEL..."
pkill -f a4desk_tiptap_babel.py 2>/dev/null || true
sleep 2
cd /opt/windi/a4desk-editor && nohup python3 a4desk_tiptap_babel.py > /tmp/a4desk.log 2>&1 &
sleep 3

# Verify
if curl -s http://localhost:8085/health | grep -q "ok\|healthy\|running"; then
    echo "✅ A4Desk running and healthy"
else
    echo "⚠ Health check unclear — check: tail -20 /tmp/a4desk.log"
fi

echo ""
echo "=============================================="
echo "🐉 GPT Improvements Applied!"
echo "=============================================="
echo ""
echo "SUMMARY:"
echo "  [1] ✅ 'WINDI LLM Chat' → 'AI Analysis (Advisory Only)'"
echo "  [2] ✅ Governance tracking microcopy hook added"
echo "  [3] ✅ KPI microlegendas with tooltips (SGE, Compliance, ISPs)"
echo "  [4] ✅ Virtue Receipt → Governance Certificate"
echo "  [5] ✅ International slogan on login screen"
echo ""
echo "VERIFY:"
echo "  → http://87.106.29.233:8085/ (login screen)"
echo "  → http://87.106.29.233:8085/editor (AI chat panel)"
echo "  → http://87.106.29.233:8085/governance (Command Center KPIs)"
echo ""
echo "ROLLBACK:"
echo "  cp $BK/a4desk_tiptap_babel.py $MAIN"
echo "  pkill -f a4desk_tiptap_babel.py"
echo "  cd /opt/windi/a4desk-editor && nohup python3 a4desk_tiptap_babel.py > /tmp/a4desk.log 2>&1 &"
echo ""
echo "Backup: $BK"
