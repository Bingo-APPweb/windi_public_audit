"""
W-COMM-001 Communiqué Bridge v1.0.0
====================================
Padrão: mesmo do W-JOURN-001 Editor Bridge
Porta:  :8091 (Sandbox Core — domínio extension)
Prefix: /communique/bridge/

Endpoints:
  POST /communique/bridge/open     → cria sessão Canvas (C1)
  POST /communique/bridge/save     → auto-save content_blocks
  POST /communique/bridge/publish  → gate humano + Ledger seal + QR
  GET  /communique/bridge/status   → estado completo da sessão

Invariants:
  I9  — Prohibition of Autonomy Escalation (publicação exige human_approved)
  I11 — Permanência de Evidência Criptográfica (Ledger IRREMEDIÁVEL)
  C6  — (se financeiro) IA prepara, humano aprova

Deploy:
  cp comm_bridge_blueprint.py /opt/windi/agents/constitutional-agent/blueprints/
  # Adicionar ao agent.py: from blueprints.comm_bridge_blueprint import comm_bridge_bp
  # Registar:             app.register_blueprint(comm_bridge_bp)
  # Reiniciar via nohup (ver playbook)
"""

from flask import Blueprint, request, jsonify
import sqlite3, hashlib, uuid, datetime, json, os, logging

logger = logging.getLogger("W-COMM-001")

comm_bridge_bp = Blueprint("comm_bridge", __name__, url_prefix="/communique/bridge")

# ─────────────────────────────────────────────
# DB — mesmo padrão que drafts do JOURN bridge
# ─────────────────────────────────────────────
DB_PATH = os.environ.get("WINDI_DB_PATH", "/opt/windi/data/comm_bridge.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS comm_sessions (
            id          TEXT PRIMARY KEY,
            wallet_id   TEXT,
            title       TEXT NOT NULL,
            doc_type    TEXT DEFAULT 'communique',
            status      TEXT DEFAULT 'draft',
            stage       TEXT DEFAULT 'C1',
            content_blocks TEXT DEFAULT '[]',
            metadata    TEXT DEFAULT '{}',
            ledger_receipt TEXT,
            verify_url  TEXT,
            qr_hash     TEXT,
            human_approved INTEGER DEFAULT 0,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS comm_revisions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL,
            content_blocks TEXT NOT NULL,
            saved_at    TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES comm_sessions(id)
        );
        """)

# Init na importação
try:
    init_db()
    logger.info("W-COMM-001 DB inicializado")
except Exception as e:
    logger.error(f"DB init error: {e}")


# ─────────────────────────────────────────────
# STAGE MAP — paralelo ao J1-J6 do JOURN
# C1 = Intenção recebida
# C2 = Rascunho Canvas criado
# C3 = Edição / iteração
# C4 = Revisão final
# C5 = Aguarda aprovação humana
# C6 = Selado no Ledger + QR gerado
# ─────────────────────────────────────────────
STAGES = ["C1","C2","C3","C4","C5","C6"]


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"

def gen_session_id():
    return "COMM-" + uuid.uuid4().hex[:8].upper()

def compute_hash(content_blocks: str) -> str:
    return hashlib.sha256(content_blocks.encode()).hexdigest()

def seal_ledger(session_id: str, title: str, content_hash: str,
                wallet_id: str = "human-dragon") -> dict:
    """
    Envia receipt ao Forensic Ledger :8101
    Retorna {receipt_id, hash, verify_url}
    """
    import urllib.request, urllib.error

    receipt_id = f"WINDI-COMM-{session_id}-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    payload = json.dumps({
        "id":               receipt_id,
        "actor":            wallet_id,
        "app":              "communique-bridge",
        "doc_name":         title,
        "doc_type":         "communique",
        "governance_level": "HIGH",
        "content":          f"SHA-256:{content_hash} | Communiqué Canvas selado via Bridge C6"
    }).encode()

    try:
        req = urllib.request.Request(
            "http://localhost:8101/api/receipts",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            result = json.loads(r.read())
            verify_url = f"https://windi-domain.com/verify-public/?id={receipt_id}"
            return {"receipt_id": receipt_id, "hash": content_hash,
                    "verify_url": verify_url, "ledger_status": "SEALED"}
    except Exception as e:
        logger.warning(f"Ledger seal falhou (offline?): {e}")
        verify_url = f"https://windi-domain.com/verify-public/?id={receipt_id}"
        return {"receipt_id": receipt_id, "hash": content_hash,
                "verify_url": verify_url, "ledger_status": "PENDING_RETRY"}


# ─────────────────────────────────────────────
# POST /communique/bridge/open
# Body: { "title", "wallet_id"?, "initial_blocks"? }
# ─────────────────────────────────────────────
@comm_bridge_bp.route("/open", methods=["POST"])
def bridge_open():
    data = request.get_json(silent=True) or {}
    title      = data.get("title", "Communiqué sem título")
    wallet_id  = data.get("wallet_id", "anonymous")
    init_blocks = json.dumps(data.get("initial_blocks", []))

    session_id = gen_session_id()
    ts = now_iso()

    try:
        with get_db() as db:
            db.execute("""
                INSERT INTO comm_sessions
                  (id, wallet_id, title, content_blocks, created_at, updated_at)
                VALUES (?,?,?,?,?,?)
            """, (session_id, wallet_id, title, init_blocks, ts, ts))

        logger.info(f"[COMM] Sessão aberta: {session_id} | '{title}'")
        return jsonify({
            "status":     "ok",
            "session_id": session_id,
            "stage":      "C1",
            "title":      title,
            "message":    "Sessão Canvas criada. Pronto para edição.",
            "created_at": ts
        }), 201

    except Exception as e:
        logger.error(f"bridge_open error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


# ─────────────────────────────────────────────
# POST /communique/bridge/save
# Body: { "session_id", "content_blocks", "stage"? }
# Auto-save — sem gate humano necessário
# ─────────────────────────────────────────────
@comm_bridge_bp.route("/save", methods=["POST"])
def bridge_save():
    data = request.get_json(silent=True) or {}
    session_id    = data.get("session_id")
    content_blocks = data.get("content_blocks")  # lista de layers/blocks
    stage          = data.get("stage", "C3")

    if not session_id or content_blocks is None:
        return jsonify({"status": "error", "detail": "session_id e content_blocks obrigatórios"}), 400

    blocks_str = json.dumps(content_blocks) if isinstance(content_blocks, list) else content_blocks
    content_hash = compute_hash(blocks_str)
    ts = now_iso()

    try:
        with get_db() as db:
            # Verificar sessão existe
            row = db.execute("SELECT id, status FROM comm_sessions WHERE id=?",
                             (session_id,)).fetchone()
            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404
            if row["status"] == "published":
                return jsonify({"status": "error",
                                "detail": "Sessão já publicada — I11 IRREMEDIÁVEL"}), 409

            # Atualizar sessão
            db.execute("""
                UPDATE comm_sessions
                SET content_blocks=?, stage=?, updated_at=?
                WHERE id=?
            """, (blocks_str, stage, ts, session_id))

            # Gravar revisão
            db.execute("""
                INSERT INTO comm_revisions (session_id, content_blocks, saved_at)
                VALUES (?,?,?)
            """, (session_id, blocks_str, ts))

        logger.info(f"[COMM] Auto-save: {session_id} | stage={stage} | hash={content_hash[:8]}")
        return jsonify({
            "status":       "ok",
            "session_id":   session_id,
            "stage":        stage,
            "content_hash": content_hash,
            "saved_at":     ts,
            "message":      "Rascunho guardado."
        }), 200

    except Exception as e:
        logger.error(f"bridge_save error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


# ─────────────────────────────────────────────
# POST /communique/bridge/publish
# Body: { "session_id", "human_approved"? }
# I9 GATE: sem human_approved=true → 202 awaiting
# ─────────────────────────────────────────────
@comm_bridge_bp.route("/publish", methods=["POST"])
def bridge_publish():
    data           = request.get_json(silent=True) or {}
    session_id     = data.get("session_id")
    human_approved = data.get("human_approved", False)

    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400

    try:
        with get_db() as db:
            row = db.execute("""
                SELECT id, title, content_blocks, status, wallet_id
                FROM comm_sessions WHERE id=?
            """, (session_id,)).fetchone()

            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404
            if row["status"] == "published":
                return jsonify({
                    "status":     "already_published",
                    "session_id": session_id,
                    "verify_url": db.execute(
                        "SELECT verify_url FROM comm_sessions WHERE id=?",
                        (session_id,)).fetchone()["verify_url"],
                    "message":    "I11 — já selado, imutável."
                }), 200

            # ── I9 GATE ──────────────────────────────
            if not human_approved:
                db.execute("""
                    UPDATE comm_sessions SET stage='C5', updated_at=? WHERE id=?
                """, (now_iso(), session_id))
                logger.info(f"[COMM] I9 Gate: aguarda aprovação humana — {session_id}")
                return jsonify({
                    "status":     "awaiting_approval",
                    "session_id": session_id,
                    "stage":      "C5",
                    "message":    "I9 — publicação requer human_approved=true. "
                                  "AI processes. Human decides. WINDI guarantees."
                }), 202
            # ─────────────────────────────────────────

            # Hash do conteúdo final
            content_hash = compute_hash(row["content_blocks"])

            # Selar no Ledger
            seal = seal_ledger(
                session_id  = session_id,
                title       = row["title"],
                content_hash= content_hash,
                wallet_id   = row["wallet_id"] or "human-dragon"
            )

            ts = now_iso()
            db.execute("""
                UPDATE comm_sessions
                SET status='published', stage='C6',
                    human_approved=1,
                    ledger_receipt=?, verify_url=?, qr_hash=?,
                    updated_at=?
                WHERE id=?
            """, (seal["receipt_id"], seal["verify_url"],
                  content_hash, ts, session_id))

        logger.info(f"[COMM] PUBLISHED: {session_id} | receipt={seal['receipt_id']}")
        return jsonify({
            "status":       "published",
            "session_id":   session_id,
            "stage":        "C6",
            "ledger_receipt": seal["receipt_id"],
            "content_hash": content_hash,
            "verify_url":   seal["verify_url"],
            "qr_payload":   f"WINDI:{seal['receipt_id']}|{content_hash[:16]}",
            "ledger_status": seal["ledger_status"],
            "published_at": ts,
            "message":      "Communiqué selado. I11 IRREMEDIÁVEL. "
                            "AI processes. Human decides. WINDI guarantees."
        }), 200

    except Exception as e:
        logger.error(f"bridge_publish error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


# ─────────────────────────────────────────────
# GET /communique/bridge/status?session_id=XXX
# ─────────────────────────────────────────────
@comm_bridge_bp.route("/status", methods=["GET"])
def bridge_status():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400

    try:
        with get_db() as db:
            row = db.execute("""
                SELECT id, wallet_id, title, doc_type, status, stage,
                       human_approved, ledger_receipt, verify_url, qr_hash,
                       created_at, updated_at
                FROM comm_sessions WHERE id=?
            """, (session_id,)).fetchone()

            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404

            # Contar revisões
            rev_count = db.execute(
                "SELECT COUNT(*) FROM comm_revisions WHERE session_id=?",
                (session_id,)).fetchone()[0]

        return jsonify({
            "status":         "ok",
            "session_id":     row["id"],
            "wallet_id":      row["wallet_id"],
            "title":          row["title"],
            "doc_type":       row["doc_type"],
            "stage":          row["stage"],
            "session_status": row["status"],
            "human_approved": bool(row["human_approved"]),
            "revisions":      rev_count,
            "ledger_receipt": row["ledger_receipt"],
            "verify_url":     row["verify_url"],
            "qr_hash":        row["qr_hash"],
            "created_at":     row["created_at"],
            "updated_at":     row["updated_at"],
            "invariants": {
                "I9":  "ENFORCED — publicação requer human_approved",
                "I11": "ENFORCED — Ledger IRREMEDIÁVEL após C6"
            }
        }), 200

    except Exception as e:
        logger.error(f"bridge_status error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500
