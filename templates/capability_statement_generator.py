"""
WINDI Template Generator: CAPABILITY STATEMENT
Research Capability Statement - Executable Governance
Para BMBF, Editais Universitários, Parcerias Institucionais
Trilíngue EN/DE/PT com evidência de artefatos registrados
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
WINDI_BLUE = HexColor('#1e40af')

# =============================================================================
# DATABASE FUNCTIONS
# =============================================================================
def register_document(receipt_id, doc_type, title, file_hash):
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

def get_registered_artifacts():
    """Fetch all registered artifacts as evidence"""
    try:
        conn = sqlite3.connect('/opt/windi/data/template_registry.db')
        cur = conn.cursor()
        cur.execute("""
            SELECT receipt_number, document_type, document_title, 
                   generated_at, validation_status
            FROM documents_registry 
            ORDER BY id DESC
        """)
        rows = cur.fetchall()
        conn.close()
        return rows
    except:
        return []

def generate_receipt(content_hash_input, author=""):
    timestamp = datetime.now()
    date_code = timestamp.strftime("%d%b%y").upper()
    hash_input = f"{content_hash_input}{timestamp.isoformat()}{author}"
    content_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:12].upper()
    receipt_id = f"WINDI-CAP-{date_code}-{content_hash[:8]}"
    return {
        'id': receipt_id,
        'hash': content_hash.lower(),
        'timestamp': timestamp.isoformat(),
        'author': author
    }

def generate_qr_code(data, size=100):
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1e40af", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

# =============================================================================
# CAPABILITY DATA
# =============================================================================
CAPABILITY_DATA = {
    'title_en': 'Research Capability Statement',
    'title_de': 'Forschungsfähigkeitsnachweis',
    'subtitle': 'Executable Governance Document Generation System',
    'date': '28 January 2026',
    'version': '1.0',
    
    'institution': {
        'name': 'WINDI Publishing House',
        'type': 'Pre-AI Governance Layer Platform',
        'location': 'Kempten (Allgäu), Bavaria, Germany',
        'focus': 'Institutional AI Governance for Banking, Government & Enterprise'
    },
    
    'executive_summary_en': '''WINDI Publishing House has developed and validated a functional prototype for Executable Governance Document Generation. This system demonstrates technical capability in automated generation of formally structured, registered, and cryptographically referenceable documents within AI-assisted decision processes.

The system maintains human decision authority while enabling AI-assisted document structuring, addressing EU AI Act Article 50 transparency requirements and institutional accountability standards.''',

    'executive_summary_de': '''WINDI Publishing House hat einen funktionalen Prototyp für die Generierung von Executable Governance-Dokumenten entwickelt und validiert. Dieses System demonstriert technische Fähigkeiten in der automatisierten Erzeugung formal strukturierter, registrierter und kryptographisch referenzierbarer Dokumente im Kontext KI-gestützter Entscheidungsprozesse.

Das System bewahrt die menschliche Entscheidungshoheit bei gleichzeitiger KI-gestützter Dokumentenstrukturierung und erfüllt die Transparenzanforderungen des EU AI Act Artikel 50.''',

    'capabilities': [
        {
            'name_en': 'Automated Structured Document Generation',
            'name_de': 'Automatisierte strukturierte Dokumentengenerierung',
            'desc_en': 'System generates formal documents with unique identifiers, emission records, integrity hashes, and controlled storage paths.',
            'desc_de': 'System erzeugt formale Dokumente mit eindeutigen Identifikatoren, Emissionsprotokollen, Integritäts-Hashes und kontrollierten Speicherpfaden.',
            'evidence': 'WINDI-BABEL-28JAN26-95C4964C (Bescheid)'
        },
        {
            'name_en': 'Cryptographic Document Registry',
            'name_de': 'Kryptographisches Dokumentenregister',
            'desc_en': 'SQLite-based registry with SHA-256 hashing, public verification endpoints, and audit counters for institutional transparency.',
            'desc_de': 'SQLite-basiertes Register mit SHA-256-Hashing, öffentlichen Verifizierungsendpunkten und Audit-Zählern für institutionelle Transparenz.',
            'evidence': '/verify/<receipt> endpoint operational'
        },
        {
            'name_en': 'Human-Only Decision Fields',
            'name_de': 'Nur-Mensch-Entscheidungsfelder',
            'desc_en': '"Nur Mensch" fields block AI input for substantive decisions, ensuring human authority over approvals, signatures, and judgments.',
            'desc_de': '"Nur Mensch"-Felder blockieren KI-Eingaben für substantielle Entscheidungen und gewährleisten menschliche Autorität über Genehmigungen und Urteile.',
            'evidence': 'Constitutional Validator with 9 Articles'
        },
        {
            'name_en': 'Multi-Language Governance Templates',
            'name_de': 'Mehrsprachige Governance-Vorlagen',
            'desc_en': 'Template system supporting German, English, and Portuguese with consistent governance principles across languages.',
            'desc_de': 'Vorlagensystem mit Unterstützung für Deutsch, Englisch und Portugiesisch mit konsistenten Governance-Prinzipien.',
            'evidence': 'WINDI-TR-28JAN26-B18F5427 (Technical Report)'
        },
        {
            'name_en': 'QR-Code Verification System',
            'name_de': 'QR-Code-Verifizierungssystem',
            'desc_en': 'Embedded QR codes in generated documents link to public verification pages showing document status and audit history.',
            'desc_de': 'Eingebettete QR-Codes in generierten Dokumenten verlinken zu öffentlichen Verifizierungsseiten mit Dokumentstatus und Audit-Historie.',
            'evidence': 'All generated PDFs include institutional QR'
        },
        {
            'name_en': 'Forensic Audit Trail',
            'name_de': 'Forensischer Audit-Trail',
            'desc_en': 'Complete audit trail with constitutional validation records, verification counters, and timestamp logging for institutional oversight.',
            'desc_de': 'Vollständiger Audit-Trail mit Verfassungsvalidierungsprotokollen, Verifizierungszählern und Zeitstempelprotokollierung.',
            'evidence': 'constitutional_audit table with Article tracking'
        }
    ],
    
    'research_relevance_en': '''This prototype supports exploration of how governance artifacts can be machine-generated, versioned, and made traceable without displacing human decision authority.

Research domains addressed:
- Digital Governance Systems
- Auditable AI-Human Interfaces  
- Executable Policy Frameworks
- Institutional Accountability Mechanisms
- EU AI Act Compliance Architecture''',

    'research_relevance_de': '''Dieser Prototyp unterstützt die Erforschung, wie Governance-Artefakte maschinell erzeugt, versioniert und nachvollziehbar gemacht werden können, ohne die menschliche Entscheidungshoheit zu ersetzen.

Adressierte Forschungsbereiche:
- Digitale Governance-Systeme
- Auditierbare KI-Mensch-Schnittstellen
- Ausführbare Policy-Frameworks
- Institutionelle Rechenschaftsmechanismen
- EU AI Act Compliance-Architektur''',

    'principle': {
        'en': 'AI processes. Human decides. WINDI guarantees.',
        'de': 'KI verarbeitet. Der Mensch entscheidet. WINDI garantiert.',
        'pt': 'IA processa. Humano decide. WINDI garante.'
    }
}

# =============================================================================
# PDF GENERATOR
# =============================================================================
def generate_capability_statement_pdf(data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2.5*cm
    )
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle('Title', parent=styles['Heading1'],
        fontSize=22, textColor=WINDI_BLUE, alignment=TA_CENTER,
        spaceAfter=6, fontName='Helvetica-Bold')
    
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
        fontSize=12, textColor=WINDI_GRAY, alignment=TA_CENTER,
        spaceAfter=20, fontName='Helvetica-Oblique')
    
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'],
        fontSize=13, textColor=WINDI_BLUE, spaceBefore=16,
        spaceAfter=8, fontName='Helvetica-Bold')
    
    subhead_style = ParagraphStyle('Subhead', parent=styles['Heading3'],
        fontSize=11, textColor=WINDI_TEAL, spaceBefore=10,
        spaceAfter=6, fontName='Helvetica-Bold')
    
    body_style = ParagraphStyle('Body', parent=styles['Normal'],
        fontSize=10, textColor=WINDI_DARK, alignment=TA_JUSTIFY,
        spaceAfter=10, leading=14, fontName='Helvetica')
    
    german_style = ParagraphStyle('German', parent=body_style,
        fontName='Helvetica-Oblique', textColor=WINDI_GRAY, fontSize=9)
    
    # Generate receipt
    receipt = generate_receipt(f"Capability{data['date']}", "WINDI-System")
    
    # Fetch live artifacts
    artifacts = get_registered_artifacts()
    
    elements = []
    
    # === HEADER ===
    elements.append(Paragraph("FORSCHUNGSFÄHIGKEITSNACHWEIS", subtitle_style))
    elements.append(Paragraph(data['title_en'], title_style))
    elements.append(Paragraph(data['subtitle'], subtitle_style))
    elements.append(Spacer(1, 0.3*cm))
    
    # Institution box
    inst_data = [
        [data['institution']['name']],
        [data['institution']['type']],
        [data['institution']['location']],
        [f"Focus: {data['institution']['focus']}"]
    ]
    inst_table = Table(inst_data, colWidths=[15*cm])
    inst_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), WINDI_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOX', (0, 0), (-1, -1), 1, WINDI_BLUE),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(inst_table)
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph(f"Date: {data['date']} | Version: {data['version']}", subtitle_style))
    
    # === EXECUTIVE SUMMARY ===
    elements.append(Paragraph("Executive Summary", heading_style))
    elements.append(Paragraph(data['executive_summary_en'], body_style))
    elements.append(Paragraph(data['executive_summary_de'], german_style))
    
    elements.append(PageBreak())
    
    # === DEMONSTRATED CAPABILITIES ===
    elements.append(Paragraph("Demonstrated Technical Capabilities", heading_style))
    elements.append(Paragraph("Nachgewiesene technische Fähigkeiten", german_style))
    elements.append(Spacer(1, 0.3*cm))
    
    for i, cap in enumerate(data['capabilities'], 1):
        elements.append(Paragraph(f"{i}. {cap['name_en']}", subhead_style))
        elements.append(Paragraph(cap['desc_en'], body_style))
        elements.append(Paragraph(f"<i>{cap['name_de']}: {cap['desc_de']}</i>", german_style))
        elements.append(Paragraph(f"<b>Evidence:</b> {cap['evidence']}", 
            ParagraphStyle('Evidence', parent=body_style, fontSize=9, textColor=WINDI_TEAL)))
        elements.append(Spacer(1, 0.2*cm))
    
    elements.append(PageBreak())
    
    # === LIVE EVIDENCE: REGISTERED ARTIFACTS ===
    elements.append(Paragraph("Live Evidence: Registered Governance Artifacts", heading_style))
    elements.append(Paragraph("Lebende Evidenz: Registrierte Governance-Artefakte", german_style))
    elements.append(Spacer(1, 0.3*cm))
    
    # Build artifacts table from live database
    artifact_header = ['Receipt ID', 'Type', 'Title', 'Status']
    artifact_rows = [artifact_header]
    
    for art in artifacts:
        artifact_rows.append([
            art[0][:28] + '...' if len(art[0]) > 28 else art[0],
            art[1],
            art[2][:35] + '...' if len(art[2]) > 35 else art[2],
            art[4] if art[4] else 'VALID'
        ])
    
    if len(artifact_rows) > 1:
        art_table = Table(artifact_rows, colWidths=[5*cm, 2.5*cm, 5.5*cm, 2*cm])
        art_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), WINDI_TEAL),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (-1, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, WINDI_GRAY),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TEXTCOLOR', (-1, 1), (-1, -1), WINDI_TEAL),
            ('FONTNAME', (-1, 1), (-1, -1), 'Helvetica-Bold'),
        ]))
        elements.append(art_table)
    
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(
        f"<i>Total registered artifacts: {len(artifacts)} | All artifacts publicly verifiable via /verify/&lt;receipt&gt;</i>",
        ParagraphStyle('Note', fontSize=9, textColor=WINDI_GRAY, alignment=TA_CENTER)))
    
    # === RESEARCH RELEVANCE ===
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("Research Relevance | Forschungsrelevanz", heading_style))
    elements.append(Paragraph(data['research_relevance_en'].replace('\n', '<br/>'), body_style))
    elements.append(Paragraph(data['research_relevance_de'].replace('\n', '<br/>'), german_style))
    
    # === PRINCIPLE BOX ===
    elements.append(Spacer(1, 0.5*cm))
    principle_data = [
        ['Core Governance Principle | Kern-Governance-Prinzip'],
        [data['principle']['en']],
        [data['principle']['de']],
        [data['principle']['pt']]
    ]
    principle_table = Table(principle_data, colWidths=[15*cm])
    principle_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), WINDI_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOX', (0, 0), (-1, -1), 2, WINDI_BLUE),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TEXTCOLOR', (0, 1), (-1, -1), WINDI_DARK),
    ]))
    elements.append(principle_table)
    
    elements.append(PageBreak())
    
    # === CERTIFICATION ===
    elements.append(Paragraph("NUR MENSCH / HUMAN ONLY", ParagraphStyle('Warning',
        parent=heading_style, textColor=HexColor('#dc2626'), fontSize=14, alignment=TA_CENTER)))
    elements.append(Paragraph("Institutional Certification | Institutionelle Zertifizierung", subtitle_style))
    elements.append(Spacer(1, 0.3*cm))
    
    cert_data = [
        ['CAPABILITY STATEMENT CERTIFICATION'],
        [''],
        ['I certify that the technical capabilities described in this document'],
        ['have been demonstrated and validated as of the date indicated.'],
        [''],
        ['Ich bestätige, dass die in diesem Dokument beschriebenen technischen'],
        ['Fähigkeiten zum angegebenen Datum demonstriert und validiert wurden.'],
        [''],
        [''],
        ['Certifying Authority / Zertifizierende Stelle:'],
        [''],
        ['Name: _________________________________________________'],
        [''],
        ['Title / Titel: _________________________________________'],
        [''],
        ['Organization: WINDI Publishing House'],
        [''],
        ['Date / Datum: _________________________________________'],
        [''],
        ['Signature / Unterschrift: ______________________________'],
        [''],
        [''],
        ['☐ CERTIFIED / ZERTIFIZIERT    ☐ PENDING REVIEW / IN PRÜFUNG']
    ]
    
    cert_table = Table(cert_data, colWidths=[15*cm])
    cert_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#fef2f2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#991b1b')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOX', (0, 0), (-1, -1), 2, HexColor('#dc2626')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(cert_table)
    
    elements.append(Spacer(1, 0.8*cm))
    
    # === WINDI RECEIPT ===
    elements.append(HRFlowable(width="100%", thickness=2, color=WINDI_BLUE))
    elements.append(Spacer(1, 0.3*cm))
    
    verify_url = f"https://windi.publish/verify/{receipt['id']}"
    qr_verify = generate_qr_code(verify_url)
    qr_img = Image(qr_verify, width=2.5*cm, height=2.5*cm)
    
    receipt_style = ParagraphStyle('Receipt', fontSize=9, textColor=WINDI_GRAY, alignment=TA_CENTER)
    
    receipt_data = [
        [qr_img, 
         Paragraph(f'''<b>WINDI-RECEIPT</b><br/>
         <font size="8" color="#1e40af">{receipt['id']}</font><br/>
         <font size="7">Hash: {receipt['hash']}</font><br/>
         <font size="7">{receipt['timestamp'][:19]}</font><br/>
         <font size="8"><b>Executable Governance Capability Statement</b></font>''', receipt_style)]
    ]
    
    receipt_table = Table(receipt_data, colWidths=[3*cm, 12*cm])
    receipt_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(receipt_table)
    
    # Build
    doc.build(elements)
    buffer.seek(0)
    
    # Register
    register_document(
        receipt['id'],
        'Capability Statement',
        'Research Capability Statement - Executable Governance',
        receipt['hash']
    )
    
    return buffer.getvalue(), receipt

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
    print("=" * 60)
    print("🏛️ Gerando: Research Capability Statement")
    print("🏛️ Executable Governance Document Generation System")
    print("=" * 60)
    
    pdf_bytes, receipt = generate_capability_statement_pdf(CAPABILITY_DATA)
    
    output_path = '/opt/windi/templates/WINDI_Capability_Statement_2026-01-28.pdf'
    with open(output_path, 'wb') as f:
        f.write(pdf_bytes)
    
    print(f"PDF gerado: {output_path}")
    print(f"Receipt ID: {receipt['id']}")
    print(f"Hash: {receipt['hash']}")
    print("=" * 60)
    print("🏛️ Ready for BMBF / University / Institutional Partners 🏛️")
    print("=" * 60)
