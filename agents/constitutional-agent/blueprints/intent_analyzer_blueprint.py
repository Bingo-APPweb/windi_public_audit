"""
W-INTENT-001 — Intent Analyzer Blueprint
Endpoint: POST /grove/intent-analyze
Constelação: :8091 (domain extension of constitutional-agent)

Missão:
  Receber o prompt bruto do USER, classificar a intenção,
  detectar ambiguidades e devolver 1 pergunta cirúrgica de clarificação
  + contexto estruturado para o agente especializado correcto.

Invariantes:
  I13 — Converge sempre para 1 pergunta concreta, nunca loop
  G3  — Propõe. O humano decide.
  I9  — Nunca escalada autónoma

Autor: Liga IA+H · Human Dragon: Jober Mögele Correa
Data:  2026-03-24
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone

intent_analyzer = Blueprint("intent_analyzer", __name__)

# ─── Domain Map ──────────────────────────────────────────────────────────────
# Mapeamento de keywords → agente responsável + domínio

DOMAIN_MAP = {
    "legal": {
        "agent": "W-LEGAL-001",
        "endpoint": "/legal/",
        "keywords": [
            "contrato", "contract", "vertrag",
            "cláusula", "clause", "klausel",
            "evidência", "evidence", "beweis",
            "tribunal", "court", "gericht",
            "processo", "process", "verfahren",
            "advogado", "lawyer", "anwalt",
            "jurídico", "legal", "rechtlich",
            "prova", "proof", "nachweis",
            "petição", "petition", "antrag",
            "réu", "defendant", "beklagter",
            "litigio", "litigation", "rechtsstreit",
            "caso", "case", "fall"
        ],
        "clarify_templates": [
            "Em que fase está o processo: investigação, instrução, julgamento ou recurso?",
            "O documento é para uso interno ou para apresentar em tribunal?",
            "Qual é a jurisdição principal: Alemanha, União Europeia, Brasil ou internacional?"
        ]
    },
    "notary": {
        "agent": "W-NOTARY-001",
        "endpoint": "/notary/",
        "keywords": [
            "notário", "notary", "notar",
            "autenticação", "authentication", "beglaubigung",
            "escritura", "deed", "urkunde",
            "certidão", "certificate", "zertifikat",
            "reconhecimento", "recognition", "anerkennung",
            "firma", "signature", "unterschrift",
            "procuração", "power of attorney", "vollmacht"
        ],
        "clarify_templates": [
            "O documento exige reconhecimento de firma ou autenticação electrónica (eIDAS)?",
            "É para uso doméstico (DE) ou internacional (apostila)?",
            "Precisa de selo notarial físico ou verificação digital no Ledger é suficiente?"
        ]
    },
    "accounting": {
        "agent": "W-ACCT-001",
        "endpoint": "/accounting/",
        "keywords": [
            "fatura", "invoice", "rechnung",
            "contabilidade", "accounting", "buchhaltung",
            "imposto", "tax", "steuer",
            "elster", "datev", "gobd",
            "xrechnung", "zugferd",
            "balanço", "balance", "bilanz",
            "declaração fiscal", "tax return", "steuererklärung"
        ],
        "clarify_templates": [
            "É para geração de fatura (XRechnung/ZUGFeRD) ou análise de documento existente?",
            "O output será para DATEV, ELSTER ou uso interno?",
            "O período fiscal: corrente, anterior ou histórico (GoBD)?"
        ]
    },
    "compliance": {
        "agent": "W-COMPLY-001",
        "endpoint": "/compliance/",
        "keywords": [
            "gdpr", "dsgvo", "compliance",
            "auditoria", "audit", "prüfung",
            "regulamento", "regulation", "verordnung",
            "eu ai act", "ai act",
            "política", "policy", "richtlinie",
            "privacidade", "privacy", "datenschutz",
            "consentimento", "consent", "einwilligung"
        ],
        "clarify_templates": [
            "É uma análise de compliance GDPR, EU AI Act, ou outra regulamentação?",
            "O âmbito é interno (política da empresa) ou externo (auditoria de terceiros)?",
            "Precisa de relatório selado no Ledger ou análise informal primeiro?"
        ]
    },
    "journalism": {
        "agent": "W-JOURN-001",
        "endpoint": "/jornal/",
        "keywords": [
            "artigo", "article", "artikel",
            "publicação", "publication", "veröffentlichung",
            "reportagem", "report", "bericht",
            "editorial", "editorial", "leitartikel",
            "jornalismo", "journalism", "journalismus",
            "notícia", "news", "nachricht",
            "communiqué", "comunicado"
        ],
        "clarify_templates": [
            "É um artigo de opinião, reportagem factual ou comunicado oficial?",
            "A publicação precisa de selo forense (Ledger) ou é apenas rascunho?",
            "O público-alvo é interno (WINDI) ou externo (imprensa, redes sociais)?"
        ]
    },
    "verify": {
        "agent": "VERIFY-PUBLIC",
        "endpoint": "/verify-public/",
        "keywords": [
            "verificar", "verify", "verifizieren",
            "autêntico", "authentic", "authentisch",
            "hash", "sha-256", "ledger",
            "receipt", "recibo", "quittung",
            "qr code", "qr", "scannen",
            "integridade", "integrity", "integrität",
            "selado", "sealed", "versiegelt"
        ],
        "clarify_templates": [
            "Tem o ID do receipt ou o QR code do documento?",
            "O documento foi criado no WINDI ou é externo (análise de autenticidade)?",
            "Precisa de relatório de verificação formal ou confirmação rápida?"
        ]
    },
    "grove": {
        "agent": "W-GROVE-001",
        "endpoint": "/grove/",
        "keywords": [
            "debate", "discussão", "discussion", "diskussion",
            "arena", "grove", "conselho", "council", "rat",
            "multi-agente", "multi-agent", "mehrere agenten",
            "divergência", "divergence", "abweichung",
            "consenso", "consensus", "konsens"
        ],
        "clarify_templates": [
            "Quer convocar o Grove Arena para um debate multi-agente?",
            "Quantos agentes devem participar na análise?",
            "O resultado deve ser selado ou é exploratório?"
        ]
    }
}

# ─── Intent Levels ───────────────────────────────────────────────────────────

INTENT_LEVELS = {
    "clear":     "Intenção clara — avançar directamente para o agente",
    "ambiguous": "Intenção parcialmente clara — 1 pergunta de clarificação",
    "unclear":   "Intenção pouco clara — reformulação necessária",
    "multi":     "Múltiplos domínios detectados — priorização necessária"
}

# ─── Core Functions ──────────────────────────────────────────────────────────

def detect_domains(text: str) -> list:
    """Detecta domínios relevantes no texto do USER."""
    text_lower = text.lower()
    matched = []

    for domain, config in DOMAIN_MAP.items():
        score = 0
        matched_keywords = []
        for kw in config["keywords"]:
            if kw.lower() in text_lower:
                score += 1
                matched_keywords.append(kw)
        if score > 0:
            matched.append({
                "domain": domain,
                "agent": config["agent"],
                "endpoint": config["endpoint"],
                "score": score,
                "matched_keywords": matched_keywords,
                "clarify_templates": config["clarify_templates"]
            })

    # Ordenar por score descendente
    return sorted(matched, key=lambda x: x["score"], reverse=True)


def select_clarification_question(domains: list, user_text: str) -> str:
    """
    Selecciona 1 pergunta cirúrgica de clarificação.
    Regra I13: máximo 1 pergunta por turno.
    """
    if not domains:
        return "Pode descrever brevemente o tipo de documento ou acção que precisa?"

    top_domain = domains[0]
    templates = top_domain["clarify_templates"]

    # Escolher o template mais relevante baseado no texto
    text_lower = user_text.lower()

    if any(w in text_lower for w in ["fase", "phase", "quando", "when", "etapa"]):
        return templates[0]
    elif any(w in text_lower for w in ["formato", "format", "exportar", "export", "tipo"]):
        return templates[1] if len(templates) > 1 else templates[0]
    elif any(w in text_lower for w in ["jurisdição", "jurisdiction", "país", "country", "região"]):
        return templates[2] if len(templates) > 2 else templates[0]
    else:
        return templates[0]


def classify_intent(domains: list, user_text: str) -> dict:
    """Classifica a intenção e determina o nível de clareza."""
    word_count = len(user_text.split())

    if not domains:
        return {
            "level": "unclear",
            "description": INTENT_LEVELS["unclear"],
            "confidence": 0.0
        }

    if len(domains) > 2 and domains[0]["score"] <= 2:
        return {
            "level": "multi",
            "description": INTENT_LEVELS["multi"],
            "confidence": 0.4
        }

    top_score = domains[0]["score"]
    confidence = min(top_score / 5.0, 1.0)

    if top_score >= 3 and word_count >= 8:
        return {
            "level": "clear",
            "description": INTENT_LEVELS["clear"],
            "confidence": confidence
        }
    else:
        return {
            "level": "ambiguous",
            "description": INTENT_LEVELS["ambiguous"],
            "confidence": confidence
        }


def build_routing_context(domains: list) -> dict:
    """Constrói o contexto de routing para o agente especializado."""
    if not domains:
        return {"suggested_agent": None, "fallback": "W-COMM-001"}

    primary = domains[0]
    return {
        "suggested_agent": primary["agent"],
        "suggested_endpoint": primary["endpoint"],
        "domain": primary["domain"],
        "confidence": min(primary["score"] / 5.0, 1.0),
        "alternatives": [
            {"agent": d["agent"], "domain": d["domain"], "score": d["score"]}
            for d in domains[1:3]  # max 2 alternativas
        ]
    }


# ─── Main Endpoint ────────────────────────────────────────────────────────────

@intent_analyzer.route("/grove/intent-analyze", methods=["POST"])
def analyze_intent():
    """
    POST /grove/intent-analyze

    Body:
    {
        "prompt": "texto do utilizador",
        "wallet_id": "opcional — para contexto de sessão",
        "session_context": {}  // opcional — histórico resumido
    }

    Response:
    {
        "intent": { level, description, confidence },
        "domains_detected": [...],
        "clarification_question": "1 pergunta cirúrgica",
        "routing": { suggested_agent, suggested_endpoint, ... },
        "action": "clarify | route | reformulate",
        "constitutional": { i13_applied, g3_applied },
        "timestamp": "..."
    }
    """
    try:
        body = request.get_json(force=True, silent=True) or {}
        user_prompt = body.get("prompt", "").strip()
        wallet_id   = body.get("wallet_id", "anonymous")
        session_ctx = body.get("session_context", {})

        if not user_prompt:
            return jsonify({
                "error": "Campo 'prompt' é obrigatório",
                "code": "MISSING_PROMPT"
            }), 400

        # ── Análise ──
        domains  = detect_domains(user_prompt)
        intent   = classify_intent(domains, user_prompt)
        routing  = build_routing_context(domains)
        question = select_clarification_question(domains, user_prompt)

        # ── Determinar acção recomendada (I13: convergir sempre) ──
        if intent["level"] == "clear":
            action = "route"          # avançar directamente para o agente
        elif intent["level"] in ("ambiguous", "multi"):
            action = "clarify"        # fazer 1 pergunta
        else:
            action = "reformulate"    # pedir ao user para reformular

        # ── Response ──
        response = {
            "intent": intent,
            "domains_detected": [
                {
                    "domain": d["domain"],
                    "agent": d["agent"],
                    "score": d["score"],
                    "matched_keywords": d["matched_keywords"]
                }
                for d in domains[:3]
            ],
            "clarification_question": question if action == "clarify" else None,
            "routing": routing,
            "action": action,
            "constitutional": {
                "i13_applied": True,   # máx 1 pergunta por turno
                "g3_applied": True,    # propõe, não executa
                "note": "AI processes. Human decides. WINDI guarantees."
            },
            "meta": {
                "wallet_id": wallet_id,
                "prompt_length": len(user_prompt),
                "prompt_word_count": len(user_prompt.split()),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({
            "error": "Erro interno no Intent Analyzer",
            "detail": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500


# ─── Health Check ─────────────────────────────────────────────────────────────

@intent_analyzer.route("/grove/intent-analyze/health", methods=["GET"])
def intent_health():
    return jsonify({
        "agent":   "W-INTENT-001",
        "version": "v1.0.0",
        "status":  "active",
        "domains": list(DOMAIN_MAP.keys()),
        "invariants": ["I13", "G3", "I9"],
        "endpoint": "POST /grove/intent-analyze",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200
