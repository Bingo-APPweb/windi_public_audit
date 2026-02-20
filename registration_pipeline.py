#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
WINDI Registration Pipeline v1.0.0
═══════════════════════════════════════════════════════════════════════════════
Extension for ID Genesis (FastAPI, port 8096)

Completes the chain:
  Landing Page → Lead Capture → SMTP Verification → Token Click →
  WALLET Creation → Welcome Email → a4Desk Desktop

"KI verarbeitet. Mensch entscheidet. WINDI garantiert."

Deployment: /opt/windi/id-genesis/registration_pipeline.py
Import into ID Genesis main app: from registration_pipeline import router as reg_router
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import json
import hashlib
import secrets
import sqlite3
import smtplib
import ssl
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, formatdate
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

# ─── Configuration ────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DB_PATH = os.environ.get("REG_DB_PATH", "/opt/windi/data/windi_registration.db")
LOG_FILE = "/opt/windi/logs/registration.log"
BASE_URL = os.environ.get("BASE_URL", "https://admin.windia4desk.tech")

# SMTP Config — Strato
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.strato.de")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER = os.environ.get("SMTP_USER", "info@a4desk.de")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
SMTP_FROM_NAME = os.environ.get("SMTP_FROM_NAME", "a4Desk by WINDI")
SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", "noreply@a4desk.de")

VERIFICATION_EXPIRY_HOURS = 48
MAX_EMAILS_PER_HOUR = 50

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [REG] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("registration")

# ─── FastAPI Router ───────────────────────────────────────────
router = APIRouter(prefix="/api", tags=["registration"])


# ─── Pydantic Models ─────────────────────────────────────────

class LeadRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=200)
    company: Optional[str] = Field(default="", max_length=200)
    interest: Optional[str] = Field(default="", max_length=500)
    lang: Optional[str] = Field(default="de", pattern="^(de|en|pt)$")
    source: Optional[str] = Field(default="a4desk-landing-v2")
    timestamp: Optional[str] = None

class LeadResponse(BaseModel):
    status: str
    lead_id: str
    message: str
    timestamp: str
    verification_sent: bool = False

class WalletInfo(BaseModel):
    wallet_id: str
    wallet_type: str  # "human" or "company"
    name: str
    email: str
    company: Optional[str] = ""
    created_at: str


# ─── Database ─────────────────────────────────────────────────

def get_db():
    """Get database connection with row factory."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize registration database tables."""
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        company TEXT DEFAULT '',
        interest TEXT DEFAULT '',
        lang TEXT DEFAULT 'de',
        source TEXT DEFAULT '',
        status TEXT DEFAULT 'pending',
        registration_type TEXT DEFAULT 'human',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        verified_at TIMESTAMP DEFAULT NULL,
        wallet_id TEXT DEFAULT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS verification_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id TEXT NOT NULL,
        email TEXT NOT NULL,
        token TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        used_at TIMESTAMP DEFAULT NULL,
        FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS wallets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        wallet_id TEXT UNIQUE NOT NULL,
        wallet_type TEXT NOT NULL DEFAULT 'human',
        lead_id TEXT NOT NULL,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        company TEXT DEFAULT '',
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_access TIMESTAMP DEFAULT NULL,
        virtue_receipts INTEGER DEFAULT 0,
        FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS email_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient TEXT NOT NULL,
        email_type TEXT NOT NULL,
        status TEXT DEFAULT 'sent',
        error TEXT DEFAULT NULL,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        hash TEXT NOT NULL
    )''')

    c.execute('CREATE INDEX IF NOT EXISTS idx_lead_email ON leads(email)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_token ON verification_tokens(token)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_wallet_email ON wallets(email)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_wallet_id ON wallets(wallet_id)')

    conn.commit()
    conn.close()
    logger.info("Registration database initialized")


# Initialize on import
init_db()


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.post("/leads", response_model=LeadResponse)
async def capture_lead(lead: LeadRequest):
    """
    Enhanced lead capture with email verification.
    Replaces the simple lead capture with full pipeline:
    1. Validate + Store lead
    2. Detect registration type (Human vs Company)
    3. Generate verification token
    4. Send verification email via Strato SMTP
    """
    now = datetime.now(timezone.utc)
    lead_id = f"LEAD-{now.strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)}"

    # Detect registration type
    reg_type = "company" if lead.company and len(lead.company.strip()) > 1 else "human"

    conn = get_db()
    c = conn.cursor()

    # Check for duplicate email (already verified)
    c.execute('SELECT lead_id, status, wallet_id FROM leads WHERE email = ? AND status = ?',
              (lead.email, 'verified'))
    existing = c.fetchone()
    if existing:
        conn.close()
        return LeadResponse(
            status="already_registered",
            lead_id=existing['lead_id'],
            message=_msg("already_registered", lead.lang or "de"),
            timestamp=now.isoformat(),
            verification_sent=False
        )

    # Check for pending verification (resend if expired)
    c.execute('SELECT lead_id FROM leads WHERE email = ? AND status = ?',
              (lead.email, 'pending'))
    pending = c.fetchone()
    if pending:
        # Resend verification
        lead_id = pending['lead_id']
        logger.info(f"Resending verification for {lead.email} (lead: {lead_id})")
    else:
        # New lead
        c.execute('''INSERT INTO leads
            (lead_id, name, email, company, interest, lang, source, registration_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (lead_id, lead.name, lead.email, lead.company or '',
             lead.interest or '', lead.lang or 'de', lead.source or '', reg_type)
        )
        conn.commit()
        logger.info(f"New lead captured: {lead_id} ({reg_type}) - {lead.email}")

    conn.close()

    # Generate token and send verification email
    verification_sent = False
    if SMTP_PASS:  # Only send if SMTP is configured
        try:
            token = _generate_token(lead_id, lead.email)
            verification_sent = _send_verification_email(
                to_email=lead.email,
                name=lead.name,
                company=lead.company or '',
                token=token,
                lang=lead.lang or 'de',
                reg_type=reg_type
            )
        except Exception as e:
            logger.error(f"Email send failed for {lead.email}: {e}")
    else:
        logger.warning("SMTP_PASS not configured — verification email not sent")

    return LeadResponse(
        status="received",
        lead_id=lead_id,
        message=_msg("received", lead.lang or "de"),
        timestamp=now.isoformat(),
        verification_sent=verification_sent
    )


@router.get("/verify", response_class=HTMLResponse)
async def verify_email(token: str = Query(...)):
    """
    Email verification endpoint.
    User clicks the link in their email → token validated → WALLET created.
    """
    conn = get_db()
    c = conn.cursor()

    # Find token
    c.execute('''SELECT vt.id, vt.lead_id, vt.email, vt.expires_at, vt.used_at,
                        l.name, l.company, l.lang, l.registration_type
                 FROM verification_tokens vt
                 JOIN leads l ON l.lead_id = vt.lead_id
                 WHERE vt.token = ?''', (token,))
    row = c.fetchone()

    if not row:
        conn.close()
        return _verification_page("error", "invalid", "de")

    if row['used_at']:
        conn.close()
        return _verification_page("already_verified", "used", row['lang'] or 'de',
                                   name=row['name'])

    if datetime.fromisoformat(row['expires_at']) < datetime.now(timezone.utc):
        conn.close()
        return _verification_page("error", "expired", row['lang'] or 'de')

    # ✅ Token valid — Create WALLET
    now = datetime.now(timezone.utc)
    wallet_type = row['registration_type'] or 'human'
    wallet_prefix = "WDI-H" if wallet_type == "human" else "WDI-C"
    wallet_id = f"{wallet_prefix}-{now.strftime('%Y%m%d')}-{secrets.token_hex(2)}"

    # Mark token as used
    c.execute('UPDATE verification_tokens SET used_at = ? WHERE id = ?',
              (now.isoformat(), row['id']))

    # Update lead status
    c.execute('UPDATE leads SET status = ?, verified_at = ?, wallet_id = ? WHERE lead_id = ?',
              ('verified', now.isoformat(), wallet_id, row['lead_id']))

    # Create WALLET
    c.execute('''INSERT INTO wallets
        (wallet_id, wallet_type, lead_id, name, email, company)
        VALUES (?, ?, ?, ?, ?, ?)''',
        (wallet_id, wallet_type, row['lead_id'],
         row['name'], row['email'], row['company'] or '')
    )

    conn.commit()
    conn.close()

    logger.info(f"WALLET created: {wallet_id} ({wallet_type}) for {row['email']}")

    # Send welcome email
    if SMTP_PASS:
        try:
            _send_welcome_email(
                to_email=row['email'],
                name=row['name'],
                company=row['company'] or '',
                wallet_id=wallet_id,
                lang=row['lang'] or 'de',
                reg_type=wallet_type
            )
        except Exception as e:
            logger.error(f"Welcome email failed for {row['email']}: {e}")

    return _verification_page("success", "verified", row['lang'] or 'de',
                               name=row['name'], wallet_id=wallet_id)


@router.get("/leads/stats")
async def leads_stats():
    """Return lead capture and registration statistics."""
    conn = get_db()
    c = conn.cursor()

    stats = {}

    c.execute('SELECT COUNT(*) as total FROM leads')
    stats['total_leads'] = c.fetchone()['total']

    c.execute('SELECT status, COUNT(*) as count FROM leads GROUP BY status')
    stats['by_status'] = {row['status']: row['count'] for row in c.fetchall()}

    c.execute('SELECT registration_type, COUNT(*) as count FROM leads GROUP BY registration_type')
    stats['by_type'] = {row['registration_type']: row['count'] for row in c.fetchall()}

    c.execute('SELECT COUNT(*) as total FROM wallets')
    stats['total_wallets'] = c.fetchone()['total']

    c.execute('SELECT wallet_type, COUNT(*) as count FROM wallets GROUP BY wallet_type')
    stats['wallets_by_type'] = {row['wallet_type']: row['count'] for row in c.fetchall()}

    c.execute('SELECT COUNT(*) as total FROM email_log WHERE status = "sent"')
    stats['emails_sent'] = c.fetchone()['total']

    c.execute('''SELECT COUNT(*) as total FROM verification_tokens 
                 WHERE used_at IS NULL AND expires_at > ?''',
              (datetime.now(timezone.utc).isoformat(),))
    stats['pending_verifications'] = c.fetchone()['total']

    conn.close()

    return {
        "service": "WINDI Registration Pipeline",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stats": stats
    }


@router.get("/wallets")
async def list_wallets():
    """List all created WALLETs."""
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT wallet_id, wallet_type, name, email, company, status, 
                        created_at, virtue_receipts
                 FROM wallets ORDER BY created_at DESC LIMIT 50''')
    wallets = [dict(row) for row in c.fetchall()]
    conn.close()
    return {"wallets": wallets, "count": len(wallets)}


@router.get("/wallet/{wallet_id}")
async def get_wallet(wallet_id: str):
    """Get WALLET details by ID."""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM wallets WHERE wallet_id = ?', (wallet_id,))
    wallet = c.fetchone()
    conn.close()

    if not wallet:
        raise HTTPException(status_code=404, detail="WALLET not found")
    return dict(wallet)


# ═══════════════════════════════════════════════════════════════
# SMTP — Email Sending
# ═══════════════════════════════════════════════════════════════

def _send_email(to_email: str, subject: str, html_body: str, email_type: str) -> bool:
    """Send email via Strato SMTP (SSL on port 465)."""
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = formataddr((SMTP_FROM_NAME, SMTP_FROM_EMAIL))
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["Date"] = formatdate(localtime=True)
        msg["X-WINDI-System"] = "a4Desk Document Governance Intelligence"
        msg["Reply-To"] = "info@a4desk.de"

        # Plain text fallback
        import re
        text = re.sub(r'<br\s*/?>', '\n', html_body)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&bull;', '*', text)

        msg.attach(MIMEText(text.strip(), "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Strato uses SSL on port 465
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_FROM_EMAIL, to_email, msg.as_string())

        _log_email(to_email, email_type, "sent")
        logger.info(f"Email sent to {to_email}: {subject}")
        return True

    except Exception as e:
        logger.error(f"SMTP error sending to {to_email}: {e}")
        _log_email(to_email, email_type, "error", str(e))
        return False


def _generate_token(lead_id: str, email: str) -> str:
    """Generate secure verification token."""
    token = secrets.token_urlsafe(48)
    expires = datetime.now(timezone.utc) + timedelta(hours=VERIFICATION_EXPIRY_HOURS)

    conn = get_db()
    c = conn.cursor()
    # Invalidate old tokens for this lead
    c.execute('UPDATE verification_tokens SET used_at = ? WHERE lead_id = ? AND used_at IS NULL',
              (datetime.now(timezone.utc).isoformat(), lead_id))
    # Create new token
    c.execute('INSERT INTO verification_tokens (lead_id, email, token, expires_at) VALUES (?, ?, ?, ?)',
              (lead_id, email, token, expires.isoformat()))
    conn.commit()
    conn.close()
    return token


def _send_verification_email(to_email: str, name: str, company: str,
                              token: str, lang: str, reg_type: str) -> bool:
    """Send verification email with Noir+Gold template."""
    verify_url = f"{BASE_URL}/clone/verify?token={token}"

    subjects = {
        "de": "Bitte bestätigen Sie Ihre E-Mail — a4Desk",
        "en": "Please verify your email — a4Desk",
        "pt": "Confirme seu e-mail — a4Desk",
    }

    greetings = {"de": f"Hallo {name},", "en": f"Hello {name},", "pt": f"Olá {name},"}

    if reg_type == "company" and company:
        messages = {
            "de": f'vielen Dank für die Registrierung von <strong>{company}</strong> bei a4Desk.<br>'
                  f'Bitte bestätigen Sie Ihre E-Mail-Adresse, um Ihr Unternehmens-WALLET zu erstellen.',
            "en": f'thank you for registering <strong>{company}</strong> with a4Desk.<br>'
                  f'Please verify your email to create your company WALLET.',
            "pt": f'obrigado por registrar <strong>{company}</strong> no a4Desk.<br>'
                  f'Confirme seu e-mail para criar o WALLET da empresa.',
        }
    else:
        messages = {
            "de": f'vielen Dank für Ihre Registrierung bei a4Desk.<br>'
                  f'Bitte bestätigen Sie Ihre E-Mail-Adresse, um Ihr persönliches WALLET zu erstellen.',
            "en": f'thank you for registering with a4Desk.<br>'
                  f'Please verify your email to create your personal WALLET.',
            "pt": f'obrigado por se registrar no a4Desk.<br>'
                  f'Confirme seu e-mail para criar seu WALLET pessoal.',
        }

    buttons = {"de": "E-Mail bestätigen →", "en": "Verify Email →", "pt": "Confirmar E-mail →"}
    notes = {
        "de": f"Dieser Link ist {VERIFICATION_EXPIRY_HOURS} Stunden gültig.",
        "en": f"This link is valid for {VERIFICATION_EXPIRY_HOURS} hours.",
        "pt": f"Este link é válido por {VERIFICATION_EXPIRY_HOURS} horas.",
    }
    disclaimers = {
        "de": "Falls Sie diese Registrierung nicht vorgenommen haben, ignorieren Sie diese E-Mail.",
        "en": "If you did not register, please ignore this email.",
        "pt": "Se você não se registrou, ignore este e-mail.",
    }

    html = _email_template(
        greeting=greetings.get(lang, greetings["de"]),
        message=messages.get(lang, messages["de"]),
        button_url=verify_url,
        button_text=buttons.get(lang, buttons["de"]),
        note=notes.get(lang, notes["de"]),
        disclaimer=disclaimers.get(lang, disclaimers["de"]),
        lang=lang
    )

    return _send_email(to_email, subjects.get(lang, subjects["de"]), html, "verification")


def _send_welcome_email(to_email: str, name: str, company: str,
                         wallet_id: str, lang: str, reg_type: str) -> bool:
    """Send welcome email with WALLET ID."""
    desk_url = f"{BASE_URL}/clone/app/"

    subjects = {
        "de": "Willkommen bei a4Desk — Ihr WALLET ist bereit",
        "en": "Welcome to a4Desk — Your WALLET is ready",
        "pt": "Bem-vindo ao a4Desk — Seu WALLET está pronto",
    }

    greetings = {"de": f"Willkommen, {name}!", "en": f"Welcome, {name}!", "pt": f"Bem-vindo, {name}!"}

    wallet_html = (f'<span style="color:#C9A84C;">WALLET-ID:</span> '
                   f'<code style="background:#2A2A2A;padding:4px 10px;border-radius:4px;'
                   f'color:#E8D48B;font-family:monospace;font-size:14px;">{wallet_id}</code>')

    if reg_type == "company" and company:
        messages = {
            "de": f'Ihr Unternehmens-WALLET für <strong>{company}</strong> wurde erstellt.<br><br>'
                  f'{wallet_html}<br><br>'
                  f'Sie können jetzt Ihre Dokumente mit KI-gestützter Governance analysieren — '
                  f'bevor eine einzige Unterschrift gesetzt wird.',
            "en": f'Your company WALLET for <strong>{company}</strong> has been created.<br><br>'
                  f'{wallet_html}<br><br>'
                  f'You can now analyze your documents with AI-powered governance — '
                  f'before a single signature is placed.',
            "pt": f'O WALLET da empresa <strong>{company}</strong> foi criado.<br><br>'
                  f'{wallet_html}<br><br>'
                  f'Agora você pode analisar seus documentos com governança IA — '
                  f'antes que uma única assinatura seja feita.',
        }
    else:
        messages = {
            "de": f'Ihr persönliches WALLET wurde erstellt.<br><br>'
                  f'{wallet_html}<br><br>'
                  f'Sie können jetzt Ihre Dokumente mit KI-gestützter Governance analysieren.',
            "en": f'Your personal WALLET has been created.<br><br>'
                  f'{wallet_html}<br><br>'
                  f'You can now analyze your documents with AI-powered governance.',
            "pt": f'Seu WALLET pessoal foi criado.<br><br>'
                  f'{wallet_html}<br><br>'
                  f'Agora você pode analisar seus documentos com governança IA.',
        }

    buttons = {"de": "Zum a4Desk →", "en": "Go to a4Desk →", "pt": "Ir para o a4Desk →"}
    features = {
        "de": "✔ Document Governance Intelligence &nbsp; ✔ eIDAS-konform &nbsp; ✔ DSGVO by Design &nbsp; ✔ Made in Germany",
        "en": "✔ Document Governance Intelligence &nbsp; ✔ eIDAS-compliant &nbsp; ✔ GDPR by Design &nbsp; ✔ Made in Germany",
        "pt": "✔ Document Governance Intelligence &nbsp; ✔ eIDAS-compatível &nbsp; ✔ LGPD by Design &nbsp; ✔ Made in Germany",
    }

    html = _email_template(
        greeting=greetings.get(lang, greetings["de"]),
        message=messages.get(lang, messages["de"]),
        button_url=desk_url,
        button_text=buttons.get(lang, buttons["de"]),
        note=features.get(lang, features["de"]),
        lang=lang
    )

    return _send_email(to_email, subjects.get(lang, subjects["de"]), html, "welcome")


# ═══════════════════════════════════════════════════════════════
# HTML Templates
# ═══════════════════════════════════════════════════════════════

def _email_template(greeting: str, message: str, button_url: str = "",
                     button_text: str = "", note: str = "", disclaimer: str = "",
                     lang: str = "de") -> str:
    """Noir+Gold email template — compatible with all email clients."""
    motto = {
        "de": "KI verarbeitet. Mensch entscheidet. WINDI garantiert.",
        "en": "AI processes. Human decides. WINDI guarantees.",
        "pt": "IA processa. Humano decide. WINDI garante.",
    }

    btn_block = ""
    if button_url:
        btn_block = f'''<tr><td align="center" style="padding:24px 0 16px;">
            <table><tr><td style="border-radius:8px;background:#C9A84C;">
            <a href="{button_url}" target="_blank" style="display:inline-block;padding:14px 36px;
            font-family:Helvetica,Arial,sans-serif;font-size:16px;font-weight:bold;color:#0A0A0A;
            text-decoration:none;border-radius:8px;">{button_text}</a>
            </td></tr></table></td></tr>'''

    note_block = f'<tr><td style="padding:8px 0;color:#8B7633;font-size:12px;text-align:center;font-family:Helvetica,Arial,sans-serif;">{note}</td></tr>' if note else ""
    disc_block = f'<tr><td style="padding:4px 0;color:#666;font-size:11px;text-align:center;font-family:Helvetica,Arial,sans-serif;">{disclaimer}</td></tr>' if disclaimer else ""

    return f'''<!DOCTYPE html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#0A0A0A;font-family:Helvetica,Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0A0A0A;"><tr><td align="center" style="padding:24px 16px;">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#121212;border:1px solid #2A2A2A;border-radius:12px;overflow:hidden;">
<tr><td style="height:3px;background:linear-gradient(90deg,#8B7633,#C9A84C,#8B7633);"></td></tr>
<tr><td align="center" style="padding:32px 40px 16px;"><span style="font-size:24px;font-weight:bold;color:#F0EDE6;">a4<span style="color:#C9A84C;">Desk</span></span><br><span style="font-family:monospace;font-size:10px;color:#8B7633;letter-spacing:3px;">DOCUMENT GOVERNANCE INTELLIGENCE</span></td></tr>
<tr><td style="padding:0 40px;"><div style="height:1px;background:#2A2A2A;"></div></td></tr>
<tr><td style="padding:28px 40px;"><table width="100%" cellpadding="0" cellspacing="0">
<tr><td style="font-size:18px;font-weight:bold;color:#C9A84C;padding-bottom:16px;">{greeting}</td></tr>
<tr><td style="font-size:15px;line-height:24px;color:#F0EDE6;padding-bottom:8px;">{message}</td></tr>
{btn_block}{note_block}{disc_block}
</table></td></tr>
<tr><td style="padding:0 40px;"><div style="height:1px;background:#2A2A2A;"></div></td></tr>
<tr><td align="center" style="padding:20px 40px 12px;"><div style="font-size:11px;color:#8B7633;font-style:italic;">{motto.get(lang, motto["de"])}</div></td></tr>
<tr><td align="center" style="padding:0 40px 20px;"><div style="font-size:10px;color:#555;">WINDI Publishing House &bull; Kempten (Allg&auml;u) &bull; Bavaria, Germany<br><a href="{BASE_URL}/clone/#legal-impressum" style="color:#8B7633;text-decoration:none;">Impressum</a> &bull; <a href="{BASE_URL}/clone/#legal-datenschutz" style="color:#8B7633;text-decoration:none;">Datenschutz</a></div></td></tr>
<tr><td style="height:3px;background:linear-gradient(90deg,#8B7633,#C9A84C,#8B7633);"></td></tr>
</table></td></tr></table></body></html>'''


def _verification_page(status: str, reason: str, lang: str,
                        name: str = "", wallet_id: str = "") -> str:
    """Render verification result page in WINDI Noir+Gold style."""
    titles = {
        "success": {"de": "E-Mail bestätigt!", "en": "Email Verified!", "pt": "E-mail Confirmado!"},
        "already_verified": {"de": "Bereits bestätigt", "en": "Already Verified", "pt": "Já Confirmado"},
        "error": {"de": "Verifizierung fehlgeschlagen", "en": "Verification Failed", "pt": "Verificação Falhou"},
    }

    messages_map = {
        "success": {
            "de": f'Ihr WALLET wurde erstellt!<br><br><span style="color:#C9A84C;">WALLET-ID:</span> <code style="background:#2A2A2A;padding:6px 14px;border-radius:6px;color:#E8D48B;font-size:16px;">{wallet_id}</code><br><br>Sie können sich jetzt bei a4Desk anmelden.',
            "en": f'Your WALLET has been created!<br><br><span style="color:#C9A84C;">WALLET ID:</span> <code style="background:#2A2A2A;padding:6px 14px;border-radius:6px;color:#E8D48B;font-size:16px;">{wallet_id}</code><br><br>You can now sign in to a4Desk.',
            "pt": f'Seu WALLET foi criado!<br><br><span style="color:#C9A84C;">WALLET ID:</span> <code style="background:#2A2A2A;padding:6px 14px;border-radius:6px;color:#E8D48B;font-size:16px;">{wallet_id}</code><br><br>Agora você pode entrar no a4Desk.',
        },
        "already_verified": {
            "de": f'{name}, Ihre E-Mail wurde bereits bestätigt. Bitte melden Sie sich an.',
            "en": f'{name}, your email has already been verified. Please sign in.',
            "pt": f'{name}, seu e-mail já foi confirmado. Faça login.',
        },
        "invalid": {
            "de": 'Dieser Bestätigungslink ist ungültig. Bitte registrieren Sie sich erneut.',
            "en": 'This verification link is invalid. Please register again.',
            "pt": 'Este link de verificação é inválido. Registre-se novamente.',
        },
        "expired": {
            "de": 'Dieser Link ist abgelaufen. Bitte registrieren Sie sich erneut.',
            "en": 'This link has expired. Please register again.',
            "pt": 'Este link expirou. Registre-se novamente.',
        },
    }

    title = titles.get(status, titles["error"]).get(lang, "Error")
    msg_key = reason if reason in messages_map else status
    message = messages_map.get(msg_key, messages_map["invalid"]).get(lang, "Error")

    icon = "✅" if status == "success" else "ℹ️" if status == "already_verified" else "❌"
    btn_label = {"de": "Zum a4Desk →", "en": "Go to a4Desk →", "pt": "Ir para o a4Desk →"}.get(lang, "Go →")
    btn_url = f"{BASE_URL}/clone/app/"
    back_label = {"de": "Zurück zur Startseite", "en": "Back to Homepage", "pt": "Voltar à Página Inicial"}.get(lang, "Back")

    motto = {
        "de": "KI verarbeitet. Mensch entscheidet. WINDI garantiert.",
        "en": "AI processes. Human decides. WINDI guarantees.",
        "pt": "IA processa. Humano decide. WINDI garante.",
    }

    return f'''<!DOCTYPE html><html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>a4Desk — {title}</title>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;700;800&family=Outfit:wght@300;400;500&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0A0A0F;color:#F0EDE6;font-family:'Outfit',sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px}}
.card{{max-width:520px;width:100%;background:#121218;border:1px solid #2A2A38;border-radius:16px;overflow:hidden;text-align:center}}
.gold-bar{{height:3px;background:linear-gradient(90deg,#8B7633,#C9A84C,#8B7633)}}
.icon{{font-size:48px;padding-top:40px}}
h1{{font-family:'Bricolage Grotesque',sans-serif;font-size:28px;font-weight:800;color:#C9A84C;padding:16px 40px 0}}
.msg{{font-size:15px;line-height:24px;color:#F0EDE6;padding:16px 40px 24px}}
.btn{{display:inline-block;padding:14px 36px;background:#C9A84C;color:#0A0A0A;text-decoration:none;font-weight:600;font-size:16px;border-radius:8px;margin-bottom:12px}}
.btn:hover{{background:#E8D48B}}
.back{{display:block;color:#8B7633;text-decoration:none;font-size:13px;padding-bottom:24px}}
.back:hover{{color:#C9A84C}}
.footer{{padding:16px 40px 20px;border-top:1px solid #2A2A38}}
.footer p{{font-size:11px;color:#8B7633;font-style:italic}}
.footer small{{font-size:10px;color:#555;display:block;margin-top:6px}}
code{{font-family:'JetBrains Mono',monospace}}
</style></head><body>
<div class="card">
<div class="gold-bar"></div>
<div class="icon">{icon}</div>
<h1>{title}</h1>
<div class="msg">{message}</div>
{"<a href='" + btn_url + "' class='btn'>" + btn_label + "</a>" if status in ("success", "already_verified") else ""}
<a href="{BASE_URL}/clone/" class="back">{back_label}</a>
<div class="footer">
<p>{motto.get(lang, motto["de"])}</p>
<small>a4Desk by WINDI &bull; Kempten (Allgäu) &bull; Bavaria</small>
</div>
<div class="gold-bar"></div>
</div></body></html>'''


# ═══════════════════════════════════════════════════════════════
# Utilities
# ═══════════════════════════════════════════════════════════════

def _msg(key: str, lang: str) -> str:
    """Get trilingual message."""
    messages = {
        "received": {
            "de": "Vielen Dank! Bitte prüfen Sie Ihre E-Mail zur Bestätigung.",
            "en": "Thank you! Please check your email for verification.",
            "pt": "Obrigado! Verifique seu e-mail para confirmação.",
        },
        "already_registered": {
            "de": "Diese E-Mail ist bereits registriert. Bitte melden Sie sich an.",
            "en": "This email is already registered. Please sign in.",
            "pt": "Este e-mail já está registrado. Faça login.",
        },
    }
    return messages.get(key, {}).get(lang, messages.get(key, {}).get("de", ""))


def _log_email(recipient: str, email_type: str, status: str, error: str = None):
    """Log email send attempt."""
    email_hash = hashlib.sha256(
        f"{recipient}:{email_type}:{datetime.now(timezone.utc).isoformat()}".encode()
    ).hexdigest()[:16]

    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('INSERT INTO email_log (recipient, email_type, status, error, hash) VALUES (?, ?, ?, ?, ?)',
                  (recipient, email_type, status, error, email_hash))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to log email: {e}")


# ═══════════════════════════════════════════════════════════════
# Integration Helper
# ═══════════════════════════════════════════════════════════════

def integrate_with_app(app):
    """
    Call this from ID Genesis main app to integrate the registration pipeline.
    
    Usage in id_genesis main app:
        from registration_pipeline import integrate_with_app
        integrate_with_app(app)
    """
    app.include_router(router)
    logger.info("Registration Pipeline integrated with ID Genesis")


if __name__ == "__main__":
    """Standalone mode for testing."""
    import uvicorn
    from fastapi import FastAPI

    app = FastAPI(
        title="WINDI Registration Pipeline",
        version="1.0.0",
        description="Lead capture, email verification, and WALLET creation"
    )
    app.include_router(router)

    # Health endpoint
    @app.get("/health")
    async def health():
        return {
            "service": "WINDI Registration Pipeline",
            "version": "1.0.0",
            "status": "healthy",
            "smtp_configured": bool(SMTP_PASS),
            "principle": "KI verarbeitet. Mensch entscheidet. WINDI garantiert."
        }

    port = int(os.environ.get("PORT", "8096"))
    uvicorn.run(app, host="0.0.0.0", port=port)
