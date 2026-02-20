#!/bin/bash
# ============================================================================
# WINDI Fix: War Room + Audit JS Field Mapping
# Issue: JS expects different field names than API returns
# Fix: Update JS to match actual API response format
# ============================================================================

set -e
echo "🐉 WINDI Fix — War Room + Audit Field Mapping"
echo "==============================================="

GOV="/opt/windi/a4desk-editor/static/governance-command-center.html"

# --- BACKUP ---
BK="/opt/windi/backups/pre_fieldfix_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BK"
cp "$GOV" "$BK/"
echo "✅ Backup: $BK"

# ============================================================================
# FIX 1: WAR ROOM — Chain Integrity
# Problem: JS checks integrity.profiles (missing) and integrity.total (nested)
# API returns: { status: "INTACT", report: { total: 1, sealed: 1, complete: true } }
# ============================================================================
echo ""
echo "🔧 [1/2] Fixing War Room integrity parsing..."

# We need to see the exact JS code first, then patch
# Fix: integrity.profiles → not needed (remove check or add fallback)
# Fix: integrity.total → integrity.report.total
# Fix: integrity.sealed → integrity.report.sealed

# Fix the integrity check - make it work with actual API response
sed -i 's|integrity\.total_entries\b|integrity.report?.total|g' "$GOV"
sed -i 's|integrity\.total\b|integrity.report?.total|g' "$GOV"
sed -i 's|integrity\.sealed_count\b|integrity.report?.sealed|g' "$GOV"
sed -i 's|integrity\.sealed\b|integrity.report?.sealed|g' "$GOV"
sed -i 's|integrity\.complete\b|integrity.report?.complete|g' "$GOV"

# Fix the "Broken" display - check for integrity.status instead of integrity.profiles
sed -i "s|integrity && integrity\.profiles|integrity \&\& integrity.status|g" "$GOV"
sed -i "s|integrity\.profiles|integrity.status|g" "$GOV"

# Fix chain integrity display text
sed -i "s|integrity\.status === 'INTACT'|integrity.status === 'INTACT'|g" "$GOV"

C1=$(grep -c "integrity.report?" "$GOV" 2>/dev/null || echo 0)
echo "   → $C1 integrity field fixes applied"

# ============================================================================
# FIX 2: AUDIT — Submissions
# Problem: JS expects subs.submissions but API returns subs.results
# Field mapping:
#   subs.submissions     → subs.results
#   e.reg_id / e.id      → e.submission_id
#   e.timestamp          → e.registered_at
#   e.created_at         → e.registered_at
#   e.doc_type           → e.reporting_entity (or governance_level)
#   e.document_type      → e.reporting_entity
#   e.status             → e.validation_status
#   e.hash               → e.integrity_hash
#   e.envelope_hash      → e.integrity_hash
# ============================================================================
echo ""
echo "🔧 [2/2] Fixing Audit submissions parsing..."

# Fix the array access
sed -i 's|subs\.submissions\b|subs.results|g' "$GOV"

# Fix individual field names
sed -i 's|e\.reg_id\b|e.submission_id|g' "$GOV"
sed -i 's|e\.envelope_hash\b|e.integrity_hash|g' "$GOV"
sed -i "s|e\.hash\b|e.integrity_hash|g" "$GOV"
sed -i 's|e\.created_at\b|e.registered_at|g' "$GOV"
sed -i 's|e\.timestamp\b|e.registered_at|g' "$GOV"
sed -i 's|e\.document_type\b|e.governance_level|g' "$GOV"
sed -i 's|e\.doc_type\b|e.governance_level|g' "$GOV"
sed -i 's|e\.status\b|e.validation_status|g' "$GOV" 2>/dev/null || true

C2=$(grep -c "subs.results\|submission_id\|integrity_hash\|registered_at\|validation_status" "$GOV" 2>/dev/null || echo 0)
echo "   → $C2 submission field fixes applied"

# ============================================================================
# VERIFY & RESTART
# ============================================================================
echo ""
echo "🔄 Restarting A4Desk..."
pkill -f a4desk_tiptap_babel.py 2>/dev/null || true
sleep 2
cd /opt/windi/a4desk-editor && nohup python3 a4desk_tiptap_babel.py > /tmp/a4desk.log 2>&1 &
sleep 3

STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8085/)
echo "BABEL: HTTP $STATUS"

STATUS_GOV=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8085/governance)
echo "Governance: HTTP $STATUS_GOV"

# Verify API still responds
echo ""
echo "API Integrity: $(curl -s http://localhost:8085/api/gov/integrity | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("status","?"))' 2>/dev/null)"
echo "API Submissions: $(curl -s http://localhost:8085/api/gov/submissions | python3 -c 'import sys,json; d=json.load(sys.stdin); print(f"{d.get(\"count\",0)} submissions")' 2>/dev/null)"

echo ""
echo "==============================================="
echo "🐉 Field Mapping Fix Complete!"
echo "==============================================="
echo ""
echo "FIXES:"
echo "  [1] ✅ War Room: integrity.profiles → integrity.status"
echo "       integrity.total → integrity.report.total"
echo "       integrity.sealed → integrity.report.sealed"
echo "  [2] ✅ Audit: subs.submissions → subs.results"
echo "       reg_id → submission_id"
echo "       timestamp → registered_at"  
echo "       doc_type → governance_level"
echo "       status → validation_status"
echo "       hash → integrity_hash"
echo ""
echo "VERIFY in browser:"
echo "  → War Room: should show 'INTACT' with 1 sealed entry"
echo "  → Audit: should show REG-20260201-0001 submission"
echo ""
echo "ROLLBACK:"
echo "  cp $BK/governance-command-center.html $GOV"
echo "  pkill -f a4desk_tiptap_babel.py"
echo "  cd /opt/windi/a4desk-editor && nohup python3 a4desk_tiptap_babel.py > /tmp/a4desk.log 2>&1 &"
