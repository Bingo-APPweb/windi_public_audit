#!/usr/bin/env python3
"""
WINDI QR Engine — N4: Verification QR Code Generation
"AI processes. Human decides. WINDI guarantees."

Generates gold-branded QR codes for document verification.
QR links to verify URL with serial number and short hash.

Design:
- Foreground: WINDI Gold #8B6914
- Background: KLAR card white #FDFBF5
- Error correction: HIGH (30% damage tolerance)
- Border: 2 modules (compact)
"""

import io
from urllib.parse import urlencode

# ── Configuration ──
VERIFY_BASE_URL = "https://windi-domain.com/verify-public/"
WINDI_GOLD = "#8B6914"
KLAR_WHITE = "#FDFBF5"
DEFAULT_SIZE = 150
DEFAULT_BORDER = 2

# Try to import qrcode - graceful degradation if unavailable
try:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_H
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False
    ERROR_CORRECT_H = None

# Try to import PIL for image manipulation
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def generate_verify_url(serial: str, content_hash: str) -> str:
    """
    Generate verification URL with serial and short hash.

    Args:
        serial: WINDI serial number (e.g., WINDI-2026-0001)
        content_hash: Full SHA-256 hex digest

    Returns:
        Verify URL: https://windi-domain.com/vault/verify?serial=X&hash=Y
    """
    # Use short hash (16 chars) in URL - full hash is in document metadata
    short_hash = content_hash[:16] if content_hash else ""

    return f"{VERIFY_BASE_URL}?id={serial or short_hash}"


def generate_qr_image(url: str, size: int = DEFAULT_SIZE,
                      color: str = WINDI_GOLD, bg: str = KLAR_WHITE) -> bytes | None:
    """
    Generate QR code PNG image bytes.

    Args:
        url: URL to encode in QR
        size: Image size in pixels (default 150x150)
        color: Foreground color hex (default WINDI Gold #8B6914)
        bg: Background color hex (default KLAR white #FDFBF5)

    Returns:
        PNG image bytes, or None if qrcode library unavailable
    """
    if not HAS_QRCODE or not HAS_PIL:
        return None

    try:
        # Create QR code with HIGH error correction (30% damage tolerance)
        qr = qrcode.QRCode(
            version=None,  # Auto-size based on data
            error_correction=ERROR_CORRECT_H,
            box_size=10,
            border=DEFAULT_BORDER,
        )
        qr.add_data(url)
        qr.make(fit=True)

        # Generate image with WINDI Gold foreground
        img = qr.make_image(fill_color=color, back_color=bg)

        # Convert to PIL Image if needed and resize
        if hasattr(img, 'get_image'):
            pil_img = img.get_image()
        else:
            pil_img = img

        # Resize to target size
        pil_img = pil_img.resize((size, size), Image.Resampling.LANCZOS)

        # Save to bytes
        output = io.BytesIO()
        pil_img.save(output, format="PNG")
        return output.getvalue()

    except Exception as e:
        print(f"[qr_engine] Warning: QR generation failed: {e}")
        return None


def generate_qr_with_label(url: str, serial: str, size: int = DEFAULT_SIZE) -> bytes | None:
    """
    Generate QR code with serial label underneath.

    Args:
        url: URL to encode in QR
        serial: Serial number to display as label
        size: QR code size in pixels

    Returns:
        PNG image bytes (QR + label), or None if libraries unavailable
    """
    if not HAS_QRCODE or not HAS_PIL:
        return None

    try:
        # Generate base QR image
        qr_bytes = generate_qr_image(url, size)
        if not qr_bytes:
            return None

        # Load QR image
        qr_img = Image.open(io.BytesIO(qr_bytes))

        # Create composite image with space for label
        label_height = 20
        composite = Image.new("RGB", (size, size + label_height), KLAR_WHITE)

        # Paste QR at top
        composite.paste(qr_img, (0, 0))

        # Draw serial label
        draw = ImageDraw.Draw(composite)

        # Try to use a small font, fall back to default
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 10)
        except Exception:
            font = ImageFont.load_default()

        # Center the label
        text_bbox = draw.textbbox((0, 0), serial, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = (size - text_width) // 2
        text_y = size + 2

        # Draw in WINDI Gold
        draw.text((text_x, text_y), serial, fill=WINDI_GOLD, font=font)

        # Save to bytes
        output = io.BytesIO()
        composite.save(output, format="PNG")
        return output.getvalue()

    except Exception as e:
        print(f"[qr_engine] Warning: QR with label generation failed: {e}")
        return None


def get_qr_for_document(serial: str, content_hash: str, size: int = DEFAULT_SIZE,
                        with_label: bool = False) -> tuple[bytes | None, str]:
    """
    Convenience function for document embedding.

    Args:
        serial: WINDI serial number
        content_hash: Full SHA-256 hex digest
        size: QR size in pixels
        with_label: Include serial label below QR

    Returns:
        Tuple of (PNG bytes or None, verify URL)
    """
    url = generate_verify_url(serial, content_hash)

    if with_label:
        qr_bytes = generate_qr_with_label(url, serial, size)
    else:
        qr_bytes = generate_qr_image(url, size)

    return (qr_bytes, url)


def is_available() -> bool:
    """Check if QR generation is available."""
    return HAS_QRCODE and HAS_PIL


# ── CLI Test ──
if __name__ == "__main__":
    import sys

    print("WINDI QR Engine - N4 Module")
    print("=" * 50)
    print(f"qrcode library: {'OK' if HAS_QRCODE else 'NOT AVAILABLE'}")
    print(f"Pillow library: {'OK' if HAS_PIL else 'NOT AVAILABLE'}")
    print(f"QR generation: {'AVAILABLE' if is_available() else 'DEGRADED'}")

    if is_available():
        # Test URL generation
        test_serial = "WINDI-2026-0001"
        test_hash = "abc123def456789012345678901234567890123456789012345678901234"
        url = generate_verify_url(test_serial, test_hash)
        print(f"\nTest URL: {url}")

        # Test QR generation
        qr_bytes = generate_qr_image(url)
        if qr_bytes:
            print(f"QR PNG size: {len(qr_bytes)} bytes")

            # Save test QR if arg provided
            if len(sys.argv) > 1 and sys.argv[1] == "--save":
                with open("/tmp/windi_qr_test.png", "wb") as f:
                    f.write(qr_bytes)
                print("Saved: /tmp/windi_qr_test.png")

        # Test QR with label
        qr_label_bytes = generate_qr_with_label(url, test_serial)
        if qr_label_bytes:
            print(f"QR+Label PNG size: {len(qr_label_bytes)} bytes")

            if len(sys.argv) > 1 and sys.argv[1] == "--save":
                with open("/tmp/windi_qr_label_test.png", "wb") as f:
                    f.write(qr_label_bytes)
                print("Saved: /tmp/windi_qr_label_test.png")
    else:
        print("\nQR generation not available - missing dependencies")
