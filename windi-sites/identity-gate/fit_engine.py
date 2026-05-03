"""
W-FIT-001 — FIT Engine: Adaptive Maturity System
=================================================
§5 FIT ENGINE — Invisible Operational Maturity

Port: :8192 (via W-SITES-001 router)
Invariants: I9, I11, I14

Concept:
  The system measures when a human is ready to operate with responsibility
  — without ever asking.

Layers:
  1. LIVE        → passive observation (FIT 0-14)
  2. INTERACTIVE → micro-decisions (FIT 15-34)
  3. GUIDED      → semi-autonomy (FIT 35-59)
  4. BUILDER     → real autonomy (FIT 60-84)
  5. SOVEREIGN   → institutional operator (FIT 85+)

Guardrails (NON-NEGOTIABLE):
  ❌ Not a surveillance system
  ❌ Not infantile gamification
  ❌ Never breaks I9 (FIT never decides for human)

Liga IA+H · Kempten, Bavaria · 2026
"AI processes. Human decides. WINDI guarantees."
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime, timezone
from enum import Enum
import sqlite3
import uuid
import json

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

FIT_DB_PATH = "/opt/windi/windi-sites/identity-gate/fit_engine.db"
VERSION = "v0.1.0"

# FIT Weights (Governance and Decision have higher weight)
FIT_WEIGHTS = {
    "presence": 0.15,
    "decision": 0.20,
    "consistency": 0.15,
    "recovery": 0.15,
    "autonomy": 0.15,
    "governance": 0.20
}

# Layer thresholds (invisible to user)
FIT_THRESHOLDS = {
    "live": 0,           # Layer 1: passive
    "interactive": 15,   # Layer 2: micro-decisions
    "guided": 35,        # Layer 3: semi-autonomy
    "builder": 60,       # Layer 4: real autonomy
    "sovereign": 85      # Layer 5: institutional operator
}

# ═══════════════════════════════════════════════════════════════════════════
# DATABASE SCHEMA
# ═══════════════════════════════════════════════════════════════════════════

def init_fit_db():
    """Initialize FIT Engine database with required tables."""
    conn = sqlite3.connect(FIT_DB_PATH)
    cursor = conn.cursor()

    # FIT Events table (atomic events)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fit_events (
            id TEXT PRIMARY KEY,
            did TEXT NOT NULL,
            session_id TEXT NOT NULL,
            layer TEXT NOT NULL,
            event_type TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            duration_ms INTEGER DEFAULT 0,
            hesitation_ms INTEGER DEFAULT 0,
            input_changes INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            component TEXT,
            complexity TEXT DEFAULT 'low',
            template_id TEXT,
            metadata TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # FIT Scores table (calculated per DID)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fit_scores (
            did TEXT PRIMARY KEY,
            presence REAL DEFAULT 0.0,
            decision REAL DEFAULT 0.0,
            consistency REAL DEFAULT 0.0,
            recovery REAL DEFAULT 0.0,
            autonomy REAL DEFAULT 0.0,
            governance REAL DEFAULT 0.0,
            fit_score REAL DEFAULT 0.0,
            fit_level INTEGER DEFAULT 1,
            total_events INTEGER DEFAULT 0,
            last_event_at TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # FIT Milestones table (for Ledger proof, optional)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fit_milestones (
            id TEXT PRIMARY KEY,
            did TEXT NOT NULL,
            level_reached INTEGER NOT NULL,
            score_at_milestone REAL NOT NULL,
            receipt_id TEXT,
            timestamp TEXT NOT NULL
        )
    """)

    # Indices for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fit_events_did ON fit_events(did)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fit_events_session ON fit_events(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fit_events_timestamp ON fit_events(timestamp)")

    conn.commit()
    conn.close()
    print("[FIT-ENGINE] Database initialized")

# Initialize on import
init_fit_db()

# ═══════════════════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════════════════

class FitLayer(str, Enum):
    LIVE = "LIVE"
    INTERACTIVE = "INTERACTIVE"
    GUIDED = "GUIDED"
    BUILDER = "BUILDER"

class FitEventType(str, Enum):
    VIEW = "view"
    EDIT = "edit"
    DECISION = "decision"
    ERROR = "error"
    SUBMIT = "submit"
    RECOVERY = "recovery"

class FitEventMetrics(BaseModel):
    duration_ms: int = Field(default=0, ge=0, description="Active time in milliseconds")
    hesitation_ms: int = Field(default=0, ge=0, description="Time before first action")
    input_changes: int = Field(default=0, ge=0, description="Number of input modifications")
    error_count: int = Field(default=0, ge=0, description="Errors during interaction")

class FitEventContext(BaseModel):
    component: Optional[str] = Field(default=None, description="UI component identifier")
    complexity: Literal["low", "medium", "high"] = Field(default="low")
    template_id: Optional[str] = Field(default=None)

class FitEventCreate(BaseModel):
    """Atomic FIT event from frontend."""
    session_id: str = Field(..., description="Browser session UUID")
    layer: FitLayer = Field(..., description="Current operational layer")
    event_type: FitEventType = Field(..., description="Type of interaction")
    metrics: FitEventMetrics = Field(default_factory=FitEventMetrics)
    context: FitEventContext = Field(default_factory=FitEventContext)
    metadata: Optional[Dict[str, Any]] = Field(default=None)

class FitScoreResponse(BaseModel):
    """FIT score for a DID (internal use only)."""
    did: str
    fit_score: float
    fit_level: int
    layer_name: str
    dimensions: Dict[str, float]
    total_events: int
    capabilities: List[str]

# ═══════════════════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════════════════

fit_router = APIRouter(prefix="/fit", tags=["FIT Engine"])

def get_fit_db():
    """Get FIT database connection with row factory."""
    conn = sqlite3.connect(FIT_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_caller_did(request: Request) -> Optional[str]:
    """Extract DID from request headers."""
    return request.headers.get("X-WINDI-DID")

# ═══════════════════════════════════════════════════════════════════════════
# FIT CALCULATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════

def calculate_fit_dimensions(did: str, conn: sqlite3.Connection) -> Dict[str, float]:
    """
    Calculate FIT dimensions from event history.

    This is where behavior becomes signal.
    """
    cursor = conn.cursor()

    # Get recent events (last 30 days)
    cursor.execute("""
        SELECT * FROM fit_events
        WHERE did = ?
        AND datetime(timestamp) > datetime('now', '-30 days')
        ORDER BY timestamp DESC
    """, (did,))
    events = cursor.fetchall()

    if not events:
        return {
            "presence": 0.0,
            "decision": 0.0,
            "consistency": 0.0,
            "recovery": 0.0,
            "autonomy": 0.0,
            "governance": 0.0
        }

    # ─── PRESENCE ───────────────────────────────────────────────────────────
    # Based on: active time, return frequency, interaction depth
    total_duration = sum(e["duration_ms"] for e in events)
    unique_sessions = len(set(e["session_id"] for e in events))
    view_events = len([e for e in events if e["event_type"] == "view"])

    # Normalize: 1 hour active time = 0.5, 10 sessions = 0.3, 50 views = 0.2
    presence_time = min(total_duration / (60 * 60 * 1000), 1.0) * 0.5
    presence_return = min(unique_sessions / 10, 1.0) * 0.3
    presence_depth = min(view_events / 50, 1.0) * 0.2
    presence = presence_time + presence_return + presence_depth

    # ─── DECISION QUALITY ───────────────────────────────────────────────────
    # Based on: corrections / total decisions
    decision_events = [e for e in events if e["event_type"] == "decision"]
    if decision_events:
        total_decisions = len(decision_events)
        corrections = sum(e["input_changes"] for e in decision_events)
        # More corrections = lower quality (but not zero)
        decision = max(0.2, 1 - (corrections / (total_decisions * 3)))
    else:
        decision = 0.0

    # ─── CONSISTENCY ────────────────────────────────────────────────────────
    # Based on: stable patterns vs erratic behavior
    submit_events = [e for e in events if e["event_type"] == "submit"]
    if len(submit_events) >= 3:
        # Check hesitation variance (stable = low variance)
        hesitations = [e["hesitation_ms"] for e in submit_events]
        avg_hesitation = sum(hesitations) / len(hesitations)
        variance = sum((h - avg_hesitation) ** 2 for h in hesitations) / len(hesitations)
        # Lower variance = higher consistency
        consistency = max(0.2, 1 - min(variance / 10000000, 0.8))
    else:
        consistency = 0.3  # Default for new users

    # ─── RECOVERY ───────────────────────────────────────────────────────────
    # Based on: successful recoveries / total errors
    error_events = [e for e in events if e["event_type"] == "error"]
    recovery_events = [e for e in events if e["event_type"] == "recovery"]
    if error_events:
        recovery = min(len(recovery_events) / len(error_events), 1.0)
    else:
        recovery = 1.0  # No errors = perfect recovery

    # ─── AUTONOMY ───────────────────────────────────────────────────────────
    # Based on: independent actions vs guided actions
    # High complexity events without errors = autonomy
    high_complexity = [e for e in events if e["complexity"] == "high"]
    if events:
        autonomy_ratio = len(high_complexity) / len(events)
        error_in_complex = len([e for e in high_complexity if e["error_count"] > 0])
        if high_complexity:
            autonomy = autonomy_ratio * (1 - error_in_complex / len(high_complexity))
        else:
            autonomy = 0.1
    else:
        autonomy = 0.0

    # ─── GOVERNANCE ─────────────────────────────────────────────────────────
    # Based on: compliant actions / total actions (I9 adherence)
    # Submit without excessive changes = governance compliance
    if submit_events:
        compliant = len([e for e in submit_events if e["input_changes"] <= 2])
        governance = compliant / len(submit_events)
    else:
        governance = 0.5  # Neutral for new users

    return {
        "presence": round(min(presence, 1.0), 3),
        "decision": round(min(decision, 1.0), 3),
        "consistency": round(min(consistency, 1.0), 3),
        "recovery": round(min(recovery, 1.0), 3),
        "autonomy": round(min(autonomy, 1.0), 3),
        "governance": round(min(governance, 1.0), 3)
    }

def calculate_fit_score(dimensions: Dict[str, float]) -> float:
    """Calculate composite FIT score from dimensions."""
    score = sum(dimensions[k] * FIT_WEIGHTS[k] for k in FIT_WEIGHTS)
    return round(score * 100, 1)

def get_fit_level(score: float) -> int:
    """Determine FIT level from score."""
    if score >= FIT_THRESHOLDS["sovereign"]:
        return 5
    elif score >= FIT_THRESHOLDS["builder"]:
        return 4
    elif score >= FIT_THRESHOLDS["guided"]:
        return 3
    elif score >= FIT_THRESHOLDS["interactive"]:
        return 2
    else:
        return 1

def get_layer_name(level: int) -> str:
    """Get human-readable layer name."""
    names = {1: "LIVE", 2: "INTERACTIVE", 3: "GUIDED", 4: "BUILDER", 5: "SOVEREIGN"}
    return names.get(level, "LIVE")

def get_capabilities(level: int) -> List[str]:
    """Get capabilities unlocked at this level (invisible to user)."""
    caps = {
        1: ["view_sites", "browse_templates"],
        2: ["edit_fields", "micro_decisions", "interactive_mode"],
        3: ["create_low", "guided_templates", "basic_export"],
        4: ["create_med", "create_high", "full_export", "custom_domains"],
        5: ["sovereign_mode", "enterprise_features", "api_access", "governance_tools"]
    }
    # Cumulative capabilities
    result = []
    for l in range(1, level + 1):
        result.extend(caps.get(l, []))
    return result

# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@fit_router.get("/health")
async def fit_health():
    """FIT Engine health check."""
    return {
        "service": "W-FIT-001",
        "version": VERSION,
        "status": "operational",
        "invariants": ["I9", "I11", "I14"],
        "note": "Measures maturity without asking"
    }

@fit_router.post("/collect")
async def collect_fit_event(
    event: FitEventCreate,
    request: Request
):
    """
    Collect a FIT event from frontend.

    This is the entry point for all behavioral data.
    Lightweight, invisible, meaningful.
    """
    caller_did = get_caller_did(request)
    if not caller_did:
        # Anonymous users get tracked by session only (no DID score)
        # Still collect for aggregate analysis
        caller_did = f"anon:{event.session_id[:8]}"

    event_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    conn = get_fit_db()
    cursor = conn.cursor()

    try:
        # Store event
        cursor.execute("""
            INSERT INTO fit_events (
                id, did, session_id, layer, event_type, timestamp,
                duration_ms, hesitation_ms, input_changes, error_count,
                component, complexity, template_id, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id,
            caller_did,
            event.session_id,
            event.layer.value,
            event.event_type.value,
            now,
            event.metrics.duration_ms,
            event.metrics.hesitation_ms,
            event.metrics.input_changes,
            event.metrics.error_count,
            event.context.component,
            event.context.complexity,
            event.context.template_id,
            json.dumps(event.metadata) if event.metadata else None
        ))

        # Recalculate FIT score for this DID (if not anonymous)
        if not caller_did.startswith("anon:"):
            dimensions = calculate_fit_dimensions(caller_did, conn)
            fit_score = calculate_fit_score(dimensions)
            fit_level = get_fit_level(fit_score)

            # Get event count
            cursor.execute("SELECT COUNT(*) FROM fit_events WHERE did = ?", (caller_did,))
            total_events = cursor.fetchone()[0]

            # Upsert FIT score
            cursor.execute("""
                INSERT INTO fit_scores (
                    did, presence, decision, consistency, recovery, autonomy, governance,
                    fit_score, fit_level, total_events, last_event_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(did) DO UPDATE SET
                    presence = excluded.presence,
                    decision = excluded.decision,
                    consistency = excluded.consistency,
                    recovery = excluded.recovery,
                    autonomy = excluded.autonomy,
                    governance = excluded.governance,
                    fit_score = excluded.fit_score,
                    fit_level = excluded.fit_level,
                    total_events = excluded.total_events,
                    last_event_at = excluded.last_event_at,
                    updated_at = excluded.updated_at
            """, (
                caller_did,
                dimensions["presence"],
                dimensions["decision"],
                dimensions["consistency"],
                dimensions["recovery"],
                dimensions["autonomy"],
                dimensions["governance"],
                fit_score,
                fit_level,
                total_events,
                now,
                now
            ))

        conn.commit()

        # Return minimal response (invisible tracking)
        return {"ok": True, "event_id": event_id}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"FIT collect failed: {str(e)}")
    finally:
        conn.close()

@fit_router.get("/score")
async def get_fit_score_endpoint(request: Request):
    """
    Get FIT score for current DID.

    INTERNAL USE ONLY — never expose raw score to user.
    Used by other services to check capabilities.
    """
    caller_did = get_caller_did(request)
    if not caller_did:
        raise HTTPException(status_code=401, detail="DID required")

    conn = get_fit_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM fit_scores WHERE did = ?", (caller_did,))
        row = cursor.fetchone()

        if not row:
            # New user, calculate from events
            dimensions = calculate_fit_dimensions(caller_did, conn)
            fit_score = calculate_fit_score(dimensions)
            fit_level = get_fit_level(fit_score)
            total_events = 0
        else:
            dimensions = {
                "presence": row["presence"],
                "decision": row["decision"],
                "consistency": row["consistency"],
                "recovery": row["recovery"],
                "autonomy": row["autonomy"],
                "governance": row["governance"]
            }
            fit_score = row["fit_score"]
            fit_level = row["fit_level"]
            total_events = row["total_events"]

        return FitScoreResponse(
            did=caller_did,
            fit_score=fit_score,
            fit_level=fit_level,
            layer_name=get_layer_name(fit_level),
            dimensions=dimensions,
            total_events=total_events,
            capabilities=get_capabilities(fit_level)
        )

    finally:
        conn.close()

@fit_router.get("/gate/{capability}")
async def check_capability(capability: str, request: Request):
    """
    Check if DID has a specific capability.

    Used by other services to gate features invisibly.
    """
    caller_did = get_caller_did(request)
    if not caller_did:
        return {"allowed": False, "reason": "no_did"}

    conn = get_fit_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT fit_level FROM fit_scores WHERE did = ?", (caller_did,))
        row = cursor.fetchone()

        if not row:
            level = 1
        else:
            level = row["fit_level"]

        caps = get_capabilities(level)
        allowed = capability in caps

        return {
            "allowed": allowed,
            "capability": capability,
            "level": level,
            "layer": get_layer_name(level)
        }

    finally:
        conn.close()

@fit_router.get("/stats")
async def fit_stats():
    """
    Aggregate FIT statistics (admin/analytics).
    """
    conn = get_fit_db()
    cursor = conn.cursor()

    try:
        # Total events
        cursor.execute("SELECT COUNT(*) FROM fit_events")
        total_events = cursor.fetchone()[0]

        # Total DIDs with scores
        cursor.execute("SELECT COUNT(*) FROM fit_scores")
        total_dids = cursor.fetchone()[0]

        # Level distribution
        cursor.execute("""
            SELECT fit_level, COUNT(*) as count
            FROM fit_scores
            GROUP BY fit_level
        """)
        levels = {row[0]: row[1] for row in cursor.fetchall()}

        # Average score
        cursor.execute("SELECT AVG(fit_score) FROM fit_scores")
        avg_score = cursor.fetchone()[0] or 0

        return {
            "total_events": total_events,
            "total_dids": total_dids,
            "avg_fit_score": round(avg_score, 1),
            "level_distribution": {
                "LIVE": levels.get(1, 0),
                "INTERACTIVE": levels.get(2, 0),
                "GUIDED": levels.get(3, 0),
                "BUILDER": levels.get(4, 0),
                "SOVEREIGN": levels.get(5, 0)
            }
        }

    finally:
        conn.close()

# ═══════════════════════════════════════════════════════════════════════════
# §5.1 TRANSPARENCY ENDPOINT — /fit/me
# ═══════════════════════════════════════════════════════════════════════════
# Constitutional requirement: User must be able to see their own FIT.
# "User is author, not product" — if you measure without showing, you're Google.
# ═══════════════════════════════════════════════════════════════════════════

def get_layer_description(level: int) -> str:
    """Human-readable description of each layer."""
    descriptions = {
        1: "You're exploring. The system is learning your patterns.",
        2: "You're making decisions. Interactive features are available.",
        3: "You're building with guidance. Templates and basic creation unlocked.",
        4: "You're operating autonomously. Full creation capabilities active.",
        5: "You're a sovereign operator. Enterprise and governance tools available."
    }
    return descriptions.get(level, "Unknown layer")

def get_next_layer_hint(level: int, dimensions: Dict[str, float]) -> Optional[Dict[str, Any]]:
    """What the user needs to reach the next layer."""
    if level >= 5:
        return None  # Already at max

    next_level = level + 1
    next_threshold = list(FIT_THRESHOLDS.values())[next_level]
    next_name = get_layer_name(next_level)

    # Find weakest dimension
    weakest = min(dimensions.items(), key=lambda x: x[1])

    return {
        "next_layer": next_name,
        "threshold": next_threshold,
        "hint": f"Your '{weakest[0]}' dimension ({weakest[1]:.1%}) has room to grow.",
        "suggestion": get_dimension_suggestion(weakest[0])
    }

def get_dimension_suggestion(dimension: str) -> str:
    """Concrete suggestion for improving a dimension."""
    suggestions = {
        "presence": "Spend more time exploring and returning to the platform.",
        "decision": "Make deliberate choices — fewer corrections means clearer thinking.",
        "consistency": "Establish steady patterns in how you work.",
        "recovery": "When errors happen, resolve them — that builds resilience.",
        "autonomy": "Try more complex tasks without relying on defaults.",
        "governance": "Follow the approval flow — publish with verification."
    }
    return suggestions.get(dimension, "Continue using the platform thoughtfully.")

@fit_router.get("/me")
async def fit_me(request: Request):
    """
    Show the user their own FIT profile.

    TRANSPARENCY ENDPOINT — Constitutional requirement.
    The user has the right to know:
    - Their current FIT score and layer
    - How each dimension is calculated
    - What capabilities are unlocked
    - What they need to reach the next level

    This is not gamification. This is auditability.
    """
    caller_did = get_caller_did(request)
    if not caller_did:
        return {
            "authenticated": False,
            "message": "Sign in to see your operational maturity profile.",
            "note": "Without identity, the system observes but does not attribute."
        }

    conn = get_fit_db()
    cursor = conn.cursor()

    try:
        # Get current FIT score
        cursor.execute("SELECT * FROM fit_scores WHERE did = ?", (caller_did,))
        row = cursor.fetchone()

        if not row:
            # New user, no events yet
            return {
                "authenticated": True,
                "did": caller_did,
                "fit_score": 0.0,
                "fit_level": 1,
                "layer": "LIVE",
                "layer_description": get_layer_description(1),
                "dimensions": {
                    "presence": 0.0,
                    "decision": 0.0,
                    "consistency": 0.0,
                    "recovery": 0.0,
                    "autonomy": 0.0,
                    "governance": 0.0
                },
                "dimension_weights": FIT_WEIGHTS,
                "total_events": 0,
                "capabilities": get_capabilities(1),
                "next_level": get_next_layer_hint(1, {"presence": 0, "decision": 0, "consistency": 0, "recovery": 0, "autonomy": 0, "governance": 0}),
                "transparency_note": "This is your operational maturity profile. The system observes your patterns to unlock capabilities — and you can always see what it sees."
            }

        dimensions = {
            "presence": row["presence"],
            "decision": row["decision"],
            "consistency": row["consistency"],
            "recovery": row["recovery"],
            "autonomy": row["autonomy"],
            "governance": row["governance"]
        }

        return {
            "authenticated": True,
            "did": caller_did,
            "fit_score": row["fit_score"],
            "fit_level": row["fit_level"],
            "layer": get_layer_name(row["fit_level"]),
            "layer_description": get_layer_description(row["fit_level"]),
            "dimensions": dimensions,
            "dimension_weights": FIT_WEIGHTS,
            "dimension_explanations": {
                "presence": "How actively you engage with the platform",
                "decision": "Quality and clarity of your choices",
                "consistency": "Stability of your behavioral patterns",
                "recovery": "How you handle and resolve errors",
                "autonomy": "Independence in complex tasks",
                "governance": "Adherence to verification and approval flows"
            },
            "total_events": row["total_events"],
            "last_activity": row["last_event_at"],
            "capabilities": get_capabilities(row["fit_level"]),
            "next_level": get_next_layer_hint(row["fit_level"], dimensions),
            "transparency_note": "This is your operational maturity profile. The system observes your patterns to unlock capabilities — and you can always see what it sees.",
            "constitutional_basis": "I2 (Transparency of Process) — You have the right to know how you are being evaluated."
        }

    finally:
        conn.close()

# ═══════════════════════════════════════════════════════════════════════════
# MODULE EXPORT
# ═══════════════════════════════════════════════════════════════════════════

print("[FIT-ENGINE] W-FIT-001 loaded (observable maturity system — /fit/me available)")
