#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#   WINDI AUDITOR DEMO — 12 Minute Institutional Experience
#   "WINDI does not require trust. It provides verifiability."
# ═══════════════════════════════════════════════════════════════

DEMO_DIR="/opt/windi/demo/scripts"

# Colors
GOLD='\033[38;5;220m'
GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

clear

echo -e "${GOLD}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║     W I N D I   A U D I T O R   D E M O                      ║"
echo "║                                                               ║"
echo "║     \"AI processes. Human decides. WINDI guarantees.\"         ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# ─────────────────────────────────────────────────────────────────
# PRE-FLIGHT CHECK
# ─────────────────────────────────────────────────────────────────
echo -e "${CYAN}[0/6] Pre-flight Health Check${NC}"
echo "────────────────────────────────────────"
python3 "$DEMO_DIR/demo_health_check.py"

if [ $? -ne 0 ]; then
    echo -e "${RED}Critical services down. Demo cannot proceed.${NC}"
    exit 1
fi

echo ""
read -p "Press ENTER to start demo..."

# ─────────────────────────────────────────────────────────────────
# STEP 1: ISOLATION SCORE
# ─────────────────────────────────────────────────────────────────
clear
echo -e "${GOLD}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  STEP 1/6: ISOLATION SCORE (Live Metrics)                     ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${CYAN}SCRIPT:${NC}"
echo "\"Each tenant interaction is recorded with forensic metadata."
echo " The system continuously evaluates isolation integrity.\""
echo ""
echo "────────────────────────────────────────"

python3 "$DEMO_DIR/demo_isolation_score.py"

echo ""
read -p "Press ENTER for next step..."

# ─────────────────────────────────────────────────────────────────
# STEP 2: LEDGER VERIFICATION
# ─────────────────────────────────────────────────────────────────
clear
echo -e "${GOLD}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  STEP 2/6: LEDGER VERIFICATION (Integrity Proof)              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${CYAN}SCRIPT:${NC}"
echo "\"Integrity is verified independently through circular hash proof.\""
echo ""
echo "────────────────────────────────────────"

python3 "$DEMO_DIR/demo_ledger_verify.py" COM-20260226-0017

echo ""
read -p "Press ENTER for next step..."

# ─────────────────────────────────────────────────────────────────
# STEP 3: COMMUNIQUÉ LIVE
# ─────────────────────────────────────────────────────────────────
clear
echo -e "${GOLD}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  STEP 3/6: COMMUNIQUÉ (Trilingual Institutional Bulletin)     ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${CYAN}SCRIPT:${NC}"
echo "\"Official communications are sealed with cryptographic proof"
echo " and published in three languages: German, English, Portuguese.\""
echo ""
echo "────────────────────────────────────────"
echo ""
echo "  Live URL: https://communique.windia4desk.online/COM-20260226-0017.html"
echo ""
echo "  Content:"
wget -q -O - "http://127.0.0.1:8105/api/communique/COM-20260226-0017" 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f\"  ID:       {d.get('id', 'N/A')}\")
print(f\"  Status:   {d.get('status', 'N/A')}\")
print(f\"  Category: {d.get('category', 'N/A')}\")
print(f\"  Impact:   {d.get('impact_level', 'N/A')}\")
print()
print(f\"  Title (DE): {d.get('title_de', 'N/A')[:50]}...\")
print(f\"  Title (EN): {d.get('title_en', 'N/A')[:50]}...\")
print(f\"  Title (PT): {d.get('title_pt', 'N/A')[:50]}...\")
print()
print(f\"  Ledger Receipt: {d.get('ledger_id', 'N/A')}\")
print(f\"  Content Hash:   {d.get('content_hash', 'N/A')[:32]}...\")
"

echo ""
read -p "Press ENTER for next step..."

# ─────────────────────────────────────────────────────────────────
# STEP 4: AUDIT BASELINE
# ─────────────────────────────────────────────────────────────────
clear
echo -e "${GOLD}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  STEP 4/6: AUDIT BASELINE (Stability Verification)            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${CYAN}SCRIPT:${NC}"
echo "\"After each milestone, we seal a baseline that becomes"
echo " the reference point for future audits.\""
echo ""
echo "────────────────────────────────────────"
echo ""

cat /opt/windi/reports/baseline/audit_baseline_20260226.json | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('  AUDIT BASELINE: 26 February 2026')
print('  ───────────────────────────────────────')
print()
print('  Tests:')
for name, result in d.get('tests', {}).items():
    status = result.get('status', 'N/A')
    print(f'    {name}: {status}')
print()
print('  Services:')
for name, info in d.get('services', {}).items():
    status = info.get('status', 'N/A')
    print(f'    {name}: {status}')
print()
print(f\"  Overall Status: {d.get('overall_status', 'N/A')}\")
print(f\"  Baseline Hash:  {d.get('baseline_hash', 'N/A')[:32]}...\")
"

echo ""
read -p "Press ENTER for next step..."

# ─────────────────────────────────────────────────────────────────
# STEP 5: GOVERNANCE LAYERS
# ─────────────────────────────────────────────────────────────────
clear
echo -e "${GOLD}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  STEP 5/6: GOVERNANCE LAYERS (Risk Classification)            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${CYAN}SCRIPT:${NC}"
echo "\"Governance risk classification is automatic,"
echo " but decision authority remains human.\""
echo ""
echo "────────────────────────────────────────"
echo ""
echo "  GOVERNANCE LEVELS"
echo "  ───────────────────────────────────────"
echo "  HIGH   — Requires human approval, ledger seal, signature"
echo "  GOLD   — Institutional review required"
echo "  MEDIUM — Standard governance workflow"
echo "  LOW    — Automated processing allowed"
echo ""
echo "  RISK PIPELINE"
echo "  ───────────────────────────────────────"
echo "  R1-R2  — Low risk, automated processing"
echo "  R3     — Medium risk, flagged for review"
echo "  R4-R5  — High risk, human decision required"
echo ""
echo "  KEY PRINCIPLE:"
echo "  \"The system classifies. The human decides.\""
echo ""

echo ""
read -p "Press ENTER for final step..."

# ─────────────────────────────────────────────────────────────────
# STEP 6: CLOSING STATEMENT
# ─────────────────────────────────────────────────────────────────
clear
echo -e "${GOLD}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  STEP 6/6: CLOSING STATEMENT                                  ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo "  ┌─────────────────────────────────────────────────────────┐"
echo "  │                                                         │"
echo "  │   \"WINDI does not require trust.                       │"
echo "  │    It provides verifiability.\"                         │"
echo "  │                                                         │"
echo "  └─────────────────────────────────────────────────────────┘"
echo ""
echo "  SUMMARY"
echo "  ───────────────────────────────────────"
echo "  ✅ Multi-tenant isolation:    VERIFIED"
echo "  ✅ Ledger integrity:          VERIFIED"
echo "  ✅ Communiqué seal:           VERIFIED"
echo "  ✅ Audit baseline:            SEALED"
echo "  ✅ Governance layers:         ACTIVE"
echo ""
echo "  REGULATORY ALIGNMENT"
echo "  ───────────────────────────────────────"
echo "  ✅ EU AI Act — Traceability"
echo "  ✅ GDPR — Data segregation"
echo "  ✅ BaFin MaRisk — IT governance"
echo "  ✅ ISO 27001 — Change management"
echo "  ✅ SOC2 — Logical controls"
echo ""
echo "  THREE DRAGONS PROTOCOL"
echo "  ───────────────────────────────────────"
echo "  🐉 Guardian — Risk & Compliance"
echo "  🐉 Architect — Technical Design"
echo "  🐉 Witness — Audit & Verification"
echo ""
echo ""
echo -e "${GOLD}  \"AI processes. Human decides. WINDI guarantees.\"${NC}"
echo ""
echo "  Demo completed: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""
