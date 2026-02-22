#!/usr/bin/env python3
"""
WINDI PDF Renderer — PDF Document Generation
Uses reportlab for communiqués, certificates, governance decisions, and formal PDFs.
"""

import re
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm, mm
    from reportlab.lib.colors import HexColor
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, HRFlowable
    )
    from reportlab.pdfgen import canvas
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

# ── WINDI Design Tokens ──
GOLD = HexColor("#8B6914") if HAS_REPORTLAB else None
DARK = HexColor("#2C2924") if HAS_REPORTLAB else None
DIM = HexColor("#6B6560") if HAS_REPORTLAB else None
PARCHMENT = HexColor("#F5F0E0") if HAS_REPORTLAB else None
BORDER = HexColor("#DDD6C2") if HAS_REPORTLAB else None
WHITE = HexColor("#FFFFFF") if HAS_REPORTLAB else None


def render_pdf(context, filepath):
    """Render a PDF document from context."""
    if not HAS_REPORTLAB:
        raise ImportError("reportlab not installed. Run: pip install reportlab")

    doc_type = context.get("doc_type", "report")
    language = context.get("language", "de")

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        topMargin=2.5 * cm,
        bottomMargin=2 * cm,
        leftMargin=2.5 * cm,
        rightMargin=2 * cm,
    )

    styles = _build_styles()
    story = []

    # Header info
    _add_header_block(story, styles, context)

    # Body content
    _render_body(story, styles, context)

    # Governance seal
    _add_governance_seal(story, styles, context)

    # Build with custom header/footer
    doc.build(story, onFirstPage=_page_template, onLaterPages=_page_template)


def _build_styles():
    """Create WINDI-branded paragraph styles."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="WINDITitle",
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=DARK,
        spaceAfter=6,
        leading=26,
    ))

    styles.add(ParagraphStyle(
        name="WINDIHeading1",
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=DARK,
        spaceBefore=18,
        spaceAfter=8,
        leading=20,
    ))

    styles.add(ParagraphStyle(
        name="WINDIHeading2",
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=DARK,
        spaceBefore=14,
        spaceAfter=6,
        leading=16,
    ))

    styles.add(ParagraphStyle(
        name="WINDIBody",
        fontName="Helvetica",
        fontSize=10.5,
        textColor=DARK,
        spaceAfter=6,
        leading=14,
    ))

    styles.add(ParagraphStyle(
        name="WINDIBullet",
        fontName="Helvetica",
        fontSize=10.5,
        textColor=DARK,
        leftIndent=20,
        spaceAfter=4,
        leading=14,
        bulletIndent=8,
    ))

    styles.add(ParagraphStyle(
        name="WINDIMeta",
        fontName="Helvetica",
        fontSize=8.5,
        textColor=DIM,
        spaceAfter=3,
    ))

    styles.add(ParagraphStyle(
        name="WINDIGold",
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=GOLD,
        spaceAfter=2,
    ))

    styles.add(ParagraphStyle(
        name="WINDISeal",
        fontName="Courier",
        fontSize=7.5,
        textColor=DIM,
        spaceAfter=2,
        leading=10,
    ))

    return styles


def _add_header_block(story, styles, context):
    """Add document header with type, date, entities."""
    doc_type = context.get("doc_type", "note")
    language = context.get("language", "de")
    entities = context.get("entities", {})
    isp = context.get("isp", {})

    type_labels = {
        "de": {"communique": "Communiqué", "governance_decision": "Governance-Beschluss",
               "certificate": "Bescheinigung", "security_advisory": "Sicherheitshinweis",
               "report": "Bericht", "analysis": "Analyse"},
        "en": {"communique": "Communiqué", "governance_decision": "Governance Decision",
               "certificate": "Certificate", "security_advisory": "Security Advisory",
               "report": "Report", "analysis": "Analysis"},
        "pt": {"communique": "Comunicado", "governance_decision": "Decisão de Governança",
               "certificate": "Certificado", "security_advisory": "Alerta de Segurança",
               "report": "Relatório", "analysis": "Análise"},
    }

    labels = type_labels.get(language, type_labels["en"])
    title = labels.get(doc_type, doc_type.replace("_", " ").title())

    # Organization
    org = isp.get("organization", "WINDI Publishing House")
    story.append(Paragraph(org, styles["WINDIMeta"]))

    # Title
    story.append(Spacer(1, 8))
    story.append(Paragraph(title, styles["WINDITitle"]))

    # Date
    date_str = datetime.now().strftime("%d.%m.%Y" if language == "de" else "%Y-%m-%d")
    story.append(Paragraph(date_str, styles["WINDIMeta"]))

    # Entities
    meta_parts = []
    if entities.get("org"):
        meta_parts.append(" | ".join(entities["org"]))
    if entities.get("person"):
        meta_parts.append(" | ".join(entities["person"]))
    if meta_parts:
        story.append(Paragraph(" · ".join(meta_parts), styles["WINDIMeta"]))

    # Separator
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=12))


def _render_body(story, styles, context):
    """Convert markdown text to PDF flowables."""
    text = context.get("text", "")
    lines = text.strip().split("\n")

    for line in lines:
        stripped = line.strip()

        if not stripped:
            story.append(Spacer(1, 6))
            continue

        # Headings
        if stripped.startswith("### "):
            clean = _sanitize_for_reportlab(stripped[4:])
            story.append(Paragraph(clean, styles["WINDIHeading2"]))
        elif stripped.startswith("## "):
            clean = _sanitize_for_reportlab(stripped[3:])
            story.append(Paragraph(clean, styles["WINDIHeading1"]))
        elif stripped.startswith("# "):
            clean = _sanitize_for_reportlab(stripped[2:])
            story.append(Paragraph(clean, styles["WINDITitle"]))
        # Bullets
        elif stripped.startswith("- ") or stripped.startswith("• ") or stripped.startswith("* "):
            content = _md_to_reportlab(stripped[2:])
            story.append(Paragraph(f"•  {content}", styles["WINDIBullet"]))
        # Numbered list
        elif re.match(r"^\d+[\.\)]\s", stripped):
            content = re.sub(r"^\d+[\.\)]\s", "", stripped)
            content = _md_to_reportlab(content)
            story.append(Paragraph(content, styles["WINDIBullet"]))
        # Horizontal rule
        elif stripped in ("---", "***", "___"):
            story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=8, spaceAfter=8))
        # Table
        elif "|" in stripped and stripped.startswith("|"):
            # Collect table lines
            # (handled inline as we process line by line - simplified for now)
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if not all(re.match(r"^[\s\-:]+$", c) for c in cells):
                row_text = "  |  ".join(cells)
                story.append(Paragraph(_sanitize_for_reportlab(row_text), styles["WINDIBody"]))
        # Regular paragraph
        else:
            content = _md_to_reportlab(stripped)
            story.append(Paragraph(content, styles["WINDIBody"]))


def _add_governance_seal(story, styles, context):
    """Add WINDI governance seal at document end."""
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=8))

    # Seal header
    story.append(Paragraph("WINDI-RECEIPT", styles["WINDIGold"]))

    # Metadata
    tier = context.get("tier", "HIGH")
    sge = context.get("sge", {})
    receipt = context.get("receipt")

    fields = [
        f"Tier: {tier}  |  SGE: {sge.get('score', '—')}  |  Risk: {sge.get('risk', '—')}",
        f"Timestamp: {context.get('timestamp', '—')}",
    ]

    if receipt:
        fields.append(f"Hash: {receipt.get('hash', '—')[:32]}...")

    for field in fields:
        story.append(Paragraph(field, styles["WINDISeal"]))

    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "AI processes. Human decides. WINDI guarantees.",
        styles["WINDIGold"]
    ))


def _page_template(canvas_obj, doc):
    """Add header/footer to each page."""
    canvas_obj.saveState()

    # Header gold line
    canvas_obj.setStrokeColor(GOLD)
    canvas_obj.setLineWidth(2)
    canvas_obj.line(2 * cm, A4[1] - 1.5 * cm, A4[0] - 2 * cm, A4[1] - 1.5 * cm)

    # Header text
    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.setFillColor(DIM)
    canvas_obj.drawRightString(A4[0] - 2 * cm, A4[1] - 1.3 * cm, "WINDI Governance")

    # Footer
    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.setFillColor(DIM)
    canvas_obj.drawString(2.5 * cm, 1.2 * cm,
                          "WINDI Publishing House · Pre-AI Governance Layer")
    canvas_obj.drawRightString(A4[0] - 2 * cm, 1.2 * cm,
                               f"Page {doc.page}")

    # Footer gold line
    canvas_obj.setStrokeColor(GOLD)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(2 * cm, 1.5 * cm, A4[0] - 2 * cm, 1.5 * cm)

    canvas_obj.restoreState()


def _md_to_reportlab(text):
    """Convert markdown inline formatting to reportlab XML."""
    # Bold
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    # Italic
    text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', text)
    # Code
    text = re.sub(r'`([^`]+)`', r'<font face="Courier" size="9" color="#8B4513">\1</font>', text)
    # Sanitize remaining special chars
    return _sanitize_for_reportlab(text, preserve_tags=True)


def _sanitize_for_reportlab(text, preserve_tags=False):
    """Sanitize text for reportlab XML paragraphs."""
    if preserve_tags:
        # Only escape & that aren't part of entities and < > that aren't tags
        text = re.sub(r'&(?!amp;|lt;|gt;|#\d+;)', '&amp;', text)
        return text
    else:
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        # Remove markdown bold/italic markers
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        return text
