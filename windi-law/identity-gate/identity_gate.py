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
from datetime import datetime, timezone
import sqlite3
import uuid
import secrets
import hashlib
import base64
import httpx
import os

# Ed25519 cryptography
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════

DB_PATH = "/opt/windi/windi-law/identity-gate/windi_law_identity.db"
LEDGER_URL = "http://127.0.0.1:8101/api/receipts"
VERSION = "v1.0.0"

# Identity states
STATE_UNBORN = "UNBORN"
STATE_PROVISIONAL = "PROVISIONAL"
STATE_VERIFIED = "VERIFIED"
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
            created_at  TEXT NOT NULL
        )
    """)

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
        async with httpx.AsyncClient() as client:
            r = await client.post(LEDGER_URL, json=payload, timeout=10.0)
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

# Mount static files and templates
templates = Jinja2Templates(directory="/opt/windi/windi-law/identity-gate/templates")

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
        "db": DB_PATH,
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

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Insert company
        cursor.execute("""
            INSERT INTO companies (id, legal_name, country, vat_number, type, state, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (company_id, data.legal_name, data.country, data.vat_number, data.type, STATE_PROVISIONAL, now))

        # Insert admin with DID
        cursor.execute("""
            INSERT INTO admins (id, company_id, full_name, email, role, did, public_key, fingerprint, state, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (admin_id, company_id, data.admin_name, data.admin_email, "admin",
              wallet["did"], wallet["public_key"], wallet["fingerprint"], STATE_PROVISIONAL, now))

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

        return {
            "success": True,
            "company_id": company_id,
            "admin_id": admin_id,
            "did": wallet["did"],
            "fingerprint": wallet["fingerprint"],
            "public_key": wallet["public_key"],
            "api_key": api_key,
            "state": STATE_PROVISIONAL,
            "ledger_receipt": ledger_result,
            "message": "Identity created. Workspace access granted.",
            "workspace_url": "/law/workspace/"
        }

    except sqlite3.IntegrityError as e:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")


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
        raise HTTPException(status_code=404, detail="Identity not found")

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
    """Render Identity Gate UI."""
    return templates.TemplateResponse("gate.html", {"request": request})


# ═══════════════════════════════════════════════════════════════
# ROOT REDIRECT
# ═══════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    """Root redirect to gate."""
    return JSONResponse(
        status_code=200,
        content={
            "service": f"WINDI-LAW Identity Gate {VERSION}",
            "gate_url": "/law/gate",
            "health_url": "/law/health",
            "register_url": "/law/register",
            "invariants": ["I9", "I11", "I13", "G3"],
            "blocking_rule": "if(!did||!wallet){blockWorkspace()}"
        }
    )


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8122)
