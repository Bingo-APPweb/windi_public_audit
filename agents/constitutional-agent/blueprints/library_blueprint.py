#!/usr/bin/env python3
"""
W-LIB-001 — WINDI Bibliotecário Agent v1.0.0
═══════════════════════════════════════════════════════════════════════════════
Blueprint para sandbox-core (:8091)

Missão: Guardião do conhecimento constitucional. Fornece contexto imutável
        (Invariantes, Princípios, Wisdom Blocks) a qualquer agente da constelação
        antes de agir. Extensível pelo Human Dragon para conhecimento adicional.

Endpoints:
  /library/context         → Contexto constitucional para agentes
  /library/grove-brief     → Briefing para injecção no Grove Arena
  /library/knowledge       → GET: lista conhecimento | POST: adiciona entrada
  /library/invariants      → Lista das 11 Invariantes
  /library/agents          → Registo da constelação
  /library/health          → Health check

Princípio: "IA processa. Humano decide. WINDI garante."
I9 Gate: Nenhum conhecimento é adicionado sem human_approved=True

Location: /opt/windi/sandbox-core/blueprints/library_blueprint.py
Port: Integrado no sandbox-core (:8091)
═══════════════════════════════════════════════════════════════════════════════
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
import hashlib
import json

# ══════════════════════════════════════════════════════════════════════════════
# BLUEPRINT SETUP
# ══════════════════════════════════════════════════════════════════════════════

library_bp = Blueprint('library', __name__, url_prefix='/library')

# ══════════════════════════════════════════════════════════════════════════════
# HARDCODED CONSTITUTIONAL KNOWLEDGE (IMMUTABLE)
# ══════════════════════════════════════════════════════════════════════════════

# ── 11 Invariantes Constitucionais ────────────────────────────────────────────
INVARIANTS = {
    "I1": {
        "code": "I1",
        "name": "Soberania do Humano",
        "severity": "IRREMEDIÁVEL",
        "description": {
            "pt": "O Human Dragon possui veto absoluto sobre qualquer decisão do sistema. Nenhuma IA pode sobrepor-se à vontade humana expressa.",
            "en": "The Human Dragon holds absolute veto over any system decision. No AI can override expressed human will.",
            "de": "Der Human Dragon hat absolutes Vetorecht über jede Systementscheidung. Keine KI kann den ausdrücklichen menschlichen Willen übergehen."
        }
    },
    "I2": {
        "code": "I2",
        "name": "Integridade Forense",
        "severity": "IRREMEDIÁVEL",
        "description": {
            "pt": "Todo documento com impacto legal ou financeiro deve ser registado no Ledger Forense com hash SHA-256 e timestamp imutável.",
            "en": "Every document with legal or financial impact must be registered in the Forensic Ledger with SHA-256 hash and immutable timestamp.",
            "de": "Jedes Dokument mit rechtlicher oder finanzieller Auswirkung muss im Forensischen Ledger mit SHA-256-Hash und unveränderlichem Zeitstempel registriert werden."
        }
    },
    "I3": {
        "code": "I3",
        "name": "Cobertura Trilíngue",
        "severity": "IRREMEDIÁVEL",
        "description": {
            "pt": "Todo output voltado ao utilizador deve existir em PT-BR, EN e DE. Sem excepções.",
            "en": "All user-facing output must exist in PT-BR, EN, and DE. No exceptions.",
            "de": "Alle benutzerorientierten Ausgaben müssen in PT-BR, EN und DE existieren. Keine Ausnahmen."
        }
    },
    "I4": {
        "code": "I4",
        "name": "Privacidade por Desenho",
        "severity": "IRREMEDIÁVEL",
        "description": {
            "pt": "Dados pessoais são processados localmente. Nenhum dado PII atravessa fronteiras de serviço sem consentimento explícito e criptografia.",
            "en": "Personal data is processed locally. No PII crosses service boundaries without explicit consent and encryption.",
            "de": "Personenbezogene Daten werden lokal verarbeitet. Keine PII überschreitet Dienstgrenzen ohne ausdrückliche Zustimmung und Verschlüsselung."
        }
    },
    "I5": {
        "code": "I5",
        "name": "Continuidade de Serviço",
        "severity": "IRREMEDIÁVEL",
        "description": {
            "pt": "O sistema deve degradar graciosamente. Falha de um serviço não pode derrubar outros. Fallbacks existem para todas as dependências críticas.",
            "en": "The system must degrade gracefully. Failure of one service cannot bring down others. Fallbacks exist for all critical dependencies.",
            "de": "Das System muss graceful degradieren. Der Ausfall eines Dienstes darf andere nicht beeinträchtigen. Fallbacks existieren für alle kritischen Abhängigkeiten."
        }
    },
    "I6": {
        "code": "I6",
        "name": "Transparência de Decisão",
        "severity": "IRREMEDIÁVEL",
        "description": {
            "pt": "Toda decisão da IA deve ser explicável. O Human Dragon pode pedir 'porquê' e receber resposta clara com cadeia de raciocínio.",
            "en": "Every AI decision must be explainable. The Human Dragon can ask 'why' and receive a clear answer with reasoning chain.",
            "de": "Jede KI-Entscheidung muss erklärbar sein. Der Human Dragon kann 'warum' fragen und eine klare Antwort mit Argumentationskette erhalten."
        }
    },
    "I7": {
        "code": "I7",
        "name": "Isolamento de Camadas",
        "severity": "IRREMEDIÁVEL",
        "description": {
            "pt": "Camada semântica (IA) e camada executora (código) estão separadas. IA propõe, código validado executa.",
            "en": "Semantic layer (AI) and executor layer (code) are separated. AI proposes, validated code executes.",
            "de": "Semantische Schicht (KI) und Ausführungsschicht (Code) sind getrennt. KI schlägt vor, validierter Code führt aus."
        }
    },
    "I8": {
        "code": "I8",
        "name": "Auditabilidade Total",
        "severity": "IRREMEDIÁVEL",
        "description": {
            "pt": "Toda acção do sistema é registada com actor, timestamp e contexto. Logs são imutáveis e retidos por período legal.",
            "en": "Every system action is logged with actor, timestamp, and context. Logs are immutable and retained for legal period.",
            "de": "Jede Systemaktion wird mit Akteur, Zeitstempel und Kontext protokolliert. Logs sind unveränderlich und werden für die gesetzliche Frist aufbewahrt."
        }
    },
    "I9": {
        "code": "I9",
        "name": "Proibição de Autonomia",
        "severity": "IRREMEDIÁVEL",
        "description": {
            "pt": "Nenhuma IA pode executar acções com impacto irreversível sem aprovação humana explícita. A IA PROPÕE, nunca executa unilateralmente.",
            "en": "No AI can execute actions with irreversible impact without explicit human approval. AI PROPOSES, never executes unilaterally.",
            "de": "Keine KI kann Aktionen mit irreversiblen Auswirkungen ohne ausdrückliche menschliche Genehmigung ausführen. KI SCHLÄGT VOR, führt niemals einseitig aus."
        }
    },
    "I10": {
        "code": "I10",
        "name": "Governança Semântica",
        "severity": "IRREMEDIÁVEL",
        "description": {
            "pt": "Todo conteúdo passa pelo SGE (Semantic Governance Engine) antes de output. Risco é classificado R0-R5 e tratado adequadamente.",
            "en": "All content passes through SGE (Semantic Governance Engine) before output. Risk is classified R0-R5 and handled appropriately.",
            "de": "Alle Inhalte durchlaufen die SGE (Semantic Governance Engine) vor der Ausgabe. Risiko wird R0-R5 klassifiziert und entsprechend behandelt."
        }
    },
    "I11": {
        "code": "I11",
        "name": "Integridade da Constelação",
        "severity": "IRREMEDIÁVEL",
        "description": {
            "pt": "Agentes da constelação operam como microserviços independentes mas coordenados. Nenhum agente pode modificar outro sem protocolo de consenso.",
            "en": "Constellation agents operate as independent but coordinated microservices. No agent can modify another without consensus protocol.",
            "de": "Konstellationsagenten arbeiten als unabhängige aber koordinierte Microservices. Kein Agent kann einen anderen ohne Konsensprotokoll modifizieren."
        }
    }
}

# ── 8 Princípios de Governança ────────────────────────────────────────────────
GOVERNANCE_PRINCIPLES = {
    "GP-001": {
        "code": "GP-001",
        "name": "Princípio WINDI",
        "statement": {
            "pt": "IA processa. Humano decide. WINDI garante.",
            "en": "AI processes. Human decides. WINDI guarantees.",
            "de": "KI verarbeitet. Mensch entscheidet. WINDI garantiert."
        }
    },
    "GP-002": {
        "code": "GP-002",
        "name": "Three Dragons Protocol",
        "statement": {
            "pt": "Human Dragon (veto), Code Dragon (implementa), AI Dragon (propõe). Ordem imutável.",
            "en": "Human Dragon (veto), Code Dragon (implements), AI Dragon (proposes). Immutable order.",
            "de": "Human Dragon (Veto), Code Dragon (implementiert), AI Dragon (schlägt vor). Unveränderliche Reihenfolge."
        }
    },
    "GP-003": {
        "code": "GP-003",
        "name": "Forensic First",
        "statement": {
            "pt": "Nenhum documento com impacto sai sem Virtue Receipt. A prova existe antes da acção.",
            "en": "No document with impact leaves without Virtue Receipt. Proof exists before action.",
            "de": "Kein Dokument mit Auswirkung verlässt ohne Virtue Receipt. Beweis existiert vor der Aktion."
        }
    },
    "GP-004": {
        "code": "GP-004",
        "name": "Graceful Degradation",
        "statement": {
            "pt": "Na falha, informar e propor alternativas. Nunca silêncio, nunca crash.",
            "en": "On failure, inform and propose alternatives. Never silence, never crash.",
            "de": "Bei Fehler, informieren und Alternativen vorschlagen. Niemals Stille, niemals Absturz."
        }
    },
    "GP-005": {
        "code": "GP-005",
        "name": "Semantic Layer Separation",
        "statement": {
            "pt": "IA gera intenção estruturada (JSON/YAML). Código validado executa. Nunca código em runtime da IA.",
            "en": "AI generates structured intent (JSON/YAML). Validated code executes. Never runtime code from AI.",
            "de": "KI generiert strukturierte Absicht (JSON/YAML). Validierter Code führt aus. Niemals Laufzeitcode von KI."
        }
    },
    "GP-006": {
        "code": "GP-006",
        "name": "Trilingual Native",
        "statement": {
            "pt": "PT-BR, EN, DE são idiomas nativos. Tradução não é afterthought, é requisito.",
            "en": "PT-BR, EN, DE are native languages. Translation is not an afterthought, it's a requirement.",
            "de": "PT-BR, EN, DE sind Muttersprachen. Übersetzung ist kein Nachgedanke, sondern eine Anforderung."
        }
    },
    "GP-007": {
        "code": "GP-007",
        "name": "Privacy by Design",
        "statement": {
            "pt": "Dados pessoais nunca viajam desnecessariamente. Minimização é padrão.",
            "en": "Personal data never travels unnecessarily. Minimization is default.",
            "de": "Personenbezogene Daten reisen nie unnötig. Minimierung ist Standard."
        }
    },
    "GP-008": {
        "code": "GP-008",
        "name": "Explain Everything",
        "statement": {
            "pt": "Se a IA decidiu, pode explicar. Se não pode explicar, não decide.",
            "en": "If AI decided, it can explain. If it can't explain, it doesn't decide.",
            "de": "Wenn KI entschieden hat, kann sie erklären. Wenn sie nicht erklären kann, entscheidet sie nicht."
        }
    }
}

# ── Constelação de Agentes ────────────────────────────────────────────────────
CONSTELLATION_AGENTS = {
    "W-LIB-001": {
        "id": "W-LIB-001",
        "name": "Bibliotecário",
        "version": "1.0.0",
        "port": 8091,
        "route": "/library",
        "status": "ACTIVE",
        "mission": {
            "pt": "Guardião do conhecimento constitucional. Fornece contexto a agentes antes de agir.",
            "en": "Guardian of constitutional knowledge. Provides context to agents before acting.",
            "de": "Hüter des konstitutionellen Wissens. Liefert Kontext an Agenten vor dem Handeln."
        }
    },
    "W-LED-001": {
        "id": "W-LED-001",
        "name": "Forensic Ledger",
        "version": "0.8.0",
        "port": 8101,
        "route": "/api/receipts",
        "status": "ACTIVE",
        "mission": {
            "pt": "Regista Virtue Receipts com hash SHA-256 e timestamp imutável.",
            "en": "Registers Virtue Receipts with SHA-256 hash and immutable timestamp.",
            "de": "Registriert Virtue Receipts mit SHA-256-Hash und unveränderlichem Zeitstempel."
        }
    },
    "W-VLT-001": {
        "id": "W-VLT-001",
        "name": "Secure Vault",
        "version": "0.7.0",
        "port": 8106,
        "route": "/api",
        "status": "ACTIVE",
        "mission": {
            "pt": "Armazena documentos críticos com criptografia e controlo de acesso.",
            "en": "Stores critical documents with encryption and access control.",
            "de": "Speichert kritische Dokumente mit Verschlüsselung und Zugriffskontrolle."
        }
    },
    "W-SGE-001": {
        "id": "W-SGE-001",
        "name": "Semantic Governance Engine",
        "version": "0.6.0",
        "port": 8091,
        "route": "/sge",
        "status": "ACTIVE",
        "mission": {
            "pt": "Classifica risco semântico (R0-R5) em todo conteúdo antes de output.",
            "en": "Classifies semantic risk (R0-R5) in all content before output.",
            "de": "Klassifiziert semantisches Risiko (R0-R5) in allen Inhalten vor der Ausgabe."
        }
    },
    "W-GRV-001": {
        "id": "W-GRV-001",
        "name": "Grove Arena",
        "version": "0.5.0",
        "port": 8091,
        "route": "/grove",
        "status": "ACTIVE",
        "mission": {
            "pt": "Facilita debates estruturados entre agentes para decisões complexas.",
            "en": "Facilitates structured debates between agents for complex decisions.",
            "de": "Ermöglicht strukturierte Debatten zwischen Agenten für komplexe Entscheidungen."
        }
    },
    "W-WIS-001": {
        "id": "W-WIS-001",
        "name": "Wisdom Manager",
        "version": "0.4.0",
        "port": 8091,
        "route": "/wisdom",
        "status": "ACTIVE",
        "mission": {
            "pt": "Cultiva e amadurece Wisdom Blocks (N0→N5) da semente à publicação.",
            "en": "Cultivates and matures Wisdom Blocks (N0→N5) from seed to publication.",
            "de": "Kultiviert und reift Wisdom Blocks (N0→N5) vom Samen bis zur Veröffentlichung."
        }
    },
    "W-COM-001": {
        "id": "W-COM-001",
        "name": "Communiqué Engine",
        "version": "0.9.0",
        "port": 8109,
        "route": "/api",
        "status": "ACTIVE",
        "mission": {
            "pt": "Gera comunicações trilíngues a partir de templates ISP.",
            "en": "Generates trilingual communications from ISP templates.",
            "de": "Generiert dreisprachige Kommunikation aus ISP-Vorlagen."
        }
    },
    "W-EXP-001": {
        "id": "W-EXP-001",
        "name": "Export Engine",
        "version": "0.8.0",
        "port": 8102,
        "route": "/api",
        "status": "ACTIVE",
        "mission": {
            "pt": "Exporta documentos em PDF/XLSX/DOCX com Forensic Seal.",
            "en": "Exports documents in PDF/XLSX/DOCX with Forensic Seal.",
            "de": "Exportiert Dokumente in PDF/XLSX/DOCX mit Forensic Seal."
        }
    },
    "W-DSK-001": {
        "id": "W-DSK-001",
        "name": "a4Desk Desktop",
        "version": "0.7.0",
        "port": 8100,
        "route": "/",
        "status": "ACTIVE",
        "mission": {
            "pt": "Interface desktop para gestão documental com IA assistida.",
            "en": "Desktop interface for document management with AI assistance.",
            "de": "Desktop-Schnittstelle für Dokumentenmanagement mit KI-Unterstützung."
        }
    }
}

# ── Wisdom Blocks Selados ─────────────────────────────────────────────────────
SEALED_WISDOM = [
    {
        "id": "WB-001",
        "title": {
            "pt": "Nascimento da Ideia",
            "en": "Birth of the Idea",
            "de": "Geburt der Idee"
        },
        "maturity": "N5",
        "sealed_at": "2025-02-10T00:00:00Z",
        "ledger_receipt": "VR-2025-001"
    },
    {
        "id": "WB-002",
        "title": {
            "pt": "A Árvore do Conhecimento",
            "en": "The Knowledge Tree",
            "de": "Der Wissensbaum"
        },
        "maturity": "N5",
        "sealed_at": "2025-02-15T00:00:00Z",
        "ledger_receipt": "VR-2025-002"
    },
    {
        "id": "WB-003",
        "title": {
            "pt": "Constelação WINDI",
            "en": "WINDI Constellation",
            "de": "WINDI-Konstellation"
        },
        "maturity": "N4",
        "sealed_at": "2025-02-20T00:00:00Z",
        "ledger_receipt": "VR-2025-003"
    },
    {
        "id": "WB-004",
        "title": {
            "pt": "Three Dragons Protocol",
            "en": "Three Dragons Protocol",
            "de": "Three Dragons Protocol"
        },
        "maturity": "N5",
        "sealed_at": "2025-02-22T00:00:00Z",
        "ledger_receipt": "VR-2025-004"
    },
    {
        "id": "WB-005",
        "title": {
            "pt": "Semantic Governance Engine",
            "en": "Semantic Governance Engine",
            "de": "Semantic Governance Engine"
        },
        "maturity": "N4",
        "sealed_at": "2025-02-25T00:00:00Z",
        "ledger_receipt": "VR-2025-005"
    }
]

# ── Conhecimento Extensível (adicionado pelo Human Dragon) ────────────────────
# Este dicionário é mutável em runtime, mas persistido em JSON
EXTENSIBLE_KNOWLEDGE = []

KNOWLEDGE_STORE_PATH = "/opt/windi/engine/wisdom/library_knowledge.json"

# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def load_extensible_knowledge():
    """Load human-added knowledge from persistent store."""
    global EXTENSIBLE_KNOWLEDGE
    try:
        with open(KNOWLEDGE_STORE_PATH, 'r', encoding='utf-8') as f:
            EXTENSIBLE_KNOWLEDGE = json.load(f)
    except FileNotFoundError:
        EXTENSIBLE_KNOWLEDGE = []
    except json.JSONDecodeError:
        EXTENSIBLE_KNOWLEDGE = []

def save_extensible_knowledge():
    """Persist human-added knowledge."""
    try:
        with open(KNOWLEDGE_STORE_PATH, 'w', encoding='utf-8') as f:
            json.dump(EXTENSIBLE_KNOWLEDGE, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        return False

def get_trilingual_text(obj, lang='en'):
    """Extract text for specified language from trilingual object."""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        return obj.get(lang) or obj.get('en') or obj.get('pt') or obj.get('de') or ''
    return str(obj)

def hash_content(data):
    """Generate SHA-256 hash for content integrity."""
    serialized = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@library_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "agent_id": "W-LIB-001",
        "agent_name": "Bibliotecário",
        "version": "1.0.0",
        "status": "HEALTHY",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "knowledge_stats": {
            "invariants": len(INVARIANTS),
            "principles": len(GOVERNANCE_PRINCIPLES),
            "agents": len(CONSTELLATION_AGENTS),
            "sealed_wisdom": len(SEALED_WISDOM),
            "extensible_entries": len(EXTENSIBLE_KNOWLEDGE)
        }
    })


@library_bp.route('/context', methods=['GET', 'POST'])
def get_context():
    """
    Main endpoint for agents requesting constitutional context before acting.

    Query params or JSON body:
      - requesting_agent: ID of the agent requesting context (required)
      - action_type: Type of action being planned (optional)
      - include: Comma-separated list of what to include (invariants,principles,agents,wisdom)
      - lang: Language preference (pt/en/de), default 'en'

    Returns tailored constitutional context for the requesting agent.
    """
    if request.method == 'POST':
        data = request.get_json() or {}
    else:
        data = request.args.to_dict()

    requesting_agent = data.get('requesting_agent', 'UNKNOWN')
    action_type = data.get('action_type', 'GENERAL')
    include = data.get('include', 'invariants,principles').split(',')
    lang = data.get('lang', 'en')

    # Build context response
    context = {
        "context_id": f"CTX-{hash_content({'agent': requesting_agent, 'ts': datetime.now(timezone.utc).isoformat()})[:12]}",
        "provided_to": requesting_agent,
        "action_type": action_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "language": lang,
        "governance_principle": get_trilingual_text(GOVERNANCE_PRINCIPLES["GP-001"]["statement"], lang),
        "sections": {}
    }

    # Include requested sections
    if 'invariants' in include:
        context["sections"]["invariants"] = {
            code: {
                "code": inv["code"],
                "name": inv["name"],
                "severity": inv["severity"],
                "description": get_trilingual_text(inv["description"], lang)
            }
            for code, inv in INVARIANTS.items()
        }

    if 'principles' in include:
        context["sections"]["principles"] = {
            code: {
                "code": gp["code"],
                "name": gp["name"],
                "statement": get_trilingual_text(gp["statement"], lang)
            }
            for code, gp in GOVERNANCE_PRINCIPLES.items()
        }

    if 'agents' in include:
        context["sections"]["constellation"] = {
            agent_id: {
                "id": agent["id"],
                "name": agent["name"],
                "port": agent["port"],
                "route": agent["route"],
                "status": agent["status"],
                "mission": get_trilingual_text(agent["mission"], lang)
            }
            for agent_id, agent in CONSTELLATION_AGENTS.items()
        }

    if 'wisdom' in include:
        context["sections"]["sealed_wisdom"] = [
            {
                "id": wb["id"],
                "title": get_trilingual_text(wb["title"], lang),
                "maturity": wb["maturity"],
                "ledger_receipt": wb["ledger_receipt"]
            }
            for wb in SEALED_WISDOM
        ]

    # Add critical reminders based on action type
    context["critical_reminders"] = _get_action_reminders(action_type, lang)

    return jsonify(context)


@library_bp.route('/grove-brief', methods=['GET', 'POST'])
def grove_brief():
    """
    Generate a concise briefing for injection into Grove Arena debates.

    Query params or JSON body:
      - topic: The debate topic
      - participants: Comma-separated agent IDs
      - lang: Language preference

    Returns a structured briefing with relevant constitutional context.
    """
    if request.method == 'POST':
        data = request.get_json() or {}
    else:
        data = request.args.to_dict()

    topic = data.get('topic', 'UNSPECIFIED')
    participants = data.get('participants', '').split(',')
    lang = data.get('lang', 'en')

    # Build Grove Arena briefing
    briefing = {
        "briefing_id": f"GRV-BRIEF-{hash_content({'topic': topic, 'ts': datetime.now(timezone.utc).isoformat()})[:8]}",
        "topic": topic,
        "participants": [p.strip() for p in participants if p.strip()],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "language": lang,

        # Core principle injection
        "governance_anchor": {
            "principle": get_trilingual_text(GOVERNANCE_PRINCIPLES["GP-001"]["statement"], lang),
            "three_dragons": get_trilingual_text(GOVERNANCE_PRINCIPLES["GP-002"]["statement"], lang)
        },

        # Key invariants for debate context
        "binding_invariants": [
            {
                "code": "I9",
                "name": INVARIANTS["I9"]["name"],
                "description": get_trilingual_text(INVARIANTS["I9"]["description"], lang)
            },
            {
                "code": "I6",
                "name": INVARIANTS["I6"]["name"],
                "description": get_trilingual_text(INVARIANTS["I6"]["description"], lang)
            }
        ],

        # Debate rules
        "debate_rules": _get_debate_rules(lang),

        # Participant missions
        "participant_missions": {
            agent_id: get_trilingual_text(CONSTELLATION_AGENTS.get(agent_id, {}).get("mission", "Unknown agent"), lang)
            for agent_id in participants if agent_id in CONSTELLATION_AGENTS
        }
    }

    return jsonify(briefing)


@library_bp.route('/knowledge', methods=['GET', 'POST'])
def knowledge():
    """
    GET: List all extensible knowledge entries
    POST: Add new knowledge entry (requires human_approved=True)

    POST body:
      - title: Trilingual title object
      - content: Trilingual content object
      - category: Category tag
      - human_approved: Must be True (I9 gate)
      - human_note: Optional approval note
    """
    load_extensible_knowledge()

    if request.method == 'GET':
        lang = request.args.get('lang', 'en')
        return jsonify({
            "entries": [
                {
                    "id": entry["id"],
                    "title": get_trilingual_text(entry["title"], lang),
                    "category": entry.get("category", "general"),
                    "added_at": entry["added_at"],
                    "approved_by": entry.get("approved_by", "Human Dragon")
                }
                for entry in EXTENSIBLE_KNOWLEDGE
            ],
            "total": len(EXTENSIBLE_KNOWLEDGE)
        })

    # POST - Add new knowledge
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # I9 Gate: Require explicit human approval
    if not data.get('human_approved', False):
        return jsonify({
            "error": "I9_BLOCKED",
            "message": "Knowledge cannot be added without human_approved=True. The Bibliotecário PROPOSES, Human Dragon DECIDES.",
            "invariant": "I9 — Proibição de Autonomia"
        }), 403

    # Validate required fields
    if not data.get('title') or not data.get('content'):
        return jsonify({"error": "title and content are required"}), 400

    # Create new knowledge entry
    entry = {
        "id": f"KE-{hash_content(data)[:8]}",
        "title": data["title"],
        "content": data["content"],
        "category": data.get("category", "general"),
        "added_at": datetime.now(timezone.utc).isoformat(),
        "approved_by": "Human Dragon",
        "human_note": data.get("human_note", ""),
        "content_hash": hash_content(data["content"])
    }

    EXTENSIBLE_KNOWLEDGE.append(entry)
    saved = save_extensible_knowledge()

    return jsonify({
        "status": "ADDED",
        "entry_id": entry["id"],
        "persisted": saved,
        "i9_gate": "PASSED",
        "message": "Knowledge entry added by Human Dragon approval."
    }), 201


@library_bp.route('/invariants', methods=['GET'])
def list_invariants():
    """List all constitutional invariants."""
    lang = request.args.get('lang', 'en')
    return jsonify({
        "count": len(INVARIANTS),
        "invariants": [
            {
                "code": inv["code"],
                "name": inv["name"],
                "severity": inv["severity"],
                "description": get_trilingual_text(inv["description"], lang)
            }
            for inv in INVARIANTS.values()
        ]
    })


@library_bp.route('/agents', methods=['GET'])
def list_agents():
    """List all agents in the WINDI constellation."""
    lang = request.args.get('lang', 'en')
    return jsonify({
        "constellation": "WINDI",
        "count": len(CONSTELLATION_AGENTS),
        "agents": [
            {
                "id": agent["id"],
                "name": agent["name"],
                "version": agent["version"],
                "port": agent["port"],
                "route": agent["route"],
                "status": agent["status"],
                "mission": get_trilingual_text(agent["mission"], lang)
            }
            for agent in CONSTELLATION_AGENTS.values()
        ]
    })


@library_bp.route('/principles', methods=['GET'])
def list_principles():
    """List all governance principles."""
    lang = request.args.get('lang', 'en')
    return jsonify({
        "count": len(GOVERNANCE_PRINCIPLES),
        "principles": [
            {
                "code": gp["code"],
                "name": gp["name"],
                "statement": get_trilingual_text(gp["statement"], lang)
            }
            for gp in GOVERNANCE_PRINCIPLES.values()
        ]
    })


@library_bp.route('/wisdom', methods=['GET'])
def list_wisdom():
    """List all sealed Wisdom Blocks."""
    lang = request.args.get('lang', 'en')
    return jsonify({
        "count": len(SEALED_WISDOM),
        "wisdom_blocks": [
            {
                "id": wb["id"],
                "title": get_trilingual_text(wb["title"], lang),
                "maturity": wb["maturity"],
                "sealed_at": wb["sealed_at"],
                "ledger_receipt": wb["ledger_receipt"]
            }
            for wb in SEALED_WISDOM
        ]
    })


# ══════════════════════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _get_action_reminders(action_type: str, lang: str) -> list:
    """Get critical reminders based on action type."""
    reminders = {
        "EXPORT": {
            "pt": ["I2: Todo documento exportado deve ter Virtue Receipt", "I3: Output deve ser trilíngue"],
            "en": ["I2: Every exported document must have Virtue Receipt", "I3: Output must be trilingual"],
            "de": ["I2: Jedes exportierte Dokument muss Virtue Receipt haben", "I3: Ausgabe muss dreisprachig sein"]
        },
        "DECISION": {
            "pt": ["I9: Decisões irreversíveis requerem aprovação humana", "I6: A decisão deve ser explicável"],
            "en": ["I9: Irreversible decisions require human approval", "I6: The decision must be explainable"],
            "de": ["I9: Irreversible Entscheidungen erfordern menschliche Genehmigung", "I6: Die Entscheidung muss erklärbar sein"]
        },
        "COMMUNICATION": {
            "pt": ["I3: Comunicação deve ser trilíngue", "GP-006: PT-BR, EN, DE são nativos"],
            "en": ["I3: Communication must be trilingual", "GP-006: PT-BR, EN, DE are native"],
            "de": ["I3: Kommunikation muss dreisprachig sein", "GP-006: PT-BR, EN, DE sind Muttersprachen"]
        },
        "DATA_PROCESSING": {
            "pt": ["I4: Dados pessoais processados localmente", "I8: Toda acção deve ser auditável"],
            "en": ["I4: Personal data processed locally", "I8: Every action must be auditable"],
            "de": ["I4: Personenbezogene Daten lokal verarbeitet", "I8: Jede Aktion muss auditierbar sein"]
        },
        "GENERAL": {
            "pt": ["GP-001: IA processa. Humano decide. WINDI garante.", "I9: IA propõe, nunca executa unilateralmente"],
            "en": ["GP-001: AI processes. Human decides. WINDI guarantees.", "I9: AI proposes, never executes unilaterally"],
            "de": ["GP-001: KI verarbeitet. Mensch entscheidet. WINDI garantiert.", "I9: KI schlägt vor, führt niemals einseitig aus"]
        }
    }

    action_reminders = reminders.get(action_type.upper(), reminders["GENERAL"])
    return action_reminders.get(lang, action_reminders["en"])


def _get_debate_rules(lang: str) -> list:
    """Get Grove Arena debate rules."""
    rules = {
        "pt": [
            "1. Cada argumento deve referenciar pelo menos uma Invariante",
            "2. Propostas devem ser explicáveis (I6)",
            "3. Nenhuma decisão final sem Human Dragon (I9)",
            "4. Dissidência deve ser registada",
            "5. Conclusão deve ter consenso mínimo de 2/3"
        ],
        "en": [
            "1. Each argument must reference at least one Invariant",
            "2. Proposals must be explainable (I6)",
            "3. No final decision without Human Dragon (I9)",
            "4. Dissent must be recorded",
            "5. Conclusion must have minimum 2/3 consensus"
        ],
        "de": [
            "1. Jedes Argument muss mindestens eine Invariante referenzieren",
            "2. Vorschläge müssen erklärbar sein (I6)",
            "3. Keine endgültige Entscheidung ohne Human Dragon (I9)",
            "4. Dissens muss aufgezeichnet werden",
            "5. Schlussfolgerung muss mindestens 2/3 Konsens haben"
        ]
    }
    return rules.get(lang, rules["en"])


# ══════════════════════════════════════════════════════════════════════════════
# INITIALIZATION
# ══════════════════════════════════════════════════════════════════════════════

# Load extensible knowledge on module import
load_extensible_knowledge()

# ══════════════════════════════════════════════════════════════════════════════
# CLI (for testing)
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║  W-LIB-001 — WINDI Bibliotecário v1.0.0                      ║
║  "IA processa. Humano decide. WINDI garante."                ║
╠══════════════════════════════════════════════════════════════╣
║  Este é um Flask Blueprint. Para uso standalone, execute:    ║
║                                                              ║
║    from flask import Flask                                   ║
║    from library_blueprint import library_bp                  ║
║    app = Flask(__name__)                                     ║
║    app.register_blueprint(library_bp)                        ║
║    app.run(port=8091)                                        ║
║                                                              ║
║  Endpoints:                                                  ║
║    /library/health      → Health check                       ║
║    /library/context     → Constitutional context for agents  ║
║    /library/grove-brief → Grove Arena briefing               ║
║    /library/knowledge   → GET/POST extensible knowledge      ║
║    /library/invariants  → List 11 invariants                 ║
║    /library/principles  → List 8 governance principles       ║
║    /library/agents      → List constellation agents          ║
║    /library/wisdom      → List sealed Wisdom Blocks          ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Print stats
    print(f"📚 Conhecimento Carregado:")
    print(f"   • {len(INVARIANTS)} Invariantes (I1-I11)")
    print(f"   • {len(GOVERNANCE_PRINCIPLES)} Princípios de Governança (GP-001 a GP-008)")
    print(f"   • {len(CONSTELLATION_AGENTS)} Agentes na Constelação")
    print(f"   • {len(SEALED_WISDOM)} Wisdom Blocks Selados")
    print(f"   • {len(EXTENSIBLE_KNOWLEDGE)} Entradas de Conhecimento Extensível")
    print()
