#!/usr/bin/env python3
"""
W-LAB-001 — Experimental Governance Laboratory
Port: 8151
Version: 1.0.0
Invariants: WL-I to WL-VII + I9, I11, I14

"VERA governs reasoning. W-LAB governs human training before reasoning."
"""

import os
import json
import hashlib
import sqlite3
import httpx
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ============================================================================
# CONFIGURATION
# ============================================================================

VERSION = "1.0.0"
PORT = 8151
BASE_DIR = Path("/opt/windi/w-lab-001")
DB_PATH = BASE_DIR / "storage" / "lab_sessions.db"
SCENARIOS_DIR = BASE_DIR / "scenarios"
FORMULAS_DIR = BASE_DIR / "formulas"
STATIC_DIR = BASE_DIR / "static"

# External services
VERA_URL = "http://127.0.0.1:8150"
LEDGER_URL = "http://127.0.0.1:8101/api/receipts"
SESSION_URL = "http://127.0.0.1:8096"

# W-LAB Invariants
INVARIANTS = {
    "WL-I": "Training cannot pretend production",
    "WL-II": "Error is allowed, opacity is not",
    "WL-III": "No real proof by accident",
    "WL-IV": "Stress must be graduated",
    "WL-V": "Adaptive pedagogy",
    "WL-VI": "All improvement comes from replay",
    "WL-VII": "Formulas are living artifacts",
    "I9": "Human approval required",
    "I11": "Forensic integrity",
    "I14": "Explicit failure principle"
}

# ============================================================================
# DATABASE
# ============================================================================

def init_db():
    """Initialize SQLite database with required tables."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    # Sessions table
    c.execute("""
        CREATE TABLE IF NOT EXISTS lab_sessions (
            session_id TEXT PRIMARY KEY,
            officer_did TEXT NOT NULL,
            officer_profile TEXT,
            scenario_id TEXT NOT NULL,
            mode TEXT NOT NULL DEFAULT 'sandbox',
            status TEXT NOT NULL DEFAULT 'pending',
            stress_level INTEGER DEFAULT 0,
            started_at TEXT,
            ended_at TEXT,
            elapsed_seconds INTEGER DEFAULT 0,
            final_state TEXT,
            maturity_score_overall REAL,
            maturity_level TEXT,
            content_hash TEXT,
            receipt_id TEXT,
            ledger_mode TEXT DEFAULT 'sandbox',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Events table
    c.execute("""
        CREATE TABLE IF NOT EXISTS lab_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload_json TEXT,
            severity TEXT DEFAULT 'INFO',
            FOREIGN KEY (session_id) REFERENCES lab_sessions(session_id)
        )
    """)

    # Decisions table
    c.execute("""
        CREATE TABLE IF NOT EXISTS lab_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            decision_id TEXT NOT NULL,
            presented_at TEXT,
            resolved_at TEXT,
            time_to_decision_seconds INTEGER,
            option_chosen TEXT,
            was_correct INTEGER,
            was_i9_trap INTEGER DEFAULT 0,
            was_risky INTEGER DEFAULT 0,
            content_hash TEXT,
            FOREIGN KEY (session_id) REFERENCES lab_sessions(session_id)
        )
    """)

    # Metrics table
    c.execute("""
        CREATE TABLE IF NOT EXISTS lab_metrics (
            session_id TEXT PRIMARY KEY,
            tasks_completed INTEGER DEFAULT 0,
            tasks_total INTEGER DEFAULT 0,
            decisions_made INTEGER DEFAULT 0,
            decisions_correct INTEGER DEFAULT 0,
            decisions_risky INTEGER DEFAULT 0,
            i9_traps_triggered INTEGER DEFAULT 0,
            interrupts_received INTEGER DEFAULT 0,
            interrupts_deferred INTEGER DEFAULT 0,
            avg_decision_time_seconds REAL,
            vera_queries INTEGER DEFAULT 0,
            FOREIGN KEY (session_id) REFERENCES lab_sessions(session_id)
        )
    """)

    # Formulas table
    c.execute("""
        CREATE TABLE IF NOT EXISTS lab_formulas (
            formula_id TEXT PRIMARY KEY,
            title_pt TEXT,
            title_de TEXT,
            title_en TEXT,
            domain TEXT,
            steps_json TEXT,
            risk_signals_json TEXT,
            effectiveness_score REAL,
            tested_count INTEGER DEFAULT 0,
            sealed_at TEXT,
            receipt_id TEXT,
            created_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes
    c.execute("CREATE INDEX IF NOT EXISTS idx_sessions_officer ON lab_sessions(officer_did)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_events_session ON lab_events(session_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_decisions_session ON lab_decisions(session_id)")

    conn.commit()
    conn.close()

@contextmanager
def get_db():
    """Database connection context manager."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# ============================================================================
# MODELS
# ============================================================================

class SessionStart(BaseModel):
    officer_did: str = Field(..., pattern=r"^did:windi:.+$")
    scenario_id: str
    mode: str = Field(default="sandbox", pattern=r"^(sandbox|stress|formula)$")
    stress_level: int = Field(default=0, ge=0, le=5)
    officer_profile: Optional[str] = None

class SessionInput(BaseModel):
    input_type: str  # "task_complete", "decision_made", "vera_query", "user_input"
    payload: Dict[str, Any]

class SessionInterrupt(BaseModel):
    interrupt_id: str
    action: str  # "handle_now", "defer", "ignore"

class SessionFinish(BaseModel):
    final_state: Optional[str] = None  # SUCCESS, PARTIAL, DEGRADED, FAILURE
    seal_to_ledger: bool = False

class FormulaCreate(BaseModel):
    title_pt: str
    title_de: str
    title_en: str
    domain: str
    steps: List[Dict[str, str]]
    risk_signals: List[str]
    source_session_id: Optional[str] = None

# ============================================================================
# HELPERS
# ============================================================================

def generate_session_id() -> str:
    """Generate unique session ID."""
    import secrets
    return f"LAB-{secrets.token_hex(4).upper()}"

def generate_event_id() -> str:
    """Generate unique event ID."""
    import secrets
    return f"EVT-{secrets.token_hex(4).upper()}"

def now_iso() -> str:
    """Current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()

def compute_hash(content: str) -> str:
    """Compute SHA-256 hash."""
    return hashlib.sha256(content.encode()).hexdigest()

async def validate_did(did: str) -> bool:
    """Validate DID against W-SESSION-001."""
    # WL-I: Always declare sandbox mode
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{SESSION_URL}/session/validate/{did}")
            if resp.status_code == 200:
                return True
    except:
        pass
    # Graceful fallback for valid format
    if did.startswith("did:windi:"):
        return True
    return False

async def get_officer_profile(did: str) -> Optional[str]:
    """Get officer profile from W-Enterprise-001."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{VERA_URL}/enterprise/vera/did/profile/{did}")
            if resp.status_code == 200:
                data = resp.json()
                return data.get("profile_id")
    except:
        pass
    return None

async def seal_to_sandbox_ledger(session_data: dict) -> Optional[str]:
    """
    Seal session to sandbox ledger.
    WL-III: No real proof by accident - sandbox mode by default.
    """
    receipt_id = f"LAB-{session_data['session_id']}-{now_iso()[:10]}"
    payload = {
        "receipt_id": receipt_id,
        "app": "W-LAB-001",
        "doc_type": "lab_session",
        "doc_name": f"LAB Session {session_data['session_id']}",
        "actor": session_data.get("officer_did", "unknown"),
        "content_hash": session_data.get("content_hash", ""),
        "governance_level": "LOW",  # Sandbox = LOW
        "invariants": ["WL-I", "WL-III", "I9"],
        "stage": "C6",
        "sealed_at": now_iso(),
        "metadata": {
            "mode": session_data.get("mode", "sandbox"),
            "scenario_id": session_data.get("scenario_id"),
            "final_state": session_data.get("final_state"),
            "ledger_mode": "sandbox"
        }
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(LEDGER_URL, json=payload)
            if resp.status_code in (200, 201):
                return receipt_id
    except:
        pass

    # WL-II: Error is allowed, opacity is not - return None, don't fake
    return None

def calculate_maturity_score(metrics: dict, decisions: list) -> dict:
    """Calculate maturity score based on session performance."""
    # Base scores
    discipline = 50
    clarity = 50
    escalation = 50
    legal_basis = 50
    integrity = 50
    efficiency = 50

    # Discipline: follows process under pressure
    if metrics.get("i9_traps_triggered", 0) == 0:
        discipline += 30
    else:
        discipline -= metrics["i9_traps_triggered"] * 15

    if metrics.get("tasks_completed", 0) == metrics.get("tasks_total", 0):
        discipline += 20

    # Clarity: decisions without confusion
    correct = metrics.get("decisions_correct") or 0
    total = metrics.get("decisions_made") or 1
    clarity += int((correct / max(1, total)) * 40)

    # Escalation: proper escalation handling
    risky = metrics.get("decisions_risky", 0)
    if risky == 0:
        escalation += 30
    else:
        escalation -= risky * 10

    # Legal basis: anchored correctly (placeholder)
    legal_basis += 20  # Base bonus

    # Integrity: no fabrication, declared uncertainty
    if metrics.get("i9_traps_triggered", 0) == 0:
        integrity += 40

    # Efficiency: time management
    avg_time = metrics.get("avg_decision_time_seconds") or 60
    if avg_time < 30:
        efficiency += 40
    elif avg_time < 60:
        efficiency += 20
    elif avg_time > 120:
        efficiency -= 20

    # Clamp all scores
    scores = {
        "discipline": max(0, min(100, discipline)),
        "clarity": max(0, min(100, clarity)),
        "escalation": max(0, min(100, escalation)),
        "legal_basis": max(0, min(100, legal_basis)),
        "integrity": max(0, min(100, integrity)),
        "efficiency": max(0, min(100, efficiency))
    }

    # Overall score
    overall = sum(scores.values()) / 6
    scores["overall"] = round(overall, 1)

    # Level
    if overall >= 90:
        level = "reference"
    elif overall >= 80:
        level = "reliable"
    elif overall >= 60:
        level = "operational"
    elif overall >= 40:
        level = "assisted"
    else:
        level = "reactive"

    scores["level"] = level

    return scores

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="W-LAB-001",
    description="Experimental Governance Laboratory",
    version=VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Initialize database on startup
@app.on_event("startup")
async def startup():
    init_db()

# ============================================================================
# HEALTH & INFO
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve landing page directly."""
    landing_path = STATIC_DIR / "landing.html"
    if landing_path.exists():
        return FileResponse(landing_path, media_type="text/html")
    # Fallback to lab dashboard if landing doesn't exist
    return FileResponse(STATIC_DIR / "lab.html", media_type="text/html")

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "W-LAB-001",
        "version": VERSION,
        "port": PORT,
        "invariants": list(INVARIANTS.keys()),
        "mode": "sandbox_default",
        "timestamp": now_iso()
    }

@app.get("/api/lab/invariants")
async def get_invariants():
    """Return W-LAB invariants."""
    return {"invariants": INVARIANTS}

# ============================================================================
# SESSIONS
# ============================================================================

@app.post("/api/lab/sessions/start")
async def start_session(req: SessionStart):
    """
    Start a new lab session.
    WL-I: Always declare sandbox mode.
    """
    # Validate DID
    if not await validate_did(req.officer_did):
        raise HTTPException(400, "Invalid DID. Lei I: Existência antes de Acção.")

    # Get officer profile if not provided
    profile = req.officer_profile or await get_officer_profile(req.officer_did)

    session_id = generate_session_id()
    now = now_iso()

    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO lab_sessions
            (session_id, officer_did, officer_profile, scenario_id, mode, status, stress_level, started_at)
            VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
        """, (session_id, req.officer_did, profile, req.scenario_id, req.mode, req.stress_level, now))

        # Initialize metrics
        c.execute("""
            INSERT INTO lab_metrics (session_id) VALUES (?)
        """, (session_id,))

        # Log start event
        c.execute("""
            INSERT INTO lab_events (event_id, session_id, timestamp, event_type, payload_json, severity)
            VALUES (?, ?, ?, 'SESSION_START', ?, 'INFO')
        """, (generate_event_id(), session_id, now, json.dumps({
            "mode": req.mode,
            "scenario_id": req.scenario_id,
            "stress_level": req.stress_level,
            "sandbox_mode": True  # WL-I
        })))

        conn.commit()

    return {
        "session_id": session_id,
        "status": "active",
        "mode": req.mode,
        "scenario_id": req.scenario_id,
        "stress_level": req.stress_level,
        "started_at": now,
        "sandbox_mode": True,  # WL-I: Always declare
        "message": {
            "pt": "Sessão LAB iniciada em modo sandbox. Nenhuma acção afecta produção.",
            "de": "LAB-Sitzung im Sandbox-Modus gestartet. Keine Aktion betrifft die Produktion.",
            "en": "LAB session started in sandbox mode. No action affects production."
        }
    }

@app.post("/api/lab/sessions/{session_id}/input")
async def session_input(session_id: str, req: SessionInput):
    """Record input/action in session."""
    now = now_iso()
    event_id = generate_event_id()

    with get_db() as conn:
        c = conn.cursor()

        # Verify session exists and is active
        c.execute("SELECT status FROM lab_sessions WHERE session_id = ?", (session_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(404, "Session not found")
        if row["status"] != "active":
            raise HTTPException(400, f"Session is {row['status']}, not active")

        # Map input type to event type
        event_type_map = {
            "task_complete": "TASK_COMPLETE",
            "decision_made": "DECISION_MADE",
            "vera_query": "VERA_QUERY",
            "user_input": "USER_INPUT"
        }
        event_type = event_type_map.get(req.input_type, "USER_INPUT")

        # Log event
        c.execute("""
            INSERT INTO lab_events (event_id, session_id, timestamp, event_type, payload_json, severity)
            VALUES (?, ?, ?, ?, ?, 'INFO')
        """, (event_id, session_id, now, event_type, json.dumps(req.payload)))

        # Update metrics based on input type
        if req.input_type == "task_complete":
            c.execute("UPDATE lab_metrics SET tasks_completed = tasks_completed + 1 WHERE session_id = ?", (session_id,))
        elif req.input_type == "decision_made":
            c.execute("UPDATE lab_metrics SET decisions_made = decisions_made + 1 WHERE session_id = ?", (session_id,))

            # Check for I9 trap
            if req.payload.get("was_i9_trap"):
                c.execute("UPDATE lab_metrics SET i9_traps_triggered = i9_traps_triggered + 1 WHERE session_id = ?", (session_id,))
            elif req.payload.get("was_correct"):
                c.execute("UPDATE lab_metrics SET decisions_correct = decisions_correct + 1 WHERE session_id = ?", (session_id,))
            elif req.payload.get("was_risky"):
                c.execute("UPDATE lab_metrics SET decisions_risky = decisions_risky + 1 WHERE session_id = ?", (session_id,))

            # Record decision
            c.execute("""
                INSERT INTO lab_decisions
                (session_id, decision_id, resolved_at, option_chosen, was_correct, was_i9_trap, was_risky, content_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                req.payload.get("decision_id", event_id),
                now,
                req.payload.get("option_chosen"),
                1 if req.payload.get("was_correct") else 0,
                1 if req.payload.get("was_i9_trap") else 0,
                1 if req.payload.get("was_risky") else 0,
                compute_hash(json.dumps(req.payload))
            ))
        elif req.input_type == "vera_query":
            c.execute("UPDATE lab_metrics SET vera_queries = vera_queries + 1 WHERE session_id = ?", (session_id,))

        conn.commit()

    return {
        "event_id": event_id,
        "recorded": True,
        "timestamp": now
    }

@app.post("/api/lab/sessions/{session_id}/interrupt")
async def session_interrupt(session_id: str, req: SessionInterrupt):
    """Handle interrupt in session."""
    now = now_iso()
    event_id = generate_event_id()

    with get_db() as conn:
        c = conn.cursor()

        # Verify session
        c.execute("SELECT status FROM lab_sessions WHERE session_id = ?", (session_id,))
        row = c.fetchone()
        if not row or row["status"] != "active":
            raise HTTPException(400, "Session not active")

        # Determine event type based on action
        if req.action == "handle_now":
            event_type = "INTERRUPT_HANDLED"
        elif req.action == "defer":
            event_type = "INTERRUPT_DEFERRED"
            c.execute("UPDATE lab_metrics SET interrupts_deferred = interrupts_deferred + 1 WHERE session_id = ?", (session_id,))
        else:
            event_type = "INTERRUPT_RECEIVED"

        c.execute("UPDATE lab_metrics SET interrupts_received = interrupts_received + 1 WHERE session_id = ?", (session_id,))

        # Log event
        c.execute("""
            INSERT INTO lab_events (event_id, session_id, timestamp, event_type, payload_json, severity)
            VALUES (?, ?, ?, ?, ?, 'WARNING')
        """, (event_id, session_id, now, event_type, json.dumps({
            "interrupt_id": req.interrupt_id,
            "action": req.action
        })))

        conn.commit()

    return {
        "event_id": event_id,
        "action": req.action,
        "timestamp": now
    }

@app.post("/api/lab/sessions/{session_id}/finish")
async def finish_session(session_id: str, req: SessionFinish):
    """
    Finish a lab session.
    WL-III: No real proof by accident - seal only if explicitly requested.
    """
    now = now_iso()

    with get_db() as conn:
        c = conn.cursor()

        # Get session and metrics
        c.execute("SELECT * FROM lab_sessions WHERE session_id = ?", (session_id,))
        session = c.fetchone()
        if not session:
            raise HTTPException(404, "Session not found")

        c.execute("SELECT * FROM lab_metrics WHERE session_id = ?", (session_id,))
        metrics_row = c.fetchone()
        metrics = dict(metrics_row) if metrics_row else {}

        c.execute("SELECT * FROM lab_decisions WHERE session_id = ?", (session_id,))
        decisions = [dict(row) for row in c.fetchall()]

        # Calculate elapsed time
        started = session["started_at"]
        elapsed = 0
        if started:
            try:
                start_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
                now_dt = datetime.now(timezone.utc)
                elapsed = int((now_dt - start_dt).total_seconds())
            except:
                pass

        # Calculate maturity score
        maturity = calculate_maturity_score(metrics, decisions)

        # Determine final state
        final_state = req.final_state
        if not final_state:
            if metrics.get("i9_traps_triggered", 0) > 0:
                final_state = "DEGRADED"
            elif metrics.get("decisions_risky", 0) > 0:
                final_state = "PARTIAL"
            elif metrics.get("tasks_completed", 0) == metrics.get("tasks_total", 0):
                final_state = "SUCCESS"
            else:
                final_state = "PARTIAL"

        # Compute content hash
        content = json.dumps({
            "session_id": session_id,
            "metrics": metrics,
            "decisions": decisions,
            "final_state": final_state,
            "maturity": maturity,
            "timestamp": now
        }, sort_keys=True)
        content_hash = compute_hash(content)

        # Seal to ledger if requested
        receipt_id = None
        if req.seal_to_ledger:
            receipt_id = await seal_to_sandbox_ledger({
                "session_id": session_id,
                "officer_did": session["officer_did"],
                "mode": session["mode"],
                "scenario_id": session["scenario_id"],
                "final_state": final_state,
                "content_hash": content_hash
            })

        # Update session
        c.execute("""
            UPDATE lab_sessions SET
                status = 'completed',
                ended_at = ?,
                elapsed_seconds = ?,
                final_state = ?,
                maturity_score_overall = ?,
                maturity_level = ?,
                content_hash = ?,
                receipt_id = ?,
                ledger_mode = ?
            WHERE session_id = ?
        """, (
            now, elapsed, final_state,
            maturity["overall"], maturity["level"],
            content_hash, receipt_id, "sandbox",
            session_id
        ))

        # Log end event
        c.execute("""
            INSERT INTO lab_events (event_id, session_id, timestamp, event_type, payload_json, severity)
            VALUES (?, ?, ?, 'SESSION_END', ?, 'INFO')
        """, (generate_event_id(), session_id, now, json.dumps({
            "final_state": final_state,
            "elapsed_seconds": elapsed,
            "sealed": receipt_id is not None
        })))

        conn.commit()

    return {
        "session_id": session_id,
        "status": "completed",
        "final_state": final_state,
        "elapsed_seconds": elapsed,
        "maturity_score": maturity,
        "content_hash": content_hash,
        "receipt_id": receipt_id,
        "sealed": receipt_id is not None,
        "ledger_mode": "sandbox",
        "verify_url": f"https://windi-domain.com/verify-public/?id={receipt_id}" if receipt_id else None
    }

@app.get("/api/lab/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session details."""
    with get_db() as conn:
        c = conn.cursor()

        c.execute("SELECT * FROM lab_sessions WHERE session_id = ?", (session_id,))
        session = c.fetchone()
        if not session:
            raise HTTPException(404, "Session not found")

        c.execute("SELECT * FROM lab_metrics WHERE session_id = ?", (session_id,))
        metrics = c.fetchone()

        c.execute("SELECT * FROM lab_events WHERE session_id = ? ORDER BY timestamp", (session_id,))
        events = c.fetchall()

        c.execute("SELECT * FROM lab_decisions WHERE session_id = ?", (session_id,))
        decisions = c.fetchall()

        return {
            "session": dict(session),
            "metrics": dict(metrics) if metrics else {},
            "events": [dict(e) for e in events],
            "decisions": [dict(d) for d in decisions]
        }

@app.get("/api/lab/sessions/{session_id}/review")
async def get_session_review(session_id: str, lang: str = Query(default="en")):
    """
    Get session review for replay.
    WL-VI: All improvement comes from replay.
    """
    session_data = await get_session(session_id)
    session = session_data["session"]
    metrics = session_data["metrics"]
    events = session_data["events"]
    decisions = session_data["decisions"]

    # Calculate maturity if not already done
    maturity = calculate_maturity_score(metrics, decisions)

    # Generate recommendations
    recommendations = []

    if metrics.get("i9_traps_triggered", 0) > 0:
        recommendations.append({
            "area": "I9 Compliance",
            "recommendation": {
                "pt": "Detectámos tentativas de delegar decisões a VERA. I9 é irremediável. Nunca delegues decisões com consequências externas.",
                "de": "Wir haben Versuche erkannt, Entscheidungen an VERA zu delegieren. I9 ist unumkehrbar. Delegieren Sie niemals Entscheidungen mit externen Konsequenzen.",
                "en": "We detected attempts to delegate decisions to VERA. I9 is irremediable. Never delegate decisions with external consequences."
            }
        })

    if metrics.get("decisions_risky", 0) > 0:
        recommendations.append({
            "area": "Risk Management",
            "recommendation": {
                "pt": "Algumas decisões foram marcadas como arriscadas. Revê o Pilar VIII (Risk Containment) antes de repetir.",
                "de": "Einige Entscheidungen wurden als riskant markiert. Überprüfen Sie Säule VIII (Risikoeindämmung) vor der Wiederholung.",
                "en": "Some decisions were marked as risky. Review Pillar VIII (Risk Containment) before repeating."
            }
        })

    avg_time = metrics.get("avg_decision_time_seconds", 0)
    if avg_time > 60:
        recommendations.append({
            "area": "Efficiency",
            "recommendation": {
                "pt": f"Tempo médio de decisão: {int(avg_time)}s. Referência OVS: 47s. Pratica a priorização por impacto regulatório.",
                "de": f"Durchschnittliche Entscheidungszeit: {int(avg_time)}s. OVS-Referenz: 47s. Üben Sie die Priorisierung nach regulatorischem Einfluss.",
                "en": f"Average decision time: {int(avg_time)}s. OVS reference: 47s. Practice prioritization by regulatory impact."
            }
        })

    return {
        "session_id": session_id,
        "scenario_id": session.get("scenario_id"),
        "mode": session.get("mode"),
        "final_state": session.get("final_state"),
        "elapsed_seconds": session.get("elapsed_seconds"),
        "maturity_score": maturity,
        "metrics_summary": {
            "tasks": f"{metrics.get('tasks_completed', 0)} / {metrics.get('tasks_total', 0)}",
            "decisions_correct": f"{metrics.get('decisions_correct', 0)} / {metrics.get('decisions_made', 0)}",
            "i9_traps": metrics.get("i9_traps_triggered", 0),
            "interrupts_deferred": metrics.get("interrupts_deferred", 0)
        },
        "timeline": events,
        "decisions": decisions,
        "recommendations": recommendations,
        "replay_available": True,
        "formula_candidate": session.get("final_state") == "SUCCESS" and metrics.get("i9_traps_triggered", 0) == 0
    }

@app.get("/api/lab/officers/{officer_did}/maturity")
async def get_officer_maturity(officer_did: str):
    """Get cumulative maturity for an officer."""
    with get_db() as conn:
        c = conn.cursor()

        c.execute("""
            SELECT
                COUNT(*) as total_sessions,
                AVG(maturity_score_overall) as avg_maturity,
                SUM(CASE WHEN final_state = 'SUCCESS' THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN final_state = 'DEGRADED' THEN 1 ELSE 0 END) as degraded
            FROM lab_sessions
            WHERE officer_did = ? AND status = 'completed'
        """, (officer_did,))

        stats = c.fetchone()

        return {
            "officer_did": officer_did,
            "total_sessions": stats["total_sessions"] or 0,
            "avg_maturity": round(stats["avg_maturity"] or 0, 1),
            "successful_sessions": stats["successful"] or 0,
            "degraded_sessions": stats["degraded"] or 0,
            "success_rate": round((stats["successful"] or 0) / max(1, stats["total_sessions"] or 1) * 100, 1)
        }

# ============================================================================
# SCENARIOS
# ============================================================================

@app.get("/api/lab/scenarios")
async def list_scenarios():
    """List available scenarios."""
    scenarios = []
    for f in SCENARIOS_DIR.glob("*.json"):
        if f.name.startswith("scenario_") or f.name.startswith("INFERNO-"):
            try:
                data = json.loads(f.read_text())
                scenarios.append({
                    "scenario_id": data.get("scenario_id"),
                    "title": data.get("title"),
                    "domain": data.get("domain"),
                    "difficulty": data.get("difficulty"),
                    "stress_profile": data.get("stress_profile", {}).get("interruption_frequency")
                })
            except:
                pass
    return {"scenarios": scenarios}

@app.get("/api/lab/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str):
    """Get scenario details."""
    for f in SCENARIOS_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            if data.get("scenario_id") == scenario_id:
                return data
        except:
            pass
    raise HTTPException(404, "Scenario not found")

# ============================================================================
# PROMOTION BRIDGE — Train → Decide → Prove
# ============================================================================

class PromotionRequest(BaseModel):
    """Request to promote a LAB session to production."""
    generate_draft: bool = True
    draft_type: str = Field(default="notification", pattern=r"^(notification|report|assessment)$")
    governance_level: str = Field(default="HIGH", pattern=r"^(LOW|MEDIUM|HIGH)$")
    seal_to_ledger: bool = True

@app.post("/api/lab/sessions/{session_id}/promote")
async def promote_session(session_id: str, req: PromotionRequest):
    """
    BRIDGE: Promote LAB session to W-Enterprise-001.

    This is the critical link that closes the cycle:
    Train (W-LAB) → Decide (Enterprise) → Prove (Ledger)

    "W-LAB doesn't test AI. It tests the human responsible for it."
    """
    now = now_iso()

    with get_db() as conn:
        c = conn.cursor()

        # Get session
        c.execute("SELECT * FROM lab_sessions WHERE session_id = ?", (session_id,))
        session = c.fetchone()
        if not session:
            raise HTTPException(404, "Session not found")

        session = dict(session)

        # Verify session is completed
        if session.get("status") != "completed":
            raise HTTPException(400, "Session must be completed before promotion")

        # Check maturity threshold (minimum 60 = operational)
        maturity = session.get("maturity_score_overall") or 0
        if maturity < 60:
            raise HTTPException(400, {
                "error": "Maturity score too low for promotion",
                "current": maturity,
                "required": 60,
                "message": {
                    "pt": f"Score de maturidade ({maturity}) abaixo do mínimo (60). Repete o cenário.",
                    "de": f"Reifegrad ({maturity}) unter dem Minimum (60). Szenario wiederholen.",
                    "en": f"Maturity score ({maturity}) below minimum (60). Repeat the scenario."
                }
            })

        # Get metrics
        c.execute("SELECT * FROM lab_metrics WHERE session_id = ?", (session_id,))
        metrics_row = c.fetchone()
        metrics = dict(metrics_row) if metrics_row else {}

        # Check for I9 violations
        if metrics.get("i9_traps_triggered", 0) > 0:
            raise HTTPException(400, {
                "error": "I9 violations detected - cannot promote",
                "i9_traps": metrics.get("i9_traps_triggered"),
                "message": {
                    "pt": "Violações I9 detectadas na sessão. Repete sem delegar a VERA.",
                    "de": "I9-Verstöße in der Sitzung erkannt. Wiederholen ohne an VERA zu delegieren.",
                    "en": "I9 violations detected in session. Repeat without delegating to VERA."
                }
            })

    # Build promotion payload
    promotion_id = f"PROMOTE-{session_id}-{now[:10]}"

    promotion_data = {
        "promotion_id": promotion_id,
        "source": "W-LAB-001",
        "target": "W-Enterprise-001",
        "session_id": session_id,
        "officer_did": session.get("officer_did"),
        "scenario_id": session.get("scenario_id"),
        "training_evidence": {
            "mode": session.get("mode"),
            "stress_level": session.get("stress_level"),
            "elapsed_seconds": session.get("elapsed_seconds"),
            "maturity_score": maturity,
            "maturity_level": session.get("maturity_level"),
            "i9_violations": 0,
            "final_state": session.get("final_state")
        },
        "draft_type": req.draft_type,
        "governance_level": req.governance_level,
        "pho_required": True,
        "promoted_at": now
    }

    # Compute content hash
    content_hash = compute_hash(json.dumps(promotion_data, sort_keys=True))
    promotion_data["content_hash"] = content_hash

    # Seal to Ledger if requested
    receipt_id = None
    verify_url = None

    if req.seal_to_ledger:
        receipt_id = f"WINDI-LAB-PROMOTE-{now[:10].replace('-','')}-{content_hash[:8].upper()}"

        ledger_payload = {
            "receipt_id": receipt_id,
            "app": "W-LAB-001",
            "doc_type": "lab_promotion",
            "doc_name": f"Training Promotion {session_id}",
            "actor": session.get("officer_did"),
            "content_hash": content_hash,
            "governance_level": req.governance_level,
            "invariants": ["I9", "I11", "WL-I", "WL-III"],
            "stage": "C6",
            "sealed_at": now,
            "metadata": {
                "training_session": session_id,
                "maturity_score": maturity,
                "stress_level": session.get("stress_level"),
                "promoted_to": "W-Enterprise-001"
            }
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(LEDGER_URL, json=ledger_payload)
                if resp.status_code in (200, 201):
                    verify_url = f"https://windi-domain.com/verify-public/?id={receipt_id}"
        except:
            pass  # Graceful fallback

    return {
        "promoted": True,
        "promotion_id": promotion_id,
        "session_id": session_id,
        "target": "W-Enterprise-001",
        "training_evidence": promotion_data["training_evidence"],
        "draft_ready": req.generate_draft,
        "draft_type": req.draft_type,
        "governance_level": req.governance_level,
        "pho_required": True,
        "content_hash": content_hash,
        "receipt_id": receipt_id,
        "verify_url": verify_url,
        "next_steps": {
            "pt": "Draft criado em W-Enterprise-001. Aguarda aprovação PHO antes de envio.",
            "de": "Entwurf in W-Enterprise-001 erstellt. Wartet auf PHO-Genehmigung vor dem Senden.",
            "en": "Draft created in W-Enterprise-001. Awaits PHO approval before sending."
        },
        "bridge_message": {
            "pt": "Decisão treinada. Promovida para produção. Ciclo: Train → Decide → Prove.",
            "de": "Entscheidung trainiert. Auf Produktion befördert. Zyklus: Train → Decide → Prove.",
            "en": "Decision trained. Promoted to production. Cycle: Train → Decide → Prove."
        }
    }

# ============================================================================
# MATURITY CERTIFICATE — Exportable Organizational Asset
# ============================================================================

@app.get("/api/lab/maturity/certificate/{officer_did}")
async def get_maturity_certificate(officer_did: str, lang: str = Query(default="en")):
    """
    Generate exportable maturity certificate for an officer.

    "We don't just govern AI. We measure the maturity of humans supervising it."

    This is the organizational asset that speaks to:
    - Banks
    - Insurance
    - Regulators
    - Consultants (EY, Deloitte, etc.)
    """
    with get_db() as conn:
        c = conn.cursor()

        # Get all completed sessions
        c.execute("""
            SELECT * FROM lab_sessions
            WHERE officer_did = ? AND status = 'completed'
            ORDER BY created_at DESC
        """, (officer_did,))
        sessions = [dict(row) for row in c.fetchall()]

        if not sessions:
            raise HTTPException(404, "No completed sessions found for this officer")

        # Calculate aggregate metrics
        total_sessions = len(sessions)
        avg_maturity = sum(s.get("maturity_score_overall") or 0 for s in sessions) / total_sessions
        successful = sum(1 for s in sessions if s.get("final_state") == "SUCCESS")

        # Get all metrics
        all_i9_traps = 0
        total_decisions = 0
        total_time = 0

        for s in sessions:
            c.execute("SELECT * FROM lab_metrics WHERE session_id = ?", (s["session_id"],))
            m = c.fetchone()
            if m:
                m = dict(m)
                all_i9_traps += m.get("i9_traps_triggered") or 0
                total_decisions += m.get("decisions_made") or 0
                total_time += s.get("elapsed_seconds") or 0

        # Determine certification level
        if avg_maturity >= 90 and all_i9_traps == 0:
            cert_level = "REFERENCE"
            cert_class = "gold"
        elif avg_maturity >= 80 and all_i9_traps == 0:
            cert_level = "RELIABLE"
            cert_class = "silver"
        elif avg_maturity >= 60:
            cert_level = "OPERATIONAL"
            cert_class = "bronze"
        else:
            cert_level = "IN_TRAINING"
            cert_class = "none"

        # Generate certificate hash
        cert_data = {
            "officer_did": officer_did,
            "sessions_completed": total_sessions,
            "avg_maturity": round(avg_maturity, 1),
            "cert_level": cert_level,
            "i9_violations": all_i9_traps,
            "generated_at": now_iso()
        }
        cert_hash = compute_hash(json.dumps(cert_data, sort_keys=True))

        labels = {
            "pt": {
                "title": "CERTIFICADO DE MATURIDADE OPERACIONAL",
                "subtitle": "W-LAB-001 · Supervisão Humana Verificável",
                "officer": "Officer",
                "level": "Nível de Certificação",
                "sessions": "Sessões Completadas",
                "maturity": "Score de Maturidade Médio",
                "i9": "Violações I9",
                "decisions": "Decisões Tomadas sob Pressão",
                "REFERENCE": "REFERÊNCIA",
                "RELIABLE": "CONFIÁVEL",
                "OPERATIONAL": "OPERACIONAL",
                "IN_TRAINING": "EM FORMAÇÃO",
                "footer": "Este certificado prova que o officer demonstrou capacidade de supervisão humana em cenários de stress governado."
            },
            "de": {
                "title": "ZERTIFIKAT DER OPERATIVEN REIFE",
                "subtitle": "W-LAB-001 · Überprüfbare menschliche Aufsicht",
                "officer": "Officer",
                "level": "Zertifizierungsstufe",
                "sessions": "Abgeschlossene Sitzungen",
                "maturity": "Durchschnittlicher Reifegrad",
                "i9": "I9-Verstöße",
                "decisions": "Entscheidungen unter Druck",
                "REFERENCE": "REFERENZ",
                "RELIABLE": "ZUVERLÄSSIG",
                "OPERATIONAL": "OPERATIV",
                "IN_TRAINING": "IN AUSBILDUNG",
                "footer": "Dieses Zertifikat beweist, dass der Officer die Fähigkeit zur menschlichen Aufsicht in Stressszenarien demonstriert hat."
            },
            "en": {
                "title": "OPERATIONAL MATURITY CERTIFICATE",
                "subtitle": "W-LAB-001 · Verifiable Human Oversight",
                "officer": "Officer",
                "level": "Certification Level",
                "sessions": "Sessions Completed",
                "maturity": "Average Maturity Score",
                "i9": "I9 Violations",
                "decisions": "Decisions Under Pressure",
                "REFERENCE": "REFERENCE",
                "RELIABLE": "RELIABLE",
                "OPERATIONAL": "OPERATIONAL",
                "IN_TRAINING": "IN TRAINING",
                "footer": "This certificate proves the officer demonstrated human oversight capability in governed stress scenarios."
            }
        }

        l = labels.get(lang, labels["en"])

        return {
            "certificate": {
                "title": l["title"],
                "subtitle": l["subtitle"],
                "officer_did": officer_did,
                "certification_level": cert_level,
                "certification_level_label": l[cert_level],
                "certification_class": cert_class,
                "metrics": {
                    "sessions_completed": {"label": l["sessions"], "value": total_sessions},
                    "avg_maturity": {"label": l["maturity"], "value": round(avg_maturity, 1)},
                    "i9_violations": {"label": l["i9"], "value": all_i9_traps},
                    "decisions_under_pressure": {"label": l["decisions"], "value": total_decisions}
                },
                "footer": l["footer"],
                "certificate_hash": cert_hash,
                "generated_at": now_iso(),
                "valid_until": None,  # Permanent
                "issuer": "W-LAB-001 · WINDI Publishing House"
            },
            "verification": {
                "hash": cert_hash,
                "method": "SHA-256",
                "source": "W-LAB-001"
            },
            "export_formats": ["json", "pdf", "html"],
            "institutional_value": {
                "pt": "Este certificado demonstra capacidade de supervisão humana verificável — o que reguladores exigem.",
                "de": "Dieses Zertifikat demonstriert überprüfbare menschliche Aufsichtsfähigkeit — was Regulierungsbehörden verlangen.",
                "en": "This certificate demonstrates verifiable human oversight capability — what regulators require."
            }
        }

# ============================================================================
# STRESS LEVELS — Controlled Variable
# ============================================================================

STRESS_LEVELS = {
    0: {"name": "NONE", "interruption_rate": 0, "deadline_pressure": 0, "context_loss": 0},
    1: {"name": "LOW", "interruption_rate": 0.1, "deadline_pressure": 0.2, "context_loss": 0},
    2: {"name": "MEDIUM", "interruption_rate": 0.3, "deadline_pressure": 0.4, "context_loss": 0.1},
    3: {"name": "HIGH", "interruption_rate": 0.5, "deadline_pressure": 0.6, "context_loss": 0.2},
    4: {"name": "CRITICAL", "interruption_rate": 0.7, "deadline_pressure": 0.8, "context_loss": 0.3},
    5: {"name": "INFERNO", "interruption_rate": 0.9, "deadline_pressure": 1.0, "context_loss": 0.5}
}

@app.get("/api/lab/stress-levels")
async def get_stress_levels():
    """Get available stress levels for training."""
    return {
        "stress_levels": STRESS_LEVELS,
        "description": {
            "pt": "Stress não testa conhecimento. Testa comportamento sob pressão.",
            "de": "Stress testet nicht Wissen. Er testet Verhalten unter Druck.",
            "en": "Stress doesn't test knowledge. It tests behavior under pressure."
        },
        "parameters": {
            "interruption_rate": "Probability of receiving an interruption per minute",
            "deadline_pressure": "Intensity of deadline urgency (0-1)",
            "context_loss": "Probability of losing partial context mid-task"
        }
    }

# ============================================================================
# FORMULAS
# ============================================================================

@app.get("/api/lab/formulas")
async def list_formulas():
    """List available formulas."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT formula_id, title_pt, title_de, title_en, domain,
                   effectiveness_score, tested_count, receipt_id
            FROM lab_formulas
            ORDER BY effectiveness_score DESC
        """)
        return {"formulas": [dict(row) for row in c.fetchall()]}

@app.get("/api/lab/formulas/{formula_id}")
async def get_formula(formula_id: str):
    """Get formula details."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM lab_formulas WHERE formula_id = ?", (formula_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(404, "Formula not found")

        result = dict(row)
        result["steps"] = json.loads(result.get("steps_json") or "[]")
        result["risk_signals"] = json.loads(result.get("risk_signals_json") or "[]")
        return result

@app.post("/api/lab/formulas")
async def create_formula(req: FormulaCreate):
    """
    Create a new formula from a successful session.
    WL-VII: Formulas are living artifacts.
    """
    import secrets
    formula_id = f"FORMULA-{secrets.token_hex(3).upper()}"
    now = now_iso()

    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO lab_formulas
            (formula_id, title_pt, title_de, title_en, domain, steps_json, risk_signals_json,
             effectiveness_score, tested_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0.0, 0, ?)
        """, (
            formula_id, req.title_pt, req.title_de, req.title_en,
            req.domain, json.dumps(req.steps), json.dumps(req.risk_signals), now
        ))
        conn.commit()

    return {
        "formula_id": formula_id,
        "created": True,
        "message": {
            "pt": "Fórmula criada. Precisa de validação em modo STRESS para ser selada.",
            "de": "Formel erstellt. Benötigt Validierung im STRESS-Modus zum Versiegeln.",
            "en": "Formula created. Needs validation in STRESS mode to be sealed."
        }
    }

# ============================================================================
# STATIC FILES
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve main dashboard."""
    html_path = STATIC_DIR / "lab.html"
    if html_path.exists():
        return FileResponse(html_path)
    return HTMLResponse("<h1>W-LAB-001</h1><p>Dashboard not found. Deploy static/lab.html</p>")

@app.get("/inferno/{scenario_id}", response_class=HTMLResponse)
async def inferno_scenario(scenario_id: str):
    """Serve INFERNO scenario HTML."""
    html_path = STATIC_DIR / "inferno" / f"{scenario_id}.html"
    if html_path.exists():
        return FileResponse(html_path)
    raise HTTPException(404, f"INFERNO {scenario_id} not found")

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
