"""
W-MAIL-DACP-MILTER — Canonical Hash Module
Spec: §227 Section 7
Invariants: I11, I14
"""

import hashlib
import re
import email
import email.message
from email.utils import parseaddr
from typing import List, Optional


def _extract_addr(header_value: Optional[str]) -> str:
    """Extract email address from header like 'Name <email@domain>'"""
    if not header_value:
        return ""
    _, addr = parseaddr(header_value)
    return addr.lower().strip()


def _extract_addrs(header_values: List[str]) -> List[str]:
    """Extract all email addresses from To/Cc headers"""
    addrs = []
    for val in header_values:
        if val:
            # Handle comma-separated addresses
            for part in str(val).split(','):
                addr = _extract_addr(part)
                if addr:
                    addrs.append(addr)
    return addrs


def _extract_primary_body(msg: email.message.Message) -> str:
    """
    Extract primary body content.
    Prefer text/plain, fall back to stripped HTML.
    """
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disp = str(part.get('Content-Disposition', ''))

            # Skip attachments
            if 'attachment' in content_disp:
                continue

            if content_type == 'text/plain':
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        return payload.decode(charset, errors='replace')
                    except:
                        return payload.decode('utf-8', errors='replace')

        # No text/plain found, try text/html
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disp = str(part.get('Content-Disposition', ''))

            if 'attachment' in content_disp:
                continue

            if content_type == 'text/html':
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        html = payload.decode(charset, errors='replace')
                        return _strip_html_tags(html)
                    except:
                        return ""

        return ""
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or 'utf-8'
            try:
                text = payload.decode(charset, errors='replace')
                if msg.get_content_type() == 'text/html':
                    return _strip_html_tags(text)
                return text
            except:
                return ""
        return str(msg.get_payload() or "")


def _strip_html_tags(html: str) -> str:
    """Strip HTML tags for canonical comparison"""
    # Remove script and style elements
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    html = re.sub(r'<[^>]+>', ' ', html)
    # Normalize whitespace
    html = re.sub(r'\s+', ' ', html)
    return html.strip()


def _strip_dacp_footer(body: str) -> str:
    """
    Strip our own DACP footer to avoid self-reference in hash.
    Handles both plain text and HTML markers.
    """
    # Strip plain text footer
    body = re.sub(
        r'---\s*\nWINDI DACP-v1 PROOF\n.*?(?=\n---|\Z)',
        '',
        body,
        flags=re.DOTALL
    )

    # Strip HTML footer (data-windi-dacp="v1" marker)
    body = re.sub(
        r'<div\s+data-windi-dacp="v1"[^>]*>.*?</div>',
        '',
        body,
        flags=re.DOTALL | re.IGNORECASE
    )

    return body


def canonical_hash(msg: email.message.Message) -> str:
    """
    Produces a deterministic SHA-256 such that any receiver who
    reconstructs `From | To_joined | Subject | Date | normalized_body`
    arrives at the same hash.

    Spec: §227 Section 7
    """
    # 1. Pick body (prefer text/plain for canonical input)
    body = _extract_primary_body(msg)

    # 2. Strip our own footer (avoid self-reference loop)
    body = _strip_dacp_footer(body)

    # 3. Normalize line endings CRLF/CR → LF
    body = body.replace('\r\n', '\n').replace('\r', '\n')

    # 4. Strip trailing whitespace per line, then trim trailing blank lines
    body = '\n'.join(line.rstrip() for line in body.split('\n')).rstrip('\n')

    # 5. Canonical join
    to_values = msg.get_all('To', []) or []
    cc_values = msg.get_all('Cc', []) or []
    to_joined = ','.join(sorted(_extract_addrs(to_values + cc_values)))

    from_addr = _extract_addr(msg.get('From', ''))
    subject = (msg.get('Subject') or '').strip()
    date = (msg.get('Date') or '').strip()

    canonical = (
        f"From:{from_addr}\n"
        f"To:{to_joined}\n"
        f"Subject:{subject}\n"
        f"Date:{date}\n"
        f"Body:{body}"
    )

    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def hash_field(value: str) -> str:
    """Hash a single field (for GDPR compliance - no PII in Ledger)"""
    return hashlib.sha256(value.lower().strip().encode('utf-8')).hexdigest()
