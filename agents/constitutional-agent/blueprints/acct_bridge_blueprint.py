"""
W-ACCT-001 Accounting Bridge v1.0.0
=====================================
Porta:  :8091 (Sandbox Core — domain extension)
Prefix: /accounting/bridge/

Endpoints:
  POST /accounting/bridge/open     → cria sessão fiscal (F1)
  POST /accounting/bridge/save     → auto-save invoice/document
  POST /accounting/bridge/publish  → C6 gate humano + Ledger seal
  GET  /accounting/bridge/status   → estado completo

Stage Map F1-F6:
  F1 = Pedido recebido (fatura, relatório fiscal, ELSTER)
  F2 = Dados estruturados (XRechnung / ZUGFeRD)
  F3 = GoBD compliance check
  F4 = ELSTER XML gerado
  F5 = Aguarda aprovação humana — C6 IRREMEDIÁVEL
  F6 = Selado no Ledger + ELSTER pronto para transmissão

INVARIANTE C6: "IA prepara. Humano aprova. ELSTER envia."
Transmissão autónoma para Finanzamt PROIBIDA em todas as circunstâncias.

Deploy:
  cp acct_bridge_blueprint.py /opt/windi/agents/constitutional-agent/blueprints/
  # agent.py: from blueprints.acct_bridge_blueprint import acct_bridge_bp
  #           app.register_blueprint(acct_bridge_bp)
"""

from flask import Blueprint, request, jsonify
import sqlite3, hashlib, uuid, datetime, json, os, logging

logger = logging.getLogger("W-ACCT-001")

acct_bridge_bp = Blueprint("acct_bridge", __name__, url_prefix="/accounting/bridge")

DB_PATH = os.environ.get("WINDI_DB_PATH", "/opt/windi/data/acct_bridge.db")

DOC_TYPES = ["rechnung", "gutschrift", "elster_xml", "gobd_report", "jahresabschluss", "steuererklaerung"]
GOBD_STATUS = {
    "PASS":    "GoBD-konform — Revisionssicherheit gewährleistet",
    "WARN":    "GoBD-Warnung — manuelle Prüfung empfohlen",
    "FAIL":    "GoBD-Verstoß — Korrekturen erforderlich",
    "PENDING": "GoBD-Prüfung ausstehend"
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS acct_sessions (
            id              TEXT PRIMARY KEY,
            wallet_id       TEXT,
            doc_type        TEXT DEFAULT 'rechnung',
            subject         TEXT NOT NULL,
            status          TEXT DEFAULT 'draft',
            stage           TEXT DEFAULT 'F1',
            invoice_data    TEXT DEFAULT '{}',
            elster_xml      TEXT,
            gobd_status     TEXT DEFAULT 'PENDING',
            gobd_hash       TEXT,
            ledger_receipt  TEXT,
            verify_url      TEXT,
            content_hash    TEXT,
            human_approved  INTEGER DEFAULT 0,
            c6_acknowledged INTEGER DEFAULT 0,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS acct_revisions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      TEXT NOT NULL,
            invoice_data    TEXT NOT NULL,
            stage           TEXT NOT NULL,
            saved_at        TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES acct_sessions(id)
        );
        """)

try:
    init_db()
    logger.info("W-ACCT-001 DB inicializado")
except Exception as e:
    logger.error(f"DB init error: {e}")


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"

def gen_session_id():
    return "ACCT-" + uuid.uuid4().hex[:8].upper()

def compute_hash(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

def seal_ledger(session_id, subject, content_hash, doc_type, wallet_id="human-dragon"):
    import urllib.request
    receipt_id = f"WINDI-ACCT-{session_id}-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    payload = json.dumps({
        "id": receipt_id,
        "actor": wallet_id,
        "app": "accounting-bridge",
        "doc_name": subject,
        "doc_type": "doc",
        "governance_level": "HIGH",
        "content": (f"SHA-256:{content_hash} | {doc_type.upper()} selado via Bridge F6 | "
                    "C6 IRREMEDIÁVEL — IA preparou, Humano aprovou")
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


@acct_bridge_bp.route("/open", methods=["POST"])
def bridge_open():
    data      = request.get_json(silent=True) or {}
    subject   = data.get("subject", "Dokument ohne Titel")
    wallet_id = data.get("wallet_id", "anonymous")
    doc_type  = data.get("doc_type", "rechnung")
    c6_ack    = data.get("c6_acknowledged", False)

    if doc_type not in DOC_TYPES:
        return jsonify({"status": "error",
                        "detail": f"doc_type inválido. Válidos: {DOC_TYPES}"}), 400

    session_id = gen_session_id()
    ts = now_iso()
    try:
        with get_db() as db:
            db.execute("""
                INSERT INTO acct_sessions
                  (id, wallet_id, subject, doc_type, c6_acknowledged, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?)
            """, (session_id, wallet_id, subject, doc_type,
                  1 if c6_ack else 0, ts, ts))

        logger.info(f"[ACCT] Sessão aberta: {session_id} | '{subject}' | type={doc_type}")
        return jsonify({
            "status": "ok", "session_id": session_id, "stage": "F1",
            "subject": subject, "doc_type": doc_type,
            "c6_invariant": {
                "statement": "IA prepara. Humano aprova. ELSTER envia.",
                "autonomous_transmission": "PROIBIDA — IRREMEDIÁVEL",
                "action_required": "human_approved=true antes de qualquer export"
            },
            "message": "Sessão fiscal criada. C6 IRREMEDIÁVEL activo.",
            "created_at": ts
        }), 201
    except Exception as e:
        logger.error(f"bridge_open error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


@acct_bridge_bp.route("/save", methods=["POST"])
def bridge_save():
    data         = request.get_json(silent=True) or {}
    session_id   = data.get("session_id")
    invoice_data = data.get("invoice_data", {})
    elster_xml   = data.get("elster_xml")
    gobd_status  = data.get("gobd_status", "PENDING")
    stage        = data.get("stage", "F3")

    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400
    if gobd_status not in GOBD_STATUS:
        return jsonify({"status": "error",
                        "detail": f"gobd_status inválido. Válidos: {list(GOBD_STATUS.keys())}"}), 400

    inv_str      = json.dumps(invoice_data) if isinstance(invoice_data, dict) else invoice_data
    content_hash = compute_hash(inv_str + (elster_xml or ""))
    ts           = now_iso()

    try:
        with get_db() as db:
            row = db.execute("SELECT id, status FROM acct_sessions WHERE id=?",
                             (session_id,)).fetchone()
            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404
            if row["status"] == "published":
                return jsonify({"status": "error",
                                "detail": "Sessão já selada — C6+I11 IRREMEDIÁVEL"}), 409

            # GoBD FAIL bloqueia progressão para F4+
            if gobd_status == "FAIL" and stage in ("F4", "F5", "F6"):
                return jsonify({
                    "status": "gobd_violation",
                    "session_id": session_id,
                    "gobd_status": "FAIL",
                    "message": "GoBD-Verstoß — correcções obrigatórias antes de avançar. "
                               "Documento não pode ser submetido ao Finanzamt.",
                    "blocked_stages": ["F4", "F5", "F6"]
                }), 422

            db.execute("""
                UPDATE acct_sessions
                SET invoice_data=?, elster_xml=?, gobd_status=?,
                    content_hash=?, stage=?, updated_at=?
                WHERE id=?
            """, (inv_str, elster_xml, gobd_status, content_hash, stage, ts, session_id))

            db.execute("""
                INSERT INTO acct_revisions (session_id, invoice_data, stage, saved_at)
                VALUES (?,?,?,?)
            """, (session_id, inv_str, stage, ts))

        logger.info(f"[ACCT] Save: {session_id} | stage={stage} | GoBD={gobd_status}")
        return jsonify({
            "status": "ok", "session_id": session_id,
            "stage": stage, "gobd_status": gobd_status,
            "gobd_description": GOBD_STATUS[gobd_status],
            "content_hash": content_hash, "saved_at": ts,
            "elster_xml_present": bool(elster_xml),
            "c6_reminder": "IA preparou. Humano aprova. ELSTER envia.",
            "message": f"Documento guardado. GoBD: {GOBD_STATUS[gobd_status]}"
        }), 200
    except Exception as e:
        logger.error(f"bridge_save error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


@acct_bridge_bp.route("/publish", methods=["POST"])
def bridge_publish():
    data           = request.get_json(silent=True) or {}
    session_id     = data.get("session_id")
    human_approved = data.get("human_approved", False)
    c6_confirmed   = data.get("c6_confirmed", False)

    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400

    try:
        with get_db() as db:
            row = db.execute("""
                SELECT id, subject, invoice_data, elster_xml, gobd_status,
                       content_hash, status, wallet_id, doc_type
                FROM acct_sessions WHERE id=?
            """, (session_id,)).fetchone()

            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404
            if row["status"] == "published":
                return jsonify({
                    "status": "already_published", "session_id": session_id,
                    "message": "C6+I11 — já selado, imutável."
                }), 200

            if row["gobd_status"] == "FAIL":
                return jsonify({
                    "status": "gobd_blocked",
                    "session_id": session_id,
                    "message": "GoBD-Verstoß — publicação bloqueada. "
                               "Corrigir violações antes de submeter ao Finanzamt."
                }), 422

            if not human_approved or not c6_confirmed:
                db.execute("UPDATE acct_sessions SET stage='F5', updated_at=? WHERE id=?",
                           (now_iso(), session_id))
                return jsonify({
                    "status": "awaiting_c6_approval",
                    "session_id": session_id, "stage": "F5",
                    "c6_invariant": "IA prepara. Humano aprova. ELSTER envia.",
                    "required_fields": {
                        "human_approved": human_approved,
                        "c6_confirmed": c6_confirmed,
                        "both_required": True
                    },
                    "message": "C6 IRREMEDIÁVEL — requer human_approved=true E c6_confirmed=true. "
                               "AI processes. Human decides. WINDI guarantees."
                }), 202

            content_hash = row["content_hash"] or compute_hash(row["invoice_data"] or "{}")
            seal = seal_ledger(session_id, row["subject"], content_hash,
                               row["doc_type"], row["wallet_id"] or "human-dragon")
            ts = now_iso()
            db.execute("""
                UPDATE acct_sessions
                SET status='published', stage='F6', human_approved=1, c6_acknowledged=1,
                    ledger_receipt=?, verify_url=?, content_hash=?, updated_at=?
                WHERE id=?
            """, (seal["receipt_id"], seal["verify_url"], content_hash, ts, session_id))

        logger.info(f"[ACCT] PUBLISHED: {session_id} | receipt={seal['receipt_id']}")
        return jsonify({
            "status": "published", "session_id": session_id, "stage": "F6",
            "doc_type": row["doc_type"],
            "gobd_status": row["gobd_status"],
            "elster_xml_ready": bool(row["elster_xml"]),
            "ledger_receipt": seal["receipt_id"],
            "content_hash": content_hash,
            "verify_url": seal["verify_url"],
            "qr_payload": f"WINDI:{seal['receipt_id']}|{content_hash[:16]}",
            "ledger_status": seal["ledger_status"],
            "published_at": ts,
            "c6_status": "FULFILLED — IA preparou, Humano aprovou, ELSTER pronto para envio manual.",
            "next_step": "Download ELSTER XML → Submeter manualmente ao Finanzamt",
            "message": "Documento fiscal selado. C6+I11 IRREMEDIÁVEL. "
                       "AI processes. Human decides. WINDI guarantees."
        }), 200
    except Exception as e:
        logger.error(f"bridge_publish error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


@acct_bridge_bp.route("/status", methods=["GET"])
def bridge_status():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400
    try:
        with get_db() as db:
            row = db.execute("""
                SELECT id, wallet_id, subject, doc_type, gobd_status, status, stage,
                       human_approved, c6_acknowledged, elster_xml,
                       ledger_receipt, verify_url, content_hash, created_at, updated_at
                FROM acct_sessions WHERE id=?
            """, (session_id,)).fetchone()
            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404
            rev_count = db.execute(
                "SELECT COUNT(*) FROM acct_revisions WHERE session_id=?",
                (session_id,)).fetchone()[0]

        return jsonify({
            "status": "ok", "session_id": row["id"],
            "subject": row["subject"], "doc_type": row["doc_type"],
            "gobd_status": row["gobd_status"],
            "gobd_description": GOBD_STATUS.get(row["gobd_status"], ""),
            "stage": row["stage"], "session_status": row["status"],
            "human_approved": bool(row["human_approved"]),
            "c6_acknowledged": bool(row["c6_acknowledged"]),
            "elster_xml_present": bool(row["elster_xml"]),
            "revisions": rev_count,
            "ledger_receipt": row["ledger_receipt"],
            "verify_url": row["verify_url"],
            "content_hash": row["content_hash"],
            "created_at": row["created_at"], "updated_at": row["updated_at"],
            "invariants": {
                "C6": "IRREMEDIÁVEL — IA prepara, Humano aprova, ELSTER envia",
                "I9": "ENFORCED — human_approved + c6_confirmed obrigatórios",
                "I11": "ENFORCED — Ledger IRREMEDIÁVEL após F6"
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500
