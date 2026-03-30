"""
WINDI Travel — Kiwi Bridge
═══════════════════════════════════════════════════════════════
Ponte soberana para voos via Kiwi.com

WINDI recomenda. Kiwi processa. User paga lá.
IP1 Separação Financeira — INTACTO

API: Kiwi Tequila — gratuita até 1000 req/mês
Registo: https://tequila.kiwi.com

Author: Liga IA+H · Kempten 2026
"""

import os
import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

log = logging.getLogger("w-kiwi-bridge")

# ══════════════════════════════════════════════════════════════════════════════
# Configuration
# ══════════════════════════════════════════════════════════════════════════════

KIWI_API_URL = "https://api.tequila.kiwi.com/v2/search"
KIWI_API_KEY = os.getenv("KIWI_API_KEY", "")  # Tequila API key

# Travelpayouts Affiliate — §67 IP1 intacto
TRAVELPAYOUTS_ID = "513311"
KIWI_AFFILIATE_BASE = f"https://www.kiwi.com/?affilid={TRAVELPAYOUTS_ID}"


def _affiliate_link(deep_link: str) -> str:
    """Add Travelpayouts affiliate tracking to Kiwi deep link."""
    if not deep_link:
        return KIWI_AFFILIATE_BASE
    if "?" in deep_link:
        return f"{deep_link}&affilid={TRAVELPAYOUTS_ID}"
    return f"{deep_link}?affilid={TRAVELPAYOUTS_ID}"


# IATA codes for common destinations
IATA_CODES = {
    # Germany
    "munich": "MUC", "münchen": "MUC", "munique": "MUC",
    "berlin": "BER", "berlim": "BER",
    "frankfurt": "FRA", "francoforte": "FRA",
    "hamburg": "HAM", "hamburgo": "HAM",
    "düsseldorf": "DUS", "dusseldorf": "DUS",
    "cologne": "CGN", "köln": "CGN", "colonia": "CGN",
    "stuttgart": "STR", "estugarda": "STR",
    "memmingen": "FMM",  # Near Kempten!

    # Portugal
    "lisbon": "LIS", "lisboa": "LIS", "lissabon": "LIS",
    "porto": "OPO", "oporto": "OPO",
    "faro": "FAO",
    "madeira": "FNC", "funchal": "FNC",

    # Brazil
    "são paulo": "GRU", "sao paulo": "GRU",
    "rio": "GIG", "rio de janeiro": "GIG",
    "florianópolis": "FLN", "florianopolis": "FLN",
    "brasília": "BSB", "brasilia": "BSB",

    # Other popular
    "paris": "CDG",
    "london": "LHR", "londres": "LHR",
    "amsterdam": "AMS", "amesterdão": "AMS",
    "barcelona": "BCN",
    "madrid": "MAD",
    "rome": "FCO", "roma": "FCO",
    "milan": "MXP", "milão": "MXP",
    "zurich": "ZRH", "zürich": "ZRH", "zurique": "ZRH",
    "vienna": "VIE", "viena": "VIE", "wien": "VIE",
    "prague": "PRG", "praga": "PRG", "prag": "PRG",
}


def normalize_location(location: str) -> str:
    """Convert city name to IATA code if known."""
    lower = location.lower().strip()
    return IATA_CODES.get(lower, location.upper())


# ══════════════════════════════════════════════════════════════════════════════
# Flight Search
# ══════════════════════════════════════════════════════════════════════════════

async def search_flights(
    fly_from: str,
    fly_to: str,
    date_from: str,        # dd/mm/yyyy
    date_to: str = None,   # flexibility +3 days
    currency: str = "EUR",
    max_results: int = 3,
    sort: str = "price",
    adults: int = 1,
    max_stopovers: int = 2
) -> Dict[str, Any]:
    """
    Pesquisa voos soberanos via Kiwi.com.

    Returns top flights for MARIA to present.
    User books on Kiwi — WINDI never touches payment.

    IP1 Separação Financeira — INTACTO
    """
    # Normalize locations to IATA
    fly_from_iata = normalize_location(fly_from)
    fly_to_iata = normalize_location(fly_to)

    # Flexibility window
    if date_to is None:
        try:
            d = datetime.strptime(date_from, "%d/%m/%Y")
            date_to = (d + timedelta(days=3)).strftime("%d/%m/%Y")
        except ValueError:
            date_to = date_from

    # Check for API key
    if not KIWI_API_KEY:
        log.warning("[Kiwi Bridge] No KIWI_API_KEY configured — returning demo data")
        return _demo_flights(fly_from_iata, fly_to_iata, date_from, currency)

    params = {
        "fly_from": fly_from_iata,
        "fly_to": fly_to_iata,
        "date_from": date_from,
        "date_to": date_to,
        "curr": currency,
        "limit": max_results,
        "sort": sort,
        "adults": adults,
        "max_stopovers": max_stopovers,
        "partner": "picky",  # Replace with actual affiliate ID
    }

    headers = {
        "apikey": KIWI_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(KIWI_API_URL, params=params, headers=headers)

            if r.status_code != 200:
                log.warning(f"[Kiwi Bridge] API error: {r.status_code}")
                return {
                    "error": f"Kiwi API error: {r.status_code}",
                    "flights": [],
                    "origin": fly_from_iata,
                    "destination": fly_to_iata,
                }

            data = r.json()
            flights = _parse_flights(data, currency, max_results)

            log.info(f"[Kiwi Bridge] Found {len(flights)} flights {fly_from_iata}→{fly_to_iata}")

            return {
                "origin": fly_from_iata,
                "origin_city": fly_from,
                "destination": fly_to_iata,
                "destination_city": fly_to,
                "date": date_from,
                "flights": flights,
                "source": "kiwi.com",
                "windi_note": "Reserva feita no Kiwi.com — WINDI não processa pagamentos"
            }

    except httpx.TimeoutException:
        log.warning("[Kiwi Bridge] Timeout")
        return {"error": "Kiwi timeout", "flights": []}
    except Exception as e:
        log.warning(f"[Kiwi Bridge] Error: {e}")
        return {"error": str(e), "flights": []}


def _parse_flights(data: dict, currency: str, max_results: int) -> List[Dict]:
    """Parse Kiwi API response into clean flight objects."""
    flights = []

    for f in data.get("data", [])[:max_results]:
        duration_sec = f.get("duration", {}).get("departure", 0)
        duration_min = duration_sec // 60

        # Extract layovers from route
        route = f.get("route", [])
        layovers = []
        if len(route) > 1:
            layovers = [r.get("cityTo", "") for r in route[:-1]]

        # Get airlines
        airlines = f.get("airlines", [])
        airline = airlines[0] if airlines else "?"

        flights.append({
            "from": f.get("cityFrom", "?"),
            "from_iata": f.get("flyFrom", "?"),
            "to": f.get("cityTo", "?"),
            "to_iata": f.get("flyTo", "?"),
            "departure": f.get("local_departure", ""),
            "arrival": f.get("local_arrival", ""),
            "duration_min": duration_min,
            "duration_str": f"{duration_min // 60}h{duration_min % 60:02d}m",
            "price": f.get("price", 0),
            "currency": currency,
            "layovers": layovers,
            "direct": len(layovers) == 0,
            "stops": len(layovers),
            "deep_link": _affiliate_link(f.get("deep_link", "")),
            "airline": airline,
            "airlines": airlines,
        })

    return flights


def _demo_flights(fly_from: str, fly_to: str, date: str, currency: str) -> Dict:
    """Return demo data when API key not configured."""
    return {
        "origin": fly_from,
        "destination": fly_to,
        "date": date,
        "flights": [
            {
                "from": fly_from,
                "from_iata": fly_from,
                "to": fly_to,
                "to_iata": fly_to,
                "departure": f"{date.split('/')[2]}-{date.split('/')[1]}-{date.split('/')[0]}T08:30:00",
                "arrival": f"{date.split('/')[2]}-{date.split('/')[1]}-{date.split('/')[0]}T11:45:00",
                "duration_min": 195,
                "duration_str": "3h15m",
                "price": 89,
                "currency": currency,
                "layovers": [],
                "direct": True,
                "stops": 0,
                "deep_link": KIWI_AFFILIATE_BASE,
                "airline": "TAP",
                "airlines": ["TAP"],
            },
            {
                "from": fly_from,
                "from_iata": fly_from,
                "to": fly_to,
                "to_iata": fly_to,
                "departure": f"{date.split('/')[2]}-{date.split('/')[1]}-{date.split('/')[0]}T14:20:00",
                "arrival": f"{date.split('/')[2]}-{date.split('/')[1]}-{date.split('/')[0]}T19:30:00",
                "duration_min": 310,
                "duration_str": "5h10m",
                "price": 67,
                "currency": currency,
                "layovers": ["FRA"],
                "direct": False,
                "stops": 1,
                "deep_link": KIWI_AFFILIATE_BASE,
                "airline": "LH",
                "airlines": ["LH", "TAP"],
            },
        ],
        "source": "demo",
        "windi_note": "DEMO — Configure KIWI_API_KEY for real flights"
    }


# ══════════════════════════════════════════════════════════════════════════════
# MARIA Voice Formatting
# ══════════════════════════════════════════════════════════════════════════════

def format_maria_response(flights_data: Dict, lang: str = "PT") -> str:
    """Format flights for MARIA's voice response."""
    lang = lang.upper()
    flights = flights_data.get("flights", [])

    if not flights:
        msgs = {
            "PT": "Não encontrei voos disponíveis para essa rota. Quer tentar outras datas ou destinos?",
            "DE": "Keine Flüge für diese Route gefunden. Andere Daten oder Ziele versuchen?",
            "EN": "No flights found for this route. Want to try different dates or destinations?"
        }
        return msgs.get(lang, msgs["EN"])

    dest = flights_data.get("destination_city", flights_data.get("destination", "?"))
    origin = flights_data.get("origin_city", flights_data.get("origin", "?"))
    best = flights[0]

    if lang == "PT":
        intro = f"Encontrei {len(flights)} voo{'s' if len(flights) > 1 else ''} de {origin} para {dest}."
        route = "directo" if best["direct"] else f"com escala em {', '.join(best['layovers'])}"
        best_str = f"O mais barato: {best['price']}€ — {route} — {best['duration_str']}."
        cta = "Queres ver os detalhes ou reservar?"

    elif lang == "DE":
        intro = f"Ich habe {len(flights)} Flug{'e' if len(flights) > 1 else ''} von {origin} nach {dest} gefunden."
        route = "Direktflug" if best["direct"] else f"mit Zwischenstopp in {', '.join(best['layovers'])}"
        best_str = f"Der günstigste: {best['price']}€ — {route} — {best['duration_str']}."
        cta = "Möchtest du die Details sehen oder buchen?"

    else:  # EN
        intro = f"Found {len(flights)} flight{'s' if len(flights) > 1 else ''} from {origin} to {dest}."
        route = "direct" if best["direct"] else f"via {', '.join(best['layovers'])}"
        best_str = f"Cheapest: €{best['price']} — {route} — {best['duration_str']}."
        cta = "Want to see details or book?"

    return f"{intro} {best_str} {cta}"


def detect_flight_intent(text: str) -> bool:
    """Detect if user input contains flight-related intent."""
    keywords = [
        # Portuguese
        "voo", "voos", "voar", "avião", "aviao", "aeroporto", "viajar de avião",
        "passagem", "passagens", "bilhete de avião",
        # German
        "flug", "flüge", "fliegen", "flugzeug", "flughafen", "fliege nach",
        "flugticket", "flugreise",
        # English
        "flight", "flights", "fly", "flying", "plane", "airport", "airplane",
        "book a flight", "flight to",
    ]

    lower = text.lower()
    return any(kw in lower for kw in keywords)


def extract_flight_details(text: str, default_from: str = "MUC") -> Dict[str, str]:
    """Extract flight details from natural language input."""
    import re
    lower = text.lower()

    # Prepositions indicating origin/destination
    origin_preps = ["de ", "from ", "von ", "aus "]
    dest_preps = ["para ", "to ", "nach ", "pra "]

    origin = None
    destination = None

    # Find origin (city after "de/from/von")
    for prep in origin_preps:
        if prep in lower:
            after_prep = lower.split(prep, 1)[1]
            for city, iata in IATA_CODES.items():
                if after_prep.startswith(city) or f" {city}" in after_prep[:30]:
                    origin = iata
                    break
            if origin:
                break

    # Find destination (city after "para/to/nach")
    for prep in dest_preps:
        if prep in lower:
            after_prep = lower.split(prep, 1)[1]
            for city, iata in IATA_CODES.items():
                if after_prep.startswith(city) or f" {city}" in after_prep[:30]:
                    destination = iata
                    break
            if destination:
                break

    # Fallback: find any city not already used
    if not origin or not destination:
        for city, iata in IATA_CODES.items():
            if city in lower:
                if not origin and iata != destination:
                    origin = iata
                elif not destination and iata != origin:
                    destination = iata
                if origin and destination:
                    break

    # Parse date - multiple patterns
    # Pattern 1: "dia 15 de abril de 2026"
    month_names = {
        "janeiro": "01", "fevereiro": "02", "março": "03", "marco": "03",
        "abril": "04", "maio": "05", "junho": "06",
        "julho": "07", "agosto": "08", "setembro": "09",
        "outubro": "10", "novembro": "11", "dezembro": "12",
        "january": "01", "february": "02", "march": "03",
        "april": "04", "may": "05", "june": "06",
        "july": "07", "august": "08", "september": "09",
        "october": "10", "november": "11", "december": "12",
        "januar": "01", "februar": "02", "märz": "03", "marz": "03",
        "april": "04", "mai": "05", "juni": "06",
        "juli": "07", "august": "08", "september": "09",
        "oktober": "10", "november": "11", "dezember": "12",
    }

    date = None

    # Pattern: "dia X de MONTH de YEAR" or "X de MONTH"
    month_pattern = r'(?:dia\s+)?(\d{1,2})\s+(?:de\s+)?(' + '|'.join(month_names.keys()) + r')(?:\s+(?:de\s+)?(\d{4}))?'
    month_match = re.search(month_pattern, lower)
    if month_match:
        day = month_match.group(1).zfill(2)
        month = month_names.get(month_match.group(2), "01")
        year = month_match.group(3) or "2026"
        date = f"{day}/{month}/{year}"

    # Pattern 2: dd/mm/yyyy or dd-mm-yyyy
    if not date:
        date_pattern = r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.]?(\d{2,4})?'
        date_match = re.search(date_pattern, text)
        if date_match:
            day, month = date_match.group(1), date_match.group(2)
            year = date_match.group(3) or "2026"
            if len(year) == 2:
                year = "20" + year
            date = f"{day.zfill(2)}/{month.zfill(2)}/{year}"

    # Default: 7 days from now
    if not date:
        future = datetime.now() + timedelta(days=7)
        date = future.strftime("%d/%m/%Y")

    return {
        "fly_from": origin or default_from,
        "fly_to": destination or "LIS",
        "date": date
    }
