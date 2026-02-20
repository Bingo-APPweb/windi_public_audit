"""
WINDI M3 Export Engine v1.0.0
=============================
Server-side PDF generation with Dynamic Header Seal,
QR Code verification, and Forensic Receipt embedding.

Pipeline: D1 Frontend → FastAPI → Export Engine → PDF
Architecture: Stateless. Receives data, returns bytes. Zero storage.

Dependencies: reportlab, qrcode, pillow
"""

import io
import json
from tiptap_parser import tiptap_to_plaintext
import hashlib
import textwrap
from datetime import datetime, timezone

import qrcode
from qrcode.image.pil import PilImage

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics import renderPDF

# ═══════════════════════════════════════════════════════════════
# WINDI COLOR PALETTE (Noir Theme)
# ═══════════════════════════════════════════════════════════════
WINDI_BLACK = colors.HexColor("#0A0A0A")
WINDI_DARK = colors.HexColor("#1A1A1A")
WINDI_GOLD = colors.HexColor("#C5A55A")
WINDI_GOLD_LIGHT = colors.HexColor("#D4B96E")
WINDI_WHITE = colors.HexColor("#F5F5F0")
WINDI_GREY = colors.HexColor("#888888")
WINDI_GREEN = colors.HexColor("#2ECC71")
WINDI_RED = colors.HexColor("#E74C3C")

# Page dimensions
PAGE_W, PAGE_H = A4
MARGIN_L = 20 * mm
MARGIN_R = 20 * mm
MARGIN_T = 25 * mm
MARGIN_B = 25 * mm
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R


# ═══════════════════════════════════════════════════════════════
# STYLES
# ═══════════════════════════════════════════════════════════════

def get_windi_styles():
    """Return WINDI-branded paragraph styles."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='WINDI_Title',
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=WINDI_BLACK,
        spaceAfter=6 * mm,
        alignment=TA_LEFT,
    ))

    styles.add(ParagraphStyle(
        name='WINDI_H1',
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=WINDI_BLACK,
        spaceBefore=8 * mm,
        spaceAfter=4 * mm,
        alignment=TA_LEFT,
    ))

    styles.add(ParagraphStyle(
        name='WINDI_H2',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=WINDI_DARK,
        spaceBefore=6 * mm,
        spaceAfter=3 * mm,
        alignment=TA_LEFT,
    ))

    styles.add(ParagraphStyle(
        name='WINDI_Body',
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=WINDI_BLACK,
        spaceAfter=3 * mm,
        alignment=TA_JUSTIFY,
    ))

    styles.add(ParagraphStyle(
        name='WINDI_Small',
        fontName='Helvetica',
        fontSize=7,
        leading=9,
        textColor=WINDI_GREY,
        alignment=TA_LEFT,
    ))

    styles.add(ParagraphStyle(
        name='WINDI_Mono',
        fontName='Courier',
        fontSize=8,
        leading=10,
        textColor=WINDI_DARK,
        alignment=TA_LEFT,
    ))

    styles.add(ParagraphStyle(
        name='WINDI_SealTitle',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=WINDI_GOLD,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name='WINDI_SealBody',
        fontName='Courier',
        fontSize=7,
        leading=9,
        textColor=WINDI_DARK,
        alignment=TA_LEFT,
    ))

    styles.add(ParagraphStyle(
        name='WINDI_Footer',
        fontName='Helvetica',
        fontSize=6.5,
        leading=8,
        textColor=WINDI_GREY,
        alignment=TA_CENTER,
    ))

    return styles


# ═══════════════════════════════════════════════════════════════
# QR CODE GENERATOR
# ═══════════════════════════════════════════════════════════════

def generate_qr_code(data_dict, size_px=200):
    """
    Generate a QR code image from verification data.
    Returns a PIL Image.
    """
    # Compact JSON for QR
    qr_payload = json.dumps({
        "sys": "WINDI",
        "ver": "1.0",
        "rid": data_dict.get("receipt_id", ""),
        "hash": data_dict.get("content_hash", "")[:16],
        "ts": data_dict.get("timestamp", ""),
        "status": data_dict.get("status", "REGISTERED"),
    }, separators=(',', ':'))

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(qr_payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#1A1A1A", back_color="#F5F5F0")
    return img.get_image()


def qr_to_reportlab_image(pil_img, width_mm=28):
    """Convert PIL image to ReportLab Image flowable."""
    buf = io.BytesIO()
    pil_img.save(buf, format='PNG')
    buf.seek(0)
    return Image(buf, width=width_mm * mm, height=width_mm * mm)


# ═══════════════════════════════════════════════════════════════
# DYNAMIC HEADER SEAL (M3 Core)
# ═══════════════════════════════════════════════════════════════

class DynamicHeaderSeal:
    """
    WINDI Dynamic Header Seal — the M3 centerpiece.
    Renders a professional governance seal with:
    - WINDI branding bar
    - Receipt ID + Hash
    - Timestamp + Status
    - QR code for verification
    - Integrity chain reference
    """

    def __init__(self, receipt_data: dict):
        self.receipt_id = receipt_data.get("receipt_id", "UNKNOWN")
        self.content_hash = receipt_data.get("content_hash", "0" * 64)
        self.timestamp = receipt_data.get("timestamp", datetime.now(timezone.utc).isoformat())
        self.status = receipt_data.get("status", "REGISTERED")
        self.doc_title = receipt_data.get("doc_title", "Untitled Document")
        self.sge_score = receipt_data.get("sge_score", None)
        self.risk_level = receipt_data.get("risk_level", None)

    def build_flowable(self, styles):
        """Return a list of flowables that compose the seal."""
        elements = []

        # Generate QR code
        qr_img = generate_qr_code({
            "receipt_id": self.receipt_id,
            "content_hash": self.content_hash,
            "timestamp": self.timestamp,
            "status": self.status,
        })
        qr_flowable = qr_to_reportlab_image(qr_img, width_mm=26)

        # ── Gold Header Bar ──
        gold_bar = HRFlowable(
            width="100%",
            thickness=3,
            color=WINDI_GOLD,
            spaceBefore=2 * mm,
            spaceAfter=2 * mm,
        )
        elements.append(gold_bar)

        # ── Seal Content Table ──
        # Left: metadata | Right: QR code
        hash_display = self.content_hash[:12] + "..." + self.content_hash[-8:]

        # Status badge color
        status_color = "#2ECC71" if self.status == "REGISTERED" else "#E74C3C"

        meta_text = f"""
        <font name="Helvetica-Bold" size="10" color="#C5A55A">WINDI GOVERNANCE SEAL</font><br/>
        <font name="Helvetica" size="7" color="#888888">Dynamic Header Seal v1.0 — M3 Export Engine</font><br/><br/>
        <font name="Courier" size="8" color="#1A1A1A"><b>Receipt:</b>  {self.receipt_id}</font><br/>
        <font name="Courier" size="8" color="#1A1A1A"><b>Hash:</b>     {hash_display}</font><br/>
        <font name="Courier" size="8" color="#1A1A1A"><b>Time:</b>     {self.timestamp[:19]}Z</font><br/>
        <font name="Courier" size="8" color="{status_color}"><b>Status:</b>   ● {self.status}</font>
        """

        # Optional SGE/Risk info
        if self.sge_score is not None:
            meta_text += f"""<br/><font name="Courier" size="8" color="#1A1A1A"><b>SGE:</b>      {self.sge_score}</font>"""
        if self.risk_level is not None:
            meta_text += f"""<br/><font name="Courier" size="8" color="#1A1A1A"><b>Risk:</b>     {self.risk_level}</font>"""

        meta_para = Paragraph(meta_text, styles['WINDI_Body'])

        seal_table = Table(
            [[meta_para, qr_flowable]],
            colWidths=[CONTENT_W - 32 * mm, 30 * mm],
            rowHeights=[32 * mm],
        )
        seal_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (0, 0), 2 * mm),
            ('RIGHTPADDING', (1, 0), (1, 0), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 1 * mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1 * mm),
            ('BOX', (0, 0), (-1, -1), 0.5, WINDI_GOLD),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FAFAF5")),
        ]))
        elements.append(seal_table)

        # ── Bottom gold bar ──
        elements.append(HRFlowable(
            width="100%",
            thickness=1.5,
            color=WINDI_GOLD,
            spaceBefore=0,
            spaceAfter=4 * mm,
        ))

        # ── Verification note ──
        verify_text = (
            f'<font name="Helvetica" size="6" color="#888888">'
            f'Verify: Compare SHA-256 hash with WINDI Forensic Ledger  |  '
            f'Full hash: {self.content_hash[:32]}...'
            f'</font>'
        )
        elements.append(Paragraph(verify_text, styles['WINDI_Footer']))
        elements.append(Spacer(1, 4 * mm))

        return elements


# ═══════════════════════════════════════════════════════════════
# HTML-TO-FLOWABLES CONVERTER
# ═══════════════════════════════════════════════════════════════

def html_to_flowables(html_content: str, styles):
    """
    Convert simplified HTML/text content from Tiptap to ReportLab flowables.
    Handles: <h1>, <h2>, <h3>, <p>, <strong>, <em>, <ul>/<li>, plain text.
    """
    import re
    elements = []
    
    # ══════════════════════════════════════════════════
    # ▼▼▼ NOVO — B5 Safety Net (3 linhas) ▼▼▼
    # ══════════════════════════════════════════════════
    if html_content and html_content.strip().startswith('{"type":'):
        try:
            html_content = tiptap_to_plaintext(html_content)
        except Exception:
            pass
    # ══════════════════════════════════════════════════
    # ▲▲▲ FIM DO NOVO ▲▲▲
    # ══════════════════════════════════════════════════

    
    if not html_content:
        return [Paragraph("<i>Empty document</i>", styles['WINDI_Body'])]

    # Strip outer divs
    content = re.sub(r'</?div[^>]*>', '', html_content)

    # Split into blocks
    blocks = re.split(r'(<h[123][^>]*>.*?</h[123]>|<p[^>]*>.*?</p>|<ul>.*?</ul>|<li>.*?</li>)',
                       content, flags=re.DOTALL)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Headings
        h1_match = re.match(r'<h1[^>]*>(.*?)</h1>', block, re.DOTALL)
        h2_match = re.match(r'<h2[^>]*>(.*?)</h2>', block, re.DOTALL)
        h3_match = re.match(r'<h3[^>]*>(.*?)</h3>', block, re.DOTALL)
        p_match = re.match(r'<p[^>]*>(.*?)</p>', block, re.DOTALL)
        li_match = re.match(r'<li[^>]*>(.*?)</li>', block, re.DOTALL)

        if h1_match:
            text = _clean_inline_html(h1_match.group(1))
            elements.append(Paragraph(text, styles['WINDI_H1']))
        elif h2_match:
            text = _clean_inline_html(h2_match.group(1))
            elements.append(Paragraph(text, styles['WINDI_H2']))
        elif h3_match:
            text = _clean_inline_html(h3_match.group(1))
            elements.append(Paragraph(text, styles['WINDI_H2']))
        elif p_match:
            text = _clean_inline_html(p_match.group(1))
            if text.strip():
                elements.append(Paragraph(text, styles['WINDI_Body']))
        elif li_match:
            text = _clean_inline_html(li_match.group(1))
            elements.append(Paragraph(f"  •  {text}", styles['WINDI_Body']))
        elif not block.startswith('<'):
            # Plain text
            text = _clean_inline_html(block)
            if text.strip():
                elements.append(Paragraph(text, styles['WINDI_Body']))

    return elements if elements else [Paragraph("<i>Empty document</i>", styles['WINDI_Body'])]


def _clean_inline_html(text):
    """Convert Tiptap inline HTML to ReportLab-compatible markup."""
    import re
    # Keep <b>, <i>, <strong>, <em> — ReportLab understands these
    text = re.sub(r'<strong>(.*?)</strong>', r'<b>\1</b>', text)
    text = re.sub(r'<em>(.*?)</em>', r'<i>\1</i>', text)
    # Remove unknown tags
    text = re.sub(r'<(?!/?[bi]>)[^>]+>', '', text)
    # Clean up entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&amp;')
    return text.strip()


# ═══════════════════════════════════════════════════════════════
# PAGE TEMPLATE (Header + Footer on every page)
# ═══════════════════════════════════════════════════════════════

class WindiPageTemplate:
    """Draws WINDI branding on every page."""

    def __init__(self, receipt_id, doc_title):
        self.receipt_id = receipt_id
        self.doc_title = doc_title

    def on_page(self, canvas_obj, doc):
        """Called for every page."""
        canvas_obj.saveState()
        w, h = A4

        # ── Top bar (thin gold line) ──
        canvas_obj.setStrokeColor(WINDI_GOLD)
        canvas_obj.setLineWidth(1.5)
        canvas_obj.line(MARGIN_L, h - 12 * mm, w - MARGIN_R, h - 12 * mm)

        # ── Top left: WINDI branding ──
        canvas_obj.setFont("Helvetica-Bold", 8)
        canvas_obj.setFillColor(WINDI_GOLD)
        canvas_obj.drawString(MARGIN_L, h - 10 * mm, "WINDI")
        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.setFillColor(WINDI_GREY)
        canvas_obj.drawString(MARGIN_L + 28, h - 10 * mm, f"| {self.doc_title[:50]}")

        # ── Top right: Receipt ID ──
        canvas_obj.setFont("Courier", 6.5)
        canvas_obj.setFillColor(WINDI_GREY)
        canvas_obj.drawRightString(w - MARGIN_R, h - 10 * mm, self.receipt_id)

        # ── Bottom bar ──
        canvas_obj.setStrokeColor(WINDI_GOLD)
        canvas_obj.setLineWidth(0.75)
        canvas_obj.line(MARGIN_L, 14 * mm, w - MARGIN_R, 14 * mm)

        # ── Footer left ──
        canvas_obj.setFont("Helvetica", 6)
        canvas_obj.setFillColor(WINDI_GREY)
        canvas_obj.drawString(MARGIN_L, 10 * mm,
                              "AI processes. Human decides. WINDI guarantees.")

        # ── Footer center: page number ──
        canvas_obj.drawCentredString(w / 2, 10 * mm,
                                     f"— {doc.page} —")

        # ── Footer right ──
        canvas_obj.drawRightString(w - MARGIN_R, 10 * mm,
                                   f"WINDI Export Engine M3 v1.0")

        canvas_obj.restoreState()


# ═══════════════════════════════════════════════════════════════
# MAIN EXPORT FUNCTION
# ═══════════════════════════════════════════════════════════════

def export_document_pdf(
    doc_content_html: str,
    receipt_data: dict,
    doc_title: str = "Untitled Document",
    include_seal: bool = True,
    include_receipt_block: bool = True,
) -> bytes:
    """
    Generate a professional WINDI-branded PDF.

    Args:
        doc_content_html: HTML content from Tiptap editor
        receipt_data: Dict with receipt_id, content_hash, timestamp, status
        doc_title: Document title
        include_seal: Whether to include the Dynamic Header Seal
        include_receipt_block: Whether to include detailed receipt at end

    Returns:
        PDF file as bytes
    """
    buffer = io.BytesIO()
    styles = get_windi_styles()

    # Page template with branding
    page_tmpl = WindiPageTemplate(
        receipt_id=receipt_data.get("receipt_id", ""),
        doc_title=doc_title,
    )

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN_L,
        rightMargin=MARGIN_R,
        topMargin=MARGIN_T,
        bottomMargin=MARGIN_B,
        title=doc_title,
        author="WINDI Publishing House",
        subject="Governance-Protected Document",
        creator="WINDI M3 Export Engine v1.0",
    )

    story = []

    # ── 1. DYNAMIC HEADER SEAL ──
    if include_seal:
        seal = DynamicHeaderSeal(receipt_data | {"doc_title": doc_title})
        seal_elements = seal.build_flowable(styles)
        story.extend(seal_elements)

    # ── 2. DOCUMENT TITLE ──
    story.append(Paragraph(doc_title, styles['WINDI_Title']))

    # ── 3. DOCUMENT CONTENT ──
    content_flowables = html_to_flowables(doc_content_html, styles)
    story.extend(content_flowables)

    # ── 4. FORENSIC RECEIPT BLOCK (end of document) ──
    if include_receipt_block:
        story.append(Spacer(1, 10 * mm))
        story.append(HRFlowable(
            width="100%", thickness=0.5,
            color=WINDI_GREY, spaceBefore=4 * mm, spaceAfter=4 * mm
        ))

        receipt_title = Paragraph(
            '<font name="Helvetica-Bold" size="9" color="#C5A55A">'
            '■ WINDI FORENSIC RECEIPT</font>',
            styles['WINDI_Body']
        )
        story.append(receipt_title)
        story.append(Spacer(1, 2 * mm))

        # Receipt details table
        receipt_rows = [
            ["Receipt ID", receipt_data.get("receipt_id", "—")],
            ["SHA-256 Hash", receipt_data.get("content_hash", "—")],
            ["Timestamp", receipt_data.get("timestamp", "—")],
            ["Status", receipt_data.get("status", "—")],
            ["Engine", "WINDI M3 Export Engine v1.0"],
            ["Architecture", "Zero-Knowledge | Client Data Sovereignty"],
        ]

        receipt_table = Table(
            receipt_rows,
            colWidths=[35 * mm, CONTENT_W - 37 * mm],
        )
        receipt_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Courier'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('TEXTCOLOR', (0, 0), (0, -1), WINDI_GREY),
            ('TEXTCOLOR', (1, 0), (1, -1), WINDI_DARK),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2 * mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2 * mm),
            ('TOPPADDING', (0, 0), (-1, -1), 1 * mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1 * mm),
            ('LINEBELOW', (0, 0), (-1, -2), 0.25, colors.HexColor("#E0E0E0")),
            ('BOX', (0, 0), (-1, -1), 0.5, WINDI_GOLD),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FAFAF8")),
        ]))
        story.append(receipt_table)

        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph(
            '<font name="Helvetica" size="6" color="#888888">'
            'This document was processed through the WINDI Governance System. '
            'The SHA-256 hash certifies content integrity at the moment of registration. '
            'WINDI stores ONLY the hash — never the document content (Zero-Knowledge Architecture). '
            'Verify authenticity by comparing the hash with the WINDI Forensic Ledger.'
            '</font>',
            styles['WINDI_Footer']
        ))

    # ── BUILD PDF ──
    doc.build(story, onFirstPage=page_tmpl.on_page, onLaterPages=page_tmpl.on_page)
    return buffer.getvalue()


# ═══════════════════════════════════════════════════════════════
# STANDALONE TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Test with sample data
    test_receipt = {
        "receipt_id": "VR-D1-0518e41a61c6",
        "content_hash": "9d79a3564678abcdef1234567890abcdef1234567890abcdef1234567890abcd",
        "timestamp": "2026-02-17T14:46:43.821Z",
        "status": "REGISTERED",
        "sge_score": "0.85",
        "risk_level": "LOW",
    }

    test_html = """
    <h1>OURO SEMÂNTICO DESCOBERTO</h1>
    <h2>1. Confiança como Infraestrutura</h2>
    <p><strong>Mudança de paradigma:</strong></p>
    <p>Antes → confiança era assumida</p>
    <p>Agora → confiança é verificável</p>
    <h2>Elementos:</h2>
    <li>hash SHA verificáveis</li>
    <li>ledger auditável</li>
    <li>autoria comprovável</li>
    <li>integridade documental</li>
    <li>prova temporal</li>
    <p><strong>confiança deixa de ser discurso e vira evidência.</strong></p>
    """

    pdf_bytes = export_document_pdf(
        doc_content_html=test_html,
        receipt_data=test_receipt,
        doc_title="OURO SEMÂNTICO DESCOBERTO",
    )

    output_path = "/tmp/windi_m3_test.pdf"
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)
    print(f"✅ PDF generated: {output_path} ({len(pdf_bytes):,} bytes)")
