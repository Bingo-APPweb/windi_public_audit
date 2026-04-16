#!/bin/bash
# ══════════════════════════════════════════════════════════════
# Fix investor page - Update old domain links to windi-domain.com
# Run with: sudo bash /home/windi/fix-investor-links.sh
# ══════════════════════════════════════════════════════════════

FILE="/var/www/investor/index.html"
BACKUP="/var/www/investor/index.html.bak-links-$(date +%Y%m%d)"

echo "═══════════════════════════════════════════════════════════"
echo "  WINDI Investor Page — Link Migration"
echo "═══════════════════════════════════════════════════════════"

echo ""
echo "📦 Creating backup..."
cp "$FILE" "$BACKUP"

echo "🔧 Fixing links..."

# 2. War Room
sed -i 's|https://admin.windia4desk.tech/war-room/|https://windi-domain.com/war-room/|g' "$FILE"
echo "   ✅ War Room → /war-room/"

# 3. BABEL Editor → WINDI-LAW
sed -i 's|https://admin.windia4desk.tech/clone/|https://windi-domain.com/law/|g' "$FILE"
echo "   ✅ BABEL Editor → /law/"

# 4. Governance API → Keys
sed -i 's|https://admin.windia4desk.tech/api/briefing|https://windi-domain.com/keys/|g' "$FILE"
echo "   ✅ Governance API → /keys/"

# 5. Forensic API → Keys
sed -i 's|https://api.windia4desk.online:8094/api/status|https://windi-domain.com/keys/|g' "$FILE"
echo "   ✅ Forensic API → /keys/"

# 6. Virtue Receipt → Verify Public
sed -i 's|https://admin.windia4desk.tech/api/report/pdf/download?lang=de|https://windi-domain.com/verify-public/|g' "$FILE"
echo "   ✅ Virtue Receipt → /verify-public/"

# 7. Master Landing → Library
sed -i 's|https://master.windia4desk.tech|https://windi-domain.com/library/|g' "$FILE"
echo "   ✅ Master Landing → /library/"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Verification"
echo "═══════════════════════════════════════════════════════════"

echo ""
echo "Old domains remaining:"
grep -c "windia4desk" "$FILE" && echo " references found" || echo "0 - ALL CLEAN ✅"

echo ""
echo "New links:"
grep -o 'href="https://windi-domain.com[^"]*"' "$FILE" | sort -u

echo ""
echo "✅ Done! Backup: $BACKUP"
