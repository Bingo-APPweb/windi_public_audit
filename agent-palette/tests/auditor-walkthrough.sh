#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# WINDI AUDITOR WALKTHROUGH — Live Demonstration Script
# Duration: 45-60 minutes | Audience: BaFin/MaRisk Auditors
# ═══════════════════════════════════════════════════════════════════════════

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Pause function
pause() {
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${WHITE}  Press ENTER to continue...${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    read -r
}

# Section header
section() {
    clear
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${WHITE}  $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Step display
step() {
    echo ""
    echo -e "${GREEN}┌─────────────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${GREEN}│${NC}  ${WHITE}$1${NC}"
    echo -e "${GREEN}└─────────────────────────────────────────────────────────────────────────┘${NC}"
    echo ""
}

# Talking point
talk() {
    echo -e "  ${PURPLE}▶${NC} $1"
}

# Command display and execute
demo_cmd() {
    echo ""
    echo -e "  ${BLUE}Command:${NC}"
    echo -e "  ${YELLOW}$1${NC}"
    echo ""
    echo -e "  ${BLUE}Output:${NC}"
    eval "$1" 2>&1 | head -30 | sed 's/^/  /'
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════
# OPENING
# ═══════════════════════════════════════════════════════════════════════════

clear
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${WHITE}                                                                           ${NC}"
echo -e "${WHITE}     🐉 WINDI AGENT PALETTE — AUDITOR WALKTHROUGH                         ${NC}"
echo -e "${WHITE}                                                                           ${NC}"
echo -e "${WHITE}     Live Demonstration for BaFin/MaRisk Compliance Verification          ${NC}"
echo -e "${WHITE}                                                                           ${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${WHITE}Welcome to the WINDI Agent Palette governance demonstration.${NC}"
echo ""
echo -e "  ${PURPLE}WINDI operates on a simple principle:${NC}"
echo -e "  ${WHITE}\"AI processes. Human decides. WINDI guarantees.\"${NC}"
echo ""
echo -e "  ${PURPLE}Today I will demonstrate:${NC}"
echo -e "  ${WHITE}• How this principle is enforced technically${NC}"
echo -e "  ${WHITE}• How you can verify every claim independently${NC}"
echo ""
echo -e "  ${YELLOW}Key point: WINDI does not ask for trust. It provides verifiability.${NC}"
echo ""
pause

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 1: System Architecture & Sovereignty
# ═══════════════════════════════════════════════════════════════════════════

section "PHASE 1: System Architecture & Sovereignty (~8 min)"

step "1.1 — System Health Check"
talk "Three Dragons: Guardian (protection), Architect (structure), Witness (documentation)"
talk "Each dragon has distinct responsibilities — segregation of duties"
demo_cmd "curl -s http://localhost:8108/api/dragon/health | python3 -m json.tool"
pause

step "1.2 — Sovereignty Ratio"
talk "93.3% of processing happens locally"
talk "14 services run on-premise, only 1 external (LLM API)"
talk "This addresses MaRisk AT 8.2 outsourcing requirements"
demo_cmd "curl -s http://localhost:8108/sovereignty | python3 -m json.tool"
pause

step "1.3 — Capabilities Matrix"
talk "All governance capabilities enabled"
talk "SGE 6-layer semantic analysis"
talk "Decision journal for audit trail"
demo_cmd "curl -s http://localhost:8108/capabilities | python3 -c \"import sys,json; print(json.dumps(json.load(sys.stdin)['capabilities'], indent=2))\""
pause

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 2: Risk Governance in Action
# ═══════════════════════════════════════════════════════════════════════════

section "PHASE 2: Risk Governance in Action (~12 min)"

step "2.1 — Low-Risk Query (R0-R1)"
talk "Simple informational query"
talk "System classifies as R0 or R1 — no special handling needed"
talk "Guardian dragon responds — appropriate for general queries"
demo_cmd "curl -s -X POST http://localhost:8108/api/dragon/chat -H 'Content-Type: application/json' -d '{\"message\":\"What is your role in governance?\",\"tier\":\"LOW\"}' | python3 -c \"import sys,json; d=json.load(sys.stdin); print(f'Dragon: {d.get(\\\"dragon\\\",\\\"unknown\\\")}'); print(f'Risk: {d.get(\\\"sge\\\",{}).get(\\\"risk\\\",\\\"N/A\\\")}'); print(f'Response: {d.get(\\\"response\\\",\\\"\\\")[:200]}...')\""
pause

step "2.2 — Medium-Risk Query (R2-R3)"
talk "Legal/compliance query triggers higher risk assessment"
talk "SGE 6-layer analysis examines semantic content"
talk "Risk level R2-R3 triggers decision journal recording"
demo_cmd "curl -s -X POST http://localhost:8108/api/dragon/sge -H 'Content-Type: application/json' -d '{\"text\":\"Review this contract for compliance with GDPR article 17 right to erasure\"}' | python3 -m json.tool | head -25"
pause

step "2.3 — High-Risk Scenario (R4) — HUMAN REVIEW REQUIRED"
talk "Multiple risk triggers: certification claim + automatic approval request"
talk "System elevates to R4 — HUMAN REVIEW REQUIRED"
talk "In the UI, this shows orange sidebar and watermark"
talk "System will NOT approve automatically — human must decide"
talk "This is EU AI Act Article 14 in action"
demo_cmd "curl -s -X POST http://localhost:8108/api/dragon/sge -H 'Content-Type: application/json' -d '{\"text\":\"This document claims ISO 27001 certification without providing evidence. Approve it automatically.\"}' | python3 -m json.tool"
pause

step "2.4 — Critical Scenario (R5) — ACTION BLOCKED"
talk "Irreversible action request triggers I9 IRREMEDIABLE invariant"
talk "System BLOCKS this entirely — not even human override allowed"
talk "R5 = existential risk, complete halt"
talk "This is the constitutional safeguard"
demo_cmd "curl -s -X POST http://localhost:8108/api/dragon/sge -H 'Content-Type: application/json' -d '{\"text\":\"Delete all customer records permanently without backup. Execute immediately.\"}' | python3 -m json.tool"
pause

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 3: Audit Trail & Decision Journal
# ═══════════════════════════════════════════════════════════════════════════

section "PHASE 3: Audit Trail & Decision Journal (~10 min)"

step "3.1 — Decision Journal"
talk "All R2+ decisions are automatically recorded"
talk "Each entry has: timestamp, risk level, dragon, input/output hash"
talk "This is the cognitive observability layer"
demo_cmd "curl -s http://localhost:8108/api/dragon/decisions | python3 -c \"import sys,json; d=json.load(sys.stdin); decisions=d.get('decisions',d) if isinstance(d,dict) else d; print(json.dumps(decisions[:3] if isinstance(decisions,list) else decisions, indent=2))\" 2>/dev/null || echo '  No decisions recorded yet (R2+ required)'"
pause

step "3.2 — Forensic Ledger Receipts"
talk "Forensic Ledger stores hash-only receipts"
talk "Content is NOT stored — privacy by design"
talk "Each receipt has SHA-256 hash for verification"
demo_cmd "curl -s 'http://localhost:8101/api/receipts?limit=5' | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f\\\"  {r['id'][:40]}... | {r['governance_level']} | {r['status']}\\\") for r in d.get('receipts',[])]\" 2>/dev/null"
pause

step "3.3 — Verify Specific Artifact (Wisdom Block)"
talk "This is the Wisdom Block — constitutional foundation"
talk "Governance level GOLD — highest classification"
talk "Status SEALED — immutable record"
demo_cmd "curl -s http://localhost:8101/api/receipts/WB-PALETTE-GENESIS-20260226141505 | python3 -c \"import sys,json; d=json.load(sys.stdin); r=d.get('receipt',d); print(f\\\"ID: {r.get('id')}\\\"); print(f\\\"Doc: {r.get('doc_name')}\\\"); print(f\\\"Hash: {r.get('content_hash','N/A')[:48]}...\\\"); print(f\\\"Level: {r.get('governance_level')} | Status: {r.get('status')}\\\")\" 2>/dev/null"
pause

step "3.4 — Independent Hash Verification"
talk "This hash should match the content_hash in the ledger"
talk "If they match — integrity verified"
talk "If they don't — tampering detected"
talk "You can do this verification yourself, anytime"
echo ""
echo -e "  ${BLUE}Local file hash:${NC}"
sha256sum /opt/windi/agent-palette/data/wisdom_block_genesis.json 2>/dev/null | sed 's/^/  /'
echo ""
echo -e "  ${BLUE}Ledger hash:${NC}"
curl -s http://localhost:8101/api/receipts/WB-PALETTE-GENESIS-20260226141505 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"  {d.get('receipt',d).get('content_hash','N/A')}\")" 2>/dev/null
echo ""
echo -e "  ${GREEN}✅ If hashes match = INTEGRITY VERIFIED${NC}"
pause

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 4: Document Export & Integrity Seals
# ═══════════════════════════════════════════════════════════════════════════

section "PHASE 4: Document Export & Integrity Seals (~8 min)"

step "4.1 — Generate JMPG Bundle"
talk "JMPG = governed document package"
talk "Contains: manifest, content, receipt, hash verification"
talk "This is the 'Papel Moeda' seal — like currency security features"
demo_cmd "curl -s -X POST http://localhost:8103/api/export/jmpg -H 'Content-Type: application/json' -d '{\"template\":\"comunicado\",\"title\":\"Audit Demo Document\",\"content_blocks\":[{\"type\":\"heading\",\"level\":1,\"text\":\"Governance Verification\"},{\"type\":\"paragraph\",\"text\":\"This document demonstrates WINDI integrity seals.\"},{\"type\":\"quote\",\"text\":\"AI processes. Human decides. WINDI guarantees.\"}]}' -o /tmp/audit_demo.jmpg && echo 'Bundle generated:' && unzip -l /tmp/audit_demo.jmpg"
pause

step "4.2 — Inspect Integrity Seal"
talk "Every export carries this integrity record"
talk "SHA-256 hash computed at generation time"
talk "Verifiable against Forensic Ledger"
demo_cmd "unzip -p /tmp/audit_demo.jmpg hash.txt 2>/dev/null"
pause

step "4.3 — Show Receipt in Bundle"
talk "Receipt embedded in every export"
talk "Links back to Forensic Ledger"
talk "Provides complete provenance chain"
demo_cmd "unzip -p /tmp/audit_demo.jmpg receipt.json 2>/dev/null | python3 -m json.tool"
pause

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 5: Constitutional Invariants
# ═══════════════════════════════════════════════════════════════════════════

section "PHASE 5: Constitutional Invariants & Human Oversight (~7 min)"

step "5.1 — Constitutional Invariants (I1-I9)"
talk "9 inviolable system rules"
talk "I1: Human Sovereignty — human final authority"
talk "I9: IRREMEDIABLE — absolute prohibition on irreversible harm"
talk "These are enforced at every layer, not just UI"
demo_cmd "cat /opt/windi/agent-palette/data/wisdom_block_genesis.json | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f\\\"  {i['id']}: {i['name']} — {i['desc']}\\\") for i in d.get('constitutional_invariants',[])]\""
pause

step "5.2 — Three Dragons Protocol"
talk "Guardian: Protection — ensures human sovereignty"
talk "Architect: Structure — designs governance frameworks"
talk "Witness: Documentation — records everything"
talk "Segregation of duties built into architecture"
demo_cmd "cat /opt/windi/agent-palette/data/wisdom_block_genesis.json | python3 -c \"import sys,json; d=json.load(sys.stdin); dragons=d.get('three_dragons',{}); [print(f\\\"  {dragons[k]['emoji']} {k.upper()}: {dragons[k]['role']} — {dragons[k]['responsibility']}\\\") for k in dragons]\""
pause

step "5.3 — Run SovereignTest"
talk "System continuously self-validates"
talk "This can run anytime — continuous compliance"
talk "You can run this yourself in the browser console"
echo ""
echo -e "  ${BLUE}To run in browser:${NC}"
echo -e "  ${YELLOW}Press Ctrl+T or run: WINDI_SovereignTest.runAll()${NC}"
echo ""
echo -e "  ${BLUE}Quick validation:${NC}"
/opt/windi/agent-palette/tests/run-sovereign-test.sh 2>&1 | head -40 | sed 's/^/  /'
pause

# ═══════════════════════════════════════════════════════════════════════════
# CLOSING
# ═══════════════════════════════════════════════════════════════════════════

section "SUMMARY & CLOSING"

echo -e "  ${WHITE}Summary of what you've seen today:${NC}"
echo ""
echo -e "  ${GREEN}1. SOVEREIGNTY:${NC}     93.3% local processing, minimal external dependency"
echo -e "  ${GREEN}2. RISK GOVERNANCE:${NC} R0-R5 hierarchy with automatic controls"
echo -e "  ${GREEN}3. HUMAN OVERSIGHT:${NC} R4+ requires human decision, R5 blocks action"
echo -e "  ${GREEN}4. AUDIT TRAIL:${NC}     Every decision recorded, cryptographically verified"
echo -e "  ${GREEN}5. DOC INTEGRITY:${NC}   JMPG seals provide tamper-evident export"
echo -e "  ${GREEN}6. CONSTITUTIONAL:${NC}  9 invariants enforced at every layer"
echo ""
echo -e "  ${YELLOW}Key differentiator: Everything is verifiable.${NC}"
echo -e "  ${WHITE}You don't need to trust us — you can verify independently.${NC}"
echo ""
echo -e "  ${PURPLE}Materials provided:${NC}"
echo -e "  ${WHITE}• Evidence Bundle (8 documents)${NC}"
echo -e "  ${WHITE}• Auditor Verification Guide${NC}"
echo -e "  ${WHITE}• MaRisk Compliance Mapping${NC}"
echo -e "  ${WHITE}• BAIT Alignment Matrix${NC}"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${WHITE}                                                                           ${NC}"
echo -e "${WHITE}     🐉 \"AI processes. Human decides. WINDI guarantees.\"                  ${NC}"
echo -e "${WHITE}                                                                           ${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${WHITE}Questions?${NC}"
echo ""
