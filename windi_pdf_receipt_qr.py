#!/usr/bin/env python3
"""
Script para adicionar WINDI-RECEIPT + QRCode ao PDF export
"""
import re

FILE = "/opt/windi/a4desk-editor/a4desk_tiptap_babel.py"
BACKUP = "/opt/windi/backups/a4desk_tiptap_babel_pre_qr.py"

# Read file
with open(FILE, 'r') as f:
    content = f.read()

# Backup
with open(BACKUP, 'w') as f:
    f.write(content)
print(f"Backup: {BACKUP}")

# 1. Add imports after "import tempfile"
if "import qrcode" not in content:
    content = content.replace(
        "import tempfile",
        "import tempfile\nimport base64\nfrom io import BytesIO\nimport qrcode"
    )
    print("✅ Added imports")

# 2. Add QR generation function after make_receipt
qr_function = '''
def generate_qr_base64(data: str) -> str:
    """Generate QR code as base64 for HTML embedding"""
    qr = qrcode.QRCode(version=1, box_size=4, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()

'''

if "def generate_qr_base64" not in content:
    # Insert after make_receipt function
    insert_pos = content.find("# ============================================================================\n# API - DOCUMENTOS")
    if insert_pos > 0:
        content = content[:insert_pos] + qr_function + content[insert_pos:]
        print("✅ Added generate_qr_base64 function")

# 3. Modify the footer in export_document
old_footer = '<div class="footer">WINDI Publishing House</div>'
new_footer_template = '''<div class="footer" style="display: flex; justify-content: space-between; align-items: center; margin-top: 40pt; border-top: 2pt solid #0d9488; padding-top: 15pt;">
        <div style="flex: 1;">
            <div style="font-size: 10pt; color: #0d9488; font-weight: bold;">WINDI Publishing House</div>
            <div style="font-size: 8pt; color: #64748b; margin-top: 4pt;">KI verarbeitet. Mensch entscheidet. WINDI garantiert.</div>
        </div>
        <div style="text-align: right; font-size: 8pt; color: #64748b;">
            <div>📋 {doc_id}</div>
            <div>🕐 {timestamp}</div>
        </div>
    </div>'''

# For now, just update the static footer - dynamic will need more work
if 'WINDI Publishing House</div>\n</body>' in content:
    content = content.replace(
        '<div class="footer">WINDI Publishing House</div>',
        '<div class="footer" style="margin-top: 40pt; border-top: 2pt solid #0d9488; padding-top: 15pt;">'
        '<div style="font-size: 10pt; color: #0d9488; font-weight: bold;">WINDI Publishing House</div>'
        '<div style="font-size: 8pt; color: #64748b; margin-top: 4pt;">KI verarbeitet. Mensch entscheidet. WINDI garantiert.</div>'
        '</div>'
    )
    print("✅ Updated footer style")

# Write back
with open(FILE, 'w') as f:
    f.write(content)

# Validate
import subprocess
result = subprocess.run(['python3', '-m', 'py_compile', FILE], capture_output=True)
if result.returncode == 0:
    print("✅ Syntax OK")
else:
    print("❌ Syntax ERROR - rolling back")
    with open(BACKUP, 'r') as f:
        content = f.read()
    with open(FILE, 'w') as f:
        f.write(content)

print("Done!")
