"""
WINDI Guardian — Local Cognition Endpoint v1.0.0
=================================================
FastAPI service providing local AI-free conversation for WINDI FREE tier.
Port: 8110

"FREE não é limitado. FREE é soberano."
"A alma do Guardian não vem do LLM. Vem das palavras que nós escrevemos para ele."

Endpoints:
  POST /guardian/local     — Process user message locally
  GET  /guardian/health    — Health check
  GET  /guardian/stats     — Usage statistics
  POST /guardian/seed      — Re-seed response database

Architecture:
  1. Language Detection (lang_detect.py)
  2. Intent Classification (intent_engine.py)
  3. Response Selection (response_bank.py + SQLite)
  4. Escalation Logic (credits + LLM flag)
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

# ─── Setup ────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from intent_engine import classify_intent
from lang_detect import detect_language
from response_bank import (
    get_response,
    get_escalation_message,
    get_post_credits_message,
    seed_database,
    get_db,
    DB_PATH,
)

# ─── Configuration ────────────────────────────────────────────────────────────

PORT = int(os.environ.get("GUARDIAN_PORT", 8110))
HOST = os.environ.get("GUARDIAN_HOST", "0.0.0.0")
LOG_FILE = os.environ.get("GUARDIAN_LOG", "/opt/windi/logs/guardian-local.log")
CONFIDENCE_THRESHOLD = 0.6
DEFAULT_FREE_CREDITS = 5

# ─── Logging ──────────────────────────────────────────────────────────────────

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [GUARDIAN] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("guardian-local")

# ─── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="WINDI Guardian Local Cognition",
    version="1.0.0",
    description="Local AI-free conversation engine for WINDI FREE tier",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://admin.windia4desk.tech",
        "https://master.windia4desk.tech",
        "https://www.windi-domain.com",
        "http://localhost:8108",
        "http://127.0.0.1:8108",
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Session-ID", "X-Tier"],
    allow_credentials=True,
)

# ─── In-memory session store (credits tracking) ──────────────────────────────
# Production: replace with SQLite or Redis
sessions: dict = {}

# ─── Stats ────────────────────────────────────────────────────────────────────
stats = {
    "total_requests": 0,
    "local_resolved": 0,
    "llm_escalated": 0,
    "by_intent": {},
    "by_lang": {},
    "started_at": datetime.utcnow().isoformat(),
}

# ─── Models ───────────────────────────────────────────────────────────────────

class UserMessage(BaseModel):
    text: str
    session_id: str = ""
    tier: str = "FREE"
    credits_left: Optional[int] = None

class GuardianResponse(BaseModel):
    text: str
    intent: str
    confidence: float
    language: str
    requires_llm: bool
    credit_cost: int = 0
    group: str = ""
    offer_alternative: bool = False
    session_credits_left: Optional[int] = None
    processing_ms: float = 0.0

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    port: int
    uptime_seconds: float
    total_responses: int
    response_db_entries: int
    local_resolve_rate: float

# ─── Startup ──────────────────────────────────────────────────────────────────

START_TIME = time.time()

@app.on_event("startup")
async def startup():
    """Seed database on startup if empty."""
    logger.info(f"Guardian Local v1.0.0 starting on port {PORT}")
    try:
        conn = get_db()
        count = conn.execute("SELECT COUNT(*) FROM responses").fetchone()[0]
        conn.close()
        if count == 0:
            logger.info("Empty database — seeding responses...")
            inserted, _ = seed_database()
            logger.info(f"Seeded {inserted} responses")
        else:
            logger.info(f"Response database has {count} entries")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        # Seed anyway
        try:
            inserted, _ = seed_database()
            logger.info(f"Seeded {inserted} responses after error recovery")
        except Exception as e2:
            logger.error(f"Critical: cannot seed database: {e2}")


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.post("/guardian/local", response_model=GuardianResponse)
async def guardian_local(msg: UserMessage):
    """
    Process user message with local cognition.
    No LLM required for 85%+ of interactions.
    """
    t0 = time.time()

    # 1. Detect language
    lang, lang_conf = detect_language(msg.text)

    # 2. Classify intent
    intent, confidence, meta = classify_intent(msg.text)

    # 3. Determine if LLM is needed
    requires_llm = meta["requires_llm"]
    if confidence < CONFIDENCE_THRESHOLD:
        intent = "open_question"
        requires_llm = True
        meta["group"] = "E"
        meta["credit_cost"] = 1

    # 4. Get/create session for credit tracking
    sid = msg.session_id or "anon"
    if sid not in sessions:
        sessions[sid] = {
            "credits_left": msg.credits_left if msg.credits_left is not None else DEFAULT_FREE_CREDITS,
            "created_at": datetime.utcnow().isoformat(),
            "interactions": 0,
        }
    session = sessions[sid]
    session["interactions"] += 1
    credits_left = session["credits_left"]

    # 5. Build response
    if not requires_llm:
        # ── LOCAL RESOLUTION ──────────────────────────────────────
        text = get_response(intent, lang)
        if not text:
            # Fallback to English
            text = get_response(intent, "en")
        if not text:
            # Ultimate fallback
            text = get_response("help", lang) or get_response("help", "en")
    else:
        # ── ESCALATION ────────────────────────────────────────────
        if credits_left <= 0:
            text = get_post_credits_message(lang)
        else:
            text = get_escalation_message(intent, lang, credits_left)
        if not text:
            text = get_escalation_message("_escalation_generic", lang, credits_left)

    # 6. Update stats
    processing_ms = (time.time() - t0) * 1000
    stats["total_requests"] += 1
    if requires_llm:
        stats["llm_escalated"] += 1
    else:
        stats["local_resolved"] += 1
    stats["by_intent"][intent] = stats["by_intent"].get(intent, 0) + 1
    stats["by_lang"][lang] = stats["by_lang"].get(lang, 0) + 1

    logger.info(
        f"[{sid}] lang={lang} intent={intent} conf={confidence:.2f} "
        f"llm={requires_llm} ms={processing_ms:.1f}"
    )

    return GuardianResponse(
        text=text,
        intent=intent,
        confidence=confidence,
        language=lang,
        requires_llm=requires_llm,
        credit_cost=meta.get("credit_cost", 0),
        group=meta.get("group", ""),
        offer_alternative=meta.get("offer_alternative", False),
        session_credits_left=credits_left,
        processing_ms=round(processing_ms, 1),
    )


@app.get("/guardian/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    try:
        conn = get_db()
        db_count = conn.execute("SELECT COUNT(*) FROM responses").fetchone()[0]
        conn.close()
    except Exception:
        db_count = -1

    total = stats["total_requests"]
    local = stats["local_resolved"]
    rate = (local / total * 100) if total > 0 else 0.0

    return HealthResponse(
        status="GREEN" if db_count > 0 else "YELLOW",
        service="WINDI Guardian Local Cognition",
        version="1.0.0",
        port=PORT,
        uptime_seconds=round(time.time() - START_TIME, 1),
        total_responses=total,
        response_db_entries=db_count,
        local_resolve_rate=round(rate, 1),
    )


@app.get("/guardian/stats")
async def get_stats():
    """Detailed usage statistics."""
    total = stats["total_requests"]
    local = stats["local_resolved"]
    return {
        "total_requests": total,
        "local_resolved": local,
        "llm_escalated": stats["llm_escalated"],
        "local_resolve_rate": f"{(local / total * 100):.1f}%" if total > 0 else "N/A",
        "by_intent": dict(sorted(stats["by_intent"].items(), key=lambda x: -x[1])),
        "by_lang": dict(sorted(stats["by_lang"].items(), key=lambda x: -x[1])),
        "active_sessions": len(sessions),
        "started_at": stats["started_at"],
        "uptime_seconds": round(time.time() - START_TIME, 1),
    }


@app.post("/guardian/seed")
async def reseed():
    """Re-seed the response database."""
    try:
        inserted, skipped = seed_database()
        return {"status": "ok", "inserted": inserted, "skipped": skipped}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting Guardian Local on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
