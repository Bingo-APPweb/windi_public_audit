"""
W-GROVE-001 — Grove Orchestrator
Domain extension do constitutional-agent (:8091)
Version: 1.0.0

Iron Rule: Este arquivo é registado em blueprints/ e importado
pelo constitutional-agent/agent.py — NÃO cria porta própria.

Converted from FastAPI to Flask Blueprint for constitutional-agent integration.
"""

from flask import Blueprint, request, jsonify
import sqlite3
import uuid
import json
import requests
from datetime import datetime
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
GROVE_DB   = Path("/opt/windi/agents/constitutional-agent/grove.db")
LEDGER_URL = "http://127.0.0.1:8101"
SANDBOX    = "http://127.0.0.1:8091"

grove_bp = Blueprint('grove', __name__, url_prefix='/grove')

# ── Agent Registry ────────────────────────────────────────────────────────────
AGENT_REGISTRY = {
    "W-LEGAL-001":  {"topics": ["jurídico","lei","contrato","evidência","jurisdição"],   "endpoint": "/legal/analyze"},
    "W-NOTARY-001": {"topics": ["autenticidade","assinatura","certificação"],            "endpoint": "/notary/certify"},
    "W-COMPLY-001": {"topics": ["conformidade","regulação","gdpr","risco","compliance"], "endpoint": "/compliance/check"},
    "W-COMM-001":   {"topics": ["documento","whitepaper","rascunho","estrutura"],        "endpoint": "/communique/create"},
    "W-JOURN-001":  {"topics": ["publicação","notícia","manifesto","comunicado"],        "endpoint": "/journalist/draft"},
    "W-AUDIT-001":  {"topics": ["auditoria","verificação","integridade"],                "endpoint": "/audit/verify"},
    "W-ACCT-001":   {"topics": ["financeiro","contabilidade","fatura","elster"],         "endpoint": "/accounting/review"},
}

# ── DB Init ───────────────────────────────────────────────────────────────────
def init_grove_db():
    conn = sqlite3.connect(GROVE_DB)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS grove_ideas (
            id             TEXT PRIMARY KEY,
            type           TEXT NOT NULL,
            title          TEXT NOT NULL,
            content        TEXT,
            created_at     TEXT NOT NULL,
            author         TEXT NOT NULL,
            agent_source   TEXT,
            ledger_receipt TEXT,
            session_id     TEXT
        );
        CREATE TABLE IF NOT EXISTS grove_edges (
            id            TEXT PRIMARY KEY,
            source_id     TEXT NOT NULL,
            target_id     TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            created_at    TEXT NOT NULL,
            debate_round  INTEGER DEFAULT 1,
            FOREIGN KEY (source_id) REFERENCES grove_ideas(id),
            FOREIGN KEY (target_id) REFERENCES grove_ideas(id)
        );
        CREATE TABLE IF NOT EXISTS grove_sessions (
            id          TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL,
            title       TEXT,
            created_at  TEXT NOT NULL,
            sealed_at   TEXT,
            receipt_id  TEXT,
            node_count  INTEGER DEFAULT 0,
            agents_used TEXT DEFAULT '[]'
        );
    """)
    conn.commit()
    conn.close()

# Initialize DB on import
init_grove_db()

# ── Helpers ───────────────────────────────────────────────────────────────────
def suggest_agents(text: str) -> list:
    """Identifica agentes relevantes por keywords no texto."""
    text_lower = text.lower()
    suggested = []
    for agent_id, cfg in AGENT_REGISTRY.items():
        if any(t in text_lower for t in cfg["topics"]):
            suggested.append(agent_id)
    return suggested[:3]  # Máximo 3 por rodada

def create_node(session_id, title, content, node_type="idea", author="user", agent_source=None):
    node_id = f"NODE-{uuid.uuid4().hex[:8].upper()}"
    conn = sqlite3.connect(GROVE_DB)
    conn.execute(
        "INSERT INTO grove_ideas VALUES (?,?,?,?,?,?,?,?,?)",
        (node_id, node_type, title, content,
         datetime.utcnow().isoformat(), author, agent_source, None, session_id)
    )
    conn.execute(
        "UPDATE grove_sessions SET node_count = node_count + 1 WHERE id = ?",
        (session_id,)
    )
    conn.commit()
    conn.close()
    return node_id

def create_edge(source_id, target_id, relation_type, round_num=1):
    edge_id = f"EDGE-{uuid.uuid4().hex[:8].upper()}"
    conn = sqlite3.connect(GROVE_DB)
    conn.execute(
        "INSERT INTO grove_edges VALUES (?,?,?,?,?,?)",
        (edge_id, source_id, target_id, relation_type,
         datetime.utcnow().isoformat(), round_num)
    )
    conn.commit()
    conn.close()
    return edge_id

# ── Endpoints ─────────────────────────────────────────────────────────────────

@grove_bp.route("/health", methods=["GET"])
def grove_health():
    """Health check for W-GROVE-001."""
    return jsonify({
        "status": "alive",
        "agent": "W-GROVE-001",
        "version": "1.0.0",
        "principle": "AI processes. Human decides. WINDI guarantees."
    })

@grove_bp.route("/seed", methods=["POST"])
def seed_idea():
    """
    Planta a semente: recebe ideia bruta, cria sessão + nó inicial,
    sugere agentes. NÃO activa agentes ainda — humano confirma primeiro.
    """
    data = request.get_json() or {}
    idea = data.get("idea", "")
    title = data.get("title", "") or idea[:60]
    context = data.get("context")
    user = data.get("user", "anonymous")

    if not idea:
        return jsonify({"error": "idea is required"}), 400

    session_id = f"GS-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    # Cria sessão
    conn = sqlite3.connect(GROVE_DB)
    conn.execute(
        "INSERT INTO grove_sessions VALUES (?,?,?,?,?,?,?,?)",
        (session_id, user, title[:80], datetime.utcnow().isoformat(),
         None, None, 0, '[]')
    )
    conn.commit()
    conn.close()

    # Cria nó raiz
    root_id = create_node(session_id, idea[:80], idea, "idea", user)

    # Sugestão de agentes (sem activar)
    suggested = suggest_agents(idea)

    return jsonify({
        "status": "seeded",
        "session_id": session_id,
        "root_node_id": root_id,
        "suggested_agents": suggested,
        "message": "Ideia plantada. Confirme os agentes a activar.",
        "principle": "Humano confirma. WINDI processa. Grove regista."
    })

@grove_bp.route("/debate", methods=["POST"])
def debate_idea():
    """
    Rodada de debate: activa agentes confirmados pelo humano,
    cria nós derivados + arestas semânticas.
    """
    data = request.get_json() or {}
    idea_id = data.get("idea_id", "")
    user_response = data.get("user_response", "")
    confirm_agents = data.get("confirm_agents", [])

    if not idea_id:
        return jsonify({"error": "idea_id is required"}), 400

    # VALIDATE: idea_id must exist in database BEFORE processing
    conn = sqlite3.connect(GROVE_DB)
    row = conn.execute(
        "SELECT id, session_id FROM grove_ideas WHERE id = ?", (idea_id,)
    ).fetchone()
    conn.close()

    if not row:
        return jsonify({
            "error": "idea_id not found",
            "idea_id": idea_id,
            "hint": "Use the root_node_id from /grove/seed response"
        }), 404

    session_id = row[1]  # Pre-fetched, used for all nodes

    new_nodes = []
    new_edges = []
    agents_used = []

    for agent_id in confirm_agents:
        if agent_id not in AGENT_REGISTRY:
            continue

        # Chama agente interno
        cfg = AGENT_REGISTRY[agent_id]
        try:
            resp = requests.post(
                f"{SANDBOX}{cfg['endpoint']}",
                json={"query": user_response, "context": "grove_debate"},
                timeout=10
            )
            insight = resp.json().get("result", f"[{agent_id} sem resposta]")
        except Exception:
            insight = f"[{agent_id} offline — insight pendente]"

        # Cria nó do agente (session_id já validado)
        nid = create_node(
            session_id, f"Perspetiva: {agent_id}",
            str(insight), "hypothesis", agent_id, agent_id
        )
        # Cria aresta semântica
        eid = create_edge(idea_id, nid, "supports")
        new_nodes.append(nid)
        new_edges.append(eid)
        agents_used.append(agent_id)

    # Regista agentes usados na sessão (session_id já validado no início)
    if agents_used:
        conn = sqlite3.connect(GROVE_DB)
        conn.execute(
            "UPDATE grove_sessions SET agents_used = ? WHERE id = ?",
            (json.dumps(agents_used), session_id)
        )
        conn.commit()
        conn.close()

    return jsonify({
        "status": "debated",
        "new_nodes": new_nodes,
        "new_edges": new_edges,
        "agents_consulted": agents_used,
        "next": "Revise os nós criados e sintetize ou continue o debate."
    })

@grove_bp.route("/ideas", methods=["GET"])
def list_sessions():
    """Lista todas as sessões do Grove."""
    conn = sqlite3.connect(GROVE_DB)
    sessions = conn.execute(
        "SELECT id, user_id, title, created_at, sealed_at, node_count FROM grove_sessions ORDER BY created_at DESC LIMIT 50"
    ).fetchall()
    conn.close()

    return jsonify({
        "sessions": [
            {
                "id": s[0],
                "user": s[1],
                "title": s[2],
                "created_at": s[3],
                "sealed": s[4] is not None,
                "node_count": s[5]
            }
            for s in sessions
        ]
    })

@grove_bp.route("/ideas/<session_id>", methods=["GET"])
def get_session(session_id):
    """Retorna detalhes de uma sessão."""
    conn = sqlite3.connect(GROVE_DB)
    session = conn.execute(
        "SELECT * FROM grove_sessions WHERE id = ?", (session_id,)
    ).fetchone()
    conn.close()

    if not session:
        return jsonify({"error": "Sessão não encontrada"}), 404

    return jsonify({
        "id": session[0],
        "user": session[1],
        "title": session[2],
        "created_at": session[3],
        "sealed_at": session[4],
        "receipt_id": session[5],
        "node_count": session[6],
        "agents_used": json.loads(session[7] or '[]')
    })

@grove_bp.route("/ideas/<session_id>/graph", methods=["GET"])
def get_idea_graph(session_id):
    """Retorna a topologia completa da constelação de ideias."""
    conn = sqlite3.connect(GROVE_DB)
    nodes = conn.execute(
        "SELECT * FROM grove_ideas WHERE session_id = ?", (session_id,)
    ).fetchall()
    edges = conn.execute(
        """SELECT e.* FROM grove_edges e
           JOIN grove_ideas n ON e.source_id = n.id
           WHERE n.session_id = ?""", (session_id,)
    ).fetchall()
    session = conn.execute(
        "SELECT * FROM grove_sessions WHERE id = ?", (session_id,)
    ).fetchone()
    conn.close()

    cols_n = ["id","type","title","content","created_at","author","agent_source","ledger_receipt","session_id"]
    cols_e = ["id","source_id","target_id","relation_type","created_at","debate_round"]

    return jsonify({
        "session_id": session_id,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": [dict(zip(cols_n, n)) for n in nodes],
        "edges": [dict(zip(cols_e, e)) for e in edges],
        "sealed": session[4] is not None if session else False
    })

@grove_bp.route("/ideas/<session_id>/seal", methods=["POST"])
def seal_grove_session(session_id):
    """
    Sela a constelação no Ledger.
    Princípio: Humano aprova → WINDI sela → Hash imutável.
    """
    data = request.get_json() or {}
    user = data.get("user", "anonymous")

    conn = sqlite3.connect(GROVE_DB)
    session = conn.execute(
        "SELECT * FROM grove_sessions WHERE id = ?", (session_id,)
    ).fetchone()
    node_count = conn.execute(
        "SELECT COUNT(*) FROM grove_ideas WHERE session_id = ?", (session_id,)
    ).fetchone()[0]
    conn.close()

    if not session:
        return jsonify({"error": "Sessão não encontrada"}), 404

    receipt_id = f"WINDI-GROVE-{session_id}"

    ledger_payload = {
        "id":               receipt_id,
        "actor":            user,
        "app":              "grove",
        "doc_name":         f"Idea Graph — {session[2] or session_id}",
        "doc_type":         "doc",
        "governance_level": "MEDIUM",
        "metadata": json.dumps({
            "session_id":       session_id,
            "node_count":       node_count,
            "agents_consulted": json.loads(session[7] or '[]'),
            "grove_version":    "W-GROVE-001 v1.0.0"
        })
    }

    # Envia ao Ledger
    try:
        r = requests.post(f"{LEDGER_URL}/api/receipts", json=ledger_payload, timeout=10)
        ledger_resp = r.json()
    except Exception as e:
        ledger_resp = {"error": str(e)}

    # Actualiza sessão
    conn = sqlite3.connect(GROVE_DB)
    conn.execute(
        "UPDATE grove_sessions SET sealed_at=?, receipt_id=? WHERE id=?",
        (datetime.utcnow().isoformat(), receipt_id, session_id)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "status":     "sealed",
        "receipt_id": receipt_id,
        "ledger":     ledger_resp,
        "principle":  "AI processes. Human decides. WINDI guarantees."
    })
