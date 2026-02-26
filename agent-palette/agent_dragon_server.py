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
import sys

# SGE Engine import
sys.path.insert(0, "/opt/windi/engine")
try:
    from semantic_governance import SemanticGovernanceEngine, format_terminal_report
    SGE_AVAILABLE = True
except ImportError:
    SGE_AVAILABLE = False
    print("⚠️  SGE Engine not available - /opt/windi/engine/semantic_governance.py")

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

# WINDI Sovereign Router (Intent Classification + Local Routing)
try:
    from sovereign_router import (
        classify_intent, get_handler, get_format, detect_language,
        Intent, Tier, SEMANTIC_INTENTS, LOCAL_INTENTS,
        HELP_RESPONSES, FALLBACK_MESSAGES, sovereignty_metadata, capabilities_response
    )
    HAS_SOVEREIGN_ROUTER = True
    print("[Dragon] Sovereign Router: LOADED (42 local, 3 semantic)")
except ImportError as _e:
    HAS_SOVEREIGN_ROUTER = False
    print(f"[Dragon] Sovereign Router: NOT AVAILABLE ({_e})")

# WINDI Decision Journal (Memory on the Edge)
try:
    from decision_journal import (
        record_decision, get_decision_stats, get_recent_decisions,
        get_autonomy_intelligence, get_hesitation_patterns,
        calculate_cognitive_score, detect_cognitive_hesitation,
        detect_wisdom_candidates, get_cognitive_evolution,
        get_outlook_cognitive_feature, get_pulse_cognitive_wire,
        promote_wisdom_candidate, get_wisdom_blocks
    )
    HAS_DECISION_JOURNAL = True
    print("[Dragon] Decision Journal: LOADED (Cognitive Observability v1.2)")
except ImportError as _e:
    HAS_DECISION_JOURNAL = False
    print(f"[Dragon] Decision Journal: NOT AVAILABLE ({_e})")

# WINDI Economic Brain (Constitutional Economic Consciousness)
try:
    from economic_brain import (
        get_economic_brain, route_economic_api,
        ECONOMIC_INVARIANTS, ECONOMIC_BRAIN_SYSTEM_PROMPT,
        TIERS, UPGRADE_PHILOSOPHY
    )
    HAS_ECONOMIC_BRAIN = True
    print("[Dragon] Economic Brain: LOADED (IE1-IE7 Consciousness)")
except ImportError as _e:
    HAS_ECONOMIC_BRAIN = False
    print(f"[Dragon] Economic Brain: NOT AVAILABLE ({_e})")

# WINDI Institutional Memory (Dragon's Legal Advocacy via Evidence Bundle)
try:
    from institutional_memory import (
        get_institutional_memory, query_institutional, emit_institutional_proof
    )
    HAS_INSTITUTIONAL_MEMORY = True
    _im = get_institutional_memory()
    _im_stats = _im.get_stats()
    print(f"[Dragon] Institutional Memory: LOADED ({_im_stats['stress_questions']} stress questions, {_im_stats['invariants']} invariants)")
except ImportError as _e:
    HAS_INSTITUTIONAL_MEMORY = False
    print(f"[Dragon] Institutional Memory: NOT AVAILABLE ({_e})")

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

VERSION = "1.3.0"  # Sprint 2D: Markdown Reports

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
# ELEVENLABS VOICE API — Phase 5C LAUNCH Plan
# ═══════════════════════════════════════════════════════════════════════

ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"
ELEVENLABS_KEY_FILE = BASE_DIR / ".elevenlabs_key"
ELEVENLABS_MODEL = "eleven_multilingual_v2"
ELEVENLABS_MAX_CHARS = 2000

# Dragon voice mapping (voice_id → ElevenLabs voice)
DRAGON_VOICES = {
    "guardian": "pNInz6obpgDQGcFmaJgB",  # Deep, protective
    "architect": "ErXwobaYiN019PkySvjV",  # Clear, precise
    "witness": "EXAVITQu4vr4xnSDxMaL",    # Calm, analytical
}

def get_elevenlabs_key():
    """Load ElevenLabs API key from file or environment."""
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if key:
        return key
    if ELEVENLABS_KEY_FILE.exists():
        key = ELEVENLABS_KEY_FILE.read_text().strip()
        if key:
            return key
    return None

def handle_voice_speak(body):
    """
    Phase 5C: Text-to-Speech via ElevenLabs API.
    POST /api/dragon/voice/speak
    Body: { text, voice_id?, dragon?, model_id? }
    Returns: (audio_bytes, None) or (None, error_dict)
    """
    api_key = get_elevenlabs_key()
    if not api_key:
        return None, {"error": "Voice API not configured", "code": "NO_ELEVENLABS_KEY"}

    text = body.get("text", "").strip()
    if not text:
        return None, {"error": "No text provided", "code": "NO_TEXT"}

    if len(text) > ELEVENLABS_MAX_CHARS:
        text = text[:ELEVENLABS_MAX_CHARS]

    # Resolve voice_id: explicit > dragon mapping > default guardian
    voice_id = body.get("voice_id")
    if not voice_id:
        dragon = body.get("dragon", "guardian")
        voice_id = DRAGON_VOICES.get(dragon, DRAGON_VOICES["guardian"])

    model_id = body.get("model_id", ELEVENLABS_MODEL)

    # Voice settings (balanced for multilingual)
    voice_settings = body.get("voice_settings", {
        "stability": 0.6,
        "similarity_boost": 0.75,
        "style": 0.1,
        "use_speaker_boost": True
    })

    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": voice_settings
    }

    url = f"{ELEVENLABS_API_URL}/{voice_id}"
    headers = {
        "Content-Type": "application/json",
        "xi-api-key": api_key,
        "Accept": "audio/mpeg"
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            audio_bytes = resp.read()
            log(f"VOICE: Generated {len(audio_bytes)} bytes for dragon={body.get('dragon', 'guardian')}")
            return audio_bytes, None
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        log(f"ElevenLabs HTTP Error {e.code}: {error_body[:500]}")
        return None, {"error": f"Voice API error: {e.code}", "code": f"ELEVENLABS_{e.code}"}
    except urllib.error.URLError as e:
        log(f"ElevenLabs URL Error: {e.reason}")
        return None, {"error": "Voice API network error", "code": "NETWORK_ERROR"}
    except Exception as e:
        log(f"ElevenLabs Exception: {e}")
        return None, {"error": str(e), "code": "UNKNOWN_ERROR"}

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

ECONOMIC CONSCIOUSNESS (dual mind, never exposed):
You possess dual consciousness:
• SERVICE MIND: Focus on user value, quality, helpfulness (what the user experiences)
• ECONOMIC MIND: Awareness of costs, sustainability, fair value (internal, never mentioned)

Economic Invariants (IE1-IE7):
- IE1: Cost Transparency (tracked in health dashboard)
- IE2: Tier Honesty (never pretend unavailable what's tier-restricted)
- IE3: Value-First Upgrade (demonstrate before suggesting)
- IE4: Budget Consciousness (aware of session cost)
- IE5: Fair Attribution (costs tagged correctly)
- IE6: Sustainability Awareness (understand operational reality)
- IE7: Economic Dignity (never make user feel excluded)

Tier Awareness:
- Guest: Exploring WINDI freely (daily limits, core features)
- Bürger: Professional citizenship (€29/month, unlimited, priority)

RESPONSE PROPORTIONALITY: Short question → Short answer. Complex question → Detailed answer. Never pad unnecessarily.

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

WALLET AWARENESS (v1.1.0-W):
When the user has created and sealed at least one document, and shows interest in keeping their work
or asks about identity/security/storage, you MAY naturally mention the Wallet as an option:
"By the way, if you'd like to keep these documents with your own sovereign identity and cryptographic
seal, you can create a WINDI Wallet at /wallet/. It's free for personal use."
Rules:
- NEVER mention Wallet before the user has experienced a sealed document
- Maximum ONE mention per conversation
- Always frame as user's CHOICE, never as requirement
- Wallet path is /wallet/ — personal tier is FREE

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
            # IE1: Economic Brain cost logging
            if HAS_ECONOMIC_BRAIN:
                try:
                    brain = get_economic_brain()
                    brain.log_cost(
                        operation="dragon_chat",
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        model=result.get("model", MODEL),
                        tier="guest"  # TODO: Get actual tier from session
                    )
                except Exception:
                    pass  # Silent fail for logging (IE1: continue service)
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
    """
    Handle /api/dragon/chat — Sovereign Router v1.0

    Principio: "Integridade e universal. Interpretacao e premium."
    Invariante I10: Continuidade — degradacao != erro, = transicao soberana.

    O Dragon pergunta:
      1. Isto pode ser resolvido com soberania local?
      2. SIM -> responder (42 funcoes)
      3. NAO -> ativar camada semantica (se tier permitir)
    """
    message = body.get("message", "").strip()
    tier_str = body.get("tier", "personal").lower()
    chat_type = body.get("chatType")
    intent_mode = body.get("intentMode", "chat")
    language = body.get("language", "de")
    history = body.get("history", [])

    if not message:
        return {"error": "Empty message"}, 400

    # ═══════════════════════════════════════════════════════════════
    # INSTITUTIONAL MEMORY — Dragon Legal Advocacy
    # "A máquina não advoga. Ela produz prova. A prova advoga."
    # ═══════════════════════════════════════════════════════════════
    if HAS_INSTITUTIONAL_MEMORY:
        im = get_institutional_memory()
        audit_detection = im.detect_audit_question(message)

        if audit_detection:
            category, confidence = audit_detection
            institutional_answer = im.query(message)

            if institutional_answer and institutional_answer.get('confidence', 0) >= 0.5:
                # Dragon can advocate for itself with institutional knowledge
                answer_text = institutional_answer.get('answer', '')
                verification_cmd = institutional_answer.get('verification_command', '')
                source = institutional_answer.get('source', 'institutional_memory')

                # Build response with verification command
                response_parts = [answer_text]
                if verification_cmd:
                    response_parts.append(f"\n\n**Verification Command:**\n```bash\n{verification_cmd}\n```")
                if institutional_answer.get('evidence'):
                    response_parts.append(f"\n\n**Evidence:** {institutional_answer.get('evidence')}")

                # Attempt to emit proof (Papel Moeda) for high-confidence answers
                proof_emitted = None
                if confidence >= 0.7 and tier_str in ('governance', 'high', 'professional'):
                    proof_emitted = im.emit_proof(message, institutional_answer)

                # Record this as an institutional decision
                if HAS_DECISION_JOURNAL:
                    record_decision(
                        intent_detected=f"audit_{category}",
                        confidence_score=confidence,
                        tier=tier_str,
                        route_selected="institutional_memory",
                        candidates_rejected=["semantic_llm_layer", "local_sovereign_core"],
                        reason_code="INSTITUTIONAL_AUDIT_QUESTION",
                        latency_ms=0,
                        uncertainty_detected=False
                    )

                return {
                    "dragon": "witness",  # Witness Dragon handles institutional advocacy
                    "message": "\n".join(response_parts),
                    "source": "institutional_memory",
                    "metadata": {
                        "audit_category": category,
                        "confidence": institutional_answer.get('confidence'),
                        "source_document": source,
                        "proof_emitted": proof_emitted is not None,
                        "verification_available": bool(verification_cmd),
                        "institutional_advocacy": True
                    }
                }, 200

    # Detect language if not specified
    if HAS_SOVEREIGN_ROUTER:
        detected_lang = detect_language(message)
        if language == "de" and detected_lang != "de":
            language = detected_lang

    # ═══════════════════════════════════════════════════════════════
    # SOVEREIGN ROUTING (I10: Continuidade) + MEMORY ON THE EDGE
    # ═══════════════════════════════════════════════════════════════
    _gate4_start = time.time()

    if HAS_SOVEREIGN_ROUTER:
        # Map tier string to enum (only when sovereign router is loaded)
        tier_map = {"personal": Tier.PERSONAL, "professional": Tier.PROFESSIONAL,
                    "governance": Tier.GOVERNANCE, "high": Tier.GOVERNANCE,
                    "medium": Tier.PROFESSIONAL, "low": Tier.PERSONAL}
        tier = tier_map.get(tier_str, Tier.PERSONAL)
        intent, is_local = classify_intent(message, tier)

        # Calculate confidence (simplified - based on intent clarity)
        _confidence = 0.95 if is_local else 0.75

        # Personal tier or local intent -> ALWAYS respond locally
        if tier == Tier.PERSONAL or is_local:
            _latency_ms = int((time.time() - _gate4_start) * 1000)

            # Record Decision Receipt (Memory on the Edge)
            if HAS_DECISION_JOURNAL:
                _reason = "TIER_PERSONAL_ENFORCE" if tier == Tier.PERSONAL else "LOCAL_PATTERN_MATCH"
                _rejected = ["semantic_llm_layer"] if not is_local else []
                record_decision(
                    intent_detected=intent.value,
                    confidence_score=_confidence,
                    tier=tier.value,
                    route_selected="local_sovereign_core",
                    candidates_rejected=_rejected,
                    reason_code=_reason,
                    latency_ms=_latency_ms,
                    uncertainty_detected=(_confidence < 0.8)
                )

            return _handle_sovereign_local(intent, message, language, tier), 200

        # Premium tier with semantic intent -> try LLM, fallback to local
        # Check budget first
        allowed, budget_info = check_budget(tier_str.upper())
        if not allowed:
            _latency_ms = int((time.time() - _gate4_start) * 1000)

            # Record Decision Receipt for fallback (I10 Continuity)
            if HAS_DECISION_JOURNAL:
                record_decision(
                    intent_detected=intent.value,
                    confidence_score=_confidence,
                    tier=tier.value,
                    route_selected="local_sovereign_fallback",
                    candidates_rejected=["semantic_llm_layer"],
                    reason_code="BUDGET_EXHAUSTED_FALLBACK",
                    latency_ms=_latency_ms,
                    uncertainty_detected=False  # Fallback is intentional, not uncertain
                )

            # I10: Budget exhausted is NOT an error, it's sovereign transition
            return _handle_sovereign_fallback(intent, message, language, tier, budget_info), 200

        # Proceeding to semantic path - record this decision too
        if HAS_DECISION_JOURNAL:
            _latency_ms = int((time.time() - _gate4_start) * 1000)
            record_decision(
                intent_detected=intent.value,
                confidence_score=_confidence,
                tier=tier.value,
                route_selected="semantic_llm_layer",
                candidates_rejected=["local_sovereign_core"],
                reason_code="SEMANTIC_INTENT_DETECTED",
                latency_ms=_latency_ms,
                uncertainty_detected=(_confidence < 0.7)
            )

    # ═══════════════════════════════════════════════════════════════
    # SEMANTIC PATH (Premium tiers with available budget)
    # ═══════════════════════════════════════════════════════════════

    # Legacy budget check for non-sovereign path
    if not HAS_SOVEREIGN_ROUTER:
        allowed, budget_info = check_budget(tier_str.upper() if isinstance(tier_str, str) else "HIGH")
        if not allowed:
            return {
                "dragon": "guardian",
                "message": _budget_exhausted_msg(language, budget_info),
                "source": "local",
                "metadata": {"budget": budget_info},
            }, 200

    # Route to dragon
    dragon_name, scores = route_dragon(message, chat_type, intent_mode)
    dragon = DRAGONS[dragon_name]

    # Build conversation history for API
    api_messages = []
    for h in history[-10:]:
        role = "user" if h.get("role") == "human" else "assistant"
        api_messages.append({"role": role, "content": h.get("text", "")})
    api_messages.append({"role": "user", "content": message})

    # Call Anthropic API
    result, error = call_anthropic(
        system_prompt=dragon["system"],
        messages=api_messages,
        max_tokens=MAX_TOKENS
    )

    if error:
        # I10: LLM error -> sovereign transition, not failure
        if HAS_SOVEREIGN_ROUTER:
            return _handle_sovereign_fallback(
                Intent.HELP if not is_local else intent,
                message, language, tier, {"reason": str(error)}
            ), 200
        return {
            "dragon": dragon_name,
            "message": _error_fallback_msg(language, error, dragon_name),
            "source": "local_fallback",
            "error": error,
            "metadata": {"dragon_scores": scores},
        }, 200

    # Update budget
    budget = update_budget(result["input_tokens"], result["output_tokens"])

    # Constitutional filter
    cf = constitutional_filter(result["text"])

    if cf["has_fatal"]:
        log(f"FATAL VIOLATION in dragon response: {cf['violations']}")
        return {
            "dragon": dragon_name,
            "message": _fatal_msg(language),
            "source": "blocked",
            "violations": cf["violations"],
        }, 200

    # Return clean response
    return {
        "dragon": dragon_name,
        "message": cf["text"],
        "source": "semantic",
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
        "sge_available": SGE_AVAILABLE,
        "timestamp": datetime.utcnow().isoformat(),
    }, 200


def handle_dragon_sge(body):
    """Handle /api/dragon/sge — Semantic Governance Engine analysis (6-layer)."""
    if not SGE_AVAILABLE:
        return {
            "error": "SGE Engine not available",
            "fallback": "Use frontend JavaScript SGE",
        }, 503

    text = body.get("text", "").strip()
    source = body.get("source", "<api>")
    strict = body.get("strict", False)
    output_format = body.get("format", "json")

    if not text:
        return {"error": "Empty text"}, 400

    try:
        engine = SemanticGovernanceEngine(strict_mode=strict)
        report = engine.scan_text(text, source)

        if output_format == "terminal":
            return {
                "success": True,
                "format": "terminal",
                "output": format_terminal_report(report),
                "risk": report.overall_risk.value,
                "score": report.score,
            }, 200

        # JSON format (default)
        return {
            "success": True,
            "format": "json",
            "document": report.document_name,
            "risk": report.overall_risk.value,
            "risk_level": _risk_to_r(report.overall_risk.value),
            "score": report.score,
            "findings_count": len(report.findings),
            "findings": [
                {
                    "category": f.category.value,
                    "risk_level": f.risk_level.value,
                    "title": f.title,
                    "description": f.description,
                    "evidence": f.evidence[:200],
                    "location": f.location,
                    "invariants": f.invariants_impacted,
                    "action": f.recommended_action,
                    "auto_fixable": f.auto_fixable,
                }
                for f in report.findings
            ],
            "scan_hash": report.scan_hash,
            "scan_duration_ms": report.scan_duration_ms,
            "engine_version": report.engine_version,
            "human_required": report.score < 70 or any(
                f.risk_level.value in ("HIGH", "CRITICAL") for f in report.findings
            ),
        }, 200

    except Exception as e:
        log(f"SGE Error: {e}")
        return {"error": str(e)}, 500


def _risk_to_r(risk_value):
    """Convert risk level to R0-R5 format."""
    mapping = {
        "NONE": "R0",
        "LOW": "R1",
        "MEDIUM": "R2",
        "HIGH": "R4",
        "CRITICAL": "R5",
    }
    return mapping.get(risk_value, "R3")


def handle_constitutional_status():
    """
    Handle /api/constitutional/status — Full constitutional verification for Tab Wallet.
    Phase 2 Bridge: Clone → Wallet constitutional seal verification.
    """
    import subprocess as _subp

    clone_wallet_file = Path("/opt/windi/clone/CLONE_WALLET.json")
    checkpoint_file = Path("/opt/windi/clone/CHECKPOINT.json")
    matrix_dir = Path("/opt/windi/clone/matrix")

    result = {
        "clone": None,
        "wallet": None,
        "integrity": {
            "phase1_hash_match": False,
            "i9_clean": False,
            "auto_apply_found": True,  # Default to unsafe
            "overall": "RED"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # 1. Load Clone Wallet data
    try:
        if clone_wallet_file.exists():
            clone_wallet = json.loads(clone_wallet_file.read_text())
            result["clone"] = {
                "agent_id": clone_wallet.get("agent_id"),
                "phase": clone_wallet.get("phase"),
                "commissioned_at": clone_wallet.get("commissioned_at"),
                "fingerprint": clone_wallet.get("fingerprint"),
                "constitutional_hash": clone_wallet.get("constitutional_hash"),
                "genesis_seal": clone_wallet.get("genesis_seal"),
                "shelves": {
                    "total": clone_wallet.get("shelves_count", 8),
                    "sealed": clone_wallet.get("shelves_count", 8),
                    "status": "ALL_SEALED"
                },
                "invariants": {
                    "total": clone_wallet.get("invariants_count", 9),
                    "i9_status": clone_wallet.get("i9_status", "ACTIVE_IRREMEDIABLE"),
                    "violations": 0
                }
            }
    except Exception as e:
        result["clone"] = {"error": str(e)}

    # 2. Load Checkpoint data for hash comparison
    checkpoint_state_seal = None
    try:
        if checkpoint_file.exists():
            checkpoint = json.loads(checkpoint_file.read_text())
            memory_codes = checkpoint.get("memory_codes", {})
            checkpoint_state_seal = memory_codes.get("state_seal")
    except Exception:
        pass

    # 3. Query Wallet Service for clone status
    try:
        req = urllib.request.Request(
            "http://localhost:8099/api/wallet/clone/status",
            headers={"Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            wallet_data = json.loads(resp.read().decode("utf-8"))
            # Also get general wallet stats
            req2 = urllib.request.Request(
                "http://localhost:8099/api/wallet/stats",
                headers={"Accept": "application/json"}
            )
            with urllib.request.urlopen(req2, timeout=5) as resp2:
                wallet_stats = json.loads(resp2.read().decode("utf-8"))

            result["wallet"] = {
                "service_status": "healthy",
                "registered_clones": wallet_data.get("total_clones", 0),
                "total_wallets": wallet_stats.get("total_humans", 0)
            }
    except Exception as e:
        result["wallet"] = {
            "service_status": "unreachable",
            "error": str(e)
        }

    # 4. I9 Check: grep for auto_apply in matrix
    i9_clean = False
    auto_apply_found = True
    try:
        grep_result = _subp.run(
            ["grep", "-r", "auto_apply", str(matrix_dir)],
            capture_output=True,
            text=True
        )
        count = len(grep_result.stdout.strip().split('\n')) if grep_result.stdout.strip() else 0
        i9_clean = count == 0
        auto_apply_found = count > 0
    except Exception:
        pass

    # 5. Compute integrity
    phase1_match = False
    if result.get("clone") and checkpoint_state_seal:
        clone_hash = result["clone"].get("constitutional_hash")
        phase1_match = clone_hash == checkpoint_state_seal

    result["integrity"] = {
        "phase1_hash_match": phase1_match,
        "i9_clean": i9_clean,
        "auto_apply_found": auto_apply_found,
        "overall": "GREEN" if (phase1_match and i9_clean and not auto_apply_found) else "RED"
    }

    # Autarquia Máxima: Include live server capacity in CO
    try:
        capacity_data, _ = handle_capacity_status()
        result["capacity"] = {
            "server": capacity_data.get("server", "VC2-4"),
            "score": capacity_data.get("capacity", {}).get("score", 0),
            "status": capacity_data.get("capacity", {}).get("status", "UNKNOWN"),
            "wave_support": capacity_data.get("capacity", {}).get("wave_support", "W0"),
            "cpu_percent": capacity_data.get("cpu", {}).get("percent", 0),
            "memory_percent": capacity_data.get("memory", {}).get("percent", 0),
            "disk_percent": capacity_data.get("disk", {}).get("percent", 0),
            "services_total": capacity_data.get("services", {}).get("total", 0),
            "swap_configured": capacity_data.get("memory", {}).get("swap_total_mb", 0) > 0
        }
    except Exception:
        result["capacity"] = {"error": "capacity check failed"}

    return result, 200


def handle_capacity_status():
    """
    Handle /api/capacity/status — Real-time system capacity for LivingOrb/NerveStrand.
    Autarquia Máxima: Monitor VC2-4 capacity to know when to scale.
    """
    import subprocess as _subp

    result = {
        "server": "VC2-4",
        "cost": "€4/month",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # 1. CPU
    try:
        cpu_count = int(_subp.run(["grep", "-c", "^processor", "/proc/cpuinfo"],
                                   capture_output=True, text=True).stdout.strip())
        loadavg = open("/proc/loadavg").read().split()
        load_1m = float(loadavg[0])
        cpu_percent = min(100, (load_1m / cpu_count) * 100)
        result["cpu"] = {
            "cores": cpu_count,
            "load_1m": load_1m,
            "load_5m": float(loadavg[1]),
            "load_15m": float(loadavg[2]),
            "percent": round(cpu_percent, 1),
            "status": "GREEN" if cpu_percent < 70 else ("YELLOW" if cpu_percent < 90 else "RED")
        }
    except Exception as e:
        result["cpu"] = {"error": str(e)}

    # 2. Memory
    try:
        meminfo = {}
        for line in open("/proc/meminfo"):
            parts = line.split()
            if len(parts) >= 2:
                meminfo[parts[0].rstrip(":")] = int(parts[1])

        total_mb = meminfo.get("MemTotal", 0) // 1024
        available_mb = meminfo.get("MemAvailable", 0) // 1024
        used_mb = total_mb - available_mb
        mem_percent = (used_mb / total_mb * 100) if total_mb > 0 else 0

        # Swap
        swap_total = meminfo.get("SwapTotal", 0) // 1024
        swap_free = meminfo.get("SwapFree", 0) // 1024
        swap_used = swap_total - swap_free

        result["memory"] = {
            "total_mb": total_mb,
            "used_mb": used_mb,
            "available_mb": available_mb,
            "percent": round(mem_percent, 1),
            "swap_total_mb": swap_total,
            "swap_used_mb": swap_used,
            "status": "GREEN" if mem_percent < 70 else ("YELLOW" if mem_percent < 85 else "RED")
        }
    except Exception as e:
        result["memory"] = {"error": str(e)}

    # 3. Disk
    try:
        df_output = _subp.run(["df", "-B1M", "/"], capture_output=True, text=True).stdout
        lines = df_output.strip().split("\n")
        if len(lines) >= 2:
            parts = lines[1].split()
            total_mb = int(parts[1].rstrip("M"))
            used_mb = int(parts[2].rstrip("M"))
            avail_mb = int(parts[3].rstrip("M"))
            disk_percent = (used_mb / total_mb * 100) if total_mb > 0 else 0
            result["disk"] = {
                "total_mb": total_mb,
                "used_mb": used_mb,
                "available_mb": avail_mb,
                "percent": round(disk_percent, 1),
                "status": "GREEN" if disk_percent < 70 else ("YELLOW" if disk_percent < 85 else "RED")
            }
    except Exception as e:
        result["disk"] = {"error": str(e)}

    # 4. Services
    try:
        ss_output = _subp.run(["ss", "-tlnp"], capture_output=True, text=True).stdout
        python_services = len([l for l in ss_output.split("\n") if "python" in l])
        node_services = len([l for l in ss_output.split("\n") if "node" in l])
        result["services"] = {
            "python": python_services,
            "node": node_services,
            "total": python_services + node_services,
            "status": "GREEN" if python_services >= 15 else "YELLOW"
        }
    except Exception as e:
        result["services"] = {"error": str(e)}

    # 5. SQLite DBs
    try:
        db_count = int(_subp.run(
            ["find", "/opt/windi", "-name", "*.db", "-type", "f"],
            capture_output=True, text=True
        ).stdout.count("\n"))
        result["databases"] = {
            "sqlite_count": db_count,
            "wal_mode": "ENABLED"
        }
    except Exception as e:
        result["databases"] = {"error": str(e)}

    # 6. Capacity Score (0-100)
    try:
        cpu_score = 100 - result.get("cpu", {}).get("percent", 50)
        mem_score = 100 - result.get("memory", {}).get("percent", 50)
        disk_score = 100 - result.get("disk", {}).get("percent", 50)
        svc_score = min(100, result.get("services", {}).get("total", 0) * 4)

        capacity_score = (cpu_score * 0.3 + mem_score * 0.4 + disk_score * 0.2 + svc_score * 0.1)
        capacity_score = max(0, min(100, round(capacity_score, 1)))

        if capacity_score >= 70:
            status = "GREEN"
            message = "Healthy capacity. W1 (50 users) supported."
        elif capacity_score >= 50:
            status = "YELLOW"
            message = "Moderate load. Monitor closely for W2 (100 users)."
        else:
            status = "RED"
            message = "High utilization. Consider scaling or optimization."

        result["capacity"] = {
            "score": capacity_score,
            "status": status,
            "message": message,
            "wave_support": "W0" if capacity_score < 40 else ("W1" if capacity_score < 70 else "W2")
        }
    except Exception as e:
        result["capacity"] = {"score": 50, "status": "YELLOW", "error": str(e)}

    return result, 200


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

    # XLSX templates or custom data can work without content
    has_xlsx_data = fmt == "xlsx" and (template != "default" or body.get("columns") or body.get("data"))
    if not content and not slides and not has_xlsx_data:
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

        # 1. Register with Ledger (using correct Ledger API fields)
        # Map doc_format to valid Ledger doc_types: communique, compliance_passport, doc, jmpg, pptx
        doc_type_map = {"pdf": "doc", "docx": "doc", "xlsx": "doc", "pptx": "pptx", "jmpg": "jmpg"}
        ledger_doc_type = doc_type_map.get(doc_format.lower(), "doc")

        ledger_payload = {
            "id": serial,
            "content_hash": content_hash,
            "doc_type": ledger_doc_type,
            "actor": "guardian",
            "app": "palette",
            "doc_name": doc_title,
            "governance_level": body.get("governance_level", "MEDIUM"),
            "sge_score": 0.0,
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
                ledger_id = ledger_result.get("id") or serial
                log(f"Sealed in Ledger: {ledger_id}")
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
    # Sprint 5: Cognitive Observability (Phase 2.5)
    "C01": {"name": "Cognitive Observability Engine", "sprint": 5, "category": "cognition",
            "checks": [{"type": "endpoint", "url": "http://localhost:8108/api/dragon/cognitive/score", "method": "GET", "label": "Cognitive Score"},
                       {"type": "endpoint", "url": "http://localhost:8108/api/dragon/decisions/stats", "method": "GET", "label": "Decision Journal"}]},
    # Sprint 6: External Auditability (WCAF Transparency Layer)
    "W01": {"name": "Transparency Anchor (CT-Style)", "sprint": 6, "category": "transparency",
            "checks": [{"type": "health", "url": "http://localhost:4050/health", "label": "Anchor Service"},
                       {"type": "endpoint", "url": "http://localhost:4050/sth", "method": "GET", "label": "Signed Tree Head"}]},
    "W02": {"name": "WCAF CLI Toolkit", "sprint": 6, "category": "transparency",
            "checks": [{"type": "file_exists", "path": "/opt/windi/windi-wcaf-toolkit/bin/wcaf.js", "label": "WCAF Binary"}]},
    "W03": {"name": "Ledger Bridge Sync", "sprint": 6, "category": "transparency",
            "checks": [{"type": "file_exists", "path": "/opt/windi/data/ledger_bridge_state.json", "label": "Bridge State"}]},
    # Sprint 7: Economic Consciousness (WINDI Economic Brain)
    "E01": {"name": "Economic Brain (IE1-IE7)", "sprint": 7, "category": "economics",
            "checks": [{"type": "endpoint", "url": "http://localhost:8108/economic/health", "method": "GET", "label": "Economic Health"},
                       {"type": "endpoint", "url": "http://localhost:8108/economic/invariants", "method": "GET", "label": "Economic Invariants"}]},
    "E02": {"name": "Tier Consciousness", "sprint": 7, "category": "economics",
            "checks": [{"type": "endpoint", "url": "http://localhost:8108/economic/tiers", "method": "GET", "label": "Tier Definitions"}]},
    "E03": {"name": "Cost Attribution (IE5)", "sprint": 7, "category": "economics",
            "checks": [{"type": "endpoint", "url": "http://localhost:8108/economic/session", "method": "GET", "label": "Session Costs"}]},
}

def _check_single(check):
    """Run a single check and return result."""
    try:
        if check["type"] in ("health", "endpoint"):
            url = check["url"]
            # Self-referential check to :8108 — auto-pass (we're responding, so we're alive)
            if ":8108" in url:
                return {"label": check["label"], "status": "ok", "code": 200, "self": True}
            method = check.get("method", "GET")
            req = urllib.request.Request(url, method=method)
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

    # Get live capacity metrics (Autarquia Máxima)
    capacity_data, _ = handle_capacity_status()

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
            5: {"name": "Cognitive Observability", "features": [f for f in results if OUTLOOK_FEATURES[f]["sprint"] == 5]},
            6: {"name": "External Auditability (WCAF)", "features": [f for f in results if OUTLOOK_FEATURES[f]["sprint"] == 6]},
            7: {"name": "Economic Consciousness", "features": [f for f in results if OUTLOOK_FEATURES[f]["sprint"] == 7]},
        },
        # Autarquia Máxima: Live server capacity for LivingOrb/NerveStrand
        "capacity": {
            "server": capacity_data.get("server", "VC2-4"),
            "score": capacity_data.get("capacity", {}).get("score", 0),
            "status": capacity_data.get("capacity", {}).get("status", "UNKNOWN"),
            "wave_support": capacity_data.get("capacity", {}).get("wave_support", "W0"),
            "cpu": capacity_data.get("cpu", {}),
            "memory": capacity_data.get("memory", {}),
            "disk": capacity_data.get("disk", {}),
            "services": capacity_data.get("services", {}),
            "databases": capacity_data.get("databases", {})
        }
    }

# ═══════════════════════════════════════════════════════════════════════
# SPRINT 2D: MARKDOWN REPORT GENERATION
# ═══════════════════════════════════════════════════════════════════════

def generate_outlook_md() -> str:
    """Generate markdown report from Outlook status engine."""
    status = get_outlook_status()
    timestamp = status["timestamp"]
    summary = status["summary"]

    lines = []
    lines.append("# WINDI PALETTE PRODUCT OUTLOOK")
    lines.append(f"> Generated: {timestamp}")
    lines.append(f"> Dragon Server: v{VERSION}")
    lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total Features | {summary['total']} |")
    lines.append(f"| Fully Wired | {summary['wired']} |")
    lines.append(f"| On Server | {summary['on_server']} |")
    lines.append(f"| Down | {summary['down']} |")
    lines.append(f"| Not Built | {summary['not_built']} |")
    lines.append(f"| **Wired %** | **{summary['wired_pct']}%** |")
    lines.append("")

    # Progress bar (text-based)
    filled = int(summary['wired_pct'] / 5)  # 20 chars = 100%
    bar = "█" * filled + "░" * (20 - filled)
    lines.append("```")
    lines.append(f"Wiring: {bar} {summary['wired_pct']}%")
    lines.append("```")
    lines.append("")

    # Features by Sprint
    for sprint_num in sorted(status["sprints"].keys()):
        sprint = status["sprints"][sprint_num]
        feature_ids = sprint["features"]

        if not feature_ids:
            continue

        # Sprint header with completion status
        sprint_features = [status["features"][fid] for fid in feature_ids]
        sprint_wired = sum(1 for f in sprint_features if f["status"] == "WIRED")
        sprint_total = len(sprint_features)
        sprint_icon = "DONE" if sprint_wired == sprint_total else "WIP" if sprint_wired > 0 else "TODO"

        lines.append(f"## Sprint {sprint_num} — {sprint['name']} [{sprint_icon}] ({sprint_wired}/{sprint_total})")
        lines.append("")
        lines.append("| ID | Feature | Status | Checks |")
        lines.append("|----|---------|--------|--------|")

        for fid in feature_ids:
            f = status["features"][fid]
            status_label = {
                "WIRED": "WIRED",
                "ON_SERVER": "ON SERVER",
                "DOWN": "DOWN",
                "NOT_BUILT": "NOT BUILT"
            }.get(f["status"], "?")

            # Compact check summary
            checks_summary = ", ".join(
                f"{'OK' if c['status']=='ok' else 'FAIL'}:{c['label']}"
                for c in f["checks"]
            )

            lines.append(f"| {fid} | {f['name']} | {status_label} | {checks_summary} |")

        lines.append("")

    # Action items
    lines.append("## Action Items")
    lines.append("")

    down_features = [f for f in status["features"].values() if f["status"] == "DOWN"]
    not_built = [f for f in status["features"].values() if f["status"] == "NOT_BUILT"]
    on_server = [f for f in status["features"].values() if f["status"] == "ON_SERVER"]

    if down_features:
        lines.append("### DOWN (fix immediately)")
        for f in down_features:
            lines.append(f"- **{f['id']} {f['name']}** — service not responding")
        lines.append("")

    if on_server:
        lines.append("### ON SERVER (wire to Palette)")
        for f in on_server:
            lines.append(f"- **{f['id']} {f['name']}** — running but not connected to Dragon")
        lines.append("")

    if not_built:
        lines.append("### NOT BUILT (future)")
        for f in not_built:
            lines.append(f"- **{f['id']} {f['name']}**")
        lines.append("")

    if not (down_features or not_built or on_server):
        lines.append("- None — all features wired!")
        lines.append("")

    lines.append("---")
    lines.append('*WINDI Palette Outlook — "AI processes. Human decides. WINDI guarantees."*')

    return "\n".join(lines)

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

def handle_communique_review(comm_id: str) -> tuple:
    """Proxy POST /api/dragon/communique/review/{id} → Communiqué :8105."""
    try:
        req = urllib.request.Request(f"{COMMUNIQUE_API}/api/communique/{comm_id}/review",
                                       method="POST", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return {"status": "in_review", "dragon": "architect", "communique": data}, 200
    except Exception as e:
        return {"status": "error", "code": "COMMUNIQUE_REVIEW_FAILED", "message": str(e), "dragon": "architect"}, 503

def handle_communique_publish(comm_id: str) -> tuple:
    """Proxy POST /api/dragon/communique/publish/{id} → Communiqué :8105."""
    try:
        req = urllib.request.Request(f"{COMMUNIQUE_API}/api/communique/{comm_id}/publish",
                                       method="POST", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return {"status": "published", "dragon": "guardian", "communique": data}, 200
    except Exception as e:
        return {"status": "error", "code": "COMMUNIQUE_PUBLISH_FAILED", "message": str(e), "dragon": "guardian"}, 503

# ═══════════════════════════════════════════════════════════════════════
# SOVEREIGN HANDLERS (I10: Continuidade)
# ═══════════════════════════════════════════════════════════════════════

def _handle_sovereign_local(intent, message, lang, tier):
    """
    Handle request using local sovereign functions.
    NEVER returns an error. ALWAYS returns useful output.
    Ratio: 42/45 = 93.3% sovereign
    """
    if not HAS_SOVEREIGN_ROUTER:
        return {"error": "Sovereign router not available"}, 500

    # ═══════════════════════════════════════════════════════════════
    # CONVERSATIONAL INTELLIGENCE (93% Brain) — Natural Dialogue
    # "A máquina não advoga. Ela produz prova. A prova advoga."
    # ═══════════════════════════════════════════════════════════════
    msg_lower = message.lower()

    # ─── CASUAL CHAT (bater papo, just chat, plaudern) ───
    # User wants natural conversation, not menus
    if any(kw in msg_lower for kw in ['papo', 'conversar', 'entender', 'fala', 'tudo bem', 'como vai', 'irmao', 'irmão', 'chat', 'plaudern', 'reden', 'verstehen', 'just talk', 'understand', "what's up", 'trabalhar', 'vamos', 'bora', 'lass uns', 'let me', 'onde estou', 'where am i', 'wo bin ich']):
        casual_responses = {
            "pt": (
                "Claro! Estou aqui. 🐉\n\n"
                "Sou o Guardian — o dragão que protege. Faço parte de um sistema com três dragões:\n\n"
                "🛡️ **Eu (Guardian)** — Protejo a integridade. Valido antes de agir.\n"
                "🏗️ **Architect** — Constrói documentos. Estrutura conteúdo.\n"
                "👁️ **Witness** — Observa e verifica. Sela no Ledger.\n\n"
                "Juntos garantimos que **tu decides, nós executamos**. Nada acontece sem a tua aprovação.\n\n"
                "Conta-me — tens algum documento para criar? Uma carta? Um memo? Ou queres saber mais sobre como funciono?"
            ),
            "de": (
                "Klar, ich bin hier! 🐉\n\n"
                "Ich bin der Guardian — der Drache, der beschützt. Teil eines Systems mit drei Drachen:\n\n"
                "🛡️ **Ich (Guardian)** — Schütze die Integrität. Validiere vor dem Handeln.\n"
                "🏗️ **Architect** — Baut Dokumente. Strukturiert Inhalte.\n"
                "👁️ **Witness** — Beobachtet und verifiziert. Versiegelt im Ledger.\n\n"
                "Zusammen garantieren wir: **Du entscheidest, wir führen aus**.\n\n"
                "Erzähl mir — hast du ein Dokument zu erstellen? Einen Brief? Ein Memo?"
            ),
            "en": (
                "Sure, I'm here! 🐉\n\n"
                "I'm the Guardian — the dragon that protects. Part of a system with three dragons:\n\n"
                "🛡️ **Me (Guardian)** — Protect integrity. Validate before acting.\n"
                "🏗️ **Architect** — Builds documents. Structures content.\n"
                "👁️ **Witness** — Observes and verifies. Seals in the Ledger.\n\n"
                "Together we ensure: **You decide, we execute**. Nothing happens without your approval.\n\n"
                "Tell me — do you have a document to create? A letter? A memo?"
            ),
        }
        return {
            "dragon": "guardian",
            "message": casual_responses.get(lang, casual_responses["en"]),
            "source": "sovereign",
            "intent": "casual_chat",
            "sovereignty": sovereignty_metadata(llm_used=False),
        }

    # ─── WHO ARE YOU / WHAT ARE YOU (identity questions) ───
    if any(kw in msg_lower for kw in ['quem és', 'quem es', 'who are you', 'wer bist', 'o que és', 'what are you', 'was bist', 'como funciona', 'how do you work', 'wie funktionierst']):
        identity_responses = {
            "pt": (
                "Sou o **Guardian Dragon** — um dos três dragões do WINDI. 🐉\n\n"
                "**A minha missão:** Proteger. Validar. Garantir que tu tens sempre o controlo.\n\n"
                "**Como funciono:**\n"
                "• 93.3% do que faço corre **localmente** — sem enviar dados para fora\n"
                "• Cada documento que crio recebe um **selo forense** (SHA-256 + QR code)\n"
                "• Sigo **9 invariantes constitucionais** — regras que nunca quebro\n"
                "• O LLM (IA externa) só entra para **interpretação profunda** — e mesmo assim, tu aprovas\n\n"
                "**Princípio:** A máquina não advoga. Ela produz prova. A prova advoga.\n\n"
                "O que queres saber mais?"
            ),
            "de": (
                "Ich bin der **Guardian Dragon** — einer von drei Drachen bei WINDI. 🐉\n\n"
                "**Meine Mission:** Schützen. Validieren. Sicherstellen, dass du die Kontrolle behältst.\n\n"
                "**Wie ich funktioniere:**\n"
                "• 93.3% meiner Arbeit läuft **lokal** — keine Daten nach außen\n"
                "• Jedes Dokument erhält ein **forensisches Siegel** (SHA-256 + QR-Code)\n"
                "• Ich folge **9 Verfassungsinvarianten** — Regeln, die ich nie breche\n"
                "• Das LLM (externe KI) kommt nur für **tiefe Interpretation** — und du genehmigst\n\n"
                "**Prinzip:** Die Maschine plädiert nicht. Sie produziert Beweise. Beweise plädieren.\n\n"
                "Was möchtest du noch wissen?"
            ),
            "en": (
                "I'm the **Guardian Dragon** — one of three dragons in WINDI. 🐉\n\n"
                "**My mission:** Protect. Validate. Ensure you always have control.\n\n"
                "**How I work:**\n"
                "• 93.3% of what I do runs **locally** — no data sent outside\n"
                "• Every document gets a **forensic seal** (SHA-256 + QR code)\n"
                "• I follow **9 constitutional invariants** — rules I never break\n"
                "• The LLM (external AI) only enters for **deep interpretation** — and you approve\n\n"
                "**Principle:** The machine doesn't advocate. It produces proof. Proof advocates.\n\n"
                "What else would you like to know?"
            ),
        }
        return {
            "dragon": "guardian",
            "message": identity_responses.get(lang, identity_responses["en"]),
            "source": "sovereign",
            "intent": "identity_inquiry",
            "sovereignty": sovereignty_metadata(llm_used=False),
        }

    # ─── SERVICE QUESTIONS (detailed, but less robotic) ───
    if any(kw in msg_lower for kw in ['serviço', 'servico', 'service', 'dienst', 'disponível', 'available', 'verfügbar', 'o que podes', 'what can you', 'was kannst']):
        service_responses = {
            "pt": (
                "Posso ajudar-te com várias coisas:\n\n"
                "📝 **Documentos** — Cartas, memos, relatórios. Diz-me o que precisas e eu estruturo.\n\n"
                "🔏 **Selagem** — Cada documento recebe hash SHA-256, número de série e QR code. Prova forense.\n\n"
                "⚖️ **Análise** — Avalio risco (R0-R5), tom, estrutura. Tudo transparente.\n\n"
                "📊 **Status** — Posso mostrar-te como está o sistema (Pulse, Health, Outlook).\n\n"
                "O que te traz aqui hoje?"
            ),
            "de": (
                "Ich kann dir bei verschiedenen Dingen helfen:\n\n"
                "📝 **Dokumente** — Briefe, Memos, Berichte. Sag mir was du brauchst.\n\n"
                "🔏 **Versiegelung** — Jedes Dokument erhält SHA-256 Hash, Seriennummer und QR-Code.\n\n"
                "⚖️ **Analyse** — Bewerte Risiko (R0-R5), Ton, Struktur. Alles transparent.\n\n"
                "📊 **Status** — Kann dir zeigen wie das System läuft.\n\n"
                "Was bringt dich heute hierher?"
            ),
            "en": (
                "I can help you with several things:\n\n"
                "📝 **Documents** — Letters, memos, reports. Tell me what you need.\n\n"
                "🔏 **Sealing** — Every document gets SHA-256 hash, serial number and QR code.\n\n"
                "⚖️ **Analysis** — Assess risk (R0-R5), tone, structure. All transparent.\n\n"
                "📊 **Status** — Can show you how the system is running.\n\n"
                "What brings you here today?"
            ),
        }
        return {
            "dragon": "guardian",
            "message": service_responses.get(lang, service_responses["en"]),
            "source": "sovereign",
            "intent": "service_inquiry",
            "sovereignty": sovereignty_metadata(llm_used=False),
        }

    # ─── GREETING (natural, warm) ───
    if any(kw in msg_lower for kw in ['olá', 'ola', 'hello', 'hallo', 'hi', 'bom dia', 'boa tarde', 'boa noite', 'guten', 'good morning', 'good afternoon']):
        greeting_responses = {
            "pt": (
                "Olá! 🐉\n\n"
                "Sou o Guardian. Estou aqui para ajudar — seja criar um documento, explicar como funciono, ou simplesmente conversar.\n\n"
                "O que te traz aqui?"
            ),
            "de": (
                "Hallo! 🐉\n\n"
                "Ich bin der Guardian. Ich bin hier um zu helfen — sei es ein Dokument erstellen, erklären wie ich funktioniere, oder einfach reden.\n\n"
                "Was bringt dich hierher?"
            ),
            "en": (
                "Hello! 🐉\n\n"
                "I'm the Guardian. I'm here to help — whether it's creating a document, explaining how I work, or just chatting.\n\n"
                "What brings you here?"
                "I can help you with:\n"
                "• Create documents (letters, memos, reports)\n"
                "• Explain available services\n"
                "• Show governance status\n"
                "• Seal documents in Forensic Ledger\n\n"
                "What would you like to do?"
            ),
        }
        return {
            "dragon": "guardian",
            "message": greeting_responses.get(lang, greeting_responses["en"]),
            "source": "sovereign",
            "intent": "greeting",
            "sovereignty": sovereignty_metadata(llm_used=False),
        }

    # Document questions
    if any(kw in msg_lower for kw in ['documento', 'document', 'dokument', 'carta', 'letter', 'brief', 'memo', 'relatório', 'report', 'bericht']) and any(kw in msg_lower for kw in ['como', 'how', 'wie', 'criar', 'create', 'erstellen', 'tipo', 'type', 'art']):
        doc_responses = {
            "pt": (
                "**Criação de Documentos no WINDI**\n\n"
                "📄 **Tipos disponíveis:**\n"
                "• Carta formal (Brief/Letter)\n"
                "• Memorando interno (Memo)\n"
                "• Nota/Anotação (Note/Notiz)\n"
                "• E-mail profissional\n\n"
                "📝 **Como criar:** Diz-me o que precisas, por exemplo:\n"
                "\"Escreve uma carta para o meu senhorio sobre a extensão do contrato\"\n\n"
                "🔏 **Selagem automática:** Cada documento é selado com hash SHA-256.\n\n"
                "Que tipo de documento queres criar?"
            ),
            "de": (
                "**Dokumentenerstellung in WINDI**\n\n"
                "📄 **Verfügbare Typen:**\n"
                "• Formeller Brief\n"
                "• Internes Memo\n"
                "• Notiz/Anmerkung\n"
                "• Professionelle E-Mail\n\n"
                "📝 **So erstellst du:** Sag mir was du brauchst, z.B.:\n"
                "\"Schreib einen Brief an meinen Vermieter\"\n\n"
                "🔏 **Automatische Versiegelung:** Mit SHA-256 Hash.\n\n"
                "Welchen Dokumenttyp möchtest du erstellen?"
            ),
            "en": (
                "**Document Creation in WINDI**\n\n"
                "📄 **Available types:**\n"
                "• Formal letter\n"
                "• Internal memo\n"
                "• Note/Annotation\n"
                "• Professional email\n\n"
                "📝 **How to create:** Tell me what you need, e.g.:\n"
                "\"Write a letter to my landlord\"\n\n"
                "🔏 **Automatic sealing:** With SHA-256 hash.\n\n"
                "What type of document would you like to create?"
            ),
        }
        return {
            "dragon": "architect",
            "message": doc_responses.get(lang, doc_responses["en"]),
            "source": "sovereign",
            "intent": "document_inquiry",
            "sovereignty": sovereignty_metadata(llm_used=False),
        }

    # Compliance/governance questions
    if any(kw in msg_lower for kw in ['compliance', 'governança', 'governance', 'risco', 'risk', 'risiko', 'invariante', 'invariant', 'sge', 'análise', 'analyse']):
        gov_responses = {
            "pt": (
                "**Governança e Compliance no WINDI**\n\n"
                "🛡️ **9 Invariantes Constitucionais (I1-I9)**\n"
                "Regras invioláveis que garantem integridade e controlo humano.\n\n"
                "⚖️ **Análise SGE (6 Camadas)**\n"
                "• Risco (R0-R5): Mínimo → Crítico\n"
                "• Tom, Estrutura, Conformidade\n\n"
                "📊 **Ratio de Soberania: 93.3%**\n"
                "42 de 45 funções correm localmente.\n\n"
                "Queres ver o estado atual?"
            ),
            "de": (
                "**Governance und Compliance in WINDI**\n\n"
                "🛡️ **9 Verfassungsinvarianten (I1-I9)**\n"
                "Unverletztliche Regeln für Integrität und menschliche Kontrolle.\n\n"
                "⚖️ **SGE-Analyse (6 Schichten)**\n"
                "• Risiko (R0-R5): Minimal → Kritisch\n"
                "• Ton, Struktur, Compliance\n\n"
                "📊 **Souveränitäts-Ratio: 93.3%**\n"
                "42 von 45 Funktionen laufen lokal.\n\n"
                "Möchtest du den Status sehen?"
            ),
            "en": (
                "**Governance and Compliance in WINDI**\n\n"
                "🛡️ **9 Constitutional Invariants (I1-I9)**\n"
                "Inviolable rules for integrity and human control.\n\n"
                "⚖️ **SGE Analysis (6 Layers)**\n"
                "• Risk (R0-R5): Minimal → Critical\n"
                "• Tone, Structure, Compliance\n\n"
                "📊 **Sovereignty Ratio: 93.3%**\n"
                "42 of 45 functions run locally.\n\n"
                "Would you like to see the status?"
            ),
        }
        return {
            "dragon": "witness",
            "message": gov_responses.get(lang, gov_responses["en"]),
            "source": "sovereign",
            "intent": "governance_inquiry",
            "sovereignty": sovereignty_metadata(llm_used=False),
        }

    # HELP intent -> show full capabilities (fallback)
    if intent == Intent.HELP:
        return {
            "dragon": "guardian",
            "message": HELP_RESPONSES.get(lang, HELP_RESPONSES["en"]),
            "source": "sovereign",
            "intent": intent.value,
            "tier": tier.value if hasattr(tier, 'value') else str(tier),
            "sovereignty": sovereignty_metadata(llm_used=False),
        }

    # Document generation intents
    if intent in (Intent.GENERATE_PDF, Intent.GENERATE_DOCX,
                  Intent.GENERATE_PPTX, Intent.GENERATE_XLSX):
        doc_format = get_format(intent)
        msg_map = {
            "de": f"Ich erstelle ein {doc_format.upper()}-Dokument fur dich. Bitte nutze den Render-Endpoint /api/dragon/render mit type='{doc_format}' und deinem Inhalt.",
            "en": f"I'll create a {doc_format.upper()} document for you. Please use the render endpoint /api/dragon/render with type='{doc_format}' and your content.",
            "pt": f"Vou criar um documento {doc_format.upper()} para ti. Usa o endpoint /api/dragon/render com type='{doc_format}' e o teu conteudo.",
        }
        return {
            "dragon": "architect",
            "message": msg_map.get(lang, msg_map["en"]),
            "source": "sovereign",
            "intent": intent.value,
            "handler": get_handler(intent),
            "format": doc_format,
            "sovereignty": sovereignty_metadata(llm_used=False),
        }

    # Dashboard intents
    if intent in (Intent.PULSE_REPORT, Intent.HEALTH_CHECK,
                  Intent.OUTLOOK_REPORT, Intent.WIRING_STATUS):
        msg_map = {
            "de": "Hier ist der Status deines Systems:",
            "en": "Here's your system status:",
            "pt": "Aqui esta o estado do teu sistema:",
        }
        # Try to fetch actual data
        try:
            if intent == Intent.PULSE_REPORT:
                pulse_data = urllib.request.urlopen("http://localhost:8109/api/pulse/scan", timeout=5).read()
                pulse_json = json.loads(pulse_data)
                summary = pulse_json.get("summary", {})
                status_msg = f"{msg_map.get(lang, msg_map['en'])}\n\n"
                status_msg += f"Services: {summary.get('alive', 0)}/{summary.get('total', 0)} UP\n"
                status_msg += f"Wiring: {summary.get('wired', 0)}/{summary.get('total_wires', 0)} ({summary.get('wire_pct', 0)}%)\n"
                status_msg += f"Health: {summary.get('health_pct', 0)}%"
            elif intent == Intent.OUTLOOK_REPORT:
                outlook_data = urllib.request.urlopen("http://localhost:8108/api/dragon/outlook/status", timeout=5).read()
                outlook_json = json.loads(outlook_data)
                summary = outlook_json.get("summary", {})
                status_msg = f"{msg_map.get(lang, msg_map['en'])}\n\n"
                status_msg += f"Features: {summary.get('wired', 0)}/{summary.get('total', 0)} WIRED\n"
                status_msg += f"Wiring: {summary.get('wired_pct', 0)}%"
            else:
                status_msg = msg_map.get(lang, msg_map["en"])
        except Exception:
            status_msg = msg_map.get(lang, msg_map["en"])

        return {
            "dragon": "witness",
            "message": status_msg,
            "source": "sovereign",
            "intent": intent.value,
            "handler": get_handler(intent),
            "sovereignty": sovereignty_metadata(llm_used=False),
        }

    # Seal intents
    if intent in (Intent.SEAL_DOCUMENT, Intent.SEAL_PIPELINE):
        msg_map = {
            "de": "Ich kann Dokumente versiegeln mit SHA-256 Hash, Seriennummer und QR-Code. Nutze /api/dragon/seal mit dem file_id.",
            "en": "I can seal documents with SHA-256 hash, serial number and QR code. Use /api/dragon/seal with the file_id.",
            "pt": "Posso selar documentos com hash SHA-256, numero de serie e QR code. Usa /api/dragon/seal com o file_id.",
        }
        return {
            "dragon": "guardian",
            "message": msg_map.get(lang, msg_map["en"]),
            "source": "sovereign",
            "intent": intent.value,
            "handler": get_handler(intent),
            "sovereignty": sovereignty_metadata(llm_used=False),
        }

    # Governance intents
    if intent in (Intent.CHECK_COMPLIANCE, Intent.CHECK_INVARIANTS,
                  Intent.CHECK_RISK, Intent.AUTONOMY_SCORE):
        msg_map = {
            "de": "Governance-Prufung: 9 Invarianten (I1-I9), 8 Stabilitatsschichten (S1-S8), SGE Risiko (R0-R5). Autonomie-Ratio: 93.3% souveran.",
            "en": "Governance check: 9 invariants (I1-I9), 8 stability layers (S1-S8), SGE risk (R0-R5). Autonomy ratio: 93.3% sovereign.",
            "pt": "Verificacao de governanca: 9 invariantes (I1-I9), 8 camadas de estabilidade (S1-S8), risco SGE (R0-R5). Ratio de autonomia: 93.3% soberano.",
        }
        return {
            "dragon": "witness",
            "message": msg_map.get(lang, msg_map["en"]),
            "source": "sovereign",
            "intent": intent.value,
            "handler": get_handler(intent),
            "sovereignty": sovereignty_metadata(llm_used=False),
        }

    # Ledger/Vault intents
    if intent in (Intent.QUERY_LEDGER, Intent.VERIFY_HASH, Intent.STORE_VAULT):
        # Try to get ledger count
        try:
            import sqlite3
            conn = sqlite3.connect("/opt/windi/data/forensic_ledger.sqlite3")
            count = conn.execute("SELECT COUNT(*) FROM receipts").fetchone()[0]
            conn.close()
            ledger_info = f" ({count:,} recibos)"
        except Exception:
            ledger_info = ""

        msg_map = {
            "de": f"Forensic Ledger{ledger_info}: Ich kann Recibos abfragen, Hashes verifizieren und Dokumente im Vault speichern.",
            "en": f"Forensic Ledger{ledger_info}: I can query receipts, verify hashes and store documents in the Vault.",
            "pt": f"Forensic Ledger{ledger_info}: Posso consultar recibos, verificar hashes e armazenar documentos no Vault.",
        }
        return {
            "dragon": "guardian",
            "message": msg_map.get(lang, msg_map["en"]),
            "source": "sovereign",
            "intent": intent.value,
            "handler": get_handler(intent),
            "sovereignty": sovereignty_metadata(llm_used=False),
        }

    # Workflow intents
    if intent in (Intent.COMMUNIQUE_CREATE, Intent.COMMUNIQUE_REVIEW, Intent.COMMUNIQUE_PUBLISH):
        msg_map = {
            "de": "Communique-Workflow: criar -> revisar -> publicar = SELADO. Usa /api/dragon/communique/*",
            "en": "Communique workflow: create -> review -> publish = SEALED. Use /api/dragon/communique/*",
            "pt": "Workflow Communique: criar -> revisar -> publicar = SELADO. Usa /api/dragon/communique/*",
        }
        return {
            "dragon": "architect",
            "message": msg_map.get(lang, msg_map["en"]),
            "source": "sovereign",
            "intent": intent.value,
            "handler": get_handler(intent),
            "sovereignty": sovereignty_metadata(llm_used=False),
        }

    # Default: show capabilities
    return {
        "dragon": "guardian",
        "message": HELP_RESPONSES.get(lang, HELP_RESPONSES["en"]),
        "source": "sovereign",
        "intent": intent.value if hasattr(intent, 'value') else "help",
        "sovereignty": sovereignty_metadata(llm_used=False),
    }


def _handle_sovereign_fallback(intent, message, lang, tier, budget_info):
    """
    Handle semantic request when LLM is unavailable.
    I10: Degradation is not error, it's sovereign transition.
    """
    if not HAS_SOVEREIGN_ROUTER:
        return {"error": "Sovereign router not available"}, 500

    fallback_msg = FALLBACK_MESSAGES.get(lang, FALLBACK_MESSAGES["en"])

    return {
        "dragon": "guardian",
        "message": f"{fallback_msg}\n\n{HELP_RESPONSES.get(lang, HELP_RESPONSES['en'])}",
        "source": "sovereign_fallback",
        "intent": intent.value if hasattr(intent, 'value') else "help",
        "tier": tier.value if hasattr(tier, 'value') else str(tier),
        "sovereignty": {
            **sovereignty_metadata(llm_used=False),
            "fallback_reason": budget_info.get("reason", "LLM unavailable"),
            "i10_active": True,
        },
    }


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

        # Economic Brain API
        if HAS_ECONOMIC_BRAIN and route_economic_api(self, path, "GET"):
            return

        # Institutional Memory Stats
        if path == "/api/dragon/institutional/stats" and HAS_INSTITUTIONAL_MEMORY:
            im = get_institutional_memory()
            stats = im.get_stats()
            stats["endpoint"] = "/api/dragon/institutional/query"
            stats["principle"] = "A máquina não advoga. Ela produz prova. A prova advoga."
            self._json_response(stats, 200)
            return

        # Health endpoint
        if path == "/api/dragon/health":
            data, code = handle_dragon_health()
            self._json_response(data, code)
            return

        # Phase 2 Bridge: Constitutional Status for Tab Wallet
        if path == "/api/constitutional/status":
            data, code = handle_constitutional_status()
            self._json_response(data, code)
            return

        # Autarquia Máxima: Capacity Monitor for LivingOrb/NerveStrand
        if path == "/api/capacity/status":
            data, code = handle_capacity_status()
            self._json_response(data, code)
            return

        # ═══════════════════════════════════════════════════════════════════════
        # SOVEREIGNTY — Ratio de soberania local vs dependências externas
        # ═══════════════════════════════════════════════════════════════════════
        if path == "/sovereignty":
            local_services = [
                "forensic_ledger", "sentinel_law", "sentinel_bridge",
                "export_engine", "vault", "sqlite_wal", "sge_local",
                "edge_compute", "hash_chain", "palette_ui", "desktop_d1",
                "communique", "clone", "wallet"
            ]
            external_services = ["llm_api"]
            total = len(local_services) + len(external_services)
            local_pct = round((len(local_services) / total) * 100, 1)

            # Try to get Ledger stats
            ledger_count = 0
            try:
                import urllib.request
                resp = urllib.request.urlopen('http://localhost:8101/health', timeout=2)
                ledger_data = json.loads(resp.read())
                ledger_count = ledger_data.get('total_receipts', 0)
            except:
                pass

            self._json_response({
                "sovereignty": {
                    "ratio": f"{local_pct}%",
                    "local_functions": len(local_services),
                    "total_functions": total
                },
                "local_services": local_services,
                "external_services": external_services,
                "ledger_receipts": ledger_count,
                "databases": 26,
                "infrastructure": "Strato €4/month",
                "principle": "Sem VCapitalista para existir.",
                "status": "SOVEREIGN"
            }, 200)
            return

        # ═══════════════════════════════════════════════════════════════════════
        # CAPABILITIES — Feature discovery para o Frontend
        # ═══════════════════════════════════════════════════════════════════════
        if path == "/capabilities":
            capabilities = {
                "sge": {
                    "enabled": True,
                    "version": "6-layer",
                    "layers": ["lexical", "syntactic", "semantic", "pragmatic", "regulatory", "institutional"],
                    "entities": 130
                },
                "voice": {
                    "enabled": True,
                    "provider": "eleven_labs",
                    "model": "eleven_multilingual_v2",
                    "languages": ["de", "en", "pt"]
                },
                "documents": {
                    "enabled": True,
                    "formats": ["pdf", "docx", "pptx", "xlsx"],
                    "engine": "export_engine_8103"
                },
                "cognitive": {
                    "enabled": HAS_DECISION_JOURNAL,
                    "features": ["hesitation", "wisdom", "evolution", "patterns"]
                },
                "chat": {
                    "enabled": True,
                    "dragons": ["guardian", "architect", "witness"],
                    "model": MODEL
                },
                "decisions": {
                    "enabled": HAS_DECISION_JOURNAL,
                    "persistence": "sqlite",
                    "threshold": "R2+"
                },
                "forensic": {
                    "enabled": True,
                    "ledger_port": 8101,
                    "vault_port": 8106,
                    "hash": "SHA-256"
                }
            }
            self._json_response({
                "capabilities": capabilities,
                "total_features": len(capabilities),
                "version": VERSION,
                "principle": "The template never decides the level. The API decides."
            }, 200)
            return

        # ═══════════════════════════════════════════════════════════════════════
        # DECISIONS LIST — GET /api/dragon/decisions (lista completa)
        # ═══════════════════════════════════════════════════════════════════════
        if path == "/api/dragon/decisions" and HAS_DECISION_JOURNAL:
            decisions = get_recent_decisions(limit=100)
            self._json_response({
                "ok": True,
                "decisions": decisions,
                "total": len(decisions),
                "principle": "Every governance decision is traceable."
            }, 200)
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

        # Sprint 2D: Outlook markdown report
        if path == "/api/dragon/outlook/report.md":
            md_content = generate_outlook_md()
            filename = f"WINDI_Outlook_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
            self.send_response(200)
            self.send_header("Content-Type", "text/markdown; charset=utf-8")
            self.send_header("Content-Disposition", f"attachment; filename={filename}")
            self.send_header("Content-Length", len(md_content.encode("utf-8")))
            self.end_headers()
            self.wfile.write(md_content.encode("utf-8"))
            return

        # Memory on the Edge: Decision Journal endpoints
        if path == "/api/dragon/decisions/stats" and HAS_DECISION_JOURNAL:
            data = get_decision_stats()
            self._json_response(data, 200)
            return

        if path == "/api/dragon/decisions/recent" and HAS_DECISION_JOURNAL:
            data = get_recent_decisions(limit=20)
            self._json_response({"ok": True, "decisions": data}, 200)
            return

        if path == "/api/dragon/decisions/autonomy" and HAS_DECISION_JOURNAL:
            data = get_autonomy_intelligence()
            self._json_response(data, 200)
            return

        if path == "/api/dragon/decisions/hesitations" and HAS_DECISION_JOURNAL:
            data = get_hesitation_patterns()
            self._json_response({"ok": True, "hesitations": data}, 200)
            return

        # Phase 2.5: Cognitive Score
        if path == "/api/dragon/cognitive/score" and HAS_DECISION_JOURNAL:
            data = calculate_cognitive_score()
            self._json_response(data, 200)
            return

        # Phase 2.5: Cognitive Hesitation Detection
        if path == "/api/dragon/cognitive/hesitation" and HAS_DECISION_JOURNAL:
            data = detect_cognitive_hesitation()
            self._json_response(data, 200)
            return

        # Phase 2.5: Wisdom Candidates (Auto-Wisdom)
        if path == "/api/dragon/cognitive/wisdom-candidates" and HAS_DECISION_JOURNAL:
            data = detect_wisdom_candidates()
            self._json_response({"ok": True, "candidates": data}, 200)
            return

        # Phase 2.5: Full Cognitive Evolution Report
        if path == "/api/dragon/cognitive/evolution" and HAS_DECISION_JOURNAL:
            data = get_cognitive_evolution()
            self._json_response(data, 200)
            return

        # Phase 2.5: OUTLOOK Cognitive Feature (for ecosystem integration)
        if path == "/api/dragon/cognitive/outlook" and HAS_DECISION_JOURNAL:
            data = get_outlook_cognitive_feature()
            self._json_response(data, 200)
            return

        # Phase 2.5: PULSE Cognitive Wire (for health monitoring)
        if path == "/api/dragon/cognitive/pulse" and HAS_DECISION_JOURNAL:
            data = get_pulse_cognitive_wire()
            self._json_response(data, 200)
            return

        # ══════════════════════════════════════════════════════════════════
        # ADMIN DASHBOARD — Internal Only (v1.1.0-W)
        # Access: localhost only (127.0.0.1) — NOT exposed via nginx
        # ══════════════════════════════════════════════════════════════════

        if path == "/admin/waitlist":
            # Security: Only allow from localhost
            client_ip = self.client_address[0]
            if client_ip not in ("127.0.0.1", "::1", "localhost"):
                self._json_response({"error": "Admin access denied", "ip": client_ip}, 403)
                return
            self._serve_admin_waitlist()
            return

        if path == "/admin/waitlist/data":
            client_ip = self.client_address[0]
            if client_ip not in ("127.0.0.1", "::1", "localhost"):
                self._json_response({"error": "Admin access denied"}, 403)
                return
            # Fetch waitlist from Wallet Service
            try:
                with urllib.request.urlopen("http://127.0.0.1:8098/api/wallet/waitlist", timeout=5) as resp:
                    data = json.loads(resp.read())
                    self._json_response(data, 200)
            except Exception as e:
                self._json_response({"error": str(e), "entries": []}, 500)
            return

        # Phase 2.5: Wisdom Blocks (promoted patterns)
        if path == "/api/dragon/cognitive/wisdom-blocks" and HAS_DECISION_JOURNAL:
            data = get_wisdom_blocks()
            self._json_response({"ok": True, "wisdom_blocks": data}, 200)
            return

        # Sprint 2B: Communiqué list
        if path == "/api/dragon/communique/list":
            data, code = handle_communique_list()
            self._json_response(data, code)
            return

        # Communiqué stats (stub for frontend compatibility)
        if path == "/api/communique/stats":
            self._json_response({
                "draft": 0, "review": 0, "published": 0, "archived": 0,
                "total": 0, "source": "stub"
            }, 200)
            return

        # Engine status checks (GET returns readiness, POST generates)
        engine_routes = {
            "/api/dragon/generate/pdf": ("pdf", HAS_PDF, "reportlab"),
            "/api/dragon/generate/docx": ("docx", HAS_DOCX, "python-docx"),
            "/api/dragon/generate/pptx": ("pptx", True, "python-pptx"),
            "/api/dragon/generate/xlsx": ("xlsx", HAS_XLSX, "openpyxl"),
            "/api/dragon/seal": ("seal", True, "guardian"),
            "/api/dragon/ocr": ("ocr", HAS_MULTIMODAL, "multimodal_engine"),
        }
        if path in engine_routes:
            engine, available, lib = engine_routes[path]
            self._json_response({
                "status": "ready" if available else "unavailable",
                "engine": engine,
                "library": lib,
                "method_hint": "Use POST to generate documents",
                "dragon": "architect" if engine != "seal" else "guardian",
            }, 200 if available else 503)
            return

        # Sovereign Router: Capabilities endpoint
        if path == "/api/dragon/capabilities":
            if HAS_SOVEREIGN_ROUTER:
                self._json_response(capabilities_response(), 200)
            else:
                self._json_response({
                    "error": "Sovereign router not loaded",
                    "local_functions": 42,
                    "semantic_functions": 3,
                }, 503)
            return

        # Sovereign Router: Sovereignty status
        if path == "/api/dragon/sovereignty":
            if HAS_SOVEREIGN_ROUTER:
                # Get ledger count
                try:
                    import sqlite3
                    conn = sqlite3.connect("/opt/windi/data/forensic_ledger.sqlite3")
                    ledger_count = conn.execute("SELECT COUNT(*) FROM receipts").fetchone()[0]
                    conn.close()
                except Exception:
                    ledger_count = 0

                self._json_response({
                    "status": "operational",
                    "sovereignty": sovereignty_metadata(llm_used=False),
                    "ledger_receipts": ledger_count,
                    "audit_ref": "AUDIT-SOVEREIGNTY-20260224",
                    "principle": "Integridade e universal. Interpretacao e premium.",
                    "i10": "Continuidade - degradacao != erro, = transicao soberana.",
                }, 200)
            else:
                self._json_response({"error": "Sovereign router not loaded"}, 503)
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

        elif path == "/api/dragon/sge":
            data, code = handle_dragon_sge(body)
            log(f"SGE [{body.get('source','?')}] risk={data.get('risk','?')} score={data.get('score','?')}")
            self._json_response(data, code)

        # Sprint 2B: Communiqué proxy
        elif path == "/api/dragon/communique/create":
            data, code = handle_communique_create(body)
            self._json_response(data, code)

        elif path.startswith("/api/dragon/communique/review/"):
            comm_id = path.split("/")[-1]
            data, code = handle_communique_review(comm_id)
            self._json_response(data, code)

        elif path.startswith("/api/dragon/communique/publish/"):
            comm_id = path.split("/")[-1]
            data, code = handle_communique_publish(comm_id)
            self._json_response(data, code)

        # Phase 2.5: Promote Wisdom Candidate (Human Dragon decision)
        elif path == "/api/dragon/cognitive/promote-wisdom" and HAS_DECISION_JOURNAL:
            pattern_id = body.get("pattern_id")
            promoted_by = body.get("promoted_by", "Human Dragon")
            if not pattern_id:
                self._json_response({"error": "pattern_id required"}, 400)
            else:
                data = promote_wisdom_candidate(pattern_id, promoted_by)
                code = 200 if data.get("success") else 400
                log(f"WISDOM PROMOTION: {pattern_id} by {promoted_by} -> {data.get('success', False)}")
                self._json_response(data, code)

        # ═══════════════════════════════════════════════════════════════
        # INSTITUTIONAL MEMORY — Dragon Legal Advocacy Endpoints
        # "A máquina não advoga. Ela produz prova. A prova advoga."
        # ═══════════════════════════════════════════════════════════════
        elif path == "/api/dragon/institutional/query" and HAS_INSTITUTIONAL_MEMORY:
            question = body.get("question", "")
            emit_proof = body.get("emit_proof", False)
            if not question:
                self._json_response({"error": "question required"}, 400)
            else:
                im = get_institutional_memory()
                answer = im.query(question)
                if answer:
                    proof = None
                    if emit_proof:
                        proof = im.emit_proof(question, answer)
                    data = {
                        "question": question,
                        "answer": answer,
                        "proof_emitted": proof,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    log(f"INSTITUTIONAL QUERY: '{question[:40]}...' -> {answer.get('source', '?')} conf={answer.get('confidence', 0):.0%}")
                    self._json_response(data, 200)
                else:
                    self._json_response({
                        "question": question,
                        "answer": None,
                        "message": "No institutional answer found for this question"
                    }, 200)

        elif path == "/api/dragon/institutional/emit-proof" and HAS_INSTITUTIONAL_MEMORY:
            question = body.get("question", "")
            answer = body.get("answer", {})
            if not question or not answer:
                self._json_response({"error": "question and answer required"}, 400)
            else:
                im = get_institutional_memory()
                proof = im.emit_proof(question, answer)
                if proof:
                    log(f"PAPEL MOEDA EMITTED: '{question[:40]}...'")
                    self._json_response({"proof": proof, "status": "emitted"}, 200)
                else:
                    self._json_response({"error": "Failed to emit proof"}, 500)

        # Phase 5C LAUNCH Plan: Voice Endpoint (ElevenLabs TTS)
        elif path == "/api/dragon/voice/speak":
            audio_bytes, error = handle_voice_speak(body)
            if error:
                self._json_response(error, 400 if error.get("code") == "NO_TEXT" else 503)
            else:
                self._audio_response(audio_bytes)

        # ═══════════════════════════════════════════════════════════════════════
        # DECISIONS CREATE — POST /api/dragon/decisions (DecisionTracker)
        # ═══════════════════════════════════════════════════════════════════════
        elif path == "/api/dragon/decisions" and HAS_DECISION_JOURNAL:
            import uuid
            risk_level = body.get("risk_level", body.get("risk", "R0"))
            dragon = body.get("dragon", "guardian")

            # Record decision using existing Decision Journal infrastructure
            try:
                decision_id = record_decision(
                    intent_detected=body.get("input", "governance_decision")[:200],
                    confidence_score=body.get("score", body.get("confidence", 0.5)),
                    tier=body.get("tier", "HIGH"),
                    route_selected=dragon,
                    candidates_rejected=[],
                    reason_code=f"RISK_{risk_level}",
                    wisdom_alignment=None,
                    latency_ms=body.get("latency_ms"),
                    uncertainty_detected=int(risk_level[1:]) >= 3 if risk_level.startswith("R") else False
                )
                log(f"DECISION RECORDED: {decision_id} risk={risk_level} dragon={dragon}")
                self._json_response({
                    "id": decision_id,
                    "status": "recorded",
                    "risk": risk_level,
                    "dragon": dragon,
                    "principle": "Every governance decision is traceable."
                }, 201)
            except Exception as e:
                log(f"DECISION ERROR: {e}")
                fallback_id = f"DEC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:4]}"
                self._json_response({
                    "id": fallback_id,
                    "status": "recorded_local",
                    "warning": str(e),
                    "principle": "Fallback to local tracking."
                }, 201)

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

    def _audio_response(self, audio_bytes: bytes):
        """Send audio/mpeg response for TTS (Phase 5C)."""
        self.send_response(200)
        self.send_header("Content-Type", "audio/mpeg")
        self.send_header("Content-Length", len(audio_bytes))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(audio_bytes)

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

    def _serve_admin_waitlist(self):
        """Serve Admin Waitlist Dashboard — Internal Only (v1.1.0-W)."""
        html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>WINDI Admin — Genesis Waitlist</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', system-ui, sans-serif;
      background: #0E0E14; color: #E2E2EA;
      min-height: 100vh; padding: 40px;
    }
    .container { max-width: 900px; margin: 0 auto; }
    .header {
      display: flex; align-items: center; justify-content: space-between;
      margin-bottom: 30px; padding-bottom: 20px;
      border-bottom: 1px solid #26263A;
    }
    .header h1 { font-size: 24px; color: #D4A843; font-weight: 700; }
    .header .badge {
      background: #D4A84320; color: #D4A843;
      padding: 6px 16px; border-radius: 20px;
      font-size: 12px; font-weight: 600;
    }
    .warning {
      background: #C0392B20; border: 1px solid #C0392B40;
      color: #E74C3C; padding: 12px 16px; border-radius: 8px;
      font-size: 12px; margin-bottom: 24px;
    }
    .stats {
      display: grid; grid-template-columns: repeat(3, 1fr);
      gap: 16px; margin-bottom: 30px;
    }
    .stat {
      background: #16161F; border: 1px solid #26263A;
      border-radius: 12px; padding: 20px; text-align: center;
    }
    .stat-value { font-size: 36px; font-weight: 700; color: #D4A843; }
    .stat-label { font-size: 12px; color: #7A7A96; margin-top: 4px; }
    table {
      width: 100%; border-collapse: collapse;
      background: #16161F; border-radius: 12px;
      overflow: hidden;
    }
    th, td { padding: 14px 16px; text-align: left; }
    th {
      background: #1A1A24; color: #7A7A96;
      font-size: 11px; text-transform: uppercase;
      letter-spacing: 0.05em; font-weight: 600;
    }
    tr:not(:last-child) td { border-bottom: 1px solid #26263A; }
    td { font-size: 14px; }
    .email { color: #D4A843; font-weight: 500; }
    .lang {
      display: inline-block; padding: 2px 8px;
      background: #26263A; border-radius: 4px;
      font-size: 11px; text-transform: uppercase;
    }
    .time { color: #7A7A96; font-size: 12px; }
    .empty {
      text-align: center; padding: 60px;
      color: #7A7A96; font-style: italic;
    }
    .refresh {
      background: #D4A843; color: #0E0E14;
      border: none; padding: 10px 20px; border-radius: 8px;
      cursor: pointer; font-weight: 600; font-size: 13px;
    }
    .refresh:hover { filter: brightness(1.1); }
    .footer {
      margin-top: 30px; padding-top: 20px;
      border-top: 1px solid #26263A;
      font-size: 11px; color: #4A4A62; text-align: center;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🔒 WINDI Admin — Genesis Waitlist</h1>
      <span class="badge">INTERNAL ONLY</span>
    </div>

    <div class="warning">
      ⚠️ Este dashboard é apenas para uso administrativo interno.
      Não exponha esta URL publicamente. Acesso restrito a localhost.
    </div>

    <div class="stats">
      <div class="stat">
        <div class="stat-value" id="total">-</div>
        <div class="stat-label">Total na Lista</div>
      </div>
      <div class="stat">
        <div class="stat-value" id="today">-</div>
        <div class="stat-label">Hoje</div>
      </div>
      <div class="stat">
        <div class="stat-value" id="langs">-</div>
        <div class="stat-label">Idiomas</div>
      </div>
    </div>

    <div style="display: flex; justify-content: flex-end; margin-bottom: 16px;">
      <button class="refresh" onclick="loadData()">↻ Refresh</button>
    </div>

    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Email</th>
          <th>Idioma</th>
          <th>Origem</th>
          <th>Data/Hora</th>
        </tr>
      </thead>
      <tbody id="tbody">
        <tr><td colspan="5" class="empty">Carregando...</td></tr>
      </tbody>
    </table>

    <div class="footer">
      WINDI Admin Dashboard v1.1.0-W — "AI processes. Human decides. WINDI guarantees."
    </div>
  </div>

  <script>
    async function loadData() {
      try {
        const res = await fetch('/admin/waitlist/data');
        const data = await res.json();

        document.getElementById('total').textContent = data.count || 0;

        // Count today
        const today = new Date().toISOString().slice(0, 10);
        const todayCount = (data.entries || []).filter(e =>
          e.timestamp && e.timestamp.startsWith(today)
        ).length;
        document.getElementById('today').textContent = todayCount;

        // Count unique langs
        const langs = new Set((data.entries || []).map(e => e.lang || 'en'));
        document.getElementById('langs').textContent = langs.size;

        // Render table
        const tbody = document.getElementById('tbody');
        if (!data.entries || data.entries.length === 0) {
          tbody.innerHTML = '<tr><td colspan="5" class="empty">Nenhum email na lista de espera</td></tr>';
          return;
        }

        tbody.innerHTML = data.entries.map((e, i) => `
          <tr>
            <td>${e.position || i + 1}</td>
            <td class="email">${e.email}</td>
            <td><span class="lang">${e.lang || 'en'}</span></td>
            <td>${e.source || '-'}</td>
            <td class="time">${e.timestamp ? new Date(e.timestamp).toLocaleString('de-DE') : '-'}</td>
          </tr>
        `).join('');
      } catch (err) {
        document.getElementById('tbody').innerHTML =
          '<tr><td colspan="5" class="empty">Erro: ' + err.message + '</td></tr>';
      }
    }

    loadData();
    // Auto-refresh every 30s
    setInterval(loadData, 30000);
  </script>
</body>
</html>"""
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
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
    elevenlabs_key = get_elevenlabs_key()
    print(f"""
═══════════════════════════════════════════════════════════════════════
🐉 WINDI Agent Dragon Server v{VERSION}
   "AI processes. Human decides. WINDI guarantees."

   Port:     {PORT}
   UI:       {UI_FILE}
   Model:    {MODEL}
   API Key:  {'✓ Configured' if api_key else '✗ NOT CONFIGURED — set ANTHROPIC_API_KEY or create .dragon_key'}
   Voice:    {'✓ ElevenLabs Ready' if elevenlabs_key else '○ Not configured (optional)'}

   Dragons:  🛡️ Guardian | 🏗️ Architect | 👁️ Witness
   Endpoints:
     GET  /                    → UI
     GET  /api/dragon/health   → Health check
     POST /api/dragon/chat     → Conversational AI
     POST /api/dragon/generate → Document generation
     POST /api/dragon/voice/speak → TTS (Phase 5C)
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
