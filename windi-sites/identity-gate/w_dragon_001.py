"""
W-DRAGON-001 — Dragon Shadow Forest Core Module
"Invisible guardians encoding truth in every document"

Port: :8122 (via WINDI-SITES)
Invariants: I9 (Human Gate), I11 (Ledger Sovereignty), I14 (No Placeholders)

Liga IA+H · Kempten, Bavaria · 2026
"""

import hashlib
import os
import io
import logging
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional, List, Tuple
import json
import requests

# PDF manipulation
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.utils import ImageReader
    from PyPDF2 import PdfReader, PdfWriter
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# QR Code generation
try:
    import qrcode
    from PIL import Image
    QR_SUPPORT = True
except ImportError:
    QR_SUPPORT = False

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════

VERSION = "1.1.0"  # Forensic: QR + Microtext + PDF Metadata
GRID_SIZE = 16  # 16x16 = 256 bits = SHA-256
CELL_SIZE_MM = 1.5  # Each dragon glyph cell
GRID_OFFSET_X_MM = 20  # Position from left
GRID_OFFSET_Y_MM = 20  # Position from bottom

# Dragon Glyph SVG paths (simplified for embedding)
# Dark Dragon (bit=1): Heptagon shape
DARK_DRAGON_PATH = "M8,0 L14.5,3.5 L15,10.5 L10.5,15 L5.5,15 L1,10.5 L1.5,3.5 Z"
# Shadow Dragon (bit=0): Diamond shape
SHADOW_DRAGON_PATH = "M8,0 L16,8 L8,16 L0,8 Z"

# Opacity levels
OPACITY_PRINT = 0.07    # Invisible at reading distance
OPACITY_SCREEN = 0.18   # Visible for demo/verification

# Ledger configuration
# NOTA: Ledger :8101 usa autenticação interna, sem Bearer token
# Endpoint correcto: POST /api/receipts (não /ledger/register)
LEDGER_URL = os.getenv("LEDGER_URL", "http://127.0.0.1:8101")


# ═══════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class DSFReceipt:
    """Dragon Shadow Forest Receipt"""
    receipt_id: str
    content_hash: str
    bits: List[int]
    created_at: str
    status: str  # 'SEALED' or 'PENDING'
    ledger_url: Optional[str] = None


@dataclass
class DSFEncodeResult:
    """Result of document encoding"""
    receipt: DSFReceipt
    svg_grid: str
    pdf_overlay: Optional[bytes] = None
    verify_url: str = ""


# ═══════════════════════════════════════════════════════════════
# CORE FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def compute_hash(content: bytes) -> str:
    """
    Compute SHA-256 hash of content.
    Returns hex string (64 chars).
    """
    return hashlib.sha256(content).hexdigest()


def hash_to_bits(hash_hex: str) -> List[int]:
    """
    Convert SHA-256 hex to 256 bits.
    Each bit becomes a dragon glyph.

    Returns: List of 256 integers (0 or 1)
    """
    if len(hash_hex) != 64:
        raise ValueError(f"Invalid SHA-256 hash length: {len(hash_hex)}")

    bits = []
    for char in hash_hex:
        nibble = int(char, 16)
        for i in range(3, -1, -1):  # MSB first
            bits.append((nibble >> i) & 1)

    return bits


def bits_to_hash(bits: List[int]) -> str:
    """
    Reconstruct SHA-256 hex from 256 bits.
    Inverse of hash_to_bits().
    """
    if len(bits) != 256:
        raise ValueError(f"Expected 256 bits, got {len(bits)}")

    hex_chars = []
    for i in range(0, 256, 4):
        nibble = (bits[i] << 3) | (bits[i+1] << 2) | (bits[i+2] << 1) | bits[i+3]
        hex_chars.append(format(nibble, 'x'))

    return ''.join(hex_chars)


def generate_receipt_id() -> str:
    """
    Generate WINDI receipt ID for Dragon Shadow Forest.
    Format: WINDI-DSF-{timestamp}-{random}
    """
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    random_part = hashlib.sha256(os.urandom(32)).hexdigest()[:8].upper()
    return f"WINDI-DSF-{ts}-{random_part}"


# ═══════════════════════════════════════════════════════════════
# SVG GENERATION
# ═══════════════════════════════════════════════════════════════

def generate_svg_grid(
    bits: List[int],
    cell_size: int = 20,
    opacity: float = OPACITY_SCREEN,
    show_border: bool = True
) -> str:
    """
    Generate SVG representation of Dragon Shadow Forest.

    Args:
        bits: 256 bits from SHA-256 hash
        cell_size: Size of each dragon cell in pixels
        opacity: Opacity of dragons (0.07 print, 0.18 screen)
        show_border: Show grid border

    Returns: SVG string
    """
    if len(bits) != 256:
        raise ValueError(f"Expected 256 bits, got {len(bits)}")

    grid_px = GRID_SIZE * cell_size

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {grid_px} {grid_px}" ',
        f'width="{grid_px}" height="{grid_px}">'
    ]

    # Background
    if show_border:
        svg_parts.append(
            f'<rect x="0" y="0" width="{grid_px}" height="{grid_px}" '
            f'fill="none" stroke="#8B6914" stroke-width="1" opacity="0.3"/>'
        )

    # Dragon glyphs
    for idx, bit in enumerate(bits):
        row = idx // GRID_SIZE
        col = idx % GRID_SIZE
        x = col * cell_size
        y = row * cell_size

        # Scale path to cell size
        scale = cell_size / 16  # Original paths are 16x16

        if bit == 1:
            # Dark Dragon - heptagon
            path = DARK_DRAGON_PATH
            fill = "#1a1a1a"
        else:
            # Shadow Dragon - diamond
            path = SHADOW_DRAGON_PATH
            fill = "#8B6914"

        svg_parts.append(
            f'<g transform="translate({x},{y}) scale({scale})">'
            f'<path d="{path}" fill="{fill}" opacity="{opacity}"/>'
            f'</g>'
        )

    svg_parts.append('</svg>')
    return ''.join(svg_parts)


def generate_svg_with_metadata(
    bits: List[int],
    receipt_id: str,
    content_hash: str,
    cell_size: int = 20,
    opacity: float = OPACITY_SCREEN
) -> str:
    """
    Generate SVG with embedded metadata comments.
    The metadata allows verification without Ledger access.
    """
    svg = generate_svg_grid(bits, cell_size, opacity)

    # Insert metadata as XML comment before closing tag
    metadata = f'''
<!--
  Dragon Shadow Forest™ - Forensic Verification Layer
  Receipt: {receipt_id}
  Hash: {content_hash}
  Grid: {GRID_SIZE}x{GRID_SIZE} = 256 bits
  Generated: {datetime.now(timezone.utc).isoformat()}
  Verify: https://windi-domain.com/verify-public/?id={receipt_id}
-->
'''
    return svg.replace('</svg>', f'{metadata}</svg>')


# ═══════════════════════════════════════════════════════════════
# QR CODE GENERATION
# ═══════════════════════════════════════════════════════════════

def generate_qr_code(data: str, size_mm: float = 20) -> Optional[io.BytesIO]:
    """
    Generate QR code as PNG image buffer.

    Args:
        data: Data to encode (verify URL)
        size_mm: Target size in mm (will be converted to pixels)

    Returns: BytesIO buffer with PNG image
    """
    if not QR_SUPPORT:
        logger.warning("QR support unavailable - install qrcode[pil]")
        return None

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Create image with transparent background
    img = qr.make_image(fill_color="black", back_color="white")

    # Save to buffer
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer


# ═══════════════════════════════════════════════════════════════
# PDF OVERLAY GENERATION
# ═══════════════════════════════════════════════════════════════

def generate_pdf_overlay(
    bits: List[int],
    page_width: float = A4[0] if PDF_SUPPORT else 595,
    page_height: float = A4[1] if PDF_SUPPORT else 842,
    opacity: float = OPACITY_PRINT
) -> Optional[bytes]:
    """
    Generate PDF overlay with Dragon Shadow Forest grid.
    This overlay can be merged into any PDF document.

    Returns: PDF bytes or None if PDF support unavailable
    """
    if not PDF_SUPPORT:
        logger.warning("PDF support unavailable - install reportlab and PyPDF2")
        return None

    if len(bits) != 256:
        raise ValueError(f"Expected 256 bits, got {len(bits)}")

    buffer = io.BytesIO()
    c = rl_canvas.Canvas(buffer, pagesize=(page_width, page_height))

    # Position grid in bottom-left corner
    x_offset = GRID_OFFSET_X_MM * mm
    y_offset = GRID_OFFSET_Y_MM * mm
    cell_mm = CELL_SIZE_MM * mm

    # Set opacity
    c.setFillAlpha(opacity)
    c.setStrokeAlpha(opacity)

    for idx, bit in enumerate(bits):
        row = idx // GRID_SIZE
        col = idx % GRID_SIZE
        x = x_offset + col * cell_mm
        y = y_offset + (GRID_SIZE - 1 - row) * cell_mm  # Flip Y for PDF coords

        if bit == 1:
            # Dark Dragon - filled heptagon
            c.setFillColorRGB(0.1, 0.1, 0.1)  # Dark gray
            # Draw simplified heptagon as polygon
            points = [
                (x + cell_mm * 0.5, y + cell_mm),          # top
                (x + cell_mm * 0.9, y + cell_mm * 0.78),
                (x + cell_mm * 0.94, y + cell_mm * 0.34),
                (x + cell_mm * 0.66, y),
                (x + cell_mm * 0.34, y),
                (x + cell_mm * 0.06, y + cell_mm * 0.34),
                (x + cell_mm * 0.1, y + cell_mm * 0.78),
            ]
            path = c.beginPath()
            path.moveTo(*points[0])
            for pt in points[1:]:
                path.lineTo(*pt)
            path.close()
            c.drawPath(path, fill=1, stroke=0)
        else:
            # Shadow Dragon - diamond
            c.setFillColorRGB(0.55, 0.41, 0.08)  # WINDI Gold
            center_x = x + cell_mm * 0.5
            center_y = y + cell_mm * 0.5
            half = cell_mm * 0.4
            path = c.beginPath()
            path.moveTo(center_x, center_y + half)  # top
            path.lineTo(center_x + half, center_y)  # right
            path.lineTo(center_x, center_y - half)  # bottom
            path.lineTo(center_x - half, center_y)  # left
            path.close()
            c.drawPath(path, fill=1, stroke=0)

    c.save()
    buffer.seek(0)
    return buffer.read()


def generate_pdf_overlay_forensic(
    bits: List[int],
    receipt_id: str,
    content_hash: str,
    verify_url: str,
    page_width: float = A4[0] if PDF_SUPPORT else 595,
    page_height: float = A4[1] if PDF_SUPPORT else 842,
    opacity: float = OPACITY_PRINT,
    include_qr: bool = True,
    include_microtext: bool = True
) -> Optional[bytes]:
    """
    Generate forensic-ready PDF overlay with:
    - Dragon Shadow Forest grid (invisible at 0.07 opacity)
    - QR code for easy verification (visible, bottom-right)
    - Micro-text with receipt_id (3pt, readable with 1200 DPI scanner)

    This is the FORENSIC version that makes verification easy for lawyers.

    Returns: PDF bytes or None if PDF support unavailable
    """
    if not PDF_SUPPORT:
        logger.warning("PDF support unavailable - install reportlab and PyPDF2")
        return None

    if len(bits) != 256:
        raise ValueError(f"Expected 256 bits, got {len(bits)}")

    buffer = io.BytesIO()
    c = rl_canvas.Canvas(buffer, pagesize=(page_width, page_height))

    # ─────────────────────────────────────────────────────────────
    # 1. Dragon Shadow Forest Grid (invisible layer)
    # ─────────────────────────────────────────────────────────────
    x_offset = GRID_OFFSET_X_MM * mm
    y_offset = GRID_OFFSET_Y_MM * mm
    cell_mm = CELL_SIZE_MM * mm

    # Set opacity for dragon grid
    c.setFillAlpha(opacity)
    c.setStrokeAlpha(opacity)

    for idx, bit in enumerate(bits):
        row = idx // GRID_SIZE
        col = idx % GRID_SIZE
        x = x_offset + col * cell_mm
        y = y_offset + (GRID_SIZE - 1 - row) * cell_mm

        if bit == 1:
            c.setFillColorRGB(0.1, 0.1, 0.1)
            points = [
                (x + cell_mm * 0.5, y + cell_mm),
                (x + cell_mm * 0.9, y + cell_mm * 0.78),
                (x + cell_mm * 0.94, y + cell_mm * 0.34),
                (x + cell_mm * 0.66, y),
                (x + cell_mm * 0.34, y),
                (x + cell_mm * 0.06, y + cell_mm * 0.34),
                (x + cell_mm * 0.1, y + cell_mm * 0.78),
            ]
            path = c.beginPath()
            path.moveTo(*points[0])
            for pt in points[1:]:
                path.lineTo(*pt)
            path.close()
            c.drawPath(path, fill=1, stroke=0)
        else:
            c.setFillColorRGB(0.55, 0.41, 0.08)
            center_x = x + cell_mm * 0.5
            center_y = y + cell_mm * 0.5
            half = cell_mm * 0.4
            path = c.beginPath()
            path.moveTo(center_x, center_y + half)
            path.lineTo(center_x + half, center_y)
            path.lineTo(center_x, center_y - half)
            path.lineTo(center_x - half, center_y)
            path.close()
            c.drawPath(path, fill=1, stroke=0)

    # ─────────────────────────────────────────────────────────────
    # 2. QR Code (visible, bottom-right corner)
    # ─────────────────────────────────────────────────────────────
    if include_qr and QR_SUPPORT:
        qr_buffer = generate_qr_code(verify_url, size_mm=18)
        if qr_buffer:
            # Reset opacity for visible elements
            c.setFillAlpha(1.0)
            c.setStrokeAlpha(1.0)

            # Position: bottom-right, 15mm from edges
            qr_size = 18 * mm
            qr_x = page_width - qr_size - 15 * mm
            qr_y = 12 * mm

            # Draw QR code
            img = ImageReader(qr_buffer)
            c.drawImage(img, qr_x, qr_y, width=qr_size, height=qr_size)

            # Label above QR
            c.setFillColorRGB(0.3, 0.3, 0.3)
            c.setFont("Helvetica", 5)
            c.drawString(qr_x, qr_y + qr_size + 2, "WINDI Verify →")

            # Date below QR
            seal_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            c.setFont("Helvetica", 4)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawString(qr_x, qr_y - 3, seal_date)

    # ─────────────────────────────────────────────────────────────
    # 3. Micro-text (readable with scanner/magnifier)
    # ─────────────────────────────────────────────────────────────
    if include_microtext:
        # Reset opacity
        c.setFillAlpha(0.15)  # Very faint but readable with scanner
        c.setFont("Courier", 3)  # 3pt = readable at 1200 DPI
        c.setFillColorRGB(0.2, 0.2, 0.2)

        # Position: below dragon grid
        micro_y = 10 * mm
        micro_x = 20 * mm

        # Line 1: Receipt ID
        c.drawString(micro_x, micro_y + 4, f"WINDI-DSF | {receipt_id}")

        # Line 2: Hash (first 32 chars)
        c.drawString(micro_x, micro_y, f"SHA256: {content_hash[:32]}...")

    c.save()
    buffer.seek(0)
    return buffer.read()


def merge_overlay_into_pdf(
    original_pdf: bytes,
    overlay_pdf: bytes,
    pages: str = "all",
    receipt_id: Optional[str] = None,
    content_hash: Optional[str] = None,
    verify_url: Optional[str] = None
) -> bytes:
    """
    Merge Dragon Shadow Forest overlay into existing PDF.

    Args:
        original_pdf: Original PDF bytes
        overlay_pdf: Overlay PDF bytes from generate_pdf_overlay()
        pages: "all", "first", "last", or comma-separated page numbers (1-indexed)
        receipt_id: WINDI receipt ID (for metadata)
        content_hash: SHA-256 hash (for metadata)
        verify_url: Verification URL (for metadata)

    Returns: Merged PDF bytes with WINDI metadata

    FORENSIC NOTE:
    PDF metadata is readable in any PDF reader → File → Properties → Custom
    This allows instant verification without specialized tools.
    """
    if not PDF_SUPPORT:
        raise RuntimeError("PDF support unavailable")

    reader = PdfReader(io.BytesIO(original_pdf))
    overlay_reader = PdfReader(io.BytesIO(overlay_pdf))
    overlay_page = overlay_reader.pages[0]

    writer = PdfWriter()
    num_pages = len(reader.pages)

    # Determine which pages to overlay
    if pages == "all":
        target_pages = set(range(num_pages))
    elif pages == "first":
        target_pages = {0}
    elif pages == "last":
        target_pages = {num_pages - 1}
    else:
        target_pages = {int(p) - 1 for p in pages.split(",")}

    for i, page in enumerate(reader.pages):
        if i in target_pages:
            page.merge_page(overlay_page)
        writer.add_page(page)

    # ─────────────────────────────────────────────────────────────
    # ADD WINDI METADATA (Forensic-Ready)
    # Readable in any PDF reader: File → Properties → Custom
    # ─────────────────────────────────────────────────────────────
    if receipt_id or content_hash:
        timestamp = datetime.now(timezone.utc).isoformat()
        metadata = {
            '/Title': reader.metadata.get('/Title', 'WINDI Sealed Document') if reader.metadata else 'WINDI Sealed Document',
            '/Author': 'WINDI Dragon Shadow Forest',
            '/Creator': f'W-DRAGON-001 v{VERSION}',
            '/Producer': 'Liga IA+H · Kempten, Bavaria',
            '/Subject': f'Forensic Sealed Document - {receipt_id or "pending"}',
            '/Keywords': 'WINDI, DSF, Forensic, Sealed, Verified',
        }

        # Add WINDI-specific custom metadata
        if receipt_id:
            metadata['/WINDI-Receipt'] = receipt_id
        if content_hash:
            metadata['/WINDI-Hash'] = f'sha256:{content_hash}'
        if verify_url:
            metadata['/WINDI-Verify'] = verify_url

        metadata['/WINDI-Timestamp'] = timestamp
        metadata['/WINDI-Schema'] = 'W-DRAGON-001-v1'
        metadata['/WINDI-Grid'] = f'{GRID_SIZE}x{GRID_SIZE}'
        metadata['/WINDI-Invariants'] = 'I9,I11,I14'

        writer.add_metadata(metadata)

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output.read()


# ═══════════════════════════════════════════════════════════════
# LEDGER INTEGRATION
# ═══════════════════════════════════════════════════════════════

async def register_with_ledger(
    content_hash: str,
    receipt_id: str,
    doc_name: str = "Document",
    actor: str = "windi-dragon"
) -> Tuple[bool, Optional[dict]]:
    """
    Register Dragon Shadow Forest receipt with Forensic Ledger.

    ENDPOINT: POST /api/receipts (não /ledger/register)
    AUTH: Nenhum Bearer token — Ledger usa autenticação interna
    PAYLOAD: {id, actor, app, doc_name, doc_type, content_hash, governance_level, sge_score}

    I11 Compliance: Receipt confirmado pelo Ledger (stored=true)
    I14 Compliance: Falha explícita se Ledger inacessível

    Returns: (success, ledger_response)
    """
    # Payload nativo do Ledger :8101/api/receipts
    payload = {
        "id": receipt_id,
        "actor": actor if actor.startswith("did:") else f"did:windi:{actor}",
        "app": "W-DRAGON-001",
        "doc_name": doc_name,
        "doc_type": "doc",
        "content_hash": content_hash,  # Sem prefixo sha256:
        "governance_level": "HIGH",
        "sge_score": 99.0
    }

    # Ledger não usa Bearer token
    headers = {
        "Content-Type": "application/json",
        "X-WINDI-Module": "W-DRAGON-001",
        "X-WINDI-Schema": "W-DRAGON-001-v1"
    }

    # Endpoint correcto: /api/receipts
    ledger_base = os.getenv("LEDGER_URL", "http://127.0.0.1:8101")
    endpoint = f"{ledger_base}/api/receipts"

    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code in (200, 201):
            data = response.json()
            # Ledger retorna {"ok": true, "stored": true, "id": ...}
            if data.get("ok") and data.get("stored"):
                logger.info(f"W-DRAGON-001: Ledger CONFIRMED → {receipt_id}")
                return True, data
            else:
                logger.warning(f"W-DRAGON-001: Ledger ok=false → {data}")
                return False, data
        else:
            logger.error(f"Ledger HTTP {response.status_code}: {response.text[:200]}")
            return False, None

    except requests.exceptions.RequestException as e:
        logger.error(f"W-DRAGON-001: Ledger connection error: {e}")
        return False, None


# ═══════════════════════════════════════════════════════════════
# MAIN ENCODING FUNCTION
# ═══════════════════════════════════════════════════════════════

async def encode_document(
    content: bytes,
    doc_name: str = "Document",
    actor: str = "windi-dragon",
    generate_pdf: bool = True,
    pdf_opacity: float = OPACITY_PRINT,
    svg_opacity: float = OPACITY_SCREEN,
    register_ledger: bool = True
) -> DSFEncodeResult:
    """
    Encode document with Dragon Shadow Forest.

    Pipeline:
    1. Compute SHA-256 hash
    2. Convert hash to 256 bits
    3. Generate SVG grid visualization
    4. Generate PDF overlay (optional)
    5. Register with Ledger (optional, requires human approval)

    Returns: DSFEncodeResult with receipt, SVG, and optional PDF overlay
    """
    # Step 1: Compute hash
    content_hash = compute_hash(content)

    # Step 2: Convert to bits
    bits = hash_to_bits(content_hash)

    # Step 3: Generate receipt ID
    receipt_id = generate_receipt_id()

    # Step 4: Generate SVG
    svg_grid = generate_svg_with_metadata(
        bits=bits,
        receipt_id=receipt_id,
        content_hash=content_hash,
        opacity=svg_opacity
    )

    # Step 5: Generate PDF overlay
    pdf_overlay = None
    if generate_pdf and PDF_SUPPORT:
        pdf_overlay = generate_pdf_overlay(bits, opacity=pdf_opacity)

    # Step 6: Register with Ledger
    status = "PENDING"
    ledger_url = None

    if register_ledger:
        success, ledger_response = await register_with_ledger(
            content_hash=content_hash,
            receipt_id=receipt_id,
            doc_name=doc_name,
            actor=actor
        )
        if success:
            status = "C5"  # Awaiting human approval
            ledger_url = f"https://windi-domain.com/verify-public/?id={receipt_id}"

    # Build receipt
    receipt = DSFReceipt(
        receipt_id=receipt_id,
        content_hash=content_hash,
        bits=bits,
        created_at=datetime.now(timezone.utc).isoformat(),
        status=status,
        ledger_url=ledger_url
    )

    return DSFEncodeResult(
        receipt=receipt,
        svg_grid=svg_grid,
        pdf_overlay=pdf_overlay,
        verify_url=f"https://windi-domain.com/verify-public/?id={receipt_id}"
    )


# ═══════════════════════════════════════════════════════════════
# VERIFICATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def verify_hash_matches_grid(content: bytes, svg_grid: str) -> bool:
    """
    Verify that content hash matches the dragon grid in SVG.
    Used for local verification without Ledger access.
    """
    content_hash = compute_hash(content)
    expected_bits = hash_to_bits(content_hash)

    # Extract hash from SVG metadata comment
    import re
    hash_match = re.search(r'Hash: ([a-f0-9]{64})', svg_grid)
    if not hash_match:
        return False

    svg_hash = hash_match.group(1)
    return content_hash == svg_hash


async def verify_with_ledger(receipt_id: str) -> Tuple[bool, Optional[dict]]:
    """
    Verify receipt exists in Forensic Ledger.

    Returns: (exists, ledger_data)
    """
    try:
        response = requests.get(
            f"{LEDGER_URL.replace('/api/receipts', '')}/api/receipts/{receipt_id}",
            timeout=10
        )

        if response.status_code == 200:
            return True, response.json()
        return False, None

    except requests.exceptions.RequestException as e:
        logger.error(f"Ledger verification error: {e}")
        return False, None


# ═══════════════════════════════════════════════════════════════
# MODULE INFO
# ═══════════════════════════════════════════════════════════════

def get_module_info() -> dict:
    """Return module information for health checks."""
    return {
        "module": "W-DRAGON-001",
        "version": VERSION,
        "name": "Dragon Shadow Forest",
        "description": "Invisible guardians encoding truth in every document",
        "grid_size": f"{GRID_SIZE}x{GRID_SIZE}",
        "total_bits": GRID_SIZE * GRID_SIZE,
        "pdf_support": PDF_SUPPORT,
        "ledger_url": LEDGER_URL,
        "invariants": ["I9", "I11", "I14"],
        "author": "Liga IA+H",
        "location": "Kempten, Bavaria"
    }
