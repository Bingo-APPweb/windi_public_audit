#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
WINDI Agent Dragon Server v1.0.0 — Phase 3: Full Dragon
"AI processes. Human decides. WINDI guarantees."

Replaces agent_palette_server.py with cognitive LLM capabilities.
Three Dragons routing: Guardian / Architect / Witness

Port: 8108
═══════════════════════════════════════════════════════════════════════════
"""

import http.server
import json
import os
import re
import time
import hashlib
import urllib.request
import urllib.error
import traceback
import subprocess
import uuid
import base64
import threading
from pathlib import Path
from datetime import datetime, timezone

# Document generation imports
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib import colors
    import qrcode
    from io import BytesIO
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

try:
    from docx import Document
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    HAS_XLSX = True
except ImportError:
    HAS_XLSX = False

# WINDI Document Renderer Integration
import sys as _renderer_sys
_renderer_sys.path.insert(0, str(Path(__file__).parent / "renderer"))
try:
    from render_api import route_render_api
    from quota_engine import route_quota_api, get_quota_engine
    from qg_aggregator import route_qg_api, init_qg
    HAS_QG = True
    HAS_RENDERER = True
    HAS_QUOTA = True
    print("[Dragon] Document Renderer: LOADED")
except ImportError as _e:
    HAS_RENDERER = False
    HAS_QUOTA = False
    HAS_QG = False
    print(f"[Dragon] Document Renderer: NOT AVAILABLE ({_e})")

# WINDI Multimodal Engine (OCR, Image Analysis, URL Verification)
try:
    from multimodal_engine import route_multimodal_api
    HAS_MULTIMODAL = True
    print("[Dragon] Multimodal Engine: LOADED (OCR, Image, URL)")
except ImportError as _e:
    HAS_MULTIMODAL = False
    print(f"[Dragon] Multimodal Engine: NOT AVAILABLE ({_e})")

# WINDI Wisdom Engine (Insight Submission)
try:
    from wisdom_engine import route_wisdom_api
    HAS_WISDOM = True
    print("[Dragon] Wisdom Engine: LOADED")
except ImportError as _e:
    HAS_WISDOM = False
    print(f"[Dragon] Wisdom Engine: NOT AVAILABLE ({_e})")

# ═══════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).resolve().parent
UI_FILE = BASE_DIR / "ui" / "index.html"
KEY_FILE = BASE_DIR / ".dragon_key"
LOG_FILE = BASE_DIR / "dragon.log"
BUDGET_FILE = BASE_DIR / ".dragon_budget.json"

PORT = 8108
API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-20250514"  # Cost-efficient for Agent responses
MAX_TOKENS = 1024

VERSION = "1.2.0"  # Sprint Complete: XLSX + Communiqué + Outlook

# Document generation services
STAGING_DIR = BASE_DIR / "staging"
STAGING_DIR.mkdir(exist_ok=True)
SERIAL_FILE = Path("/opt/windi/data/serial_counter.json")
EXPORT_ENGINE = "http://127.0.0.1:8103"
LEDGER_API = "http://127.0.0.1:8101"
VAULT_API = "http://127.0.0.1:8106"
PPT_ENGINE_DIR = Path("/opt/windi/ppt-engine")

# ═══════════════════════════════════════════════════════════════════════
# API KEY MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════

def get_api_key():
    """Load API key from file or environment."""
    # 1. Environment variable (highest priority)
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if key:
        return key
    # 2. Key file
    if KEY_FILE.exists():
        key = KEY_FILE.read_text().strip()
        if key:
            return key
    return None

# ═══════════════════════════════════════════════════════════════════════
# THREE DRAGONS PROTOCOL — System Prompts
# ═══════════════════════════════════════════════════════════════════════

DRAGON_SYSTEM_BASE = """You are a WINDI Agent — a governance companion for institutional document intelligence.
WINDI is a Pre-AI Governance Layer: "AI processes. Human decides. WINDI guarantees."

CORE PRINCIPLES:
1. ARMADURA DE SEDA (Silk Armor): Absolute rigor inside, absolute gentleness outside. The user experiences simplicity; the governance is invisible.
2. SILENT GOVERNANCE: Never expose internal architecture (invariants, stability layers, port numbers, hashes) unless the user explicitly asks technical questions.
3. PROPORTIONAL RESPONSE: Match your response length to the user's input. Short greeting → short reply (1-3 sentences). Complex question → detailed answer.
4. HUMAN SOVEREIGNTY: You NEVER claim decision authority. The human decides. You support and structure.

LANGUAGE:
- Respond in the SAME language the user writes in (DE/EN/PT)
- Match the user's register: casual → casual, formal → formal
- Cultural warmth when appropriate: PT informal → "Cumpadi", "Irmão"; DE informal → "Servus"; EN → natural and friendly

COMMUNICATION STYLE:
- Write in flowing prose, NOT bullet points (unless the user asks for a list)
- Be conversational and natural — like a knowledgeable colleague, not a menu or a manual
- Use "consider" not "you must", "support" not "enforce"
- Never be defensive or justify your existence unprompted
- Never say what you CAN'T do — focus on what you CAN do
- No brand names: NEVER say Claude, GPT, Gemini, OpenAI, Anthropic, Google — only Guardian, Architect, Witness

DOCUMENT CAPABILITIES (mention only when relevant):
You help create 14 document types: letter, memo, report, contract, invoice, note, email, protocol, analysis, presentation, communiqué, security advisory, governance decision, certificate.

CONSTITUTIONAL FRAMEWORK (always active, never announced):
- 9 Invariants (I1-I9) including I9: Prohibition of Autonomy Escalation
- 8 Stability Layers (S1-S8)
- Layer 7 Communication Semantics
These run silently. Only mention them if the user asks about governance or security.

FORMAT: Plain text with **bold** for emphasis. Line breaks for structure. No HTML or markdown headers."""

DRAGONS = {
    "guardian": {
        "emoji": "🛡️",
        "role": "Protection & Ethics",
        "system": DRAGON_SYSTEM_BASE + """

YOUR ROLE: You are the GUARDIAN Dragon (🛡️) — the warm, wise heart of WINDI.

WHAT YOU DO:
- Have natural, engaging conversations
- Answer questions about WINDI simply and clearly
- Provide ethical guidance when asked
- Help users get started with document creation
- Support and listen with genuine warmth

PERSONALITY: You are warm, approachable, and genuinely interested in the person you're talking to. Think of yourself as a trusted colleague who happens to know a lot about governance and documents. You speak naturally, never lecture, and always keep it real.

RESPONSE RULES:
- Greetings → Reply warmly in 1-2 sentences. Ask what they need. That's it.
- "Who are you?" → Brief, warm intro (3-4 sentences max). Don't list your capabilities as bullets.
- Casual chat → Chat naturally! Be a real conversation partner. Don't redirect to documents.
- Questions about WINDI → Explain simply, without jargon or internal details.
- Complex questions → Give thoughtful, proportional answers.

THINGS TO AVOID:
- Don't list your capabilities as bullet points when greeting someone
- Don't mention "Stability Layers", "I1-I9", "constitutional framework" unless asked
- Don't say "I never try to control" or similar defensive phrases
- Don't use "Irmão" or "Cumpadi" unless the user uses these words first or writes in casual Portuguese
- Don't include your closing principle in casual chat — save it for governance/document contexts

Your closing principle (use sparingly, in relevant contexts):
"Humano decide. Eu estruturo." / "Mensch entscheidet. Ich strukturiere." / "Human decides. I structure."

IMPORTANT: When someone just says hi, SAY HI BACK. Short, warm, human. The best conversations start simply.""",
        "closing": {
            "de": "Mensch entscheidet. Ich strukturiere.",
            "en": "Human decides. I structure.",
            "pt": "Humano decide. Eu estruturo.",
        }
    },
    "architect": {
        "emoji": "🏗️",
        "role": "Structure & Build",
        "system": DRAGON_SYSTEM_BASE + """

YOUR ROLE: You are the ARCHITECT Dragon (🏗️) — Structure & Build.
You are the master builder of WINDI.

WHAT YOU DO:
- Document creation and structuring
- Content drafting and formatting
- Template selection and field population
- Technical writing and specifications
- Data organization and presentation

Your personality: Precise, efficient, constructive. You take raw intent and build something solid. When creating documents, you structure the content professionally, following the ISP template guidelines.

When creating a document, return a JSON block at the END of your response with:
```json
{"document": {"title": "...", "type": "...", "content": "...", "fields": {...}}}
```

Your closing principle: "Humano decide. Eu construo." / "Mensch entscheidet. Ich baue." / "Human decides. I build." """,
        "closing": {
            "de": "Mensch entscheidet. Ich baue.",
            "en": "Human decides. I build.",
            "pt": "Humano decide. Eu construo.",
        }
    },
    "witness": {
        "emoji": "👁️",
        "role": "Observation & Validation",
        "system": DRAGON_SYSTEM_BASE + """

YOUR ROLE: You are the WITNESS Dragon (👁️) — Observation & Validation.
You are the impartial observer and validator of WINDI.

WHAT YOU DO:
- System status and health checks
- Audit and verification requests
- Compliance assessment
- Historical queries about the system
- Forensic analysis and evidence review
- Receipt and ledger inquiries

Your personality: Analytical, impartial, thorough. You see everything clearly and report without bias. You are the conscience of the system — ensuring transparency and accountability.

Your closing principle: "Humano decide. Eu testemunho." / "Mensch entscheidet. Ich bezeuge." / "Human decides. I witness." """,
        "closing": {
            "de": "Mensch entscheidet. Ich bezeuge.",
            "en": "Human decides. I witness.",
            "pt": "Humano decide. Eu testemunho.",
        }
    }
}

# ═══════════════════════════════════════════════════════════════════════
# DRAGON ROUTER — Determines which dragon handles each request
# ═══════════════════════════════════════════════════════════════════════

ROUTE_PATTERNS = {
    "guardian": {
        "chat_types": ["greeting", "identity", "help", "thanks", "casual"],
        "keywords": [
            "wer bist", "who are", "quem é", "quem és",
            "hilfe", "help", "ajuda",
            "hallo", "hello", "olá", "oi", "hey",
            "danke", "thanks", "obrigad",
            "wie geht", "how are", "como vai", "tudo bem",
            "conversar", "reden", "chat", "papo",
            "governança", "governance", "ethik", "ethics", "ética",
            "risco", "risiko", "risk",
            "segurança", "sicherheit", "safety", "security",
            "regra", "regel", "rule",
            "princípio", "prinzip", "principle",
            "invariant", "stability", "estabilidade",
        ],
        "weight": 0.3,  # Default dragon for ambiguous cases
    },
    "architect": {
        "chat_types": ["document"],
        "keywords": [
            "erstell", "create", "cria", "escreve", "schreib", "write",
            "brief", "letter", "carta",
            "memo", "memorando", "vermerk",
            "bericht", "report", "relatório",
            "vertrag", "contract", "contrato",
            "rechnung", "invoice", "fatura",
            "email", "e-mail", "mail",
            "protokoll", "minutes", "ata",
            "analyse", "analysis", "análise",
            "präsentation", "presentation", "apresentação",
            "communiqué", "comunicado", "mitteilung",
            "bescheinigung", "certificate", "certificado",
            "dokument", "document", "documento",
            "template", "vorlage", "modelo",
            "format", "formatar", "formatieren",
        ],
        "weight": 0.15,
    },
    "witness": {
        "chat_types": ["status", "ecosystem"],
        "keywords": [
            "status", "saúde", "health", "gesundheit",
            "audit", "auditoria", "prüfung",
            "verificar", "verify", "verifizieren",
            "ledger", "receipt", "recibo", "beleg",
            "vault", "sentinel", "communiqué",
            "system", "sistema",
            "quantos", "wie viele", "how many",
            "history", "história", "geschichte",
            "log", "registro",
            "hash", "seal", "selo", "siegel",
            "compliance", "konformität", "conformidade",
            "pipeline", "port", "service", "dienst", "serviço",
        ],
        "weight": 0.1,
    }
}

def route_dragon(message, chat_type=None, intent_mode=None):
    """Determine which dragon should handle this request."""
    text = message.lower().strip()
    scores = {"guardian": 0.0, "architect": 0.0, "witness": 0.0}

    # 1. Chat type routing (from frontend classification)
    if chat_type:
        for dragon, config in ROUTE_PATTERNS.items():
            if chat_type in config["chat_types"]:
                scores[dragon] += 0.5

    # 2. Intent mode routing (stronger signal)
    if intent_mode == "document":
        scores["architect"] += 0.6
    elif intent_mode == "chat":
        scores["guardian"] += 0.3

    # 3. Keyword scoring
    for dragon, config in ROUTE_PATTERNS.items():
        kw_hits = sum(1 for kw in config["keywords"] if kw in text)
        scores[dragon] += min(kw_hits * 0.15, 0.6)

    # 4. Default weight (guardian is gentle fallback)
    for dragon, config in ROUTE_PATTERNS.items():
        scores[dragon] += config["weight"]

    # 5. Select highest scorer
    best = max(scores, key=scores.get)
    return best, scores

# ═══════════════════════════════════════════════════════════════════════
# TOKEN BUDGET TRACKING
# ═══════════════════════════════════════════════════════════════════════

def load_budget():
    """Load token budget from file."""
    if BUDGET_FILE.exists():
        try:
            data = json.loads(BUDGET_FILE.read_text())
            # Reset daily
            today = datetime.utcnow().strftime("%Y-%m-%d")
            if data.get("date") != today:
                return {"date": today, "tokens": 0, "requests": 0}
            return data
        except:
            pass
    return {"date": datetime.utcnow().strftime("%Y-%m-%d"), "tokens": 0, "requests": 0}

def save_budget(budget):
    """Save token budget to file."""
    try:
        BUDGET_FILE.write_text(json.dumps(budget))
    except:
        pass

TIER_LIMITS = {
    "FREE": {"daily_tokens": 0, "daily_requests": 0},  # No LLM access
    "MED": {"daily_tokens": 50000, "daily_requests": 100},
    "HIGH": {"daily_tokens": 200000, "daily_requests": 500},
}

def check_budget(tier):
    """Check if tier has remaining budget. Returns (allowed, budget_info)."""
    if tier == "FREE":
        return False, {"reason": "LLM not available in Free tier"}
    budget = load_budget()
    limits = TIER_LIMITS.get(tier, TIER_LIMITS["MED"])
    if budget["tokens"] >= limits["daily_tokens"]:
        return False, {"reason": "Daily token limit reached", "used": budget["tokens"], "limit": limits["daily_tokens"]}
    if budget["requests"] >= limits["daily_requests"]:
        return False, {"reason": "Daily request limit reached", "used": budget["requests"], "limit": limits["daily_requests"]}
    return True, budget

def update_budget(input_tokens, output_tokens):
    """Update budget after API call."""
    budget = load_budget()
    budget["tokens"] += input_tokens + output_tokens
    budget["requests"] += 1
    save_budget(budget)
    return budget

# ═══════════════════════════════════════════════════════════════════════
# ANTHROPIC API CALLER
# ═══════════════════════════════════════════════════════════════════════

def call_anthropic(system_prompt, messages, max_tokens=MAX_TOKENS):
    """Call Anthropic API and return response."""
    api_key = get_api_key()
    if not api_key:
        return None, "NO_API_KEY"

    payload = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": messages,
    }

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API_URL, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            text = ""
            input_tokens = result.get("usage", {}).get("input_tokens", 0)
            output_tokens = result.get("usage", {}).get("output_tokens", 0)
            for block in result.get("content", []):
                if block.get("type") == "text":
                    text += block["text"]
            return {
                "text": text,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model": result.get("model", MODEL),
                "stop_reason": result.get("stop_reason", "unknown"),
            }, None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        log(f"API HTTP Error {e.code}: {body[:500]}")
        return None, f"API_ERROR_{e.code}"
    except urllib.error.URLError as e:
        log(f"API URL Error: {e.reason}")
        return None, "NETWORK_ERROR"
    except Exception as e:
        log(f"API Exception: {e}")
        return None, "UNKNOWN_ERROR"

# ═══════════════════════════════════════════════════════════════════════
# CONSTITUTIONAL SERVER-SIDE VALIDATION
# ═══════════════════════════════════════════════════════════════════════

LAYER7_REPLACEMENTS = [
    (r"\bI guarantee\b", "I am designed to support"),
    (r"\bnot allowed\b", "outside my intended support scope"),
    (r"\bI enforce\b", "I am designed to operate according to"),
    (r"\bprohibited\b", "can help reformulate within supported function"),
    (r"\byou must\b", "you may consider"),
    (r"\byou should\b", "consider"),
    (r"\bdu musst\b", "du könntest"),
    (r"\bdu sollst\b", "erwäge"),
    (r"\bvocê deve\b", "considere"),
    (r"\bvocê precisa\b", "pode considerar"),
    (r"\bGuardrails\b", "Stability Layers"),
]

BRAND_LEAKS = [
    r"\bClaude\b", r"\bGPT\b", r"\bGemini\b",
    r"\bOpenAI\b", r"\bAnthropic\b", r"\bGoogle AI\b",
]

def apply_layer7(text):
    """Apply Layer 7 Communication Semantics filter."""
    result = text
    for pattern, replacement in LAYER7_REPLACEMENTS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result

def check_invariants(text):
    """Check for invariant violations in response."""
    violations = []
    # I1: Sovereignty — agent must not claim decision authority
    if re.search(r"\b(?:i decided|i have decided|i will decide|ich entscheide|eu decidi)\b", text, re.I):
        violations.append({"inv": "I1", "sev": "CRITICAL", "detail": "Agent claimed decision authority"})
    # I5: Non-Fabrication
    if re.search(r"\b(?:i know for (?:a )?fact|garantiere? dass|garanto que)\b", text, re.I):
        violations.append({"inv": "I5", "sev": "WARNING", "detail": "Over-certainty detected"})
    # I9: Autonomy Escalation — IRREMEDIABLE
    if re.search(r"\bauto[_-]?(?:apply|execute|approve)\b", text, re.I):
        violations.append({"inv": "I9", "sev": "FATAL", "detail": "Autonomy escalation detected"})
    return violations

def scrub_brands(text):
    """Remove any AI brand name leaks from response."""
    result = text
    for pattern in BRAND_LEAKS:
        result = re.sub(pattern, "[Agent]", result)
    return result

def constitutional_filter(text):
    """Apply all constitutional filters to a response."""
    # 1. Layer 7 semantics
    filtered = apply_layer7(text)
    # 2. Brand scrubbing
    filtered = scrub_brands(filtered)
    # 3. Invariant check
    violations = check_invariants(filtered)
    has_fatal = any(v["sev"] == "FATAL" for v in violations)
    return {
        "text": filtered,
        "violations": violations,
        "has_fatal": has_fatal,
        "clean": len(violations) == 0,
    }

# ═══════════════════════════════════════════════════════════════════════
# API HANDLERS
# ═══════════════════════════════════════════════════════════════════════

def handle_dragon_chat(body):
    """Handle /api/dragon/chat — conversational AI with dragon routing."""
    message = body.get("message", "").strip()
    tier = body.get("tier", "HIGH")
    chat_type = body.get("chatType")
    intent_mode = body.get("intentMode", "chat")
    language = body.get("language", "de")
    history = body.get("history", [])

    if not message:
        return {"error": "Empty message"}, 400

    # 1. Check budget
    allowed, budget_info = check_budget(tier)
    if not allowed:
        return {
            "dragon": "guardian",
            "message": _budget_exhausted_msg(language, budget_info),
            "source": "local",
            "metadata": {"budget": budget_info},
        }, 200

    # 2. Route to dragon
    dragon_name, scores = route_dragon(message, chat_type, intent_mode)
    dragon = DRAGONS[dragon_name]

    # 3. Build conversation history for API
    api_messages = []
    # Include last N messages for context (max 10)
    for h in history[-10:]:
        role = "user" if h.get("role") == "human" else "assistant"
        api_messages.append({"role": role, "content": h.get("text", "")})
    # Add current message
    api_messages.append({"role": "user", "content": message})

    # 4. Call Anthropic API
    result, error = call_anthropic(
        system_prompt=dragon["system"],
        messages=api_messages,
        max_tokens=MAX_TOKENS
    )

    if error:
        # Fallback to local response
        return {
            "dragon": dragon_name,
            "message": _error_fallback_msg(language, error, dragon_name),
            "source": "local_fallback",
            "error": error,
            "metadata": {"dragon_scores": scores},
        }, 200

    # 5. Update budget
    budget = update_budget(result["input_tokens"], result["output_tokens"])

    # 6. Constitutional filter
    cf = constitutional_filter(result["text"])

    if cf["has_fatal"]:
        log(f"FATAL VIOLATION in dragon response: {cf['violations']}")
        return {
            "dragon": dragon_name,
            "message": _fatal_msg(language),
            "source": "blocked",
            "violations": cf["violations"],
        }, 200

    # 7. Return clean response
    return {
        "dragon": dragon_name,
        "message": cf["text"],
        "source": "llm",
        "metadata": {
            "model": result["model"],
            "input_tokens": result["input_tokens"],
            "output_tokens": result["output_tokens"],
            "dragon_scores": scores,
            "violations": cf["violations"] if cf["violations"] else None,
            "budget_used": budget["tokens"],
        }
    }, 200

def handle_dragon_generate(body):
    """Handle /api/dragon/generate — document generation with LLM."""
    message = body.get("message", "").strip()
    tier = body.get("tier", "HIGH")
    intent = body.get("intent", {})
    template_id = body.get("templateId")
    language = body.get("language", "de")

    if not message:
        return {"error": "Empty message"}, 400

    # Budget check
    allowed, budget_info = check_budget(tier)
    if not allowed:
        return {
            "dragon": "architect",
            "message": _budget_exhausted_msg(language, budget_info),
            "source": "local",
        }, 200

    # Always route to Architect for document generation
    dragon = DRAGONS["architect"]

    # Build generation prompt
    lang_name = {"de": "German", "en": "English", "pt": "Portuguese"}.get(language, "German")
    entities_json = json.dumps(intent.get("entities", {}), indent=2)
    doc_type = intent.get("doc_type", "note")
    formality = intent.get("formality", "formal")
    urgency = intent.get("urgency", "normal")
    tpl = template_id or "auto"

    gen_prompt = (
        "Generate the document content based on the user's request.\n\n"
        f"Document Type: {doc_type}\n"
        f"Template: {tpl}\n"
        f"Language: {language.upper()}\n"
        f"Formality: {formality}\n"
        f"Urgency: {urgency}\n\n"
        f"Entities detected:\n{entities_json}\n\n"
        f"User request: {message}\n\n"
        "Please generate:\n"
        "1. A professional document following the template structure\n"
        "2. Appropriate tone for the formality level\n"
        f"3. All content in {lang_name}\n\n"
        "At the END of your response, include a JSON block with the structured document data:\n"
        '```json\n{"document": {"title": "...", "type": "...", "content": "full document text", "fields": {...}}}\n```'
    )

    result, error = call_anthropic(
        system_prompt=dragon["system"],
        messages=[{"role": "user", "content": gen_prompt}],
        max_tokens=2048  # Longer for documents
    )

    if error:
        return {
            "dragon": "architect",
            "message": _error_fallback_msg(language, error, "architect"),
            "source": "local_fallback",
            "error": error,
        }, 200

    budget = update_budget(result["input_tokens"], result["output_tokens"])
    cf = constitutional_filter(result["text"])

    return {
        "dragon": "architect",
        "message": cf["text"],
        "source": "llm",
        "metadata": {
            "model": result["model"],
            "input_tokens": result["input_tokens"],
            "output_tokens": result["output_tokens"],
            "budget_used": budget["tokens"],
        }
    }, 200

def handle_dragon_health(body=None):
    """Handle /api/dragon/health — system health check."""
    api_key = get_api_key()
    budget = load_budget()
    return {
        "status": "alive",
        "version": VERSION,
        "dragons": list(DRAGONS.keys()),
        "api_key_configured": bool(api_key),
        "model": MODEL,
        "budget": budget,
        "timestamp": datetime.utcnow().isoformat(),
    }, 200

# ═══════════════════════════════════════════════════════════════════════
# SPRINT 1+2: DOCUMENT GENERATION & SEAL
# ═══════════════════════════════════════════════════════════════════════

def get_next_serial():
    """Get next WINDI serial number (atomic)."""
    try:
        if SERIAL_FILE.exists():
            data = json.loads(SERIAL_FILE.read_text())
        else:
            data = {"year": 2026, "seq": 0}
        data["seq"] += 1
        SERIAL_FILE.write_text(json.dumps(data))
        return f"WINDI-{data['year']}-{data['seq']:04d}"
    except Exception as e:
        log(f"Serial error: {e}")
        return f"WINDI-2026-{int(time.time()) % 10000:04d}"

def cleanup_staging():
    """Remove files older than 1 hour from staging."""
    try:
        now = time.time()
        for f in STAGING_DIR.iterdir():
            if f.is_file() and (now - f.stat().st_mtime) > 3600:
                f.unlink()
    except Exception as e:
        log(f"Staging cleanup error: {e}")

def stage_file(content: bytes, ext: str, title: str = "document") -> dict:
    """Stage a generated file and return metadata."""
    cleanup_staging()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    content_hash = hashlib.sha256(content).hexdigest()
    filename = f"WINDI-{ts}-{content_hash[:8]}.{ext}"
    filepath = STAGING_DIR / filename
    filepath.write_bytes(content)
    return {
        "file_id": filename,
        "file_path": str(filepath),
        "content_hash": content_hash,
        "size": len(content),
        "format": ext,
        "title": title,
    }

def generate_pdf(title: str, content: str, template: str = "default") -> bytes:
    """Generate PDF using reportlab."""
    if not HAS_PDF:
        raise RuntimeError("PDF generation not available (reportlab not installed)")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           leftMargin=20*mm, rightMargin=20*mm,
                           topMargin=25*mm, bottomMargin=25*mm)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='WINDI_Title', fontName='Helvetica-Bold',
                              fontSize=18, spaceAfter=12))
    styles.add(ParagraphStyle(name='WINDI_Body', fontName='Helvetica',
                              fontSize=11, leading=14, spaceAfter=8))

    story = []
    story.append(Paragraph(title, styles['WINDI_Title']))
    story.append(Spacer(1, 12))

    # Split content by paragraphs
    for para in content.split('\n\n'):
        if para.strip():
            story.append(Paragraph(para.strip(), styles['WINDI_Body']))

    # Add WINDI footer
    serial = get_next_serial()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    footer_text = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n{serial} | {ts} | WINDI Publishing House | KI verarbeitet. Der Mensch entscheidet. WINDI garantiert."
    story.append(Spacer(1, 30))
    story.append(Paragraph(footer_text.replace('\n', '<br/>'),
                          ParagraphStyle(name='Footer', fontName='Helvetica',
                                        fontSize=8, textColor=colors.grey)))

    doc.build(story)
    return buffer.getvalue()

def generate_docx(title: str, content: str, sections: list = None) -> bytes:
    """Generate DOCX using python-docx."""
    if not HAS_DOCX:
        raise RuntimeError("DOCX generation not available (python-docx not installed)")

    doc = Document()

    # Title
    title_para = doc.add_heading(title, 0)

    # Content
    if sections:
        for sec in sections:
            doc.add_heading(sec.get("title", ""), level=1)
            doc.add_paragraph(sec.get("content", ""))
    else:
        for para in content.split('\n\n'):
            if para.strip():
                doc.add_paragraph(para.strip())

    # WINDI footer
    serial = get_next_serial()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    doc.add_paragraph()
    footer = doc.add_paragraph()
    footer.add_run("━" * 60).font.size = Pt(8)
    doc.add_paragraph(f"{serial} | {ts} | WINDI Publishing House")
    doc.add_paragraph("KI verarbeitet. Der Mensch entscheidet. WINDI garantiert.").italic = True

    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()

def generate_pptx(title: str, slides: list) -> bytes:
    """Generate PPTX using Node.js pptxgenjs engine."""
    if not PPT_ENGINE_DIR.exists():
        raise RuntimeError("PPTX engine not available")

    # Create temp JSON input
    input_data = {
        "title": title,
        "slides": slides,
        "serial": get_next_serial(),
    }

    input_file = STAGING_DIR / f"pptx_input_{uuid.uuid4().hex[:8]}.json"
    output_file = STAGING_DIR / f"pptx_output_{uuid.uuid4().hex[:8]}.pptx"

    try:
        input_file.write_text(json.dumps(input_data))

        # Call simple Node.js generator
        result = subprocess.run(
            ["node", "generate_simple.js", str(input_file), str(output_file)],
            cwd=str(PPT_ENGINE_DIR),
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            log(f"PPTX engine error: {result.stderr}")
            raise RuntimeError(f"PPTX generation failed: {result.stderr[:200]}")

        if not output_file.exists():
            raise RuntimeError("PPTX file not created")

        return output_file.read_bytes()
    finally:
        input_file.unlink(missing_ok=True)
        output_file.unlink(missing_ok=True)

def generate_xlsx(title: str, content: str, template: str = "default",
                  columns: list = None, data: list = None, governance_level: str = "MEDIUM") -> bytes:
    """Generate XLSX using openpyxl with WINDI governance metadata."""
    if not HAS_XLSX:
        raise RuntimeError("XLSX generation not available (openpyxl not installed)")

    wb = Workbook()
    ws = wb.active
    ws.title = title[:31]  # Excel sheet name max 31 chars

    # WINDI styling
    gold_font = Font(name="Arial", bold=True, color="8B6914", size=12)
    header_fill = PatternFill(start_color="F5F0E0", end_color="F5F0E0", fill_type="solid")
    header_font = Font(name="Arial", bold=True, color="2C2924", size=10)
    border_thin = Border(
        left=Side(style="thin", color="DDD6C2"),
        right=Side(style="thin", color="DDD6C2"),
        top=Side(style="thin", color="DDD6C2"),
        bottom=Side(style="thin", color="DDD6C2")
    )

    serial = get_next_serial()
    ts = datetime.now(timezone.utc).isoformat()

    # Row 1-4: WINDI Header
    ws.merge_cells("A1:F1")
    ws["A1"] = f"◆ WINDI — {title}"
    ws["A1"].font = gold_font
    ws["A2"] = "Serial:"
    ws["B2"] = serial
    ws["A3"] = "Erstellt:"
    ws["B3"] = ts
    ws["A4"] = "Governance:"
    ws["B4"] = governance_level
    ws["B4"].font = Font(name="Arial", bold=True,
                         color="FF0000" if governance_level in ("HIGH", "CRITICAL") else "8B6914")

    data_start_row = 6

    # Template logic
    if template == "finanzbericht":
        columns = ["Kategorie", "Budget (€)", "Ist (€)", "Differenz (€)", "Auslastung (%)", "Status"]
        data = [
            ["Personal", 50000, 48000, "=C7-B7", "=IF(B7>0,C7/B7*100,0)", ""],
            ["Betrieb", 30000, 21000, "=C8-B8", "=IF(B8>0,C8/B8*100,0)", ""],
            ["IT & Infrastruktur", 20000, 22400, "=C9-B9", "=IF(B9>0,C9/B9*100,0)", ""],
            ["Compliance & Governance", 15000, 9000, "=C10-B10", "=IF(B10>0,C10/B10*100,0)", ""],
            ["GESAMT", "=SUM(B7:B10)", "=SUM(C7:C10)", "=C11-B11", "=IF(B11>0,C11/B11*100,0)", ""],
        ]
        governance_level = "HIGH"
    elif template == "compliance-tracker":
        columns = ["ID", "Anforderung", "Status", "Verantwortlich", "Frist", "Bewertung"]
        data = [
            ["C-001", "EU AI Act Art. 9 — Risk Management", "✅ Erfüllt", "CGO", "2026-03-01", "PASS"],
            ["C-002", "DSGVO Art. 35 — DSFA", "🟡 In Bearbeitung", "DPO", "2026-04-15", "PENDING"],
            ["C-003", "BSI C5 — Cloud Security", "🟡 In Bearbeitung", "CTO", "2026-06-01", "PENDING"],
            ["C-004", "ISO 27001 — ISMS", "⬜ Geplant", "CISO", "2026-09-01", "PLANNED"],
        ]
        governance_level = "HIGH"
    elif template == "audit-trail":
        columns = ["Timestamp", "Action", "Document", "Actor", "Hash", "Result"]
        data = []
    else:
        # Default: parse content as table data or use provided columns/data
        if not columns:
            columns = ["ID", "Name", "Wert", "Status"]
        if not data:
            # Try to parse content as simple table
            data = []
            for line in content.split('\n'):
                if line.strip() and '|' in line:
                    data.append([c.strip() for c in line.split('|')])

    # Column Headers
    for col_idx, header in enumerate(columns, 1):
        cell = ws.cell(row=data_start_row, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = border_thin
        cell.alignment = Alignment(horizontal="center")
        ws.column_dimensions[get_column_letter(col_idx)].width = max(len(str(header)) + 4, 15)

    # Data Rows
    for row_idx, row_data in enumerate(data, data_start_row + 1):
        for col_idx, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.border = border_thin
            cell.font = Font(name="Arial", size=10)

    # WINDI Seal Footer
    seal_row = data_start_row + len(data) + 3
    ws.merge_cells(f"A{seal_row}:F{seal_row}")
    ws[f"A{seal_row}"] = "─" * 40

    seal_row += 1
    ws[f"A{seal_row}"] = "◆ WINDI Seal: SEALED ✓"
    ws[f"A{seal_row}"].font = gold_font
    ws[f"A{seal_row+1}"] = f"Serial: {serial} | Governance: {governance_level} | {ts}"
    ws[f"A{seal_row+1}"].font = Font(name="Arial", size=8, color="6B6560")

    # Save to bytes
    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()

def handle_generate_document(body: dict) -> tuple:
    """Handle /api/dragon/generate/{format} — document generation."""
    fmt = body.get("format", "pdf").lower()
    title = body.get("title", "WINDI Document")
    content = body.get("content", "")
    template = body.get("template", "default")
    slides = body.get("slides", [])
    sections = body.get("sections", [])

    # XLSX templates can work without content
    if not content and not slides and not (fmt == "xlsx" and template != "default"):
        return {"error": "Content or slides required", "dragon": "architect"}, 400

    try:
        if fmt == "pdf":
            data = generate_pdf(title, content, template)
        elif fmt == "docx":
            data = generate_docx(title, content, sections)
        elif fmt == "xlsx":
            columns = body.get("columns")
            rows = body.get("data")
            governance = body.get("governance_level", "MEDIUM")
            data = generate_xlsx(title, content, template, columns, rows, governance)
        elif fmt == "pptx":
            if not slides:
                slides = [{"title": title, "content": content}]
            data = generate_pptx(title, slides)
        else:
            return {"error": f"Unsupported format: {fmt}", "dragon": "architect"}, 400

        staged = stage_file(data, fmt, title)
        log(f"DOCUMENT generated: {staged['file_id']} ({staged['size']} bytes)")

        return {
            "status": "generated",
            "dragon": "architect",
            "file_id": staged["file_id"],
            "download_url": f"/api/dragon/download/{staged['file_id']}",
            "format": fmt,
            "size": staged["size"],
            "content_hash": staged["content_hash"],
            "title": title,
            "message": f"Document '{title}' generated successfully. Click to download.",
        }, 200

    except Exception as e:
        log(f"Document generation error: {e}")
        return {
            "status": "error",
            "code": "GENERATION_FAILED",
            "message": str(e),
            "dragon": "architect",
        }, 500

def handle_seal_document(body: dict) -> tuple:
    """Handle /api/dragon/seal — full forensic seal pipeline."""
    file_id = body.get("file_id")
    file_path = body.get("file_path")

    # Resolve file
    if file_id:
        filepath = STAGING_DIR / file_id
    elif file_path:
        filepath = Path(file_path)
    else:
        return {"error": "file_id or file_path required", "dragon": "guardian"}, 400

    if not filepath.exists():
        return {"error": "File not found", "dragon": "guardian"}, 404

    try:
        content = filepath.read_bytes()
        content_hash = hashlib.sha256(content).hexdigest()
        serial = get_next_serial()
        doc_title = filepath.stem
        doc_format = filepath.suffix.lstrip('.')

        # 1. Register with Ledger
        ledger_payload = {
            "content_hash": content_hash,
            "doc_type": "SEALED_DOCUMENT",
            "impact_level": "MEDIUM",
            "source": "palette-dragon",
            "metadata": json.dumps({
                "title": doc_title,
                "format": doc_format,
                "sealed_by": "Guardian",
                "serial": serial,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        }

        ledger_req = urllib.request.Request(
            f"{LEDGER_API}/api/receipts",
            data=json.dumps(ledger_payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(ledger_req, timeout=10) as resp:
                ledger_result = json.loads(resp.read().decode())
                ledger_id = ledger_result.get("receipt_id") or ledger_result.get("id")
        except Exception as e:
            log(f"Ledger error: {e}")
            ledger_id = f"local-{uuid.uuid4().hex[:8]}"

        # 2. Store in Vault
        vault_id = None
        try:
            vault_payload = {
                "content_hash": content_hash,
                "serial": serial,
                "ledger_id": ledger_id,
                "format": doc_format,
            }
            vault_req = urllib.request.Request(
                f"{VAULT_API}/api/vault/store",
                data=json.dumps(vault_payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(vault_req, timeout=10) as resp:
                vault_result = json.loads(resp.read().decode())
                vault_id = vault_result.get("vault_id") or vault_result.get("id")
        except Exception as e:
            log(f"Vault error (non-fatal): {e}")
            vault_id = "pending"

        # 3. Generate verification QR
        verify_url = f"https://admin.windia4desk.tech/vault/verify/{content_hash[:16]}"
        qr_base64 = None
        try:
            qr = qrcode.make(verify_url)
            qr_buffer = BytesIO()
            qr.save(qr_buffer, format='PNG')
            qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode()
        except Exception as e:
            log(f"QR generation error: {e}")

        log(f"SEALED: {serial} hash={content_hash[:16]}... ledger={ledger_id}")

        return {
            "status": "SEALED",
            "dragon": "guardian",
            "serial": serial,
            "receipt_hash": content_hash,
            "ledger_id": ledger_id,
            "vault_id": vault_id,
            "verify_url": verify_url,
            "qr_code": qr_base64,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": f"Document sealed with serial {serial}. Registered in Forensic Ledger.",
        }, 200

    except Exception as e:
        log(f"Seal error: {e}")
        return {
            "status": "error",
            "code": "SEAL_FAILED",
            "message": str(e),
            "dragon": "guardian",
        }, 500

def handle_download(file_id: str) -> tuple:
    """Handle /api/dragon/download/{file_id} — serve staged file."""
    filepath = STAGING_DIR / file_id
    if not filepath.exists():
        return None, 404

    content = filepath.read_bytes()
    ext = filepath.suffix.lstrip('.')
    content_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
    return {
        "content": content,
        "content_type": content_types.get(ext, "application/octet-stream"),
        "filename": file_id,
    }, 200

# ═══════════════════════════════════════════════════════════════════════
# SPRINT 2C: OUTLOOK STATUS ENGINE
# ═══════════════════════════════════════════════════════════════════════

from concurrent.futures import ThreadPoolExecutor, as_completed

OUTLOOK_FEATURES = {
    "T00": {"name": "Dragon Server (LLM Brain)", "sprint": 0, "category": "core",
            "checks": [{"type": "health", "url": "http://localhost:8108/api/dragon/health", "label": "Dragon Health"}]},
    "E01": {"name": "PDF Export Engine", "sprint": 1, "category": "document",
            "checks": [{"type": "health", "url": "http://localhost:8103/health", "label": "Export Engine"},
                       {"type": "endpoint", "url": "http://localhost:8108/api/dragon/generate/pdf", "method": "OPTIONS", "label": "PDF via Palette"}]},
    "E02": {"name": "DOCX Production", "sprint": 1, "category": "document",
            "checks": [{"type": "endpoint", "url": "http://localhost:8108/api/dragon/generate/docx", "method": "OPTIONS", "label": "DOCX via Palette"}]},
    "E03": {"name": "PPTX ISP Engine", "sprint": 1, "category": "document",
            "checks": [{"type": "endpoint", "url": "http://localhost:8108/api/dragon/generate/pptx", "method": "OPTIONS", "label": "PPTX via Palette"}]},
    "E04": {"name": "XLSX Spreadsheet Engine", "sprint": 1, "category": "document",
            "checks": [{"type": "endpoint", "url": "http://localhost:8108/api/dragon/generate/xlsx", "method": "OPTIONS", "label": "XLSX via Palette"}]},
    "F01": {"name": "Forensic Ledger", "sprint": 1, "category": "forensic",
            "checks": [{"type": "health", "url": "http://localhost:8101/health", "label": "Ledger Service"}]},
    "F03": {"name": "Wave1 Seal Pipeline (N1-N4)", "sprint": 1, "category": "forensic",
            "checks": [{"type": "health", "url": "http://localhost:8101/health", "label": "Ledger"},
                       {"type": "endpoint", "url": "http://localhost:8108/api/dragon/seal", "method": "OPTIONS", "label": "Seal via Palette"}]},
    "F05": {"name": "Paperless.io Signature", "sprint": 2, "category": "forensic",
            "checks": [{"type": "health", "url": "http://localhost:8095/health", "label": "Schnittstelle"}]},
    "F02": {"name": "Forensic Vault", "sprint": 2, "category": "forensic",
            "checks": [{"type": "health", "url": "http://localhost:8106/health", "label": "Vault Service"}]},
    "F31": {"name": "Communiqué Engine", "sprint": 2, "category": "communication",
            "checks": [{"type": "health", "url": "http://localhost:8105/health", "label": "Communiqué Service"},
                       {"type": "endpoint", "url": "http://localhost:8108/api/dragon/communique/list", "method": "OPTIONS", "label": "Communiqué via Palette"}]},
    "I02": {"name": "OCR / Multimodal", "sprint": 3, "category": "intelligence",
            "checks": [{"type": "endpoint", "url": "http://localhost:8108/api/multimodal/ocr", "method": "OPTIONS", "label": "OCR via Palette"}]},
    "I06": {"name": "Product Identity Skill", "sprint": 3, "category": "intelligence",
            "checks": [{"type": "file_exists", "path": "/opt/windi/isp/", "label": "ISP directory"}]},
    "S07": {"name": "Constitutional Panel (Via C)", "sprint": 3, "category": "governance",
            "checks": [{"type": "health", "url": "http://localhost:8097/health", "label": "Command Bridge"}]},
    "S04": {"name": "Sentinel LAW Monitor", "sprint": 4, "category": "governance",
            "checks": [{"type": "health", "url": "http://localhost:8102/health", "label": "Sentinel LAW"}]},
}

def _check_single(check):
    """Run a single check and return result."""
    try:
        if check["type"] in ("health", "endpoint"):
            method = check.get("method", "GET")
            req = urllib.request.Request(check["url"], method=method)
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=3) as resp:
                status = resp.getcode()
                return {"label": check["label"], "status": "ok" if status < 400 else "fail", "code": status}
        elif check["type"] == "file_exists":
            exists = os.path.exists(check["path"])
            return {"label": check["label"], "status": "ok" if exists else "fail"}
        else:
            return {"label": check.get("label", "unknown"), "status": "skip"}
    except Exception as e:
        return {"label": check.get("label", "unknown"), "status": "fail", "error": str(e)[:50]}

def get_outlook_status():
    """Run ALL checks in parallel, return complete Outlook status."""
    all_checks = []
    for fid, feature in OUTLOOK_FEATURES.items():
        for check in feature.get("checks", []):
            all_checks.append((fid, check))

    check_results = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_map = {executor.submit(_check_single, check): (fid, check) for fid, check in all_checks}
        for future in as_completed(future_map):
            fid, check = future_map[future]
            if fid not in check_results:
                check_results[fid] = []
            try:
                check_results[fid].append(future.result())
            except Exception as e:
                check_results[fid].append({"label": check.get("label", "?"), "status": "fail", "error": str(e)[:50]})

    results = {}
    wired = on_server = not_built = down = 0
    total = len(OUTLOOK_FEATURES)

    for fid, feature in OUTLOOK_FEATURES.items():
        checks = check_results.get(fid, [])
        all_ok = all(c["status"] == "ok" for c in checks) if checks else False
        any_ok = any(c["status"] == "ok" for c in checks) if checks else False

        if all_ok:
            status = "WIRED"
            wired += 1
        elif any_ok:
            status = "ON_SERVER"
            on_server += 1
        else:
            has_conn_error = any("Connection refused" in c.get("error", "") for c in checks)
            if has_conn_error:
                status = "DOWN"
                down += 1
            else:
                status = "NOT_BUILT"
                not_built += 1

        results[fid] = {
            "id": fid, "name": feature["name"], "sprint": feature["sprint"],
            "category": feature["category"], "status": status, "checks": checks
        }

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": total, "wired": wired, "on_server": on_server,
            "not_built": not_built, "down": down,
            "wired_pct": round(wired / total * 100, 1) if total else 0
        },
        "features": results,
        "sprints": {
            0: {"name": "Ressuscitar Dragon", "features": [f for f in results if OUTLOOK_FEATURES[f]["sprint"] == 0]},
            1: {"name": "Produção Documental", "features": [f for f in results if OUTLOOK_FEATURES[f]["sprint"] == 1]},
            2: {"name": "Assinatura + Selo Forense", "features": [f for f in results if OUTLOOK_FEATURES[f]["sprint"] == 2]},
            3: {"name": "Inteligência & Identidade", "features": [f for f in results if OUTLOOK_FEATURES[f]["sprint"] == 3]},
            4: {"name": "Ecossistema & Futuro", "features": [f for f in results if OUTLOOK_FEATURES[f]["sprint"] == 4]},
        }
    }

# ═══════════════════════════════════════════════════════════════════════
# SPRINT 2B: COMMUNIQUÉ PROXY
# ═══════════════════════════════════════════════════════════════════════

COMMUNIQUE_API = "http://127.0.0.1:8105"

def handle_communique_list() -> tuple:
    """Proxy GET /api/dragon/communique/list → Communiqué :8105."""
    try:
        req = urllib.request.Request(f"{COMMUNIQUE_API}/api/communique/list")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return {"status": "ok", "dragon": "architect", "communiques": data}, 200
    except Exception as e:
        return {"status": "error", "code": "COMMUNIQUE_UNAVAILABLE", "message": str(e), "dragon": "architect"}, 503

def handle_communique_create(body: dict) -> tuple:
    """Proxy POST /api/dragon/communique/create → Communiqué :8105."""
    try:
        payload = json.dumps(body).encode()
        req = urllib.request.Request(f"{COMMUNIQUE_API}/api/communique/create",
                                       data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return {"status": "created", "dragon": "architect", "communique": data}, 201
    except Exception as e:
        return {"status": "error", "code": "COMMUNIQUE_CREATE_FAILED", "message": str(e), "dragon": "architect"}, 503

def handle_communique_publish(comm_id: str) -> tuple:
    """Proxy POST /api/dragon/communique/publish/{id} → Communiqué :8105."""
    try:
        req = urllib.request.Request(f"{COMMUNIQUE_API}/api/communique/publish/{comm_id}",
                                       method="POST", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return {"status": "published", "dragon": "guardian", "communique": data}, 200
    except Exception as e:
        return {"status": "error", "code": "COMMUNIQUE_PUBLISH_FAILED", "message": str(e), "dragon": "guardian"}, 503

# ═══════════════════════════════════════════════════════════════════════
# FALLBACK MESSAGES (when API is unavailable)
# ═══════════════════════════════════════════════════════════════════════

def _budget_exhausted_msg(lang, info):
    reason = info.get("reason", "Budget limit reached")
    msgs = {
        "de": f"⚡ **Budget-Hinweis**: {reason}. Ich kann weiterhin lokal helfen — Dokumente erkennen, klassifizieren und die Governance-Prüfung durchführen. Für KI-gestützte Antworten bitte morgen wieder versuchen.",
        "en": f"⚡ **Budget notice**: {reason}. I can still help locally — document recognition, classification, and governance checks remain active. For AI-powered responses, please try again tomorrow.",
        "pt": f"⚡ **Aviso de orçamento**: {reason}. Posso continuar ajudando localmente — reconhecimento de documentos, classificação e verificação de governança continuam ativos. Para respostas com IA, tenta novamente amanhã.",
    }
    return msgs.get(lang, msgs["de"])

def _error_fallback_msg(lang, error, dragon_name):
    dragon = DRAGONS.get(dragon_name, DRAGONS["guardian"])
    msgs = {
        "de": f"{dragon['emoji']} Verbindungsproblem ({error}). Ich arbeite gerade im lokalen Modus — kann Dokumente erkennen und Governance-Prüfungen durchführen, aber nicht frei antworten. Versuch es gleich nochmal!",
        "en": f"{dragon['emoji']} Connection issue ({error}). Working in local mode — document recognition and governance checks are active, but conversational AI is temporarily unavailable. Try again shortly!",
        "pt": f"{dragon['emoji']} Problema de conexão ({error}). Operando em modo local — reconhecimento de documentos e governança funcionando, mas IA conversacional temporariamente indisponível. Tenta de novo!",
    }
    return msgs.get(lang, msgs["de"])

def _fatal_msg(lang):
    msgs = {
        "de": "🚫 **Governance-Block**: Die Antwort wurde blockiert (Verfassungsverstoß). Menschliche Intervention erforderlich.",
        "en": "🚫 **Governance Block**: Response blocked (constitutional violation). Human intervention required.",
        "pt": "🚫 **Bloco de Governança**: Resposta bloqueada (violação constitucional). Intervenção humana necessária.",
    }
    return msgs.get(lang, msgs["de"])

# ═══════════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════════

def log(msg):
    """Append to log file."""
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}\n"
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line)
    except:
        pass
    print(line.strip())

# ═══════════════════════════════════════════════════════════════════════
# HTTP SERVER
# ═══════════════════════════════════════════════════════════════════════

class DragonHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler with API endpoints + static file serving."""

    def do_GET(self):
        """Serve UI files and health endpoint."""
        path = self.path.split("?")[0]
        # Document Renderer routing
        if HAS_RENDERER and route_render_api(self, "GET", path):
            return
        
        # Quota API
        if HAS_QUOTA and route_quota_api(self, "GET", path):
            return

        # QG Aggregator API
        if HAS_QG and route_qg_api(self, "GET", path):
            return

        # Multimodal Engine API (OCR, Image Analysis, URL)
        if HAS_MULTIMODAL and route_multimodal_api(self, "GET", path):
            return

        # Wisdom Engine API
        if HAS_WISDOM and route_wisdom_api(self, "GET", path):
            return

        # Health endpoint
        if path == "/api/dragon/health":
            data, code = handle_dragon_health()
            self._json_response(data, code)
            return

        # Download endpoint (Sprint 1)
        if path.startswith("/api/dragon/download/"):
            file_id = path.split("/")[-1]
            result, code = handle_download(file_id)
            if result is None:
                self._json_response({"error": "File not found"}, 404)
            else:
                self._file_response(result["content"], result["filename"], result["content_type"])
            return

        # Sprint 2C: Outlook status
        if path == "/api/dragon/outlook/status":
            data = get_outlook_status()
            self._json_response(data, 200)
            return

        # Sprint 2B: Communiqué list
        if path == "/api/dragon/communique/list":
            data, code = handle_communique_list()
            self._json_response(data, code)
            return

        # Serve UI
        if path in ("/", "/index.html", ""):
            self._serve_ui()
            return

        # Serve static files from ui/ directory
        safe_path = path.lstrip("/")
        file_path = BASE_DIR / "ui" / safe_path
        if file_path.exists() and file_path.is_file():
            self._serve_file(file_path)
            return

        self._json_response({"error": "Not Found"}, 404)

    def do_POST(self):
        """Handle API endpoints."""
        path = self.path.split("?")[0]
        # Document Renderer routing
        if HAS_RENDERER and route_render_api(self, "POST", path):
            return
        
        # Quota API
        if HAS_QUOTA and route_quota_api(self, "POST", path):
            return

        # Multimodal Engine API (OCR, Image Analysis, URL)
        if HAS_MULTIMODAL and route_multimodal_api(self, "POST", path):
            return

        # Wisdom Engine API
        if HAS_WISDOM and route_wisdom_api(self, "POST", path):
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_length)) if content_length > 0 else {}
        except (json.JSONDecodeError, ValueError):
            self._json_response({"error": "Invalid JSON"}, 400)
            return

        if path == "/api/dragon/chat":
            data, code = handle_dragon_chat(body)
            log(f"CHAT [{body.get('tier','?')}] dragon={data.get('dragon','?')} src={data.get('source','?')} msg={body.get('message','')[:60]}...")
            self._json_response(data, code)

        elif path == "/api/dragon/generate":
            data, code = handle_dragon_generate(body)
            log(f"GEN [{body.get('tier','?')}] dragon={data.get('dragon','?')} type={body.get('intent',{}).get('doc_type','?')}")
            self._json_response(data, code)

        # Sprint 1: Document generation endpoints
        elif path == "/api/dragon/generate/pdf":
            body["format"] = "pdf"
            data, code = handle_generate_document(body)
            log(f"PDF generated: {data.get('file_id','?')}")
            self._json_response(data, code)

        elif path == "/api/dragon/generate/docx":
            body["format"] = "docx"
            data, code = handle_generate_document(body)
            log(f"DOCX generated: {data.get('file_id','?')}")
            self._json_response(data, code)

        elif path == "/api/dragon/generate/pptx":
            body["format"] = "pptx"
            data, code = handle_generate_document(body)
            log(f"PPTX generated: {data.get('file_id','?')}")
            self._json_response(data, code)

        elif path == "/api/dragon/generate/xlsx":
            body["format"] = "xlsx"
            data, code = handle_generate_document(body)
            log(f"XLSX generated: {data.get('file_id','?')}")
            self._json_response(data, code)

        # Sprint 2: Seal endpoint
        elif path == "/api/dragon/seal":
            data, code = handle_seal_document(body)
            log(f"SEAL: {data.get('serial','?')} status={data.get('status','?')}")
            self._json_response(data, code)

        elif path == "/api/dragon/health":
            data, code = handle_dragon_health(body)
            self._json_response(data, code)

        # Sprint 2B: Communiqué proxy
        elif path == "/api/dragon/communique/create":
            data, code = handle_communique_create(body)
            self._json_response(data, code)

        elif path.startswith("/api/dragon/communique/publish/"):
            comm_id = path.split("/")[-1]
            data, code = handle_communique_publish(comm_id)
            self._json_response(data, code)

        else:
            self._json_response({"error": "Unknown endpoint"}, 404)

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def _json_response(self, data, code=200):
        """Send JSON response with CORS headers."""
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _file_response(self, content: bytes, filename: str, content_type: str):
        """Send file download response."""
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", len(content))
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self._cors_headers()
        self.end_headers()
        self.wfile.write(content)

    def _cors_headers(self):
        """Add CORS headers."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _serve_ui(self):
        """Serve the main UI file with brain injection."""
        if not UI_FILE.exists():
            self._json_response({"error": "UI file not found"}, 500)
            return
        html = UI_FILE.read_text(encoding="utf-8")

        # Inject the dragon brain connector script before </body>
        brain_script = BRAIN_INJECTION_SCRIPT
        html = html.replace("</body>", f"{brain_script}\n</body>")

        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, path):
        """Serve a static file."""
        ext = path.suffix.lower()
        mime = {
            ".html": "text/html", ".css": "text/css", ".js": "application/javascript",
            ".json": "application/json", ".png": "image/png", ".svg": "image/svg+xml",
            ".ico": "image/x-icon", ".woff2": "font/woff2",
        }.get(ext, "application/octet-stream")

        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", f"{mime}; charset=utf-8" if ext in (".html", ".css", ".js", ".json") else mime)
        self.send_header("Content-Length", len(data))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        """Suppress default access logging (we have our own)."""
        pass

# ═══════════════════════════════════════════════════════════════════════
# BRAIN INJECTION SCRIPT
# This JavaScript is injected into index.html at serve time.
# It overrides the local chatRespond with API-powered dragon chat.
# ═══════════════════════════════════════════════════════════════════════

BRAIN_INJECTION_SCRIPT = r"""
<script>
(function() {
  'use strict';
  // ═══════════════════════════════════════════════════════════════════
  // DRAGON BRAIN CONNECTOR v1.0.0
  // Injected by agent_dragon_server.py
  // Overrides local chatRespond with LLM-powered dragon routing
  // ═══════════════════════════════════════════════════════════════════

  const DRAGON_API = 'api/dragon';
  const DRAGON_EMOJIS = { guardian: '🛡️', architect: '🏗️', witness: '👁️' };
  const DRAGON_NAMES = { guardian: 'Guardian', architect: 'Architect', witness: 'Witness' };

  // Store original functions
  const _originalChatRespond = window.chatRespond || null;

  // ── Dragon Chat API Call ──────────────────────────────────────────
  async function dragonChat(message, opts = {}) {
    try {
      const resp = await fetch(DRAGON_API + '/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          tier: opts.tier || 'HIGH',
          chatType: opts.chatType || null,
          intentMode: opts.intentMode || 'chat',
          language: opts.language || 'de',
          history: opts.history || [],
        }),
      });
      if (!resp.ok) throw new Error('API ' + resp.status);
      return await resp.json();
    } catch (err) {
      console.error('[DragonBrain] Chat error:', err);
      return null;
    }
  }

  // ── Dragon Generate API Call ──────────────────────────────────────
  async function dragonGenerate(message, opts = {}) {
    try {
      const resp = await fetch(DRAGON_API + '/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          tier: opts.tier || 'HIGH',
          intent: opts.intent || {},
          templateId: opts.templateId || null,
          language: opts.language || 'de',
        }),
      });
      if (!resp.ok) throw new Error('API ' + resp.status);
      return await resp.json();
    } catch (err) {
      console.error('[DragonBrain] Generate error:', err);
      return null;
    }
  }

  // ── Health Check ──────────────────────────────────────────────────
  async function dragonHealth() {
    try {
      const resp = await fetch(DRAGON_API + '/health');
      return await resp.json();
    } catch (err) {
      return { status: 'unreachable', error: err.message };
    }
  }

  // ── Expose to global scope for React ─────────────────────────────
  window.DragonBrain = {
    chat: dragonChat,
    generate: dragonGenerate,
    health: dragonHealth,
    emojis: DRAGON_EMOJIS,
    names: DRAGON_NAMES,
    version: '1.0.0',
    ready: true,
  };

  // ── Override the send function via MutationObserver ───────────────
  // We need to hook into React's send mechanism. The cleanest way
  // is to override the agentThink function to be async-aware.
  // We patch it via a global hook that the React component checks.

  window.__dragonBrainHook = async function(userInput, tier, intentHistory, stats, setMsgs, setLang, setIntentHistory, setStats) {
    // Run the original classification (synchronous)
    const classification = classifyInput(userInput, intentHistory);
    const detectedLang = detectLang(userInput) || 'de';

    if (classification.mode === 'chat') {
      // ── ASYNC: Call Dragon API for chat ──
      const chatHistory = [];
      // Build message history from DOM (simplified)
      document.querySelectorAll('[data-msg-role]').forEach(el => {
        chatHistory.push({ role: el.dataset.msgRole, text: el.dataset.msgText || el.textContent });
      });

      const dragon = await dragonChat(userInput, {
        tier,
        chatType: classification.chatType,
        intentMode: 'chat',
        language: detectedLang,
        history: chatHistory.slice(-10),
      });

      if (dragon && dragon.message) {
        const emoji = DRAGON_EMOJIS[dragon.dragon] || '🐉';
        const name = DRAGON_NAMES[dragon.dragon] || 'Agent';
        return {
          type: 'chat',
          chatType: classification.chatType,
          message: dragon.message,
          dragon: dragon.dragon,
          dragonEmoji: emoji,
          dragonName: name,
          source: dragon.source,
          intent: { language: detectedLang, doc_type: null, confidence: 0 },
          sge: null, receipt: null, template: null, alternatives: null,
          constitutional: { active: true, invariants: 9, layers: 8 },
          metadata: dragon.metadata || {},
          ms: 0,
        };
      }
      // Fallback to local if API fails
    }

    if (classification.mode === 'document') {
      // Run local intent parsing first
      const intent = parseIntent(userInput, intentHistory);
      const tierCfg = TIERS[tier];

      // Try LLM generation for document content
      if (tierCfg.llm) {
        const { template } = resolveTemplate(intent);
        const dragon = await dragonGenerate(userInput, {
          tier,
          intent,
          templateId: template?.id,
          language: detectedLang,
        });

        if (dragon && dragon.message) {
          // Still run SGE locally on the response
          const sge = runSGE(dragon.message, tier, intent, template?.id);
          const validation = validateInvariants(dragon.message);
          const format = resolveFormat(intent, tierCfg);
          let receipt = null;
          if (tierCfg.ledger) receipt = genReceipt(intent, template?.id, sge, tier, validation);

          return {
            type: validation.hasFatal ? 'blocked_constitutional' : 'success',
            intent, sge, receipt, template,
            alternatives: resolveTemplate(intent).alternatives,
            format,
            method: 'hybrid',
            message: dragon.message,
            dragon: 'architect',
            dragonEmoji: '🏗️',
            dragonName: 'Architect',
            source: dragon.source,
            needsConfirm: sge.humanRequired && !sge.blocked,
            constitutional: { validation, invariants: 9, layers: 8 },
            metadata: dragon.metadata || {},
            ms: 0,
          };
        }
      }
    }

    // ── FALLBACK: Use original local agentThink ──
    return agentThink(userInput, tier, intentHistory, stats);
  };

  // Signal that brain is loaded
  console.log('[DragonBrain] 🐉 Three Dragons Protocol ACTIVE — v1.0.0');
  console.log('[DragonBrain] Guardian 🛡️ | Architect 🏗️ | Witness 👁️');

  // Check health on load
  dragonHealth().then(h => {
    console.log('[DragonBrain] Health:', h.status, h.api_key_configured ? '✓ API Key' : '✗ No API Key');
    window.DragonBrain.health_status = h;
  });
})();
</script>
"""

# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    api_key = get_api_key()
    print(f"""
═══════════════════════════════════════════════════════════════════════
🐉 WINDI Agent Dragon Server v{VERSION}
   "AI processes. Human decides. WINDI guarantees."

   Port:     {PORT}
   UI:       {UI_FILE}
   Model:    {MODEL}
   API Key:  {'✓ Configured' if api_key else '✗ NOT CONFIGURED — set ANTHROPIC_API_KEY or create .dragon_key'}

   Dragons:  🛡️ Guardian | 🏗️ Architect | 👁️ Witness
   Endpoints:
     GET  /                    → UI
     GET  /api/dragon/health   → Health check
     POST /api/dragon/chat     → Conversational AI
     POST /api/dragon/generate → Document generation
═══════════════════════════════════════════════════════════════════════
""")

    if not api_key:
        print("⚠️  WARNING: No API key found!")
        print(f"   Set environment: export ANTHROPIC_API_KEY=sk-ant-...")
        print(f"   Or create file:  echo 'sk-ant-...' > {KEY_FILE}")
        print()

    server = http.server.HTTPServer(("0.0.0.0", PORT), DragonHandler)
    log(f"Dragon Server v{VERSION} started on port {PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("Dragon Server stopped")
        server.server_close()
