#!/usr/bin/env python3
"""
WINDI Hash Injector — N2+N3+N4: SHA-256 Seal + Serial + QR Code
"AI processes. Human decides. WINDI guarantees."

Injects SHA-256 content hash, serial number, and verification QR code into documents.
The hash is computed from PRE-footer content (not circular).

Seal format (N3 serial FIRST for human readability):
    WINDI Seal  |  WINDI-2026-XXXX  |  VR-PAL-xxx  |  SHA-256: {hash[:12]}...  |  Gov: {level}  |  {timestamp}  [QR]
    Verify: admin.windia4desk.tech/vault/verify

QR code (N4) links to verification URL with serial and short hash.
"""

import hashlib
import io
from datetime import datetime, timezone

# N4: QR code generation (graceful degradation if unavailable)
try:
    from qr_engine import get_qr_for_document, is_available as qr_available
    HAS_QR = qr_available()
except ImportError:
    HAS_QR = False
    def get_qr_for_document(*args, **kwargs):
        return (None, "")

# ── WINDI Design Tokens ──
WINDI_GOLD_HEX = "#8B6914"
WINDI_DIM_HEX = "#6B6560"
WINDI_GOLD_RGB = (0x8B, 0x69, 0x14)
WINDI_DIM_RGB = (0x6B, 0x65, 0x60)
FONT_SEAL = "JetBrains Mono"
FONT_SEAL_FALLBACK = "Consolas"
VERIFY_URL = "admin.windia4desk.tech/vault/verify"


def compute_content_hash(content_bytes: bytes) -> str:
    """
    Compute SHA-256 hex digest of content bytes.

    Args:
        content_bytes: Raw document bytes

    Returns:
        64-character lowercase hex digest
    """
    return hashlib.sha256(content_bytes).hexdigest()


def short_hash(full_hash: str) -> str:
    """
    Extract first 12 characters of hash for display.

    Args:
        full_hash: Full 64-character hex digest

    Returns:
        First 12 characters
    """
    return full_hash[:12]


def _utc_timestamp() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


# ═══════════════════════════════════════════════════════════════════════════════
# DOCX INJECTION
# ═══════════════════════════════════════════════════════════════════════════════

def inject_docx(docx_bytes: bytes, content_hash: str, receipt_id: str,
                governance_level: str, doc_name: str, serial: str = None) -> bytes:
    """
    Inject WINDI seal into DOCX footer and metadata.

    Footer on every section: gold separator + seal line + verify URL + QR code
    Metadata: keywords, comments, category

    Args:
        docx_bytes: Original DOCX file bytes
        content_hash: Full SHA-256 hex digest (pre-footer)
        receipt_id: Unique receipt ID (e.g., VR-PAL-xxx)
        governance_level: LOW/MED/HIGH
        doc_name: Document filename
        serial: WINDI serial number (e.g., WINDI-2026-0001)

    Returns:
        Sealed DOCX bytes
    """
    from docx import Document
    from docx.shared import Pt, RGBColor, Cm, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    # Load document from bytes
    doc = Document(io.BytesIO(docx_bytes))

    timestamp = _utc_timestamp()
    short = short_hash(content_hash)
    # N3: Serial goes FIRST in seal line for human readability
    if serial:
        seal_line = f"WINDI Seal  |  {serial}  |  {receipt_id}  |  SHA-256: {short}...  |  Gov: {governance_level}  |  {timestamp}"
    else:
        seal_line = f"WINDI Seal  |  {receipt_id}  |  SHA-256: {short}...  |  Gov: {governance_level}  |  {timestamp}"

    # N4: Generate QR code
    qr_bytes, verify_url = get_qr_for_document(serial, content_hash, size=100)

    # Inject footer into all sections
    for section in doc.sections:
        footer = section.footer
        footer.is_linked_to_previous = False

        # Clear existing footer content or get first paragraph
        if footer.paragraphs:
            # Add separator above existing content
            sep_para = footer.paragraphs[0].insert_paragraph_before("")
        else:
            sep_para = footer.add_paragraph()

        # Gold separator line
        sep_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sep_para.paragraph_format.space_before = Pt(6)
        sep_para.paragraph_format.space_after = Pt(2)
        sep_run = sep_para.add_run("━" * 50)
        sep_run.font.size = Pt(6)
        sep_run.font.color.rgb = RGBColor(*WINDI_GOLD_RGB)

        # Seal line paragraph
        seal_para = footer.add_paragraph()
        seal_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        seal_para.paragraph_format.space_after = Pt(1)
        seal_run = seal_para.add_run(seal_line)
        seal_run.font.name = FONT_SEAL_FALLBACK
        seal_run.font.size = Pt(7)
        seal_run.font.color.rgb = RGBColor(*WINDI_GOLD_RGB)

        # Verify URL hint
        verify_para = footer.add_paragraph()
        verify_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        verify_para.paragraph_format.space_after = Pt(2)
        verify_run = verify_para.add_run(f"Verify: {VERIFY_URL}")
        verify_run.font.name = FONT_SEAL_FALLBACK
        verify_run.font.size = Pt(6)
        verify_run.font.color.rgb = RGBColor(*WINDI_DIM_RGB)

        # N4: Add QR image (centered below text)
        if qr_bytes and HAS_QR:
            try:
                qr_para = footer.add_paragraph()
                qr_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                qr_para.paragraph_format.space_before = Pt(2)
                qr_para.paragraph_format.space_after = Pt(4)
                qr_stream = io.BytesIO(qr_bytes)
                qr_run = qr_para.add_run()
                qr_run.add_picture(qr_stream, width=Cm(1.5))
            except Exception:
                pass  # Graceful degradation

    # Inject metadata
    core_props = doc.core_properties

    # Keywords: windi-seal;serial:{serial};sha256:{hash};receipt:{id};gov:{level}
    keywords = f"windi-seal;sha256:{content_hash};receipt:{receipt_id};gov:{governance_level}"
    if serial:
        keywords = f"windi-seal;serial:{serial};sha256:{content_hash};receipt:{receipt_id};gov:{governance_level}"
    core_props.keywords = keywords

    # Comments: Full seal info
    serial_line = f"Serial: {serial}\n" if serial else ""
    core_props.comments = (
        f"WINDI Governance Seal\n"
        f"{serial_line}"
        f"Receipt: {receipt_id}\n"
        f"SHA-256: {content_hash}\n"
        f"Governance Level: {governance_level}\n"
        f"Sealed: {timestamp}\n"
        f"Verify: https://{VERIFY_URL}"
    )

    # Category: WINDI-GOV-{level}
    core_props.category = f"WINDI-GOV-{governance_level}"

    # Save to bytes
    output = io.BytesIO()
    doc.save(output)
    return output.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# PDF INJECTION
# ═══════════════════════════════════════════════════════════════════════════════

def inject_pdf(pdf_bytes: bytes, content_hash: str, receipt_id: str,
               governance_level: str, doc_name: str, serial: str = None) -> bytes:
    """
    Inject WINDI seal into PDF footer overlay and custom metadata.

    Uses reportlab canvas overlay for footer + QR code.
    Custom metadata: /WINDIHash, /WINDIReceipt, /WINDIGovLevel, /WINDISerial

    Args:
        pdf_bytes: Original PDF file bytes
        content_hash: Full SHA-256 hex digest
        receipt_id: Unique receipt ID
        governance_level: LOW/MED/HIGH
        doc_name: Document filename
        serial: WINDI serial number (e.g., WINDI-2026-0001)

    Returns:
        Sealed PDF bytes
    """
    from PyPDF2 import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.utils import ImageReader
    import os

    timestamp = _utc_timestamp()
    short = short_hash(content_hash)
    # N3: Serial goes FIRST in seal line
    if serial:
        seal_line = f"WINDI Seal  |  {serial}  |  {receipt_id}  |  SHA-256: {short}...  |  Gov: {governance_level}  |  {timestamp}"
    else:
        seal_line = f"WINDI Seal  |  {receipt_id}  |  SHA-256: {short}...  |  Gov: {governance_level}  |  {timestamp}"

    # N4: Generate QR code
    qr_bytes, verify_url = get_qr_for_document(serial, content_hash, size=100)

    # Try to register JetBrains Mono, fallback to Courier
    seal_font = "Courier"
    try:
        font_paths = [
            "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Regular.ttf",
            "/usr/share/fonts/jetbrains-mono/JetBrainsMono-Regular.ttf",
            os.path.expanduser("~/.fonts/JetBrainsMono-Regular.ttf"),
        ]
        for fp in font_paths:
            if os.path.exists(fp):
                pdfmetrics.registerFont(TTFont("JetBrainsMono", fp))
                seal_font = "JetBrainsMono"
                break
    except Exception:
        pass

    # Read original PDF
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()

    # Create overlay with seal for each page
    for page_num, page in enumerate(reader.pages):
        # Get page dimensions
        media_box = page.mediabox
        page_width = float(media_box.width)
        page_height = float(media_box.height)

        # Create overlay
        overlay_buffer = io.BytesIO()
        c = canvas.Canvas(overlay_buffer, pagesize=(page_width, page_height))

        # Draw gold separator line
        gold_color = HexColor(WINDI_GOLD_HEX)
        dim_color = HexColor(WINDI_DIM_HEX)

        y_pos = 25
        line_width = page_width * 0.6
        x_start = (page_width - line_width) / 2

        c.setStrokeColor(gold_color)
        c.setLineWidth(0.5)
        c.line(x_start, y_pos + 15, x_start + line_width, y_pos + 15)

        # Draw seal line
        c.setFont(seal_font, 6)
        c.setFillColor(gold_color)
        seal_width = c.stringWidth(seal_line, seal_font, 6)
        c.drawString((page_width - seal_width) / 2, y_pos + 5, seal_line)

        # Draw verify URL
        c.setFont(seal_font, 5)
        c.setFillColor(dim_color)
        verify_text = f"Verify: {VERIFY_URL}"
        verify_width = c.stringWidth(verify_text, seal_font, 5)
        c.drawString((page_width - verify_width) / 2, y_pos - 3, verify_text)

        # N4: Draw QR code in bottom-right corner
        if qr_bytes and HAS_QR:
            try:
                qr_stream = io.BytesIO(qr_bytes)
                qr_image = ImageReader(qr_stream)
                qr_size = 45  # points (~1.5cm)
                qr_x = page_width - qr_size - 15
                qr_y = 10
                c.drawImage(qr_image, qr_x, qr_y, width=qr_size, height=qr_size)
            except Exception:
                pass  # Graceful degradation

        c.save()

        # Merge overlay with page
        overlay_buffer.seek(0)
        overlay_reader = PdfReader(overlay_buffer)
        overlay_page = overlay_reader.pages[0]
        page.merge_page(overlay_page)

        writer.add_page(page)

    # Add custom metadata
    keywords = f"windi-seal;sha256:{content_hash};receipt:{receipt_id};gov:{governance_level}"
    if serial:
        keywords = f"windi-seal;serial:{serial};sha256:{content_hash};receipt:{receipt_id};gov:{governance_level}"

    metadata = {
        "/WINDIHash": content_hash,
        "/WINDIReceipt": receipt_id,
        "/WINDIGovLevel": governance_level,
        "/WINDISealed": timestamp,
        "/WINDIVerify": f"https://{VERIFY_URL}",
        "/Keywords": keywords,
        "/Subject": f"WINDI Governance Sealed Document - {doc_name}",
    }
    if serial:
        metadata["/WINDISerial"] = serial
    writer.add_metadata(metadata)

    # Write output
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# PPTX INJECTION
# ═══════════════════════════════════════════════════════════════════════════════

def inject_pptx(pptx_bytes: bytes, content_hash: str, receipt_id: str,
                governance_level: str, doc_name: str, serial: str = None) -> bytes:
    """
    Inject WINDI seal into PPTX last slide notes, core properties, and QR image.

    Args:
        pptx_bytes: Original PPTX file bytes
        content_hash: Full SHA-256 hex digest
        receipt_id: Unique receipt ID
        governance_level: LOW/MED/HIGH
        doc_name: Document filename
        serial: WINDI serial number (e.g., WINDI-2026-0001)

    Returns:
        Sealed PPTX bytes
    """
    from pptx import Presentation
    from pptx.util import Pt, Cm, Emu
    from pptx.dml.color import RGBColor

    timestamp = _utc_timestamp()
    short = short_hash(content_hash)
    # N3: Serial goes FIRST in seal line
    if serial:
        seal_line = f"WINDI Seal  |  {serial}  |  {receipt_id}  |  SHA-256: {short}...  |  Gov: {governance_level}  |  {timestamp}"
    else:
        seal_line = f"WINDI Seal  |  {receipt_id}  |  SHA-256: {short}...  |  Gov: {governance_level}  |  {timestamp}"

    # N4: Generate QR code
    qr_bytes, verify_url = get_qr_for_document(serial, content_hash, size=150)

    # Load presentation
    prs = Presentation(io.BytesIO(pptx_bytes))

    # Get last slide
    if prs.slides:
        last_slide = prs.slides[-1]

        # Access or create notes slide
        if not last_slide.has_notes_slide:
            notes_slide = last_slide.notes_slide
        else:
            notes_slide = last_slide.notes_slide

        # Add seal to notes
        notes_frame = notes_slide.notes_text_frame

        # Add separator
        sep_para = notes_frame.add_paragraph()
        sep_para.text = "\n" + "━" * 40

        # Add seal line
        seal_para = notes_frame.add_paragraph()
        seal_para.text = seal_line

        # Add verify URL
        verify_para = notes_frame.add_paragraph()
        verify_para.text = f"Verify: {VERIFY_URL}"

        # Add full hash reference
        hash_para = notes_frame.add_paragraph()
        hash_para.text = f"\nFull SHA-256: {content_hash}"

        # N4: Add QR image to last slide (bottom-right corner)
        if qr_bytes and HAS_QR:
            try:
                qr_stream = io.BytesIO(qr_bytes)
                qr_size = Cm(2)  # 2cm x 2cm

                # Get slide dimensions
                slide_width = prs.slide_width
                slide_height = prs.slide_height

                # Position: bottom-right with margin
                margin = Cm(0.5)
                left = slide_width - qr_size - margin
                top = slide_height - qr_size - margin

                # Add QR image to slide
                last_slide.shapes.add_picture(qr_stream, left, top, width=qr_size, height=qr_size)
            except Exception:
                pass  # Graceful degradation

    # Inject core properties
    core_props = prs.core_properties

    # Keywords
    keywords = f"windi-seal;sha256:{content_hash};receipt:{receipt_id};gov:{governance_level}"
    if serial:
        keywords = f"windi-seal;serial:{serial};sha256:{content_hash};receipt:{receipt_id};gov:{governance_level}"
    core_props.keywords = keywords

    # Comments
    serial_line = f"Serial: {serial}\n" if serial else ""
    core_props.comments = (
        f"WINDI Governance Seal\n"
        f"{serial_line}"
        f"Receipt: {receipt_id}\n"
        f"SHA-256: {content_hash}\n"
        f"Governance Level: {governance_level}\n"
        f"Sealed: {timestamp}\n"
        f"Verify: https://{VERIFY_URL}"
    )

    # Category
    core_props.category = f"WINDI-GOV-{governance_level}"

    # Save to bytes
    output = io.BytesIO()
    prs.save(output)
    return output.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# XLSX INJECTION (for completeness)
# ═══════════════════════════════════════════════════════════════════════════════

def inject_xlsx(xlsx_bytes: bytes, content_hash: str, receipt_id: str,
                governance_level: str, doc_name: str, serial: str = None) -> bytes:
    """
    Inject WINDI seal into XLSX properties and add seal sheet.

    Args:
        xlsx_bytes: Original XLSX file bytes
        content_hash: Full SHA-256 hex digest
        receipt_id: Unique receipt ID
        governance_level: LOW/MED/HIGH
        doc_name: Document filename
        serial: WINDI serial number (e.g., WINDI-2026-0001)

    Returns:
        Sealed XLSX bytes
    """
    from openpyxl import load_workbook
    from openpyxl.styles import Font, Alignment

    timestamp = _utc_timestamp()
    short = short_hash(content_hash)
    # N3: Serial goes FIRST in seal line
    if serial:
        seal_line = f"WINDI Seal  |  {serial}  |  {receipt_id}  |  SHA-256: {short}...  |  Gov: {governance_level}  |  {timestamp}"
    else:
        seal_line = f"WINDI Seal  |  {receipt_id}  |  SHA-256: {short}...  |  Gov: {governance_level}  |  {timestamp}"

    # Load workbook
    wb = load_workbook(io.BytesIO(xlsx_bytes))

    # Inject core properties
    keywords = f"windi-seal;sha256:{content_hash};receipt:{receipt_id};gov:{governance_level}"
    if serial:
        keywords = f"windi-seal;serial:{serial};sha256:{content_hash};receipt:{receipt_id};gov:{governance_level}"
    wb.properties.keywords = keywords
    wb.properties.category = f"WINDI-GOV-{governance_level}"
    serial_part = f"Serial: {serial} | " if serial else ""
    wb.properties.comments = (
        f"WINDI Governance Seal | {serial_part}Receipt: {receipt_id} | "
        f"SHA-256: {content_hash} | Gov: {governance_level} | "
        f"Sealed: {timestamp}"
    )

    # Add WINDI-SEAL sheet at the end
    seal_sheet = wb.create_sheet("WINDI-SEAL")

    # Gold color
    gold_font = Font(name="Consolas", size=9, color="8B6914", bold=True)
    dim_font = Font(name="Consolas", size=8, color="6B6560")

    seal_sheet["A1"] = "WINDI Governance Seal"
    seal_sheet["A1"].font = gold_font

    # N3: Add serial row (row 3)
    row = 3
    if serial:
        seal_sheet[f"A{row}"] = "Serial:"
        seal_sheet[f"B{row}"] = serial
        seal_sheet[f"A{row}"].font = dim_font
        seal_sheet[f"B{row}"].font = gold_font
        row += 1

    seal_sheet[f"A{row}"] = "Receipt ID:"
    seal_sheet[f"B{row}"] = receipt_id
    seal_sheet[f"A{row}"].font = dim_font
    seal_sheet[f"B{row}"].font = gold_font
    row += 1

    seal_sheet[f"A{row}"] = "SHA-256:"
    seal_sheet[f"B{row}"] = content_hash
    seal_sheet[f"A{row}"].font = dim_font
    seal_sheet[f"B{row}"].font = Font(name="Consolas", size=8, color="8B6914")
    row += 1

    seal_sheet[f"A{row}"] = "Governance:"
    seal_sheet[f"B{row}"] = governance_level
    seal_sheet[f"A{row}"].font = dim_font
    seal_sheet[f"B{row}"].font = gold_font
    row += 1

    seal_sheet[f"A{row}"] = "Sealed:"
    seal_sheet[f"B{row}"] = timestamp
    seal_sheet[f"A{row}"].font = dim_font
    seal_sheet[f"B{row}"].font = dim_font
    row += 2

    seal_sheet[f"A{row}"] = f"Verify: {VERIFY_URL}"
    seal_sheet[f"A{row}"].font = dim_font

    # Adjust column widths
    seal_sheet.column_dimensions["A"].width = 15
    seal_sheet.column_dimensions["B"].width = 70

    # Save to bytes
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# UNIFIED ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

INJECTORS = {
    "docx": inject_docx,
    "pdf": inject_pdf,
    "pptx": inject_pptx,
    "xlsx": inject_xlsx,
}


def seal_document(doc_bytes: bytes, doc_format: str, receipt_id: str,
                  governance_level: str, doc_name: str, serial: str = None) -> tuple:
    """
    Unified entry point for document sealing (N2+N3).

    IMPORTANT: Hash is computed from PRE-footer content (not circular).

    Args:
        doc_bytes: Original document bytes (PRE-footer)
        doc_format: Document format (docx, pdf, pptx, xlsx)
        receipt_id: Unique receipt ID (e.g., VR-PAL-xxx)
        governance_level: LOW/MED/HIGH
        doc_name: Document filename
        serial: WINDI serial number (e.g., WINDI-2026-0001)

    Returns:
        Tuple of (sealed_bytes, content_hash)
    """
    # Compute hash from PRE-footer content
    content_hash = compute_content_hash(doc_bytes)

    # Get injector for format
    fmt = doc_format.lower().lstrip(".")
    injector = INJECTORS.get(fmt)

    if not injector:
        # Unsupported format - return original bytes with hash
        return (doc_bytes, content_hash)

    # Inject seal with serial (N3)
    try:
        sealed_bytes = injector(doc_bytes, content_hash, receipt_id, governance_level, doc_name, serial=serial)
        return (sealed_bytes, content_hash)
    except Exception as e:
        # On injection failure, return original bytes
        print(f"[hash_injector] Warning: seal injection failed for {fmt}: {e}")
        return (doc_bytes, content_hash)


def verify_seal(doc_bytes: bytes, expected_hash: str, doc_format: str) -> dict:
    """
    Extract hash from document metadata and compare with expected.

    Args:
        doc_bytes: Sealed document bytes
        expected_hash: Expected SHA-256 hash
        doc_format: Document format

    Returns:
        Dict with verification results:
        {
            "valid": bool,
            "extracted_hash": str or None,
            "expected_hash": str,
            "match": bool,
            "receipt_id": str or None,
            "governance_level": str or None,
            "error": str or None
        }
    """
    fmt = doc_format.lower().lstrip(".")
    result = {
        "valid": False,
        "extracted_hash": None,
        "expected_hash": expected_hash,
        "match": False,
        "receipt_id": None,
        "governance_level": None,
        "serial": None,
        "error": None,
    }

    try:
        if fmt == "docx":
            result.update(_verify_docx(doc_bytes, expected_hash))
        elif fmt == "pdf":
            result.update(_verify_pdf(doc_bytes, expected_hash))
        elif fmt == "pptx":
            result.update(_verify_pptx(doc_bytes, expected_hash))
        elif fmt == "xlsx":
            result.update(_verify_xlsx(doc_bytes, expected_hash))
        else:
            result["error"] = f"Unsupported format: {fmt}"
    except Exception as e:
        result["error"] = str(e)

    return result


def _verify_docx(doc_bytes: bytes, expected_hash: str) -> dict:
    """Verify DOCX seal."""
    from docx import Document

    doc = Document(io.BytesIO(doc_bytes))
    keywords = doc.core_properties.keywords or ""

    # Parse keywords: windi-seal;serial:{serial};sha256:{hash};receipt:{id};gov:{level}
    parts = dict(p.split(":", 1) for p in keywords.split(";") if ":" in p)

    extracted_hash = parts.get("sha256")
    receipt_id = parts.get("receipt")
    governance_level = parts.get("gov")
    serial = parts.get("serial")

    return {
        "valid": extracted_hash is not None,
        "extracted_hash": extracted_hash,
        "match": extracted_hash == expected_hash,
        "receipt_id": receipt_id,
        "governance_level": governance_level,
        "serial": serial,
    }


def _verify_pdf(doc_bytes: bytes, expected_hash: str) -> dict:
    """Verify PDF seal."""
    from PyPDF2 import PdfReader

    reader = PdfReader(io.BytesIO(doc_bytes))
    metadata = reader.metadata or {}

    extracted_hash = metadata.get("/WINDIHash")
    receipt_id = metadata.get("/WINDIReceipt")
    governance_level = metadata.get("/WINDIGovLevel")
    serial = metadata.get("/WINDISerial")

    return {
        "valid": extracted_hash is not None,
        "extracted_hash": extracted_hash,
        "match": extracted_hash == expected_hash,
        "receipt_id": receipt_id,
        "governance_level": governance_level,
        "serial": serial,
    }


def _verify_pptx(doc_bytes: bytes, expected_hash: str) -> dict:
    """Verify PPTX seal."""
    from pptx import Presentation

    prs = Presentation(io.BytesIO(doc_bytes))
    keywords = prs.core_properties.keywords or ""

    # Parse keywords
    parts = dict(p.split(":", 1) for p in keywords.split(";") if ":" in p)

    extracted_hash = parts.get("sha256")
    receipt_id = parts.get("receipt")
    governance_level = parts.get("gov")
    serial = parts.get("serial")

    return {
        "valid": extracted_hash is not None,
        "extracted_hash": extracted_hash,
        "match": extracted_hash == expected_hash,
        "receipt_id": receipt_id,
        "governance_level": governance_level,
        "serial": serial,
    }


def _verify_xlsx(doc_bytes: bytes, expected_hash: str) -> dict:
    """Verify XLSX seal."""
    from openpyxl import load_workbook

    wb = load_workbook(io.BytesIO(doc_bytes))
    keywords = wb.properties.keywords or ""

    # Parse keywords
    parts = dict(p.split(":", 1) for p in keywords.split(";") if ":" in p)

    extracted_hash = parts.get("sha256")
    receipt_id = parts.get("receipt")
    governance_level = parts.get("gov")
    serial = parts.get("serial")

    return {
        "valid": extracted_hash is not None,
        "extracted_hash": extracted_hash,
        "match": extracted_hash == expected_hash,
        "receipt_id": receipt_id,
        "governance_level": governance_level,
        "serial": serial,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CLI TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    print("WINDI Hash Injector - N2 Module")
    print("=" * 50)

    # Test hash computation
    test_data = b"Test document content"
    test_hash = compute_content_hash(test_data)
    print(f"Test hash: {test_hash}")
    print(f"Short hash: {short_hash(test_hash)}")

    # List available injectors
    print(f"\nAvailable formats: {list(INJECTORS.keys())}")

    # Quick DOCX test if file provided
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        with open(filepath, "rb") as f:
            doc_bytes = f.read()

        fmt = filepath.split(".")[-1].lower()
        receipt_id = "VR-PAL-test123456"
        gov_level = "HIGH"

        sealed, content_hash = seal_document(doc_bytes, fmt, receipt_id, gov_level, filepath)

        out_path = filepath.replace(f".{fmt}", f"_sealed.{fmt}")
        with open(out_path, "wb") as f:
            f.write(sealed)

        print(f"\nSealed: {out_path}")
        print(f"Content hash: {content_hash}")
        print(f"Sealed size: {len(sealed)} bytes")

        # Verify
        verify_result = verify_seal(sealed, content_hash, fmt)
        print(f"Verify: {verify_result}")
