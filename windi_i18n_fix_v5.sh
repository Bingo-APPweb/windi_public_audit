#!/bin/bash
echo "=== WINDI i18n FIX v5.0 - Dynamic Translation ==="

FILE="/opt/windi/a4desk-editor/a4desk_tiptap_babel.py"
BACKUP="/opt/windi/backups/a4desk_tiptap_babel_pre_i18n_v5_$(date +%Y%m%d_%H%M).py"

echo "Backup: $BACKUP"
cp "$FILE" "$BACKUP"

echo "Step 1: Adding translation keys to DE..."
sed -i "s/chat_context: 'Bitte dieses Dokument überarbeiten:'/chat_context: 'Bitte dieses Dokument überarbeiten:', send: 'Senden', chat_placeholder: 'Nachricht eingeben... (Enter zum Senden, Shift+Enter für neue Zeile)', welcome: 'Hallo! Ich bin WINDI LLM. Wie kann ich Ihnen mit Ihrem Dokument helfen?', thinking: 'Denke nach...'/g" "$FILE"

echo "Step 2: Adding translation keys to EN..."
sed -i "s/chat_context: 'Please revise this document:', send: 'Send', chat_placeholder: 'Type your message... (Enter to send, Shift+Enter for new line)'/chat_context: 'Please revise this document:', send: 'Send', chat_placeholder: 'Type your message... (Enter to send, Shift+Enter for new line)', welcome: 'Hello! I am WINDI LLM. How can I help with your document today?', thinking: 'Thinking...'/g" "$FILE"

echo "Step 3: Adding translation keys to PT..."
sed -i "s/chat_context: 'Por favor revise este documento:', send: 'Enviar', chat_placeholder: 'Type your message...'/chat_context: 'Por favor revise este documento:', send: 'Enviar', chat_placeholder: 'Digite sua mensagem... (Enter para enviar, Shift+Enter para nova linha)', welcome: 'Olá! Sou o WINDI LLM. Como posso ajudar com seu documento hoje?', thinking: 'Pensando...'/g" "$FILE"

echo "Step 4: Making welcome message dynamic..."
sed -i 's|Hello! I am WINDI LLM. How can I help with your document today?|<span data-t="welcome">Hello! I am WINDI LLM. How can I help with your document today?</span>|g' "$FILE"

echo "Step 5: Making thinking message dynamic..."
sed -i "s|Thinking\.\.\.</div>|<span data-t=\"thinking\">Thinking...</span></div>|g" "$FILE"

echo "Validating..."
if python3 -m py_compile "$FILE" 2>/dev/null; then
    echo "OK"
else
    echo "ERROR - rollback"
    cp "$BACKUP" "$FILE"
    exit 1
fi

echo ""
echo "Changes:"
diff "$BACKUP" "$FILE"

echo ""
echo "Done! Rollback: cp $BACKUP $FILE"
