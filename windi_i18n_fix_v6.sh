#!/bin/bash
echo "=== WINDI i18n FIX v6.0 - Pass lang to Agent ==="

FILE="/opt/windi/a4desk-editor/a4desk_tiptap_babel.py"
BACKUP="/opt/windi/backups/a4desk_tiptap_babel_pre_i18n_v6_$(date +%Y%m%d_%H%M).py"

echo "Backup: $BACKUP"
cp "$FILE" "$BACKUP"

echo "Step 1: Adding lang to frontend fetch..."
sed -i "s/dragon: 'claude'/dragon: 'claude', lang: currentLang/g" "$FILE"

echo "Step 2: Pass lang to Gateway in backend..."
# Find the gateway call and add lang
sed -i 's/"dragon": dragon/"dragon": dragon, "lang": data.get("lang", "de")/g' "$FILE"

echo "Validating..."
if python3 -m py_compile "$FILE" 2>/dev/null; then
    echo "OK"
else
    echo "ERROR - rollback"
    cp "$BACKUP" "$FILE"
    exit 1
fi

echo "Changes:"
diff "$BACKUP" "$FILE"

echo ""
echo "Done! Rollback: cp $BACKUP $FILE"
