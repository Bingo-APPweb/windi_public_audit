#!/usr/bin/env python3
"""
Patch A4 Desk para suportar Bescheid PDF com QR Codes
"""

import re

FILE_PATH = '/opt/windi/a4desk-editor/a4desk_tiptap_babel.py'

# 1. Import a adicionar
IMPORT_CODE = '''
# WINDI Templates
sys.path.insert(0, '/opt/windi/templates')
try:
    from bescheid_generator import generate_bescheid_pdf, BEISPIEL_BAUGENEHMIGUNG
    BESCHEID_AVAILABLE = True
except ImportError:
    BESCHEID_AVAILABLE = False
'''

# 2. Nova rota a adicionar
ROUTE_CODE = '''
@app.route('/api/document/<doc_id>/export/bescheid-pdf', methods=['GET'])
def export_bescheid_pdf(doc_id):
    """Exportar como Bescheid PDF com QR Codes WINDI"""
    if not BESCHEID_AVAILABLE:
        return jsonify({"error": "Bescheid generator not available"}), 500
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({"error": "Not found"}), 404
    
    data = BEISPIEL_BAUGENEHMIGUNG.copy()
    data['subject'] = row['title']
    
    pdf_bytes, receipt = generate_bescheid_pdf(data)
    
    output_path = f"/tmp/Bescheid_{doc_id}.pdf"
    with open(output_path, 'wb') as f:
        f.write(pdf_bytes)
    
    return send_file(output_path, as_attachment=True, 
                     download_name=f"Bescheid_{receipt['id']}.pdf",
                     mimetype='application/pdf')

'''

# Ler arquivo
with open(FILE_PATH, 'r') as f:
    content = f.read()

# Backup
with open(FILE_PATH + '.backup_bescheid', 'w') as f:
    f.write(content)
print("✅ Backup criado")

# 1. Adicionar import depois de "import requests"
if 'BESCHEID_AVAILABLE' not in content:
    content = content.replace('import requests', 'import requests' + IMPORT_CODE)
    print("✅ Import adicionado")
else:
    print("⚠️ Import já existe")

# 2. Adicionar rota depois de "# API - LLM CHAT"
if 'export_bescheid_pdf' not in content:
    content = content.replace('# API - LLM CHAT', ROUTE_CODE + '# API - LLM CHAT')
    print("✅ Rota Bescheid adicionada")
else:
    print("⚠️ Rota já existe")

# Salvar
with open(FILE_PATH, 'w') as f:
    f.write(content)

print("✅ Patch aplicado com sucesso!")
print("   Reinicie o servidor: sudo systemctl restart windi")
