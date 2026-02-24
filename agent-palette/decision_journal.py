#!/usr/bin/env python3
"""
WINDI Decision Journal — Memory on the Edge
=============================================

Captures the "friction" of Dragon's thinking at Gate 4.
This precedes the Forensic Receipt, recording WHY decisions were made.

Principle: "O registo de intencionalidade supera o registo de factos"
Invariant: I10 Continuity — learning never blocks execution

Deploy: /opt/windi/agent-palette/decision_journal.py
Version: 1.0.0
"""

import os
import json
import uuid
import time
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum

__version__ = "1.2.0"  # Phase 2.5: Cognitive Observability + Auto-Wisdom
__author__ = "WINDI Publishing House"

# ═══════════════════════════════════════════════════════════════
#  CONSTITUTIONAL PRINCIPLE (from Twin Dragon Audit)
# ═══════════════════════════════════════════════════════════════
#
#  "O sistema não sente. Observa.
#   Não imagina. Mede.
#   Não decide sozinho. Propõe — e espera pelo humano."
#
#  This is Cognitive Observability, not consciousness.
#  This is Decision Auditability, not autonomy.
#  This is what the European institutional market will trust.
#
# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).resolve().parent
JOURNAL_DB = BASE_DIR / "decision_journal.db"
JOURNAL_LOG = BASE_DIR / "decision_journal.log"

# Pattern mining threshold
PATTERN_MINING_INTERVAL = 100  # Analyze every N decisions

# Maturity thresholds (calibrated by Twin Dragon Audit)
MATURITY_MINIMUM = 100      # Minimum decisions for basic maturity
MATURITY_DIVERSE = 500      # Diverse decisions for real maturity
WISDOM_PROMOTION_AUTO = 20  # Auto-promote at N hits with 95%+ confidence
WISDOM_PROMOTION_MANUAL = 10  # Manual promotion threshold (Human Dragon)

# Async queue for non-blocking writes
_write_queue: List[Dict] = []
_queue_lock = threading.Lock()
_writer_thread: Optional[threading.Thread] = None
_writer_running = False


class ReasonCode(Enum):
    """Reason codes for routing decisions."""
    # Sovereignty reasons
    SOVEREIGN_DEFAULT = "SOVEREIGN_DEFAULT"
    TIER_PERSONAL_ENFORCE = "TIER_PERSONAL_ENFORCE"
    I10_CONTINUITY_BYPASS = "I10_CONTINUITY_BYPASS"
    LOCAL_PATTERN_MATCH = "LOCAL_PATTERN_MATCH"

    # Semantic reasons
    SEMANTIC_INTENT_DETECTED = "SEMANTIC_INTENT_DETECTED"
    BUDGET_AVAILABLE = "BUDGET_AVAILABLE"
    HIGH_CONFIDENCE_LLM = "HIGH_CONFIDENCE_LLM"

    # Fallback reasons
    BUDGET_EXHAUSTED_FALLBACK = "BUDGET_EXHAUSTED_FALLBACK"
    API_UNAVAILABLE_FALLBACK = "API_UNAVAILABLE_FALLBACK"
    LOW_CONFIDENCE_FALLBACK = "LOW_CONFIDENCE_FALLBACK"
    TIER_RESTRICTION_FALLBACK = "TIER_RESTRICTION_FALLBACK"


# ═══════════════════════════════════════════════════════════════
#  DATABASE INITIALIZATION
# ═══════════════════════════════════════════════════════════════

def _init_db():
    """Initialize the Decision Journal SQLite database."""
    conn = sqlite3.connect(str(JOURNAL_DB))
    cursor = conn.cursor()

    # Decision Receipts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS decision_receipts (
            dr_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            intent_detected TEXT NOT NULL,
            confidence_score REAL NOT NULL,
            tier TEXT NOT NULL,
            route_selected TEXT NOT NULL,
            candidates_rejected TEXT,
            reason_code TEXT NOT NULL,
            wisdom_alignment TEXT,
            latency_ms INTEGER,
            pattern_id TEXT,
            uncertainty_detected INTEGER DEFAULT 0,
            created_at INTEGER NOT NULL
        )
    """)

    # Pattern cache table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pattern_cache (
            pattern_id TEXT PRIMARY KEY,
            intent TEXT NOT NULL,
            route TEXT NOT NULL,
            hit_count INTEGER DEFAULT 1,
            avg_confidence REAL,
            avg_latency_ms REAL,
            last_seen TEXT,
            created_at TEXT
        )
    """)

    # Wisdom alignment index
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wisdom_hits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wisdom_id TEXT NOT NULL,
            dr_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (dr_id) REFERENCES decision_receipts(dr_id)
        )
    """)

    # Indexes for fast queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dr_timestamp ON decision_receipts(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dr_intent ON decision_receipts(intent_detected)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dr_route ON decision_receipts(route_selected)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dr_reason ON decision_receipts(reason_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pattern_intent ON pattern_cache(intent)")

    conn.commit()
    conn.close()


# Initialize on import
_init_db()


# ═══════════════════════════════════════════════════════════════
#  DECISION RECEIPT GENERATION
# ═══════════════════════════════════════════════════════════════

def generate_dr_id() -> str:
    """Generate a UUIDv7-style Decision Receipt ID."""
    # UUIDv7 = timestamp + random
    ts = int(time.time() * 1000)
    ts_hex = format(ts, '012x')
    rand_hex = uuid.uuid4().hex[:20]
    return f"DR-{ts_hex[:8]}-{rand_hex[:12]}"


def create_decision_receipt(
    intent_detected: str,
    confidence_score: float,
    tier: str,
    route_selected: str,
    candidates_rejected: List[str],
    reason_code: str,
    wisdom_alignment: Optional[List[str]] = None,
    latency_ms: Optional[int] = None,
    pattern_id: Optional[str] = None,
    uncertainty_detected: bool = False
) -> Dict[str, Any]:
    """
    Create a Decision Receipt capturing the routing decision.

    This is the core of Memory on the Edge — capturing WHY
    the Dragon made a choice, not just WHAT it chose.
    """
    now = datetime.now(timezone.utc)

    dr = {
        "dr_id": generate_dr_id(),
        "timestamp": now.isoformat(),
        "context": {
            "intent_detected": intent_detected,
            "confidence_score": round(confidence_score, 4),
            "tier": tier,
        },
        "decision_logic": {
            "route_selected": route_selected,
            "candidates_rejected": candidates_rejected,
            "reason_code": reason_code,
            "wisdom_alignment": wisdom_alignment or [],
        },
        "edge_learning": {
            "latency_ms": latency_ms,
            "pattern_id": pattern_id or _derive_pattern_id(intent_detected, route_selected),
            "uncertainty_detected": uncertainty_detected,
        }
    }

    return dr


def _derive_pattern_id(intent: str, route: str) -> str:
    """Derive a pattern ID from intent and route."""
    intent_short = intent.upper().replace("_", "-")[:12]
    route_short = "LOC" if "local" in route.lower() else "SEM"
    return f"P-AUTO-{intent_short}-{route_short}"


# ═══════════════════════════════════════════════════════════════
#  ASYNC JOURNAL WRITER
# ═══════════════════════════════════════════════════════════════

def _writer_loop():
    """Background thread for async journal writes."""
    global _writer_running

    while _writer_running:
        entries_to_write = []

        with _queue_lock:
            if _write_queue:
                entries_to_write = _write_queue.copy()
                _write_queue.clear()

        if entries_to_write:
            _batch_write(entries_to_write)

        time.sleep(0.1)  # 100ms batch interval


def _batch_write(entries: List[Dict]):
    """Write a batch of decision receipts to the journal."""
    try:
        conn = sqlite3.connect(str(JOURNAL_DB))
        cursor = conn.cursor()

        for dr in entries:
            cursor.execute("""
                INSERT INTO decision_receipts (
                    dr_id, timestamp, intent_detected, confidence_score,
                    tier, route_selected, candidates_rejected, reason_code,
                    wisdom_alignment, latency_ms, pattern_id,
                    uncertainty_detected, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dr["dr_id"],
                dr["timestamp"],
                dr["context"]["intent_detected"],
                dr["context"]["confidence_score"],
                dr["context"]["tier"],
                dr["decision_logic"]["route_selected"],
                json.dumps(dr["decision_logic"]["candidates_rejected"]),
                dr["decision_logic"]["reason_code"],
                json.dumps(dr["decision_logic"]["wisdom_alignment"]),
                dr["edge_learning"]["latency_ms"],
                dr["edge_learning"]["pattern_id"],
                1 if dr["edge_learning"]["uncertainty_detected"] else 0,
                int(time.time())
            ))

            # Update pattern cache
            _update_pattern_cache(cursor, dr)

            # Record wisdom hits
            for wisdom_id in dr["decision_logic"]["wisdom_alignment"]:
                cursor.execute("""
                    INSERT INTO wisdom_hits (wisdom_id, dr_id, timestamp)
                    VALUES (?, ?, ?)
                """, (wisdom_id, dr["dr_id"], dr["timestamp"]))

        conn.commit()
        conn.close()

        # Also append to log file for redundancy
        _append_to_log(entries)

    except Exception as e:
        print(f"[DecisionJournal] Write error: {e}")


def _update_pattern_cache(cursor, dr: Dict):
    """Update the pattern cache with this decision."""
    pattern_id = dr["edge_learning"]["pattern_id"]
    intent = dr["context"]["intent_detected"]
    route = dr["decision_logic"]["route_selected"]
    confidence = dr["context"]["confidence_score"]
    latency = dr["edge_learning"]["latency_ms"] or 0

    # Check if pattern exists
    cursor.execute("SELECT hit_count, avg_confidence, avg_latency_ms FROM pattern_cache WHERE pattern_id = ?", (pattern_id,))
    row = cursor.fetchone()

    if row:
        # Update existing pattern
        hit_count = row[0] + 1
        avg_conf = ((row[1] * row[0]) + confidence) / hit_count
        avg_lat = ((row[2] * row[0]) + latency) / hit_count

        cursor.execute("""
            UPDATE pattern_cache
            SET hit_count = ?, avg_confidence = ?, avg_latency_ms = ?, last_seen = ?
            WHERE pattern_id = ?
        """, (hit_count, avg_conf, avg_lat, dr["timestamp"], pattern_id))
    else:
        # Insert new pattern
        cursor.execute("""
            INSERT INTO pattern_cache (pattern_id, intent, route, hit_count, avg_confidence, avg_latency_ms, last_seen, created_at)
            VALUES (?, ?, ?, 1, ?, ?, ?, ?)
        """, (pattern_id, intent, route, confidence, latency, dr["timestamp"], dr["timestamp"]))


def _append_to_log(entries: List[Dict]):
    """Append entries to the log file for redundancy."""
    try:
        with open(JOURNAL_LOG, "a") as f:
            for dr in entries:
                f.write(json.dumps(dr) + "\n")
    except Exception as e:
        print(f"[DecisionJournal] Log append error: {e}")


def start_writer():
    """Start the background writer thread."""
    global _writer_thread, _writer_running

    if _writer_thread is None or not _writer_thread.is_alive():
        _writer_running = True
        _writer_thread = threading.Thread(target=_writer_loop, daemon=True)
        _writer_thread.start()
        print("[DecisionJournal] Background writer started")


def stop_writer():
    """Stop the background writer thread."""
    global _writer_running
    _writer_running = False
    if _writer_thread:
        _writer_thread.join(timeout=1.0)


# Auto-start writer on import
start_writer()


# ═══════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════

def record_decision(
    intent_detected: str,
    confidence_score: float,
    tier: str,
    route_selected: str,
    candidates_rejected: List[str],
    reason_code: str,
    wisdom_alignment: Optional[List[str]] = None,
    latency_ms: Optional[int] = None,
    uncertainty_detected: bool = False
) -> str:
    """
    Record a routing decision asynchronously.

    Returns the Decision Receipt ID immediately.
    The actual write happens in the background.

    This is the main entry point for Gate 4 integration.
    """
    dr = create_decision_receipt(
        intent_detected=intent_detected,
        confidence_score=confidence_score,
        tier=tier,
        route_selected=route_selected,
        candidates_rejected=candidates_rejected,
        reason_code=reason_code,
        wisdom_alignment=wisdom_alignment,
        latency_ms=latency_ms,
        uncertainty_detected=uncertainty_detected
    )

    with _queue_lock:
        _write_queue.append(dr)

    return dr["dr_id"]


def get_decision_stats() -> Dict[str, Any]:
    """Get statistics from the Decision Journal."""
    try:
        conn = sqlite3.connect(str(JOURNAL_DB))
        cursor = conn.cursor()

        # Total decisions
        cursor.execute("SELECT COUNT(*) FROM decision_receipts")
        total = cursor.fetchone()[0]

        # Today's decisions
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cursor.execute("SELECT COUNT(*) FROM decision_receipts WHERE timestamp LIKE ?", (f"{today}%",))
        today_count = cursor.fetchone()[0]

        # Route distribution
        cursor.execute("""
            SELECT route_selected, COUNT(*) as cnt
            FROM decision_receipts
            GROUP BY route_selected
            ORDER BY cnt DESC
        """)
        routes = {row[0]: row[1] for row in cursor.fetchall()}

        # Reason code distribution
        cursor.execute("""
            SELECT reason_code, COUNT(*) as cnt
            FROM decision_receipts
            GROUP BY reason_code
            ORDER BY cnt DESC
        """)
        reasons = {row[0]: row[1] for row in cursor.fetchall()}

        # Average confidence
        cursor.execute("SELECT AVG(confidence_score) FROM decision_receipts")
        avg_confidence = cursor.fetchone()[0] or 0.0

        # Uncertainty rate
        cursor.execute("SELECT COUNT(*) FROM decision_receipts WHERE uncertainty_detected = 1")
        uncertain = cursor.fetchone()[0]
        uncertainty_rate = (uncertain / total * 100) if total > 0 else 0.0

        # Local vs Semantic ratio
        cursor.execute("SELECT COUNT(*) FROM decision_receipts WHERE route_selected LIKE '%local%'")
        local_count = cursor.fetchone()[0]
        local_ratio = (local_count / total * 100) if total > 0 else 0.0

        # Top patterns
        cursor.execute("""
            SELECT pattern_id, hit_count, avg_confidence
            FROM pattern_cache
            ORDER BY hit_count DESC
            LIMIT 10
        """)
        top_patterns = [
            {"pattern_id": row[0], "hits": row[1], "avg_confidence": round(row[2], 4)}
            for row in cursor.fetchall()
        ]

        conn.close()

        return {
            "total_decisions": total,
            "today_decisions": today_count,
            "avg_confidence": round(avg_confidence, 4),
            "uncertainty_rate": round(uncertainty_rate, 2),
            "local_intelligence_ratio": round(local_ratio, 2),
            "route_distribution": routes,
            "reason_distribution": reasons,
            "top_patterns": top_patterns,
            "journal_version": __version__,
        }

    except Exception as e:
        return {"error": str(e)}


def get_recent_decisions(limit: int = 20) -> List[Dict]:
    """Get the most recent decision receipts."""
    try:
        conn = sqlite3.connect(str(JOURNAL_DB))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT dr_id, timestamp, intent_detected, confidence_score,
                   tier, route_selected, candidates_rejected, reason_code,
                   wisdom_alignment, latency_ms, pattern_id, uncertainty_detected
            FROM decision_receipts
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))

        results = []
        for row in cursor.fetchall():
            results.append({
                "dr_id": row[0],
                "timestamp": row[1],
                "context": {
                    "intent_detected": row[2],
                    "confidence_score": row[3],
                    "tier": row[4],
                },
                "decision_logic": {
                    "route_selected": row[5],
                    "candidates_rejected": json.loads(row[6]) if row[6] else [],
                    "reason_code": row[7],
                    "wisdom_alignment": json.loads(row[8]) if row[8] else [],
                },
                "edge_learning": {
                    "latency_ms": row[9],
                    "pattern_id": row[10],
                    "uncertainty_detected": bool(row[11]),
                }
            })

        conn.close()
        return results

    except Exception as e:
        return [{"error": str(e)}]


def get_autonomy_intelligence() -> Dict[str, Any]:
    """
    Calculate the Local Active Intelligence metrics.

    This shows users the value of their tier Personal:
    they're not using a "capped version", but a system
    that learns locally from their choices.
    """
    try:
        conn = sqlite3.connect(str(JOURNAL_DB))
        cursor = conn.cursor()

        # Total local decisions (no LLM)
        cursor.execute("""
            SELECT COUNT(*) FROM decision_receipts
            WHERE route_selected LIKE '%local%'
        """)
        local_decisions = cursor.fetchone()[0]

        # Total decisions
        cursor.execute("SELECT COUNT(*) FROM decision_receipts")
        total = cursor.fetchone()[0]

        # Patterns learned
        cursor.execute("SELECT COUNT(*) FROM pattern_cache")
        patterns_learned = cursor.fetchone()[0]

        # High confidence decisions (> 0.9)
        cursor.execute("SELECT COUNT(*) FROM decision_receipts WHERE confidence_score > 0.9")
        high_confidence = cursor.fetchone()[0]

        # Wisdom alignments
        cursor.execute("SELECT COUNT(DISTINCT wisdom_id) FROM wisdom_hits")
        wisdom_active = cursor.fetchone()[0]

        # Average latency for local decisions
        cursor.execute("""
            SELECT AVG(latency_ms) FROM decision_receipts
            WHERE route_selected LIKE '%local%' AND latency_ms IS NOT NULL
        """)
        avg_local_latency = cursor.fetchone()[0] or 0

        # Fallback success rate (I10 continuity)
        cursor.execute("""
            SELECT COUNT(*) FROM decision_receipts
            WHERE reason_code LIKE '%FALLBACK%'
        """)
        fallback_count = cursor.fetchone()[0]

        conn.close()

        local_ratio = (local_decisions / total * 100) if total > 0 else 0
        high_conf_ratio = (high_confidence / total * 100) if total > 0 else 0

        return {
            "local_intelligence": {
                "decisions_without_api": local_decisions,
                "total_decisions": total,
                "sovereignty_ratio": round(local_ratio, 2),
            },
            "learning_metrics": {
                "patterns_learned": patterns_learned,
                "high_confidence_decisions": high_confidence,
                "high_confidence_ratio": round(high_conf_ratio, 2),
                "wisdom_blocks_active": wisdom_active,
            },
            "performance": {
                "avg_local_latency_ms": round(avg_local_latency, 1),
                "i10_fallbacks_handled": fallback_count,
            },
            "message": _generate_autonomy_message(local_ratio, patterns_learned),
        }

    except Exception as e:
        return {"error": str(e)}


def _generate_autonomy_message(local_ratio: float, patterns: int) -> str:
    """Generate a human-readable autonomy message."""
    if local_ratio >= 99:
        return f"Autonomia Total: {patterns} padroes aprendidos localmente. Zero dependencia externa."
    elif local_ratio >= 95:
        return f"Autonomia Elevada: {local_ratio}% decisoes locais, {patterns} padroes activos."
    elif local_ratio >= 90:
        return f"Autonomia Solida: {local_ratio}% soberano, sistema a aprender com as tuas escolhas."
    else:
        return f"A Construir Autonomia: {local_ratio}% local, {patterns} padroes em crescimento."


# ═══════════════════════════════════════════════════════════════
#  PATTERN MINING (Phase 2.5 preparation)
# ═══════════════════════════════════════════════════════════════

def should_trigger_mining() -> bool:
    """Check if pattern mining should be triggered."""
    try:
        conn = sqlite3.connect(str(JOURNAL_DB))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM decision_receipts")
        total = cursor.fetchone()[0]
        conn.close()
        return total > 0 and total % PATTERN_MINING_INTERVAL == 0
    except:
        return False


def get_hesitation_patterns(confidence_threshold: float = 0.7) -> List[Dict]:
    """
    Detect patterns where the router hesitates (low confidence).
    These are candidates for new Wisdom Blocks.
    """
    try:
        conn = sqlite3.connect(str(JOURNAL_DB))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT intent_detected, COUNT(*) as cnt, AVG(confidence_score) as avg_conf
            FROM decision_receipts
            WHERE confidence_score < ?
            GROUP BY intent_detected
            HAVING cnt >= 3
            ORDER BY cnt DESC
        """, (confidence_threshold,))

        hesitations = [
            {
                "intent": row[0],
                "occurrences": row[1],
                "avg_confidence": round(row[2], 4),
                "suggestion": f"Consider adding Wisdom Block for '{row[0]}' intent"
            }
            for row in cursor.fetchall()
        ]

        conn.close()
        return hesitations

    except Exception as e:
        return [{"error": str(e)}]


# ═══════════════════════════════════════════════════════════════
#  WINDI COGNITIVE SCORE (Phase 2.5: Self-Calibrating Router)
# ═══════════════════════════════════════════════════════════════

# Thresholds for cognitive evolution
HESITATION_THRESHOLD = 0.75  # Below this = hesitation
WISDOM_AUTO_CREATE_THRESHOLD = 5  # Create wisdom after N hesitations
COGNITIVE_MATURITY_THRESHOLD = 100  # Decisions needed for maturity

def calculate_cognitive_score() -> Dict[str, Any]:
    """
    Calculate the WINDI Cognitive Score.

    This score measures how "intelligent" the system has become
    based on its decision patterns, confidence evolution, and
    learning trajectory.

    Score Components:
    - Sovereignty (40%): How many decisions are local
    - Confidence (25%): Average decision confidence
    - Stability (20%): Consistency of routing patterns
    - Learning (15%): Pattern accumulation rate
    """
    try:
        conn = sqlite3.connect(str(JOURNAL_DB))
        cursor = conn.cursor()

        # Total decisions
        cursor.execute("SELECT COUNT(*) FROM decision_receipts")
        total = cursor.fetchone()[0]

        if total == 0:
            return {
                "score": 0,
                "grade": "NASCENT",
                "components": {},
                "message": "Sem decisoes registadas. O sistema ainda nao iniciou aprendizagem."
            }

        # Component 1: Sovereignty (40%)
        cursor.execute("SELECT COUNT(*) FROM decision_receipts WHERE route_selected LIKE '%local%'")
        local_count = cursor.fetchone()[0]
        sovereignty_ratio = local_count / total
        sovereignty_score = sovereignty_ratio * 40

        # Component 2: Confidence (25%)
        cursor.execute("SELECT AVG(confidence_score) FROM decision_receipts")
        avg_confidence = cursor.fetchone()[0] or 0
        confidence_score = avg_confidence * 25

        # Component 3: Stability (20%)
        # Measure how consistent the routing is for same intents
        cursor.execute("""
            SELECT intent_detected,
                   COUNT(DISTINCT route_selected) as route_variance
            FROM decision_receipts
            GROUP BY intent_detected
        """)
        intent_routes = cursor.fetchall()
        if intent_routes:
            # Lower variance = higher stability
            avg_variance = sum(r[1] for r in intent_routes) / len(intent_routes)
            stability_ratio = max(0, 1 - (avg_variance - 1) * 0.5)  # 1 route = 100%, 2 routes = 50%
            stability_score = stability_ratio * 20
        else:
            stability_score = 0

        # Component 4: Learning (15%)
        cursor.execute("SELECT COUNT(*) FROM pattern_cache")
        patterns = cursor.fetchone()[0]
        # Learning curve: more patterns = better, but with diminishing returns
        learning_ratio = min(1.0, patterns / 20)  # Cap at 20 patterns for full score
        learning_score = learning_ratio * 15

        # Total score
        total_score = sovereignty_score + confidence_score + stability_score + learning_score

        # Grade assignment
        if total_score >= 90:
            grade = "SOVEREIGN"
            stage = "Cognicao Soberana"
        elif total_score >= 75:
            grade = "AUTONOMOUS"
            stage = "Autonomia"
        elif total_score >= 60:
            grade = "INTELLIGENT"
            stage = "Edge Intelligence"
        elif total_score >= 40:
            grade = "LEARNING"
            stage = "Acumulacao"
        else:
            grade = "BOOTSTRAP"
            stage = "Bootstrap"

        # Maturity assessment
        maturity = min(100, (total / COGNITIVE_MATURITY_THRESHOLD) * 100)

        conn.close()

        return {
            "score": round(total_score, 2),
            "grade": grade,
            "stage": stage,
            "maturity_pct": round(maturity, 1),
            "components": {
                "sovereignty": {
                    "score": round(sovereignty_score, 2),
                    "max": 40,
                    "ratio": round(sovereignty_ratio * 100, 1),
                },
                "confidence": {
                    "score": round(confidence_score, 2),
                    "max": 25,
                    "avg": round(avg_confidence, 4),
                },
                "stability": {
                    "score": round(stability_score, 2),
                    "max": 20,
                    "ratio": round(stability_ratio * 100 if 'stability_ratio' in dir() else 0, 1),
                },
                "learning": {
                    "score": round(learning_score, 2),
                    "max": 15,
                    "patterns": patterns,
                },
            },
            "total_decisions": total,
            "message": _generate_cognitive_message(grade, total_score, patterns),
        }

    except Exception as e:
        return {"error": str(e)}


def _generate_cognitive_message(grade: str, score: float, patterns: int) -> str:
    """Generate a human-readable cognitive evolution message."""
    messages = {
        "SOVEREIGN": f"Cognicao Soberana activa. Score {score}/100. {patterns} padroes consolidados. O sistema observa-se a si proprio.",
        "AUTONOMOUS": f"Autonomia operacional. Score {score}/100. Decisoes emergem localmente.",
        "INTELLIGENT": f"Edge Intelligence activa. Score {score}/100. A aprender com cada escolha.",
        "LEARNING": f"Fase de acumulacao. Score {score}/100. Padroes em formacao.",
        "BOOTSTRAP": f"Bootstrap inicial. Score {score}/100. Sistema a despertar.",
    }
    return messages.get(grade, f"Score: {score}/100")


# ═══════════════════════════════════════════════════════════════
#  AUTO-WISDOM GENERATION (Phase 2.5: Self-Calibrating)
# ═══════════════════════════════════════════════════════════════

def detect_wisdom_candidates() -> List[Dict]:
    """
    Detect patterns that should become Wisdom Blocks.

    A pattern becomes a Wisdom candidate when:
    1. It has been seen multiple times (hit_count >= 5)
    2. It has high confidence (> 0.9)
    3. It's consistently routed the same way

    This is the bridge between correlation and causality.
    """
    try:
        conn = sqlite3.connect(str(JOURNAL_DB))
        cursor = conn.cursor()

        # Find high-confidence, frequently-used patterns
        cursor.execute("""
            SELECT pattern_id, intent, route, hit_count, avg_confidence
            FROM pattern_cache
            WHERE hit_count >= 5 AND avg_confidence > 0.9
            ORDER BY hit_count DESC
        """)

        candidates = []
        for row in cursor.fetchall():
            candidates.append({
                "pattern_id": row[0],
                "intent": row[1],
                "route": row[2],
                "evidence": {
                    "hit_count": row[3],
                    "avg_confidence": round(row[4], 4),
                },
                "suggested_wisdom": {
                    "id": f"W-AUTO-{row[0].split('-')[-1]}",
                    "type": "pattern_consolidation",
                    "content": f"Intent '{row[1]}' consistently routes to '{row[2]}' with {row[4]:.1%} confidence",
                    "source": "decision_journal_mining",
                },
                "ready_for_promotion": row[3] >= 10 and row[4] > 0.95,
            })

        conn.close()
        return candidates

    except Exception as e:
        return [{"error": str(e)}]


def detect_cognitive_hesitation() -> Dict[str, Any]:
    """
    Detect where the system is "hesitating" cognitively.

    Hesitation indicators:
    1. Low confidence decisions (< 0.75)
    2. Route switching for same intent
    3. High latency decisions
    4. Uncertainty flags

    This enables self-calibration: the system knows where it's weak.
    """
    try:
        conn = sqlite3.connect(str(JOURNAL_DB))
        cursor = conn.cursor()

        # Low confidence decisions
        cursor.execute("""
            SELECT intent_detected, COUNT(*) as cnt, AVG(confidence_score) as avg_conf
            FROM decision_receipts
            WHERE confidence_score < ?
            GROUP BY intent_detected
            ORDER BY cnt DESC
        """, (HESITATION_THRESHOLD,))

        low_confidence = [
            {"intent": row[0], "count": row[1], "avg_confidence": round(row[2], 4)}
            for row in cursor.fetchall()
        ]

        # Route inconsistency (same intent, different routes)
        cursor.execute("""
            SELECT intent_detected, COUNT(DISTINCT route_selected) as routes,
                   GROUP_CONCAT(DISTINCT route_selected) as route_list
            FROM decision_receipts
            GROUP BY intent_detected
            HAVING routes > 1
        """)

        inconsistent = [
            {"intent": row[0], "route_variance": row[1], "routes": row[2].split(",")}
            for row in cursor.fetchall()
        ]

        # High latency decisions (> 50ms for local)
        cursor.execute("""
            SELECT intent_detected, AVG(latency_ms) as avg_lat, COUNT(*) as cnt
            FROM decision_receipts
            WHERE route_selected LIKE '%local%' AND latency_ms > 50
            GROUP BY intent_detected
            ORDER BY avg_lat DESC
        """)

        slow_decisions = [
            {"intent": row[0], "avg_latency_ms": round(row[1], 1), "count": row[2]}
            for row in cursor.fetchall()
        ]

        # Uncertainty flags
        cursor.execute("""
            SELECT intent_detected, COUNT(*) as cnt
            FROM decision_receipts
            WHERE uncertainty_detected = 1
            GROUP BY intent_detected
            ORDER BY cnt DESC
        """)

        uncertain = [
            {"intent": row[0], "uncertainty_count": row[1]}
            for row in cursor.fetchall()
        ]

        conn.close()

        # Calculate hesitation score (0-100, lower is better)
        total_hesitation_signals = (
            len(low_confidence) * 3 +
            len(inconsistent) * 5 +
            len(slow_decisions) * 1 +
            len(uncertain) * 2
        )
        hesitation_score = min(100, total_hesitation_signals * 5)

        return {
            "hesitation_score": hesitation_score,
            "health": "HEALTHY" if hesitation_score < 20 else "ATTENTION" if hesitation_score < 50 else "CALIBRATION_NEEDED",
            "signals": {
                "low_confidence_intents": low_confidence,
                "routing_inconsistency": inconsistent,
                "slow_decisions": slow_decisions,
                "uncertainty_flags": uncertain,
            },
            "recommendations": _generate_calibration_recommendations(
                low_confidence, inconsistent, slow_decisions
            ),
        }

    except Exception as e:
        return {"error": str(e)}


def _generate_calibration_recommendations(low_conf: List, inconsistent: List, slow: List) -> List[str]:
    """Generate actionable calibration recommendations."""
    recommendations = []

    if low_conf:
        top = low_conf[0]
        recommendations.append(
            f"Adicionar Wisdom Block para intent '{top['intent']}' - confianca media {top['avg_confidence']:.1%}"
        )

    if inconsistent:
        top = inconsistent[0]
        recommendations.append(
            f"Consolidar routing para '{top['intent']}' - {top['route_variance']} rotas diferentes detectadas"
        )

    if slow:
        top = slow[0]
        recommendations.append(
            f"Optimizar handler para '{top['intent']}' - latencia media {top['avg_latency_ms']}ms"
        )

    if not recommendations:
        recommendations.append("Sistema calibrado. Sem accoes necessarias.")

    return recommendations


def get_cognitive_evolution() -> Dict[str, Any]:
    """
    Get the full cognitive evolution report.

    This combines:
    - Cognitive Score
    - Hesitation Detection
    - Wisdom Candidates
    - Learning Trajectory

    This is Cognitive Observability — not consciousness.
    This is Decision Auditability — not autonomy.
    """
    score = calculate_cognitive_score()
    hesitation = detect_cognitive_hesitation()
    wisdom_candidates = detect_wisdom_candidates()

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cognitive_score": score,
        "hesitation_analysis": hesitation,
        "wisdom_candidates": wisdom_candidates,
        "evolution_stage": score.get("stage", "UNKNOWN"),
        "principle": "O sistema nao sente. Observa. Nao imagina. Mede. Nao decide sozinho. Propoe — e espera pelo humano.",
    }


# ═══════════════════════════════════════════════════════════════
#  OUTLOOK & PULSE INTEGRATION (Cognitive Observability Metrics)
# ═══════════════════════════════════════════════════════════════

def get_outlook_cognitive_feature() -> Dict[str, Any]:
    """
    Export cognitive metrics as an OUTLOOK feature.

    This allows WINDI Outlook to track cognitive evolution
    alongside document production and seal pipeline features.
    """
    try:
        score = calculate_cognitive_score()
        stats = get_decision_stats()

        # Determine status based on cognitive health
        cognitive_grade = score.get("grade", "BOOTSTRAP")
        if cognitive_grade in ("SOVEREIGN", "AUTONOMOUS"):
            status = "WIRED"
        elif cognitive_grade in ("INTELLIGENT", "LEARNING"):
            status = "ON_SERVER"
        else:
            status = "NOT_BUILT"

        return {
            "id": "C01",
            "name": "Cognitive Observability Engine",
            "sprint": 5,  # Phase 2.5 is Sprint 5
            "category": "cognition",
            "status": status,
            "checks": [
                {
                    "label": "Decision Journal",
                    "status": "ok" if stats.get("total_decisions", 0) > 0 else "pending",
                    "metric": f"{stats.get('total_decisions', 0)} decisions"
                },
                {
                    "label": "Cognitive Score",
                    "status": "ok" if score.get("score", 0) >= 60 else "attention",
                    "metric": f"{score.get('score', 0):.1f}/100 ({cognitive_grade})"
                },
                {
                    "label": "Pattern Learning",
                    "status": "ok" if len(stats.get("top_patterns", [])) > 0 else "pending",
                    "metric": f"{len(stats.get('top_patterns', []))} patterns"
                },
            ],
            "cognitive_metrics": {
                "score": score.get("score", 0),
                "grade": cognitive_grade,
                "stage": score.get("stage", "Unknown"),
                "maturity_pct": score.get("maturity_pct", 0),
                "decisions_total": stats.get("total_decisions", 0),
                "decisions_today": stats.get("today_decisions", 0),
                "local_ratio": stats.get("local_intelligence_ratio", 0),
                "patterns_learned": len(stats.get("top_patterns", [])),
                "avg_confidence": stats.get("avg_confidence", 0),
            }
        }

    except Exception as e:
        return {
            "id": "C01",
            "name": "Cognitive Observability Engine",
            "status": "DOWN",
            "error": str(e)
        }


def get_pulse_cognitive_wire() -> Dict[str, Any]:
    """
    Export cognitive metrics as a PULSE wire check.

    This allows WINDI Pulse to monitor cognitive health
    as part of the ecosystem health dashboard.
    """
    try:
        score = calculate_cognitive_score()
        hesitation = detect_cognitive_hesitation()
        stats = get_decision_stats()

        # Health based on hesitation score
        hesitation_score = hesitation.get("hesitation_score", 0)
        if hesitation_score == 0:
            health = "HEALTHY"
            health_code = 200
        elif hesitation_score < 20:
            health = "GOOD"
            health_code = 200
        elif hesitation_score < 50:
            health = "ATTENTION"
            health_code = 200
        else:
            health = "CALIBRATION_NEEDED"
            health_code = 503

        return {
            "service": "Cognitive Observability",
            "port": 8108,
            "endpoint": "/api/dragon/cognitive/score",
            "status": health,
            "code": health_code,
            "wire": {
                "name": "W-COG-01",
                "description": "Decision Journal → Pattern Cache → Cognitive Score",
                "status": "WIRED" if stats.get("total_decisions", 0) > 0 else "PENDING",
            },
            "metrics": {
                "cognitive_score": score.get("score", 0),
                "cognitive_grade": score.get("grade", "BOOTSTRAP"),
                "hesitation_score": hesitation_score,
                "decisions_total": stats.get("total_decisions", 0),
                "patterns_learned": len(stats.get("top_patterns", [])),
                "sovereignty_ratio": stats.get("local_intelligence_ratio", 0),
                "avg_latency_ms": score.get("components", {}).get("stability", {}).get("ratio", 0),
            },
            "thresholds": {
                "maturity_minimum": MATURITY_MINIMUM,
                "maturity_diverse": MATURITY_DIVERSE,
                "current_progress": f"{stats.get('total_decisions', 0)}/{MATURITY_DIVERSE}",
            }
        }

    except Exception as e:
        return {
            "service": "Cognitive Observability",
            "status": "DOWN",
            "code": 500,
            "error": str(e)
        }


def promote_wisdom_candidate(pattern_id: str, promoted_by: str = "Human Dragon") -> Dict[str, Any]:
    """
    Manually promote a pattern to Wisdom Block.

    This is the Human Dragon's prerogative — to observe what the system
    proposes and decide to formalize it as Wisdom.

    "O sistema propõe. O humano decide."
    """
    try:
        conn = sqlite3.connect(str(JOURNAL_DB))
        cursor = conn.cursor()

        # Find the pattern
        cursor.execute("""
            SELECT pattern_id, intent, route, hit_count, avg_confidence
            FROM pattern_cache
            WHERE pattern_id = ?
        """, (pattern_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return {"error": f"Pattern '{pattern_id}' not found"}

        pattern_id, intent, route, hits, confidence = row

        # Check minimum threshold
        if hits < WISDOM_PROMOTION_MANUAL:
            conn.close()
            return {
                "error": f"Pattern has only {hits} hits. Minimum for manual promotion is {WISDOM_PROMOTION_MANUAL}.",
                "pattern_id": pattern_id
            }

        # Generate Wisdom Block ID
        wisdom_id = f"W-COG-{datetime.now().strftime('%Y%m%d')}-{pattern_id.split('-')[-1][:4].upper()}"

        # Create Wisdom Block record
        wisdom_block = {
            "id": wisdom_id,
            "type": "pattern_promotion",
            "source": "decision_journal",
            "pattern_id": pattern_id,
            "intent": intent,
            "route": route,
            "evidence": {
                "hit_count": hits,
                "avg_confidence": round(confidence, 4),
            },
            "promoted_by": promoted_by,
            "promoted_at": datetime.now(timezone.utc).isoformat(),
            "principle": "O sistema propoe. O humano decide.",
        }

        # Store in a wisdom_blocks table (create if not exists)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wisdom_blocks (
                wisdom_id TEXT PRIMARY KEY,
                pattern_id TEXT,
                intent TEXT,
                route TEXT,
                hit_count INTEGER,
                avg_confidence REAL,
                promoted_by TEXT,
                promoted_at TEXT,
                content TEXT
            )
        """)

        cursor.execute("""
            INSERT INTO wisdom_blocks (wisdom_id, pattern_id, intent, route, hit_count, avg_confidence, promoted_by, promoted_at, content)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            wisdom_id, pattern_id, intent, route, hits, confidence,
            promoted_by, wisdom_block["promoted_at"],
            f"Intent '{intent}' routes to '{route}' with {confidence:.1%} confidence (verified by {hits} decisions)"
        ))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "wisdom_block": wisdom_block,
            "message": f"Pattern '{pattern_id}' promoted to Wisdom Block '{wisdom_id}' by {promoted_by}",
        }

    except Exception as e:
        return {"error": str(e)}


def get_wisdom_blocks() -> List[Dict]:
    """Get all promoted Wisdom Blocks."""
    try:
        conn = sqlite3.connect(str(JOURNAL_DB))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT wisdom_id, pattern_id, intent, route, hit_count, avg_confidence, promoted_by, promoted_at, content
            FROM wisdom_blocks
            ORDER BY promoted_at DESC
        """)

        blocks = [
            {
                "wisdom_id": row[0],
                "pattern_id": row[1],
                "intent": row[2],
                "route": row[3],
                "evidence": {"hit_count": row[4], "avg_confidence": row[5]},
                "promoted_by": row[6],
                "promoted_at": row[7],
                "content": row[8],
            }
            for row in cursor.fetchall()
        ]

        conn.close()
        return blocks

    except Exception as e:
        return [{"error": str(e)}]


# ═══════════════════════════════════════════════════════════════
#  SELF-TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"WINDI Decision Journal v{__version__}")
    print("=" * 50)

    # Test decision recording
    dr_id = record_decision(
        intent_detected="generate_pdf",
        confidence_score=0.98,
        tier="personal",
        route_selected="local_sovereign_core",
        candidates_rejected=["semantic_llm_layer"],
        reason_code="SOVEREIGN_DEFAULT",
        wisdom_alignment=["W-GOLD-01"],
        latency_ms=12
    )
    print(f"[TEST] Recorded decision: {dr_id}")

    # Wait for async write
    import time
    time.sleep(0.5)

    # Get stats
    stats = get_decision_stats()
    print(f"[TEST] Total decisions: {stats.get('total_decisions', 0)}")
    print(f"[TEST] Local ratio: {stats.get('local_intelligence_ratio', 0)}%")

    # Get autonomy intelligence
    autonomy = get_autonomy_intelligence()
    print(f"[TEST] Autonomy: {autonomy.get('message', 'N/A')}")

    print("=" * 50)
    print("Decision Journal ready for Gate 4 integration")
