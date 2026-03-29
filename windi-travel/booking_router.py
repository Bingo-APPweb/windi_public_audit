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

# ── Logging (no PII — I1) ─────────────────────────────────────────────────────
log = logging.getLogger("w-maria-001-booking")

# ── Config ────────────────────────────────────────────────────────────────────
GOOGLE_PLACES_KEY = os.getenv("GOOGLE_PLACES_KEY", "")
LEDGER_URL        = os.getenv("LEDGER_URL", "http://localhost:8101/api/receipts")
LEDGER_APP        = "W-MARIA-001"
OPEN_METEO_URL    = "https://api.open-meteo.com/v1/forecast"

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

    # 2. Places — Google Places or sovereign fallback
    candidates = []
    if req.lat and req.lng:
        candidates = await search_places(req.intent, lat, lng, lang)

    if not candidates:
        sovereign_mode = True
        # I10: graceful fallback — return best effort answer
        fb = SOVEREIGN_FALLBACK.get(req.intent.type, SOVEREIGN_FALLBACK["restaurant"])
        queue_txt = {"PT": "Sem dados em tempo real", "DE": "Keine Echtzeitdaten", "EN": "No real-time data"}[lang]
        reason_txt = {"PT": "Modo soberano · APIs externas indisponíveis", "DE": "Souveräner Modus · Externe APIs nicht verfügbar", "EN": "Sovereign mode · External APIs unavailable"}[lang]
        decision = PlaceResult(
            name=fb["name"], type=req.intent.type,
            distance_text="?", queue_status=queue_txt,
            reason=reason_txt, open_now=None,
        )
        voice = MariaVoice(
            PT=f"Estou em modo soberano. Não consegui dados em tempo real, mas recomendo explorar {fb['name']} na sua área.",
            DE=f"Ich bin im souveränen Modus. Keine Echtzeitdaten verfügbar. Ich empfehle {fb['name']} in Ihrer Nähe.",
            EN=f"Running in sovereign mode. No real-time data available. I suggest checking {fb['name']} nearby.",
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

    return PlanResponse(
        request_id=request_id,
        decision=decision,
        context={k: v for k, v in ctx.items() if k not in ("lat", "lng")},
        maria_voice=voice,
        intent_parsed=req.intent.model_dump(),
        ledger_receipt_id=receipt_id,
        cost_eur=0.0,  # Google Places free tier; ElevenLabs billed separately
        sovereign_mode=sovereign_mode,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
