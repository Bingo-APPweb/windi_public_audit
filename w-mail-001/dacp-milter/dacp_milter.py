#!/usr/bin/env python3
"""
W-MAIL-DACP-MILTER v1.0 — Main Milter Module
Spec: §227 W-MAIL-DACP-MILTER
Invariants: I9, I11, I14

This milter intercepts outbound email, generates DACP proofs,
injects verification footers, and seals to the Forensic Ledger.

MUST run BEFORE OpenDKIM in the milter chain.
"""

import os
import sys
import time
import email
import secrets
import logging
import threading
from datetime import datetime
from io import BytesIO
from typing import Optional

import Milter
from Milter.utils import parse_addr

from canonical import canonical_hash, hash_field, _extract_addr, _extract_addrs
from footer import generate_plain_footer, generate_html_footer, has_dacp_footer
from ledger_client import seal_proof, is_ledger_reachable, LedgerError
from metrics import get_metrics, increment, record_processing_time
from ratelimit import is_allowed
from selector_loader import load_dkim_selector, get_dkim_selector
from http_server import start_http_server

# Configure logging
LOG_PATH = os.environ.get('LOG_PATH', '/logs/dacp-milter.log')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('dacp-milter')

# Configuration
DOMAIN = os.environ.get('DOMAIN', 'windisites.de')
MILTER_SOCKET = os.environ.get('MILTER_SOCKET', 'inet:8890@0.0.0.0')


def generate_proof_id() -> str:
    """Generate unique proof ID: WINDI-MAIL-PROOF-{timestamp}-{random}"""
    ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    rand = secrets.token_hex(4).upper()
    return f"WINDI-MAIL-PROOF-{ts}-{rand}"


def _valid_upstream_proof_id(value: str) -> bool:
    """Accept only WINDI proof namespaces that may be sealed by DACP."""
    if not value:
        return False
    allowed_prefixes = (
        'WINDI-SITES-PROOFMAIL-',
        'WINDI-MAIL-PROOF-',
    )
    return value.startswith(allowed_prefixes) and all(
        c.isalnum() or c in '-_' for c in value
    )


class DACPMilter(Milter.Base):
    """
    DACP Milter implementation.

    Lifecycle:
    1. connect() - connection established
    2. envfrom() - MAIL FROM received
    3. envrcpt() - RCPT TO received (may be called multiple times)
    4. header() - each header received
    5. eoh() - end of headers
    6. body() - body chunks received
    7. eom() - end of message (where we inject footer and seal)
    8. close() - connection closed
    """

    def __init__(self):
        self.id = Milter.uniqueID()
        self.start_time = time.time()
        self.mail_from = None
        self.rcpt_to = []
        self.headers = {}
        self.body_chunks = []
        self.subject = None
        self.date = None
        self.content_type = None
        self.is_multipart = False

    @Milter.noreply
    def connect(self, hostname, family, hostaddr):
        """Connection established"""
        logger.debug(f"[{self.id}] Connect from {hostname}")
        return Milter.CONTINUE

    @Milter.noreply
    def envfrom(self, f, *params):
        """MAIL FROM received"""
        self.mail_from = f
        self.rcpt_to = []
        self.headers = {}
        self.body_chunks = []
        self.subject = None
        self.date = None
        self.content_type = None
        self.is_multipart = False
        logger.debug(f"[{self.id}] MAIL FROM: {f}")
        return Milter.CONTINUE

    @Milter.noreply
    def envrcpt(self, to, *params):
        """RCPT TO received"""
        self.rcpt_to.append(to)
        logger.debug(f"[{self.id}] RCPT TO: {to}")
        return Milter.CONTINUE

    @Milter.noreply
    def header(self, name, value):
        """Header received"""
        name_lower = name.lower()
        self.headers[name_lower] = value

        if name_lower == 'subject':
            self.subject = value
        elif name_lower == 'date':
            self.date = value
        elif name_lower == 'content-type':
            self.content_type = value
            self.is_multipart = 'multipart' in value.lower()

        return Milter.CONTINUE

    @Milter.noreply
    def eoh(self):
        """End of headers"""
        return Milter.CONTINUE

    def body(self, chunk):
        """Body chunk received"""
        self.body_chunks.append(chunk)
        return Milter.CONTINUE

    def eom(self):
        """
        End of message - this is where the magic happens.

        1. Check bypass conditions
        2. Rate limit check
        3. Generate proof_id
        4. Compute canonical hash
        5. Inject footer
        6. Add headers
        7. Seal to Ledger
        8. Return ACCEPT or TEMPFAIL
        """
        try:
            return self._process_message()
        except Exception as e:
            logger.error(f"[{self.id}] Unexpected error: {e}", exc_info=True)
            increment('errors_total')
            return Milter.TEMPFAIL

    def _process_message(self) -> int:
        """Process the message and apply DACP"""

        # === BYPASS CHECKS (§227 Section 8) ===

        # 1. Already sealed (our seal) - idempotent.
        # A requested proof id from an upstream app is not a seal yet.
        if (
            'x-windi-dacp-proof-id' in self.headers
            and 'x-windi-dacp-body-hash' in self.headers
        ):
            logger.info(f"[{self.id}] Bypass: already sealed")
            increment('bypassed_already_sealed_total')
            return Milter.ACCEPT

        # 7. Internal system mail
        if self.headers.get('x-windi-internal') == '1':
            logger.info(f"[{self.id}] Bypass: internal mail")
            increment('bypassed_internal_total')
            return Milter.ACCEPT

        # 4. Encrypted body
        ct = self.content_type or ''
        if any(x in ct.lower() for x in ['multipart/encrypted', 'application/pkcs7-mime', 'application/pgp-encrypted']):
            logger.info(f"[{self.id}] Bypass: encrypted content")
            increment('bypassed_encrypted_total')
            return Milter.ACCEPT

        # 8. DSN / Bounce
        if self._is_dsn():
            logger.info(f"[{self.id}] Bypass: DSN/bounce")
            increment('bypassed_dsn_total')
            return Milter.ACCEPT

        # === RATE LIMIT CHECK ===
        from_addr = _extract_addr(self.mail_from)
        from_hash = hash_field(from_addr)

        if not is_allowed(from_hash):
            logger.warning(f"[{self.id}] Rate limited: {from_addr}")
            increment('tempfail_ratelimit_total')
            return Milter.TEMPFAIL

        # === BUILD EMAIL MESSAGE FOR PROCESSING ===
        body_data = b''.join(self.body_chunks)

        # Reconstruct message for canonical hash
        msg_text = self._build_message_text(body_data)
        msg = email.message_from_string(msg_text)

        # 2. Check for forward of externally-sealed mail
        body_str = body_data.decode('utf-8', errors='replace')
        is_forward_reseal = has_dacp_footer(body_str) and 'x-windi-dacp-proof-id' not in self.headers

        if is_forward_reseal:
            logger.info(f"[{self.id}] Re-sealing forwarded mail with existing DACP footer")
            increment('resealed_forwarded_total')

        # === GENERATE OR INHERIT PROOF ===
        requested_proof_id = (
            self.headers.get('x-windi-dacp-requested-proof-id', '').strip()
            or self.headers.get('x-windi-proof-id', '').strip()
        )
        if _valid_upstream_proof_id(requested_proof_id):
            proof_id = requested_proof_id
            logger.info(f"[{self.id}] Inherited upstream proof id: {proof_id}")
        else:
            if requested_proof_id:
                logger.warning(f"[{self.id}] Ignoring invalid upstream proof id: {requested_proof_id}")
            proof_id = generate_proof_id()
        sealed_at = datetime.utcnow()

        # Compute canonical hash BEFORE injecting footer
        body_hash = canonical_hash(msg)

        # Hash PII fields for GDPR compliance
        to_addrs = _extract_addrs(self.rcpt_to)
        to_hashes = [hash_field(addr) for addr in to_addrs]
        subject_hash = hash_field(self.subject or '')

        # === INJECT FOOTER ===
        # Include body_hash for independent verification without UI
        plain_footer = generate_plain_footer(proof_id, body_hash, sealed_at)
        html_footer = generate_html_footer(proof_id, body_hash, sealed_at)

        if self.is_multipart:
            # Inject in both text/plain and text/html parts
            self._inject_multipart_footer(plain_footer, html_footer)
        else:
            # Simple text body
            self.addrcpt('<%s>' % self.mail_from)  # dummy to trigger body replacement
            self.replacebody((body_data.decode('utf-8', errors='replace') + plain_footer).encode('utf-8'))

        # === ADD HEADERS ===
        self.addheader('X-WINDI-DACP-Proof-ID', proof_id)
        self.addheader('X-WINDI-DACP-Version', 'v1')
        self.addheader('X-WINDI-DACP-Body-Hash', body_hash)
        self.addheader('X-WINDI-DACP-Sealed-At', sealed_at.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z")
        self.addheader('X-WINDI-DACP-Verify', f"https://windi-domain.com/verify-public/web/verify.html?id={proof_id}")

        # === SEAL TO LEDGER (I14: tempfail on failure) ===
        try:
            seal_proof(
                proof_id=proof_id,
                from_hash=from_hash,
                to_hashes=to_hashes,
                subject_hash=subject_hash,
                body_hash=body_hash,
                dkim_selector=get_dkim_selector() or 'rsa',
                domain=DOMAIN,
                actor=from_addr
            )
            logger.info(f"[{self.id}] Sealed: {proof_id}")
            increment('sealed_total')

        except LedgerError as e:
            logger.error(f"[{self.id}] Ledger seal failed: {e}")
            increment('tempfail_ledger_total')
            return Milter.TEMPFAIL

        # Record processing time
        elapsed = time.time() - self.start_time
        record_processing_time(elapsed)

        return Milter.ACCEPT

    def _is_dsn(self) -> bool:
        """Check if message is a DSN/bounce"""
        ct = self.content_type or ''
        from_addr = (self.mail_from or '').lower()

        if 'multipart/report' in ct.lower() and 'delivery-status' in ct.lower():
            return True
        if 'mailer-daemon' in from_addr:
            return True
        if self.headers.get('auto-submitted', '').lower() in ['auto-replied', 'auto-generated']:
            return True

        return False

    def _build_message_text(self, body_data: bytes) -> str:
        """Build full message text for parsing"""
        headers_text = []
        headers_text.append(f"From: {self.mail_from}")
        headers_text.append(f"To: {', '.join(self.rcpt_to)}")
        if self.subject:
            headers_text.append(f"Subject: {self.subject}")
        if self.date:
            headers_text.append(f"Date: {self.date}")
        if self.content_type:
            headers_text.append(f"Content-Type: {self.content_type}")

        return '\r\n'.join(headers_text) + '\r\n\r\n' + body_data.decode('utf-8', errors='replace')

    def _inject_multipart_footer(self, plain_footer: str, html_footer: str):
        """Inject footer into multipart message parts"""
        # For multipart, we need to modify each part
        # This is complex with libmilter - simplified approach:
        # Replace entire body with modified version

        body_data = b''.join(self.body_chunks)
        body_str = body_data.decode('utf-8', errors='replace')

        # Simple heuristic: inject plain footer at end
        # More sophisticated handling would parse MIME boundaries
        modified_body = body_str + '\r\n' + plain_footer

        self.replacebody(modified_body.encode('utf-8'))

    def close(self):
        """Connection closed"""
        logger.debug(f"[{self.id}] Connection closed")
        return Milter.CONTINUE


def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("W-MAIL-DACP-MILTER v1.0 starting")
    logger.info(f"Domain: {DOMAIN}")
    logger.info(f"Socket: {MILTER_SOCKET}")
    logger.info("=" * 60)

    # Load DKIM selector
    selector = load_dkim_selector(DOMAIN)
    if selector:
        logger.info(f"DKIM selector loaded: {selector}")
    else:
        logger.warning("DKIM selector not found - using default 'rsa'")

    # Check Ledger connectivity
    if is_ledger_reachable():
        logger.info("Ledger is reachable")
    else:
        logger.warning("Ledger not reachable at startup - will retry on each message")

    # Start HTTP admin server in background thread
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()
    logger.info("HTTP admin server started on port 8895")

    # Configure milter
    Milter.factory = DACPMilter
    Milter.set_flags(Milter.ADDHDRS | Milter.CHGBODY)

    logger.info("Starting milter loop...")
    Milter.runmilter("dacp-milter", MILTER_SOCKET, timeout=300)

    logger.info("Milter stopped")


if __name__ == "__main__":
    main()
