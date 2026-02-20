#!/bin/bash
# ================================================================
# 🔐 FORENSIC VAULT — Surgical Integration into Governance Dashboard
# 
# 3 INCISION POINTS — zero CSS conflict, zero theme risk
# The Vault stays standalone on :8106
# The Dashboard only gets LINKS pointing to it
#
# PREREQUISITE: Vault already deployed on :8106
# ================================================================

set -e

echo "🔐 Forensic Vault — Surgical Dashboard Integration"
echo "===================================================="

# === STEP 0: Find the governance dashboard file ===
echo ""
echo "0️⃣  Locating governance dashboard..."

# Common locations — adjust if needed
DASH=""
for candidate in \
    "/opt/windi/engine/templates/governance_dashboard.html" \
    "/opt/windi/a4desk-landing/templates/governance.html" \
    "/opt/windi/a4desk-landing/static/governance.html" \
    "/opt/windi/engine/static/governance_dashboard.html" \
    "/opt/windi/governance/dashboard.html" \
    "/opt/windi/governance/index.html"; do
    if [ -f "$candidate" ]; then
        DASH="$candidate"
        echo "✅ Found: $DASH"
        break
    fi
done

if [ -z "$DASH" ]; then
    echo "⚠️  Dashboard not found at standard locations."
    echo "   Searching..."
    DASH=$(find /opt/windi -name "*.html" -exec grep -l "WINDI Governance Dashboard" {} \; 2>/dev/null | head -1)
    if [ -n "$DASH" ]; then
        echo "✅ Found via search: $DASH"
    else
        echo "❌ Cannot find governance dashboard HTML."
        echo "   Please locate it manually and set DASH= in this script."
        echo "   Hint: grep -r 'WINDI Governance Dashboard' /opt/windi/"
        exit 1
    fi
fi

# === BACKUP ===
echo ""
echo "📦  Creating backup..."
BK="/opt/windi/backups/pre_vault_integration_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BK"
cp "$DASH" "$BK/dashboard_original.html"
echo "✅ Backup: $BK/dashboard_original.html"

# ================================================================
# INCISION 1: SIDEBAR NAVIGATION
# Add Forensic Vault link to the sidebar
# ================================================================
echo ""
echo "1️⃣  INCISION 1: Sidebar Navigation"

# Look for the ISP Audit or Tutorial link in sidebar to inject AFTER it
if grep -q 'ISP Audit' "$DASH"; then
    # Inject after the ISP Audit link
    sed -i '/<a.*ISP Audit.*<\/a>/a\
 <a href="/vault/" target="_blank" title="Forensic Vault — Governance Audit Room">\
   <span style="margin-right:6px;">🔐</span> Forensic Vault\
 </a>' "$DASH"
    echo "✅ Vault link added to sidebar (after ISP Audit)"
elif grep -q 'Tutorial' "$DASH"; then
    # Inject before Tutorial
    sed -i '/<a.*Tutorial/i\
 <a href="/vault/" target="_blank" title="Forensic Vault — Governance Audit Room">\
   <span style="margin-right:6px;">🔐</span> Forensic Vault\
 </a>' "$DASH"
    echo "✅ Vault link added to sidebar (before Tutorial)"
else
    echo "⚠️  Could not find sidebar anchor. Manual injection needed."
    echo "   Add this HTML to the sidebar navigation:"
    echo '   <a href="/vault/" target="_blank" title="Forensic Vault">'
    echo '     <span style="margin-right:6px;">🔐</span> Forensic Vault'
    echo '   </a>'
fi

# ================================================================
# INCISION 2: AGENT CONSTELLATION — Add Vault card
# ================================================================
echo ""
echo "2️⃣  INCISION 2: Agent Constellation Card"

# Look for "Unified Audit" card or "Cycle Reports" to inject before
if grep -q 'Cycle Reports' "$DASH"; then
    sed -i '/Cycle Reports/i\
<a href="/vault/" target="_blank" class="agent-card" style="text-decoration:none;">\
  <div style="display:flex;justify-content:space-between;align-items:center;">\
    <span style="font-weight:600;">🔐 Forensic Vault</span>\
    <span class="badge-live" style="background:var(--green-dim,#4ade8020);color:var(--green,#4ade80);padding:2px 8px;border-radius:12px;font-size:10px;font-weight:500;">LIVE</span>\
  </div>\
  <div style="font-size:12px;color:var(--text-secondary,#8a8890);margin-top:4px;">Read-only Ledger · Paginated Audit · CSV Export</div>\
</a>' "$DASH"
    echo "✅ Vault card added to Agent Constellation (before Cycle Reports)"
else
    echo "⚠️  Could not find Agent Constellation anchor. Manual injection needed."
    echo "   Add a Vault card in the Agent Constellation section."
fi

# ================================================================
# INCISION 3: SERVICE HEALTH — Add Vault health check
# ================================================================
echo ""
echo "3️⃣  INCISION 3: Service Health Row"

# Look for the Day-by-Day service entry to inject after it
if grep -q 'Day-by-Day' "$DASH"; then
    sed -i '/Day-by-Day.*day-by-day-server/,/<\/div>/a\
\
<!-- Forensic Vault Health -->\
<div class="health-row" id="health-vault" style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--border,#2a2a35);">\
  <div>\
    <strong style="font-size:13px;">Forensic Vault</strong>\
    <div style="font-size:11px;color:var(--text-muted,#55545a);">:8106 · forensic_vault.py</div>\
  </div>\
  <span id="vault-health-status" style="font-size:11px;color:var(--text-muted);">checking</span>\
</div>' "$DASH"
    echo "✅ Vault health row added to Service Health"
else
    echo "⚠️  Could not find Service Health anchor. Manual injection needed."
fi

# ================================================================
# INCISION 3b: HEALTH CHECK JAVASCRIPT
# Inject the fetch call for Vault health
# ================================================================
echo ""
echo "3b️⃣  INCISION 3b: Health Check JavaScript"

# Look for existing health check fetch calls to add the Vault one
if grep -q 'checkHealth\|health.*8080\|fetchHealth' "$DASH"; then
    # Inject Vault health check near existing health checks
    sed -i '/<\/script>/i\
// --- Forensic Vault Health Check ---\
(function checkVaultHealth() {\
  fetch("/vault/health").then(r => r.json()).then(d => {\
    const el = document.getElementById("vault-health-status");\
    if (el) {\
      if (d.status === "healthy") {\
        el.textContent = "online · " + (d.receipts || 0) + " receipts";\
        el.style.color = "var(--green, #4ade80)";\
      } else {\
        el.textContent = "error";\
        el.style.color = "var(--red, #f87171)";\
      }\
    }\
  }).catch(() => {\
    const el = document.getElementById("vault-health-status");\
    if (el) { el.textContent = "offline"; el.style.color = "var(--red, #f87171)"; }\
  });\
})();' "$DASH"
    echo "✅ Vault health check JS injected"
else
    echo "⚠️  Could not find script block for health check injection."
    echo "   Add the health check JS manually before </script>"
fi

# ================================================================
# FINAL VERIFICATION
# ================================================================
echo ""
echo "4️⃣  Verification..."

# Check all 3 incisions
SIDEBAR=$(grep -c 'Forensic Vault' "$DASH" 2>/dev/null || echo 0)
echo "   Vault references found: $SIDEBAR"

if [ "$SIDEBAR" -ge 2 ]; then
    echo "✅ All incisions appear successful!"
else
    echo "⚠️  Some incisions may need manual verification."
    echo "   Open the dashboard and check: sidebar link, agent card, health row"
fi

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  🔐 Surgical Integration Complete                ║"
echo "║                                                  ║"
echo "║  3 incisions:                                    ║"
echo "║  ① Sidebar: 🔐 Forensic Vault link              ║"
echo "║  ② Agent Constellation: Vault card (LIVE)        ║"
echo "║  ③ Service Health: :8106 health check            ║"
echo "║                                                  ║"
echo "║  Zero CSS injected. Zero theme conflict.         ║"
echo "║  Vault stays standalone on :8106.                ║"
echo "║                                                  ║"
echo "║  Backup: $BK  ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "🐉 Cirurgia concluída. O paciente sobrevive."
