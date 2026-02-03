#!/usr/bin/env python3
"""
Patch para detectar Bescheid no chat e gerar PDF
"""

FILE_PATH = '/opt/windi/a4desk-editor/a4desk_tiptap_babel.py'

# Nova função chat com detecção de Bescheid
NEW_CHAT_FUNCTION = '''@app.route('/api/chat', methods=['POST'])
def chat():
    """Enviar mensagem para o WINDI Agent via Gateway - com suporte a Bescheid"""
    data = request.json or {}
    message = data.get('message', '')
    context = data.get('context', '')
    dragon = data.get('dragon', 'claude')
    
    # Detectar pedido de Bescheid
    msg_lower = message.lower()
    if BESCHEID_AVAILABLE and ('bescheid' in msg_lower and ('baugenehmigung' in msg_lower or 'erstellen' in msg_lower)):
        # Gerar Bescheid PDF
        from bescheid_generator import generate_bescheid_pdf, BEISPIEL_BAUGENEHMIGUNG
        import uuid
        
        bescheid_data = BEISPIEL_BAUGENEHMIGUNG.copy()
        
        # Extrair nome se mencionado
        if 'antragsteller:' in msg_lower:
            try:
                name_part = message.split('ntragsteller:')[1].split(',')[0].strip()
                bescheid_data['recipient_name'] = name_part
            except:
                pass
        
        pdf_bytes, receipt = generate_bescheid_pdf(bescheid_data)
        
        # Salvar PDF
        pdf_filename = f"Bescheid_{receipt['id']}.pdf"
        pdf_path = f"/opt/windi/a4desk-editor/static/{pdf_filename}"
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)
        
        return jsonify({
            "response": f"""✅ **Bescheid erstellt!**

📄 **Receipt:** {receipt['id']}
🔐 **Hash:** {receipt['hash']}

📥 [Download PDF](/static/{pdf_filename})

---
*KI verarbeitet. Der Mensch entscheidet. WINDI garantiert.*

⚠️ **Nur Mensch:** Bitte prüfen Sie den TENOR und unterschreiben Sie das Dokument.""",
            "receipt": receipt['id'],
            "pdf_url": f"/static/{pdf_filename}"
        })
    
    # Chat normal via Gateway
    try:
        resp = requests.post(f"{CONFIG['gateway']}/api/chat", json={
            "message": message,
            "context": context,
            "dragon": dragon
        }, timeout=60)
        result = resp.json()
        return jsonify(result)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Gateway error: {str(e)}"}), 503
'''

# Ler arquivo
with open(FILE_PATH, 'r') as f:
    content = f.read()

# Backup
with open(FILE_PATH + '.backup_chat', 'w') as f:
    f.write(content)
print("✅ Backup criado")

# Substituir função chat
import re
pattern = r'@app\.route\(\'/api/chat\'.*?except requests\.exceptions\.RequestException as e:\s*return jsonify\(\{"error": f"Gateway error: \{str\(e\)\}"\}\), 503'
if re.search(pattern, content, re.DOTALL):
    content = re.sub(pattern, NEW_CHAT_FUNCTION.strip(), content, flags=re.DOTALL)
    print("✅ Função chat atualizada com suporte a Bescheid")
else:
    print("❌ Padrão não encontrado")

# Salvar
with open(FILE_PATH, 'w') as f:
    f.write(content)

print("✅ Patch aplicado!")
print("   Reinicie: pkill -9 -f a4desk && cd /opt/windi/a4desk-editor && nohup python3 a4desk_tiptap_babel.py &")
