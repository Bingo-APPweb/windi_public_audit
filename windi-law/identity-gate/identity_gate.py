"""
WINDI-LAW Identity Gate v1.0.0
Port: :8122
Sovereign Identity Management for Legal Professionals

Liga IA+H · Kempten, Bavaria · 2026
"AI processes. Human decides. WINDI guarantees."
"""

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, field_validator
import re
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import sqlite3
import uuid
import secrets
import hashlib
import base64
import requests
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv("/opt/windi/windi-law/identity-gate/.env")
except ImportError:
    pass  # dotenv not installed, rely on system env vars

# Ed25519 cryptography
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════

DB_PATH = "/opt/windi/windi-law/identity-gate/windi_law_identity.db"
LEDGER_URL = "http://127.0.0.1:8101/api/receipts"
VERSION = "v1.2.0"

# Admin secret for verification (from environment)
ADMIN_SECRET = os.environ.get("WINDI_ADMIN_SECRET", "windi-law-admin-2026")

# Email verification settings
EMAIL_VERIFY_HOURS = 48  # Hours before downgrade to EMAIL_PENDING
EMAIL_FROM = os.environ.get("WINDI_EMAIL_FROM", "noreply@windi-domain.com")
DOMAIN_URL = os.environ.get("WINDI_DOMAIN_URL", "https://windi-domain.com")

# SMTP Configuration (Strato)
SMTP_HOST = os.environ.get("WINDI_SMTP_HOST", "smtp.strato.de")
SMTP_PORT = int(os.environ.get("WINDI_SMTP_PORT", "465"))
SMTP_USER = os.environ.get("WINDI_SMTP_USER", "")
SMTP_PASS = os.environ.get("WINDI_SMTP_PASS", "")

# Identity states
STATE_UNBORN = "UNBORN"
STATE_PROVISIONAL = "PROVISIONAL"
STATE_VERIFIED = "VERIFIED"
STATE_EMAIL_PENDING = "EMAIL_PENDING"  # Email not verified after 48h
STATE_SUSPENDED = "SUSPENDED"
STATE_REVOKED = "REVOKED"

# ═══════════════════════════════════════════════════════════════
# HOST-AWARE ROUTING (windilaw.de vs windi-domain.com/law/)
# ═══════════════════════════════════════════════════════════════

def get_base_path(request: Request) -> str:
    """
    Returns '' for windilaw.de, '/law' for windi-domain.com
    X-Forwarded-Host has priority (nginx proxy)
    """
    host = request.headers.get("host", "")
    forwarded = request.headers.get("x-forwarded-host", "")
    effective_host = forwarded or host
    if "windilaw.de" in effective_host:
        return ""
    return "/law"

# ═══════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════

class CompanyRegister(BaseModel):
    legal_name: str
    country: str
    vat_number: Optional[str] = None
    type: str  # law_firm, corporation, individual
    admin_name: str
    admin_email: str

    @field_validator('admin_email')
    @classmethod
    def validate_email(cls, v):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email format')
        return v


class WalletCreate(BaseModel):
    admin_id: str


class KeysGenerate(BaseModel):
    admin_id: str
    is_dev: bool = False
    scope: List[str] = ["verify", "seal"]


class ConsentSign(BaseModel):
    admin_id: str
    consent_ledger: bool
    consent_ai: bool
    eu_ai_act_art14: bool


class IdentityVerify(BaseModel):
    did: str


# ═══════════════════════════════════════════════════════════════
# DATABASE INITIALIZATION
# ═══════════════════════════════════════════════════════════════

def init_db():
    """Initialize SQLite database with required schema."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id          TEXT PRIMARY KEY,
            legal_name  TEXT NOT NULL,
            country     TEXT NOT NULL,
            vat_number  TEXT,
            type        TEXT CHECK(type IN ('law_firm','corporation','individual')),
            state       TEXT DEFAULT 'PROVISIONAL',
            created_at  TEXT NOT NULL,
            ledger_receipt TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id          TEXT PRIMARY KEY,
            company_id  TEXT REFERENCES companies(id),
            full_name   TEXT NOT NULL,
            email       TEXT UNIQUE NOT NULL,
            role        TEXT DEFAULT 'admin',
            did         TEXT UNIQUE,
            public_key  TEXT,
            fingerprint TEXT,
            state       TEXT DEFAULT 'PROVISIONAL',
            created_at  TEXT NOT NULL,
            email_verified INTEGER DEFAULT 0,
            email_token TEXT,
            email_token_expires TEXT
        )
    """)

    # Migration: Add email verification columns if they don't exist
    try:
        cursor.execute("ALTER TABLE admins ADD COLUMN email_verified INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Column already exists
    try:
        cursor.execute("ALTER TABLE admins ADD COLUMN email_token TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE admins ADD COLUMN email_token_expires TEXT")
    except sqlite3.OperationalError:
        pass

    # §LOGIN: Add login token columns for magic link authentication
    try:
        cursor.execute("ALTER TABLE admins ADD COLUMN login_token TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE admins ADD COLUMN login_token_expires TEXT")
    except sqlite3.OperationalError:
        pass

    # §120.7: Add PIN login columns (6-digit code alternative to magic link)
    try:
        cursor.execute("ALTER TABLE admins ADD COLUMN login_pin TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE admins ADD COLUMN login_pin_expires TEXT")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id          TEXT PRIMARY KEY,
            admin_id    TEXT REFERENCES admins(id),
            api_key     TEXT UNIQUE NOT NULL,
            dev_key     TEXT,
            scope       TEXT NOT NULL,
            is_dev      INTEGER DEFAULT 0,
            created_at  TEXT NOT NULL,
            active      INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consents (
            id          TEXT PRIMARY KEY,
            admin_id    TEXT REFERENCES admins(id),
            consent_ledger  INTEGER DEFAULT 0,
            consent_ai      INTEGER DEFAULT 0,
            eu_ai_act_art14 INTEGER DEFAULT 0,
            signed_at   TEXT NOT NULL,
            ip_hash     TEXT
        )
    """)

    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════
# CRYPTOGRAPHY FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def generate_did_and_wallet():
    """Generate Ed25519 keypair and DID."""
    from cryptography.hazmat.primitives import serialization

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Get raw public key bytes (32 bytes for Ed25519)
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )

    did = f"did:windi:{uuid.uuid4()}"
    fingerprint = hashlib.sha256(pub_bytes).hexdigest()[:16]
    public_key_b64 = base64.b64encode(pub_bytes).decode()

    return {
        "did": did,
        "public_key": public_key_b64,
        "fingerprint": fingerprint
    }


def generate_api_keys(is_dev: bool = False):
    """Generate API key and optional DEV key."""
    api_key = f"wl_{secrets.token_urlsafe(32)}"
    dev_key = f"wl_dev_{secrets.token_urlsafe(32)}" if is_dev else None
    return api_key, dev_key


def hash_ip(ip: str) -> str:
    """Hash IP for privacy-preserving logging."""
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def generate_email_token() -> str:
    """Generate secure token for email verification."""
    return secrets.token_urlsafe(32)


def get_email_token_expiry() -> str:
    """Get expiry timestamp for email token (48 hours from now)."""
    from datetime import timedelta
    expiry = datetime.now(timezone.utc) + timedelta(hours=EMAIL_VERIFY_HOURS)
    return expiry.isoformat()


async def send_verification_email(email: str, token: str, full_name: str, lang: str = "en"):
    """
    Send verification email asynchronously.
    For now, logs to console. In production, integrate with SMTP or Dispatch Gateway.
    """
    verify_url = f"{DOMAIN_URL}/law/verify-email/{token}"

    # Trilingual email subjects and bodies
    subjects = {
        "de": "WINDI-LAW: Bestätigen Sie Ihre E-Mail",
        "en": "WINDI-LAW: Confirm your email",
        "pt": "WINDI-LAW: Confirme seu email"
    }

    bodies = {
        "de": f"""
Hallo {full_name},

Willkommen bei WINDI-LAW!

Bitte bestätigen Sie Ihre E-Mail-Adresse, indem Sie auf den folgenden Link klicken:

{verify_url}

Dieser Link ist 48 Stunden gültig.

Sie haben bereits Zugang zum Workspace. Die E-Mail-Bestätigung ermöglicht HIGH-Operationen.

Mit freundlichen Grüßen,
WINDI Publishing House
        """,
        "en": f"""
Hello {full_name},

Welcome to WINDI-LAW!

Please confirm your email address by clicking the link below:

{verify_url}

This link is valid for 48 hours.

You already have access to the workspace. Email confirmation enables HIGH operations.

Best regards,
WINDI Publishing House
        """,
        "pt": f"""
Olá {full_name},

Bem-vindo ao WINDI-LAW!

Por favor, confirme seu email clicando no link abaixo:

{verify_url}

Este link é válido por 48 horas.

Você já tem acesso ao workspace. A confirmação de email habilita operações HIGH.

Atenciosamente,
WINDI Publishing House
        """
    }

    subject = subjects.get(lang, subjects["en"])
    body = bodies.get(lang, bodies["en"])

    # Check SMTP credentials
    if not SMTP_USER or not SMTP_PASS:
        print(f"⚠️ SMTP not configured - email logged to console")
        print(f"📧 To: {email} | Subject: {subject}")
        print(f"🔗 Verify URL: {verify_url}")
        return True  # Return success for development

    # Send via SMTP (Strato SSL port 465)
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = email

        # Plain text version
        text_part = MIMEText(body.strip(), "plain", "utf-8")
        msg.attach(text_part)

        # HTML version (simple formatting)
        html_body = body.strip().replace("\n", "<br>\n")
        html_content = f"""
        <html>
        <body style="font-family: 'JetBrains Mono', monospace; color: #1A1A1A; max-width: 600px;">
            <div style="border-bottom: 2px solid #8B7424; padding-bottom: 10px; margin-bottom: 20px;">
                <strong style="color: #8B7424;">WINDI-LAW</strong>
            </div>
            <p>{html_body}</p>
            <div style="margin-top: 30px; padding-top: 10px; border-top: 1px solid #E0DED8; font-size: 12px; color: #666;">
                WINDI Publishing House · Kempten, Bavaria
            </div>
        </body>
        </html>
        """
        html_part = MIMEText(html_content, "html", "utf-8")
        msg.attach(html_part)

        # SSL connection to Strato
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(EMAIL_FROM, email, msg.as_string())

        print(f"✅ Verification email sent to {email}")
        return True

    except Exception as e:
        print(f"❌ SMTP Error: {e}")
        # Log to console as fallback
        print(f"📧 FALLBACK - To: {email} | Subject: {subject}")
        print(f"🔗 Verify URL: {verify_url}")
        return False


# ═══════════════════════════════════════════════════════════════
# §LOGIN — Magic Link Login Email
# ═══════════════════════════════════════════════════════════════

def generate_login_pin() -> str:
    """Generate 6-digit PIN for login (§120.7)."""
    import random
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])


async def send_login_email(email: str, token: str, full_name: str, lang: str = "en", pin: str = None):
    """Send magic link login email with optional PIN code (§120.7)."""
    login_url = f"{DOMAIN_URL}/law/login/{token}"

    # §120.7: Include PIN in email if provided
    pin_section_de = f"\n\n📱 ODER gib diesen Code ein:\n\n   {pin}\n\n(Code 15 Minuten gültig)" if pin else ""
    pin_section_en = f"\n\n📱 OR enter this code:\n\n   {pin}\n\n(Code valid for 15 minutes)" if pin else ""
    pin_section_pt = f"\n\n📱 OU insere este código:\n\n   {pin}\n\n(Código válido por 15 minutos)" if pin else ""

    subjects = {
        "de": "WINDI-LAW: Dein Login-Code",
        "en": "WINDI-LAW: Your login code",
        "pt": "WINDI-LAW: Teu código de acesso"
    }

    bodies = {
        "de": f"""
Hallo {full_name},

Hier ist dein Login-Link für WINDI-LAW:

{login_url}
{pin_section_de}
Link ist 1 Stunde gültig.

Falls du diese Anfrage nicht gestellt hast, ignoriere diese E-Mail.

Mit freundlichen Grüßen,
WINDI Publishing House
        """,
        "en": f"""
Hello {full_name},

Here is your login link for WINDI-LAW:

{login_url}
{pin_section_en}
Link is valid for 1 hour.

If you did not request this, please ignore this email.

Best regards,
WINDI Publishing House
        """,
        "pt": f"""
Olá {full_name},

Aqui está o teu link de acesso ao WINDI-LAW:

{login_url}
{pin_section_pt}
Link válido por 1 hora.

Se não solicitaste este acesso, ignora este email.

Atenciosamente,
WINDI Publishing House
        """
    }

    subject = subjects.get(lang, subjects["en"])
    body = bodies.get(lang, bodies["en"])

    if not SMTP_USER or not SMTP_PASS:
        print(f"⚠️ SMTP not configured - login email logged to console")
        print(f"📧 To: {email} | Subject: {subject}")
        print(f"🔗 Login URL: {login_url}")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = email

        text_part = MIMEText(body.strip(), "plain", "utf-8")
        msg.attach(text_part)

        html_body = body.strip().replace("\n", "<br>\n")
        html_content = f"""
        <html>
        <body style="font-family: 'JetBrains Mono', monospace; color: #1A1A1A; max-width: 600px;">
            <div style="border-bottom: 2px solid #1a3a6b; padding-bottom: 10px; margin-bottom: 20px;">
                <strong style="color: #1a3a6b;">WINDI-LAW</strong>
            </div>
            <p>{html_body}</p>
            <div style="margin-top: 30px; padding-top: 10px; border-top: 1px solid #E0DED8; font-size: 12px; color: #666;">
                WINDI Publishing House · Kempten, Bavaria
            </div>
        </body>
        </html>
        """
        html_part = MIMEText(html_content, "html", "utf-8")
        msg.attach(html_part)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(EMAIL_FROM, email, msg.as_string())

        print(f"✅ Login email sent to {email}")
        return True

    except Exception as e:
        print(f"❌ SMTP Error (login): {e}")
        print(f"📧 FALLBACK - To: {email} | Subject: {subject}")
        print(f"🔗 Login URL: {login_url}")
        return False


def get_login_token_expiry() -> str:
    """Return expiry time for login token (1 hour from now)."""
    return (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()


# ═══════════════════════════════════════════════════════════════
# LEDGER INTEGRATION
# ═══════════════════════════════════════════════════════════════

async def seal_identity_in_ledger(company_id: str, did: str, admin_email: str, event_type: str = "GENESIS"):
    """Seal identity event in Forensic Ledger."""
    receipt_id = f"WINDI-LAW-{event_type}-{company_id[:8].upper()}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    # Generate content hash from DID + company_id
    content_to_hash = f"{did}|{company_id}|{event_type}|{admin_email}"
    content_hash = f"sha256:{hashlib.sha256(content_to_hash.encode()).hexdigest()}"

    payload = {
        "id": receipt_id,
        "actor": admin_email,
        "app": "windi-law-identity-gate",
        "doc_name": f"Identity Gate — {event_type} — {company_id[:8]}",
        "doc_type": "doc",
        "governance_level": "HIGH",
        "content_hash": content_hash,
        "sge_score": 1.0,  # Identity genesis = highest governance
        "metadata": {
            "did": did,
            "gate_version": VERSION,
            "event_type": event_type,
            "invariants": ["I9", "I11", "I13", "G3"],
            "eu_ai_act_art14": True
        }
    }

    try:
        r = requests.post(LEDGER_URL, json=payload, timeout=10.0)
        return r.json()
    except Exception as e:
        return {"error": str(e), "receipt_id": receipt_id}


# ═══════════════════════════════════════════════════════════════
# FASTAPI APPLICATION
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title="WINDI-LAW Identity Gate",
    version=VERSION,
    description="Sovereign Identity Management for Legal Professionals"
)

# ─── AI Draft Module ─────────────────────────────────────────────────────────
from ai_draft import ai_draft_router
app.include_router(ai_draft_router)

# ─── Dragon Shadow Forest Module ──────────────────────────────────────────────
try:
    from w_dragon_001_law_routes import dragon_router
    app.include_router(dragon_router)
    print("[WINDI-LAW] W-DRAGON-001 Dragon Shadow Forest loaded")
except ImportError as e:
    print(f"[WINDI-LAW] W-DRAGON-001 not available: {e}")

# ─── Canvas Integration §166 ──────────────────────────────────────────────────
try:
    from canvas_integration import law_generate_document_cover
    CANVAS_AVAILABLE = True
    print("[WINDI-LAW] W-CANVAS-001 integration loaded")
except ImportError as e:
    CANVAS_AVAILABLE = False
    print(f"[WINDI-LAW] W-CANVAS-001 not available: {e}")

# Mount static files and templates
templates = Jinja2Templates(directory="/opt/windi/windi-law/identity-gate/templates")
# Disable Jinja2 cache to avoid unhashable type error with dict globals
templates.env.cache = None

# Initialize database on startup
@app.on_event("startup")
async def startup():
    init_db()
    print(f"[WINDI-LAW] Identity Gate {VERSION} started on :8122")


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.get("/health")
async def health():
    """Health check endpoint."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM companies")
    companies = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM admins")
    admins = cursor.fetchone()[0]
    conn.close()

    return {
        "service": f"WINDI-LAW Identity Gate {VERSION}",
        "status": "healthy",
        "port": 8122,
        "companies": companies,
        "admins": admins,
        "invariants": ["I9", "I11", "I13", "G3"],
        "blocking_rule": "if(!did||!wallet){blockWorkspace()}",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/register")
async def register(data: CompanyRegister, request: Request):
    """
    Complete registration flow:
    1. Create company
    2. Create admin
    3. Generate wallet (DID + Ed25519)
    4. Generate API keys
    5. Seal in Ledger
    """
    now = datetime.now(timezone.utc).isoformat()
    company_id = str(uuid.uuid4())
    admin_id = str(uuid.uuid4())

    # Generate DID and wallet
    wallet = generate_did_and_wallet()

    # Generate API keys
    api_key, dev_key = generate_api_keys(is_dev=False)
    key_id = str(uuid.uuid4())

    # Generate email verification token
    email_token = generate_email_token()
    email_token_expires = get_email_token_expiry()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Insert company
        cursor.execute("""
            INSERT INTO companies (id, legal_name, country, vat_number, type, state, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (company_id, data.legal_name, data.country, data.vat_number, data.type, STATE_VERIFIED, now))

        # Insert admin with DID — Auto-VERIFIED for immediate workspace access
        # email_verified=0 until they click the link
        cursor.execute("""
            INSERT INTO admins (id, company_id, full_name, email, role, did, public_key, fingerprint, state, created_at, email_verified, email_token, email_token_expires)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (admin_id, company_id, data.admin_name, data.admin_email, "admin",
              wallet["did"], wallet["public_key"], wallet["fingerprint"], STATE_VERIFIED, now,
              0, email_token, email_token_expires))

        # Insert API key
        cursor.execute("""
            INSERT INTO api_keys (id, admin_id, api_key, dev_key, scope, is_dev, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (key_id, admin_id, api_key, dev_key, '["verify","seal"]', 0, now))

        conn.commit()

        # Seal in Ledger
        ledger_result = await seal_identity_in_ledger(
            company_id, wallet["did"], data.admin_email, "GENESIS"
        )

        # Update company with ledger receipt
        if "id" in ledger_result or "receipt_id" in ledger_result:
            receipt_id = ledger_result.get("id") or ledger_result.get("receipt_id")
            cursor.execute("""
                UPDATE companies SET ledger_receipt = ? WHERE id = ?
            """, (receipt_id, company_id))
            conn.commit()

        conn.close()

        # Send verification email (async, non-blocking)
        # Detect language from request headers or default to EN
        accept_lang = request.headers.get("Accept-Language", "en")
        lang = "de" if "de" in accept_lang.lower() else ("pt" if "pt" in accept_lang.lower() else "en")
        await send_verification_email(data.admin_email, email_token, data.admin_name, lang)

        return {
            "success": True,
            "company_id": company_id,
            "admin_id": admin_id,
            "did": wallet["did"],
            "fingerprint": wallet["fingerprint"],
            "public_key": wallet["public_key"],
            "api_key": api_key,
            "state": STATE_VERIFIED,
            "email_verified": False,
            "email_verification_sent": True,
            "ledger_receipt": ledger_result,
            "message": "Identity created. Workspace access granted. Verification email sent.",
            "workspace_url": f"{get_base_path(request)}/workspace/"
        }

    except sqlite3.IntegrityError as e:
        conn.close()
        err = str(e).lower()

        # P0 FIX: Esconder detalhes internos — I13: dar acção ao utilizador
        if "unique" in err and "email" in err:
            raise HTTPException(status_code=409, detail={
                "error": "Email já registado no sistema",
                "code": "DUPLICATE_EMAIL",
                "action": "Aceda ao seu dashboard ou use outro email",
                "gate": f"{get_base_path(request)}/gate"
            })
        elif "unique" in err and ("vat" in err or "company" in err):
            raise HTTPException(status_code=409, detail={
                "error": "Entidade já registada no sistema",
                "code": "DUPLICATE_ENTITY",
                "action": "Contacte o administrador da conta existente",
                "gate": f"{get_base_path(request)}/gate"
            })
        else:
            # Nunca expor o erro real — log interno apenas
            import logging
            logging.error(f"[WINDI-LAW] Register IntegrityError: {e}")
            raise HTTPException(status_code=500, detail={
                "error": "Erro no registo",
                "code": "REGISTRATION_FAILED",
                "action": "Tente novamente ou contacte o suporte"
            })


@app.get("/verify-email/{token}", response_class=HTMLResponse)
async def verify_email(token: str, request: Request):
    """
    Verify email address using token from email link.
    Returns HTML page with success/error message.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Find admin with this token
    cursor.execute("""
        SELECT id, full_name, email, email_token_expires, email_verified, did
        FROM admins WHERE email_token = ?
    """, (token,))
    admin = cursor.fetchone()

    if not admin:
        conn.close()
        return templates.TemplateResponse(request, "verify-email-result.html", context={
            "success": False,
            "error": "invalid_token",
            "message_de": "Ungültiger oder abgelaufener Bestätigungslink.",
            "message_en": "Invalid or expired verification link.",
            "message_pt": "Link de verificação inválido ou expirado."
        })

    admin_id, full_name, email, token_expires, already_verified, did = admin

    # Check if already verified
    if already_verified:
        conn.close()
        return templates.TemplateResponse(request, "verify-email-result.html", context={
            "success": True,
            "already_verified": True,
            "message_de": "E-Mail bereits bestätigt!",
            "message_en": "Email already verified!",
            "message_pt": "Email já verificado!",
            "did": did
        })

    # Check if token expired
    if token_expires:
        expiry = datetime.fromisoformat(token_expires.replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expiry:
            conn.close()
            return templates.TemplateResponse(request, "verify-email-result.html", context={
                "success": False,
                "error": "expired",
                "message_de": "Bestätigungslink abgelaufen. Bitte fordern Sie einen neuen an.",
                "message_en": "Verification link expired. Please request a new one.",
                "message_pt": "Link de verificação expirado. Solicite um novo."
            })

    # Mark as verified
    cursor.execute("""
        UPDATE admins
        SET email_verified = 1, email_token = NULL, email_token_expires = NULL
        WHERE id = ?
    """, (admin_id,))
    conn.commit()
    conn.close()

    return templates.TemplateResponse(request, "verify-email-result.html", context={
        "success": True,
        "full_name": full_name,
        "email": email,
        "did": did,
        "message_de": "E-Mail erfolgreich bestätigt!",
        "message_en": "Email successfully verified!",
        "message_pt": "Email verificado com sucesso!"
    })


@app.post("/resend-verification")
async def resend_verification(request: Request):
    """Resend verification email."""
    body = await request.json()
    email = body.get("email")

    if not email:
        raise HTTPException(status_code=400, detail="Email required")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, full_name, email_verified FROM admins WHERE email = ?
    """, (email,))
    admin = cursor.fetchone()

    if not admin:
        conn.close()
        raise HTTPException(status_code=404, detail="Email not found")

    admin_id, full_name, email_verified = admin

    if email_verified:
        conn.close()
        return {"success": True, "message": "Email already verified", "already_verified": True}

    # Generate new token
    new_token = generate_email_token()
    new_expiry = get_email_token_expiry()

    cursor.execute("""
        UPDATE admins SET email_token = ?, email_token_expires = ? WHERE id = ?
    """, (new_token, new_expiry, admin_id))
    conn.commit()
    conn.close()

    # Send new verification email
    accept_lang = request.headers.get("Accept-Language", "en")
    lang = "de" if "de" in accept_lang.lower() else ("pt" if "pt" in accept_lang.lower() else "en")
    await send_verification_email(email, new_token, full_name, lang)

    return {"success": True, "message": "Verification email resent"}


# ═══════════════════════════════════════════════════════════════
# §LOGIN — Magic Link Login Endpoints
# ═══════════════════════════════════════════════════════════════

@app.post("/login-request")
async def login_request(request: Request):
    """
    Request magic link login.
    Sends email with login link if user exists.
    """
    body = await request.json()
    email = body.get("email", "").strip().lower()

    if not email:
        raise HTTPException(status_code=400, detail="Email required")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, full_name, did FROM admins WHERE LOWER(email) = ?
    """, (email,))
    admin = cursor.fetchone()

    if not admin:
        conn.close()
        # Security: Don't reveal if email exists or not
        return {"success": True, "message": "If this email is registered, you will receive a login link"}

    admin_id, full_name, did = admin

    # Generate login token (magic link)
    login_token = generate_email_token()
    login_expiry = get_login_token_expiry()

    # §120.7: Generate 6-digit PIN (15 min expiry)
    login_pin = generate_login_pin()
    pin_expiry = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()

    cursor.execute("""
        UPDATE admins SET
            login_token = ?, login_token_expires = ?,
            login_pin = ?, login_pin_expires = ?
        WHERE id = ?
    """, (login_token, login_expiry, login_pin, pin_expiry, admin_id))
    conn.commit()
    conn.close()

    # Send login email with both link AND PIN
    accept_lang = request.headers.get("Accept-Language", "en")
    lang = "de" if "de" in accept_lang.lower() else ("pt" if "pt" in accept_lang.lower() else "en")
    await send_login_email(email, login_token, full_name, lang, pin=login_pin)

    return {"success": True, "message": "If this email is registered, you will receive a login code"}


@app.get("/login/{token}", response_class=HTMLResponse)
async def login_with_token(token: str, request: Request):
    """
    Validate login token and redirect to workspace.
    Sets session cookie and sessionStorage via JavaScript.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, full_name, email, did, fingerprint, public_key, login_token_expires, state
        FROM admins WHERE login_token = ?
    """, (token,))
    admin = cursor.fetchone()

    if not admin:
        conn.close()
        return templates.TemplateResponse(request, "verify-email-result.html", context={
            "success": False,
            "error": "invalid_token",
            "message_de": "Ungültiger oder bereits verwendeter Login-Link.",
            "message_en": "Invalid or already used login link.",
            "message_pt": "Link de acesso inválido ou já utilizado."
        })

    admin_id, full_name, email, did, fingerprint, public_key, token_expires, state = admin

    # Check expiry
    if token_expires:
        try:
            expiry_dt = datetime.fromisoformat(token_expires.replace('Z', '+00:00'))
            if datetime.now(timezone.utc) > expiry_dt:
                conn.close()
                return templates.TemplateResponse(request, "verify-email-result.html", context={
                    "success": False,
                    "error": "expired",
                    "message_de": "Login-Link abgelaufen. Bitte fordere einen neuen an.",
                    "message_en": "Login link expired. Please request a new one.",
                    "message_pt": "Link de acesso expirado. Por favor solicita um novo."
                })
        except:
            pass

    # Clear login token (one-time use)
    cursor.execute("""
        UPDATE admins SET login_token = NULL, login_token_expires = NULL WHERE id = ?
    """, (admin_id,))
    conn.commit()
    conn.close()

    # §120.6: Detect base path from request host
    host = request.headers.get("host", "")
    base_path = "" if "windilaw.de" in host else "/law"
    workspace_url = f"{base_path}/workspace/?did={did}"

    # Return HTML that sets sessionStorage and redirects to workspace
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>WINDI-LAW Login</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #0A0A10;
                color: #E8E6E1;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                padding: 1rem;
            }}
            .card {{
                background: #12121A;
                border: 1px solid #1A1A24;
                border-radius: 12px;
                padding: 2rem;
                text-align: center;
                max-width: 400px;
                width: 100%;
            }}
            .success {{ color: #2EC27E; font-size: 3rem; }}
            .title {{ color: #C9A84C; font-size: 1.25rem; margin: 1rem 0; font-weight: 600; }}
            .did {{ font-size: 0.7rem; color: #666; word-break: break-all; margin: 0.5rem 0; }}
            .status {{ color: #666; font-size: 0.875rem; margin-top: 1rem; }}
            .manual-link {{
                display: inline-block;
                margin-top: 1.5rem;
                padding: 0.875rem 1.5rem;
                background: #C9A84C;
                color: #0A0A10;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 1rem;
                min-height: 48px;
                line-height: 1.5;
            }}
            .manual-link:hover {{ opacity: 0.9; }}
            .hint {{ font-size: 0.75rem; color: #555; margin-top: 1rem; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="success">✓</div>
            <div class="title">Login erfolgreich!</div>
            <p>Willkommen zurück, {full_name}!</p>
            <p class="did">{did}</p>
            <p class="status" id="status">Weiterleitung zum Workspace...</p>
            <a href="{workspace_url}" class="manual-link" id="manual-btn" style="display:none;">
                → Workspace öffnen
            </a>
            <p class="hint" id="hint" style="display:none;">
                Falls die automatische Weiterleitung nicht funktioniert
            </p>
        </div>
        <script>
            // Set session data for workspace
            try {{
                var walletData = {{
                    did: "{did}",
                    fingerprint: "{fingerprint}",
                    public_key: "{public_key}",
                    state: "{state}",
                    created_at: new Date().toISOString(),
                    pioneer_number: null,
                    tier: "FREE",
                    credits: 0
                }};
                sessionStorage.setItem('windi_law_wallet', JSON.stringify(walletData));
                sessionStorage.setItem('windi_law_did', "{did}");
                sessionStorage.setItem('windi_law_fingerprint', "{fingerprint}");
            }} catch(e) {{
                console.warn('[WINDI-LAW] sessionStorage not available:', e);
            }}

            // Redirect after delay (cookie already set by server)
            setTimeout(function() {{
                window.location.href = "{workspace_url}";
            }}, 1500);

            // Show manual button after 3 seconds as fallback
            setTimeout(function() {{
                document.getElementById('manual-btn').style.display = 'inline-block';
                document.getElementById('hint').style.display = 'block';
                document.getElementById('status').textContent = 'Klicke unten falls nicht automatisch weitergeleitet';
            }}, 3000);
        </script>
    </body>
    </html>
    """

    # §120.6: Set cookie via HTTP header (more reliable than JavaScript on mobile)
    from fastapi.responses import Response
    response = Response(content=html_content, media_type="text/html")
    response.set_cookie(
        key="windi_did",
        value=did,
        max_age=31536000,  # 1 year
        path="/",
        samesite="lax",
        httponly=False  # Needs to be readable by JavaScript for Fast Lane
    )
    return response


# ═══════════════════════════════════════════════════════════════
# §120.7 — PIN Login (6-digit code alternative to magic link)
# ═══════════════════════════════════════════════════════════════

class PinLogin(BaseModel):
    email: str
    pin: str


@app.post("/login-pin")
async def login_with_pin(data: PinLogin, request: Request):
    """
    Validate 6-digit PIN and return session data.
    More reliable than magic links on mobile devices.
    """
    email = data.email.strip().lower()
    pin = data.pin.strip()

    if len(pin) != 6 or not pin.isdigit():
        raise HTTPException(status_code=400, detail="Invalid PIN format")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, full_name, did, fingerprint, public_key, state, login_pin, login_pin_expires
        FROM admins WHERE LOWER(email) = ?
    """, (email,))
    admin = cursor.fetchone()

    if not admin:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid email or PIN")

    admin_id, full_name, did, fingerprint, public_key, state, stored_pin, pin_expires = admin

    # Verify PIN matches
    if stored_pin != pin:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid email or PIN")

    # Check PIN expiry
    if pin_expires:
        try:
            expiry_dt = datetime.fromisoformat(pin_expires.replace('Z', '+00:00'))
            if datetime.now(timezone.utc) > expiry_dt:
                conn.close()
                raise HTTPException(status_code=401, detail="PIN expired. Please request a new one.")
        except:
            pass

    # Clear PIN (one-time use)
    cursor.execute("""
        UPDATE admins SET login_pin = NULL, login_pin_expires = NULL WHERE id = ?
    """, (admin_id,))
    conn.commit()
    conn.close()

    # Return session data (frontend will store in sessionStorage)
    return {
        "success": True,
        "did": did,
        "fingerprint": fingerprint,
        "public_key": public_key,
        "state": state,
        "full_name": full_name,
        "workspace_url": "/law/workspace/?did=" + did
    }


@app.post("/wallet/create")
async def wallet_create(data: WalletCreate):
    """Generate new wallet for existing admin."""
    wallet = generate_did_and_wallet()
    now = datetime.now(timezone.utc).isoformat()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE admins
        SET did = ?, public_key = ?, fingerprint = ?
        WHERE id = ?
    """, (wallet["did"], wallet["public_key"], wallet["fingerprint"], data.admin_id))

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Admin not found")

    conn.commit()
    conn.close()

    return {
        "success": True,
        "admin_id": data.admin_id,
        "did": wallet["did"],
        "fingerprint": wallet["fingerprint"],
        "public_key": wallet["public_key"]
    }


@app.post("/keys/generate")
async def keys_generate(data: KeysGenerate):
    """Generate API keys for admin."""
    api_key, dev_key = generate_api_keys(is_dev=data.is_dev)
    key_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    scope_json = str(data.scope).replace("'", '"')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verify admin exists
    cursor.execute("SELECT id FROM admins WHERE id = ?", (data.admin_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Admin not found")

    cursor.execute("""
        INSERT INTO api_keys (id, admin_id, api_key, dev_key, scope, is_dev, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (key_id, data.admin_id, api_key, dev_key, scope_json, 1 if data.is_dev else 0, now))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "key_id": key_id,
        "api_key": api_key,
        "dev_key": dev_key,
        "scope": data.scope,
        "is_dev": data.is_dev
    }


@app.get("/identity/{did}")
async def identity_get(did: str, request: Request):
    """Get identity by DID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.id, a.full_name, a.email, a.did, a.fingerprint, a.state, a.created_at,
               c.legal_name, c.country, c.type, c.ledger_receipt
        FROM admins a
        JOIN companies c ON a.company_id = c.id
        WHERE a.did = ?
    """, (did,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        # P1 FIX: I13 - dar acção ao utilizador
        raise HTTPException(status_code=404, detail={
            "error": "Identidade não encontrada",
            "code": "NOT_FOUND",
            "did": did,
            "action": f"Registe a sua entidade em {get_base_path(request)}/gate",
            "gate": f"{get_base_path(request)}/gate"
        })

    return {
        "admin_id": row[0],
        "full_name": row[1],
        "email": row[2],
        "did": row[3],
        "fingerprint": row[4],
        "state": row[5],
        "created_at": row[6],
        "company": {
            "legal_name": row[7],
            "country": row[8],
            "type": row[9],
            "ledger_receipt": row[10]
        }
    }


@app.post("/identity/verify")
async def identity_verify(data: IdentityVerify):
    """Verify DID before allowing workspace access."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.state, a.fingerprint, c.state as company_state
        FROM admins a
        JOIN companies c ON a.company_id = c.id
        WHERE a.did = ?
    """, (data.did,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return {
            "valid": False,
            "reason": "DID not found",
            "workspace_access": False
        }

    admin_state, fingerprint, company_state = row

    # Check states
    if admin_state in [STATE_SUSPENDED, STATE_REVOKED]:
        return {
            "valid": False,
            "reason": f"Identity {admin_state.lower()}",
            "workspace_access": False
        }

    if company_state in [STATE_SUSPENDED, STATE_REVOKED]:
        return {
            "valid": False,
            "reason": f"Company {company_state.lower()}",
            "workspace_access": False
        }

    return {
        "valid": True,
        "state": admin_state,
        "fingerprint": fingerprint,
        "workspace_access": True,
        "permissions": ["verify", "seal"] if admin_state == STATE_VERIFIED else ["verify"]
    }


@app.post("/consent/sign")
async def consent_sign(data: ConsentSign, request: Request):
    """Sign consents (EU AI Act Art.14)."""
    if not (data.consent_ledger and data.consent_ai and data.eu_ai_act_art14):
        raise HTTPException(
            status_code=400,
            detail="All consents required: consent_ledger, consent_ai, eu_ai_act_art14"
        )

    consent_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    ip_hashed = hash_ip(request.client.host if request.client else "unknown")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO consents (id, admin_id, consent_ledger, consent_ai, eu_ai_act_art14, signed_at, ip_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (consent_id, data.admin_id, 1, 1, 1, now, ip_hashed))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "consent_id": consent_id,
        "admin_id": data.admin_id,
        "signed_at": now,
        "consents": {
            "consent_ledger": True,
            "consent_ai": True,
            "eu_ai_act_art14": True
        }
    }


@app.get("/gate/", response_class=HTMLResponse)
@app.get("/gate", response_class=HTMLResponse)
async def gate_ui(request: Request):
    """Render Identity Gate UI."""
    return templates.TemplateResponse(request, "gate.html")


# ═══════════════════════════════════════════════════════════════
# WORKSPACE — FAIL-CLOSED (P0 CRITICAL)
# ═══════════════════════════════════════════════════════════════

from fastapi.responses import RedirectResponse

# §123 — Workspace static files (demo pages, assets like .html, .css, .js)
@app.get("/workspace/{filename}")
async def workspace_static(filename: str, request: Request):
    """Serve static files from workspace directory (demo pages, assets)."""
    import os

    # Security: only allow specific file extensions
    allowed_extensions = ['.html', '.css', '.js', '.png', '.jpg', '.svg', '.ico']
    ext = os.path.splitext(filename)[1].lower()

    if not ext or ext not in allowed_extensions:
        raise HTTPException(status_code=403, detail="File type not allowed")

    # Security: prevent directory traversal
    if '..' in filename or '/' in filename:
        raise HTTPException(status_code=403, detail="Invalid path")

    filepath = f"/opt/windi/windi-law/workspace/{filename}"

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")

    # Determine content type
    content_types = {
        '.html': 'text/html',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.svg': 'image/svg+xml',
        '.ico': 'image/x-icon'
    }
    content_type = content_types.get(ext, 'application/octet-stream')

    with open(filepath, 'rb') as f:
        content = f.read()

    from fastapi.responses import Response
    return Response(content=content, media_type=content_type)

@app.get("/workspace/")
@app.get("/workspace")
async def workspace_gate(request: Request):
    """
    Workspace só abre com DID VERIFIED.
    P0 FIX: FAIL-CLOSED — sem DID válido, redirige para /gate
    """
    did = request.headers.get("X-WINDI-DID", "").strip()

    # Também verificar query param e cookie como fallback
    if not did:
        did = request.query_params.get("did", "").strip()
    if not did:
        did = request.cookies.get("windi_did", "").strip()

    if not did:
        return RedirectResponse(url=f"{get_base_path(request)}/gate", status_code=302)

    # Verificar DID no DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT state FROM admins WHERE did = ?", (did,))
    admin = cursor.fetchone()
    conn.close()

    if not admin:
        return RedirectResponse(url=f"{get_base_path(request)}/gate", status_code=302)

    admin_state = admin[0]

    if admin_state != STATE_VERIFIED:
        # Mostrar wall de verificação pendente
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html lang="de">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>WINDI LAW — Identität in Prüfung</title>
            <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet">
        </head>
        <body style="background:#07090D;color:#F5F0E0;
          font-family:'JetBrains Mono',monospace;
          display:flex;align-items:center;justify-content:center;
          min-height:100vh;text-align:center;margin:0;">
          <div>
            <div style="font-size:48px;margin-bottom:1.5rem">🔐</div>
            <div style="font-size:18px;font-weight:500;
              color:#C9A84C;margin-bottom:0.75rem">
              Identidade em Verificação
            </div>
            <div style="font-size:13px;color:rgba(245,240,224,0.6);
              margin-bottom:2rem;max-width:420px;line-height:1.6">
              O Human Dragon irá validar a sua conta.<br>
              Estado actual: <strong style="color:#C9A84C">{admin_state}</strong>
            </div>
            <a href="{get_base_path(request)}/gate" style="font-size:12px;
              color:rgba(201,168,76,0.8);text-decoration:none;
              border:1px solid rgba(201,168,76,0.3);
              padding:10px 20px;border-radius:4px;
              transition:all 0.2s ease;">
              ← Voltar ao Gate
            </a>
          </div>
        </body>
        </html>
        """, status_code=403)

    # DID VERIFIED — servir workspace
    try:
        with open("/opt/windi/windi-law/workspace/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html><body style="background:#07090D;color:#F5F0E0;
          font-family:monospace;text-align:center;padding:4rem;">
          <h1 style="color:#C9A84C">Workspace em Construção</h1>
          <p>O workspace está a ser preparado.</p>
          <a href="{get_base_path(request)}/dashboard/{did}" style="color:#C9A84C">Ver Dashboard →</a>
        </body></html>
        """.format(did=did), status_code=200)


# ═══════════════════════════════════════════════════════════════
# DASHBOARD ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.get("/dashboard/{did}", response_class=HTMLResponse)
async def dashboard(did: str, request: Request):
    """Render Dashboard for authenticated admin."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get admin data
    cursor.execute("""
        SELECT a.id, a.full_name, a.email, a.did, a.fingerprint, a.state, a.created_at,
               c.legal_name, c.country, c.type, c.ledger_receipt
        FROM admins a
        JOIN companies c ON a.company_id = c.id
        WHERE a.did = ?
    """, (did,))
    admin = cursor.fetchone()

    if not admin:
        conn.close()
        raise HTTPException(status_code=404, detail="Identity not found")

    # Get API keys
    cursor.execute("""
        SELECT api_key, dev_key, scope, is_dev FROM api_keys WHERE admin_id = ? AND active = 1
    """, (admin[0],))
    keys = cursor.fetchall()

    # Get receipts from Ledger (we'll fetch them separately)
    conn.close()

    # Prepare context for template
    context = {
        "admin_id": admin[0],
        "full_name": admin[1],
        "email": admin[2],
        "did": admin[3],
        "fingerprint": admin[4],
        "state": admin[5],
        "created_at": admin[6],
        "company_name": admin[7],
        "country": admin[8],
        "company_type": admin[9],
        "genesis_receipt": admin[10],
        "api_keys": keys,
        "version": VERSION
    }

    return templates.TemplateResponse(request, "dashboard.html", context=context)


@app.get("/dashboard/{did}/json")
async def dashboard_json(did: str):
    """
    P2 FIX: Export Identity Card portátil com genesis_receipt + verify_url garantidos.
    Formato: windi_identity_card v1.0
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.id, a.full_name, a.email, a.did, a.fingerprint, a.state, a.created_at,
               c.legal_name, c.country, c.type, c.ledger_receipt, c.vat_number
        FROM admins a
        JOIN companies c ON a.company_id = c.id
        WHERE a.did = ?
    """, (did,))
    admin = cursor.fetchone()

    if not admin:
        conn.close()
        raise HTTPException(status_code=404, detail={
            "error": "Identity not found",
            "code": "NOT_FOUND",
            "action": "Register at /law/gate"
        })

    # Count API keys
    cursor.execute("""
        SELECT COUNT(*) FROM api_keys WHERE admin_id = ? AND active = 1
    """, (admin[0],))
    keys_count = cursor.fetchone()[0]
    conn.close()

    # P2 FIX: Gerar genesis_receipt_id a partir do DID
    # Padrão: WINDI-LAW-GENESIS-{did_uuid[:8].upper()}
    did_uuid = did.split(":")[-1] if ":" in did else did
    did_short = did_uuid.replace("-", "")[:8].upper()
    genesis_receipt_id = f"WINDI-LAW-GENESIS-{did_short}"

    # Usar receipt do DB se existir, senão usar o gerado
    actual_receipt = admin[10] if admin[10] else genesis_receipt_id

    # verify_url canónica — sempre presente
    verify_url = f"https://windi-domain.com/verify-public/?id={actual_receipt}"

    # Identity Card portátil — formato exportável v1.0
    return {
        "windi_identity_card": {
            "version": "1.0",
            "did": admin[3],
            "entity": admin[7],
            "admin": admin[1],
            "email": admin[2],
            "country": admin[8],
            "type": admin[9],
            "vat_number": admin[11],
            "status": admin[5],
            "fingerprint": admin[4],
            "created_at": admin[6],
            "genesis_receipt": actual_receipt,
            "verify_url": verify_url,
            "keys_count": keys_count,
            "invariants": ["I9", "I11", "I13", "G3"],
            "constitutional_phrase": "Verification is not requested. It is granted.",
            "issued_by": "WINDI-LAW · Liga IA+H · Kempten, Bavaria"
        }
    }


# ═══════════════════════════════════════════════════════════════
# ADMIN PANEL (Human Dragon Only)
# ═══════════════════════════════════════════════════════════════

@app.get("/admin/panel")
async def admin_panel(x_admin_secret: Optional[str] = Header(None)):
    """List all admins (Human Dragon only)."""
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid admin secret")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.full_name, a.email, a.did, a.state, a.created_at,
               c.legal_name, c.country
        FROM admins a
        JOIN companies c ON a.company_id = c.id
        ORDER BY a.created_at DESC
    """)
    admins = cursor.fetchall()
    conn.close()

    return {
        "total": len(admins),
        "admins": [
            {
                "full_name": a[0],
                "email": a[1],
                "did": a[2],
                "state": a[3],
                "created_at": a[4],
                "company": a[5],
                "country": a[6]
            }
            for a in admins
        ]
    }


@app.post("/admin/verify/{did}")
async def admin_verify(did: str, x_admin_secret: Optional[str] = Header(None)):
    """Promote admin to VERIFIED status (Human Dragon only)."""
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid admin secret")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get admin
    cursor.execute("""
        SELECT a.id, a.full_name, a.email, a.state, c.id as company_id
        FROM admins a
        JOIN companies c ON a.company_id = c.id
        WHERE a.did = ?
    """, (did,))
    admin = cursor.fetchone()

    if not admin:
        conn.close()
        raise HTTPException(status_code=404, detail="Admin not found")

    if admin[3] == STATE_VERIFIED:
        conn.close()
        return {"success": False, "message": "Admin already verified", "state": STATE_VERIFIED}

    # Update state
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
        UPDATE admins SET state = ? WHERE did = ?
    """, (STATE_VERIFIED, did))

    # Also update company state
    cursor.execute("""
        UPDATE companies SET state = ? WHERE id = ?
    """, (STATE_VERIFIED, admin[4]))

    conn.commit()
    conn.close()

    # Seal verification in Ledger
    receipt_id = f"WINDI-LAW-VERIFY-{did[10:18].upper()}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    content_hash = f"sha256:{hashlib.sha256(f'{did}|VERIFIED|{now}'.encode()).hexdigest()}"

    ledger_payload = {
        "id": receipt_id,
        "actor": "Human Dragon",
        "app": "windi-law-admin",
        "doc_name": f"Identity Verification — {admin[1]}",
        "doc_type": "doc",
        "governance_level": "HIGH",
        "content_hash": content_hash,
        "sge_score": 1.0,
        "metadata": {
            "did": did,
            "admin_email": admin[2],
            "previous_state": admin[3],
            "new_state": STATE_VERIFIED,
            "verified_at": now,
            "verified_by": "Human Dragon",
            "invariants": ["I9", "I11"],
            "phrase": "Verification is not requested. It is granted."
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(LEDGER_URL, json=ledger_payload, timeout=10.0)
            ledger_result = r.json()
    except Exception as e:
        ledger_result = {"error": str(e), "receipt_id": receipt_id}

    return {
        "success": True,
        "did": did,
        "admin_name": admin[1],
        "previous_state": admin[3],
        "new_state": STATE_VERIFIED,
        "verified_at": now,
        "ledger_receipt": ledger_result,
        "message": "Identity verified by Human Dragon"
    }


# ═══════════════════════════════════════════════════════════════
# §166 CANVAS INTEGRATION
# ═══════════════════════════════════════════════════════════════

class LawCoverRequest(BaseModel):
    doc_title: str
    jurisdiction: str
    doc_type: str
    actor: str = "windi-law"

@app.post("/api/canvas/law-cover")
async def generate_law_cover(body: LawCoverRequest):
    """
    Generate branded cover for legal documents.
    §166 · I9-P: AI renders, Human approves, WINDI seals.
    """
    if not CANVAS_AVAILABLE:
        return {"error": "Canvas integration not available", "canvas_available": False}

    result = await law_generate_document_cover(
        doc_title=body.doc_title,
        jurisdiction=body.jurisdiction,
        doc_type=body.doc_type,
        actor=body.actor
    )

    if result:
        return {
            "success": True,
            "job_id": result.get("job_id"),
            "download_url": result.get("download_url"),
            "sha256": result.get("sha256"),
            "ledger_receipt": result.get("ledger_receipt"),
            "render_ms": result.get("render_ms")
        }
    else:
        return {"success": False, "error": "Canvas worker offline or render failed"}

@app.get("/api/canvas/status")
async def canvas_status_law():
    """Check W-CANVAS-001 availability."""
    if not CANVAS_AVAILABLE:
        return {"available": False, "reason": "Integration module not loaded"}

    try:
        import httpx
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get("http://127.0.0.1:8155/canvas/health")
            if r.status_code == 200:
                data = r.json()
                return {
                    "available": True,
                    "service": data.get("service"),
                    "version": data.get("version")
                }
    except Exception:
        pass

    return {"available": False, "reason": "Canvas worker not responding"}


# ═══════════════════════════════════════════════════════════════
# ROOT REDIRECT
# ═══════════════════════════════════════════════════════════════

@app.get("/")
async def root(request: Request):
    """Root redirect to gate."""
    from fastapi.responses import RedirectResponse
    base = get_base_path(request)
    return RedirectResponse(url=f"{base}/gate", status_code=301)

@app.get("/info")
async def info(request: Request):
    """Service info endpoint."""
    base = get_base_path(request)
    return JSONResponse(
        status_code=200,
        content={
            "service": f"WINDI-LAW Identity Gate {VERSION}",
            "gate_url": f"{base}/gate",
            "health_url": f"{base}/health",
            "register_url": f"{base}/register",
            "invariants": ["I9", "I11", "I13", "G3"],
            "blocking_rule": "if(!did||!wallet){blockWorkspace()}"
        }
    )


# ═══════════════════════════════════════════════════════════════
# §121 — LAW AGENT CORPS PROXY
# Forwards requests to constitutional-agent on :8093
# ═══════════════════════════════════════════════════════════════

AGENT_CORPS_URL = "http://127.0.0.1:8093"

@app.api_route("/agents/{agent_type}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_to_agent_corps(agent_type: str, path: str, request: Request):
    """
    Proxy requests to LAW Agent Corps (W-LEGAL, W-NOTARY, W-AUDIT, W-COMPLY, W-ACCT)

    Routes:
      /agents/legal/*       → :8093/legal/*
      /agents/notary/*      → :8093/notary/*
      /agents/audit/*       → :8093/audit/*
      /agents/compliance/*  → :8093/compliance/*
      /agents/accounting/*  → :8093/accounting/*
    """
    allowed_agents = ["legal", "notary", "audit", "compliance", "accounting", "grove"]

    if agent_type not in allowed_agents:
        raise HTTPException(404, f"Agent '{agent_type}' not found. Available: {allowed_agents}")

    # Build target URL
    target_url = f"{AGENT_CORPS_URL}/{agent_type}/{path}"

    # Forward request
    try:
        body = await request.body()
        headers = {
            "Content-Type": request.headers.get("content-type", "application/json"),
            "X-Forwarded-For": request.client.host if request.client else "unknown",
            "X-Original-Path": f"/agents/{agent_type}/{path}"
        }

        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=body,
            timeout=30
        )

        return JSONResponse(
            content=resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"raw": resp.text},
            status_code=resp.status_code
        )
    except requests.exceptions.ConnectionError:
        raise HTTPException(503, "LAW Agent Corps unavailable. Please try again.")
    except Exception as e:
        raise HTTPException(500, f"Proxy error: {str(e)}")


@app.get("/agents/health")
async def agent_corps_health():
    """Check LAW Agent Corps health"""
    try:
        resp = requests.get(f"{AGENT_CORPS_URL}/health", timeout=5)
        data = resp.json()
        data["proxy"] = "identity-gate"
        data["agents_available"] = ["legal", "notary", "audit", "compliance", "accounting"]
        return data
    except:
        return {"status": "unavailable", "message": "LAW Agent Corps not responding on :8093"}


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8122)
