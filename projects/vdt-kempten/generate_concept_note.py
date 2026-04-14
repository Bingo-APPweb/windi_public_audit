#!/usr/bin/env python3
"""
VDT Concept Note PDF Generator v1.1
Academic-ready format for IDT Kempten
"""

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from datetime import datetime

# Colors
GOLD = HexColor('#8B6914')
INK = HexColor('#1A1612')
INK2 = HexColor('#4A3F2F')
GRAY = HexColor('#7A6E5E')

def create_styles():
    styles = getSampleStyleSheet()

    # Title style
    styles.add(ParagraphStyle(
        name='DocTitle',
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=INK,
        spaceAfter=6,
        alignment=TA_CENTER
    ))

    # Subtitle
    styles.add(ParagraphStyle(
        name='Subtitle',
        fontName='Helvetica-Oblique',
        fontSize=11,
        textColor=INK2,
        spaceAfter=20,
        alignment=TA_CENTER
    ))

    # Section heading
    styles.add(ParagraphStyle(
        name='SectionHead',
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=GOLD,
        spaceBefore=16,
        spaceAfter=8,
        leftIndent=0
    ))

    # Body text
    styles.add(ParagraphStyle(
        name='Body',
        fontName='Helvetica',
        fontSize=10,
        textColor=INK,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=8
    ))

    # Quote/highlight
    styles.add(ParagraphStyle(
        name='Quote',
        fontName='Helvetica-Oblique',
        fontSize=10,
        textColor=INK2,
        leftIndent=20,
        rightIndent=20,
        spaceBefore=8,
        spaceAfter=8,
        alignment=TA_CENTER
    ))

    # Keywords
    styles.add(ParagraphStyle(
        name='Keywords',
        fontName='Helvetica',
        fontSize=9,
        textColor=GRAY,
        spaceBefore=4,
        spaceAfter=16,
        alignment=TA_CENTER
    ))

    # Footer
    styles.add(ParagraphStyle(
        name='Footer',
        fontName='Helvetica-Oblique',
        fontSize=8,
        textColor=GRAY,
        alignment=TA_CENTER,
        spaceBefore=20
    ))

    # Bullet (renamed to avoid conflict with reportlab built-in)
    styles.add(ParagraphStyle(
        name='VDTBullet',
        fontName='Helvetica',
        fontSize=10,
        textColor=INK,
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=4
    ))

    return styles

def build_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2.5*cm,
        rightMargin=2.5*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = create_styles()
    story = []

    # === HEADER ===
    story.append(Paragraph("CONCEPT NOTE", styles['Keywords']))
    story.append(Paragraph("VDT — Verifiable Digital Transformation", styles['DocTitle']))
    story.append(Paragraph("A proof layer for organizational learning systems", styles['Subtitle']))

    # Keywords
    story.append(Paragraph(
        "<b>Keywords:</b> Proof of Human Oversight · Digital Transformation · EU AI Act Art.14 · Organizational Learning · KMU Onboarding",
        styles['Keywords']
    ))

    # === ABSTRACT ===
    story.append(Paragraph("Abstract", styles['SectionHead']))
    story.append(Paragraph(
        "This concept note proposes a joint research initiative to address the <b>Proof Gap</b> in digital transformation: "
        "the structural inability of current systems to verify that transformation processes were actually executed as designed. "
        "We introduce the PHO Framework (Proof of Human Oversight) as a cryptographic proof layer for organizational learning, "
        "with application to the LeBi Interreg project's KMU onboarding methodology.",
        styles['Body']
    ))

    # === 1. RESEARCH PROBLEM ===
    story.append(Paragraph("1. Research Problem", styles['SectionHead']))
    story.append(Paragraph(
        "Digital transformation frameworks — in learning, onboarding, and organizational change — operate under a structural blind spot: "
        "<b>they can document process design, but not process proof.</b>",
        styles['Body']
    ))
    story.append(Paragraph(
        "Current systems measure adoption perception, training completion rates, and self-reported compliance. "
        "What they cannot measure is: who made which decision, when, under which authorization, and whether the agreed process was actually followed — not just recorded.",
        styles['Body']
    ))
    story.append(Paragraph(
        "We define this as the <b>Proof Gap</b>: the distance between documented transformation and verifiable transformation.",
        styles['Body']
    ))

    # === 2. RESEARCH QUESTION ===
    story.append(Paragraph("2. Research Question", styles['SectionHead']))
    story.append(Paragraph(
        "\"How can digital transformation and organizational learning processes be made <b>independently auditable and cryptographically verifiable</b> — not only documented — using proof-of-oversight mechanisms?\"",
        styles['Quote']
    ))
    story.append(Paragraph(
        "<b>Sub-questions:</b> (a) What constitutes valid proof of human decision in a learning process? "
        "(b) How can PHO be operationalized in onboarding? "
        "(c) What is the minimum viable proof layer for EU AI Act Article 14 compliance?",
        styles['Body']
    ))

    # === 3. METHODOLOGY ===
    story.append(Paragraph("3. Methodology", styles['SectionHead']))
    story.append(Paragraph(
        "<b>Empirical base:</b> 16+ KMU pilot companies from the LeBi Interreg project (Vorarlberg, Ostschweiz, Süddeutschland), Q1 2026 – Q4 2028.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>Intervention:</b> Integration of a PHO layer into LeBi's onboarding toolbox. Each critical decision step is anchored to an immutable ledger record: "
        "actor DID (decentralized identifier), timestamp, authorization level, process deviation (if any).",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>Measurement:</b> Comparative analysis of (a) documented process vs (b) proven process execution. Gap quantification. Human oversight coverage score (SGE).",
        styles['Body']
    ))

    # === PAGE BREAK ===
    story.append(PageBreak())

    # === 4. EXPECTED OUTPUTS ===
    story.append(Paragraph("4. Expected Outputs", styles['SectionHead']))

    story.append(Paragraph("<b>Academic:</b>", styles['Body']))
    story.append(Paragraph("• Peer-reviewed paper: \"From Digital Transformation to Verifiable Transformation\"", styles['VDTBullet']))
    story.append(Paragraph("• Framework definition and validation methodology", styles['VDTBullet']))
    story.append(Paragraph("• Empirical dataset from 16+ KMU pilots", styles['VDTBullet']))

    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Practical:</b>", styles['Body']))
    story.append(Paragraph("• Replicable PHO-onboarding integration model", styles['VDTBullet']))
    story.append(Paragraph("• Open methodology for KMU adoption", styles['VDTBullet']))
    story.append(Paragraph("• Certification pathway aligned with EU AI Act Art. 14", styles['VDTBullet']))

    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Societal:</b>", styles['Body']))
    story.append(Paragraph("• First empirical evidence base for proof-of-oversight in organizational learning in German-speaking Europe", styles['VDTBullet']))

    # === 5. EU ALIGNMENT ===
    story.append(Paragraph("5. EU Regulatory Alignment", styles['SectionHead']))
    story.append(Paragraph(
        "This initiative directly addresses <b>EU AI Act Article 14</b> (Human Oversight) and <b>GDPR Article 22</b> requirements "
        "for meaningful human involvement in automated systems. The PHO Framework was designed as a constitutional primitive, not a compliance patch.",
        styles['Body']
    ))
    story.append(Paragraph(
        "The GRC (Governance, Risk, Compliance) market is projected at €65B globally. "
        "A proof-based verification layer positions this research at the intersection of academic rigor and market relevance.",
        styles['Body']
    ))

    # === 6. PARTNERSHIP MODEL ===
    story.append(Paragraph("6. Partnership Model", styles['SectionHead']))

    # Table for contributions
    data = [
        ['IDT Kempten brings', 'PHO Framework brings'],
        ['Academic credibility', 'Proof of Human Oversight (PHO)'],
        ['Access to real KMUs', 'Decentralized Identity (DID)'],
        ['LeBi project infrastructure', 'Immutable ledger technology'],
        ['Interreg / EU network', 'Production-ready system'],
        ['Institutional language', 'EU AI Act alignment']
    ]

    table = Table(data, colWidths=[7*cm, 7*cm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, 0), GOLD),
        ('TEXTCOLOR', (0, 1), (-1, -1), INK),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, GOLD),
    ]))
    story.append(table)

    # === CLOSING NOTE ===
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "This is an initial working hypothesis intended to be refined together with IDT's research perspective. "
        "The framework presented here is functional but open — the academic framing, research design, and pilot scope "
        "are all areas where IDT's expertise would be essential to shape the final direction.",
        styles['Quote']
    ))

    # === FOOTER ===
    story.append(Spacer(1, 30))
    story.append(Paragraph(
        f"PHO Framework · WINDI Publishing House · Kempten, Bavaria<br/>"
        f"Concept Note v1.1 · {datetime.now().strftime('%B %Y')}",
        styles['Footer']
    ))

    # Build PDF
    doc.build(story)
    return output_path

if __name__ == "__main__":
    output = "/opt/windi/projects/vdt-kempten/VDT_Concept_Note_v1.1.pdf"
    build_pdf(output)
    print(f"PDF created: {output}")
