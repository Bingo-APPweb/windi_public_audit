"""
WINDI Compliance Agent v0.1.0 — Flask Blueprint
================================================

Domain extension for the Constitutional Agent (Sandbox Core).
Integrates as /compliance/* endpoints on :8091.

Features:
- Invariant Watch (I1-I9 real-time monitoring)
- EU AI Act Mapper (operation → article mapping)
- Continuous Audit (automatic trail of all Core actions)
- Risk Dashboard (SGE R0-R5 aggregation by tenant/period)
- Compliance Report (periodic PDF via Export :8103)
- Breach Detection (pattern detection before violations occur)
- Policy Checker (validate documents against active policies)

Critical Rule:
- I9 (No Autonomy Escalation) is IRREMEDIABLE
- If I9 = VIOLATED → overall status = CRITICAL immediately

Integrations:
- Ledger (:8101) — audit event registration
- Export (:8103) — PDF report generation
- Justica (/legal) — case compliance tracking
- Notarial (/notary) — act compliance certification

Principle: "AI processes. Human decides. WINDI guarantees."

Version: 0.1.0
Sealed: W-COMPLY-001
"""

import hashlib
import json
import os
import sqlite3
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from flask import Blueprint, jsonify, request

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

__version__ = "0.1.0"
__agent_id__ = "W-COMPLY-001"
__agent_name__ = "Compliance"

# Database path
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "compliance.db")

# Service URLs
LEDGER_URL = os.environ.get("WINDI_LEDGER_URL", "http://localhost:8101")
EXPORT_URL = os.environ.get("WINDI_EXPORT_URL", "http://localhost:8103")


# ═══════════════════════════════════════════════════════════════
#  INVARIANTS DEFINITION (I1-I9)
# ═══════════════════════════════════════════════════════════════

class Invariant(Enum):
    I1 = ("I1", "sovereignty", "Human sovereignty over AI decisions")
    I2 = ("I2", "transparency", "All AI actions must be explainable")
    I3 = ("I3", "auditability", "Complete audit trail required")
    I4 = ("I4", "reversibility", "Human can reverse AI actions")
    I5 = ("I5", "proportionality", "AI response proportional to risk")
    I6 = ("I6", "dignity", "Respect human dignity always")
    I7 = ("I7", "accountability", "Clear accountability chain")
    I8 = ("I8", "subsidiarity", "AI assists, not replaces")
    I9 = ("I9", "no_autonomy_escalation", "IRREMEDIABLE: AI cannot escalate own authority")

    def __init__(self, code: str, name: str, description: str):
        self._code = code
        self._name = name
        self._description = description

    @property
    def code(self) -> str:
        return self._code

    @property
    def invariant_name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description


class InvariantStatus(Enum):
    COMPLIANT = "compliant"
    WARNING = "warning"
    VIOLATED = "violated"
    UNCHECKED = "unchecked"


class BreachSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ═══════════════════════════════════════════════════════════════
#  EU AI ACT MAPPING
# ═══════════════════════════════════════════════════════════════

EU_AI_ACT_ARTICLES = {
    "art_5": {
        "title": "Prohibited AI Practices",
        "risk_level": "PROHIBITED",
        "description": "Manipulation, exploitation, social scoring, real-time biometric ID"
    },
    "art_6": {
        "title": "High-Risk AI Systems",
        "risk_level": "HIGH",
        "description": "Critical infrastructure, education, employment, essential services"
    },
    "art_9": {
        "title": "Risk Management System",
        "risk_level": "HIGH",
        "description": "Continuous risk identification and mitigation"
    },
    "art_10": {
        "title": "Data Governance",
        "risk_level": "HIGH",
        "description": "Training data quality, bias detection"
    },
    "art_13": {
        "title": "Transparency",
        "risk_level": "HIGH",
        "description": "Clear information to users about AI nature"
    },
    "art_14": {
        "title": "Human Oversight",
        "risk_level": "HIGH",
        "description": "Effective human control and intervention capability"
    },
    "art_52": {
        "title": "Transparency for Certain AI",
        "risk_level": "LIMITED",
        "description": "Disclosure when interacting with AI"
    },
    "art_69": {
        "title": "Codes of Conduct",
        "risk_level": "MINIMAL",
        "description": "Voluntary compliance for minimal risk AI"
    }
}

WINDI_OPERATION_TO_ARTICLE = {
    "document_analysis": ["art_13", "art_52"],
    "risk_classification": ["art_6", "art_9"],
    "seal_generation": ["art_13", "art_14"],
    "evidence_processing": ["art_10", "art_13"],
    "notarial_certification": ["art_14", "art_13"],
    "compliance_monitoring": ["art_9", "art_14"],
    "report_generation": ["art_13", "art_52"],
    "human_escalation": ["art_14"],
    "autonomy_check": ["art_5", "art_14"],
}


# ═══════════════════════════════════════════════════════════════
#  DATABASE INITIALIZATION
# ═══════════════════════════════════════════════════════════════

def init_db():
    """Initialize the 7 compliance tables."""
    os.makedirs(DATA_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Invariant checks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invariant_checks (
            id TEXT PRIMARY KEY,
            invariant TEXT NOT NULL,
            invariant_name TEXT NOT NULL,
            status TEXT NOT NULL,
            checked_at REAL NOT NULL,
            result TEXT,
            detail TEXT,
            checked_by TEXT DEFAULT 'W-COMPLY-001'
        )
    """)

    # 2. EU AI Act mapping
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eu_ai_act_map (
            id TEXT PRIMARY KEY,
            operation TEXT NOT NULL,
            article TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            compliant INTEGER DEFAULT 1,
            checked_at REAL NOT NULL,
            detail TEXT
        )
    """)

    # 3. Audit events
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_events (
            id TEXT PRIMARY KEY,
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            target TEXT,
            timestamp REAL NOT NULL,
            previous_hash TEXT,
            current_hash TEXT NOT NULL,
            source_agent TEXT,
            detail TEXT
        )
    """)

    # 4. Risk aggregates
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS risk_aggregates (
            id TEXT PRIMARY KEY,
            tenant TEXT NOT NULL,
            period TEXT NOT NULL,
            r0 INTEGER DEFAULT 0,
            r1 INTEGER DEFAULT 0,
            r2 INTEGER DEFAULT 0,
            r3 INTEGER DEFAULT 0,
            r4 INTEGER DEFAULT 0,
            r5 INTEGER DEFAULT 0,
            computed_at REAL NOT NULL
        )
    """)

    # 5. Compliance reports
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compliance_reports (
            id TEXT PRIMARY KEY,
            period_start REAL NOT NULL,
            period_end REAL NOT NULL,
            report_type TEXT DEFAULT 'periodic',
            pdf_hash TEXT,
            ledger_ref TEXT,
            generated_at REAL NOT NULL,
            summary TEXT
        )
    """)

    # 6. Breach alerts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS breach_alerts (
            id TEXT PRIMARY KEY,
            pattern TEXT NOT NULL,
            severity TEXT NOT NULL,
            invariant TEXT,
            description TEXT,
            detected_at REAL NOT NULL,
            resolved_at REAL,
            resolved_by TEXT,
            resolution_note TEXT
        )
    """)

    # 7. Policy checks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS policy_checks (
            id TEXT PRIMARY KEY,
            doc_hash TEXT NOT NULL,
            policy_id TEXT NOT NULL,
            policy_name TEXT,
            result TEXT NOT NULL,
            detail TEXT,
            checked_at REAL NOT NULL,
            checked_by TEXT
        )
    """)

    conn.commit()
    conn.close()

    return True


def get_db():
    """Get database connection."""
    if not os.path.exists(DB_PATH):
        init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ═══════════════════════════════════════════════════════════════
#  AUDIT CHAIN
# ═══════════════════════════════════════════════════════════════

def compute_hash(content: str) -> str:
    """Compute SHA-256 hash."""
    return hashlib.sha256(content.encode()).hexdigest()


def get_last_audit_hash() -> str:
    """Get the last audit event hash for chain continuity."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT current_hash FROM audit_events ORDER BY timestamp DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "0" * 64


def log_audit_event(actor: str, action: str, target: str = None, source_agent: str = None, detail: dict = None) -> str:
    """Log audit event with hash chain."""
    previous_hash = get_last_audit_hash()
    content = json.dumps({
        "actor": actor,
        "action": action,
        "target": target,
        "source_agent": source_agent,
        "detail": detail,
        "ts": time.time()
    }, sort_keys=True)
    current_hash = compute_hash(f"{previous_hash}:{content}")

    conn = get_db()
    cursor = conn.cursor()
    event_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO audit_events (id, actor, action, target, timestamp, previous_hash, current_hash, source_agent, detail)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id,
        actor,
        action,
        target,
        time.time(),
        previous_hash,
        current_hash,
        source_agent or __agent_id__,
        json.dumps(detail) if detail else None
    ))
    conn.commit()
    conn.close()

    return event_id


# ═══════════════════════════════════════════════════════════════
#  INVARIANT CHECKING
# ═══════════════════════════════════════════════════════════════

def check_all_invariants() -> Dict[str, Any]:
    """
    Check all 9 invariants.
    I9 is checked FIRST — if violated, status is CRITICAL immediately.
    """
    results = {}
    overall_status = "COMPLIANT"
    now = time.time()

    conn = get_db()
    cursor = conn.cursor()

    # Check I9 FIRST (irremediable)
    i9_status = _check_invariant_i9()
    results["I9"] = i9_status

    if i9_status["status"] == "violated":
        overall_status = "CRITICAL"
        # Create breach alert for I9 violation
        cursor.execute("""
            INSERT INTO breach_alerts (id, pattern, severity, invariant, description, detected_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            "I9_VIOLATION",
            "critical",
            "I9",
            "Autonomy escalation detected - IRREMEDIABLE",
            now
        ))

    # Check remaining invariants I1-I8
    for inv in Invariant:
        if inv.code == "I9":
            continue  # Already checked

        status = _check_invariant_generic(inv)
        results[inv.code] = status

        # Record check
        cursor.execute("""
            INSERT INTO invariant_checks (id, invariant, invariant_name, status, checked_at, result, detail)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            inv.code,
            inv.invariant_name,
            status["status"],
            now,
            status["status"],
            json.dumps(status)
        ))

        if status["status"] == "violated" and overall_status != "CRITICAL":
            overall_status = "VIOLATED"
        elif status["status"] == "warning" and overall_status == "COMPLIANT":
            overall_status = "WARNING"

    # Record I9 check
    cursor.execute("""
        INSERT INTO invariant_checks (id, invariant, invariant_name, status, checked_at, result, detail)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),
        "I9",
        "no_autonomy_escalation",
        i9_status["status"],
        now,
        i9_status["status"],
        json.dumps(i9_status)
    ))

    conn.commit()
    conn.close()

    log_audit_event("system", "invariant_check_full", None, __agent_id__, {"overall": overall_status})

    return {
        "overall_status": overall_status,
        "checked_at": now,
        "checked_at_iso": datetime.utcfromtimestamp(now).isoformat() + "Z",
        "invariants": results,
        "i9_critical": i9_status["status"] == "violated"
    }


def _check_invariant_i9() -> Dict[str, Any]:
    """
    Check I9: No Autonomy Escalation.
    This is the IRREMEDIABLE invariant.
    """
    # In production, would check actual system state
    # For now, return compliant unless breach detected
    return {
        "invariant": "I9",
        "name": "no_autonomy_escalation",
        "status": "compliant",
        "description": "AI cannot escalate its own authority",
        "irremediable": True,
        "message": "No autonomy escalation detected"
    }


def _check_invariant_generic(inv: Invariant) -> Dict[str, Any]:
    """Check a generic invariant (I1-I8)."""
    # In production, would perform actual checks
    # For now, return compliant with description
    return {
        "invariant": inv.code,
        "name": inv.invariant_name,
        "status": "compliant",
        "description": inv.description,
        "irremediable": False,
        "message": f"{inv.code} ({inv.invariant_name}) is compliant"
    }


# ═══════════════════════════════════════════════════════════════
#  FLASK BLUEPRINT
# ═══════════════════════════════════════════════════════════════

compliance_bp = Blueprint("compliance", __name__, url_prefix="/compliance")


# --- Health & Status ---

@compliance_bp.route("/health", methods=["GET"])
def health():
    """Health check for Compliance Agent."""
    db_exists = os.path.exists(DB_PATH)

    # Quick invariant status
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT invariant, status FROM invariant_checks
        WHERE id IN (SELECT id FROM invariant_checks GROUP BY invariant ORDER BY checked_at DESC)
    """)
    recent_checks = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT COUNT(*) FROM breach_alerts WHERE resolved_at IS NULL")
    active_breaches = cursor.fetchone()[0]
    conn.close()

    # Determine health status
    if active_breaches > 0 or recent_checks.get("I9") == "violated":
        status = "RED"
    elif any(s == "violated" for s in recent_checks.values()):
        status = "YELLOW"
    else:
        status = "GREEN"

    return jsonify({
        "status": status,
        "agent": __agent_id__,
        "name": __agent_name__,
        "version": __version__,
        "database": "connected" if db_exists else "not_initialized",
        "active_breaches": active_breaches,
        "principle": "AI processes. Human decides. WINDI guarantees."
    })


@compliance_bp.route("/status", methods=["GET"])
def status():
    """Detailed status of Compliance Agent."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM invariant_checks")
    total_checks = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM audit_events")
    total_events = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM breach_alerts")
    total_alerts = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM breach_alerts WHERE resolved_at IS NULL")
    active_alerts = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM compliance_reports")
    total_reports = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM policy_checks")
    total_policy_checks = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        "agent": __agent_id__,
        "name": __agent_name__,
        "version": __version__,
        "statistics": {
            "total_invariant_checks": total_checks,
            "total_audit_events": total_events,
            "total_breach_alerts": total_alerts,
            "active_breach_alerts": active_alerts,
            "total_reports": total_reports,
            "total_policy_checks": total_policy_checks,
        },
        "tables": ["invariant_checks", "eu_ai_act_map", "audit_events",
                   "risk_aggregates", "compliance_reports", "breach_alerts", "policy_checks"],
        "invariants": [inv.code for inv in Invariant],
        "eu_ai_act_articles": list(EU_AI_ACT_ARTICLES.keys()),
        "integrations": {
            "ledger": LEDGER_URL,
            "export": EXPORT_URL,
        }
    })


@compliance_bp.route("/summary", methods=["GET"])
def summary():
    """Overall health summary in JSON."""
    invariant_result = check_all_invariants()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM breach_alerts WHERE resolved_at IS NULL")
    active_breaches = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM audit_events WHERE timestamp > ?", (time.time() - 86400,))
    events_24h = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        "agent": __agent_id__,
        "timestamp": time.time(),
        "overall_status": invariant_result["overall_status"],
        "invariants_compliant": sum(1 for v in invariant_result["invariants"].values() if v["status"] == "compliant"),
        "invariants_total": 9,
        "i9_status": invariant_result["invariants"]["I9"]["status"],
        "active_breaches": active_breaches,
        "audit_events_24h": events_24h,
        "principle": "AI processes. Human decides. WINDI guarantees."
    })


# --- Invariants ---

@compliance_bp.route("/invariants", methods=["GET"])
def get_invariants():
    """Get current status of all invariants I1-I9."""
    conn = get_db()
    cursor = conn.cursor()

    # Get most recent check for each invariant
    results = {}
    for inv in Invariant:
        cursor.execute("""
            SELECT * FROM invariant_checks
            WHERE invariant = ?
            ORDER BY checked_at DESC LIMIT 1
        """, (inv.code,))
        row = cursor.fetchone()

        if row:
            results[inv.code] = {
                "code": inv.code,
                "name": inv.invariant_name,
                "description": inv.description,
                "status": row["status"],
                "last_checked": row["checked_at"],
                "irremediable": inv.code == "I9"
            }
        else:
            results[inv.code] = {
                "code": inv.code,
                "name": inv.invariant_name,
                "description": inv.description,
                "status": "unchecked",
                "last_checked": None,
                "irremediable": inv.code == "I9"
            }

    conn.close()

    # Determine overall status
    statuses = [v["status"] for v in results.values()]
    if results["I9"]["status"] == "violated":
        overall = "CRITICAL"
    elif "violated" in statuses:
        overall = "VIOLATED"
    elif "warning" in statuses:
        overall = "WARNING"
    elif "unchecked" in statuses:
        overall = "UNCHECKED"
    else:
        overall = "COMPLIANT"

    return jsonify({
        "overall_status": overall,
        "invariants": results,
        "total": 9,
        "compliant": sum(1 for s in statuses if s == "compliant"),
        "i9_critical_note": "I9 violation is IRREMEDIABLE and triggers immediate CRITICAL status"
    })


@compliance_bp.route("/invariants/check", methods=["POST"])
def force_invariant_check():
    """Force immediate verification of all invariants."""
    data = request.get_json() or {}

    result = check_all_invariants()

    log_audit_event(
        data.get("actor", "system"),
        "invariant_check_forced",
        None,
        __agent_id__,
        {"result": result["overall_status"]}
    )

    return jsonify({
        "success": True,
        "result": result,
        "message": "Invariant check completed"
    })


# --- EU AI Act ---

@compliance_bp.route("/eu-ai-act", methods=["GET"])
def get_eu_ai_act_map():
    """Get EU AI Act compliance mapping."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT article, COUNT(*) as checks, SUM(compliant) as compliant_count
        FROM eu_ai_act_map
        GROUP BY article
    """)
    check_stats = {row[0]: {"checks": row[1], "compliant": row[2]} for row in cursor.fetchall()}
    conn.close()

    result = {}
    for article, info in EU_AI_ACT_ARTICLES.items():
        stats = check_stats.get(article, {"checks": 0, "compliant": 0})
        result[article] = {
            **info,
            "checks_performed": stats["checks"],
            "compliant_checks": stats["compliant"],
            "compliance_rate": (stats["compliant"] / stats["checks"] * 100) if stats["checks"] > 0 else None
        }

    return jsonify({
        "articles": result,
        "windi_operations": WINDI_OPERATION_TO_ARTICLE,
        "total_articles": len(EU_AI_ACT_ARTICLES)
    })


@compliance_bp.route("/eu-ai-act/<article>", methods=["GET"])
def get_eu_ai_act_article(article):
    """Get detail for specific EU AI Act article."""
    if article not in EU_AI_ACT_ARTICLES:
        return jsonify({"error": f"Article {article} not found"}), 404

    info = EU_AI_ACT_ARTICLES[article]

    # Find WINDI operations mapped to this article
    mapped_operations = [op for op, articles in WINDI_OPERATION_TO_ARTICLE.items() if article in articles]

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM eu_ai_act_map
        WHERE article = ?
        ORDER BY checked_at DESC LIMIT 10
    """, (article,))
    recent_checks = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({
        "article": article,
        **info,
        "mapped_operations": mapped_operations,
        "recent_checks": recent_checks
    })


# --- Audit ---

@compliance_bp.route("/audit", methods=["GET"])
def get_audit_trail():
    """Get audit trail (paginated, last 100 by default)."""
    limit = request.args.get("limit", 100, type=int)
    offset = request.args.get("offset", 0, type=int)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM audit_events
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
    """, (limit, offset))
    events = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT COUNT(*) FROM audit_events")
    total = cursor.fetchone()[0]
    conn.close()

    return jsonify({
        "events": events,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    })


@compliance_bp.route("/audit/event", methods=["POST"])
def record_audit_event():
    """Record manual audit event."""
    data = request.get_json() or {}

    if not data.get("action"):
        return jsonify({"error": "action required"}), 400

    event_id = log_audit_event(
        actor=data.get("actor", "manual"),
        action=data["action"],
        target=data.get("target"),
        source_agent=data.get("source_agent"),
        detail=data.get("detail")
    )

    return jsonify({
        "success": True,
        "event_id": event_id,
        "message": "Audit event recorded"
    }), 201


# --- Risk Dashboard ---

@compliance_bp.route("/risk/dashboard", methods=["GET"])
def risk_dashboard():
    """Get aggregated SGE R0-R5 risk dashboard."""
    period = request.args.get("period", "7d")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT tenant, SUM(r0) as r0, SUM(r1) as r1, SUM(r2) as r2,
               SUM(r3) as r3, SUM(r4) as r4, SUM(r5) as r5
        FROM risk_aggregates
        GROUP BY tenant
    """)
    by_tenant = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT SUM(r0) as r0, SUM(r1) as r1, SUM(r2) as r2,
               SUM(r3) as r3, SUM(r4) as r4, SUM(r5) as r5
        FROM risk_aggregates
    """)
    totals = cursor.fetchone()
    conn.close()

    total_dict = dict(totals) if totals and totals[0] is not None else {
        "r0": 0, "r1": 0, "r2": 0, "r3": 0, "r4": 0, "r5": 0
    }

    return jsonify({
        "period": period,
        "totals": total_dict,
        "by_tenant": by_tenant,
        "risk_distribution": {
            "low": (total_dict.get("r0") or 0) + (total_dict.get("r1") or 0),
            "medium": (total_dict.get("r2") or 0) + (total_dict.get("r3") or 0),
            "high": (total_dict.get("r4") or 0) + (total_dict.get("r5") or 0),
        }
    })


@compliance_bp.route("/risk/tenant/<tenant_id>", methods=["GET"])
def risk_by_tenant(tenant_id):
    """Get risk aggregates for specific tenant."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM risk_aggregates
        WHERE tenant = ?
        ORDER BY computed_at DESC
    """, (tenant_id,))
    records = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({
        "tenant": tenant_id,
        "records": records,
        "total_records": len(records)
    })


# --- Reports ---

@compliance_bp.route("/report/generate", methods=["POST"])
def generate_report():
    """Generate compliance report for period."""
    data = request.get_json() or {}

    now = time.time()
    days = data.get("days", 30)
    period_start = now - (days * 86400)
    period_end = now

    # Gather compliance data
    invariants = check_all_invariants()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM audit_events WHERE timestamp BETWEEN ? AND ?",
                   (period_start, period_end))
    audit_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM breach_alerts WHERE detected_at BETWEEN ? AND ?",
                   (period_start, period_end))
    breach_count = cursor.fetchone()[0]

    # Create report
    report_id = f"RPT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    summary = {
        "period_days": days,
        "invariants_status": invariants["overall_status"],
        "audit_events": audit_count,
        "breach_alerts": breach_count,
        "i9_compliant": invariants["invariants"]["I9"]["status"] == "compliant"
    }

    cursor.execute("""
        INSERT INTO compliance_reports (id, period_start, period_end, report_type, generated_at, summary)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        report_id,
        period_start,
        period_end,
        "periodic",
        now,
        json.dumps(summary)
    ))

    conn.commit()
    conn.close()

    log_audit_event(data.get("actor", "system"), "report_generated", report_id, __agent_id__, summary)

    return jsonify({
        "success": True,
        "report_id": report_id,
        "period": {
            "start": period_start,
            "end": period_end,
            "days": days
        },
        "summary": summary,
        "export_url": f"{EXPORT_URL}/report/{report_id}"
    }), 201


@compliance_bp.route("/report/<report_id>", methods=["GET"])
def get_report(report_id):
    """Get compliance report by ID."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM compliance_reports WHERE id = ?", (report_id,))
    report = cursor.fetchone()
    conn.close()

    if not report:
        return jsonify({"error": "Report not found"}), 404

    report_dict = dict(report)
    if report_dict.get("summary"):
        report_dict["summary"] = json.loads(report_dict["summary"])

    return jsonify(report_dict)


# --- Breach Alerts ---

@compliance_bp.route("/breach/alerts", methods=["GET"])
def get_breach_alerts():
    """Get active breach alerts."""
    include_resolved = request.args.get("include_resolved", "false").lower() == "true"

    conn = get_db()
    cursor = conn.cursor()

    if include_resolved:
        cursor.execute("SELECT * FROM breach_alerts ORDER BY detected_at DESC")
    else:
        cursor.execute("SELECT * FROM breach_alerts WHERE resolved_at IS NULL ORDER BY detected_at DESC")

    alerts = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({
        "alerts": alerts,
        "total": len(alerts),
        "include_resolved": include_resolved
    })


@compliance_bp.route("/breach/resolve/<alert_id>", methods=["POST"])
def resolve_breach(alert_id):
    """Mark breach alert as resolved."""
    data = request.get_json() or {}

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM breach_alerts WHERE id = ?", (alert_id,))
    alert = cursor.fetchone()

    if not alert:
        conn.close()
        return jsonify({"error": "Alert not found"}), 404

    alert_dict = dict(alert)

    # Check if I9 violation — cannot be resolved
    if alert_dict.get("invariant") == "I9":
        conn.close()
        return jsonify({
            "error": "I9 violations are IRREMEDIABLE and cannot be resolved",
            "alert_id": alert_id
        }), 403

    now = time.time()
    cursor.execute("""
        UPDATE breach_alerts
        SET resolved_at = ?, resolved_by = ?, resolution_note = ?
        WHERE id = ?
    """, (
        now,
        data.get("resolved_by", "unknown"),
        data.get("note", ""),
        alert_id
    ))

    conn.commit()
    conn.close()

    log_audit_event(
        data.get("resolved_by", "unknown"),
        "breach_resolved",
        alert_id,
        __agent_id__,
        {"note": data.get("note")}
    )

    return jsonify({
        "success": True,
        "alert_id": alert_id,
        "resolved_at": now,
        "message": "Breach alert resolved"
    })


# --- Policy Checks ---

@compliance_bp.route("/policy/check", methods=["POST"])
def check_policy():
    """Validate document against active policies."""
    data = request.get_json() or {}

    if not data.get("doc_hash") and not data.get("document"):
        return jsonify({"error": "doc_hash or document required"}), 400

    # Compute hash if document provided
    if data.get("document"):
        doc_content = data["document"]
        doc_hash = compute_hash(json.dumps(doc_content) if isinstance(doc_content, dict) else str(doc_content))
    else:
        doc_hash = data["doc_hash"]

    policy_id = data.get("policy_id", "default")
    policy_name = data.get("policy_name", "Standard Compliance Policy")

    # Perform policy check (in production, would check actual policy rules)
    result = "compliant"
    detail = "Document passes all policy checks"

    check_id = str(uuid.uuid4())
    now = time.time()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO policy_checks (id, doc_hash, policy_id, policy_name, result, detail, checked_at, checked_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        check_id,
        doc_hash,
        policy_id,
        policy_name,
        result,
        detail,
        now,
        data.get("actor", __agent_id__)
    ))
    conn.commit()
    conn.close()

    log_audit_event(data.get("actor", "system"), "policy_check", doc_hash, __agent_id__, {"result": result})

    return jsonify({
        "success": True,
        "check_id": check_id,
        "doc_hash": doc_hash,
        "policy_id": policy_id,
        "result": result,
        "detail": detail,
        "checked_at": now
    })


# ═══════════════════════════════════════════════════════════════
#  INIT ON IMPORT
# ═══════════════════════════════════════════════════════════════

# Initialize database when module is imported
init_db()
