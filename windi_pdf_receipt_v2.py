#!/usr/bin/env python3
"""
Add dynamic WINDI-RECEIPT + QRCode to PDF export
"""

FILE = "/opt/windi/a4desk-editor/a4desk_tiptap_babel.py"

with open(FILE, 'r') as f:
    content = f.read()

# Find and replace the export_document function's HTML template
old_html_start = '''    body_html = content_html if content_html else text.replace(chr(10), '<br>')
    html_content = f"""<!DOCTYPE html>'''

new_html_start = '''    body_html = content_html if content_html else text.replace(chr(10), '<br>')
    
    # Get receipt for footer
    receipt_data = json.loads(row["receipt"]) if row["receipt"] else None
    receipt_id = receipt_data.get("receipt_id", doc_id) if receipt_data else doc_id
    receipt_hash = receipt_data.get("hash", "---") if receipt_data else "---"
    receipt_ts = receipt_data.get("timestamp", "---")[:19] if receipt_data else "---"
    doc_status = row["status"].upper()
    
    # Generate QR code
    qr_data = f"WINDI:{receipt_id}|{receipt_hash}"
    qr_base64 = generate_qr_base64(qr_data)
    
    html_content = f"""<!DOCTYPE html>'''

if old_html_start in content:
    content = content.replace(old_html_start, new_html_start)
    print("✅ Added receipt/QR logic")

# Replace footer
old_footer = '''<div class="footer" style="margin-top: 40pt; border-top: 2pt solid #0d9488; padding-top: 15pt;"><div style="font-size: 10pt; color: #0d9488; font-weight: bold;">WINDI Publishing House</div><div style="font-size: 8pt; color: #64748b; margin-top: 4pt;">KI verarbeitet. Mensch entscheidet. WINDI garantiert.</div></div>'''

new_footer = '''<div class="footer" style="margin-top: 40pt; border-top: 2pt solid #0d9488; padding-top: 15pt; display: flex; justify-content: space-between; align-items: flex-start;">
        <div style="flex: 1;">
            <div style="font-size: 10pt; color: #0d9488; font-weight: bold;">🏛️ WINDI Publishing House</div>
            <div style="font-size: 8pt; color: #64748b; margin-top: 4pt;">KI verarbeitet. Mensch entscheidet. WINDI garantiert.</div>
            <div style="font-size: 8pt; color: #1e293b; margin-top: 8pt; font-family: monospace;">
                <strong>WINDI-RECEIPT:</strong> {receipt_id}<br/>
                <strong>Hash:</strong> {receipt_hash}<br/>
                <strong>Status:</strong> {doc_status}
            </div>
        </div>
        <div style="text-align: right;">
            <img src="data:image/png;base64,{qr_base64}" style="width: 60px; height: 60px;"/>
            <div style="font-size: 7pt; color: #64748b; margin-top: 2pt;">Scan to verify</div>
        </div>
    </div>'''

if old_footer in content:
    content = content.replace(old_footer, new_footer)
    print("✅ Updated footer with receipt + QR")

with open(FILE, 'w') as f:
    f.write(content)

# Validate
import subprocess
result = subprocess.run(['python3', '-m', 'py_compile', FILE], capture_output=True)
if result.returncode == 0:
    print("✅ Syntax OK")
else:
    print(f"❌ Syntax ERROR: {result.stderr.decode()}")
    # Rollback
    import shutil
    shutil.copy("/opt/windi/backups/a4desk_tiptap_babel_pre_qr.py", FILE)
    print("🔙 Rolled back")

print("Done!")
