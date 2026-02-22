#!/usr/bin/env python3
"""
WINDI DOCX Renderer — Word Document Generation
Uses python-docx to create professional .docx files with WINDI governance.
"""

import re
from datetime import datetime

try:
    from docx import Document
    from docx.shared import Pt, Inches, Cm, RGBColor, Emu
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.section import WD_ORIENT
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


# ── WINDI Design Tokens ──
WINDI_GOLD = RGBColor(0x8B, 0x69, 0x14) if HAS_DOCX else None
WINDI_DARK = RGBColor(0x2C, 0x29, 0x24) if HAS_DOCX else None
WINDI_DIM = RGBColor(0x6B, 0x65, 0x60) if HAS_DOCX else None
WINDI_BORDER = RGBColor(0xDD, 0xD6, 0xC2) if HAS_DOCX else None

FONT_HEADING = "Calibri"
FONT_BODY = "Calibri"
FONT_MONO = "Consolas"


def render_docx(context, filepath):
    """
    Render a DOCX document from context.

    Args:
        context (dict): Rendering context with text, intent, ISP, SGE data
        filepath (str): Output file path
    """
    if not HAS_DOCX:
        raise ImportError("python-docx not installed. Run: pip install python-docx")

    doc = Document()
    text = context["text"]
    intent = context.get("intent", {})
    doc_type = context.get("doc_type", "note")
    language = context.get("language", "de")
    formality = context.get("formality", "formal")
    entities = context.get("entities", {})
    isp = context.get("isp", {})
    receipt = context.get("receipt")

    # ── Page Setup ──
    section = doc.sections[0]
    section.page_width = Cm(21)  # A4
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2)

    # ── Default Style ──
    style = doc.styles["Normal"]
    style.font.name = FONT_BODY
    style.font.size = Pt(11)
    style.font.color.rgb = WINDI_DARK
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.line_spacing = 1.15

    # ── Header ──
    _add_header(doc, isp, language)

    # ── Title Block ──
    _add_title_block(doc, doc_type, language, entities, formality)

    # ── Body Content (Markdown → DOCX) ──
    _render_markdown_to_docx(doc, text)

    # ── Governance Footer ──
    _add_governance_footer(doc, context)

    # ── WINDI Receipt (if sealed) ──
    if receipt:
        _add_receipt_block(doc, receipt)

    doc.save(filepath)


def _add_header(doc, isp, language):
    """Add WINDI institutional header."""
    header = doc.sections[0].header
    hp = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # ISP branding or WINDI default
    org_name = isp.get("organization", "WINDI Publishing House")
    run = hp.add_run(org_name)
    run.font.size = Pt(8)
    run.font.color.rgb = WINDI_DIM
    run.font.name = FONT_HEADING

    run2 = hp.add_run("  |  WINDI Governance")
    run2.font.size = Pt(7)
    run2.font.color.rgb = WINDI_GOLD
    run2.font.name = FONT_HEADING


def _add_title_block(doc, doc_type, language, entities, formality):
    """Add document title and metadata block."""
    type_labels = {
        "de": {
            "letter": "Brief", "memo": "Memorandum", "report": "Bericht",
            "contract": "Vertrag", "invoice": "Rechnung", "note": "Notiz",
            "email": "E-Mail", "protocol": "Protokoll", "analysis": "Analyse",
            "presentation": "Präsentation", "communique": "Communiqué",
            "security_advisory": "Sicherheitshinweis",
            "governance_decision": "Governance-Beschluss",
            "certificate": "Bescheinigung",
        },
        "en": {
            "letter": "Letter", "memo": "Memorandum", "report": "Report",
            "contract": "Contract", "invoice": "Invoice", "note": "Note",
            "email": "Email", "protocol": "Meeting Minutes", "analysis": "Analysis",
            "presentation": "Presentation", "communique": "Communiqué",
            "security_advisory": "Security Advisory",
            "governance_decision": "Governance Decision",
            "certificate": "Certificate",
        },
        "pt": {
            "letter": "Carta", "memo": "Memorando", "report": "Relatório",
            "contract": "Contrato", "invoice": "Fatura", "note": "Nota",
            "email": "E-mail", "protocol": "Ata de Reunião", "analysis": "Análise",
            "presentation": "Apresentação", "communique": "Comunicado",
            "security_advisory": "Alerta de Segurança",
            "governance_decision": "Decisão de Governança",
            "certificate": "Certificado",
        },
    }

    labels = type_labels.get(language, type_labels["en"])
    title = labels.get(doc_type, doc_type.replace("_", " ").title())

    # Title
    tp = doc.add_paragraph()
    tp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    tp.paragraph_format.space_before = Pt(12)
    tp.paragraph_format.space_after = Pt(4)
    run = tp.add_run(title)
    run.font.size = Pt(22)
    run.font.bold = True
    run.font.color.rgb = WINDI_DARK
    run.font.name = FONT_HEADING

    # Date line
    dp = doc.add_paragraph()
    dp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    dp.paragraph_format.space_after = Pt(2)
    date_str = datetime.now().strftime("%d.%m.%Y" if language == "de" else "%Y-%m-%d")
    drun = dp.add_run(date_str)
    drun.font.size = Pt(9)
    drun.font.color.rgb = WINDI_DIM
    drun.font.name = FONT_BODY

    # Entity metadata line
    meta_parts = []
    if entities.get("org"):
        meta_parts.append("🏢 " + ", ".join(entities["org"]))
    if entities.get("person"):
        meta_parts.append("👤 " + ", ".join(entities["person"]))
    if entities.get("money"):
        meta_parts.append("💶 " + ", ".join(entities["money"]))

    if meta_parts:
        mp = doc.add_paragraph()
        mp.paragraph_format.space_after = Pt(8)
        mrun = mp.add_run(" · ".join(meta_parts))
        mrun.font.size = Pt(9)
        mrun.font.color.rgb = WINDI_DIM
        mrun.font.name = FONT_BODY

    # Separator line
    sep = doc.add_paragraph()
    sep.paragraph_format.space_before = Pt(4)
    sep.paragraph_format.space_after = Pt(12)
    srun = sep.add_run("─" * 60)
    srun.font.size = Pt(6)
    srun.font.color.rgb = WINDI_BORDER


def _render_markdown_to_docx(doc, text):
    """Convert markdown-ish text to DOCX paragraphs."""
    lines = text.split("\n")
    i = 0
    in_list = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Empty line
        if not stripped:
            if in_list:
                in_list = False
            i += 1
            continue

        # Headings
        if stripped.startswith("### "):
            _add_heading(doc, stripped[4:], level=3)
        elif stripped.startswith("## "):
            _add_heading(doc, stripped[3:], level=2)
        elif stripped.startswith("# "):
            _add_heading(doc, stripped[2:], level=1)
        # Bullet list
        elif stripped.startswith("- ") or stripped.startswith("• ") or stripped.startswith("* "):
            content = stripped[2:]
            _add_list_item(doc, content, ordered=False)
            in_list = True
        # Numbered list
        elif re.match(r"^\d+[\.\)]\s", stripped):
            content = re.sub(r"^\d+[\.\)]\s", "", stripped)
            _add_list_item(doc, content, ordered=True)
            in_list = True
        # Horizontal rule
        elif stripped in ("---", "***", "___"):
            sep = doc.add_paragraph()
            sep.paragraph_format.space_before = Pt(6)
            sep.paragraph_format.space_after = Pt(6)
            run = sep.add_run("─" * 60)
            run.font.size = Pt(6)
            run.font.color.rgb = WINDI_BORDER
        # Table (pipe-separated)
        elif "|" in stripped and stripped.startswith("|"):
            table_lines = []
            while i < len(lines) and "|" in lines[i].strip():
                table_lines.append(lines[i].strip())
                i += 1
            _add_table(doc, table_lines)
            continue
        # Regular paragraph
        else:
            _add_paragraph(doc, stripped)

        i += 1


def _add_heading(doc, text, level=1):
    """Add a heading with WINDI styling."""
    sizes = {1: 18, 2: 14, 3: 12}
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16 if level == 1 else 12)
    p.paragraph_format.space_after = Pt(6)
    clean = _strip_markdown_inline(text)
    run = p.add_run(clean)
    run.font.size = Pt(sizes.get(level, 12))
    run.font.bold = True
    run.font.color.rgb = WINDI_DARK
    run.font.name = FONT_HEADING


def _add_paragraph(doc, text):
    """Add a body paragraph with inline formatting."""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    _add_formatted_runs(p, text)


def _add_list_item(doc, text, ordered=False):
    """Add a list item (bullet or numbered)."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(1)
    p.paragraph_format.first_line_indent = Cm(-0.5)
    p.paragraph_format.space_after = Pt(3)

    prefix = "•  " if not ordered else ""
    run = p.add_run(prefix)
    run.font.size = Pt(11)
    run.font.name = FONT_BODY
    _add_formatted_runs(p, text)


def _add_formatted_runs(paragraph, text):
    """Parse inline markdown (bold, italic, code) into runs."""
    # Split by **bold**, *italic*, `code`
    parts = re.split(r'(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)', text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2])
            run.font.bold = True
        elif part.startswith("*") and part.endswith("*"):
            run = paragraph.add_run(part[1:-1])
            run.font.italic = True
        elif part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1])
            run.font.name = FONT_MONO
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(0x8B, 0x45, 0x13)
        else:
            run = paragraph.add_run(part)
        run.font.name = run.font.name or FONT_BODY
        run.font.size = run.font.size or Pt(11)
        if not run.font.color.rgb:
            run.font.color.rgb = WINDI_DARK


def _add_table(doc, lines):
    """Convert markdown table lines to DOCX table."""
    rows_data = []
    for line in lines:
        if re.match(r"^\|[\s\-:]+\|$", line):
            continue  # Skip separator row
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells:
            rows_data.append(cells)

    if not rows_data:
        return

    cols = max(len(r) for r in rows_data)
    table = doc.add_table(rows=len(rows_data), cols=cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    for r_idx, row in enumerate(rows_data):
        for c_idx, cell_text in enumerate(row):
            if c_idx < cols:
                cell = table.cell(r_idx, c_idx)
                cell.text = cell_text.strip()
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.space_after = Pt(2)
                    for run in paragraph.runs:
                        run.font.size = Pt(10)
                        run.font.name = FONT_BODY
                        if r_idx == 0:
                            run.font.bold = True
                            run.font.color.rgb = WINDI_GOLD


def _add_governance_footer(doc, context):
    """Add WINDI governance footer."""
    footer = doc.sections[0].footer
    fp = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER

    sge = context.get("sge", {})
    tier = context.get("tier", "HIGH")
    score = sge.get("score", "—")

    footer_text = f"WINDI Governance · {tier} · SGE {score}"
    run = fp.add_run(footer_text)
    run.font.size = Pt(7)
    run.font.color.rgb = WINDI_DIM
    run.font.name = FONT_HEADING

    # Page number
    run2 = fp.add_run("  |  ")
    run2.font.size = Pt(7)
    run2.font.color.rgb = WINDI_DIM


def _add_receipt_block(doc, receipt):
    """Add WINDI-RECEIPT governance seal at document end."""
    doc.add_paragraph()  # Spacer

    sep = doc.add_paragraph()
    srun = sep.add_run("─" * 60)
    srun.font.size = Pt(6)
    srun.font.color.rgb = WINDI_BORDER

    rp = doc.add_paragraph()
    rp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    rp.paragraph_format.space_after = Pt(2)
    title_run = rp.add_run("🛡️ WINDI-RECEIPT")
    title_run.font.size = Pt(8)
    title_run.font.bold = True
    title_run.font.color.rgb = WINDI_GOLD
    title_run.font.name = FONT_HEADING

    # Receipt fields
    fields = [
        ("Hash", receipt.get("hash", "—")[:16] + "..."),
        ("Type", receipt.get("doc_type", "—")),
        ("Risk", receipt.get("risk_level", "—")),
        ("Sealed", receipt.get("timestamp", "—")),
    ]
    for label, value in fields:
        fp = doc.add_paragraph()
        fp.paragraph_format.space_after = Pt(1)
        lrun = fp.add_run(f"{label}: ")
        lrun.font.size = Pt(7)
        lrun.font.bold = True
        lrun.font.color.rgb = WINDI_DIM
        lrun.font.name = FONT_MONO
        vrun = fp.add_run(value)
        vrun.font.size = Pt(7)
        vrun.font.color.rgb = WINDI_DIM
        vrun.font.name = FONT_MONO


def _strip_markdown_inline(text):
    """Remove inline markdown formatting."""
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    return text.strip()
