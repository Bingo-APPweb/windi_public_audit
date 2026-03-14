"""
W-NOTARY-001 Notary Bridge v1.0.0
==================================
Padrão: mesmo do W-JOURN-001 / W-COMM-001 / W-LEGAL-001
Porta:  :8091 (Sandbox Core — domínio extension)
Prefix: /notary/bridge/

Endpoints:
  POST /notary/bridge/open     → cria sessão certidão (N1)
  POST /notary/bridge/save     → auto-save conteúdo
  POST /notary/bridge/publish  → gate humano + Ledger seal + QR
  GET  /notary/bridge/status   → estado completo da sessão

Stage Map (N1-N6):
  N1 = Pedido de certidão recebido
  N2 = Documento preparado
  N3 = Verificação de dados
  N4 = Revisão final
  N5 = Aguarda autenticação humana (I9 GATE)
  N6 = Selado no Ledger + QR gerado

Invariants:
  I9  — Prohibition of Autonomy Escalation (autenticação exige human_approved)
  I11 — Permanência de Evidência Criptográfica (Ledger IRREMEDIÁVEL)
"""

from flask import Blueprint, request, jsonify
import sqlite3, hashlib, uuid, datetime, json, os, logging

logger = logging.getLogger("W-NOTARY-001")

notary_bridge_bp = Blueprint("notary_bridge", __name__, url_prefix="/notary/bridge")

# ─────────────────────────────────────────────
# DB
# ─────────────────────────────────────────────
DB_PATH = os.environ.get("WINDI_NOTARY_DB", "/opt/windi/data/notary_bridge.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS notary_sessions (
            id              TEXT PRIMARY KEY,
            wallet_id       TEXT,
            title           TEXT NOT NULL,
            cert_type       TEXT DEFAULT 'certidao',
            declarant_name  TEXT,
            declarant_doc   TEXT,
            purpose         TEXT,
            status          TEXT DEFAULT 'draft',
            stage           TEXT DEFAULT 'N1',
            content         TEXT DEFAULT '',
            metadata        TEXT DEFAULT '{}',
            ledger_receipt  TEXT,
            verify_url      TEXT,
            qr_hash         TEXT,
            human_approved  INTEGER DEFAULT 0,
            notary_name     TEXT,
            notary_seal     TEXT,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS notary_revisions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL,
            content     TEXT NOT NULL,
            saved_at    TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES notary_sessions(id)
        );

        CREATE TABLE IF NOT EXISTS notary_witnesses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL,
            name        TEXT NOT NULL,
            document    TEXT,
            added_at    TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES notary_sessions(id)
        );
        """)

# Init na importação
try:
    init_db()
    logger.info("W-NOTARY-001 DB inicializado")
except Exception as e:
    logger.error(f"DB init error: {e}")


# ─────────────────────────────────────────────
# STAGE MAP
# N1 = Pedido de certidão recebido
# N2 = Documento preparado
# N3 = Verificação de dados
# N4 = Revisão final
# N5 = Aguarda autenticação humana
# N6 = Selado no Ledger + QR gerado
# ─────────────────────────────────────────────
STAGES = ["N1", "N2", "N3", "N4", "N5", "N6"]

CERT_TYPES = [
    "certidao",
    "atestado",
    "declaracao",
    "reconhecimento_firma",
    "autenticacao",
    "procuracao",
    "ata_notarial",
    "escritura",
    "outro"
]


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"

def gen_session_id():
    return "NOTARY-" + uuid.uuid4().hex[:8].upper()

def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()

def seal_ledger(session_id: str, title: str, content_hash: str,
                wallet_id: str = "human-dragon", cert_type: str = "certidao") -> dict:
    """
    Envia receipt ao Forensic Ledger :8101
    """
    import urllib.request, urllib.error

    receipt_id = f"WINDI-NOTARY-{session_id}-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    payload = json.dumps({
        "id":               receipt_id,
        "actor":            wallet_id,
        "app":              "notary-bridge",
        "doc_name":         title,
        "doc_type":         cert_type,
        "governance_level": "CRITICAL",
        "content":          f"SHA-256:{content_hash} | Certidão selada via Notary Bridge N6"
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
        logger.warning(f"Ledger seal falhou: {e}")
        verify_url = f"https://windi-domain.com/verify-public/?id={receipt_id}"
        return {"receipt_id": receipt_id, "hash": content_hash,
                "verify_url": verify_url, "ledger_status": "PENDING_RETRY"}


# ─────────────────────────────────────────────
# POST /notary/bridge/open
# Body: { "title", "cert_type"?, "declarant_name"?, "declarant_doc"?, "purpose"? }
# ─────────────────────────────────────────────
@notary_bridge_bp.route("/open", methods=["POST"])
def bridge_open():
    data = request.get_json(silent=True) or {}
    title          = data.get("title", "Certidão sem título")
    wallet_id      = data.get("wallet_id", "anonymous")
    cert_type      = data.get("cert_type", "certidao")
    declarant_name = data.get("declarant_name", "")
    declarant_doc  = data.get("declarant_doc", "")
    purpose        = data.get("purpose", "")

    session_id = gen_session_id()
    ts = now_iso()

    try:
        with get_db() as db:
            db.execute("""
                INSERT INTO notary_sessions
                  (id, wallet_id, title, cert_type, declarant_name, declarant_doc, purpose, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (session_id, wallet_id, title, cert_type, declarant_name, declarant_doc, purpose, ts, ts))

        logger.info(f"[NOTARY] Sessão aberta: {session_id} | '{title}' | tipo={cert_type}")
        return jsonify({
            "status":         "ok",
            "session_id":     session_id,
            "stage":          "N1",
            "title":          title,
            "cert_type":      cert_type,
            "declarant_name": declarant_name,
            "message":        "Sessão notarial criada. Pronto para elaboração.",
            "created_at":     ts
        }), 201

    except Exception as e:
        logger.error(f"bridge_open error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


# ─────────────────────────────────────────────
# POST /notary/bridge/save
# Body: { "session_id", "content", "stage"?, "witnesses"? }
# ─────────────────────────────────────────────
@notary_bridge_bp.route("/save", methods=["POST"])
def bridge_save():
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    content    = data.get("content", "")
    stage      = data.get("stage", "N3")
    witnesses  = data.get("witnesses", [])

    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400

    content_hash = compute_hash(content)
    ts = now_iso()

    try:
        with get_db() as db:
            row = db.execute("SELECT id, status FROM notary_sessions WHERE id=?",
                             (session_id,)).fetchone()
            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404
            if row["status"] == "authenticated":
                return jsonify({"status": "error",
                                "detail": "Certidão já autenticada — I11 IRREMEDIÁVEL"}), 409

            # Atualizar sessão
            db.execute("""
                UPDATE notary_sessions
                SET content=?, stage=?, updated_at=?
                WHERE id=?
            """, (content, stage, ts, session_id))

            # Gravar revisão
            db.execute("""
                INSERT INTO notary_revisions (session_id, content, saved_at)
                VALUES (?,?,?)
            """, (session_id, content, ts))

            # Adicionar testemunhas se fornecidas
            for w in witnesses:
                db.execute("""
                    INSERT INTO notary_witnesses (session_id, name, document, added_at)
                    VALUES (?,?,?,?)
                """, (session_id, w.get("name", ""), w.get("document", ""), ts))

        logger.info(f"[NOTARY] Auto-save: {session_id} | stage={stage} | hash={content_hash[:8]}")
        return jsonify({
            "status":       "ok",
            "session_id":   session_id,
            "stage":        stage,
            "content_hash": content_hash,
            "witnesses_added": len(witnesses),
            "saved_at":     ts,
            "message":      "Documento notarial guardado."
        }), 200

    except Exception as e:
        logger.error(f"bridge_save error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


# ─────────────────────────────────────────────
# POST /notary/bridge/publish
# Body: { "session_id", "human_approved"?, "notary_name"?, "notary_seal"? }
# I9 GATE: sem human_approved=true → 202 awaiting
# ─────────────────────────────────────────────
@notary_bridge_bp.route("/publish", methods=["POST"])
def bridge_publish():
    data           = request.get_json(silent=True) or {}
    session_id     = data.get("session_id")
    human_approved = data.get("human_approved", False)
    notary_name    = data.get("notary_name", "Notário WINDI")
    notary_seal    = data.get("notary_seal", "WINDI-SEAL-001")

    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400

    try:
        with get_db() as db:
            row = db.execute("""
                SELECT id, title, content, status, wallet_id, cert_type, declarant_name
                FROM notary_sessions WHERE id=?
            """, (session_id,)).fetchone()

            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404
            if row["status"] == "authenticated":
                return jsonify({
                    "status":     "already_authenticated",
                    "session_id": session_id,
                    "verify_url": db.execute(
                        "SELECT verify_url FROM notary_sessions WHERE id=?",
                        (session_id,)).fetchone()["verify_url"],
                    "message":    "I11 — certidão já autenticada, imutável."
                }), 200

            # ── I9 GATE ──────────────────────────────
            if not human_approved:
                db.execute("""
                    UPDATE notary_sessions SET stage='N5', updated_at=? WHERE id=?
                """, (now_iso(), session_id))
                logger.info(f"[NOTARY] I9 Gate: aguarda autenticação — {session_id}")
                return jsonify({
                    "status":     "awaiting_authentication",
                    "session_id": session_id,
                    "stage":      "N5",
                    "message":    "I9 — certidão requer autenticação humana (human_approved=true). "
                                  "AI processes. Human decides. WINDI guarantees.",
                    "warning":    "Documento notarial não pode ser selado sem fé pública humana."
                }), 202
            # ─────────────────────────────────────────

            # Hash do conteúdo final
            content_hash = compute_hash(row["content"])

            # Gerar selo notarial
            seal_ts = now_iso()
            seal_hash = compute_hash(f"{notary_name}:{notary_seal}:{seal_ts}:{content_hash}")

            # Selar no Ledger
            seal = seal_ledger(
                session_id   = session_id,
                title        = row["title"],
                content_hash = content_hash,
                wallet_id    = row["wallet_id"] or "human-dragon",
                cert_type    = row["cert_type"] or "certidao"
            )

            ts = now_iso()
            db.execute("""
                UPDATE notary_sessions
                SET status='authenticated', stage='N6',
                    human_approved=1,
                    notary_name=?, notary_seal=?,
                    ledger_receipt=?, verify_url=?, qr_hash=?,
                    updated_at=?
                WHERE id=?
            """, (notary_name, notary_seal, seal["receipt_id"], seal["verify_url"], content_hash, ts, session_id))

            # Contar testemunhas
            witness_count = db.execute(
                "SELECT COUNT(*) FROM notary_witnesses WHERE session_id=?",
                (session_id,)).fetchone()[0]

        logger.info(f"[NOTARY] AUTHENTICATED: {session_id} | receipt={seal['receipt_id']}")
        return jsonify({
            "status":         "authenticated",
            "session_id":     session_id,
            "stage":          "N6",
            "ledger_receipt": seal["receipt_id"],
            "content_hash":   content_hash,
            "verify_url":     seal["verify_url"],
            "qr_payload":     f"WINDI:{seal['receipt_id']}|{content_hash[:16]}",
            "ledger_status":  seal["ledger_status"],
            "notary": {
                "name":       notary_name,
                "seal":       notary_seal,
                "seal_hash":  seal_hash[:16] + "...",
                "sealed_at":  seal_ts
            },
            "declarant":      row["declarant_name"],
            "witnesses":      witness_count,
            "authenticated_at": ts,
            "message":        "Certidão autenticada. I11 IRREMEDIÁVEL. "
                              "AI processes. Human decides. WINDI guarantees."
        }), 200

    except Exception as e:
        logger.error(f"bridge_publish error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


# ─────────────────────────────────────────────
# GET /notary/bridge/status?session_id=XXX
# ─────────────────────────────────────────────
@notary_bridge_bp.route("/status", methods=["GET"])
def bridge_status():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400

    try:
        with get_db() as db:
            row = db.execute("""
                SELECT id, wallet_id, title, cert_type, declarant_name, declarant_doc,
                       purpose, status, stage, human_approved,
                       notary_name, notary_seal,
                       ledger_receipt, verify_url, qr_hash,
                       created_at, updated_at
                FROM notary_sessions WHERE id=?
            """, (session_id,)).fetchone()

            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404

            # Contar revisões
            rev_count = db.execute(
                "SELECT COUNT(*) FROM notary_revisions WHERE session_id=?",
                (session_id,)).fetchone()[0]

            # Obter testemunhas
            witnesses = db.execute(
                "SELECT name, document, added_at FROM notary_witnesses WHERE session_id=?",
                (session_id,)).fetchall()
            witness_list = [{"name": w["name"], "document": w["document"], "added_at": w["added_at"]} for w in witnesses]

        return jsonify({
            "status":          "ok",
            "session_id":      row["id"],
            "wallet_id":       row["wallet_id"],
            "title":           row["title"],
            "cert_type":       row["cert_type"],
            "declarant": {
                "name":        row["declarant_name"],
                "document":    row["declarant_doc"]
            },
            "purpose":         row["purpose"],
            "stage":           row["stage"],
            "session_status":  row["status"],
            "human_approved":  bool(row["human_approved"]),
            "revisions":       rev_count,
            "witnesses":       witness_list,
            "notary": {
                "name":        row["notary_name"],
                "seal":        row["notary_seal"]
            } if row["notary_name"] else None,
            "ledger_receipt":  row["ledger_receipt"],
            "verify_url":      row["verify_url"],
            "qr_hash":         row["qr_hash"],
            "created_at":      row["created_at"],
            "updated_at":      row["updated_at"],
            "invariants": {
                "I9":  "ENFORCED — autenticação requer human_approved",
                "I11": "ENFORCED — Ledger IRREMEDIÁVEL após N6"
            },
            "stage_map": {
                "N1": "Pedido de certidão recebido",
                "N2": "Documento preparado",
                "N3": "Verificação de dados",
                "N4": "Revisão final",
                "N5": "Aguarda autenticação",
                "N6": "Selado no Ledger"
            },
            "cert_types_available": CERT_TYPES
        }), 200

    except Exception as e:
        logger.error(f"bridge_status error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500
