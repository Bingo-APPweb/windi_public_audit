"""
WINDI Travel — Deutsche Bahn Bridge
═══════════════════════════════════════════════════════════════
§103 — Intermodal Intelligence

Ponte soberana para comboios via Deutsche Bahn API.
WINDI recomenda. DB processa. User paga lá.
IP1 Separação Financeira — INTACTO

API: Deutsche Bahn Journey Planner
Docs: https://developer.deutschebahn.com/

Author: Liga IA+H · Kempten 2026
"""

import os
import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from math import radians, cos, sin, asin, sqrt

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv("/opt/windi/windi-travel/identity-gate/.env")
except ImportError:
    pass

log = logging.getLogger("w-db-bridge")

# ══════════════════════════════════════════════════════════════════════════════
# Configuration
# ══════════════════════════════════════════════════════════════════════════════

# Primary: v6.db.transport.rest (community-maintained, no auth required, CORS enabled)
# Docs: https://v6.db.transport.rest/
DB_REST_API_URL = "https://v6.db.transport.rest"

# Fallback: v5 API (legacy but stable)
DB_REST_V5_URL = "https://v5.db.transport.rest"

# Legacy credentials (kept for future DB Marketplace integration)
DB_CLIENT_ID = os.getenv("DB_CLIENT_ID", "")
DB_API_KEY = os.getenv("DB_API_KEY", "")

# ══════════════════════════════════════════════════════════════════════════════
# Station Codes (German rail stations)
# ══════════════════════════════════════════════════════════════════════════════

STATION_CODES = {
    # Germany major (city names + IATA codes)
    "munich": "8000261", "münchen": "8000261", "munique": "8000261", "muc": "8000261",
    "berlin": "8011160", "berlim": "8011160", "ber": "8011160", "txl": "8011160", "sxf": "8011160",
    "frankfurt": "8000105", "francoforte": "8000105", "fra": "8000105",
    "hamburg": "8002549", "hamburgo": "8002549", "ham": "8002549",
    "cologne": "8000207", "köln": "8000207", "colonia": "8000207", "cgn": "8000207",
    "düsseldorf": "8000085", "dusseldorf": "8000085", "dus": "8000085",
    "stuttgart": "8000096", "estugarda": "8000096", "str": "8000096",
    "nuremberg": "8000284", "nürnberg": "8000284", "nue": "8000284",
    "kempten": "8000199", "fmm": "8000199",  # Near Memmingen airport

    # Austria
    "vienna": "8100003", "viena": "8100003", "wien": "8100003", "vie": "8100003",
    "salzburg": "8100002", "szg": "8100002",
    "innsbruck": "8100108", "inn": "8100108",

    # Switzerland
    "zurich": "8503000", "zürich": "8503000", "zurique": "8503000", "zrh": "8503000",
    "basel": "8500010", "basileia": "8500010", "bsl": "8500010",
    "bern": "8507000", "berna": "8507000", "brn": "8507000",

    # France
    "paris": "8727100", "cdg": "8727100", "ory": "8727100",
    "strasbourg": "8700011", "estrasburgo": "8700011", "sxb": "8700011",

    # Netherlands
    "amsterdam": "8400058", "amesterdão": "8400058", "ams": "8400058",

    # Belgium
    "brussels": "8814001", "bruxelas": "8814001", "brüssel": "8814001", "bru": "8814001",

    # Italy
    "milan": "8300046", "milão": "8300046", "mxp": "8300046", "lin": "8300046",
    "venice": "8300120", "veneza": "8300120", "venedig": "8300120", "vce": "8300120",
    "rome": "8300263", "roma": "8300263", "fco": "8300263",

    # Czech Republic
    "prague": "5400014", "praga": "5400014", "prag": "5400014", "prg": "5400014",

    # Portugal (for completeness — these would need connecting flights)
    "lisbon": "9400007", "lisboa": "9400007", "lis": "9400007",
    "porto": "9400006", "opo": "9400006",
}

# Coordinates for distance calculation (lat, lng)
# Includes IATA codes as aliases
CITY_COORDS = {
    # Germany (city names + IATA)
    "munich": (48.1351, 11.5820), "muc": (48.1351, 11.5820),
    "berlin": (52.5200, 13.4050), "ber": (52.5200, 13.4050), "txl": (52.5200, 13.4050),
    "frankfurt": (50.1109, 8.6821), "fra": (50.1109, 8.6821),
    "hamburg": (53.5511, 9.9937), "ham": (53.5511, 9.9937),
    "cologne": (50.9375, 6.9603), "cgn": (50.9375, 6.9603),
    "vienna": (48.2082, 16.3738), "vie": (48.2082, 16.3738),
    "zurich": (47.3769, 8.5417), "zrh": (47.3769, 8.5417),
    "paris": (48.8566, 2.3522), "cdg": (48.8566, 2.3522),
    "amsterdam": (52.3676, 4.9041), "ams": (52.3676, 4.9041),
    "prague": (50.0755, 14.4378), "prg": (50.0755, 14.4378),
    "milan": (45.4642, 9.1900), "mxp": (45.4642, 9.1900),
    "brussels": (50.8503, 4.3517), "bru": (50.8503, 4.3517),
    "kempten": (47.7267, 10.3168), "fmm": (47.7267, 10.3168),
}


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in km."""
    R = 6371  # Earth radius in km

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    return R * c


def estimate_distance(origin: str, destination: str) -> float:
    """
    Estimate distance between two cities in km.
    Returns 9999 if unknown (forces flight-only).
    """
    origin_lower = origin.lower().strip()
    dest_lower = destination.lower().strip()

    # Try direct lookup
    origin_coords = CITY_COORDS.get(origin_lower)
    dest_coords = CITY_COORDS.get(dest_lower)

    if origin_coords and dest_coords:
        return _haversine(
            origin_coords[0], origin_coords[1],
            dest_coords[0], dest_coords[1]
        )

    # Unknown → default to flight
    return 9999


def should_include_trains(origin: str, destination: str) -> bool:
    """
    §103 — Determine if train search makes sense.

    Rule: Include trains if distance < 800km (European rail sweet spot).
    """
    distance = estimate_distance(origin, destination)

    if distance < 800:
        log.info(f"[§103] Train search ENABLED: {origin} → {destination} ({distance:.0f}km)")
        return True
    else:
        log.info(f"[§103] Train search SKIPPED: {origin} → {destination} ({distance:.0f}km > 800km)")
        return False


def detect_train_intent(text: str) -> bool:
    """
    Detect if user input contains train-related intent.

    §103 — Intermodal Intelligence: Recognize train queries.
    """
    lower = text.lower()

    keywords = [
        # Portuguese
        "trem", "trens", "comboio", "comboios", "estação", "estacao",
        "bilhete de trem", "horário do trem", "horario do trem",
        # German
        "zug", "züge", "zuge", "bahn", "bahnhof", "ice", "ic", "re", "rb",
        "zugfahrt", "bahnfahrt", "zugverbindung", "fahrplan",
        "mit dem zug", "zugticket",
        # English
        "train", "trains", "railway", "rail", "station",
        "train ticket", "train schedule", "by train",
    ]

    return any(kw in lower for kw in keywords)


def extract_train_details(text: str, default_from: str = "kempten") -> Dict[str, Any]:
    """Extract train journey details from natural language."""
    import re
    from datetime import datetime, timedelta

    lower = text.lower()

    # Find origin and destination
    origin = None
    destination = None

    # Prepositions for origin/destination
    origin_preps = ["de ", "saindo de ", "partindo de ", "from ", "von ", "aus "]
    dest_preps = ["para ", "até ", "to ", "nach ", "pra "]
    via_preps = ["via ", "passando por ", "über "]

    # §149 FIX: Extract DESTINATION FIRST (most important for "nach Frankfurt")
    for prep in dest_preps:
        if prep in lower:
            after_prep = lower.split(prep, 1)[1].split()[0:3]
            for word in after_prep:
                clean = word.strip(".,!?")
                if clean in STATION_CODES:
                    destination = clean
                    break
            if destination:
                break

    # Extract origin (only after destination is found)
    for prep in origin_preps:
        if prep in lower:
            after_prep = lower.split(prep, 1)[1].split()[0:3]
            for word in after_prep:
                clean = word.strip(".,!?")
                if clean in STATION_CODES and clean != destination:  # Don't use same station
                    origin = clean
                    break
            if origin:
                break

    # Extract via station
    via = None
    for prep in via_preps:
        if prep in lower:
            after_prep = lower.split(prep, 1)[1].split()[0:3]
            for word in after_prep:
                clean = word.strip(".,!?")
                if clean in STATION_CODES and clean not in (origin, destination):
                    via = clean
                    break
            if via:
                break

    # Fallback: find any station not already used (only for origin if missing)
    if not origin and destination:
        for station in STATION_CODES.keys():
            pattern = r'\b' + re.escape(station) + r'\b'
            if re.search(pattern, lower) and station != destination:
                origin = station
                break

    # If still no origin but have destination, use default
    if not origin and destination:
        origin = default_from

    # If no destination found, try to find any station
    if not destination:
        for station in STATION_CODES.keys():
            pattern = r'\b' + re.escape(station) + r'\b'
            if re.search(pattern, lower) and station != origin:
                destination = station
                break

    # Parse time preference
    time = "08:00"  # Default morning
    if any(w in lower for w in ["manhã", "manha", "morning", "morgen", "früh", "fruh", "cedo"]):
        time = "07:00"
    elif any(w in lower for w in ["tarde", "afternoon", "nachmittag"]):
        time = "14:00"
    elif any(w in lower for w in ["noite", "evening", "abend"]):
        time = "18:00"

    # Parse date
    date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    month_names = {
        "janeiro": "01", "fevereiro": "02", "março": "03", "marco": "03",
        "abril": "04", "maio": "05", "junho": "06",
        "julho": "07", "agosto": "08", "setembro": "09",
        "outubro": "10", "novembro": "11", "dezembro": "12",
        "january": "01", "february": "02", "march": "03",
        "april": "04", "may": "05", "june": "06",
        "juli": "07", "august": "08", "september": "09",
        "oktober": "10", "november": "11", "dezember": "12",
    }

    month_pattern = r'(?:dia\s+)?(\d{1,2})\s+(?:de\s+)?(' + '|'.join(month_names.keys()) + r')(?:\s+(?:de\s+)?(\d{4}))?'
    month_match = re.search(month_pattern, lower)
    if month_match:
        day = month_match.group(1).zfill(2)
        month = month_names.get(month_match.group(2), "01")
        year = month_match.group(3) or "2026"
        date = f"{year}-{month}-{day}"

    return {
        "origin": origin,
        "destination": destination,
        "via": via,
        "date": date,
        "time": time,
        "destination_missing": not destination
    }


def normalize_station(location: str) -> Optional[str]:
    """Convert city name to DB station ID if known."""
    lower = location.lower().strip()
    return STATION_CODES.get(lower)


async def search_trains(
    origin: str,
    destination: str,
    date: str,  # Format: YYYY-MM-DD
    time: str = "08:00",  # Format: HH:MM
    passengers: int = 1,
) -> Dict[str, Any]:
    """
    §103 — Search trains via v6.db.transport.rest API (no auth required).

    Returns normalized travel_option format compatible with flights.
    """
    origin_station = normalize_station(origin)
    dest_station = normalize_station(destination)

    if not origin_station:
        log.warning(f"[§103] Unknown origin station: {origin}")
        return {"trains": [], "error": f"Unknown station: {origin}"}

    if not dest_station:
        log.warning(f"[§103] Unknown destination station: {destination}")
        return {"trains": [], "error": f"Unknown station: {destination}"}

    # Format departure datetime
    try:
        dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        departure_iso = dt.isoformat()
    except ValueError:
        # Fallback to today at 08:00
        dt = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        departure_iso = dt.isoformat()

    # v6.db.transport.rest journeys endpoint
    # Docs: https://v6.db.transport.rest/
    url = f"{DB_REST_API_URL}/journeys"
    params = {
        "from": origin_station,
        "to": dest_station,
        "departure": departure_iso,
        "results": 5,
        "stopovers": "false",
        "transfers": 2,  # Max 2 transfers
        "nationalExpress": "true",
        "national": "true",
        "regionalExpress": "true",
        "regional": "true",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                log.info(f"[§103] v6 API returned {len(data.get('journeys', []))} journeys")
                return normalize_v6_journeys(data, origin, destination)
            else:
                log.warning(f"[§103] v6 API returned {response.status_code}, trying v5 fallback")
                return await _search_trains_v5_fallback(origin_station, dest_station, departure_iso, origin, destination)

    except httpx.TimeoutException:
        log.error("[§103] v6 API timeout, trying v5 fallback")
        return await _search_trains_v5_fallback(origin_station, dest_station, departure_iso, origin, destination)
    except Exception as e:
        log.error(f"[§103] v6 API error: {e}")
        return {"trains": [], "error": str(e)}


async def _search_trains_v5_fallback(
    origin_station: str,
    dest_station: str,
    departure_iso: str,
    origin: str,
    destination: str,
) -> Dict[str, Any]:
    """
    Fallback to v5.db.transport.rest API.
    """
    url = f"{DB_REST_V5_URL}/journeys"
    params = {
        "from": origin_station,
        "to": dest_station,
        "departure": departure_iso,
        "results": 5,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                log.info(f"[§103] v5 fallback returned {len(data.get('journeys', []))} journeys")
                return normalize_v6_journeys(data, origin, destination)  # Same format
            else:
                log.warning(f"[§103] Fallback API returned {response.status_code}")
                return {"trains": [], "error": f"Fallback failed: {response.status_code}"}

    except Exception as e:
        log.error(f"[§103] Fallback error: {e}")
        return {"trains": [], "error": str(e)}


def normalize_v6_journeys(data: Dict, origin: str, destination: str) -> Dict[str, Any]:
    """
    §103 — Normalize v6.db.transport.rest response to unified travel_option format.

    v6 API returns journeys with legs structure:
    {
        "journeys": [
            {
                "type": "journey",
                "legs": [
                    {
                        "origin": {...},
                        "destination": {...},
                        "departure": "2026-04-05T08:30:00+02:00",
                        "arrival": "2026-04-05T12:15:00+02:00",
                        "line": {"name": "ICE 123", "product": "nationalExpress"},
                        ...
                    }
                ]
            }
        ]
    }
    """
    results = []
    journeys = data.get("journeys", [])

    for j in journeys[:5]:  # Limit to 5 results
        try:
            legs = j.get("legs", [])
            if not legs:
                continue

            # Get first and last leg for times
            first_leg = legs[0]
            last_leg = legs[-1]

            departure = first_leg.get("departure", "")
            arrival = last_leg.get("arrival", "")

            # Calculate total duration
            duration_minutes = 0
            if departure and arrival:
                try:
                    dep_dt = datetime.fromisoformat(departure)
                    arr_dt = datetime.fromisoformat(arrival)
                    duration_minutes = int((arr_dt - dep_dt).total_seconds() / 60)
                except Exception as e:
                    log.warning(f"[§103] Duration calc error: {e}")

            # Count transfers (legs - 1, but only count train legs)
            train_legs = [l for l in legs if l.get("line")]
            transfers = max(0, len(train_legs) - 1)

            # Get train type from first leg
            line = first_leg.get("line", {})
            train_type = line.get("name", "").split()[0] if line.get("name") else ""
            product = line.get("product", "")

            # Map product to train type if name not available
            if not train_type and product:
                product_map = {
                    "nationalExpress": "ICE",
                    "national": "IC",
                    "regionalExpress": "RE",
                    "regional": "RB",
                }
                train_type = product_map.get(product, product.upper())

            # Price (v6 API sometimes includes price)
            price_info = j.get("price", {})
            price = price_info.get("amount", 0) if isinstance(price_info, dict) else 0

            # Format departure time for display
            dep_time_str = ""
            if departure:
                try:
                    dep_dt = datetime.fromisoformat(departure)
                    dep_time_str = dep_dt.strftime("%H:%M")
                except:
                    pass

            results.append({
                "type": "train",
                "origin": origin.title(),
                "destination": destination.title(),
                "departure_time": departure,
                "arrival_time": arrival,
                "duration_total": duration_minutes,
                "price": price,
                "transfers": transfers,
                "direct": transfers == 0,
                "city_center_departure": True,
                "city_center_arrival": True,
                "provider": "db",
                "train_type": train_type,
                "booking_url": _build_db_booking_url(origin, destination, departure),
            })

        except Exception as e:
            log.warning(f"[§103] Failed to normalize v6 journey: {e}")
            continue

    log.info(f"[§103] Normalized {len(results)} train journeys")
    return {
        "trains": results,
        "origin": origin,
        "destination": destination,
        "source": "deutschebahn.com",
    }


def normalize_trains(db_response: Dict, origin: str, destination: str) -> Dict[str, Any]:
    """
    §103 — Normalize DB API response to unified travel_option format.
    """
    results = []

    journeys = db_response.get("journeys", db_response.get("connections", []))

    for j in journeys[:10]:  # Limit to 10 results
        try:
            # Extract journey details
            departure = j.get("departure", j.get("dep", {}).get("time", ""))
            arrival = j.get("arrival", j.get("arr", {}).get("time", ""))

            # Calculate duration
            duration_minutes = j.get("duration_minutes", j.get("duration", 0))
            if not duration_minutes and departure and arrival:
                try:
                    dep_dt = datetime.fromisoformat(departure.replace("Z", "+00:00"))
                    arr_dt = datetime.fromisoformat(arrival.replace("Z", "+00:00"))
                    duration_minutes = int((arr_dt - dep_dt).total_seconds() / 60)
                except:
                    duration_minutes = 0

            # Count transfers
            legs = j.get("legs", j.get("sections", []))
            transfers = max(0, len(legs) - 1) if legs else j.get("transfers", 0)

            # Price (if available)
            price = j.get("price", {}).get("amount", 0)
            if isinstance(price, dict):
                price = price.get("value", 0)

            # Train type (ICE, IC, RE, etc.)
            train_type = ""
            if legs:
                first_leg = legs[0]
                train_type = first_leg.get("line", {}).get("product",
                             first_leg.get("train", {}).get("type", ""))

            # Build booking URL
            booking_url = _build_db_booking_url(origin, destination, departure)

            results.append({
                "type": "train",
                "origin": origin.title(),
                "destination": destination.title(),
                "departure_time": departure,
                "arrival_time": arrival,
                "duration_total": duration_minutes,
                "price": price,
                "transfers": transfers,
                "direct": transfers == 0,
                "city_center_departure": True,
                "city_center_arrival": True,
                "provider": "db",
                "train_type": train_type,
                "booking_url": booking_url,
            })

        except Exception as e:
            log.warning(f"[§103] Failed to normalize journey: {e}")
            continue

    return {
        "trains": results,
        "origin": origin,
        "destination": destination,
        "source": "deutschebahn.com",
    }


def normalize_departures(timetable_data: Dict, origin: str, destination: str) -> Dict[str, Any]:
    """
    Normalize free timetable API response (departures only).
    Less detailed but still useful.
    """
    results = []

    departures = timetable_data if isinstance(timetable_data, list) else timetable_data.get("departures", [])

    dest_lower = destination.lower()

    for dep in departures[:20]:
        try:
            # Filter by destination
            direction = dep.get("direction", "").lower()
            if dest_lower not in direction:
                continue

            departure_time = dep.get("dateTime", dep.get("time", ""))
            train_type = dep.get("name", dep.get("train", ""))

            # Estimate duration based on typical speeds
            distance = estimate_distance(origin, destination)
            avg_speed = 120 if "ICE" in train_type else 80  # km/h
            duration_minutes = int((distance / avg_speed) * 60)

            results.append({
                "type": "train",
                "origin": origin.title(),
                "destination": destination.title(),
                "departure_time": departure_time,
                "arrival_time": "",  # Not available in free API
                "duration_total": duration_minutes,
                "price": 0,  # Not available in free API
                "transfers": 0,  # Unknown
                "direct": True,  # Assume direct for simplicity
                "city_center_departure": True,
                "city_center_arrival": True,
                "provider": "db",
                "train_type": train_type,
                "booking_url": _build_db_booking_url(origin, destination, departure_time),
            })

        except Exception as e:
            log.warning(f"[§103] Failed to parse departure: {e}")
            continue

    return {
        "trains": results[:5],  # Limit results
        "origin": origin,
        "destination": destination,
        "source": "deutschebahn.com",
    }


def _build_db_booking_url(origin: str, destination: str, departure: str) -> str:
    """Build Deutsche Bahn booking URL."""
    base = "https://www.bahn.de/buchung/start"

    # Parse date from departure
    date_str = ""
    if departure:
        try:
            dt = datetime.fromisoformat(departure.replace("Z", "+00:00"))
            date_str = dt.strftime("%d.%m.%Y")
        except:
            pass

    return f"{base}?S={origin}&Z={destination}&datum={date_str}"


# ══════════════════════════════════════════════════════════════════════════════
# Exports
# ══════════════════════════════════════════════════════════════════════════════

__all__ = [
    "search_trains",
    "should_include_trains",
    "estimate_distance",
    "normalize_station",
    "STATION_CODES",
    "CITY_COORDS",
]
