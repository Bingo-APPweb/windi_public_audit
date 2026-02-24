#!/usr/bin/env python3
"""
WINDI Sovereign Router v1.1
============================

v1.1 Changelog (Guardian Audit):
  - FIX A: Removed unused get_local_handler() mapping
  - FIX B: Render parsing separates command from payload
  - FIX C: Service URLs from environment
  - FIX D: Single language detector
  - FIX E: Tier trust with signed header validation
  - FIX F: S02/S03 patterns added for semantic intents
  - FIX G: Semantic fallback executes local work
  - FIX H: Sovereign-by-default for ALL tiers

Principio: "Integridade e universal. Interpretacao e premium."
Invariante I10: Continuidade — degradacao != erro, = transicao soberana.
Ratio Auditado: 93.3% local (42 funcoes) / 6.7% semantico (3 funcoes LLM)

Deploy: /opt/windi/agent-palette/sovereign_router.py
Sealed: AUDIT-SOVEREIGNTY-20260224
"""

import os
import re
from enum import Enum
from typing import Tuple, Dict, Optional, List

__version__ = "1.1.0"
__author__ = "WINDI Publishing House"


# ═══════════════════════════════════════════════════════════════
#  SERVICE URLS (from environment, FIX C)
# ═══════════════════════════════════════════════════════════════

LEDGER_URL = os.environ.get("WINDI_LEDGER_URL", "http://localhost:8101")
VAULT_URL = os.environ.get("WINDI_VAULT_URL", "http://localhost:8106")
COMMUNIQUE_URL = os.environ.get("WINDI_COMMUNIQUE_URL", "http://localhost:8105")
OCR_URL = os.environ.get("WINDI_OCR_URL", "http://localhost:8095")
SENTINEL_URL = os.environ.get("WINDI_SENTINEL_URL", "http://localhost:8102")
WAR_ROOM_URL = os.environ.get("WINDI_WARROOM_URL", "http://localhost:8090")
WALLET_URL = os.environ.get("WINDI_WALLET_URL", "http://localhost:8099")
CLONE_URL = os.environ.get("WINDI_CLONE_URL", "http://localhost:8092")
BRIDGE_URL = os.environ.get("WINDI_BRIDGE_URL", "http://localhost:8097")
LANDING_URL = os.environ.get("WINDI_LANDING_URL", "http://localhost:8107")
GENESIS_URL = os.environ.get("WINDI_GENESIS_URL", "http://localhost:8096")
CORTEX_URL = os.environ.get("WINDI_CORTEX_URL", "http://localhost:8889")

# Trusted tier header name (FIX E)
TIER_HEADER = "X-WINDI-TIER"
TIER_SECRET = os.environ.get("WINDI_TIER_SECRET", "")


# ═══════════════════════════════════════════════════════════════
#  ENUMS
# ═══════════════════════════════════════════════════════════════

class Intent(Enum):
    """45 total intents: 42 local + 3 semantic."""

    # Document Production (4 local)
    GENERATE_PDF = "generate_pdf"
    GENERATE_DOCX = "generate_docx"
    GENERATE_PPTX = "generate_pptx"
    GENERATE_XLSX = "generate_xlsx"

    # Seal & Forensic (6 local)
    SEAL_DOCUMENT = "seal_document"
    QUERY_LEDGER = "query_ledger"
    VERIFY_HASH = "verify_hash"
    STORE_VAULT = "store_vault"
    SEAL_PIPELINE = "seal_pipeline"
    DOWNLOAD_FILE = "download_file"

    # Governance & Compliance (8 local)
    CHECK_COMPLIANCE = "check_compliance"
    CHECK_INVARIANTS = "check_invariants"
    CHECK_RISK = "check_risk"
    AUTONOMY_SCORE = "autonomy_score"
    METADATA_CLASSIFY = "metadata_classify"
    SENTINEL_STATUS = "sentinel_status"
    I9_CHECK = "i9_check"
    SGE_ANALYZE = "sge_analyze"

    # Dashboards & Reporting (6 local)
    PULSE_REPORT = "pulse_report"
    OUTLOOK_REPORT = "outlook_report"
    HEALTH_CHECK = "health_check"
    WIRING_STATUS = "wiring_status"
    WAR_ROOM = "war_room"
    BUDGET_STATUS = "budget_status"

    # Workflow & Pipeline (8 local)
    COMMUNIQUE_CREATE = "communique_create"
    COMMUNIQUE_REVIEW = "communique_review"
    COMMUNIQUE_PUBLISH = "communique_publish"
    OCR_DOCUMENT = "ocr_document"
    ISP_SELECT = "isp_select"
    ISP_LIST = "isp_list"
    AUTOCAT_CLASSIFY = "autocat_classify"
    PAPERLESS_BRIDGE = "paperless_bridge"

    # Infrastructure & System (10 local)
    TRILINGUAL_DETECT = "trilingual_detect"
    THEME_TOGGLE = "theme_toggle"
    DRAGON_IDENTITY = "dragon_identity"
    COMMAND_BRIDGE = "command_bridge"
    WALLET_CHECK = "wallet_check"
    CLONE_STATUS = "clone_status"
    LANDING_INFO = "landing_info"
    ID_GENESIS = "id_genesis"
    CORTEX_STATUS = "cortex_status"
    HELP = "help"

    # Semantic / LLM Required (3)
    CHAT_INTERPRETIVE = "chat_interpretive"
    SEMANTIC_ANALYSIS = "semantic_analysis"
    TEXT_GENERATION = "text_generation"


class Tier(Enum):
    """WINDI service tiers."""
    PERSONAL = "personal"
    PROFESSIONAL = "professional"
    GOVERNANCE = "governance"


class SovereigntyLevel(Enum):
    """How the response was generated."""
    SOVEREIGN = "sovereign"
    SOVEREIGN_FALLBACK = "sovereign_fallback"
    SEMANTIC = "semantic"


# ═══════════════════════════════════════════════════════════════
#  INTENT SETS
# ═══════════════════════════════════════════════════════════════

SEMANTIC_INTENTS = frozenset({
    Intent.CHAT_INTERPRETIVE,
    Intent.SEMANTIC_ANALYSIS,
    Intent.TEXT_GENERATION,
})

LOCAL_INTENTS = frozenset(set(Intent) - SEMANTIC_INTENTS)

DOCUMENT_INTENTS = frozenset({
    Intent.GENERATE_PDF,
    Intent.GENERATE_DOCX,
    Intent.GENERATE_PPTX,
    Intent.GENERATE_XLSX,
})

# FIX G: Maps semantic intent to best local alternative
SEMANTIC_TO_LOCAL_FALLBACK: Dict[Intent, Intent] = {
    Intent.CHAT_INTERPRETIVE: Intent.HELP,
    Intent.SEMANTIC_ANALYSIS: Intent.CHECK_RISK,
    Intent.TEXT_GENERATION: Intent.HELP,
}


# ═══════════════════════════════════════════════════════════════
#  INTENT CLASSIFICATION
# ═══════════════════════════════════════════════════════════════

INTENT_PATTERNS: Dict[Intent, List[str]] = {
    # Document generation
    Intent.GENERATE_PDF: [
        r'\b(gerar?\s*pdf|criar?\s*pdf|create\s*pdf|pdf\s*(erstellen|erzeugen)|exportar?\s*pdf)\b',
        r'\b(relat[oó]rio|report|bericht)\b.*\b(pdf)\b',
        r'\bpdf\b',
    ],
    Intent.GENERATE_DOCX: [
        r'\b(gerar?\s*doc|criar?\s*doc|create\s*doc|doc[x]?\s*erstellen)\b',
        r'\b(word\s*(document|dokument|documento))\b',
        r'\bdocx\b',
    ],
    Intent.GENERATE_PPTX: [
        r'\b(pptx|apresenta[cç][aã]o|presentation|pr[aä]sentation|slides?|deck)\b',
        r'\b(criar?\s*slide|create\s*slide|folie[n]?\s*erstellen)\b',
    ],
    Intent.GENERATE_XLSX: [
        r'\b(xlsx|excel|spreadsheet|planilha|tabelle|tabellenkalkulation)\b',
    ],

    # Seal & Forensic
    Intent.SEAL_DOCUMENT: [
        r'\b(seal|selar|selo|siegel|versiegeln|stamp|carimbar)\b',
        r'\b(assinar?\s*document|sign\s*document|dokument\s*signieren)\b',
    ],
    Intent.SEAL_PIPELINE: [
        r'\b(seal\s*pipeline|pipeline.*seal|n1.*n4|wave\s*1)\b',
        r'\b(full\s*seal|selo\s*completo|vollst[aä]ndig.*versiegeln)\b',
    ],
    Intent.QUERY_LEDGER: [
        r'\b(ledger|recibo|receipt|quittung|beleg)\b',
        r'\b(forensic|forense|forensisch)\b.*\b(buscar?|search|suchen|query)\b',
        r'\b(listar?\s*recib|list\s*receipt|quittungen\s*auflisten)\b',
    ],
    Intent.VERIFY_HASH: [
        r'\b(verify|verificar|[uü]berpr[uü]fen|validar)\b.*\b(hash|sha|integrity|integridade)\b',
    ],
    Intent.STORE_VAULT: [
        r'\b(vault|cofre|tresor)\b.*\b(store|guardar|speichern|armazenar)\b',
    ],

    # Governance
    Intent.CHECK_COMPLIANCE: [
        r'\b(compliance|conformidade|konformit[aä]t|passport)\b',
        r'\b(eu\s*ai\s*act|regulament)\b',
    ],
    Intent.CHECK_INVARIANTS: [
        r'\b(invariant[es]?|invariante[ns]?)\b',
        r'\b(i[1-9]|i10)\s*(check|status|verificar|pr[uü]fen)\b',
    ],
    Intent.CHECK_RISK: [
        r'\b(risk|risco|risiko)\b.*\b(r[0-5]|classif|level)\b',
        r'\b(sge)\b.*\b(analys|an[aá]lis|analyz)\b',
    ],
    Intent.SGE_ANALYZE: [
        r'\b(sge)\b',
        r'\b(semantic\s*governance|governan[cç]a\s*sem[aâ]ntica)\b',
    ],
    Intent.AUTONOMY_SCORE: [
        r'\b(autonom|soberan|sovereignty|autonomy|unabh[aä]ngigkeit)\b',
        r'\b(93|42\s*(de|of|von)\s*45|ratio)\b',
    ],
    Intent.SENTINEL_STATUS: [
        r'\b(sentinel|sentinela|w[aä]chter)\b',
    ],
    Intent.I9_CHECK: [
        r'\bi9\b',
        r'\b(escalation|escala[cç][aã]o|eskalation)\b',
    ],
    Intent.METADATA_CLASSIFY: [
        r'\b(metadata|metadados|metadaten)\b.*\b(classif|kategor)\b',
    ],

    # Dashboards
    Intent.PULSE_REPORT: [
        r'\b(pulse|pulso|puls)\b',
        r'\b(system\s*status|estado\s*do\s*sistema|systemstatus)\b',
    ],
    Intent.OUTLOOK_REPORT: [
        r'\b(outlook|perspectiva|ausblick)\b',
        r'\b(roadmap|sprint|product\s*status)\b',
    ],
    Intent.HEALTH_CHECK: [
        r'\b(health|sa[uú]de|gesundheit|diagnos)\b',
        r'\b(servi[cç]os?|services?|dienste?)\b.*\b(status|up|down)\b',
    ],
    Intent.WIRING_STATUS: [
        r'\b(wir(ing|e|ed)|conex[oõ]es?|verdrahtung)\b',
    ],
    Intent.WAR_ROOM: [
        r'\b(war\s*room|sala\s*de\s*guerra|kriegsraum)\b',
    ],
    Intent.BUDGET_STATUS: [
        r'\b(budget|or[cç]amento|token|cr[eé]dito|verbrauch)\b',
    ],

    # Workflow
    Intent.COMMUNIQUE_CREATE: [
        r'\b(communiqu[eé]|comunicado|mitteilung)\b.*\b(criar?|create|erstellen|new|nov)\b',
        r'\b(criar?\s*communiqu[eé]|create\s*communiqu[eé])\b',
    ],
    Intent.COMMUNIQUE_REVIEW: [
        r'\b(communiqu[eé]|comunicado|mitteilung)\b.*\b(review|revisar|pr[uü]fen|rever)\b',
    ],
    Intent.COMMUNIQUE_PUBLISH: [
        r'\b(communiqu[eé]|comunicado|mitteilung)\b.*\b(publish|publicar|ver[oö]ffentlichen)\b',
    ],
    Intent.OCR_DOCUMENT: [
        r'\b(ocr|digitalizar?|scan|escanear?|erkennung)\b',
        r'\b(extrair?\s*text|extract\s*text|text\s*erkennen)\b',
    ],
    Intent.ISP_SELECT: [
        r'\b(isp|template|modelo|vorlage)\b.*\b(institucional|institutional)\b',
        r'\b(perfil\s*institucional|institutional\s*profile|institutionsprofil)\b',
    ],
    Intent.ISP_LIST: [
        r'\b(isp|templates?|modelos?|vorlagen?)\b.*\b(list|listar?|auflisten)\b',
    ],
    Intent.AUTOCAT_CLASSIFY: [
        r'\b(autocat|auto\s*classif|categorizar?|kategorisieren)\b',
    ],
    Intent.PAPERLESS_BRIDGE: [
        r'\b(paperless|schnittstelle|connector|bridge\s*paper)\b',
    ],

    # System
    Intent.HELP: [
        r'\b(help|ajuda|hilfe)\b',
        r'\b(o\s+que\s+(podes?|consegue)|what\s+can\s+you|was\s+kannst?\s+du)\b',
        r'\b(funcion|capabilit|f[aä]higkeit|capacidade)\b',
        r'\b(ol[aá]|hello|hallo|hi\b|oi\b|bom\s*dia|good\s*morning|guten\s*morgen)\b',
    ],
    Intent.DRAGON_IDENTITY: [
        r'\b(dragon|drag[aã]o|drache|guardian|architect|witness)\b.*\b(who|quem|wer|identit)\b',
        r'\b(three\s*dragons|tr[eê]s\s*drag[oõ]es|drei\s*drachen)\b',
    ],
    Intent.WALLET_CHECK: [
        r'\b(wallet|carteira|espelho|geldb[oö]rse)\b',
    ],
    Intent.CLONE_STATUS: [
        r'\b(clone|klon|clon)\b.*\b(status|estado|zustand)\b',
    ],
    Intent.COMMAND_BRIDGE: [
        r'\b(command\s*bridge|ponte\s*de\s*comando|befehlsbr[uü]cke)\b',
    ],

    # FIX F: Semantic intents WITH patterns
    Intent.SEMANTIC_ANALYSIS: [
        r'\b(analis[ae]\s*(profundamente|sem[aâ]ntic|semantic|detalhad))\b',
        r'\b(interpret[ae]|explica\s*risco|risk\s*narrative|risikoanalyse)\b',
        r'\b(deep\s*analy[sz]|tiefenanalyse|an[aá]lise\s*profunda)\b',
    ],
    Intent.TEXT_GENERATION: [
        r'\b(escreve|redige|reformula|gerar?\s*texto|write\s*a\s*text|verfassen)\b',
        r'\b(draft|rascunho|entwurf)\b.*\b(text|narrativa|narrative)\b',
        r'\b(genera?te?\s*(text|content|conte[uú]do)|text\s*generieren)\b',
    ],
}


def classify_intent(message: str, tier: Tier = Tier.PERSONAL) -> Tuple[Intent, bool]:
    """
    Classify user intent. Sovereign-by-default for ALL tiers (FIX H).
    Returns: (Intent, is_local)
    """
    msg_lower = message.lower().strip()

    if not msg_lower:
        return (Intent.HELP, True)

    best_intent: Optional[Intent] = None
    best_score = 0

    for intent, patterns in INTENT_PATTERNS.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, msg_lower, re.IGNORECASE):
                score += 1
        if score > best_score:
            best_score = score
            best_intent = intent

    # LOCAL intent matched -> always local
    if best_intent and best_intent in LOCAL_INTENTS:
        return (best_intent, True)

    # SEMANTIC intent matched
    if best_intent and best_intent in SEMANTIC_INTENTS:
        if tier == Tier.PERSONAL:
            fallback = SEMANTIC_TO_LOCAL_FALLBACK.get(best_intent, Intent.HELP)
            return (fallback, True)
        return (best_intent, False)

    # No match -> default by tier
    if tier == Tier.PERSONAL:
        return (Intent.HELP, True)
    else:
        return (Intent.CHAT_INTERPRETIVE, False)


# ═══════════════════════════════════════════════════════════════
#  TIER TRUST (FIX E)
# ═══════════════════════════════════════════════════════════════

def resolve_tier(request_data: dict, headers: Optional[dict] = None) -> Tier:
    """Resolve tier with trust validation (FIX E)."""
    if headers and TIER_HEADER in headers:
        header_tier = headers[TIER_HEADER].lower().strip()
        if TIER_SECRET:
            sig = headers.get("X-WINDI-TIER-SIG", "")
            if not _verify_tier_signature(header_tier, sig):
                return Tier.PERSONAL
        return _parse_tier(header_tier)

    if not TIER_SECRET:
        json_tier = request_data.get("tier", "personal").lower().strip()
        return _parse_tier(json_tier)

    return Tier.PERSONAL


def _parse_tier(tier_str: str) -> Tier:
    return {
        "personal": Tier.PERSONAL,
        "professional": Tier.PROFESSIONAL,
        "governance": Tier.GOVERNANCE,
    }.get(tier_str, Tier.PERSONAL)


def _verify_tier_signature(tier: str, signature: str) -> bool:
    if not TIER_SECRET or not signature:
        return False
    import hmac
    import hashlib
    expected = hmac.new(TIER_SECRET.encode(), tier.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


# ═══════════════════════════════════════════════════════════════
#  RENDER PARSING (FIX B)
# ═══════════════════════════════════════════════════════════════

FORMAT_MAP: Dict[Intent, str] = {
    Intent.GENERATE_PDF: "pdf",
    Intent.GENERATE_DOCX: "docx",
    Intent.GENERATE_PPTX: "pptx",
    Intent.GENERATE_XLSX: "xlsx",
}

COMMAND_STRIP_PATTERNS = [
    r'^(criar?|create|erstellen|gerar?|generate|exportar?|machen?)\s+',
    r'\b(um|uma|ein|eine|a|an)\s+',
    r'\b(pdf|docx|pptx|xlsx|word|excel|presentation|apresenta[cç][aã]o|pr[aä]sentation)\b',
    r'\b(document|documento|dokument)\b',
    r'\b(por\s*favor|please|bitte)\b',
    r'^\s+|\s+$',
]


def get_format(intent: Intent) -> Optional[str]:
    return FORMAT_MAP.get(intent)


def get_handler(intent: Intent) -> str:
    """Return handler name for an intent (for response metadata)."""
    if intent in (Intent.GENERATE_PDF, Intent.GENERATE_DOCX,
                  Intent.GENERATE_PPTX, Intent.GENERATE_XLSX):
        return "document_renderer"
    elif intent in (Intent.SEAL_DOCUMENT, Intent.SEAL_PIPELINE):
        return "seal_engine"
    elif intent in (Intent.QUERY_LEDGER, Intent.VERIFY_HASH):
        return "ledger_api"
    elif intent in (Intent.STORE_VAULT, Intent.DOWNLOAD_FILE):
        return "vault_api"
    elif intent in (Intent.CHAT_INTERPRETIVE, Intent.SEMANTIC_ANALYSIS, Intent.TEXT_GENERATION):
        return "llm_semantic"
    elif intent in (Intent.PULSE_REPORT, Intent.HEALTH_CHECK, Intent.WIRING_STATUS):
        return "pulse_monitor"
    elif intent in (Intent.OUTLOOK_REPORT,):
        return "outlook_api"
    elif intent == Intent.OCR_DOCUMENT:
        return "multimodal_engine"
    elif intent in (Intent.COMMUNIQUE_CREATE, Intent.COMMUNIQUE_REVIEW, Intent.COMMUNIQUE_PUBLISH):
        return "communique_engine"
    elif intent in (Intent.CHECK_COMPLIANCE, Intent.CHECK_INVARIANTS, Intent.CHECK_RISK,
                    Intent.AUTONOMY_SCORE, Intent.SGE_ANALYZE, Intent.I9_CHECK):
        return "governance_engine"
    elif intent == Intent.HELP:
        return "help_local"
    else:
        return "sovereign_local"


def parse_render_request(message: str, request_data: dict, intent: Intent) -> dict:
    """Parse document generation request (FIX B)."""
    fmt = FORMAT_MAP.get(intent, "docx")

    explicit_title = request_data.get("title", "").strip()
    explicit_content = request_data.get("content", "").strip()

    if explicit_title or explicit_content:
        return {
            "format": fmt,
            "title": explicit_title or f"WINDI {fmt.upper()} Document",
            "content": explicit_content or explicit_title,
            "needs_input": False,
        }

    cleaned = message
    for pattern in COMMAND_STRIP_PATTERNS:
        cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    if len(cleaned) > 10:
        return {
            "format": fmt,
            "title": cleaned[:80],
            "content": cleaned,
            "needs_input": False,
        }

    return {
        "format": fmt,
        "title": "",
        "content": "",
        "needs_input": True,
    }


# ═══════════════════════════════════════════════════════════════
#  LANGUAGE DETECTION (FIX D: single detector)
# ═══════════════════════════════════════════════════════════════

PT_MARKERS = frozenset([
    'pode', 'criar', 'gerar', 'como', 'preciso', 'quero', 'fazer',
    'ajuda', 'documento', 'obrigado', 'por', 'favor', 'bom',
    'dia', 'boa', 'tarde', 'noite', 'verificar', 'mostrar', 'listar',
    'qual', 'quais', 'quando', 'onde', 'porque', 'sistema', 'estado',
    'selar', 'selo', 'recibo', 'risco', 'governanca', 'relatorio',
])

DE_MARKERS = frozenset([
    'kann', 'kannst', 'erstellen', 'bitte', 'hilfe', 'dokument', 'wie',
    'brauche', 'mochte', 'machen', 'danke', 'guten', 'morgen',
    'tag', 'abend', 'zeigen', 'prufen', 'status', 'welche',
    'wann', 'warum', 'konnen', 'soll', 'bericht', 'uberprufen',
    'versiegeln', 'siegel', 'quittung', 'risiko', 'governance',
    'nicht', 'auch', 'noch', 'oder', 'aber', 'schon',
])


def detect_language(text: str) -> str:
    """Single trilingual detector (FIX D)."""
    words = set(text.lower().split())
    pt_score = len(words & PT_MARKERS)
    de_score = len(words & DE_MARKERS)

    if pt_score > de_score and pt_score > 0:
        return "pt"
    elif de_score > pt_score and de_score > 0:
        return "de"
    return "en"


# ═══════════════════════════════════════════════════════════════
#  RESPONSE TEMPLATES
# ═══════════════════════════════════════════════════════════════

HELP_RESPONSES: Dict[str, str] = {
    "de": (
        "**WINDI Governance Terminal - Dein Souveraner Assistent**\n\n"
        "Ich kann dir sofort helfen mit:\n\n"
        "**Dokumente:** PDF, DOCX, PPTX, XLSX erstellen\n"
        "**Versiegeln:** SHA-256 + Seriennummer + QR-Code + Forensic Ledger\n"
        "**Compliance:** Governance Score, Invarianten, Risiko (R0-R5)\n"
        "**Dashboards:** Pulse, Outlook, Health, War Room\n"
        "**Workflows:** Communique, OCR, ISP Templates\n\n"
        "Alles lauft lokal. Keine externe API. Volle Souveranitat.\n\n"
        "Was mochtest du tun?"
    ),
    "en": (
        "**WINDI Governance Terminal - Your Sovereign Assistant**\n\n"
        "I can help you right now with:\n\n"
        "**Documents:** Create PDF, DOCX, PPTX, XLSX\n"
        "**Sealing:** SHA-256 + serial number + QR code + Forensic Ledger\n"
        "**Compliance:** Governance score, invariants, risk (R0-R5)\n"
        "**Dashboards:** Pulse, Outlook, Health, War Room\n"
        "**Workflows:** Communique, OCR, ISP Templates\n\n"
        "Everything runs locally. No external API. Full sovereignty.\n\n"
        "What would you like to do?"
    ),
    "pt": (
        "**WINDI Governance Terminal - O Teu Assistente Soberano**\n\n"
        "Posso ajudar-te agora mesmo com:\n\n"
        "**Documentos:** Criar PDF, DOCX, PPTX, XLSX\n"
        "**Selagem:** SHA-256 + numero de serie + QR code + Forensic Ledger\n"
        "**Compliance:** Governance score, invariantes, risco (R0-R5)\n"
        "**Dashboards:** Pulse, Outlook, Health, War Room\n"
        "**Workflows:** Communique, OCR, ISP Templates\n\n"
        "Tudo corre localmente. Sem API externa. Soberania total.\n\n"
        "O que desejas fazer?"
    ),
}

FALLBACK_MESSAGES: Dict[str, str] = {
    "de": (
        "Ich arbeite gerade im souveranen Modus - keine externe API verfugbar.\n"
        "Ich kann dir trotzdem helfen mit lokalen Funktionen:\n"
        "Dokumente erstellen, versiegeln, Compliance prufen, Dashboards anzeigen.\n\n"
        "Was mochtest du tun?"
    ),
    "en": (
        "I'm currently in sovereign mode - no external API available.\n"
        "I can still help you with local functions:\n"
        "Create documents, seal them, check compliance, show dashboards.\n\n"
        "What would you like to do?"
    ),
    "pt": (
        "Estou em modo soberano - sem API externa disponivel.\n"
        "Posso ajudar-te com funcoes locais:\n"
        "Criar documentos, selar, verificar compliance, mostrar dashboards.\n\n"
        "O que desejas fazer?"
    ),
}

RENDER_INPUT_PROMPTS: Dict[str, Dict[str, str]] = {
    "pdf": {
        "de": "Ich erstelle gerne ein PDF. Was soll der Inhalt sein?",
        "en": "I'll create a PDF. What should the content be?",
        "pt": "Vou criar um PDF. Qual deve ser o conteudo?",
    },
    "docx": {
        "de": "Ich erstelle gerne ein Word-Dokument. Was soll der Inhalt sein?",
        "en": "I'll create a Word document. What should the content be?",
        "pt": "Vou criar um documento Word. Qual deve ser o conteudo?",
    },
    "pptx": {
        "de": "Ich erstelle gerne eine Prasentation. Was ist das Thema?",
        "en": "I'll create a presentation. What's the topic?",
        "pt": "Vou criar uma apresentacao. Qual e o tema?",
    },
    "xlsx": {
        "de": "Ich erstelle gerne eine Tabelle. Welche Daten soll sie enthalten?",
        "en": "I'll create a spreadsheet. What data should it contain?",
        "pt": "Vou criar uma tabela. Que dados deve conter?",
    },
}

FALLBACK_WITH_ACTION: Dict[str, str] = {
    "de": (
        "Ich habe deine Anfrage mit lokaler Governance bearbeitet.\n"
        "Hier sind die Ergebnisse:\n\n{local_result}\n\n"
        "Fur KI-erweiterte Interpretation steht der Professional-Tier zur Verfugung."
    ),
    "en": (
        "I've processed your request with local governance.\n"
        "Here are the results:\n\n{local_result}\n\n"
        "For AI-enhanced interpretation, the Professional tier is available."
    ),
    "pt": (
        "Processei o teu pedido com governanca local.\n"
        "Aqui estao os resultados:\n\n{local_result}\n\n"
        "Para interpretacao amplificada por IA, o tier Professional esta disponivel."
    ),
}


# ═══════════════════════════════════════════════════════════════
#  SOVEREIGNTY METADATA
# ═══════════════════════════════════════════════════════════════

def sovereignty_metadata(llm_used: bool = False) -> dict:
    return {
        "total_functions": 45,
        "local_functions": 42,
        "semantic_functions": 3,
        "ratio": "93.3%",
        "llm_used": llm_used,
        "audit_ref": "AUDIT-SOVEREIGNTY-20260224",
        "principle": "Integridade e universal. Interpretacao e premium.",
        "i10": "Continuidade - degradacao != erro, = transicao soberana.",
    }


def capabilities_response() -> dict:
    return {
        "version": __version__,
        "sovereignty": sovereignty_metadata(),
        "capabilities": {
            "documents": ["PDF", "DOCX", "PPTX", "XLSX"],
            "sealing": ["SHA-256 hashing", "Serial numbers", "QR codes", "Forensic Ledger", "Vault storage"],
            "governance": ["9 Invariants", "I10 Continuity", "8 Stability Layers", "SGE R0-R5", "Compliance Passport"],
            "dashboards": ["Pulse", "Outlook", "Health", "Wiring", "War Room"],
            "workflows": ["Communique", "OCR", "ISP Templates", "AutoCat", "Seal Pipeline"],
        },
        "tiers": {
            "personal": {"price": "Free", "functions": 42, "llm": False},
            "professional": {"price": "EUR 25-40/user", "functions": 45, "llm": True},
            "governance": {"price": "EUR 80-120/user", "functions": 45, "llm": True},
        },
    }


# ═══════════════════════════════════════════════════════════════
#  SELF-TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"WINDI Sovereign Router v{__version__}")
    print(f"Local: {len(LOCAL_INTENTS)} | Semantic: {len(SEMANTIC_INTENTS)} | Total: {len(Intent)}")
    print()

    tests = [
        ("Criar um PDF", Tier.PERSONAL, True),
        ("o que podes fazer?", Tier.PERSONAL, True),
        ("analisa profundamente este texto", Tier.PERSONAL, True),
        ("analisa profundamente este texto", Tier.GOVERNANCE, False),
    ]

    for msg, tier, expected in tests:
        intent, is_local = classify_intent(msg, tier)
        ok = "PASS" if is_local == expected else "FAIL"
        print(f"  [{ok}] {msg[:40]} -> {intent.value} (local={is_local})")

    print(f"\nRatio: {len(LOCAL_INTENTS)}/{len(Intent)} = {len(LOCAL_INTENTS)/len(Intent)*100:.1f}% sovereign")
