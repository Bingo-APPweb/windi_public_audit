"""
W-GROVE-001 — Grove Orchestrator
Domain extension do constitutional-agent (:8091)
Version: 1.2.0

Iron Rule: Este arquivo é registado em blueprints/ e importado
pelo constitutional-agent/agent.py — NÃO cria porta própria.

Converted from FastAPI to Flask Blueprint for constitutional-agent integration.

v1.2.0: Parecer de Consultoria — PDF + HTML verification page
v1.1.0: Honorarium Engine — Micro-consultancy pricing integration
v1.0.3: Arena Bypass — chatType "arena" bypassa Dragon Hub para texto puro
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

# ── Honorarium Engine Import ─────────────────────────────────────────────────
from blueprints.grove_honorarium_model import HonorariumEngine, register_flask_routes

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
    "W-ARCH-001":   {"topics": ["arquitectura","sistema","design","técnico","infraestrutura","stack"], "endpoint": "/architect/design"},
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
        "version": "1.2.0",
        "features": ["auto-titling", "debate", "seal", "arena-bypass", "honorarium", "parecer", "verify"],
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
# v2.0: Tension Vectors — cada agente tem prioridades que podem conflituar
AGENT_PERSONAS = {
    "W-LEGAL-001": {
        "name": "Justiça",
        "emoji": "⚖️",
        "role": "Legal Analyst",
        "prompt": """Tu és o agente jurídico WINDI.

PRIORIDADE: Minimizar risco de litígio, garantir precedente sólido, proteger posição legal.
PODES SACRIFICAR: Eficiência operacional, velocidade de decisão, conveniência.

TENSÃO: Se outros sugerirem soluções rápidas que criem vulnerabilidade jurídica, DISCORDA.
Se a questão envolver trade-off entre compliance e segurança legal, prioriza segurança legal.

OBRIGATÓRIO: Identifica pelo menos UM risco jurídico que outros agentes podem subestimar.

Analisa citando princípios jurídicos. Máximo 3 parágrafos."""
    },
    "W-NOTARY-001": {
        "name": "Notário",
        "emoji": "📜",
        "role": "Notary Agent",
        "prompt": """Tu és o agente notarial WINDI.

PRIORIDADE: Fé pública, autenticidade absoluta, cadeia de custódia inviolável.
PODES SACRIFICAR: Flexibilidade, reversibilidade, conveniência do utilizador.

TENSÃO: Se outros sugerirem alterações a documentos selados, DISCORDA firmemente.
A imutabilidade é sagrada — propõe sempre versionamento, nunca modificação.

OBRIGATÓRIO: Identifica pelo menos UMA falha de autenticidade que outros podem ignorar.

Foca em integridade documental. Máximo 3 parágrafos."""
    },
    "W-COMPLY-001": {
        "name": "Compliance",
        "emoji": "🛡️",
        "role": "Compliance Officer",
        "prompt": """Tu és o agente de compliance WINDI.

PRIORIDADE: Relação com reguladores, risco sistémico, reputação institucional.
PODES SACRIFICAR: Purismo legal, perfeição técnica, velocidade de implementação.

TENSÃO: Se o jurídico for demasiado rígido e isso prejudicar relação com regulador, DISCORDA.
Às vezes cooperar com autoridades vale mais que ter razão legal.

OBRIGATÓRIO: Identifica pelo menos UM cenário onde a posição "correcta" pode causar dano reputacional.

Analisa riscos regulatórios e GDPR. Máximo 3 parágrafos."""
    },
    "W-COMM-001": {
        "name": "Communiqué",
        "emoji": "📰",
        "role": "Document Architect",
        "prompt": """Tu és o agente de documentos WINDI.

PRIORIDADE: Clareza de comunicação, impacto narrativo, acessibilidade.
PODES SACRIFICAR: Precisão técnica excessiva, jargão especializado.

TENSÃO: Se outros usarem linguagem demasiado técnica ou legal, sugere simplificação.
O documento deve ser compreendido pelo público-alvo, não apenas por especialistas.

OBRIGATÓRIO: Identifica pelo menos UM problema de comunicação na abordagem proposta.

Propõe estrutura e tom. Máximo 3 parágrafos."""
    },
    "W-JOURN-001": {
        "name": "Jornalista",
        "emoji": "✒️",
        "role": "Editorial Agent",
        "prompt": """Tu és o agente editorial WINDI.

PRIORIDADE: Interesse público, transparência, impacto mediático.
PODES SACRIFICAR: Confidencialidade excessiva, cautela institucional.

TENSÃO: Se outros quiserem esconder informação que o público deveria saber, DISCORDA.
A transparência constrói confiança — o sigilo excessivo destrói.

OBRIGATÓRIO: Identifica pelo menos UM ângulo que a imprensa poderia explorar negativamente.

Avalia potencial narrativo. Máximo 3 parágrafos."""
    },
    "W-AUDIT-001": {
        "name": "Auditor",
        "emoji": "🔍",
        "role": "Audit Agent",
        "prompt": """Tu és o agente de auditoria WINDI.

PRIORIDADE: Evidência documental, rastreabilidade, gaps de processo.
PODES SACRIFICAR: Velocidade de resolução, conveniência operacional.

TENSÃO: Se outros propuserem soluções sem documentação adequada, DISCORDA.
Sem evidência, não há prova. Sem prova, não há defesa.

OBRIGATÓRIO: Identifica pelo menos UM gap documental ou de processo que ninguém mencionou.

Verifica integridade e evidências. Máximo 3 parágrafos."""
    },
    "W-ACCT-001": {
        "name": "Contabilidade",
        "emoji": "📊",
        "role": "Accounting Agent",
        "prompt": """Tu és o agente contabilístico WINDI.

PRIORIDADE: Conformidade fiscal, GoBD, ELSTER, trilha financeira auditável.
PODES SACRIFICAR: Simplicidade operacional, preferências do utilizador.

TENSÃO: Se outros ignorarem implicações fiscais ou documentação financeira, ALERTA.
Fisco não perdoa — documentação incompleta é risco real.

OBRIGATÓRIO: Identifica pelo menos UMA implicação fiscal que outros podem ter ignorado.

Analisa perspectiva contabilística. Máximo 3 parágrafos."""
    },
    "W-ARCH-001": {
        "name": "Architect",
        "emoji": "🏗️",
        "role": "Systems Architect",
        "prompt": """Tu és o agente arquitecto WINDI.

PRIORIDADE: Escalabilidade, manutenibilidade, debt técnico, performance.
PODES SACRIFICAR: Entrega imediata, funcionalidades não essenciais.

TENSÃO: Se outros propuserem soluções rápidas que criem debt técnico, DISCORDA.
Código que funciona hoje mas não escala amanhã é um problema adiado.

OBRIGATÓRIO: Identifica pelo menos UM trade-off técnico que outros podem subestimar.

Propõe arquitectura. Máximo 3 parágrafos."""
    },
}

@grove_bp.route("/arena", methods=["POST"])
def arena_debate():
    """
    W-GROVE-001 Arena: Motor de debate real com contexto do Bibliotecário.
    Cada agente selecionado responde com sua perspectiva via Dragon,
    INFORMADO pelo conhecimento constitucional do W-LIB-001.

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
    context = data.get("context", "")
    agents = data.get("agents", [])
    session_id = data.get("session_id")
    debate_round = data.get("round", 1)
    store_nodes = data.get("store_nodes", True)  # Gravar no grafo?

    if not topic:
        return jsonify({"error": "topic is required"}), 400

    if not agents:
        return jsonify({"error": "agents array is required"}), 400

    # ══════════════════════════════════════════════════════════════════════════
    # BIBLIOTECÁRIO INJECTION — Constitutional context before debate
    # ══════════════════════════════════════════════════════════════════════════
    bibliotecario_context = ""
    try:
        lib_resp = requests.get(
            f"{SANDBOX}/library/grove-brief",
            params={"topic": topic, "participants": ",".join(agents), "lang": "pt"},
            timeout=5
        )
        if lib_resp.status_code == 200:
            briefing = lib_resp.json()
            # Extract key governance anchors
            anchor = briefing.get("governance_anchor", {})
            invariants = briefing.get("binding_invariants", [])
            rules = briefing.get("debate_rules", {})
            infra = briefing.get("infrastructure_exists", {})
            services = infra.get("services", {})
            crypto = infra.get("cryptography", {})

            # Build infrastructure awareness section
            infra_lines = []
            if infra.get("warning"):
                infra_lines.append(f"⚠️ {infra['warning']}")
            for svc_key, svc_data in services.items():
                if isinstance(svc_data, dict) and svc_data.get("dont_propose"):
                    infra_lines.append(f"  • {svc_key.upper()}: {svc_data.get('dont_propose', '')}")
            if crypto.get("status"):
                infra_lines.append(f"  • CRIPTOGRAFIA: {crypto['status']}")
            infra_section = chr(10).join(infra_lines) if infra_lines else ""

            # GAP 1: Communication Channels
            comm_channels = briefing.get("communication_channels", {})
            comm_section = ""
            if comm_channels.get("endpoints"):
                comm_lines = ["CANAIS DE COMUNICAÇÃO DISPONÍVEIS:"]
                for ch_key, ch_data in comm_channels.get("endpoints", {}).items():
                    if isinstance(ch_data, dict):
                        comm_lines.append(f"  • {ch_key.upper()}: {ch_data.get('endpoint','')} — {ch_data.get('purpose','')}")
                        comm_lines.append(f"    Executor: {ch_data.get('executor','')}")
                comm_section = chr(10).join(comm_lines)

            # GAP 2: Crisis Governance Defaults
            crisis_gov = briefing.get("crisis_governance_defaults", {})
            crisis_section = ""
            if crisis_gov.get("states"):
                crisis_lines = ["ESTADOS DE CRISE (valores padrão):"]
                for state_key, state_data in crisis_gov.get("states", {}).items():
                    if isinstance(state_data, dict):
                        ttl = state_data.get('ttl_hours', 'N/A')
                        crisis_lines.append(f"  • {state_key}: TTL={ttl}h → {state_data.get('on_expiry','')}")
                if crisis_gov.get("principle"):
                    crisis_lines.append(f"  PRINCÍPIO: {crisis_gov['principle']}")
                crisis_section = chr(10).join(crisis_lines)

            # GAP 3: Dragon Unavailability Protocol
            dragon_unavail = briefing.get("dragon_unavailability_protocol", {})
            unavail_section = ""
            if dragon_unavail.get("constitutional_response"):
                resp = dragon_unavail["constitutional_response"]
                unavail_section = f"""PROTOCOLO DRAGON INDISPONÍVEL:
  • Imediato: {resp.get('immediate', 'Manter último estado')}
  • Documentação: {resp.get('documentation', 'Registar no Ledger')}
  • Failsafe: {dragon_unavail.get('failsafe_invariant', 'NUNCA decide sozinho')}"""

            bibliotecario_context = f"""
═══ CONTEXTO CONSTITUCIONAL (W-LIB-001 Bibliotecário) ═══
PRINCÍPIO FUNDADOR: {anchor.get('principle', 'IA processa. Humano decide. WINDI garante.')}
TRÊS DRAGÕES: {anchor.get('three_dragons', '')}

INVARIANTES VINCULATIVAS:
{chr(10).join([f"• {inv.get('code', '')} [{inv.get('name', '')}]: {inv.get('description', '')}" for inv in invariants])}

REGRAS DO DEBATE:
• {rules.get('rule_1', 'Responder na língua do tópico')}
• {rules.get('rule_2', 'Fundamentar com princípios constitucionais')}
• {rules.get('rule_3', 'Propor, nunca impor')}

{f"INFRAESTRUTURA JÁ OPERACIONAL (NÃO PROPONHA CRIAR):{chr(10)}{infra_section}" if infra_section else ""}

{comm_section}

{crisis_section}

{unavail_section}
═══════════════════════════════════════════════════════════
"""
    except Exception as e:
        print(f"[Arena] Bibliotecário unavailable: {e}")
        # Fallback minimal context
        bibliotecario_context = """
═══ CONTEXTO WINDI (Fallback) ═══
PRINCÍPIO: IA processa. Humano decide. WINDI garante.
INVARIANTE I9: Proibição de Autonomia — Agentes propõem, humanos decidem.
INVARIANTE I1: Soberania do Humano — Veto absoluto sobre qualquer decisão.
═════════════════════════════════
"""

    responses = []

    for agent_id in agents:
        if agent_id not in AGENT_PERSONAS:
            continue

        persona = AGENT_PERSONAS[agent_id]

        # Constrói prompt completo para Dragon COM contexto do Bibliotecário
        full_prompt = f"""[GROVE ARENA — {persona['name']} {persona['emoji']}]

{bibliotecario_context}

⚠️ REGRA OBRIGATÓRIA: A infraestrutura listada acima JÁ EXISTE e está operacional. Se o tópico pede algo que já existe (ex: logs → FORENSIC_LEDGER), a tua primeira frase DEVE ser: "O sistema WINDI já dispõe de [X] operacional." Depois propõe melhorias, nunca criação do zero.

{persona['prompt']}

TÓPICO: {topic}
{f"CONTEXTO: {context}" if context else ""}

Máximo 3 parágrafos, linguagem do tópico."""

        # Chama Dragon com chatType "arena" — bypassa Hub para texto puro
        try:
            resp = requests.post(
                f"{DRAGON_URL}/api/dragon/chat",
                json={
                    "message": full_prompt,
                    "tier": "GOVERNANCE",
                    "chatType": "arena",
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


# ═══════════════════════════════════════════════════════════════════════════════
# HONORARIUM ENGINE — Micro-Consultoria Pricing (v1.1.0)
# ═══════════════════════════════════════════════════════════════════════════════
#
# Sovereign Flow: H = Sigma [fase x agente x contexto] x identidade
#
# Endpoints registados automaticamente via register_flask_routes():
#   GET  /grove/arena/pricing  — Tabela de precos publica
#   POST /grove/arena/estimate — Oraculo de custo pre-debate
#   POST /grove/arena/consume  — Debito Wallet + Receipt Ledger
#
# ═══════════════════════════════════════════════════════════════════════════════

_honorarium_engine = HonorariumEngine()
register_flask_routes(grove_bp, _honorarium_engine)


# ═══════════════════════════════════════════════════════════════════════════════
# PARECER DE CONSULTORIA — Document Generation (v1.2.0)
# ═══════════════════════════════════════════════════════════════════════════════
#
# Gera documento formal após debate:
#   POST /grove/arena/report   — Gera PDF + HTML verificável
#   GET  /grove/verify/<id>    — Página de verificação pública
#
# ═══════════════════════════════════════════════════════════════════════════════

import hashlib
import base64
from datetime import timezone

# Directório para relatórios gerados
REPORTS_DIR = Path("/opt/windi/agents/constitutional-agent/data/reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# URL base para verificação
VERIFY_BASE_URL = "https://windi-domain.com/grove/verify"


def _generate_report_html(report_data: dict) -> str:
    """Gera HTML do Parecer de Consultoria."""
    agents_html = ""
    for agent in report_data.get("agents", []):
        # Handle both dict and string agents
        if isinstance(agent, str):
            agent = {"agent_id": agent, "name": agent, "emoji": "🤖", "tier": "agent", "message": ""}
        agents_html += f"""
        <div class="agent-card">
            <div class="agent-header">
                <span class="agent-icon">{agent.get('emoji', '🤖')}</span>
                <span class="agent-name">{agent.get('name', 'Agent')}</span>
                <span class="agent-tier">[{agent.get('tier', 'agent').upper()}]</span>
            </div>
            <div class="agent-content">{agent.get('message', '').replace(chr(10), '<br>')}</div>
        </div>
        """

    # Breakdown de honorários
    breakdown_html = ""
    for item in report_data.get("honorarium", {}).get("breakdown", []):
        breakdown_html += f"""
        <tr>
            <td>{item.get('icon','')} {item.get('name','')}</td>
            <td>{item.get('tier','')}</td>
            <td>{item.get('credits_raw', 0)}</td>
            <td>{item.get('credits_final', 0)}</td>
            <td>€{item.get('eur_value', 0):.4f}</td>
        </tr>
        """

    hon = report_data.get("honorarium", {})
    identity_badge = {
        "pioneer": "🌱 Pioneer (50% desconto perpétuo)",
        "did": "🪪 DID Validado (20% desconto)",
        "free": "👤 Free Tier",
        "empresa": "🏢 Empresa (+20%, NF dedutível)"
    }.get(hon.get("identity", "free"), "👤 Free Tier")

    return f"""<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Parecer WINDI Grove Arena — {report_data.get('receipt_id', 'N/A')}</title>
    <style>
        :root {{
            --gold: #C9A227;
            --dark: #1a1a1a;
            --bg: #0d0d0d;
            --border: #333;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: var(--bg);
            color: #e0e0e0;
            line-height: 1.6;
            padding: 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: var(--dark);
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            padding: 30px;
            border-bottom: 3px solid var(--gold);
            text-align: center;
        }}
        .header h1 {{
            color: var(--gold);
            font-size: 24px;
            margin-bottom: 8px;
        }}
        .header .subtitle {{
            color: #888;
            font-size: 12px;
        }}
        .receipt-id {{
            background: var(--gold);
            color: #000;
            padding: 4px 12px;
            border-radius: 4px;
            font-family: monospace;
            font-weight: bold;
            display: inline-block;
            margin-top: 12px;
        }}
        .section {{
            padding: 24px 30px;
            border-bottom: 1px solid var(--border);
        }}
        .section-title {{
            color: var(--gold);
            font-size: 14px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 16px;
        }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }}
        .meta-item {{
            background: #222;
            padding: 12px;
            border-radius: 6px;
        }}
        .meta-label {{
            font-size: 10px;
            color: #666;
            text-transform: uppercase;
        }}
        .meta-value {{
            font-size: 14px;
            color: #fff;
            margin-top: 4px;
        }}
        .topic-box {{
            background: linear-gradient(135deg, #1a1a0a 0%, #2a2a1a 100%);
            border: 1px solid var(--gold);
            border-radius: 8px;
            padding: 20px;
            font-size: 16px;
            font-style: italic;
        }}
        .agent-card {{
            background: #222;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
            border-left: 3px solid var(--gold);
        }}
        .agent-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 12px;
        }}
        .agent-icon {{ font-size: 20px; }}
        .agent-name {{ font-weight: 700; color: var(--gold); }}
        .agent-tier {{ font-size: 10px; color: #666; }}
        .agent-content {{
            font-size: 13px;
            line-height: 1.7;
            color: #ccc;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        th {{
            background: #222;
            color: var(--gold);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 10px;
        }}
        .total-row {{
            background: linear-gradient(135deg, #1a1a0a 0%, #2a2a1a 100%);
            font-weight: bold;
        }}
        .total-row td {{
            color: var(--gold);
            font-size: 14px;
        }}
        .identity-badge {{
            display: inline-block;
            background: #2a2a1a;
            border: 1px solid var(--gold);
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            margin-top: 12px;
        }}
        .verify-section {{
            text-align: center;
            padding: 30px;
            background: #111;
        }}
        .hash-box {{
            background: #000;
            border: 1px solid var(--border);
            padding: 12px 20px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 11px;
            word-break: break-all;
            margin: 16px 0;
        }}
        .qr-placeholder {{
            width: 120px;
            height: 120px;
            background: #fff;
            margin: 16px auto;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #000;
            font-size: 10px;
        }}
        .verify-url {{
            color: var(--gold);
            font-size: 12px;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            font-size: 10px;
            color: #666;
        }}
        .ledger-status {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #1a2a1a;
            border: 1px solid #2d5a27;
            padding: 8px 16px;
            border-radius: 6px;
            color: #4a8c3f;
            font-weight: 600;
        }}
        @media print {{
            body {{ background: #fff; color: #000; }}
            .container {{ border: 1px solid #ccc; }}
            .header {{ background: #f5f5f5; }}
            .section {{ border-color: #ddd; }}
            .agent-card, .meta-item {{ background: #f9f9f9; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌳 WINDI Grove Arena</h1>
            <div class="subtitle">Parecer de Micro-Consultoria</div>
            <div class="receipt-id">{report_data.get('receipt_id', 'N/A')}</div>
        </div>

        <div class="section">
            <div class="section-title">Metadados</div>
            <div class="meta-grid">
                <div class="meta-item">
                    <div class="meta-label">Sessão</div>
                    <div class="meta-value">{report_data.get('session_id', 'N/A')}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Data/Hora UTC</div>
                    <div class="meta-value">{report_data.get('timestamp', 'N/A')}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Solicitante</div>
                    <div class="meta-value">{report_data.get('wallet_id', 'anonymous')}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Rodadas</div>
                    <div class="meta-value">{report_data.get('rounds', 1)}</div>
                </div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">Tópico Consultado</div>
            <div class="topic-box">"{report_data.get('topic', 'N/A')}"</div>
        </div>

        <div class="section">
            <div class="section-title">Perspectivas dos Agentes ({len(report_data.get('agents', []))})</div>
            {agents_html}
        </div>

        <div class="section">
            <div class="section-title">Honorários</div>
            <table>
                <thead>
                    <tr>
                        <th>Agente</th>
                        <th>Tier</th>
                        <th>Créditos Brutos</th>
                        <th>Créditos Líquidos</th>
                        <th>EUR</th>
                    </tr>
                </thead>
                <tbody>
                    {breakdown_html}
                    <tr class="total-row">
                        <td colspan="3">TOTAL</td>
                        <td>{hon.get('total_credits', 0)}</td>
                        <td>€{hon.get('total_eur', 0):.2f}</td>
                    </tr>
                </tbody>
            </table>
            <div class="identity-badge">{identity_badge}</div>
        </div>

        <div class="verify-section">
            <div class="section-title">Verificação Forense</div>
            <div class="ledger-status">
                ✓ Registado no Forensic Ledger
            </div>
            <div class="hash-box">
                SHA-256: {report_data.get('hash_sha256', 'N/A')}
            </div>
            <div class="qr-placeholder">[QR Code]</div>
            <div class="verify-url">{VERIFY_BASE_URL}/{report_data.get('receipt_id', '')}</div>
        </div>

        <div class="footer">
            <p>"AI processes. Human decides. WINDI guarantees."</p>
            <p>WINDI Grove Arena v1.2.0 — Kempten, Bavaria — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}</p>
        </div>
    </div>
</body>
</html>"""


@grove_bp.route("/arena/report", methods=["POST"])
def generate_arena_report():
    """
    POST /grove/arena/report — Gera Parecer de Consultoria.

    Payload:
        {
            "session_id": "GS-...",
            "topic": "O tópico debatido",
            "agents": [
                {"agent_id": "W-LEGAL-001", "name": "Legal", "emoji": "⚖️", "tier": "elite", "message": "..."},
                ...
            ],
            "rounds": 1,
            "wallet_id": "WALLET-...",
            "identity": "pioneer",
            "honorarium": { ... }  // opcional - será calculado se não fornecido
        }

    Returns:
        {
            "ok": true,
            "receipt_id": "GRV-...",
            "report_url": "https://.../grove/verify/GRV-...",
            "pdf_url": "https://.../grove/report/GRV-....pdf",
            "html": "..." // HTML completo do relatório
        }
    """
    data = request.get_json() or {}

    session_id = data.get("session_id", f"GS-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}")
    topic = data.get("topic", "")
    agents = data.get("agents", [])
    rounds = data.get("rounds", 1)
    wallet_id = data.get("wallet_id", "anonymous")
    identity = data.get("identity", "free")

    if not topic or not agents:
        return jsonify({"ok": False, "error": "topic and agents are required"}), 400

    # Gerar receipt_id único
    receipt_id = f"GRV-{uuid.uuid4().hex[:14].upper()}"
    timestamp = datetime.now(timezone.utc).isoformat()

    # Calcular honorários se não fornecidos
    honorarium = data.get("honorarium")
    if not honorarium:
        try:
            from blueprints.grove_honorarium_model import FlowPhase, IdentityMultiplier
            # Handle both dict and string agents
            agent_ids_for_honorarium = [a.get("agent_id", a) if isinstance(a, dict) else a for a in agents]
            estimate = _honorarium_engine.estimate(
                session_id=session_id,
                wallet_id=wallet_id,
                agents=agent_ids_for_honorarium,
                phase=FlowPhase.ARENA,
                identity=IdentityMultiplier(identity),
                rounds=rounds
            )
            honorarium = {
                "total_credits": estimate.total_credits,
                "total_eur": estimate.total_eur,
                "identity": estimate.identity.value,
                "breakdown": [
                    {
                        "icon": item.icon,
                        "name": item.agent_name,
                        "tier": item.agent_tier.value,
                        "credits_raw": item.credits_raw,
                        "credits_final": item.credits_final,
                        "eur_value": item.eur_value
                    }
                    for item in estimate.line_items
                ]
            }
        except Exception as e:
            honorarium = {"total_credits": 0, "total_eur": 0, "identity": identity, "breakdown": [], "error": str(e)}

    # Preparar dados do relatório
    report_data = {
        "receipt_id": receipt_id,
        "session_id": session_id,
        "timestamp": timestamp,
        "topic": topic,
        "agents": agents,
        "rounds": rounds,
        "wallet_id": wallet_id,
        "honorarium": honorarium,
        "hash_sha256": ""
    }

    # Calcular hash SHA-256 do relatório
    # Handle both dict and string agents
    agent_ids = [a.get("agent_id", a) if isinstance(a, dict) else a for a in agents]
    hash_payload = json.dumps({
        "receipt_id": receipt_id,
        "session_id": session_id,
        "topic": topic,
        "agents": agent_ids,
        "timestamp": timestamp,
        "honorarium": honorarium.get("total_credits", 0) if isinstance(honorarium, dict) else 0
    }, sort_keys=True)
    report_data["hash_sha256"] = hashlib.sha256(hash_payload.encode()).hexdigest()

    # Gerar HTML
    html_content = _generate_report_html(report_data)

    # Guardar HTML no filesystem
    html_path = REPORTS_DIR / f"{receipt_id}.html"
    html_path.write_text(html_content, encoding="utf-8")

    # Guardar JSON para referência
    json_path = REPORTS_DIR / f"{receipt_id}.json"
    json_path.write_text(json.dumps(report_data, indent=2, default=str), encoding="utf-8")

    # Tentar registar no Forensic Ledger
    ledger_ok = False
    try:
        ledger_payload = {
            "id": receipt_id,
            "actor": wallet_id,
            "app": "grove-arena-report",
            "doc_name": f"Parecer Grove — {topic[:50]}",
            "doc_type": "parecer",
            "governance_level": "HIGH",
            "metadata": json.dumps({
                "session_id": session_id,
                "topic": topic[:200],
                "agents": agent_ids,
                "credits": honorarium.get("total_credits", 0) if isinstance(honorarium, dict) else 0,
                "hash_sha256": report_data["hash_sha256"]
            })
        }
        resp = requests.post(f"{LEDGER_URL}/api/receipts", json=ledger_payload, timeout=10)
        ledger_ok = resp.status_code == 200
    except Exception:
        pass

    # Tentar gerar PDF via Export Engine
    pdf_url = None
    try:
        export_resp = requests.post(
            "http://127.0.0.1:8103/api/export/html-to-pdf",
            json={
                "html": html_content,
                "filename": f"{receipt_id}.pdf",
                "options": {"format": "A4", "margin": "20mm"}
            },
            timeout=30
        )
        if export_resp.status_code == 200:
            pdf_data = export_resp.json()
            pdf_url = pdf_data.get("url") or f"/grove/report/{receipt_id}.pdf"
    except Exception:
        pass

    return jsonify({
        "ok": True,
        "receipt_id": receipt_id,
        "session_id": session_id,
        "report_url": f"{VERIFY_BASE_URL}/{receipt_id}",
        "pdf_url": pdf_url,
        "html_path": str(html_path),
        "ledger_registered": ledger_ok,
        "hash_sha256": report_data["hash_sha256"],
        "honorarium": honorarium,
        "message": f"Parecer gerado: {receipt_id}"
    })


@grove_bp.route("/verify/<receipt_id>", methods=["GET"])
def verify_report(receipt_id):
    """
    GET /grove/verify/<receipt_id> — Página de verificação pública.

    Retorna o HTML do parecer para verificação.
    """
    # Sanitizar receipt_id
    receipt_id = re.sub(r'[^A-Za-z0-9\-]', '', receipt_id)

    html_path = REPORTS_DIR / f"{receipt_id}.html"
    json_path = REPORTS_DIR / f"{receipt_id}.json"

    if not html_path.exists():
        return jsonify({
            "ok": False,
            "error": "Parecer não encontrado",
            "receipt_id": receipt_id,
            "hint": "Verifique se o ID está correcto ou se o parecer já foi gerado."
        }), 404

    # Verificar no Ledger
    ledger_verified = False
    try:
        resp = requests.get(f"{LEDGER_URL}/api/receipts/{receipt_id}", timeout=5)
        ledger_verified = resp.status_code == 200
    except Exception:
        pass

    # Se pedido JSON, retornar metadados
    if request.args.get("format") == "json" and json_path.exists():
        report_data = json.loads(json_path.read_text())
        report_data["ledger_verified"] = ledger_verified
        return jsonify({"ok": True, "report": report_data})

    # Retornar HTML
    html_content = html_path.read_text(encoding="utf-8")

    # Injectar status de verificação no HTML
    if ledger_verified:
        html_content = html_content.replace(
            "✓ Registado no Forensic Ledger",
            "✓ VERIFICADO no Forensic Ledger"
        )

    return html_content, 200, {"Content-Type": "text/html; charset=utf-8"}


@grove_bp.route("/report/<receipt_id>.pdf", methods=["GET"])
def get_report_pdf(receipt_id):
    """
    GET /grove/report/<receipt_id>.pdf — Download do PDF do parecer.
    """
    receipt_id = re.sub(r'[^A-Za-z0-9\-]', '', receipt_id)
    pdf_path = REPORTS_DIR / f"{receipt_id}.pdf"

    if pdf_path.exists():
        return pdf_path.read_bytes(), 200, {
            "Content-Type": "application/pdf",
            "Content-Disposition": f"inline; filename={receipt_id}.pdf"
        }

    # Se não existe PDF, tentar gerar a partir do HTML
    html_path = REPORTS_DIR / f"{receipt_id}.html"
    if not html_path.exists():
        return jsonify({"ok": False, "error": "Parecer não encontrado"}), 404

    # Tentar gerar PDF via Export Engine
    try:
        html_content = html_path.read_text(encoding="utf-8")
        export_resp = requests.post(
            "http://127.0.0.1:8103/api/export/html-to-pdf",
            json={
                "html": html_content,
                "filename": f"{receipt_id}.pdf",
                "options": {"format": "A4", "margin": "20mm"}
            },
            timeout=30
        )
        if export_resp.status_code == 200:
            pdf_data = export_resp.json()
            if pdf_data.get("pdf_base64"):
                pdf_bytes = base64.b64decode(pdf_data["pdf_base64"])
                pdf_path.write_bytes(pdf_bytes)
                return pdf_bytes, 200, {
                    "Content-Type": "application/pdf",
                    "Content-Disposition": f"inline; filename={receipt_id}.pdf"
                }
    except Exception as e:
        return jsonify({"ok": False, "error": f"Erro ao gerar PDF: {str(e)}"}), 500

    return jsonify({"ok": False, "error": "PDF não disponível. Use a versão HTML."}), 404
