#!/usr/bin/env python3
"""
VDT Concept Note PDF Generator v1.1 — Deutsche Version
Akademisches Format für IDT Kempten
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

    styles.add(ParagraphStyle(
        name='DocTitle',
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=INK,
        spaceAfter=6,
        alignment=TA_CENTER
    ))

    styles.add(ParagraphStyle(
        name='Subtitle',
        fontName='Helvetica-Oblique',
        fontSize=11,
        textColor=INK2,
        spaceAfter=20,
        alignment=TA_CENTER
    ))

    styles.add(ParagraphStyle(
        name='SectionHead',
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=GOLD,
        spaceBefore=16,
        spaceAfter=8,
        leftIndent=0
    ))

    styles.add(ParagraphStyle(
        name='Body',
        fontName='Helvetica',
        fontSize=10,
        textColor=INK,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=8
    ))

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

    styles.add(ParagraphStyle(
        name='Keywords',
        fontName='Helvetica',
        fontSize=9,
        textColor=GRAY,
        spaceBefore=4,
        spaceAfter=16,
        alignment=TA_CENTER
    ))

    styles.add(ParagraphStyle(
        name='Footer',
        fontName='Helvetica-Oblique',
        fontSize=8,
        textColor=GRAY,
        alignment=TA_CENTER,
        spaceBefore=20
    ))

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
    story.append(Paragraph("KONZEPTPAPIER", styles['Keywords']))
    story.append(Paragraph("VDT — Verifizierbare Digitale Transformation", styles['DocTitle']))
    story.append(Paragraph("Eine Nachweisschicht für organisationale Lernsysteme", styles['Subtitle']))

    # Keywords
    story.append(Paragraph(
        "<b>Schlüsselbegriffe:</b> Proof of Human Oversight · Digitale Transformation · EU AI Act Art.14 · Organisationales Lernen · KMU-Onboarding",
        styles['Keywords']
    ))

    # === ABSTRACT ===
    story.append(Paragraph("Zusammenfassung", styles['SectionHead']))
    story.append(Paragraph(
        "Dieses Konzeptpapier schlägt eine gemeinsame Forschungsinitiative vor, um die <b>Nachweislücke</b> in der digitalen Transformation zu adressieren: "
        "die strukturelle Unfähigkeit aktueller Systeme zu verifizieren, dass Transformationsprozesse tatsächlich wie konzipiert ausgeführt wurden. "
        "Wir stellen das PHO Framework (Proof of Human Oversight) als kryptographische Nachweisschicht für organisationales Lernen vor, "
        "mit Anwendung auf die KMU-Onboarding-Methodik des LeBi Interreg-Projekts.",
        styles['Body']
    ))

    # === 1. FORSCHUNGSPROBLEM ===
    story.append(Paragraph("1. Forschungsproblem", styles['SectionHead']))
    story.append(Paragraph(
        "Frameworks für digitale Transformation — in Lernen, Onboarding und organisationalem Wandel — operieren unter einem strukturellen blinden Fleck: "
        "<b>Sie können Prozessdesign dokumentieren, aber nicht Prozessnachweis erbringen.</b>",
        styles['Body']
    ))
    story.append(Paragraph(
        "Aktuelle Systeme messen Adoptionswahrnehmung, Trainingsabschlussquoten und selbstberichtete Compliance. "
        "Was sie nicht messen können: Wer hat welche Entscheidung getroffen, wann, unter welcher Autorisierung, und ob der vereinbarte Prozess tatsächlich befolgt wurde — nicht nur dokumentiert.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Wir definieren dies als die <b>Nachweislücke</b> (Proof Gap): die Distanz zwischen dokumentierter Transformation und verifizierbarer Transformation.",
        styles['Body']
    ))

    # === 2. FORSCHUNGSFRAGE ===
    story.append(Paragraph("2. Forschungsfrage", styles['SectionHead']))
    story.append(Paragraph(
        "\"Wie können digitale Transformation und organisationale Lernprozesse <b>unabhängig auditierbar und kryptographisch verifizierbar</b> gemacht werden — nicht nur dokumentiert — mittels Proof-of-Oversight-Mechanismen?\"",
        styles['Quote']
    ))
    story.append(Paragraph(
        "<b>Unterfragen:</b> (a) Was konstituiert einen validen Nachweis menschlicher Entscheidung in einem Lernprozess? "
        "(b) Wie kann PHO im Onboarding operationalisiert werden? "
        "(c) Was ist die minimal tragfähige Nachweisschicht für EU AI Act Artikel 14 Compliance?",
        styles['Body']
    ))

    # === 3. METHODOLOGIE ===
    story.append(Paragraph("3. Methodologie", styles['SectionHead']))
    story.append(Paragraph(
        "<b>Empirische Basis:</b> 16+ KMU-Pilotunternehmen aus dem LeBi Interreg-Projekt (Vorarlberg, Ostschweiz, Süddeutschland), Q1 2026 – Q4 2028.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>Intervention:</b> Integration einer PHO-Schicht in LeBis Onboarding-Toolbox. Jeder kritische Entscheidungsschritt wird an einen unveränderlichen Ledger-Eintrag verankert: "
        "Akteur-DID (dezentraler Identifikator), Zeitstempel, Autorisierungsstufe, Prozessabweichung (falls vorhanden).",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>Messung:</b> Vergleichende Analyse von (a) dokumentiertem Prozess vs. (b) nachgewiesener Prozessausführung. Lückenquantifizierung. Human Oversight Coverage Score (SGE).",
        styles['Body']
    ))

    # === PAGE BREAK ===
    story.append(PageBreak())

    # === 4. ERWARTETE ERGEBNISSE ===
    story.append(Paragraph("4. Erwartete Ergebnisse", styles['SectionHead']))

    story.append(Paragraph("<b>Akademisch:</b>", styles['Body']))
    story.append(Paragraph("• Peer-Review-Publikation: \"Von Digitaler Transformation zu Verifizierbarer Transformation\"", styles['VDTBullet']))
    story.append(Paragraph("• Framework-Definition und Validierungsmethodologie", styles['VDTBullet']))
    story.append(Paragraph("• Empirischer Datensatz aus 16+ KMU-Pilotprojekten", styles['VDTBullet']))

    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Praktisch:</b>", styles['Body']))
    story.append(Paragraph("• Replizierbares PHO-Onboarding-Integrationsmodell", styles['VDTBullet']))
    story.append(Paragraph("• Offene Methodologie für KMU-Adoption", styles['VDTBullet']))
    story.append(Paragraph("• Zertifizierungspfad gemäß EU AI Act Art. 14", styles['VDTBullet']))

    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Gesellschaftlich:</b>", styles['Body']))
    story.append(Paragraph("• Erste empirische Evidenzbasis für Proof-of-Oversight in organisationalem Lernen im deutschsprachigen Europa", styles['VDTBullet']))

    # === 5. EU-REGULATORISCHE AUSRICHTUNG ===
    story.append(Paragraph("5. EU-Regulatorische Ausrichtung", styles['SectionHead']))
    story.append(Paragraph(
        "Diese Initiative adressiert direkt <b>EU AI Act Artikel 14</b> (Human Oversight) und <b>DSGVO Artikel 22</b> Anforderungen "
        "für bedeutsame menschliche Beteiligung in automatisierten Systemen. Das PHO Framework wurde als konstitutionelles Primitiv konzipiert, nicht als Compliance-Patch.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Der GRC-Markt (Governance, Risk, Compliance) wird global auf €65 Mrd. projiziert. "
        "Eine nachweisbasierte Verifikationsschicht positioniert diese Forschung an der Schnittstelle von akademischer Rigorosität und Marktrelevanz.",
        styles['Body']
    ))

    # === 6. PARTNERSCHAFTSMODELL ===
    story.append(Paragraph("6. Partnerschaftsmodell", styles['SectionHead']))

    data = [
        ['IDT Kempten bringt ein', 'PHO Framework bringt ein'],
        ['Akademische Glaubwürdigkeit', 'Proof of Human Oversight (PHO)'],
        ['Zugang zu realen KMUs', 'Dezentrale Identität (DID)'],
        ['LeBi-Projektinfrastruktur', 'Unveränderliche Ledger-Technologie'],
        ['Interreg / EU-Netzwerk', 'Produktionsreifes System'],
        ['Institutionelle Sprache', 'EU AI Act Alignment']
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
        "Dies ist eine erste Arbeitshypothese, die gemeinsam mit der Forschungsperspektive des IDT verfeinert werden soll. "
        "Das hier vorgestellte Framework ist funktional, aber offen — die akademische Rahmung, das Forschungsdesign und der Pilotumfang "
        "sind alles Bereiche, in denen die Expertise des IDT essentiell wäre, um die finale Richtung zu gestalten.",
        styles['Quote']
    ))

    # === FOOTER ===
    story.append(Spacer(1, 30))
    story.append(Paragraph(
        f"PHO Framework · WINDI Publishing House · Kempten, Bayern<br/>"
        f"Konzeptpapier v1.1 · {datetime.now().strftime('%B %Y')}",
        styles['Footer']
    ))

    doc.build(story)
    return output_path

if __name__ == "__main__":
    output = "/opt/windi/projects/vdt-kempten/VDT_Konzeptpapier_v1.1_DE.pdf"
    build_pdf(output)
    print(f"PDF erstellt: {output}")
