"""
WINDI Distribution Email Module
================================
Sends sealed documents via SMTP using environment configuration.

Configuration via .env:
  WINDI_SMTP_HOST=smtp.strato.de
  WINDI_SMTP_PORT=465
  WINDI_SMTP_USER=noreply@a4desk.de
  WINDI_SMTP_PASS=...
  WINDI_SMTP_FROM=noreply@a4desk.de
"""

import smtplib
import ssl
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv("/opt/windi/.env")
except ImportError:
    pass  # dotenv not installed, rely on system env vars


def get_smtp_config():
    """Load SMTP configuration from environment."""
    return {
        "host": os.environ.get("WINDI_SMTP_HOST", "smtp.strato.de"),
        "port": int(os.environ.get("WINDI_SMTP_PORT", 465)),
        "user": os.environ.get("WINDI_SMTP_USER", ""),
        "password": os.environ.get("WINDI_SMTP_PASS", ""),
        "from_addr": os.environ.get("WINDI_SMTP_FROM", "noreply@a4desk.de"),
    }


def send_document_email(to_address, doc_title, doc_content, receipt_id, lang="en"):
    """
    Send a sealed document via email.

    Args:
        to_address: Recipient email address
        doc_title: Document title for subject line
        doc_content: Plain text content of document
        receipt_id: WINDI receipt ID for forensic reference
        lang: Language code (en, de, pt) for footer text

    Returns:
        dict: {success: bool, to: str, error: str|None, timestamp: str}
    """
    config = get_smtp_config()

    if not config["user"] or not config["password"]:
        return {
            "success": False,
            "to": to_address,
            "error": "SMTP not configured (missing credentials)",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # Build email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[WINDI] {doc_title}"
    msg["From"] = f"WINDI Palette <{config['from_addr']}>"
    msg["To"] = to_address

    # Multilingual footer
    footers = {
        "en": f"Document sealed by WINDI Forensic Ledger.\nReceipt ID: {receipt_id}\n\nVerify: https://windi.app/verify/{receipt_id}",
        "de": f"Dokument versiegelt durch WINDI Forensic Ledger.\nQuittungs-ID: {receipt_id}\n\nVerifizieren: https://windi.app/verify/{receipt_id}",
        "pt": f"Documento selado pelo WINDI Forensic Ledger.\nID do Recibo: {receipt_id}\n\nVerificar: https://windi.app/verify/{receipt_id}"
    }
    footer = footers.get(lang, footers["en"])

    # Plain text version
    text_content = f"{doc_content}\n\n{'─' * 40}\n{footer}"

    # HTML version
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #f9fafb;">
    <div style="background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <!-- Header -->
        <div style="padding: 20px 24px; background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); border-bottom: 3px solid #C5A572;">
            <h1 style="color: #ffffff; margin: 0; font-size: 18px; font-weight: 600;">{doc_title}</h1>
        </div>

        <!-- Content -->
        <div style="padding: 24px; white-space: pre-wrap; line-height: 1.6; color: #1a1a1a; font-size: 14px;">
{doc_content}
        </div>

        <!-- Forensic Footer -->
        <div style="padding: 16px 24px; background: #f3f4f6; border-top: 1px solid #e5e7eb;">
            <table style="width: 100%;">
                <tr>
                    <td style="vertical-align: top;">
                        <div style="font-size: 11px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">WINDI Forensic Seal</div>
                        <div style="font-family: 'JetBrains Mono', 'Fira Code', monospace; font-size: 12px; color: #1a1a1a;">{receipt_id}</div>
                    </td>
                    <td style="text-align: right; vertical-align: top;">
                        <a href="https://windi.app/verify/{receipt_id}" style="display: inline-block; padding: 8px 16px; background: #C5A572; color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 12px; font-weight: 600;">Verify</a>
                    </td>
                </tr>
            </table>
        </div>
    </div>

    <div style="text-align: center; padding: 16px; font-size: 11px; color: #9ca3af;">
        Sent via WINDI Palette · AI processes. Human decides.
    </div>
</body>
</html>"""

    msg.attach(MIMEText(text_content, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    # Send via SMTP
    try:
        context = ssl.create_default_context()

        if config["port"] == 465:
            # SSL from start (SMTPS)
            with smtplib.SMTP_SSL(config["host"], config["port"], context=context, timeout=30) as server:
                server.login(config["user"], config["password"])
                server.sendmail(config["from_addr"], to_address, msg.as_string())
        else:
            # STARTTLS
            with smtplib.SMTP(config["host"], config["port"], timeout=30) as server:
                server.starttls(context=context)
                server.login(config["user"], config["password"])
                server.sendmail(config["from_addr"], to_address, msg.as_string())

        return {
            "success": True,
            "to": to_address,
            "error": None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except smtplib.SMTPAuthenticationError as e:
        return {
            "success": False,
            "to": to_address,
            "error": f"SMTP authentication failed: {e}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except smtplib.SMTPException as e:
        return {
            "success": False,
            "to": to_address,
            "error": f"SMTP error: {e}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "to": to_address,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Quick test when run directly
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv("/opt/windi/.env")

    config = get_smtp_config()
    print(f"SMTP Config: {config['host']}:{config['port']} as {config['user']}")
    print(f"From: {config['from_addr']}")
    print(f"Password configured: {'Yes' if config['password'] else 'No'}")
