#!/bin/bash
echo "=== Fix content handling ==="

FILE="/opt/windi/a4desk-editor/a4desk_tiptap_babel.py"
BACKUP="/opt/windi/backups/a4desk_tiptap_babel_pre_content_fix_$(date +%Y%m%d_%H%M).py"

cp "$FILE" "$BACKUP"
echo "Backup: $BACKUP"

# Fix: handle both string and dict for content
sed -i 's/content_data = data.get('\''content'\'', {})/content_data = data.get('\''content'\'', {})\n    if isinstance(content_data, str):\n        content_data = {"text": content_data, "html": ""}/g' "$FILE"

if python3 -m py_compile "$FILE" 2>/dev/null; then
    echo "OK"
    diff "$BACKUP" "$FILE"
else
    echo "ERROR - rollback"
    cp "$BACKUP" "$FILE"
fi
