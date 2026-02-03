#!/bin/bash
echo "=== WINDI i18n FIX v3.0 ==="

FILE="/opt/windi/a4desk-editor/a4desk_tiptap_babel.py"
BACKUP="/opt/windi/backups/a4desk_tiptap_babel_pre_i18n_$(date +%Y%m%d_%H%M).py"

echo "Backup: $BACKUP"
cp "$FILE" "$BACKUP"

echo "Fixing hardcoded PT..."

# Fix placeholder
sed -i 's/Digite sua mensagem... (Enter para enviar, Shift+Enter para nova linha)/Type your message.../g' "$FILE"

# Fix title
sed -i 's/Enviar documento para revisão/Send document for review/g' "$FILE"

# Fix button text
sed -i 's/fa-paper-plane"><\/i> Enviar/fa-paper-plane"><\/i> Send/g' "$FILE"

echo "Validating..."
if python3 -m py_compile "$FILE" 2>/dev/null; then
    echo "OK"
    echo "Changes:"
    diff "$BACKUP" "$FILE"
else
    echo "ERROR - rollback"
    cp "$BACKUP" "$FILE"
    exit 1
fi

echo "Done! Rollback: cp $BACKUP $FILE"
