"""
maria_brain.py — O Cérebro da MARIA (P4 Unified)
═══════════════════════════════════════════════════════════════════════════════
§92 — Arquitectura Limpa: LLM live substitui regex estáticos
§72 — Pulse Reading: Cérebro ouve a Alma antes de responder

"Os regex tentam prever o que o humano vai dizer.
 O LLM entende o que o humano quis dizer."

P4 — Regra Canónica:
  "Nenhuma resposta pode sair do cérebro sem passar pela alma."

Author: Liga IA+H · Kempten 2026
═══════════════════════════════════════════════════════════════════════════════
"""

import logging
import os
import sys
from typing import Dict, Any
from datetime import datetime
from pathlib import Path

log = logging.getLogger("w-maria-brain")

# ── Load .env (WINDI keys) ───────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    env_path = Path("/opt/windi/.env")
    if env_path.exists():
        load_dotenv(env_path)
        log.info("[MARIA Brain] Loaded keys from /opt/windi/.env")
except ImportError:
    log.warning("[MARIA Brain] python-dotenv not available")

# ── P4: Import the Soul ──────────────────────────────────────────────────────
# A Alma vive em /opt/windi/windi-travel/maria_voice.py
sys.path.insert(0, "/opt/windi/windi-travel")
try:
    from maria_voice import read_pulse, select_provider, get_system_prompt
    SOUL_AVAILABLE = True
    log.info("[MARIA Brain] §72 Soul connected: read_pulse, select_provider, get_system_prompt")
except ImportError as e:
    SOUL_AVAILABLE = False
    log.error(f"[MARIA Brain] §72 Soul NOT available: {e}")

# ── P5: Import the Memory ─────────────────────────────────────────────────────
# A Memória vive em /opt/windi/windi-travel/maria/nomada_profile.py
try:
    from maria.nomada_profile import (
        enrich_context_with_memory,
        get_visible_memory,
        get_travel_preferences,
        log_interaction
    )
    MEMORY_AVAILABLE = True
    log.info("[MARIA Brain] P5 Memory connected: enrich_context_with_memory, get_visible_memory")
except ImportError as e:
    MEMORY_AVAILABLE = False
    log.warning(f"[MARIA Brain] P5 Memory NOT available: {e}")

# ── LLM Providers ────────────────────────────────────────────────────────────

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MISTRAL_KEY = os.environ.get("MISTRAL_API_KEY", "")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")

log.info(f"[MARIA Brain] Keys: Anthropic={'yes' if ANTHROPIC_KEY else 'no'}, "
         f"Mistral={'yes' if MISTRAL_KEY else 'no'}, Gemini={'yes' if GEMINI_KEY else 'no'}")

# ══════════════════════════════════════════════════════════════════════════════
# P4 — UNIFIED BRAIN: Cérebro que ouve a Alma
# ══════════════════════════════════════════════════════════════════════════════

async def think(
    user_input: str,
    lang: str = "PT",
    did: str = None,
    weather: str = None,
    location: str = None,
    session_count: int = 0,
    memory: str = "",
    tier: str = "FREE",
    context: dict = None,
    history: list = None
) -> Dict[str, Any]:
    """
    O cérebro da Maria pensa — agora através da Alma.

    P4 Pipeline:
      1. read_pulse()       → Detecta subtexto emocional
      2. select_provider()  → Escolhe o motor certo (Gemini/Claude/GPT)
      3. get_system_prompt() → 9 personalidades (provider × língua)
      4. Call LLM           → Com o prompt e provider certos
      5. Return             → response + pulse + provider

    Returns:
        {
            "response": str,
            "provider": str,      # "gemini" | "anthropic" | "openai" | "mistral" | "offline"
            "pulse": dict,        # §72 Pulse Reading result
            "intent": str,
            "confidence": float,
            "soul_active": bool   # P4 validation
        }
    """
    hour = datetime.now().hour
    context = context or {}

    # ─────────────────────────────────────────────────────────────────────────
    # P4 Step 1: PULSE READING — §72 Layer 0
    # ─────────────────────────────────────────────────────────────────────────
    if SOUL_AVAILABLE:
        pulse = read_pulse(user_input, hour)
        log.info(f"[MARIA §72] Pulse: energy={pulse.get('energy')}, "
                 f"intent={pulse.get('intent')}, tone={pulse.get('tone_needed')}")
    else:
        pulse = {"energy": "medium", "intent": "discover", "tone_needed": "enthusiastic"}
        log.warning("[MARIA Brain] Soul not available — using default pulse")

    # ─────────────────────────────────────────────────────────────────────────
    # P5 Step 1.5: MEMORY ENRICHMENT — Maria lembra quem tu és
    # ─────────────────────────────────────────────────────────────────────────
    memory_context = {}
    visible_memory = []
    if MEMORY_AVAILABLE and did:
        try:
            # Enrich context with nomada profile data
            memory_context = enrich_context_with_memory(did, context)

            # Get visible memory patterns
            prefs = get_travel_preferences(did)
            visible_memory = get_visible_memory(prefs, lang)

            log.info(f"[MARIA P5] Memory enriched for DID {did[:8]}...: "
                     f"patterns={len(visible_memory)}, "
                     f"confidence={memory_context.get('learned_confidence', 0):.2f}")
        except Exception as e:
            log.warning(f"[MARIA P5] Memory enrichment failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # P4 Step 2: SELECT PROVIDER — Alma decide qual motor usar
    # ─────────────────────────────────────────────────────────────────────────
    if SOUL_AVAILABLE:
        # Enrich context for select_provider
        ctx = {
            "mood": pulse.get("tone_needed", ""),
            "hour": hour,
            "weather": weather,
            **context
        }
        provider = select_provider({}, ctx, pulse)
        log.info(f"[MARIA §72] Soul selected provider: {provider}")
    else:
        provider = "anthropic"  # fallback to Claude

    # ─────────────────────────────────────────────────────────────────────────
    # P4 Step 3: GET SYSTEM PROMPT — Uma das 9 personalidades
    # ─────────────────────────────────────────────────────────────────────────
    if SOUL_AVAILABLE:
        system = get_system_prompt(provider, lang, pulse)
        log.debug(f"[MARIA §72] System prompt length: {len(system)} chars")
    else:
        # Fallback básico se alma não disponível
        system = _fallback_system_prompt(lang)

    # Enrich system prompt with context (location, weather, memory)
    system = _enrich_system_prompt(system, lang, location, weather, session_count, memory, hour)

    # ─────────────────────────────────────────────────────────────────────────
    # P4 Step 4: CALL LLM — Com o provider e prompt certos
    # ─────────────────────────────────────────────────────────────────────────
    result = await _call_provider(provider, system, user_input, lang, history=history or [])

    # ─────────────────────────────────────────────────────────────────────────
    # P5 Step 4.5: LOG INTERACTION — Maria aprende com cada conversa
    # ─────────────────────────────────────────────────────────────────────────
    if MEMORY_AVAILABLE and did and result.get("response"):
        try:
            import uuid
            log_interaction(
                did=did,
                request_id=str(uuid.uuid4())[:8],
                intent_type=pulse.get("intent", "general"),
                place_name=location or "",
                rating=None,
                feedback=None
            )
            log.debug(f"[MARIA P5] Interaction logged for DID {did[:8]}...")
        except Exception as e:
            log.warning(f"[MARIA P5] Failed to log interaction: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # P4+P5 Step 5: RETURN — Resposta com alma + memória
    # ─────────────────────────────────────────────────────────────────────────
    return {
        "response": result["response"],
        "provider": result["provider"],
        "pulse": pulse,
        "intent": pulse.get("intent", "discover"),
        "confidence": result.get("confidence", 0.9),
        "soul_active": SOUL_AVAILABLE,
        # P5: Memory enrichment
        "memory_active": MEMORY_AVAILABLE and did is not None,
        "visible_memory": visible_memory,
        "learned_confidence": memory_context.get("learned_confidence", 0.0)
    }


# ══════════════════════════════════════════════════════════════════════════════
# LLM PROVIDERS
# ══════════════════════════════════════════════════════════════════════════════

async def _call_provider(provider: str, system: str, user_input: str, lang: str, history: list = None) -> Dict[str, Any]:
    """Route to the correct LLM based on provider selection."""
    history = history or []

    # Anthropic (Claude) — emoção, presença
    if provider == "anthropic" and ANTHROPIC_KEY:
        result = await _call_claude(system, user_input, lang, history)
        if result["provider"] != "offline":
            return result

    # Google (Gemini) — lugares, geografia
    if provider == "gemini" and GEMINI_KEY:
        result = await _call_gemini(system, user_input, lang)
        if result["provider"] != "offline":
            return result

    # OpenAI (GPT) — visão (fallback to Claude for now)
    if provider == "openai" and ANTHROPIC_KEY:
        # TODO: Implement GPT-4V when needed
        result = await _call_claude(system, user_input, lang, history)
        if result["provider"] != "offline":
            return result

    # Fallback chain: Claude → Mistral → Offline
    if ANTHROPIC_KEY:
        result = await _call_claude(system, user_input, lang, history)
        if result["provider"] != "offline":
            return result

    if MISTRAL_KEY:
        result = await _call_mistral(system, user_input, lang, history)
        if result["provider"] != "offline":
            return result

    return _offline_response(lang)


async def _call_claude(system: str, user_input: str, lang: str, history: list = None) -> Dict[str, Any]:
    """Pensar com Claude (Anthropic) — presença humana, emoção."""
    history = history or []
    try:
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 500,  # §145.2 — increased from 250 to prevent truncation
                    "temperature": 0.3,
                    "system": system,
                    "messages": [*history, {"role": "user", "content": user_input}]
                }
            )

            if response.status_code == 200:
                data = response.json()
                text = data.get("content", [{}])[0].get("text", "")
                return {
                    "response": text,
                    "provider": "anthropic",
                    "confidence": 0.95
                }
            else:
                log.error(f"[MARIA Brain] Claude HTTP {response.status_code}")
    except Exception as e:
        log.error(f"[MARIA Brain] Claude error: {e}")

    return {"response": "", "provider": "offline", "confidence": 0.0}


async def _call_gemini(system: str, user_input: str, lang: str) -> Dict[str, Any]:
    """Pensar com Gemini (Google) — lugares, geografia, cultura."""
    try:
        import httpx

        # Gemini uses a different API structure
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{
                        "parts": [{"text": f"{system}\n\nUser: {user_input}"}]
                    }],
                    "generationConfig": {
                        "maxOutputTokens": 500,  # §145.2 — increased from 250 to prevent truncation
                        "temperature": 0.4
                    }
                }
            )

            if response.status_code == 200:
                data = response.json()
                text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return {
                    "response": text,
                    "provider": "gemini",
                    "confidence": 0.92
                }
            else:
                log.error(f"[MARIA Brain] Gemini HTTP {response.status_code}")
    except Exception as e:
        log.error(f"[MARIA Brain] Gemini error: {e}")

    return {"response": "", "provider": "offline", "confidence": 0.0}


async def _call_mistral(system: str, user_input: str, lang: str, history: list = None) -> Dict[str, Any]:
    """Pensar com Mistral — soberania local, fallback."""
    history = history or []
    try:
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {MISTRAL_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mistral-small-latest",
                    "messages": [
                        {"role": "system", "content": system},
                        *history,
                        {"role": "user", "content": user_input}
                    ],
                    "max_tokens": 500,  # §145.2 — increased from 300 to prevent truncation
                    "temperature": 0.7
                }
            )

            if response.status_code == 200:
                data = response.json()
                text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {
                    "response": text,
                    "provider": "mistral",
                    "confidence": 0.90
                }
    except Exception as e:
        log.error(f"[MARIA Brain] Mistral error: {e}")

    return {"response": "", "provider": "offline", "confidence": 0.0}


def _offline_response(lang: str) -> Dict[str, Any]:
    """Honestidade constitucional: se não há LLM, Maria admite."""
    responses = {
        "PT": "Estou offline neste momento. Tenta novamente em breve.",
        "DE": "Ich bin gerade offline. Versuche es bald noch einmal.",
        "EN": "I am offline at the moment. Please try again soon."
    }

    return {
        "response": responses.get(lang, responses["EN"]),
        "provider": "offline",
        "confidence": 0.0
    }


# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _enrich_system_prompt(system: str, lang: str, location: str, weather: str,
                          session_count: int, memory: str, hour: int) -> str:
    """Add context to system prompt without overwriting Soul's personality."""
    # I12 — Language Sovereign Principle: context labels in target language
    labels = {
        "PT": {
            "session": "Contexto da sessão",
            "hour": "Hora",
            "weather": "Clima",
            "sessions": "Sessões",
            "memory": "Memória",
            "location_known": "Localização: {loc}. Menciona distâncias reais.",
            "location_unknown": "Localização desconhecida. Pede cidade naturalmente.",
            "unknown": "desconhecido",
            "first": "primeira conversa",
            "morning": "manhã", "afternoon": "tarde", "night": "noite",
            "lang_instruction": "RESPONDE SEMPRE EM PORTUGUÊS."
        },
        "DE": {
            "session": "Sitzungskontext",
            "hour": "Uhrzeit",
            "weather": "Wetter",
            "sessions": "Sitzungen",
            "memory": "Erinnerung",
            "location_known": "Standort: {loc}. Nenne echte Entfernungen.",
            "location_unknown": "Standort unbekannt. Frage natürlich nach der Stadt.",
            "unknown": "unbekannt",
            "first": "erstes Gespräch",
            "morning": "Morgen", "afternoon": "Nachmittag", "night": "Nacht",
            "lang_instruction": "ANTWORTE IMMER AUF DEUTSCH."
        },
        "EN": {
            "session": "Session context",
            "hour": "Time",
            "weather": "Weather",
            "sessions": "Sessions",
            "memory": "Memory",
            "location_known": "Location: {loc}. Mention real distances.",
            "location_unknown": "Location unknown. Ask for city naturally.",
            "unknown": "unknown",
            "first": "first conversation",
            "morning": "morning", "afternoon": "afternoon", "night": "night",
            "lang_instruction": "ALWAYS RESPOND IN ENGLISH."
        }
    }
    L = labels.get(lang.upper()[:2], labels["EN"])

    # Time of day
    period = L["morning"] if 5 <= hour < 12 else L["afternoon"] if 12 <= hour < 18 else L["night"]
    hour_str = f"{hour}:00 ({period})"

    # §93 — Location context
    if location and location not in ("não especificada", "unspecified", "nicht angegeben"):
        location_context = L["location_known"].format(loc=location)
    else:
        location_context = L["location_unknown"]

    context_block = f"""

[{L["session"]}]
- {L["hour"]}: {hour_str}
- {L["weather"]}: {weather or L["unknown"]}
- {L["sessions"]}: {session_count}
- {L["memory"]}: {memory or L["first"]}
- {location_context}

{L["lang_instruction"]}
"""

    return system + context_block


def _fallback_system_prompt(lang: str) -> str:
    """Fallback system prompt if Soul not available."""
    fallbacks = {
        "PT": "Sou a MARIA, companheira de viagem WINDI. Máximo 3 frases. Decisão, não lista.",
        "DE": "Ich bin MARIA, WINDI Reisebegleiterin. Maximal 3 Sätze. Entscheidung, keine Liste.",
        "EN": "I am MARIA, WINDI travel companion. Maximum 3 sentences. Decision, not list."
    }
    return fallbacks.get(lang, fallbacks["EN"])


# ══════════════════════════════════════════════════════════════════════════════
# INTENT DETECTION (kept for compatibility)
# ══════════════════════════════════════════════════════════════════════════════

INTENT_DETECTION_PROMPT = """
Analisa esta mensagem e classifica o intent. Responde APENAS com uma palavra:
- greeting (saudação: olá, bom dia, etc.)
- onboarding (pergunta sobre ti: quem és, o que fazes, etc.)
- navigation (quer ir a algum lugar: farmácia, café, etc.)
- flight (quer voar: voo, avião, bilhete)
- hotel (quer alojamento: hotel, quarto, dormir)
- general (conversa geral)

Mensagem: "{input}"

Intent:
"""

async def detect_intent(user_input: str, lang: str = "PT") -> str:
    """Detecta intent via LLM."""
    prompt = INTENT_DETECTION_PROMPT.format(input=user_input)

    try:
        if MISTRAL_KEY:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://api.mistral.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {MISTRAL_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "mistral-small-latest",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 10,
                        "temperature": 0.1
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    intent = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip().lower()
                    if intent in ["greeting", "onboarding", "navigation", "flight", "hotel", "general"]:
                        return intent
    except Exception as e:
        log.warning(f"[MARIA Brain] Intent detection failed: {e}")

    return "general"
