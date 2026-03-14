"""
W-LEGAL-001 Legal Bridge v1.0.0
================================
Padrão: mesmo do W-JOURN-001 / W-COMM-001
Porta:  :8091 (Sandbox Core — domínio extension)
Prefix: /legal/bridge/

Endpoints:
  POST /legal/bridge/open     → cria sessão contrato (L1)
  POST /legal/bridge/save     → auto-save cláusulas/conteúdo
  POST /legal/bridge/publish  → gate humano + Ledger seal + QR
  GET  /legal/bridge/status   → estado completo da sessão

Stage Map (L1-L6):
  L1 = Brief jurídico recebido
  L2 = Rascunho contrato criado
  L3 = Edição / revisão jurídica
  L4 = Revisão final (partes)
  L5 = Aguarda assinatura humana (I9 GATE)
  L6 = Selado no Ledger + QR gerado

Invariants:
  I9  — Prohibition of Autonomy Escalation (assinatura exige human_approved)
  I11 — Permanência de Evidência Criptográfica (Ledger IRREMEDIÁVEL)
"""

from flask import Blueprint, request, jsonify
import sqlite3, hashlib, uuid, datetime, json, os, logging

logger = logging.getLogger("W-LEGAL-001")

legal_bridge_bp = Blueprint("legal_bridge", __name__, url_prefix="/legal/bridge")

# ─────────────────────────────────────────────
# DB
# ─────────────────────────────────────────────
DB_PATH = os.environ.get("WINDI_LEGAL_DB", "/opt/windi/data/legal_bridge.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS legal_sessions (
            id              TEXT PRIMARY KEY,
            wallet_id       TEXT,
            title           TEXT NOT NULL,
            doc_type        TEXT DEFAULT 'contract',
            contract_type   TEXT,
            parties         TEXT DEFAULT '[]',
            jurisdiction    TEXT DEFAULT 'BR',
            status          TEXT DEFAULT 'draft',
            stage           TEXT DEFAULT 'L1',
            content         TEXT DEFAULT '',
            clauses         TEXT DEFAULT '[]',
            metadata        TEXT DEFAULT '{}',
            ledger_receipt  TEXT,
            verify_url      TEXT,
            qr_hash         TEXT,
            human_approved  INTEGER DEFAULT 0,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS legal_revisions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL,
            content     TEXT NOT NULL,
            clauses     TEXT,
            saved_at    TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES legal_sessions(id)
        );

        CREATE TABLE IF NOT EXISTS legal_signatures (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL,
            party_name  TEXT NOT NULL,
            party_role  TEXT,
            signed_at   TEXT NOT NULL,
            signature_hash TEXT,
            FOREIGN KEY(session_id) REFERENCES legal_sessions(id)
        );
        """)

# Init na importação
try:
    init_db()
    logger.info("W-LEGAL-001 DB inicializado")
except Exception as e:
    logger.error(f"DB init error: {e}")


# ─────────────────────────────────────────────
# STAGE MAP
# L1 = Brief jurídico recebido
# L2 = Rascunho contrato criado
# L3 = Edição / revisão jurídica
# L4 = Revisão final (partes)
# L5 = Aguarda assinatura humana
# L6 = Selado no Ledger + QR gerado
# ─────────────────────────────────────────────
STAGES = ["L1", "L2", "L3", "L4", "L5", "L6"]

CONTRACT_TYPES = [
    "prestacao_servicos",
    "compra_venda",
    "locacao",
    "parceria",
    "confidencialidade",
    "trabalho",
    "sociedade",
    "licenciamento",
    "outro"
]


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"

def gen_session_id():
    return "LEGAL-" + uuid.uuid4().hex[:8].upper()

def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()

def seal_ledger(session_id: str, title: str, content_hash: str,
                wallet_id: str = "human-dragon", contract_type: str = "contract") -> dict:
    """
    Envia receipt ao Forensic Ledger :8101
    """
    import urllib.request, urllib.error

    receipt_id = f"WINDI-LEGAL-{session_id}-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    payload = json.dumps({
        "id":               receipt_id,
        "actor":            wallet_id,
        "app":              "legal-bridge",
        "doc_name":         title,
        "doc_type":         "doc",
        "governance_level": "HIGH",
        "content_hash":     f"sha256:{content_hash}",
        "sge_score":        0.0
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
# POST /legal/bridge/open
# Body: { "title", "wallet_id"?, "contract_type"?, "parties"?, "jurisdiction"? }
# ─────────────────────────────────────────────
@legal_bridge_bp.route("/open", methods=["POST"])
def bridge_open():
    data = request.get_json(silent=True) or {}
    title         = data.get("title", "Contrato sem título")
    wallet_id     = data.get("wallet_id", "anonymous")
    contract_type = data.get("contract_type", "outro")
    parties       = json.dumps(data.get("parties", []))
    jurisdiction  = data.get("jurisdiction", "BR")

    session_id = gen_session_id()
    ts = now_iso()

    try:
        with get_db() as db:
            db.execute("""
                INSERT INTO legal_sessions
                  (id, wallet_id, title, contract_type, parties, jurisdiction, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?)
            """, (session_id, wallet_id, title, contract_type, parties, jurisdiction, ts, ts))

        logger.info(f"[LEGAL] Sessão aberta: {session_id} | '{title}' | tipo={contract_type}")
        return jsonify({
            "status":        "ok",
            "session_id":    session_id,
            "stage":         "L1",
            "title":         title,
            "contract_type": contract_type,
            "jurisdiction":  jurisdiction,
            "message":       "Sessão jurídica criada. Pronto para elaboração.",
            "created_at":    ts
        }), 201

    except Exception as e:
        logger.error(f"bridge_open error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


# ─────────────────────────────────────────────
# POST /legal/bridge/save
# Body: { "session_id", "content", "clauses"?, "stage"?, "parties"? }
# ─────────────────────────────────────────────
@legal_bridge_bp.route("/save", methods=["POST"])
def bridge_save():
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    content    = data.get("content", "")
    clauses    = data.get("clauses")
    stage      = data.get("stage", "L3")
    parties    = data.get("parties")

    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400

    clauses_str = json.dumps(clauses) if clauses else None
    parties_str = json.dumps(parties) if parties else None
    content_hash = compute_hash(content)
    ts = now_iso()

    try:
        with get_db() as db:
            row = db.execute("SELECT id, status FROM legal_sessions WHERE id=?",
                             (session_id,)).fetchone()
            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404
            if row["status"] == "sealed":
                return jsonify({"status": "error",
                                "detail": "Contrato já selado — I11 IRREMEDIÁVEL"}), 409

            # Atualizar sessão
            update_fields = ["content=?", "stage=?", "updated_at=?"]
            update_values = [content, stage, ts]

            if clauses_str:
                update_fields.append("clauses=?")
                update_values.append(clauses_str)
            if parties_str:
                update_fields.append("parties=?")
                update_values.append(parties_str)

            update_values.append(session_id)

            db.execute(f"""
                UPDATE legal_sessions
                SET {", ".join(update_fields)}
                WHERE id=?
            """, update_values)

            # Gravar revisão
            db.execute("""
                INSERT INTO legal_revisions (session_id, content, clauses, saved_at)
                VALUES (?,?,?,?)
            """, (session_id, content, clauses_str, ts))

        logger.info(f"[LEGAL] Auto-save: {session_id} | stage={stage} | hash={content_hash[:8]}")
        return jsonify({
            "status":       "ok",
            "session_id":   session_id,
            "stage":        stage,
            "content_hash": content_hash,
            "saved_at":     ts,
            "message":      "Rascunho jurídico guardado."
        }), 200

    except Exception as e:
        logger.error(f"bridge_save error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


# ─────────────────────────────────────────────
# POST /legal/bridge/publish
# Body: { "session_id", "human_approved"?, "signer_name"?, "signer_role"? }
# I9 GATE: sem human_approved=true → 202 awaiting
# ─────────────────────────────────────────────
@legal_bridge_bp.route("/publish", methods=["POST"])
def bridge_publish():
    data           = request.get_json(silent=True) or {}
    session_id     = data.get("session_id")
    human_approved = data.get("human_approved", False)
    signer_name    = data.get("signer_name", "Human Dragon")
    signer_role    = data.get("signer_role", "Signatário")

    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400

    try:
        with get_db() as db:
            row = db.execute("""
                SELECT id, title, content, clauses, status, wallet_id, contract_type, parties
                FROM legal_sessions WHERE id=?
            """, (session_id,)).fetchone()

            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404
            if row["status"] == "sealed":
                return jsonify({
                    "status":     "already_sealed",
                    "session_id": session_id,
                    "verify_url": db.execute(
                        "SELECT verify_url FROM legal_sessions WHERE id=?",
                        (session_id,)).fetchone()["verify_url"],
                    "message":    "I11 — contrato já selado, imutável."
                }), 200

            # ── I9 GATE ──────────────────────────────
            if not human_approved:
                db.execute("""
                    UPDATE legal_sessions SET stage='L5', updated_at=? WHERE id=?
                """, (now_iso(), session_id))
                logger.info(f"[LEGAL] I9 Gate: aguarda assinatura — {session_id}")
                return jsonify({
                    "status":     "awaiting_signature",
                    "session_id": session_id,
                    "stage":      "L5",
                    "message":    "I9 — contrato requer assinatura humana (human_approved=true). "
                                  "AI processes. Human decides. WINDI guarantees.",
                    "warning":    "Documento jurídico não pode ser selado sem decisão humana explícita."
                }), 202
            # ─────────────────────────────────────────

            # Hash do conteúdo final (content + clauses)
            full_content = row["content"] + (row["clauses"] or "")
            content_hash = compute_hash(full_content)

            # Registar assinatura
            sig_ts = now_iso()
            sig_hash = compute_hash(f"{signer_name}:{signer_role}:{sig_ts}:{content_hash}")
            db.execute("""
                INSERT INTO legal_signatures (session_id, party_name, party_role, signed_at, signature_hash)
                VALUES (?,?,?,?,?)
            """, (session_id, signer_name, signer_role, sig_ts, sig_hash))

            # Selar no Ledger
            seal = seal_ledger(
                session_id    = session_id,
                title         = row["title"],
                content_hash  = content_hash,
                wallet_id     = row["wallet_id"] or "human-dragon",
                contract_type = row["contract_type"] or "contract"
            )

            ts = now_iso()
            db.execute("""
                UPDATE legal_sessions
                SET status='sealed', stage='L6',
                    human_approved=1,
                    ledger_receipt=?, verify_url=?, qr_hash=?,
                    updated_at=?
                WHERE id=?
            """, (seal["receipt_id"], seal["verify_url"], content_hash, ts, session_id))

        logger.info(f"[LEGAL] SEALED: {session_id} | receipt={seal['receipt_id']}")
        return jsonify({
            "status":         "sealed",
            "session_id":     session_id,
            "stage":          "L6",
            "ledger_receipt": seal["receipt_id"],
            "content_hash":   content_hash,
            "verify_url":     seal["verify_url"],
            "qr_payload":     f"WINDI:{seal['receipt_id']}|{content_hash[:16]}",
            "ledger_status":  seal["ledger_status"],
            "signature": {
                "signer":     signer_name,
                "role":       signer_role,
                "signed_at":  sig_ts,
                "sig_hash":   sig_hash[:16] + "..."
            },
            "sealed_at":      ts,
            "message":        "Contrato selado. I11 IRREMEDIÁVEL. "
                              "AI processes. Human decides. WINDI guarantees."
        }), 200

    except Exception as e:
        logger.error(f"bridge_publish error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


# ─────────────────────────────────────────────
# GET /legal/bridge/status?session_id=XXX
# ─────────────────────────────────────────────
@legal_bridge_bp.route("/status", methods=["GET"])
def bridge_status():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400

    try:
        with get_db() as db:
            row = db.execute("""
                SELECT id, wallet_id, title, doc_type, contract_type, parties,
                       jurisdiction, status, stage, human_approved,
                       ledger_receipt, verify_url, qr_hash,
                       created_at, updated_at
                FROM legal_sessions WHERE id=?
            """, (session_id,)).fetchone()

            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404

            # Contar revisões
            rev_count = db.execute(
                "SELECT COUNT(*) FROM legal_revisions WHERE session_id=?",
                (session_id,)).fetchone()[0]

            # Obter assinaturas
            sigs = db.execute(
                "SELECT party_name, party_role, signed_at FROM legal_signatures WHERE session_id=?",
                (session_id,)).fetchall()
            signatures = [{"name": s["party_name"], "role": s["party_role"], "signed_at": s["signed_at"]} for s in sigs]

        return jsonify({
            "status":          "ok",
            "session_id":      row["id"],
            "wallet_id":       row["wallet_id"],
            "title":           row["title"],
            "doc_type":        row["doc_type"],
            "contract_type":   row["contract_type"],
            "parties":         json.loads(row["parties"]) if row["parties"] else [],
            "jurisdiction":    row["jurisdiction"],
            "stage":           row["stage"],
            "session_status":  row["status"],
            "human_approved":  bool(row["human_approved"]),
            "revisions":       rev_count,
            "signatures":      signatures,
            "ledger_receipt":  row["ledger_receipt"],
            "verify_url":      row["verify_url"],
            "qr_hash":         row["qr_hash"],
            "created_at":      row["created_at"],
            "updated_at":      row["updated_at"],
            "invariants": {
                "I9":  "ENFORCED — assinatura requer human_approved",
                "I11": "ENFORCED — Ledger IRREMEDIÁVEL após L6"
            },
            "stage_map": {
                "L1": "Brief jurídico recebido",
                "L2": "Rascunho criado",
                "L3": "Revisão jurídica",
                "L4": "Revisão final (partes)",
                "L5": "Aguarda assinatura",
                "L6": "Selado no Ledger"
            }
        }), 200

    except Exception as e:
        logger.error(f"bridge_status error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500
