#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WINDI Style Research Engine - Academic Whitepaper Generator
28 Janeiro 2026 - EU AI Act Compliant
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import HexColor
from io import BytesIO
from datetime import datetime
import hashlib
import sqlite3

WINDI_TEAL = HexColor('#0d9488')
WINDI_DARK = HexColor('#1e293b')
WINDI_GRAY = HexColor('#64748b')
WINDI_PURPLE = HexColor('#7c3aed')

def register_document(receipt_number, doc_type, title, db_path='/opt/windi/data/template_registry.db'):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO documents_registry (receipt_number, document_type, document_title) VALUES (?, ?, ?)",
                      (receipt_number, doc_type, title))
        conn.commit()
        conn.close()
        print(f"✅ Document registered: {receipt_number}")
    except Exception as e:
        print(f"⚠️ Registration note: {e}")

def generate_whitepaper():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2.5*cm, leftMargin=2.5*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    
    style_title = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, textColor=WINDI_DARK, alignment=TA_CENTER, spaceAfter=20)
    style_subtitle = ParagraphStyle('Subtitle', parent=styles['Heading2'], fontSize=14, textColor=WINDI_TEAL, alignment=TA_CENTER, spaceAfter=30)
    style_h1 = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=16, textColor=WINDI_TEAL, spaceBefore=20, spaceAfter=10)
    style_h2 = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=13, textColor=WINDI_DARK, spaceBefore=15, spaceAfter=8)
    style_body = ParagraphStyle('Body', parent=styles['Normal'], fontSize=11, textColor=WINDI_DARK, alignment=TA_JUSTIFY, spaceAfter=10, leading=14)
    style_abstract = ParagraphStyle('Abstract', parent=styles['Normal'], fontSize=10, textColor=WINDI_GRAY, alignment=TA_JUSTIFY, leftIndent=1*cm, rightIndent=1*cm, spaceAfter=20, leading=13)
    
    elements = []
    
    # TÍTULO
    elements.append(Paragraph("WINDI Style Research Engine", style_title))
    elements.append(Paragraph("Institutional Style Learning with Constitutional Governance<br/>A Pre-AI Governance Layer Innovation", style_subtitle))
    elements.append(Paragraph(f"<b>Version:</b> 1.1.0 | <b>Date:</b> 28 January 2026 | <b>Status:</b> Production Ready",
                             ParagraphStyle('Meta', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, textColor=WINDI_GRAY)))
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=1, color=WINDI_TEAL))
    elements.append(Spacer(1, 20))
    
    # ABSTRACT
    elements.append(Paragraph("<b>Abstract</b>", style_h2))
    abstract_text = ("The WINDI Style Research Engine introduces a novel approach to institutional document generation "
                    "that learns formatting patterns from authoritative sources while maintaining strict governance controls. "
                    "Unlike traditional LLM-based systems that risk content fabrication, our system extracts only structural "
                    "patterns—headings, tone, formatting conventions—from a whitelisted set of institutional domains. "
                    "This paper presents the architecture, implementation, and EU AI Act compliance aspects of the Style "
                    "Research Engine, demonstrating how AI systems can learn from the real world without compromising "
                    "human sovereignty over decision-making.")
    elements.append(Paragraph(abstract_text, style_abstract))
    
    # 1. INTRODUCTION
    elements.append(Paragraph("1. Introduction", style_h1))
    intro1 = ("The challenge of generating institutional documents that conform to established formatting standards "
             "has traditionally required either rigid templates or unconstrained AI generation. Rigid templates lack "
             "adaptability; unconstrained AI risks producing content that appears authoritative but may contain "
             "fabricated information. The WINDI Style Research Engine addresses this challenge through a third "
             "approach: governed pattern learning.")
    elements.append(Paragraph(intro1, style_body))
    
    intro2 = ("Our system operates under the WINDI constitutional framework, which enforces the principle: "
             "<i>\"AI processes. Human decides. WINDI guarantees.\"</i> This means the AI may assist with document "
             "structure and formatting, but all substantive decisions—approvals, rejections, legal determinations—remain "
             "exclusively in human hands through \"Nur Mensch\" (Human-Only) fields.")
    elements.append(Paragraph(intro2, style_body))
    
    # 2. EU AI ACT COMPLIANCE
    elements.append(Paragraph("2. EU AI Act Compliance", style_h1))
    compliance_intro = ("The Style Research Engine was designed with EU AI Act (Regulation 2024/1689) compliance as a "
                       "foundational requirement, not an afterthought. The following table maps our technical controls to "
                       "specific regulatory requirements:")
    elements.append(Paragraph(compliance_intro, style_body))
    
    compliance_data = [
        ['EU AI Act Article', 'Requirement', 'WINDI Implementation'],
        ['Art. 13 - Transparency', 'AI systems must be transparent', 'Style profiles as human-readable JSON'],
        ['Art. 14 - Human Oversight', 'Meaningful human control', '"Nur Mensch" fields block AI decisions'],
        ['Art. 15 - Accuracy', 'Appropriate accuracy levels', 'Constitutional Validator, Score ≥70'],
        ['Art. 50 - Transparency', 'Users must be informed', 'AI disclosure on every document'],
        ['Art. 9 - Risk Management', 'Risk management system', 'Whitelist governance, fail-closed'],
    ]
    
    compliance_table = Table(compliance_data, colWidths=[3.5*cm, 4.5*cm, 7*cm])
    compliance_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), WINDI_TEAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, WINDI_GRAY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#ffffff'), HexColor('#f8fafc')]),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(compliance_table)
    elements.append(Spacer(1, 15))
    
    # 3. ARCHITECTURE
    elements.append(Paragraph("3. System Architecture", style_h1))
    arch_intro = "The Style Research Engine consists of six interconnected modules, each with specific governance responsibilities:"
    elements.append(Paragraph(arch_intro, style_body))
    
    elements.append(Paragraph("3.1 Domain Whitelist (domains.py)", style_h2))
    whitelist_text = ("The first line of defense is a strict whitelist of permitted source domains. Only institutional, "
                     "academic, and governmental sources are allowed: EU institutions (europa.eu), German federal government "
                     "(bundesregierung.de, bmbf.de), academic institutions (mit.edu, stanford.edu, tu-muenchen.de), and "
                     "international organizations (iso.org, who.int). Any URL not matching the whitelist is rejected.")
    elements.append(Paragraph(whitelist_text, style_body))
    
    elements.append(Paragraph("3.2 Secure Fetcher (fetcher.py)", style_h2))
    fetcher_text = ("The fetcher implements multiple security controls: 15-second timeout, 2MB maximum download size, "
                   "content-type validation (HTML only), and SSL certificate verification. Any failure results in "
                   "rejection—the system never proceeds with partial or uncertain data.")
    elements.append(Paragraph(fetcher_text, style_body))
    
    elements.append(Paragraph("3.3 Pattern Extractor (extractor.py)", style_h2))
    extractor_text = ("This is the core innovation: the extractor analyzes HTML structure to identify patterns WITHOUT "
                     "copying content. It extracts: heading hierarchy, section patterns, tone indicators, formatting signals, "
                     "and voice patterns. The output is metadata about structure, never the content itself.")
    elements.append(Paragraph(extractor_text, style_body))
    
    elements.append(Paragraph("3.4 Style Profiler (profiler.py)", style_h2))
    profiler_text = ("Extracted patterns are normalized into a StyleProfile JSON structure. Each profile includes a "
                    "cryptographic hash for integrity verification and timestamps for audit purposes.")
    elements.append(Paragraph(profiler_text, style_body))
    
    # 4. RESULTS
    elements.append(Paragraph("4. Implementation Results", style_h1))
    results_intro = "The Style Research Engine was deployed on 28 January 2026 and demonstrated successful pattern learning:"
    elements.append(Paragraph(results_intro, style_body))
    
    results_data = [
        ['Style Profile', 'Source', 'Headings', 'Tone', 'Status'],
        ['EU Official Document', 'europa.eu', '5', 'Neutral', 'Cached'],
        ['BMBF Research Format', 'bmbf.de', '16', 'Active', 'Cached'],
        ['German Government', 'bundesregierung.de', '-', '-', 'Available'],
        ['MIT Technical Report', 'mit.edu', '-', '-', 'Available'],
    ]
    
    results_table = Table(results_data, colWidths=[4*cm, 3.5*cm, 2*cm, 2*cm, 2.5*cm])
    results_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), WINDI_PURPLE),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, WINDI_GRAY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#ffffff'), HexColor('#f8fafc')]),
    ]))
    elements.append(results_table)
    elements.append(Spacer(1, 15))
    
    results_text = ("Integration testing with the WINDI Bescheid generator confirmed that style detection and application "
                   "works seamlessly. Documents with EU-Format or BMBF-Format specifications correctly display the applied "
                   "style while maintaining Quality Scores of 97/100 under Constitutional Validator review.")
    elements.append(Paragraph(results_text, style_body))
    
    # 5. KEY INNOVATIONS
    elements.append(Paragraph("5. Key Innovations", style_h1))
    
    innov1 = ("<b>Pattern Learning, Not Content Copying:</b> The system extracts structural metadata without ever "
             "copying or storing actual content from source documents. This eliminates copyright concerns while "
             "enabling genuine style learning.")
    elements.append(Paragraph(innov1, style_body))
    
    innov2 = ("<b>Governed Internet Access:</b> Rather than allowing unrestricted web access, the system operates "
             "within a strict whitelist. This represents a middle ground between isolated template systems and "
             "unrestricted AI agents.")
    elements.append(Paragraph(innov2, style_body))
    
    innov3 = ("<b>Constitutional Integration:</b> Style application is integrated with the WINDI Constitutional "
             "Validator, ensuring that stylistic changes never override governance controls.")
    elements.append(Paragraph(innov3, style_body))
    
    # 6. CONCLUSION
    elements.append(Paragraph("6. Conclusion", style_h1))
    conclusion1 = ("The WINDI Style Research Engine demonstrates that AI systems can learn from real-world institutional "
                  "sources while maintaining strict governance controls. By extracting patterns rather than content, "
                  "and by operating within a constitutional framework, the system achieves adaptability and control.")
    elements.append(Paragraph(conclusion1, style_body))
    
    conclusion2 = ("This work contributes to the emerging field of Pre-AI Governance Layers—systems that structure "
                  "AI capabilities within human-defined constraints. As the EU AI Act comes into effect, such approaches "
                  "will be essential for organizations seeking to leverage AI while maintaining compliance.")
    elements.append(Paragraph(conclusion2, style_body))
    
    motto = "<i>\"AI processes. Human decides. WINDI guarantees.\"</i>"
    elements.append(Paragraph(motto, ParagraphStyle('Motto', parent=style_body, alignment=TA_CENTER, textColor=WINDI_TEAL, fontSize=12, spaceBefore=20)))
    
    # FOOTER
    elements.append(Spacer(1, 30))
    elements.append(HRFlowable(width="100%", thickness=1, color=WINDI_GRAY))
    elements.append(Spacer(1, 10))
    
    timestamp = datetime.now().strftime("%d%b%y").upper()
    content_hash = hashlib.sha256(f"style-whitepaper-{timestamp}".encode()).hexdigest()[:8].upper()
    receipt_id = f"WINDI-WP-{timestamp}-{content_hash}"
    
    elements.append(Paragraph(f"<b>WINDI-RECEIPT:</b> {receipt_id}", ParagraphStyle('Receipt', parent=styles['Normal'], fontSize=9, textColor=WINDI_GRAY)))
    elements.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | <b>Publisher:</b> WINDI Publishing House, Kempten",
                             ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, textColor=WINDI_GRAY)))
    elements.append(Paragraph("This document was generated with AI assistance under WINDI Constitutional Governance. EU AI Act Art. 50 Transparency Disclosure.",
                             ParagraphStyle('Disclosure', parent=styles['Normal'], fontSize=8, textColor=WINDI_GRAY, spaceBefore=10)))
    
    doc.build(elements)
    buffer.seek(0)
    register_document(receipt_id, "Whitepaper", "WINDI Style Research Engine - Academic Whitepaper")
    
    return buffer.getvalue(), {'id': receipt_id, 'hash': content_hash.lower(), 'type': 'Whitepaper'}


if __name__ == '__main__':
    print("=" * 60)
    print("🎓 Generating: WINDI Style Research Engine Whitepaper")
    print("🎓 EU AI Act Compliant - For Academic Publication")
    print("=" * 60)
    
    pdf_bytes, receipt = generate_whitepaper()
    
    output_path = '/opt/windi/templates/WINDI_Style_Research_Whitepaper.pdf'
    with open(output_path, 'wb') as f:
        f.write(pdf_bytes)
    
    print(f"PDF saved: {output_path}")
    print(f"Receipt ID: {receipt['id']}")
    print("=" * 60)
    print("🎓 Ready for Master Arbeiten / Academic Publication!")
