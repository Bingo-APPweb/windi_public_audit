#!/usr/bin/env python3
"""
W-JMPG-001 — JPEG Manifest Proof Graphic Renderer
§134 · Liga IA+H · Kempten, Bavaria · 05 Abril 2026

"Se o receipt é a prova estrutural, o .jmpg é a sua forma portátil no mundo."
"""

import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from PIL import Image, ImageDraw, ImageFont
import qrcode

# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

OUTPUT_DIR = Path("/opt/windi/media/comm/jmpg")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# KLAR theme colors (light/parchment)
COLORS = {
    "bg": "#F5F0E0",
    "text_dark": "#1A1A1A",
    "text_muted": "#6B6B6B",
    "gold": "#8B6914",
    "gold_dark": "#6B5A45",
    "success": "#2D5A2D",
    "border": "#D5D0C5",
}

# Status badge colors (SGV integration ready)
STATUS_COLORS = {
    "VERIFIED": "#2D5A2D",    # green
    "SEALED": "#2D5A2D",      # green
    "TRACEABLE": "#8B6914",   # gold/yellow
    "UNVERIFIED": "#6B6B6B",  # grey
    "SUSPICIOUS": "#9C4040",  # red
}

# Profile dimensions
PROFILES = {
    "telegram_square": (1080, 1080),
    "telegram_landscape": (1600, 900),
    "story_vertical": (1080, 1920),
}

# Font paths (system fonts)
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]


def get_font(style: str = "regular", size: int = 24) -> ImageFont.FreeTypeFont:
    """Get font with fallback to default."""
    try:
        if style == "bold":
            return ImageFont.truetype(FONT_PATHS[0], size)
        elif style == "mono":
            return ImageFont.truetype(FONT_PATHS[2], size)
        else:
            return ImageFont.truetype(FONT_PATHS[1], size)
    except (IOError, OSError):
        return ImageFont.load_default()


# ═══════════════════════════════════════════════════════════════════════════════
# QR Code Generator
# ═══════════════════════════════════════════════════════════════════════════════

def generate_qr(data: str, size: int = 260) -> Image.Image:
    """Generate QR code image."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="#1A1A1A", back_color="#F5F0E0")
    return qr_img.resize((size, size), Image.Resampling.LANCZOS)


# ═══════════════════════════════════════════════════════════════════════════════
# Card Data Builder
# ═══════════════════════════════════════════════════════════════════════════════

def build_card_data(
    receipt_id: str,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    source_app: Optional[str] = None,
    content_hash: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Build card data from receipt information."""

    # Extract source app from receipt_id if not provided
    # Format: WINDI-VDCUT-20260405133947-50A4F74A
    if not source_app and "-" in receipt_id:
        parts = receipt_id.split("-")
        if len(parts) >= 2:
            source_app = parts[1]

    # Parse timestamp from receipt_id if not provided
    if not timestamp and "-" in receipt_id:
        parts = receipt_id.split("-")
        if len(parts) >= 3:
            ts = parts[2]
            if len(ts) >= 8:
                try:
                    dt = datetime.strptime(ts[:8], "%Y%m%d")
                    timestamp = dt.strftime("%d %b %Y")
                except ValueError:
                    pass

    if not timestamp:
        timestamp = datetime.now().strftime("%d %b %Y")

    # Generate hash short if we have a full hash
    hash_short = None
    if content_hash:
        if len(content_hash) > 16:
            hash_short = f"SHA-256: {content_hash[:4].upper()}...{content_hash[-4:].upper()}"
        else:
            hash_short = f"SHA-256: {content_hash.upper()}"
    else:
        # Generate from receipt_id
        h = hashlib.sha256(receipt_id.encode()).hexdigest()
        hash_short = f"SHA-256: {h[:4].upper()}...{h[-4:].upper()}"

    verify_url = f"https://windi-domain.com/verify-public/?id={receipt_id}"

    return {
        "title": title or "Sealed content with public proof",
        "subtitle": subtitle or "WINDI Proof Card",
        "date": timestamp,
        "status": "VERIFIED",
        "receipt_id": receipt_id,
        "hash_short": hash_short,
        "verify_url": verify_url,
        "protocol": ".jmpg v1",
        "source_app": source_app or "WINDI",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Renderer — telegram_square (1080x1080)
# ═══════════════════════════════════════════════════════════════════════════════

def render_telegram_square(card: Dict[str, Any], output_path: Path) -> Path:
    """Render 1080x1080 telegram square proof card."""

    width, height = 1080, 1080
    img = Image.new("RGB", (width, height), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    # Fonts
    font_header = get_font("bold", 42)
    font_subheader = get_font("regular", 28)
    font_title = get_font("bold", 38)
    font_body = get_font("regular", 32)
    font_mono = get_font("mono", 26)
    font_small = get_font("regular", 24)

    # Padding
    pad = 80

    # ─── Header ───────────────────────────────────────────────────────────────
    draw.text((pad, 70), "WINDI Proof Card", font=font_header, fill=COLORS["gold"])
    draw.text((pad, 130), f"{card['date']} · {card['source_app']}", font=font_subheader, fill=COLORS["text_muted"])

    # ─── Divider ──────────────────────────────────────────────────────────────
    draw.line([(pad, 190), (width - pad, 190)], fill=COLORS["border"], width=2)

    # ─── Title ────────────────────────────────────────────────────────────────
    # Word wrap title if too long
    title = card["title"]
    max_width = width - (pad * 2)

    # Simple word wrap
    words = title.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font_title)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    y = 240
    for line in lines[:3]:  # Max 3 lines
        draw.text((pad, y), line, font=font_title, fill=COLORS["text_dark"])
        y += 50

    # ─── Status Badge ─────────────────────────────────────────────────────────
    status_y = y + 40

    # Draw status badge background with dynamic color
    badge_text = f"  {card['status']}  "
    bbox = draw.textbbox((0, 0), badge_text, font=font_body)
    badge_width = bbox[2] - bbox[0] + 40
    badge_height = bbox[3] - bbox[1] + 20

    # Get status color (SGV ready)
    status_color = STATUS_COLORS.get(card["status"], COLORS["success"])

    draw.rounded_rectangle(
        [(pad, status_y), (pad + badge_width, status_y + badge_height)],
        radius=8,
        fill=status_color,
    )
    draw.text((pad + 20, status_y + 8), card["status"], font=font_body, fill="#FFFFFF")

    # ─── Receipt Info ─────────────────────────────────────────────────────────
    info_y = status_y + badge_height + 50

    draw.text((pad, info_y), "Receipt:", font=font_small, fill=COLORS["text_muted"])

    # Break receipt ID into two lines for readability
    receipt_id = card["receipt_id"]
    if len(receipt_id) > 28:
        # Split at timestamp boundary (WINDI-VDCUT-20260405 | 135729-94F5566F)
        parts = receipt_id.rsplit("-", 2)
        if len(parts) >= 3:
            line1 = "-".join(parts[:-2]) + "-" + parts[-2][:8]
            line2 = parts[-2][8:] + "-" + parts[-1]
            draw.text((pad, info_y + 35), line1, font=font_mono, fill=COLORS["text_dark"])
            draw.text((pad, info_y + 70), line2, font=font_mono, fill=COLORS["text_dark"])
            info_y += 35  # Adjust for extra line
        else:
            draw.text((pad, info_y + 35), receipt_id, font=font_mono, fill=COLORS["text_dark"])
    else:
        draw.text((pad, info_y + 35), receipt_id, font=font_mono, fill=COLORS["text_dark"])

    draw.text((pad, info_y + 100), card["hash_short"], font=font_mono, fill=COLORS["gold_dark"])

    # ─── QR Code ──────────────────────────────────────────────────────────────
    qr_size = 280
    qr_x = width - pad - qr_size
    qr_y = height - pad - qr_size - 80

    qr_img = generate_qr(card["verify_url"], qr_size)
    img.paste(qr_img, (qr_x, qr_y))

    # QR label
    draw.text((qr_x + 20, qr_y + qr_size + 10), "Verify authenticity", font=font_small, fill=COLORS["text_muted"])

    # ─── Footer ───────────────────────────────────────────────────────────────
    footer_y = height - pad - 20

    draw.text((pad, footer_y - 30), f"Protocol: {card['protocol']}", font=font_small, fill=COLORS["text_muted"])

    # Verify URL (shortened for display)
    short_url = card["verify_url"].replace("https://", "")
    if len(short_url) > 50:
        short_url = short_url[:47] + "..."
    draw.text((pad, footer_y), short_url, font=font_small, fill=COLORS["gold_dark"])

    # ─── WINDI Mark ───────────────────────────────────────────────────────────
    mark_text = "WINDI"
    bbox = draw.textbbox((0, 0), mark_text, font=font_header)
    mark_x = width - pad - (bbox[2] - bbox[0])
    draw.text((mark_x, footer_y - 30), mark_text, font=font_header, fill=COLORS["gold"])

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "JPEG", quality=92)

    return output_path


# ═══════════════════════════════════════════════════════════════════════════════
# Renderer — telegram_landscape (1600x900)
# ═══════════════════════════════════════════════════════════════════════════════

def render_telegram_landscape(card: Dict[str, Any], output_path: Path) -> Path:
    """Render 1600x900 telegram landscape proof card."""

    width, height = 1600, 900
    img = Image.new("RGB", (width, height), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    # Fonts
    font_header = get_font("bold", 48)
    font_subheader = get_font("regular", 32)
    font_title = get_font("bold", 44)
    font_body = get_font("regular", 36)
    font_mono = get_font("mono", 28)
    font_small = get_font("regular", 26)

    pad = 80

    # Left column (text)
    left_width = width - 450

    # Header
    draw.text((pad, 60), "WINDI Proof Card", font=font_header, fill=COLORS["gold"])
    draw.text((pad, 120), f"{card['date']} · {card['source_app']}", font=font_subheader, fill=COLORS["text_muted"])

    # Divider
    draw.line([(pad, 180), (left_width - 40, 180)], fill=COLORS["border"], width=2)

    # Title
    draw.text((pad, 220), card["title"][:60], font=font_title, fill=COLORS["text_dark"])

    # Status
    status_y = 300
    draw.rounded_rectangle(
        [(pad, status_y), (pad + 200, status_y + 50)],
        radius=8,
        fill=COLORS["success"],
    )
    draw.text((pad + 20, status_y + 8), card["status"], font=font_body, fill="#FFFFFF")

    # Receipt info
    draw.text((pad, 400), "Receipt:", font=font_small, fill=COLORS["text_muted"])
    draw.text((pad, 440), card["receipt_id"], font=font_mono, fill=COLORS["text_dark"])

    draw.text((pad, 510), "Hash:", font=font_small, fill=COLORS["text_muted"])
    draw.text((pad, 550), card["hash_short"], font=font_mono, fill=COLORS["gold_dark"])

    # Footer
    draw.text((pad, height - 100), f"Protocol: {card['protocol']}", font=font_small, fill=COLORS["text_muted"])
    draw.text((pad, height - 60), card["verify_url"].replace("https://", ""), font=font_small, fill=COLORS["gold_dark"])

    # Right column (QR)
    qr_size = 320
    qr_x = width - pad - qr_size
    qr_y = (height - qr_size) // 2 - 30

    qr_img = generate_qr(card["verify_url"], qr_size)
    img.paste(qr_img, (qr_x, qr_y))

    draw.text((qr_x + 60, qr_y + qr_size + 20), "Scan to verify", font=font_small, fill=COLORS["text_muted"])

    # WINDI mark
    draw.text((qr_x + 80, height - 80), "WINDI", font=font_header, fill=COLORS["gold"])

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "JPEG", quality=92)

    return output_path


# ═══════════════════════════════════════════════════════════════════════════════
# Main Render Function
# ═══════════════════════════════════════════════════════════════════════════════

def render_jmpg(
    receipt_id: str,
    profile: str = "telegram_square",
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    source_app: Optional[str] = None,
    content_hash: Optional[str] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Render a JMPG proof card.

    Args:
        receipt_id: WINDI receipt ID
        profile: Render profile (telegram_square, telegram_landscape, story_vertical)
        title: Optional title text
        subtitle: Optional subtitle
        source_app: Source application name
        content_hash: Content hash for display
        output_dir: Output directory (default: /opt/windi/media/comm/jmpg)

    Returns:
        Dict with ok, receipt_id, image_path, verify_url
    """

    if profile not in PROFILES:
        return {
            "ok": False,
            "error": f"Unknown profile: {profile}. Available: {list(PROFILES.keys())}",
        }

    # Build card data
    card = build_card_data(
        receipt_id=receipt_id,
        title=title,
        subtitle=subtitle,
        source_app=source_app,
        content_hash=content_hash,
    )

    # Determine output path
    out_dir = output_dir or OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{receipt_id}_{profile}.jpg"
    output_path = out_dir / filename

    # Render based on profile
    try:
        if profile == "telegram_square":
            render_telegram_square(card, output_path)
        elif profile == "telegram_landscape":
            render_telegram_landscape(card, output_path)
        elif profile == "story_vertical":
            # TODO: Implement story_vertical
            render_telegram_square(card, output_path)  # Fallback for now

        return {
            "ok": True,
            "receipt_id": receipt_id,
            "profile": profile,
            "image_path": str(output_path),
            "verify_url": card["verify_url"],
            "card_data": card,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CLI Test
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python jmpg_renderer.py <receipt_id> [profile] [title]")
        print("Profiles: telegram_square (default), telegram_landscape, story_vertical")
        sys.exit(1)

    receipt_id = sys.argv[1]
    profile = sys.argv[2] if len(sys.argv) > 2 else "telegram_square"
    title = sys.argv[3] if len(sys.argv) > 3 else None

    result = render_jmpg(receipt_id, profile=profile, title=title)

    if result["ok"]:
        print(f"✓ Rendered: {result['image_path']}")
        print(f"  Verify: {result['verify_url']}")
    else:
        print(f"✗ Error: {result['error']}")
        sys.exit(1)
