#!/usr/bin/env python3
"""
Add WINDI-RECEIPT verification endpoint
"""

FILE = "/opt/windi/a4desk-editor/a4desk_tiptap_babel.py"

with open(FILE, 'r') as f:
    content = f.read()

# Add verify endpoint after health endpoint
verify_endpoint = '''
@app.route('/api/verify/<receipt_id>', methods=['GET'])
def verify_receipt(receipt_id):
    """Public endpoint to verify WINDI-RECEIPT authenticity"""
    # First check babel_documents.db
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, status, language, receipt, created_at, updated_at 
        FROM documents WHERE receipt LIKE ?
    """, (f'%{receipt_id}%',))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        receipt_data = json.loads(row["receipt"]) if row["receipt"] else {}
        return jsonify({
            "verified": True,
            "source": "A4Desk",
            "document_id": row["id"],
            "title": row["title"],
            "status": row["status"],
            "language": row["language"],
            "receipt": receipt_data,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "principle": "KI verarbeitet. Mensch entscheidet. WINDI garantiert.",
            "verification_timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    # Also check template_registry.db
    try:
        import sqlite3
        reg_conn = sqlite3.connect('/opt/windi/data/template_registry.db')
        reg_conn.row_factory = sqlite3.Row
        reg_cursor = reg_conn.cursor()
        reg_cursor.execute("""
            SELECT receipt_number, document_type, document_title, generated_at, 
                   file_hash, validation_status, verified_count
            FROM documents_registry WHERE receipt_number = ?
        """, (receipt_id,))
        reg_row = reg_cursor.fetchone()
        
        if reg_row:
            # Update verification count
            reg_cursor.execute("""
                UPDATE documents_registry 
                SET verified_count = verified_count + 1, last_verified_at = ?
                WHERE receipt_number = ?
            """, (datetime.now(timezone.utc).isoformat(), receipt_id))
            reg_conn.commit()
            reg_conn.close()
            
            return jsonify({
                "verified": True,
                "source": "TemplateRegistry",
                "receipt_number": reg_row["receipt_number"],
                "document_type": reg_row["document_type"],
                "document_title": reg_row["document_title"],
                "generated_at": reg_row["generated_at"],
                "file_hash": reg_row["file_hash"],
                "validation_status": reg_row["validation_status"],
                "verified_count": reg_row["verified_count"] + 1,
                "principle": "KI verarbeitet. Mensch entscheidet. WINDI garantiert.",
                "verification_timestamp": datetime.now(timezone.utc).isoformat()
            })
        reg_conn.close()
    except Exception as e:
        pass
    
    return jsonify({
        "verified": False,
        "error": "Receipt not found",
        "receipt_id": receipt_id,
        "message": "This receipt ID was not found in WINDI systems.",
        "verification_timestamp": datetime.now(timezone.utc).isoformat()
    }), 404

'''

# Insert after health endpoint
health_marker = '''@app.route('/api/health')
def health():
    return jsonify({"status": "healthy", "service": "A4 Desk BABEL v3", "engine": "Tiptap", "storage": "SQLite"})'''

if '/api/verify/' not in content:
    content = content.replace(health_marker, health_marker + verify_endpoint)
    print("✅ Added /api/verify endpoint")
else:
    print("ℹ️ Verify endpoint already exists")

with open(FILE, 'w') as f:
    f.write(content)

# Validate
import subprocess
result = subprocess.run(['python3', '-m', 'py_compile', FILE], capture_output=True)
if result.returncode == 0:
    print("✅ Syntax OK")
else:
    print(f"❌ Syntax ERROR: {result.stderr.decode()}")

print("Done!")
