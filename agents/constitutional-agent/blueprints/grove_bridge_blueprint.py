"""
GROVE ARENA — Tri-Divergence Bridge v1.0.0
============================================
Porta:  :8091 (Sandbox Core — domain extension)
Prefix: /grove/bridge/

Endpoints:
  POST /grove/bridge/open      → cria sessão arena (G1)
  POST /grove/bridge/council   → submete questão ao conselho de 7 sábios
  POST /grove/bridge/publish   → gate humano + Ledger seal da síntese
  GET  /grove/bridge/status    → estado + divergence analysis

Stage Map G1-G6:
  G1 = Questão recebida
  G2 = Conselho convocado (7 agentes)
  G3 = Perspectivas individuais recolhidas
  G4 = Tri-Divergence calculado
  G5 = Aguarda aprovação humana (I9 GATE)
  G6 = Síntese selada no Ledger IRREMEDIÁVEL

Invariante I6 — Exposição de Conflitos:
  ALL_AGREE   → consenso — síntese directa
  TWO_VS_ONE  → conflito minoritário — ambas posições visíveis
  ALL_DIFFER  → conflito total — escalar para Human Dragon (I9)

NOTA: Este bridge AUGMENTA o /grove/arena existente — não substitui.
      /grove/arena = resposta imediata multi-agente
      /grove/bridge/* = sessão persistente com Tri-Divergence + Ledger

Deploy:
  cp grove_bridge_blueprint.py /opt/windi/agents/constitutional-agent/blueprints/
  # agent.py: from blueprints.grove_bridge_blueprint import grove_bridge_bp
  #           app.register_blueprint(grove_bridge_bp)
"""

from flask import Blueprint, request, jsonify
import sqlite3, hashlib, uuid, datetime, json, os, logging

logger = logging.getLogger("GROVE-ARENA")

grove_bridge_bp = Blueprint("grove_bridge", __name__, url_prefix="/grove/bridge")

DB_PATH = os.environ.get("WINDI_DB_PATH", "/opt/windi/data/grove_bridge.db")

COUNCIL = [
    {"id": "W-LEGAL-001",   "role": "Análise Jurídica",       "emoji": "⚖️"},
    {"id": "W-NOTARY-001",  "role": "Integridade Documental", "emoji": "🔏"},
    {"id": "W-COMPLY-001",  "role": "Compliance Check",       "emoji": "🛡️"},
    {"id": "W-JOURN-001",   "role": "Perspectiva Editorial",  "emoji": "📰"},
    {"id": "W-AUDIT-001",   "role": "Auditoria",              "emoji": "🔍"},
    {"id": "W-ACCT-001",    "role": "Considerações Fiscais",  "emoji": "🧾"},
    {"id": "W-COMM-001",    "role": "Comunicação",            "emoji": "✍️"},
]

DIVERGENCE = {
    "ALL_AGREE":   "Consenso — síntese directa possível",
    "TWO_VS_ONE":  "Conflito minoritário — ambas posições expostas (I6)",
    "ALL_DIFFER":  "Conflito total — escalar para Human Dragon (I9)",
    "CALCULATING": "Tri-Divergence em cálculo"
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS grove_sessions (
            id                  TEXT PRIMARY KEY,
            wallet_id           TEXT,
            question            TEXT NOT NULL,
            status              TEXT DEFAULT 'draft',
            stage               TEXT DEFAULT 'G1',
            perspectives        TEXT DEFAULT '{}',
            divergence_status   TEXT DEFAULT 'CALCULATING',
            divergence_map      TEXT DEFAULT '{}',
            synthesis           TEXT,
            ledger_receipt      TEXT,
            verify_url          TEXT,
            content_hash        TEXT,
            human_approved      INTEGER DEFAULT 0,
            escalated_to_human  INTEGER DEFAULT 0,
            created_at          TEXT NOT NULL,
            updated_at          TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS grove_perspectives (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL,
            agent_id    TEXT NOT NULL,
            position    TEXT NOT NULL,
            reasoning   TEXT,
            confidence  REAL DEFAULT 0.5,
            submitted_at TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES grove_sessions(id)
        );
        """)

try:
    init_db()
    logger.info("GROVE ARENA DB inicializado")
except Exception as e:
    logger.error(f"DB init error: {e}")


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"

def gen_session_id():
    return "GROVE-" + uuid.uuid4().hex[:8].upper()

def compute_hash(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

def calculate_divergence(perspectives: dict) -> dict:
    if not perspectives:
        return {"status": "CALCULATING", "groups": {}}
    position_groups = {}
    for agent_id, data in perspectives.items():
        pos = data.get("position", "neutral")
        pos_key = _classify_position(pos)
        if pos_key not in position_groups:
            position_groups[pos_key] = []
        position_groups[pos_key].append(agent_id)
    unique_groups = len(position_groups)
    total_agents  = len(perspectives)
    if unique_groups == 1:
        status = "ALL_AGREE"
    elif unique_groups == 2:
        status = "TWO_VS_ONE"
    else:
        status = "ALL_DIFFER"
    return {
        "status": status,
        "description": DIVERGENCE[status],
        "groups": position_groups,
        "total_agents": total_agents,
        "unique_positions": unique_groups,
        "escalate_required": status == "ALL_DIFFER"
    }

def _classify_position(text: str) -> str:
    text_lower = text.lower()
    if any(w in text_lower for w in ["sim", "yes", "ja", "aprovado", "válido", "recomend",
                                      "conforme", "correcto", "passível"]):
        return "SUPPORT"
    if any(w in text_lower for w in ["não", "no", "nein", "inválido", "risco", "violação",
                                      "bloqueado", "falha", "problema"]):
        return "OPPOSE"
    if any(w in text_lower for w in ["condicional", "depende", "parcial", "revisar",
                                      "verificar", "sujeito"]):
        return "CONDITIONAL"
    return "NEUTRAL"

def seal_ledger(session_id, question, content_hash, divergence_status, wallet_id="human-dragon"):
    import urllib.request
    receipt_id = f"WINDI-GROVE-{session_id}-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    payload = json.dumps({
        "id": receipt_id,
        "actor": wallet_id,
        "app": "grove-arena-bridge",
        "doc_name": f"Grove Synthesis: {question[:80]}",
        "doc_type": "doc",
        "governance_level": "HIGH",
        "content": (f"SHA-256:{content_hash} | Grove Arena síntese | "
                    f"Tri-Divergence: {divergence_status} | G6 IRREMEDIÁVEL")
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


@grove_bridge_bp.route("/open", methods=["POST"])
def bridge_open():
    data      = request.get_json(silent=True) or {}
    question  = data.get("question", "Questão sem título")
    wallet_id = data.get("wallet_id", "anonymous")
    session_id = gen_session_id()
    ts = now_iso()
    try:
        with get_db() as db:
            db.execute("""
                INSERT INTO grove_sessions
                  (id, wallet_id, question, created_at, updated_at)
                VALUES (?,?,?,?,?)
            """, (session_id, wallet_id, question, ts, ts))
        logger.info(f"[GROVE] Sessão aberta: {session_id} | '{question[:60]}'")
        return jsonify({
            "status": "ok", "session_id": session_id, "stage": "G1",
            "question": question,
            "council": COUNCIL,
            "divergence_states": DIVERGENCE,
            "i6_invariant": "Exposição de Conflitos — ALL_DIFFER escala para Human Dragon",
            "message": "Grove Arena convocada. 7 Sábios prontos.",
            "created_at": ts
        }), 201
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500


@grove_bridge_bp.route("/council", methods=["POST"])
def bridge_council():
    data         = request.get_json(silent=True) or {}
    session_id   = data.get("session_id")
    perspectives = data.get("perspectives", {})
    synthesis    = data.get("synthesis")
    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400
    ts = now_iso()
    try:
        with get_db() as db:
            row = db.execute("SELECT id, status FROM grove_sessions WHERE id=?",
                             (session_id,)).fetchone()
            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404
            if row["status"] == "published":
                return jsonify({"status": "error",
                                "detail": "Sessão já selada — I11 IRREMEDIÁVEL"}), 409
            div = calculate_divergence(perspectives)
            div_status = div["status"]
            for agent_id, p in perspectives.items():
                if isinstance(p, dict):
                    db.execute("""
                        INSERT INTO grove_perspectives
                          (session_id, agent_id, position, reasoning, confidence, submitted_at)
                        VALUES (?,?,?,?,?,?)
                    """, (session_id, agent_id,
                          p.get("position", ""),
                          p.get("reasoning", ""),
                          float(p.get("confidence", 0.5)),
                          ts))
            stage = "G5" if div_status == "ALL_DIFFER" else "G4"
            db.execute("""
                UPDATE grove_sessions
                SET perspectives=?, divergence_status=?, divergence_map=?,
                    synthesis=?, stage=?, updated_at=?,
                    escalated_to_human=?
                WHERE id=?
            """, (json.dumps(perspectives), div_status, json.dumps(div),
                  synthesis, stage, ts,
                  1 if div_status == "ALL_DIFFER" else 0,
                  session_id))
        logger.info(f"[GROVE] Council: {session_id} | divergence={div_status}")
        response = {
            "status": "ok", "session_id": session_id, "stage": stage,
            "divergence": div,
            "perspectives_received": len(perspectives),
            "council_agents": [a["id"] for a in COUNCIL],
            "saved_at": ts
        }
        if div_status == "ALL_DIFFER":
            response["i6_escalation"] = {
                "required": True,
                "message": "I6+I9 — Conflito total detectado. "
                           "Escalar para Human Dragon antes de selar síntese.",
                "action": "Human Dragon deve revisar todas as perspectivas e decidir."
            }
        elif div_status == "TWO_VS_ONE":
            response["i6_note"] = {
                "message": "I6 — Conflito minoritário exposto. "
                           "Ambas posições visíveis na síntese.",
                "minority_group": min(div["groups"].items(),
                                     key=lambda x: len(x[1]), default=(None,[]))[0]
            }
        response["message"] = (
            f"Tri-Divergence calculado: {div_status} — {DIVERGENCE[div_status]}"
        )
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"bridge_council error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


@grove_bridge_bp.route("/publish", methods=["POST"])
def bridge_publish():
    data           = request.get_json(silent=True) or {}
    session_id     = data.get("session_id")
    human_approved = data.get("human_approved", False)
    synthesis      = data.get("synthesis")
    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400
    try:
        with get_db() as db:
            row = db.execute("""
                SELECT id, question, perspectives, divergence_status, synthesis,
                       status, wallet_id, escalated_to_human
                FROM grove_sessions WHERE id=?
            """, (session_id,)).fetchone()
            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404
            if row["status"] == "published":
                return jsonify({
                    "status": "already_published", "session_id": session_id,
                    "message": "I11 — já selado, imutável."
                }), 200
            if row["divergence_status"] == "ALL_DIFFER" and not human_approved:
                return jsonify({
                    "status": "all_differ_escalation",
                    "session_id": session_id,
                    "divergence_status": "ALL_DIFFER",
                    "i6_message": "I6 — Conflito total. Human Dragon deve decidir.",
                    "i9_message": "I9 — human_approved=true obrigatório em ALL_DIFFER.",
                    "message": "Conflito total entre os 7 Sábios. "
                               "AI processes. Human decides. WINDI guarantees."
                }), 202
            if not human_approved:
                db.execute("UPDATE grove_sessions SET stage='G5', updated_at=? WHERE id=?",
                           (now_iso(), session_id))
                return jsonify({
                    "status": "awaiting_approval", "session_id": session_id, "stage": "G5",
                    "divergence_status": row["divergence_status"],
                    "message": "I9 — Grove síntese requer human_approved=true. "
                               "AI processes. Human decides. WINDI guarantees."
                }), 202
            final_synthesis = synthesis or row["synthesis"] or ""
            content_hash    = compute_hash(
                (row["perspectives"] or "") + final_synthesis)
            seal = seal_ledger(session_id, row["question"], content_hash,
                               row["divergence_status"], row["wallet_id"] or "human-dragon")
            ts = now_iso()
            db.execute("""
                UPDATE grove_sessions
                SET status='published', stage='G6', human_approved=1,
                    synthesis=?, ledger_receipt=?, verify_url=?,
                    content_hash=?, updated_at=?
                WHERE id=?
            """, (final_synthesis, seal["receipt_id"], seal["verify_url"],
                  content_hash, ts, session_id))
        logger.info(f"[GROVE] PUBLISHED: {session_id} | receipt={seal['receipt_id']}")
        return jsonify({
            "status": "published", "session_id": session_id, "stage": "G6",
            "divergence_status": row["divergence_status"],
            "divergence_description": DIVERGENCE.get(row["divergence_status"], ""),
            "synthesis": final_synthesis,
            "ledger_receipt": seal["receipt_id"],
            "content_hash": content_hash,
            "verify_url": seal["verify_url"],
            "qr_payload": f"WINDI:{seal['receipt_id']}|{content_hash[:16]}",
            "ledger_status": seal["ledger_status"],
            "published_at": ts,
            "council": [a["id"] for a in COUNCIL],
            "message": "Grove síntese selada. I6+I11 IRREMEDIÁVEL. "
                       "AI processes. Human decides. WINDI guarantees."
        }), 200
    except Exception as e:
        logger.error(f"bridge_publish error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


@grove_bridge_bp.route("/status", methods=["GET"])
def bridge_status():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400
    try:
        with get_db() as db:
            row = db.execute("""
                SELECT id, wallet_id, question, status, stage,
                       divergence_status, divergence_map, synthesis,
                       human_approved, escalated_to_human,
                       ledger_receipt, verify_url, content_hash,
                       created_at, updated_at
                FROM grove_sessions WHERE id=?
            """, (session_id,)).fetchone()
            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404
            persp_count = db.execute(
                "SELECT COUNT(*) FROM grove_perspectives WHERE session_id=?",
                (session_id,)).fetchone()[0]
        return jsonify({
            "status": "ok", "session_id": row["id"],
            "question": row["question"],
            "stage": row["stage"], "session_status": row["status"],
            "council_size": len(COUNCIL),
            "perspectives_received": persp_count,
            "divergence_status": row["divergence_status"],
            "divergence_description": DIVERGENCE.get(row["divergence_status"], ""),
            "divergence_map": json.loads(row["divergence_map"] or "{}"),
            "synthesis": row["synthesis"],
            "human_approved": bool(row["human_approved"]),
            "escalated_to_human": bool(row["escalated_to_human"]),
            "ledger_receipt": row["ledger_receipt"],
            "verify_url": row["verify_url"],
            "content_hash": row["content_hash"],
            "created_at": row["created_at"], "updated_at": row["updated_at"],
            "invariants": {
                "I6": "ENFORCED — Tri-Divergence exposto: ALL_AGREE/TWO_VS_ONE/ALL_DIFFER",
                "I9": "ENFORCED — human_approved obrigatório; ALL_DIFFER escala para Human Dragon",
                "I11": "ENFORCED — Ledger IRREMEDIÁVEL após G6"
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500
