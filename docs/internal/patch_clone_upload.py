#!/usr/bin/env python3
"""
WINDI Clone — PDF/DOCX Upload Fix
Fixes: hFile() doesn't extract text from PDF/DOCX files

Two parts:
  1. Adds /api/extract endpoint to clone_server.py
  2. Patches the landing page JS hFile() function

Usage on Strato:
  pip install PyPDF2 --break-system-packages
  python3 /opt/windi/docs/internal/patch_clone_upload.py
  # Then restart clone-app
"""

import os
import sys

# ═══════════════════════════════════════════════════════════════
# PART 1: Add /api/extract endpoint to clone_server.py
# ═══════════════════════════════════════════════════════════════

CLONE_SERVER = '/opt/windi/clone-app/clone_server.py'

if not os.path.exists(CLONE_SERVER):
    print(f"❌ Not found: {CLONE_SERVER}")
    sys.exit(1)

with open(CLONE_SERVER, 'r', encoding='utf-8') as f:
    server_content = f.read()

# Add imports at the top (after existing imports)
import_block = """import tempfile
import io
"""

# Find the right place to add imports — after the last 'import' or 'from' line
if 'import tempfile' not in server_content:
    # Add after "from flask import"
    if 'from flask import' in server_content:
        flask_import_line = server_content.split('\n')
        for i, line in enumerate(flask_import_line):
            if line.startswith('from flask import') or line.startswith('import requests'):
                last_import_idx = i
        # Insert after last import
        flask_import_line.insert(last_import_idx + 1, import_block)
        server_content = '\n'.join(flask_import_line)
        print("  ✅ Added tempfile/io imports")

# Add the extract endpoint BEFORE the proxy catch-all route
extract_endpoint = '''
# ═══ WINDI FILE EXTRACT — PDF/DOCX text extraction ═══
@app.route("/api/extract", methods=["POST"])
def extract_text():
    """Extract text from uploaded PDF/DOCX files for analysis"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    f = request.files['file']
    filename = f.filename.lower() if f.filename else ''

    try:
        if filename.endswith('.pdf'):
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(io.BytesIO(f.read()))
                text = '\\n'.join(page.extract_text() or '' for page in reader.pages)
            except ImportError:
                return jsonify({"error": "PDF support not installed. Run: pip install PyPDF2 --break-system-packages"}), 500

        elif filename.endswith('.docx') or filename.endswith('.doc'):
            try:
                import docx
                doc = docx.Document(io.BytesIO(f.read()))
                text = '\\n'.join(para.text for para in doc.paragraphs if para.text.strip())
            except ImportError:
                return jsonify({"error": "DOCX support not installed"}), 500

        elif filename.endswith('.txt') or filename.endswith('.md') or filename.endswith('.rtf'):
            text = f.read().decode('utf-8', errors='replace')

        else:
            return jsonify({"error": f"Unsupported format: {filename}"}), 400

        text = text.strip()
        if not text:
            return jsonify({"error": "No text could be extracted from file"}), 400

        return jsonify({
            "success": True,
            "text": text,
            "filename": f.filename,
            "chars": len(text),
            "source": "windi-extract"
        })

    except Exception as e:
        return jsonify({"error": f"Extraction failed: {str(e)}"}), 500

'''

# Insert BEFORE the proxy catch-all route
proxy_marker = '@app.route("/api/<path:subpath>"'
if proxy_marker in server_content and '/api/extract' not in server_content:
    server_content = server_content.replace(proxy_marker, extract_endpoint + proxy_marker)
    print("  ✅ Added /api/extract endpoint (before proxy catch-all)")
elif '/api/extract' in server_content:
    print("  ℹ️  /api/extract already exists — skipping")
else:
    print("  ❌ Could not find proxy route marker — add endpoint manually")

# Write updated server
with open(CLONE_SERVER, 'w', encoding='utf-8') as f:
    f.write(server_content)
print(f"  📁 Updated: {CLONE_SERVER}")

# ═══════════════════════════════════════════════════════════════
# PART 2: Patch the landing page hFile() in the HTML
# ═══════════════════════════════════════════════════════════════

# The landing page is served by the index() route — need to find where the HTML lives
# It could be inline in clone_server.py or in a template file
# Let's check both options

# First, find the HTML source
import subprocess
result = subprocess.run(['grep', '-rn', 'async function hFile', '/opt/windi/clone-app/'],
                       capture_output=True, text=True)
html_files = result.stdout.strip().split('\n') if result.stdout.strip() else []

# Also check static files
result2 = subprocess.run(['grep', '-rn', 'async function hFile', '/opt/windi/a4desk-editor/static/'],
                        capture_output=True, text=True)
if result2.stdout.strip():
    html_files.extend(result2.stdout.strip().split('\n'))

# Also check if index() returns a rendered template or inline HTML
result3 = subprocess.run(['grep', '-A5', 'def index', CLONE_SERVER],
                        capture_output=True, text=True)
print(f"\n  ℹ️  index() function:\n{result3.stdout}")

print(f"\n  ℹ️  Files containing hFile: {len(html_files)}")
for hf in html_files:
    print(f"    {hf[:100]}")

# Now patch each file that contains the old hFile
old_hFile = '''async function hFile(f){
  if(!f)return;
  if(f.name.endsWith('.txt')||f.name.endsWith('.md')){
    document.getElementById('dt').value=await f.text();
    document.getElementById('tw').classList.add('op');
    scan();
  } else {
    document.getElementById('tw').classList.add('op');
    document.getElementById('dt').focus();
  }
}'''

new_hFile = '''async function hFile(f){
  if(!f)return;
  const dt=document.getElementById('dt');
  const tw=document.getElementById('tw');
  tw.classList.add('op');
  if(f.name.endsWith('.txt')||f.name.endsWith('.md')){
    dt.value=await f.text();
    scan();
  } else if(f.name.endsWith('.pdf')||f.name.endsWith('.docx')||f.name.endsWith('.doc')||f.name.endsWith('.rtf')){
    dt.value='⏳ Dokument wird analysiert...';
    dt.disabled=true;
    try{
      const fd=new FormData();
      fd.append('file',f);
      const res=await fetch('/api/extract',{method:'POST',body:fd});
      const data=await res.json();
      if(data.success&&data.text){
        dt.value=data.text;
        dt.disabled=false;
        scan();
      }else{
        dt.value='';
        dt.disabled=false;
        dt.placeholder=data.error||'Extraktion fehlgeschlagen — Text manuell einfügen';
        dt.focus();
      }
    }catch(e){
      dt.value='';
      dt.disabled=false;
      dt.placeholder='Server nicht erreichbar — Text manuell einfügen';
      dt.focus();
    }
  } else {
    dt.focus();
  }
}'''

files_patched = 0

# Search all potential files
for search_dir in ['/opt/windi/clone-app/', '/opt/windi/a4desk-editor/static/']:
    for root, dirs, files in os.walk(search_dir):
        for fname in files:
            if fname.endswith(('.html', '.py')):
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if old_hFile in content:
                        content = content.replace(old_hFile, new_hFile)
                        with open(fpath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"  ✅ Patched hFile in: {fpath}")
                        files_patched += 1
                except:
                    pass

if files_patched == 0:
    print("  ⚠️  hFile exact pattern not found — trying flexible match...")
    # Try matching just the function signature and body
    for search_dir in ['/opt/windi/clone-app/', '/opt/windi/a4desk-editor/static/']:
        for root, dirs, files in os.walk(search_dir):
            for fname in files:
                if fname.endswith(('.html', '.py')):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        if 'async function hFile(f){' in content and "document.getElementById('dt').focus()" in content:
                            # Find and replace using start/end markers
                            start = content.index('async function hFile(f){')
                            # Find matching closing brace
                            brace_count = 0
                            end = start
                            found_first = False
                            for i in range(start, min(start + 600, len(content))):
                                if content[i] == '{':
                                    brace_count += 1
                                    found_first = True
                                elif content[i] == '}':
                                    brace_count -= 1
                                    if found_first and brace_count == 0:
                                        end = i + 1
                                        break
                            if end > start:
                                content = content[:start] + new_hFile + content[end:]
                                with open(fpath, 'w', encoding='utf-8') as f:
                                    f.write(content)
                                print(f"  ✅ Patched hFile (flexible) in: {fpath}")
                                files_patched += 1
                    except:
                        pass

# Also update the drop zone text to show supported formats
for search_dir in ['/opt/windi/clone-app/', '/opt/windi/a4desk-editor/static/']:
    for root, dirs, files in os.walk(search_dir):
        for fname in files:
            if fname.endswith(('.html', '.py')):
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Update drop zone subtitle to be clearer
                    if "PDF, DOCX, TXT" in content and "wird automatisch" not in content:
                        content = content.replace(
                            "PDF, DOCX, TXT",
                            "PDF, DOCX, TXT — wird automatisch analysiert"
                        )
                        with open(fpath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"  ✅ Updated drop zone hint in: {fpath}")
                except:
                    pass

# ═══════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════

print("\n" + "═" * 60)
print("✅ CLONE UPLOAD FIX APPLIED")
print("═" * 60)
print(f"\n  Endpoint: /api/extract (PDF + DOCX + TXT)")
print(f"  JS fixes: {files_patched} file(s) patched")
print(f"\n⚡ NEXT STEPS:")
print(f"  1. Install PyPDF2:  pip install PyPDF2 --break-system-packages")
print(f"  2. Restart clone:   pkill -f clone_server.py")
print(f"     cd /opt/windi/clone-app && nohup python3 clone_server.py > /tmp/clone.log 2>&1 &")
print(f"  3. Test: Upload a PDF at clone.windia4desk.tech")
print(f"\n🐉 Three Dragons Protocol — I1-I9 ACTIVE")
