#!/usr/bin/env python3
"""
WINDI XLSX Renderer v2.0.0 — Professional Excel Document Generation
"AI processes. Human decides. WINDI guarantees."

Design philosophy: Think like Excel, not like CSS.
  - NamedStyles for consistency
  - Semantic grid layout
  - Print-ready from the start
  - Currency-aware per locale
  - Governance as audit trail
"""

import re
from datetime import datetime
from copy import copy

try:
    from openpyxl import Workbook
    from openpyxl.styles import (
        Font, PatternFill, Alignment, Border, Side, NamedStyle,
        numbers, Protection,
    )
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.page import PageMargins
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


# ═══════════════════════════════════════════════════════════════
# WINDI KLAR Design Tokens
# ═══════════════════════════════════════════════════════════════
KLAR = {
    "gold":         "8B6914",
    "gold_light":   "D4A843",
    "gold_bg":      "F5EDD4",
    "parchment":    "F5F0E0",
    "parchment_lt": "FAF8F0",
    "card":         "FDFBF5",
    "text":         "2C2924",
    "dim":          "6B6560",
    "border":       "DDD6C2",
    "border_dark":  "B8AD94",
    "white":        "FFFFFF",
    "red":          "C62828",
    "green":        "2E7D32",
    "rule":         "8B6914",
}

# ── Reusable border pieces ────────────────────────────────────
_no = Side(style=None)
_thin = Side(style="thin", color=KLAR["border"])
_thin_dark = Side(style="thin", color=KLAR["border_dark"])
_gold_med = Side(style="medium", color=KLAR["gold"])
_gold_thin = Side(style="thin", color=KLAR["gold"])
_double_gold = Side(style="double", color=KLAR["gold"])

BORDER_NONE = Border(left=_no, right=_no, top=_no, bottom=_no)
BORDER_BOTTOM_THIN = Border(bottom=_thin)
BORDER_BOTTOM_GOLD = Border(bottom=_gold_med)
BORDER_TOP_GOLD = Border(top=_gold_med)
BORDER_DOUBLE_GOLD = Border(top=_double_gold, bottom=_double_gold)
BORDER_TABLE_HEADER = Border(bottom=_gold_med, top=_gold_thin)
BORDER_TABLE_CELL = Border(bottom=_thin)
BORDER_BOX_TOP_LEFT = Border(top=_thin_dark, left=_thin_dark)
BORDER_BOX_TOP = Border(top=_thin_dark)
BORDER_BOX_TOP_RIGHT = Border(top=_thin_dark, right=_thin_dark)
BORDER_BOX_LEFT = Border(left=_thin_dark)
BORDER_BOX_RIGHT = Border(right=_thin_dark)
BORDER_BOX_BOTTOM_LEFT = Border(bottom=_thin_dark, left=_thin_dark)
BORDER_BOX_BOTTOM = Border(bottom=_thin_dark)
BORDER_BOX_BOTTOM_RIGHT = Border(bottom=_thin_dark, right=_thin_dark)

# ── Fills ─────────────────────────────────────────────────────
FILL_PARCHMENT = PatternFill("solid", fgColor=KLAR["parchment"])
FILL_GOLD_BG = PatternFill("solid", fgColor=KLAR["gold_bg"])
FILL_CARD = PatternFill("solid", fgColor=KLAR["card"])
FILL_ALT = PatternFill("solid", fgColor=KLAR["parchment_lt"])
FILL_WHITE = PatternFill("solid", fgColor=KLAR["white"])
FILL_GOLD_HEADER = PatternFill("solid", fgColor=KLAR["parchment"])

# ── Fonts ─────────────────────────────────────────────────────
FONT_TITLE = Font(name="Calibri", size=22, bold=True, color=KLAR["text"])
FONT_SUBTITLE = Font(name="Calibri", size=11, color=KLAR["dim"])
FONT_SECTION = Font(name="Calibri", size=11, bold=True, color=KLAR["gold"])
FONT_LABEL = Font(name="Calibri", size=9, color=KLAR["dim"])
FONT_BODY = Font(name="Calibri", size=10, color=KLAR["text"])
FONT_BODY_BOLD = Font(name="Calibri", size=10, bold=True, color=KLAR["text"])
FONT_TABLE_HEADER = Font(name="Calibri", size=9.5, bold=True, color=KLAR["gold"])
FONT_TABLE_BODY = Font(name="Calibri", size=10, color=KLAR["text"])
FONT_MONEY = Font(name="Calibri", size=10, color=KLAR["text"])
FONT_MONEY_BOLD = Font(name="Calibri", size=10, bold=True, color=KLAR["text"])
FONT_TOTAL_LABEL = Font(name="Calibri", size=11, bold=True, color=KLAR["gold"])
FONT_TOTAL_VALUE = Font(name="Calibri", size=12, bold=True, color=KLAR["text"])
FONT_DIM = Font(name="Calibri", size=8.5, color=KLAR["dim"])
FONT_DIM_ITALIC = Font(name="Calibri", size=8.5, italic=True, color=KLAR["dim"])
FONT_GOV_LABEL = Font(name="Consolas", size=8.5, bold=True, color=KLAR["gold"])
FONT_GOV_VALUE = Font(name="Consolas", size=8.5, color=KLAR["dim"])
FONT_GOV_HASH = Font(name="Consolas", size=7.5, color=KLAR["border_dark"])
FONT_GOV_TITLE = Font(name="Calibri", size=14, bold=True, color=KLAR["gold"])
FONT_GOV_PRINCIPLE = Font(name="Calibri", size=9, italic=True, color=KLAR["gold"])

# ── Alignments ────────────────────────────────────────────────
ALIGN_LEFT = Alignment(horizontal="left", vertical="center", wrap_text=False)
ALIGN_CENTER = Alignment(horizontal="center", vertical="center")
ALIGN_RIGHT = Alignment(horizontal="right", vertical="center")
ALIGN_LEFT_WRAP = Alignment(horizontal="left", vertical="center", wrap_text=True)
ALIGN_RIGHT_TOP = Alignment(horizontal="right", vertical="top")

# ── Currency formats per locale ───────────────────────────────
CURRENCY_FMT = {
    "de": '#,##0.00 [$€-407]',
    "en": '[$€-409]#,##0.00',
    "pt": '#,##0.00 [$€-816]',
}

# ── Trilingual labels ─────────────────────────────────────────
LABELS = {
    "de": {
        "title": "RECHNUNG", "nr": "Rechnungsnr.", "date": "Datum",
        "due": "Fällig", "from": "ABSENDER", "to": "EMPFÄNGER",
        "item": "Pos.", "desc": "Beschreibung", "qty": "Menge",
        "price": "Einzelpreis", "total": "Gesamt",
        "subtotal": "Zwischensumme", "tax": "MwSt. (19%)",
        "grand": "GESAMTBETRAG", "terms": "Zahlungsziel: 30 Tage netto",
        "bank": "Bankverbindung", "governance": "WINDI Governance",
        "page": "Seite", "generated": "Erstellt mit WINDI Document Engine",
    },
    "en": {
        "title": "INVOICE", "nr": "Invoice No.", "date": "Date",
        "due": "Due Date", "from": "FROM", "to": "TO",
        "item": "#", "desc": "Description", "qty": "Qty",
        "price": "Unit Price", "total": "Total",
        "subtotal": "Subtotal", "tax": "VAT (19%)",
        "grand": "TOTAL DUE", "terms": "Payment terms: Net 30 days",
        "bank": "Bank Details", "governance": "WINDI Governance",
        "page": "Page", "generated": "Generated by WINDI Document Engine",
    },
    "pt": {
        "title": "FATURA", "nr": "Nº da Fatura", "date": "Data",
        "due": "Vencimento", "from": "EMISSOR", "to": "CLIENTE",
        "item": "Item", "desc": "Descrição", "qty": "Qtd",
        "price": "Preço Unit.", "total": "Total",
        "subtotal": "Subtotal", "tax": "IVA (23%)",
        "grand": "TOTAL A PAGAR", "terms": "Condições: 30 dias",
        "bank": "Dados Bancários", "governance": "WINDI Governance",
        "page": "Página", "generated": "Gerado pelo WINDI Document Engine",
    },
}


# ═══════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════

def render_xlsx(context, filepath):
    """Render an XLSX document from context."""
    if not HAS_OPENPYXL:
        raise ImportError("openpyxl not installed")

    doc_type = context.get("doc_type", "report")
    wb = Workbook()
    ws = wb.active

    # Route to doc-type renderer
    if doc_type in ("invoice", "rechnung"):
        _render_invoice(ws, context)
    else:
        _render_data_sheet(ws, context)

    # Governance sheet (always)
    _add_governance_sheet(wb, context)

    wb.save(filepath)


# ═══════════════════════════════════════════════════════════════
# INVOICE RENDERER — P0 KLAR Edition
# ═══════════════════════════════════════════════════════════════

def _render_invoice(ws, context):
    """Professional invoice with KLAR theme, boxes, and print layout."""
    lang = context.get("language", "de")
    text = context.get("text", "")
    user_input = context.get("user_input", "")
    entities = context.get("entities", {})
    json_fields = _extract_json_fields(text)
    # Smart source: prefer user's original input for entity extraction
    extraction_text = user_input if user_input else text
    L = LABELS.get(lang, LABELS["en"])

    # ══════════════════════════════════════════════════════════
    # PARSE USER INPUT — Extract company and items from natural language
    # ══════════════════════════════════════════════════════════
    parsed_input = {}
    if user_input:
        try:
            parsed_input = _parse_invoice_input(user_input, lang)
        except Exception:
            parsed_input = {}

    # Debug logging
    try:
        with open("/tmp/xlsx_debug.log", "w") as _dbg:
            _dbg.write(f"text length: {len(text)}\n")
            _dbg.write(f"user_input length: {len(user_input)}\n")
            _dbg.write(f"extraction_text length: {len(extraction_text)}\n")
            _dbg.write(f"json_fields keys: {list(json_fields.keys())}\n")
            _dbg.write(f"parsed_input: {parsed_input}\n")
            _dbg.write(f"company: {json_fields.get('company_name', 'NOT FOUND')}\n")
            _dbg.write(f"client: {json_fields.get('client_name', 'NOT FOUND')}\n")
            _dbg.write(f"extraction_text first 300: {repr(extraction_text[:300])}\n")
    except Exception:
        pass
    cur_fmt = CURRENCY_FMT.get(lang, CURRENCY_FMT["de"])
    tax_rate = 0.23 if lang == "pt" else 0.19

    ws.title = L["title"]
    ws.sheet_properties.tabColor = KLAR["gold"]

    # ── Page Setup (print-ready) ──────────────────────────────
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.orientation = "portrait"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.page_margins = PageMargins(
        left=0.6, right=0.6, top=0.5, bottom=0.5,
        header=0.3, footer=0.3,
    )
    ws.print_title_rows = "1:2"
    ws.oddHeader.center.text = ""
    ws.oddFooter.left.text = f"&8&K{KLAR['dim']}{L['generated']}"
    ws.oddFooter.right.text = f"&8&K{KLAR['dim']}{L['page']} &P"

    # ── Column widths (A-G) ───────────────────────────────────
    # A=Pos/Label  B=Desc  C=spacer  D=Qty  E=Price  F=Total  G=margin
    widths = {"A": 8, "B": 32, "C": 3, "D": 10, "E": 14, "F": 16, "G": 2}
    for col, w in widths.items():
        ws.column_dimensions[col].width = w

    row = 1

    # ══════════════════════════════════════════════════════════
    # HEADER ZONE — Title + Gold Rule + Invoice Info
    # ══════════════════════════════════════════════════════════

    # Row 1: Title
    ws.merge_cells(f"A{row}:C{row}")
    c = ws.cell(row=row, column=1, value=L["title"])
    c.font = FONT_TITLE
    c.alignment = ALIGN_LEFT
    ws.row_dimensions[row].height = 36

    # Right side: Invoice Nr + Date
    ws.merge_cells(f"E{row}:F{row}")
    c = ws.cell(row=row, column=5, value=f"{L['nr']}:")
    c.font = FONT_LABEL
    c.alignment = ALIGN_RIGHT

    row = 2
    ws.merge_cells(f"A{row}:C{row}")
    ws.row_dimensions[row].height = 4  # gold rule spacer

    # Invoice number + date on right
    inv_nr = json_fields.get("invoice_number") or f"WINDI-{datetime.now().strftime('%Y%m%d')}-001"
    ws.merge_cells(f"E{row}:F{row}")
    c = ws.cell(row=row, column=5, value=inv_nr)
    c.font = FONT_BODY_BOLD
    c.alignment = ALIGN_RIGHT

    row = 3
    # Gold rule across full width
    for col in range(1, 7):
        ws.cell(row=row, column=col).border = BORDER_BOTTOM_GOLD
    ws.row_dimensions[row].height = 6

    row = 4
    ws.merge_cells(f"E{row}:F{row}")
    c = ws.cell(row=row, column=5, value=f"{L['date']}:")
    c.font = FONT_LABEL
    c.alignment = ALIGN_RIGHT

    row = 5
    date_str = datetime.now().strftime("%d.%m.%Y" if lang == "de" else "%d/%m/%Y" if lang == "pt" else "%Y-%m-%d")
    ws.merge_cells(f"E{row}:F{row}")
    c = ws.cell(row=row, column=5, value=date_str)
    c.font = FONT_BODY
    c.alignment = ALIGN_RIGHT
    ws.row_dimensions[row].height = 18

    # ══════════════════════════════════════════════════════════
    # PARTY BOXES — EMISSOR / CLIENTE (side by side)
    # ══════════════════════════════════════════════════════════

    row = 7
    ws.row_dimensions[row].height = 6  # spacer

    row = 8
    # ── Left box: FROM ──
    _draw_box(ws, row, row + 4, 1, 2)
    ws.merge_cells(f"A{row}:B{row}")
    c = ws.cell(row=row, column=1, value=L["from"])
    c.font = FONT_SECTION
    c.alignment = ALIGN_LEFT
    c.fill = FILL_PARCHMENT

    # FROM content
    orgs = entities.get("org", [])
    persons = entities.get("person", [])

    # Extract company/client from user input if not in JSON
    if not json_fields.get("company_name") and not orgs:
        _enrich_from_input(json_fields, extraction_text)
    from_name = json_fields.get("company_name") or (orgs[0] if orgs else "[Firma / Company]")
    from_addr = json_fields.get("company_address", "")
    from_tax = json_fields.get("company_tax_id", "")

    ws.merge_cells(f"A{row+1}:B{row+1}")
    ws.cell(row=row + 1, column=1, value=from_name).font = FONT_BODY_BOLD
    ws.merge_cells(f"A{row+2}:B{row+2}")
    ws.cell(row=row + 2, column=1, value=from_addr or "[Adresse / Address]").font = FONT_BODY
    ws.merge_cells(f"A{row+3}:B{row+3}")
    ws.cell(row=row + 3, column=1, value=from_tax or "[USt-IdNr. / Tax ID]").font = FONT_DIM

    # ── Right box: TO ──
    _draw_box(ws, row, row + 4, 4, 6)
    ws.merge_cells(f"D{row}:F{row}")
    c = ws.cell(row=row, column=4, value=L["to"])
    c.font = FONT_SECTION
    c.alignment = ALIGN_LEFT
    c.fill = FILL_PARCHMENT

    # Priority: parsed_input > json_fields > entities > placeholder
    to_name = (
        parsed_input.get("company")
        or json_fields.get("client_name")
        or (orgs[1] if len(orgs) > 1 else None)
        or (orgs[0] if orgs else None)
        or (persons[0] if persons else None)
        or "[Kunde / Client]"
    )
    to_addr = parsed_input.get("address") or json_fields.get("client_address", "")
    to_ref = json_fields.get("client_reference", "")

    ws.merge_cells(f"D{row+1}:F{row+1}")
    ws.cell(row=row + 1, column=4, value=to_name).font = FONT_BODY_BOLD
    ws.merge_cells(f"D{row+2}:F{row+2}")
    ws.cell(row=row + 2, column=4, value=to_addr or "[Adresse / Address]").font = FONT_BODY
    ws.merge_cells(f"D{row+3}:F{row+3}")
    ws.cell(row=row + 3, column=4, value=to_ref or "[Referenz / Reference]").font = FONT_DIM

    # Set consistent row heights for boxes
    for r in range(row, row + 5):
        ws.row_dimensions[r].height = 18

    # ══════════════════════════════════════════════════════════
    # ITEMS TABLE
    # ══════════════════════════════════════════════════════════

    row = 14
    ws.row_dimensions[row].height = 6  # spacer before table

    row = 15
    # Gold rule above table
    for col in range(1, 7):
        ws.cell(row=row, column=col).border = BORDER_BOTTOM_GOLD
    ws.row_dimensions[row].height = 4

    # Table header
    row = 16
    th = [
        (1, L["item"], ALIGN_CENTER, 1),
        (2, L["desc"], ALIGN_LEFT, 2),
        (4, L["qty"], ALIGN_CENTER, 4),
        (5, L["price"], ALIGN_RIGHT, 5),
        (6, L["total"], ALIGN_RIGHT, 6),
    ]
    for col, text_val, align, _ in th:
        c = ws.cell(row=row, column=col, value=text_val)
        c.font = FONT_TABLE_HEADER
        c.alignment = align
        c.fill = FILL_PARCHMENT
        c.border = BORDER_TABLE_HEADER

    # Also style column C header (part of desc span)
    ws.cell(row=row, column=3).fill = FILL_PARCHMENT
    ws.cell(row=row, column=3).border = BORDER_TABLE_HEADER
    ws.row_dimensions[row].height = 22

    # ── Parse items ───────────────────────────────────────────
    items = _extract_invoice_items(extraction_text, entities, json_fields, parsed_input)
    item_start = row + 1

    for i, item in enumerate(items):
        r = item_start + i
        ws.row_dimensions[r].height = 22

        # Pos number
        c = ws.cell(row=r, column=1, value=i + 1)
        c.font = FONT_TABLE_BODY
        c.alignment = ALIGN_CENTER

        # Description (spans B:C)
        ws.merge_cells(f"B{r}:C{r}")
        c = ws.cell(row=r, column=2, value=item["desc"])
        c.font = FONT_TABLE_BODY
        c.alignment = ALIGN_LEFT

        # Qty
        c = ws.cell(row=r, column=4, value=item["qty"])
        c.font = FONT_TABLE_BODY
        c.alignment = ALIGN_CENTER

        # Unit price
        c = ws.cell(row=r, column=5, value=item["price"])
        c.font = FONT_MONEY
        c.number_format = cur_fmt
        c.alignment = ALIGN_RIGHT

        # Total (formula)
        c = ws.cell(row=r, column=6)
        c.value = f"=D{r}*E{r}"
        c.font = FONT_MONEY
        c.number_format = cur_fmt
        c.alignment = ALIGN_RIGHT

        # Alternate row shading
        if i % 2 == 1:
            for col in range(1, 7):
                ws.cell(row=r, column=col).fill = FILL_ALT

        # Bottom border on every item row
        for col in range(1, 7):
            existing = ws.cell(row=r, column=col).border
            ws.cell(row=r, column=col).border = BORDER_TABLE_CELL

    last_item_row = item_start + len(items) - 1

    # ══════════════════════════════════════════════════════════
    # TOTALS ZONE
    # ══════════════════════════════════════════════════════════

    row = last_item_row + 2
    ws.row_dimensions[row].height = 20

    # Subtotal
    c = ws.cell(row=row, column=5, value=f"{L['subtotal']}:")
    c.font = FONT_TABLE_HEADER
    c.alignment = ALIGN_RIGHT
    c = ws.cell(row=row, column=6)
    c.value = f"=SUM(F{item_start}:F{last_item_row})"
    c.font = FONT_MONEY_BOLD
    c.number_format = cur_fmt
    c.alignment = ALIGN_RIGHT

    # Tax
    row += 1
    ws.row_dimensions[row].height = 18
    tax_label = L["tax"]
    c = ws.cell(row=row, column=5, value=f"{tax_label}:")
    c.font = FONT_DIM
    c.alignment = ALIGN_RIGHT
    c = ws.cell(row=row, column=6)
    c.value = f"=F{row-1}*{tax_rate}"
    c.font = FONT_MONEY
    c.number_format = cur_fmt
    c.alignment = ALIGN_RIGHT
    c.border = BORDER_BOTTOM_THIN

    # Grand total — with double gold rule
    row += 1
    ws.row_dimensions[row].height = 8  # small spacer

    row += 1
    ws.row_dimensions[row].height = 28
    c = ws.cell(row=row, column=4, value=L["grand"])
    c.font = FONT_TOTAL_LABEL
    c.alignment = ALIGN_RIGHT

    ws.merge_cells(f"E{row}:F{row}")
    c = ws.cell(row=row, column=5)
    c.value = f"=F{row-3}+F{row-2}"
    c.font = FONT_TOTAL_VALUE
    c.number_format = cur_fmt
    c.alignment = ALIGN_RIGHT
    c.border = BORDER_DOUBLE_GOLD
    # Also style merged cell F
    ws.cell(row=row, column=6).border = BORDER_DOUBLE_GOLD

    # ══════════════════════════════════════════════════════════
    # FOOTER — Terms + WINDI branding
    # ══════════════════════════════════════════════════════════

    row += 2
    # Gold rule
    for col in range(1, 7):
        ws.cell(row=row, column=col).border = BORDER_TOP_GOLD
    ws.row_dimensions[row].height = 6

    row += 1
    ws.merge_cells(f"A{row}:C{row}")
    ws.cell(row=row, column=1, value=L["terms"]).font = FONT_DIM
    ws.row_dimensions[row].height = 16

    row += 2
    ws.merge_cells(f"A{row}:F{row}")
    ws.cell(row=row, column=1, value="AI processes. Human decides. WINDI guarantees.").font = FONT_DIM_ITALIC

    # ══════════════════════════════════════════════════════════
    # Print area
    # ══════════════════════════════════════════════════════════
    ws.print_area = f"A1:F{row}"


# ═══════════════════════════════════════════════════════════════
# DATA SHEET RENDERER (reports, memos, protocols, etc.)
# ═══════════════════════════════════════════════════════════════

def _render_data_sheet(ws, context):
    """Render a generic data/report spreadsheet from markdown text."""
    text = context.get("text", "")
    lang = context.get("language", "de")
    doc_type = context.get("doc_type", "report")

    title = doc_type.replace("_", " ").title()
    ws.title = title[:31]  # Excel tab name limit
    ws.sheet_properties.tabColor = KLAR["gold"]

    # Page setup
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.page_margins = PageMargins(left=0.6, right=0.6, top=0.5, bottom=0.5)

    # Column widths
    for col in range(1, 8):
        ws.column_dimensions[get_column_letter(col)].width = 18

    row = 1
    # Title
    ws.merge_cells("A1:F1")
    c = ws.cell(row=1, column=1, value=title)
    c.font = FONT_TITLE
    c.alignment = ALIGN_LEFT
    ws.row_dimensions[1].height = 36

    # Gold rule
    row = 2
    for col in range(1, 7):
        ws.cell(row=row, column=col).border = BORDER_BOTTOM_GOLD
    ws.row_dimensions[row].height = 4

    # Date
    row = 3
    ws.cell(row=row, column=1, value=datetime.now().strftime("%d.%m.%Y")).font = FONT_DIM
    ws.row_dimensions[row].height = 16

    # Parse text content
    row = 5
    lines = text.strip().split("\n")
    in_table_header = False

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            row += 1
            continue

        if stripped.startswith("#"):
            level = min(len(stripped) - len(stripped.lstrip("#")), 4)
            clean = stripped.lstrip("# ").strip()
            fonts = [FONT_TITLE, FONT_SECTION,
                     Font(name="Calibri", size=10, bold=True, color=KLAR["text"]),
                     Font(name="Calibri", size=10, bold=True, color=KLAR["dim"])]
            ws.merge_cells(f"A{row}:F{row}")
            c = ws.cell(row=row, column=1, value=clean)
            c.font = fonts[min(level - 1, 3)]
            if level == 1:
                ws.row_dimensions[row].height = 28
            else:
                ws.row_dimensions[row].height = 22
            row += 1

        elif "|" in stripped and stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            is_sep = all(re.match(r"^[\s\-:]+$", c) for c in cells)
            if is_sep:
                in_table_header = False
                continue
            # Check if next line is separator (= this is header)
            is_header = (idx + 1 < len(lines) and
                         re.match(r"^\|[\s\-:|]+\|", lines[idx + 1].strip()))
            for c_idx, cell_text in enumerate(cells):
                c = ws.cell(row=row, column=c_idx + 1, value=cell_text)
                if is_header:
                    c.font = FONT_TABLE_HEADER
                    c.fill = FILL_PARCHMENT
                    c.border = BORDER_TABLE_HEADER
                else:
                    c.font = FONT_TABLE_BODY
                    c.border = BORDER_TABLE_CELL
            ws.row_dimensions[row].height = 20
            row += 1

        elif stripped.startswith(("- ", "• ", "* ")):
            ws.cell(row=row, column=1, value="•").font = FONT_BODY
            ws.cell(row=row, column=1).alignment = ALIGN_CENTER
            ws.merge_cells(f"B{row}:F{row}")
            ws.cell(row=row, column=2, value=stripped[2:]).font = FONT_BODY
            ws.row_dimensions[row].height = 18
            row += 1

        elif stripped.startswith("**") and stripped.endswith("**"):
            ws.merge_cells(f"A{row}:F{row}")
            ws.cell(row=row, column=1, value=stripped.strip("*")).font = FONT_BODY_BOLD
            ws.row_dimensions[row].height = 18
            row += 1

        else:
            ws.merge_cells(f"A{row}:F{row}")
            c = ws.cell(row=row, column=1, value=stripped)
            c.font = FONT_BODY
            c.alignment = ALIGN_LEFT_WRAP
            ws.row_dimensions[row].height = 18
            row += 1


# ═══════════════════════════════════════════════════════════════
# GOVERNANCE SHEET — Premium audit trail
# ═══════════════════════════════════════════════════════════════

def _add_governance_sheet(wb, context):
    """Professional governance metadata sheet with KLAR styling."""
    gs = wb.create_sheet("WINDI Governance")
    gs.sheet_properties.tabColor = KLAR["gold"]

    # Page setup
    gs.page_setup.paperSize = gs.PAPERSIZE_A4
    gs.page_margins = PageMargins(left=0.6, right=0.6, top=0.5, bottom=0.5)

    gs.column_dimensions["A"].width = 22
    gs.column_dimensions["B"].width = 48
    gs.column_dimensions["C"].width = 3
    gs.column_dimensions["D"].width = 22
    gs.column_dimensions["E"].width = 24

    row = 1
    # Title
    gs.merge_cells(f"A{row}:E{row}")
    c = gs.cell(row=row, column=1, value="WINDI GOVERNANCE RECEIPT")
    c.font = FONT_GOV_TITLE
    c.alignment = ALIGN_LEFT
    gs.row_dimensions[row].height = 30

    # Gold rule
    row = 2
    for col in range(1, 6):
        gs.cell(row=row, column=col).border = BORDER_BOTTOM_GOLD
    gs.row_dimensions[row].height = 4

    row = 3
    gs.row_dimensions[row].height = 8

    # ── Document metadata (left) ──
    row = 4
    meta_left = [
        ("Engine", "WINDI Document Renderer v2.0.0"),
        ("Format", "XLSX (openpyxl)"),
        ("Tier", context.get("tier", "—")),
        ("Language", context.get("language", "—").upper()),
        ("Doc Type", context.get("doc_type", "—")),
        ("Timestamp", context.get("timestamp", datetime.now().isoformat())),
        ("Formality", context.get("formality", "formal")),
    ]

    for i, (label, value) in enumerate(meta_left):
        r = row + i
        gs.cell(row=r, column=1, value=label).font = FONT_GOV_LABEL
        gs.cell(row=r, column=2, value=value).font = FONT_GOV_VALUE
        gs.row_dimensions[r].height = 16

    # ── SGE data (right) ──
    sge = context.get("sge") or {}
    meta_right = [
        ("SGE Score", str(sge.get("score", "—"))),
        ("Risk Level", str(sge.get("risk", "R0"))),
        ("Human Required", str(sge.get("humanRequired", False))),
        ("Blocked", str(sge.get("blocked", False))),
        ("Invariants I1-I9", "PASS" if not sge.get("hasFatal") else "FAIL"),
        ("Stability S1-S8", "ACTIVE"),
        ("Layer L7", "APPLIED"),
    ]

    for i, (label, value) in enumerate(meta_right):
        r = row + i
        gs.cell(row=r, column=4, value=label).font = FONT_GOV_LABEL
        c = gs.cell(row=r, column=5, value=value)
        c.font = FONT_GOV_VALUE
        # Color code risk
        if label == "Risk Level":
            risk = value
            if risk in ("R0", "R1"):
                c.font = Font(name="Consolas", size=8.5, color=KLAR["green"])
            elif risk in ("R4", "R5"):
                c.font = Font(name="Consolas", size=8.5, color=KLAR["red"])
        elif label.startswith("Invariants"):
            if "PASS" in value:
                c.font = Font(name="Consolas", size=8.5, bold=True, color=KLAR["green"])
            else:
                c.font = Font(name="Consolas", size=8.5, bold=True, color=KLAR["red"])

    # ── Forensic receipt ──
    row = row + max(len(meta_left), len(meta_right)) + 1
    gs.row_dimensions[row].height = 6
    for col in range(1, 6):
        gs.cell(row=row, column=col).border = BORDER_BOTTOM_THIN

    row += 1
    receipt = context.get("receipt") or {}
    if receipt:
        gs.merge_cells(f"A{row}:E{row}")
        gs.cell(row=row, column=1, value="FORENSIC RECEIPT").font = FONT_GOV_LABEL
        gs.row_dimensions[row].height = 20

        receipt_fields = [
            ("Receipt Hash", receipt.get("hash", "—")),
            ("Categories", ", ".join(receipt.get("categories", []))),
            ("Governance", receipt.get("governance", "—")),
            ("Decision", receipt.get("decision", "—")),
            ("Flags", str(receipt.get("flags", []))),
        ]
        for i, (label, value) in enumerate(receipt_fields):
            r = row + 1 + i
            gs.cell(row=r, column=1, value=label).font = FONT_GOV_LABEL
            gs.merge_cells(f"B{r}:E{r}")
            c = gs.cell(row=r, column=2, value=str(value))
            c.font = FONT_GOV_HASH if "hash" in label.lower() else FONT_GOV_VALUE
            gs.row_dimensions[r].height = 16
        row = row + len(receipt_fields) + 2
    else:
        gs.merge_cells(f"A{row}:E{row}")
        gs.cell(row=row, column=1, value="No forensic receipt (tier may not include ledger)").font = FONT_DIM
        row += 2

    # ── Closing principle ──
    for col in range(1, 6):
        gs.cell(row=row, column=col).border = BORDER_TOP_GOLD
    gs.row_dimensions[row].height = 6

    row += 1
    gs.merge_cells(f"A{row}:E{row}")
    gs.cell(row=row, column=1, value="AI processes. Human decides. WINDI guarantees.").font = FONT_GOV_PRINCIPLE
    gs.row_dimensions[row].height = 20

    gs.print_area = f"A1:E{row}"


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _draw_box(ws, r1, r2, c1, c2):
    """Draw a rectangular box border around a cell range."""
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            top = _thin_dark if r == r1 else _no
            bottom = _thin_dark if r == r2 else _no
            left = _thin_dark if c == c1 else _no
            right = _thin_dark if c == c2 else _no
            ws.cell(row=r, column=c).border = Border(
                top=top, bottom=bottom, left=left, right=right,
            )
            # Light background inside box
            if r > r1:
                ws.cell(row=r, column=c).fill = FILL_CARD


BORDER_BOTTOM_THIN = Border(bottom=_thin)


def _extract_invoice_items(text, entities, json_fields=None, parsed_input=None):
    """Extract invoice line items from text content."""
    json_fields = json_fields or {}
    parsed_input = parsed_input or {}
    items = []
    money_values = entities.get("money", [])

    # Priority 1: Parsed user input (most reliable for natural language)
    if parsed_input.get("items"):
        for pitem in parsed_input["items"]:
            desc = pitem.get("description") or "Service"
            qty = pitem.get("qty") or 1
            price = pitem.get("unit_price") or 0
            items.append({"desc": desc, "qty": qty, "price": price})
        if items:
            return items

    # Priority 2: JSON fields from LLM response
    if json_fields.get("items"):
        for jitem in json_fields["items"]:
            desc = jitem.get("description") or jitem.get("desc") or "Service"
            qty = jitem.get("quantity") or jitem.get("qty") or 1
            price = jitem.get("unit_price") or jitem.get("price") or 0
            if isinstance(price, str):
                price = float(re.sub(r"[^\d.]", "", price.replace(",", "")) or "0")
            if isinstance(qty, str):
                qty = int(re.sub(r"[^\d]", "", qty) or "1")
            items.append({"desc": desc, "qty": qty, "price": price})
        if items:
            return items

    # Try text patterns
    lines = text.split("\n")
    for line in lines:
        stripped = line.strip()
        # Match both formats: €1,234.56 (EN) and €1.234,56 (DE/PT) and plain €800
        money_match = re.search(
            r'[€$£]\s*[\d.,]+|[\d.,]+\s*[€$£]', stripped
        )
        if money_match and (
            stripped.startswith("-") or stripped.startswith("•") or re.match(r"^\d+[\.\)]", stripped)
        ):
            desc = re.sub(r'[€$£]\s*[\d,]+(?:\.\d{2})?|[\d,]+(?:\.\d{2})?\s*[€$£]', '', stripped)
            desc = re.sub(r'^[-•\d\.\)]\s*', '', desc).strip().rstrip(":").strip()
            price_str = _parse_eur_amount(money_match.group())
            price = price_str
            items.append({"desc": desc or "Service", "qty": 1, "price": price})

    # Fallback: money entities
    if not items and money_values:
        for mv in money_values:
            price_str = re.sub(r'[^\d.]', '', mv.replace(",", ""))
            try:
                price = float(price_str)
            except ValueError:
                price = 0
            items.append({"desc": "Service / Dienstleistung", "qty": 1, "price": price})

    # Template placeholders (3 rows for professional look)
    if not items:
        items = [
            {"desc": "[Descrição 1]", "qty": 1, "price": 0},
            {"desc": "[Descrição 2]", "qty": 1, "price": 0},
            {"desc": "[Descrição 3]", "qty": 1, "price": 0},
        ]

    return items



def _parse_eur_amount(raw):
    """Parse European currency: €2.500,00 → 2500.0 / €800 → 800.0 / €1,234.56 → 1234.56"""
    s = raw.replace("€", "").replace("$", "").replace("£", "").strip()
    # Detect format: if comma is after last dot → DE/PT format (1.234,56)
    has_comma = "," in s
    has_dot = "." in s
    if has_comma and has_dot:
        if s.rfind(",") > s.rfind("."):
            # DE/PT: 2.500,00 → remove dots, comma→dot
            s = s.replace(".", "").replace(",", ".")
        else:
            # EN: 1,234.56 → remove commas
            s = s.replace(",", "")
    elif has_comma and not has_dot:
        # Could be DE decimal (0,50) or DE thousands (1,000)
        parts = s.split(",")
        if len(parts) == 2 and len(parts[1]) == 2:
            # Likely decimal: 800,00 → 800.00
            s = s.replace(",", ".")
        else:
            # Thousands separator: 1,000 → 1000
            s = s.replace(",", "")
    # else: has_dot only → EN format, keep as is
    try:
        return float(s)
    except ValueError:
        return 0.0


def _enrich_from_input(json_fields, user_input):
    """Extract company/client names from user's natural language input."""
    if not user_input:
        return

    text_lower = user_input.lower()

    # Pattern: "für/para/for [Company]" — extract org after preposition
    org_patterns = [
        r'(?:für|para|for|an|to|a)\s+([A-Z][A-Za-zÀ-ÿ&.\-]+(?:\s+[A-Z][A-Za-zÀ-ÿ&.\-]+)*(?:\s+(?:GmbH|AG|Ltd|Inc|SA|S\.A\.|e\.V\.|UG|OHG|KG|Co|Corp))?)',
    ]
    for pat in org_patterns:
        m = re.search(pat, user_input)
        if m:
            name = m.group(1).strip().rstrip(".,;:")
            if len(name) > 2 and not json_fields.get("client_name"):
                json_fields["client_name"] = name
                break


def _parse_german_price(raw):
    """
    Parse German/European price format.

    Rules:
    - €2.500 = 2500 (dot is thousands separator)
    - €2.500,00 = 2500.00
    - €2,50 = 2.50 (comma is decimal)
    - €1.200,50 = 1200.50
    - 2500 EUR = 2500.00
    """
    if not raw:
        return 0.0

    # Remove currency symbols and whitespace
    s = re.sub(r'[€$£]|\s|EUR|eur', '', str(raw)).strip()
    if not s:
        return 0.0

    has_comma = ',' in s
    has_dot = '.' in s

    if has_comma and has_dot:
        # Both present: check which comes last
        if s.rfind(',') > s.rfind('.'):
            # DE/PT format: 1.234,56 → remove dots, comma→dot
            s = s.replace('.', '').replace(',', '.')
        else:
            # EN format: 1,234.56 → remove commas
            s = s.replace(',', '')
    elif has_comma and not has_dot:
        # Comma only - check if it's decimal or thousands
        parts = s.split(',')
        if len(parts) == 2 and len(parts[1]) <= 2:
            # Decimal: 2500,00 or 2,50 → comma is decimal
            s = s.replace(',', '.')
        else:
            # Thousands: 1,000,000 → remove commas
            s = s.replace(',', '')
    elif has_dot and not has_comma:
        # Dot only - check if thousands or decimal
        parts = s.split('.')
        if len(parts) == 2 and len(parts[1]) == 3 and len(parts[0]) >= 1:
            # German thousands: 2.500 → remove dot (it's a thousands separator)
            s = s.replace('.', '')
        elif len(parts) > 2:
            # Multiple dots: 1.000.000 → thousands separator
            s = s.replace('.', '')
        # else: single dot with ≤2 decimal digits → keep as decimal

    try:
        return float(s)
    except ValueError:
        return 0.0


def _parse_invoice_input(user_input, language="de"):
    """
    Parse invoice data from user's natural language input.

    Returns:
        {
            "company": "Siemens AG",
            "address": "...",
            "items": [
                {"description": "Widget", "qty": 3, "unit_price": 2500.00},
            ],
            "payment_terms": None,
            "reference": None,
        }
    """
    result = {
        "company": None,
        "address": None,
        "items": [],
        "payment_terms": None,
        "reference": None,
    }

    if not user_input:
        return result

    text = user_input.strip()

    # ══════════════════════════════════════════════════════════
    # 1. EXTRACT COMPANY NAME (trilingual)
    # ══════════════════════════════════════════════════════════

    # Patterns for company extraction (order matters - more specific first)
    company_patterns = [
        # "Kunde: Siemens AG" / "Client: Siemens AG" / "Cliente: BMW"
        r'(?:Kunde|Client|Cliente)\s*:\s*([A-ZÀ-Ý][A-Za-zÀ-ÿ&.\-\s]+(?:GmbH|AG|Ltd|Inc|SA|S\.A\.|e\.V\.|UG|OHG|KG|Co|Corp\.?)?)',
        # "für/fuer Siemens AG" / "for Siemens AG" / "para Siemens AG"
        r'(?:für|fuer|for|para)\s+([A-ZÀ-Ý][A-Za-zÀ-ÿ&.\-\s]+(?:GmbH|AG|Ltd|Inc|SA|S\.A\.|e\.V\.|UG|OHG|KG|Co|Corp\.?)?)',
        # "an Deutsche Bahn" / "to Deutsche Bahn"
        r'(?:an|to|a)\s+([A-ZÀ-Ý][A-Za-zÀ-ÿ&.\-\s]+(?:GmbH|AG|Ltd|Inc|SA|S\.A\.|e\.V\.|UG|OHG|KG|Co|Corp\.?)?)',
    ]

    for pattern in company_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            # Clean trailing punctuation and common words that aren't part of company name
            company = re.sub(r'[,;:\.]$', '', company).strip()
            # Stop at common delimiters that signal end of company name
            company = re.split(r'\s*[,;]\s*(?:Positionen|items|Artikel|Position|mit|with|com)\s*', company, flags=re.IGNORECASE)[0]
            if len(company) > 2:
                result["company"] = company.strip()
                break

    # ══════════════════════════════════════════════════════════
    # 2. EXTRACT ITEMS (quantity, description, price)
    # ══════════════════════════════════════════════════════════

    items = []

    # Price pattern - matches €2.500, €2.500,00, 2500 EUR, etc.
    price_pattern = r'[€$£]\s*[\d.,]+|[\d.,]+\s*(?:EUR|eur|€|\$|£)'

    # Pattern 1: "3x Widget à €2.500" or "3 x Widget a €2.500,00" or "3x Widget 2500 EUR"
    # Matches: qty, description, price
    item_patterns = [
        # "3x Widget à €2.500" or "3 x Widget a 2500 EUR"
        r'(\d+)\s*[xX×]\s*([^€$£\d,;]+?)\s*(?:[àaá@]|at)?\s*(' + price_pattern + r')',
        # "3x Widget €2.500" (no à/a separator)
        r'(\d+)\s*[xX×]\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-]+?)\s+(' + price_pattern + r')',
        # "3 Widget 2500 EUR" (space instead of x)
        r'(\d+)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-]+?)\s+(' + price_pattern + r')',
    ]

    # First try to find "Positionen:" or "items:" section
    positions_match = re.search(r'(?:Positionen|items|Artikel)\s*:\s*(.+)', text, re.IGNORECASE)
    items_text = positions_match.group(1) if positions_match else text

    # Split on common item separators - only split before "Nx Item" patterns
    # Avoid splitting on price decimals like "3.500,00 EUR"
    item_chunks = re.split(r'\s*[,;]\s*(?=\d+\s*[xX×]\s*[A-Za-z])', items_text)

    for chunk in item_chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        for pattern in item_patterns:
            match = re.search(pattern, chunk, re.IGNORECASE)
            if match:
                qty_str, desc, price_str = match.groups()
                qty = int(qty_str) if qty_str.isdigit() else 1
                desc = desc.strip().rstrip('àaá@: ')
                # Clean up description
                desc = re.sub(r'\s+', ' ', desc).strip()
                if desc and len(desc) > 1:
                    price = _parse_german_price(price_str)
                    items.append({
                        "description": desc,
                        "qty": qty,
                        "unit_price": price,
                    })
                break

    # Pattern 2: If no items found with qty pattern, try "1x Beratung €12.500,00" or just item + price
    if not items:
        # Try single item pattern without explicit separator
        single_patterns = [
            r'(\d+)\s*[xX×]\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-]+?)\s*(' + price_pattern + r')',
            r'([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-]+?)\s+(' + price_pattern + r')',
        ]
        for pattern in single_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                groups = match.groups()
                if len(groups) == 3:
                    qty_str, desc, price_str = groups
                    qty = int(qty_str) if qty_str.isdigit() else 1
                elif len(groups) == 2:
                    desc, price_str = groups
                    qty = 1
                else:
                    continue

                desc = desc.strip().rstrip('àaá@: ')
                desc = re.sub(r'\s+', ' ', desc).strip()
                # Filter out company names that might have been matched
                if desc and len(desc) > 1 and desc.lower() not in ['für', 'for', 'para', 'an', 'to']:
                    if result["company"] and desc.lower() == result["company"].lower():
                        continue
                    price = _parse_german_price(price_str)
                    if price > 0:
                        items.append({
                            "description": desc,
                            "qty": qty,
                            "unit_price": price,
                        })

    result["items"] = items
    return result


def _extract_json_fields(text):
    """Extract structured fields from LLM JSON block."""
    import json as _json
    fields = {}
    try:
        bt3 = chr(96) * 3
        start = text.find(bt3 + "json")
        if start < 0:
            start = text.find('{"document"')
        if start >= 0:
            end = text.find(bt3, start + 4) if bt3 + "json" in text[start:start + 8] else -1
            raw = ""
            if end > start:
                raw = text[start:end].lstrip(chr(96)).lstrip("json").strip()
            else:
                brace = text.find("{", start)
                if brace >= 0:
                    depth = 0
                    for i in range(brace, min(brace + 5000, len(text))):
                        if text[i] == "{":
                            depth += 1
                        elif text[i] == "}":
                            depth -= 1
                        if depth == 0:
                            raw = text[brace : i + 1]
                            break
            if raw:
                parsed = _json.loads(raw)
                if "document" in parsed:
                    doc = parsed["document"]
                    fields = doc.get("fields", {})
                    if "content" in doc:
                        fields["_content"] = doc["content"]
                elif "fields" in parsed:
                    fields = parsed["fields"]
                else:
                    fields = parsed
    except Exception:
        pass
    return fields
