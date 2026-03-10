"""
VPR Manage Blueprint — W-VPR-SPEC-MANAGE-v1.0
Fase 1: Auth + Profile Edit + DB Schema

Domain extension of Sandbox Core (:8091) — Flask version
Ledger receipt selado: VR-VPR-MANAGE-SPEC-V1
"""

from flask import Blueprint, request, jsonify, send_file
from functools import wraps
import sqlite3
import hashlib
import json
import jwt
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Load .env file if exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

# ─── Config ────────────────────────────────────────────────────────────────
VPR_MANAGE_SECRET = os.getenv("VPR_MANAGE_SECRET", "windi-vpr-manage-secret-change-in-prod")
VPR_DB_PATH       = os.getenv("VPR_DB_PATH", "/opt/windi/data/vpr_manage.db")
LEDGER_URL        = os.getenv("LEDGER_URL", "http://127.0.0.1:8101")
TOKEN_TTL         = 6 * 3600  # 6 horas — alinhado ao Dragon Hub

vpr_manage_bp = Blueprint("vpr_manage", __name__, url_prefix="/vpr")

# ─── DB Init ───────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(VPR_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_vpr_manage_db():
    """Cria todas as tabelas da Fase 1."""
    Path(VPR_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = get_db()
    c = conn.cursor()

    # Perfil do operador
    c.execute("""
    CREATE TABLE IF NOT EXISTS vpr_profiles (
        wallet_id        TEXT PRIMARY KEY,
        did_short        TEXT UNIQUE NOT NULL,
        role             TEXT DEFAULT '',
        location         TEXT DEFAULT '',
        available_for    TEXT DEFAULT '[]',
        bio              TEXT DEFAULT '',
        languages        TEXT DEFAULT '["PT"]',
        contact_mode     TEXT DEFAULT '{}',
        avatar_hash      TEXT DEFAULT '',
        updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ledger_receipt   TEXT DEFAULT ''
    )""")

    # Histórico de edições (append-only, I1)
    c.execute("""
    CREATE TABLE IF NOT EXISTS vpr_profile_history (
        id             TEXT PRIMARY KEY,
        wallet_id      TEXT NOT NULL,
        field_changed  TEXT NOT NULL,
        old_value      TEXT,
        new_value      TEXT,
        actor          TEXT DEFAULT 'operator',
        ts             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ledger_receipt TEXT DEFAULT ''
    )""")

    # Curadoria de receipts (Fase 2 schema, criado agora)
    c.execute("""
    CREATE TABLE IF NOT EXISTS vpr_curation (
        receipt_id     TEXT PRIMARY KEY,
        wallet_id      TEXT NOT NULL,
        is_highlighted BOOLEAN DEFAULT FALSE,
        is_pinned      BOOLEAN DEFAULT FALSE,
        sort_order     INTEGER DEFAULT 999,
        category_tag   TEXT DEFAULT '',
        private_note   TEXT DEFAULT '',
        visibility     TEXT DEFAULT 'PUBLIC',
        updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # Jurisdições declaradas
    c.execute("""
    CREATE TABLE IF NOT EXISTS vpr_jurisdictions (
        id                  TEXT PRIMARY KEY,
        wallet_id           TEXT NOT NULL,
        jurisdictions       TEXT DEFAULT '[]',
        primary_jurisdiction TEXT DEFAULT 'DE',
        declared_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        declaration_receipt TEXT DEFAULT ''
    )""")

    # Analytics (Fase 4 schema, criado agora)
    c.execute("""
    CREATE TABLE IF NOT EXISTS vpr_analytics (
        id           TEXT PRIMARY KEY,
        wallet_id    TEXT NOT NULL,
        event_type   TEXT NOT NULL,
        receipt_id   TEXT DEFAULT '',
        referrer     TEXT DEFAULT '',
        country_code TEXT DEFAULT '',
        event_ts     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # Sessões de autenticação
    c.execute("""
    CREATE TABLE IF NOT EXISTS vpr_sessions (
        token_id    TEXT PRIMARY KEY,
        wallet_id   TEXT NOT NULL,
        did_short   TEXT NOT NULL,
        issued_at   INTEGER NOT NULL,
        expires_at  INTEGER NOT NULL,
        revoked     BOOLEAN DEFAULT FALSE
    )""")

    conn.commit()
    conn.close()
    print(f"[VPR-MANAGE] DB inicializado: {VPR_DB_PATH}")


# ─── Auth ──────────────────────────────────────────────────────────────────

def _issue_token(wallet_id: str, did_short: str) -> str:
    now = int(time.time())
    token_id = str(uuid.uuid4())
    payload = {
        "sub": wallet_id,
        "did": did_short,
        "jti": token_id,
        "iat": now,
        "exp": now + TOKEN_TTL
    }
    token = jwt.encode(payload, VPR_MANAGE_SECRET, algorithm="HS256")

    # Persiste sessão
    conn = get_db()
    conn.execute(
        "INSERT INTO vpr_sessions (token_id, wallet_id, did_short, issued_at, expires_at) VALUES (?,?,?,?,?)",
        (token_id, wallet_id, did_short, now, now + TOKEN_TTL)
    )
    conn.commit()
    conn.close()
    return token

def _verify_token(token_str: str):
    try:
        payload = jwt.decode(token_str, VPR_MANAGE_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None, "Token expirado"
    except jwt.InvalidTokenError:
        return None, "Token inválido"

    # Verifica revogação
    conn = get_db()
    row = conn.execute(
        "SELECT revoked FROM vpr_sessions WHERE token_id=?", (payload["jti"],)
    ).fetchone()
    conn.close()

    if not row or row["revoked"]:
        return None, "Sessão revogada"

    return {
        "wallet_id": payload["sub"],
        "did_short": payload["did"],
        "token_id": payload["jti"]
    }, None

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"ok": False, "error": "Token ausente"}), 401
        token = auth_header[7:]
        operator, error = _verify_token(token)
        if error:
            return jsonify({"ok": False, "error": error}), 401
        # Inject operator into kwargs
        kwargs["operator"] = operator
        return f(*args, **kwargs)
    return decorated


# ─── Ledger Seal ───────────────────────────────────────────────────────────

def _seal_to_ledger(receipt_id: str, actor: str, doc_name: str, payload: dict) -> str:
    """Sela ação no Forensic Ledger (:8101)."""
    import urllib.request
    content_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    body = json.dumps({
        "id": receipt_id,
        "actor": actor,
        "app": "vpr-manage",
        "doc_name": doc_name,
        "doc_type": "doc",
        "governance_level": "MEDIUM",
        "content_hash": content_hash,
        "sge_score": 1.0
    }).encode()
    try:
        req = urllib.request.Request(
            f"{LEDGER_URL}/api/receipts",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read())
            return result.get("id", receipt_id)
    except Exception as e:
        print(f"[VPR-MANAGE] Ledger seal failed: {e}")
        return receipt_id


# ─── Endpoints: Health ─────────────────────────────────────────────────────

@vpr_manage_bp.route("/manage/health", methods=["GET"])
def manage_health():
    """Health check do módulo VPR Manage."""
    conn = get_db()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    conn.close()
    return jsonify({
        "status": "ok",
        "module": "vpr-manage",
        "version": "1.0.0",
        "phase": 1,
        "db": VPR_DB_PATH,
        "tables": [t["name"] for t in tables]
    })


# ─── Endpoints: Auth ───────────────────────────────────────────────────────

@vpr_manage_bp.route("/<did_short>/manage/login", methods=["POST"])
def manage_login(did_short):
    """
    Login no painel privado.
    Fase 1: wallet_id + did_short.
    """
    body = request.get_json() or {}
    wallet_id = body.get("wallet_id", "")
    body_did = body.get("did_short", "")

    if not wallet_id:
        return jsonify({"ok": False, "error": "wallet_id obrigatório"}), 400
    if body_did != did_short:
        return jsonify({"ok": False, "error": "did_short não confere"}), 403

    # Garante que perfil existe (cria se novo operador)
    conn = get_db()
    existing = conn.execute(
        "SELECT wallet_id FROM vpr_profiles WHERE did_short=?", (did_short,)
    ).fetchone()

    if not existing:
        conn.execute(
            "INSERT OR IGNORE INTO vpr_profiles (wallet_id, did_short) VALUES (?,?)",
            (wallet_id, did_short)
        )
        conn.commit()

    conn.close()

    token = _issue_token(wallet_id, did_short)
    return jsonify({"ok": True, "token": token, "ttl": TOKEN_TTL, "did_short": did_short})


@vpr_manage_bp.route("/<did_short>/manage/logout", methods=["POST"])
@require_auth
def manage_logout(did_short, operator=None):
    if operator["did_short"] != did_short:
        return jsonify({"ok": False, "error": "Acesso negado"}), 403

    conn = get_db()
    conn.execute(
        "UPDATE vpr_sessions SET revoked=1 WHERE token_id=?", (operator["token_id"],)
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "message": "Sessão encerrada"})


# ─── Endpoints: Profile ────────────────────────────────────────────────────

@vpr_manage_bp.route("/<did_short>/manage/profile", methods=["GET"])
@require_auth
def get_profile(did_short, operator=None):
    if operator["did_short"] != did_short:
        return jsonify({"ok": False, "error": "Acesso negado"}), 403

    conn = get_db()
    row = conn.execute(
        "SELECT * FROM vpr_profiles WHERE did_short=?", (did_short,)
    ).fetchone()
    conn.close()

    if not row:
        return jsonify({"ok": False, "error": "Perfil não encontrado"}), 404

    profile = dict(row)
    for field in ["available_for", "languages", "contact_mode"]:
        try:
            profile[field] = json.loads(profile[field] or "[]")
        except Exception:
            profile[field] = []

    return jsonify({"ok": True, "profile": profile})


@vpr_manage_bp.route("/<did_short>/manage/profile", methods=["POST"])
@require_auth
def update_profile(did_short, operator=None):
    if operator["did_short"] != did_short:
        return jsonify({"ok": False, "error": "Acesso negado"}), 403

    body = request.get_json() or {}

    conn = get_db()
    current = conn.execute(
        "SELECT * FROM vpr_profiles WHERE did_short=?", (did_short,)
    ).fetchone()

    if not current:
        conn.close()
        return jsonify({"ok": False, "error": "Perfil não encontrado"}), 404

    allowed_fields = ["role", "location", "available_for", "bio", "languages", "contact_mode", "avatar_hash"]
    updates = {}
    history_entries = []

    # Valida bio (max 400 chars)
    if "bio" in body and len(body.get("bio", "")) > 400:
        conn.close()
        return jsonify({"ok": False, "error": "Bio máximo 400 caracteres"}), 400

    for field in allowed_fields:
        if field in body:
            new_val = body[field]
            if isinstance(new_val, (list, dict)):
                new_val_str = json.dumps(new_val)
            else:
                new_val_str = str(new_val) if new_val is not None else ""

            old_val = current[field] if field in current.keys() else ""
            if old_val != new_val_str:
                updates[field] = new_val_str
                history_entries.append({
                    "id": str(uuid.uuid4()),
                    "wallet_id": operator["wallet_id"],
                    "field_changed": field,
                    "old_value": str(old_val),
                    "new_value": new_val_str
                })

    if not updates:
        conn.close()
        return jsonify({"ok": True, "message": "Nenhuma alteração detectada"})

    # Aplica updates
    set_clause = ", ".join([f"{k}=?" for k in updates])
    values = list(updates.values()) + [datetime.now(timezone.utc).isoformat(), did_short]
    conn.execute(
        f"UPDATE vpr_profiles SET {set_clause}, updated_at=? WHERE did_short=?",
        values
    )

    # Registra histórico (I1 — append-only)
    receipt_id = f"VR-VPR-PROFILE-{operator['wallet_id'][:8].upper()}-{int(time.time())}"
    for entry in history_entries:
        entry["ledger_receipt"] = receipt_id
        conn.execute(
            "INSERT INTO vpr_profile_history (id,wallet_id,field_changed,old_value,new_value,ledger_receipt) VALUES (?,?,?,?,?,?)",
            (entry["id"], entry["wallet_id"], entry["field_changed"],
             entry["old_value"], entry["new_value"], entry["ledger_receipt"])
        )

    conn.commit()
    conn.close()

    # Sela no Ledger
    _seal_to_ledger(
        receipt_id,
        actor=operator["wallet_id"],
        doc_name=f"VPR Profile Update — {did_short}",
        payload={"fields_changed": list(updates.keys()), "did_short": did_short}
    )

    return jsonify({
        "ok": True,
        "updated_fields": list(updates.keys()),
        "receipt": receipt_id
    })


# ─── Endpoints: Dashboard ─────────────────────────────────────────────────

@vpr_manage_bp.route("/<did_short>/manage", methods=["GET"])
def manage_dashboard(did_short):
    """
    Dashboard principal do painel privado.
    Retorna HTML — auth via token no sessionStorage.
    """
    html_path = Path(__file__).parent.parent / "static" / "vpr_manage.html"
    if html_path.exists():
        return send_file(html_path, mimetype="text/html")
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VPR Manage — {did_short}</title>
<style>
  body {{ font-family: 'JetBrains Mono', monospace; background: #F5F0E0; color: #1a1a1a; margin: 0; padding: 0; }}
  .loading {{ display: flex; align-items: center; justify-content: center; height: 100vh; font-size: 1.2rem; }}
</style>
</head>
<body>
  <div class="loading">VPR Manage carregando... instale o arquivo estático.</div>
  <script>window.__VPR_DID__ = "{did_short}";</script>
</body>
</html>""", 200, {"Content-Type": "text/html"}
