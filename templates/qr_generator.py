"""
WINDI QR Code Generator
Dual QR system: Institutional + Document

- QR Institucional: windi.ai/governance (same for all docs)
- QR Documento: windi.ai/verify?id=... (unique per doc)
"""

from io import BytesIO
import json

# Check if qrcode is available
try:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_M, ERROR_CORRECT_H
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False


# URLs
GOVERNANCE_URL = 'https://windi.ai/governance'
VERIFY_BASE_URL = 'https://windi.ai/verify'


def is_available():
    """Check if QR code generation is available."""
    return QRCODE_AVAILABLE


def generate_qr(data, size=100, error_correction='M'):
    """
    Generate QR code image.
    
    Args:
        data: String or dict to encode
        size: Image size in pixels
        error_correction: 'L', 'M', 'Q', or 'H'
    
    Returns:
        BytesIO with PNG image, or None if not available
    """
    if not QRCODE_AVAILABLE:
        return None
    
    if isinstance(data, dict):
        data = json.dumps(data, separators=(',', ':'))
    
    ec_map = {
        'L': qrcode.constants.ERROR_CORRECT_L,
        'M': qrcode.constants.ERROR_CORRECT_M,
        'Q': qrcode.constants.ERROR_CORRECT_Q,
        'H': qrcode.constants.ERROR_CORRECT_H
    }
    
    qr = qrcode.QRCode(
        version=None,
        error_correction=ec_map.get(error_correction, ERROR_CORRECT_M),
        box_size=10,
        border=1
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((size, size))
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer


def generate_institutional_qr(language='de', size=100):
    """
    Generate institutional QR code.
    Same for ALL WINDI documents.
    Points to governance/methodology page.
    
    Args:
        language: 'de' or 'en'
        size: Image size in pixels
    
    Returns:
        BytesIO with PNG image
    """
    url = f"{GOVERNANCE_URL}?lang={language}"
    return generate_qr(url, size=size, error_correction='M')


def generate_document_qr(receipt, size=100):
    """
    Generate document-specific QR code.
    Unique for EACH document.
    Contains verification URL with hash.
    
    Args:
        receipt: Receipt dict from receipt.generate_receipt()
        size: Image size in pixels
    
    Returns:
        BytesIO with PNG image
    """
    # Compact JSON for QR
    qr_data = {
        'id': receipt['id'],
        'h': receipt['hash'],
        'v': receipt['verify_url']
    }
    return generate_qr(qr_data, size=size, error_correction='H')


def generate_both_qr(receipt, language='de', size=100):
    """
    Generate both QR codes for a document.
    
    Args:
        receipt: Receipt dict
        language: 'de' or 'en'
        size: Image size in pixels
    
    Returns:
        tuple: (institutional_qr, document_qr) as BytesIO objects
    """
    inst_qr = generate_institutional_qr(language=language, size=size)
    doc_qr = generate_document_qr(receipt, size=size)
    return (inst_qr, doc_qr)
