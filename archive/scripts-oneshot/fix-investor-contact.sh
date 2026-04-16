#!/bin/bash
# Fix investor page contact info
# Run with: sudo bash /home/windi/fix-investor-contact.sh

FILE="/var/www/investor/index.html"
BACKUP="/var/www/investor/index.html.bak-$(date +%Y%m%d)"

echo "Backing up to $BACKUP..."
cp "$FILE" "$BACKUP"

echo "Fixing contact email..."
sed -i 's/&#x1F310; master\.windia4desk\.tech/\&#x2709;\&#xFE0F; jober@a4desk.de/' "$FILE"

echo "Verifying fix..."
grep -n "jober@a4desk.de" "$FILE" && echo "✅ Contact fixed!" || echo "❌ Fix failed"
