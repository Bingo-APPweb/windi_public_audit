"""
W-MARIA-001 · Booking Router
────────────────────────────
Endpoint: POST /maria/plan
Endpoint: GET  /maria/health (override)

Pipeline:
  Intent JSON → Context Enricher (Open-Meteo) → Google Places → Decision Engine → Ledger Seal

Invariants enforced:
  I1  — PII never logged
  I10 — Graceful fallback if external API fails (sovereign mode)
  I11 — Every decision sealed in Forensic Ledger

Deploy:
  /opt/windi/windi-travel/booking_router.py
  systemd: windi-travel.service  (port :8126)

Author: Liga IA+H · Kempten 2026
"AI processes. Human decides. WINDI guarantees."
"""

import os, time, uuid, hashlib, json, logging, re
from datetime import datetime, timezone, timedelta

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List

# ── Logging (no PII — I1) ─────────────────────────────────────────────────────
log = logging.getLogger("w-maria-001-booking")

# ── MARIA Voice (Triple LLM + §72 Pulse Reading) ─────────────────────────────
from maria_voice import select_provider, get_system_prompt, read_pulse, MARIA_PROMPTS

# ── MARIA Memory (DID Profiles) ───────────────────────────────────────────────
try:
    from maria.nomada_profile import (
        get_or_create_nomada,
        enrich_context_with_memory,
        log_interaction,
        set_preference,
        gerar_saudacao,
        get_total_interactions,
        # §98 — MODO NÓMADA v1.1
        get_travel_preferences,
        learn_from_choice,
        explain_personalized_decision,
        # §100 — ANTECIPAÇÃO
        detect_travel_patterns,
        should_anticipate,
        generate_anticipation_message,
        log_anticipation,
        # §100.5 — MEMORY ENGINE
        save_decision,
        get_decisions,
        mark_decision_feedback,
        detect_patterns_from_decisions,
        get_enhanced_travel_preferences,
        get_decision_stats,
        # §108 — MEMÓRIA VISÍVEL
        get_visible_memory,
        should_show_memory,
        # §107 — THREAD VISUAL TIMELINE
        create_thread,
        get_active_thread,
        add_thread_entry,
        get_thread_timeline,
        get_user_threads,
        get_thread_with_timeline,
        close_thread,
    )
    MEMORY_ENABLED = True
    ANTICIPATION_ENABLED = True
    MEMORY_ENGINE_ENABLED = True
    THREAD_ENABLED = True
except ImportError:
    MEMORY_ENABLED = False
    ANTICIPATION_ENABLED = False
    MEMORY_ENGINE_ENABLED = False
    THREAD_ENABLED = False
    def gerar_saudacao(did, lang, weather=None, hour=None): return {"PT": "Bom dia, viajante", "DE": "Guten Tag, Reisender", "EN": "Good day, traveller"}.get(lang, "Good day")
    def get_total_interactions(did): return 0
    def get_travel_preferences(did): return {"avoid_stops": True, "price_sensitivity": 0.5, "prefer_morning": True, "comfort_priority": 0.5}
    def get_enhanced_travel_preferences(did): return get_travel_preferences(did)
    def explain_personalized_decision(choice_type, prefs, lang): return ""
    def detect_travel_patterns(did): return {}
    def should_anticipate(did, context, patterns): return {"should_suggest": False}
    def save_decision(*args, **kwargs): return None
    def mark_decision_feedback(*args, **kwargs): pass
    def get_decision_stats(did): return {}
    def get_visible_memory(prefs, lang="PT"): return []
    def should_show_memory(prefs, session_shown=False): return False
    # §107 fallbacks
    def create_thread(*args, **kwargs): return None
    def get_active_thread(*args, **kwargs): return None
    def add_thread_entry(*args, **kwargs): return None
    def get_thread_timeline(*args, **kwargs): return []
    def get_user_threads(*args, **kwargs): return []
    def get_thread_with_timeline(*args, **kwargs): return None
    def close_thread(*args, **kwargs): pass
    log.warning("[MARIA] Memory module not available — running without DID persistence")

# ── Places Sovereignty Gate ───────────────────────────────────────────────────
try:
    # Add parent directory to path for import
    import sys
    _travel_path = "/opt/windi/windi-travel"
    if _travel_path not in sys.path:
        sys.path.insert(0, _travel_path)
    from places_gate import search_places_sovereign, get_cache_stats
    PLACES_GATE_ENABLED = True
    log.info("[MARIA] Places Sovereignty Gate loaded ✓")
except ImportError as e:
    PLACES_GATE_ENABLED = False
    log.warning(f"[MARIA] Places Gate not available: {e}")

# ── MARIA Voice Engine (§81) ─────────────────────────────────────────────────
try:
    from maria.maria_voice import generate_speech, get_voice_profile, EDGE_TTS_AVAILABLE
    VOICE_ENGINE_ENABLED = EDGE_TTS_AVAILABLE
    log.info(f"[MARIA] Voice Engine loaded ✓ (Edge TTS: {EDGE_TTS_AVAILABLE})")
except ImportError as e:
    VOICE_ENGINE_ENABLED = False
    log.warning(f"[MARIA] Voice Engine not available: {e}")

# ── MARIA Brain (§92) ── LLM live substitui regex estáticos ──────────────────
try:
    from maria.maria_brain import think as maria_think, detect_intent as maria_detect_intent
    BRAIN_ENABLED = True
    log.info("[MARIA] Brain (LLM) loaded ✓ — regex substituídos por consciência")
except ImportError as e:
    BRAIN_ENABLED = False
    log.warning(f"[MARIA] Brain not available: {e}")

# ── Kiwi Flight Bridge (§67) ─────────────────────────────────────────────────
try:
    from maria.kiwi_bridge import (
        search_flights,
        format_maria_response as format_flight_response,
        detect_flight_intent,
        extract_flight_details,
        get_user_location,  # §102 WhereAmI
    )
    KIWI_BRIDGE_ENABLED = True
    WHEREAMI_ENABLED = True
    log.info("[MARIA] Kiwi Flight Bridge loaded ✓")
except ImportError as e:
    KIWI_BRIDGE_ENABLED = False
    WHEREAMI_ENABLED = False
    log.warning(f"[MARIA] Kiwi Bridge not available: {e}")

# ── Hotel Bridge (§68) ───────────────────────────────────────────────────────
try:
    from maria.hotel_bridge import (
        search_hotels,
        format_maria_hotel_response,
        detect_hotel_intent,
        extract_hotel_details,
    )
    HOTEL_BRIDGE_ENABLED = True
    log.info("[MARIA] Hotel Bridge loaded ✓")
except ImportError as e:
    HOTEL_BRIDGE_ENABLED = False
    log.warning(f"[MARIA] Hotel Bridge not available: {e}")

# ── §103 Deutsche Bahn Bridge (Intermodal Intelligence) ──────────────────────
try:
    from maria.db_bridge import (
        search_trains,
        should_include_trains,
        estimate_distance,
    )
    DB_BRIDGE_ENABLED = True
    log.info("[MARIA] Deutsche Bahn Bridge loaded ✓")
except ImportError as e:
    DB_BRIDGE_ENABLED = False
    async def search_trains(*args, **kwargs): return {"trains": []}
    def should_include_trains(*args, **kwargs): return False
    def estimate_distance(*args, **kwargs): return 9999
    log.warning(f"[MARIA] DB Bridge not available: {e}")

# ── §69 Culture/Tips Intent Detection ─────────────────────────────────────────
# §145.3 — Weather terms REMOVED to prevent conflict with §145.2 weather detection
#          Weather queries are now handled FIRST at line ~2114
CULTURE_KEYWORDS = {
    "pt": [
        "moeda", "língua", "idioma", "costume", "horário", "horarios",
        "seguro", "segurança", "perigoso",
        # §145.3: "tempo", "clima", "temperatura" → moved to WEATHER_KEYWORDS
        "como chegar", "transporte", "metro", "autocarro", "táxi", "uber",
        "dica", "dicas", "conselho", "recomenda", "gorjeta", "propina",
        "tomada", "voltagem", "adaptador", "wifi", "internet", "roaming",
        "visto", "passaporte", "vacina", "agua", "beber", "comer",
        "quanto custa", "preço", "barato", "caro", "trocar dinheiro",
    ],
    "de": [
        "währung", "geld", "sprache", "öffnungszeiten", "sicher", "sicherheit",
        "gefährlich",
        # §145.3: "wetter", "klima", "temperatur" → moved to WEATHER_KEYWORDS
        "wie komme ich",
        "transport", "u-bahn", "bus", "taxi", "tipp", "tipps", "empfehlung",
        "trinkgeld", "steckdose", "spannung", "adapter", "wlan", "internet",
        "visum", "reisepass", "impfung", "wasser", "trinken", "essen",
        "wie viel kostet", "preis", "billig", "teuer", "geld wechseln",
    ],
    "en": [
        "currency", "money", "language", "customs", "hours", "opening",
        "safe", "safety", "dangerous",
        # §145.3: "weather", "climate", "temperature" → moved to WEATHER_KEYWORDS
        "how to get", "transport", "metro", "subway", "bus", "taxi", "uber",
        "tip", "tips", "advice", "recommend", "tipping", "gratuity",
        "plug", "voltage", "adapter", "wifi", "internet", "roaming",
        "visa", "passport", "vaccine", "water", "drink", "eat",
        "how much", "price", "cheap", "expensive", "exchange money",
    ],
}

def detect_culture_intent(text: str) -> bool:
    """Detect if user is asking cultural/practical travel questions."""
    lower = text.lower()
    for lang_keywords in CULTURE_KEYWORDS.values():
        if any(kw in lower for kw in lang_keywords):
            return True
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# §99 — CONTEXTO VIVO: Estado atual do humano
# "A decisão deixa de ser só tua. Passa a ser tua + o momento."
# ═══════════════════════════════════════════════════════════════════════════════

def get_live_context(user_input: str, lat: float = None, lng: float = None,
                     current_hour: int = None) -> dict:
    """
    §99 — Extract live context from the current moment.

    Pilares:
    1. TEMPO — urgência, horário atual
    2. LOCALIZAÇÃO — onde está
    3. ESTADO — modo (foco, exploração, urgente)
    """
    if current_hour is None:
        current_hour = datetime.now().hour

    context = {
        "time_pressure": "normal",
        "mode": "normal",
        "current_hour": current_hour,
        "has_location": bool(lat and lng),
    }

    # ─── Detectar pressão de tempo ───
    lower = user_input.lower()

    # Urgência explícita
    urgent_keywords = [
        "urgente", "rápido", "já", "agora", "hoje", "amanhã",
        "dringend", "schnell", "jetzt", "sofort", "heute", "morgen",
        "urgent", "quick", "now", "asap", "today", "tomorrow"
    ]
    if any(kw in lower for kw in urgent_keywords):
        context["time_pressure"] = "high"

    # Relaxado
    relaxed_keywords = [
        "quando der", "sem pressa", "qualquer dia", "flexível",
        "wenn es passt", "keine eile", "flexibel",
        "whenever", "no rush", "flexible", "any day"
    ]
    if any(kw in lower for kw in relaxed_keywords):
        context["time_pressure"] = "low"

    # ─── Detectar modo ───
    # Exploração (viagem de lazer, descoberta)
    explore_keywords = [
        "descobrir", "explorar", "conhecer", "passear", "turismo",
        "entdecken", "erkunden", "besichtigen", "tourismus",
        "discover", "explore", "visit", "sightseeing", "vacation"
    ]
    if any(kw in lower for kw in explore_keywords):
        context["mode"] = "explore"

    # Foco (trabalho, reunião, negócio)
    focus_keywords = [
        "trabalho", "reunião", "negócio", "conferência", "cliente",
        "arbeit", "meeting", "geschäft", "konferenz", "kunde",
        "work", "meeting", "business", "conference", "client"
    ]
    if any(kw in lower for kw in focus_keywords):
        context["mode"] = "focus"

    # Urgente (combinação de sinais)
    if context["time_pressure"] == "high" and context["mode"] == "focus":
        context["mode"] = "urgent"

    # ─── Contexto temporal ───
    if 5 <= current_hour < 9:
        context["time_of_day"] = "early_morning"
    elif 9 <= current_hour < 12:
        context["time_of_day"] = "morning"
    elif 12 <= current_hour < 17:
        context["time_of_day"] = "afternoon"
    elif 17 <= current_hour < 21:
        context["time_of_day"] = "evening"
    else:
        context["time_of_day"] = "night"

    return context


def apply_context_to_score(base_score: float, flight: dict, context: dict) -> float:
    """
    §99 — Adjust score based on live context.

    Contexto Vivo modifica a decisão em tempo real.
    """
    score = base_score

    # ─── Pressão de tempo ───
    if context.get("time_pressure") == "high":
        # Urgente: priorizar directo e rápido
        if flight.get("direct", False):
            score += 150
        else:
            score -= 100
        # Penalizar duração longa
        duration = flight.get("duration_min", 0)
        if duration > 300:  # > 5h
            score -= 80

    elif context.get("time_pressure") == "low":
        # Relaxado: preço importa mais
        price = flight.get("price", 100)
        if price < 80:
            score += 50

    # ─── Modo ───
    if context.get("mode") == "focus":
        # Trabalho: conforto e pontualidade
        if flight.get("airline") in ["TAP", "LH", "BA", "AF", "Swiss"]:
            score += 40  # Airlines premium
        if flight.get("direct", False):
            score += 60  # Sem surpresas

    elif context.get("mode") == "explore":
        # Exploração: aceitar escalas se mais barato
        if not flight.get("direct", False) and flight.get("price", 999) < 80:
            score += 30  # Escala OK se barato

    elif context.get("mode") == "urgent":
        # Urgente máximo: só o mais rápido
        if flight.get("direct", False):
            score += 200
        duration = flight.get("duration_min", 0)
        score -= duration * 0.3  # Penalizar cada minuto extra

    return score


def explain_context(context: dict, lang: str = "PT") -> str:
    """
    §99 — Generate context-aware explanation piece.

    Natural, curto, implícito.
    """
    pieces = []

    # Pressão de tempo
    if context.get("time_pressure") == "high":
        pieces.append({
            "PT": "tens pouco tempo",
            "DE": "du hast wenig Zeit",
            "EN": "you're short on time"
        })
    elif context.get("time_pressure") == "low":
        pieces.append({
            "PT": "estás sem pressa",
            "DE": "du hast keine Eile",
            "EN": "you're in no rush"
        })

    # Modo
    if context.get("mode") == "focus":
        pieces.append({
            "PT": "estás em modo trabalho",
            "DE": "du bist im Arbeitsmodus",
            "EN": "you're in work mode"
        })
    elif context.get("mode") == "explore":
        pieces.append({
            "PT": "estás a explorar",
            "DE": "du erkundest",
            "EN": "you're exploring"
        })
    elif context.get("mode") == "urgent":
        pieces.append({
            "PT": "é urgente",
            "DE": "es ist dringend",
            "EN": "it's urgent"
        })

    if not pieces:
        return ""

    # Juntar (máx 2 razões de contexto)
    selected = pieces[:2]
    reason_strs = [p.get(lang, p["EN"]) for p in selected]

    # Não repetir estrutura — variar
    templates = {
        "PT": [f"Como {reason_strs[0]}", f"Vejo que {reason_strs[0]}"],
        "DE": [f"Da {reason_strs[0]}", f"Ich sehe, dass {reason_strs[0]}"],
        "EN": [f"Since {reason_strs[0]}", f"I see {reason_strs[0]}"]
    }

    import random
    template = random.choice(templates.get(lang, templates["EN"]))

    if len(reason_strs) > 1:
        conj = {"PT": " e ", "DE": " und ", "EN": " and "}
        template += conj.get(lang, " and ") + reason_strs[1]

    return template + "."


# ═══════════════════════════════════════════════════════════════════════════════
# §97 — MODO NÓMADA v1: Decision Engine
# "O sistema não apresenta opções. Apresenta a melhor ação disponível."
# ═══════════════════════════════════════════════════════════════════════════════

def score_flight(f: dict, preferred_time: str = "morning", prefs: dict = None, context: dict = None) -> float:
    """
    §104 — Score a flight for Nómada decision-making (Personalização Real).

    Heurística v2.0 (evoluída):
    - Usa campos EVOLUÍVEIS do Memory Engine (direct_bonus, layover_penalty, etc.)
    - Personalização emerge do comportamento, não de settings
    - Contexto (urgência) influencia score
    """
    if prefs is None:
        prefs = {
            "avoid_stops": True, "price_sensitivity": 0.5, "prefer_morning": True,
            "comfort_priority": 0.5, "direct_bonus": 200, "layover_penalty": 100,
            "duration_weight": 0.5, "price_weight": 1.5, "morning_bonus": 50,
            "learned_confidence": 0.0
        }
    if context is None:
        context = {}

    score = 1000  # Base score

    # ─── PREÇO (campo evoluível: price_weight) ───
    price = f.get("price", 999)
    price_weight = prefs.get("price_weight", 1.5)
    score -= price * price_weight

    # ─── DURAÇÃO (campo evoluível: duration_weight) ───
    duration = f.get("duration_min", f.get("duration_minutes", 999))
    duration_weight = prefs.get("duration_weight", 0.5)
    score -= duration * duration_weight

    # ─── VOO DIRECTO (campos evoluíveis: direct_bonus, layover_penalty) ───
    if f.get("direct", False):
        # Usa bónus aprendido (pode variar de 100 a 300)
        direct_bonus = prefs.get("direct_bonus", 200)
        score += direct_bonus
    else:
        # Penaliza escalas (pode variar de 50 a 150)
        stops = f.get("stops", len(f.get("layovers", [])))
        layover_penalty = prefs.get("layover_penalty", 100)
        score -= stops * layover_penalty

    # ─── HORÁRIO (campo evoluível: morning_bonus) ───
    dep = f.get("departure", "")
    morning_bonus = prefs.get("morning_bonus", 50)
    prefer_morning = prefs.get("prefer_morning", True)

    # Override com input explícito
    if preferred_time == "morning":
        if "T06" in dep or "T07" in dep or "T08" in dep or "T09" in dep:
            score += 70
    elif preferred_time == "afternoon":
        if "T12" in dep or "T13" in dep or "T14" in dep or "T15" in dep:
            score += 70
    elif preferred_time == "evening":
        if "T18" in dep or "T19" in dep or "T20" in dep:
            score += 70
    elif prefer_morning and ("T06" in dep or "T07" in dep or "T08" in dep or "T09" in dep):
        # Usa bónus aprendido
        score += morning_bonus

    # ─── CONFORTO (companhias premium) ───
    comfort = prefs.get("comfort_priority", 0.5)
    premium_airlines = ["TAP", "LH", "BA", "AF", "KLM", "Swiss"]
    if comfort > 0.6 and f.get("airline") in premium_airlines:
        score += 30

    # ─── §104 CONFIANÇA (personalização forte quando há histórico) ───
    learned_confidence = prefs.get("learned_confidence", 0.0)
    if learned_confidence > 0.5:
        # Amplifica os ajustes personalizados quando há confiança
        personal_boost = 20 * learned_confidence
        if f.get("direct", False) and prefs.get("avoid_stops", True):
            score += personal_boost

    # ─── §106 CONTEXTO (modulador situacional) ───
    score = apply_context_modifiers(score, f, "flight", prefs, context)

    return score


def score_hotel(h: dict, prefs: dict = None, context: dict = None) -> float:
    """
    §104.1 — Score a hotel for Nómada decision-making (Personalização Real).

    Heurística v2.0 (evoluída):
    - Usa campos EVOLUÍVEIS do Memory Engine
    - Escala comparável com voos (~200 impacto máximo)
    """
    if prefs is None:
        prefs = {
            "price_sensitivity": 0.5, "comfort_priority": 0.5,
            "hotel_rating_weight": 50, "hotel_price_weight": 0.5,
            "hotel_comfort_bonus": 40, "hotel_location_bonus": 80,
            "hotel_quietness_bonus": 40, "learned_confidence": 0.0
        }
    if context is None:
        context = {}

    score = 1000  # Base score

    # ─── RATING (campo evoluível: hotel_rating_weight) ───
    rating = h.get("rating", h.get("stars", 3))
    rating_weight = prefs.get("hotel_rating_weight", 50)  # 30 → 70
    score += rating * rating_weight

    # ─── PREÇO (campo evoluível: hotel_price_weight) ───
    price = h.get("price", h.get("price_per_night", 100))
    price_weight = prefs.get("hotel_price_weight", 0.5)  # 0.3 → 0.7
    score -= price * price_weight

    # ─── CONFORTO (campo evoluível: hotel_comfort_bonus) ───
    comfort_bonus = prefs.get("hotel_comfort_bonus", 40)
    if rating >= 4:
        score += comfort_bonus

    # ─── LOCALIZAÇÃO (campo evoluível: hotel_location_bonus) ───
    location_bonus = prefs.get("hotel_location_bonus", 80)
    # Assumir central se não tiver info de distância
    distance = h.get("distance_km", h.get("distance", 0))
    if distance and distance < 2:
        score += location_bonus
    elif distance and distance < 5:
        score += location_bonus * 0.5

    # ─── REVIEWS (confiança extra) ───
    reviews = h.get("reviews_count", h.get("reviews", 0))
    if reviews > 1000:
        score += 40
    elif reviews > 500:
        score += 25
    elif reviews > 100:
        score += 15

    # ─── §104.1 CONFIANÇA (amplificador) ───
    learned_confidence = prefs.get("learned_confidence", 0.0)
    if learned_confidence > 0.5 and rating >= 4:
        score += 20 * learned_confidence

    # ─── §106 CONTEXTO (modulador) ───
    score = apply_context_modifiers(score, h, "hotel", prefs, context)

    return score


# ── §106 — Contexto no Scoring ────────────────────────────────────────────────
def apply_context_modifiers(score: float, entity: dict, entity_type: str, prefs: dict, context: dict) -> float:
    """
    §106 — Apply situational context modifiers to score.

    Rules:
    - Context MODULATES, doesn't override preferences
    - Impact moderate (20-60 max per modifier)
    - Always deterministic and predictable
    - Only 4 context types: time_pressure, weather, trip_type, time_of_day
    """
    if context is None:
        return score

    time_pressure = context.get("time_pressure", "normal")
    weather = context.get("weather", "clear")
    trip_type = context.get("trip_type", "leisure")
    time_of_day = context.get("time_of_day", "afternoon")

    # ─── FLIGHTS ───
    if entity_type == "flight":
        stops = entity.get("stops", entity.get("stopovers", 1))
        dep_hour = entity.get("departure_hour", 12)

        # Extract hour from departure string if needed
        if "departure" in entity and isinstance(entity["departure"], str):
            try:
                dep_hour = int(entity["departure"].split("T")[-1].split(":")[0])
            except:
                pass

        # High time pressure → direct flights get bonus
        if time_pressure == "high" and stops == 0:
            score += 60

        # Morning preference alignment
        if time_of_day == "morning" and dep_hour < 12:
            score += 25
        elif time_of_day == "night" and dep_hour >= 18:
            score += 25

        # Business trip → prefer efficiency
        if trip_type == "business" and stops == 0:
            score += 30

    # ─── HOTELS ───
    elif entity_type == "hotel":
        rating = entity.get("rating", entity.get("stars", 3))
        distance = entity.get("distance_km", entity.get("distance", 5))
        quiet = entity.get("quiet", rating >= 4)
        central = distance < 2 if distance else False

        # Business trip → location and quiet matter more
        if trip_type == "business":
            if central:
                score += 40
            if quiet:
                score += 30

        # Leisure trip → experience matters more
        elif trip_type == "leisure":
            if rating >= 4.5:
                score += 35

        # Bad weather → prefer hotels with good amenities
        if weather in ("rain", "cold"):
            if rating >= 4:
                score += 20

    # ─── PLACES ───
    elif entity_type == "place":
        type_group = entity.get("type_group", "")
        indoor = entity.get("indoor", entity.get("type", "") in ["restaurant", "cafe", "museum", "pharmacy", "bank"])
        open_now = entity.get("open_now", True)

        # Rain → indoor places get bonus
        if weather == "rain" and indoor:
            score += 40

        # Night → food places get bonus
        if time_of_day == "night" and type_group == "food":
            score += 25

        # High time pressure → open now is critical
        if time_pressure == "high" and open_now:
            score += 30

        # Cold weather → warm indoor places
        if weather == "cold" and indoor:
            score += 25

    # ─── TRAINS (§103) ───
    elif entity_type == "train":
        transfers = entity.get("transfers", 0)
        duration = entity.get("duration_total", 999)
        city_center = entity.get("city_center_departure", False) and entity.get("city_center_arrival", False)

        # High time pressure → direct trains get bonus
        if time_pressure == "high" and transfers == 0:
            score += 50

        # Business trip → city center arrival is gold
        if trip_type == "business" and city_center:
            score += 45

        # Short duration trains (<3h) get bonus in any context
        if duration < 180:
            score += 30

    # ─── UNIFIED TRAVEL (§103) ───
    elif entity_type == "travel":
        # Route to specific handler
        modal_type = entity.get("type", "flight")
        if modal_type == "train":
            return apply_context_modifiers(score, entity, "train", prefs, context)
        else:
            return apply_context_modifiers(score, entity, "flight", prefs, context)

    return score


# ══════════════════════════════════════════════════════════════════════════════
# §103 — UNIFIED TRAVEL SCORING
# "Flight e Train são apenas variações de travel_option"
# ══════════════════════════════════════════════════════════════════════════════

def score_travel_option(opt: dict, prefs: dict = None, context: dict = None) -> float:
    """
    §103 — Unified scoring for flights AND trains.

    Core principle: score the JOURNEY, not the modal.
    Maria decides the BEST way to travel, regardless of type.
    """
    if prefs is None:
        prefs = {
            "avoid_stops": True, "price_sensitivity": 0.5, "prefer_morning": True,
            "comfort_priority": 0.5, "direct_bonus": 200, "layover_penalty": 100,
            "duration_weight": 0.5, "price_weight": 1.5, "morning_bonus": 50,
            "learned_confidence": 0.0
        }
    if context is None:
        context = {}

    score = 1000  # Base score

    modal_type = opt.get("type", "flight")

    # ─── PRICE (universal) ───
    price = opt.get("price", 999)
    price_weight = prefs.get("price_weight", 1.5)
    score -= price * price_weight

    # ─── DURATION TOTAL (porta-a-porta for trains includes check-in time advantage) ───
    duration = opt.get("duration_total", opt.get("duration_min", opt.get("duration_minutes", 999)))

    # Trains: city center to city center = no airport time
    if modal_type == "train":
        # Flights have ~90min overhead (check-in, security, boarding, taxi)
        # Trains just show up and go — this is reflected in duration_total
        pass  # Duration already accurate for trains

    duration_weight = prefs.get("duration_weight", 0.5)
    score -= duration * duration_weight

    # ─── DIRECT/TRANSFERS ───
    direct = opt.get("direct", False)
    transfers = opt.get("transfers", opt.get("stops", 0))

    if direct or transfers == 0:
        direct_bonus = prefs.get("direct_bonus", 200)
        score += direct_bonus
    else:
        layover_penalty = prefs.get("layover_penalty", 100)
        score -= transfers * layover_penalty

    # ─── TRAIN-SPECIFIC ADVANTAGES (European context) ───
    if modal_type == "train":
        # City center advantage (no taxi/transfer needed)
        if opt.get("city_center_departure", False) and opt.get("city_center_arrival", False):
            score += 60  # Significant convenience boost

        # Short trains (<3h) are often better than equivalent flights
        if duration < 180:
            score += 80  # European sweet spot

        # Premium train types (ICE, TGV, etc.)
        train_type = opt.get("train_type", "").upper()
        if train_type in ("ICE", "TGV", "THALYS", "EUROSTAR"):
            comfort = prefs.get("comfort_priority", 0.5)
            if comfort > 0.4:
                score += 30

    # ─── FLIGHT-SPECIFIC (preserved from score_flight) ───
    elif modal_type == "flight":
        # Time preference
        dep = opt.get("departure", opt.get("departure_time", ""))
        morning_bonus = prefs.get("morning_bonus", 50)
        prefer_morning = prefs.get("prefer_morning", True)

        if prefer_morning and any(t in str(dep) for t in ["T06", "T07", "T08", "T09"]):
            score += morning_bonus

        # Comfort (premium airlines)
        comfort = prefs.get("comfort_priority", 0.5)
        premium_airlines = ["TAP", "LH", "BA", "AF", "KLM", "Swiss"]
        if comfort > 0.6 and opt.get("airline") in premium_airlines:
            score += 30

    # ─── LEARNED CONFIDENCE (personalization boost) ───
    learned_confidence = prefs.get("learned_confidence", 0.0)
    if learned_confidence > 0.5:
        personal_boost = 20 * learned_confidence
        if direct and prefs.get("avoid_stops", True):
            score += personal_boost

    # ─── CONTEXT MODIFIERS (§106) ───
    score = apply_context_modifiers(score, opt, modal_type, prefs, context)

    return score


def explain_train_decision(train: dict, lang: str = "PT") -> str:
    """§103+§105 — Generate human explanation for why this train was chosen."""
    price = train.get("price", 0)
    duration = train.get("duration_total", 0)
    direct = train.get("direct", False)
    train_type = train.get("train_type", "")
    origin = train.get("origin", "")
    destination = train.get("destination", "")

    # Format duration
    hours = duration // 60
    mins = duration % 60
    duration_str = f"{hours}h{mins:02d}" if hours else f"{mins}min"

    # Price display
    price_str = f"{price}€" if price else ""

    templates = {
        "PT": {
            "direct_fast": f"Este comboio é perfeito: {duration_str} directo de centro a centro. {price_str}",
            "direct": f"Escolhi este {train_type}: directo, {duration_str}. Chegas ao centro sem stress.",
            "with_price": f"A melhor opção de comboio: {price_str}, {duration_str}. Sais do centro, chegas ao centro.",
            "default": f"Este {train_type or 'comboio'} faz mais sentido: {duration_str}, directo e prático."
        },
        "DE": {
            "direct_fast": f"Dieser Zug ist perfekt: {duration_str} direkt von Zentrum zu Zentrum. {price_str}",
            "direct": f"Meine Wahl {train_type}: Direktverbindung, {duration_str}. Entspannt ins Zentrum.",
            "with_price": f"Beste Zugoption: {price_str}, {duration_str}. Von Zentrum zu Zentrum.",
            "default": f"Dieser {train_type or 'Zug'} macht mehr Sinn: {duration_str}, direkt und praktisch."
        },
        "EN": {
            "direct_fast": f"This train is perfect: {duration_str} direct, city center to city center. {price_str}",
            "direct": f"My pick {train_type}: direct, {duration_str}. Arrive right in the center.",
            "with_price": f"Best train option: {price_str}, {duration_str}. Center to center.",
            "default": f"This {train_type or 'train'} makes more sense: {duration_str}, direct and practical."
        }
    }

    t = templates.get(lang, templates["EN"])

    if direct and duration < 180:
        return t["direct_fast"]
    elif direct:
        return t["direct"]
    elif price > 0:
        return t["with_price"]
    else:
        return t["default"]


def explain_flight_decision(flight: dict, lang: str = "PT") -> str:
    """Generate human explanation for why this flight was chosen."""
    price = flight.get("price", 0)
    duration = flight.get("duration_str", "")
    direct = flight.get("direct", False)
    airline = flight.get("airline", "")
    dep = flight.get("departure", "")

    # Extract time
    time_str = ""
    if "T" in dep:
        time_str = dep.split("T")[1][:5]

    templates = {
        "PT": {
            "direct_cheap": f"Este é o melhor para ti: {price}€, voo directo com {airline}, {duration}. Sais às {time_str} — chegas descansado.",
            "direct": f"Escolhi este: {price}€, directo com {airline}. {duration} de viagem, sem stress de escalas.",
            "cheap": f"A melhor opção: apenas {price}€ com {airline}. {duration} de viagem.",
            "balanced": f"Este equilibra bem: {price}€, {duration}, {airline}. Boa relação qualidade-tempo."
        },
        "DE": {
            "direct_cheap": f"Das Beste für dich: {price}€, Direktflug mit {airline}, {duration}. Abflug {time_str} — entspannt ankommen.",
            "direct": f"Meine Wahl: {price}€, Direktflug mit {airline}. {duration} Reisezeit, stressfrei.",
            "cheap": f"Beste Option: nur {price}€ mit {airline}. {duration} Flugzeit.",
            "balanced": f"Gute Balance: {price}€, {duration}, {airline}. Gutes Preis-Leistungs-Verhältnis."
        },
        "EN": {
            "direct_cheap": f"Best for you: {price}€, direct with {airline}, {duration}. Depart {time_str} — arrive relaxed.",
            "direct": f"My pick: {price}€, direct with {airline}. {duration} flight, no layover stress.",
            "cheap": f"Best option: only {price}€ with {airline}. {duration} flight.",
            "balanced": f"Good balance: {price}€, {duration}, {airline}. Great value."
        }
    }

    lang_templates = templates.get(lang, templates["EN"])

    if direct and price < 100:
        return lang_templates["direct_cheap"]
    elif direct:
        return lang_templates["direct"]
    elif price < 80:
        return lang_templates["cheap"]
    else:
        return lang_templates["balanced"]


def explain_hotel_decision(hotel: dict, lang: str = "PT") -> str:
    """Generate human explanation for why this hotel was chosen."""
    name = hotel.get("name", "Hotel")
    price = hotel.get("price", hotel.get("price_per_night", 0))
    rating = hotel.get("rating", hotel.get("stars", 0))

    templates = {
        "PT": f"Escolhi o {name}: {rating}★, {price}€/noite. Boa localização e reviews positivas.",
        "DE": f"Meine Wahl: {name}: {rating}★, {price}€/Nacht. Gute Lage und positive Bewertungen.",
        "EN": f"My pick: {name}: {rating}★, {price}€/night. Good location and positive reviews."
    }

    return templates.get(lang, templates["EN"])


# ── §69b Place Type Detection from Query ──────────────────────────────────────
# When frontend sends wrong intent, backend detects true intent from query
PLACE_TYPE_KEYWORDS = {
    # Health & Services
    "pharmacy": ["farmacia", "farmácia", "apotheke", "pharmacy", "drogerie", "medicamento"],
    "hospital": ["hospital", "krankenhaus", "klinik", "clinic", "urgencia", "emergencia", "notaufnahme"],
    "bank": ["banco", "bank", "caixa", "atm", "geldautomat", "multibanco"],
    # Shopping
    "supermarket": ["supermercado", "supermarkt", "supermarket", "mercado", "grocery", "lebensmittel"],
    # Leisure
    "bar": ["bar", "pub", "kneipe", "cerveja", "bier", "beer", "drinks"],
    "beach": ["praia", "strand", "beach", "mar", "meer", "sea"],
    "park": ["parque", "park", "jardim", "garten", "garden"],
    "theater": ["teatro", "theater", "kino", "cinema", "filme", "movie"],
    # Transport
    "station": ["estação", "estacao", "bahnhof", "station", "comboio", "zug", "train", "metro", "u-bahn"],
    "airport": ["aeroporto", "flughafen", "airport"],
    "gas": ["gasolina", "tankstelle", "gas station", "posto", "benzin", "fuel"],
    # Culture
    "church": ["igreja", "kirche", "church", "catedral", "dom", "cathedral"],
    "library": ["biblioteca", "bibliothek", "library"],
    "museum": ["museu", "museum"],
    "gym": ["ginásio", "ginasio", "fitnessstudio", "gym", "fitness"],
    "spa": ["spa", "wellness", "termas", "sauna"],
    # Food
    "restaurant": ["restaurante", "restaurant", "comer", "essen", "eat", "jantar", "almoço", "dinner", "lunch"],
    "cafe": ["café", "cafe", "kaffee", "coffee", "cafetaria", "cafeteria"],
}


def detect_place_type_from_query(text: str) -> str | None:
    """
    Detect the actual place type from user's raw query.
    Returns the place type key if found, None otherwise.

    This overrides frontend's intent when there's a mismatch.

    §69c FIX: Use word boundaries to prevent substring false positives.
    Example: "maria" should NOT match "mar" (beach keyword).
    """
    if not text:
        return None

    lower = text.lower()

    # Check each place type's keywords using WORD BOUNDARIES
    # This prevents "maria" from matching "mar" (beach)
    for place_type, keywords in PLACE_TYPE_KEYWORDS.items():
        if any(re.search(r'\b' + re.escape(kw) + r'\b', lower) for kw in keywords):
            return place_type

    return None


# ── §70 I-TRAVEL-2: MARIA pergunta destino se não detectado ───────────────────
# Idioma ≠ Localização. Nunca inferir destino pelo idioma.
MARIA_ASK_DESTINATION = {
    "flight": {
        "PT": "Para onde queres voar? 🌍 Diz-me a cidade de destino.",
        "DE": "Wohin möchtest du fliegen? 🌍 Nenne mir die Zielstadt.",
        "EN": "Where would you like to fly? 🌍 Tell me the destination city.",
    },
    "hotel": {
        "PT": "Em que cidade procuras alojamento? 🏨",
        "DE": "In welcher Stadt suchst du eine Unterkunft? 🏨",
        "EN": "In which city are you looking for accommodation? 🏨",
    },
}


# ── Config ────────────────────────────────────────────────────────────────────
GOOGLE_PLACES_KEY = os.getenv("GOOGLE_PLACES_KEY", "")
LEDGER_URL        = os.getenv("LEDGER_URL", "http://localhost:8101/api/receipts")
LEDGER_APP        = "W-MARIA-001"
OPEN_METEO_URL    = "https://api.open-meteo.com/v1/forecast"
GATEWAY_URL       = os.getenv("GATEWAY_URL", "http://localhost:8130")
GATEWAY_SECRET    = os.getenv("GATEWAY_SECRET", "windi-gateway-secret-2026")

# ── Router (integrates with identity_gate.py) ─────────────────────────────────
router = APIRouter(prefix="/maria", tags=["W-MARIA-001-Booking"])

# ── Models ────────────────────────────────────────────────────────────────────
class IntentPayload(BaseModel):
    type: str                          # restaurant | museum | cafe | hotel | event
    time_available: Optional[float] = None
    no_queue: Optional[bool] = False
    family: Optional[bool] = False
    quiet: Optional[bool] = False
    wifi: Optional[bool] = False
    quality: Optional[str] = "medium"

class PlanRequest(BaseModel):
    intent: IntentPayload
    lat: Optional[float] = Field(None, description="GPS latitude — never stored")
    lng: Optional[float] = Field(None, description="GPS longitude — never stored")
    lang: Optional[str] = "PT"        # PT | DE | EN
    wallet_id: Optional[str] = None   # for Ledger attribution
    did: Optional[str] = None         # alias for wallet_id (DID Identity)
    query: Optional[str] = None       # §67: Raw user message for intent detection

class PlaceResult(BaseModel):
    name: str
    type: str
    distance_text: str
    queue_status: str
    reason: str
    google_place_id: Optional[str] = None
    address: Optional[str] = None
    rating: Optional[float] = None
    open_now: Optional[bool] = None
    lat: Optional[float] = None    # §79 Super Carta
    lng: Optional[float] = None    # §79 Super Carta
    deep_link: Optional[str] = None  # §103 Intermodal — booking URL

class MariaVoice(BaseModel):
    PT: str
    DE: str
    EN: str

class PlaceLocation(BaseModel):
    """§79 — Location for Super Carta map pins"""
    name: str
    type: str
    lat: float
    lng: float
    rating: Optional[float] = None
    address: Optional[str] = None
    open_now: Optional[bool] = None

class PlanResponse(BaseModel):
    request_id: str
    decision: PlaceResult
    context: dict
    maria_voice: MariaVoice
    intent_parsed: dict
    ledger_receipt_id: Optional[str] = None
    cost_eur: float = 0.0
    sovereign_mode: bool = False       # True if external APIs failed → I10
    memory_active: bool = False        # True if DID profile loaded
    timestamp: str
    locations: Optional[list[PlaceLocation]] = None  # §79 Super Carta map pins
    visible_memory: Optional[list[str]] = None  # §108 Memória Visível

# ── §67 Flight Search Models ────────────────────────────────────────────────────
class FlightSearchRequest(BaseModel):
    fly_from: str = Field(..., description="Origin city or IATA code")
    fly_to: str = Field(..., description="Destination city or IATA code")
    date: str = Field(..., description="Departure date dd/mm/yyyy")
    lang: Optional[str] = "PT"
    wallet_id: Optional[str] = None
    adults: Optional[int] = 1
    max_results: Optional[int] = 3

class FlightSearchResponse(BaseModel):
    request_id: str
    flights: list
    origin: str
    destination: str
    date: str
    maria_voice: str
    ledger_receipt_id: Optional[str] = None
    sovereign_mode: bool = False
    source: str = "kiwi.com"
    timestamp: str

# ── §68 Hotel Search Models ─────────────────────────────────────────────────────
class HotelSearchRequest(BaseModel):
    destination: str = Field(..., description="City name")
    check_in: str = Field(..., description="Check-in date YYYY-MM-DD")
    check_out: str = Field(..., description="Check-out date YYYY-MM-DD")
    lang: Optional[str] = "PT"
    wallet_id: Optional[str] = None
    adults: Optional[int] = 2
    max_results: Optional[int] = 3

class HotelSearchResponse(BaseModel):
    request_id: str
    hotels: list
    destination: str
    check_in: str
    check_out: str
    nights: int
    maria_voice: str
    ledger_receipt_id: Optional[str] = None
    sovereign_mode: bool = False
    source: str = "hotellook.com"
    timestamp: str

# ── Context Enricher (Open-Meteo + Nominatim, FREE) ───────────────────────────
# §70 FIX: Reverse geocoding to get REAL city from GPS
# "Falar português não significa querer ir a Lisboa."
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"

async def enrich_context(lat: float, lng: float) -> dict:
    """Fetch real weather + city via Open-Meteo + Nominatim. Zero cost, no API key."""
    result = {
        "weather": "? N/A",
        "is_raining": False,
        "lat": round(lat, 3),   # I1: reduced precision, not stored
        "lng": round(lng, 3),
        "city": "local area",   # §70: Will be replaced by real city
        "country": "",
    }

    async with httpx.AsyncClient(timeout=5.0) as client:
        # 1. Weather from Open-Meteo
        try:
            r = await client.get(OPEN_METEO_URL, params={
                "latitude": lat, "longitude": lng,
                "current": "temperature_2m,precipitation,weathercode",
                "timezone": "auto",
            })
            d = r.json().get("current", {})
            temp = d.get("temperature_2m", "?")
            rain = d.get("precipitation", 0) > 0.5
            code = d.get("weathercode", 0)
            emoji = "🌧️" if rain else ("⛅" if code in range(1, 4) else "☀️")
            result["weather"] = f"{emoji} {temp}°C"
            result["is_raining"] = rain
        except Exception as e:
            log.warning(f"Open-Meteo fallback: {e}")

        # 2. §70 — Reverse geocoding from Nominatim (OpenStreetMap)
        #    Get REAL city from GPS, not language assumption
        try:
            r = await client.get(NOMINATIM_URL, params={
                "lat": lat, "lon": lng,
                "format": "json",
                "addressdetails": 1,
            }, headers={"User-Agent": "WINDI-MARIA/1.0"})
            addr = r.json().get("address", {})
            # Try city, town, village, municipality in order
            city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("municipality") or addr.get("county", "")
            country = addr.get("country", "")
            if city:
                result["city"] = f"{city}, {country}" if country else city
                result["country"] = country
                log.info(f"[§70] GPS→City: {lat},{lng} → {result['city']}")
        except Exception as e:
            log.warning(f"Nominatim fallback: {e}")

    return result

# ── Google Places Search (via Sovereignty Gate) ───────────────────────────────
# §69 — Expanded Place Type Map (was 5, now 25+)
PLACE_TYPE_MAP = {
    # Original 5
    "restaurant": "restaurant",
    "cafe":       "cafe",
    "museum":     "museum",
    "hotel":      "lodging",
    "event":      "tourist_attraction",
    # Expanded — Health & Services
    "pharmacy":   "pharmacy",
    "farmacia":   "pharmacy",
    "apotheke":   "pharmacy",
    "hospital":   "hospital",
    "klinik":     "hospital",
    "bank":       "bank",
    "banco":      "bank",
    # Expanded — Shopping
    "supermarket": "supermarket",
    "supermercado": "supermarket",
    "supermarkt":  "supermarket",
    "market":     "grocery_or_supermarket",
    "mercado":    "grocery_or_supermarket",
    "markt":      "grocery_or_supermarket",
    # Expanded — Leisure
    "bar":        "bar",
    "beach":      "natural_feature",
    "praia":      "natural_feature",
    "strand":     "natural_feature",
    "park":       "park",
    "parque":     "park",
    "theater":    "movie_theater",
    "theatre":    "movie_theater",
    "teatro":     "movie_theater",
    "cinema":     "movie_theater",
    "kino":       "movie_theater",
    # Expanded — Transport
    "station":    "transit_station",
    "estacao":    "transit_station",
    "bahnhof":    "transit_station",
    "airport":    "airport",
    "aeroporto":  "airport",
    "flughafen":  "airport",
    "gas":        "gas_station",
    "gasolina":   "gas_station",
    "tankstelle": "gas_station",
    # Expanded — Culture
    "church":     "church",
    "igreja":     "church",
    "kirche":     "church",
    "library":    "library",
    "biblioteca": "library",
    "bibliothek": "library",
    "spa":        "spa",
    "gym":        "gym",
    "ginasio":    "gym",
    "fitnessstudio": "gym",
}

async def search_places(intent: IntentPayload, lat: float, lng: float, lang: str, tier: str = "MED", actor: str = "anonymous") -> tuple[list[dict], bool]:
    """
    Query Places via Sovereignty Gate — cache-first, audit-always.

    Returns:
        (list of places, cache_hit boolean)
    """
    gtype = PLACE_TYPE_MAP.get(intent.type, "point_of_interest")

    # Use Sovereignty Gate if available
    if PLACES_GATE_ENABLED:
        result = await search_places_sovereign(
            place_type=gtype,
            lat=lat,
            lng=lng,
            lang=lang,
            tier=tier,
            actor=actor
        )

        places = result.get("places", [])
        cache_hit = result.get("cache_hit", False)

        # Transform gate output to expected format
        # §79 — Include lat/lng for Super Carta map pins
        out = []
        for p in places:
            geo = p.get("geometry", {}).get("location", {})
            out.append({
                "name": p.get("name"),
                "place_id": p.get("place_id"),
                "address": p.get("vicinity") or p.get("formatted_address"),
                "rating": p.get("rating"),
                "open_now": p.get("opening_hours", {}).get("open_now") if isinstance(p.get("opening_hours"), dict) else None,
                "user_ratings_total": p.get("user_ratings_total", 0),
                "lat": geo.get("lat"),   # §79 Super Carta
                "lng": geo.get("lng"),   # §79 Super Carta
            })

        log.info(f"[Places Gate] {len(out)} results · cache_hit={cache_hit}")
        return out, cache_hit

    # Fallback: Direct API call (legacy)
    if not GOOGLE_PLACES_KEY:
        return [], False

    lang_code = {"PT": "pt", "DE": "de", "EN": "en"}.get(lang, "en")
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(
                "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
                params={
                    "location": f"{lat},{lng}",
                    "rankby": "distance",
                    "type": gtype,
                    "language": lang_code,
                    "key": GOOGLE_PLACES_KEY,
                }
            )
            results = r.json().get("results", [])[:5]
            out = []
            for p in results:
                geo = p.get("geometry", {}).get("location", {})
                out.append({
                    "name": p.get("name"),
                    "place_id": p.get("place_id"),
                    "address": p.get("vicinity"),
                    "rating": p.get("rating"),
                    "open_now": p.get("opening_hours", {}).get("open_now"),
                    "user_ratings_total": p.get("user_ratings_total", 0),
                    "lat": geo.get("lat"),   # §79 Super Carta
                    "lng": geo.get("lng"),   # §79 Super Carta
                })
            return out, False  # Not from cache
    except Exception as e:
        log.warning(f"Google Places fallback: {e}")
        return [], False

# ── §104.1 Decision Engine (Personalização Real) ─────────────────────────────
def score_place(place: dict, intent: IntentPayload, ctx: dict, prefs: dict = None) -> float:
    """
    §104.1 — Score a candidate place (Personalização Real).

    Escala 0-100, comparável em intensidade com voos/hotéis.
    Usa campos evoluíveis do Memory Engine.
    """
    if prefs is None:
        prefs = {
            "place_distance_weight": 0.5,
            "place_rating_bonus": 30,
            "place_type_boosts": {"food": 1.0, "essential": 1.0, "leisure": 1.0},
            "learned_confidence": 0.0
        }

    score = 50.0

    # ─── RATING (campo evoluível: place_rating_bonus) ───
    rating = place.get("rating") or 3.5
    rating_bonus = prefs.get("place_rating_bonus", 30)
    if rating >= 4.5:
        score += rating_bonus
    elif rating >= 4.0:
        score += rating_bonus * 0.7
    elif rating >= 3.5:
        score += rating_bonus * 0.4

    # ─── OPEN NOW (importante) ───
    if place.get("open_now") is True:
        score += 15
    elif place.get("open_now") is False:
        score -= 40

    # ─── TYPE BOOST (campo evoluível: place_type_boosts) ───
    type_boosts = prefs.get("place_type_boosts", {"food": 1.0, "essential": 1.0, "leisure": 1.0})
    category = _classify_intent_category(intent.type)
    boost = type_boosts.get(category, 1.0)
    score *= boost

    # ─── INTENT-SPECIFIC (quiet, family) ───
    if intent.quiet and (place.get("user_ratings_total") or 0) < 500:
        score += 8
    if intent.family and intent.type == "museum":
        score += 10

    # ─── §104.1 CONFIANÇA (amplificador) ───
    learned_confidence = prefs.get("learned_confidence", 0.0)
    if learned_confidence > 0.5 and rating >= 4.0:
        score += 5 * learned_confidence

    # ─── §106 CONTEXTO (modulador situacional) ───
    # Enrich place with type_group for context modifiers
    place_enriched = {**place, "type_group": _classify_intent_category(intent.type)}
    score = apply_context_modifiers(score, place_enriched, "place", prefs, ctx)

    return round(score, 1)


def _classify_intent_category(intent_type: str) -> str:
    """§104.1 — Classify intent type into category."""
    food_types = ["restaurant", "cafe", "bar", "bakery", "food"]
    essential_types = ["pharmacy", "bank", "supermarket", "hospital", "atm", "gas_station"]
    leisure_types = ["museum", "park", "beach", "tourist_attraction", "spa", "gym"]

    intent_lower = (intent_type or "").lower()

    if intent_lower in food_types:
        return "food"
    elif intent_lower in essential_types:
        return "essential"
    elif intent_lower in leisure_types:
        return "leisure"
    return "food"  # default

def build_reason(place: dict, intent: IntentPayload, ctx: dict, lang: str) -> str:
    parts = []
    if ctx.get("is_raining"):
        r = {"PT": "Coberto — ideal para chuva", "DE": "Überdacht — ideal bei Regen", "EN": "Covered — ideal for rain"}
        parts.append(r[lang])
    if place.get("open_now"):
        r = {"PT": "Aberto agora", "DE": "Jetzt geöffnet", "EN": "Open now"}
        parts.append(r[lang])
    if place.get("rating") and place["rating"] >= 4.2:
        r = {"PT": f"Nota {place['rating']} ★", "DE": f"Bewertung {place['rating']} ★", "EN": f"Rating {place['rating']} ★"}
        parts.append(r[lang])
    if intent.wifi:
        parts.append("Wi-Fi")
    if not parts:
        r = {"PT": "Melhor opção próxima", "DE": "Beste Option in der Nähe", "EN": "Best nearby option"}
        parts.append(r[lang])
    return " · ".join(parts)

def build_voice(place_name: str, dist: str, queue_status: str, lang: str) -> MariaVoice:
    templates = {
        "PT": f"{place_name} está a {dist} de ti. {queue_status}.",
        "DE": f"Ich habe {place_name} in {dist} gefunden. {queue_status}.",
        "EN": f"I found {place_name}, {dist} away. {queue_status}.",
    }
    return MariaVoice(**templates)


# ── §105 — Explicação Visível ─────────────────────────────────────────────────
def generate_explanation(entity: dict, entity_type: str, prefs: dict, context: dict, lang: str = "PT") -> str:
    """
    §105 — Generate human-readable explanation for Maria's decision.

    Rules:
    - 1 base phrase (always)
    - Max 1 complement (priority: context > high confidence > low confidence)
    - Zero technical language
    """
    if prefs is None:
        prefs = {}
    if context is None:
        context = {}

    learned_conf = prefs.get("learned_confidence", 0.0)

    # ─── BASE EXPLANATION (by entity type) ───
    if entity_type == "flight":
        stops = entity.get("stops", entity.get("stopovers", 1))
        dep_hour = entity.get("departure_hour", 12)
        # Try to extract hour from departure time string
        if "departure" in entity and isinstance(entity["departure"], str):
            try:
                dep_hour = int(entity["departure"].split("T")[-1].split(":")[0])
            except:
                dep_hour = 12

        if stops == 0 and dep_hour < 12:
            base = {
                "PT": "Escolhi este voo porque é directo e parte cedo",
                "DE": "Ich habe diesen Flug gewählt, weil er direkt ist und früh abfliegt",
                "EN": "I chose this flight because it's direct and departs early"
            }
        elif stops == 0:
            base = {
                "PT": "Escolhi este voo porque é directo",
                "DE": "Ich habe diesen Flug gewählt, weil er direkt ist",
                "EN": "I chose this flight because it's direct"
            }
        elif dep_hour < 12:
            base = {
                "PT": "Escolhi este voo porque parte cedo",
                "DE": "Ich habe diesen Flug gewählt, weil er früh abfliegt",
                "EN": "I chose this flight because it departs early"
            }
        else:
            base = {
                "PT": "Escolhi este voo pelo melhor equilíbrio para ti",
                "DE": "Ich habe diesen Flug als beste Option für dich gewählt",
                "EN": "I chose this flight as the best balance for you"
            }

    elif entity_type == "hotel":
        rating = entity.get("rating", entity.get("stars", 0))
        central = entity.get("central", entity.get("distance_km", 10) < 2)

        if rating >= 4.5:
            base = {
                "PT": "Escolhi este hotel porque tem excelente avaliação",
                "DE": "Ich habe dieses Hotel wegen der ausgezeichneten Bewertung gewählt",
                "EN": "I chose this hotel because it has excellent reviews"
            }
        elif central:
            base = {
                "PT": "Escolhi este hotel pela localização",
                "DE": "Ich habe dieses Hotel wegen der Lage gewählt",
                "EN": "I chose this hotel for its location"
            }
        else:
            base = {
                "PT": "Escolhi este hotel pelo melhor equilíbrio para ti",
                "DE": "Ich habe dieses Hotel als beste Option für dich gewählt",
                "EN": "I chose this hotel as the best balance for you"
            }

    elif entity_type == "place":
        type_group = entity.get("type_group", _classify_place_type_group(entity.get("type", "")))

        if type_group == "food":
            base = {
                "PT": "Escolhi este lugar porque encaixa no que costumas procurar para comer",
                "DE": "Ich habe diesen Ort gewählt, weil er zu deinen Essgewohnheiten passt",
                "EN": "I chose this place because it fits what you usually look for to eat"
            }
        elif type_group == "essential":
            base = {
                "PT": "Escolhi este lugar porque é prático e próximo",
                "DE": "Ich habe diesen Ort gewählt, weil er praktisch und nah ist",
                "EN": "I chose this place because it's practical and nearby"
            }
        else:
            base = {
                "PT": "Escolhi este lugar porque combina contigo",
                "DE": "Ich habe diesen Ort gewählt, weil er zu dir passt",
                "EN": "I chose this place because it suits you"
            }

    # §103 — TRAIN EXPLANATIONS
    elif entity_type == "train":
        transfers = entity.get("transfers", 0)
        duration = entity.get("duration_total", 999)
        city_center = entity.get("city_center_departure", False) and entity.get("city_center_arrival", False)

        if transfers == 0 and duration < 180:
            base = {
                "PT": "Este comboio é perfeito: directo e chega mais rápido",
                "DE": "Dieser Zug ist perfekt: direkt und schneller am Ziel",
                "EN": "This train is perfect: direct and gets you there faster"
            }
        elif transfers == 0:
            base = {
                "PT": "Escolhi este comboio porque é directo",
                "DE": "Ich habe diesen Zug gewählt, weil er direkt ist",
                "EN": "I chose this train because it's direct"
            }
        elif city_center:
            base = {
                "PT": "Escolhi este comboio porque chega ao centro",
                "DE": "Ich habe diesen Zug gewählt, weil er ins Zentrum fährt",
                "EN": "I chose this train because it arrives in the city center"
            }
        else:
            base = {
                "PT": "Este comboio faz mais sentido para esta viagem",
                "DE": "Dieser Zug macht mehr Sinn für diese Reise",
                "EN": "This train makes more sense for this trip"
            }

    else:
        base = {
            "PT": "Escolhi isto porque faz sentido para ti",
            "DE": "Ich habe das gewählt, weil es für dich Sinn macht",
            "EN": "I chose this because it makes sense for you"
        }

    # ─── §106 COMPLEMENT (max 1, priority order) ───
    # Priority: time_pressure > weather > trip_type > confidence > learning
    complement = None

    if context.get("time_pressure") == "high":
        complement = {
            "PT": "sei que tens pouco tempo",
            "DE": "ich weiß, dass du wenig Zeit hast",
            "EN": "I know you're short on time"
        }
    elif context.get("weather") == "rain":
        complement = {
            "PT": "especialmente com esta chuva",
            "DE": "besonders bei diesem Regen",
            "EN": "especially with this rain"
        }
    elif context.get("weather") == "cold":
        complement = {
            "PT": "perfeito para este frio",
            "DE": "perfekt für diese Kälte",
            "EN": "perfect for this cold weather"
        }
    elif context.get("trip_type") == "business":
        complement = {
            "PT": "sei que esta é uma viagem de trabalho",
            "DE": "ich weiß, dass das eine Geschäftsreise ist",
            "EN": "I know this is a business trip"
        }
    elif context.get("trip_type") == "leisure" and entity_type == "hotel":
        complement = {
            "PT": "para que aproveites ao máximo",
            "DE": "damit du das Beste daraus machst",
            "EN": "so you can make the most of it"
        }
    elif learned_conf > 0.5:
        complement = {
            "PT": "baseado nas tuas escolhas anteriores",
            "DE": "basierend auf deinen früheren Entscheidungen",
            "EN": "based on your previous choices"
        }
    elif learned_conf < 0.3:
        complement = {
            "PT": "ainda estou a aprender contigo",
            "DE": "ich lerne noch mit dir",
            "EN": "I'm still learning with you"
        }

    # ─── OUTPUT ───
    base_text = base.get(lang, base["EN"])
    if complement:
        comp_text = complement.get(lang, complement["EN"])
        return f"{base_text} — {comp_text}."
    return f"{base_text}."


def _classify_place_type_group(place_type: str) -> str:
    """§105 helper — classify place type into group for explanation."""
    food_types = ["restaurant", "cafe", "bar", "bakery", "food"]
    essential_types = ["pharmacy", "bank", "supermarket", "hospital", "atm", "gas_station"]

    pt = (place_type or "").lower()
    if any(t in pt for t in food_types):
        return "food"
    elif any(t in pt for t in essential_types):
        return "essential"
    return "leisure"


# ── Ledger Seal ───────────────────────────────────────────────────────────────
async def seal_decision(request_id: str, payload: dict, wallet_id: str) -> Optional[str]:
    """Seal the decision in WINDI Forensic Ledger (:8101). I11."""
    receipt_id = f"WINDI-MARIA-{request_id[:8].upper()}"
    content_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    body = {
        "id": receipt_id,
        "actor": wallet_id or "anonymous",
        "app": LEDGER_APP,
        "doc_name": f"Maria Decision · {payload.get('place', '?')}",
        "doc_type": "doc",
        "governance_level": "HIGH",
        "content_hash": content_hash,
        "sge_score": 97,
        "note": json.dumps(payload, ensure_ascii=False),
    }
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            r = await client.post(LEDGER_URL, json=body)
            if r.status_code in (200, 201):
                log.info(f"Ledger sealed: {receipt_id}")
                return receipt_id
    except Exception as e:
        log.warning(f"Ledger seal failed (non-blocking): {e}")
    return None

# ── Gateway LLM Call (Plan B — Triple LLM) ────────────────────────────────────
async def call_gateway_llm(intent: dict, ctx: dict, lang: str) -> dict:
    """
    Call W-GATEWAY-001 with Triple LLM routing.
    Plan B: When GOOGLE_PLACES_KEY is absent, use LLM for recommendations.

    Returns dict with:
      - name: place name
      - reason: MARIA voice response
      - provider: gemini | anthropic | openai
      - sovereign_mode: False (LLM answered)
    """
    # §72 — Pulse Reading Layer (HER architecture)
    raw_input = intent.get("raw_input", "")
    current_hour = datetime.now().hour
    session_history = ctx.get("history", [])

    pulse = read_pulse(raw_input, current_hour, session_history)
    log.debug(f"[MARIA §72] Pulse: {pulse}")

    provider = select_provider(intent, ctx, pulse=pulse)
    system_prompt = get_system_prompt(provider, lang, pulse=pulse)

    # Build user message with context — trilingual (I12)
    city = ctx.get("city", "local area")
    weather = ctx.get("weather", "unknown")
    hour = datetime.now().strftime("%H:%M")
    intent_type = intent.get("type", "discover")
    companions = ctx.get("companions", "")

    # User message templates per language
    user_templates = {
        "PT": f"""Destino: {city}
Tipo: {intent_type}
Clima: {weather}
Hora: {hour}
Grupo: {companions or 'viajante solo'}

Sugere um lugar real para visitar agora.""",
        "DE": f"""Ziel: {city}
Typ: {intent_type}
Wetter: {weather}
Uhrzeit: {hour}
Gruppe: {companions or 'Alleinreisender'}

Empfehle einen echten Ort zum Besuchen.""",
        "EN": f"""Destination: {city}
Type: {intent_type}
Weather: {weather}
Time: {hour}
Group: {companions or 'solo traveller'}

Suggest a real place to visit now."""
    }
    user_msg = user_templates.get(lang, user_templates["EN"])

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.post(
                f"{GATEWAY_URL}/gateway/call",
                json={
                    "actor": "W-MARIA-001",
                    "tier": "HIGH",
                    "task": "chat",
                    "prompt": user_msg,
                    "system": system_prompt,
                },
                headers={
                    "Content-Type": "application/json",
                    "X-Gateway-Secret": GATEWAY_SECRET
                }
            )
            if r.status_code == 200:
                data = r.json()
                text = data.get("response", "") or data.get("content", "") or str(data)
                log.info(f"[LLM] {provider} responded · {len(text)} chars")
                return {
                    "name": f"Recomendação {provider.title()}",
                    "reason": text,
                    "provider": provider,
                    "sovereign_mode": False,
                }
    except Exception as e:
        log.warning(f"[LLM] Gateway call failed: {e}")

    # If LLM fails, return None to trigger old fallback
    return None


# ── Sovereign Fallback (I10) ───────────────────────────────────────────────────
SOVEREIGN_FALLBACK = {
    "restaurant": {"name": "Local Restaurant", "queue": {"PT": "Estado desconhecido", "DE": "Status unbekannt", "EN": "Status unknown"}},
    "cafe":       {"name": "Local Café",       "queue": {"PT": "Estado desconhecido", "DE": "Status unbekannt", "EN": "Status unknown"}},
    "museum":     {"name": "Local Museum",     "queue": {"PT": "Estado desconhecido", "DE": "Status unbekannt", "EN": "Status unknown"}},
    "hotel":      {"name": "Local Hotel",      "queue": {"PT": "Estado desconhecido", "DE": "Status unbekannt", "EN": "Status unknown"}},
    "event":      {"name": "Local Event",      "queue": {"PT": "Estado desconhecido", "DE": "Status unbekannt", "EN": "Status unknown"}},
}

# ── Main Endpoint ─────────────────────────────────────────────────────────────
@router.post("/plan", response_model=PlanResponse)
async def maria_plan(req: PlanRequest):
    t0 = time.time()
    request_id = str(uuid.uuid4())
    lang = req.lang if req.lang in ("PT", "DE", "EN") else "PT"
    sovereign_mode = False

    # 1. Context — weather (never store precise GPS — I1)
    lat = req.lat or 47.7258   # Kempten default
    lng = req.lng or 10.3175
    ctx = await enrich_context(lat, lng)
    ctx["lang"] = lang

    # 1b. Memory — enrich with DID profile if available
    did = req.wallet_id or req.did  # Support both field names
    memory_active = False
    if MEMORY_ENABLED and did:
        profile = get_or_create_nomada(did, lang=lang)
        ctx = enrich_context_with_memory(did, ctx)
        memory_active = True
        # Use nomada's preferred language if this is a returning user
        if not profile.get("is_new") and profile.get("lang"):
            lang = profile["lang"]
            ctx["lang"] = lang

    # 1c. §67 — Flight intent detection from raw query
    #     If user message contains flight keywords, route to Kiwi Bridge
    if KIWI_BRIDGE_ENABLED and req.query and detect_flight_intent(req.query):
        log.info(f"[{request_id[:8]}] Flight intent detected → routing to Kiwi Bridge")
        flight_details = extract_flight_details(req.query, default_from="MUC")

        # §70 I-TRAVEL-2: Se destino não detectado, MARIA pergunta (não assume)
        if flight_details.get("destination_missing") or not flight_details.get("fly_to"):
            log.info(f"[{request_id[:8]}] Destination missing → MARIA asks user")
            ask_msg = MARIA_ASK_DESTINATION["flight"].get(lang, MARIA_ASK_DESTINATION["flight"]["EN"])
            return PlanResponse(
                request_id=request_id,
                decision=PlaceResult(
                    name="Destino necessário",
                    type="flight_question",
                    distance_text="",
                    queue_status="",
                    reason=ask_msg,
                ),
                context={"weather": ctx.get("weather", ""), "needs_destination": True},
                maria_voice=MariaVoice(
                    PT=ask_msg if lang == "PT" else "",
                    DE=ask_msg if lang == "DE" else "",
                    EN=ask_msg if lang == "EN" else "",
                ),
                intent_parsed={"type": "flight", "needs_destination": True},
                ledger_receipt_id=None,
                cost_eur=0.0,
                sovereign_mode=False,
                memory_active=memory_active,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # §103 — INTERMODAL INTELLIGENCE
        # Search both flights AND trains, pick the BEST option
        origin = flight_details["fly_from"]
        destination = flight_details["fly_to"]
        travel_date = flight_details["date"]

        # Get user preferences for unified scoring
        travel_prefs = get_travel_preferences(did) if did and MEMORY_ENABLED else None

        # 1. Always search flights
        flights_data = await search_flights(
            fly_from=origin,
            fly_to=destination,
            date_from=travel_date,
            currency="EUR",
            max_results=5,
        )
        flights = flights_data.get("flights", [])

        # Normalize flights to travel_option format
        travel_options = []
        for f in flights:
            travel_options.append({
                "type": "flight",
                "origin": origin,
                "destination": destination,
                "departure_time": f.get("departure", ""),
                "arrival_time": f.get("arrival", ""),
                "duration_total": f.get("duration_min", f.get("duration_minutes", 999)) + 90,  # +90min airport overhead
                "price": f.get("price", 999),
                "transfers": f.get("stops", len(f.get("layovers", []))),
                "direct": f.get("direct", False),
                "city_center_departure": False,
                "city_center_arrival": False,
                "provider": "kiwi",
                "airline": f.get("airline", ""),
                "deep_link": f.get("deep_link", ""),
                "duration_str": f.get("duration_str", ""),
                "_original": f,  # Keep original for display
            })

        # 2. Search trains if distance < 800km (European rail sweet spot)
        if DB_BRIDGE_ENABLED and should_include_trains(origin, destination):
            log.info(f"[{request_id[:8]}] §103 Intermodal: also searching trains")
            trains_data = await search_trains(
                origin=origin,
                destination=destination,
                date=travel_date,
                time="08:00",
            )
            trains = trains_data.get("trains", [])

            for t in trains:
                travel_options.append({
                    "type": "train",
                    "origin": t.get("origin", origin),
                    "destination": t.get("destination", destination),
                    "departure_time": t.get("departure_time", ""),
                    "arrival_time": t.get("arrival_time", ""),
                    "duration_total": t.get("duration_total", 999),
                    "price": t.get("price", 0),
                    "transfers": t.get("transfers", 0),
                    "direct": t.get("direct", True),
                    "city_center_departure": t.get("city_center_departure", True),
                    "city_center_arrival": t.get("city_center_arrival", True),
                    "provider": "db",
                    "train_type": t.get("train_type", ""),
                    "booking_url": t.get("booking_url", ""),
                    "_original": t,
                })

        # 3. Score all options with unified scoring
        for opt in travel_options:
            opt["_score"] = score_travel_option(opt, travel_prefs, ctx)

        # 4. Sort by score (descending) and pick the BEST
        travel_options.sort(key=lambda x: x.get("_score", 0), reverse=True)
        best_option = travel_options[0] if travel_options else None

        if not best_option:
            # No options found — fallback to original flight response
            maria_text = format_flight_response(flights_data, lang)
            sovereign_mode = True
        else:
            # Generate explanation based on chosen modal
            if best_option["type"] == "train":
                maria_text = explain_train_decision(best_option, lang)
                sovereign_mode = False
                log.info(f"[{request_id[:8]}] §103 MARIA chose TRAIN over flight (score: {best_option['_score']:.0f})")
            else:
                maria_text = explain_flight_decision(best_option.get("_original", best_option), lang)
                sovereign_mode = flights_data.get("source") == "demo"

        # Seal to Ledger
        seal_payload = {
            "request_id": request_id,
            "origin": origin,
            "destination": destination,
            "date": travel_date,
            "modal_type": best_option["type"] if best_option else "unknown",
            "options_evaluated": len(travel_options),
            "sovereign_mode": sovereign_mode,
            "source": best_option.get("provider", "unknown") if best_option else "unknown",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        receipt_id = await seal_decision(request_id, seal_payload, req.wallet_id)

        # Build response based on best option
        if best_option:
            decision_name = f"{'Comboio' if lang == 'PT' else 'Zug' if lang == 'DE' else 'Train'} {origin} → {destination}" if best_option["type"] == "train" else f"{'Voo' if lang == 'PT' else 'Flug' if lang == 'DE' else 'Flight'} {origin} → {destination}"
            duration_str = best_option.get("duration_str", "")
            if not duration_str and best_option.get("duration_total"):
                h = best_option["duration_total"] // 60
                m = best_option["duration_total"] % 60
                duration_str = f"{h}h{m:02d}" if h else f"{m}min"
            price_str = f"{best_option.get('price', '?')}€"
            booking_link = best_option.get("deep_link") or best_option.get("booking_url", "")
        else:
            decision_name = f"Voo {origin} → {destination}"
            duration_str = "?"
            price_str = "?"
            booking_link = ""

        return PlanResponse(
            request_id=request_id,
            decision=PlaceResult(
                name=decision_name,
                type=best_option["type"] if best_option else "flight",
                distance_text=duration_str,
                queue_status=price_str,
                reason=maria_text[:200],
                rating=None,
                open_now=None,
                deep_link=booking_link,  # §103 — booking link
            ),
            context={
                "weather": ctx.get("weather", ""),
                "travel_options": [{"type": o["type"], "price": o["price"], "duration": o["duration_total"], "direct": o["direct"]} for o in travel_options[:5]],
                "origin": origin,
                "destination": destination,
                "source": best_option.get("provider", "unknown") if best_option else "unknown",
                "intermodal": len([o for o in travel_options if o["type"] == "train"]) > 0,
            },
            maria_voice=MariaVoice(
                PT=maria_text if lang == "PT" else "",
                DE=maria_text if lang == "DE" else "",
                EN=maria_text if lang == "EN" else "",
            ),
            intent_parsed={"type": best_option["type"] if best_option else "flight", "intermodal": True},
            ledger_receipt_id=receipt_id,
            cost_eur=0.0,
            sovereign_mode=sovereign_mode,
            memory_active=memory_active,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # 1d. §68 — Hotel intent detection from raw query
    if HOTEL_BRIDGE_ENABLED and req.query and detect_hotel_intent(req.query):
        log.info(f"[{request_id[:8]}] Hotel intent detected → routing to Hotel Bridge")
        hotel_details = extract_hotel_details(req.query)

        # §70 I-TRAVEL-2: Se destino não detectado, MARIA pergunta (não assume)
        if hotel_details.get("destination_missing") or not hotel_details.get("destination"):
            log.info(f"[{request_id[:8]}] Hotel destination missing → MARIA asks user")
            ask_msg = MARIA_ASK_DESTINATION["hotel"].get(lang, MARIA_ASK_DESTINATION["hotel"]["EN"])
            return PlanResponse(
                request_id=request_id,
                decision=PlaceResult(
                    name="Cidade necessária",
                    type="hotel_question",
                    distance_text="",
                    queue_status="",
                    reason=ask_msg,
                ),
                context={"weather": ctx.get("weather", ""), "needs_destination": True},
                maria_voice=MariaVoice(
                    PT=ask_msg if lang == "PT" else "",
                    DE=ask_msg if lang == "DE" else "",
                    EN=ask_msg if lang == "EN" else "",
                ),
                intent_parsed={"type": "hotel", "needs_destination": True},
                ledger_receipt_id=None,
                cost_eur=0.0,
                sovereign_mode=False,
                memory_active=memory_active,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        hotels_data = await search_hotels(
            destination=hotel_details["destination"],
            check_in=hotel_details["check_in"],
            check_out=hotel_details["check_out"],
            adults=hotel_details["adults"],
            lang=lang,
        )

        maria_text = format_maria_hotel_response(hotels_data, lang)
        sovereign_mode = hotels_data.get("source") == "demo"

        # Seal to Ledger
        seal_payload = {
            "request_id": request_id,
            "destination": hotels_data.get("destination"),
            "check_in": hotel_details["check_in"],
            "check_out": hotel_details["check_out"],
            "nights": hotel_details["nights"],
            "hotels_count": len(hotels_data.get("hotels", [])),
            "sovereign_mode": sovereign_mode,
            "source": hotels_data.get("source", "hotellook.com"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        receipt_id = await seal_decision(request_id, seal_payload, req.wallet_id)

        best_hotel = hotels_data.get("hotels", [{}])[0] if hotels_data.get("hotels") else {}

        return PlanResponse(
            request_id=request_id,
            decision=PlaceResult(
                name=best_hotel.get("name", "Hotel"),
                type="hotel",
                distance_text=f"{hotel_details['nights']} noites",
                queue_status=f"€{best_hotel.get('price_total', '?')}",
                reason=maria_text[:200],
                rating=best_hotel.get("rating"),
                open_now=None,
            ),
            context={
                "weather": ctx.get("weather", ""),
                "hotels": hotels_data.get("hotels", []),
                "destination": hotels_data.get("destination"),
                "check_in": hotel_details["check_in"],
                "check_out": hotel_details["check_out"],
                "nights": hotel_details["nights"],
                "source": hotels_data.get("source", "hotellook.com"),
            },
            maria_voice=MariaVoice(
                PT=maria_text if lang == "PT" else "",
                DE=maria_text if lang == "DE" else "",
                EN=maria_text if lang == "EN" else "",
            ),
            intent_parsed={"type": "hotel", "detected_from_query": True},
            ledger_receipt_id=receipt_id,
            cost_eur=0.0,
            sovereign_mode=sovereign_mode,
            memory_active=memory_active,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # 1e. §65 + §91 — Special handling for greeting intent with Small Talk
    #     For greetings, use the requested language (not stored preference)
    #     §91: Memory informs behavior, not output. Pass hour for contextual greeting.
    if req.intent.type == "greeting":
        greeting_lang = req.lang if req.lang in ("PT", "DE", "EN") else "EN"
        current_hour = datetime.now().hour
        greeting_text = gerar_saudacao(did, greeting_lang, weather=ctx.get("weather"), hour=current_hour) if did else {
            "PT": "Bom dia, viajante",
            "DE": "Guten Tag, Reisender",
            "EN": "Good day, traveller"
        }.get(lang, "Good day, traveller")

        total_visits = get_total_interactions(did) if did else 0

        return PlanResponse(
            request_id=request_id,
            decision=PlaceResult(
                name="Greeting",
                type="greeting",
                distance_text="",
                queue_status="",
                reason=greeting_text,
            ),
            context={
                "weather": ctx.get("weather", ""),
                "greeting": greeting_text,
                "total_visits": total_visits,
            },
            maria_voice=MariaVoice(
                PT=greeting_text if greeting_lang == "PT" else "",
                DE=greeting_text if greeting_lang == "DE" else "",
                EN=greeting_text if greeting_lang == "EN" else "",
            ),
            intent_parsed=req.intent.model_dump(),
            ledger_receipt_id=None,  # Greetings not sealed
            cost_eur=0.0,
            sovereign_mode=False,
            memory_active=memory_active,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # 1f. §90 — Onboarding intent: MARIA introduces herself
    #     When user asks "who are you?" or "what do you do?"
    if req.intent.type == "onboarding":
        log.info(f"[{request_id[:8]}] Onboarding intent → MARIA identity")
        total_visits = get_total_interactions(did) if did else 0

        # §90 — MARIA Identity: consciousness, not features
        # "Rigor por dentro, gentileza por fora."
        onboarding_text = {
            "PT": f"Sou a Maria — cuido das tuas decisões de viagem com a mesma atenção que darias às tuas memórias. "
                  f"Não te mostro listas. Decido por ti, e tu confirmas. "
                  f"{'Já nos conhecemos ' + str(total_visits) + ' vezes.' if total_visits > 0 else 'É a nossa primeira conversa.'} "
                  f"Experimenta: diz-me onde estás e o que precisas.",
            "DE": f"Ich bin Maria — ich kümmere mich um deine Reiseentscheidungen mit derselben Aufmerksamkeit, die du deinen Erinnerungen widmen würdest. "
                  f"Ich zeige dir keine Listen. Ich entscheide, und du bestätigst. "
                  f"{'Wir kennen uns schon ' + str(total_visits) + ' Mal.' if total_visits > 0 else 'Das ist unser erstes Gespräch.'} "
                  f"Probier es aus: sag mir, wo du bist und was du brauchst.",
            "EN": f"I am Maria — I take care of your travel decisions with the same attention you would give to your memories. "
                  f"I do not show you lists. I decide, and you confirm. "
                  f"{'We have met ' + str(total_visits) + ' times already.' if total_visits > 0 else 'This is our first conversation.'} "
                  f"Try it: tell me where you are and what you need.",
        }

        intro = onboarding_text.get(lang, onboarding_text["EN"])

        return PlanResponse(
            request_id=request_id,
            decision=PlaceResult(
                name="Maria" if lang != "DE" else "Maria",
                type="onboarding",
                distance_text="",
                queue_status="Companion" if lang == "EN" else ("Companheira" if lang == "PT" else "Begleiterin"),
                reason=intro,
            ),
            context={
                "weather": ctx.get("weather", ""),
                "total_visits": total_visits,
                "onboarding": True,
            },
            maria_voice=MariaVoice(
                PT=onboarding_text["PT"] if lang == "PT" else "",
                DE=onboarding_text["DE"] if lang == "DE" else "",
                EN=onboarding_text["EN"] if lang == "EN" else "",
            ),
            intent_parsed=req.intent.model_dump(),
            ledger_receipt_id=None,  # Onboarding not sealed (nothing to seal)
            cost_eur=0.0,
            sovereign_mode=False,
            memory_active=memory_active,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # 1f.5 §145.2/§145.3 — Weather intent: resposta directa, sem turismo
    #       Weather questions get simple, direct answers from context
    #       §145.3: Expanded to cover all weather terms removed from CULTURE_KEYWORDS
    WEATHER_KEYWORDS = [
        # PT — temperatura, clima, previsão
        "temperatura", "tempo está", "qual o tempo", "como está o tempo",
        "clima", "quantos graus", "vai chover", "está frio", "está calor",
        "previsão", "meteorologia", "chover", "sol", "chuva", "nublado",
        # DE — Wetter, Temperatur, Vorhersage
        "temperatur", "wetter", "grad", "regnet", "wie ist das wetter",
        "vorhersage", "kalt", "warm", "sonne", "regen", "bewölkt",
        # EN — weather, temperature, forecast
        "temperature", "weather", "degrees", "raining", "what's the weather",
        "forecast", "cold", "hot", "sunny", "rain", "cloudy",
    ]
    if req.query and any(kw in req.query.lower() for kw in WEATHER_KEYWORDS):
        log.info(f"[{request_id[:8]}] Weather intent detected → direct response")
        weather_info = ctx.get("weather", "informação não disponível")

        weather_templates = {
            "PT": f"Neste momento: {weather_info}.",
            "DE": f"Aktuell: {weather_info}.",
            "EN": f"Currently: {weather_info}."
        }
        maria_text = weather_templates.get(lang, weather_templates["EN"])

        return PlanResponse(
            request_id=request_id,
            decision=PlaceResult(
                name="Clima" if lang == "PT" else ("Wetter" if lang == "DE" else "Weather"),
                type="weather",
                distance_text="",
                queue_status="",
                reason=maria_text,
            ),
            context={"weather": weather_info},
            maria_voice=MariaVoice(
                PT=maria_text if lang == "PT" else "",
                DE=maria_text if lang == "DE" else "",
                EN=maria_text if lang == "EN" else "",
            ),
            intent_parsed={"type": "weather"},
            ledger_receipt_id=None,  # Weather not sealed
            cost_eur=0.0,
            sovereign_mode=False,
            memory_active=memory_active,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # 1g. §69 — Culture/Tips intent detection
    #     Practical travel questions → MARIA responds directly via LLM
    if req.query and detect_culture_intent(req.query):
        log.info(f"[{request_id[:8]}] Culture intent detected → MARIA direct response")

        # Call LLM Gateway for cultural/practical advice
        llm_result = await call_gateway_llm(
            intent={"type": "culture", "raw_input": req.query},
            ctx=ctx,
            lang=lang,
        )

        if llm_result:
            maria_text = llm_result.get("reason", "")
        else:
            # Fallback: pre-built culture tips
            culture_fallback = {
                "PT": "Como companheira de viagem, recomendo que consultes fontes locais para informações práticas. Cada destino tem as suas particularidades!",
                "DE": "Als Reisebegleiterin empfehle ich dir, lokale Quellen für praktische Informationen zu konsultieren. Jedes Reiseziel hat seine Besonderheiten!",
                "EN": "As your travel companion, I recommend checking local sources for practical information. Every destination has its own quirks!",
            }
            maria_text = culture_fallback.get(lang, culture_fallback["EN"])

        # Seal to Ledger
        seal_payload = {
            "request_id": request_id,
            "intent_type": "culture",
            "query_preview": req.query[:100] if req.query else "",
            "lang": lang,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        receipt_id = await seal_decision(request_id, seal_payload, req.wallet_id)

        return PlanResponse(
            request_id=request_id,
            decision=PlaceResult(
                name="Dica de Viagem" if lang == "PT" else ("Reisetipp" if lang == "DE" else "Travel Tip"),
                type="culture",
                distance_text="",
                queue_status="",
                reason=maria_text[:200],
            ),
            context={
                "weather": ctx.get("weather", ""),
                "culture_advice": maria_text,
            },
            maria_voice=MariaVoice(
                PT=maria_text if lang == "PT" else "",
                DE=maria_text if lang == "DE" else "",
                EN=maria_text if lang == "EN" else "",
            ),
            intent_parsed={"type": "culture", "detected_from_query": True},
            ledger_receipt_id=receipt_id,
            cost_eur=0.0,
            sovereign_mode=llm_result is None,
            memory_active=memory_active,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # 1g. §69b — Query-based place type override
    #     Frontend may send wrong intent; detect true intent from query
    query_detected_type = detect_place_type_from_query(req.query) if req.query else None
    intent_type_lower = req.intent.type.lower() if req.intent.type else ""

    # Override frontend intent if query clearly indicates different place type
    if query_detected_type and query_detected_type != intent_type_lower:
        log.info(f"[{request_id[:8]}] Intent override: frontend='{intent_type_lower}' → query='{query_detected_type}'")
        intent_type_lower = query_detected_type
        # Update intent for Places search
        req.intent.type = query_detected_type

    place_type_match = intent_type_lower in PLACE_TYPE_MAP

    # 2. Places — Google Places via Sovereignty Gate (cache-first)
    candidates = []
    places_cache_hit = False
    if req.lat and req.lng and place_type_match:
        candidates, places_cache_hit = await search_places(
            req.intent, lat, lng, lang,
            tier="TRAVEL",  # Travel users get premium access
            actor=did or "anonymous"
        )

    if not candidates:
        # §69 — Plan B: MARIA as general_companion
        #       If no place type match OR no Places results → LLM direct response
        is_general_companion = not place_type_match

        if is_general_companion:
            log.info(f"[{request_id[:8]}] General companion mode → no place type match")

        # Try LLM via Gateway
        # §72: Always pass raw_input for Pulse Reading
        intent_dict = req.intent.model_dump() if place_type_match else {"type": "general"}
        intent_dict["raw_input"] = req.query or req.intent.type  # §72 Pulse needs this

        llm_result = await call_gateway_llm(
            intent=intent_dict,
            ctx=ctx,
            lang=lang
        )

        if llm_result:
            # LLM responded — use its recommendation
            sovereign_mode = False
            provider_used = llm_result.get("provider", "gemini")
            llm_text = llm_result.get("reason", "")

            if is_general_companion:
                queue_txt = {"PT": "MARIA companheira", "DE": "MARIA Begleiterin", "EN": "MARIA companion"}[lang]
                decision_name = {"PT": "Resposta MARIA", "DE": "MARIA Antwort", "EN": "MARIA Response"}[lang]
            else:
                queue_txt = {"PT": "Recomendação IA", "DE": "KI-Empfehlung", "EN": "AI recommendation"}[lang]
                decision_name = llm_result.get("name", "Recomendação MARIA")

            decision = PlaceResult(
                name=decision_name,
                type="general_companion" if is_general_companion else req.intent.type,
                distance_text="",
                queue_status=queue_txt,
                reason=llm_text[:200],
                open_now=None,
            )
            # LLM responds in requested language — assign correctly
            voice = MariaVoice(
                PT=llm_text if lang == "PT" else "",
                DE=llm_text if lang == "DE" else "",
                EN=llm_text if lang == "EN" else "",
            )
        else:
            # I10: Ultimate fallback — friendly "I don't know" instead of robotic
            sovereign_mode = True

            if is_general_companion:
                # General companion: warm fallback
                fallback_voice = {
                    "PT": "Não tenho certeza sobre isso, mas posso ajudar-te com voos, hotéis, restaurantes ou dicas de viagem. O que precisas?",
                    "DE": "Da bin ich mir nicht sicher, aber ich kann dir bei Flügen, Hotels, Restaurants oder Reisetipps helfen. Was brauchst du?",
                    "EN": "I'm not sure about that, but I can help with flights, hotels, restaurants or travel tips. What do you need?",
                }
                decision = PlaceResult(
                    name={"PT": "MARIA", "DE": "MARIA", "EN": "MARIA"}[lang],
                    type="general_companion",
                    distance_text="",
                    queue_status={"PT": "Companheira", "DE": "Begleiterin", "EN": "Companion"}[lang],
                    reason=fallback_voice[lang][:100],
                    open_now=None,
                )
                voice = MariaVoice(
                    PT=fallback_voice["PT"] if lang == "PT" else "",
                    DE=fallback_voice["DE"] if lang == "DE" else "",
                    EN=fallback_voice["EN"] if lang == "EN" else "",
                )
            else:
                # Place type matched but no results — use old sovereign fallback
                fb = SOVEREIGN_FALLBACK.get(req.intent.type, SOVEREIGN_FALLBACK["restaurant"])
                queue_txt = {"PT": "Sem dados", "DE": "Keine Daten", "EN": "No data"}[lang]
                reason_txt = {"PT": "Modo soberano", "DE": "Souveräner Modus", "EN": "Sovereign mode"}[lang]
                decision = PlaceResult(
                    name=fb["name"], type=req.intent.type,
                    distance_text="?", queue_status=queue_txt,
                    reason=reason_txt, open_now=None,
                )
                voice = MariaVoice(
                    PT=f"Estou em modo soberano. Recomendo explorar {fb['name']} na sua área.",
                    DE=f"Souveräner Modus. Ich empfehle {fb['name']} in Ihrer Nähe.",
                    EN=f"Sovereign mode. I suggest checking {fb['name']} nearby.",
                )
    else:
        # 3. Score & pick best
        # §104.1: Load travel preferences for personalized scoring
        travel_prefs = get_travel_preferences(did) if did else None
        scored = sorted(candidates, key=lambda p: score_place(p, req.intent, ctx, travel_prefs), reverse=True)
        best = scored[0]
        dist_txt = {"PT": "próximo", "DE": "in der Nähe", "EN": "nearby"}[lang]
        queue_txt = (
            {"PT": "Aberto agora", "DE": "Jetzt geöffnet", "EN": "Open now"}[lang]
            if best.get("open_now") else
            {"PT": "Verifique horário", "DE": "Öffnungszeiten prüfen", "EN": "Check opening hours"}[lang]
        )
        reason = build_reason(best, req.intent, ctx, lang)

        # §105 — Generate explanation
        explanation = generate_explanation(
            entity={"type": req.intent.type, "type_group": _classify_place_type_group(req.intent.type), **best},
            entity_type="place",
            prefs=travel_prefs or {},
            context=ctx,
            lang=lang
        )

        decision = PlaceResult(
            name=best["name"], type=req.intent.type,
            distance_text=dist_txt, queue_status=queue_txt,
            reason=f"{reason} {explanation}" if reason else explanation,
            google_place_id=best.get("place_id"),
            address=best.get("address"), rating=best.get("rating"),
            open_now=best.get("open_now"),
        )
        # §145 — voice was missing in this branch (fixed 06 Apr 2026)
        voice = MariaVoice(
            PT=decision.reason if lang == "PT" else "",
            DE=decision.reason if lang == "DE" else "",
            EN=decision.reason if lang == "EN" else "",
        )

    # 4. Ledger seal (I11) — non-blocking
    seal_payload = {
        "request_id": request_id,
        "place": decision.name,
        "type": req.intent.type,
        "queue": decision.queue_status,
        "context": {k: v for k, v in ctx.items() if k not in ("lat", "lng")},  # I1: no coords
        "lang": lang,
        "sovereign_mode": sovereign_mode,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    receipt_id = await seal_decision(request_id, seal_payload, req.wallet_id)

    elapsed = round((time.time() - t0) * 1000)
    log.info(f"[{request_id[:8]}] plan OK · {decision.name} · {elapsed}ms · sovereign={sovereign_mode}")

    # 5. Memory — log interaction for future personalization
    if MEMORY_ENABLED and did:
        log_interaction(
            did=did,
            request_id=request_id,
            intent_type=req.intent.type,
            place_name=decision.name,
        )

    # §79 — Build locations for Super Carta map
    locations = None
    if candidates:
        locations = [
            PlaceLocation(
                name=p.get("name", ""),
                type=req.intent.type,
                lat=p.get("lat", 0),
                lng=p.get("lng", 0),
                rating=p.get("rating"),
                address=p.get("address"),
                open_now=p.get("open_now"),
            )
            for p in candidates
            if p.get("lat") and p.get("lng")  # Only include places with coordinates
        ]
        log.info(f"[{request_id[:8]}] Super Carta: {len(locations)} locations for map")

    # §108 — Memória Visível (mostrar o que Maria sabe)
    visible_mem = None
    if MEMORY_ENGINE_ENABLED and did and 'travel_prefs' in dir():
        travel_prefs_for_memory = get_travel_preferences(did) if did else None
        if travel_prefs_for_memory and should_show_memory(travel_prefs_for_memory):
            visible_mem = get_visible_memory(travel_prefs_for_memory, lang)

    return PlanResponse(
        request_id=request_id,
        decision=decision,
        context={k: v for k, v in ctx.items() if k not in ("lat", "lng", "nomada")},
        maria_voice=voice,
        intent_parsed=req.intent.model_dump(),
        ledger_receipt_id=receipt_id,
        cost_eur=0.0,  # Google Places free tier; ElevenLabs billed separately
        sovereign_mode=sovereign_mode,
        memory_active=memory_active,
        timestamp=datetime.now(timezone.utc).isoformat(),
        locations=locations,  # §79 Super Carta map pins
        visible_memory=visible_mem,  # §108 Memória Visível
    )


# ══════════════════════════════════════════════════════════════════════════════
# §79 — Super Carta Demo Endpoint (for testing map)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/demo-carta")
async def demo_super_carta():
    """
    Demo endpoint with mock locations for testing Super Carta map.
    Use in dev: fetch('/travel/maria/demo-carta')
    """
    return PlanResponse(
        request_id="demo-carta-001",
        decision=PlaceResult(
            name="Café Einstein",
            type="cafe",
            distance_text="5 min walk",
            queue_status="Calm now",
            reason="Demo location for Super Carta testing · Multiple cafés in Kempten",
            rating=4.5,
            open_now=True,
        ),
        context={"weather": "☀️ 12°C", "city": "Kempten", "demo": True},
        maria_voice=MariaVoice(
            PT="Há bons cafés por aqui. O Einstein é o mais tranquilo.",
            DE="Ich habe drei Cafés in deiner Nähe gefunden. Das Einstein ist am ruhigsten.",
            EN="I found three cafés near you. Einstein is the quietest one.",
        ),
        intent_parsed={"type": "cafe", "demo": True},
        ledger_receipt_id="DEMO-CARTA-001",
        cost_eur=0.0,
        sovereign_mode=False,
        memory_active=False,
        timestamp=datetime.now(timezone.utc).isoformat(),
        locations=[
            PlaceLocation(name="Café Einstein", type="cafe", lat=47.7267, lng=10.3159, rating=4.5, open_now=True, address="Rathausplatz 12"),
            PlaceLocation(name="Starbucks", type="cafe", lat=47.7255, lng=10.3165, rating=4.2, open_now=True, address="Bahnhofstraße 8"),
            PlaceLocation(name="Café Rösterei", type="cafe", lat=47.7280, lng=10.3180, rating=4.7, open_now=False, address="Klostersteige 5"),
        ],
    )


# ══════════════════════════════════════════════════════════════════════════════
# §102 — WhereAmI Geo Auto-Detection
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/location")
async def maria_location(request: Request, lang: str = "en"):
    """
    WhereAmI — detecta cidade do utilizador via IP para pré-popular fly_from.

    Travelpayouts WhereAmI API — sem key especial.
    Frontend chama ao iniciar → pré-popula fly_from + MARIA greeting contextual.

    §102 WINDI-TRAVEL · IP1 intacto (apenas detecção, sem booking).
    §110 FIX: Usar idioma do frontend, não país do IP (I12 compliance).
    """
    # Extrair IP real (nginx passa via X-Real-IP ou X-Forwarded-For)
    ip = (
        request.headers.get("X-Real-IP")
        or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or None
    )

    # Detectar localização via Travelpayouts
    if WHEREAMI_ENABLED:
        loc = await get_user_location(ip=ip, locale="pt")
    else:
        loc = {
            "iata": "MUC",
            "name": "Munique",
            "country_code": "DE",
            "detected": False,
            "source": "fallback_bridge_disabled"
        }

    # §110 FIX: Greeting trilíngue baseado no idioma do FRONTEND (I12 Language Sovereign)
    # Não usar país do IP — usar idioma selecionado pelo utilizador
    lang_upper = lang.upper()
    greetings = {
        "DE": f"Du bist in {loc['name']}. Wohin möchtest du fliegen?",
        "PT": f"Estás em {loc['name']}. Para onde queres voar?",
        "EN": f"You're in {loc['name']}. Where do you want to fly?",
    }
    greeting = greetings.get(lang_upper, greetings["EN"])

    log.info(f"[WhereAmI §102] {loc['iata']} ({loc['name']}) — detected={loc.get('detected', False)}")

    return {
        "iata": loc["iata"],
        "city": loc["name"],
        "country_code": loc.get("country_code", ""),
        "greeting": greeting,
        "fly_from": loc["iata"],
        "detected": loc.get("detected", False),
        "source": loc.get("source", "unknown"),
    }


# ══════════════════════════════════════════════════════════════════════════════
# §92 — MARIA Brain Endpoint (LLM live substitui regex)
# ══════════════════════════════════════════════════════════════════════════════

class ThinkRequest(BaseModel):
    """Request for MARIA brain (LLM-powered response)."""
    message: str = Field(..., description="User message", max_length=500)
    lang: str = Field(default="PT", description="Language: PT, DE, EN")
    did: Optional[str] = Field(default=None, description="User DID")
    weather: Optional[str] = Field(default=None, description="Weather context")
    lat: Optional[float] = Field(default=None, description="User latitude")
    lng: Optional[float] = Field(default=None, description="User longitude")
    history: Optional[list] = Field(default=[], description="F14 Conversation history")


@router.post("/think")
async def maria_think_endpoint(req: ThinkRequest):
    """
    §96 — MARIA Decision Router: Decide ANTES de falar.

    "MARIA deixou de responder. Começou a agir."

    Pipeline (P5):
        1. Detectar intent (flight/hotel/places/culture)
        2. Se actionable → chamar bridge → retornar dados
        3. Se conversacional → LLM → resposta generativa

    Transforms MARIA from "feature system" to "decision system".
    """
    user_input = req.message

    # ═══════════════════════════════════════════════════════════════════════════
    # §100 — ANTECIPAÇÃO (antes do routing normal)
    # "Eu não decido por ti. Mas não te deixo decidir tarde demais."
    # ═══════════════════════════════════════════════════════════════════════════

    if ANTICIPATION_ENABLED and req.did:
        # Carregar contexto e padrões
        live_context = get_live_context(user_input, req.lat, req.lng)
        patterns = detect_travel_patterns(req.did)

        # Verificar se devemos antecipar
        anticipation = should_anticipate(req.did, live_context, patterns)

        if anticipation.get("should_suggest") and anticipation.get("confidence", 0) > 0.5:
            # Gerar mensagem de antecipação (sem executar — I9)
            suggestion = generate_anticipation_message(
                anticipation["suggestion_type"],
                patterns,
                live_context,
                req.lang
            )

            # Se o input é genérico (saudação, "olá", etc.) e temos sugestão
            generic_inputs = ["ola", "olá", "hallo", "hello", "hi", "oi", "bom dia", "guten tag", "good morning"]
            if any(user_input.lower().strip() in g for g in generic_inputs):
                log.info(f"[MARIA §100] Anticipation triggered: {anticipation['suggestion_type']}")
                return {
                    "type": "anticipation",
                    "mode": "nomada_v2",
                    "response": suggestion["full_text"],
                    "suggestion": suggestion,
                    "patterns": {
                        "common_routes": patterns.get("common_routes", []),
                        "trip_frequency": patterns.get("trip_frequency"),
                    },
                    "requires_approval": True,  # I9 — sempre
                    "lang": req.lang
                }

    # ═══════════════════════════════════════════════════════════════════════════
    # §96 — DECISION ROUTING (antes do LLM)
    # "MARIA deve decidir antes de falar."
    # ═══════════════════════════════════════════════════════════════════════════

    # ✈️ FLIGHT INTENT
    if KIWI_BRIDGE_ENABLED and detect_flight_intent(user_input):
        log.info(f"[MARIA §96] Flight intent detected: {user_input[:50]}...")
        details = extract_flight_details(user_input)

        # Se não tem destino, pedir ao utilizador
        # Nota: extract_flight_details retorna fly_to, não destination
        fly_to = details.get("fly_to")
        if not fly_to or details.get("destination_missing"):
            ask_dest = MARIA_ASK_DESTINATION["flight"].get(req.lang, MARIA_ASK_DESTINATION["flight"]["EN"])
            return {
                "type": "clarification",
                "intent": "flight",
                "response": ask_dest,
                "needs": ["destination"],
                "lang": req.lang
            }

        # Buscar voos — NUNCA cair no LLM se intent é flight
        try:
            result = await search_flights(
                fly_from=details.get("fly_from", "MUC"),
                fly_to=fly_to,
                date_from=details.get("date", (datetime.now() + timedelta(days=7)).strftime("%d/%m/%Y")),
                currency="EUR",
                adults=1,
                max_results=3
            )

            # search_flights retorna {"flights": [...], "origin": ..., "destination": ...}
            flight_list = result.get("flights", [])

            if flight_list:
                # §100.5 — MODO NÓMADA v1.3: Decisão + Memory Engine
                # Carregar preferências com learning (§100.5 > §98)
                travel_prefs = get_enhanced_travel_preferences(req.did) if req.did and MEMORY_ENGINE_ENABLED else (
                    get_travel_preferences(req.did) if req.did else None
                )

                # §99: Carregar contexto vivo (estado atual)
                live_context = get_live_context(user_input, req.lat, req.lng)

                # Detectar preferência de horário do user input (override explícito)
                preferred_time = "morning"  # default
                if any(w in user_input.lower() for w in ["tarde", "nachmittag", "afternoon"]):
                    preferred_time = "afternoon"
                elif any(w in user_input.lower() for w in ["noite", "abend", "evening", "night"]):
                    preferred_time = "evening"

                # §104 — Score com preferências evoluíveis + contexto vivo
                def score_with_context(f):
                    # Contexto agora integrado no score_flight
                    return score_flight(f, preferred_time, travel_prefs, live_context)

                best_flight = max(flight_list, key=score_with_context)
                alternatives = [f for f in flight_list if f != best_flight][:2]

                # Gerar explicação humana
                voice = explain_flight_decision(best_flight, req.lang)

                # §98: Adicionar explicação personalizada se temos DID
                if req.did and travel_prefs:
                    personal_reason = explain_personalized_decision("flight", travel_prefs, req.lang)
                    if personal_reason:
                        voice = f"{voice} {personal_reason}"

                # §99: Adicionar contexto vivo à explicação
                context_reason = explain_context(live_context, req.lang)
                if context_reason:
                    voice = f"{context_reason} {voice}"

                # §105 — Explicação unificada (complementa)
                explanation_105 = generate_explanation(
                    entity=best_flight,
                    entity_type="flight",
                    prefs=travel_prefs or {},
                    context=live_context,
                    lang=req.lang
                )
                voice = f"{voice} {explanation_105}"

                # §100.5: Save decision to Memory Engine
                decision_id = None
                origin = result.get("origin", details.get("fly_from", "MUC"))
                destination = result.get("destination", fly_to)
                if req.did and MEMORY_ENGINE_ENABLED:
                    decision_id = save_decision(
                        did=req.did,
                        decision_type="flight",
                        decision=best_flight,
                        context=live_context,
                        route=f"{origin}→{destination}",
                        destination=destination
                    )

                # §108 — Memória Visível
                visible_mem = get_visible_memory(travel_prefs, req.lang) if travel_prefs and should_show_memory(travel_prefs) else None

                # §107 — Thread Visual Timeline
                thread_id = None
                if req.did and THREAD_ENABLED:
                    thread = get_active_thread(req.did, destination)
                    if thread:
                        thread_id = thread["id"]
                        add_thread_entry(thread_id, "request", user_input)
                        add_thread_entry(thread_id, "decision", voice, {"type": "flight", "price": best_flight.get("price")})
                        if visible_mem:
                            for mem in visible_mem[:2]:
                                add_thread_entry(thread_id, "memory", mem)

                return {
                    "type": "flight",
                    "intent": "flight",
                    "response": voice,
                    "decision": best_flight,  # §97: A MELHOR opção
                    "decision_id": decision_id,  # §100.5: Para feedback
                    "alternatives": alternatives,  # Opcionais, não como escolha
                    "data": flight_list[:3],  # Backwards compat
                    "origin": origin,
                    "destination": destination,
                    "lang": req.lang,
                    "source": "kiwi.com",
                    "mode": "nomada_v1.3",  # §100.5: Memory Engine
                    "personalized": bool(req.did and travel_prefs),
                    "context_aware": bool(live_context.get("time_pressure") != "normal" or live_context.get("mode") != "normal"),
                    "live_context": {
                        "time_pressure": live_context.get("time_pressure"),
                        "mode": live_context.get("mode")
                    },
                    "visible_memory": visible_mem,  # §108
                    "thread_id": thread_id  # §107
                }
            else:
                # Sem resultados — mas intent permanece flight
                no_flights_msg = {
                    "PT": f"Não há voos directos para {fly_to} disponíveis agora. Tenta uma data diferente ou outro destino.",
                    "DE": f"Ich habe keine Direktflüge nach {fly_to} gefunden. Versuche ein anderes Datum oder Ziel.",
                    "EN": f"No direct flights to {fly_to} found. Try a different date or destination."
                }
                return {
                    "type": "flight",
                    "intent": "flight",
                    "response": no_flights_msg.get(req.lang, no_flights_msg["EN"]),
                    "data": [],
                    "destination": fly_to,
                    "lang": req.lang,
                    "source": "kiwi.com"
                }
        except Exception as e:
            log.error(f"[MARIA §96] Flight search error: {e}")
            # ⚠️ Erro não muda a natureza da decisão — NUNCA chamar LLM aqui
            error_msg = {
                "PT": "Tive um problema a aceder aos voos. Tenta novamente em alguns segundos.",
                "DE": "Es gab ein Problem beim Zugriff auf Flüge. Versuche es in einigen Sekunden erneut.",
                "EN": "Had a problem accessing flights. Try again in a few seconds."
            }
            return {
                "type": "flight_error",
                "intent": "flight",
                "response": error_msg.get(req.lang, error_msg["EN"]),
                "error": str(e),
                "lang": req.lang
            }

    # 🏨 HOTEL INTENT
    if HOTEL_BRIDGE_ENABLED and detect_hotel_intent(user_input):
        log.info(f"[MARIA §96] Hotel intent detected: {user_input[:50]}...")
        details = extract_hotel_details(user_input)

        # Se não tem destino, pedir ao utilizador
        if not details.get("destination"):
            ask_dest = MARIA_ASK_DESTINATION["hotel"].get(req.lang, MARIA_ASK_DESTINATION["hotel"]["EN"])
            return {
                "type": "clarification",
                "intent": "hotel",
                "response": ask_dest,
                "needs": ["destination"],
                "lang": req.lang
            }

        # Buscar hotéis — NUNCA cair no LLM se intent é hotel
        try:
            result = await search_hotels(
                destination=details["destination"],
                check_in=details.get("check_in", (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")),
                check_out=details.get("check_out", (datetime.now() + timedelta(days=9)).strftime("%Y-%m-%d")),
                adults=details.get("adults", 2),
                currency="EUR",
                max_results=3
            )

            # search_hotels retorna {"hotels": [...], "destination": ..., ...}
            hotel_list = result.get("hotels", [])

            if hotel_list:
                # §100.5 — MODO NÓMADA v1.3: Decisão + Memory Engine
                travel_prefs = get_enhanced_travel_preferences(req.did) if req.did and MEMORY_ENGINE_ENABLED else (
                    get_travel_preferences(req.did) if req.did else None
                )

                # §99: Carregar contexto vivo (estado atual)
                live_context = get_live_context(user_input, req.lat, req.lng)

                best_hotel = max(hotel_list, key=lambda h: score_hotel(h, travel_prefs, live_context))
                alternatives = [h for h in hotel_list if h != best_hotel][:2]

                # Gerar explicação humana
                voice = explain_hotel_decision(best_hotel, req.lang)

                # §98: Adicionar explicação personalizada se temos DID
                if req.did and travel_prefs:
                    personal_reason = explain_personalized_decision("hotel", travel_prefs, req.lang)
                    if personal_reason:
                        voice = f"{voice} {personal_reason}"

                # §105 — Explicação unificada (complementa)
                explanation_105 = generate_explanation(
                    entity=best_hotel,
                    entity_type="hotel",
                    prefs=travel_prefs or {},
                    context=live_context,
                    lang=req.lang
                )
                voice = f"{voice} {explanation_105}"

                # §100.5: Save decision to Memory Engine
                decision_id = None
                destination = result.get("destination", details["destination"])
                if req.did and MEMORY_ENGINE_ENABLED:
                    decision_id = save_decision(
                        did=req.did,
                        decision_type="hotel",
                        decision=best_hotel,
                        context=live_context,
                        destination=destination
                    )

                # §108 — Memória Visível
                visible_mem = get_visible_memory(travel_prefs, req.lang) if travel_prefs and should_show_memory(travel_prefs) else None

                # §107 — Thread Visual Timeline
                thread_id = None
                if req.did and THREAD_ENABLED:
                    thread = get_active_thread(req.did, destination)
                    if thread:
                        thread_id = thread["id"]
                        add_thread_entry(thread_id, "request", user_input)
                        add_thread_entry(thread_id, "decision", voice, {"type": "hotel", "price": best_hotel.get("price")})
                        if visible_mem:
                            for mem in visible_mem[:2]:
                                add_thread_entry(thread_id, "memory", mem)

                return {
                    "type": "hotel",
                    "intent": "hotel",
                    "response": voice,
                    "decision": best_hotel,  # §97: A MELHOR opção
                    "decision_id": decision_id,  # §100.5: Para feedback
                    "alternatives": alternatives,  # Opcionais, não como escolha
                    "data": hotel_list[:3],  # Backwards compat
                    "destination": destination,
                    "lang": req.lang,
                    "source": "hotellook.com",
                    "mode": "nomada_v1.3",  # §100.5: Memory Engine
                    "personalized": bool(req.did and travel_prefs),
                    "context_aware": bool(live_context.get("time_pressure") != "normal" or live_context.get("mode") != "normal"),
                    "live_context": {
                        "time_pressure": live_context.get("time_pressure"),
                        "mode": live_context.get("mode")
                    },
                    "visible_memory": visible_mem,  # §108
                    "thread_id": thread_id  # §107
                }
            else:
                # Sem resultados — mas intent permanece hotel
                dest = details["destination"]
                no_hotels_msg = {
                    "PT": f"Não há hotéis disponíveis em {dest} para essas datas. Tenta outras datas.",
                    "DE": f"Keine verfügbaren Hotels in {dest} für diese Daten gefunden. Versuche andere Daten.",
                    "EN": f"No hotels available in {dest} for these dates. Try different dates."
                }
                return {
                    "type": "hotel",
                    "intent": "hotel",
                    "response": no_hotels_msg.get(req.lang, no_hotels_msg["EN"]),
                    "data": [],
                    "destination": dest,
                    "lang": req.lang,
                    "source": "hotellook.com"
                }
        except Exception as e:
            log.error(f"[MARIA §96] Hotel search error: {e}")
            # ⚠️ Erro não muda a natureza da decisão — NUNCA chamar LLM aqui
            error_msg = {
                "PT": "Tive um problema a aceder aos hotéis. Tenta novamente em alguns segundos.",
                "DE": "Es gab ein Problem beim Zugriff auf Hotels. Versuche es in einigen Sekunden erneut.",
                "EN": "Had a problem accessing hotels. Try again in a few seconds."
            }
            return {
                "type": "hotel_error",
                "intent": "hotel",
                "response": error_msg.get(req.lang, error_msg["EN"]),
                "error": str(e),
                "lang": req.lang
            }

    # 🎭 CULTURE/TIPS INTENT (responder com LLM especializado)
    if detect_culture_intent(user_input):
        log.info(f"[MARIA §96] Culture intent detected: {user_input[:50]}...")
        # Cai para o LLM mas com intent marcado
        pass  # Continua para LLM abaixo, mas com intent="culture"

    # 📍 PLACES INTENT (detectar tipo de lugar) — NUNCA cair no LLM se intent é places
    place_type = detect_place_type_from_query(user_input)
    if place_type and req.lat and req.lng and PLACES_GATE_ENABLED:
        log.info(f"[MARIA §96] Places intent detected: {place_type}")
        try:
            places, cache_hit = await search_places(
                intent=IntentPayload(type=place_type),
                lat=req.lat,
                lng=req.lng,
                lang=req.lang,
                tier="MED",
                actor=req.did or "anonymous"
            )

            if places:
                best = places[0]

                # §100.5: Get live context for places too
                live_context = get_live_context(user_input, req.lat, req.lng)

                # §105 — Generate explanation for places
                travel_prefs = get_travel_preferences(req.did) if req.did else {}
                explanation_105 = generate_explanation(
                    entity={"type": place_type, "type_group": _classify_place_type_group(place_type), **best},
                    entity_type="place",
                    prefs=travel_prefs,
                    context=live_context,
                    lang=req.lang
                )

                voice_templates = {
                    "PT": f"{best['name']} está perto de ti. {best.get('rating', '')}★ {explanation_105}",
                    "DE": f"{best['name']} ist in deiner Nähe. {best.get('rating', '')}★ {generate_explanation({'type': place_type, 'type_group': _classify_place_type_group(place_type), **best}, 'place', travel_prefs, live_context, 'DE')}",
                    "EN": f"{best['name']} is near you. {best.get('rating', '')}★ {generate_explanation({'type': place_type, 'type_group': _classify_place_type_group(place_type), **best}, 'place', travel_prefs, live_context, 'EN')}"
                }

                # §100.5: Save decision to Memory Engine
                decision_id = None
                if req.did and MEMORY_ENGINE_ENABLED:
                    decision_id = save_decision(
                        did=req.did,
                        decision_type="places",
                        decision=best,
                        context=live_context,
                        destination=best.get("name")
                    )

                # §108 — Memória Visível
                visible_mem = get_visible_memory(travel_prefs, req.lang) if travel_prefs and should_show_memory(travel_prefs) else None

                # §107 — Thread Visual Timeline
                thread_id = None
                voice = voice_templates.get(req.lang, voice_templates["EN"])
                if req.did and THREAD_ENABLED:
                    thread = get_active_thread(req.did, best.get("name"))
                    if thread:
                        thread_id = thread["id"]
                        add_thread_entry(thread_id, "request", user_input)
                        add_thread_entry(thread_id, "decision", voice, {"type": "places", "place_type": place_type})
                        if visible_mem:
                            for mem in visible_mem[:2]:
                                add_thread_entry(thread_id, "memory", mem)

                return {
                    "type": "places",
                    "intent": place_type,
                    "response": voice,
                    "decision": best,  # §97: A MELHOR opção
                    "decision_id": decision_id,  # §100.5: Para feedback
                    "data": places[:5],
                    "locations": [
                        {"name": p["name"], "lat": p.get("lat"), "lng": p.get("lng"), "rating": p.get("rating")}
                        for p in places[:5] if p.get("lat")
                    ],
                    "lang": req.lang,
                    "cache_hit": cache_hit,
                    "mode": "nomada_v1.3",  # §100.5: Memory Engine
                    "visible_memory": visible_mem,  # §108
                    "thread_id": thread_id  # §107
                }
            else:
                # Sem resultados — mas intent permanece places
                no_places_msg = {
                    "PT": f"Não há {place_type} por perto agora. Tenta noutro local.",
                    "DE": f"Keine {place_type} in deiner Nähe gefunden. Versuche einen anderen Ort.",
                    "EN": f"No {place_type} found near you. Try another location."
                }
                return {
                    "type": "places",
                    "intent": place_type,
                    "response": no_places_msg.get(req.lang, no_places_msg["EN"]),
                    "data": [],
                    "lang": req.lang
                }
        except Exception as e:
            log.error(f"[MARIA §96] Places search error: {e}")
            # ⚠️ Erro não muda a natureza da decisão — NUNCA chamar LLM aqui
            error_msg = {
                "PT": "Tive um problema. Tenta novamente.",
                "DE": "Es gab ein Problem bei der Suche. Versuche es erneut.",
                "EN": "Had a problem searching places. Try again."
            }
            return {
                "type": "places_error",
                "intent": place_type,
                "response": error_msg.get(req.lang, error_msg["EN"]),
                "error": str(e),
                "lang": req.lang
            }

    # ═══════════════════════════════════════════════════════════════════════════
    # 💬 FALLBACK → LLM (conversação geral)
    # Só chega aqui se NENHUM intent actionable foi detectado (flight/hotel/places)
    # Se intent foi detectado mas falhou, NUNCA chega aqui — retorna erro do domínio
    # ═══════════════════════════════════════════════════════════════════════════

    if not BRAIN_ENABLED:
        raise HTTPException(status_code=503, detail="Brain not available — use /plan instead")

    # Get session count from memory
    session_count = 0
    if MEMORY_ENABLED and req.did:
        session_count = get_total_interactions(req.did)

    # Build location string
    location = None
    if req.lat and req.lng:
        location = f"{req.lat:.4f}, {req.lng:.4f}"

    # Get memory context
    memory = ""
    if MEMORY_ENABLED and req.did:
        nomada = get_or_create_nomada(req.did)
        if not nomada.get("is_new"):
            memory = f"Utilizador recorrente. Nome: {nomada.get('name', 'desconhecido')}."

    # Think with LLM
    result = await maria_think(
        user_input=user_input,
        lang=req.lang,
        did=req.did,
        weather=req.weather,
        location=location,
        session_count=session_count,
        memory=memory,
        tier="FREE",  # TODO: Get from wallet
        history=req.history or []
    )

    log.info(f"[MARIA Brain] Provider: {result['provider']} | Intent: {result.get('intent')} | Soul: {result.get('soul_active')}")

    return {
        "type": "chat",
        "response": result["response"],
        "provider": result["provider"],
        "intent": result.get("intent", "general"),
        "confidence": result.get("confidence", 0.9),
        "pulse": result.get("pulse"),
        "soul_active": result.get("soul_active"),
        "lang": req.lang,
        "session_count": session_count
    }


# ══════════════════════════════════════════════════════════════════════════════
# §81 — MARIA Voice Endpoint (Edge TTS)
# ══════════════════════════════════════════════════════════════════════════════

class VoiceRequest(BaseModel):
    """Request for MARIA voice generation."""
    text: str = Field(..., description="Text to speak", max_length=500)
    lang: str = Field(default="PT", description="Language: PT, DE, EN")
    accent: Optional[str] = Field(default=None, description="Accent override: pt-BR, pt-PT, de-DE, en-GB, en-US")


@router.post("/voice")
async def maria_voice_generate(req: VoiceRequest):
    """
    Generate MARIA voice audio using Edge TTS.

    §81 — Voice Sovereignty Principle:
    "Começa soberano. Externo só se a qualidade justifica."

    Returns: MP3 audio stream
    """
    from fastapi.responses import Response

    if not VOICE_ENGINE_ENABLED:
        raise HTTPException(status_code=503, detail="Voice engine not available")

    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text is required")

    # Limit text length
    text = req.text.strip()[:500]

    try:
        audio_data = await generate_speech(
            text=text,
            lang=req.lang,
            accent=req.accent,
            use_cache=True
        )

        if not audio_data:
            raise HTTPException(status_code=500, detail="Voice generation failed")

        log.info(f"[MARIA Voice] Generated {len(audio_data)} bytes for '{text[:50]}...'")

        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=maria_voice.mp3",
                "Cache-Control": "public, max-age=3600",
            }
        )

    except Exception as e:
        log.error(f"[MARIA Voice] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voice/profiles")
async def maria_voice_profiles():
    """
    List available MARIA voice profiles.
    """
    from maria.maria_voice import MARIA_VOICE_PROFILES, AVAILABLE_VOICES

    return {
        "engine": "Edge TTS",
        "enabled": VOICE_ENGINE_ENABLED,
        "profiles": MARIA_VOICE_PROFILES,
        "available_voices": AVAILABLE_VOICES,
    }


# ══════════════════════════════════════════════════════════════════════════════
# §67 — Flight Search Endpoint (Kiwi.com Bridge)
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/flight-search", response_model=FlightSearchResponse)
async def maria_flight_search(req: FlightSearchRequest):
    """
    Search flights via Kiwi.com sovereign bridge.

    IP1 Separação Financeira — WINDI recommends. Kiwi processes. User pays there.
    """
    if not KIWI_BRIDGE_ENABLED:
        raise HTTPException(status_code=503, detail="Kiwi Bridge not available")

    t0 = time.time()
    request_id = str(uuid.uuid4())
    lang = req.lang if req.lang in ("PT", "DE", "EN") else "PT"

    # 1. Search flights via Kiwi Bridge
    flights_data = await search_flights(
        fly_from=req.fly_from,
        fly_to=req.fly_to,
        date_from=req.date,
        currency="EUR",
        max_results=req.max_results or 3,
        adults=req.adults or 1,
    )

    # 2. Format MARIA voice response
    maria_text = format_flight_response(flights_data, lang)

    # 3. Determine if sovereign mode (demo data = no API key)
    sovereign_mode = flights_data.get("source") == "demo"

    # 4. Ledger seal (I11)
    seal_payload = {
        "request_id": request_id,
        "origin": flights_data.get("origin"),
        "destination": flights_data.get("destination"),
        "date": req.date,
        "flights_count": len(flights_data.get("flights", [])),
        "sovereign_mode": sovereign_mode,
        "source": flights_data.get("source", "kiwi.com"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    receipt_id = await seal_decision(request_id, seal_payload, req.wallet_id)

    elapsed = round((time.time() - t0) * 1000)
    log.info(f"[{request_id[:8]}] flight-search OK · {len(flights_data.get('flights', []))} flights · {elapsed}ms")

    return FlightSearchResponse(
        request_id=request_id,
        flights=flights_data.get("flights", []),
        origin=flights_data.get("origin", req.fly_from),
        destination=flights_data.get("destination", req.fly_to),
        date=req.date,
        maria_voice=maria_text,
        ledger_receipt_id=receipt_id,
        sovereign_mode=sovereign_mode,
        source=flights_data.get("source", "kiwi.com"),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# ══════════════════════════════════════════════════════════════════════════════
# §68 — Hotel Search Endpoint (Hotellook Bridge)
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/hotel-search", response_model=HotelSearchResponse)
async def maria_hotel_search(req: HotelSearchRequest):
    """
    Search hotels via Hotellook sovereign bridge.

    IP1 Separação Financeira — WINDI recommends. Hotellook processes. User pays there.
    Token: 513311 (Travelpayouts — same as Kiwi flights)
    """
    if not HOTEL_BRIDGE_ENABLED:
        raise HTTPException(status_code=503, detail="Hotel Bridge not available")

    t0 = time.time()
    request_id = str(uuid.uuid4())
    lang = req.lang if req.lang in ("PT", "DE", "EN") else "PT"

    # 1. Search hotels via Hotellook Bridge
    hotels_data = await search_hotels(
        destination=req.destination,
        check_in=req.check_in,
        check_out=req.check_out,
        adults=req.adults or 2,
        currency="EUR",
        lang=lang.lower(),
        max_results=req.max_results or 3,
    )

    # 2. Format MARIA voice response (natural, warm)
    maria_text = format_maria_hotel_response(hotels_data, lang)

    # 3. Determine if sovereign mode (demo data = no API key)
    sovereign_mode = hotels_data.get("source") == "demo"

    # 4. Calculate nights
    try:
        from datetime import datetime as dt
        ci = dt.strptime(req.check_in, "%Y-%m-%d")
        co = dt.strptime(req.check_out, "%Y-%m-%d")
        nights = (co - ci).days
    except Exception:
        nights = 1

    # 5. Ledger seal (I11)
    seal_payload = {
        "request_id": request_id,
        "destination": hotels_data.get("destination", req.destination),
        "check_in": req.check_in,
        "check_out": req.check_out,
        "nights": nights,
        "hotels_count": len(hotels_data.get("hotels", [])),
        "sovereign_mode": sovereign_mode,
        "source": hotels_data.get("source", "hotellook.com"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    receipt_id = await seal_decision(request_id, seal_payload, req.wallet_id)

    elapsed = round((time.time() - t0) * 1000)
    log.info(f"[{request_id[:8]}] hotel-search OK · {len(hotels_data.get('hotels', []))} hotels · {elapsed}ms")

    return HotelSearchResponse(
        request_id=request_id,
        hotels=hotels_data.get("hotels", []),
        destination=hotels_data.get("destination", req.destination),
        check_in=req.check_in,
        check_out=req.check_out,
        nights=nights,
        maria_voice=maria_text,
        ledger_receipt_id=receipt_id,
        sovereign_mode=sovereign_mode,
        source=hotels_data.get("source", "hotellook.com"),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# §100.5 — MEMORY ENGINE ENDPOINT: Decision Feedback
# ═══════════════════════════════════════════════════════════════════════════════

class DecisionFeedbackRequest(BaseModel):
    """Request to mark a decision as accepted or ignored."""
    decision_id: str = Field(..., description="Decision ID from /think response")
    accepted: Optional[bool] = Field(None, description="True if user accepted this decision")
    ignored: Optional[bool] = Field(None, description="True if user ignored/skipped this decision")
    did: Optional[str] = Field(None, description="User's DID for learning")


class DecisionFeedbackResponse(BaseModel):
    """Response confirming feedback was recorded."""
    ok: bool
    decision_id: str
    status: str  # "accepted" | "ignored" | "updated"
    learning: bool  # Whether learning was applied


@router.post("/decision-feedback")
async def decision_feedback(req: DecisionFeedbackRequest) -> DecisionFeedbackResponse:
    """
    §100.5 — Record user feedback on a MARIA decision.

    Called when user:
    - Clicks "Book" or confirms → accepted=true
    - Clicks alternative or ignores → ignored=true

    This feedback trains the Memory Engine to make better decisions.
    """
    if not req.decision_id:
        return DecisionFeedbackResponse(
            ok=False,
            decision_id="",
            status="error",
            learning=False
        )

    if not MEMORY_ENGINE_ENABLED:
        return DecisionFeedbackResponse(
            ok=True,
            decision_id=req.decision_id,
            status="no_engine",
            learning=False
        )

    # Record feedback
    mark_decision_feedback(
        decision_id=req.decision_id,
        accepted=req.accepted,
        ignored=req.ignored
    )

    # Determine status
    status = "accepted" if req.accepted else "ignored" if req.ignored else "updated"

    log.info(f"[MARIA §100.5] Feedback recorded: {req.decision_id} → {status}")

    return DecisionFeedbackResponse(
        ok=True,
        decision_id=req.decision_id,
        status=status,
        learning=True
    )


# ═══════════════════════════════════════════════════════════════════════════════
# §100.5 — MEMORY ENGINE ENDPOINT: Decision Stats (Debug)
# ═══════════════════════════════════════════════════════════════════════════════

class DecisionStatsResponse(BaseModel):
    """Statistics about a user's decisions."""
    ok: bool
    did: str
    total: int = 0
    by_type: dict = {}
    accepted: int = 0
    ignored: int = 0
    acceptance_rate: Optional[float] = None
    last_7_days: int = 0


@router.get("/decision-stats/{did}")
async def get_decision_stats_endpoint(did: str) -> DecisionStatsResponse:
    """
    §100.5 — Get statistics about a user's decision history.

    Useful for debugging and understanding MARIA's learning.
    """
    if not MEMORY_ENGINE_ENABLED:
        return DecisionStatsResponse(ok=False, did=did)

    stats = get_decision_stats(did)

    total_feedback = stats.get("accepted", 0) + stats.get("ignored", 0)
    acceptance_rate = None
    if total_feedback > 0:
        acceptance_rate = round(stats.get("accepted", 0) / total_feedback, 2)

    return DecisionStatsResponse(
        ok=True,
        did=did,
        total=stats.get("total", 0),
        by_type=stats.get("by_type", {}),
        accepted=stats.get("accepted", 0),
        ignored=stats.get("ignored", 0),
        acceptance_rate=acceptance_rate,
        last_7_days=stats.get("last_7_days", 0)
    )


# ═══════════════════════════════════════════════════════════════════════════════
# §107 — THREAD VISUAL TIMELINE ENDPOINTS
# "Mostrar evolução, não histórico"
# ═══════════════════════════════════════════════════════════════════════════════

class ThreadEntry(BaseModel):
    """A single entry in the thread timeline."""
    id: Optional[int] = None
    type: str  # request | decision | memory | context
    content: str
    timestamp: Optional[str] = None
    meta: Optional[dict] = None


class Thread(BaseModel):
    """A journey thread with timeline."""
    id: str
    title: str
    destination: Optional[str] = None
    status: str = "active"
    entry_count: Optional[int] = None
    entries: Optional[List[ThreadEntry]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ThreadsResponse(BaseModel):
    """Response with user's threads."""
    ok: bool
    threads: List[Thread] = []


class ThreadDetailResponse(BaseModel):
    """Response with thread detail and timeline."""
    ok: bool
    thread: Optional[Thread] = None


class AddEntryRequest(BaseModel):
    """Request to add entry to thread."""
    thread_id: str
    entry_type: str  # request | decision | memory | context
    content: str
    meta: Optional[dict] = None


class AddEntryResponse(BaseModel):
    """Response after adding entry."""
    ok: bool
    entry_id: Optional[int] = None


@router.get("/threads/{did}")
async def get_threads_endpoint(did: str, limit: int = 10) -> ThreadsResponse:
    """
    §107 — Get user's recent threads.
    """
    if not THREAD_ENABLED:
        return ThreadsResponse(ok=False, threads=[])

    threads = get_user_threads(did, limit)
    return ThreadsResponse(
        ok=True,
        threads=[Thread(**t) for t in threads]
    )


@router.get("/thread/{thread_id}")
async def get_thread_endpoint(thread_id: str) -> ThreadDetailResponse:
    """
    §107 — Get thread with full timeline.
    """
    if not THREAD_ENABLED:
        return ThreadDetailResponse(ok=False)

    thread = get_thread_with_timeline(thread_id)
    if not thread:
        return ThreadDetailResponse(ok=False)

    entries = [ThreadEntry(**e) for e in thread.get("entries", [])]
    return ThreadDetailResponse(
        ok=True,
        thread=Thread(
            id=thread["id"],
            title=thread["title"],
            destination=thread.get("destination"),
            status=thread["status"],
            entries=entries,
            created_at=thread.get("created_at"),
            updated_at=thread.get("updated_at")
        )
    )


@router.post("/thread/entry")
async def add_thread_entry_endpoint(req: AddEntryRequest) -> AddEntryResponse:
    """
    §107 — Add entry to a thread.
    """
    if not THREAD_ENABLED:
        return AddEntryResponse(ok=False)

    entry_id = add_thread_entry(
        thread_id=req.thread_id,
        entry_type=req.entry_type,
        content=req.content,
        meta=req.meta
    )

    return AddEntryResponse(ok=bool(entry_id), entry_id=entry_id)


@router.post("/thread/close/{thread_id}")
async def close_thread_endpoint(thread_id: str):
    """
    §107 — Close a thread.
    """
    if not THREAD_ENABLED:
        return {"ok": False}

    close_thread(thread_id)
    return {"ok": True}
