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

# Garantir que .env é carregado (fallback se identity_gate não fez)
try:
    from dotenv import load_dotenv
    load_dotenv("/opt/windi/windi-travel/identity-gate/.env")
except ImportError:
    pass

log = logging.getLogger("w-kiwi-bridge")

# ══════════════════════════════════════════════════════════════════════════════
# Configuration
# ══════════════════════════════════════════════════════════════════════════════

KIWI_API_URL = "https://api.tequila.kiwi.com/v2/search"
KIWI_API_KEY = os.getenv("KIWI_API_KEY", "")  # Tequila API key

# Travelpayouts — Motor alternativo quando KIWI não disponível
# Token: https://travelpayouts.com/developers/api
TRAVELPAYOUTS_TOKEN = os.getenv("TRAVELPAYOUTS_TOKEN", "")
TRAVELPAYOUTS_MARKER = os.getenv("TRAVELPAYOUTS_MARKER", "513311")
TRAVELPAYOUTS_API_URL = "https://api.travelpayouts.com/v1/prices/cheap"

# Legacy affiliate link (mantido para compatibilidade)
TRAVELPAYOUTS_ID = TRAVELPAYOUTS_MARKER  # alias
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
# WhereAmI — Geo-detection via Travelpayouts (§102)
# ══════════════════════════════════════════════════════════════════════════════

async def get_user_location(ip: str = None, locale: str = "pt") -> Dict[str, Any]:
    """
    Detecta localização do utilizador via Travelpayouts WhereAmI API.
    Usado para auto-popular fly_from no workspace.

    Sem API key especial — usa IP do request.
    Fallback: Kempten → MUC (base WINDI).
    """
    url = f"https://www.travelpayouts.com/whereami?locale={locale}"
    if ip and ip not in ("127.0.0.1", "::1", "localhost"):
        url += f"&ip={ip}"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(url)
            if r.status_code == 200:
                data = r.json()
                log.info(f"[WhereAmI] Detected: {data.get('name', '?')} ({data.get('iata', '?')})")

                # §145.12 fix: Parse coordinates "lng:lat" → separate lat/lng
                coords = data.get("coordinates", "")
                lat, lng = None, None
                if coords and ":" in coords:
                    try:
                        parts = coords.split(":")
                        lng = float(parts[0])
                        lat = float(parts[1])
                    except (ValueError, IndexError):
                        pass

                return {
                    "iata": data.get("iata", "MUC"),
                    "name": data.get("name", "Munique"),
                    "country_code": data.get("country_code", "DE"),
                    "country_name": data.get("country_name", "Germany"),
                    "coordinates": coords,
                    "lat": lat,
                    "lng": lng,
                    "detected": True,
                    "source": "travelpayouts_whereami"
                }
    except httpx.TimeoutException:
        log.warning("[WhereAmI] Timeout — fallback MUC")
    except Exception as e:
        log.warning(f"[WhereAmI] Error: {e} — fallback MUC")

    # Fallback: Kempten → MUC
    return {
        "iata": "MUC",
        "name": "Munique",
        "country_code": "DE",
        "country_name": "Germany",
        "coordinates": "",
        "detected": False,
        "source": "fallback_default"
    }


# ══════════════════════════════════════════════════════════════════════════════
# Travelpayouts Data API (Motor alternativo)
# ══════════════════════════════════════════════════════════════════════════════

async def _travelpayouts_search(
    fly_from: str,
    fly_to: str,
    date_from: str,
    currency: str = "EUR",
    max_results: int = 5,
) -> Dict[str, Any]:
    """
    Motor Travelpayouts Data API.
    Substitui KIWI Tequila quando KIWI_API_KEY não está disponível.
    Schema de output IDÊNTICO ao search_flights() — maria_brain.py não muda.

    IP1: Reserva acontece no Aviasales — WINDI recebe comissão via marker.
    """
    # Converter data para yyyy-mm (formato TP)
    depart_month = ""
    dd = mm = "01"
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%Y-%m"):
        try:
            dt = datetime.strptime(date_from, fmt)
            depart_month = dt.strftime("%Y-%m")
            dd = dt.strftime("%d")
            mm = dt.strftime("%m")
            break
        except ValueError:
            continue
    if not depart_month:
        depart_month = datetime.now().strftime("%Y-%m")

    # Link afiliado com marker WINDI
    aff_link = (
        f"https://www.aviasales.com/search/{fly_from}{dd}{mm}{fly_to}1"
        f"?marker={TRAVELPAYOUTS_MARKER}"
    )

    params = {
        "origin":      fly_from,
        "destination": fly_to,
        "depart_date": depart_month,
        "currency":    currency.lower(),
        "token":       TRAVELPAYOUTS_TOKEN,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(TRAVELPAYOUTS_API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        if not data.get("success"):
            log.warning(f"[Kiwi Bridge] TP API: {data.get('error')} — demo fallback")
            return _demo_flights(fly_from, fly_to, date_from, currency)

        raw = data.get("data", {})
        if not raw:
            log.info("[Kiwi Bridge] TP API: sem resultados — demo fallback")
            return _demo_flights(fly_from, fly_to, date_from, currency)

        flights = []
        for dest_key, variants in raw.items():
            for transfer_key, info in variants.items():
                try:
                    price     = info.get("price", 0)
                    airline   = info.get("airline", "")
                    dep_at    = info.get("departure_at", "")
                    transfers = int(transfer_key)

                    # Schema IDÊNTICO ao _parse_flights()
                    flights.append({
                        "from":         fly_from,
                        "from_iata":    fly_from,
                        "to":           fly_to,
                        "to_iata":      fly_to,
                        "departure":    dep_at,
                        "arrival":      dep_at,
                        "duration_min": 180,  # Estimativa (TP não fornece duração)
                        "duration_str": "~3h",
                        "price":        price,
                        "currency":     currency.upper(),
                        "layovers":     [],
                        "direct":       transfers == 0,
                        "stops":        transfers,
                        "deep_link":    aff_link,
                        "airline":      airline,
                        "airlines":     [airline] if airline else [],
                    })
                except Exception as e:
                    log.warning(f"[Kiwi Bridge] TP parse error: {e}")
                    continue

        flights.sort(key=lambda x: x.get("price") or 99999)
        log.info(f"[Kiwi Bridge] TP: {len(flights)} resultados para {fly_from}→{fly_to}")

        return {
            "origin": fly_from,
            "origin_city": fly_from,
            "destination": fly_to,
            "destination_city": fly_to,
            "date": date_from,
            "flights": flights[:max_results],
            "source": "travelpayouts",
            "data_type": "cached_7d",
            "windi_note": "Preços indicativos (cache 7 dias). Confirma disponibilidade no parceiro."
        }

    except httpx.TimeoutException:
        log.error("[Kiwi Bridge] TP timeout — demo fallback")
        return _demo_flights(fly_from, fly_to, date_from, currency)
    except Exception as e:
        log.error(f"[Kiwi Bridge] TP error: {e} — demo fallback")
        return _demo_flights(fly_from, fly_to, date_from, currency)


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

    # Check for API key — cascade: KIWI → Travelpayouts → Demo
    if not KIWI_API_KEY:
        if TRAVELPAYOUTS_TOKEN:
            log.info(f"[Kiwi Bridge] Using Travelpayouts (KIWI_API_KEY not set)")
            return await _travelpayouts_search(fly_from_iata, fly_to_iata, date_from, currency, max_results)
        else:
            log.warning("[Kiwi Bridge] No API keys configured — returning demo data")
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
    # Parse date - handle both DD/MM/YYYY and YYYY-MM-DD formats
    if "/" in date:
        # DD/MM/YYYY → YYYY-MM-DD
        iso_date = f"{date.split('/')[2]}-{date.split('/')[1]}-{date.split('/')[0]}"
    elif "-" in date and len(date) == 10:
        # Already YYYY-MM-DD
        iso_date = date
    else:
        iso_date = date  # fallback

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
                "departure": f"{iso_date}T08:30:00",
                "arrival": f"{iso_date}T11:45:00",
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
                "departure": f"{iso_date}T14:20:00",
                "arrival": f"{iso_date}T19:30:00",
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
    """Format flights for MARIA's natural voice response — warm and conversational."""
    lang = lang.upper()
    flights = flights_data.get("flights", [])

    if not flights:
        msgs = {
            "PT": "Hmm, não encontrei voos para essa rota nas datas que pediste. Queres que tente outros dias ou outro destino?",
            "DE": "Hmm, für diese Strecke habe ich leider keine Flüge gefunden. Soll ich andere Tage oder ein anderes Ziel versuchen?",
            "EN": "Hmm, I couldn't find flights for that route on those dates. Want me to try different days or another destination?"
        }
        return msgs.get(lang, msgs["EN"])

    dest = flights_data.get("destination_city", flights_data.get("destination", "?"))
    origin = flights_data.get("origin_city", flights_data.get("origin", "?"))
    best = flights[0]
    price = best['price']
    duration = best['duration_str']
    is_direct = best["direct"]
    layovers = best.get('layovers', [])

    if lang == "PT":
        # Natural, warm Portuguese
        if is_direct:
            if price < 100:
                voice = f"Boa notícia! Encontrei um voo directo para {dest} por apenas {price}€. São {duration} de viagem, bem tranquilo."
            else:
                voice = f"Tenho aqui um voo directo para {dest} — {duration} de viagem por {price}€. Sem escalas, chegas descansado!"
        else:
            stopover = layovers[0] if layovers else "uma cidade"
            if price < 80:
                voice = f"Achei uma pechincha! {price}€ para {dest}, com uma paragem em {stopover}. Demora {duration}, mas o preço compensa."
            else:
                voice = f"Encontrei voo para {dest} por {price}€, com escala em {stopover}. São {duration} no total."

        voice += " Queres que reserve ou preferes ver outras opções?"

    elif lang == "DE":
        # Natural, warm German
        if is_direct:
            if price < 100:
                voice = f"Super Nachricht! Direktflug nach {dest} für nur {price}€. {duration} Flugzeit, ganz entspannt."
            else:
                voice = f"Ich hab einen Direktflug nach {dest} — {duration} für {price}€. Ohne Umsteigen, du kommst ausgeruht an!"
        else:
            stopover = layovers[0] if layovers else "einer Stadt"
            if price < 80:
                voice = f"Ein echtes Schnäppchen! {price}€ nach {dest}, mit Zwischenstopp in {stopover}. Dauert {duration}, aber der Preis ist top."
            else:
                voice = f"Flug nach {dest} für {price}€, mit Umstieg in {stopover}. Insgesamt {duration}."

        voice += " Soll ich buchen oder möchtest du andere Optionen sehen?"

    else:  # EN
        # Natural, warm English
        if is_direct:
            if price < 100:
                voice = f"Great news! Found a direct flight to {dest} for just €{price}. It's {duration}, nice and easy."
            else:
                voice = f"Got a direct flight to {dest} — {duration} for €{price}. No layovers, you'll arrive fresh!"
        else:
            stopover = layovers[0] if layovers else "one city"
            if price < 80:
                voice = f"Found a bargain! €{price} to {dest}, with a stop in {stopover}. Takes {duration}, but that price is great."
            else:
                voice = f"Flight to {dest} for €{price}, connecting through {stopover}. {duration} total."

        voice += " Want me to book it or show you other options?"

    return voice


def detect_flight_intent(text: str) -> bool:
    """
    Detect if user input contains flight-related intent.

    §146 F14 Fix: Follow-up questions about previous context should NOT
    trigger intent detection — they should go to LLM with history.
    """
    lower = text.lower()

    # §146 F14: Follow-up patterns — route to LLM, not intent
    # These are questions about something mentioned before, not new searches
    followup_patterns = [
        # Portuguese
        "qual é o", "qual o", "que mencionei", "que eu disse", "que falei",
        "onde fica", "onde é", "como chego", "quanto custa o",
        # German
        "welcher", "welches", "was ist der", "was ist das", "wo ist",
        "wo liegt", "wie komme ich", "was kostet",
        # English
        "which is the", "what is the", "what's the", "where is",
        "how do i get", "what did i", "that i mentioned",
    ]

    for pattern in followup_patterns:
        if pattern in lower:
            return False  # Not an intent — route to LLM with history

    keywords = [
        # Portuguese
        "voo", "voos", "voar", "avião", "aviao", "aeroporto", "viajar de avião",
        "passagem", "passagens", "bilhete de avião", "bilhete", "bilhetes",
        "tiquet", "tiquete", "ticket", "tickets",
        # German
        "flug", "flüge", "fliegen", "flugzeug", "flughafen", "fliege nach",
        "flugticket", "flugreise", "flugkarte",
        # English
        "flight", "flights", "fly", "flying", "plane", "airport", "airplane",
        "book a flight", "flight to", "air ticket",
    ]

    return any(kw in lower for kw in keywords)


def extract_flight_details(text: str, default_from: str = "MUC") -> Dict[str, str]:
    """Extract flight details from natural language input."""
    import re
    lower = text.lower()

    # Prepositions indicating origin/destination
    # Order matters: longer/more specific preps first to avoid false matches
    # "de " appears in "15 de abril" so we check more specific preps first
    origin_preps = ["saindo de ", "partindo de ", "via ", "from ", "von ", "aus "]
    dest_preps = ["para ", "to ", "nach ", "pra ", "até "]

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
    # Two-pass search: first exact startswith, then broader search
    for prep in dest_preps:
        if prep in lower:
            after_prep = lower.split(prep, 1)[1]
            # Pass 1: exact match at start (most reliable)
            for city, iata in IATA_CODES.items():
                if after_prep.startswith(city):
                    destination = iata
                    break
            # Pass 2: broader search only if pass 1 failed
            if not destination:
                for city, iata in IATA_CODES.items():
                    if f" {city}" in after_prep[:30] and iata != origin:
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

    # §70 I-TRAVEL-2: Destino extraído do texto ou None — NUNCA assumido
    return {
        "fly_from": origin or default_from,
        "fly_to": destination,  # None se não detectado → MARIA pergunta
        "date": date,
        "destination_missing": destination is None,  # flag para MARIA perguntar
    }
