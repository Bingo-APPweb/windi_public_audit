#!/bin/bash
echo "═══════════════════════════════════════════════════════════════"
echo "🌐 WINDI i18n FIX v1.0 - DE/EN Priority"
echo "═══════════════════════════════════════════════════════════════"

FILE="/opt/windi/a4desk-editor/a4desk_tiptap_babel.py"
BACKUP="/opt/windi/backups/a4desk_tiptap_babel_pre_i18n_$(date +%Y%m%d_%H%M).py"

echo "📦 Creating backup: $BACKUP"
cp "$FILE" "$BACKUP"

echo ""
echo "🔄 Fixing hardcoded PT strings..."

# Fix 1: Button title - "Enviar documento para revisão" → use JS i18n
sed -i 's/title="Enviar documento para revisão"/title="${t.send_doc_review || '\''Send for review'\''}"/g' "$FILE"

# Fix 2: Button text - "Enviar" → use JS i18n  
sed -i 's/<i class="fas fa-paper-plane"><\/i> Enviar/<i class="fas fa-paper-plane"><\/i> ${t.send || '\''Send'\''}/g' "$FILE"

# Fix 3: Add missing translation keys to all languages
# First check if send_doc_review exists
if ! grep -q "send_doc_review" "$FILE"; then
    echo "   Adding send_doc_review and send keys..."
    
    # Add to EN
    sed -i 's/"en": {"lang_name": "English"/"en": {"lang_name": "English", "send": "Send", "send_doc_review": "Send document for review"/g' "$FILE"
    
    # Add to DE  
    sed -i 's/"de": {"lang_name": "Deutsch"/"de": {"lang_name": "Deutsch", "send": "Senden", "send_doc_review": "Dokument zur Prüfung senden"/g' "$FILE"
    
    # Add to PT
    sed -i 's/"pt": {"lang_name": "Português"/"pt": {"lang_name": "Português", "send": "Enviar", "send_doc_review": "Enviar documento para revisão"/g' "$FILE"
fi

echo "✅ Validating Python syntax..."
python3 -m py_compile "$FILE" 2>/dev/null && echo "   ✅ Syntax OK" || echo "   ❌ Syntax ERROR - rolling back"

if ! python3 -m py_compile "$FILE" 2>/dev/null; then
    cp "$BACKUP" "$FILE"
    echo "   🔙 Rolled back to backup"
    exit 1
fi

echo ""
echo "📊 Changes summary:"
diff "$BACKUP" "$FILE" | grep "^[<>]" | wc -l | xargs echo "   Lines changed:"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🌐 i18n FIX COMPLETE"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "   Rollback: cp $BACKUP $FILE"
echo ""
echo "   Next: Restart a4desk"
echo "   pkill -f 'python3 a4desk_tiptap_babel.py'"
echo "   cd /opt/windi/a4desk-editor && nohup python3 a4desk_tiptap_babel.py > /tmp/a4desk.log 2>&1 &"
