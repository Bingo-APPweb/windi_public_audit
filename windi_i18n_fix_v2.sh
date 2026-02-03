#!/bin/bash
echo "═══════════════════════════════════════════════════════════════"
echo "🌐 WINDI i18n FIX v2.0 - DE/EN Priority"
echo "═══════════════════════════════════════════════════════════════"

FILE="/opt/windi/a4desk-editor/a4desk_tiptap_babel.py"
BACKUP="/opt/windi/backups/a4desk_tiptap_babel_pre_i18n_$(date +%Y%m%d_%H%M).py"

echo "📦 Creating backup: $BACKUP"
cp "$FILE" "$BACKUP"

echo ""
echo "🔄 Step 1: Fix HTML elements with data attributes..."

# Fix placeholder - add data-i18n attribute
sed -i 's/placeholder="Digite sua mensagem... (Enter para enviar, Shift+Enter para nova linha)"/placeholder="Type your message..." data-i18n-placeholder="chat_placeholder"/g' "$FILE"

# Fix send doc button title
sed -i 's/title="Enviar documento para revisão"/title="Send document for review" data-i18n-title="send_doc_title"/g' "$FILE"

# Fix send button text - change to use span with data attribute
sed -i 's/<i class="fas fa-paper-plane"><\/i> Enviar/<i class="fas fa-paper-plane"><\/i> <span data-i18n="send">Send<\/span>/g' "$FILE"

echo "🔄 Step 2: Add translation keys to JS object..."

# Add keys to EN section (before delete: 'Delete')
sed -i "/delete: 'Delete', to_chat: 'Chat', confirm_delete: 'Delete this document\?',/c\\        delete: 'Delete', to_chat: 'Chat', confirm_delete: 'Delete this document?',\\n        send: 'Send', send_doc_title: 'Send document for review', chat_placeholder: 'Type your message... (Enter to send, Shift+Enter for new line)'," "$FILE"

# Add keys to DE section (before delete: 'Löschen')  
sed -i "/delete: 'Löschen', to_chat: 'Chat', confirm_delete: 'Dieses Dokument löschen\?',/c\\        delete: 'Löschen', to_chat: 'Chat', confirm_delete: 'Dieses Dokument löschen?',\\n        send: 'Senden', send_doc_title: 'Dokument zur Prüfung senden', chat_placeholder: 'Nachricht eingeben... (Enter zum Senden, Shift+Enter für neue Zeile)'," "$FILE"

# Add keys to PT section (before delete: 'Apagar')
sed -i "/delete: 'Apagar', to_chat: 'Chat', confirm_delete: 'Apagar este documento\?',/c\\        delete: 'Apagar', to_chat: 'Chat', confirm_delete: 'Apagar este documento?',\\n        send: 'Enviar', send_doc_title: 'Enviar documento para revisão', chat_placeholder: 'Digite sua mensagem... (Enter para enviar, Shift+Enter para nova linha)'," "$FILE"

echo "✅ Validating Python syntax..."
if python3 -m py_compile "$FILE" 2>/dev/null; then
    echo "   ✅ Syntax OK"
else
    echo "   ❌ Syntax ERROR - rolling back"
    cp "$BACKUP" "$FILE"
    exit 1
fi

echo ""
echo "📊 Changes:"
diff "$BACKUP" "$FILE" | head -30

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🌐 i18n FIX v2.0 COMPLETE"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Rollback: cp $BACKUP $FILE"
echo ""
echo "Next steps:"
echo "1. pkill -9 -f a4desk"
echo "2. cd /opt/windi/a4desk-editor && nohup python3 a4desk_tiptap_babel.py > /tmp/a4desk.log 2>&1 &"
