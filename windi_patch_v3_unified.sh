#!/bin/bash
# ============================================================================
# WINDI Patch v3 UNIFIED — Witness Recs + Governance Noir/Klar Toggle
# Date: 2026-02-07
# Three Dragons Consensus: Guardian ✅ Architect ✅ Witness ✅
# ============================================================================

set -e
echo "🐉 WINDI Patch v3 UNIFIED"
echo "========================="

MAIN="/opt/windi/a4desk-editor/a4desk_tiptap_babel.py"
GOV="/opt/windi/a4desk-editor/static/governance-command-center.html"

# --- BACKUP ---
BK="/opt/windi/backups/pre_v3_unified_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BK"
cp "$MAIN" "$BK/"
cp "$GOV" "$BK/"
echo "✅ Backup: $BK"

# --- PRE-CHECK ---
if ! grep -q "AI Analysis" "$MAIN"; then
    echo "❌ v2 changes not found in BABEL. Run v2 first."
    exit 1
fi
echo "✅ v2 baseline confirmed"

# ============================================================================
# PART A: BABEL EDITOR — Witness Recommendations
# ============================================================================
echo ""
echo "━━━ PART A: BABEL Witness Changes ━━━"

# A1. "Command Center" → "Governance Dashboard"
echo "🔧 [A1] Command Center → Governance Dashboard..."
sed -i 's/Command Center/Governance Dashboard/g' "$MAIN"
sed -i 's/command-center/governance-dashboard/g' "$MAIN"
sed -i 's/command_center/governance_dashboard/g' "$MAIN"
echo "   → $(grep -c 'Governance Dashboard' "$MAIN" 2>/dev/null || echo 0) replacements"

# A2. "Human Decision Required" banner in AI chat
echo "🔧 [A2] Adding HDR banner to AI chat..."
sed -i 's|Willkommen! Wie kann ich helfen?|Willkommen! Wie kann ich helfen?<div style="margin-top:8px;padding:4px 8px;background:rgba(184,134,11,0.15);border-left:2px solid #b8860b;font-size:11px;color:#b8860b;">⚖️ Human Decision Required — AI is advisory only</div>|g' "$MAIN"
echo "   → $(grep -c 'Human Decision Required' "$MAIN" 2>/dev/null || echo 0) replacements"

# A3. "WINDI-RECEIPT (Immutable)"
echo "🔧 [A3] Adding (Immutable) to WINDI-RECEIPT..."
sed -i 's|WINDI-RECEIPT|WINDI-RECEIPT (Immutable)|g' "$MAIN"
echo "   → $(grep -c 'Immutable' "$MAIN" 2>/dev/null || echo 0) replacements"

# A4. "WINDI Verified" seal
echo "🔧 [A4] Adding WINDI Verified seal..."
sed -i 's|Governance Receipt|Governance Certificate (WINDI Verified)|g' "$MAIN"
sed -i 's|governance-receipt|governance-certificate|g' "$MAIN"
echo "   → $(grep -c 'WINDI Verified' "$MAIN" 2>/dev/null || echo 0) replacements"

# A5. Compact badge in top bar
echo "🔧 [A5] Adding compact WINDI Verified badge..."
sed -i 's|A4 Desk BABEL v4.7-gov</span>|A4 Desk BABEL v4.7-gov</span><span style="font-size:10px;margin-left:8px;color:#b8860b;opacity:0.7;">WINDI Verified</span>|g' "$MAIN"
echo "   → Done"

# BABEL Syntax Check
echo ""
echo "🔍 BABEL syntax check..."
python3 -c "
with open('$MAIN') as f: content = f.read()
compile(content, '$MAIN', 'exec')
print('✅ BABEL Python syntax OK')
" 2>/dev/null || {
    echo "❌ BABEL SYNTAX ERROR — rolling back!"
    cp "$BK/a4desk_tiptap_babel.py" "$MAIN"
    echo "Restored BABEL. Skipping Part B."
    exit 1
}

# ============================================================================
# PART B: GOVERNANCE PAGE — Noir/Klar Toggle
# ============================================================================
echo ""
echo "━━━ PART B: Governance Noir/Klar Toggle ━━━"

# B1. Inject Klar theme CSS BEFORE </style> (line 875)
echo "🔧 [B1] Injecting Klar theme CSS..."
sed -i '/<\/style>/i\
/* ====== KLAR THEME (Light Mode) ====== */\
[data-theme="klar"] {\
  --void: #f5f5f0;\
  --surface-0: #ffffff;\
  --surface-1: #f0ede6;\
  --surface-2: #e8e4db;\
  --gold: #8b6914;\
  --gold-bright: #a07d1a;\
  --gold-dim: #c9a227;\
  --text-primary: #1a1a1a;\
  --text-secondary: #4a4a4a;\
  --text-muted: #6a6a6a;\
  --border-subtle: #d4d0c8;\
  --border-default: #b8b4ac;\
  --status-success: #2d6a30;\
  --status-warning: #8b6914;\
  --status-danger: #a82020;\
  --status-info: #1a5276;\
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);\
  --shadow-md: 0 4px 12px rgba(0,0,0,0.1);\
}\
[data-theme="klar"] .gc-header {\
  background: linear-gradient(135deg, #ffffff 0%, #f0ede6 100%);\
  border-bottom: 1px solid #d4d0c8;\
}\
[data-theme="klar"] .gc-card {\
  background: #ffffff;\
  border: 1px solid #d4d0c8;\
}\
[data-theme="klar"] .gc-tab.active {\
  background: #8b6914;\
  color: #ffffff;\
}\
[data-theme="klar"] .gc-tab:not(.active) {\
  background: #f0ede6;\
  color: #4a4a4a;\
  border: 1px solid #d4d0c8;\
}\
[data-theme="klar"] .gc-tab:not(.active):hover {\
  background: #e8e4db;\
}\
[data-theme="klar"] .gc-kpi-value {\
  color: #1a1a1a;\
}\
[data-theme="klar"] .gc-table th {\
  background: #f0ede6;\
  color: #1a1a1a;\
}\
[data-theme="klar"] .gc-table td {\
  border-color: #d4d0c8;\
  color: #1a1a1a;\
}\
[data-theme="klar"] input,\
[data-theme="klar"] select,\
[data-theme="klar"] textarea {\
  background: #ffffff;\
  color: #1a1a1a;\
  border-color: #d4d0c8;\
}\
/* Theme toggle button */\
.theme-toggle-gov {\
  position: fixed;\
  top: 12px;\
  right: 16px;\
  z-index: 1000;\
  background: var(--surface-1);\
  border: 1px solid var(--border-subtle);\
  border-radius: 20px;\
  padding: 6px 14px;\
  cursor: pointer;\
  font-size: 16px;\
  transition: all 0.3s ease;\
}\
.theme-toggle-gov:hover {\
  border-color: var(--gold);\
  box-shadow: 0 0 8px rgba(201,162,39,0.3);\
}' "$GOV"

echo "   → Klar CSS injected"

# B2. Add toggle button AFTER <body> tag (line 877)
echo "🔧 [B2] Adding theme toggle button..."
sed -i 's|<body>|<body>\n<button class="theme-toggle-gov" onclick="toggleTheme()" title="Toggle Noir/Klar">🌙</button>|' "$GOV"
echo "   → Toggle button added"

# B3. Add toggleTheme() function BEFORE </script> (line ~1085)
echo "🔧 [B3] Adding toggleTheme() function..."
sed -i '/<\/script>/i\
\
// === THEME TOGGLE (Noir/Klar) ===\
function toggleTheme() {\
  const html = document.documentElement;\
  const btn = document.querySelector(".theme-toggle-gov");\
  const current = html.getAttribute("data-theme");\
  if (current === "dark") {\
    html.setAttribute("data-theme", "klar");\
    btn.textContent = "☀️";\
    localStorage.setItem("windi-gov-theme", "klar");\
  } else {\
    html.setAttribute("data-theme", "dark");\
    btn.textContent = "🌙";\
    localStorage.setItem("windi-gov-theme", "dark");\
  }\
}\
// Restore saved theme\
(function() {\
  var saved = localStorage.getItem("windi-gov-theme");\
  if (saved === "klar") {\
    document.documentElement.setAttribute("data-theme", "klar");\
    var btn = document.querySelector(".theme-toggle-gov");\
    if (btn) btn.textContent = "☀️";\
  }\
})();' "$GOV"

echo "   → toggleTheme() function added"

# B4. Also rename "Command Center" in governance page
echo "🔧 [B4] Renaming Command Center in governance page..."
sed -i 's/Command Center/Governance Dashboard/g' "$GOV"
sed -i 's/command-center/governance-dashboard/g' "$GOV"
echo "   → $(grep -c 'Governance Dashboard' "$GOV" 2>/dev/null || echo 0) replacements"

# ============================================================================
# RESTART & VERIFY
# ============================================================================
echo ""
echo "🔄 Restarting A4Desk..."
pkill -f a4desk_tiptap_babel.py 2>/dev/null || true
sleep 2
cd /opt/windi/a4desk-editor && nohup python3 a4desk_tiptap_babel.py > /tmp/a4desk.log 2>&1 &
sleep 3

# Check BABEL
STATUS_BABEL=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8085/)
echo "BABEL: HTTP $STATUS_BABEL"

# Check Governance
STATUS_GOV=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8085/static/governance-command-center.html)
echo "Governance: HTTP $STATUS_GOV"

# Check exports still work
DOC_ID=$(sqlite3 /opt/windi/data/babel_documents.db "SELECT id FROM documents ORDER BY created_at DESC LIMIT 1;" 2>/dev/null)
if [ -n "$DOC_ID" ]; then
    PDF_S=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8085/export/$DOC_ID?format=pdf")
    echo "PDF Export: HTTP $PDF_S"
fi

echo ""
echo "==================================================="
echo "🐉 Patch v3 UNIFIED — Complete!"
echo "==================================================="
echo ""
echo "THREE DRAGONS CONSENSUS: Guardian ✅ Architect ✅ Witness ✅"
echo ""
echo "PART A — BABEL Witness Changes:"
echo "  [A1] ✅ Command Center → Governance Dashboard"
echo "  [A2] ✅ Human Decision Required banner"
echo "  [A3] ✅ WINDI-RECEIPT (Immutable)"
echo "  [A4] ✅ Governance Certificate (WINDI Verified)"
echo "  [A5] ✅ Compact WINDI Verified badge"
echo ""
echo "PART B — Governance Noir/Klar Toggle:"
echo "  [B1] ✅ Klar theme CSS variables + components"
echo "  [B2] ✅ 🌙/☀️ toggle button (top-right)"
echo "  [B3] ✅ toggleTheme() with localStorage persistence"
echo "  [B4] ✅ Command Center → Governance Dashboard"
echo ""
echo "VERIFY:"
echo "  → http://87.106.29.233:8085/ (BABEL login + editor)"
echo "  → http://87.106.29.233:8085/governance (Dashboard + toggle)"
echo ""
echo "ROLLBACK:"
echo "  cp $BK/a4desk_tiptap_babel.py $MAIN"
echo "  cp $BK/governance-command-center.html $GOV"
echo "  pkill -f a4desk_tiptap_babel.py"
echo "  cd /opt/windi/a4desk-editor && nohup python3 a4desk_tiptap_babel.py > /tmp/a4desk.log 2>&1 &"
echo ""
echo "Backup: $BK"
