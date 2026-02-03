#!/bin/bash
echo "=== WINDI i18n FIX v4.0 - Chat Messages ==="

FILE="/opt/windi/a4desk-editor/a4desk_tiptap_babel.py"
BACKUP="/opt/windi/backups/a4desk_tiptap_babel_pre_i18n_v4_$(date +%Y%m%d_%H%M).py"

echo "Backup: $BACKUP"
cp "$FILE" "$BACKUP"

echo "Fixing chat welcome message..."
sed -i 's/Olá! Sou o WINDI LLM. Como posso ajudar com seu documento hoje?/Hello! I am WINDI LLM. How can I help with your document today?/g' "$FILE"

echo "Fixing thinking message..."
sed -i 's/Pensando\.\.\./Thinking.../g' "$FILE"

echo "Validating..."
if python3 -m py_compile "$FILE" 2>/dev/null; then
    echo "OK - Changes:"
    diff "$BACKUP" "$FILE"
else
    echo "ERROR - rollback"
    cp "$BACKUP" "$FILE"
    exit 1
fi

echo "Done! Rollback: cp $BACKUP $FILE"
