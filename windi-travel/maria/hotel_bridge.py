"""
WINDI Travel — Hotel Bridge via Hotellook/Travelpayouts
═══════════════════════════════════════════════════════════════
Mesmo token 513311 — zero registo adicional.
WINDI recomenda. Parceiro processa. User paga lá.
IP1 Separação Financeira — INTACTO.

API: Hotellook (Travelpayouts network)
Parceiros: Booking.com, Airbnb, Agoda, Hotels.com + 200 mais

Author: Liga IA+H · Kempten 2026
"""

import os
import logging
from datetime import date
from typing import Dict, Any, List, Optional

import httpx

log = logging.getLogger("w-hotel-bridge")

# ══════════════════════════════════════════════════════════════════════════════
# Configuration — same Travelpayouts token as Kiwi
# ══════════════════════════════════════════════════════════════════════════════

TRAVELPAYOUTS_TOKEN = "513311"
HOTEL_LOOKUP_URL = "https://engine.hotellook.com/api/v2/lookup.json"
HOTEL_SEARCH_URL = "https://engine.hotellook.com/api/v2/search/start.json"
HOTEL_RESULT_URL = "https://engine.hotellook.com/api/v2/search/getResult.json"

# City name mappings (same as kiwi_bridge for consistency)
CITY_NAMES = {
    # Portugal
    "lisboa": "Lisbon", "lisbon": "Lisbon", "lissabon": "Lisbon",
    "porto": "Porto", "oporto": "Porto",
    "faro": "Faro",
    # Germany
    "munique": "Munich", "münchen": "Munich", "munich": "Munich",
    "berlim": "Berlin", "berlin": "Berlin",
    "frankfurt": "Frankfurt",
    "hamburgo": "Hamburg", "hamburg": "Hamburg",
    # Brazil
    "são paulo": "Sao Paulo", "sao paulo": "Sao Paulo",
    "rio de janeiro": "Rio de Janeiro", "rio": "Rio de Janeiro",
    # Other
    "paris": "Paris",
    "londres": "London", "london": "London",
    "madrid": "Madrid",
    "barcelona": "Barcelona",
    "roma": "Rome", "rome": "Rome",
    "milão": "Milan", "milan": "Milan",
    "amesterdão": "Amsterdam", "amsterdam": "Amsterdam",
    "viena": "Vienna", "vienna": "Vienna", "wien": "Vienna",
    "praga": "Prague", "prague": "Prague", "prag": "Prague",
    "zurique": "Zurich", "zurich": "Zurich", "zürich": "Zurich",
}


def normalize_city(city: str) -> str:
    """Normalize city name for API lookup."""
    lower = city.lower().strip()
    return CITY_NAMES.get(lower, city.title())


# ══════════════════════════════════════════════════════════════════════════════
# Hotel Search
# ══════════════════════════════════════════════════════════════════════════════

async def search_hotels(
    destination: str,
    check_in: str,      # YYYY-MM-DD
    check_out: str,     # YYYY-MM-DD
    adults: int = 2,
    currency: str = "EUR",
    lang: str = "pt",
    max_results: int = 3
) -> Dict[str, Any]:
    """
    Search hotels via Hotellook/Travelpayouts.

    Returns top hotels for MARIA to present.
    User books on partner site — WINDI never touches payment.

    IP1 Separação Financeira — INTACTO
    """
    destination_normalized = normalize_city(destination)
    lang_code = {"PT": "pt", "DE": "de", "EN": "en"}.get(lang.upper(), "en")

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            # Step 1: Resolve destination to Hotellook city ID
            lookup_resp = await client.get(HOTEL_LOOKUP_URL, params={
                "query": destination_normalized,
                "lang": lang_code,
                "lookFor": "city",
                "token": TRAVELPAYOUTS_TOKEN
            })

            if lookup_resp.status_code != 200:
                log.warning(f"[Hotel Bridge] Lookup failed: {lookup_resp.status_code}")
                return _demo_hotels(destination, check_in, check_out, adults, currency)

            lookup_data = lookup_resp.json()
            locations = lookup_data.get("results", {}).get("locations", [])

            if not locations:
                log.warning(f"[Hotel Bridge] City not found: {destination}")
                return _demo_hotels(destination, check_in, check_out, adults, currency)

            city_id = locations[0].get("id")
            city_name = locations[0].get("cityName", destination_normalized)

            # Step 2: Start async hotel search
            search_resp = await client.get(HOTEL_SEARCH_URL, params={
                "cityId": city_id,
                "checkIn": check_in,
                "checkOut": check_out,
                "adults": adults,
                "currency": currency,
                "token": TRAVELPAYOUTS_TOKEN,
                "marker": TRAVELPAYOUTS_TOKEN,
                "waitForResult": 1
            })

            if search_resp.status_code != 200:
                log.warning(f"[Hotel Bridge] Search failed: {search_resp.status_code}")
                return _demo_hotels(destination, check_in, check_out, adults, currency)

            search_data = search_resp.json()
            search_id = search_data.get("searchId")

            if not search_id:
                log.warning("[Hotel Bridge] No searchId returned")
                return _demo_hotels(destination, check_in, check_out, adults, currency)

            # Step 3: Get results
            results_resp = await client.get(HOTEL_RESULT_URL, params={
                "searchId": search_id,
                "limit": max_results,
                "sortBy": "price",
                "sortAsc": 1,
                "token": TRAVELPAYOUTS_TOKEN
            })

            if results_resp.status_code != 200:
                log.warning(f"[Hotel Bridge] Results failed: {results_resp.status_code}")
                return _demo_hotels(destination, check_in, check_out, adults, currency)

            results_data = results_resp.json()
            hotels = _parse_hotels(
                results_data.get("result", []),
                destination_normalized,
                check_in, check_out,
                adults, currency,
                max_results
            )

            log.info(f"[Hotel Bridge] Found {len(hotels)} hotels in {city_name}")

            return {
                "destination": city_name,
                "check_in": check_in,
                "check_out": check_out,
                "nights": _calc_nights(check_in, check_out),
                "adults": adults,
                "hotels": hotels,
                "source": "hotellook.com",
                "windi_note": "Reserva no parceiro — WINDI não processa pagamentos"
            }

    except httpx.TimeoutException:
        log.warning("[Hotel Bridge] Timeout")
        return _demo_hotels(destination, check_in, check_out, adults, currency)
    except Exception as e:
        log.warning(f"[Hotel Bridge] Error: {e}")
        return _demo_hotels(destination, check_in, check_out, adults, currency)


def _calc_nights(check_in: str, check_out: str) -> int:
    """Calculate number of nights between dates."""
    try:
        d_in = date.fromisoformat(check_in)
        d_out = date.fromisoformat(check_out)
        return (d_out - d_in).days
    except:
        return 1


def _parse_hotels(
    results: List[dict],
    destination: str,
    check_in: str,
    check_out: str,
    adults: int,
    currency: str,
    max_results: int
) -> List[Dict]:
    """Parse Hotellook API response into clean hotel objects."""
    hotels = []
    nights = _calc_nights(check_in, check_out)

    for h in results[:max_results]:
        price_total = h.get("priceFrom", 0)
        price_per_night = round(price_total / nights) if nights else price_total

        hotels.append({
            "name": h.get("hotelName", "?"),
            "stars": h.get("stars", 0),
            "rating": h.get("guestScore", 0),
            "reviews": h.get("reviewsCount", 0),
            "price_per_night": price_per_night,
            "price_total": price_total,
            "currency": currency,
            "nights": nights,
            "location": destination,
            "address": h.get("address", ""),
            "deep_link": _affiliate_link(destination, check_in, check_out, adults),
            "breakfast": h.get("hasBreakfast", False),
            "free_cancellation": h.get("hasFreeCancellation", False),
            "wifi": h.get("hasWifi", True),
        })

    return hotels


def _affiliate_link(destination: str, check_in: str, check_out: str, adults: int) -> str:
    """Generate Hotellook affiliate deep link."""
    return (
        f"https://www.hotellook.com/hotels?marker={TRAVELPAYOUTS_TOKEN}"
        f"&destination={destination}"
        f"&checkIn={check_in}&checkOut={check_out}"
        f"&adults={adults}"
    )


def _demo_hotels(
    destination: str,
    check_in: str,
    check_out: str,
    adults: int,
    currency: str
) -> Dict:
    """Return demo data when API unavailable."""
    nights = _calc_nights(check_in, check_out)
    dest = normalize_city(destination)

    return {
        "destination": dest,
        "check_in": check_in,
        "check_out": check_out,
        "nights": nights,
        "adults": adults,
        "hotels": [
            {
                "name": f"Hotel Central {dest}",
                "stars": 3,
                "rating": 8.2,
                "reviews": 1247,
                "price_per_night": 65,
                "price_total": 65 * nights,
                "currency": currency,
                "nights": nights,
                "location": dest,
                "address": "Centro Histórico",
                "deep_link": _affiliate_link(dest, check_in, check_out, adults),
                "breakfast": True,
                "free_cancellation": True,
                "wifi": True,
            },
            {
                "name": f"Pensão {dest} Classic",
                "stars": 2,
                "rating": 7.8,
                "reviews": 523,
                "price_per_night": 45,
                "price_total": 45 * nights,
                "currency": currency,
                "nights": nights,
                "location": dest,
                "address": "Zona Histórica",
                "deep_link": _affiliate_link(dest, check_in, check_out, adults),
                "breakfast": True,
                "free_cancellation": False,
                "wifi": True,
            },
        ],
        "source": "demo",
        "windi_note": "DEMO — Hotellook API indisponível"
    }


# ══════════════════════════════════════════════════════════════════════════════
# MARIA Voice Formatting — Natural, warm tone
# ══════════════════════════════════════════════════════════════════════════════

def format_maria_hotel_response(data: Dict, lang: str = "PT") -> str:
    """Format hotels for MARIA's natural voice response."""
    lang = lang.upper()
    hotels = data.get("hotels", [])

    if not hotels:
        msgs = {
            "PT": "Hmm, não encontrei alojamento disponível para essas datas. Queres tentar outros dias?",
            "DE": "Hmm, keine Unterkunft für diese Daten gefunden. Andere Tage versuchen?",
            "EN": "Hmm, no accommodation available for those dates. Want to try different days?"
        }
        return msgs.get(lang, msgs["EN"])

    best = hotels[0]
    dest = data.get("destination", "?")
    nights = data.get("nights", 1)
    price_night = best.get("price_per_night", 0)
    price_total = best.get("price_total", 0)
    stars = "⭐" * int(best.get("stars", 0)) if best.get("stars") else ""
    name = best.get("name", "?")

    # Build extras string
    extras = []
    if best.get("breakfast"):
        extras.append({"PT": "pequeno-almoço incluído", "DE": "Frühstück inklusive", "EN": "breakfast included"}[lang])
    if best.get("free_cancellation"):
        extras.append({"PT": "cancelamento gratuito", "DE": "kostenlose Stornierung", "EN": "free cancellation"}[lang])
    extras_str = " · ".join(extras)

    if lang == "PT":
        if price_night < 50:
            voice = f"Achei uma boa opção em {dest}! O {name} {stars} por apenas €{price_night}/noite — €{price_total} para {nights} noites."
        else:
            voice = f"Encontrei alojamento em {dest}. O {name} {stars} fica a €{price_night}/noite, total €{price_total} para {nights} noites."
        if extras_str:
            voice += f" {extras_str.capitalize()}."
        voice += " Queres que reserve ou preferes ver outras opções?"

    elif lang == "DE":
        if price_night < 50:
            voice = f"Gute Option in {dest}! Das {name} {stars} für nur €{price_night}/Nacht — €{price_total} für {nights} Nächte."
        else:
            voice = f"Unterkunft in {dest} gefunden. Das {name} {stars} kostet €{price_night}/Nacht, gesamt €{price_total} für {nights} Nächte."
        if extras_str:
            voice += f" {extras_str.capitalize()}."
        voice += " Soll ich buchen oder andere Optionen zeigen?"

    else:  # EN
        if price_night < 50:
            voice = f"Found a great option in {dest}! {name} {stars} for just €{price_night}/night — €{price_total} for {nights} nights."
        else:
            voice = f"Found accommodation in {dest}. {name} {stars} at €{price_night}/night, total €{price_total} for {nights} nights."
        if extras_str:
            voice += f" {extras_str.capitalize()}."
        voice += " Want me to book it or show other options?"

    return voice


# ══════════════════════════════════════════════════════════════════════════════
# Hotel Intent Detection
# ══════════════════════════════════════════════════════════════════════════════

def detect_hotel_intent(text: str) -> bool:
    """Detect if user input contains hotel-related intent."""
    keywords = [
        # Portuguese
        "hotel", "hotéis", "hostel", "hostels", "pousada", "pensão",
        "alojamento", "ficar", "dormir", "quarto", "quartos",
        "reservar quarto", "onde ficar", "acomodação",
        # German
        "hotel", "hotels", "hostel", "pension", "unterkunft",
        "übernachten", "übernachtung", "zimmer", "schlafen",
        "wo übernachten", "bleiben",
        # English
        "hotel", "hotels", "hostel", "hostels", "accommodation",
        "stay", "sleep", "room", "rooms", "guesthouse", "b&b",
        "where to stay", "book a room", "lodging",
    ]

    lower = text.lower()
    return any(kw in lower for kw in keywords)


def extract_hotel_details(text: str, default_nights: int = 2) -> Dict[str, Any]:
    """Extract hotel booking details from natural language."""
    import re
    from datetime import datetime, timedelta

    lower = text.lower()

    # Find destination
    destination = None
    for city_key, city_name in CITY_NAMES.items():
        if city_key in lower:
            destination = city_name
            break

    # Find number of nights
    nights = default_nights
    nights_match = re.search(r'(\d+)\s*(?:noite|nacht|night|noches)', lower)
    if nights_match:
        nights = int(nights_match.group(1))

    # Find check-in date
    check_in = None
    # Pattern: "dia X de MONTH" or "X de MONTH" or "YYYY-MM-DD"
    month_names = {
        "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4,
        "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9,
        "outubro": 10, "novembro": 11, "dezembro": 12,
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5,
        "june": 6, "july": 7, "august": 8, "september": 9, "october": 10,
        "november": 11, "december": 12,
        "januar": 1, "februar": 2, "märz": 3, "marz": 3, "mai": 5,
        "juni": 6, "juli": 7, "oktober": 10, "dezember": 12,
    }

    for month_name, month_num in month_names.items():
        pattern = rf'(?:dia\s+)?(\d{{1,2}})\s+(?:de\s+)?{month_name}'
        match = re.search(pattern, lower)
        if match:
            day = int(match.group(1))
            year = datetime.now().year
            if month_num < datetime.now().month:
                year += 1
            check_in = f"{year}-{month_num:02d}-{day:02d}"
            break

    # Default: 7 days from now
    if not check_in:
        future = datetime.now() + timedelta(days=7)
        check_in = future.strftime("%Y-%m-%d")

    check_out_date = datetime.strptime(check_in, "%Y-%m-%d") + timedelta(days=nights)
    check_out = check_out_date.strftime("%Y-%m-%d")

    # Find number of adults
    adults = 2  # default
    adults_match = re.search(r'(\d+)\s*(?:pessoa|person|adult|erwachsen)', lower)
    if adults_match:
        adults = int(adults_match.group(1))

    # §70 I-TRAVEL-2: Destino extraído do texto ou None — NUNCA assumido
    return {
        "destination": destination,  # None se não detectado → MARIA pergunta
        "check_in": check_in,
        "check_out": check_out,
        "nights": nights,
        "adults": adults,
        "destination_missing": destination is None,  # flag para MARIA perguntar
    }
