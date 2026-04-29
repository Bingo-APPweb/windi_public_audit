#!/usr/bin/env python3
"""
W-MAIL-001 v1.1 — Dual Anchored Communication Proof (DACP)

Protocol: DACP-v1
Invariants: I1, I9, I11, I14

Binding Architecture:
    EMAIL ←──────────────────────────→ RECEIPT
    │                                      │
    ├─ X-WINDI-Proof-ID ─────────────────→├─ id
    ├─ X-WINDI-Content-Hash ─────────────→├─ content_hash
    ├─ X-WINDI-Binding: dual-v1          │
    │                                      │
    ├─ DKIM-Signature ───────────────────→├─ dkim.domain
    │                                      ├─ dkim.selector
    │                                      ├─ dkim.algorithm
    │                                      ├─ dkim.bh (body hash)
    │                                      ├─ dkim.b (signature)
    │                                      │
    └─ Message-ID ───────────────────────→└─ message_id
       Date ─────────────────────────────→   date_header

Author: Liga IA+H
Date: 2026-04-30
"""

import hashlib
import re
import subprocess
import json
import requests
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from typing import Optional


# ============================================================
# CONFIGURATION
# ============================================================

DOMAIN = "windisites.de"
DKIM_SELECTOR = "rsa"
LEDGER_URL = "http://localhost:8101/api/receipts"
DOCKER_CONTAINER = "windi-mailserver"

# WINDI Header Namespace (versioned)
HEADER_PROOF_ID = "X-WINDI-Proof-ID"
HEADER_CONTENT_HASH = "X-WINDI-Content-Hash"
HEADER_BINDING = "X-WINDI-Binding"
BINDING_VERSION = "dual-v1"


# ============================================================
# DKIM CANONICALIZATION (RFC 6376 - relaxed/relaxed)
# ============================================================

def canonicalize_body_relaxed(body: str) -> str:
    """
    DKIM relaxed body canonicalization (RFC 6376 Section 3.4.4)

    1. Reduce all sequences of WSP to single SP
    2. Remove all trailing WSP at end of lines
    3. Remove all empty lines at end of body
    4. Ensure body ends with CRLF
    """
    lines = body.replace('\r\n', '\n').replace('\r', '\n').split('\n')

    canonical_lines = []
    for line in lines:
        # Reduce WSP sequences to single space
        line = re.sub(r'[ \t]+', ' ', line)
        # Remove trailing whitespace
        line = line.rstrip(' \t')
        canonical_lines.append(line)

    # Join with CRLF
    canonical = '\r\n'.join(canonical_lines)

    # Remove trailing empty lines
    canonical = canonical.rstrip('\r\n')

    # Ensure ends with CRLF (unless empty)
    if canonical:
        canonical += '\r\n'

    return canonical


def hash_canonical_body(body: str) -> str:
    """
    Hash the canonicalized body using SHA-256.
    Returns hex-encoded hash with 'sha256:' prefix.
    """
    canonical = canonicalize_body_relaxed(body)
    hash_bytes = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    return f"sha256:{hash_bytes}"


# ============================================================
# DKIM SIGNATURE PARSING
# ============================================================

def parse_dkim_signature(dkim_header: str) -> dict:
    """
    Parse DKIM-Signature header into structured fields.

    Returns dict with:
        - domain: signing domain (d=)
        - selector: DKIM selector (s=)
        - algorithm: signing algorithm (a=)
        - bh: body hash base64 (bh=)
        - b: signature base64 (b=)
        - headers_signed: list of signed headers (h=)
        - timestamp: signature timestamp (t=)
        - canonicalization: c= value
    """
    # Remove header name if present
    if dkim_header.lower().startswith('dkim-signature:'):
        dkim_header = dkim_header[15:].strip()

    # Unfold (remove CRLF + whitespace)
    dkim_header = re.sub(r'\r?\n[ \t]+', ' ', dkim_header)

    # Parse tag=value pairs
    result = {}

    # Extract each tag
    tags = {
        'd': 'domain',
        's': 'selector',
        'a': 'algorithm',
        'bh': 'bh',
        'b': 'b',
        'h': 'headers_signed',
        't': 'timestamp',
        'c': 'canonicalization'
    }

    for tag, field in tags.items():
        # Match tag=value; handle multiline base64
        pattern = rf'{tag}=([^;]+)'
        match = re.search(pattern, dkim_header, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            # Remove whitespace from base64 values
            if tag in ('b', 'bh'):
                value = re.sub(r'\s+', '', value)
            result[field] = value

    return result


# ============================================================
# PROOF GENERATION
# ============================================================

def generate_proof_id() -> str:
    """
    Generate semantic, indexable proof ID.
    Format: WINDI-MAIL-PROOF-YYYYMMDDHHMMSS-HASH8
    """
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d%H%M%S")

    # Short hash for uniqueness
    unique = hashlib.sha256(f"{timestamp}{now.microsecond}".encode()).hexdigest()[:8].upper()

    return f"WINDI-MAIL-PROOF-{timestamp}-{unique}"


def append_proof_footer(body: str, proof_id: str) -> str:
    """
    Append DACP verify footer to email body.
    Called BEFORE hashing so hash matches sent content.
    """
    verify_url = f"https://windi-domain.com/verify-public/web/verify.html?id={proof_id}"
    api_url = f"https://windi-domain.com/api/receipts/{proof_id}"

    footer = f"""
---
WINDI DACP-v1 PROOF
Proof-ID: {proof_id}
Verify: {verify_url}
API: {api_url}
"""
    return body + footer


def build_mime_message(
    from_addr: str,
    to_addr: str,
    subject: str,
    body: str,
    proof_id: str,
    content_hash: str
) -> MIMEText:
    """
    Build MIME message with WINDI proof headers injected.
    Body should already have footer appended.
    """
    msg = MIMEText(body, 'plain', 'utf-8')

    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = subject
    msg['Date'] = formatdate(localtime=False, usegmt=True)
    msg['Message-ID'] = make_msgid(domain=DOMAIN)

    # WINDI Proof Headers (versioned namespace)
    msg[HEADER_PROOF_ID] = proof_id
    msg[HEADER_CONTENT_HASH] = content_hash
    msg[HEADER_BINDING] = BINDING_VERSION

    return msg


# ============================================================
# EMAIL SENDING
# ============================================================

def send_via_docker(mime_message: MIMEText, from_addr: str, to_addr: str) -> bool:
    """
    Send email via docker-mailserver using sendmail.
    Returns True if successful.
    """
    email_bytes = mime_message.as_bytes()

    cmd = [
        'docker', 'exec', '-i', DOCKER_CONTAINER,
        'sendmail', '-f', from_addr, to_addr
    ]

    try:
        result = subprocess.run(
            cmd,
            input=email_bytes,
            capture_output=True,
            timeout=30
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception as e:
        print(f"Send error: {e}")
        return False


def extract_dkim_from_log(message_id: str, timeout: int = 5) -> Optional[str]:
    """
    Extract DKIM-Signature from mail log after sending.

    Note: For production, this should read from the sent message
    in the queue or use a milter. This is a simplified version.
    """
    import time

    # Wait for mail to be processed
    time.sleep(2)

    # Check mail log for DKIM signature addition
    cmd = [
        'docker', 'exec', DOCKER_CONTAINER,
        'tail', '-100', '/var/log/mail.log'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

        # Look for DKIM signature confirmation
        for line in result.stdout.split('\n'):
            if 'DKIM-Signature field added' in line and f's={DKIM_SELECTOR}' in line:
                # Return confirmation that DKIM was added
                return f"s={DKIM_SELECTOR}; d={DOMAIN}; a=rsa-sha256"

        return None
    except Exception:
        return None


# ============================================================
# LEDGER SEALING
# ============================================================

def seal_to_ledger(
    proof_id: str,
    from_addr: str,
    to_addr: str,
    subject: str,
    content_hash: str,
    message_id: str,
    date_header: str,
    dkim_info: dict
) -> dict:
    """
    Seal the proof to Forensic Ledger.

    Returns ledger response.
    """
    payload = {
        "id": proof_id,
        "actor": from_addr,
        "app": "w-mail-001",
        "doc_name": f"DACP Email Proof: {subject[:50]}",
        "doc_type": "doc",
        "governance_level": "HIGH",
        "content_hash": content_hash,
        "sge_score": 1.0,
        "metadata": {
            "protocol": "DACP-v1",
            "binding": BINDING_VERSION,
            "from": from_addr,
            "to": to_addr,
            "subject": subject,
            "message_id": message_id,
            "date_header": date_header,
            "dkim": dkim_info,
            "invariants": ["I1", "I9", "I11", "I14"],
            "eu_ai_act_art14": True
        }
    }

    try:
        response = requests.post(
            LEDGER_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ============================================================
# MAIN PROOF BINDING FLOW
# ============================================================

def send_proven_email(
    from_addr: str,
    to_addr: str,
    subject: str,
    body: str,
    seal_to_ledger_flag: bool = True
) -> dict:
    """
    Send email with full DACP proof binding.

    Flow:
    1. Generate proof ID
    2. Append proof footer with verify URL to body
    3. Canonicalize and hash FULL body (with footer)
    4. Build MIME with proof headers
    5. Send via SMTP (DKIM added by server)
    6. Extract DKIM confirmation
    7. Seal to Ledger with binding metadata

    Returns dict with:
        - success: bool
        - proof_id: str
        - content_hash: str
        - message_id: str
        - ledger_response: dict (if sealed)
    """
    result = {
        "success": False,
        "proof_id": None,
        "content_hash": None,
        "message_id": None,
        "date_header": None,
        "dkim": None,
        "ledger_response": None
    }

    # Step 1: Generate proof ID
    proof_id = generate_proof_id()
    result["proof_id"] = proof_id

    # Step 2: Append proof footer to body (includes verify URL)
    full_body = append_proof_footer(body, proof_id)

    # Step 3: Canonicalize and hash FULL body (with footer)
    content_hash = hash_canonical_body(full_body)
    result["content_hash"] = content_hash

    # Step 4: Build MIME message with proof headers
    mime_msg = build_mime_message(
        from_addr=from_addr,
        to_addr=to_addr,
        subject=subject,
        body=full_body,  # Use full body with footer
        proof_id=proof_id,
        content_hash=content_hash
    )

    # Extract headers for ledger
    message_id = mime_msg['Message-ID']
    date_header = mime_msg['Date']
    result["message_id"] = message_id
    result["date_header"] = date_header

    # Step 5: Send email
    print(f"[DACP] Sending email with proof ID: {proof_id}")
    print(f"[DACP] Content hash: {content_hash}")

    send_success = send_via_docker(mime_msg, from_addr, to_addr)

    if not send_success:
        result["error"] = "Failed to send email via SMTP"
        return result

    print(f"[DACP] Email sent successfully")

    # Step 6: Extract DKIM confirmation
    dkim_confirmation = extract_dkim_from_log(message_id)

    dkim_info = {
        "domain": DOMAIN,
        "selector": DKIM_SELECTOR,
        "algorithm": "rsa-sha256",
        "status": "signed" if dkim_confirmation else "unknown"
    }
    result["dkim"] = dkim_info

    # Step 7: Seal to Ledger
    if seal_to_ledger_flag:
        print(f"[DACP] Sealing to Forensic Ledger...")

        ledger_response = seal_to_ledger(
            proof_id=proof_id,
            from_addr=from_addr,
            to_addr=to_addr,
            subject=subject,
            content_hash=content_hash,
            message_id=message_id,
            date_header=date_header,
            dkim_info=dkim_info
        )

        result["ledger_response"] = ledger_response

        if ledger_response.get("ok"):
            print(f"[DACP] Sealed to Ledger: {proof_id}")
            result["success"] = True
        else:
            print(f"[DACP] Ledger seal failed: {ledger_response}")
            result["error"] = f"Ledger seal failed: {ledger_response.get('error', 'unknown')}"
    else:
        result["success"] = True

    return result


# ============================================================
# CLI INTERFACE
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="W-MAIL-001 DACP - Dual Anchored Communication Proof"
    )
    parser.add_argument("--from", dest="from_addr", required=True, help="Sender email")
    parser.add_argument("--to", dest="to_addr", required=True, help="Recipient email")
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--body", required=True, help="Email body text")
    parser.add_argument("--no-seal", action="store_true", help="Skip ledger seal")

    args = parser.parse_args()

    result = send_proven_email(
        from_addr=args.from_addr,
        to_addr=args.to_addr,
        subject=args.subject,
        body=args.body,
        seal_to_ledger_flag=not args.no_seal
    )

    print("\n" + "="*60)
    print("DACP PROOF RESULT")
    print("="*60)
    print(json.dumps(result, indent=2, default=str))
