#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════════
  WINDI DRAGON CHAT SERVICE v2.2 — "Boca Descosida"
  Port: 8111

  REFACTORING A.4 — Connecting to Existing Intelligence:

  WEEK 1 (Complete):
  Action #1: Chat → Orchestrator (:8112) as execution backend
  Action #2: detect_language() from guardian-local (real detection)
  Action #3: Tier context via session (FREE/MED/HIGH routing)

  WEEK 2 (Complete):
  Action #4: needs_llm switch — smart routing decision
  Action #5: Local service queries — Ledger, Communiqué, Vault direct access
  Action #7: Layer 7 Semantics — entity extraction from natural language

  ANTI-ROBOTIC FIXES (v2.2):
  - Knowledge Base: local answers for WINDI concepts (Dignity ID, Vault, etc.)
  - Conversational Handler: contextual responses, no more greeting loops
  - Session Context: remembers if already greeted, adapts response

  COGNITIVE INTERFACE LAYER (v2.3):
  - 93% backend cognition → visible to human
  - Insight Generator: metrics → human language
  - Recommendation Engine: suggests next steps
  - Proactive Messages: Dragon speaks without being asked

  CONSTITUTIONAL PRINCIPLES (unchanged):
  1. Dragon suggests, never executes without confirmation
  2. Dragon never shows brand (no "Claude", "GPT", "Gemini")
  3. Session memory, not surveillance (in-memory only, no persistence)
  4. Dragon respects tier (FREE=local, MED=Guardian, HIGH=Council)
  5. Dragon speaks user's language (auto-detection via guardian-local)

  ARCHITECTURE:
  - FREE tier: 100% local motor (no external calls)
  - MED tier: Orchestrator /generate for content
  - HIGH tier: Orchestrator /orchestrate for full pipeline

  "42 músculos treinados. Boca descosida." — 27 Feb 2026
═══════════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import json
import re
import hashlib
import time
import urllib.request
import urllib.error
import smtplib
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ═══════════════════════════════════════════════════════════════════════════════════
# ECOSYSTEM IMPORTS — Connecting to existing intelligence
# ═══════════════════════════════════════════════════════════════════════════════════

# Add paths for ecosystem imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/opt/windi/guardian-local')
sys.path.insert(0, '/opt/windi/a4desk-editor/intent_parser')

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv('/opt/windi/.env')
except ImportError:
    pass  # dotenv not available, use system env vars

# Action #2: Real language detection from guardian-local
try:
    from lang_detect import detect_language as guardian_detect_language
    LANG_DETECT_SOURCE = "guardian-local"
except ImportError:
    guardian_detect_language = None
    LANG_DETECT_SOURCE = "fallback"

# Intent Parser for classify (optional, graceful degradation)
try:
    from intent_patterns import parse_intent, detect_create_intent
    INTENT_PARSER_AVAILABLE = True
except ImportError:
    parse_intent = None
    detect_create_intent = None
    INTENT_PARSER_AVAILABLE = False

# Dragon APIs for gate checking
from dragon_apis import get_gate, gate_status, WINDI_TIER

# Cognitive Interface Layer — makes intelligence visible
try:
    from cognitive_interface import CognitiveInterface, get_proactive_message
    CIL_AVAILABLE = True
except ImportError:
    CognitiveInterface = None
    get_proactive_message = None
    CIL_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════════

VERSION = "2.6.0"  # Template Messages System — Patch v1.2.0
PORT = 8111

# Action #1: Orchestrator as execution backend
ORCHESTRATOR_URL = os.environ.get("ORCHESTRATOR_URL", "http://localhost:8112")

# Session configuration (Principle 3: no surveillance)
SESSIONS = {}
SESSION_TTL = 3600  # 1 hour
MAX_SESSION_MESSAGES = 50

# ═══════════════════════════════════════════════════════════════════════════════════
# DISTRIBUTION LAYER — Send documents via Email, SMS, WhatsApp
# ═══════════════════════════════════════════════════════════════════════════════════

SMTP_HOST = os.environ.get("WINDI_SMTP_HOST", "localhost")
SMTP_PORT = int(os.environ.get("WINDI_SMTP_PORT", "25"))
SMTP_USER = os.environ.get("WINDI_SMTP_USER", "")
SMTP_PASS = os.environ.get("WINDI_SMTP_PASS", "")
SMTP_FROM = os.environ.get("WINDI_SMTP_FROM", "noreply@a4desk.de")
SMTP_USE_TLS = os.environ.get("WINDI_SMTP_TLS", "false").lower() == "true"

# Twilio for SMS (optional)
TWILIO_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM = os.environ.get("TWILIO_PHONE_NUMBER", "")

# WhatsApp Business API (optional)
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_API_TOKEN", "")
WHATSAPP_PHONE_ID = os.environ.get("WHATSAPP_PHONE_ID", "")

# LinkedIn API (optional)
LINKEDIN_CLIENT_ID = os.environ.get("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = os.environ.get("LINKEDIN_CLIENT_SECRET", "")
LINKEDIN_ACCESS_TOKEN = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_ORG_ID = os.environ.get("LINKEDIN_ORG_ID", "")  # For company page posts
LINKEDIN_API_URL = "https://api.linkedin.com/v2"

# Distribution log (for audit)
DISTRIBUTION_LOG = []

# Action #5: Service endpoints for local queries
SERVICE_ENDPOINTS = {
    "ledger": {
        "url": "http://localhost:8101",
        "stats": "/health",
        "list": "/api/receipts",
        "count_field": "receipt_count",
    },
    "vault": {
        "url": "http://localhost:8106",
        "stats": "/api/stats",
        "list": "/api/receipts",
        "count_field": "total",
    },
    "communique": {
        "url": "http://localhost:8105",
        "stats": "/api/communique/stats",
        "list": "/api/communique/list",
        "count_field": "total",
    },
    "export": {
        "url": "http://localhost:8103",
        "stats": "/health",
        "list": None,
        "count_field": None,
    },
    "pott": {
        "url": "http://localhost:8114",
        "stats": "/api/stats",
        "list": "/api/potts",
        "count_field": "total",
    },
}

# Action #7: Layer 7 Semantic Patterns
SEMANTIC_PATTERNS = {
    # Count queries
    "count": {
        "patterns": [
            r"\b(how many|quantos?|wieviele?|combien|cuántos?)\b",
            r"\b(count|contar|zählen|anzahl|número|numero)\b",
            r"\b(total|gesamt|soma)\b.*\b(receipts?|communiqués?|documents?)\b",
        ],
        "extract": lambda m, t: {"action": "count", "target": extract_target(t)},
    },
    # List queries
    "list": {
        "patterns": [
            r"\b(list|liste|listar|show|zeig|mostra|mostrar)\b",
            r"\b(últimos?|latest|letzte|recent|recentes?)\b",
            r"\b(all|alle|todos|todas)\b.*\b(receipts?|communiqués?)\b",
        ],
        "extract": lambda m, t: {"action": "list", "target": extract_target(t), "limit": extract_limit(t)},
    },
    # Status queries
    "status": {
        "patterns": [
            r"\b(status|estado|zustand|health|saúde|gesundheit)\b",
            r"\b(online|offline|running|rodando|läuft)\b",
            r"\b(services?|serviços?|dienste?)\b",
        ],
        "extract": lambda m, t: {"action": "status", "target": "services"},
    },
    # Specific entity lookup
    "lookup": {
        "patterns": [
            r"\b(find|buscar|finden|search|procurar|suchen)\b",
            r"\b(receipt|communiqué|documento)\b.*\b([A-Z]{2,4}-\d{8}-[A-Z0-9]+)\b",
        ],
        "extract": lambda m, t: {"action": "lookup", "target": extract_target(t), "id": extract_id(t)},
    },
}


# ═══════════════════════════════════════════════════════════════════════════════════
# ACTION #7: LAYER 7 SEMANTIC EXTRACTION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════════

def extract_target(text: str) -> str:
    """Extract the target entity type from natural language."""
    text_lower = text.lower()

    # Map natural language to service targets
    target_map = {
        "ledger": ["ledger", "receipts", "recibos", "quittungen", "receipt", "recibo"],
        "communique": ["communiqué", "communiques", "comunicados", "mitteilungen", "communique"],
        "vault": ["vault", "cofre", "tresor", "archive", "arquivo", "archiv"],
        "pott": ["pott", "potts", "federation", "federação", "föderation"],
        "services": ["services", "serviços", "dienste", "service", "serviço"],
    }

    for target, keywords in target_map.items():
        for kw in keywords:
            if kw in text_lower:
                return target

    return "services"  # Default


def extract_limit(text: str) -> int:
    """Extract numeric limit from text (e.g., 'last 5', 'últimos 10')."""
    # Look for numbers near limit keywords
    match = re.search(r'\b(\d+)\s*(últimos?|latest|letzte|recent|recentes?)\b', text.lower())
    if match:
        return min(int(match.group(1)), 50)  # Cap at 50

    match = re.search(r'\b(últimos?|latest|letzte|recent|recentes?)\s*(\d+)\b', text.lower())
    if match:
        return min(int(match.group(2)), 50)

    # Default limit
    return 5


def extract_id(text: str) -> str:
    """Extract entity ID from text (e.g., 'COM-20260227-ABC123')."""
    match = re.search(r'\b([A-Z]{2,4}-\d{8}-[A-Z0-9]+)\b', text)
    return match.group(1) if match else None


def parse_semantic_query(text: str) -> dict:
    """
    ACTION #7: Parse natural language into structured query.
    Returns semantic interpretation of the query.
    """
    text_lower = text.lower()

    for query_type, config in SEMANTIC_PATTERNS.items():
        for pattern in config["patterns"]:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                return {
                    "type": query_type,
                    "needs_llm": False,  # Action #4: local queries don't need LLM
                    **config["extract"](match, text)
                }

    return {"type": "unknown", "needs_llm": True}


# ═══════════════════════════════════════════════════════════════════════════════════
# CONSTITUTIONAL IDENTITY — Dragon speaks as WINDI (Principle 2)
# ═══════════════════════════════════════════════════════════════════════════════════

DRAGON_IDENTITY = {
    "de": {
        "name": "WINDI",
        "greeting": "Ich bin WINDI. Wie kann ich dir helfen?",
        "suggest_prefix": "Ich schlage vor:",
        "confirm_ask": "Soll ich das ausführen?",
        "confirm_buttons": ["Ja, ausführen", "Nein, nur anzeigen"],
        "executed": "Aktion ausgeführt.",
        "cancelled": "Aktion abgebrochen.",
        "tier_blocked": "Diese Funktion erfordert ein höheres Tier.",
        "closing": "Mensch entscheidet. WINDI beobachtet.",
        "processing": "Verarbeite...",
        "error": "Ein Fehler ist aufgetreten. Bitte versuche es erneut.",
    },
    "en": {
        "name": "WINDI",
        "greeting": "I am WINDI. How can I help you?",
        "suggest_prefix": "I suggest:",
        "confirm_ask": "Should I execute this?",
        "confirm_buttons": ["Yes, execute", "No, just show"],
        "executed": "Action executed.",
        "cancelled": "Action cancelled.",
        "tier_blocked": "This feature requires a higher tier.",
        "closing": "Human decides. WINDI observes.",
        "processing": "Processing...",
        "error": "An error occurred. Please try again.",
    },
    "pt": {
        "name": "WINDI",
        "greeting": "Eu sou WINDI. Como posso ajudar?",
        "suggest_prefix": "Sugiro:",
        "confirm_ask": "Devo executar isto?",
        "confirm_buttons": ["Sim, executar", "Não, apenas mostrar"],
        "executed": "Acção executada.",
        "cancelled": "Acção cancelada.",
        "tier_blocked": "Esta funcionalidade requer um tier superior.",
        "closing": "Humano decide. WINDI observa.",
        "processing": "A processar...",
        "error": "Ocorreu um erro. Tenta novamente.",
    },
    "fr": {
        "name": "WINDI",
        "greeting": "Je suis WINDI. Comment puis-je vous aider?",
        "suggest_prefix": "Je suggère:",
        "confirm_ask": "Dois-je exécuter cela?",
        "confirm_buttons": ["Oui, exécuter", "Non, juste montrer"],
        "executed": "Action exécutée.",
        "cancelled": "Action annulée.",
        "tier_blocked": "Cette fonctionnalité nécessite un niveau supérieur.",
        "closing": "L'humain décide. WINDI observe.",
        "processing": "Traitement...",
        "error": "Une erreur s'est produite. Veuillez réessayer.",
    },
    "es": {
        "name": "WINDI",
        "greeting": "Soy WINDI. ¿Cómo puedo ayudarte?",
        "suggest_prefix": "Sugiero:",
        "confirm_ask": "¿Debo ejecutar esto?",
        "confirm_buttons": ["Sí, ejecutar", "No, solo mostrar"],
        "executed": "Acción ejecutada.",
        "cancelled": "Acción cancelada.",
        "tier_blocked": "Esta funcionalidad requiere un nivel superior.",
        "closing": "El humano decide. WINDI observa.",
        "processing": "Procesando...",
        "error": "Ocurrió un error. Inténtalo de nuevo.",
    },
}

# Action types that require confirmation (Principle 1)
CONFIRMABLE_ACTIONS = [
    "export", "seal", "publish", "delete", "send", "submit",
    "finalize", "execute", "create_did", "register", "commit",
    "create", "generate", "orchestrate"
]

# ═══════════════════════════════════════════════════════════════════════════════════
# LOCAL KNOWLEDGE BASE — Answer questions without LLM
# ═══════════════════════════════════════════════════════════════════════════════════

KNOWLEDGE_BASE = {
    "dignity_id": {
        "keywords": ["dignity id", "dignityid", "dignity-id", "did", "identidade"],
        "de": "**Dignity ID** ist dein souveräner digitaler Identifier im WINDI-Ökosystem. Er basiert auf Ed25519-Kryptografie und UUID v7, ist vollständig anonym bis du ihn mit einer Wallet verbindest, und gehört nur dir — nicht einer Plattform.",
        "en": "**Dignity ID** is your sovereign digital identifier in the WINDI ecosystem. It's based on Ed25519 cryptography and UUID v7, fully anonymous until you link it to a wallet, and belongs only to you — not to any platform.",
        "pt": "**Dignity ID** é o teu identificador digital soberano no ecossistema WINDI. Baseia-se em criptografia Ed25519 e UUID v7, é totalmente anónimo até o ligares a uma wallet, e pertence apenas a ti — não a nenhuma plataforma.",
    },
    "windi": {
        "keywords": ["windi", "o que é windi", "was ist windi", "what is windi"],
        "de": "**WINDI** (Workforce Intelligence & Digital Identity) ist ein Governance-System für dokumentenbasierte Souveränität. Es kombiniert forensische Beweissicherung, KI-gestützte Textanalyse und kryptografische Versiegelung — alles ohne Abhängigkeit von zentralen Plattformen.",
        "en": "**WINDI** (Workforce Intelligence & Digital Identity) is a governance system for document-based sovereignty. It combines forensic evidence preservation, AI-assisted text analysis, and cryptographic sealing — all without dependence on central platforms.",
        "pt": "**WINDI** (Workforce Intelligence & Digital Identity) é um sistema de governança para soberania baseada em documentos. Combina preservação forense de evidências, análise de texto assistida por IA e selagem criptográfica — tudo sem dependência de plataformas centrais.",
    },
    "vault": {
        "keywords": ["vault", "cofre", "tresor", "forensic vault"],
        "de": "**Forensic Vault** ist das Audit-Archiv des WINDI-Systems. Es speichert keine Inhalte — nur kryptografische Hashes und Metadaten. Du behältst die Originale, das System beweist ihre Existenz.",
        "en": "**Forensic Vault** is the audit archive of the WINDI system. It stores no content — only cryptographic hashes and metadata. You keep the originals, the system proves their existence.",
        "pt": "**Forensic Vault** é o arquivo de auditoria do sistema WINDI. Não armazena conteúdos — apenas hashes criptográficos e metadados. Tu guardas os originais, o sistema prova a sua existência.",
    },
    "ledger": {
        "keywords": ["ledger", "forensic ledger", "receipts", "recibos"],
        "de": "**Forensic Ledger** speichert Virtue Receipts — kryptografische Belege jeder Aktion im System. Jeder Receipt hat ID, SHA-256 Hash, Zeitstempel und Governance-Level.",
        "en": "**Forensic Ledger** stores Virtue Receipts — cryptographic proofs of every action in the system. Each receipt has ID, SHA-256 hash, timestamp, and governance level.",
        "pt": "**Forensic Ledger** armazena Virtue Receipts — provas criptográficas de cada acção no sistema. Cada receipt tem ID, hash SHA-256, timestamp e nível de governança.",
    },
    "communique": {
        "keywords": ["communiqué", "communique", "comunicado", "mitteilung"],
        "de": "**Communiqué** ist ein offizielles Dokument im WINDI-System. Es durchläuft DRAFT→REVIEW→PUBLISHED und wird bei Veröffentlichung kryptografisch versiegelt und im Ledger registriert.",
        "en": "**Communiqué** is an official document in the WINDI system. It goes through DRAFT→REVIEW→PUBLISHED and gets cryptographically sealed and registered in the Ledger upon publication.",
        "pt": "**Communiqué** é um documento oficial no sistema WINDI. Passa por DRAFT→REVIEW→PUBLISHED e é selado criptograficamente e registado no Ledger ao ser publicado.",
    },
    "pott": {
        "keywords": ["pott", "federation", "federação", "creator"],
        "de": "**Pott** ist eine Creator-Federation im WINDI-System. Creators erhalten 85% der Einnahmen, die Federation 15%. Daten kreuzen niemals Pott-Grenzen.",
        "en": "**Pott** is a creator federation in the WINDI system. Creators receive 85% of revenue, the federation 15%. Data never crosses Pott boundaries.",
        "pt": "**Pott** é uma federação de creators no sistema WINDI. Creators recebem 85% da receita, a federação 15%. Dados nunca cruzam fronteiras de Pott.",
    },
    "tier": {
        "keywords": ["tier", "tiers", "free", "med", "high", "nível", "stufe"],
        "de": "**Tiers** bestimmen Zugriff: FREE (lokale Templates), MED (Guardian AI), HIGH (Council mit Architect+Witness). Master-Subdomain = HIGH, Admin = MED, WWW = FREE.",
        "en": "**Tiers** determine access: FREE (local templates), MED (Guardian AI), HIGH (Council with Architect+Witness). Master subdomain = HIGH, Admin = MED, WWW = FREE.",
        "pt": "**Tiers** determinam acesso: FREE (templates locais), MED (Guardian AI), HIGH (Council com Architect+Witness). Subdomínio Master = HIGH, Admin = MED, WWW = FREE.",
    },
    "three_dragons": {
        "keywords": ["dragons", "guardian", "architect", "witness", "dragões"],
        "de": "**Three Dragons**: Guardian (Compliance, Risiko), Architect (Kreation, Struktur), Witness (Validierung, Audit). Zusammen bilden sie den Council für HIGH-Tier Entscheidungen.",
        "en": "**Three Dragons**: Guardian (compliance, risk), Architect (creation, structure), Witness (validation, audit). Together they form the Council for HIGH-tier decisions.",
        "pt": "**Three Dragons**: Guardian (compliance, risco), Architect (criação, estrutura), Witness (validação, auditoria). Juntos formam o Council para decisões de tier HIGH.",
    },
}

# Conversational responses for different situations
CONVERSATIONAL_RESPONSES = {
    "de": {
        "understanding": "Verstehe. Lass uns das klären. Was genau möchtest du wissen oder tun?",
        "confused": "Ich bin hier um zu helfen. Frag mich über WINDI-Konzepte, oder sag mir was du erstellen möchtest.",
        "greeting_response": "Hallo! Ich bin WINDI — dein Governance-Assistent. Du kannst mich fragen was Dignity ID ist, den Vault-Status prüfen, oder ein Dokument erstellen.",
        "robotic_complaint": "Du hast recht, das war robotisch. Lass uns konkret werden — was brauchst du gerade?",
        "capability": "Ich kann: Fragen über WINDI beantworten, Service-Status zeigen, Dokumente erstellen (MED/HIGH tier), und dich durch Governance führen.",
    },
    "en": {
        "understanding": "I see. Let's clarify that. What exactly would you like to know or do?",
        "confused": "I'm here to help. Ask me about WINDI concepts, or tell me what you'd like to create.",
        "greeting_response": "Hello! I'm WINDI — your governance assistant. You can ask me what Dignity ID is, check Vault status, or create a document.",
        "robotic_complaint": "You're right, that was robotic. Let's be concrete — what do you need right now?",
        "capability": "I can: answer questions about WINDI, show service status, create documents (MED/HIGH tier), and guide you through governance.",
    },
    "pt": {
        "understanding": "Percebo. Vamos esclarecer isso. O que exactamente queres saber ou fazer?",
        "confused": "Estou aqui para ajudar. Pergunta-me sobre conceitos WINDI, ou diz-me o que queres criar.",
        "greeting_response": "Olá! Sou o WINDI — o teu assistente de governança. Podes perguntar-me o que é Dignity ID, verificar o estado do Vault, ou criar um documento.",
        "robotic_complaint": "Tens razão, isso foi robótico. Vamos ser concretos — o que precisas agora?",
        "capability": "Posso: responder a perguntas sobre WINDI, mostrar estado dos serviços, criar documentos (tier MED/HIGH), e guiar-te pela governança.",
    },
}


def search_knowledge_base(text: str, lang: str) -> str:
    """Search local knowledge base for answers."""
    text_lower = text.lower()

    for concept, data in KNOWLEDGE_BASE.items():
        for keyword in data["keywords"]:
            if keyword in text_lower:
                return data.get(lang, data.get("en", ""))

    return None


def get_cognitive_insights(text: str, lang: str) -> str:
    """
    Get cognitive insights when user asks for them.

    This is the CIL in action — revealing the 93% that was hidden.
    """
    if not CIL_AVAILABLE:
        return None

    text_lower = text.lower()

    # Patterns that trigger cognitive insights
    insight_patterns = [
        "insight", "einsicht", "percepção",
        "recommendation", "empfehlung", "recomendação",
        "o que devo", "what should i", "was soll ich",
        "próximo passo", "next step", "nächster schritt",
        "o que achas", "what do you think", "was denkst du",
        "como estou", "how am i doing", "wie mache ich",
        "analisa", "analyze", "analysiere",
        "suggest", "sugere", "schlage vor",
    ]

    if any(pattern in text_lower for pattern in insight_patterns):
        try:
            cil = CognitiveInterface(lang)
            summary = cil.get_cognitive_summary()

            # Build response with top insights
            lines = []

            # Add top 2 insights
            for insight in summary.get("insights", [])[:2]:
                lines.append(insight.get("text", ""))

            # Add top recommendation
            if summary.get("top_recommendation"):
                lines.append("")
                lines.append(summary["top_recommendation"].get("text", ""))

            return "\n\n".join(lines)
        except Exception as e:
            return None

    return None


def get_proactive_insight(lang: str, high_impact: bool = True) -> str:
    """
    Get a proactive insight to share when the conversation is stale.

    This is what makes the Dragon feel intelligent — it speaks without being asked.

    If high_impact=True, returns the most transformational insight (Audience Core).
    """
    if not CIL_AVAILABLE:
        return None

    try:
        cil = CognitiveInterface(lang)

        if high_impact:
            # Get the most powerful insight — Audience Core
            insights = cil.insight_generator.generate_high_impact_insights()
            if insights:
                return insights[0].get("text")

        # Fallback to standard proactive message
        return get_proactive_message(lang)
    except:
        return None


def get_transformational_phrase(lang: str) -> str:
    """
    Get the phrase that stays in the mind:

    "Não precisas de mais seguidores.
     Precisas de reconhecer os que já mudam o teu mundo."
    """
    if not CIL_AVAILABLE:
        return None

    try:
        cil = CognitiveInterface(lang)
        return cil.insight_generator.get_transformational_phrase()
    except:
        return None


def get_conversational_response(text: str, lang: str, session: dict) -> str:
    """Generate contextual conversational response instead of robotic greeting."""
    text_lower = text.lower()
    responses = CONVERSATIONAL_RESPONSES.get(lang, CONVERSATIONAL_RESPONSES["en"])
    history = session.get("messages", [])

    # Detect complaint about robotic behavior
    robotic_complaints = ["robotizado", "robotic", "roboter", "mesmo", "same", "gleiche", "loop", "repetindo", "repetitivo"]
    if any(word in text_lower for word in robotic_complaints):
        return responses["robotic_complaint"]

    # Detect "help me use" patterns — most common help request
    help_use_patterns = [
        "me ajud",  # me ajude, me ajuda, me ajudar
        "ajuda-me", "ajude-me",
        "help me", "help us",
        "hilf mir", "helfen sie",
        "como usar", "how to use", "wie benutze",
        "como funciona", "how does it work", "wie funktioniert",
        "aproveitar", "utilizar",
        "como posso", "how can i", "wie kann ich",
    ]
    if any(pattern in text_lower for pattern in help_use_patterns):
        return responses["capability"]

    # Detect request for understanding
    understanding_words = ["entender", "understand", "verstehen", "precisamos", "need to"]
    if any(word in text_lower for word in understanding_words):
        return responses["understanding"]

    # Detect capability question
    capability_words = ["o que podes", "what can you", "was kannst", "o que fazes", "what do you do", "was machst"]
    if any(word in text_lower for word in capability_words):
        return responses["capability"]

    # Detect question marks with short messages (likely needs help)
    if "?" in text and len(text) < 50:
        # Short question, give helpful response instead of greeting
        message_count = len([m for m in history if m.get("role") == "user"])
        if message_count > 0:
            # Not first message, be helpful
            return responses["confused"]

    # If there was a previous greeting, don't repeat it
    if len(history) > 0:
        last_assistant = [m for m in history if m.get("role") == "assistant"]
        if last_assistant:
            last_response = last_assistant[-1].get("content", "")
            identity = DRAGON_IDENTITY.get(lang, DRAGON_IDENTITY["de"])
            if identity["greeting"] in last_response:
                # Already greeted, give different response
                return responses["confused"]

    return None  # Use default greeting only for first interaction


# ═══════════════════════════════════════════════════════════════════════════════════
# ACTION #2: LANGUAGE DETECTION — Using guardian-local
# ═══════════════════════════════════════════════════════════════════════════════════

def detect_language(text: str) -> tuple:
    """
    Detect language using guardian-local's robust detector.
    Returns (lang_code, confidence).
    """
    if guardian_detect_language:
        return guardian_detect_language(text)

    # Fallback: simple pattern matching (degraded mode)
    text_lower = text.lower()
    patterns = {
        "de": r"\b(ich|du|wir|ist|und|der|die|das|ein|eine|nicht|haben|sein|möchte|brauche)\b",
        "pt": r"\b(eu|tu|nós|está|e|o|a|um|uma|não|ter|ser|quero|preciso|olá|obrigado)\b",
        "en": r"\b(i|you|we|is|and|the|a|an|not|have|be|want|need|hello|thanks)\b",
        "fr": r"\b(je|tu|nous|est|et|le|la|un|une|ne|pas|avoir|être|veux|merci)\b",
        "es": r"\b(yo|tú|nosotros|es|y|el|la|un|una|no|tener|ser|quiero|gracias)\b",
    }

    scores = {}
    for lang, pattern in patterns.items():
        matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
        scores[lang] = matches

    if not scores or max(scores.values()) == 0:
        return "de", 0.3  # Default: German

    best = max(scores, key=scores.get)
    confidence = min(scores[best] / max(len(text.split()), 1) * 2, 0.95)
    return best, round(confidence, 2)


# ═══════════════════════════════════════════════════════════════════════════════════
# ACTION #4: INTENT CLASSIFICATION WITH needs_llm SWITCH
# Route chat vs query vs action — minimize LLM calls for local-resolvable queries
# ═══════════════════════════════════════════════════════════════════════════════════

def classify_intent(text: str, lang: str) -> dict:
    """
    Classify user intent with smart needs_llm routing (Action #4).

    The key insight: many queries can be resolved locally by querying
    WINDI services directly, without needing LLM processing.

    Returns:
        {
            "type": "chat" | "query" | "create" | "action",
            "needs_orchestrator": bool,
            "needs_llm": bool,  # Action #4: smart LLM switch
            "needs_confirmation": bool,
            "semantic": {...},  # Action #7: Layer 7 parsed data
            "details": {...}
        }
    """
    text_lower = text.lower()

    # ─── Action #7: Try Layer 7 semantic parsing first ────────────────────
    semantic = parse_semantic_query(text)

    if semantic["type"] != "unknown":
        # Local query detected — no LLM needed!
        return {
            "type": "query",
            "needs_orchestrator": False,
            "needs_llm": False,  # Action #4: route locally
            "needs_confirmation": False,
            "semantic": semantic,
            "details": {"query_type": semantic["action"], "target": semantic.get("target")}
        }

    # ─── Use IntentParser for create detection ────────────────────────────
    if INTENT_PARSER_AVAILABLE and parse_intent:
        intent = parse_intent(text)
        if intent.get("has_create_intent"):
            return {
                "type": "create",
                "needs_orchestrator": True,
                "needs_llm": True,  # Creation needs LLM
                "needs_confirmation": True,
                "semantic": {"type": "create", "needs_llm": True},
                "details": intent
            }

    # ─── Fallback: keyword-based classification ───────────────────────────

    # Query patterns (local resolution, no LLM)
    query_patterns = [
        r"\b(status|health|how many|quantos|wieviele|count|stats)\b",
        r"\b(what is|was ist|o que é|wie viel|quanto)\b.*\b(ledger|vault|communiqué|pott)\b",
        r"\b(show me|zeig mir|mostra-me|list|liste)\b",
    ]
    for pattern in query_patterns:
        if re.search(pattern, text_lower):
            return {
                "type": "query",
                "needs_orchestrator": False,
                "needs_llm": False,  # Action #4: local query
                "needs_confirmation": False,
                "semantic": {"type": "status", "action": "status", "target": "services"},
                "details": {"query_type": "status"}
            }

    # Create/action patterns (needs orchestrator + LLM)
    # Include both infinitive (criar) and imperative (cria) forms
    action_patterns = [
        r"\b(create|erstell[et]?n?|cria[r]?|make|mach[et]?n?|fa[zç][ae]?[r]?)\b",
        r"\b(generat[e]?|generier[et]?n?|ger[ae][r]?|writ[e]?|schreib[et]?n?|escrev[ae][r]?)\b",
        r"\b(publish|veröffentlich[et]?n?|public[ao][r]?|seal|versiegl[et]?n?|sel[ao][r]?)\b",
        r"\b(export|exportier[et]?n?|export[ao][r]?|send|send[et]?n?|envi[ao][r]?)\b",
        r"\b(analyz[e]?|analysier[et]?n?|analis[ae][r]?|summariz[e]?|zusammenfass[et]?n?|resum[ie][r]?)\b",
        r"\b(rascunho|draft|entwurf|brief|carta|letter)\b",  # Document type triggers
    ]
    for pattern in action_patterns:
        if re.search(pattern, text_lower):
            return {
                "type": "action",
                "needs_orchestrator": True,
                "needs_llm": True,  # Action #4: creation needs LLM
                "needs_confirmation": True,
                "semantic": {"type": "action", "needs_llm": True},
                "details": {"action_detected": pattern}
            }

    # ─── Conversational patterns (may need LLM for complex questions) ─────
    complex_question_patterns = [
        r"\b(explain|explique|erkläre|why|porque|warum|how does|como funciona)\b",
        r"\b(what should|was soll|o que devo|recommend|empfehle|recomenda)\b",
        r"\b(compare|comparar|vergleiche|difference|diferença|unterschied)\b",
    ]
    for pattern in complex_question_patterns:
        if re.search(pattern, text_lower):
            return {
                "type": "chat",
                "needs_orchestrator": True,  # Complex questions need LLM
                "needs_llm": True,
                "needs_confirmation": False,
                "semantic": {"type": "complex_question", "needs_llm": True},
                "details": {"question_type": "complex"}
            }

    # Default: simple chat (local response, no LLM)
    return {
        "type": "chat",
        "needs_orchestrator": False,
        "needs_llm": False,  # Simple greetings don't need LLM
        "needs_confirmation": False,
        "semantic": {"type": "chat", "needs_llm": False},
        "details": {}
    }


# ═══════════════════════════════════════════════════════════════════════════════════
# ACTION #1: ORCHESTRATOR INTEGRATION — Backend execution
# ═══════════════════════════════════════════════════════════════════════════════════

def query_orchestrator(prompt: str, tier: str, lang: str, mode: str = "generate") -> dict:
    """
    Query the WINDI Orchestrator for content generation.

    Args:
        prompt: User's message
        tier: FREE/MED/HIGH
        lang: Detected language code
        mode: "generate" (content only) or "orchestrate" (full pipeline)

    Returns:
        {success: bool, response: str, source: str, ...}
    """
    # FREE tier: no orchestrator access
    if tier == "FREE":
        identity = DRAGON_IDENTITY.get(lang, DRAGON_IDENTITY["de"])
        return {
            "success": True,
            "response": identity["tier_blocked"],
            "source": "local",
            "tier_blocked": True
        }

    # Build request
    endpoint = f"{ORCHESTRATOR_URL}/{mode}"
    payload = {
        "prompt": prompt,
        "language": lang,
        "tenant_id": "palette",  # Multi-tenant context
    }

    # HIGH tier: full pipeline with I9 gate
    if tier == "HIGH" and mode == "orchestrate":
        payload["human_ack"] = "DRAFT_ONLY"  # Respect I9: human approves

    try:
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())

            # Extract response text based on response structure
            response_text = None

            # /generate returns content directly
            if "content" in result:
                content = result["content"]
                if isinstance(content, dict):
                    response_text = content.get(f"body_{lang}") or content.get("body_en") or content.get("body_de")
                else:
                    response_text = str(content)

            # /orchestrate returns structured result with dragon_result
            elif "dragon_result" in result:
                dr = result["dragon_result"]
                response_text = dr.get(f"body_{lang}") or dr.get("body_en") or dr.get("summary", "")

            # /orchestrate full pipeline returns steps + status
            elif "steps" in result and "status" in result:
                status = result.get("status", "")
                steps = result.get("steps", {})
                arch = steps.get("architect", {})
                com_id = result.get("com_id", "")

                # Build user-friendly response
                if status == "DRAFT_CREATED" and com_id:
                    title = arch.get("title", "Document")
                    templates = {
                        "de": f"📝 **Entwurf erstellt**: {title}\n\n`{com_id}` wartet auf deine Genehmigung.\n\nNächste Schritte:\n- Prüfen und bearbeiten\n- Zur Veröffentlichung freigeben",
                        "en": f"📝 **Draft created**: {title}\n\n`{com_id}` awaits your approval.\n\nNext steps:\n- Review and edit\n- Approve for publication",
                        "pt": f"📝 **Rascunho criado**: {title}\n\n`{com_id}` aguarda a tua aprovação.\n\nPróximos passos:\n- Rever e editar\n- Aprovar para publicação",
                    }
                    response_text = templates.get(lang, templates["en"])
                elif arch.get("summary"):
                    response_text = arch.get("summary")
                else:
                    response_text = f"Status: {status}"

            # Direct body fields (from /generate trilingual)
            elif f"body_{lang}" in result:
                response_text = result[f"body_{lang}"]
            elif "body_en" in result:
                response_text = result["body_en"]
            elif "body_de" in result:
                response_text = result["body_de"]

            # Fallback
            if not response_text:
                response_text = result.get("message", result.get("summary", ""))

            # Sanitize: remove any brand names (Principle 2)
            response_text = sanitize_response(response_text)

            return {
                "success": True,
                "response": response_text,
                "source": "orchestrator",
                "mode": mode,
                "raw": result
            }

    except urllib.error.URLError as e:
        return {
            "success": False,
            "response": DRAGON_IDENTITY.get(lang, DRAGON_IDENTITY["de"])["error"],
            "source": "local",
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "response": DRAGON_IDENTITY.get(lang, DRAGON_IDENTITY["de"])["error"],
            "source": "local",
            "error": str(e)
        }


def sanitize_response(text: str) -> str:
    """Remove AI brand names from response (Principle 2)."""
    if not text:
        return text

    replacements = [
        (r"\bClaude\b", "WINDI"),
        (r"\bGPT-?\d*\b", "WINDI"),
        (r"\bGemini\b", "WINDI"),
        (r"\bOpenAI\b", "WINDI"),
        (r"\bAnthropic\b", "WINDI"),
        (r"\bGoogle AI\b", "WINDI"),
        (r"\bI am an AI\b", "I am WINDI"),
        (r"\bIch bin eine KI\b", "Ich bin WINDI"),
        (r"\bSou uma IA\b", "Eu sou WINDI"),
        (r"\bas an AI assistant\b", ""),
        (r"\bals KI-Assistent\b", ""),
        (r"\bcomo assistente de IA\b", ""),
    ]

    result = text
    for pattern, replacement in replacements:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result.strip()


# ═══════════════════════════════════════════════════════════════════════════════════
# ACTION #5: LOCAL QUERY HANDLERS — Direct service queries without orchestrator
# ═══════════════════════════════════════════════════════════════════════════════════

# Trilingual response templates for local queries
LOCAL_QUERY_TEMPLATES = {
    "de": {
        "ledger_count": "📊 Forensic Ledger: **{count}** Einträge registriert",
        "ledger_list": "📋 Letzte {limit} Einträge im Ledger:\n{items}",
        "vault_count": "🏛️ Forensic Vault: **{count}** Dokumente archiviert",
        "vault_list": "📋 Letzte {limit} Dokumente im Vault:\n{items}",
        "communique_count": "📣 Communiqué Engine: **{count}** Mitteilungen ({published} publiziert)",
        "communique_list": "📋 Letzte {limit} Communiqués:\n{items}",
        "pott_count": "🎨 Pott Federation: **{count}** Potts aktiv",
        "services": "🔧 {online}/{total} Dienste online",
        "services_detail": "🔧 Dienststatus:\n{details}",
        "lookup_found": "🔍 Gefunden: {type} **{id}**\n{details}",
        "lookup_not_found": "🔍 Nicht gefunden: {id}",
        "unknown": "Diese Abfrage kann ich lokal nicht beantworten.",
        "error": "Fehler beim Abfragen von {service}: {error}",
    },
    "en": {
        "ledger_count": "📊 Forensic Ledger: **{count}** entries registered",
        "ledger_list": "📋 Last {limit} Ledger entries:\n{items}",
        "vault_count": "🏛️ Forensic Vault: **{count}** documents archived",
        "vault_list": "📋 Last {limit} Vault documents:\n{items}",
        "communique_count": "📣 Communiqué Engine: **{count}** communiqués ({published} published)",
        "communique_list": "📋 Last {limit} Communiqués:\n{items}",
        "pott_count": "🎨 Pott Federation: **{count}** Potts active",
        "services": "🔧 {online}/{total} services online",
        "services_detail": "🔧 Service status:\n{details}",
        "lookup_found": "🔍 Found: {type} **{id}**\n{details}",
        "lookup_not_found": "🔍 Not found: {id}",
        "unknown": "I cannot answer this query locally.",
        "error": "Error querying {service}: {error}",
    },
    "pt": {
        "ledger_count": "📊 Forensic Ledger: **{count}** entradas registadas",
        "ledger_list": "📋 Últimas {limit} entradas no Ledger:\n{items}",
        "vault_count": "🏛️ Forensic Vault: **{count}** documentos arquivados",
        "vault_list": "📋 Últimos {limit} documentos no Vault:\n{items}",
        "communique_count": "📣 Communiqué Engine: **{count}** comunicados ({published} publicados)",
        "communique_list": "📋 Últimos {limit} Communiqués:\n{items}",
        "pott_count": "🎨 Pott Federation: **{count}** Potts activos",
        "services": "🔧 {online}/{total} serviços online",
        "services_detail": "🔧 Estado dos serviços:\n{details}",
        "lookup_found": "🔍 Encontrado: {type} **{id}**\n{details}",
        "lookup_not_found": "🔍 Não encontrado: {id}",
        "unknown": "Não consigo responder a esta consulta localmente.",
        "error": "Erro ao consultar {service}: {error}",
    },
}


def query_service(service: str, endpoint: str, timeout: float = 3.0) -> dict:
    """Query a WINDI service endpoint and return JSON response."""
    config = SERVICE_ENDPOINTS.get(service, {})
    if not config:
        return {"error": f"Unknown service: {service}"}

    url = f"{config['url']}{endpoint}"
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode())
            return {"error": f"HTTP {resp.status}"}
    except urllib.error.URLError as e:
        return {"error": str(e.reason)}
    except Exception as e:
        return {"error": str(e)}


def handle_local_query(semantic: dict, lang: str) -> str:
    """
    ACTION #5: Handle queries by directly querying WINDI services.

    Args:
        semantic: Parsed semantic query from Layer 7
        lang: User's language code

    Returns:
        Formatted response string in user's language
    """
    templates = LOCAL_QUERY_TEMPLATES.get(lang, LOCAL_QUERY_TEMPLATES["en"])
    action = semantic.get("action", "status")
    target = semantic.get("target", "services")

    # ─── STATUS: Service health check ─────────────────────────────────────
    if action == "status":
        online = 0
        total = len(SERVICE_ENDPOINTS)
        details = []

        for name, config in SERVICE_ENDPOINTS.items():
            try:
                req = urllib.request.Request(f"{config['url']}/health", method="GET")
                with urllib.request.urlopen(req, timeout=2) as resp:
                    if resp.status == 200:
                        online += 1
                        details.append(f"  ✅ {name}: online")
                    else:
                        details.append(f"  ❌ {name}: HTTP {resp.status}")
            except Exception as e:
                details.append(f"  ❌ {name}: offline")

        if semantic.get("verbose"):
            return templates["services_detail"].format(details="\n".join(details))
        return templates["services"].format(online=online, total=total)

    # ─── COUNT: Get totals from services ──────────────────────────────────
    if action == "count":
        if target == "ledger":
            result = query_service("ledger", "/health")
            if "error" not in result:
                count = result.get("receipt_count", 0)
                return templates["ledger_count"].format(count=count)

        elif target == "vault":
            result = query_service("vault", "/api/stats")
            if "error" not in result:
                count = result.get("total", 0)
                return templates["vault_count"].format(count=count)

        elif target == "communique":
            result = query_service("communique", "/api/communique/stats")
            if "error" not in result:
                count = result.get("total", 0)
                published = result.get("by_status", {}).get("PUBLISHED", 0)
                return templates["communique_count"].format(count=count, published=published)

        elif target == "pott":
            result = query_service("pott", "/api/stats")
            if "error" not in result:
                count = result.get("total", 0)
                return templates["pott_count"].format(count=count)

        return templates["services"].format(online="?", total=len(SERVICE_ENDPOINTS))

    # ─── LIST: Get recent items from services ─────────────────────────────
    if action == "list":
        limit = semantic.get("limit", 5)

        if target == "ledger":
            result = query_service("ledger", f"/api/receipts?limit={limit}")
            if "error" not in result and "receipts" in result:
                items = []
                for r in result["receipts"][:limit]:
                    items.append(f"  • `{r.get('id', '?')}` — {r.get('doc_name', 'untitled')[:40]}")
                return templates["ledger_list"].format(limit=limit, items="\n".join(items) or "  (none)")

        elif target == "vault":
            result = query_service("vault", f"/api/receipts?per_page={limit}")
            if "error" not in result and "receipts" in result:
                items = []
                for r in result["receipts"][:limit]:
                    items.append(f"  • `{r.get('id', '?')}` — {r.get('doc_name', 'untitled')[:40]}")
                return templates["vault_list"].format(limit=limit, items="\n".join(items) or "  (none)")

        elif target == "communique":
            result = query_service("communique", f"/api/communique/list?limit={limit}")
            if "error" not in result and "communiques" in result:
                items = []
                for c in result["communiques"][:limit]:
                    status_icon = "✅" if c.get("status") == "PUBLISHED" else "📝"
                    items.append(f"  {status_icon} `{c.get('id', '?')}` — {c.get('title_de', c.get('title_en', 'untitled'))[:40]}")
                return templates["communique_list"].format(limit=limit, items="\n".join(items) or "  (none)")

        return templates["unknown"]

    # ─── LOOKUP: Find specific entity by ID ───────────────────────────────
    if action == "lookup":
        entity_id = semantic.get("id")
        if not entity_id:
            return templates["unknown"]

        # Try to determine service from ID prefix
        if entity_id.startswith("COM-"):
            result = query_service("communique", f"/api/communique/{entity_id}")
        elif entity_id.startswith("JMPG-") or entity_id.startswith("VR-"):
            result = query_service("ledger", f"/api/receipts/{entity_id}")
        else:
            # Try ledger first, then communique
            result = query_service("ledger", f"/api/receipts/{entity_id}")
            if "error" in result:
                result = query_service("communique", f"/api/communique/{entity_id}")

        if "error" not in result:
            details = json.dumps(result, indent=2, ensure_ascii=False)[:500]
            return templates["lookup_found"].format(type=target, id=entity_id, details=f"```json\n{details}\n```")

        return templates["lookup_not_found"].format(id=entity_id)

    return templates["unknown"]


# ═══════════════════════════════════════════════════════════════════════════════════
# SESSION MANAGEMENT (Principle 3: no surveillance)
# ═══════════════════════════════════════════════════════════════════════════════════

def get_session(session_id: str, tier: str = None) -> dict:
    """Get or create ephemeral session."""
    now = time.time()

    # Clean expired sessions
    expired = [sid for sid, s in SESSIONS.items() if now - s.get("created_at", 0) > SESSION_TTL]
    for sid in expired:
        del SESSIONS[sid]

    if session_id not in SESSIONS:
        SESSIONS[session_id] = {
            "messages": [],
            "lang": None,  # Will be set on first message
            "lang_confidence": 0,
            "tier": tier or "FREE",
            "created_at": now,
            "pending_action": None,
        }
    elif tier:
        SESSIONS[session_id]["tier"] = tier

    return SESSIONS[session_id]


def add_message(session: dict, role: str, content: str, metadata: dict = None):
    """Add message to session (capped at MAX_SESSION_MESSAGES)."""
    session["messages"].append({
        "role": role,
        "content": content,
        "metadata": metadata or {},
        "ts": datetime.utcnow().isoformat()
    })

    if len(session["messages"]) > MAX_SESSION_MESSAGES:
        session["messages"] = session["messages"][-MAX_SESSION_MESSAGES:]


# ═══════════════════════════════════════════════════════════════════════════════════
# MAIN CHAT HANDLER — The "descosida boca"
# ═══════════════════════════════════════════════════════════════════════════════════

def process_chat(message: str, session: dict) -> dict:
    """
    Process a chat message through the intelligence pipeline.

    Flow:
    1. Detect language (Action #2)
    2. Classify intent
    3. Route: local query OR orchestrator
    4. Apply constitutional principles
    5. Return response
    """
    tier = session.get("tier", "FREE")

    # ─── Action #2: Language Detection ─────────────────────────────────
    # Detect on first message, then lock for session consistency
    if session.get("lang") is None or session.get("lang_confidence", 0) < 0.5:
        lang, confidence = detect_language(message)
        session["lang"] = lang
        session["lang_confidence"] = confidence
    else:
        lang = session["lang"]
        confidence = session["lang_confidence"]

    identity = DRAGON_IDENTITY.get(lang, DRAGON_IDENTITY["de"])

    # ─── Intent Classification (with Action #4 needs_llm + Action #7 semantics) ───
    intent = classify_intent(message, lang)
    semantic = intent.get("semantic", {})

    # ─── Routing Decision (Actions #3, #4, #5) ────────────────────────────
    #
    # Action #4: needs_llm switch
    #   - If needs_llm=False → resolve locally (Action #5)
    #   - If needs_llm=True → route to Orchestrator (Action #1)
    #
    # Action #3: Tier-aware routing
    #   - FREE: local only, no orchestrator
    #   - MED: orchestrator /generate
    #   - HIGH: orchestrator /orchestrate
    #

    # ─── FIRST: Check Knowledge Base for concept questions ─────────────
    # Questions like "O que é Dignity ID?" should be answered from local knowledge
    kb_answer = search_knowledge_base(message, lang)
    if kb_answer:
        response_text = kb_answer
        source = "knowledge_base"
        needs_confirmation = False

    # ─── COGNITIVE INTERFACE LAYER: Check for insight requests ────────
    # "What should I do?" → CIL reveals cognition
    elif CIL_AVAILABLE:
        cil_response = get_cognitive_insights(message, lang)
        if cil_response:
            response_text = cil_response
            source = "cognitive_interface"
            needs_confirmation = False
        else:
            # Continue to other handlers
            cil_response = None

    if not kb_answer and (not CIL_AVAILABLE or not cil_response):
        if intent["type"] == "query" and not intent.get("needs_llm", True):
            # ─── Action #5: Local query — direct service access ───────────────
            response_text = handle_local_query(semantic, lang)
            source = "local"
            needs_confirmation = False

        elif intent.get("needs_orchestrator") or intent.get("needs_llm"):
            # ─── Actions #1 + #3: LLM needed — route via Orchestrator ─────────
            if tier == "FREE":
                # FREE tier: try proactive insight instead of tier block
                proactive = get_proactive_insight(lang) if CIL_AVAILABLE else None
                if proactive:
                    response_text = proactive
                    source = "cognitive_interface"
                else:
                    response_text = identity["tier_blocked"]
                    source = "local"
                needs_confirmation = False
            else:
                # MED: generate only, HIGH: full orchestrate
                mode = "orchestrate" if tier == "HIGH" else "generate"
                result = query_orchestrator(message, tier, lang, mode)
                response_text = result.get("response", identity["error"])
                source = result.get("source", "local")
                needs_confirmation = intent.get("needs_confirmation", False) and result.get("success", False)
        else:
            # ─── Conversational chat: intelligent response, NOT robotic ───────
            # Try proactive insight first (reveals cognition!)
            proactive = get_proactive_insight(lang) if CIL_AVAILABLE else None
            conversational = get_conversational_response(message, lang, session)

            if conversational:
                response_text = conversational
                # Append a proactive insight if available
                if proactive and len(session.get("messages", [])) > 1:
                    response_text = f"{conversational}\n\n{proactive}"
                    source = "cognitive_interface"
                else:
                    source = "local"
            elif proactive:
                # Use proactive insight instead of greeting
                response_text = proactive
                source = "cognitive_interface"
            else:
                # First interaction: use greeting
                response_text = identity["greeting"]
                source = "local"
            needs_confirmation = False

    # ─── Constitutional Closing ────────────────────────────────────────
    # Don't append closing if it's already there or if it's a short response
    if len(response_text) > 50 and identity["closing"] not in response_text:
        response_text = f"{response_text}\n\n_{identity['closing']}_"

    # ─── Build Response ────────────────────────────────────────────────
    add_message(session, "user", message)
    add_message(session, "assistant", response_text, {"source": source, "intent": intent["type"]})

    result = {
        "success": True,
        "response": response_text,
        "lang": lang,
        "lang_confidence": confidence,
        "lang_source": LANG_DETECT_SOURCE,
        "tier": tier,
        "source": source,
        "intent_type": intent["type"],
        "action_pending": needs_confirmation,
    }

    if needs_confirmation:
        session["pending_action"] = intent
        result["confirm_buttons"] = identity["confirm_buttons"]

    return result


# ═══════════════════════════════════════════════════════════════════════════════════
# DISTRIBUTION LAYER — Send sealed documents via multiple channels
# ═══════════════════════════════════════════════════════════════════════════════════

def send_email(to: str, subject: str, body: str, html: bool = True) -> dict:
    """
    Send email via SMTP.

    Returns:
        {"success": True/False, "message": "...", "channel": "email"}
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = SMTP_FROM
        msg["To"] = to
        msg["Subject"] = subject

        if html:
            msg.attach(MIMEText(body, "html", "utf-8"))
        else:
            msg.attach(MIMEText(body, "plain", "utf-8"))

        if SMTP_PORT == 465:
            import ssl
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context)
        elif SMTP_USE_TLS:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.starttls()
        else:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)

        if SMTP_USER:
            server.login(SMTP_USER, SMTP_PASS)

        server.sendmail(SMTP_FROM, [to], msg.as_string())
        server.quit()

        log_entry = {
            "channel": "email",
            "to": to,
            "subject": subject,
            "timestamp": datetime.now().isoformat(),
            "success": True,
        }
        DISTRIBUTION_LOG.append(log_entry)

        return {"success": True, "message": f"Email sent to {to}", "channel": "email"}
    except Exception as e:
        log_entry = {
            "channel": "email",
            "to": to,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "success": False,
        }
        DISTRIBUTION_LOG.append(log_entry)
        return {"success": False, "message": f"Email failed: {e}", "channel": "email"}


def send_sms(to: str, message: str) -> dict:
    """
    Send SMS via Twilio.

    Returns:
        {"success": True/False, "message": "...", "channel": "sms"}
    """
    if not TWILIO_SID or not TWILIO_TOKEN or not TWILIO_FROM:
        return {"success": False, "message": "Twilio not configured", "channel": "sms"}

    try:
        # Twilio REST API call
        import base64
        auth = base64.b64encode(f"{TWILIO_SID}:{TWILIO_TOKEN}".encode()).decode()

        data = urllib.parse.urlencode({
            "To": to,
            "From": TWILIO_FROM,
            "Body": message[:1600],  # SMS limit
        }).encode()

        req = urllib.request.Request(
            f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json",
            data=data,
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())

        log_entry = {
            "channel": "sms",
            "to": to,
            "sid": result.get("sid"),
            "timestamp": datetime.now().isoformat(),
            "success": True,
        }
        DISTRIBUTION_LOG.append(log_entry)

        return {"success": True, "message": f"SMS sent to {to}", "channel": "sms", "sid": result.get("sid")}
    except Exception as e:
        log_entry = {
            "channel": "sms",
            "to": to,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "success": False,
        }
        DISTRIBUTION_LOG.append(log_entry)
        return {"success": False, "message": f"SMS failed: {e}", "channel": "sms"}


def send_whatsapp(to: str, message: str) -> dict:
    """
    Send WhatsApp message via WhatsApp Business API.

    Returns:
        {"success": True/False, "message": "...", "channel": "whatsapp"}
    """
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_ID:
        return {"success": False, "message": "WhatsApp not configured", "channel": "whatsapp"}

    try:
        data = json.dumps({
            "messaging_product": "whatsapp",
            "to": to.replace("+", "").replace(" ", ""),
            "type": "text",
            "text": {"body": message},
        }).encode()

        req = urllib.request.Request(
            f"https://graph.facebook.com/v17.0/{WHATSAPP_PHONE_ID}/messages",
            data=data,
            headers={
                "Authorization": f"Bearer {WHATSAPP_TOKEN}",
                "Content-Type": "application/json",
            },
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())

        log_entry = {
            "channel": "whatsapp",
            "to": to,
            "message_id": result.get("messages", [{}])[0].get("id"),
            "timestamp": datetime.now().isoformat(),
            "success": True,
        }
        DISTRIBUTION_LOG.append(log_entry)

        return {"success": True, "message": f"WhatsApp sent to {to}", "channel": "whatsapp"}
    except Exception as e:
        log_entry = {
            "channel": "whatsapp",
            "to": to,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "success": False,
        }
        DISTRIBUTION_LOG.append(log_entry)
        return {"success": False, "message": f"WhatsApp failed: {e}", "channel": "whatsapp"}


# ═══════════════════════════════════════════════════════════════════════════════════
# WHATSAPP MEDIA LAYER v1.0.0 — Images, Videos, Documents, Stickers
# Added: 2026-03-08 | Meta Graph API v17.0
# ═══════════════════════════════════════════════════════════════════════════════════

WHATSAPP_GRAPH_URL = "https://graph.facebook.com/v17.0"
LEDGER_URL_INTERNAL = "http://127.0.0.1:8101"


# ═══════════════════════════════════════════════════════════════════════════════════
# PATCH v1.1.0 — BSUID Ready (Meta username transition June 2026)
# Supports: E.164 phone | BSUID (DE_abc123...) | @username
# Added: 2026-03-08
# ═══════════════════════════════════════════════════════════════════════════════════

def detect_wa_id_type(recipient: str) -> dict:
    """
    Automatically detect WhatsApp identifier type.
    Returns {"type": "phone"|"bsuid"|"username", "value": ..., "country": ...}

    Formats:
    - phone:    +49151234567 (E.164)
    - bsuid:    DE_abc123xyz... (2-letter country + underscore + 10-128 alphanumeric)
    - username: @joberdragon (starts with @)
    """
    r = recipient.strip()

    # E.164 phone number: starts with + followed by 7-15 digits
    if re.match(r'^\+\d{7,15}$', r):
        return {"type": "phone", "value": r, "country": None}

    # BSUID format: 2-letter country code + underscore + 10-128 alphanumeric
    bsuid_match = re.match(r'^([A-Z]{2})_([A-Za-z0-9]{10,128})$', r)
    if bsuid_match:
        return {"type": "bsuid", "value": r, "country": bsuid_match.group(1)}

    # Username handle: starts with @
    if r.startswith('@') and len(r) > 1:
        return {"type": "username", "value": r, "country": None}

    # Fallback: treat as phone without + (try to normalize)
    if re.match(r'^\d{7,15}$', r):
        return {"type": "phone", "value": f"+{r}", "country": None}

    # Unknown format — pass through as-is
    return {"type": "unknown", "value": r, "country": None}


def resolve_wa_recipient(recipient: str) -> str:
    """
    Normalize any identifier for use in Meta API payload.
    BSUID and username pass through directly.
    Phone numbers: ensure E.164 format and strip + for API.
    """
    info = detect_wa_id_type(recipient)

    if info["type"] == "phone":
        # Meta API expects number without + prefix
        v = info["value"]
        return v.lstrip('+') if v.startswith('+') else v

    # BSUID and @username pass directly to Meta API
    return info["value"]


def parse_wa_webhook(payload: dict) -> dict:
    """
    Extract identifiers from Meta webhook (dual phone/BSUID support).
    Compatible with pre and post June 2026 format.

    Returns:
        {
            "from": str,           # phone OR bsuid (depends on user settings)
            "bsuid": str,          # ExternalUserId when available
            "id_type": str,        # "phone" | "bsuid" | "username"
            "message_id": str,
            "timestamp": str,
            "type": str,           # "text" | "image" | "video" | etc.
            "text": str,           # message body (if text)
            "contact_name": str,   # user's WhatsApp name
        }
    """
    try:
        entry = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

        messages = value.get("messages", [])
        msg = messages[0] if messages else {}

        contacts = value.get("contacts", [])
        contact = contacts[0] if contacts else {}

        # Meta returns BSUID in ExternalUserId (when available, post-2026)
        from_id = msg.get("from", "")
        wa_id = contact.get("wa_id", from_id)
        external_uid = msg.get("ExternalUserId")  # New Meta 2026 field

        # Determine effective BSUID
        bsuid = external_uid or (wa_id if detect_wa_id_type(wa_id)["type"] == "bsuid" else None)

        return {
            "from": from_id,
            "bsuid": bsuid,
            "id_type": detect_wa_id_type(from_id)["type"],
            "message_id": msg.get("id"),
            "timestamp": msg.get("timestamp"),
            "type": msg.get("type"),
            "text": msg.get("text", {}).get("body") if msg.get("type") == "text" else None,
            "contact_name": contact.get("profile", {}).get("name"),
            "wa_id": wa_id,
        }
    except Exception as e:
        return {"error": str(e), "raw": payload}


def send_whatsapp_any_id(to: str, message: str = None, media_type: str = None,
                         media_id: str = None, media_url: str = None,
                         caption: str = "", filename: str = None) -> dict:
    """
    Universal WhatsApp send function — accepts any identifier type.
    Automatically detects: E.164 phone | BSUID | @username

    Args:
        to:         Any WhatsApp identifier (+49xxx, DE_abc123..., @username)
        message:    Text message (if sending text)
        media_type: "image" | "video" | "document" | "audio" (if sending media)
        media_id:   Media ID from upload (if sending media)
        media_url:  Public media URL (if sending media)
        caption:    Caption for media
        filename:   Filename for documents

    Returns:
        {"success": True/False, "message_id": ..., "id_type": ..., "resolved_to": ...}
    """
    id_info = detect_wa_id_type(to)
    resolved = resolve_wa_recipient(to)

    # Determine what to send
    if message and not media_type:
        # Text message
        result = send_whatsapp(to, message)
    elif media_type:
        # Media message
        result = send_whatsapp_media(
            to=to,
            media_type=media_type,
            media_id=media_id,
            media_url=media_url,
            caption=caption,
            filename=filename
        )
    else:
        return {"success": False, "error": "Provide message or media_type"}

    # Enrich result with ID type info
    if result.get("success"):
        result["id_type"] = id_info["type"]
        result["resolved_to"] = resolved
        if id_info["country"]:
            result["country"] = id_info["country"]

    return result


def upload_media_to_whatsapp(file_bytes: bytes, filename: str, mime_type: str = None) -> dict:
    """
    Upload media file to Meta WhatsApp API.
    Returns {"success": True, "media_id": "..."} or {"success": False, "error": "..."}

    Supported types:
    - Image: image/jpeg, image/png, image/webp (max 5MB)
    - Video: video/mp4, video/3gpp (max 16MB)
    - Doc:   application/pdf, application/vnd.openxmlformats-officedocument... (max 100MB)
    - Audio: audio/aac, audio/mpeg, audio/ogg (max 16MB)
    """
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_ID:
        return {"success": False, "error": "WHATSAPP_API_TOKEN or WHATSAPP_PHONE_ID not configured"}

    if mime_type is None:
        mime_type, _ = mimetypes.guess_type(filename)
        mime_type = mime_type or "application/octet-stream"

    # Size limits by type
    size_mb = len(file_bytes) / (1024 * 1024)
    size_limits = {"image": 5, "video": 16, "audio": 16, "application": 100}
    media_category = mime_type.split("/")[0]
    limit = size_limits.get(media_category, 100)
    if size_mb > limit:
        return {"success": False, "error": f"File too large: {size_mb:.1f}MB (max {limit}MB for {media_category})"}

    try:
        boundary = "WINDIBoundary20260308"
        body_parts = []
        body_parts.append(f"--{boundary}".encode())
        body_parts.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode())
        body_parts.append(f"Content-Type: {mime_type}".encode())
        body_parts.append(b"")
        body_parts.append(file_bytes)
        body_parts.append(f"--{boundary}".encode())
        body_parts.append(b'Content-Disposition: form-data; name="messaging_product"')
        body_parts.append(b"")
        body_parts.append(b"whatsapp")
        body_parts.append(f"--{boundary}--".encode())

        body = b"\r\n".join(body_parts)

        url = f"{WHATSAPP_GRAPH_URL}/{WHATSAPP_PHONE_ID}/media"
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Authorization", f"Bearer {WHATSAPP_TOKEN}")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            media_id = result.get("id")
            if media_id:
                return {"success": True, "media_id": media_id, "mime_type": mime_type}
            return {"success": False, "error": f"Meta API did not return media_id: {result}"}

    except Exception as e:
        return {"success": False, "error": f"Upload error: {str(e)}"}


def send_whatsapp_media(to: str, media_type: str, media_id: str = None,
                        media_url: str = None, caption: str = "", filename: str = None) -> dict:
    """
    Send media via WhatsApp (image, video, document, audio).

    Args:
        to:         Destination number (+49xxx)
        media_type: "image" | "video" | "document" | "audio"
        media_id:   ID from upload_media_to_whatsapp() [preferred, GDPR safer]
        media_url:  Public direct URL [alternative if no upload]
        caption:    Caption (not supported in audio/document without caption)
        filename:   Filename (required for document)

    Returns: {"success": True/False, "message_id": "...", "error": "..."}
    """
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_ID:
        return {"success": False, "error": "WhatsApp credentials not configured"}

    if not media_id and not media_url:
        return {"success": False, "error": "Provide media_id (upload) or media_url"}

    # Build media payload
    if media_id:
        media_payload = {"id": media_id}
    else:
        media_payload = {"link": media_url}

    if caption and media_type in ("image", "video", "document"):
        media_payload["caption"] = caption

    if media_type == "document":
        media_payload["filename"] = filename or "documento_windi.pdf"

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to.replace("+", "").replace(" ", ""),
        "type": media_type,
        media_type: media_payload,
    }

    try:
        url = f"{WHATSAPP_GRAPH_URL}/{WHATSAPP_PHONE_ID}/messages"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Authorization", f"Bearer {WHATSAPP_TOKEN}")
        req.add_header("Content-Type", "application/json")

        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
            msg_id = result.get("messages", [{}])[0].get("id")
            return {
                "success": True,
                "message_id": msg_id,
                "media_type": media_type,
                "to": to,
                "had_caption": bool(caption),
            }

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if hasattr(e, 'read') else str(e)
        return {"success": False, "error": f"HTTP {e.code}: {error_body}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_whatsapp_image(to: str, image_url: str = None, image_id: str = None,
                        caption: str = "") -> dict:
    """Shortcut: send image (JPEG/PNG/WebP, max 5MB)."""
    return send_whatsapp_media(to, "image", media_id=image_id,
                               media_url=image_url, caption=caption)


def send_whatsapp_video(to: str, video_url: str = None, video_id: str = None,
                        caption: str = "") -> dict:
    """Shortcut: send video (MP4/3GPP, max 16MB)."""
    return send_whatsapp_media(to, "video", media_id=video_id,
                               media_url=video_url, caption=caption)


def send_whatsapp_document(to: str, doc_url: str = None, doc_id: str = None,
                           caption: str = "", filename: str = "documento.pdf") -> dict:
    """Shortcut: send document (PDF/DOCX/JMPG, max 100MB)."""
    return send_whatsapp_media(to, "document", media_id=doc_id,
                               media_url=doc_url, caption=caption, filename=filename)


def send_whatsapp_sticker(to: str, sticker_url: str = None, sticker_id: str = None) -> dict:
    """Shortcut: send sticker (static WebP, max 100KB)."""
    return send_whatsapp_media(to, "sticker", media_id=sticker_id, media_url=sticker_url)


# ═══════════════════════════════════════════════════════════════════════════════════
# WHATSAPP TEMPLATE MESSAGES SYSTEM v1.0.0
# Meta requires pre-approved templates to initiate conversations
# Added: 2026-03-08
# ═══════════════════════════════════════════════════════════════════════════════════

# WINDI Pre-defined Templates (submit to Meta for approval)
# Format: template_name -> {languages, category, components}
WINDI_WHATSAPP_TEMPLATES = {
    # ── Document Delivery ──────────────────────────────────────────
    "windi_document_ready": {
        "category": "UTILITY",
        "languages": ["de", "en", "pt"],
        "components": {
            "de": {
                "header": {"type": "text", "text": "📄 Dokument bereit"},
                "body": "Hallo {{1}},\n\nIhr Dokument \"{{2}}\" ist bereit und wurde kryptographisch versiegelt.\n\n🛡️ Receipt-ID: {{3}}\n\nKlicken Sie auf den Link unten, um es zu verifizieren.",
                "footer": "WINDI Publishing · Kempten, Bavaria",
                "buttons": [{"type": "URL", "text": "Dokument öffnen", "url": "https://windi.publishing.de/verify/{{4}}"}]
            },
            "en": {
                "header": {"type": "text", "text": "📄 Document Ready"},
                "body": "Hello {{1}},\n\nYour document \"{{2}}\" is ready and has been cryptographically sealed.\n\n🛡️ Receipt ID: {{3}}\n\nClick the link below to verify it.",
                "footer": "WINDI Publishing · Kempten, Bavaria",
                "buttons": [{"type": "URL", "text": "Open Document", "url": "https://windi.publishing.de/verify/{{4}}"}]
            },
            "pt": {
                "header": {"type": "text", "text": "📄 Documento Pronto"},
                "body": "Olá {{1}},\n\nO seu documento \"{{2}}\" está pronto e foi selado criptograficamente.\n\n🛡️ Receipt ID: {{3}}\n\nClique no link abaixo para verificar.",
                "footer": "WINDI Publishing · Kempten, Bavaria",
                "buttons": [{"type": "URL", "text": "Abrir Documento", "url": "https://windi.publishing.de/verify/{{4}}"}]
            },
        },
        "variables": ["recipient_name", "document_title", "receipt_id", "receipt_id_for_url"],
    },

    # ── Seal Notification ──────────────────────────────────────────
    "windi_seal_complete": {
        "category": "UTILITY",
        "languages": ["de", "en", "pt"],
        "components": {
            "de": {
                "header": {"type": "text", "text": "🛡️ Versiegelung abgeschlossen"},
                "body": "Dokument \"{{1}}\" wurde erfolgreich versiegelt.\n\n📋 Receipt: {{2}}\n🕐 Zeit: {{3}}\n🔐 Hash: {{4}}...\n\nDieses Dokument ist jetzt kryptographisch verifizierbar.",
                "footer": "WINDI Forensic Ledger",
            },
            "en": {
                "header": {"type": "text", "text": "🛡️ Seal Complete"},
                "body": "Document \"{{1}}\" has been successfully sealed.\n\n📋 Receipt: {{2}}\n🕐 Time: {{3}}\n🔐 Hash: {{4}}...\n\nThis document is now cryptographically verifiable.",
                "footer": "WINDI Forensic Ledger",
            },
            "pt": {
                "header": {"type": "text", "text": "🛡️ Selagem Concluída"},
                "body": "O documento \"{{1}}\" foi selado com sucesso.\n\n📋 Receipt: {{2}}\n🕐 Hora: {{3}}\n🔐 Hash: {{4}}...\n\nEste documento é agora criptograficamente verificável.",
                "footer": "WINDI Forensic Ledger",
            },
        },
        "variables": ["document_title", "receipt_id", "timestamp", "hash_preview"],
    },

    # ── Verification Code ──────────────────────────────────────────
    "windi_verification_code": {
        "category": "AUTHENTICATION",
        "languages": ["de", "en", "pt"],
        "components": {
            "de": {
                "body": "Dein WINDI Verifizierungscode ist: *{{1}}*\n\nGültig für 10 Minuten. Teile diesen Code mit niemandem.",
                "footer": "WINDI Security",
            },
            "en": {
                "body": "Your WINDI verification code is: *{{1}}*\n\nValid for 10 minutes. Do not share this code with anyone.",
                "footer": "WINDI Security",
            },
            "pt": {
                "body": "O teu código de verificação WINDI é: *{{1}}*\n\nVálido por 10 minutos. Não partilhes este código com ninguém.",
                "footer": "WINDI Security",
            },
        },
        "variables": ["verification_code"],
    },

    # ── Welcome Message ────────────────────────────────────────────
    "windi_welcome": {
        "category": "MARKETING",
        "languages": ["de", "en", "pt"],
        "components": {
            "de": {
                "header": {"type": "text", "text": "🐉 Willkommen bei WINDI"},
                "body": "Hallo {{1}},\n\nWillkommen bei WINDI Publishing! Wir freuen uns, dich an Bord zu haben.\n\nMit WINDI kannst du:\n✓ Dokumente kryptographisch versiegeln\n✓ Forensische Beweise erstellen\n✓ Souveräne digitale Identität nutzen\n\nBei Fragen sind wir hier.",
                "footer": "Human decides. WINDI observes.",
            },
            "en": {
                "header": {"type": "text", "text": "🐉 Welcome to WINDI"},
                "body": "Hello {{1}},\n\nWelcome to WINDI Publishing! We're glad to have you on board.\n\nWith WINDI you can:\n✓ Cryptographically seal documents\n✓ Create forensic evidence\n✓ Use sovereign digital identity\n\nWe're here if you have questions.",
                "footer": "Human decides. WINDI observes.",
            },
            "pt": {
                "header": {"type": "text", "text": "🐉 Bem-vindo ao WINDI"},
                "body": "Olá {{1}},\n\nBem-vindo ao WINDI Publishing! Estamos felizes por te ter connosco.\n\nCom o WINDI podes:\n✓ Selar documentos criptograficamente\n✓ Criar evidências forenses\n✓ Usar identidade digital soberana\n\nEstamos aqui se tiveres dúvidas.",
                "footer": "Human decides. WINDI observes.",
            },
        },
        "variables": ["recipient_name"],
    },

    # ── Payment Reminder ───────────────────────────────────────────
    "windi_payment_reminder": {
        "category": "UTILITY",
        "languages": ["de", "en", "pt"],
        "components": {
            "de": {
                "header": {"type": "text", "text": "💳 Zahlungserinnerung"},
                "body": "Hallo {{1}},\n\nDies ist eine freundliche Erinnerung an die ausstehende Zahlung:\n\n📋 Rechnung: {{2}}\n💰 Betrag: {{3}}\n📅 Fällig: {{4}}\n\nBei Fragen kontaktiere uns bitte.",
                "footer": "WINDI Wallet",
            },
            "en": {
                "header": {"type": "text", "text": "💳 Payment Reminder"},
                "body": "Hello {{1}},\n\nThis is a friendly reminder about your pending payment:\n\n📋 Invoice: {{2}}\n💰 Amount: {{3}}\n📅 Due: {{4}}\n\nPlease contact us if you have any questions.",
                "footer": "WINDI Wallet",
            },
            "pt": {
                "header": {"type": "text", "text": "💳 Lembrete de Pagamento"},
                "body": "Olá {{1}},\n\nEste é um lembrete amigável sobre o pagamento pendente:\n\n📋 Fatura: {{2}}\n💰 Valor: {{3}}\n📅 Vencimento: {{4}}\n\nContacta-nos se tiveres dúvidas.",
                "footer": "WINDI Wallet",
            },
        },
        "variables": ["recipient_name", "invoice_id", "amount", "due_date"],
    },

    # ── Appointment Confirmation ───────────────────────────────────
    "windi_appointment": {
        "category": "UTILITY",
        "languages": ["de", "en", "pt"],
        "components": {
            "de": {
                "header": {"type": "text", "text": "📅 Terminbestätigung"},
                "body": "Hallo {{1}},\n\nDein Termin wurde bestätigt:\n\n📋 Betreff: {{2}}\n📅 Datum: {{3}}\n🕐 Uhrzeit: {{4}}\n📍 Ort: {{5}}\n\nWir freuen uns auf dich!",
                "footer": "WINDI Scheduling",
            },
            "en": {
                "header": {"type": "text", "text": "📅 Appointment Confirmed"},
                "body": "Hello {{1}},\n\nYour appointment has been confirmed:\n\n📋 Subject: {{2}}\n📅 Date: {{3}}\n🕐 Time: {{4}}\n📍 Location: {{5}}\n\nWe look forward to seeing you!",
                "footer": "WINDI Scheduling",
            },
            "pt": {
                "header": {"type": "text", "text": "📅 Compromisso Confirmado"},
                "body": "Olá {{1}},\n\nO teu compromisso foi confirmado:\n\n📋 Assunto: {{2}}\n📅 Data: {{3}}\n🕐 Hora: {{4}}\n📍 Local: {{5}}\n\nEstamos à tua espera!",
                "footer": "WINDI Scheduling",
            },
        },
        "variables": ["recipient_name", "subject", "date", "time", "location"],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════════
# HTML BUILDER MESSAGE TEMPLATES v1.0.0
# Distribution templates for Email, SMS, WhatsApp — used by /html-builder Send feature
# Added: 2026-03-11
# ═══════════════════════════════════════════════════════════════════════════════════

MESSAGE_TEMPLATES = {
    # ── Default Email Template ──────────────────────────────────────
    "MSG-DEFAULT-EMAIL": {
        "id": "MSG-DEFAULT-EMAIL",
        "name": {
            "de": "Dokumentlieferung",
            "en": "Document Delivery",
            "pt": "Entrega de Documento"
        },
        "channel": "email",
        "subject": {
            "de": "📄 Dokument: {doc_title}",
            "en": "📄 Document: {doc_title}",
            "pt": "📄 Documento: {doc_title}"
        },
        "body": {
            "de": "Hallo,\n\nSie haben ein neues Dokument von WINDI erhalten:\n\n📄 {doc_title}\n\n{doc_preview}\n\n🛡️ Versiegelungsnachweis: {receipt_id}\n\nVerifizieren Sie das Dokument unter:\n{verify_url}\n\nMit freundlichen Grüßen,\nWINDI Publishing",
            "en": "Hello,\n\nYou have received a new document from WINDI:\n\n📄 {doc_title}\n\n{doc_preview}\n\n🛡️ Seal Receipt: {receipt_id}\n\nVerify the document at:\n{verify_url}\n\nBest regards,\nWINDI Publishing",
            "pt": "Olá,\n\nRecebeu um novo documento do WINDI:\n\n📄 {doc_title}\n\n{doc_preview}\n\n🛡️ Recibo de Selagem: {receipt_id}\n\nVerifique o documento em:\n{verify_url}\n\nCom os melhores cumprimentos,\nWINDI Publishing"
        },
        "variables": ["doc_title", "doc_preview", "receipt_id", "verify_url"],
        "category": "document"
    },

    # ── Default SMS Template ────────────────────────────────────────
    "MSG-DEFAULT-SMS": {
        "id": "MSG-DEFAULT-SMS",
        "name": {
            "de": "Kurznachricht",
            "en": "Short Message",
            "pt": "Mensagem Curta"
        },
        "channel": "sms",
        "body": {
            "de": "WINDI: {doc_title} (ID: {receipt_id})\nVerifizieren: {verify_url}",
            "en": "WINDI: {doc_title} (ID: {receipt_id})\nVerify: {verify_url}",
            "pt": "WINDI: {doc_title} (ID: {receipt_id})\nVerificar: {verify_url}"
        },
        "variables": ["doc_title", "receipt_id", "verify_url"],
        "max_length": 160,
        "category": "document"
    },

    # ── Default WhatsApp Template ───────────────────────────────────
    "MSG-DEFAULT-WA": {
        "id": "MSG-DEFAULT-WA",
        "name": {
            "de": "WhatsApp Nachricht",
            "en": "WhatsApp Message",
            "pt": "Mensagem WhatsApp"
        },
        "channel": "whatsapp",
        "body": {
            "de": "📄 *{doc_title}*\n\n{doc_preview}\n\n🛡️ Receipt: `{receipt_id}`\n\n🔗 Verifizieren: {verify_url}",
            "en": "📄 *{doc_title}*\n\n{doc_preview}\n\n🛡️ Receipt: `{receipt_id}`\n\n🔗 Verify: {verify_url}",
            "pt": "📄 *{doc_title}*\n\n{doc_preview}\n\n🛡️ Receipt: `{receipt_id}`\n\n🔗 Verificar: {verify_url}"
        },
        "variables": ["doc_title", "doc_preview", "receipt_id", "verify_url"],
        "category": "document"
    },

    # ── Formal Document Template ────────────────────────────────────
    "MSG-FORMAL-EMAIL": {
        "id": "MSG-FORMAL-EMAIL",
        "name": {
            "de": "Formelle Mitteilung",
            "en": "Formal Notification",
            "pt": "Notificação Formal"
        },
        "channel": "email",
        "subject": {
            "de": "Offizielle Mitteilung: {doc_title}",
            "en": "Official Notification: {doc_title}",
            "pt": "Notificação Oficial: {doc_title}"
        },
        "body": {
            "de": "Sehr geehrte Damen und Herren,\n\nhiermit übersenden wir Ihnen das folgende kryptographisch versiegelte Dokument:\n\n{doc_title}\n\n{doc_preview}\n\nDieses Dokument wurde am {timestamp} im WINDI Forensic Ledger registriert.\n\nVersiegelungs-ID: {receipt_id}\nVerifikation: {verify_url}\n\nMit freundlichen Grüßen",
            "en": "Dear Sir or Madam,\n\nPlease find attached the following cryptographically sealed document:\n\n{doc_title}\n\n{doc_preview}\n\nThis document was registered in the WINDI Forensic Ledger on {timestamp}.\n\nSeal ID: {receipt_id}\nVerification: {verify_url}\n\nKind regards",
            "pt": "Exmo(a) Senhor(a),\n\nEnviamos o seguinte documento selado criptograficamente:\n\n{doc_title}\n\n{doc_preview}\n\nEste documento foi registado no WINDI Forensic Ledger em {timestamp}.\n\nID de Selagem: {receipt_id}\nVerificação: {verify_url}\n\nCom os melhores cumprimentos"
        },
        "variables": ["doc_title", "doc_preview", "receipt_id", "verify_url", "timestamp"],
        "category": "formal"
    },

    # ── Brief Notification ──────────────────────────────────────────
    "MSG-BRIEF-WA": {
        "id": "MSG-BRIEF-WA",
        "name": {
            "de": "Kurze Benachrichtigung",
            "en": "Brief Notification",
            "pt": "Notificação Breve"
        },
        "channel": "whatsapp",
        "body": {
            "de": "📄 Neues Dokument: *{doc_title}*\n🔗 {verify_url}",
            "en": "📄 New document: *{doc_title}*\n🔗 {verify_url}",
            "pt": "📄 Novo documento: *{doc_title}*\n🔗 {verify_url}"
        },
        "variables": ["doc_title", "verify_url"],
        "category": "brief"
    },
}


def get_message_template(template_id: str, lang: str = "en") -> dict:
    """
    Get a message template by ID and language.

    Args:
        template_id: Template ID (e.g., "MSG-DEFAULT-EMAIL")
        lang: Language code (de, en, pt)

    Returns:
        {"found": True, "template": {...}} or {"found": False, "error": "..."}
    """
    template = MESSAGE_TEMPLATES.get(template_id)
    if not template:
        return {
            "found": False,
            "error": f"Template '{template_id}' not found",
            "available": list(MESSAGE_TEMPLATES.keys())
        }

    # Resolve language-specific fields
    name = template["name"].get(lang, template["name"].get("en", ""))
    subject = template.get("subject", {}).get(lang, template.get("subject", {}).get("en", "")) if "subject" in template else None
    body = template["body"].get(lang, template["body"].get("en", ""))

    return {
        "found": True,
        "id": template_id,
        "name": name,
        "channel": template["channel"],
        "subject": subject,
        "body": body,
        "variables": template.get("variables", []),
        "category": template.get("category", "general"),
        "max_length": template.get("max_length"),
    }


def list_message_templates(channel: str = None, lang: str = "en") -> list:
    """
    List available message templates.

    Args:
        channel: Filter by channel (email, sms, whatsapp)
        lang: Language for template names

    Returns:
        List of template summaries
    """
    results = []
    for tid, template in MESSAGE_TEMPLATES.items():
        if channel and template["channel"] != channel:
            continue

        name = template["name"].get(lang, template["name"].get("en", ""))

        results.append({
            "id": tid,
            "name": name,
            "channel": template["channel"],
            "category": template.get("category", "general"),
            "variables": template.get("variables", []),
        })

    return results


def render_message_template(template_id: str, lang: str, variables: dict) -> dict:
    """
    Render a message template with variable substitution.

    Args:
        template_id: Template ID
        lang: Language code
        variables: Dict of variable values

    Returns:
        {"success": True, "rendered": {...}} or {"success": False, "error": "..."}
    """
    tpl = get_message_template(template_id, lang)
    if not tpl.get("found"):
        return {"success": False, "error": tpl.get("error")}

    # Render subject (if applicable)
    rendered_subject = tpl.get("subject", "")
    if rendered_subject:
        for key, value in variables.items():
            rendered_subject = rendered_subject.replace(f"{{{key}}}", str(value))

    # Render body
    rendered_body = tpl["body"]
    for key, value in variables.items():
        rendered_body = rendered_body.replace(f"{{{key}}}", str(value))

    # Apply max_length for SMS
    if tpl.get("max_length") and len(rendered_body) > tpl["max_length"]:
        rendered_body = rendered_body[:tpl["max_length"] - 3] + "..."

    return {
        "success": True,
        "template_id": template_id,
        "channel": tpl["channel"],
        "language": lang,
        "rendered": {
            "subject": rendered_subject if rendered_subject else None,
            "body": rendered_body,
        },
        "variables_used": list(variables.keys()),
    }


def get_template(template_name: str, lang: str = "en") -> dict:
    """
    Get a WINDI WhatsApp template by name and language.

    Returns:
        {"found": True, "template": {...}, "variables": [...]} or
        {"found": False, "error": "..."}
    """
    template = WINDI_WHATSAPP_TEMPLATES.get(template_name)
    if not template:
        available = list(WINDI_WHATSAPP_TEMPLATES.keys())
        return {"found": False, "error": f"Template '{template_name}' not found", "available": available}

    # Get language-specific components
    components = template.get("components", {})
    lang_components = components.get(lang) or components.get("en") or list(components.values())[0]

    return {
        "found": True,
        "template_name": template_name,
        "language": lang,
        "category": template.get("category"),
        "components": lang_components,
        "variables": template.get("variables", []),
        "supported_languages": template.get("languages", []),
    }


def list_templates(category: str = None, lang: str = None) -> list:
    """
    List all available WINDI WhatsApp templates.

    Args:
        category: Filter by category (UTILITY, MARKETING, AUTHENTICATION)
        lang: Filter by language support

    Returns:
        List of template summaries
    """
    results = []
    for name, template in WINDI_WHATSAPP_TEMPLATES.items():
        # Apply filters
        if category and template.get("category") != category:
            continue
        if lang and lang not in template.get("languages", []):
            continue

        results.append({
            "name": name,
            "category": template.get("category"),
            "languages": template.get("languages"),
            "variables": template.get("variables"),
            "variable_count": len(template.get("variables", [])),
        })

    return results


def render_template(template_name: str, lang: str, variables: dict) -> dict:
    """
    Render a template with actual variable values.

    Args:
        template_name: Name of the template
        lang: Language code (de, en, pt)
        variables: Dict mapping variable names to values

    Returns:
        {"success": True, "rendered": {...}} or {"success": False, "error": "..."}
    """
    tpl = get_template(template_name, lang)
    if not tpl.get("found"):
        return {"success": False, "error": tpl.get("error")}

    components = tpl["components"]
    expected_vars = tpl["variables"]

    # Check all required variables are provided
    missing = [v for v in expected_vars if v not in variables]
    if missing:
        return {"success": False, "error": f"Missing variables: {missing}", "required": expected_vars}

    # Build variable list in order ({{1}}, {{2}}, etc.)
    var_values = [str(variables.get(v, "")) for v in expected_vars]

    # Render body text
    rendered_body = components.get("body", "")
    for i, val in enumerate(var_values, 1):
        rendered_body = rendered_body.replace(f"{{{{{i}}}}}", val)

    # Render header if exists
    rendered_header = None
    if "header" in components:
        rendered_header = components["header"].copy()
        if rendered_header.get("type") == "text":
            header_text = rendered_header.get("text", "")
            for i, val in enumerate(var_values, 1):
                header_text = header_text.replace(f"{{{{{i}}}}}", val)
            rendered_header["text"] = header_text

    # Render buttons if exist
    rendered_buttons = None
    if "buttons" in components:
        rendered_buttons = []
        for btn in components["buttons"]:
            new_btn = btn.copy()
            if "url" in new_btn:
                url = new_btn["url"]
                for i, val in enumerate(var_values, 1):
                    url = url.replace(f"{{{{{i}}}}}", val)
                new_btn["url"] = url
            rendered_buttons.append(new_btn)

    return {
        "success": True,
        "template_name": template_name,
        "language": lang,
        "rendered": {
            "header": rendered_header,
            "body": rendered_body,
            "footer": components.get("footer"),
            "buttons": rendered_buttons,
        },
        "variable_values": var_values,
    }


def send_whatsapp_template(to: str, template_name: str, lang: str,
                           variables: dict, header_media: dict = None) -> dict:
    """
    Send a WhatsApp template message.

    Args:
        to: Recipient (phone/BSUID/@username)
        template_name: Name of the approved template
        lang: Language code (de, en, pt)
        variables: Dict mapping variable names to values
        header_media: Optional media for header {"type": "image"|"video"|"document", "link": "..."}

    Returns:
        {"success": True, "message_id": "...", ...} or {"success": False, "error": "..."}
    """
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_ID:
        return {"success": False, "error": "WhatsApp credentials not configured"}

    # Get and validate template
    tpl = get_template(template_name, lang)
    if not tpl.get("found"):
        return {"success": False, "error": tpl.get("error")}

    # Build variable list
    expected_vars = tpl["variables"]
    missing = [v for v in expected_vars if v not in variables]
    if missing:
        return {"success": False, "error": f"Missing variables: {missing}"}

    var_values = [str(variables.get(v, "")) for v in expected_vars]

    # Resolve recipient
    resolved_to = resolve_wa_recipient(to)

    # Build Meta API payload for template message
    # https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-message-templates

    components = []

    # Header component (if template has header)
    if header_media:
        components.append({
            "type": "header",
            "parameters": [{
                "type": header_media["type"],
                header_media["type"]: {"link": header_media["link"]}
            }]
        })

    # Body component with variables
    if var_values:
        body_params = [{"type": "text", "text": v} for v in var_values]
        components.append({
            "type": "body",
            "parameters": body_params
        })

    # Button component (if URL button with variable)
    tpl_components = tpl.get("components", {})
    if "buttons" in tpl_components:
        for idx, btn in enumerate(tpl_components["buttons"]):
            if btn.get("type") == "URL" and "{{" in btn.get("url", ""):
                # URL has variable - need to pass it
                # Find which variable index is used in URL
                for i, var in enumerate(expected_vars, 1):
                    if f"{{{{{i}}}}}" in btn.get("url", ""):
                        components.append({
                            "type": "button",
                            "sub_type": "url",
                            "index": str(idx),
                            "parameters": [{"type": "text", "text": var_values[i-1]}]
                        })
                        break

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": resolved_to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": lang},
            "components": components if components else None
        }
    }

    # Remove None components
    if payload["template"]["components"] is None:
        del payload["template"]["components"]

    try:
        url = f"{WHATSAPP_GRAPH_URL}/{WHATSAPP_PHONE_ID}/messages"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Authorization", f"Bearer {WHATSAPP_TOKEN}")
        req.add_header("Content-Type", "application/json")

        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
            msg_id = result.get("messages", [{}])[0].get("id")

            # Detect ID type
            id_info = detect_wa_id_type(to)

            return {
                "success": True,
                "message_id": msg_id,
                "template_name": template_name,
                "language": lang,
                "variables_sent": var_values,
                "id_type": id_info["type"],
                "to": to,
            }

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if hasattr(e, 'read') else str(e)
        return {"success": False, "error": f"HTTP {e.code}: {error_body}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def seal_whatsapp_media_send(to: str, media_type: str, caption: str,
                             message_id: str, actor: str = "Dragon",
                             bsuid: str = None) -> dict:
    """
    Seal WhatsApp media send in Forensic Ledger.
    GDPR: recipient identifier is hashed, never stored raw.

    PATCH v1.1.0: Now supports BSUID for Meta username transition (June 2026).
    - Detects identifier type automatically (phone/bsuid/username)
    - Stores wa_id_type for analytics
    - BSUID stored when available (also hashed for GDPR)
    """
    # Detect identifier type
    id_info = detect_wa_id_type(to)
    wa_id_type = id_info["type"]

    # GDPR: always hash the identifier
    to_hash = hashlib.sha256(to.encode()).hexdigest()[:16]
    bsuid_hash = hashlib.sha256(bsuid.encode()).hexdigest()[:16] if bsuid else None

    receipt_id = f"WINDI-WA-{media_type.upper()}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    payload = {
        "id": receipt_id,
        "actor": actor,
        "app": "dragon_chat_service",
        "doc_name": f"WhatsApp {media_type} → {to_hash}",
        "doc_type": "communique",
        "governance_level": "MEDIUM",
        # PATCH v1.1.0: BSUID fields at top level for Ledger schema
        "bsuid": bsuid_hash,           # Hashed BSUID when available
        "wa_id_type": wa_id_type,      # "phone" | "bsuid" | "username"
        "metadata": {
            "channel": "whatsapp",
            "media_type": media_type,
            "recipient_hash": to_hash,
            "bsuid_hash": bsuid_hash,  # Also in metadata for redundancy
            "wa_id_type": wa_id_type,
            "country": id_info.get("country"),  # From BSUID prefix (e.g., "DE")
            "message_id": message_id,
            "caption_length": len(caption) if caption else 0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "patch_version": "1.1.0",
        }
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{LEDGER_URL_INTERNAL}/api/receipts",
            data=data, method="POST"
        )
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode())
            return {
                "sealed": True,
                "receipt_id": receipt_id,
                "wa_id_type": wa_id_type,
                "ledger": result
            }
    except Exception as e:
        # Ledger seal is best-effort — does not block send
        return {"sealed": False, "error": str(e), "wa_id_type": wa_id_type}


def create_document_email_html(doc_title: str, doc_content: str, receipt_id: str, lang: str = "en") -> str:
    """
    Create HTML email template for document distribution.
    """
    templates = {
        "de": {
            "subject": f"📄 WINDI Dokument: {doc_title}",
            "header": "Versiegeltes Dokument von WINDI",
            "body_intro": "Ein neues Dokument wurde mit Ihnen geteilt:",
            "receipt_label": "Receipt-ID",
            "verify_label": "Dokument verifizieren",
            "footer": "Dieses Dokument wurde kryptographisch versiegelt und ist auf der WINDI-Blockchain verifizierbar.",
        },
        "en": {
            "subject": f"📄 WINDI Document: {doc_title}",
            "header": "Sealed Document from WINDI",
            "body_intro": "A new document has been shared with you:",
            "receipt_label": "Receipt ID",
            "verify_label": "Verify Document",
            "footer": "This document has been cryptographically sealed and is verifiable on the WINDI blockchain.",
        },
        "pt": {
            "subject": f"📄 WINDI Documento: {doc_title}",
            "header": "Documento Selado do WINDI",
            "body_intro": "Um novo documento foi partilhado contigo:",
            "receipt_label": "ID Recibo",
            "verify_label": "Verificar Documento",
            "footer": "Este documento foi selado criptograficamente e é verificável na blockchain WINDI.",
        },
    }

    t = templates.get(lang, templates["en"])
    verify_url = f"https://windi-domain.com/verify/{receipt_id}"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family: 'Outfit', -apple-system, sans-serif; background: #0a0a0a; color: #e8e6e3; padding: 40px; margin: 0;">
      <div style="max-width: 600px; margin: 0 auto; background: #111; border-radius: 16px; padding: 32px; border: 1px solid #222;">
        <div style="text-align: center; margin-bottom: 24px;">
          <span style="font-size: 48px;">🐉</span>
          <h1 style="color: #c8a438; margin: 16px 0 8px; font-size: 24px;">{t['header']}</h1>
        </div>

        <p style="color: #888; margin-bottom: 16px;">{t['body_intro']}</p>

        <div style="background: #1a1a1a; border-radius: 12px; padding: 20px; border: 1px solid #333; margin-bottom: 24px;">
          <h2 style="color: #e8e6e3; margin: 0 0 12px; font-size: 18px;">📄 {doc_title}</h2>
          <p style="color: #aaa; font-size: 14px; line-height: 1.6; margin: 0; white-space: pre-wrap;">{doc_content[:500]}{'...' if len(doc_content) > 500 else ''}</p>
        </div>

        <div style="background: #1B4332; border-radius: 10px; padding: 16px; margin-bottom: 24px; font-family: monospace; font-size: 12px;">
          <div style="color: #81C784;">🛡️ {t['receipt_label']}: <strong>{receipt_id}</strong></div>
        </div>

        <div style="text-align: center; margin-bottom: 24px;">
          <a href="{verify_url}" style="display: inline-block; background: #c8a438; color: #0a0a0a; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 14px;">
            🔐 {t['verify_label']}
          </a>
        </div>

        <p style="color: #555; font-size: 11px; text-align: center; margin: 0;">
          {t['footer']}<br>
          <em>AI processes. Human decides. WINDI guarantees.</em>
        </p>
      </div>
    </body>
    </html>
    """

    return html, t['subject']


# ═══════════════════════════════════════════════════════════════════════════════════
# LINKEDIN INTEGRATION v1.0.0 — Share Posts & Direct Messages
# Added: 2026-03-12 | LinkedIn API v2
# ═══════════════════════════════════════════════════════════════════════════════════

def send_linkedin_post(message: str, doc_title: str = None, verify_url: str = None) -> dict:
    """
    Post content to LinkedIn (organization page or personal profile).

    Args:
        message: Text content to post
        doc_title: Optional document title for structured post
        verify_url: Optional verification URL to include

    Returns:
        {"success": True/False, "message": "...", "channel": "linkedin"}
    """
    if not LINKEDIN_ACCESS_TOKEN:
        return {"success": False, "message": "LinkedIn not configured", "channel": "linkedin"}

    try:
        # Build post text
        post_text = message
        if doc_title:
            post_text = f"📄 {doc_title}\n\n{message}"
        if verify_url:
            post_text += f"\n\n🔐 Verify: {verify_url}"

        # Determine author: organization or personal profile
        if LINKEDIN_ORG_ID:
            author = f"urn:li:organization:{LINKEDIN_ORG_ID}"
        else:
            # Need to get user's profile URN from /me endpoint
            me_req = urllib.request.Request(
                f"{LINKEDIN_API_URL}/me",
                headers={"Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}"},
            )
            with urllib.request.urlopen(me_req, timeout=10) as resp:
                me_data = json.loads(resp.read().decode())
                author = f"urn:li:person:{me_data['id']}"

        # Create UGC post (User Generated Content)
        post_data = json.dumps({
            "author": author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": post_text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }).encode()

        req = urllib.request.Request(
            f"{LINKEDIN_API_URL}/ugcPosts",
            data=post_data,
            headers={
                "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            },
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())

        log_entry = {
            "channel": "linkedin",
            "type": "post",
            "post_id": result.get("id"),
            "timestamp": datetime.now().isoformat(),
            "success": True,
        }
        DISTRIBUTION_LOG.append(log_entry)

        return {"success": True, "message": "LinkedIn post published", "channel": "linkedin", "post_id": result.get("id")}

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else str(e)
        log_entry = {
            "channel": "linkedin",
            "type": "post",
            "error": error_body,
            "timestamp": datetime.now().isoformat(),
            "success": False,
        }
        DISTRIBUTION_LOG.append(log_entry)
        return {"success": False, "message": f"LinkedIn post failed: {error_body}", "channel": "linkedin"}
    except Exception as e:
        log_entry = {
            "channel": "linkedin",
            "type": "post",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "success": False,
        }
        DISTRIBUTION_LOG.append(log_entry)
        return {"success": False, "message": f"LinkedIn post failed: {e}", "channel": "linkedin"}


def send_linkedin_dm(recipient_urn: str, message: str, doc_title: str = None, verify_url: str = None) -> dict:
    """
    Send a direct message on LinkedIn.

    Args:
        recipient_urn: LinkedIn member URN (urn:li:person:xxx) or profile ID
        message: Message content
        doc_title: Optional document title
        verify_url: Optional verification URL

    Returns:
        {"success": True/False, "message": "...", "channel": "linkedin"}
    """
    if not LINKEDIN_ACCESS_TOKEN:
        return {"success": False, "message": "LinkedIn not configured", "channel": "linkedin"}

    try:
        # Normalize recipient URN
        if not recipient_urn.startswith("urn:li:"):
            recipient_urn = f"urn:li:person:{recipient_urn}"

        # Build message text
        msg_text = message
        if doc_title:
            msg_text = f"📄 {doc_title}\n\n{message}"
        if verify_url:
            msg_text += f"\n\n🔐 Verify: {verify_url}"

        # LinkedIn Messaging API
        dm_data = json.dumps({
            "recipients": [recipient_urn],
            "body": msg_text,
            "messageType": "MEMBER_TO_MEMBER"
        }).encode()

        req = urllib.request.Request(
            f"{LINKEDIN_API_URL}/messages",
            data=dm_data,
            headers={
                "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            },
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())

        log_entry = {
            "channel": "linkedin",
            "type": "dm",
            "to": recipient_urn,
            "timestamp": datetime.now().isoformat(),
            "success": True,
        }
        DISTRIBUTION_LOG.append(log_entry)

        return {"success": True, "message": f"LinkedIn DM sent to {recipient_urn}", "channel": "linkedin"}

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else str(e)
        log_entry = {
            "channel": "linkedin",
            "type": "dm",
            "to": recipient_urn,
            "error": error_body,
            "timestamp": datetime.now().isoformat(),
            "success": False,
        }
        DISTRIBUTION_LOG.append(log_entry)
        return {"success": False, "message": f"LinkedIn DM failed: {error_body}", "channel": "linkedin"}
    except Exception as e:
        log_entry = {
            "channel": "linkedin",
            "type": "dm",
            "to": recipient_urn,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "success": False,
        }
        DISTRIBUTION_LOG.append(log_entry)
        return {"success": False, "message": f"LinkedIn DM failed: {e}", "channel": "linkedin"}


def distribute_document(recipients: list, doc_title: str, doc_content: str, receipt_id: str, lang: str = "en") -> dict:
    """
    Distribute a sealed document to multiple recipients via their preferred channels.

    Args:
        recipients: List of {"channel": "email"|"sms"|"whatsapp"|"linkedin_post"|"linkedin_dm", "value": "address/number/urn"}
        doc_title: Document title
        doc_content: Document content
        receipt_id: Virtue Receipt ID
        lang: Language for templates

    Returns:
        {"success": True, "sent": [...], "failed": [...]}
    """
    sent = []
    failed = []

    html_body, subject = create_document_email_html(doc_title, doc_content, receipt_id, lang)
    verify_url = f"https://windi-domain.com/verify/{receipt_id}"
    plain_message = f"📄 {doc_title}\n\n{doc_content[:500]}...\n\n🛡️ Receipt: {receipt_id}\n\nVerify: {verify_url}"

    for recipient in recipients:
        channel = recipient.get("channel", "email")
        value = recipient.get("value", "")

        if channel == "email":
            result = send_email(value, subject, html_body, html=True)
        elif channel == "sms":
            result = send_sms(value, plain_message[:160])  # SMS short version
        elif channel == "whatsapp":
            result = send_whatsapp(value, plain_message)
        elif channel == "linkedin_post":
            # LinkedIn post (value can be empty for org page, or custom text)
            result = send_linkedin_post(doc_content[:500], doc_title, verify_url)
        elif channel == "linkedin_dm":
            # LinkedIn DM (value is recipient URN or profile ID)
            result = send_linkedin_dm(value, plain_message, doc_title, verify_url)
        else:
            result = {"success": False, "message": f"Unknown channel: {channel}", "channel": channel}

        if result["success"]:
            sent.append({"channel": channel, "to": value})
        else:
            failed.append({"channel": channel, "to": value, "error": result["message"]})

    return {
        "success": len(failed) == 0,
        "sent": sent,
        "failed": failed,
        "total_sent": len(sent),
        "total_failed": len(failed),
    }


# ═══════════════════════════════════════════════════════════════════════════════════
# HTTP HANDLER
# ═══════════════════════════════════════════════════════════════════════════════════

class DragonChatHandler(BaseHTTPRequestHandler):

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Session-ID, X-Tier")

    def _json_response(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path

        if path in ["/", "/health"]:
            gate = gate_status()
            self._json_response({
                "service": "dragon-chat",
                "version": VERSION,
                "status": "healthy",
                "tier": gate["tier"],
                "architecture": {
                    "orchestrator": ORCHESTRATOR_URL,
                    "lang_detect": LANG_DETECT_SOURCE,
                    "intent_parser": "available" if INTENT_PARSER_AVAILABLE else "fallback",
                    "semantic_parser": "layer7",  # Action #7
                    "cognitive_interface": "available" if CIL_AVAILABLE else "unavailable",
                    "local_services": list(SERVICE_ENDPOINTS.keys()),  # Action #5
                },
                "actions": {
                    "week1": ["#1 Orchestrator", "#2 LangDetect", "#3 TierRouting"],
                    "week2": ["#4 NeedsLLM", "#5 LocalQueries", "#7 Layer7Semantics"],
                    "v2.2": ["KnowledgeBase", "ConversationalHandler", "SessionContext"],
                    "v2.3": ["CognitiveInterface", "InsightGenerator", "ProactiveMessages"],
                    "v2.4": ["WhatsAppMedia", "ImageVideoDocument", "LedgerSeal"],
                    "v2.5": ["BSUID_Ready", "detect_wa_id_type", "parse_wa_webhook", "send_any_id"],
                    "v2.6": ["TemplateMessages", "render_template", "send_template", "pre_approved_templates"],
                },
                "whatsapp_patch": {
                    "version": "1.2.0",
                    "bsuid_ready": True,
                    "templates_ready": True,
                    "supported_ids": ["phone", "bsuid", "username"],
                    "meta_deadline": "June 2026",
                    "endpoints": [
                        "/whatsapp/send-any",
                        "/whatsapp/detect-id",
                        "/whatsapp/webhook",
                        "/whatsapp/templates",
                        "/whatsapp/templates/{name}",
                        "/whatsapp/templates/render",
                        "/whatsapp/templates/send",
                    ],
                },
                "knowledge_base": list(KNOWLEDGE_BASE.keys()),
                "principles": [
                    "1. Suggests, never executes without confirmation",
                    "2. Never shows brand names (WINDI identity)",
                    "3. Session memory, not surveillance (ephemeral)",
                    "4. Respects tier gates (FREE/MED/HIGH routing)",
                    "5. Speaks user's language (guardian-local detection)"
                ],
                "active_sessions": len(SESSIONS),
                "refactoring": "A.4 v2.6 — Template Messages System (Meta pre-approved)"
            })
            return

        if path == "/gate":
            self._json_response(gate_status())
            return

        # ─── DISTRIBUTE STATUS (GET) — Check channel configuration ────────────
        if path == "/distribute/status":
            self._json_response({
                "success": True,
                "channels": {
                    "email": {
                        "configured": bool(SMTP_HOST),
                        "from": SMTP_FROM,
                    },
                    "sms": {
                        "configured": bool(TWILIO_SID and TWILIO_TOKEN),
                    },
                    "whatsapp": {
                        "configured": bool(WHATSAPP_TOKEN and WHATSAPP_PHONE_ID),
                    },
                    "linkedin": {
                        "configured": bool(LINKEDIN_ACCESS_TOKEN),
                        "org_id": LINKEDIN_ORG_ID if LINKEDIN_ORG_ID else None,
                        "features": ["post", "dm"] if LINKEDIN_ACCESS_TOKEN else [],
                    },
                },
                "recent_distributions": DISTRIBUTION_LOG[-10:],
            })
            return

        if path == "/identity":
            query = parse_qs(urlparse(self.path).query)
            lang = query.get("lang", ["de"])[0]
            self._json_response(DRAGON_IDENTITY.get(lang, DRAGON_IDENTITY["de"]))
            return

        # ─── COGNITIVE INTERFACE ENDPOINTS ────────────────────────────────
        if path == "/cognition/insights" or path == "/cognition":
            query = parse_qs(urlparse(self.path).query)
            lang = query.get("lang", ["en"])[0]

            if CIL_AVAILABLE:
                try:
                    cil = CognitiveInterface(lang)
                    summary = cil.get_cognitive_summary()
                    self._json_response({
                        "success": True,
                        "lang": lang,
                        "insights": summary.get("insights", []),
                        "recommendations": summary.get("recommendations", []),
                        "timeline": summary.get("timeline", ""),
                        "transformational_phrase": cil.insight_generator.get_transformational_phrase(),
                    })
                except Exception as e:
                    self._json_response({"success": False, "error": str(e)}, 500)
            else:
                self._json_response({"success": False, "error": "CIL not available"}, 503)
            return

        if path == "/cognition/high-impact":
            query = parse_qs(urlparse(self.path).query)
            lang = query.get("lang", ["en"])[0]

            if CIL_AVAILABLE:
                try:
                    cil = CognitiveInterface(lang)
                    insights = cil.insight_generator.generate_high_impact_insights()
                    self._json_response({
                        "success": True,
                        "lang": lang,
                        "insights": insights,
                        "transformational_phrase": cil.insight_generator.get_transformational_phrase(),
                    })
                except Exception as e:
                    self._json_response({"success": False, "error": str(e)}, 500)
            else:
                self._json_response({"success": False, "error": "CIL not available"}, 503)
            return

        if path == "/cognition/addictive":
            query = parse_qs(urlparse(self.path).query)
            lang = query.get("lang", ["en"])[0]

            if CIL_AVAILABLE:
                try:
                    cil = CognitiveInterface(lang)
                    insights = cil.insight_generator.generate_addictive_insights()
                    self._json_response({
                        "success": True,
                        "lang": lang,
                        "insights": insights,
                    })
                except Exception as e:
                    self._json_response({"success": False, "error": str(e)}, 500)
            else:
                self._json_response({"success": False, "error": "CIL not available"}, 503)
            return

        # ─── MESSAGE TEMPLATES ENDPOINT — For HTML Builder distribution ───
        if path == "/message-templates":
            query = parse_qs(urlparse(self.path).query)
            channel = query.get("channel", [None])[0]
            lang = query.get("lang", ["en"])[0]

            templates = list_message_templates(channel=channel, lang=lang)
            self._json_response({
                "success": True,
                "templates": templates,
                "count": len(templates),
                "channels": ["email", "sms", "whatsapp"],
            })
            return

        if path.startswith("/message-templates/") and not path.endswith("/render"):
            # GET /message-templates/{id}
            template_id = path.split("/")[-1]
            query = parse_qs(urlparse(self.path).query)
            lang = query.get("lang", ["en"])[0]

            result = get_message_template(template_id, lang)
            if result.get("found"):
                self._json_response({"success": True, **result})
            else:
                self._json_response({"success": False, "error": result.get("error")}, 404)
            return

        self._json_response({"error": "Not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_length).decode()) if content_length else {}
        except Exception as e:
            self._json_response({"error": f"Invalid JSON: {e}"}, 400)
            return

        # ─── CHAT ENDPOINT ───────────────────────────────────────────────
        if path == "/chat":
            session_id = self.headers.get("X-Session-ID") or body.get("session_id")
            tier = self.headers.get("X-Tier") or body.get("tier", "FREE")
            message = body.get("message", "").strip()

            if not session_id:
                session_id = hashlib.sha256(f"{time.time()}{os.urandom(8).hex()}".encode()).hexdigest()[:32]

            if not message:
                self._json_response({"error": "Message required"}, 400)
                return

            session = get_session(session_id, tier.upper())
            result = process_chat(message, session)
            result["session_id"] = session_id

            self._json_response(result)
            return

        # ─── CONFIRM ACTION ENDPOINT ─────────────────────────────────────
        if path == "/confirm":
            session_id = self.headers.get("X-Session-ID") or body.get("session_id")
            confirmed = body.get("confirmed", False)

            if not session_id or session_id not in SESSIONS:
                self._json_response({"error": "Invalid session"}, 400)
                return

            session = SESSIONS[session_id]
            pending = session.get("pending_action")
            lang = session.get("lang", "de")
            identity = DRAGON_IDENTITY.get(lang, DRAGON_IDENTITY["de"])

            if not pending:
                self._json_response({"error": "No pending action"}, 400)
                return

            if confirmed:
                # Execute via orchestrator if HIGH tier
                if session.get("tier") == "HIGH":
                    # Could trigger full orchestrate pipeline here
                    pass
                response_text = identity["executed"]
            else:
                response_text = identity["cancelled"]

            session["pending_action"] = None
            add_message(session, "system", response_text)

            self._json_response({
                "success": True,
                "executed": confirmed,
                "response": response_text
            })
            return

        # ─── MESSAGE TEMPLATES RENDER — For HTML Builder distribution ─────
        if path == "/message-templates/render":
            template_id = body.get("template_id", "")
            lang = body.get("lang", "en")
            variables = body.get("variables", {})

            if not template_id:
                self._json_response({"success": False, "error": "template_id required"}, 400)
                return

            result = render_message_template(template_id, lang, variables)
            self._json_response(result)
            return

        # ─── DISTRIBUTE ENDPOINT — Send documents via channels ───────────
        if path == "/distribute":
            recipients = body.get("recipients", [])
            doc_title = body.get("doc_title", "")
            doc_content = body.get("doc_content", "")
            receipt_id = body.get("receipt_id", "")
            lang = body.get("lang", "en")
            template_id = body.get("template_id")  # Optional: use template instead of default
            custom_message = body.get("custom_message")  # Optional: custom message body

            if not recipients:
                self._json_response({"success": False, "error": "No recipients provided"}, 400)
                return

            if not doc_title or not receipt_id:
                self._json_response({"success": False, "error": "doc_title and receipt_id required"}, 400)
                return

            # Build verify URL
            verify_url = f"https://windi-domain.com/verify/{receipt_id}"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

            # Use custom message or template if provided
            final_content = doc_content
            if custom_message:
                final_content = custom_message
            elif template_id:
                # Render template with variables
                variables = {
                    "doc_title": doc_title,
                    "doc_preview": doc_content[:300] + "..." if len(doc_content) > 300 else doc_content,
                    "receipt_id": receipt_id,
                    "verify_url": verify_url,
                    "timestamp": timestamp,
                }
                rendered = render_message_template(template_id, lang, variables)
                if rendered.get("success"):
                    final_content = rendered["rendered"]["body"]

            result = distribute_document(recipients, doc_title, final_content, receipt_id, lang)
            result["template_used"] = template_id if template_id else "default"
            result["custom_message_used"] = bool(custom_message)
            self._json_response(result)
            return

        # ─── DISTRIBUTE STATUS ENDPOINT — Check configuration ────────────
        if path == "/distribute/status":
            self._json_response({
                "success": True,
                "channels": {
                    "email": {
                        "configured": bool(SMTP_HOST),
                        "from": SMTP_FROM,
                    },
                    "sms": {
                        "configured": bool(TWILIO_SID and TWILIO_TOKEN),
                    },
                    "whatsapp": {
                        "configured": bool(WHATSAPP_TOKEN and WHATSAPP_PHONE_ID),
                    },
                    "linkedin": {
                        "configured": bool(LINKEDIN_ACCESS_TOKEN),
                        "org_id": LINKEDIN_ORG_ID if LINKEDIN_ORG_ID else None,
                        "features": ["post", "dm"] if LINKEDIN_ACCESS_TOKEN else [],
                    },
                },
                "recent_distributions": DISTRIBUTION_LOG[-10:],
            })
            return

        # ─── WHATSAPP MEDIA ENDPOINTS v1.0.0 ────────────────────────────
        if path == "/whatsapp/send-image":
            # Body: {"to": "+49xxx", "image_url": "https://...", "caption": "..."}
            # OR:   {"to": "+49xxx", "image_id": "meta_media_id", "caption": "..."}
            to = body.get("to", "")
            img_url = body.get("image_url")
            img_id = body.get("image_id")
            caption = body.get("caption", "")

            if not to:
                self._json_response({"success": False, "error": "Field 'to' required"}, 400)
                return

            result = send_whatsapp_image(to, image_url=img_url, image_id=img_id, caption=caption)
            if result.get("success"):
                seal = seal_whatsapp_media_send(to, "image", caption, result.get("message_id", ""))
                result["receipt"] = seal
            self._json_response(result)
            return

        if path == "/whatsapp/send-video":
            # Body: {"to": "+49xxx", "video_url": "https://...", "caption": "..."}
            to = body.get("to", "")
            vid_url = body.get("video_url")
            vid_id = body.get("video_id")
            caption = body.get("caption", "")

            if not to:
                self._json_response({"success": False, "error": "Field 'to' required"}, 400)
                return

            result = send_whatsapp_video(to, video_url=vid_url, video_id=vid_id, caption=caption)
            if result.get("success"):
                seal = seal_whatsapp_media_send(to, "video", caption, result.get("message_id", ""))
                result["receipt"] = seal
            self._json_response(result)
            return

        if path == "/whatsapp/send-document":
            # Body: {"to": "+49xxx", "doc_url": "https://...file.pdf", "caption": "...", "filename": "relatorio.pdf"}
            to = body.get("to", "")
            doc_url = body.get("doc_url")
            doc_id = body.get("doc_id")
            caption = body.get("caption", "")
            filename = body.get("filename", "documento_windi.pdf")

            if not to:
                self._json_response({"success": False, "error": "Field 'to' required"}, 400)
                return

            result = send_whatsapp_document(to, doc_url=doc_url, doc_id=doc_id,
                                            caption=caption, filename=filename)
            if result.get("success"):
                seal = seal_whatsapp_media_send(to, "document", caption, result.get("message_id", ""))
                result["receipt"] = seal
            self._json_response(result)
            return

        if path == "/whatsapp/upload-media":
            # Body JSON: {"file_url": "https://...", "filename": "imagem.jpg", "mime_type": "image/jpeg"}
            # Returns {"media_id": "...", "mime_type": "..."}
            file_url = body.get("file_url")
            filename = body.get("filename", "upload.bin")
            mime_type = body.get("mime_type")

            if file_url:
                try:
                    with urllib.request.urlopen(file_url, timeout=20) as r:
                        file_bytes = r.read()
                    result = upload_media_to_whatsapp(file_bytes, filename, mime_type)
                    self._json_response(result)
                except Exception as e:
                    self._json_response({"success": False, "error": f"Failed to download file: {e}"}, 400)
            else:
                self._json_response({"success": False, "error": "Provide 'file_url' for upload"}, 400)
            return

        if path == "/whatsapp/send":
            # Text-only send (existing compatibility)
            to = body.get("to", "")
            message = body.get("message", "")

            if not to or not message:
                self._json_response({"success": False, "error": "Fields 'to' and 'message' required"}, 400)
                return

            result = send_whatsapp(to, message)
            self._json_response(result)
            return

        # ─── PATCH v1.1.0: BSUID-READY ENDPOINTS ────────────────────────

        if path == "/whatsapp/send-any":
            # Universal send: accepts phone, BSUID, or @username
            # Body: {"to": "+49xxx" | "DE_abc123..." | "@username", "message": "..." OR media fields}
            to = body.get("to", "")
            message = body.get("message")
            media_type = body.get("media_type")
            media_id = body.get("media_id")
            media_url = body.get("media_url") or body.get("image_url") or body.get("video_url") or body.get("doc_url")
            caption = body.get("caption", "")
            filename = body.get("filename")

            if not to:
                self._json_response({"success": False, "error": "Field 'to' required"}, 400)
                return

            result = send_whatsapp_any_id(
                to=to,
                message=message,
                media_type=media_type,
                media_id=media_id,
                media_url=media_url,
                caption=caption,
                filename=filename
            )

            # Seal if successful
            if result.get("success") and (message or media_type):
                seal = seal_whatsapp_media_send(
                    to=to,
                    media_type=media_type or "text",
                    caption=caption or message or "",
                    message_id=result.get("message_id", ""),
                    bsuid=to if result.get("id_type") == "bsuid" else None
                )
                result["receipt"] = seal

            self._json_response(result)
            return

        if path == "/whatsapp/detect-id":
            # Utility: detect identifier type without sending
            # Body: {"recipient": "+49xxx" | "DE_abc123..." | "@username"}
            recipient = body.get("recipient", body.get("to", ""))
            if not recipient:
                self._json_response({"success": False, "error": "Field 'recipient' required"}, 400)
                return

            info = detect_wa_id_type(recipient)
            resolved = resolve_wa_recipient(recipient)
            self._json_response({
                "success": True,
                "recipient": recipient,
                "type": info["type"],
                "resolved": resolved,
                "country": info.get("country"),
            })
            return

        if path == "/whatsapp/webhook":
            # Webhook receiver: parse incoming Meta webhook and extract BSUID
            # POST from Meta: {"entry": [{"changes": [...]}]}
            parsed = parse_wa_webhook(body)
            if "error" in parsed:
                self._json_response({"success": False, "error": parsed["error"]}, 400)
                return

            # Log to distribution log for audit
            DISTRIBUTION_LOG.append({
                "channel": "whatsapp_webhook",
                "direction": "incoming",
                "from": parsed.get("from"),
                "bsuid": parsed.get("bsuid"),
                "id_type": parsed.get("id_type"),
                "message_id": parsed.get("message_id"),
                "type": parsed.get("type"),
                "timestamp": datetime.now().isoformat(),
            })

            self._json_response({
                "success": True,
                "parsed": parsed,
                "bsuid_detected": parsed.get("bsuid") is not None,
            })
            return

        # ─── WHATSAPP TEMPLATE MESSAGES v1.0.0 ────────────────────────────
        # Pre-approved Meta templates for initiating conversations
        # Templates must be submitted to Meta for approval before use

        if path == "/whatsapp/templates":
            # List all available templates
            # Body (optional): {"category": "UTILITY", "lang": "en"}
            category = body.get("category")
            lang = body.get("lang")
            templates = list_templates(category=category, lang=lang)
            self._json_response({
                "success": True,
                "count": len(templates),
                "templates": templates,
                "note": "Templates must be approved by Meta before use"
            })
            return

        if path == "/whatsapp/templates/render":
            # Preview a rendered template before sending
            # Body: {"template": "windi_document_ready", "lang": "de", "variables": {...}}
            template_name = body.get("template")
            lang = body.get("lang", "en")
            variables = body.get("variables", {})

            if not template_name:
                self._json_response({"success": False, "error": "Field 'template' required"}, 400)
                return

            rendered = render_template(template_name, lang, variables)
            if "error" in rendered:
                self._json_response({"success": False, "error": rendered["error"]}, 400)
                return

            self._json_response({
                "success": True,
                "template": template_name,
                "lang": lang,
                "rendered": rendered,
                "preview": True
            })
            return

        if path == "/whatsapp/templates/send":
            # Send a template message to initiate conversation
            # Body: {
            #   "to": "+49xxx" | "DE_abc123..." | "@username",
            #   "template": "windi_document_ready",
            #   "lang": "de",
            #   "variables": {"recipient_name": "Max", "document_title": "Vertrag", ...},
            #   "header_media": {"type": "document", "link": "https://..."} (optional)
            # }
            to = body.get("to")
            template_name = body.get("template")
            lang = body.get("lang", "en")
            variables = body.get("variables", {})
            header_media = body.get("header_media")

            if not to:
                self._json_response({"success": False, "error": "Field 'to' required"}, 400)
                return

            if not template_name:
                self._json_response({"success": False, "error": "Field 'template' required"}, 400)
                return

            result = send_whatsapp_template(
                to=to,
                template_name=template_name,
                lang=lang,
                variables=variables,
                header_media=header_media
            )

            # Seal if successful
            if result.get("success"):
                seal = seal_whatsapp_media_send(
                    to=to,
                    media_type="template",
                    caption=f"Template: {template_name} ({lang})",
                    message_id=result.get("message_id", ""),
                    bsuid=to if result.get("id_type") == "bsuid" else None
                )
                result["receipt"] = seal

            self._json_response(result)
            return

        # Get specific template by name: /whatsapp/templates/{template_name}
        # NOTE: Must come AFTER /render and /send routes
        if path.startswith("/whatsapp/templates/") and path.count("/") == 3:
            template_name = path.split("/")[-1]
            lang = body.get("lang", "en")
            template = get_template(template_name, lang)
            if template:
                self._json_response({
                    "success": True,
                    "template": template,
                    "lang": lang
                })
            else:
                self._json_response({
                    "success": False,
                    "error": f"Template '{template_name}' not found",
                    "available": list_templates()
                }, 404)
            return

        # ─── CLEAR SESSION ENDPOINT ──────────────────────────────────────
        if path == "/clear":
            session_id = self.headers.get("X-Session-ID") or body.get("session_id")
            if session_id and session_id in SESSIONS:
                del SESSIONS[session_id]
            self._json_response({"success": True, "message": "Session cleared"})
            return

        self._json_response({"error": "Not found"}, 404)

    def log_message(self, format, *args):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[DragonChat v2] {ts} {args[0]}")


# ═══════════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 74)
    print("  WINDI DRAGON CHAT SERVICE v2.0 — 'Liberar a Porteira'")
    print("=" * 74)
    print(f"\n  Port: {PORT}")
    print(f"  Tier: {WINDI_TIER} — {get_gate()['label']}")
    print(f"  Version: {VERSION}")
    print(f"\n  Ecosystem Connections (Actions #1-#3):")
    print(f"    #1 Orchestrator: {ORCHESTRATOR_URL}")
    print(f"    #2 Lang Detect:  {LANG_DETECT_SOURCE}")
    print(f"    #3 Intent Parse: {'available' if INTENT_PARSER_AVAILABLE else 'fallback'}")
    print("\n  Constitutional Principles:")
    print("    1. Suggests, never executes without confirmation")
    print("    2. Never shows brand (WINDI identity only)")
    print("    3. Session memory, not surveillance (ephemeral)")
    print("    4. Respects tier (FREE→local, MED→generate, HIGH→orchestrate)")
    print("    5. Speaks user's language (6 languages supported)")
    print("\n  Endpoints:")
    print("    GET  /health   — Service health + architecture")
    print("    POST /chat     — Main chat endpoint")
    print("    POST /confirm  — Confirm/cancel pending action")
    print("    POST /clear    — Clear session")
    print("\n" + "=" * 74)
    print(f"  42 muscles trained. Mouth unstitched. → http://localhost:{PORT}/")
    print("=" * 74 + "\n")

    server = HTTPServer(("0.0.0.0", PORT), DragonChatHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[DragonChat v2] Shutting down gracefully...")
        server.shutdown()


if __name__ == "__main__":
    main()
