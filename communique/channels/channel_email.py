"""
W-DIST-001 — Email Distribution Channel
========================================

Sends WINDI Communiqués via SMTP email.

Features:
- HTML + plain text multipart
- Verify URL prominent
- Optional .jmpg attachment
- Trilingual support (DE/EN/PT)

"Um email deixa de ser uma mensagem. Passa a ser um artefacto verificável."

Liga IA+H · Kempten, Bavaria · 2026
"""

import os
import ssl
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment
load_dotenv("/opt/windi/.env")

log = logging.getLogger("w-dist-email")

# SMTP Configuration
SMTP_HOST = os.environ.get("WINDI_SMTP_HOST", "smtp.strato.de")
SMTP_PORT = int(os.environ.get("WINDI_SMTP_PORT", 465))
SMTP_USER = os.environ.get("WINDI_SMTP_USER")
SMTP_PASS = os.environ.get("WINDI_SMTP_PASS")
SMTP_FROM = os.environ.get("WINDI_SMTP_FROM", "noreply@a4desk.de")
SMTP_TLS = os.environ.get("WINDI_SMTP_TLS", "false").lower() == "true"


def get_info() -> dict:
    """Return channel info for router."""
    return {
        "type": "email",
        "smtp_host": SMTP_HOST,
        "configured": bool(SMTP_USER and SMTP_PASS),
        "from": SMTP_FROM
    }


def build_html(communique: dict, lang: str = "de") -> str:
    """
    Build HTML email body.

    Clean, simple HTML that renders in all email clients.
    No JavaScript, no external CSS, inline styles only.
    """
    # Extract fields with fallbacks
    title = (
        communique.get(f"title_{lang}") or
        communique.get("title_de") or
        communique.get("title_en") or
        "WINDI Communiqué"
    )
    receipt_id = (
        communique.get("receipt_id") or
        communique.get("evidence_jmpg_id") or
        "PENDING"
    )
    verify_url = (
        communique.get("evidence_verify_url") or
        f"https://windi-domain.com/verify-public/?id={receipt_id}"
    )
    timestamp = communique.get("sealed_at") or datetime.now(timezone.utc).isoformat()

    # Trilingual strings
    STRINGS = {
        "de": {
            "header": "WINDI Communiqué",
            "sealed": "Dieser Inhalt wurde im Forensic Ledger versiegelt.",
            "moment": "Der erfasste Moment wurde mit überprüfbarer Integrität registriert.",
            "receipt": "Empfangsbeleg",
            "verify": "Authentizität überprüfen",
            "footer": "AI processes. Human decides. WINDI guarantees."
        },
        "en": {
            "header": "WINDI Communiqué",
            "sealed": "This content has been sealed in the Forensic Ledger.",
            "moment": "The captured moment was registered with verifiable integrity.",
            "receipt": "Receipt",
            "verify": "Verify Authenticity",
            "footer": "AI processes. Human decides. WINDI guarantees."
        },
        "pt": {
            "header": "WINDI Communiqué",
            "sealed": "Este conteúdo foi selado no Forensic Ledger.",
            "moment": "O momento capturado foi registado com integridade verificável.",
            "receipt": "Recibo",
            "verify": "Verificar Autenticidade",
            "footer": "AI processes. Human decides. WINDI guarantees."
        }
    }

    s = STRINGS.get(lang, STRINGS["en"])

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: Arial, sans-serif; background-color: #F5F0E0; margin: 0; padding: 20px;">
  <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background-color: #FFFFFF; border-radius: 8px; overflow: hidden;">
    <tr>
      <td style="background-color: #0A0A10; padding: 20px; text-align: center;">
        <h1 style="color: #C9A84C; margin: 0; font-size: 24px;">🔐 {s['header']}</h1>
      </td>
    </tr>
    <tr>
      <td style="padding: 30px;">
        <h2 style="color: #1A1A1A; margin: 0 0 15px 0; font-size: 18px;">{title}</h2>
        <p style="color: #333333; line-height: 1.6; margin: 0 0 20px 0;">
          <strong>{s['sealed']}</strong>
        </p>
        <p style="color: #666666; line-height: 1.6; margin: 0 0 25px 0;">
          {s['moment']}
        </p>
        <hr style="border: none; border-top: 1px solid #E0DED8; margin: 20px 0;">
        <p style="color: #333333; margin: 0 0 10px 0;">
          <strong>{s['receipt']}:</strong><br>
          <code style="background-color: #F5F0E0; padding: 5px 10px; border-radius: 4px; font-family: monospace; font-size: 12px;">{receipt_id}</code>
        </p>
        <p style="margin: 25px 0;">
          <a href="{verify_url}" style="display: inline-block; background-color: #C9A84C; color: #0A0A10; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
            🔐 {s['verify']}
          </a>
        </p>
        <hr style="border: none; border-top: 1px solid #E0DED8; margin: 20px 0;">
        <p style="color: #999999; font-size: 12px; font-style: italic; margin: 0;">
          {s['footer']}
        </p>
        <p style="color: #CCCCCC; font-size: 10px; margin: 10px 0 0 0;">
          {timestamp}
        </p>
      </td>
    </tr>
  </table>
</body>
</html>"""

    return html


def build_text(communique: dict, lang: str = "de") -> str:
    """
    Build plain text fallback for email clients that don't support HTML.
    """
    title = (
        communique.get(f"title_{lang}") or
        communique.get("title_de") or
        communique.get("title_en") or
        "WINDI Communiqué"
    )
    receipt_id = (
        communique.get("receipt_id") or
        communique.get("evidence_jmpg_id") or
        "PENDING"
    )
    verify_url = (
        communique.get("evidence_verify_url") or
        f"https://windi-domain.com/verify-public/?id={receipt_id}"
    )

    STRINGS = {
        "de": {"sealed": "Versiegelt im Forensic Ledger", "verify": "Überprüfen"},
        "en": {"sealed": "Sealed in Forensic Ledger", "verify": "Verify"},
        "pt": {"sealed": "Selado no Forensic Ledger", "verify": "Verificar"}
    }
    s = STRINGS.get(lang, STRINGS["en"])

    text = f"""WINDI Communiqué
================

{title}

{s['sealed']}

Receipt:
{receipt_id}

{s['verify']}:
{verify_url}

---
AI processes. Human decides. WINDI guarantees.
Liga IA+H · Kempten, Bavaria · 2026
"""
    return text


def send(
    communique: dict,
    to: str = None,
    to_email: str = None,
    lang: str = "de",
    attach_jmpg: bool = False,
    **kwargs
) -> dict:
    """
    Send communiqué via email.

    Args:
        communique: Communiqué dict with evidence_* fields
        to: Recipient email address
        to_email: Alias for 'to'
        lang: Language for email content (de/en/pt)
        attach_jmpg: Whether to attach .jmpg file if present

    Returns:
        {success, message_id, to, ...}
    """
    recipient = to or to_email
    if not recipient:
        return {
            "success": False,
            "error": "missing_recipient",
            "message": "No recipient email provided (use 'to' or 'to_email')"
        }

    if not SMTP_USER or not SMTP_PASS:
        return {
            "success": False,
            "error": "smtp_not_configured",
            "message": "SMTP credentials not configured"
        }

    # Build message
    msg = MIMEMultipart("alternative")

    # Extract subject
    title = (
        communique.get(f"title_{lang}") or
        communique.get("title_de") or
        communique.get("title_en") or
        "WINDI Communiqué"
    )
    receipt_id = communique.get("receipt_id") or communique.get("evidence_jmpg_id") or "SEALED"

    msg["Subject"] = f"🔐 WINDI Communiqué: {title[:50]}"
    msg["From"] = SMTP_FROM
    msg["To"] = recipient
    msg["X-WINDI-Receipt"] = receipt_id

    # Attach plain text and HTML
    text_part = MIMEText(build_text(communique, lang), "plain", "utf-8")
    html_part = MIMEText(build_html(communique, lang), "html", "utf-8")

    msg.attach(text_part)
    msg.attach(html_part)

    # Optionally attach .jmpg
    jmpg_path = communique.get("evidence_jmpg_path")
    if attach_jmpg and jmpg_path and os.path.exists(jmpg_path):
        try:
            with open(jmpg_path, "rb") as f:
                jmpg_data = f.read()

            jmpg_filename = os.path.basename(jmpg_path)
            attachment = MIMEBase("application", "octet-stream")
            attachment.set_payload(jmpg_data)
            encoders.encode_base64(attachment)
            attachment.add_header(
                "Content-Disposition",
                f"attachment; filename={jmpg_filename}"
            )
            msg.attach(attachment)
            log.info(f"[W-DIST-EMAIL] Attached JMPG: {jmpg_filename}")
        except Exception as e:
            log.warning(f"[W-DIST-EMAIL] Failed to attach JMPG: {e}")

    # Send via SMTP
    try:
        log.info(f"[W-DIST-EMAIL] Sending to {recipient} via {SMTP_HOST}:{SMTP_PORT}")

        # Use SSL for port 465, STARTTLS for port 587
        if SMTP_PORT == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(SMTP_FROM, [recipient], msg.as_string())
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                if SMTP_TLS:
                    server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(SMTP_FROM, [recipient], msg.as_string())

        log.info(f"[W-DIST-EMAIL] Sent successfully to {recipient}")

        return {
            "success": True,
            "to": recipient,
            "receipt_id": receipt_id,
            "subject": msg["Subject"],
            "lang": lang,
            "jmpg_attached": attach_jmpg and jmpg_path is not None,
            "sent_at": datetime.now(timezone.utc).isoformat()
        }

    except smtplib.SMTPAuthenticationError as e:
        log.error(f"[W-DIST-EMAIL] Authentication failed: {e}")
        return {
            "success": False,
            "error": "auth_failed",
            "message": "SMTP authentication failed"
        }
    except smtplib.SMTPException as e:
        log.error(f"[W-DIST-EMAIL] SMTP error: {e}")
        return {
            "success": False,
            "error": "smtp_error",
            "message": str(e)
        }
    except Exception as e:
        log.error(f"[W-DIST-EMAIL] Unexpected error: {e}")
        return {
            "success": False,
            "error": "exception",
            "message": str(e)
        }


# Module info
__version__ = "1.0.0"
__channel_id__ = "email"
__channel_name__ = "Email Distribution Channel"
