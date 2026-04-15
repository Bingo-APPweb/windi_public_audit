#!/usr/bin/env python3
"""
W-COST-001 — Cost Intelligence Layer
=====================================
Centralizes LLM cost tracking, alerting, and learning.

Port: 8152
Invariants: I9, I11, I14

Endpoints:
  POST /api/cost/record     — Record a cost event from W-GATEWAY
  GET  /api/cost/summary    — Daily/weekly cost summary
  GET  /api/cost/by-service — Cost breakdown by service
  GET  /api/cost/alerts     — Check and trigger alerts
  GET  /api/cost/wisdom     — Candidates for Wisdom Blocks
  GET  /health              — Health check

Liga IA+H · 15 Abril 2026
"""

import os
import json
import sqlite3
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from pathlib import Path

# Load .env file
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

PORT = 8152
DB_PATH = "/opt/windi/w-cost-001/cost_ledger.db"
LOG_PATH = "/opt/windi/logs/w-cost-001.log"

# Cost per 1M tokens (EUR) — April 2026 pricing
PRICING = {
    "claude-opus-4-5-20251101": {"input": 15.0, "output": 75.0},
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    "claude-haiku-3-5-20241022": {"input": 0.25, "output": 1.25},
    "mistral-large-latest": {"input": 2.0, "output": 6.0},
    "mistral-small-latest": {"input": 0.2, "output": 0.6},
    "default": {"input": 3.0, "output": 15.0},
}

# Alert thresholds (EUR)
THRESHOLDS = {
    "daily_yellow": float(os.getenv("COST_DAILY_YELLOW", "2.0")),
    "daily_red": float(os.getenv("COST_DAILY_RED", "5.0")),
    "weekly_red": float(os.getenv("COST_WEEKLY_RED", "15.0")),
    "spike_percent": float(os.getenv("COST_SPIKE_PERCENT", "50.0")),
    "dev_max_tokens": int(os.getenv("COST_DEV_MAX_TOKENS", "10000")),
}

# Telegram config (reuse W-SEC-001 credentials)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_ALERT_CHAT_ID", "")

# Environment
ENV = os.getenv("WINDI_ENV", "production")  # "dev" or "production"

# ═══════════════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════════════

os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("w-cost-001")

# ═══════════════════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════════════════

def init_db():
    """Initialize SQLite database with cost tracking tables."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cost_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            service TEXT NOT NULL,
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            tier TEXT DEFAULT 'FREE',
            tokens_in INTEGER NOT NULL,
            tokens_out INTEGER NOT NULL,
            cost_eur REAL NOT NULL,
            wallet_id TEXT,
            task_type TEXT,
            metadata TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts_sent (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            threshold REAL,
            actual REAL,
            message TEXT
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_cost_timestamp ON cost_events(timestamp)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_cost_service ON cost_events(service)
    """)
    conn.commit()
    conn.close()
    log.info(f"Database initialized: {DB_PATH}")


@contextmanager
def get_db():
    """Database connection context manager."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════
# COST CALCULATION
# ═══════════════════════════════════════════════════════════════════════════

def calculate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    """Calculate cost in EUR based on model and token counts."""
    pricing = PRICING.get(model, PRICING["default"])
    cost_in = (tokens_in / 1_000_000) * pricing["input"]
    cost_out = (tokens_out / 1_000_000) * pricing["output"]
    return round(cost_in + cost_out, 6)


# ═══════════════════════════════════════════════════════════════════════════
# TELEGRAM ALERTS
# ═══════════════════════════════════════════════════════════════════════════

async def send_telegram_alert(message: str, alert_type: str = "INFO"):
    """Send alert via Telegram using W-SEC-001 pattern."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.warning("Telegram not configured, skipping alert")
        return False

    emoji = {"INFO": "ℹ️", "YELLOW": "🟡", "RED": "🔴", "SPIKE": "⚡"}.get(alert_type, "📊")

    text = f"""
{emoji} **W-COST-001 Alert**

{message}

_Liga IA+H · Cost Intelligence_
"""

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": text,
                    "parse_mode": "Markdown",
                },
            )
            if resp.status_code == 200:
                log.info(f"Telegram alert sent: {alert_type}")
                return True
            else:
                log.error(f"Telegram error: {resp.text}")
                return False
    except Exception as e:
        log.error(f"Telegram failed: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="W-COST-001",
    description="Cost Intelligence Layer — Liga IA+H",
    version="1.0.0",
)

# Static files
app.mount("/static", StaticFiles(directory="/opt/windi/w-cost-001/static"), name="static")


@app.get("/")
async def root():
    """Serve dashboard."""
    return FileResponse("/opt/windi/w-cost-001/static/index.html")


class CostEvent(BaseModel):
    """Cost event from W-GATEWAY."""
    service: str
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-20250514"
    tier: str = "FREE"
    tokens_in: int
    tokens_out: int
    wallet_id: Optional[str] = None
    task_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup():
    init_db()
    log.info(f"W-COST-001 starting on :{PORT} [ENV={ENV}]")
    log.info(f"Thresholds: daily_yellow=€{THRESHOLDS['daily_yellow']}, daily_red=€{THRESHOLDS['daily_red']}")


@app.get("/health")
async def health():
    """Health check endpoint."""
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM cost_events").fetchone()[0]
    return {
        "status": "healthy",
        "service": "W-COST-001",
        "port": PORT,
        "env": ENV,
        "events_recorded": count,
        "thresholds": THRESHOLDS,
    }


@app.post("/api/cost/record")
async def record_cost(event: CostEvent, background_tasks: BackgroundTasks):
    """
    Record a cost event from W-GATEWAY.

    Called after each LLM API call with token counts.
    Automatically calculates cost and checks thresholds.
    """
    # DEV mode protection
    total_tokens = event.tokens_in + event.tokens_out
    if ENV == "dev" and total_tokens > THRESHOLDS["dev_max_tokens"]:
        log.warning(f"DEV MODE: Blocking {total_tokens} tokens (max={THRESHOLDS['dev_max_tokens']})")
        raise HTTPException(
            status_code=429,
            detail=f"DEV mode: token limit exceeded ({total_tokens} > {THRESHOLDS['dev_max_tokens']})"
        )

    # Calculate cost
    cost_eur = calculate_cost(event.model, event.tokens_in, event.tokens_out)
    timestamp = datetime.now(timezone.utc).isoformat()

    # Store event
    with get_db() as conn:
        conn.execute("""
            INSERT INTO cost_events
            (timestamp, service, provider, model, tier, tokens_in, tokens_out, cost_eur, wallet_id, task_type, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            event.service,
            event.provider,
            event.model,
            event.tier,
            event.tokens_in,
            event.tokens_out,
            cost_eur,
            event.wallet_id,
            event.task_type,
            json.dumps(event.metadata) if event.metadata else None,
        ))
        conn.commit()

    log.info(f"Recorded: {event.service} | {event.model} | {event.tokens_in}+{event.tokens_out} tokens | €{cost_eur:.4f}")

    # Check thresholds in background
    background_tasks.add_task(check_and_alert)

    return {
        "status": "recorded",
        "cost_eur": cost_eur,
        "tokens_total": total_tokens,
        "timestamp": timestamp,
    }


@app.get("/api/cost/summary")
async def cost_summary(days: int = 7):
    """
    Get cost summary for the last N days.

    Returns daily totals and running weekly total.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    with get_db() as conn:
        # Daily totals
        daily = conn.execute("""
            SELECT
                date(timestamp) as day,
                SUM(cost_eur) as total_cost,
                SUM(tokens_in) as total_in,
                SUM(tokens_out) as total_out,
                COUNT(*) as calls
            FROM cost_events
            WHERE timestamp >= ?
            GROUP BY date(timestamp)
            ORDER BY day DESC
        """, (cutoff,)).fetchall()

        # Overall totals
        totals = conn.execute("""
            SELECT
                SUM(cost_eur) as total_cost,
                SUM(tokens_in) as total_in,
                SUM(tokens_out) as total_out,
                COUNT(*) as calls
            FROM cost_events
            WHERE timestamp >= ?
        """, (cutoff,)).fetchone()

        # Today's total
        today = datetime.now(timezone.utc).date().isoformat()
        today_total = conn.execute("""
            SELECT SUM(cost_eur) as cost FROM cost_events
            WHERE date(timestamp) = ?
        """, (today,)).fetchone()[0] or 0

    return {
        "period_days": days,
        "today_eur": round(today_total, 4),
        "period_total_eur": round(totals[0] or 0, 4),
        "period_tokens_in": totals[1] or 0,
        "period_tokens_out": totals[2] or 0,
        "period_calls": totals[3] or 0,
        "thresholds": {
            "daily_yellow": THRESHOLDS["daily_yellow"],
            "daily_red": THRESHOLDS["daily_red"],
            "weekly_red": THRESHOLDS["weekly_red"],
        },
        "status": get_cost_status(today_total),
        "daily": [
            {
                "day": row[0],
                "cost_eur": round(row[1], 4),
                "tokens_in": row[2],
                "tokens_out": row[3],
                "calls": row[4],
            }
            for row in daily
        ],
    }


def get_cost_status(today_cost: float) -> str:
    """Determine cost status based on today's spending."""
    if today_cost >= THRESHOLDS["daily_red"]:
        return "RED"
    elif today_cost >= THRESHOLDS["daily_yellow"]:
        return "YELLOW"
    else:
        return "GREEN"


@app.get("/api/cost/by-service")
async def cost_by_service(days: int = 7):
    """
    Get cost breakdown by service.

    Helps identify which services consume the most budget.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    with get_db() as conn:
        by_service = conn.execute("""
            SELECT
                service,
                SUM(cost_eur) as total_cost,
                SUM(tokens_in + tokens_out) as total_tokens,
                COUNT(*) as calls,
                AVG(tokens_in + tokens_out) as avg_tokens
            FROM cost_events
            WHERE timestamp >= ?
            GROUP BY service
            ORDER BY total_cost DESC
        """, (cutoff,)).fetchall()

    return {
        "period_days": days,
        "services": [
            {
                "service": row[0],
                "cost_eur": round(row[1], 4),
                "total_tokens": row[2],
                "calls": row[3],
                "avg_tokens_per_call": round(row[4], 0),
            }
            for row in by_service
        ],
    }


@app.get("/api/cost/wisdom")
async def wisdom_candidates(min_calls: int = 5, min_avg_tokens: int = 2000):
    """
    Identify candidates for Wisdom Blocks.

    Finds repetitive high-cost task types that could be cached
    or converted to local knowledge.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

    with get_db() as conn:
        candidates = conn.execute("""
            SELECT
                task_type,
                service,
                COUNT(*) as calls,
                AVG(tokens_in + tokens_out) as avg_tokens,
                SUM(cost_eur) as total_cost
            FROM cost_events
            WHERE timestamp >= ? AND task_type IS NOT NULL
            GROUP BY task_type, service
            HAVING calls >= ? AND avg_tokens >= ?
            ORDER BY total_cost DESC
            LIMIT 10
        """, (cutoff, min_calls, min_avg_tokens)).fetchall()

    return {
        "period_days": 30,
        "criteria": {
            "min_calls": min_calls,
            "min_avg_tokens": min_avg_tokens,
        },
        "candidates": [
            {
                "task_type": row[0],
                "service": row[1],
                "calls": row[2],
                "avg_tokens": round(row[3], 0),
                "total_cost_eur": round(row[4], 4),
                "recommendation": "Consider Wisdom Block caching",
            }
            for row in candidates
        ],
        "principle": "Tasks that repeat with high token cost → candidates for local knowledge",
    }


@app.get("/api/cost/test-alert")
async def test_alert():
    """
    Test Telegram alert delivery.

    Sends a test message to verify configuration.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return {
            "status": "not_configured",
            "token_set": bool(TELEGRAM_BOT_TOKEN),
            "chat_id_set": bool(TELEGRAM_CHAT_ID),
        }

    success = await send_telegram_alert(
        f"**Test Alert**\n\nW-COST-001 Telegram integration verified.\nTimestamp: {datetime.now(timezone.utc).isoformat()}",
        "INFO"
    )

    return {
        "status": "sent" if success else "failed",
        "chat_id": TELEGRAM_CHAT_ID[:4] + "****",  # Partial for privacy
    }


@app.get("/api/cost/alerts")
async def get_alerts(days: int = 7):
    """
    Get recent alerts history.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    with get_db() as conn:
        alerts = conn.execute("""
            SELECT timestamp, alert_type, threshold, actual, message
            FROM alerts_sent
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT 50
        """, (cutoff,)).fetchall()

    return {
        "period_days": days,
        "alerts": [
            {
                "timestamp": row[0],
                "type": row[1],
                "threshold": row[2],
                "actual": row[3],
                "message": row[4],
            }
            for row in alerts
        ],
    }


async def check_and_alert():
    """
    Check current costs against thresholds and send alerts.

    Called in background after each cost record.
    """
    today = datetime.now(timezone.utc).date().isoformat()
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    with get_db() as conn:
        # Today's total
        today_cost = conn.execute(
            "SELECT SUM(cost_eur) FROM cost_events WHERE date(timestamp) = ?",
            (today,)
        ).fetchone()[0] or 0

        # Weekly total
        weekly_cost = conn.execute(
            "SELECT SUM(cost_eur) FROM cost_events WHERE timestamp >= ?",
            (week_ago,)
        ).fetchone()[0] or 0

        # Check if alert already sent today
        alert_today = conn.execute(
            "SELECT COUNT(*) FROM alerts_sent WHERE date(timestamp) = ? AND alert_type = ?",
            (today, "daily_red")
        ).fetchone()[0]

    # Daily RED alert
    if today_cost >= THRESHOLDS["daily_red"] and alert_today == 0:
        msg = f"**Daily budget exceeded!**\n\nToday: €{today_cost:.2f}\nThreshold: €{THRESHOLDS['daily_red']:.2f}"
        await send_telegram_alert(msg, "RED")
        log_alert("daily_red", THRESHOLDS["daily_red"], today_cost, msg)

    # Daily YELLOW alert
    elif today_cost >= THRESHOLDS["daily_yellow"]:
        # Only alert once per threshold crossing
        pass  # Log only, no Telegram for yellow

    # Weekly RED alert
    if weekly_cost >= THRESHOLDS["weekly_red"]:
        with get_db() as conn:
            weekly_alert = conn.execute(
                "SELECT COUNT(*) FROM alerts_sent WHERE timestamp >= ? AND alert_type = ?",
                (week_ago, "weekly_red")
            ).fetchone()[0]

        if weekly_alert == 0:
            msg = f"**Weekly budget exceeded!**\n\nThis week: €{weekly_cost:.2f}\nThreshold: €{THRESHOLDS['weekly_red']:.2f}"
            await send_telegram_alert(msg, "RED")
            log_alert("weekly_red", THRESHOLDS["weekly_red"], weekly_cost, msg)


def log_alert(alert_type: str, threshold: float, actual: float, message: str):
    """Log alert to database."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO alerts_sent (timestamp, alert_type, threshold, actual, message)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            alert_type,
            threshold,
            actual,
            message,
        ))
        conn.commit()


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=PORT)
