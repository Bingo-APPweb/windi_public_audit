"""
WINDI Travel — Identity Gate v1.0
P3-A · "Gently proves. Silently seals."
Integrar como blueprint no server.py existente (:8126)

Pattern: domain extension · fail-closed · DID obrigatório
"""

import os
import re
import time
import uuid
import hashlib
import secrets
import sqlite3
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Optional

import requests
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
DB_PATH    = BASE_DIR / "travel_users.db"
TEMPLATES  = Jinja2Templates(directory=str(BASE_DIR / "templates"))

LEDGER_URL = "https://www.windi-domain.com/api/receipts"
BASE_URL   = os.getenv("BASE_URL", "https://www.windi-domain.com/travel")

SMTP_HOST  = os.getenv("WINDI_SMTP_HOST", "smtp.strato.de")
SMTP_PORT  = int(os.getenv("WINDI_SMTP_PORT", "465"))
SMTP_USER  = os.getenv("WINDI_SMTP_USER", "noreply@a4desk.de")
SMTP_PASS  = os.getenv("WINDI_SMTP_PASS", "")

SESSION_TTL_H  = 24          # horas de sessão válida
TOKEN_TTL_MIN  = 60          # minutos para verificar email

router = APIRouter()  # No prefix — nginx strips /travel/

# ── Database ──────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS travel_users (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet_id    TEXT UNIQUE NOT NULL,
                email        TEXT UNIQUE NOT NULL,
                name         TEXT,
                email_verified INTEGER DEFAULT 0,
                tier         TEXT DEFAULT 'FREE',
                created_at   TEXT DEFAULT (datetime('now')),
                last_seen    TEXT
            );

            CREATE TABLE IF NOT EXISTS travel_sessions (
                token        TEXT PRIMARY KEY,
                wallet_id    TEXT NOT NULL,
                created_at   TEXT DEFAULT (datetime('now')),
                expires_at   TEXT NOT NULL,
                ip           TEXT
            );

            CREATE TABLE IF NOT EXISTS travel_verify_tokens (
                token        TEXT PRIMARY KEY,
                wallet_id    TEXT NOT NULL,
                email        TEXT NOT NULL,
                created_at   TEXT DEFAULT (datetime('now')),
                expires_at   TEXT NOT NULL,
                used         INTEGER DEFAULT 0
            );
        """)
        db.commit()

# ── Helpers ───────────────────────────────────────────────────────────────────

def generate_wallet_id() -> str:
    """
    DID Universal WINDI — §64
    Formato: did:windi:{produto}:{uuid}

    "No WINDI não há estranhos.
     Quem tem um DID WINDI é cidadão de todo o ecossistema."
    """
    return f"did:windi:travel:{uuid.uuid4().hex[:12].lower()}"


def is_valid_windi_did(did: str) -> bool:
    """
    Valida qualquer DID do ecossistema WINDI — §64

    Aceita:
      did:windi:travel:xxx  ✅
      did:windi:law:xxx     ✅
      did:windi:xxx         ✅
      WID-TRAVEL-xxx        ✅ (legacy)
      WID-LAW-xxx           ✅ (legacy)

    "Entraste pelo Travel? O teu DID já te conhece no LAW."
    """
    if not did:
        return False
    # Universal format
    if did.startswith("did:windi:"):
        return True
    # Legacy formats (backwards compatible)
    if did.startswith("WID-"):
        return True
    return False

def make_session(wallet_id: str, ip: str) -> str:
    token = secrets.token_urlsafe(32)
    expires = (datetime.utcnow() + timedelta(hours=SESSION_TTL_H)).isoformat()
    with get_db() as db:
        db.execute(
            "INSERT INTO travel_sessions VALUES (?,?,datetime('now'),?,?)",
            (token, wallet_id, expires, ip)
        )
        db.execute(
            "UPDATE travel_users SET last_seen=datetime('now') WHERE wallet_id=?",
            (wallet_id,)
        )
        db.commit()
    return token

def validate_session(token: str) -> Optional[sqlite3.Row]:
    if not token:
        return None
    with get_db() as db:
        row = db.execute(
            """SELECT u.* FROM travel_sessions s
               JOIN travel_users u ON u.wallet_id = s.wallet_id
               WHERE s.token=? AND s.expires_at > datetime('now')
               AND u.email_verified=1""",
            (token,)
        ).fetchone()
    return row

def get_session_from_request(request: Request) -> Optional[sqlite3.Row]:
    token = request.cookies.get("windi_travel_session")
    return validate_session(token)

def seal_gate_event(event_type: str, wallet_id: str, note: str = ""):
    """Seal Identity Gate events to Forensic Ledger · I11"""
    try:
        payload = {
            "id": f"WINDI-TRAVEL-GATE-{event_type.upper()}-{int(time.time())}",
            "actor": wallet_id,
            "app": "windi-travel-gate-v1",
            "doc_name": f"Travel Gate: {event_type}",
            "doc_type": "doc",
            "governance_level": "MEDIUM",
            "content_hash": f"sha256:{hashlib.sha256(f'{wallet_id}|{event_type}|{time.time()}'.encode()).hexdigest()}",
            "sge_score": 85,
            "invariant": "I11",
            "note": note or f"Identity Gate event: {event_type}"
        }
        requests.post(LEDGER_URL, json=payload, timeout=4)
    except Exception:
        pass  # Gate nunca falha por causa do Ledger

def send_verify_email(email: str, name: str, wallet_id: str, token: str) -> bool:
    """Enviar email de verificação SMTP Strato"""
    verify_url = f"{BASE_URL}/gate/verify-email/{token}"
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "WINDI Travel — Verificar email / E-Mail bestätigen"
        msg["From"] = SMTP_USER
        msg["To"] = email

        # Carregar template HTML
        tpl_path = BASE_DIR / "templates" / "email_verify_travel.html"
        if tpl_path.exists():
            html_body = tpl_path.read_text().replace("{{VERIFY_URL}}", verify_url)\
                                             .replace("{{NAME}}", name or "Viajante")\
                                             .replace("{{WALLET_ID}}", wallet_id)
        else:
            html_body = f"""
            <p>Olá {name},</p>
            <p>Clica para verificar o teu email:</p>
            <a href="{verify_url}">{verify_url}</a>
            <p>Wallet: {wallet_id}</p>
            """

        msg.attach(MIMEText(html_body, "html"))

        # Port 465 = SSL, Port 587 = STARTTLS
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(SMTP_USER, email, msg.as_string())
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(SMTP_USER, email, msg.as_string())
        print(f"[TRAVEL GATE] Email sent to {email}")
        return True
    except Exception as e:
        print(f"[TRAVEL GATE] SMTP error: {e}")
        return False

# ── Routes ────────────────────────────────────────────────────────────────────

# DISABLED — DID Wizard now served by identity_gate.py /gate
# The full 5-step wizard with DID generation is in identity-gate/templates/gate.html
# @router.get("/gate", response_class=HTMLResponse)
# async def gate_page(request: Request):
#     """Landing do Identity Gate — verifica se já tem sessão válida"""
#     user = get_session_from_request(request)
#     if user:
#         return RedirectResponse(url="/travel/workspace/", status_code=302)
#     return TEMPLATES.TemplateResponse(request, "gate_travel.html", {
#         "step": "register",
#         "error": None,
#         "base_url": BASE_URL
#     })

@router.post("/gate/register", response_class=HTMLResponse)
async def gate_register(
    request: Request,
    name:  str  = Form(...),
    email: str  = Form(...),
):
    """Step 1 — Registar ou reconhecer utilizador"""
    email = email.strip().lower()

    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        return TEMPLATES.TemplateResponse(request, "gate_travel.html", {
            "step": "register",
            "error": "Email inválido.",
            "base_url": BASE_URL
        })

    with get_db() as db:
        existing = db.execute(
            "SELECT * FROM travel_users WHERE email=?", (email,)
        ).fetchone()

        if existing:
            wallet_id = existing["wallet_id"]
            # Se já verificado → login directo
            if existing["email_verified"]:
                token = make_session(wallet_id, request.client.host or "unknown")
                seal_gate_event("LOGIN", wallet_id, f"Returning traveller: {email}")
                response = RedirectResponse(url="/travel/workspace/", status_code=302)
                response.set_cookie(
                    "windi_travel_session", token,
                    max_age=SESSION_TTL_H * 3600,
                    httponly=True, samesite="lax"
                )
                return response
            # Se não verificado → reenviar email
        else:
            wallet_id = generate_wallet_id()
            db.execute(
                "INSERT INTO travel_users (wallet_id, email, name) VALUES (?,?,?)",
                (wallet_id, email, name.strip())
            )
            db.commit()
            seal_gate_event("REGISTER", wallet_id, f"New traveller registered: {email}")

        # Gerar token de verificação
        verify_token = secrets.token_urlsafe(32)
        expires = (datetime.utcnow() + timedelta(minutes=TOKEN_TTL_MIN)).isoformat()
        db.execute(
            "INSERT OR REPLACE INTO travel_verify_tokens VALUES (?,?,?,datetime('now'),?,0)",
            (verify_token, wallet_id, email, expires)
        )
        db.commit()

    # Enviar email
    send_verify_email(email, name, wallet_id, verify_token)
    seal_gate_event("EMAIL_SENT", wallet_id, f"Verify email sent to {email}")

    return TEMPLATES.TemplateResponse(request, "gate_travel.html", {
        "step": "check_email",
        "email": email,
        "error": None,
        "base_url": BASE_URL
    })

@router.get("/gate/verify-email/{token}", response_class=HTMLResponse)
async def gate_verify_email(request: Request, token: str):
    """Step 2 — Confirmar email via link"""
    with get_db() as db:
        row = db.execute(
            """SELECT * FROM travel_verify_tokens
               WHERE token=? AND used=0 AND expires_at > datetime('now')""",
            (token,)
        ).fetchone()

        if not row:
            return TEMPLATES.TemplateResponse(request, "gate_travel.html", {
                "step": "error",
                "error": "Link expirado ou inválido. Por favor regista-te novamente.",
                "base_url": BASE_URL
            })

        wallet_id = row["wallet_id"]

        # Marcar token como usado + verificar email
        db.execute("UPDATE travel_verify_tokens SET used=1 WHERE token=?", (token,))
        db.execute(
            "UPDATE travel_users SET email_verified=1 WHERE wallet_id=?", (wallet_id,)
        )
        db.commit()

    session_token = make_session(wallet_id, request.client.host or "unknown")
    seal_gate_event("EMAIL_VERIFIED", wallet_id, "Email verified · Travel Gate activated")

    response = RedirectResponse(url="/travel/workspace/", status_code=302)
    response.set_cookie(
        "windi_travel_session", session_token,
        max_age=SESSION_TTL_H * 3600,
        httponly=True, samesite="lax"
    )
    return response

@router.get("/gate/logout")
async def gate_logout(request: Request):
    """Terminar sessão"""
    token = request.cookies.get("windi_travel_session")
    if token:
        with get_db() as db:
            db.execute("DELETE FROM travel_sessions WHERE token=?", (token,))
            db.commit()
    response = RedirectResponse(url="/travel/gate", status_code=302)
    response.delete_cookie("windi_travel_session")
    return response

@router.post("/gate/resend")
async def gate_resend(request: Request, email: str = Form(...)):
    """Reenviar email de verificação"""
    email = email.strip().lower()

    with get_db() as db:
        user = db.execute(
            "SELECT * FROM travel_users WHERE email=?", (email,)
        ).fetchone()

        if not user:
            return TEMPLATES.TemplateResponse(request, "gate_travel.html", {
                "step": "error",
                "error": "Email não encontrado. Por favor regista-te novamente.",
                "base_url": BASE_URL
            })

        wallet_id = user["wallet_id"]
        name = user["name"] or "Viajante"

        # Gerar novo token
        verify_token = secrets.token_urlsafe(32)
        expires = (datetime.utcnow() + timedelta(minutes=TOKEN_TTL_MIN)).isoformat()
        db.execute(
            "INSERT OR REPLACE INTO travel_verify_tokens VALUES (?,?,?,datetime('now'),?,0)",
            (verify_token, wallet_id, email, expires)
        )
        db.commit()

    # Enviar email
    success = send_verify_email(email, name, wallet_id, verify_token)
    seal_gate_event("EMAIL_RESENT", wallet_id, f"Verify email resent to {email}")

    return TEMPLATES.TemplateResponse(request, "gate_travel.html", {
        "step": "check_email",
        "email": email,
        "error": None if success else "Erro ao enviar email. Tenta novamente.",
        "base_url": BASE_URL
    })

@router.get("/gate/status")
async def gate_status(request: Request):
    """Health check do Identity Gate"""
    try:
        with get_db() as db:
            users  = db.execute("SELECT COUNT(*) FROM travel_users WHERE email_verified=1").fetchone()[0]
            active = db.execute(
                "SELECT COUNT(*) FROM travel_sessions WHERE expires_at > datetime('now')"
            ).fetchone()[0]
        return JSONResponse({
            "status": "GREEN",
            "gate": "windi-travel-gate-v1",
            "verified_travellers": users,
            "active_sessions": active,
            "invariants": ["I9","I11","I13"],
            "principle": "Gently proves. Silently seals."
        })
    except Exception as e:
        return JSONResponse({"status": "RED", "error": str(e)}, status_code=500)

# ── Workspace Guard ────────────────────────────────────────────────────────────
def require_auth(request: Request) -> sqlite3.Row:
    """
    Usar este helper nos routes do workspace:

        user = require_auth(request)
        if isinstance(user, RedirectResponse):
            return user
    """
    user = get_session_from_request(request)
    if not user:
        return RedirectResponse(url="/travel/gate", status_code=302)
    return user

# ── Init DB on module load ────────────────────────────────────────────────────
init_db()
