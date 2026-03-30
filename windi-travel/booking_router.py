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

import os, time, uuid, hashlib, json, logging
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

# ── MARIA Voice (Triple LLM) ──────────────────────────────────────────────────
from maria_voice import select_provider, get_system_prompt, MARIA_PROMPTS

# ── MARIA Memory (DID Profiles) ───────────────────────────────────────────────
try:
    from maria.nomada_profile import (
        get_or_create_nomada,
        enrich_context_with_memory,
        log_interaction,
        set_preference,
    )
    MEMORY_ENABLED = True
except ImportError:
    MEMORY_ENABLED = False
    log.warning("[MARIA] Memory module not available — running without DID persistence")

# ── Logging (no PII — I1) ─────────────────────────────────────────────────────
log = logging.getLogger("w-maria-001-booking")

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

# ── Context Enricher (Open-Meteo, FREE) ───────────────────────────────────────
async def enrich_context(lat: float, lng: float) -> dict:
    """Fetch real weather via Open-Meteo. Zero cost, no API key."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
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
            return {
                "weather": f"{emoji} {temp}°C",
                "is_raining": rain,
                "lat": round(lat, 3),   # I1: reduced precision, not stored
                "lng": round(lng, 3),
            }
    except Exception as e:
        log.warning(f"Open-Meteo fallback: {e}")
        return {"weather": "? N/A", "is_raining": False, "lat": lat, "lng": lng}

# ── Google Places Search ───────────────────────────────────────────────────────
PLACE_TYPE_MAP = {
    "restaurant": "restaurant",
    "cafe":       "cafe",
    "museum":     "museum",
    "hotel":      "lodging",
    "event":      "tourist_attraction",
}

async def search_places(intent: IntentPayload, lat: float, lng: float, lang: str) -> list[dict]:
    """Query Google Places Nearby Search. Returns top 3 candidates."""
    if not GOOGLE_PLACES_KEY:
        return []  # sovereign fallback handled upstream
    gtype = PLACE_TYPE_MAP.get(intent.type, "point_of_interest")
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
            return out
    except Exception as e:
        log.warning(f"Google Places fallback: {e}")
        return []

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
    provider = select_provider(intent, ctx)
    system_prompt = get_system_prompt(provider, lang)

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
    did = req.wallet_id
    if MEMORY_ENABLED and did:
        profile = get_or_create_nomada(did, lang=lang)
        ctx = enrich_context_with_memory(did, ctx)
        # Use nomada's preferred language if this is a returning user
        if not profile.get("is_new") and profile.get("lang"):
            lang = profile["lang"]
            ctx["lang"] = lang

    # 2. Places — Google Places or sovereign fallback
    candidates = []
    if req.lat and req.lng:
        candidates = await search_places(req.intent, lat, lng, lang)

    if not candidates:
        # Plan B: Try LLM via Gateway before falling back to generic
        llm_result = await call_gateway_llm(
            intent=req.intent.model_dump(),
            ctx=ctx,
            lang=lang
        )

        if llm_result:
            # LLM responded — use its recommendation
            sovereign_mode = False
            provider_used = llm_result.get("provider", "gemini")
            llm_text = llm_result.get("reason", "")

            queue_txt = {"PT": "Recomendação IA", "DE": "KI-Empfehlung", "EN": "AI recommendation"}[lang]
            decision = PlaceResult(
                name=llm_result.get("name", "Recomendação MARIA"),
                type=req.intent.type,
                distance_text="?",
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
            # I10: Ultimate fallback — return generic answer
            sovereign_mode = True
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
        memory_active=MEMORY_ENABLED and did is not None,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
