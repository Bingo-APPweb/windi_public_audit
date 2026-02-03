"""
WINDI-RECEIPT Generator
Unique document certification with hash and timestamp

"KI verarbeitet. Der Mensch entscheidet. WINDI garantiert."
"""

import hashlib
from datetime import datetime


# Configuration
WINDI_VERIFY_BASE_URL = 'https://windi.ai/verify'
WINDI_GOVERNANCE_URL = 'https://windi.ai/governance'

# Declarations (DE primary, EN secondary)
DECLARATIONS = {
    'de': 'KI verarbeitet. Der Mensch entscheidet. WINDI garantiert.',
    'en': 'AI processes. Human decides. WINDI guarantees.'
}

COMPLIANCE_TEXT = {
    'de': 'EU AI Act Art. 50 · Transparenzpflichten',
    'en': 'EU AI Act Art. 50 · Transparency obligations'
}


def generate_receipt(content, author="", timestamp=None, language='de'):
    """
    Generate WINDI-RECEIPT for a document.
    
    Args:
        content: Document content (string or dict)
        author: Author name
        timestamp: Optional datetime (uses now if None)
        language: 'de' or 'en'
    
    Returns:
        dict with receipt data
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    # Generate hash
    hash_input = f"{str(content)}{author}{timestamp.isoformat()}"
    full_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    short_hash = full_hash[:12].lower()
    
    # Generate ID
    date_code = timestamp.strftime('%d%b%y').upper()
    receipt_id = f"WINDI-BABEL-{date_code}-{short_hash[:8].upper()}"
    
    # Verification URL
    verify_url = f"{WINDI_VERIFY_BASE_URL}?id={receipt_id}&h={short_hash}"
    
    return {
        'id': receipt_id,
        'hash': short_hash,
        'full_hash': full_hash,
        'timestamp': timestamp,
        'timestamp_iso': timestamp.isoformat(),
        'date_formatted': timestamp.strftime('%d.%m.%Y %H:%M'),
        'author': author,
        'verify_url': verify_url,
        'governance_url': WINDI_GOVERNANCE_URL,
        'declaration': DECLARATIONS.get(language, DECLARATIONS['de']),
        'compliance': COMPLIANCE_TEXT.get(language, COMPLIANCE_TEXT['de']),
        'language': language
    }


def verify_receipt(receipt_id, hash_short):
    """
    Verify a receipt (placeholder for database lookup).
    
    In production, this would query the forensic ledger.
    """
    # TODO: Implement database lookup
    return {
        'valid': True,
        'receipt_id': receipt_id,
        'hash': hash_short,
        'message': 'Receipt verification requires database connection'
    }
