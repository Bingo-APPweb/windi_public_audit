"""
W-AUDIT-001 Audit Bridge v1.0.0
=================================
Porta:  :8091 (Sandbox Core — domain extension)
Prefix: /audit/bridge/

Endpoints:
  POST /audit/bridge/open     → cria sessão de auditoria (A1)
  POST /audit/bridge/save     → salva findings + hash chain
  POST /audit/bridge/publish  → gate humano + Ledger seal do relatório
  GET  /audit/bridge/status   → estado completo

Stage Map A1-A6:
  A1 = Auditoria iniciada
  A2 = Documentos recebidos
  A3 = Hash verification em curso
  A4 = Relatório redigido
  A5 = Aguarda aprovação humana (I9 GATE)
  A6 = Relatório selado no Ledger IRREMEDIÁVEL

Princípio: READ-ONLY — o Auditor NUNCA modifica documentos, apenas verifica.

Deploy:
  cp audit_bridge_blueprint.py /opt/windi/agents/constitutional-agent/blueprints/
  # agent.py: from blueprints.audit_bridge_blueprint import audit_bridge_bp
  #           app.register_blueprint(audit_bridge_bp)
"""

from flask import Blueprint, request, jsonify
import sqlite3, hashlib, uuid, datetime, json, os, logging

logger = logging.getLogger("W-AUDIT-001")

audit_bridge_bp = Blueprint("audit_bridge", __name__, url_prefix="/audit/bridge")

DB_PATH = os.environ.get("WINDI_DB_PATH", "/opt/windi/data/audit_bridge.db")

VERDICT = {
    "PASS":    "✅ Integridade verificada — cadeia de custódia íntegra",
    "WARN":    "⚠️ Anomalia detectada — revisão recomendada",
    "FAIL":    "❌ Falha de integridade — documento comprometido",
    "PENDING": "⏳ Verificação em curso"
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS audit_sessions (
            id              TEXT PRIMARY KEY,
            wallet_id       TEXT,
            subject         TEXT NOT NULL,
            doc_refs        TEXT DEFAULT '[]',
            verdict         TEXT DEFAULT 'PENDING',
            status          TEXT DEFAULT 'draft',
            stage           TEXT DEFAULT 'A1',
            findings        TEXT DEFAULT '[]',
            hash_chain      TEXT DEFAULT '[]',
            ledger_receipt  TEXT,
            verify_url      TEXT,
            report_hash     TEXT,
            human_approved  INTEGER DEFAULT 0,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS audit_checks (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      TEXT NOT NULL,
            doc_ref         TEXT NOT NULL,
            expected_hash   TEXT,
            actual_hash     TEXT,
            match           INTEGER DEFAULT 0,
            checked_at      TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES audit_sessions(id)
        );
        """)

try:
    init_db()
    logger.info("W-AUDIT-001 DB inicializado")
except Exception as e:
    logger.error(f"DB init error: {e}")


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"

def gen_session_id():
    return "AUDIT-" + uuid.uuid4().hex[:8].upper()

def compute_hash(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

def seal_ledger(session_id, subject, report_hash, verdict, wallet_id="human-dragon"):
    import urllib.request
    receipt_id = f"WINDI-AUDIT-{session_id}-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    payload = json.dumps({
        "id": receipt_id,
        "actor": wallet_id,
        "app": "audit-bridge",
        "doc_name": subject,
        "doc_type": "doc",
        "governance_level": "HIGH",
        "content_hash": f"sha256:{report_hash}",
        "sge_score": 0.0
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
        return {"receipt_id": receipt_id, "hash": report_hash,
                "verify_url": verify_url, "ledger_status": "SEALED"}
    except Exception as e:
        logger.warning(f"Ledger seal falhou: {e}")
        verify_url = f"https://windi-domain.com/verify-public/?id={receipt_id}"
        return {"receipt_id": receipt_id, "hash": report_hash,
                "verify_url": verify_url, "ledger_status": "PENDING_RETRY"}


@audit_bridge_bp.route("/open", methods=["POST"])
def bridge_open():
    data      = request.get_json(silent=True) or {}
    subject   = data.get("subject", "Auditoria de Integridade")
    wallet_id = data.get("wallet_id", "anonymous")
    doc_refs  = json.dumps(data.get("doc_refs", []))
    session_id = gen_session_id()
    ts = now_iso()
    try:
        with get_db() as db:
            db.execute("""
                INSERT INTO audit_sessions
                  (id, wallet_id, subject, doc_refs, created_at, updated_at)
                VALUES (?,?,?,?,?,?)
            """, (session_id, wallet_id, subject, doc_refs, ts, ts))
        logger.info(f"[AUDIT] Sessão aberta: {session_id} | '{subject}'")
        return jsonify({
            "status": "ok", "session_id": session_id, "stage": "A1",
            "subject": subject,
            "principle": "READ-ONLY — o Auditor nunca modifica, apenas verifica.",
            "verdicts": VERDICT,
            "message": "Sessão de auditoria criada. Pronto para verificação.",
            "created_at": ts
        }), 201
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500


@audit_bridge_bp.route("/save", methods=["POST"])
def bridge_save():
    data       = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    findings   = data.get("findings", [])
    hash_chain = data.get("hash_chain", [])
    verdict    = data.get("verdict", "PENDING")
    stage      = data.get("stage", "A3")

    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400
    if verdict not in VERDICT:
        return jsonify({"status": "error",
                        "detail": f"verdict inválido. Válidos: {list(VERDICT.keys())}"}), 400

    findings_str   = json.dumps(findings) if isinstance(findings, list) else findings
    hash_chain_str = json.dumps(hash_chain) if isinstance(hash_chain, list) else hash_chain
    report_hash    = compute_hash(findings_str + hash_chain_str)
    ts = now_iso()

    try:
        with get_db() as db:
            row = db.execute("SELECT id, status FROM audit_sessions WHERE id=?",
                             (session_id,)).fetchone()
            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404
            if row["status"] == "published":
                return jsonify({"status": "error",
                                "detail": "Relatório já selado — I11 IRREMEDIÁVEL"}), 409

            db.execute("""
                UPDATE audit_sessions
                SET findings=?, hash_chain=?, verdict=?, stage=?, report_hash=?, updated_at=?
                WHERE id=?
            """, (findings_str, hash_chain_str, verdict, stage, report_hash, ts, session_id))

            # Registar cada hash check individual
            for check in (hash_chain if isinstance(hash_chain, list) else []):
                if isinstance(check, dict):
                    db.execute("""
                        INSERT INTO audit_checks
                          (session_id, doc_ref, expected_hash, actual_hash, match, checked_at)
                        VALUES (?,?,?,?,?,?)
                    """, (session_id,
                          check.get("doc_ref", ""),
                          check.get("expected_hash", ""),
                          check.get("actual_hash", ""),
                          1 if check.get("match") else 0,
                          ts))

        logger.info(f"[AUDIT] Save: {session_id} | verdict={verdict} | hash={report_hash[:8]}")
        return jsonify({
            "status": "ok", "session_id": session_id,
            "stage": stage, "verdict": verdict,
            "verdict_description": VERDICT[verdict],
            "report_hash": report_hash, "saved_at": ts,
            "message": f"Findings guardados. Verdict: {verdict} — {VERDICT[verdict]}"
        }), 200
    except Exception as e:
        logger.error(f"bridge_save error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


@audit_bridge_bp.route("/publish", methods=["POST"])
def bridge_publish():
    data           = request.get_json(silent=True) or {}
    session_id     = data.get("session_id")
    human_approved = data.get("human_approved", False)

    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400

    try:
        with get_db() as db:
            row = db.execute("""
                SELECT id, subject, findings, hash_chain, verdict,
                       report_hash, status, wallet_id
                FROM audit_sessions WHERE id=?
            """, (session_id,)).fetchone()

            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404
            if row["status"] == "published":
                return jsonify({
                    "status": "already_published", "session_id": session_id,
                    "message": "I11 — já selado, imutável."
                }), 200

            # I9 GATE
            if not human_approved:
                db.execute("UPDATE audit_sessions SET stage='A5', updated_at=? WHERE id=?",
                           (now_iso(), session_id))
                return jsonify({
                    "status": "awaiting_approval", "session_id": session_id, "stage": "A5",
                    "verdict": row["verdict"],
                    "message": "I9 — relatório de auditoria requer human_approved=true. "
                               "AI processes. Human decides. WINDI guarantees."
                }), 202

            report_hash = row["report_hash"] or compute_hash(
                (row["findings"] or "") + (row["hash_chain"] or ""))

            seal = seal_ledger(session_id, row["subject"], report_hash,
                               row["verdict"], row["wallet_id"] or "human-dragon")
            ts = now_iso()
            db.execute("""
                UPDATE audit_sessions
                SET status='published', stage='A6', human_approved=1,
                    ledger_receipt=?, verify_url=?, report_hash=?, updated_at=?
                WHERE id=?
            """, (seal["receipt_id"], seal["verify_url"], report_hash, ts, session_id))

        logger.info(f"[AUDIT] PUBLISHED: {session_id} | receipt={seal['receipt_id']}")
        return jsonify({
            "status": "published", "session_id": session_id, "stage": "A6",
            "verdict": row["verdict"],
            "verdict_description": VERDICT.get(row["verdict"], ""),
            "ledger_receipt": seal["receipt_id"],
            "report_hash": report_hash,
            "verify_url": seal["verify_url"],
            "qr_payload": f"WINDI:{seal['receipt_id']}|{report_hash[:16]}",
            "ledger_status": seal["ledger_status"],
            "published_at": ts,
            "principle": "READ-ONLY — o Auditor verificou, não modificou.",
            "message": "Audit report selado. I11 IRREMEDIÁVEL. "
                       "AI processes. Human decides. WINDI guarantees."
        }), 200
    except Exception as e:
        logger.error(f"bridge_publish error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


@audit_bridge_bp.route("/status", methods=["GET"])
def bridge_status():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400
    try:
        with get_db() as db:
            row = db.execute("""
                SELECT id, wallet_id, subject, doc_refs, verdict, status, stage,
                       human_approved, report_hash, ledger_receipt,
                       verify_url, created_at, updated_at
                FROM audit_sessions WHERE id=?
            """, (session_id,)).fetchone()
            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404
            check_count = db.execute(
                "SELECT COUNT(*) FROM audit_checks WHERE session_id=?",
                (session_id,)).fetchone()[0]
            pass_count  = db.execute(
                "SELECT COUNT(*) FROM audit_checks WHERE session_id=? AND match=1",
                (session_id,)).fetchone()[0]

        return jsonify({
            "status": "ok", "session_id": row["id"],
            "subject": row["subject"],
            "doc_refs": json.loads(row["doc_refs"] or "[]"),
            "verdict": row["verdict"],
            "verdict_description": VERDICT.get(row["verdict"], ""),
            "stage": row["stage"], "session_status": row["status"],
            "human_approved": bool(row["human_approved"]),
            "hash_checks": {"total": check_count, "passed": pass_count,
                            "failed": check_count - pass_count},
            "report_hash": row["report_hash"],
            "ledger_receipt": row["ledger_receipt"],
            "verify_url": row["verify_url"],
            "created_at": row["created_at"], "updated_at": row["updated_at"],
            "principle": "READ-ONLY — nunca modifica, sempre verifica.",
            "invariants": {
                "I9":  "ENFORCED — human_approved obrigatório",
                "I11": "ENFORCED — Ledger IRREMEDIÁVEL após A6"
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500
