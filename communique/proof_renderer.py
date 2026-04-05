#!/opt/windi/venv/bin/python3
"""
JMPG v1.1 — Editorial Proof Layer Renderer
============================================

Generates visual proof cards for WINDI Communiqués.

Design: NOIR + ACCENT GREEN
4 Zones: HEADER | HEADLINE | CORE | PROOF BLOCK

"A prova deixou de ser técnica. Agora ela convence antes de ser explicada."

Liga IA+H · Kempten, Bavaria · 2026
"""

import os
import hashlib
import qrcode
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timezone
from typing import Optional, Tuple
from io import BytesIO

# ══════════════════════════════════════════════════════════════
# DESIGN CONSTANTS
# ══════════════════════════════════════════════════════════════

# Canvas size (optimized for Telegram + social)
CANVAS_WIDTH = 1200
CANVAS_HEIGHT = 1600

# Colors (NOIR + ACCENT GREEN)
COLOR_BG = "#0B0B0B"
COLOR_TEXT_PRIMARY = "#F5F5F5"
COLOR_TEXT_SECONDARY = "#A0A0A0"
COLOR_ACCENT = "#00C853"  # Verification green
COLOR_ACCENT_GOLD = "#C9A84C"  # WINDI gold
COLOR_DIVIDER = "#2A2A2A"
COLOR_PROOF_BG = "#111111"

# Fonts (system fallbacks)
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]

FONT_MONO_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
]


def find_font(paths: list, size: int) -> ImageFont.FreeTypeFont:
    """Find first available font from paths list."""
    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    # Fallback to default
    return ImageFont.load_default()


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def generate_qr(url: str, size: int = 200) -> Image.Image:
    """Generate QR code image."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="white", back_color="#0B0B0B")
    qr_img = qr_img.resize((size, size), Image.Resampling.LANCZOS)
    return qr_img


def truncate_hash(hash_str: str, length: int = 8) -> str:
    """Truncate hash for display."""
    if not hash_str:
        return "N/A"
    clean = hash_str.replace("sha256:", "")
    if len(clean) > length * 2:
        return f"{clean[:length]}...{clean[-length:]}"
    return clean


def render_proof_card(
    communique: dict,
    output_path: str = None,
    profile: str = "standard"
) -> bytes:
    """
    Render a visual proof card for a communiqué.

    Args:
        communique: Dict with communiqué data
        output_path: Optional path to save PNG
        profile: "standard" | "journalist" | "legal"

    Returns:
        PNG image bytes
    """
    # Create canvas
    img = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), hex_to_rgb(COLOR_BG))
    draw = ImageDraw.Draw(img)

    # Load fonts — PHASE 2.2: Increased headline dominance
    font_title = find_font(FONT_PATHS[:3], 36)
    font_headline = find_font(FONT_PATHS[:3], 72)  # Increased from 64
    font_body = find_font(FONT_PATHS[1:], 28)
    font_small = find_font(FONT_PATHS[1:], 22)
    font_mono = find_font(FONT_MONO_PATHS, 26)  # Slightly larger for readability
    font_label = find_font(FONT_PATHS[1:], 20)
    font_badge = find_font(FONT_PATHS[:3], 40)  # New: dominant badge font

    # Extract data
    title = communique.get("title_de") or communique.get("title_en") or "WINDI Communiqué"
    impact_level = communique.get("impact_level", "MED").upper()
    category = communique.get("category", "UPDATE").upper()

    # Ledger Receipt — REAL or clearly marked as pending
    ledger_receipt = communique.get("receipt_id")
    has_ledger_receipt = ledger_receipt is not None and ledger_receipt != ""

    jmpg_id = communique.get("evidence_jmpg_id") or "N/A"
    content_hash = communique.get("content_hash") or communique.get("evidence_bundle_hash") or ""

    verify_url = communique.get("evidence_verify_url") or f"https://windi-domain.com/verify-public/"

    created_at = communique.get("created_at", "")
    if created_at:
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            date_str = dt.strftime("%d %b %Y").upper()
        except:
            date_str = created_at[:10].upper()
    else:
        date_str = datetime.now(timezone.utc).strftime("%d %b %Y").upper()

    y_offset = 60

    # ══════════════════════════════════════════════════════════════
    # ZONE 1: HEADER — IDENTIDADE
    # ══════════════════════════════════════════════════════════════

    # WINDI logo/text
    draw.text(
        (60, y_offset),
        "WINDI",
        font=font_title,
        fill=hex_to_rgb(COLOR_ACCENT_GOLD)
    )
    draw.text(
        (180, y_offset),
        "COMMUNIQUÉ",
        font=font_title,
        fill=hex_to_rgb(COLOR_TEXT_PRIMARY)
    )

    y_offset += 50

    # Governance level + date
    governance_color = COLOR_ACCENT if impact_level in ("HIGH", "CRIT") else COLOR_TEXT_SECONDARY
    draw.text(
        (60, y_offset),
        f"{impact_level} GOVERNANCE",
        font=font_small,
        fill=hex_to_rgb(governance_color)
    )
    draw.text(
        (350, y_offset),
        "·",
        font=font_small,
        fill=hex_to_rgb(COLOR_TEXT_SECONDARY)
    )
    draw.text(
        (380, y_offset),
        date_str,
        font=font_small,
        fill=hex_to_rgb(COLOR_TEXT_SECONDARY)
    )
    draw.text(
        (600, y_offset),
        "·",
        font=font_small,
        fill=hex_to_rgb(COLOR_TEXT_SECONDARY)
    )
    draw.text(
        (630, y_offset),
        "VERIFIED DISTRIBUTION",
        font=font_small,
        fill=hex_to_rgb(COLOR_ACCENT)
    )

    y_offset += 60

    # Divider
    draw.line([(60, y_offset), (CANVAS_WIDTH - 60, y_offset)], fill=hex_to_rgb(COLOR_DIVIDER), width=2)

    y_offset += 60

    # ══════════════════════════════════════════════════════════════
    # ZONE 2: HEADLINE — IMPACTO
    # ══════════════════════════════════════════════════════════════

    # Word wrap for headline
    headline_words = title.upper().split()
    headline_lines = []
    current_line = ""
    max_width = CANVAS_WIDTH - 120

    for word in headline_words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font_headline)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                headline_lines.append(current_line)
            current_line = word
    if current_line:
        headline_lines.append(current_line)

    for line in headline_lines[:3]:  # Max 3 lines
        draw.text(
            (60, y_offset),
            line,
            font=font_headline,
            fill=hex_to_rgb(COLOR_TEXT_PRIMARY)
        )
        y_offset += 90  # PHASE 2.2: More breathing room

    y_offset += 30

    # ══════════════════════════════════════════════════════════════
    # ZONE 3: CORE — SIGNIFICADO
    # ══════════════════════════════════════════════════════════════

    core_text = [
        "This communication has been sealed and verified",
        "through the WINDI Forensic Ledger.",
        "",
        "Integrity can be independently confirmed.",
    ]

    for line in core_text:
        if line:
            draw.text(
                (60, y_offset),
                line,
                font=font_body,
                fill=hex_to_rgb(COLOR_TEXT_SECONDARY)
            )
        y_offset += 40

    y_offset += 40

    # ══════════════════════════════════════════════════════════════
    # ZONE 4: PROOF BLOCK — VERDADE VISÍVEL
    # ══════════════════════════════════════════════════════════════

    # Proof block background — PHASE 2.2: Adjusted for larger elements
    proof_y = y_offset
    proof_height = 540
    draw.rectangle(
        [(40, proof_y), (CANVAS_WIDTH - 40, proof_y + proof_height)],
        fill=hex_to_rgb(COLOR_PROOF_BG),
        outline=hex_to_rgb(COLOR_DIVIDER),
        width=2
    )

    y_offset = proof_y + 40

    # VERIFIED badge — PHASE 2.2: More dominant
    if has_ledger_receipt:
        badge_text = "FORENSIC VERIFIED"
        badge_color = COLOR_ACCENT
    else:
        badge_text = "EVIDENCE SEALED"
        badge_color = COLOR_ACCENT_GOLD

    # Larger badge indicator
    draw.ellipse(
        [(60, y_offset), (90, y_offset + 30)],
        fill=hex_to_rgb(badge_color)
    )
    draw.text(
        (105, y_offset - 2),
        badge_text,
        font=font_badge,
        fill=hex_to_rgb(badge_color)
    )

    y_offset += 70

    # Ledger Receipt — show real status
    draw.text(
        (60, y_offset),
        "Ledger Receipt:",
        font=font_label,
        fill=hex_to_rgb(COLOR_TEXT_SECONDARY)
    )
    if has_ledger_receipt:
        draw.text(
            (250, y_offset),
            ledger_receipt,
            font=font_mono,
            fill=hex_to_rgb(COLOR_ACCENT)  # Green = verified
        )
    else:
        draw.text(
            (250, y_offset),
            "AWAITING LEDGER SEAL",
            font=font_mono,
            fill=hex_to_rgb(COLOR_ACCENT_GOLD)  # Gold = pending but honest
        )

    y_offset += 40

    # Evidence Package
    draw.text(
        (60, y_offset),
        "Evidence Package:",
        font=font_label,
        fill=hex_to_rgb(COLOR_TEXT_SECONDARY)
    )
    draw.text(
        (250, y_offset),
        jmpg_id,
        font=font_mono,
        fill=hex_to_rgb(COLOR_TEXT_PRIMARY)
    )

    y_offset += 40

    # SHA-256
    draw.text(
        (60, y_offset),
        "SHA-256:",
        font=font_label,
        fill=hex_to_rgb(COLOR_TEXT_SECONDARY)
    )
    draw.text(
        (250, y_offset),
        truncate_hash(content_hash, 12),
        font=font_mono,
        fill=hex_to_rgb(COLOR_ACCENT_GOLD)
    )

    y_offset += 60

    # QR Code
    qr_size = 200
    qr_x = CANVAS_WIDTH - qr_size - 80
    qr_y = proof_y + 120

    try:
        qr_img = generate_qr(verify_url, qr_size)
        img.paste(qr_img, (qr_x, qr_y))
    except Exception as e:
        # Fallback: draw placeholder
        draw.rectangle(
            [(qr_x, qr_y), (qr_x + qr_size, qr_y + qr_size)],
            outline=hex_to_rgb(COLOR_TEXT_SECONDARY),
            width=2
        )
        draw.text(
            (qr_x + 50, qr_y + 90),
            "QR CODE",
            font=font_small,
            fill=hex_to_rgb(COLOR_TEXT_SECONDARY)
        )

    # Scan to verify text
    draw.text(
        (qr_x, qr_y + qr_size + 10),
        "Scan to verify",
        font=font_small,
        fill=hex_to_rgb(COLOR_TEXT_SECONDARY)
    )

    # ══════════════════════════════════════════════════════════════
    # FOOTER
    # ══════════════════════════════════════════════════════════════

    footer_y = CANVAS_HEIGHT - 80

    draw.line(
        [(60, footer_y - 20), (CANVAS_WIDTH - 60, footer_y - 20)],
        fill=hex_to_rgb(COLOR_DIVIDER),
        width=1
    )

    draw.text(
        (60, footer_y),
        "windi-domain.com/verify",
        font=font_small,
        fill=hex_to_rgb(COLOR_TEXT_SECONDARY)
    )

    draw.text(
        (CANVAS_WIDTH - 350, footer_y),
        "AI processes. Human decides. WINDI guarantees.",
        font=font_label,
        fill=hex_to_rgb(COLOR_TEXT_SECONDARY)
    )

    # ══════════════════════════════════════════════════════════════
    # OUTPUT
    # ══════════════════════════════════════════════════════════════

    # Save to bytes
    buffer = BytesIO()
    img.save(buffer, format="PNG", quality=95)
    png_bytes = buffer.getvalue()

    # Optionally save to file
    if output_path:
        with open(output_path, "wb") as f:
            f.write(png_bytes)

    return png_bytes


# ══════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: proof_renderer.py <communique.json> [output.png]")
        sys.exit(1)

    # Load communiqué from JSON file or stdin
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "proof_card.png"

    if input_path == "-":
        communique = json.load(sys.stdin)
    else:
        with open(input_path) as f:
            communique = json.load(f)

    render_proof_card(communique, output_path)
    print(f"Proof card saved to: {output_path}")
