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
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

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
    )
    MEMORY_ENABLED = True
except ImportError:
    MEMORY_ENABLED = False
    def gerar_saudacao(did, lang): return {"PT": "Bom dia, viajante", "DE": "Guten Tag, Reisender", "EN": "Good day, traveller"}.get(lang, "Good day")
    def get_total_interactions(did): return 0
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

# ── Kiwi Flight Bridge (§67) ─────────────────────────────────────────────────
try:
    from maria.kiwi_bridge import (
        search_flights,
        format_maria_response as format_flight_response,
        detect_flight_intent,
        extract_flight_details,
    )
    KIWI_BRIDGE_ENABLED = True
    log.info("[MARIA] Kiwi Flight Bridge loaded ✓")
except ImportError as e:
    KIWI_BRIDGE_ENABLED = False
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

# ── §69 Culture/Tips Intent Detection ─────────────────────────────────────────
CULTURE_KEYWORDS = {
    "pt": [
        "moeda", "língua", "idioma", "costume", "horário", "horarios",
        "seguro", "segurança", "perigoso", "tempo", "clima", "temperatura",
        "como chegar", "transporte", "metro", "autocarro", "táxi", "uber",
        "dica", "dicas", "conselho", "recomenda", "gorjeta", "propina",
        "tomada", "voltagem", "adaptador", "wifi", "internet", "roaming",
        "visto", "passaporte", "vacina", "agua", "beber", "comer",
        "quanto custa", "preço", "barato", "caro", "trocar dinheiro",
    ],
    "de": [
        "währung", "geld", "sprache", "öffnungszeiten", "sicher", "sicherheit",
        "gefährlich", "wetter", "klima", "temperatur", "wie komme ich",
        "transport", "u-bahn", "bus", "taxi", "tipp", "tipps", "empfehlung",
        "trinkgeld", "steckdose", "spannung", "adapter", "wlan", "internet",
        "visum", "reisepass", "impfung", "wasser", "trinken", "essen",
        "wie viel kostet", "preis", "billig", "teuer", "geld wechseln",
    ],
    "en": [
        "currency", "money", "language", "customs", "hours", "opening",
        "safe", "safety", "dangerous", "weather", "climate", "temperature",
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

class MariaVoice(BaseModel):
    PT: str
    DE: str
    EN: str

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
        out = []
        for p in places:
            out.append({
                "name": p.get("name"),
                "place_id": p.get("place_id"),
                "address": p.get("vicinity") or p.get("formatted_address"),
                "rating": p.get("rating"),
                "open_now": p.get("opening_hours", {}).get("open_now") if isinstance(p.get("opening_hours"), dict) else None,
                "user_ratings_total": p.get("user_ratings_total", 0),
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
                out.append({
                    "name": p.get("name"),
                    "place_id": p.get("place_id"),
                    "address": p.get("vicinity"),
                    "rating": p.get("rating"),
                    "open_now": p.get("opening_hours", {}).get("open_now"),
                    "user_ratings_total": p.get("user_ratings_total", 0),
                })
            return out, False  # Not from cache
    except Exception as e:
        log.warning(f"Google Places fallback: {e}")
        return [], False

# ── Decision Engine ────────────────────────────────────────────────────────────
def score_place(place: dict, intent: IntentPayload, ctx: dict) -> float:
    """Score a candidate place 0–100."""
    score = 50.0
    # Rating bonus
    score += (place.get("rating") or 3.5) * 5
    # Open now
    if place.get("open_now") is True:
        score += 15
    elif place.get("open_now") is False:
        score -= 40
    # Rain → indoor preference
    if ctx.get("is_raining") and intent.type in ("restaurant", "cafe", "museum"):
        score += 10
    # Quiet preference
    if intent.quiet and (place.get("user_ratings_total") or 0) < 500:
        score += 8
    # Family
    if intent.family and intent.type == "museum":
        score += 10
    return round(score, 1)

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
        "PT": f"Encontrei {place_name} a {dist}. {queue_status}.",
        "DE": f"Ich habe {place_name} in {dist} gefunden. {queue_status}.",
        "EN": f"I found {place_name}, {dist} away. {queue_status}.",
    }
    return MariaVoice(**templates)

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

        flights_data = await search_flights(
            fly_from=flight_details["fly_from"],
            fly_to=flight_details["fly_to"],
            date_from=flight_details["date"],
            currency="EUR",
            max_results=3,
        )

        maria_text = format_flight_response(flights_data, lang)
        sovereign_mode = flights_data.get("source") == "demo"

        # Seal to Ledger
        seal_payload = {
            "request_id": request_id,
            "origin": flights_data.get("origin"),
            "destination": flights_data.get("destination"),
            "date": flight_details["date"],
            "flights_count": len(flights_data.get("flights", [])),
            "sovereign_mode": sovereign_mode,
            "source": flights_data.get("source", "kiwi.com"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        receipt_id = await seal_decision(request_id, seal_payload, req.wallet_id)

        # Return flight results in PlanResponse format
        best_flight = flights_data.get("flights", [{}])[0] if flights_data.get("flights") else {}

        return PlanResponse(
            request_id=request_id,
            decision=PlaceResult(
                name=f"Voo {flights_data.get('origin', '?')} → {flights_data.get('destination', '?')}",
                type="flight",
                distance_text=best_flight.get("duration_str", "?"),
                queue_status=f"{best_flight.get('price', '?')}€" if best_flight else "?",
                reason=maria_text[:200],
                rating=None,
                open_now=None,
            ),
            context={
                "weather": ctx.get("weather", ""),
                "flights": flights_data.get("flights", []),
                "origin": flights_data.get("origin"),
                "destination": flights_data.get("destination"),
                "source": flights_data.get("source", "kiwi.com"),
            },
            maria_voice=MariaVoice(
                PT=maria_text if lang == "PT" else "",
                DE=maria_text if lang == "DE" else "",
                EN=maria_text if lang == "EN" else "",
            ),
            intent_parsed={"type": "flight", "detected_from_query": True},
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

    # 1e. §65 — Special handling for greeting intent
    #     For greetings, use the requested language (not stored preference)
    if req.intent.type == "greeting":
        greeting_lang = req.lang if req.lang in ("PT", "DE", "EN") else "EN"
        greeting_text = gerar_saudacao(did, greeting_lang) if did else {
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

    # 1f. §69 — Culture/Tips intent detection
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
        scored = sorted(candidates, key=lambda p: score_place(p, req.intent, ctx), reverse=True)
        best = scored[0]
        dist_txt = {"PT": "próximo", "DE": "in der Nähe", "EN": "nearby"}[lang]
        queue_txt = (
            {"PT": "Aberto agora", "DE": "Jetzt geöffnet", "EN": "Open now"}[lang]
            if best.get("open_now") else
            {"PT": "Verifique horário", "DE": "Öffnungszeiten prüfen", "EN": "Check opening hours"}[lang]
        )
        reason = build_reason(best, req.intent, ctx, lang)
        decision = PlaceResult(
            name=best["name"], type=req.intent.type,
            distance_text=dist_txt, queue_status=queue_txt,
            reason=reason, google_place_id=best.get("place_id"),
            address=best.get("address"), rating=best.get("rating"),
            open_now=best.get("open_now"),
        )
        voice = build_voice(best["name"], dist_txt, queue_txt, lang)

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
    )


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
