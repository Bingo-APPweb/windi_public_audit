"""
WINDI Template Generator: TECHNICAL REPORT
Gera PDF profissional estilo MIT com governança WINDI
Bilíngue EN/DE com QR Code de verificação institucional
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, HRFlowable, Image
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime
import hashlib
import sqlite3
import qrcode

# =============================================================================
# CORES WINDI
# =============================================================================
WINDI_TEAL = HexColor('#0d9488')
WINDI_DARK = HexColor('#1e293b')
WINDI_GRAY = HexColor('#64748b')
WINDI_LIGHT = HexColor('#f8fafc')
WINDI_GREEN = HexColor('#059669')

# =============================================================================
# DATABASE REGISTRATION
# =============================================================================
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
# RECEIPT GENERATOR
# =============================================================================
def generate_receipt(content_hash_input, author=""):
    timestamp = datetime.now()
    date_code = timestamp.strftime("%d%b%y").upper()
    hash_input = f"{content_hash_input}{timestamp.isoformat()}{author}"
    content_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:12].upper()
    receipt_id = f"WINDI-TR-{date_code}-{content_hash[:8]}"
    return {
        'id': receipt_id,
        'hash': content_hash.lower(),
        'timestamp': timestamp.isoformat(),
        'author': author
    }

# =============================================================================
# QR CODE GENERATOR
# =============================================================================
def generate_qr_code(data, size=100):
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0d9488", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

# =============================================================================
# TECHNICAL REPORT DATA
# =============================================================================
REPORT_DATA = {
    'title_en': 'Institutional Document Verification System',
    'title_de': 'Institutionelles Dokumentenverifizierungssystem',
    'subtitle_en': 'A Pre-AI Governance Layer for Auditable AI-Assisted Document Production',
    'subtitle_de': 'Eine Pre-AI Governance-Schicht für auditierbare KI-gestützte Dokumentenproduktion',
    'date': '28. Januar 2026',
    'version': '1.0',
    'classification': 'Public Technical Report',
    'authors': [
        {'name': 'Jober F.', 'role': 'Chief Governance Officer'},
        {'name': 'Claude (Anthropic)', 'role': 'AI Guardian Dragon'},
        {'name': 'GPT-4 (OpenAI)', 'role': 'AI Architect Dragon'}
    ],
    'institution': 'WINDI Publishing House',
    'location': 'Kempten (Allgäu), Bavaria, Germany',
    'abstract_en': '''This technical report documents the design, implementation, and validation of the WINDI Institutional Document Verification System. The system addresses a critical gap in AI-assisted document production: the absence of institutional accountability mechanisms. While AI systems can generate professional documents with high efficiency, they traditionally lack the governance infrastructure required for institutional trust.

WINDI implements a Pre-AI Governance Layer that ensures every AI-assisted document is cryptographically registered, publicly verifiable, and forensically auditable. The core principle governing all operations is: "AI processes. Human decides. WINDI guarantees."

The system was implemented on January 28, 2026, achieving full operational status with automated document registration, QR-code-based verification endpoints, and real-time audit trails.''',
    'abstract_de': '''Dieser technische Bericht dokumentiert das Design, die Implementierung und die Validierung des WINDI Institutionellen Dokumentenverifizierungssystems. Das System adressiert eine kritische Lücke in der KI-gestützten Dokumentenproduktion: das Fehlen institutioneller Rechenschaftsmechanismen.

WINDI implementiert eine Pre-AI Governance Layer, die sicherstellt, dass jedes KI-gestützte Dokument kryptografisch registriert, öffentlich verifizierbar und forensisch auditierbar ist.

Das Leitprinzip lautet: "KI verarbeitet. Der Mensch entscheidet. WINDI garantiert."''',
    'sections': [
        {
            'title_en': '1. Introduction',
            'title_de': '1. Einleitung',
            'content_en': '''The proliferation of AI-assisted document generation presents a fundamental challenge for institutional governance: How can organizations verify that a document was produced under proper human oversight while leveraging AI efficiency?

Traditional approaches offer two inadequate extremes: (a) prohibiting AI assistance entirely, sacrificing efficiency, or (b) allowing unrestricted AI generation, sacrificing accountability.

WINDI implements a third path: AI-assisted document production with institutional verification.''',
            'content_de': '''Die Verbreitung von KI-gestützter Dokumentengenerierung stellt eine grundlegende Herausforderung für die institutionelle Governance dar.

WINDI implementiert einen dritten Weg: KI-gestützte Dokumentenproduktion mit institutioneller Verifizierung.'''
        },
        {
            'title_en': '2. System Architecture',
            'title_de': '2. Systemarchitektur',
            'content_en': '''The WINDI verification system consists of three integrated components:

Document Registry Database: The documents_registry table serves as the central repository. Each generated document receives a unique receipt number, cryptographic hash, and timestamp at creation.

Verification Endpoint: The public endpoint /verify/<receipt> provides institutional transparency without exposing sensitive content.

Automatic Registration: Document registration occurs automatically at PDF generation time through the register_document() function.''',
            'content_de': '''Das WINDI-Verifizierungssystem besteht aus drei integrierten Komponenten:

Dokumentenregister-Datenbank: Die Tabelle documents_registry dient als zentrales Repository.

Verifizierungsendpunkt: Der öffentliche Endpunkt /verify/<receipt> bietet institutionelle Transparenz.

Automatische Registrierung: Die Dokumentenregistrierung erfolgt automatisch bei der PDF-Generierung.'''
        },
        {
            'title_en': '3. Implementation Results',
            'title_de': '3. Implementierungsergebnisse',
            'content_en': '''On January 28, 2026, the system achieved full operational status:

Test Receipt: WINDI-BABEL-28JAN26-95C4964C
Document Type: Bescheid (Administrative Decision)
Hash: 95c4964cbd11
Status: VALID
Verification Counter: Operational

The complete cycle functions: PDF generation → automatic registration → QR code embedding → public verification.''',
            'content_de': '''Am 28. Januar 2026 erreichte das System den vollen Betriebsstatus:

Test-Receipt: WINDI-BABEL-28JAN26-95C4964C
Dokumenttyp: Bescheid
Hash: 95c4964cbd11
Status: VALID

Der komplette Zyklus funktioniert: PDF-Generierung → automatische Registrierung → QR-Code-Einbettung → öffentliche Verifizierung.'''
        },
        {
            'title_en': '4. EU AI Act Compliance',
            'title_de': '4. EU AI Act Konformität',
            'content_en': '''The WINDI system directly addresses EU AI Act Article 50 transparency requirements:

- Explicit disclosure of AI involvement in document production
- Human decision points ("Nur Mensch" fields) that block AI input
- Cryptographic verification mechanisms for audit trails
- Public verification endpoints for institutional accountability''',
            'content_de': '''Das WINDI-System erfüllt direkt die Transparenzanforderungen des EU AI Act Artikel 50:

- Explizite Offenlegung der KI-Beteiligung
- Menschliche Entscheidungspunkte ("Nur Mensch"-Felder)
- Kryptografische Verifizierungsmechanismen
- Öffentliche Verifizierungsendpunkte'''
        },
        {
            'title_en': '5. Conclusion',
            'title_de': '5. Fazit',
            'content_en': '''The WINDI Institutional Document Verification System demonstrates that AI-assisted document production and institutional accountability are not mutually exclusive.

By implementing cryptographic registration, public verification endpoints, and forensic audit trails, WINDI provides the governance infrastructure necessary for institutional trust in AI-assisted workflows.

The system operates under the principle: "AI processes. Human decides. WINDI guarantees."''',
            'content_de': '''Das WINDI System zeigt, dass KI-gestützte Dokumentenproduktion und institutionelle Rechenschaftspflicht sich nicht gegenseitig ausschließen.

Das System operiert unter dem Prinzip: "KI verarbeitet. Der Mensch entscheidet. WINDI garantiert."'''
        }
    ],
    'human_approval': {
        'field': 'TECHNICAL REVIEW APPROVAL',
        'instruction_en': 'Human reviewer must sign to validate this report',
        'instruction_de': 'Menschlicher Prüfer muss zur Validierung unterschreiben'
    }
}

# =============================================================================
# PDF GENERATOR
# =============================================================================
def generate_technical_report_pdf(data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2.5*cm
    )
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle('Title', parent=styles['Heading1'],
        fontSize=24, textColor=WINDI_DARK, alignment=TA_CENTER,
        spaceAfter=6, fontName='Helvetica-Bold')
    
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
        fontSize=14, textColor=WINDI_TEAL, alignment=TA_CENTER,
        spaceAfter=20, fontName='Helvetica-Oblique')
    
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'],
        fontSize=14, textColor=WINDI_TEAL, spaceBefore=20,
        spaceAfter=10, fontName='Helvetica-Bold')
    
    body_style = ParagraphStyle('Body', parent=styles['Normal'],
        fontSize=11, textColor=WINDI_DARK, alignment=TA_JUSTIFY,
        spaceAfter=12, leading=16, fontName='Helvetica')
    
    german_style = ParagraphStyle('German', parent=body_style,
        fontName='Helvetica-Oblique', textColor=WINDI_GRAY)
    
    # Generate receipt
    content_for_hash = f"{data['title_en']}{data['date']}"
    receipt = generate_receipt(content_for_hash, "WINDI-System")
    
    elements = []
    
    # === COVER PAGE ===
    elements.append(Spacer(1, 2*cm))
    elements.append(Paragraph("TECHNICAL REPORT", subtitle_style))
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph(data['title_en'], title_style))
    elements.append(Paragraph(data['title_de'], german_style))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(data['subtitle_en'], subtitle_style))
    elements.append(Spacer(1, 1*cm))
    
    # Institution
    inst_style = ParagraphStyle('Inst', parent=styles['Normal'],
        fontSize=12, alignment=TA_CENTER, textColor=WINDI_DARK)
    elements.append(Paragraph(f"<b>{data['institution']}</b>", inst_style))
    elements.append(Paragraph(data['location'], inst_style))
    elements.append(Paragraph(data['date'], inst_style))
    elements.append(Spacer(1, 1*cm))
    
    # Authors table
    author_data = [['Research Team / Forschungsteam']]
    for author in data['authors']:
        author_data.append([f"{author['name']} — {author['role']}"])
    
    author_table = Table(author_data, colWidths=[12*cm])
    author_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), WINDI_TEAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, WINDI_TEAL),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(author_table)
    
    elements.append(PageBreak())
    
    # === ABSTRACT ===
    elements.append(Paragraph("Abstract", heading_style))
    elements.append(Paragraph(data['abstract_en'].replace('\n\n', '<br/><br/>'), body_style))
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("Zusammenfassung", heading_style))
    elements.append(Paragraph(data['abstract_de'].replace('\n\n', '<br/><br/>'), german_style))
    
    elements.append(PageBreak())
    
    # === SECTIONS ===
    for section in data['sections']:
        elements.append(Paragraph(section['title_en'], heading_style))
        elements.append(Paragraph(section['content_en'].replace('\n\n', '<br/><br/>'), body_style))
        elements.append(Spacer(1, 0.3*cm))
        elements.append(Paragraph(section['title_de'], ParagraphStyle('GerHead', 
            parent=heading_style, textColor=WINDI_GRAY, fontSize=12)))
        elements.append(Paragraph(section['content_de'].replace('\n\n', '<br/><br/>'), german_style))
        elements.append(Spacer(1, 0.5*cm))
    
    elements.append(PageBreak())
    
    # === HUMAN APPROVAL SECTION ===
    elements.append(Paragraph("NUR MENSCH / HUMAN ONLY", ParagraphStyle('Warning',
        parent=heading_style, textColor=HexColor('#dc2626'), fontSize=16, alignment=TA_CENTER)))
    elements.append(Spacer(1, 0.5*cm))
    
    approval_data = [
        ['TECHNICAL REVIEW APPROVAL'],
        [data['human_approval']['instruction_en']],
        [data['human_approval']['instruction_de']],
        [''],
        ['Reviewer Name / Prüfername: _______________________________'],
        [''],
        ['Date / Datum: _______________________________'],
        [''],
        ['Signature / Unterschrift: _______________________________'],
        [''],
        ['☐ APPROVED / GENEHMIGT    ☐ REJECTED / ABGELEHNT']
    ]
    
    approval_table = Table(approval_data, colWidths=[15*cm])
    approval_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#fef2f2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#991b1b')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 2, HexColor('#dc2626')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(approval_table)
    
    elements.append(Spacer(1, 1*cm))
    
    # === WINDI RECEIPT ===
    elements.append(HRFlowable(width="100%", thickness=1, color=WINDI_TEAL))
    elements.append(Spacer(1, 0.5*cm))
    
    # QR Codes
    verify_url = f"https://windi.publish/verify/{receipt['id']}"
    qr_verify = generate_qr_code(verify_url, size=80)
    qr_img = Image(qr_verify, width=2.5*cm, height=2.5*cm)
    
    receipt_style = ParagraphStyle('Receipt', parent=styles['Normal'],
        fontSize=9, textColor=WINDI_GRAY, alignment=TA_CENTER)
    
    receipt_data = [
        [qr_img, 
         Paragraph(f'''<b>WINDI-RECEIPT</b><br/>
         <font size="8">{receipt['id']}</font><br/>
         <font size="7">Hash: {receipt['hash']}</font><br/>
         <font size="7">{receipt['timestamp'][:19]}</font><br/>
         <font size="8"><b>AI processes. Human decides. WINDI guarantees.</b></font>''', receipt_style)]
    ]
    
    receipt_table = Table(receipt_data, colWidths=[3*cm, 12*cm])
    receipt_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(receipt_table)
    
    # Transparency notice
    elements.append(Spacer(1, 0.5*cm))
    transparency_style = ParagraphStyle('Transparency', parent=styles['Normal'],
        fontSize=8, textColor=WINDI_GRAY, alignment=TA_CENTER)
    elements.append(Paragraph(
        "🤖 This document was structured with AI assistance under WINDI governance.",
        transparency_style))
    elements.append(Paragraph(
        "Gemäß EU AI Act Art. 50 — Transparenzpflichten für KI-Systeme.",
        transparency_style))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    # Register document
    register_document(
        receipt['id'],
        'Technical Report',
        data['title_en'],
        receipt['hash']
    )
    
    return buffer.getvalue(), receipt

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
    print("Gerando Technical Report: WINDI Verification System")
    print("=" * 60)
    
    pdf_bytes, receipt = generate_technical_report_pdf(REPORT_DATA)
    
    output_path = '/opt/windi/templates/WINDI_Technical_Report_2026-01-28.pdf'
    with open(output_path, 'wb') as f:
        f.write(pdf_bytes)
    
    print(f"PDF gerado: {output_path}")
    print(f"Receipt ID: {receipt['id']}")
    print(f"Hash: {receipt['hash']}")
    print("=" * 60)
    print("\nCampos 'Nur Mensch':")
    print("- TECHNICAL REVIEW APPROVAL")
    print("- Reviewer Signature")
    print("=" * 60)
