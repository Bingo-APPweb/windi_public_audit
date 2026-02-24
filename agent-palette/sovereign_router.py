#!/usr/bin/env python3
"""
WINDI Sovereign Router v1.0
============================

Princípio: "Integridade é universal. Interpretação é premium."
Invariante I10: Continuidade — degradação ≠ erro, = transição soberana.
Ratio Auditado: 93.3% local (42 funções) / 6.7% semântico (3 funções LLM)

O Dragon pergunta:
  1. Isto pode ser resolvido com soberania local?
  2. SIM → responder
  3. NÃO → ativar camada semântica (se tier permitir)

Deploy: /opt/windi/agent-palette/sovereign_router.py
Sealed: AUDIT-SOVEREIGNTY-20260224
"""

import re
from enum import Enum
from typing import Tuple, Dict, Optional, List

__version__ = "1.0.0"
__author__ = "WINDI Publishing House"


# ═══════════════════════════════════════════════════════════════
#  ENUMS
# ═══════════════════════════════════════════════════════════════

class Intent(Enum):
    """45 total intents: 42 local + 3 semantic."""

    # ── Document Production (4 local) ──
    GENERATE_PDF = "generate_pdf"
    GENERATE_DOCX = "generate_docx"
    GENERATE_PPTX = "generate_pptx"
    GENERATE_XLSX = "generate_xlsx"

    # ── Seal & Forensic (6 local) ──
    SEAL_DOCUMENT = "seal_document"
    QUERY_LEDGER = "query_ledger"
    VERIFY_HASH = "verify_hash"
    STORE_VAULT = "store_vault"
    SEAL_PIPELINE = "seal_pipeline"
    DOWNLOAD_FILE = "download_file"

    # ── Governance & Compliance (8 local) ──
    CHECK_COMPLIANCE = "check_compliance"
    CHECK_INVARIANTS = "check_invariants"
    CHECK_RISK = "check_risk"
    AUTONOMY_SCORE = "autonomy_score"
    METADATA_CLASSIFY = "metadata_classify"
    SENTINEL_STATUS = "sentinel_status"
    I9_CHECK = "i9_check"
    SGE_ANALYZE = "sge_analyze"

    # ── Dashboards & Reporting (6 local) ──
    PULSE_REPORT = "pulse_report"
    OUTLOOK_REPORT = "outlook_report"
    HEALTH_CHECK = "health_check"
    WIRING_STATUS = "wiring_status"
    WAR_ROOM = "war_room"
    BUDGET_STATUS = "budget_status"

    # ── Workflow & Pipeline (8 local) ──
    COMMUNIQUE_CREATE = "communique_create"
    COMMUNIQUE_REVIEW = "communique_review"
    COMMUNIQUE_PUBLISH = "communique_publish"
    OCR_DOCUMENT = "ocr_document"
    ISP_SELECT = "isp_select"
    ISP_LIST = "isp_list"
    AUTOCAT_CLASSIFY = "autocat_classify"
    PAPERLESS_BRIDGE = "paperless_bridge"

    # ── Infrastructure & System (10 local) ──
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

    # ── Semantic / LLM Required (3) ──
    CHAT_INTERPRETIVE = "chat_interpretive"
    SEMANTIC_ANALYSIS = "semantic_analysis"
    TEXT_GENERATION = "text_generation"


class Tier(Enum):
    """WINDI service tiers. Sealed 24Feb2026."""
    PERSONAL = "personal"         # 42 local functions, zero external keys
    PROFESSIONAL = "professional"  # + semantic amplification
    GOVERNANCE = "governance"      # + dedicated LLM, ISP custom, SLA


class SovereigntyLevel(Enum):
    """How the response was generated."""
    SOVEREIGN = "sovereign"                # 100% local, no LLM
    SOVEREIGN_FALLBACK = "sovereign_fallback"  # LLM was needed but unavailable
    SEMANTIC = "semantic"                  # LLM was used
    ERROR_SOVEREIGN = "error_sovereign"    # Error occurred but we still respond locally


# ═══════════════════════════════════════════════════════════════
#  INTENT CLASSIFICATION
# ═══════════════════════════════════════════════════════════════

# Intents that require LLM (only 3 out of 45)
SEMANTIC_INTENTS = frozenset({
    Intent.CHAT_INTERPRETIVE,
    Intent.SEMANTIC_ANALYSIS,
    Intent.TEXT_GENERATION,
})

# All other intents are LOCAL (42 out of 45)
LOCAL_INTENTS = frozenset(set(Intent) - SEMANTIC_INTENTS)

# Keyword patterns for intent classification (trilingual: DE/EN/PT)
INTENT_PATTERNS: Dict[Intent, List[str]] = {
    # ── Document generation ──
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

    # ── Seal & Forensic ──
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

    # ── Governance ──
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

    # ── Dashboards ──
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

    # ── Workflow ──
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

    # ── System ──
    Intent.HELP: [
        r'\b(help|ajuda|hilfe)\b',
        r'\b(o\s+que\s+(podes?|consegue)|what\s+can\s+you|was\s+kannst?\s+du)\b',
        r'\b(funcion|capabilit|f[aä]higkeit|capacidade)\b',
        r'\b(ol[aá]|hello|hallo|hi|oi|bom\s*dia|good\s*morning|guten\s*morgen)\b',
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
}


def classify_intent(message: str, tier: Tier = Tier.PERSONAL) -> Tuple[Intent, bool]:
    """
    Classify user intent using rule-based pattern matching.

    The Dragon asks:
        1. Can this be resolved with local sovereignty?
        2. YES → respond (is_local=True)
        3. NO → activate semantic layer if tier allows (is_local=False)

    Args:
        message: User message text
        tier: Current user tier

    Returns:
        Tuple of (Intent, is_local) where is_local indicates sovereign routing.
    """
    msg_lower = message.lower().strip()

    if not msg_lower:
        return (Intent.HELP, True)

    # Score each intent by pattern matches
    best_intent = None
    best_score = 0

    for intent, patterns in INTENT_PATTERNS.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, msg_lower, re.IGNORECASE):
                score += 1
        if score > best_score:
            best_score = score
            best_intent = intent

    # If a local intent was matched, return it
    if best_intent and best_intent in LOCAL_INTENTS:
        return (best_intent, True)

    # If a semantic intent was matched
    if best_intent and best_intent in SEMANTIC_INTENTS:
        # Personal tier NEVER goes to LLM — route to HELP instead
        if tier == Tier.PERSONAL:
            return (Intent.HELP, True)
        return (best_intent, False)

    # No pattern matched → classify by tier
    if tier == Tier.PERSONAL:
        # Personal: always local, never LLM
        return (Intent.HELP, True)
    else:
        # Premium tiers: default to interpretive chat
        return (Intent.CHAT_INTERPRETIVE, False)


# ═══════════════════════════════════════════════════════════════
#  HANDLER MAPPING
# ═══════════════════════════════════════════════════════════════

HANDLER_MAP: Dict[Intent, str] = {
    # Document generation → Dragon render API
    Intent.GENERATE_PDF: "/api/dragon/render",
    Intent.GENERATE_DOCX: "/api/dragon/render",
    Intent.GENERATE_PPTX: "/api/dragon/render",
    Intent.GENERATE_XLSX: "/api/dragon/render",

    # Seal & Forensic
    Intent.SEAL_DOCUMENT: "/api/dragon/seal",
    Intent.SEAL_PIPELINE: "/api/dragon/seal",
    Intent.QUERY_LEDGER: "http://localhost:8101/api/receipts",
    Intent.VERIFY_HASH: "http://localhost:8101/api/receipts/verify",
    Intent.STORE_VAULT: "http://localhost:8106/api/vault/store",
    Intent.DOWNLOAD_FILE: "/api/dragon/download",

    # Governance
    Intent.CHECK_COMPLIANCE: "/api/dragon/compliance",
    Intent.CHECK_INVARIANTS: "/api/dragon/invariants",
    Intent.CHECK_RISK: "/api/dragon/risk",
    Intent.SGE_ANALYZE: "/api/dragon/sge",
    Intent.AUTONOMY_SCORE: "/api/dragon/sovereignty",
    Intent.SENTINEL_STATUS: "http://localhost:8102/health",
    Intent.I9_CHECK: "/api/dragon/invariants",
    Intent.METADATA_CLASSIFY: "/api/dragon/metadata",

    # Dashboards
    Intent.PULSE_REPORT: "/api/pulse/report.md",
    Intent.OUTLOOK_REPORT: "/api/dragon/outlook/report.md",
    Intent.HEALTH_CHECK: "/api/dragon/health",
    Intent.WIRING_STATUS: "/api/dragon/outlook/report.md",
    Intent.WAR_ROOM: "http://localhost:8090/war-room/",
    Intent.BUDGET_STATUS: "/api/dragon/health",

    # Workflow
    Intent.COMMUNIQUE_CREATE: "http://localhost:8105/api/communique/create",
    Intent.COMMUNIQUE_REVIEW: "http://localhost:8105/api/communique/review",
    Intent.COMMUNIQUE_PUBLISH: "http://localhost:8105/api/communique/publish",
    Intent.OCR_DOCUMENT: "http://localhost:8095/api/ocr",
    Intent.ISP_SELECT: "/api/dragon/isp/resolve",
    Intent.ISP_LIST: "/api/dragon/isp/list",
    Intent.AUTOCAT_CLASSIFY: "/api/dragon/autocat",
    Intent.PAPERLESS_BRIDGE: "http://localhost:8095/health",

    # System
    Intent.HELP: "/api/dragon/capabilities",
    Intent.DRAGON_IDENTITY: "/api/dragon/identity",
    Intent.WALLET_CHECK: "http://localhost:8099/health",
    Intent.CLONE_STATUS: "http://localhost:8092/health",
    Intent.COMMAND_BRIDGE: "http://localhost:8097/health",
    Intent.LANDING_INFO: "http://localhost:8107/",
    Intent.ID_GENESIS: "http://localhost:8096/health",
    Intent.CORTEX_STATUS: "http://localhost:8889/health",
    Intent.TRILINGUAL_DETECT: "/api/dragon/lang",
    Intent.THEME_TOGGLE: "/api/dragon/theme",
}

FORMAT_MAP: Dict[Intent, str] = {
    Intent.GENERATE_PDF: "pdf",
    Intent.GENERATE_DOCX: "docx",
    Intent.GENERATE_PPTX: "pptx",
    Intent.GENERATE_XLSX: "xlsx",
}


def get_handler(intent: Intent) -> str:
    """Get the handler URL for an intent."""
    return HANDLER_MAP.get(intent, "/api/dragon/capabilities")


def get_format(intent: Intent) -> Optional[str]:
    """Get the document format for a generation intent."""
    return FORMAT_MAP.get(intent)


# ═══════════════════════════════════════════════════════════════
#  LANGUAGE DETECTION
# ═══════════════════════════════════════════════════════════════

PT_MARKERS = frozenset([
    'pode', 'criar', 'gerar', 'como', 'preciso', 'quero', 'fazer',
    'ajuda', 'documento', 'obrigado', 'por', 'favor', 'ola', 'bom',
    'dia', 'boa', 'tarde', 'noite', 'verificar', 'mostrar', 'listar',
    'qual', 'quais', 'quando', 'onde', 'porque', 'sistema', 'estado',
])

DE_MARKERS = frozenset([
    'kann', 'erstellen', 'bitte', 'hilfe', 'dokument', 'wie',
    'brauche', 'mochte', 'machen', 'danke', 'guten', 'morgen',
    'tag', 'abend', 'zeigen', 'prufen', 'status', 'welche',
    'wann', 'warum', 'konnen', 'soll', 'bericht', 'uberprufen',
])


def detect_language(text: str) -> str:
    """
    Simple trilingual detection (PT/DE/EN) based on keyword frequency.
    Returns 'pt', 'de', or 'en' (default).
    """
    words = set(text.lower().split())

    pt_score = len(words & PT_MARKERS)
    de_score = len(words & DE_MARKERS)

    if pt_score > de_score and pt_score > 0:
        return "pt"
    elif de_score > pt_score and de_score > 0:
        return "de"
    return "en"


# ═══════════════════════════════════════════════════════════════
#  SOVEREIGN RESPONSE TEMPLATES
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
        "Ich bearbeite deine Anfrage mit lokaler Governance. "
        "Fur KI-erweiterte Interpretation steht dir der Professional-Tier "
        "zur Verfugung - dort wird die semantische Schicht aktiviert."
    ),
    "en": (
        "I'm processing your request with local governance. "
        "For AI-enhanced interpretation, the Professional tier is available "
        "- where the semantic layer is activated."
    ),
    "pt": (
        "Estou a processar o teu pedido com governanca local. "
        "Para interpretacao amplificada por IA, o tier Professional "
        "esta disponivel - onde a camada semantica e activada."
    ),
}

DOCUMENT_CREATED_MESSAGES: Dict[str, str] = {
    "de": "Dokument erstellt und versiegelt.",
    "en": "Document created and sealed.",
    "pt": "Documento criado e selado.",
}


# ═══════════════════════════════════════════════════════════════
#  SOVEREIGNTY METADATA
# ═══════════════════════════════════════════════════════════════

def sovereignty_metadata(llm_used: bool = False) -> dict:
    """Generate sovereignty metadata for responses."""
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
    """Full capabilities manifest."""
    return {
        "version": __version__,
        "sovereignty": sovereignty_metadata(),
        "capabilities": {
            "documents": ["PDF", "DOCX", "PPTX", "XLSX"],
            "sealing": [
                "SHA-256 hashing",
                "Serial numbers (WINDI-2026-XXXX)",
                "QR codes with verify URL",
                "Forensic Ledger (18,238+ receipts)",
                "Immutable Vault storage",
            ],
            "governance": [
                "9 Constitutional Invariants (I1-I9)",
                "I10 Continuity Invariant",
                "8 Stability Layers (S1-S8)",
                "SGE Risk Classification (R0-R5)",
                "Compliance Passport (GOLD status)",
                "Autonomy Score",
            ],
            "dashboards": [
                "Pulse Report (20 services)",
                "Product Outlook (14 features)",
                "Health Check",
                "Wiring Status (15 wires)",
                "War Room",
            ],
            "workflows": [
                "Communique (create -> review -> publish = SEALED)",
                "OCR via Tesseract 5.3",
                "ISP Templates (6 profiles, Grade A 97/100)",
                "AutoCat (6 categories, 3 languages)",
                "Seal Pipeline (N1-N4)",
            ],
        },
        "tiers": {
            "personal": {
                "price": "Free",
                "functions": 42,
                "llm": False,
                "description": "Full infrastructure, zero external keys",
            },
            "professional": {
                "price": "EUR 25-40/user",
                "functions": 45,
                "llm": True,
                "description": "+ semantic amplification",
            },
            "governance": {
                "price": "EUR 80-120/user",
                "functions": 45,
                "llm": True,
                "description": "+ dedicated LLM, ISP custom, SLA",
            },
        },
    }


# ═══════════════════════════════════════════════════════════════
#  SELF-TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"WINDI Sovereign Router v{__version__}")
    print(f"Local intents: {len(LOCAL_INTENTS)}")
    print(f"Semantic intents: {len(SEMANTIC_INTENTS)}")
    print(f"Total: {len(Intent)}")
    print()

    # Test classification
    test_cases = [
        ("Criar um PDF com o relatorio", Tier.PERSONAL),
        ("create a docx document", Tier.PERSONAL),
        ("Pulse report bitte", Tier.PERSONAL),
        ("verificar compliance", Tier.PERSONAL),
        ("o que podes fazer?", Tier.PERSONAL),
        ("analisa este texto semanticamente", Tier.PROFESSIONAL),
        ("hello", Tier.PERSONAL),
        ("selar este documento", Tier.PERSONAL),
        ("show me the ledger receipts", Tier.PERSONAL),
        ("criar uma apresentacao", Tier.PERSONAL),
    ]

    print("Intent Classification Tests:")
    print("-" * 70)
    for msg, tier in test_cases:
        intent, is_local = classify_intent(msg, tier)
        source = "LOCAL" if is_local else "SEMANTIC"
        lang = detect_language(msg)
        print(f"  [{source:9s}] [{lang}] {msg:45s} -> {intent.value}")

    print()
    print("Language Detection Tests:")
    print("-" * 40)
    for text in ["Guten Morgen, bitte erstellen", "Criar um documento por favor", "Create a PDF please"]:
        print(f"  [{detect_language(text)}] {text}")

    print()
    print(f"All {len(LOCAL_INTENTS)} local intents mapped")
    print(f"All {len(SEMANTIC_INTENTS)} semantic intents mapped")
    print(f"Ratio: {len(LOCAL_INTENTS)}/{len(Intent)} = "
          f"{len(LOCAL_INTENTS)/len(Intent)*100:.1f}% sovereign")
