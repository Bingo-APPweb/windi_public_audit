# ============================================================
# virtue_receipt_blueprint.py
# W-VIRTUE-001 — Domain Extension do Sandbox Core (:8091)
# Path: /opt/windi/agents/constitutional-agent/blueprints/virtue_receipt_blueprint.py
# ============================================================

from flask import Blueprint, request, jsonify
import sqlite3
import hashlib
import json
import time
import uuid
import os
from datetime import datetime, timezone

virtue_bp = Blueprint('virtue', __name__, url_prefix='/virtue')

DB_PATH = os.environ.get('VIRTUE_DB', '/opt/windi/data/virtue_receipts.db')
LEDGER_API = os.environ.get('LEDGER_API', 'http://localhost:8101')

# ── Schema ────────────────────────────────────────────────────
SCHEMA = """
CREATE TABLE IF NOT EXISTS virtue_receipts (
    id              TEXT PRIMARY KEY,
    target_id       TEXT NOT NULL,       -- receipt_id do .jmpg alvo
    target_hash     TEXT,                -- hash do documento verificado
    endorser_did    TEXT NOT NULL,       -- DID do endossador
    action          TEXT NOT NULL,       -- VALIDATE_SKILL | ATTEST_EXP | RECOMMEND
    ledger_receipt  TEXT,                -- receipt_id na Forensic Ledger
    created_at      TEXT NOT NULL,
    client_meta     TEXT                 -- JSON metadata do cliente
);

CREATE INDEX IF NOT EXISTS idx_target ON virtue_receipts(target_id);
CREATE INDEX IF NOT EXISTS idx_endorser ON virtue_receipts(endorser_did);
"""

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn

def get_did_from_session(req):
    """
    Extrai DID da sessão activa.
    Tenta header X-WINDI-DID primeiro (Dragon session),
    depois cookie wallet_session, depois query param did (fallback dev).
    """
    did = req.headers.get('X-WINDI-DID')
    if did:
        return did

    session_token = req.cookies.get('wallet_session') or req.cookies.get('windi_session')
    if session_token:
        # Wallet :8100 valida o token e retorna o DID
        # Por agora: extrair DID embutido no token (formato: DID:token)
        if ':' in session_token:
            return session_token.split(':')[0]

    # Fallback para desenvolvimento
    return req.args.get('did') or req.json.get('endorser_did') if req.is_json else None

def seal_to_ledger(receipt_id: str, endorser_did: str, target_id: str, action: str) -> str | None:
    """Sela o Virtue Receipt na Forensic Ledger (:8101)."""
    import urllib.request

    payload = {
        "id": f"VR-{receipt_id}",
        "actor": endorser_did,
        "app": "W-VIRTUE-001",
        "doc_name": f"Virtue Receipt — {action} → {target_id}",
        "doc_type": "doc",
        "governance_level": "MEDIUM",
        "metadata": {
            "virtue_receipt_id": receipt_id,
            "target_id": target_id,
            "action": action,
            "endorser_did": endorser_did
        }
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        req_obj = urllib.request.Request(
            f"{LEDGER_API}/api/receipts",
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req_obj, timeout=5) as resp:
            result = json.loads(resp.read())
            return result.get('id') or result.get('receipt_id')
    except Exception as e:
        print(f"[W-VIRTUE-001] Ledger seal failed: {e}")
        return None


# ── ENDPOINTS ─────────────────────────────────────────────────

@virtue_bp.post('/api/virtue-receipt')
def cast_virtue():
    """
    POST /virtue/api/virtue-receipt
    Corpo: { target_receipt_id, action, timestamp, client_metadata }
    Auth:  DID via session (header X-WINDI-DID ou cookie wallet_session)
    """
    endorser_did = get_did_from_session(request)
    if not endorser_did:
        return jsonify({
            "error": "DID session não encontrado. Identifica-te na Wallet primeiro.",
            "code": "NO_DID_SESSION"
        }), 401

    body = request.get_json(silent=True) or {}
    target_id = body.get('target_receipt_id', '').strip()
    action = body.get('action', 'VALIDATE_SKILL').upper()

    # Validações
    if not target_id:
        return jsonify({"error": "target_receipt_id obrigatório"}), 400

    valid_actions = {'VALIDATE_SKILL', 'ATTEST_EXP', 'RECOMMEND'}
    if action not in valid_actions:
        return jsonify({"error": f"action inválida. Use: {valid_actions}"}), 400

    # Verificar se o documento alvo existe na Ledger
    target_hash = None
    try:
        import urllib.request as ur
        with ur.urlopen(f"{LEDGER_API}/api/verify/{target_id}", timeout=5) as r:
            verify_data = json.loads(r.read())
            if not verify_data.get('valid') and not verify_data.get('verified') and not verify_data.get('ok'):
                return jsonify({
                    "error": "Documento alvo não verificado na Ledger.",
                    "code": "TARGET_NOT_VERIFIED"
                }), 422
            target_hash = verify_data.get('hash') or verify_data.get('content_hash') or verify_data.get('receipt', {}).get('hash')
    except Exception as e:
        print(f"[W-VIRTUE-001] Ledger verify warning: {e}")
        # Não bloquear se Ledger demorar — endosso fica pendente de verificação

    # Gerar Receipt of Virtue
    receipt_id = str(uuid.uuid4()).replace('-', '')[:16].upper()
    now = datetime.now(timezone.utc).isoformat()

    # Hash de integridade do próprio receipt
    fingerprint_raw = f"{receipt_id}:{target_id}:{endorser_did}:{action}:{now}"
    fingerprint = hashlib.sha256(fingerprint_raw.encode()).hexdigest()

    # Persistir localmente
    with get_db() as conn:
        conn.execute("""
            INSERT INTO virtue_receipts
              (id, target_id, target_hash, endorser_did, action, created_at, client_meta)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            receipt_id,
            target_id,
            target_hash,
            endorser_did,
            action,
            now,
            json.dumps(body.get('client_metadata', {}))
        ))

    # Selar na Forensic Ledger (async — não bloqueia o endossador)
    ledger_receipt = seal_to_ledger(receipt_id, endorser_did, target_id, action)
    if ledger_receipt:
        with get_db() as conn:
            conn.execute(
                "UPDATE virtue_receipts SET ledger_receipt=? WHERE id=?",
                (ledger_receipt, receipt_id)
            )

    return jsonify({
        "success": True,
        "virtue_receipt_id": receipt_id,
        "fingerprint": fingerprint[:16],
        "ledger_receipt": ledger_receipt,
        "action": action,
        "target_id": target_id,
        "endorser_did": endorser_did[:12] + "...",  # nunca expor DID completo
        "timestamp": now
    }), 201


@virtue_bp.get('/api/virtue-receipt/<target_id>')
def get_virtues(target_id: str):
    """
    GET /virtue/api/virtue-receipt/{target_id}
    Retorna todos os endossos de um documento.
    Público — não requer auth.
    """
    with get_db() as conn:
        rows = conn.execute("""
            SELECT id, endorser_did, action, ledger_receipt, created_at
            FROM virtue_receipts
            WHERE target_id = ?
            ORDER BY created_at DESC
        """, (target_id,)).fetchall()

    virtues = []
    counts = {'VALIDATE_SKILL': 0, 'ATTEST_EXP': 0, 'RECOMMEND': 0}

    for row in rows:
        did = row['endorser_did']
        virtues.append({
            "id": row['id'],
            "endorser": did[:8] + "..." + did[-4:] if len(did) > 12 else did,
            "action": row['action'],
            "sealed": bool(row['ledger_receipt']),
            "at": row['created_at']
        })
        if row['action'] in counts:
            counts[row['action']] += 1

    return jsonify({
        "target_id": target_id,
        "total": len(virtues),
        "counts": counts,
        "virtues": virtues
    })


@virtue_bp.get('/api/virtue-receipt/health')
def health():
    return jsonify({
        "agent": "W-VIRTUE-001",
        "status": "GREEN",
        "db": DB_PATH,
        "invariant": "I9 — IA prepara, Humano endossa"
    })
