#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# 🐉 WINDI Three Dragons — sqlite3.Row → dict() Fix
# Bug: sqlite3.Row is read-only; communique["receipt_id"] = ... fails silently
# Fix: Convert to mutable dict at function entry
# Date: 18 Feb 2026
# ═══════════════════════════════════════════════════════════════════

set -e
echo "🐉 Three Dragons: sqlite3.Row Mutability Fix"
echo "═══════════════════════════════════════════════"

# ── Step 1: Backup ────────────────────────────────────────────────
BK="/opt/windi/backups/pre_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BK"
cp /opt/windi/communique/communique_publisher.py "$BK/"
echo "✅ Backup: $BK/communique_publisher.py"

# ── Step 2: Apply Patch (anchored to publish_communique function) ─
python3 << 'PATCH'
from pathlib import Path

p = Path("/opt/windi/communique/communique_publisher.py")
code = p.read_text()

# Anchor: only patch inside publish_communique()
needle_func = "def publish_communique("
i = code.find(needle_func)
if i == -1:
    raise SystemExit("❌ publish_communique() not found in publisher")

head = code[:i]
tail = code[i:]

old = '    com_id = communique["id"]'
new = '    communique = dict(communique)  # Three Dragons: ensure mutable dict (sqlite3.Row is read-only!)\n    com_id = communique["id"]'

if "communique = dict(communique)" in tail:
    print("⚠️  Patch already applied — skipping")
    raise SystemExit(0)

if old not in tail:
    raise SystemExit("❌ Pattern 'com_id = communique[\"id\"]' not found inside publish_communique()")

tail2 = tail.replace(old, new, 1)
p.write_text(head + tail2)
print("✅ Patch applied: communique = dict(communique) at start of publish_communique()")
PATCH

# ── Step 3: Restart service ──────────────────────────────────────
echo ""
echo "🔄 Restarting windi-communique..."
sudo systemctl restart windi-communique
sleep 2
sudo systemctl is-active windi-communique && echo "✅ Service active" || echo "❌ Service failed!"
sudo journalctl -u windi-communique -n 10 --no-pager

# ── Step 4: Smoke Test — Create → Review → Publish ──────────────
echo ""
echo "🔥 Smoke Test: Full Pipeline"
echo "─────────────────────────────"

COM=$(curl -s -X POST http://127.0.0.1:8105/api/communique/create \
  -H "Content-Type: application/json" \
  -d '{"title_de":"RECEIPT ROW FIX","title_en":"RECEIPT ROW FIX","body_de":"Testing sqlite3.Row dict conversion","body_en":"Testing sqlite3.Row dict conversion","author_name":"Dragon","author_role":"Guardian","impact_level":"HIGH"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('id','FAIL'))")

if [ "$COM" = "FAIL" ] || [ -z "$COM" ]; then
    echo "❌ Create failed"
    exit 1
fi
echo "📄 Created: $COM"

# Review
curl -s -X POST "http://127.0.0.1:8105/api/communique/$COM/review" \
  -H "Content-Type: application/json" -d '{}' > /dev/null
echo "📋 Reviewed"

# Publish
PUBLISH_RESULT=$(curl -s -X POST "http://127.0.0.1:8105/api/communique/$COM/publish" \
  -H "Content-Type: application/json" -d '{"approved_by":"Dragon"}')
echo "📬 Publish response: $PUBLISH_RESULT"

# ── Step 5: Verify Receipt in PDF ────────────────────────────────
echo ""
echo "🔍 PDF Verification"
echo "─────────────────────"
PDF="/opt/windi/communique/published/$COM/communique.pdf"

if [ -f "$PDF" ]; then
    echo "✅ PDF exists: $(stat --printf='%s bytes, modified %y' "$PDF")"
    
    # Try pdftotext first, fall back to strings
    if command -v pdftotext &>/dev/null; then
        echo "── pdftotext output ──"
        pdftotext "$PDF" - 2>/dev/null | grep -i "receipt" | head -5
    fi
    
    echo "── strings output ──"
    strings "$PDF" | grep -i "receipt" | head -5
    
    echo "── VR- pattern ──"
    strings "$PDF" | grep -o "VR-COM-[a-f0-9]*" | head -3
else
    echo "❌ PDF not found at $PDF"
    echo "   Checking alternative paths..."
    find /opt/windi/communique/ -name "*.pdf" -newer "$BK" 2>/dev/null | head -5
fi

# ── Step 6: Cross-check Ledger ───────────────────────────────────
echo ""
echo "🛡️ Ledger Cross-Check"
echo "──────────────────────"
curl -s "http://127.0.0.1:8101/api/receipts?search=$COM&limit=3" 2>/dev/null \
  | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    receipts = data.get('receipts', data if isinstance(data, list) else [])
    for r in receipts[:3]:
        rid = r.get('receipt_id', r.get('id', '?'))
        doc = r.get('doc_name', r.get('document_name', '?'))
        print(f'  📜 {rid} — {doc}')
    if not receipts:
        print('  ⚠️  No receipts found for this COM ID')
except:
    print('  ⚠️  Could not parse ledger response')
" 2>/dev/null

echo ""
echo "═══════════════════════════════════════════════"
echo "🐉 Test ID: $COM"
echo "═══════════════════════════════════════════════"
echo ""
echo "If Receipt shows VR-COM-xxx → 🎉 sqlite3.Row was the ghost!"
echo "If Receipt shows None       → bug is in generate_pdf (next target)"
