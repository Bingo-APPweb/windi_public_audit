"""
W-GROVE-001 — Grove Orchestrator
Domain extension do constitutional-agent (:8091)
Version: 1.0.2

Iron Rule: Este arquivo é registado em blueprints/ e importado
pelo constitutional-agent/agent.py — NÃO cria porta própria.

Converted from FastAPI to Flask Blueprint for constitutional-agent integration.

v1.0.2: IA-Auto-Titling — Grove nunca deixa uma ideia sem nome
"""

from flask import Blueprint, request, jsonify
import sqlite3
import uuid
import json
import requests
import re
from datetime import datetime
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
GROVE_DB   = Path("/opt/windi/agents/constitutional-agent/grove.db")
LEDGER_URL = "http://127.0.0.1:8101"
SANDBOX    = "http://127.0.0.1:8091"
DRAGON_URL = "http://127.0.0.1:8108"

# ── IA-Auto-Titling ───────────────────────────────────────────────────────────
def generate_sophisticated_title(thought_text: str) -> str:
    """
    W-GROVE-001 v1.0.2: Gera título sofisticado quando o humano não fornece.
    Tenta primeiro via Dragon API, fallback para extração local.
    """
    if not thought_text or len(thought_text.strip()) < 5:
        return "Semente de Pensamento"

    text = thought_text.strip()

    # Tenta chamar Dragon para síntese sofisticada
    try:
        resp = requests.post(
            f"{DRAGON_URL}/api/dragon/chat",
            json={
                "message": f"Sintetiza este pensamento em um título de 3-6 palavras, sofisticado e denso. Responde APENAS com o título, sem aspas nem explicação:\n\n{text[:500]}",
                "tier": "ADMIN",
                "chatType": "grove_titling"
            },
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            ai_title = data.get("message", "").strip()
            # Limpa e valida
            ai_title = re.sub(r'^["\']|["\']$', '', ai_title)  # Remove aspas
            ai_title = ai_title.split('\n')[0].strip()  # Só primeira linha
            if 3 <= len(ai_title) <= 80 and not ai_title.lower().startswith(("aqui", "claro", "ok")):
                return ai_title
    except Exception:
        pass  # Fallback para extração local

    # Fallback: Extração inteligente local
    # Remove pontuação final e pega primeira frase/segmento
    first_sentence = re.split(r'[.!?\n]', text)[0].strip()

    # Se muito longo, pega primeiras palavras significativas
    words = first_sentence.split()
    if len(words) > 8:
        # Pega até 6 palavras, evitando cortar no meio
        title = ' '.join(words[:6])
        if not title.endswith(('de', 'da', 'do', 'e', 'ou', 'para', 'com', 'em', 'a', 'o')):
            return title + "..."
        title = ' '.join(words[:5])
        return title + "..."

    return first_sentence[:60] if len(first_sentence) <= 60 else first_sentence[:57] + "..."

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
        "version": "1.0.2",
        "features": ["auto-titling", "debate", "seal"],
        "principle": "AI processes. Human decides. WINDI guarantees."
    })

@grove_bp.route("/seed", methods=["POST"])
def seed_idea():
    """
    Planta a semente: recebe ideia bruta, cria sessão + nó inicial,
    sugere agentes. NÃO activa agentes ainda — humano confirma primeiro.

    v1.0.2: IA-Auto-Titling — se título vazio, Grove batiza a ideia.
    """
    data = request.get_json() or {}
    idea = data.get("idea", "")
    raw_title = data.get("title", "").strip()
    context = data.get("context")
    user = data.get("user", "anonymous")

    if not idea:
        return jsonify({"error": "idea is required"}), 400

    # IA-Auto-Titling: se título vazio ou genérico, Grove batiza
    auto_titled = False
    if not raw_title or raw_title.lower() in ["sem título", "ohne titel", "untitled", ""]:
        title = generate_sophisticated_title(idea)
        auto_titled = True
    else:
        title = raw_title

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

    # Cria nó raiz (usa title, não idea[:80])
    root_id = create_node(session_id, title, idea, "idea", user)

    # Sugestão de agentes (sem activar)
    suggested = suggest_agents(idea)

    return jsonify({
        "status": "seeded",
        "session_id": session_id,
        "root_node_id": root_id,
        "suggested_agents": suggested,
        "title": title,
        "auto_titled": auto_titled,  # True se Grove batizou a ideia
        "message": f"{'🌱 Grove batizou: ' if auto_titled else ''}Ideia plantada. Confirme os agentes.",
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


# ── ARENA: Motor de Debate Real ──────────────────────────────────────────────
AGENT_PERSONAS = {
    "W-LEGAL-001": {
        "name": "Justiça",
        "emoji": "⚖️",
        "role": "Legal Analyst",
        "prompt": "Tu és o agente jurídico WINDI. Analisa a questão do ponto de vista legal, citando princípios jurídicos relevantes. Sê preciso mas acessível. Máximo 3 parágrafos."
    },
    "W-NOTARY-001": {
        "name": "Notário",
        "emoji": "📜",
        "role": "Notary Agent",
        "prompt": "Tu és o agente notarial WINDI. Avalia autenticidade, certificação e fé pública. Foca em como garantir a integridade documental. Máximo 3 parágrafos."
    },
    "W-COMPLY-001": {
        "name": "Compliance",
        "emoji": "🛡️",
        "role": "Compliance Officer",
        "prompt": "Tu és o agente de compliance WINDI. Analisa riscos regulatórios, GDPR, conformidade. Identifica red flags e sugere mitigações. Máximo 3 parágrafos."
    },
    "W-COMM-001": {
        "name": "Communiqué",
        "emoji": "📰",
        "role": "Document Architect",
        "prompt": "Tu és o agente de documentos WINDI. Propõe estrutura, formato e tom ideal para comunicar esta ideia. Sugere tipo de documento adequado. Máximo 3 parágrafos."
    },
    "W-JOURN-001": {
        "name": "Jornalista",
        "emoji": "✒️",
        "role": "Editorial Agent",
        "prompt": "Tu és o agente editorial WINDI. Avalia o potencial narrativo, ângulo de publicação e impacto comunicacional. Sugere headlines. Máximo 3 parágrafos."
    },
    "W-AUDIT-001": {
        "name": "Auditor",
        "emoji": "🔍",
        "role": "Audit Agent",
        "prompt": "Tu és o agente de auditoria WINDI. Verifica integridade, rastreabilidade e evidências. Identifica gaps documentais. Máximo 3 parágrafos."
    },
    "W-ACCT-001": {
        "name": "Contabilidade",
        "emoji": "📊",
        "role": "Accounting Agent",
        "prompt": "Tu és o agente contabilístico WINDI. Analisa implicações fiscais, GoBD, ELSTER. Avalia se há necessidades de documentação financeira. Máximo 3 parágrafos."
    },
}

@grove_bp.route("/arena", methods=["POST"])
def arena_debate():
    """
    W-GROVE-001 Arena: Motor de debate real.
    Cada agente selecionado responde com sua perspectiva via Dragon.

    Input: {
        "topic": "A ideia a debater",
        "agents": ["W-LEGAL-001", "W-COMPLY-001"],
        "session_id": "GS-...",  # opcional
        "round": 1  # rodada do debate
    }

    Output: {
        "responses": [
            {"agent": "W-LEGAL-001", "name": "Justiça", "emoji": "⚖️", "message": "..."},
            ...
        ]
    }
    """
    data = request.get_json() or {}
    topic = data.get("topic", "")
    agents = data.get("agents", [])
    session_id = data.get("session_id")
    debate_round = data.get("round", 1)
    store_nodes = data.get("store_nodes", True)  # Gravar no grafo?

    if not topic:
        return jsonify({"error": "topic is required"}), 400

    if not agents:
        return jsonify({"error": "agents array is required"}), 400

    responses = []

    for agent_id in agents:
        if agent_id not in AGENT_PERSONAS:
            continue

        persona = AGENT_PERSONAS[agent_id]

        # Constrói prompt completo para Dragon (inline, sem system separado)
        full_prompt = f"""[GROVE ARENA — {persona['name']} {persona['emoji']}]

{persona['prompt']}

TÓPICO PARA ANÁLISE:
{topic}

Responde com a tua perspectiva profissional. Máximo 3 parágrafos, linguagem do tópico."""

        # Chama Dragon com chatType "general" (reconhecido)
        try:
            resp = requests.post(
                f"{DRAGON_URL}/api/dragon/chat",
                json={
                    "message": full_prompt,
                    "tier": "GOVERNANCE",
                    "chatType": "general",
                    "maxTokens": 600
                },
                timeout=30
            )

            if resp.status_code == 200:
                dragon_data = resp.json()
                agent_response = dragon_data.get("message", f"[{agent_id} sem resposta]")
            else:
                agent_response = f"[{agent_id} — Dragon retornou {resp.status_code}]"

        except requests.Timeout:
            agent_response = f"[{agent_id} — timeout na análise]"
        except Exception as e:
            agent_response = f"[{agent_id} — erro: {str(e)[:50]}]"

        responses.append({
            "agent": agent_id,
            "name": persona["name"],
            "emoji": persona["emoji"],
            "role": persona["role"],
            "message": agent_response,
            "round": debate_round,
            "ts": datetime.utcnow().isoformat()
        })

        # Grava como nó no grafo (se session_id fornecido)
        if store_nodes and session_id:
            try:
                nid = create_node(
                    session_id,
                    f"{persona['emoji']} {persona['name']} — Rodada {debate_round}",
                    agent_response,
                    "hypothesis",
                    agent_id,
                    agent_id
                )
                responses[-1]["node_id"] = nid
            except Exception:
                pass  # Não falha se gravar der erro

    return jsonify({
        "status": "arena_complete",
        "round": debate_round,
        "topic": topic[:100],
        "responses": responses,
        "agents_responded": len(responses),
        "principle": "AI processes. Human decides. WINDI guarantees."
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
