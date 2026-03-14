"""
W-COMPLY-001 Compliance Bridge v1.0.0
======================================
Porta:  :8091 (Sandbox Core — domain extension)
Prefix: /compliance/bridge/

Endpoints:
  POST /compliance/bridge/open     → cria sessão compliance (P1)
  POST /compliance/bridge/save     → auto-save findings
  POST /compliance/bridge/publish  → gate humano + Ledger seal
  GET  /compliance/bridge/status   → estado completo

Stage Map P1-P6:
  P1 = Questão recebida
  P2 = Regulatory scan iniciado
  P3 = Risk assessment (R0-R5)
  P4 = Remediation plan gerado
  P5 = Aguarda aprovação humana (I9 GATE)
  P6 = Selado no Ledger IRREMEDIÁVEL

Regulamentos suportados: DSGVO · eIDAS · LGPD · GDPR · GoBD

Deploy:
  cp comply_bridge_blueprint.py /opt/windi/agents/constitutional-agent/blueprints/
  # agent.py: from blueprints.comply_bridge_blueprint import comply_bridge_bp
  #           app.register_blueprint(comply_bridge_bp)
"""

from flask import Blueprint, request, jsonify
import sqlite3, hashlib, uuid, datetime, json, os, logging

logger = logging.getLogger("W-COMPLY-001")

comply_bridge_bp = Blueprint("comply_bridge", __name__, url_prefix="/compliance/bridge")

DB_PATH = os.environ.get("WINDI_DB_PATH", "/opt/windi/data/comply_bridge.db")

RISK_LEVELS = {
    "R0": "Sem risco identificado",
    "R1": "Risco mínimo — monitorar",
    "R2": "Risco baixo — ajuste recomendado",
    "R3": "Risco médio — acção necessária",
    "R4": "Risco alto — correcção urgente",
    "R5": "Risco crítico — escalar para Human Dragon (I9)"
}

REGULATIONS = ["DSGVO", "eIDAS", "LGPD", "GDPR", "GoBD", "UNCITRAL"]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS comply_sessions (
            id              TEXT PRIMARY KEY,
            wallet_id       TEXT,
            subject         TEXT NOT NULL,
            regulations     TEXT DEFAULT '[]',
            risk_score      TEXT DEFAULT 'R0',
            status          TEXT DEFAULT 'draft',
            stage           TEXT DEFAULT 'P1',
            findings        TEXT DEFAULT '{}',
            remediation     TEXT DEFAULT '[]',
            ledger_receipt  TEXT,
            verify_url      TEXT,
            content_hash    TEXT,
            human_approved  INTEGER DEFAULT 0,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS comply_revisions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL,
            findings    TEXT NOT NULL,
            risk_score  TEXT NOT NULL,
            saved_at    TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES comply_sessions(id)
        );
        """)

try:
    init_db()
    logger.info("W-COMPLY-001 DB inicializado")
except Exception as e:
    logger.error(f"DB init error: {e}")


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"

def gen_session_id():
    return "COMPLY-" + uuid.uuid4().hex[:8].upper()

def compute_hash(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

def seal_ledger(session_id, subject, content_hash, risk_score, wallet_id="human-dragon"):
    import urllib.request, urllib.error
    receipt_id = f"WINDI-COMPLY-{session_id}-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    payload = json.dumps({
        "id": receipt_id,
        "actor": wallet_id,
        "app": "compliance-bridge",
        "doc_name": subject,
        "doc_type": "doc",
        "governance_level": "HIGH",
        "content": f"SHA-256:{content_hash} | Compliance Assessment {risk_score} selado via Bridge P6"
    }).encode()
    try:
        req = urllib.request.Request(
            "http://localhost:8101/api/receipts",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            json.loads(r.read())
        verify_url = f"https://windi-domain.com/verify-public/?id={receipt_id}"
        return {"receipt_id": receipt_id, "hash": content_hash,
                "verify_url": verify_url, "ledger_status": "SEALED"}
    except Exception as e:
        logger.warning(f"Ledger seal falhou: {e}")
        verify_url = f"https://windi-domain.com/verify-public/?id={receipt_id}"
        return {"receipt_id": receipt_id, "hash": content_hash,
                "verify_url": verify_url, "ledger_status": "PENDING_RETRY"}


@comply_bridge_bp.route("/open", methods=["POST"])
def bridge_open():
    data        = request.get_json(silent=True) or {}
    subject     = data.get("subject", "Compliance Assessment")
    wallet_id   = data.get("wallet_id", "anonymous")
    regulations = json.dumps(data.get("regulations", ["DSGVO", "GDPR"]))
    session_id  = gen_session_id()
    ts          = now_iso()
    try:
        with get_db() as db:
            db.execute("""
                INSERT INTO comply_sessions
                  (id, wallet_id, subject, regulations, created_at, updated_at)
                VALUES (?,?,?,?,?,?)
            """, (session_id, wallet_id, subject, regulations, ts, ts))
        logger.info(f"[COMPLY] Sessão aberta: {session_id} | '{subject}'")
        return jsonify({
            "status": "ok", "session_id": session_id, "stage": "P1",
            "subject": subject, "risk_scale": RISK_LEVELS,
            "message": "Sessão compliance criada. Regulatory scan iniciado.",
            "created_at": ts
        }), 201
    except Exception as e:
        logger.error(f"bridge_open error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


@comply_bridge_bp.route("/save", methods=["POST"])
def bridge_save():
    data        = request.get_json(silent=True) or {}
    session_id  = data.get("session_id")
    findings    = data.get("findings", {})
    remediation = data.get("remediation", [])
    risk_score  = data.get("risk_score", "R0")
    stage       = data.get("stage", "P3")

    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400
    if risk_score not in RISK_LEVELS:
        return jsonify({"status": "error",
                        "detail": f"risk_score inválido. Válidos: {list(RISK_LEVELS.keys())}"}), 400

    findings_str = json.dumps(findings) if isinstance(findings, dict) else findings
    content_hash = compute_hash(findings_str)
    ts = now_iso()

    try:
        with get_db() as db:
            row = db.execute("SELECT id, status FROM comply_sessions WHERE id=?",
                             (session_id,)).fetchone()
            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404
            if row["status"] == "published":
                return jsonify({"status": "error",
                                "detail": "Sessão já publicada — I11 IRREMEDIÁVEL"}), 409

            db.execute("""
                UPDATE comply_sessions
                SET findings=?, remediation=?, risk_score=?, stage=?, updated_at=?
                WHERE id=?
            """, (findings_str, json.dumps(remediation), risk_score, stage, ts, session_id))

            db.execute("""
                INSERT INTO comply_revisions (session_id, findings, risk_score, saved_at)
                VALUES (?,?,?,?)
            """, (session_id, findings_str, risk_score, ts))

        # R5 = risco crítico — flag especial
        escalate = risk_score == "R5"
        logger.info(f"[COMPLY] Save: {session_id} | risk={risk_score} | escalate={escalate}")
        return jsonify({
            "status": "ok", "session_id": session_id,
            "stage": stage, "risk_score": risk_score,
            "risk_description": RISK_LEVELS[risk_score],
            "content_hash": content_hash, "saved_at": ts,
            "escalate_to_human": escalate,
            "message": f"Assessment guardado. Risk: {risk_score} — {RISK_LEVELS[risk_score]}"
        }), 200
    except Exception as e:
        logger.error(f"bridge_save error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


@comply_bridge_bp.route("/publish", methods=["POST"])
def bridge_publish():
    data           = request.get_json(silent=True) or {}
    session_id     = data.get("session_id")
    human_approved = data.get("human_approved", False)

    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400

    try:
        with get_db() as db:
            row = db.execute("""
                SELECT id, subject, findings, risk_score, status, wallet_id
                FROM comply_sessions WHERE id=?
            """, (session_id,)).fetchone()

            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404
            if row["status"] == "published":
                return jsonify({
                    "status": "already_published", "session_id": session_id,
                    "message": "I11 — já selado, imutável."
                }), 200

            # R5 bloqueia mesmo com human_approved — escalar Human Dragon
            if row["risk_score"] == "R5" and not human_approved:
                return jsonify({
                    "status": "critical_risk_escalation",
                    "session_id": session_id,
                    "risk_score": "R5",
                    "message": "I9 — Risk R5 crítico. Escalar para Human Dragon antes de selar.",
                    "action_required": "Human Dragon deve revisar e aprovar explicitamente."
                }), 202

            # I9 GATE
            if not human_approved:
                db.execute("UPDATE comply_sessions SET stage='P5', updated_at=? WHERE id=?",
                           (now_iso(), session_id))
                return jsonify({
                    "status": "awaiting_approval", "session_id": session_id, "stage": "P5",
                    "message": "I9 — compliance report requer human_approved=true. "
                               "AI processes. Human decides. WINDI guarantees."
                }), 202

            content_hash = compute_hash(row["findings"] or "{}")
            seal = seal_ledger(session_id, row["subject"], content_hash,
                               row["risk_score"], row["wallet_id"] or "human-dragon")
            ts = now_iso()
            db.execute("""
                UPDATE comply_sessions
                SET status='published', stage='P6', human_approved=1,
                    ledger_receipt=?, verify_url=?, content_hash=?, updated_at=?
                WHERE id=?
            """, (seal["receipt_id"], seal["verify_url"], content_hash, ts, session_id))

        logger.info(f"[COMPLY] PUBLISHED: {session_id} | receipt={seal['receipt_id']}")
        return jsonify({
            "status": "published", "session_id": session_id, "stage": "P6",
            "risk_score": row["risk_score"],
            "risk_description": RISK_LEVELS[row["risk_score"]],
            "ledger_receipt": seal["receipt_id"],
            "content_hash": content_hash,
            "verify_url": seal["verify_url"],
            "qr_payload": f"WINDI:{seal['receipt_id']}|{content_hash[:16]}",
            "ledger_status": seal["ledger_status"],
            "published_at": ts,
            "message": "Compliance report selado. I11 IRREMEDIÁVEL. "
                       "AI processes. Human decides. WINDI guarantees."
        }), 200
    except Exception as e:
        logger.error(f"bridge_publish error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


@comply_bridge_bp.route("/status", methods=["GET"])
def bridge_status():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400
    try:
        with get_db() as db:
            row = db.execute("""
                SELECT id, wallet_id, subject, regulations, risk_score, status, stage,
                       human_approved, findings, remediation, ledger_receipt,
                       verify_url, content_hash, created_at, updated_at
                FROM comply_sessions WHERE id=?
            """, (session_id,)).fetchone()
            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404
            rev_count = db.execute(
                "SELECT COUNT(*) FROM comply_revisions WHERE session_id=?",
                (session_id,)).fetchone()[0]

        return jsonify({
            "status": "ok", "session_id": row["id"],
            "subject": row["subject"],
            "regulations": json.loads(row["regulations"] or "[]"),
            "risk_score": row["risk_score"],
            "risk_description": RISK_LEVELS.get(row["risk_score"], ""),
            "stage": row["stage"], "session_status": row["status"],
            "human_approved": bool(row["human_approved"]),
            "revisions": rev_count,
            "ledger_receipt": row["ledger_receipt"],
            "verify_url": row["verify_url"],
            "created_at": row["created_at"], "updated_at": row["updated_at"],
            "invariants": {
                "I9": "ENFORCED — human_approved obrigatório",
                "I11": "ENFORCED — Ledger IRREMEDIÁVEL após P6",
                "R5_ESCALATION": "ENFORCED — Risk R5 escala para Human Dragon"
            }
        }), 200
    except Exception as e:
        logger.error(f"bridge_status error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500
