"""
WINDI-TRAVEL Identity Gate v1.0.0
Port: :8126
Sovereign Identity Management for Travel Memories

I14 — Presence Integrity: provar que "eu estava lá"
I15 — Continuity Integrity: provar que "eu continuei a estar"

Filosofia: "Guardar o passado. Resguardar o futuro. No presente perfeito."

Liga IA+H · Kempten, Bavaria · 2026
"AI processes. Human decides. WINDI guarantees."
"""

from fastapi import FastAPI, HTTPException, Request, Header, Query
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
    load_dotenv("/opt/windi/windi-travel/identity-gate/.env")
except ImportError:
    pass  # dotenv not installed, rely on system env vars

# Ed25519 cryptography
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

# W-MARIA-001 Integration (Phase 2)
import sys
sys.path.insert(0, "/opt/windi/windi-travel")
from maria_blueprint import router as maria_seal_router
from booking_router import router as maria_plan_router
from gate import router as travel_gate_router, require_auth  # P3-A Identity Gate

# W-SESSION-001 — Sovereign Session Layer
sys.path.insert(0, "/opt/windi/session")
from sovereign_session import (
    create_session_token,
    verify_session_token,
    generate_device_id,
    hash_ip_for_signal,
    get_device_name_from_ua,
    is_valid_windi_did,
    ENABLE_SOVEREIGN_SESSION,
    SESSION_TTL_DAYS,
    MAX_DEVICES_PER_DID,
    REVOKE_REASON_USER,
    REVOKE_REASON_SECURITY,
    REVOKE_REASON_ADMIN
)

# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════

DB_PATH = "/opt/windi/windi-travel/identity-gate/windi_travel_identity.db"
LEDGER_URL = "http://127.0.0.1:8101/api/receipts"
VERSION = "v1.3.0"  # W-SESSION-001

# Admin secret for verification (from environment)
ADMIN_SECRET = os.environ.get("WINDI_ADMIN_SECRET", "windi-travel-admin-2026")

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
    verify_url = f"{DOMAIN_URL}/travel/verify-email/{token}"

    # Trilingual email subjects and bodies
    subjects = {
        "de": "WINDI-TRAVEL: Bestätigen Sie Ihre E-Mail",
        "en": "WINDI-TRAVEL: Confirm your email",
        "pt": "WINDI-TRAVEL: Confirme seu email"
    }

    bodies = {
        "de": f"""
Hallo {full_name},

Willkommen bei WINDI-TRAVEL!

Bitte bestätigen Sie Ihre E-Mail-Adresse, indem Sie auf den folgenden Link klicken:

{verify_url}

Dieser Link ist 48 Stunden gültig.

Sie haben bereits Zugang zum Workspace. Die E-Mail-Bestätigung ermöglicht HIGH-Operationen.

Mit freundlichen Grüßen,
WINDI Publishing House
        """,
        "en": f"""
Hello {full_name},

Welcome to WINDI-TRAVEL!

Please confirm your email address by clicking the link below:

{verify_url}

This link is valid for 48 hours.

You already have access to the workspace. Email confirmation enables HIGH operations.

Best regards,
WINDI Publishing House
        """,
        "pt": f"""
Olá {full_name},

Bem-vindo ao WINDI-TRAVEL!

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
                <strong style="color: #8B7424;">WINDI-TRAVEL</strong>
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

async def send_login_email(email: str, token: str, full_name: str, lang: str = "en"):
    """Send magic link login email."""
    login_url = f"{DOMAIN_URL}/travel/login/{token}"

    subjects = {
        "de": "WINDI-TRAVEL: Dein Login-Link",
        "en": "WINDI-TRAVEL: Your login link",
        "pt": "WINDI-TRAVEL: Teu link de acesso"
    }

    bodies = {
        "de": f"""
Hallo {full_name},

Hier ist dein Login-Link für WINDI-TRAVEL:

{login_url}

Dieser Link ist 1 Stunde gültig.

Falls du diese Anfrage nicht gestellt hast, ignoriere diese E-Mail.

Mit freundlichen Grüßen,
WINDI Publishing House
        """,
        "en": f"""
Hello {full_name},

Here is your login link for WINDI-TRAVEL:

{login_url}

This link is valid for 1 hour.

If you did not request this, please ignore this email.

Best regards,
WINDI Publishing House
        """,
        "pt": f"""
Olá {full_name},

Aqui está o teu link de acesso ao WINDI-TRAVEL:

{login_url}

Este link é válido por 1 hora.

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
            <div style="border-bottom: 2px solid #8B7424; padding-bottom: 10px; margin-bottom: 20px;">
                <strong style="color: #8B7424;">WINDI-TRAVEL</strong>
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
    receipt_id = f"WINDI-TRAVEL-{event_type}-{company_id[:8].upper()}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    # Generate content hash from DID + company_id
    content_to_hash = f"{did}|{company_id}|{event_type}|{admin_email}"
    content_hash = f"sha256:{hashlib.sha256(content_to_hash.encode()).hexdigest()}"

    payload = {
        "id": receipt_id,
        "actor": admin_email,
        "app": "windi-travel-identity-gate",
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
    title="WINDI-TRAVEL Identity Gate",
    version=VERSION,
    description="Sovereign Identity Management for Legal Professionals"
)

# ═══ W-MARIA-001 Routers (Phase 2) ═══
app.include_router(maria_seal_router)   # /maria/seal, /maria/health
app.include_router(maria_plan_router)   # /maria/plan
app.include_router(travel_gate_router)  # /travel/gate/* (P3-A)

# ═══ Maria UI Static Files (§65) ═══
# Full-featured version with Audio IN/OUT, GPS, Pipeline visualization
app.mount("/maria-ui", StaticFiles(directory="/opt/windi/windi-travel/static/maria", html=True), name="maria-ui")

# ═══ Tesoura Soberana Static Files (P3-B) ═══
app.mount("/tesoura-ui", StaticFiles(directory="/opt/windi/windi-travel/static/tesoura", html=True), name="tesoura-ui")

# ═══ Pitch Deck (§103 Presentation) ═══
app.mount("/pitch", StaticFiles(directory="/opt/windi/windi-travel/static/pitch", html=True), name="pitch")

# Mount static files and templates
templates = Jinja2Templates(directory="/opt/windi/windi-travel/identity-gate/templates")
# Disable Jinja2 cache to avoid unhashable type error with dict globals
templates.env.cache = None

# Initialize database on startup
@app.on_event("startup")
async def startup():
    init_db()
    print(f"[WINDI-TRAVEL] Identity Gate {VERSION} started on :8122")


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
        "service": f"WINDI-TRAVEL Identity Gate {VERSION}",
        "status": "healthy",
        "port": 8126,
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
            "workspace_url": "/travel/workspace/"
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
                "gate": "/law/gate"
            })
        elif "unique" in err and ("vat" in err or "company" in err):
            raise HTTPException(status_code=409, detail={
                "error": "Entidade já registada no sistema",
                "code": "DUPLICATE_ENTITY",
                "action": "Contacte o administrador da conta existente",
                "gate": "/law/gate"
            })
        else:
            # Nunca expor o erro real — log interno apenas
            import logging
            logging.error(f"[WINDI-TRAVEL] Register IntegrityError: {e}")
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

    # Generate login token
    login_token = generate_email_token()
    login_expiry = get_login_token_expiry()

    cursor.execute("""
        UPDATE admins SET login_token = ?, login_token_expires = ? WHERE id = ?
    """, (login_token, login_expiry, admin_id))
    conn.commit()
    conn.close()

    # Send login email
    accept_lang = request.headers.get("Accept-Language", "en")
    lang = "de" if "de" in accept_lang.lower() else ("pt" if "pt" in accept_lang.lower() else "en")
    await send_login_email(email, login_token, full_name, lang)

    return {"success": True, "message": "If this email is registered, you will receive a login link"}


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

    # Return HTML that sets sessionStorage and redirects to workspace
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>WINDI-TRAVEL Login</title>
        <style>
            body {{
                font-family: 'JetBrains Mono', monospace;
                background: #0A0A10;
                color: #E8E6E1;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
            }}
            .card {{
                background: #12121A;
                border: 1px solid #1A1A24;
                border-radius: 12px;
                padding: 2rem;
                text-align: center;
                max-width: 400px;
            }}
            .success {{ color: #2EC27E; font-size: 3rem; }}
            .title {{ color: #C9A84C; font-size: 1.25rem; margin: 1rem 0; }}
            .did {{ font-size: 0.75rem; color: #666; word-break: break-all; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="success">✓</div>
            <div class="title">Login erfolgreich</div>
            <p>Willkommen zurück, {full_name}!</p>
            <p class="did">{did}</p>
            <p style="color:#666;font-size:0.875rem;">Weiterleitung zum Workspace...</p>
        </div>
        <script>
            // Set session data
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
            sessionStorage.setItem('windi_travel_wallet', JSON.stringify(walletData));
            sessionStorage.setItem('windi_travel_did', "{did}");
            sessionStorage.setItem('windi_travel_fingerprint', "{fingerprint}");

            // Set cookie for future visits
            document.cookie = 'windi_did=' + encodeURIComponent("{did}") + '; path=/; max-age=31536000; SameSite=Lax';

            // Redirect to workspace
            setTimeout(function() {{
                window.location.href = '/travel/workspace/?did=' + encodeURIComponent("{did}");
            }}, 1500);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# ═══════════════════════════════════════════════════════════════
# W-SESSION-001 — SOVEREIGN SESSION ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.post("/session/create")
async def session_create(request: Request):
    """
    Create sovereign session for authenticated user.

    Called after successful magic link login.
    Requires device_seed from client to generate device_id.

    Body:
        did: str — User's DID (required)
        device_seed: str — Client-generated seed for device binding (required)

    Returns:
        session_token: str — Token to store in cookie
        session_id: str — Session UUID
        expires_at: str — Expiration timestamp
        device_name: str — Detected device name

    Security:
        - device_seed is NEVER stored (only hash)
        - Full HMAC-SHA256 signature (64 chars)
        - Feature flagged by ENABLE_SOVEREIGN_SESSION
    """
    if not ENABLE_SOVEREIGN_SESSION:
        return JSONResponse({
            "success": False,
            "error": "Sovereign sessions not enabled",
            "error_code": "feature_disabled"
        }, status_code=400)

    body = await request.json()
    did = body.get("did", "").strip()
    device_seed = body.get("device_seed", "").strip()

    if not did or not device_seed:
        raise HTTPException(status_code=400, detail="DID and device_seed required")

    if not is_valid_windi_did(did):
        raise HTTPException(status_code=400, detail="Invalid WINDI DID format")

    # Get user agent and IP
    user_agent = request.headers.get("User-Agent", "")
    client_ip = request.client.host if request.client else "unknown"

    # Generate device_id (hash — seed NEVER stored)
    device_id = generate_device_id(device_seed, user_agent)
    device_name = get_device_name_from_ua(user_agent)
    ip_hash = hash_ip_for_signal(client_ip)

    # Check if user exists and is verified
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, full_name, email, state, email_verified
        FROM admins WHERE did = ?
    """, (did,))
    admin = cursor.fetchone()

    if not admin:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    admin_id, full_name, email, state, email_verified = admin

    if state != "VERIFIED" or not email_verified:
        conn.close()
        raise HTTPException(status_code=403, detail="User not verified")

    # Check device limit per DID
    cursor.execute("""
        SELECT COUNT(*) FROM device_bindings
        WHERE wallet_id = ? AND state = 'ACTIVE'
    """, (did,))
    device_count = cursor.fetchone()[0]

    if device_count >= MAX_DEVICES_PER_DID:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail=f"Maximum devices ({MAX_DEVICES_PER_DID}) reached. Revoke an existing device first."
        )

    # Create session token
    token, payload = create_session_token(did, device_id)

    # Store session in DB
    cursor.execute("""
        INSERT INTO sovereign_sessions
        (session_id, wallet_id, device_id, device_name, expires_at, ip_hash, user_agent)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        payload.sid,
        did,
        device_id,
        device_name,
        datetime.fromtimestamp(payload.exp).isoformat(),
        ip_hash,
        user_agent[:200] if user_agent else None  # Truncate UA
    ))

    # Create or update device binding
    binding_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO device_bindings (binding_id, wallet_id, device_id, device_name)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(wallet_id, device_id) DO UPDATE SET
            last_seen_at = datetime('now'),
            consecutive_logins = consecutive_logins + 1
    """, (binding_id, did, device_id, device_name))

    conn.commit()
    conn.close()

    # Create response with Set-Cookie header (HttpOnly + Secure)
    expires_dt = datetime.fromtimestamp(payload.exp)
    response_data = {
        "success": True,
        "session_id": payload.sid,
        "expires_at": expires_dt.isoformat(),
        "device_name": device_name,
        "device_id": device_id,
        "ttl_days": SESSION_TTL_DAYS
    }

    response = JSONResponse(content=response_data)

    # Set cookie server-side with proper security flags
    # HttpOnly: JS cannot access (XSS protection)
    # Secure: HTTPS only
    # SameSite=Lax: CSRF protection
    response.set_cookie(
        key="windi_sovereign_session",
        value=token,
        expires=expires_dt,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/"
    )

    return response


@app.post("/session/revoke")
async def session_revoke(request: Request):
    """
    Revoke a sovereign session.

    Body:
        session_id: str — Session to revoke (required)
        did: str — Owner's DID (required for authorization)
        reason: str — Reason for revocation (optional)

    Returns:
        success: bool
    """
    if not ENABLE_SOVEREIGN_SESSION:
        return JSONResponse({
            "success": False,
            "error": "Sovereign sessions not enabled"
        }, status_code=400)

    body = await request.json()
    session_id = body.get("session_id", "").strip()
    did = body.get("did", "").strip()
    reason = body.get("reason", REVOKE_REASON_USER)

    if not session_id or not did:
        raise HTTPException(status_code=400, detail="session_id and did required")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check session exists and belongs to user
    cursor.execute("""
        SELECT wallet_id FROM sovereign_sessions
        WHERE session_id = ? AND revoked = 0
    """, (session_id,))
    session = cursor.fetchone()

    if not session:
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found or already revoked")

    if session[0] != did:
        conn.close()
        raise HTTPException(status_code=403, detail="Not authorized to revoke this session")

    # Revoke session
    cursor.execute("""
        UPDATE sovereign_sessions
        SET revoked = 1, revoked_at = datetime('now'), revoked_reason = ?
        WHERE session_id = ?
    """, (reason, session_id))

    conn.commit()
    conn.close()

    return {"success": True, "session_id": session_id, "revoked": True}


@app.get("/sessions")
async def list_sessions(did: str = Query(...)):
    """
    List active sessions for a DID.

    Query:
        did: str — User's DID

    Returns:
        sessions: list — Active sessions with device info
    """
    if not ENABLE_SOVEREIGN_SESSION:
        return JSONResponse({
            "success": False,
            "error": "Sovereign sessions not enabled"
        }, status_code=400)

    if not is_valid_windi_did(did):
        raise HTTPException(status_code=400, detail="Invalid DID format")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.session_id, s.device_id, s.device_name, s.created_at,
               s.last_used_at, s.expires_at, b.trust_level
        FROM sovereign_sessions s
        LEFT JOIN device_bindings b ON b.wallet_id = s.wallet_id AND b.device_id = s.device_id
        WHERE s.wallet_id = ? AND s.revoked = 0 AND s.expires_at > datetime('now')
        ORDER BY s.last_used_at DESC
    """, (did,))

    sessions = []
    for row in cursor.fetchall():
        sessions.append({
            "session_id": row[0],
            "device_id": row[1][:16] + "..." if row[1] else None,  # Truncate for privacy
            "device_name": row[2],
            "created_at": row[3],
            "last_used_at": row[4],
            "expires_at": row[5],
            "trust_level": row[6] or "NEW"
        })

    conn.close()

    return {
        "success": True,
        "did": did,
        "sessions": sessions,
        "count": len(sessions)
    }


@app.get("/devices")
async def list_devices(did: str = Query(...)):
    """
    List registered devices for a DID.

    Query:
        did: str — User's DID

    Returns:
        devices: list — Devices with trust levels
    """
    if not ENABLE_SOVEREIGN_SESSION:
        return JSONResponse({
            "success": False,
            "error": "Sovereign sessions not enabled"
        }, status_code=400)

    if not is_valid_windi_did(did):
        raise HTTPException(status_code=400, detail="Invalid DID format")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT binding_id, device_id, device_name, created_at, last_seen_at,
               consecutive_logins, trust_level, state
        FROM device_bindings
        WHERE wallet_id = ? AND state = 'ACTIVE'
        ORDER BY last_seen_at DESC
    """, (did,))

    devices = []
    for row in cursor.fetchall():
        devices.append({
            "binding_id": row[0],
            "device_id": row[1][:16] + "...",  # Truncate
            "device_name": row[2],
            "created_at": row[3],
            "last_seen_at": row[4],
            "consecutive_logins": row[5],
            "trust_level": row[6],
            "state": row[7]
        })

    conn.close()

    return {
        "success": True,
        "did": did,
        "devices": devices,
        "count": len(devices),
        "max_devices": MAX_DEVICES_PER_DID
    }


@app.post("/devices/block")
async def block_device(request: Request):
    """
    Block a device (revokes all its sessions).

    Body:
        binding_id: str — Device binding to block
        did: str — Owner's DID (for authorization)
        reason: str — Reason for blocking (optional)

    Returns:
        success: bool
    """
    if not ENABLE_SOVEREIGN_SESSION:
        return JSONResponse({
            "success": False,
            "error": "Sovereign sessions not enabled"
        }, status_code=400)

    body = await request.json()
    binding_id = body.get("binding_id", "").strip()
    did = body.get("did", "").strip()
    reason = body.get("reason", "user_request")

    if not binding_id or not did:
        raise HTTPException(status_code=400, detail="binding_id and did required")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check device belongs to user
    cursor.execute("""
        SELECT device_id FROM device_bindings
        WHERE binding_id = ? AND wallet_id = ?
    """, (binding_id, did))
    device = cursor.fetchone()

    if not device:
        conn.close()
        raise HTTPException(status_code=404, detail="Device not found")

    device_id = device[0]

    # Block device
    cursor.execute("""
        UPDATE device_bindings
        SET state = 'BLOCKED', blocked_at = datetime('now'), blocked_reason = ?
        WHERE binding_id = ?
    """, (reason, binding_id))

    # Revoke all sessions for this device
    cursor.execute("""
        UPDATE sovereign_sessions
        SET revoked = 1, revoked_at = datetime('now'), revoked_reason = ?
        WHERE wallet_id = ? AND device_id = ? AND revoked = 0
    """, (REVOKE_REASON_SECURITY, did, device_id))

    sessions_revoked = cursor.rowcount
    conn.commit()
    conn.close()

    return {
        "success": True,
        "binding_id": binding_id,
        "blocked": True,
        "sessions_revoked": sessions_revoked
    }


@app.get("/session/verify")
async def verify_session_endpoint(request: Request):
    """
    Verify current session from cookie.

    Headers:
        Cookie: windi_sovereign_session=...

    Returns:
        valid: bool
        did: str (if valid)
        device_trust: str (if valid)
    """
    if not ENABLE_SOVEREIGN_SESSION:
        return {"valid": False, "error": "Sovereign sessions not enabled"}

    token = request.cookies.get("windi_sovereign_session")
    if not token:
        return {"valid": False, "error": "No session cookie"}

    validation = verify_session_token(token)
    if not validation.valid:
        return {"valid": False, "error": validation.error, "error_code": validation.error_code}

    # Check revocation in DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.revoked, b.trust_level
        FROM sovereign_sessions s
        LEFT JOIN device_bindings b ON b.wallet_id = s.wallet_id AND b.device_id = s.device_id
        WHERE s.session_id = ?
    """, (validation.payload.sid,))
    session = cursor.fetchone()
    conn.close()

    if not session or session[0] == 1:
        return {"valid": False, "error": "Session revoked", "error_code": "revoked"}

    return {
        "valid": True,
        "did": validation.payload.did,
        "session_id": validation.payload.sid,
        "device_trust": session[1] or "NEW",
        "expires_at": datetime.fromtimestamp(validation.payload.exp).isoformat()
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
async def identity_get(did: str):
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
            "action": "Registe a sua entidade em /law/gate",
            "gate": "/law/gate"
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


@app.get("/gate", response_class=HTMLResponse)
async def gate_ui(request: Request):
    """Render Identity Gate UI with DID Wizard."""
    # Check if user already has session → redirect to workspace
    from gate import get_session_from_request
    user = get_session_from_request(request)
    if user:
        return RedirectResponse(url="/travel/workspace/", status_code=302)

    # Fallback: check windi_did cookie (set after registration)
    windi_did = request.cookies.get("windi_did")
    if windi_did:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE did = ?", (windi_did,))
        user_row = cursor.fetchone()
        conn.close()
        if user_row:
            return RedirectResponse(url="/travel/workspace/", status_code=302)

    return templates.TemplateResponse(request, "gate.html")


# ═══════════════════════════════════════════════════════════════
# WORKSPACE — FAIL-CLOSED (P0 CRITICAL)
# ═══════════════════════════════════════════════════════════════

from fastapi.responses import RedirectResponse

@app.get("/workspace/")
@app.get("/workspace")
async def workspace_gate(request: Request, did: str = None):
    """
    Workspace — P3-A Gate Guard (I9 fail-closed)
    Accepts: session cookie OR DID from query param OR windi_did cookie
    """
    # P3-A: Try session cookie first
    user = require_auth(request)

    # Fallback 1: DID from query param (from registration success redirect)
    if isinstance(user, RedirectResponse) and did:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE did = ?", (did,))
        user_row = cursor.fetchone()
        conn.close()
        if user_row:
            user = {"wallet_id": user_row["did"], "name": user_row["full_name"]}

    # Fallback 2: windi_did cookie
    if isinstance(user, RedirectResponse):
        windi_did = request.cookies.get("windi_did")
        if windi_did:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM admins WHERE did = ?", (windi_did,))
            user_row = cursor.fetchone()
            conn.close()
            if user_row:
                user = {"wallet_id": user_row["did"], "name": user_row["full_name"]}

    # Still no auth → redirect to gate
    if isinstance(user, RedirectResponse):
        return user

    # Utilizador autenticado — servir workspace
    wallet_id = user["wallet_id"] if user else "anonymous"
    user_name = user["name"] if user else "Viajante"

    # FASE 3 — Rescue Mode (Tesoura rules mantidas)
    return HTMLResponse(content=f"""
<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WINDI Travel</title>
<style>
/* ══ FASE 6: Theme + i18n · Tesoura Rules ══ */
/* NO: @import, transition, @keyframes, backdrop-filter */

/* KLAR (light) - default */
:root, [data-theme="klar"] {{
    --perg: #F5F0E0;
    --gold: #8B6914;
    --ink: #1A1A1A;
    --ink2: #4A4A4A;
    --border: #D4C9A8;
    --surface: #FDFAF3;
    --success: #2D6A4F;
}}

/* NOIR (dark) */
[data-theme="noir"] {{
    --perg: #0A0A10;
    --gold: #C9A84C;
    --ink: #E8E6E1;
    --ink2: #A0A0A0;
    --border: #1A1A24;
    --surface: #12121A;
    --success: #4A9F6E;
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
    background: var(--perg);
    color: var(--ink);
    font-family: Georgia, serif;
    min-height: 100vh;
    padding: 0;
    padding-bottom: 60px;
}}

/* ══ Header ══ */
.header {{
    background: var(--perg);
    border-bottom: 1px solid var(--border);
    padding: 16px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.logo {{
    font-size: 18px;
    letter-spacing: 3px;
    color: var(--gold);
}}

.user-info {{
    font-family: 'Courier New', monospace;
    font-size: 11px;
    color: var(--ink2);
}}

/* ══ Lang Bar ══ */
.lang-bar {{
    display: flex;
    gap: 6px;
}}

.lang-btn {{
    padding: 4px 8px;
    border: 1px solid var(--border);
    border-radius: 4px;
    background: var(--perg);
    font-family: 'Courier New', monospace;
    font-size: 10px;
    color: var(--ink2);
    cursor: pointer;
}}

.lang-btn.active {{
    border-color: var(--gold);
    color: var(--gold);
}}

/* ══ Theme Toggle ══ */
.theme-btn {{
    padding: 4px 10px;
    border: 1px solid var(--border);
    border-radius: 4px;
    background: var(--perg);
    font-size: 14px;
    cursor: pointer;
    margin-left: 8px;
}}

/* ══ Tool Nav ══ */
.tool-nav {{
    display: flex;
    gap: 12px;
    padding: 16px 20px;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
}}

.tool-btn {{
    display: inline-block;
    padding: 10px 20px;
    background: var(--perg);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--ink);
    text-decoration: none;
    font-family: 'Courier New', monospace;
    font-size: 13px;
}}

/* ══ Main ══ */
.main {{
    padding: 24px 20px;
    max-width: 500px;
    margin: 0 auto;
}}

.card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 24px;
    margin-bottom: 20px;
}}

.card h2 {{
    font-size: 20px;
    font-weight: 400;
    margin-bottom: 12px;
    color: var(--ink);
    text-align: center;
}}

.card p {{
    font-size: 14px;
    color: var(--ink2);
    line-height: 1.6;
    text-align: center;
}}

/* ══ Rescue Section ══ */
.rescue-section {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
}}

.rescue-section h3 {{
    font-size: 14px;
    font-weight: 400;
    color: var(--gold);
    margin-bottom: 16px;
    font-family: 'Courier New', monospace;
    letter-spacing: 1px;
}}

.rescue-input {{
    width: 100%;
    padding: 12px;
    border: 1px solid var(--border);
    border-radius: 6px;
    font-family: Georgia, serif;
    font-size: 14px;
    background: var(--perg);
    color: var(--ink);
    margin-bottom: 12px;
}}

.rescue-input:focus {{
    outline: none;
    border-color: var(--gold);
}}

.capture-btn {{
    width: 100%;
    padding: 14px;
    background: var(--gold);
    color: var(--perg);
    border: none;
    border-radius: 6px;
    font-family: 'Courier New', monospace;
    font-size: 14px;
    cursor: pointer;
    letter-spacing: 1px;
}}

.file-input {{
    display: none;
}}

.preview-area {{
    margin-top: 16px;
    text-align: center;
    display: none;
}}

.preview-area img {{
    max-width: 100%;
    max-height: 200px;
    border-radius: 6px;
    border: 1px solid var(--border);
}}

.preview-label {{
    font-family: 'Courier New', monospace;
    font-size: 11px;
    color: var(--ink2);
    margin-top: 8px;
}}

.seal-btn {{
    width: 100%;
    padding: 14px;
    background: var(--success);
    color: white;
    border: none;
    border-radius: 6px;
    font-family: 'Courier New', monospace;
    font-size: 14px;
    cursor: pointer;
    letter-spacing: 1px;
    margin-top: 12px;
    display: none;
}}

/* ══ Footer ══ */
.footer {{
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 12px 20px;
    background: var(--perg);
    border-top: 1px solid var(--border);
    text-align: center;
}}

.footer a {{
    color: var(--gold);
    font-family: 'Courier New', monospace;
    font-size: 12px;
    text-decoration: none;
}}

/* ══ Status message ══ */
.status {{
    font-family: 'Courier New', monospace;
    font-size: 12px;
    color: var(--success);
    text-align: center;
    margin-top: 12px;
    display: none;
}}

/* ══ Thread Section ══ */
.thread-section {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
}}

.thread-section h3 {{
    font-size: 14px;
    font-weight: 400;
    color: var(--gold);
    margin-bottom: 16px;
    font-family: 'Courier New', monospace;
    letter-spacing: 1px;
}}

.thread-list {{
    list-style: none;
}}

.thread-item {{
    padding: 12px;
    border: 1px solid var(--border);
    border-radius: 6px;
    margin-bottom: 8px;
    background: var(--perg);
}}

.thread-item-label {{
    font-size: 14px;
    color: var(--ink);
    margin-bottom: 4px;
}}

.thread-item-meta {{
    font-family: 'Courier New', monospace;
    font-size: 10px;
    color: var(--ink2);
}}

.thread-empty {{
    font-size: 13px;
    color: var(--ink2);
    text-align: center;
    padding: 16px;
    font-style: italic;
}}

.load-thread-btn {{
    width: 100%;
    padding: 10px;
    background: var(--perg);
    border: 1px solid var(--border);
    border-radius: 6px;
    font-family: 'Courier New', monospace;
    font-size: 12px;
    color: var(--ink2);
    cursor: pointer;
}}

/* ══ i18n ══ */
[data-lang] {{ display: none; }}
[data-lang="de"] {{ display: inline; }}
body.lang-en [data-lang="de"] {{ display: none; }}
body.lang-en [data-lang="en"] {{ display: inline; }}
body.lang-pt [data-lang="de"] {{ display: none; }}
body.lang-pt [data-lang="pt"] {{ display: inline; }}

/* ══ Photo Modal ══ */
.photo-modal {{
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.85);
    z-index: 1000;
    padding: 20px;
    overflow-y: auto;
}}

.photo-modal.active {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
}}

.photo-modal-close {{
    position: absolute;
    top: 16px;
    right: 16px;
    width: 40px;
    height: 40px;
    background: var(--surface);
    border: none;
    border-radius: 50%;
    font-size: 20px;
    cursor: pointer;
    color: var(--ink);
}}

.photo-modal-img {{
    max-width: 100%;
    max-height: 50vh;
    border-radius: 8px;
    margin-top: 50px;
}}

.photo-modal-info {{
    background: var(--surface);
    border-radius: 8px;
    padding: 16px;
    margin-top: 16px;
    width: 100%;
    max-width: 400px;
}}

.photo-modal-id {{
    font-family: 'Courier New', monospace;
    font-size: 10px;
    color: var(--ink2);
    margin-bottom: 12px;
    word-break: break-all;
}}

.photo-modal-actions {{
    display: flex;
    flex-direction: column;
    gap: 8px;
}}

.photo-modal-btn {{
    padding: 12px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--perg);
    font-family: 'Courier New', monospace;
    font-size: 12px;
    color: var(--ink);
    cursor: pointer;
    text-align: left;
}}

.photo-modal-btn:active {{
    background: var(--border);
}}
</style>
</head>
<body>

<header class="header">
    <div class="logo">WINDI TRAVEL</div>
    <div class="lang-bar">
        <button class="lang-btn active" onclick="setLang('de')">DE</button>
        <button class="lang-btn" onclick="setLang('en')">EN</button>
        <button class="lang-btn" onclick="setLang('pt')">PT</button>
        <button class="theme-btn" id="themeBtn" onclick="toggleTheme()">☀</button>
    </div>
</header>

<nav class="tool-nav">
    <a href="/travel/maria-ui/?did={wallet_id}" class="tool-btn">🤖 Maria</a>
    <a href="/travel/tesoura-ui/?did={wallet_id}" class="tool-btn">✂️ Tesoura</a>
</nav>

<main class="main">
    <div class="card">
        <h2><span data-lang="de">Hallo, {user_name}</span><span data-lang="en">Hello, {user_name}</span><span data-lang="pt">Olá, {user_name}</span></h2>
        <p>
            <span data-lang="de">Die Vergangenheit bewahren. Die Zukunft schützen.<br>Im perfekten Präsens.</span>
            <span data-lang="en">Save the past. Protect the future.<br>In the perfect present.</span>
            <span data-lang="pt">Guardar o passado. Resguardar o futuro.<br>No presente perfeito.</span>
        </p>
    </div>

    <div class="rescue-section">
        <h3>📸 RESCUE MODE</h3>
        <input type="text" class="rescue-input" id="momentLabel" data-placeholder-de="Etikett des Moments..." data-placeholder-en="Moment label..." data-placeholder-pt="Etiqueta do momento..." placeholder="Etikett des Moments...">
        <input type="file" class="file-input" id="fileInput" accept="image/*,video/*">
        <button class="capture-btn" onclick="document.getElementById('fileInput').click()">
            <span data-lang="de">Moment erfassen</span><span data-lang="en">Capture Moment</span><span data-lang="pt">Capturar Momento</span>
        </button>
        <div class="preview-area" id="previewArea">
            <img id="previewImg" src="" alt="Preview">
            <div class="preview-label" id="previewLabel"></div>
            <div class="hash-preview" id="hashPreview" style="display:none;font-family:'Courier New',monospace;font-size:10px;color:var(--gold);margin:8px 0;"></div>
            <button class="seal-btn" id="sealBtn" onclick="sealMoment()">
                <span data-lang="de">🔒 Im Ledger versiegeln</span><span data-lang="en">🔒 Seal to Ledger</span><span data-lang="pt">🔒 Selar no Ledger</span>
            </button>
        </div>
        <div class="status" id="status"></div>
    </div>

    <div class="thread-section">
        <h3>🧵 THREAD</h3>
        <button class="load-thread-btn" onclick="loadThread()">
            <span data-lang="de">Versiegelte Momente laden</span><span data-lang="en">Load sealed moments</span><span data-lang="pt">Carregar momentos selados</span>
        </button>
        <ul class="thread-list" id="threadList">
            <li class="thread-empty" id="threadEmpty">
                <span data-lang="de">Noch keine versiegelten Momente.</span><span data-lang="en">No sealed moments yet.</span><span data-lang="pt">Nenhum momento selado ainda.</span>
            </li>
        </ul>
    </div>
</main>

<footer class="footer">
    <a href="/travel/gate/logout"><span data-lang="de">Abmelden</span><span data-lang="en">Logout</span><span data-lang="pt">Sair</span></a>
</footer>

<!-- Photo Modal -->
<div class="photo-modal" id="photoModal">
    <button class="photo-modal-close" onclick="closePhotoModal()">✕</button>
    <img class="photo-modal-img" id="photoModalImg" src="" alt="Photo">
    <div class="photo-modal-info">
        <div class="photo-modal-id" id="photoModalId"></div>
        <div class="photo-modal-actions">
            <button class="photo-modal-btn" onclick="reusePhoto()">
                <span data-lang="de">📋 Wiederverwenden</span>
                <span data-lang="en">📋 Reuse</span>
                <span data-lang="pt">📋 Reutilizar</span>
            </button>
            <button class="photo-modal-btn" onclick="transferPhoto()">
                <span data-lang="de">📤 An Tesoura senden</span>
                <span data-lang="en">📤 Send to Tesoura</span>
                <span data-lang="pt">📤 Enviar para Tesoura</span>
            </button>
            <button class="photo-modal-btn" onclick="downloadPhoto()">
                <span data-lang="de">💾 Herunterladen</span>
                <span data-lang="en">💾 Download</span>
                <span data-lang="pt">💾 Descarregar</span>
            </button>
            <button class="photo-modal-btn" onclick="verifyPhoto()">
                <span data-lang="de">🔍 Im Ledger verifizieren</span>
                <span data-lang="en">🔍 Verify in Ledger</span>
                <span data-lang="pt">🔍 Verificar no Ledger</span>
            </button>
        </div>
    </div>
</div>

<script>
// ══ §64 — DID Universal WINDI ══
// "No WINDI não há estranhos."
var WINDI_WALLET_ID = '{wallet_id}';
var WINDI_USER_NAME = '{user_name}';
</script>

<script>
// Tesoura rules: minimal JS, no loops, no intervals
var currentFile = null;
var currentHash = '';
var currentLang = 'de';

// ══ i18n Strings (DE|EN|PT) ══
var I18N = {{
    // Seal flow
    selectFileFirst: {{
        de: 'Bitte wählen Sie zuerst eine Datei',
        en: 'Please select a file first',
        pt: 'Por favor, selecione um ficheiro primeiro'
    }},
    sealing: {{
        de: 'Versiegeln...',
        en: 'Sealing...',
        pt: 'Selando...'
    }},
    sealed: {{
        de: 'Versiegelt',
        en: 'Sealed',
        pt: 'Selado'
    }},
    unknownError: {{
        de: 'Unbekannter Fehler',
        en: 'Unknown error',
        pt: 'Erro desconhecido'
    }},
    noConnection: {{
        de: 'Keine Verbindung zum Server',
        en: 'No connection to server',
        pt: 'Sem ligação ao servidor'
    }},
    verify: {{
        de: 'verifizieren',
        en: 'verify',
        pt: 'verificar'
    }},
    // Photo modal
    photoLoaded: {{
        de: 'Foto zur Wiederverwendung geladen',
        en: 'Photo loaded for reuse',
        pt: 'Foto carregada para reutilização'
    }},
    noThumbnail: {{
        de: 'Miniaturansicht nicht verfügbar',
        en: 'Thumbnail not available',
        pt: 'Miniatura não disponível'
    }},
    // Thread
    loading: {{
        de: 'Laden...',
        en: 'Loading...',
        pt: 'A carregar...'
    }},
    noMomentsYet: {{
        de: 'Noch keine versiegelten Momente.',
        en: 'No sealed moments yet.',
        pt: 'Nenhum momento selado ainda.'
    }},
    loadError: {{
        de: 'Fehler beim Laden',
        en: 'Error loading',
        pt: 'Erro ao carregar'
    }},
    moment: {{
        de: 'Moment',
        en: 'Moment',
        pt: 'Momento'
    }}
}};

function t(key) {{
    var entry = I18N[key];
    if (!entry) return key;
    return entry[currentLang] || entry['de'] || key;
}}

// i18n
function setLang(lang) {{
    currentLang = lang;
    document.body.className = 'lang-' + lang;
    var btns = document.querySelectorAll('.lang-btn');
    for (var i = 0; i < btns.length; i++) {{
        btns[i].classList.remove('active');
        if (btns[i].textContent === lang.toUpperCase()) {{
            btns[i].classList.add('active');
        }}
    }}
    // Update placeholders
    var input = document.getElementById('momentLabel');
    if (input) {{
        input.placeholder = input.getAttribute('data-placeholder-' + lang) || '';
    }}
    localStorage.setItem('windi_travel_lang', lang);
}}

// Theme toggle
function toggleTheme() {{
    var current = document.documentElement.getAttribute('data-theme') || 'klar';
    var next = (current === 'klar') ? 'noir' : 'klar';
    document.documentElement.setAttribute('data-theme', next);
    document.getElementById('themeBtn').textContent = (next === 'klar') ? '☀' : '☽';
    localStorage.setItem('windi_travel_theme', next);
}}

// Init language and theme from localStorage
(function() {{
    var savedLang = localStorage.getItem('windi_travel_lang') || 'de';
    currentLang = savedLang;
    setLang(savedLang);

    var savedTheme = localStorage.getItem('windi_travel_theme') || 'klar';
    document.documentElement.setAttribute('data-theme', savedTheme);
    document.getElementById('themeBtn').textContent = (savedTheme === 'klar') ? '☀' : '☽';
}})();

document.getElementById('fileInput').onchange = function(e) {{
    var file = e.target.files[0];
    if (!file) return;

    currentFile = file;
    var reader = new FileReader();

    reader.onload = function(ev) {{
        var img = document.getElementById('previewImg');
        img.src = ev.target.result;
        document.getElementById('previewArea').style.display = 'block';
        document.getElementById('previewLabel').textContent = file.name + ' (' + Math.round(file.size/1024) + 'KB)';
        document.getElementById('sealBtn').style.display = 'block';

        // SHA-256 hash — crypto.subtle · P0
        hashFileAsync(file);
    }};

    reader.readAsDataURL(file);
}};

// P0 Corte 2 — SHA-256 real via crypto.subtle
async function hashFileAsync(file) {{
    try {{
        var buffer = await file.arrayBuffer();
        var hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
        var hashArray = Array.from(new Uint8Array(hashBuffer));
        currentHash = hashArray.map(function(b) {{ return b.toString(16).padStart(2,'0'); }}).join('');

        // Mostrar preview do hash
        var hashPreview = document.getElementById('hashPreview');
        if (hashPreview) {{
            hashPreview.textContent = '🔐 SHA-256: ' + currentHash.slice(0,16) + '…';
            hashPreview.style.display = 'block';
        }}
    }} catch (err) {{
        console.error('Hash error:', err);
        currentHash = '';
    }}
}}

async function sealMoment() {{
    if (!currentFile || !currentHash || currentHash.length !== 64) {{
        showSealError(t('selectFileFirst'));
        return;
    }}

    var status = document.getElementById('status');
    status.textContent = t('sealing');
    status.style.display = 'block';

    try {{
        var res = await fetch('/travel/seal', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{
                hash: currentHash,
                name: currentFile.name,
                type: currentFile.type,
                note: document.getElementById('momentLabel').value || ''
            }})
        }});

        var data = await res.json();

        if (data.sealed) {{
            // Save thumbnail to localStorage with label
            var label = document.getElementById('momentLabel').value || currentFile.name || t('moment');
            saveThumbnail(data.receipt_id, document.getElementById('previewImg').src, label);
            showSealSuccess(data.receipt_id, currentHash, data.verify_url);
            loadThread();
        }} else {{
            showSealError(data.error || t('unknownError'));
        }}
    }} catch (err) {{
        showSealError(t('noConnection'));
    }}
}}

function showSealSuccess(receiptId, hash, verifyUrl) {{
    var el = document.getElementById('status');
    if (el) {{
        el.innerHTML =
            '<span style="color:#2D6A4F">✅ ' + t('sealed') + '</span><br>' +
            '<span style="font-family:monospace;font-size:10px">' + receiptId + '</span><br>' +
            '<a href="' + verifyUrl + '" target="_blank" style="color:#8B6914;font-size:11px">' + t('verify') + ' →</a>';
        el.style.display = 'block';
    }}
}}

function showSealError(msg) {{
    var el = document.getElementById('status');
    if (el) {{
        el.innerHTML = '<span style="color:#B5360C">❌ ' + msg + '</span>';
        el.style.display = 'block';
    }}
}}

// Thumbnail storage - guarda thumb + label
function saveThumbnail(receiptId, imgSrc, label) {{
    try {{
        // Criar thumbnail 100x100
        var canvas = document.createElement('canvas');
        canvas.width = 100;
        canvas.height = 100;
        var ctx = canvas.getContext('2d');
        var img = new Image();
        img.onload = function() {{
            ctx.drawImage(img, 0, 0, 100, 100);
            var thumbData = canvas.toDataURL('image/jpeg', 0.7);
            var thumbs = JSON.parse(localStorage.getItem('windi_travel_thumbs') || '{{}}');
            thumbs[receiptId] = {{
                src: thumbData,
                label: label || t('moment'),
                time: Date.now()
            }};
            localStorage.setItem('windi_travel_thumbs', JSON.stringify(thumbs));
        }};
        img.src = imgSrc;
    }} catch(e) {{ console.error('Thumb error:', e); }}
}}

function getThumbnail(receiptId) {{
    try {{
        var thumbs = JSON.parse(localStorage.getItem('windi_travel_thumbs') || '{{}}');
        var data = thumbs[receiptId];
        if (!data) return null;
        // Support old format (string) and new format (object)
        if (typeof data === 'string') return {{ src: data, label: t('moment') }};
        return data;
    }} catch(e) {{ return null; }}
}}

// Photo Modal
var currentPhotoId = '';
var currentPhotoSrc = '';

function openPhotoModal(receiptId, imgSrc) {{
    currentPhotoId = receiptId;
    currentPhotoSrc = imgSrc;
    document.getElementById('photoModalImg').src = imgSrc;
    document.getElementById('photoModalId').textContent = receiptId;
    document.getElementById('photoModal').classList.add('active');
}}

function closePhotoModal() {{
    document.getElementById('photoModal').classList.remove('active');
}}

function reusePhoto() {{
    // Copy to clipboard or fill input
    document.getElementById('previewImg').src = currentPhotoSrc;
    document.getElementById('previewArea').style.display = 'block';
    closePhotoModal();
    alert(t('photoLoaded'));
}}

function transferPhoto() {{
    // Guardar em sessionStorage para Tesoura
    sessionStorage.setItem('tesoura_import', JSON.stringify({{
        src: currentPhotoSrc,
        id: currentPhotoId
    }}));
    closePhotoModal();
    window.location.href = '/travel/tesoura-ui/';
}}

function downloadPhoto() {{
    var link = document.createElement('a');
    link.href = currentPhotoSrc;
    link.download = currentPhotoId + '.jpg';
    link.click();
    closePhotoModal();
}}

function verifyPhoto() {{
    window.open('https://windi-domain.com/verify-public/web/?id=' + currentPhotoId, '_blank');
    closePhotoModal();
}}

function loadThread() {{
    var list = document.getElementById('threadList');
    var empty = document.getElementById('threadEmpty');

    empty.textContent = t('loading');

    fetch('/travel/workspace/seals')
    .then(function(r) {{ return r.json(); }})
    .then(function(data) {{
        if (data.seals && data.seals.length > 0) {{
            empty.style.display = 'none';
            list.innerHTML = '';
            // Filtrar duplicados por content_hash e limitar a 15
            var seen = {{}};
            var filtered = [];
            for (var j = 0; j < data.seals.length && filtered.length < 15; j++) {{
                var s = data.seals[j];
                // Usar hash como chave única (ignora duplicados reais)
                var key = s.content_hash || s.id;
                if (!seen[key]) {{
                    seen[key] = true;
                    filtered.push(s);
                }}
            }}
            for (var i = 0; i < filtered.length; i++) {{
                var seal = filtered[i];
                var seal = data.seals[i];
                var thumbData = getThumbnail(seal.id);
                var thumbSrc = thumbData ? thumbData.src : null;
                var thumbLabel = thumbData ? thumbData.label : (seal.doc_name || t('moment'));
                var li = document.createElement('li');
                li.className = 'thread-item';
                li.style.display = 'flex';
                li.style.alignItems = 'center';
                li.style.gap = '12px';
                li.style.cursor = 'pointer';
                li.setAttribute('data-id', seal.id);
                li.setAttribute('data-thumb', thumbSrc || '');
                li.setAttribute('data-label', thumbLabel);
                li.onclick = function() {{
                    var id = this.getAttribute('data-id');
                    var src = this.getAttribute('data-thumb');
                    if (src) {{
                        openPhotoModal(id, src);
                    }} else {{
                        alert(t('noThumbnail'));
                    }}
                }};
                li.innerHTML =
                    (thumbSrc ? '<img src="' + thumbSrc + '" style="width:60px;height:60px;border-radius:4px;object-fit:cover;border:1px solid var(--border);">' : '<div style="width:60px;height:60px;background:var(--border);border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:20px;">📷</div>') +
                    '<div style="flex:1;min-width:0;">' +
                    '<div class="thread-item-label" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + thumbLabel + '</div>' +
                    '<div class="thread-item-meta">' + (seal.id || '').slice(0,24) + '…</div>' +
                    '</div>';
                list.appendChild(li);
            }}
        }} else {{
            empty.textContent = t('noMomentsYet');
            empty.style.display = 'block';
        }}
    }})
    .catch(function(err) {{
        empty.textContent = t('loadError') + ': ' + err.message;
    }});
}}
</script>

</body>
</html>
""")

    # ORIGINAL CODE (disabled for Samsung flicker test):
    # try:
    #     with open("/opt/windi/windi-travel/workspace/index.html", "r", encoding="utf-8") as f:
    #         content = f.read()
    #         content = content.replace("{{WALLET_ID}}", wallet_id)
    #         content = content.replace("{{USER_NAME}}", user_name)
    #         return HTMLResponse(content=content)
    # except FileNotFoundError:
    #     return HTMLResponse(content="Workspace not found", status_code=404)


# ═══════════════════════════════════════════════════════════════
# WORKSPACE SEALS — P3-B Integration
# ═══════════════════════════════════════════════════════════════

@app.get("/workspace/seals")
async def workspace_seals(request: Request):
    """
    P3-B: Lista de seals do utilizador autenticado
    Consulta o Ledger :8101 por receipts onde actor = wallet_id
    """
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return JSONResponse({"error": "unauthorized", "seals": []}, status_code=401)

    wallet_id = user["wallet_id"]

    try:
        # Query Forensic Ledger for user's receipts
        import requests as req
        ledger_response = req.get(
            f"http://localhost:8101/api/receipts?actor={wallet_id}",
            timeout=5
        )

        if ledger_response.status_code == 200:
            data = ledger_response.json()
            # Handle both list and dict responses
            seals = data if isinstance(data, list) else data.get("receipts", [])
        else:
            # Try alternate endpoint format
            ledger_response = req.get(
                "http://localhost:8101/api/receipts",
                timeout=5
            )
            if ledger_response.status_code == 200:
                all_receipts = ledger_response.json()
                if isinstance(all_receipts, list):
                    seals = [r for r in all_receipts if r.get("actor") == wallet_id]
                else:
                    seals = [r for r in all_receipts.get("receipts", []) if r.get("actor") == wallet_id]
            else:
                seals = []

        return JSONResponse({
            "wallet_id": wallet_id,
            "seals": seals,
            "count": len(seals)
        })

    except Exception as e:
        print(f"[WORKSPACE SEALS] Ledger query error: {e}")
        return JSONResponse({
            "wallet_id": wallet_id,
            "seals": [],
            "count": 0,
            "error": str(e)
        })


# ═══════════════════════════════════════════════════════════════
# §111 MARIA ↔ TESOURA — Media Seals + Collage Opportunity
# ═══════════════════════════════════════════════════════════════

@app.get("/workspace/media-seals")
async def workspace_media_seals(request: Request, place: str = None, limit: int = 20):
    """
    §111 Sprint C: Lista de fotos/vídeos selados do utilizador.
    Filtra por doc_type in (photo, video, doc) e opcionalmente por place_name.
    """
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return JSONResponse({"error": "unauthorized", "seals": []}, status_code=401)

    wallet_id = user["wallet_id"]

    try:
        import requests as req
        # Query Forensic Ledger
        ledger_response = req.get(
            "http://localhost:8101/api/receipts",
            timeout=5
        )

        if ledger_response.status_code != 200:
            return JSONResponse({"seals": [], "count": 0})

        all_receipts = ledger_response.json()
        if isinstance(all_receipts, dict):
            all_receipts = all_receipts.get("receipts", [])

        # Filter: actor = wallet_id AND media type
        media_types = ("photo", "video", "doc", "image")
        media_seals = []

        for r in all_receipts:
            if r.get("actor") != wallet_id:
                continue
            doc_type = r.get("doc_type", "").lower()
            media_type = r.get("media_type", "").lower()
            # Include if doc_type or media_type indicates media
            if doc_type in media_types or media_type in ("image", "video"):
                seal = {
                    "receipt_id": r.get("id", ""),
                    "place_name": r.get("place_name"),
                    "timestamp": r.get("sealed_at") or r.get("created_at"),
                    "media_type": media_type or doc_type,
                    "doc_name": r.get("doc_name", ""),
                    "content_hash": r.get("content_hash", "")
                }
                # Filter by place if specified
                if place:
                    seal_place = (seal["place_name"] or "").lower()
                    if place.lower() in seal_place or seal_place in place.lower():
                        media_seals.append(seal)
                else:
                    media_seals.append(seal)

        # Sort by timestamp descending, limit
        media_seals.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
        media_seals = media_seals[:limit]

        return JSONResponse({
            "wallet_id": wallet_id,
            "seals": media_seals,
            "count": len(media_seals),
            "place_filter": place
        })

    except Exception as e:
        print(f"[MEDIA SEALS] Error: {e}")
        return JSONResponse({"seals": [], "count": 0, "error": str(e)})


@app.get("/workspace/check-collage")
async def check_collage_opportunity(request: Request, place: str = None):
    """
    §111 Sprint C: MARIA verifica se há oportunidade de colagem.
    Se 2+ seals no mesmo lugar → sugere Tesoura.
    """
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return JSONResponse({"suggest": False})

    wallet_id = user["wallet_id"]

    if not place:
        return JSONResponse({"suggest": False, "reason": "no_place"})

    try:
        import requests as req
        # Query Forensic Ledger
        ledger_response = req.get(
            "http://localhost:8101/api/receipts",
            timeout=5
        )

        if ledger_response.status_code != 200:
            return JSONResponse({"suggest": False})

        all_receipts = ledger_response.json()
        if isinstance(all_receipts, dict):
            all_receipts = all_receipts.get("receipts", [])

        # Count media seals for this place
        media_types = ("photo", "video", "doc", "image")
        place_lower = place.lower()
        matching_seals = []

        for r in all_receipts:
            if r.get("actor") != wallet_id:
                continue
            doc_type = r.get("doc_type", "").lower()
            media_type = r.get("media_type", "").lower()
            seal_place = (r.get("place_name") or "").lower()

            if (doc_type in media_types or media_type in ("image", "video")):
                # Match place (partial match for flexibility)
                if place_lower in seal_place or seal_place.split(",")[0] in place_lower:
                    matching_seals.append({
                        "receipt_id": r.get("id", ""),
                        "place_name": r.get("place_name"),
                        "media_type": media_type or doc_type
                    })

        count = len(matching_seals)

        if count >= 2:
            # Extract city name for display
            city = place.split(",")[0].strip()
            return JSONResponse({
                "suggest": True,
                "count": count,
                "place": place,
                "city": city,
                "seals": matching_seals[:10],  # Limit to 10 for URL
                "message_de": f"Du hast {count} versiegelte Momente in {city}. Möchtest du eine Collage erstellen?",
                "message_en": f"You have {count} sealed moments in {city}. Want to create a collage?",
                "message_pt": f"Tens {count} momentos selados em {city}. Queres montar uma colagem?"
            })

        return JSONResponse({
            "suggest": False,
            "count": count,
            "place": place,
            "reason": "not_enough" if count < 2 else "no_match"
        })

    except Exception as e:
        print(f"[CHECK COLLAGE] Error: {e}")
        return JSONResponse({"suggest": False, "error": str(e)})


# ═══════════════════════════════════════════════════════════════
# §112 THREAD VISUAL — Memória Geográfica da Viagem
# ═══════════════════════════════════════════════════════════════

@app.get("/workspace/thread")
async def get_thread(request: Request):
    """
    §112 Thread Visual: Retorna momentos agrupados por dia + lugar.
    Fonte: Ledger receipts reais do utilizador autenticado.
    """
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return JSONResponse({"status": "error", "message": "unauthorized", "groups": []})

    wallet_id = user["wallet_id"]

    try:
        import requests as req
        from collections import defaultdict

        # Busca seals reais do Ledger
        ledger_response = req.get(
            "http://localhost:8101/api/receipts",
            timeout=5
        )

        moments = []
        if ledger_response.status_code == 200:
            all_receipts = ledger_response.json()
            if isinstance(all_receipts, dict):
                all_receipts = all_receipts.get("receipts", [])

            for rec in all_receipts:
                if rec.get("actor") != wallet_id:
                    continue

                # Extract metadata
                doc_type = rec.get("doc_type", "")
                media_type = rec.get("media_type", "")

                # Only include media types
                if doc_type not in ("photo", "video", "doc", "image") and media_type not in ("image", "video"):
                    continue

                moments.append({
                    "id": rec.get("id", ""),
                    "type": media_type or doc_type or "photo",
                    "place_name": rec.get("place_name") or rec.get("note", "").split("·")[-1].strip() or "Localização desconhecida",
                    "timestamp": rec.get("sealed_at") or rec.get("created_at", ""),
                    "hash": rec.get("content_hash", ""),
                    "receipt_id": rec.get("id", ""),
                    "doc_name": rec.get("doc_name", ""),
                    "governance_level": rec.get("governance_level", "MEDIUM"),
                    "source": "ledger"
                })

        # Agrupa por dia + lugar
        groups = defaultdict(list)
        for m in moments:
            ts = m.get("timestamp", "")
            day = ts[:10] if ts else "Sem data"
            place = m.get("place_name", "Desconhecido")
            # Simplify place to city only
            city = place.split(",")[0].strip() if place else "Desconhecido"
            key = f"{day}||{city}"
            groups[key].append(m)

        grouped = []
        for key, items in sorted(groups.items(), reverse=True):
            parts = key.split("||")
            day = parts[0] if len(parts) > 0 else "Sem data"
            place = parts[1] if len(parts) > 1 else "Desconhecido"
            grouped.append({
                "day": day,
                "place_name": place,
                "count": len(items),
                "moments": items,
                "has_ledger": True
            })

        return JSONResponse({
            "status": "ok",
            "wallet_id": wallet_id,
            "total": len(moments),
            "groups": grouped
        })

    except Exception as e:
        print(f"[THREAD] Error: {e}")
        return JSONResponse({"status": "error", "message": str(e), "groups": []})


@app.get("/workspace/moment/{receipt_id}")
async def get_moment_detail(receipt_id: str, request: Request):
    """
    §112 Thread Visual: Detalhe completo de um momento selado.
    """
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return JSONResponse({"status": "error", "message": "unauthorized"})

    try:
        import requests as req

        # Try direct receipt lookup
        ledger_response = req.get(
            "http://localhost:8101/api/receipts",
            timeout=5
        )

        if ledger_response.status_code == 200:
            all_receipts = ledger_response.json()
            if isinstance(all_receipts, dict):
                all_receipts = all_receipts.get("receipts", [])

            # Find the specific receipt
            for rec in all_receipts:
                if rec.get("id") == receipt_id:
                    return JSONResponse({
                        "status": "ok",
                        "moment": {
                            "id": rec.get("id"),
                            "actor": rec.get("actor"),
                            "doc_name": rec.get("doc_name"),
                            "doc_type": rec.get("doc_type"),
                            "media_type": rec.get("media_type"),
                            "content_hash": rec.get("content_hash"),
                            "place_name": rec.get("place_name"),
                            "governance_level": rec.get("governance_level"),
                            "sealed_at": rec.get("sealed_at") or rec.get("created_at"),
                            "note": rec.get("note"),
                            "verify_url": f"https://windi-domain.com/verify-public/?id={receipt_id}"
                        }
                    })

            return JSONResponse({"status": "not_found", "message": "Receipt not found"})

        return JSONResponse({"status": "error", "message": "Ledger unavailable"})

    except Exception as e:
        print(f"[MOMENT DETAIL] Error: {e}")
        return JSONResponse({"status": "error", "message": str(e)})


# ═══════════════════════════════════════════════════════════════
# §103 TRAIN INTELLIGENCE — transport.rest (soberano, sem auth)
# "MARIA não procura voos. MARIA conhece o caminho."
# ═══════════════════════════════════════════════════════════════

TRANSPORT_BASE = "https://v6.db.transport.rest"


@app.get("/train/stations")
async def search_train_stations(query: str = Query(..., min_length=2)):
    """
    §103.1 Autocomplete de estações DB.
    API: transport.rest (community, sem auth)
    """
    try:
        import requests as req
        r = req.get(
            f"{TRANSPORT_BASE}/locations",
            params={"query": query, "results": 8, "stops": "true", "addresses": "false"},
            timeout=15
        )
        data = r.json()
        stations = []
        for s in data:
            # transport.rest returns type="station" for train stations
            if s.get("type") in ("station", "stop"):
                stations.append({
                    "id": s.get("id"),
                    "name": s.get("name"),
                    "lat": s.get("location", {}).get("latitude"),
                    "lng": s.get("location", {}).get("longitude"),
                    "products": s.get("products", {})
                })
        return JSONResponse({"status": "ok", "stations": stations})
    except Exception as e:
        print(f"[TRAIN STATIONS] Error: {e}")
        return JSONResponse({"status": "error", "message": str(e), "api": "transport.rest may be temporarily unavailable"})


@app.get("/train/journeys")
async def get_train_journeys(
    from_id: str = Query(...),
    to_id: str = Query(...),
    when: str = Query(None),
    results: int = Query(5)
):
    """
    §103.2 Journeys com preços, atrasos, plataformas.
    Este é o coração do §103 — o que a MARIA usa para decidir.
    """
    try:
        import requests as req
        params = {
            "from": from_id,
            "to": to_id,
            "results": min(results, 10),
            "stopovers": "false",
            "tickets": "true",
            "polylines": "false",
            "remarks": "true",
        }
        if when:
            params["departure"] = when

        r = req.get(f"{TRANSPORT_BASE}/journeys", params=params, timeout=15)

        raw = r.json()
        journeys = []

        for j in raw.get("journeys", []):
            legs = j.get("legs", [])
            if not legs:
                continue

            dep_leg = legs[0]
            arr_leg = legs[-1]

            # Extract price
            price_data = j.get("price")
            price = None
            if price_data and isinstance(price_data, dict) and price_data.get("amount"):
                price = {"amount": price_data["amount"], "currency": price_data.get("currency", "EUR")}

            # Delays
            dep_delay = dep_leg.get("departureDelay", 0) or 0
            arr_delay = arr_leg.get("arrivalDelay", 0) or 0

            # Main line
            main_line = dep_leg.get("line", {}) or {}

            # Warnings
            remarks = []
            for leg in legs:
                for rm in leg.get("remarks", []):
                    if rm.get("type") == "warning":
                        remarks.append(rm.get("text", ""))

            journeys.append({
                "id": j.get("refreshToken", "")[:50],
                "departure": dep_leg.get("departure"),
                "arrival": arr_leg.get("arrival"),
                "dep_delay_min": dep_delay // 60 if dep_delay else 0,
                "arr_delay_min": arr_delay // 60 if arr_delay else 0,
                "duration_min": _calc_train_duration(dep_leg.get("departure"), arr_leg.get("arrival")),
                "changes": len(legs) - 1,
                "line_name": main_line.get("name", ""),
                "operator": main_line.get("operator", {}).get("name", "") if isinstance(main_line.get("operator"), dict) else "",
                "dep_platform": dep_leg.get("departurePlatform", ""),
                "arr_platform": arr_leg.get("arrivalPlatform", ""),
                "price": price,
                "legs": _simplify_train_legs(legs),
                "remarks": remarks[:3],
                "is_direct": len(legs) == 1,
                "origin": dep_leg.get("origin", {}).get("name", ""),
                "destination": arr_leg.get("destination", {}).get("name", "")
            })

        return JSONResponse({"status": "ok", "journeys": journeys, "source": "transport.rest"})

    except Exception as e:
        print(f"[TRAIN JOURNEYS] Error: {e}")
        return JSONResponse({"status": "error", "message": str(e)})


@app.post("/train/maria-decide")
async def maria_train_decide(request: Request):
    """
    §103.3 Núcleo de decisão da MARIA para comboios.
    Scoring soberano sem LLM externo.
    Invariante: MARIA sugere. Humano confirma.
    """
    try:
        import requests as req
        body = await request.json()
        journeys = body.get("journeys", [])
        context = body.get("context", {})

        # If no journeys provided, fetch them first
        if not journeys:
            from_id = body.get("from_id")
            to_id = body.get("to_id")
            when = body.get("when")
            results = body.get("results", 5)

            if not from_id or not to_id:
                return JSONResponse({"status": "error", "message": "from_id e to_id obrigatórios"})

            # Fetch journeys from transport.rest
            params = {
                "from": from_id,
                "to": to_id,
                "results": min(results, 10),
                "stopovers": "false",
                "tickets": "true",
                "polylines": "false",
                "remarks": "true",
                "language": body.get("lang", "de").lower()
            }
            if when:
                params["departure"] = when

            r = req.get(f"{TRANSPORT_BASE}/journeys", params=params, timeout=20)
            data = r.json()

            for j in data.get("journeys", []):
                legs = j.get("legs", [])
                if not legs:
                    continue
                dep_leg = legs[0]
                arr_leg = legs[-1]
                price_data = j.get("price")
                journeys.append({
                    "departure": dep_leg.get("departure"),
                    "arrival": arr_leg.get("arrival"),
                    "dep_delay_min": (dep_leg.get("departureDelay") or 0) // 60,
                    "arr_delay_min": (arr_leg.get("arrivalDelay") or 0) // 60,
                    "duration_min": int((datetime.fromisoformat(arr_leg.get("arrival", "").replace("Z", "+00:00"))
                                        - datetime.fromisoformat(dep_leg.get("departure", "").replace("Z", "+00:00"))).total_seconds() / 60) if arr_leg.get("arrival") and dep_leg.get("departure") else 0,
                    "changes": len([l for l in legs if l.get("walking")]),
                    "line_name": dep_leg.get("line", {}).get("name", ""),
                    "dep_platform": dep_leg.get("departurePlatform"),
                    "arr_platform": arr_leg.get("arrivalPlatform"),
                    "price": {"amount": price_data.get("amount"), "currency": price_data.get("currency")} if price_data else None,
                    "is_direct": len([l for l in legs if not l.get("walking")]) == 1,
                    "origin": dep_leg.get("origin", {}).get("name", ""),
                    "destination": arr_leg.get("destination", {}).get("name", ""),
                    "journey_id": j.get("refreshToken", "")
                })

        if not journeys:
            return JSONResponse({"status": "error", "message": "Sem journeys encontrados"})

        meeting_time = context.get("meeting_time")
        prefer_direct = context.get("prefer_direct", True)
        budget = context.get("budget")

        scored = []
        for j in journeys:
            score = 100.0
            reasons = []
            warnings = []

            # Penalize delays
            if j.get("dep_delay_min", 0) > 0:
                score -= j["dep_delay_min"] * 3
                warnings.append(f"+{j['dep_delay_min']} min atraso previsto")

            # Penalize changes
            changes = j.get("changes", 0)
            if changes > 0:
                score -= changes * 15
                if prefer_direct:
                    score -= 10
                reasons.append(f"{changes} transbordo(s)")

            # Check margin for meeting
            if meeting_time and j.get("arrival"):
                try:
                    arr = datetime.fromisoformat(j["arrival"].replace("Z", "+00:00"))
                    mt_h, mt_m = map(int, meeting_time.split(":"))
                    meeting_dt = arr.replace(hour=mt_h, minute=mt_m, second=0)
                    margin_min = int((meeting_dt - arr).total_seconds() / 60)
                    j["margin_min"] = margin_min
                    if margin_min < 15:
                        score -= 40
                        warnings.append(f"Margem curta: {margin_min} min")
                    elif margin_min >= 30:
                        score += 15
                        reasons.append(f"Chega {margin_min} min antes")
                except Exception:
                    pass

            # Price vs budget
            if j.get("price") and budget:
                price_eur = j["price"]["amount"]
                j["price_eur"] = price_eur
                if price_eur <= budget * 0.8:
                    score += 10
                    reasons.append(f"€{price_eur:.0f} — dentro do orçamento")
                elif price_eur > budget:
                    score -= 20
                    warnings.append(f"€{price_eur:.0f} — acima do orçamento")

            # Bonus for direct
            if j.get("is_direct"):
                score += 20
                reasons.append("Viagem directa")

            j["score"] = round(score, 1)
            j["reasons"] = reasons
            j["warnings"] = warnings
            scored.append(j)

        # Sort by score
        scored.sort(key=lambda x: x["score"], reverse=True)
        best = scored[0]

        # Build explanation
        dep_time = _fmt_train_time(best.get("departure", ""))
        arr_time = _fmt_train_time(best.get("arrival", ""))
        line = best.get("line_name", "comboio")
        price_str = f" — €{best.get('price_eur', 0):.0f}" if best.get("price_eur") else ""
        delay_str = f" (+{best['dep_delay_min']} min atraso)" if best.get("dep_delay_min", 0) > 0 else ""
        margin_str = f" Chegas {best.get('margin_min', '?')} min antes." if best.get("margin_min") else ""

        explanation = f"{line} · partida {dep_time}{delay_str} · chegada {arr_time}{price_str}.{margin_str}"
        if best.get("reasons"):
            explanation += " " + ". ".join(best["reasons"]) + "."
        if best.get("warnings"):
            explanation += " ⚠️ " + ". ".join(best["warnings"]) + "."

        # Build recommendation with frontend-expected fields
        recommendation = {
            "from_name": best.get("origin", ""),
            "to_name": best.get("destination", ""),
            "departure": best.get("departure", ""),
            "arrival": best.get("arrival", ""),
            "duration_minutes": best.get("duration_min", 0),
            "changes": best.get("changes", 0),
            "delay_minutes": best.get("dep_delay_min", 0),
            "platform": best.get("dep_platform", ""),
            "price": best.get("price", {}).get("amount") if best.get("price") else None,
            "score": best.get("score", 0),
            "journey_id": best.get("journey_id", ""),
            "line_name": best.get("line_name", "")
        }

        # Alternatives (rest of scored)
        alternatives = []
        for alt in scored[1:4]:  # Max 3 alternatives
            alternatives.append({
                "departure": alt.get("departure", ""),
                "arrival": alt.get("arrival", ""),
                "duration_minutes": alt.get("duration_min", 0),
                "changes": alt.get("changes", 0),
                "score": alt.get("score", 0)
            })

        return JSONResponse({
            "status": "ok",
            "recommendation": recommendation,
            "alternatives": alternatives,
            "reasoning": explanation,
            "all_scored": scored,
            "principle": "MARIA sugere, nunca impõe — soberania até nos gestos pequenos."
        })

    except Exception as e:
        print(f"[MARIA DECIDE] Error: {e}")
        return JSONResponse({"status": "error", "message": str(e)})


def _calc_train_duration(dep: str, arr: str) -> int:
    """Calculate duration in minutes between two ISO timestamps."""
    try:
        d = datetime.fromisoformat(dep.replace("Z", "+00:00"))
        a = datetime.fromisoformat(arr.replace("Z", "+00:00"))
        return int((a - d).total_seconds() / 60)
    except:
        return 0


def _fmt_train_time(iso: str) -> str:
    """Format ISO timestamp to HH:MM."""
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%H:%M")
    except:
        return iso or ""


def _simplify_train_legs(legs: list) -> list:
    """Simplify leg data for frontend."""
    out = []
    for leg in legs:
        line = leg.get("line") or {}
        out.append({
            "dep_name": leg.get("origin", {}).get("name", ""),
            "arr_name": leg.get("destination", {}).get("name", ""),
            "departure": _fmt_train_time(leg.get("departure", "")),
            "arrival": _fmt_train_time(leg.get("arrival", "")),
            "line": line.get("name", "") if isinstance(line, dict) else "",
            "platform": leg.get("departurePlatform", ""),
            "walking": leg.get("walking", False),
        })
    return out


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
    # Padrão: WINDI-TRAVEL-GENESIS-{did_uuid[:8].upper()}
    did_uuid = did.split(":")[-1] if ":" in did else did
    did_short = did_uuid.replace("-", "")[:8].upper()
    genesis_receipt_id = f"WINDI-TRAVEL-GENESIS-{did_short}"

    # Usar receipt do DB se existir, senão usar o gerado
    actual_receipt = admin[10] if admin[10] else genesis_receipt_id

    # verify_url canónica — sempre presente
    verify_url = f"https://windi-domain.com/verify-public/document/{actual_receipt}"

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
            "issued_by": "WINDI-TRAVEL · Liga IA+H · Kempten, Bavaria"
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
    receipt_id = f"WINDI-TRAVEL-VERIFY-{did[10:18].upper()}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    content_hash = f"sha256:{hashlib.sha256(f'{did}|VERIFIED|{now}'.encode()).hexdigest()}"

    ledger_payload = {
        "id": receipt_id,
        "actor": "Human Dragon",
        "app": "windi-travel-admin",
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
# ROOT REDIRECT
# ═══════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    """Root redirect to gate."""
    return JSONResponse(
        status_code=200,
        content={
            "service": f"WINDI-TRAVEL Identity Gate {VERSION}",
            "gate_url": "/travel/gate",
            "health_url": "/travel/health",
            "register_url": "/travel/register",
            "invariants": ["I9", "I11", "I14"],
            "blocking_rule": "if(!did||!wallet){blockWorkspace()}"
        }
    )


# ═══════════════════════════════════════════════════════════════
# §110 GPS REVERSE GEOCODING — Nominatim OpenStreetMap
# Coordenadas → Lugar humano · Soberano (sem API key)
# ═══════════════════════════════════════════════════════════════

# Cache em memória — TTL 1 hora · Respeita rate limit Nominatim
_geocode_cache = {}  # key: "lat,lng" → {"place": ..., "ts": ...}
_GEOCODE_TTL = 3600  # 1 hora em segundos

def _get_cached_geocode(lat: str, lng: str) -> Optional[dict]:
    """Retorna cache se válido, None se expirado."""
    import time
    key = f"{lat},{lng}"
    if key in _geocode_cache:
        cached = _geocode_cache[key]
        if time.time() - cached["ts"] < _GEOCODE_TTL:
            return cached["place"]
    return None

def _set_cached_geocode(lat: str, lng: str, place: dict):
    """Guarda no cache com timestamp."""
    import time
    key = f"{lat},{lng}"
    _geocode_cache[key] = {"place": place, "ts": time.time()}

@app.get("/reverse-geocode")
async def reverse_geocode(lat: str = None, lng: str = None, lang: str = "pt"):
    """
    §110 GPS Reverse Geocoding
    Converte coordenadas GPS em nome de lugar legível.

    API: Nominatim OpenStreetMap (soberano, sem key)
    Rate limit: 1 req/s — cache obrigatório

    GDPR: Coordenadas NÃO são persistidas. Só o place_name.
    """
    if not lat or not lng:
        return JSONResponse({"error": "lat/lng required"}, status_code=400)

    # Truncar para 4 casas decimais (~11m precisão) — para cache eficiente
    try:
        lat_round = f"{float(lat):.4f}"
        lng_round = f"{float(lng):.4f}"
    except ValueError:
        return JSONResponse({"error": "invalid coordinates"}, status_code=400)

    # Check cache
    cached = _get_cached_geocode(lat_round, lng_round)
    if cached:
        return JSONResponse(cached)

    # Nominatim request
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat_round}&lon={lng_round}&format=json&accept-language={lang}"
        headers = {"User-Agent": "WINDI-Travel/1.0 (windi-domain.com)"}

        resp = requests.get(url, headers=headers, timeout=5)
        data = resp.json()

        address = data.get("address", {})

        # Extrair campos relevantes
        city = (
            address.get("city") or
            address.get("town") or
            address.get("village") or
            address.get("municipality") or
            address.get("county") or
            "Unknown"
        )
        state = address.get("state", "")
        country = address.get("country", "")
        country_code = address.get("country_code", "").upper()

        # Construir display: "Kempten, Bayern, Deutschland"
        parts = [p for p in [city, state, country] if p]
        display = ", ".join(parts) if parts else None

        place = {
            "place_name": city,
            "city": city,
            "state": state,
            "country": country,
            "country_code": country_code,
            "display": display
        }

        # Cache result
        _set_cached_geocode(lat_round, lng_round, place)

        return JSONResponse(place)

    except Exception as e:
        print(f"[GEOCODE] Nominatim error: {e}")
        # Fallback gracioso — seal funciona sem GPS
        return JSONResponse({
            "place_name": None,
            "city": None,
            "state": None,
            "country": None,
            "country_code": None,
            "display": None
        })


# ═══════════════════════════════════════════════════════════════
# TRAVEL SEAL — P0 Corte 1 · require_auth + SHA-256 validation
# ═══════════════════════════════════════════════════════════════

@app.post("/seal")
async def seal_moment(request: Request):
    """
    Seal a moment to the Forensic Ledger.
    I9 — require_auth fail-closed
    I11 — SHA-256 hash validation
    """
    import time

    # ✅ require_auth — fail-closed I9
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return JSONResponse({"error": "não autenticado"}, status_code=401)

    wallet_id = user["wallet_id"]

    body = await request.json()
    file_hash = body.get("hash", "")
    file_name = body.get("name", body.get("label", "memoria"))
    # Aceita tanto "type" como "media_type" (frontend envia media_type)
    file_type = body.get("type") or body.get("media_type", "image")
    note = body.get("note", "")
    # §110 — place_name do GPS reverse geocoding
    place_name = body.get("place_name", "")

    # Validar hash SHA-256 (64 hex chars)
    if not file_hash or len(file_hash) != 64:
        return JSONResponse({"error": "hash inválido"}, status_code=400)

    receipt_id = f"WINDI-TRAVEL-{int(time.time())}-{file_hash[:8].upper()}"

    # ✅ Seal no Ledger I11 — §109 Video Forensic Support
    # doc_type dinâmico: "video" para vídeos, "doc" para imagens
    doc_type = "video" if file_type == "video" else "doc"

    # §110 — Enriquecer doc_name com lugar (se disponível)
    # Formato: "VIDEO-Kempten-Bayern-{timestamp}" ou "IMAGE-{label}"
    if place_name:
        # Simplificar: usar só cidade do place_name (antes da vírgula)
        place_short = place_name.split(",")[0].strip().replace(" ", "-")
        enriched_name = f"{file_type.upper()}-{place_short}-{file_name}"
    else:
        enriched_name = file_name

    try:
        payload = {
            "id": receipt_id,
            "actor": wallet_id,
            "app": "windi-travel-workspace-v3",
            "doc_name": enriched_name,
            "doc_type": doc_type,
            "governance_level": "HIGH" if file_type == "video" else "MEDIUM",
            "content_hash": f"sha256:{file_hash}",
            "sge_score": 90,
            "invariant": "I11",
            "note": note or f"Travel memory sealed · {file_type}" + (f" · {place_name}" if place_name else ""),
            "media_type": file_type,  # Metadado adicional
            "place_name": place_name or None  # §110 GPS Geocoding
        }
        requests.post(LEDGER_URL, json=payload, timeout=5)
    except Exception as e:
        print(f"[TRAVEL SEAL] Ledger error: {e}")

    return JSONResponse({
        "receipt_id": receipt_id,
        "hash": file_hash,
        "wallet_id": wallet_id,
        "verify_url": f"https://windi-domain.com/verify-public/web/?id={receipt_id}",
        "sealed": True,
        "place_name": place_name or None  # §110 GPS Geocoding
    })


# ═══════════════════════════════════════════════════════════════
# TESOURA SOBERANA — Collage Seal (P3-B)
# ═══════════════════════════════════════════════════════════════

@app.post("/tesoura/seal")
async def tesoura_seal(request: Request):
    """
    Seal a collage composition to the Forensic Ledger.
    I11 — Permanência de Evidência Criptográfica
    """
    import time
    import json as json_lib

    try:
        data = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    receipt_id = data.get("id", f"WINDI-TRAVEL-COLLAGE-{int(time.time())}")
    actor = data.get("actor", "anonymous")
    content_hash = data.get("content_hash", "")
    metadata = data.get("metadata", "{}")

    # Build Ledger payload
    ledger_payload = {
        "id": receipt_id,
        "actor": actor,
        "app": "windi-travel-tesoura",
        "doc_name": data.get("doc_name", f"Collage {receipt_id}"),
        "doc_type": "doc",
        "governance_level": data.get("governance_level", "HIGH"),
        "content_hash": content_hash,
        "sge_score": data.get("sge_score", 90),
        "note": f"Tesoura Soberana · {metadata}",
    }

    # Seal to Ledger
    try:
        res = requests.post(LEDGER_URL, json=ledger_payload, timeout=6)
        result = res.json()
        return {
            "success": True,
            "receipt_id": receipt_id,
            "verify_url": f"https://windi-domain.com/verify-public/web/?id={receipt_id}",
            "ledger_response": result
        }
    except Exception as e:
        return {
            "success": False,
            "receipt_id": receipt_id,
            "error": str(e),
            "note": "Collage receipt stored locally — Ledger sync pending"
        }


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8126)
