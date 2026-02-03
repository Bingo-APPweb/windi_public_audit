"""
WINDI Template Generator: BESCHEID
Gera PDF profissional com estrutura de governança WINDI

Página 1: Capa institucional + dados do processo
Página 2+: Bescheid completo com campos Nur Mensch
Rodapé: WINDI-RECEIPT com QR institucional
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime
import hashlib
import sqlite3

def register_document(receipt_id, doc_type, title, file_hash):
    """Registra documento no registry para verificação pública"""
    try:
        conn = sqlite3.connect('/opt/windi/data/template_registry.db')
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO documents_registry 
            (receipt_number, document_type, document_title, file_hash)
            VALUES (?, ?, ?, ?)
        """, (receipt_id, doc_type, title, file_hash))
        conn.commit()
        conn.close()
        print(f"✅ Document registered: {receipt_id}")
    except Exception as e:
        print(f"[!] Registry error: {e}")

# =============================================================================
# CORES WINDI
# =============================================================================
WINDI_TEAL = HexColor('#0d9488')
WINDI_DARK = HexColor('#1e293b')
WINDI_GRAY = HexColor('#64748b')
WINDI_LIGHT = HexColor('#f8fafc')
WINDI_PURPLE = HexColor('#7c3aed')
WINDI_GREEN = HexColor('#059669')
WINDI_RED = HexColor('#dc2626')


# =============================================================================
# DADOS DE EXEMPLO: BAUGENEHMIGUNG
# =============================================================================

BEISPIEL_BAUGENEHMIGUNG = {
    'authority_name': 'Stadt Kempten (Allgäu)',
    'department': 'Bauamt - Abteilung Baugenehmigungen',
    'authority_address': 'Rathausplatz 1, 87435 Kempten',
    'authority_phone': '+49 831 2525-0',
    'authority_email': 'bauamt@kempten.de',
    'case_number': 'BG-2026-0127-0042',
    'date': '27.01.2026',
    'recipient_name': 'Herr Max Mustermann',
    'recipient_street': 'Musterstraße 15',
    'recipient_city': '87435 Kempten',
    'subject': 'Antrag auf Baugenehmigung für Errichtung eines Einfamilienhauses',
    'subject_detail': 'Grundstück: Flurstück 1234/5, Gemarkung Kempten',
    'decision_type': 'GENEHMIGT',  # GENEHMIGT / ABGELEHNT / TEILWEISE / ZURÜCKGESTELLT
    'conditions': [
        'Die Bauausführung hat gemäß den genehmigten Bauvorlagen zu erfolgen.',
        'Der Baubeginn ist mindestens eine Woche vor Beginn der Bauarbeiten anzuzeigen.',
        'Die Abstandsflächen gemäß Art. 6 BayBO sind einzuhalten.',
        'Ein Standsicherheitsnachweis ist vor Baubeginn vorzulegen.'
    ],
    'facts': [
        'Am 15.12.2025 haben Sie einen Antrag auf Erteilung einer Baugenehmigung für die Errichtung eines Einfamilienhauses auf dem Grundstück Flurstück 1234/5 der Gemarkung Kempten gestellt.',
        'Das Bauvorhaben umfasst: Einfamilienhaus mit Satteldach, Grundfläche 120 m², Geschosse EG + OG + DG.',
        'Die Nachbarbeteiligung wurde durchgeführt. Es wurden keine Einwendungen erhoben.',
        'Die Gemeinde hat das Einvernehmen nach § 36 BauGB erteilt.'
    ],
    'reasoning': [
        'Das Bauvorhaben entspricht den Festsetzungen des Bebauungsplans Nr. 42 "Wohngebiet Süd".',
        'Die bauordnungsrechtlichen Anforderungen nach der Bayerischen Bauordnung (BayBO) werden erfüllt.',
        'Abstandsflächen (Art. 6 BayBO): eingehalten.',
        'Stellplätze (Art. 47 BayBO): nachgewiesen.',
        'Das Vorhaben fügt sich gemäß § 34 BauGB in die Eigenart der näheren Umgebung ein.',
        'Die Erschließung ist gesichert.'
    ],
    'legal_basis': [
        '§ 58 Abs. 1 BayBO (Baugenehmigung)',
        '§ 30 BauGB (Zulässigkeit im Geltungsbereich eines Bebauungsplans)',
        'Bebauungsplan Nr. 42 der Stadt Kempten',
        'Art. 6 BayBO (Abstandsflächen)',
        'Art. 47 BayBO (Stellplätze)'
    ],
    'signatory_name': '',  # NUR MENSCH
    'signatory_title': 'Sachbearbeiter/in Bauamt',
    'author': 'Bauamt Kempten'
}


# =============================================================================
# GERAÇÃO DO WINDI-RECEIPT
# =============================================================================

def generate_receipt(content_hash_input, author=""):
    """Gera dados do WINDI-RECEIPT."""
    timestamp = datetime.now()
    hash_input = f"{content_hash_input}{author}{timestamp.isoformat()}"
    full_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    short_hash = full_hash[:12].lower()
    date_code = timestamp.strftime('%d%b%y').upper()
    receipt_id = f"WINDI-BABEL-{date_code}-{short_hash[:8].upper()}"
    
    # URL de verificação
    verify_url = f"https://windi.ai/verify?id={receipt_id}&h={short_hash}"
    
    return {
        'id': receipt_id,
        'hash': short_hash,
        'timestamp': timestamp,
        'date_formatted': timestamp.strftime('%d.%m.%Y %H:%M'),
        'declaration': 'KI verarbeitet. Der Mensch entscheidet. WINDI garantiert.',
        'compliance': 'EU AI Act Art. 50 · Transparenzpflichten',
        'verify_url': verify_url,
        'governance_url': 'https://windi.ai/governance'
    }


# =============================================================================
# CLASSE DO DOCUMENTO
# =============================================================================

class BescheidDocTemplate(SimpleDocTemplate):
    """Template com rodapé WINDI incluindo QR Codes."""
    
    def __init__(self, *args, receipt=None, **kwargs):
        self.receipt = receipt
        super().__init__(*args, **kwargs)
    
    def afterPage(self):
        if self.receipt:
            c = self.canv
            c.saveState()
            
            # =================================================================
            # LADO ESQUERDO - QR INSTITUCIONAL
            # =================================================================
            
            qr_size = 1.4 * cm
            left_margin = 2 * cm
            bottom_y = 0.7 * cm
            
            # Tenta gerar QR Code institucional
            inst_qr = generate_qr_code('https://windi.ai/governance?lang=de', size=80)
            if inst_qr:
                from reportlab.lib.utils import ImageReader
                img = ImageReader(inst_qr)
                c.drawImage(img, left_margin, bottom_y, width=qr_size, height=qr_size)
            else:
                # Placeholder se QR não disponível
                c.setStrokeColor(WINDI_GRAY)
                c.setLineWidth(0.5)
                c.rect(left_margin, bottom_y, qr_size, qr_size)
                c.setFont('Helvetica', 5)
                c.setFillColor(WINDI_GRAY)
                c.drawCentredString(left_margin + qr_size/2, bottom_y + qr_size/2, 'QR')
            
            # Texto institucional
            text_x = left_margin + qr_size + 0.25*cm
            
            c.setFont('Helvetica-Bold', 6)
            c.setFillColor(WINDI_DARK)
            c.drawString(text_x, bottom_y + 1.05*cm, 'KI-gestützte Erstellung')
            
            c.setFont('Helvetica', 5)
            c.setFillColor(WINDI_GRAY)
            c.drawString(text_x, bottom_y + 0.7*cm, 'Menschliche Prüfung erforderlich')
            
            c.setFont('Helvetica', 5)
            c.setFillColor(WINDI_TEAL)
            c.drawString(text_x, bottom_y + 0.4*cm, 'windi.ai/governance')
            
            c.setFont('Helvetica', 4)
            c.setFillColor(HexColor('#94a3b8'))
            c.drawString(text_x, bottom_y + 0.15*cm, 'Scan für Methodologie')
            
            # =================================================================
            # LADO DIREITO - QR DO DOCUMENTO + RECEIPT
            # =================================================================
            
            # Box do receipt
            box_w = 6.8 * cm
            box_h = 1.7 * cm
            box_x = A4[0] - 2*cm - box_w
            box_y = bottom_y - 0.15*cm
            
            # Fundo
            c.setFillColor(WINDI_LIGHT)
            c.setStrokeColor(HexColor('#e2e8f0'))
            c.roundRect(box_x, box_y, box_w, box_h, 3, fill=1, stroke=1)
            
            # Linha superior roxa
            c.setStrokeColor(WINDI_PURPLE)
            c.setLineWidth(2)
            c.line(box_x, box_y + box_h, box_x + box_w, box_y + box_h)
            
            # QR Code do documento
            doc_qr = generate_qr_code(self.receipt['verify_url'], size=80)
            qr_doc_x = box_x + 0.15*cm
            qr_doc_y = box_y + 0.15*cm
            
            if doc_qr:
                from reportlab.lib.utils import ImageReader
                img = ImageReader(doc_qr)
                c.drawImage(img, qr_doc_x, qr_doc_y, width=1.4*cm, height=1.4*cm)
            else:
                # Placeholder
                c.setStrokeColor(WINDI_PURPLE)
                c.setLineWidth(0.5)
                c.rect(qr_doc_x, qr_doc_y, 1.4*cm, 1.4*cm)
                c.setFont('Helvetica', 5)
                c.setFillColor(WINDI_PURPLE)
                c.drawCentredString(qr_doc_x + 0.7*cm, qr_doc_y + 0.7*cm, 'QR')
            
            # Textos do receipt
            tx = box_x + 1.7*cm
            
            c.setFillColor(WINDI_DARK)
            c.setFont('Helvetica-Bold', 6)
            c.drawString(tx, box_y + 1.35*cm, self.receipt['id'])
            
            c.setFont('Helvetica', 5)
            c.setFillColor(WINDI_GRAY)
            c.drawString(tx, box_y + 1.05*cm, f"Hash: {self.receipt['hash']}")
            
            c.setFont('Helvetica', 5)
            c.drawString(tx, box_y + 0.75*cm, self.receipt['declaration'])
            
            c.setFont('Helvetica', 4.5)
            c.setFillColor(HexColor('#94a3b8'))
            c.drawString(tx, box_y + 0.45*cm, self.receipt['compliance'])
            
            c.setFont('Helvetica', 4)
            c.drawString(tx, box_y + 0.2*cm, f"{self.receipt['date_formatted']} · Scan to verify")
            
            c.restoreState()


def generate_qr_code(data, size=100):
    """
    Gera QR Code como BytesIO.
    Retorna None se biblioteca não disponível.
    """
    try:
        import qrcode
        from qrcode.constants import ERROR_CORRECT_M
        
        qr = qrcode.QRCode(
            version=2,
            error_correction=ERROR_CORRECT_M,
            box_size=10,
            border=1
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize((size, size))
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer
    except ImportError:
        return None


def generate_bescheid_pdf(data):
    """
    Gera PDF do Bescheid com estrutura WINDI completa.
    
    Returns:
        BytesIO com o PDF gerado
    """
    buffer = BytesIO()
    
    # Gera receipt
    receipt = generate_receipt(str(data), data.get('author', ''))
    
    doc = BescheidDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2.8*cm,
        receipt=receipt
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    
    style_header = ParagraphStyle(
        'Header',
        fontSize=9,
        leading=12,
        textColor=WINDI_DARK
    )
    
    style_title = ParagraphStyle(
        'Title',
        fontSize=18,
        leading=22,
        textColor=WINDI_DARK,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    style_section = ParagraphStyle(
        'Section',
        fontSize=11,
        leading=14,
        textColor=WINDI_TEAL,
        fontName='Helvetica-Bold',
        spaceBefore=15,
        spaceAfter=8
    )
    
    style_body = ParagraphStyle(
        'Body',
        fontSize=10,
        leading=13,
        textColor=WINDI_DARK,
        spaceAfter=6
    )
    
    style_field = ParagraphStyle(
        'Field',
        fontSize=10,
        leading=13,
        textColor=WINDI_DARK,
        leftIndent=0.5*cm,
        spaceAfter=4
    )
    
    style_nur_mensch = ParagraphStyle(
        'NurMensch',
        fontSize=8,
        leading=10,
        textColor=WINDI_GREEN,
        fontName='Helvetica-BoldOblique',
        spaceBefore=4
    )
    
    style_legal = ParagraphStyle(
        'Legal',
        fontSize=9,
        leading=12,
        textColor=WINDI_GRAY,
        spaceAfter=6
    )
    
    style_decision_approved = ParagraphStyle(
        'DecisionApproved',
        fontSize=12,
        leading=15,
        textColor=WINDI_GREEN,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceBefore=10,
        spaceAfter=10
    )
    
    style_decision_rejected = ParagraphStyle(
        'DecisionRejected',
        fontSize=12,
        leading=15,
        textColor=WINDI_RED,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceBefore=10,
        spaceAfter=10
    )
    
    elements = []
    
    # =========================================================================
    # CABEÇALHO DA AUTORIDADE
    # =========================================================================
    
    elements.append(Paragraph(f"<b>{data['authority_name']}</b>", style_header))
    elements.append(Paragraph(data['department'], style_header))
    elements.append(Paragraph(data['authority_address'], style_header))
    elements.append(Spacer(1, 0.5*cm))
    
    # Linha separadora
    elements.append(HRFlowable(width="100%", thickness=1, color=WINDI_TEAL, spaceAfter=15))
    
    # =========================================================================
    # DADOS DO PROCESSO
    # =========================================================================
    
    meta_data = [
        [Paragraph("<b>Aktenzeichen:</b>", style_body), 
         Paragraph(data['case_number'], style_body)],
        [Paragraph("<b>Datum:</b>", style_body), 
         Paragraph(data['date'], style_body)]
    ]
    
    meta_table = Table(meta_data, colWidths=[4*cm, 10*cm])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # =========================================================================
    # DESTINATÁRIO
    # =========================================================================
    
    elements.append(Paragraph(data['recipient_name'], style_body))
    elements.append(Paragraph(data['recipient_street'], style_body))
    elements.append(Paragraph(data['recipient_city'], style_body))
    elements.append(Spacer(1, 1*cm))
    
    # =========================================================================
    # TÍTULO
    # =========================================================================
    
    elements.append(Paragraph("BESCHEID", style_title))
    
    # =========================================================================
    # BETREFF
    # =========================================================================
    
    elements.append(Paragraph("<b>Betreff:</b>", style_section))
    elements.append(Paragraph(data['subject'], style_body))
    elements.append(Paragraph(data['subject_detail'], style_body))
    
    # =========================================================================
    # TENOR (DECISÃO) - NUR MENSCH
    # =========================================================================
    
    elements.append(Spacer(1, 0.5*cm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=WINDI_GRAY, spaceAfter=10))
    
    elements.append(Paragraph("TENOR", style_section))
    elements.append(Paragraph("[Nur Mensch — Entscheidung]", style_nur_mensch))
    
    # Decisão
    if data['decision_type'] == 'GENEHMIGT':
        elements.append(Paragraph("Ihr Antrag wird hiermit", style_body))
        elements.append(Paragraph("✓ GENEHMIGT", style_decision_approved))
    elif data['decision_type'] == 'ABGELEHNT':
        elements.append(Paragraph("Ihr Antrag wird hiermit", style_body))
        elements.append(Paragraph("✗ ABGELEHNT", style_decision_rejected))
    else:
        elements.append(Paragraph(f"Status: {data['decision_type']}", style_body))
    
    # Auflagen (Condições)
    if data.get('conditions') and data['decision_type'] == 'GENEHMIGT':
        elements.append(Paragraph("<b>Unter folgenden Auflagen:</b>", style_body))
        for i, condition in enumerate(data['conditions'], 1):
            elements.append(Paragraph(f"{i}. {condition}", style_field))
    
    # =========================================================================
    # SACHVERHALT (FATOS)
    # =========================================================================
    
    elements.append(Spacer(1, 0.3*cm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=WINDI_GRAY, spaceAfter=10))
    
    elements.append(Paragraph("SACHVERHALT", style_section))
    for fact in data['facts']:
        elements.append(Paragraph(fact, style_body))
    
    # =========================================================================
    # BEGRÜNDUNG (FUNDAMENTAÇÃO)
    # =========================================================================
    
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph("BEGRÜNDUNG", style_section))
    for reason in data['reasoning']:
        elements.append(Paragraph(reason, style_body))
    
    # Rechtsgrundlagen
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph("<b>Rechtsgrundlagen:</b>", style_body))
    for law in data['legal_basis']:
        elements.append(Paragraph(f"• {law}", style_field))
    
    # =========================================================================
    # RECHTSBEHELFSBELEHRUNG
    # =========================================================================
    
    elements.append(Spacer(1, 0.5*cm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=WINDI_GRAY, spaceAfter=10))
    
    elements.append(Paragraph("RECHTSBEHELFSBELEHRUNG", style_section))
    elements.append(Paragraph(
        "Gegen diesen Bescheid kann innerhalb eines Monats nach Bekanntgabe "
        "Widerspruch erhoben werden. Der Widerspruch ist bei der oben genannten "
        "Behörde schriftlich oder zur Niederschrift einzulegen.",
        style_legal
    ))
    elements.append(Paragraph(
        "Alternativ kann innerhalb eines Monats nach Bekanntgabe unmittelbar "
        "Klage beim zuständigen Verwaltungsgericht erhoben werden.",
        style_legal
    ))
    
    # =========================================================================
    # UNTERSCHRIFT - NUR MENSCH
    # =========================================================================
    
    elements.append(Spacer(1, 1*cm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=WINDI_GRAY, spaceAfter=10))
    
    elements.append(Paragraph("UNTERSCHRIFT", style_section))
    elements.append(Paragraph("[Nur Mensch — Unterschrift erforderlich]", style_nur_mensch))
    
    sig_data = [
        ['Ort:', '_' * 30, 'Datum:', '_' * 20],
        ['', '', '', ''],
        ['Unterschrift:', '_' * 50, '', ''],
        ['', '', '', ''],
        ['Name:', data.get('signatory_name', '_' * 30), '', ''],
        ['Funktion:', data.get('signatory_title', '_' * 30), '', '']
    ]
    
    sig_table = Table(sig_data, colWidths=[2.5*cm, 6*cm, 2*cm, 4*cm])
    sig_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (-1, -1), WINDI_DARK),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(sig_table)
    
    # =========================================================================
    # NOTA DE TRANSPARÊNCIA
    # =========================================================================
    
    elements.append(Spacer(1, 1*cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=WINDI_TEAL, spaceAfter=10))
    
    transparency_style = ParagraphStyle(
        'Transparency',
        fontSize=8,
        leading=11,
        textColor=WINDI_GRAY,
        alignment=TA_CENTER
    )
    
    elements.append(Paragraph(
        "Dieses Dokument wurde mit KI-Unterstützung unter menschlicher Verantwortung erstellt.",
        transparency_style
    ))
    elements.append(Paragraph(
        "Die Entscheidung (Tenor) und Unterschrift erfordern menschliche Autorisierung.",
        transparency_style
    ))
    elements.append(Paragraph(
        "Gemäß EU AI Act Art. 50 — Transparenzpflichten für KI-Systeme.",
        transparency_style
    ))
    
    # Build
    doc.build(elements)
    buffer.seek(0)
    # Register document for public verification
    register_document(
        receipt['id'],
        'Bescheid',
        data.get('subject', 'Bescheid'),
        receipt['hash']
    )
    return buffer.getvalue(), receipt


# =============================================================================
# PROMPT SCRIPT PARA WINDI
# =============================================================================

WINDI_PROMPT_BESCHEID = """
=============================================================================
WINDI PROMPT SCRIPT: BESCHEID (Decisão Administrativa)
Setor: Kommunalverwaltung (Prefeituras alemãs)
=============================================================================

CONTEXTO:
O usuário precisa criar um Bescheid (decisão administrativa oficial).
A IA deve estruturar o documento, mas NUNCA preencher os campos de decisão.

REGRA FUNDAMENTAL:
"KI strukturiert. Der Mensch entscheidet."

CAMPOS QUE A IA PODE PREENCHER:
- Cabeçalho da autoridade (se fornecido)
- Dados do processo (Aktenzeichen)
- Dados do destinatário
- Betreff (Assunto)
- Sachverhalt (Fatos - baseado em informações fornecidas)
- Rechtsgrundlagen (Base legal - conforme o tipo de processo)
- Rechtsbehelfsbelehrung (texto padrão de recursos)

CAMPOS "NUR MENSCH" (NUNCA preencher):
- TENOR (a decisão: genehmigt/abgelehnt)
- Auflagen (condições da aprovação)
- Begründung final (justificativa da decisão)
- Unterschrift (assinatura)
- Datum der Entscheidung (data da decisão)

FLUXO DO PROMPT:

1. IDENTIFICAR TIPO DE BESCHEID:
   Pergunta: "Welche Art von Bescheid möchten Sie erstellen?"
   Opções:
   - Baugenehmigung (Licença de Construção)
   - Gewerbeanmeldung (Registro Comercial)
   - Aufenthaltserlaubnis (Autorização de Residência)
   - Sozialhilfe (Assistência Social)
   - Wohngeld (Auxílio Moradia)
   - Outro: [especificar]

2. COLETAR DADOS:
   - Behörde (Autoridade): Nome, departamento, endereço
   - Aktenzeichen (Número do processo)
   - Antragsteller (Requerente): Nome, endereço
   - Antragsgegenstand (Objeto do pedido)
   - Eingangsdatum (Data de entrada)

3. ESTRUTURAR SACHVERHALT:
   Com base nos dados fornecidos, estruturar os fatos de forma neutra.

4. IDENTIFICAR RECHTSGRUNDLAGEN:
   Sugerir base legal conforme o tipo de processo.

5. GERAR DOCUMENTO:
   Criar PDF com todos os campos, deixando TENOR e UNTERSCHRIFT em branco.

6. ENTREGAR PARA REVISÃO HUMANA:
   Mensagem: "Der Bescheid ist strukturiert. Bitte überprüfen Sie den Sachverhalt und treffen Sie die Entscheidung im Tenor-Abschnitt."

=============================================================================
EXEMPLO DE INTERAÇÃO:
=============================================================================

USUÁRIO: Preciso criar um Bescheid de Baugenehmigung

WINDI: Ich werde einen Bescheid für eine Baugenehmigung strukturieren.

Bitte geben Sie folgende Informationen an:

1. **Behörde:** Welche Behörde stellt den Bescheid aus?
2. **Antragsteller:** Name und Anschrift des Antragstellers
3. **Grundstück:** Flurstück und Gemarkung
4. **Bauvorhaben:** Art und Umfang des geplanten Baus
5. **Antragsdatum:** Wann wurde der Antrag eingereicht?

[Após coletar informações]

WINDI: Der Bescheid wurde strukturiert mit:
- Sachverhalt basierend auf Ihren Angaben
- Rechtsgrundlagen: BayBO, BauGB
- Standard-Rechtsbehelfsbelehrung

⚠️ **NUR MENSCH - Ihre Entscheidung erforderlich:**
- [ ] GENEHMIGT / [ ] ABGELEHNT
- Auflagen (falls genehmigt)
- Begründung der Entscheidung
- Unterschrift

[PDF gerado com campos em branco para decisão]

=============================================================================
"""


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print("Gerando Bescheid de exemplo: Baugenehmigung")
    print("=" * 60)
    
    pdf_bytes, receipt = generate_bescheid_pdf(BEISPIEL_BAUGENEHMIGUNG)
    
    # Salva PDF
    output_path = '/opt/windi/templates/Bescheid_Baugenehmigung.pdf'
    with open(output_path, 'wb') as f:
        f.write(pdf_bytes)
    
    print(f"PDF gerado: {output_path}")
    print(f"Receipt ID: {receipt['id']}")
    print(f"Hash: {receipt['hash']}")
    print("=" * 60)
    print("\nCampos 'Nur Mensch':")
    print("- TENOR (Entscheidung)")
    print("- UNTERSCHRIFT")
    print("=" * 60)
    
    # Salva o prompt script
    prompt_path = '/opt/windi/templates/WINDI_PROMPT_Bescheid.md'
    with open(prompt_path, 'w') as f:
        f.write(WINDI_PROMPT_BESCHEID)
    
    print(f"\nPrompt Script salvo: {prompt_path}")
