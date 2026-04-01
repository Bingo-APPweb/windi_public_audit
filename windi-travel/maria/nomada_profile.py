"""
nomada_profile.py — MARIA Memory Layer
───────────────────────────────────────
Stores and retrieves nomada preferences per DID.
"MARIA remembers, but never intrudes."

Database: maria_memory.db (SQLite)
Schema:
  - nomadas:     did, lang, created_at
  - preferences: did, key, value, updated_at
  - interactions: did, request_id, intent_type, place, rating, timestamp

Invariants:
  I1 — No PII stored (only DID + preferences)
  I11 — Interactions can be sealed in Ledger

Author: Liga IA+H · Kempten 2026
"""

import sqlite3
import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import logging

log = logging.getLogger("w-maria-memory")

# ── Database Path ────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "maria_memory.db")


def get_connection() -> sqlite3.Connection:
    """Get SQLite connection with row factory."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database schema if not exists."""
    conn = get_connection()
    c = conn.cursor()

    # Nomadas — base profile
    c.execute("""
        CREATE TABLE IF NOT EXISTS nomadas (
            did TEXT PRIMARY KEY,
            lang TEXT DEFAULT 'EN',
            name TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Preferences — key-value store per DID
    c.execute("""
        CREATE TABLE IF NOT EXISTS preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            did TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(did, key)
        )
    """)

    # Interactions — history of MARIA recommendations
    c.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            did TEXT NOT NULL,
            request_id TEXT NOT NULL,
            intent_type TEXT,
            place_name TEXT,
            rating INTEGER,
            feedback TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Indexes for performance
    c.execute("CREATE INDEX IF NOT EXISTS idx_interactions_did ON interactions(did)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_preferences_did ON preferences(did)")

    conn.commit()
    conn.close()
    log.info(f"[MARIA Memory] Database initialized: {DB_PATH}")


# ── Nomada Profile ───────────────────────────────────────────────────────────

def get_or_create_nomada(did: str, lang: str = "EN", name: str = None) -> Dict[str, Any]:
    """
    Get nomada profile or create if not exists.
    Returns dict with profile data.
    """
    if not did:
        return {"did": None, "lang": lang, "name": None, "is_new": True}

    conn = get_connection()
    c = conn.cursor()

    # Try to get existing
    c.execute("SELECT * FROM nomadas WHERE did = ?", (did,))
    row = c.fetchone()

    if row:
        conn.close()
        return {
            "did": row["did"],
            "lang": row["lang"],
            "name": row["name"],
            "created_at": row["created_at"],
            "is_new": False
        }

    # Create new nomada
    created_at = datetime.now(timezone.utc).isoformat()
    c.execute(
        "INSERT INTO nomadas (did, lang, name, created_at) VALUES (?, ?, ?, ?)",
        (did, lang, name, created_at)
    )
    conn.commit()
    conn.close()

    log.info(f"[MARIA Memory] New nomada created: {did[:8]}...")
    return {
        "did": did,
        "lang": lang,
        "name": name,
        "created_at": created_at,
        "is_new": True
    }


def update_nomada_lang(did: str, lang: str):
    """Update nomada's preferred language."""
    if not did:
        return
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE nomadas SET lang = ? WHERE did = ?", (lang, did))
    conn.commit()
    conn.close()


# ── Preferences ──────────────────────────────────────────────────────────────

def set_preference(did: str, key: str, value: Any):
    """Set a preference for a nomada."""
    if not did:
        return
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    val_str = json.dumps(value) if not isinstance(value, str) else value
    c.execute("""
        INSERT INTO preferences (did, key, value, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(did, key) DO UPDATE SET value = ?, updated_at = ?
    """, (did, key, val_str, now, val_str, now))
    conn.commit()
    conn.close()


def get_preference(did: str, key: str, default: Any = None) -> Any:
    """Get a preference value."""
    if not did:
        return default
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM preferences WHERE did = ? AND key = ?", (did, key))
    row = c.fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row["value"])
        except:
            return row["value"]
    return default


def get_all_preferences(did: str) -> Dict[str, Any]:
    """Get all preferences for a nomada."""
    if not did:
        return {}
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT key, value FROM preferences WHERE did = ?", (did,))
    rows = c.fetchall()
    conn.close()
    prefs = {}
    for row in rows:
        try:
            prefs[row["key"]] = json.loads(row["value"])
        except:
            prefs[row["key"]] = row["value"]
    return prefs


# ── Interactions ─────────────────────────────────────────────────────────────

def log_interaction(
    did: str,
    request_id: str,
    intent_type: str,
    place_name: str,
    rating: int = None,
    feedback: str = None
):
    """Log an interaction for memory and learning."""
    if not did:
        return
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    c.execute("""
        INSERT INTO interactions (did, request_id, intent_type, place_name, rating, feedback, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (did, request_id, intent_type, place_name, rating, feedback, now))
    conn.commit()
    conn.close()


def get_recent_interactions(did: str, limit: int = 10) -> list:
    """Get recent interactions for context."""
    if not did:
        return []
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT intent_type, place_name, rating, timestamp
        FROM interactions
        WHERE did = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (did, limit))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_favorite_types(did: str) -> list:
    """Get most frequent intent types for a nomada."""
    if not did:
        return []
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT intent_type, COUNT(*) as count
        FROM interactions
        WHERE did = ? AND rating >= 4
        GROUP BY intent_type
        ORDER BY count DESC
        LIMIT 3
    """, (did,))
    rows = c.fetchall()
    conn.close()
    return [row["intent_type"] for row in rows]


# ── Interaction Counts ──────────────────────────────────────────────────────

def get_total_interactions(did: str) -> int:
    """Get total interaction count for a DID."""
    if not did:
        return 0
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as total FROM interactions WHERE did = ?", (did,))
    row = c.fetchone()
    conn.close()
    return row["total"] if row else 0


# ── §65 + §91 — Personalized Greeting with Small Talk ────────────────────────

def gerar_saudacao(did: str, lang: str = "DE", weather: str = None, hour: int = None) -> str:
    """
    Generate personalized greeting with natural small talk.

    §65 — Camada 2: MARIA lê o DID
    §71 — Armadura de Seda: NOT CRM language. MARIA is a friend, not a loyalty program.
    §91 — Small Talk Layer: Memory informs behavior, not output.
          "A memória serve para perguntar melhor, não para impressionar."

    The visit count changes the TONE (familiarity), not the CONTENT.
    Instead of announcing "19th visit", ask a contextual question.
    """
    import random
    from datetime import datetime

    n = get_total_interactions(did)
    h = hour if hour is not None else datetime.now().hour

    # Detect time of day for context
    if 5 <= h < 12:
        period = "morning"
    elif 12 <= h < 18:
        period = "afternoon"
    else:
        period = "evening"

    # §91 — Small Talk: Questions based on context, not memory display
    # The more visits, the more casual/familiar the tone
    greetings = {
        "PT": {
            "new": {
                "morning": "Bom dia! Primeira vez por aqui — tens planos para hoje?",
                "afternoon": "Boa tarde! Estás a explorar a zona?",
                "evening": "Boa noite! Procuras algo para esta noite?",
            },
            "familiar": {
                "morning": [
                    "Bom dia! Café primeiro ou directamente ao assunto?",
                    "Bom dia! O que te traz por cá tão cedo?",
                    "Bom dia! Dia cheio pela frente?",
                ],
                "afternoon": [
                    "Boa tarde! Algum plano especial para hoje?",
                    "Boa tarde! O que vamos descobrir?",
                    "Boa tarde! Precisas de uma sugestão?",
                ],
                "evening": [
                    "Boa noite! A planear o dia de amanhã?",
                    "Boa noite! Preciso de te encontrar um sítio?",
                    "Boa noite! Há algo que te apeteça fazer?",
                ],
            }
        },
        "DE": {
            "new": {
                "morning": "Guten Morgen! Zum ersten Mal hier — was hast du heute vor?",
                "afternoon": "Guten Tag! Erkundest du die Gegend?",
                "evening": "Guten Abend! Suchst du etwas für heute Abend?",
            },
            "familiar": {
                "morning": [
                    "Guten Morgen! Erst Kaffee oder direkt loslegen?",
                    "Guten Morgen! Was bringt dich so früh her?",
                    "Guten Morgen! Voller Tag heute?",
                ],
                "afternoon": [
                    "Guten Tag! Etwas Besonderes geplant?",
                    "Guten Tag! Was entdecken wir heute?",
                    "Guten Tag! Brauchst du einen Vorschlag?",
                ],
                "evening": [
                    "Guten Abend! Planst du für morgen?",
                    "Guten Abend! Soll ich dir etwas finden?",
                    "Guten Abend! Worauf hast du Lust?",
                ],
            }
        },
        "EN": {
            "new": {
                "morning": "Good morning! First time here — any plans for today?",
                "afternoon": "Good afternoon! Exploring the area?",
                "evening": "Good evening! Looking for something tonight?",
            },
            "familiar": {
                "morning": [
                    "Good morning! Coffee first or straight to business?",
                    "Good morning! What brings you here so early?",
                    "Good morning! Busy day ahead?",
                ],
                "afternoon": [
                    "Good afternoon! Any special plans today?",
                    "Good afternoon! What shall we discover?",
                    "Good afternoon! Need a suggestion?",
                ],
                "evening": [
                    "Good evening! Planning for tomorrow?",
                    "Good evening! Shall I find you a spot?",
                    "Good evening! Anything you feel like doing?",
                ],
            }
        }
    }

    s = greetings.get(lang, greetings["EN"])

    if n == 0:
        # First visit: welcome + contextual question
        return s["new"].get(period, s["new"]["morning"])
    else:
        # Returning visitor: familiar tone with contextual question
        options = s["familiar"].get(period, s["familiar"]["morning"])
        return random.choice(options)


# ── Context Enrichment ───────────────────────────────────────────────────────

def enrich_context_with_memory(did: str, context: dict) -> dict:
    """
    Enrich context with nomada's memory.
    Used by booking_router to personalize recommendations.
    """
    if not did:
        return context

    profile = get_or_create_nomada(did)
    recent = get_recent_interactions(did, limit=5)
    favorites = get_favorite_types(did)
    prefs = get_all_preferences(did)

    context["nomada"] = {
        "is_new": profile.get("is_new", True),
        "name": profile.get("name"),
        "preferred_lang": profile.get("lang", "EN"),
        "recent_visits": len(recent),
        "favorites": favorites,
        "quiet_preference": prefs.get("quiet", False),
        "family_mode": prefs.get("family", False),
    }

    # Add recent places to avoid repetition
    if recent:
        context["nomada"]["recent_places"] = [r["place_name"] for r in recent[:3]]

    return context


# ═══════════════════════════════════════════════════════════════════════════════
# §98 — MODO NÓMADA v1.1: Travel Preferences
# "A decisão não parte do pedido. Parte da identidade ao longo do tempo."
# ═══════════════════════════════════════════════════════════════════════════════

# Default preferences for new nomadas
DEFAULT_TRAVEL_PREFS = {
    "avoid_stops": True,       # Prefere voos directos
    "price_sensitivity": 0.5,  # 0 = ignora preço, 1 = muito sensível
    "prefer_morning": True,    # Prefere voos de manhã
    "comfort_priority": 0.5,   # 0 = aceita desconforto, 1 = prioriza conforto
    "time_sensitivity": 0.5,   # 0 = tempo não importa, 1 = quer o mais rápido
}


def get_travel_preferences(did: str) -> dict:
    """
    Get travel preferences for a nomada.
    Returns defaults merged with stored preferences.

    Used by MARIA §97/§98 scoring to personalize flight/hotel decisions.
    """
    prefs = DEFAULT_TRAVEL_PREFS.copy()

    if not did:
        return prefs

    # Load stored preferences
    stored = get_all_preferences(did)

    # Merge travel-specific preferences
    for key in DEFAULT_TRAVEL_PREFS.keys():
        if f"travel_{key}" in stored:
            prefs[key] = stored[f"travel_{key}"]

    return prefs


def update_travel_preference(did: str, key: str, value: Any):
    """
    Update a specific travel preference.
    Called when MARIA learns from user behavior.
    """
    if not did or key not in DEFAULT_TRAVEL_PREFS:
        return
    set_preference(did, f"travel_{key}", value)
    log.info(f"[MARIA §98] Updated preference for {did[:20]}...: {key}={value}")


def learn_from_choice(did: str, choice_type: str, chosen: dict, alternatives: list):
    """
    §98 — Learn preferences from user's actual choices.
    Called when user confirms a booking decision.

    Example: If user always picks direct flights even when more expensive,
    increase avoid_stops preference.
    """
    if not did:
        return

    prefs = get_travel_preferences(did)

    if choice_type == "flight":
        # Learn about stop preference
        chosen_direct = chosen.get("direct", False)
        cheaper_with_stops = any(
            not a.get("direct", False) and a.get("price", 999) < chosen.get("price", 0)
            for a in alternatives
        )
        if chosen_direct and cheaper_with_stops:
            # User chose direct even though cheaper option had stops
            new_val = min(1.0, prefs["avoid_stops"] + 0.1 if isinstance(prefs["avoid_stops"], float) else 0.9)
            update_travel_preference(did, "avoid_stops", True)
            update_travel_preference(did, "comfort_priority", new_val)

        # Learn about time preference
        dep_hour = 0
        if "T" in chosen.get("departure", ""):
            try:
                dep_hour = int(chosen["departure"].split("T")[1][:2])
            except:
                pass
        if dep_hour < 10:
            update_travel_preference(did, "prefer_morning", True)
        elif dep_hour > 17:
            update_travel_preference(did, "prefer_morning", False)

        # Learn about price sensitivity
        if alternatives:
            chosen_price = chosen.get("price", 0)
            min_price = min(a.get("price", 999) for a in alternatives)
            if chosen_price <= min_price * 1.1:  # Chose cheapest or near cheapest
                new_sens = min(1.0, prefs["price_sensitivity"] + 0.1)
                update_travel_preference(did, "price_sensitivity", new_sens)

    elif choice_type == "hotel":
        # Learn about comfort vs price
        chosen_rating = chosen.get("rating", chosen.get("stars", 3))
        if chosen_rating >= 4:
            new_comfort = min(1.0, prefs["comfort_priority"] + 0.1)
            update_travel_preference(did, "comfort_priority", new_comfort)


def explain_personalized_decision(choice_type: str, prefs: dict, lang: str = "PT") -> str:
    """
    Generate a brief personalized explanation based on preferences.
    Never invasive, always natural.
    """
    reasons = []

    if choice_type == "flight":
        if prefs.get("avoid_stops") is True or (isinstance(prefs.get("avoid_stops"), float) and prefs["avoid_stops"] > 0.7):
            reasons.append({
                "PT": "evitas escalas",
                "DE": "du vermeidest Zwischenstopps",
                "EN": "you avoid layovers"
            })
        if prefs.get("prefer_morning"):
            reasons.append({
                "PT": "preferes manhã",
                "DE": "du bevorzugst morgens",
                "EN": "you prefer mornings"
            })
        if prefs.get("price_sensitivity", 0.5) > 0.7:
            reasons.append({
                "PT": "valorizas bom preço",
                "DE": "du schätzt gute Preise",
                "EN": "you value good prices"
            })

    if not reasons:
        return ""

    # Pick 1-2 reasons max
    selected = reasons[:2]
    reason_strs = [r.get(lang, r["EN"]) for r in selected]

    templates = {
        "PT": f"Escolhi porque {' e '.join(reason_strs)}.",
        "DE": f"Gewählt, weil {' und '.join(reason_strs)}.",
        "EN": f"Chosen because {' and '.join(reason_strs)}."
    }

    return templates.get(lang, templates["EN"])


# ═══════════════════════════════════════════════════════════════════════════════
# §100 — ANTECIPAÇÃO: Sugerir antes do pedido
# "Eu não decido por ti. Mas não te deixo decidir tarde demais."
# ═══════════════════════════════════════════════════════════════════════════════

def detect_travel_patterns(did: str) -> dict:
    """
    §100 — Detect patterns from user's travel history.

    Patterns detected:
    - Preferred booking lead time (days before travel)
    - Common routes
    - Preferred days of week
    - Preferred time of day
    """
    if not did:
        return {}

    patterns = {
        "common_routes": [],
        "preferred_lead_days": 7,  # default
        "preferred_weekday": None,
        "preferred_time": "morning",
        "trip_frequency": "occasional",
    }

    # Get recent interactions
    interactions = get_recent_interactions(did, limit=20)
    if not interactions:
        return patterns

    # Analyze routes
    routes = {}
    for i in interactions:
        if i.get("intent_type") == "flight":
            route = i.get("place_name", "")  # e.g., "MUC → LIS"
            routes[route] = routes.get(route, 0) + 1

    if routes:
        # Sort by frequency
        sorted_routes = sorted(routes.items(), key=lambda x: x[1], reverse=True)
        patterns["common_routes"] = [r[0] for r in sorted_routes[:3]]

    # Analyze frequency
    if len(interactions) > 10:
        patterns["trip_frequency"] = "frequent"
    elif len(interactions) > 3:
        patterns["trip_frequency"] = "regular"

    return patterns


def should_anticipate(did: str, context: dict, patterns: dict) -> dict:
    """
    §100 — Determine if we should proactively suggest something.

    Returns:
    - should_suggest: bool
    - suggestion_type: str
    - reason: str
    - confidence: float
    """
    result = {
        "should_suggest": False,
        "suggestion_type": None,
        "reason": None,
        "confidence": 0.0,
    }

    if not did or not patterns:
        return result

    # ─── Trigger 1: Time pressure + common route ───
    if context.get("time_pressure") == "high" and patterns.get("common_routes"):
        result["should_suggest"] = True
        result["suggestion_type"] = "quick_flight"
        result["reason"] = "urgent_common_route"
        result["confidence"] = 0.8

    # ─── Trigger 2: Frequent traveler + regular pattern ───
    if patterns.get("trip_frequency") == "frequent":
        result["should_suggest"] = True
        result["suggestion_type"] = "proactive_search"
        result["reason"] = "frequent_traveler"
        result["confidence"] = 0.6

    return result


def generate_anticipation_message(
    suggestion_type: str,
    patterns: dict,
    context: dict,
    lang: str = "PT"
) -> dict:
    """
    §100 — Generate anticipation message with I9 compliance.

    Never executes — always proposes.
    """
    messages = {
        "quick_flight": {
            "PT": {
                "intro": "Percebi que tens pressa.",
                "offer": "Queres que prepare um voo para {route}?",
                "reason": "Costumas fazer esta rota."
            },
            "DE": {
                "intro": "Ich sehe, dass du es eilig hast.",
                "offer": "Soll ich einen Flug nach {route} vorbereiten?",
                "reason": "Das ist eine häufige Route von dir."
            },
            "EN": {
                "intro": "I see you're in a hurry.",
                "offer": "Want me to prepare a flight to {route}?",
                "reason": "This is a common route for you."
            }
        },
        "proactive_search": {
            "PT": {
                "intro": "Com base nas tuas viagens anteriores,",
                "offer": "posso começar a procurar opções para {route}?",
                "reason": "Viajas com frequência."
            },
            "DE": {
                "intro": "Basierend auf deinen früheren Reisen,",
                "offer": "soll ich nach Optionen für {route} suchen?",
                "reason": "Du reist häufig."
            },
            "EN": {
                "intro": "Based on your travel history,",
                "offer": "shall I start looking for options to {route}?",
                "reason": "You travel frequently."
            }
        }
    }

    template = messages.get(suggestion_type, messages["proactive_search"])
    lang_template = template.get(lang, template["EN"])

    # Get most common route
    route = patterns.get("common_routes", [""])[0] if patterns.get("common_routes") else "?"
    if " → " in route:
        route = route.split(" → ")[1]  # Destination only

    return {
        "type": "anticipation",
        "suggestion_type": suggestion_type,
        "message": {
            "intro": lang_template["intro"],
            "offer": lang_template["offer"].format(route=route),
            "reason": lang_template["reason"],
        },
        "full_text": f"{lang_template['intro']} {lang_template['offer'].format(route=route)}",
        "requires_approval": True,  # I9 — sempre requer aprovação
        "route_hint": route,
        "lang": lang,
    }


def log_anticipation(did: str, suggestion_type: str, accepted: bool):
    """
    §100 — Log anticipation outcome for learning.
    """
    if not did:
        return
    set_preference(did, f"anticipation_{suggestion_type}_accepted", accepted)
    log.info(f"[MARIA §100] Anticipation {suggestion_type} {'accepted' if accepted else 'rejected'} by {did[:20]}...")


# ── Initialize on import ─────────────────────────────────────────────────────
init_db()
