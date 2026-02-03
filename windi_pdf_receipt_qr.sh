#!/bin/bash
echo "=== WINDI PDF Receipt + QRCode ==="

FILE="/opt/windi/a4desk-editor/a4desk_tiptap_babel.py"
BACKUP="/opt/windi/backups/a4desk_tiptap_babel_pre_qr_$(date +%Y%m%d_%H%M).py"

cp "$FILE" "$BACKUP"
echo "Backup: $BACKUP"

# Primeiro, vamos ver a estrutura atual
echo ""
echo "Checking current imports..."
grep -n "^import\|^from" "$FILE" | head -20

echo ""
echo "Adding qrcode import and function..."
