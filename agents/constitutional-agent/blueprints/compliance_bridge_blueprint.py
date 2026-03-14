"""
W-COMPLIANCE-001 Compliance Bridge v1.0.0
==========================================
Padrão: mesmo do W-JOURN/COMM/LEGAL/NOTARY/AUDIT
Porta:  :8091 (Sandbox Core — domínio extension)
Prefix: /compliance/bridge/

Endpoints:
  POST /compliance/bridge/open     → cria sessão compliance (CP1)
  POST /compliance/bridge/save     → auto-save requisitos/gaps
  POST /compliance/bridge/publish  → gate humano + Ledger seal + QR
  GET  /compliance/bridge/status   → estado completo da sessão

Stage Map (CP1-CP6):
  CP1 = Pedido de compliance recebido
  CP2 = Escopo regulatório definido
  CP3 = Verificação de requisitos
  CP4 = Análise de gaps
  CP5 = Aguarda aprovação humana (I9 GATE)
  CP6 = Selado no Ledger + QR gerado

Invariants:
  I9  — Prohibition of Autonomy Escalation (certificação exige human_approved)
  I11 — Permanência de Evidência Criptográfica (Ledger IRREMEDIÁVEL)
"""

from flask import Blueprint, request, jsonify
import sqlite3, hashlib, uuid, datetime, json, os, logging

logger = logging.getLogger("W-COMPLIANCE-001")

compliance_bridge_bp = Blueprint("compliance_bridge", __name__, url_prefix="/compliance/bridge")

# ─────────────────────────────────────────────
# DB
# ─────────────────────────────────────────────
DB_PATH = os.environ.get("WINDI_COMPLIANCE_DB", "/opt/windi/data/compliance_bridge.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS compliance_sessions (
            id              TEXT PRIMARY KEY,
            wallet_id       TEXT,
            title           TEXT NOT NULL,
            regulation      TEXT DEFAULT 'eu_ai_act',
            target_entity   TEXT,
            scope           TEXT,
            status          TEXT DEFAULT 'draft',
            stage           TEXT DEFAULT 'CP1',
            executive_summary TEXT DEFAULT '',
            compliance_score REAL DEFAULT 0.0,
            metadata        TEXT DEFAULT '{}',
            ledger_receipt  TEXT,
            verify_url      TEXT,
            qr_hash         TEXT,
            human_approved  INTEGER DEFAULT 0,
            certifier_name  TEXT,
            certifier_credential TEXT,
            certification_level TEXT,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS compliance_requirements (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      TEXT NOT NULL,
            req_id          TEXT NOT NULL,
            article         TEXT,
            requirement     TEXT NOT NULL,
            status          TEXT DEFAULT 'pending',
            evidence        TEXT,
            notes           TEXT,
            weight          REAL DEFAULT 1.0,
            created_at      TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES compliance_sessions(id)
        );

        CREATE TABLE IF NOT EXISTS compliance_gaps (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      TEXT NOT NULL,
            gap_id          TEXT NOT NULL,
            requirement_id  TEXT,
            severity        TEXT DEFAULT 'medium',
            description     TEXT NOT NULL,
            remediation     TEXT,
            deadline        TEXT,
            status          TEXT DEFAULT 'open',
            created_at      TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES compliance_sessions(id)
        );

        CREATE TABLE IF NOT EXISTS compliance_revisions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL,
            content     TEXT NOT NULL,
            saved_at    TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES compliance_sessions(id)
        );
        """)

# Init na importação
try:
    init_db()
    logger.info("W-COMPLIANCE-001 DB inicializado")
except Exception as e:
    logger.error(f"DB init error: {e}")


# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
STAGES = ["CP1", "CP2", "CP3", "CP4", "CP5", "CP6"]

REGULATIONS = [
    "eu_ai_act",
    "gdpr",
    "lgpd",
    "sox",
    "iso27001",
    "iso9001",
    "hipaa",
    "pci_dss",
    "windi_constitution",
    "outro"
]

REQUIREMENT_STATUS = ["compliant", "partial", "non_compliant", "not_applicable", "pending"]
CERTIFICATION_LEVELS = ["GOLD", "SILVER", "BRONZE", "PENDING", "FAILED"]


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"

def gen_session_id():
    return "COMPL-" + uuid.uuid4().hex[:8].upper()

def gen_req_id():
    return "REQ-" + uuid.uuid4().hex[:6].upper()

def gen_gap_id():
    return "GAP-" + uuid.uuid4().hex[:6].upper()

def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()

def calculate_compliance_score(requirements: list) -> float:
    """Calcula score de compliance baseado nos requisitos."""
    if not requirements:
        return 0.0

    total_weight = sum(r.get("weight", 1.0) for r in requirements)
    compliant_weight = sum(
        r.get("weight", 1.0) for r in requirements
        if r.get("status") == "compliant"
    )
    partial_weight = sum(
        r.get("weight", 1.0) * 0.5 for r in requirements
        if r.get("status") == "partial"
    )

    if total_weight == 0:
        return 0.0

    return round(((compliant_weight + partial_weight) / total_weight) * 100, 1)

def seal_ledger(session_id: str, title: str, content_hash: str,
                wallet_id: str = "human-dragon", regulation: str = "compliance") -> dict:
    """Envia receipt ao Forensic Ledger :8101"""
    import urllib.request, urllib.error

    receipt_id = f"WINDI-COMPL-{session_id}-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    payload = json.dumps({
        "id":               receipt_id,
        "actor":            wallet_id,
        "app":              "compliance-bridge",
        "doc_name":         title,
        "doc_type":         f"compliance_{regulation}",
        "governance_level": "CRITICAL",
        "content":          f"SHA-256:{content_hash} | Compliance Report selado via Bridge CP6"
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
# POST /compliance/bridge/open
# ─────────────────────────────────────────────
@compliance_bridge_bp.route("/open", methods=["POST"])
def bridge_open():
    data = request.get_json(silent=True) or {}
    title         = data.get("title", "Relatório de Compliance")
    wallet_id     = data.get("wallet_id", "anonymous")
    regulation    = data.get("regulation", "eu_ai_act")
    target_entity = data.get("target_entity", "")
    scope         = data.get("scope", "")

    session_id = gen_session_id()
    ts = now_iso()

    try:
        with get_db() as db:
            db.execute("""
                INSERT INTO compliance_sessions
                  (id, wallet_id, title, regulation, target_entity, scope, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?)
            """, (session_id, wallet_id, title, regulation, target_entity, scope, ts, ts))

        logger.info(f"[COMPLIANCE] Sessão aberta: {session_id} | '{title}' | reg={regulation}")
        return jsonify({
            "status":        "ok",
            "session_id":    session_id,
            "stage":         "CP1",
            "title":         title,
            "regulation":    regulation,
            "target_entity": target_entity,
            "message":       "Sessão de compliance criada. Pronto para definir requisitos.",
            "created_at":    ts
        }), 201

    except Exception as e:
        logger.error(f"bridge_open error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


# ─────────────────────────────────────────────
# POST /compliance/bridge/save
# ─────────────────────────────────────────────
@compliance_bridge_bp.route("/save", methods=["POST"])
def bridge_save():
    data = request.get_json(silent=True) or {}
    session_id        = data.get("session_id")
    executive_summary = data.get("executive_summary", "")
    requirements      = data.get("requirements", [])
    gaps              = data.get("gaps", [])
    stage             = data.get("stage", "CP3")

    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400

    ts = now_iso()

    try:
        with get_db() as db:
            row = db.execute("SELECT id, status FROM compliance_sessions WHERE id=?",
                             (session_id,)).fetchone()
            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404
            if row["status"] == "certified":
                return jsonify({"status": "error",
                                "detail": "Compliance já certificado — I11 IRREMEDIÁVEL"}), 409

            # Adicionar requisitos
            reqs_added = 0
            for r in requirements:
                req_id = r.get("id", gen_req_id())
                db.execute("""
                    INSERT OR REPLACE INTO compliance_requirements
                      (session_id, req_id, article, requirement, status, evidence, notes, weight, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?)
                """, (session_id, req_id, r.get("article", ""),
                      r.get("requirement", ""), r.get("status", "pending"),
                      r.get("evidence", ""), r.get("notes", ""),
                      r.get("weight", 1.0), ts))
                reqs_added += 1

            # Adicionar gaps
            gaps_added = 0
            for g in gaps:
                gap_id = g.get("id", gen_gap_id())
                db.execute("""
                    INSERT INTO compliance_gaps
                      (session_id, gap_id, requirement_id, severity, description,
                       remediation, deadline, status, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?)
                """, (session_id, gap_id, g.get("requirement_id", ""),
                      g.get("severity", "medium"), g.get("description", ""),
                      g.get("remediation", ""), g.get("deadline", ""),
                      g.get("status", "open"), ts))
                gaps_added += 1

            # Calcular compliance score
            all_reqs = db.execute("""
                SELECT status, weight FROM compliance_requirements WHERE session_id=?
            """, (session_id,)).fetchall()
            req_list = [{"status": r["status"], "weight": r["weight"]} for r in all_reqs]
            compliance_score = calculate_compliance_score(req_list)

            # Atualizar sessão
            db.execute("""
                UPDATE compliance_sessions
                SET executive_summary=?, compliance_score=?, stage=?, updated_at=?
                WHERE id=?
            """, (executive_summary, compliance_score, stage, ts, session_id))

            # Gravar revisão
            revision_content = json.dumps({
                "executive_summary": executive_summary,
                "requirements_count": reqs_added,
                "gaps_count": gaps_added,
                "compliance_score": compliance_score
            })
            db.execute("""
                INSERT INTO compliance_revisions (session_id, content, saved_at)
                VALUES (?,?,?)
            """, (session_id, revision_content, ts))

        content_hash = compute_hash(executive_summary + str(compliance_score))
        logger.info(f"[COMPLIANCE] Auto-save: {session_id} | stage={stage} | score={compliance_score}%")
        return jsonify({
            "status":           "ok",
            "session_id":       session_id,
            "stage":            stage,
            "content_hash":     content_hash,
            "requirements_added": reqs_added,
            "gaps_added":       gaps_added,
            "compliance_score": compliance_score,
            "saved_at":         ts,
            "message":          "Relatório de compliance guardado."
        }), 200

    except Exception as e:
        logger.error(f"bridge_save error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


# ─────────────────────────────────────────────
# POST /compliance/bridge/publish
# I9 GATE: sem human_approved=true → 202 awaiting
# ─────────────────────────────────────────────
@compliance_bridge_bp.route("/publish", methods=["POST"])
def bridge_publish():
    data               = request.get_json(silent=True) or {}
    session_id         = data.get("session_id")
    human_approved     = data.get("human_approved", False)
    certifier_name     = data.get("certifier_name", "WINDI Compliance Officer")
    certifier_credential = data.get("certifier_credential", "WINDI-COMPL-001")

    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400

    try:
        with get_db() as db:
            row = db.execute("""
                SELECT id, title, executive_summary, compliance_score, status, wallet_id, regulation
                FROM compliance_sessions WHERE id=?
            """, (session_id,)).fetchone()

            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404
            if row["status"] == "certified":
                return jsonify({
                    "status":     "already_certified",
                    "session_id": session_id,
                    "verify_url": db.execute(
                        "SELECT verify_url FROM compliance_sessions WHERE id=?",
                        (session_id,)).fetchone()["verify_url"],
                    "message":    "I11 — compliance já certificado, imutável."
                }), 200

            # ── I9 GATE ──────────────────────────────
            if not human_approved:
                db.execute("""
                    UPDATE compliance_sessions SET stage='CP5', updated_at=? WHERE id=?
                """, (now_iso(), session_id))
                logger.info(f"[COMPLIANCE] I9 Gate: aguarda aprovação — {session_id}")
                return jsonify({
                    "status":     "awaiting_certification",
                    "session_id": session_id,
                    "stage":      "CP5",
                    "compliance_score": row["compliance_score"],
                    "message":    "I9 — certificação de compliance requer aprovação humana (human_approved=true). "
                                  "AI processes. Human decides. WINDI guarantees.",
                    "warning":    "Certificação não pode ser emitida sem validação humana."
                }), 202
            # ─────────────────────────────────────────

            # Determinar nível de certificação
            score = row["compliance_score"] or 0
            if score >= 95:
                certification_level = "GOLD"
            elif score >= 80:
                certification_level = "SILVER"
            elif score >= 60:
                certification_level = "BRONZE"
            else:
                certification_level = "PENDING"

            # Contar requisitos e gaps
            reqs = db.execute("""
                SELECT status FROM compliance_requirements WHERE session_id=?
            """, (session_id,)).fetchall()

            req_summary = {"compliant": 0, "partial": 0, "non_compliant": 0, "not_applicable": 0, "pending": 0}
            for r in reqs:
                if r["status"] in req_summary:
                    req_summary[r["status"]] += 1

            gaps_open = db.execute("""
                SELECT COUNT(*) FROM compliance_gaps WHERE session_id=? AND status='open'
            """, (session_id,)).fetchone()[0]

            # Hash do conteúdo final
            full_content = (row["executive_summary"] or "") + str(score) + certification_level
            content_hash = compute_hash(full_content)

            # Selar no Ledger
            seal = seal_ledger(
                session_id  = session_id,
                title       = row["title"],
                content_hash= content_hash,
                wallet_id   = row["wallet_id"] or "human-dragon",
                regulation  = row["regulation"] or "compliance"
            )

            ts = now_iso()
            db.execute("""
                UPDATE compliance_sessions
                SET status='certified', stage='CP6',
                    human_approved=1,
                    certifier_name=?, certifier_credential=?, certification_level=?,
                    ledger_receipt=?, verify_url=?, qr_hash=?,
                    updated_at=?
                WHERE id=?
            """, (certifier_name, certifier_credential, certification_level,
                  seal["receipt_id"], seal["verify_url"], content_hash, ts, session_id))

        logger.info(f"[COMPLIANCE] CERTIFIED: {session_id} | level={certification_level} | receipt={seal['receipt_id']}")
        return jsonify({
            "status":            "certified",
            "session_id":        session_id,
            "stage":             "CP6",
            "ledger_receipt":    seal["receipt_id"],
            "content_hash":      content_hash,
            "verify_url":        seal["verify_url"],
            "qr_payload":        f"WINDI:{seal['receipt_id']}|{content_hash[:16]}",
            "ledger_status":     seal["ledger_status"],
            "certification": {
                "level":         certification_level,
                "score":         score,
                "certifier":     certifier_name,
                "credential":    certifier_credential
            },
            "requirements_summary": req_summary,
            "total_requirements": len(reqs),
            "open_gaps":         gaps_open,
            "certified_at":      ts,
            "message":           f"Compliance certificado: {certification_level}. I11 IRREMEDIÁVEL. "
                                 "AI processes. Human decides. WINDI guarantees."
        }), 200

    except Exception as e:
        logger.error(f"bridge_publish error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


# ─────────────────────────────────────────────
# GET /compliance/bridge/status?session_id=XXX
# ─────────────────────────────────────────────
@compliance_bridge_bp.route("/status", methods=["GET"])
def bridge_status():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400

    try:
        with get_db() as db:
            row = db.execute("""
                SELECT id, wallet_id, title, regulation, target_entity, scope,
                       status, stage, compliance_score, human_approved,
                       certifier_name, certifier_credential, certification_level,
                       ledger_receipt, verify_url, qr_hash,
                       created_at, updated_at
                FROM compliance_sessions WHERE id=?
            """, (session_id,)).fetchone()

            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404

            # Obter requisitos
            reqs = db.execute("""
                SELECT req_id, article, requirement, status, weight
                FROM compliance_requirements WHERE session_id=?
            """, (session_id,)).fetchall()
            requirements = [{"id": r["req_id"], "article": r["article"],
                            "requirement": r["requirement"], "status": r["status"],
                            "weight": r["weight"]} for r in reqs]

            # Obter gaps
            gaps = db.execute("""
                SELECT gap_id, severity, description, remediation, status
                FROM compliance_gaps WHERE session_id=?
            """, (session_id,)).fetchall()
            gaps_list = [{"id": g["gap_id"], "severity": g["severity"],
                         "description": g["description"], "remediation": g["remediation"],
                         "status": g["status"]} for g in gaps]

            # Contar revisões
            rev_count = db.execute(
                "SELECT COUNT(*) FROM compliance_revisions WHERE session_id=?",
                (session_id,)).fetchone()[0]

        return jsonify({
            "status":            "ok",
            "session_id":        row["id"],
            "wallet_id":         row["wallet_id"],
            "title":             row["title"],
            "regulation":        row["regulation"],
            "target_entity":     row["target_entity"],
            "scope":             row["scope"],
            "stage":             row["stage"],
            "session_status":    row["status"],
            "compliance_score":  row["compliance_score"],
            "human_approved":    bool(row["human_approved"]),
            "certification": {
                "level":         row["certification_level"],
                "certifier":     row["certifier_name"],
                "credential":    row["certifier_credential"]
            } if row["certification_level"] else None,
            "requirements":      requirements,
            "requirements_count": len(requirements),
            "gaps":              gaps_list,
            "gaps_count":        len(gaps_list),
            "revisions":         rev_count,
            "ledger_receipt":    row["ledger_receipt"],
            "verify_url":        row["verify_url"],
            "qr_hash":           row["qr_hash"],
            "created_at":        row["created_at"],
            "updated_at":        row["updated_at"],
            "invariants": {
                "I9":  "ENFORCED — certificação requer human_approved",
                "I11": "ENFORCED — Ledger IRREMEDIÁVEL após CP6"
            },
            "stage_map": {
                "CP1": "Pedido de compliance recebido",
                "CP2": "Escopo regulatório definido",
                "CP3": "Verificação de requisitos",
                "CP4": "Análise de gaps",
                "CP5": "Aguarda certificação",
                "CP6": "Selado no Ledger"
            },
            "regulations_available": REGULATIONS,
            "certification_levels": CERTIFICATION_LEVELS
        }), 200

    except Exception as e:
        logger.error(f"bridge_status error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500
