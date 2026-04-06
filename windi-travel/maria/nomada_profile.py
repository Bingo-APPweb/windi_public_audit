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

    # §100.5 — MARIA Decisions (Memory Engine)
    c.execute("""
        CREATE TABLE IF NOT EXISTS maria_decisions (
            id TEXT PRIMARY KEY,
            did TEXT NOT NULL,

            decision_type TEXT,          -- flight | hotel | places
            route TEXT,                   -- MUC→LIS
            destination TEXT,             -- LIS

            context_time TEXT,            -- high | normal | low
            context_mode TEXT,            -- urgent | focus | explore | normal

            decision_json TEXT,           -- full decision object
            decision_price REAL,          -- for quick queries
            decision_direct BOOLEAN,      -- for pattern detection
            decision_morning BOOLEAN,     -- departure before 10:00

            accepted BOOLEAN DEFAULT NULL,  -- user confirmed
            ignored BOOLEAN DEFAULT NULL,   -- user ignored

            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            score REAL DEFAULT 0.0        -- quality score for learning
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_decisions_did ON maria_decisions(did)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_decisions_type ON maria_decisions(decision_type)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_decisions_route ON maria_decisions(route)")

    # §107 — Thread Visual Timeline
    c.execute("""
        CREATE TABLE IF NOT EXISTS threads (
            id TEXT PRIMARY KEY,
            did TEXT NOT NULL,
            title TEXT,
            destination TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_threads_did ON threads(did)")

    c.execute("""
        CREATE TABLE IF NOT EXISTS thread_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT NOT NULL,
            entry_type TEXT NOT NULL,
            content TEXT NOT NULL,
            meta TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (thread_id) REFERENCES threads(id)
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_thread_entries_thread ON thread_entries(thread_id)")

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

    # §145.7 — Passive confidence increment (Maria learns from presence)
    # Soft increment: +0.02 per interaction, capped at 1.0
    # This allows memory to become visible after ~5 interactions
    try:
        prefs = get_travel_preferences(did)
        current = prefs.get("learned_confidence", 0.0)
        if current < 1.0:
            new_conf = min(1.0, current + 0.02)
            update_travel_preference(did, "learned_confidence", new_conf)
            log.debug(f"[MARIA §145.7] Passive confidence: {current:.2f} → {new_conf:.2f}")
    except Exception as e:
        log.debug(f"[MARIA §145.7] Confidence update skipped: {e}")


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
    # ─── Preferências base ───
    "avoid_stops": True,       # Prefere voos directos
    "price_sensitivity": 0.5,  # 0 = ignora preço, 1 = muito sensível
    "prefer_morning": True,    # Prefere voos de manhã
    "comfort_priority": 0.5,   # 0 = aceita desconforto, 1 = prioriza conforto
    "time_sensitivity": 0.5,   # 0 = tempo não importa, 1 = quer o mais rápido

    # ─── §104 VOOS — Campos evoluíveis ───
    "direct_bonus": 200,       # Bónus quando voo é directo (100 → 300)
    "layover_penalty": 100,    # Penalidade por escala (50 → 150)
    "duration_weight": 0.5,    # Peso da duração (0.3 → 0.8)
    "price_weight": 1.5,       # Multiplicador do preço (1.0 → 2.5)
    "morning_bonus": 50,       # Bónus por voo de manhã (30 → 80)

    # ─── §104.1 HOTÉIS — Campos evoluíveis ───
    "hotel_rating_weight": 50,   # Peso do rating (30 → 70)
    "hotel_price_weight": 0.5,   # Peso do preço (0.3 → 0.7)
    "hotel_comfort_bonus": 40,   # Bónus por hotel confortável (20 → 60)
    "hotel_location_bonus": 80,  # Bónus por localização central (40 → 120)
    "hotel_quietness_bonus": 40, # Bónus por ambiente tranquilo (20 → 60)

    # ─── §104.1 LUGARES — Campos evoluíveis ───
    "place_distance_weight": 0.5,  # Peso da distância (0.3 → 0.8)
    "place_rating_bonus": 30,      # Bónus por rating alto (15 → 50)
    "place_type_boosts": {         # Bónus por categoria (evita explosão)
        "food": 1.0,               # Restaurantes, cafés, bares
        "essential": 1.0,          # Farmácias, bancos, supermercados
        "leisure": 1.0,            # Museus, parques, praias
    },

    # ─── Confiança global ───
    "learned_confidence": 0.0, # Confiança na personalização (0 → 1)

    # ─── §145.10 Feedback Signals ───
    "feedback_signals": {},    # {intent: score} — positive = +1, negative = -1
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


# ── §108 — Memória Visível ────────────────────────────────────────────────────
def get_visible_memory(prefs: dict, lang: str = "PT") -> list:
    """
    §108 — Get human-readable memory signals for UI display.

    Rules:
    - Max 3 signals (top patterns only)
    - Only show when learned_confidence > 0.3
    - Human language, not technical
    - Trilingual (PT/DE/EN)

    Returns list of strings to display, or empty if nothing to show.
    """
    if prefs is None:
        return []

    # Gate: only show memory if we have learned something
    # §145.7 — Lowered from 0.3 to 0.1 to allow early visibility
    learned_confidence = prefs.get("learned_confidence", 0.0)
    if learned_confidence < 0.1:
        return []

    signals = []

    # ─── FLIGHTS ───
    if prefs.get("direct_bonus", 200) > 240:
        signals.append({
            "PT": "Preferes voos directos",
            "DE": "Du bevorzugst Direktflüge",
            "EN": "You prefer direct flights"
        })

    if prefs.get("morning_bonus", 50) > 65:
        signals.append({
            "PT": "Gostas de partir de manhã",
            "DE": "Du fliegst gerne morgens",
            "EN": "You like to depart in the morning"
        })

    if prefs.get("price_sensitivity", 0.5) > 0.7:
        signals.append({
            "PT": "Valorizas bons preços",
            "DE": "Du achtest auf gute Preise",
            "EN": "You value good prices"
        })

    if prefs.get("layover_penalty", 100) > 130:
        signals.append({
            "PT": "Evitas escalas longas",
            "DE": "Du vermeidest lange Zwischenstopps",
            "EN": "You avoid long layovers"
        })

    # ─── HOTELS ───
    if prefs.get("hotel_location_bonus", 80) > 100:
        signals.append({
            "PT": "Valorizas hotéis bem localizados",
            "DE": "Du schätzt gut gelegene Hotels",
            "EN": "You value well-located hotels"
        })

    if prefs.get("hotel_rating_weight", 50) > 60:
        signals.append({
            "PT": "Preferes hotéis com boa avaliação",
            "DE": "Du bevorzugst gut bewertete Hotels",
            "EN": "You prefer well-rated hotels"
        })

    if prefs.get("hotel_comfort_bonus", 40) > 50:
        signals.append({
            "PT": "O conforto é importante para ti",
            "DE": "Komfort ist dir wichtig",
            "EN": "Comfort is important to you"
        })

    # ─── PLACES ───
    type_boosts = prefs.get("place_type_boosts", {})
    if type_boosts.get("food", 1.0) > 1.2:
        signals.append({
            "PT": "Costumas procurar bons restaurantes",
            "DE": "Du suchst oft nach guten Restaurants",
            "EN": "You often look for good restaurants"
        })

    if type_boosts.get("essential", 1.0) > 1.2:
        signals.append({
            "PT": "Valorizas serviços práticos por perto",
            "DE": "Du schätzt praktische Dienste in der Nähe",
            "EN": "You value practical services nearby"
        })

    # Select top 3 and convert to requested language
    top_signals = signals[:3]
    return [s.get(lang, s.get("EN", "")) for s in top_signals]


def should_show_memory(prefs: dict, session_memory_shown: bool = False) -> bool:
    """
    §108 — Decide if memory should be shown in this interaction.

    Rules:
    - Only show 1x per session (unless pattern changes)
    - Only when learned_confidence > 0.3
    - Only when there's something meaningful to show
    """
    if session_memory_shown:
        return False

    if prefs is None:
        return False

    learned_confidence = prefs.get("learned_confidence", 0.0)
    if learned_confidence < 0.3:
        return False

    # Check if we have any meaningful patterns
    signals = get_visible_memory(prefs, "EN")
    return len(signals) > 0


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
    §104 — Generate a brief personalized explanation based on learned preferences.
    Never invasive, always natural. More human when confidence is high.
    """
    learned_confidence = prefs.get("learned_confidence", 0.0)

    # §104: Se confiança alta, usar linguagem mais humana
    if learned_confidence > 0.5:
        templates = {
            "PT": "Baseado nas tuas decisões anteriores.",
            "DE": "Basierend auf deinen früheren Entscheidungen.",
            "EN": "Based on your previous decisions."
        }
        return templates.get(lang, templates["EN"])

    reasons = []

    if choice_type == "flight":
        # Usar valores evoluídos para detectar preferências fortes
        if prefs.get("direct_bonus", 200) > 220:
            reasons.append({
                "PT": "priorizas voos directos",
                "DE": "du priorisierst Direktflüge",
                "EN": "you prioritize direct flights"
            })
        elif prefs.get("avoid_stops") is True:
            reasons.append({
                "PT": "evitas escalas",
                "DE": "du vermeidest Zwischenstopps",
                "EN": "you avoid layovers"
            })

        if prefs.get("morning_bonus", 50) > 60:
            reasons.append({
                "PT": "gostas de partir cedo",
                "DE": "du fliegst gerne früh",
                "EN": "you like early departures"
            })
        elif prefs.get("prefer_morning"):
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

    if choice_type == "hotel":
        if prefs.get("comfort_priority", 0.5) > 0.7:
            reasons.append({
                "PT": "valorizas conforto",
                "DE": "du schätzt Komfort",
                "EN": "you value comfort"
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


# ═══════════════════════════════════════════════════════════════════════════════
# §100.5 — MEMORY ENGINE: Estrutura que aprende
# "A memória não é histórico. É capacidade de reconhecer padrões."
# ═══════════════════════════════════════════════════════════════════════════════

import uuid
from datetime import timedelta


def time_weight(timestamp_str: str) -> float:
    """
    §100.5 — Calculate temporal weight for a decision.

    Recent decisions have more weight than old ones.
    Formula: max(0.1, 1.0 - (age_days * 0.05))

    - Today: 1.0
    - 1 week ago: 0.65
    - 2 weeks ago: 0.3
    - 3+ weeks ago: 0.1 (minimum floor)
    """
    if not timestamp_str:
        return 0.1

    try:
        # Parse ISO timestamp
        ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        age = now - ts
        age_days = age.days

        # Decay formula
        weight = max(0.1, 1.0 - (age_days * 0.05))
        return round(weight, 2)
    except Exception as e:
        log.warning(f"[MARIA §100.5] time_weight parse error: {e}")
        return 0.1


def save_decision(
    did: str,
    decision_type: str,
    decision: dict,
    context: dict = None,
    route: str = None,
    destination: str = None
) -> str:
    """
    §100.5 — Save a decision to the Memory Engine.

    Args:
        did: User's DID
        decision_type: 'flight' | 'hotel' | 'places'
        decision: Full decision object
        context: Live context (time_pressure, mode)
        route: e.g., "MUC→LIS"
        destination: e.g., "LIS"

    Returns:
        decision_id: UUID of the saved decision
    """
    if not did:
        return None

    conn = get_connection()
    c = conn.cursor()

    decision_id = f"MD-{uuid.uuid4().hex[:12].upper()}"
    now = datetime.now(timezone.utc).isoformat()

    context = context or {}

    # Extract searchable fields from decision
    price = None
    is_direct = None
    is_morning = None

    if decision_type == "flight":
        price = decision.get("price")
        is_direct = decision.get("direct", False)
        # Check if morning departure
        dep = decision.get("departure", "")
        if "T" in dep:
            try:
                hour = int(dep.split("T")[1][:2])
                is_morning = hour < 10
            except:
                pass
    elif decision_type == "hotel":
        price = decision.get("price") or decision.get("pricePerNight")

    c.execute("""
        INSERT INTO maria_decisions (
            id, did, decision_type, route, destination,
            context_time, context_mode,
            decision_json, decision_price, decision_direct, decision_morning,
            timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        decision_id,
        did,
        decision_type,
        route,
        destination,
        context.get("time_pressure", "normal"),
        context.get("mode", "normal"),
        json.dumps(decision),
        price,
        is_direct,
        is_morning,
        now
    ))

    conn.commit()
    conn.close()

    log.info(f"[MARIA §100.5] Saved decision {decision_id} for {did[:20]}...")
    return decision_id


def get_decisions(
    did: str,
    decision_type: str = None,
    route: str = None,
    limit: int = 20
) -> list:
    """
    §100.5 — Get decisions for a DID with optional filters.

    Returns list of decisions with temporal weight applied.
    """
    if not did:
        return []

    conn = get_connection()
    c = conn.cursor()

    query = "SELECT * FROM maria_decisions WHERE did = ?"
    params = [did]

    if decision_type:
        query += " AND decision_type = ?"
        params.append(decision_type)

    if route:
        query += " AND route = ?"
        params.append(route)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    c.execute(query, params)
    rows = c.fetchall()
    conn.close()

    decisions = []
    for row in rows:
        d = dict(row)
        # Add temporal weight
        d["weight"] = time_weight(d.get("timestamp"))
        # Parse decision JSON
        if d.get("decision_json"):
            try:
                d["decision"] = json.loads(d["decision_json"])
            except:
                d["decision"] = {}
        decisions.append(d)

    return decisions


def mark_decision_feedback(decision_id: str, accepted: bool = None, ignored: bool = None):
    """
    §100.5 + §104 — Record user feedback on a decision and evolve preferences.

    Called when user confirms or ignores a MARIA suggestion.
    This is the learning signal.

    §104: Now also applies INCREMENTAL preference adjustments.
    """
    if not decision_id:
        return

    conn = get_connection()
    c = conn.cursor()

    # Get the decision details before updating
    c.execute("SELECT * FROM maria_decisions WHERE id = ?", (decision_id,))
    decision_row = c.fetchone()

    if accepted is not None:
        c.execute(
            "UPDATE maria_decisions SET accepted = ? WHERE id = ?",
            (accepted, decision_id)
        )

    if ignored is not None:
        c.execute(
            "UPDATE maria_decisions SET ignored = ? WHERE id = ?",
            (ignored, decision_id)
        )

    conn.commit()
    conn.close()

    # ─── §104 — Incremental preference evolution ───
    if decision_row:
        did = decision_row["did"] if "did" in decision_row.keys() else None
        if did and (accepted or ignored):
            _evolve_preferences_from_feedback(did, dict(decision_row), accepted, ignored)

    status = "accepted" if accepted else "ignored" if ignored else "updated"
    log.info(f"[MARIA §100.5] Decision {decision_id} marked as {status}")


def _evolve_preferences_from_feedback(did: str, decision: dict, accepted: bool, ignored: bool):
    """
    §104 + §104.1 — Incremental preference evolution based on feedback.

    Small adjustments over time → real personality emerges.
    Diferenciado por tipo (voos, hotéis, lugares) para evitar contaminação cruzada.
    """
    if not did:
        return

    # Get current preferences
    prefs = get_travel_preferences(did)
    decision_type = decision.get("decision_type")

    # ─── §104 FLIGHT feedback ───
    if decision_type == "flight":
        is_direct = decision.get("decision_direct", False)
        is_morning = decision.get("decision_morning", False)
        price = decision.get("decision_price", 0)

        if accepted:
            if is_direct:
                new_bonus = min(300, prefs.get("direct_bonus", 200) + 15)
                update_travel_preference(did, "direct_bonus", new_bonus)
            else:
                new_penalty = max(50, prefs.get("layover_penalty", 100) - 10)
                update_travel_preference(did, "layover_penalty", new_penalty)

            if is_morning:
                new_morning = min(80, prefs.get("morning_bonus", 50) + 8)
                update_travel_preference(did, "morning_bonus", new_morning)

            if price and price < 150:
                new_sens = min(0.9, prefs.get("price_sensitivity", 0.5) + 0.05)
                update_travel_preference(did, "price_sensitivity", new_sens)
            elif price and price > 300:
                new_sens = max(0.2, prefs.get("price_sensitivity", 0.5) - 0.05)
                update_travel_preference(did, "price_sensitivity", new_sens)

            new_conf = min(1.0, prefs.get("learned_confidence", 0) + 0.1)
            update_travel_preference(did, "learned_confidence", new_conf)

        elif ignored:
            if is_direct:
                new_bonus = max(100, prefs.get("direct_bonus", 200) - 10)
                update_travel_preference(did, "direct_bonus", new_bonus)
            new_conf = max(0.0, prefs.get("learned_confidence", 0) - 0.05)
            update_travel_preference(did, "learned_confidence", new_conf)

    # ─── §104.1 HOTEL feedback ───
    elif decision_type == "hotel":
        rating = decision.get("decision_rating", 0)
        price = decision.get("decision_price", 0)

        if accepted:
            # High rating accepted → increase rating weight
            if rating and rating >= 4:
                new_weight = min(70, prefs.get("hotel_rating_weight", 50) + 5)
                update_travel_preference(did, "hotel_rating_weight", new_weight)
                new_comfort = min(60, prefs.get("hotel_comfort_bonus", 40) + 5)
                update_travel_preference(did, "hotel_comfort_bonus", new_comfort)

            # Price learning for hotels
            if price and price < 80:
                new_weight = min(0.7, prefs.get("hotel_price_weight", 0.5) + 0.05)
                update_travel_preference(did, "hotel_price_weight", new_weight)
            elif price and price > 150:
                new_weight = max(0.3, prefs.get("hotel_price_weight", 0.5) - 0.05)
                update_travel_preference(did, "hotel_price_weight", new_weight)

            new_conf = min(1.0, prefs.get("learned_confidence", 0) + 0.08)
            update_travel_preference(did, "learned_confidence", new_conf)

        elif ignored:
            new_conf = max(0.0, prefs.get("learned_confidence", 0) - 0.04)
            update_travel_preference(did, "learned_confidence", new_conf)

    # ─── §104.1 PLACE feedback ───
    elif decision_type in ["place", "places"]:
        place_type = decision.get("decision_place_type", "")
        rating = decision.get("decision_rating", 0)

        if accepted:
            # High rating place → increase rating bonus
            if rating and rating >= 4:
                new_bonus = min(50, prefs.get("place_rating_bonus", 30) + 5)
                update_travel_preference(did, "place_rating_bonus", new_bonus)

            # Category boost evolution
            type_boosts = prefs.get("place_type_boosts", {"food": 1.0, "essential": 1.0, "leisure": 1.0})
            category = _classify_place_category(place_type)
            if category in type_boosts:
                new_boost = min(1.5, type_boosts[category] + 0.1)
                type_boosts[category] = new_boost
                update_travel_preference(did, "place_type_boosts", type_boosts)

            new_conf = min(1.0, prefs.get("learned_confidence", 0) + 0.06)
            update_travel_preference(did, "learned_confidence", new_conf)

        elif ignored:
            new_conf = max(0.0, prefs.get("learned_confidence", 0) - 0.03)
            update_travel_preference(did, "learned_confidence", new_conf)

    log.info(f"[MARIA §104.1] Preferences evolved for {did[:20]}... (type={decision_type}, accepted={accepted})")


def _classify_place_category(place_type: str) -> str:
    """§104.1 — Classify place type into category (evita explosão de dimensões)."""
    food_types = ["restaurant", "cafe", "bar", "bakery", "food"]
    essential_types = ["pharmacy", "bank", "supermarket", "hospital", "atm", "gas_station"]
    leisure_types = ["museum", "park", "beach", "tourist_attraction", "spa", "gym"]

    place_type_lower = (place_type or "").lower()

    if any(t in place_type_lower for t in food_types):
        return "food"
    elif any(t in place_type_lower for t in essential_types):
        return "essential"
    elif any(t in place_type_lower for t in leisure_types):
        return "leisure"
    return "food"  # default


def detect_patterns_from_decisions(did: str) -> dict:
    """
    §100.5 — Advanced pattern detection from decision history.

    Applies temporal weighting: recent decisions count more.
    Returns patterns that can be used for personalization and anticipation.
    """
    if not did:
        return {}

    decisions = get_decisions(did, limit=50)

    if not decisions:
        return {
            "has_history": False,
            "confidence": 0.0,
        }

    patterns = {
        "has_history": True,
        "total_decisions": len(decisions),
        "confidence": 0.0,

        # Flight patterns
        "prefers_direct": None,
        "prefers_morning": None,
        "avg_price_flight": None,
        "common_routes": [],
        "common_destinations": [],

        # Acceptance patterns
        "acceptance_rate": None,
        "ignore_rate": None,

        # Context patterns
        "urgent_mode_frequency": 0.0,
    }

    # ─── Analyze flights ───
    flights = [d for d in decisions if d.get("decision_type") == "flight"]
    if flights:
        # Weighted direct preference
        direct_score = 0.0
        total_weight = 0.0
        for f in flights:
            w = f.get("weight", 1.0)
            total_weight += w
            if f.get("decision_direct"):
                direct_score += w

        if total_weight > 0:
            direct_ratio = direct_score / total_weight
            patterns["prefers_direct"] = direct_ratio > 0.6

        # Weighted morning preference
        morning_score = 0.0
        morning_weight = 0.0
        for f in flights:
            if f.get("decision_morning") is not None:
                w = f.get("weight", 1.0)
                morning_weight += w
                if f.get("decision_morning"):
                    morning_score += w

        if morning_weight > 0:
            morning_ratio = morning_score / morning_weight
            patterns["prefers_morning"] = morning_ratio > 0.5

        # Average price (weighted)
        prices = []
        for f in flights:
            if f.get("decision_price"):
                prices.append(f["decision_price"] * f.get("weight", 1.0))
        if prices:
            patterns["avg_price_flight"] = round(sum(prices) / len(prices), 2)

        # Common routes (weighted frequency)
        route_scores = {}
        for f in flights:
            route = f.get("route")
            if route:
                w = f.get("weight", 1.0)
                route_scores[route] = route_scores.get(route, 0) + w

        if route_scores:
            sorted_routes = sorted(route_scores.items(), key=lambda x: x[1], reverse=True)
            patterns["common_routes"] = [r[0] for r in sorted_routes[:5]]

        # Common destinations
        dest_scores = {}
        for f in flights:
            dest = f.get("destination")
            if dest:
                w = f.get("weight", 1.0)
                dest_scores[dest] = dest_scores.get(dest, 0) + w

        if dest_scores:
            sorted_dests = sorted(dest_scores.items(), key=lambda x: x[1], reverse=True)
            patterns["common_destinations"] = [d[0] for d in sorted_dests[:5]]

    # ─── Acceptance patterns ───
    accepted_count = sum(1 for d in decisions if d.get("accepted") is True)
    ignored_count = sum(1 for d in decisions if d.get("ignored") is True)
    feedback_total = accepted_count + ignored_count

    if feedback_total > 0:
        patterns["acceptance_rate"] = round(accepted_count / feedback_total, 2)
        patterns["ignore_rate"] = round(ignored_count / feedback_total, 2)

    # ─── Context patterns ───
    urgent_count = sum(1 for d in decisions if d.get("context_time") == "high")
    if decisions:
        patterns["urgent_mode_frequency"] = round(urgent_count / len(decisions), 2)

    # ─── Confidence score ───
    # Higher confidence with more data and more feedback
    data_score = min(1.0, len(decisions) / 20)  # Max at 20 decisions
    feedback_score = min(1.0, feedback_total / 10) if feedback_total else 0
    patterns["confidence"] = round((data_score * 0.6) + (feedback_score * 0.4), 2)

    return patterns


def get_preference_adjustments(did: str) -> dict:
    """
    §100.5 — Get learned preference adjustments from decision history.

    Returns adjustments that should be applied to DEFAULT_TRAVEL_PREFS
    based on actual user behavior.
    """
    patterns = detect_patterns_from_decisions(did)

    adjustments = {}

    if patterns.get("confidence", 0) < 0.3:
        return adjustments  # Not enough data

    # Direct preference
    if patterns.get("prefers_direct") is not None:
        adjustments["avoid_stops"] = patterns["prefers_direct"]

    # Morning preference
    if patterns.get("prefers_morning") is not None:
        adjustments["prefer_morning"] = patterns["prefers_morning"]

    # Price sensitivity (if avg_price is low, user is price-sensitive)
    if patterns.get("avg_price_flight"):
        avg = patterns["avg_price_flight"]
        if avg < 100:
            adjustments["price_sensitivity"] = 0.8
        elif avg < 200:
            adjustments["price_sensitivity"] = 0.6
        elif avg > 400:
            adjustments["price_sensitivity"] = 0.3

    return adjustments


def get_enhanced_travel_preferences(did: str) -> dict:
    """
    §100.5 — Get travel preferences with Memory Engine adjustments.

    Combines:
    1. Default preferences
    2. Explicitly stored preferences
    3. Learned adjustments from decision history
    """
    # Start with defaults
    prefs = DEFAULT_TRAVEL_PREFS.copy()

    if not did:
        return prefs

    # Layer 1: Stored preferences (explicit)
    stored = get_all_preferences(did)
    for key in DEFAULT_TRAVEL_PREFS.keys():
        if f"travel_{key}" in stored:
            prefs[key] = stored[f"travel_{key}"]

    # Layer 2: Learned adjustments (implicit from behavior)
    adjustments = get_preference_adjustments(did)
    for key, value in adjustments.items():
        # Learned behavior can override defaults but not explicit preferences
        if f"travel_{key}" not in stored:
            prefs[key] = value

    return prefs


def get_decision_stats(did: str) -> dict:
    """
    §100.5 — Get statistics about a user's decisions.

    Useful for debugging and understanding user behavior.
    """
    if not did:
        return {}

    conn = get_connection()
    c = conn.cursor()

    stats = {}

    # Total decisions
    c.execute("SELECT COUNT(*) FROM maria_decisions WHERE did = ?", (did,))
    stats["total"] = c.fetchone()[0]

    # By type
    c.execute("""
        SELECT decision_type, COUNT(*) as count
        FROM maria_decisions
        WHERE did = ?
        GROUP BY decision_type
    """, (did,))
    stats["by_type"] = {row["decision_type"]: row["count"] for row in c.fetchall()}

    # Acceptance rate
    c.execute("""
        SELECT
            SUM(CASE WHEN accepted = 1 THEN 1 ELSE 0 END) as accepted,
            SUM(CASE WHEN ignored = 1 THEN 1 ELSE 0 END) as ignored
        FROM maria_decisions
        WHERE did = ?
    """, (did,))
    row = c.fetchone()
    stats["accepted"] = row["accepted"] or 0
    stats["ignored"] = row["ignored"] or 0

    # Recent activity
    c.execute("""
        SELECT COUNT(*)
        FROM maria_decisions
        WHERE did = ? AND timestamp > datetime('now', '-7 days')
    """, (did,))
    stats["last_7_days"] = c.fetchone()[0]

    conn.close()
    return stats


# ══════════════════════════════════════════════════════════════════════════════
# §107 — THREAD VISUAL TIMELINE
# "Mostrar evolução, não histórico"
# ══════════════════════════════════════════════════════════════════════════════

import uuid

def create_thread(did: str, title: str, destination: str = None) -> str:
    """
    §107 — Create a new thread for a journey.

    Returns thread_id.
    """
    if not did:
        return None

    thread_id = f"TH-{uuid.uuid4().hex[:12].upper()}"
    now = datetime.now(timezone.utc).isoformat()

    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO threads (id, did, title, destination, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (thread_id, did, title, destination, now, now))
    conn.commit()
    conn.close()

    log.info(f"[MARIA Thread] Created: {thread_id} — {title}")
    return thread_id


def get_active_thread(did: str, destination: str = None) -> dict:
    """
    §107 — Get or create active thread for destination.

    If a recent thread (< 24h) exists for same destination, reuse it.
    Otherwise create new.
    """
    if not did:
        return None

    conn = get_connection()
    c = conn.cursor()

    # Look for recent active thread (same destination, < 24h)
    if destination:
        c.execute("""
            SELECT * FROM threads
            WHERE did = ?
              AND destination = ?
              AND status = 'active'
              AND datetime(updated_at) > datetime('now', '-24 hours')
            ORDER BY updated_at DESC
            LIMIT 1
        """, (did, destination))
    else:
        # No destination — get most recent active
        c.execute("""
            SELECT * FROM threads
            WHERE did = ?
              AND status = 'active'
              AND datetime(updated_at) > datetime('now', '-24 hours')
            ORDER BY updated_at DESC
            LIMIT 1
        """, (did,))

    row = c.fetchone()
    conn.close()

    if row:
        return dict(row)

    # Create new thread
    title = f"Viagem → {destination}" if destination else "Nova viagem"
    thread_id = create_thread(did, title, destination)

    return {
        "id": thread_id,
        "did": did,
        "title": title,
        "destination": destination,
        "status": "active"
    }


def add_thread_entry(
    thread_id: str,
    entry_type: str,
    content: str,
    meta: dict = None
) -> int:
    """
    §107 — Add entry to thread.

    entry_type: "request" | "decision" | "memory" | "context"
    content: human-readable text
    meta: optional JSON metadata
    """
    if not thread_id or not entry_type or not content:
        return None

    conn = get_connection()
    c = conn.cursor()

    now = datetime.now(timezone.utc).isoformat()
    meta_json = json.dumps(meta) if meta else None

    c.execute("""
        INSERT INTO thread_entries (thread_id, entry_type, content, meta, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (thread_id, entry_type, content, meta_json, now))

    entry_id = c.lastrowid

    # Update thread timestamp
    c.execute("UPDATE threads SET updated_at = ? WHERE id = ?", (now, thread_id))

    conn.commit()
    conn.close()

    return entry_id


def get_thread_timeline(thread_id: str) -> list:
    """
    §107 — Get all entries for a thread in chronological order.

    Returns list of entry dicts.
    """
    if not thread_id:
        return []

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT id, entry_type, content, meta, timestamp
        FROM thread_entries
        WHERE thread_id = ?
        ORDER BY timestamp ASC
    """, (thread_id,))

    entries = []
    for row in c.fetchall():
        entry = {
            "id": row["id"],
            "type": row["entry_type"],
            "content": row["content"],
            "timestamp": row["timestamp"]
        }
        if row["meta"]:
            try:
                entry["meta"] = json.loads(row["meta"])
            except:
                pass
        entries.append(entry)

    conn.close()
    return entries


def get_user_threads(did: str, limit: int = 10) -> list:
    """
    §107 — Get recent threads for a user.

    Returns list of thread dicts with entry count.
    """
    if not did:
        return []

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT t.*,
               (SELECT COUNT(*) FROM thread_entries WHERE thread_id = t.id) as entry_count
        FROM threads t
        WHERE t.did = ?
        ORDER BY t.updated_at DESC
        LIMIT ?
    """, (did, limit))

    threads = []
    for row in c.fetchall():
        threads.append({
            "id": row["id"],
            "title": row["title"],
            "destination": row["destination"],
            "status": row["status"],
            "entry_count": row["entry_count"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        })

    conn.close()
    return threads


def get_thread_with_timeline(thread_id: str) -> dict:
    """
    §107 — Get thread with all entries.

    Returns thread dict with 'entries' list.
    """
    if not thread_id:
        return None

    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM threads WHERE id = ?", (thread_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return None

    thread = dict(row)
    thread["entries"] = get_thread_timeline(thread_id)
    return thread


def close_thread(thread_id: str):
    """
    §107 — Mark thread as closed.
    """
    if not thread_id:
        return

    conn = get_connection()
    c = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    c.execute(
        "UPDATE threads SET status = 'closed', updated_at = ? WHERE id = ?",
        (now, thread_id)
    )
    conn.commit()
    conn.close()


# ── Initialize on import ─────────────────────────────────────────────────────
init_db()
