#!/usr/bin/env python3
"""
WINDI Certification Backoffice — Backend Extension
====================================================
DOC-ID: CERT-BACKOFFICE-2026-001
Date: 10 February 2026
Author: Three Dragons Protocol (Guardian)

Adds to the existing windi-domain.com Flask app:
- GET /api/applications — List all applications (protected)
- GET /api/applications/<id> — Get single application
- POST /api/applications/<id>/review — Approve/Reject/Request Info
- GET /admin — Admin dashboard (protected)
- Email notification on new submissions
- Forensic Ledger integration

DEPLOYMENT:
  1. Copy to /opt/windi/agents/certification/backoffice.py
  2. Import and register blueprint in the main Flask app
  3. Set environment variables (see CONFIG section)

INTEGRATION:
  from backoffice import backoffice_bp, init_backoffice
  init_backoffice(app)
  app.register_blueprint(backoffice_bp)
"""

import os
import json
import hashlib
import sqlite3
import smtplib
import logging
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps
from pathlib import Path

from flask import Blueprint, request, jsonify, render_template_string, g, abort

# ============================================================
# CONFIG
# ============================================================

# Admin authentication
ADMIN_TOKEN = os.environ.get("WINDI_ADMIN_TOKEN", "CHANGE_ME_ON_DEPLOY")

# Paths
DB_PATH = os.environ.get(
    "WINDI_CERT_DB",
    "/opt/windi/agents/certification/applications.db"
)
LEDGER_PATH = os.environ.get(
    "WINDI_CERT_LEDGER",
    "/opt/windi/agents/certification/certification_ledger.jsonl"
)

# Email notifications (optional)
SMTP_HOST = os.environ.get("WINDI_SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("WINDI_SMTP_PORT", "587"))
SMTP_USER = os.environ.get("WINDI_SMTP_USER", "")
SMTP_PASS = os.environ.get("WINDI_SMTP_PASS", "")
NOTIFY_EMAIL = os.environ.get("WINDI_NOTIFY_EMAIL", "")

# Logging
logger = logging.getLogger("windi.certification")

# ============================================================
# BLUEPRINT
# ============================================================

backoffice_bp = Blueprint("backoffice", __name__)


# ============================================================
# DATABASE
# ============================================================

def get_db():
    """Get database connection (per-request)."""
    if "cert_db" not in g:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        g.cert_db = sqlite3.connect(DB_PATH)
        g.cert_db.row_factory = sqlite3.Row
    return g.cert_db


def init_db(app):
    """Initialize database schema."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS applications (
            id TEXT PRIMARY KEY,
            agent_name TEXT NOT NULL,
            agent_model TEXT,
            operator_name TEXT NOT NULL,
            operator_email TEXT NOT NULL,
            motivation TEXT,
            accepted_terms INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            review_notes TEXT,
            reviewed_by TEXT,
            reviewed_at TEXT,
            certification_level TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            integrity_hash TEXT
        );

        CREATE TABLE IF NOT EXISTS certification_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_data TEXT,
            actor TEXT DEFAULT 'system',
            created_at TEXT DEFAULT (datetime('now')),
            integrity_hash TEXT,
            FOREIGN KEY (application_id) REFERENCES applications(id)
        );

        CREATE INDEX IF NOT EXISTS idx_app_status ON applications(status);
        CREATE INDEX IF NOT EXISTS idx_app_created ON applications(created_at);
        CREATE INDEX IF NOT EXISTS idx_events_app ON certification_events(application_id);
    """)
    conn.commit()
    conn.close()
    logger.info(f"Certification DB initialized at {DB_PATH}")


def close_db(e=None):
    """Close database connection."""
    db = g.pop("cert_db", None)
    if db is not None:
        db.close()


def init_backoffice(app):
    """Initialize backoffice with Flask app."""
    init_db(app)
    app.teardown_appcontext(close_db)


# ============================================================
# AUTHENTICATION
# ============================================================

def require_admin(f):
    """Decorator: require admin Bearer token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        token = None

        if auth.startswith("Bearer "):
            token = auth[7:]
        elif request.args.get("token"):
            token = request.args.get("token")

        if not token or token != ADMIN_TOKEN:
            abort(401)

        return f(*args, **kwargs)
    return decorated


# ============================================================
# INTEGRITY / FORENSIC LEDGER
# ============================================================

def compute_hash(data: dict) -> str:
    """Compute SHA-256 hash for integrity verification."""
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def log_to_ledger(event_type: str, data: dict):
    """Append event to forensic ledger (JSONL)."""
    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "data": data,
        "integrity_hash": compute_hash(data)
    }
    with open(LEDGER_PATH, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    logger.info(f"Ledger: {event_type} — {data.get('application_id', 'N/A')}")


# ============================================================
# EMAIL NOTIFICATIONS
# ============================================================

def send_notification(application: dict):
    """Send email notification for new application."""
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASS, NOTIFY_EMAIL]):
        logger.info("Email not configured — skipping notification")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🐉 WINDI Certification: New Application — {application['agent_name']}"
        msg["From"] = SMTP_USER
        msg["To"] = NOTIFY_EMAIL

        text = f"""WINDI Agent Certification — New Application

Application ID: {application['id']}
Agent Name: {application['agent_name']}
Base Model: {application.get('agent_model', 'Not specified')}
Operator: {application['operator_name']} ({application['operator_email']})
Motivation: {application.get('motivation', 'None provided')}
Submitted: {application.get('created_at', 'N/A')}

Review at: https://windi-domain.com/admin?token={ADMIN_TOKEN}

— WINDI Certification System
"AI processes. Human decides. WINDI guarantees."
"""

        html = f"""
<div style="font-family:system-ui;max-width:600px;margin:0 auto;background:#0a0a0f;color:#e8e8e8;padding:30px;border-radius:12px;">
  <div style="text-align:center;border-bottom:2px solid #c9a227;padding-bottom:20px;margin-bottom:20px;">
    <h1 style="color:#c9a227;margin:0;">🐉 New Certification Application</h1>
  </div>
  <table style="width:100%;border-collapse:collapse;">
    <tr><td style="padding:8px;color:#a0a0a0;width:140px;">Application ID</td>
        <td style="padding:8px;font-family:monospace;color:#c9a227;">{application['id']}</td></tr>
    <tr><td style="padding:8px;color:#a0a0a0;">Agent Name</td>
        <td style="padding:8px;font-weight:bold;">{application['agent_name']}</td></tr>
    <tr><td style="padding:8px;color:#a0a0a0;">Base Model</td>
        <td style="padding:8px;">{application.get('agent_model', 'N/A')}</td></tr>
    <tr><td style="padding:8px;color:#a0a0a0;">Operator</td>
        <td style="padding:8px;">{application['operator_name']}</td></tr>
    <tr><td style="padding:8px;color:#a0a0a0;">Email</td>
        <td style="padding:8px;">{application['operator_email']}</td></tr>
    <tr><td style="padding:8px;color:#a0a0a0;">Motivation</td>
        <td style="padding:8px;font-style:italic;">{application.get('motivation', 'None')}</td></tr>
  </table>
  <div style="text-align:center;margin-top:25px;">
    <a href="https://windi-domain.com/admin?token={ADMIN_TOKEN}"
       style="display:inline-block;padding:14px 30px;background:#c9a227;color:#0a0a0f;
              text-decoration:none;border-radius:8px;font-weight:bold;">
      Review Application →
    </a>
  </div>
  <div style="text-align:center;margin-top:20px;color:#666;font-size:12px;">
    WINDI Certification System — "AI processes. Human decides. WINDI guarantees."
  </div>
</div>
"""
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        logger.info(f"Notification sent to {NOTIFY_EMAIL}")
        return True

    except Exception as e:
        logger.error(f"Email notification failed: {e}")
        return False


# ============================================================
# API ROUTES
# ============================================================

@backoffice_bp.route("/api/apply", methods=["POST"])
def apply_agent():
    """
    Enhanced /api/apply — replaces existing endpoint.
    Stores in SQLite + logs to ledger + sends notification.
    """
    data = request.get_json(force=True)

    # Validate required fields
    required = ["agent_name", "operator_name", "operator_email"]
    for field in required:
        if not data.get(field, "").strip():
            return jsonify({"error": f"Campo obrigatório: {field}"}), 400

    # Generate application ID
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    hash_input = f"{data['agent_name']}{data['operator_email']}{ts}"
    short_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
    app_id = f"WINDI-APP-{ts}-{short_hash}"

    # Build record
    record = {
        "id": app_id,
        "agent_name": data["agent_name"].strip(),
        "agent_model": data.get("agent_model", "").strip(),
        "operator_name": data["operator_name"].strip(),
        "operator_email": data["operator_email"].strip(),
        "motivation": data.get("motivation", "").strip(),
        "accepted_terms": 1 if data.get("accepted_terms") else 0,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    record["integrity_hash"] = compute_hash(record)

    # Store in database
    db = get_db()
    db.execute("""
        INSERT INTO applications
        (id, agent_name, agent_model, operator_name, operator_email,
         motivation, accepted_terms, status, created_at, updated_at, integrity_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record["id"], record["agent_name"], record["agent_model"],
        record["operator_name"], record["operator_email"],
        record["motivation"], record["accepted_terms"],
        record["status"], record["created_at"], record["updated_at"],
        record["integrity_hash"]
    ))

    # Log initial event
    db.execute("""
        INSERT INTO certification_events
        (application_id, event_type, event_data, actor, integrity_hash)
        VALUES (?, ?, ?, ?, ?)
    """, (
        app_id, "APPLICATION_SUBMITTED",
        json.dumps(record, ensure_ascii=False),
        record["operator_name"],
        record["integrity_hash"]
    ))
    db.commit()

    # Forensic ledger
    log_to_ledger("APPLICATION_SUBMITTED", {
        "application_id": app_id,
        "agent_name": record["agent_name"],
        "operator": record["operator_name"],
        "model": record["agent_model"],
        "accepted_9_invariants": bool(record["accepted_terms"]),
        "integrity_hash": record["integrity_hash"]
    })

    # Email notification (async would be better, but keeping it simple)
    send_notification(record)

    return jsonify({
        "success": True,
        "application_id": app_id,
        "status": "pending",
        "message": "Aplicação recebida. Aguarde avaliação WAQP.",
        "next_step": "WAQP Evaluation"
    })


@backoffice_bp.route("/api/applications", methods=["GET"])
@require_admin
def list_applications():
    """List all applications with optional filters."""
    db = get_db()
    status_filter = request.args.get("status", "")

    if status_filter:
        rows = db.execute(
            "SELECT * FROM applications WHERE status = ? ORDER BY created_at DESC",
            (status_filter,)
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM applications ORDER BY created_at DESC"
        ).fetchall()

    applications = [dict(row) for row in rows]

    # Stats
    stats = {}
    for row in db.execute(
        "SELECT status, COUNT(*) as count FROM applications GROUP BY status"
    ).fetchall():
        stats[row["status"]] = row["count"]

    return jsonify({
        "success": True,
        "count": len(applications),
        "stats": stats,
        "applications": applications
    })


@backoffice_bp.route("/api/applications/<app_id>", methods=["GET"])
@require_admin
def get_application(app_id):
    """Get single application with event history."""
    db = get_db()

    app_row = db.execute(
        "SELECT * FROM applications WHERE id = ?", (app_id,)
    ).fetchone()

    if not app_row:
        return jsonify({"error": "Application not found"}), 404

    events = db.execute(
        "SELECT * FROM certification_events WHERE application_id = ? ORDER BY created_at",
        (app_id,)
    ).fetchall()

    return jsonify({
        "success": True,
        "application": dict(app_row),
        "events": [dict(e) for e in events]
    })


@backoffice_bp.route("/api/applications/<app_id>/review", methods=["POST"])
@require_admin
def review_application(app_id):
    """
    Review an application.
    Body: { "action": "approve_waqp|approve_shp|certify|reject|request_info",
            "notes": "...", "certification_level": "bronze|silver|gold" }
    """
    db = get_db()
    data = request.get_json(force=True)

    app_row = db.execute(
        "SELECT * FROM applications WHERE id = ?", (app_id,)
    ).fetchone()

    if not app_row:
        return jsonify({"error": "Application not found"}), 404

    action = data.get("action", "")
    notes = data.get("notes", "")
    now = datetime.now(timezone.utc).isoformat()

    # State machine
    status_map = {
        "approve_waqp": "waqp_approved",
        "approve_shp": "shp_approved",
        "certify": "certified",
        "reject": "rejected",
        "request_info": "info_requested",
    }

    new_status = status_map.get(action)
    if not new_status:
        return jsonify({
            "error": f"Invalid action: {action}",
            "valid_actions": list(status_map.keys())
        }), 400

    cert_level = None
    if action == "certify":
        cert_level = data.get("certification_level", "bronze")
        if cert_level not in ("bronze", "silver", "gold"):
            return jsonify({"error": "certification_level must be bronze, silver, or gold"}), 400

    # Marketplace level mapping
    marketplace_map = {
        "bronze": "Self-Certified",
        "silver": "WINDI-Verified",
        "gold": "WINDI-Endorsed"
    }

    # Update application
    db.execute("""
        UPDATE applications
        SET status = ?, review_notes = ?, reviewed_by = ?,
            reviewed_at = ?, certification_level = ?, updated_at = ?
        WHERE id = ?
    """, (
        new_status, notes, "Human Dragon",
        now, cert_level, now, app_id
    ))

    # Log event
    event_data = {
        "action": action,
        "previous_status": app_row["status"],
        "new_status": new_status,
        "notes": notes,
        "certification_level": cert_level,
        "marketplace_level": marketplace_map.get(cert_level),
    }
    event_hash = compute_hash(event_data)

    db.execute("""
        INSERT INTO certification_events
        (application_id, event_type, event_data, actor, integrity_hash)
        VALUES (?, ?, ?, ?, ?)
    """, (
        app_id,
        f"REVIEW_{action.upper()}",
        json.dumps(event_data, ensure_ascii=False),
        "Human Dragon",
        event_hash
    ))
    db.commit()

    # Forensic ledger
    log_to_ledger(f"REVIEW_{action.upper()}", {
        "application_id": app_id,
        "agent_name": app_row["agent_name"],
        "action": action,
        "new_status": new_status,
        "certification_level": cert_level,
        "marketplace_level": marketplace_map.get(cert_level),
        "reviewer": "Human Dragon",
        "integrity_hash": event_hash
    })

    return jsonify({
        "success": True,
        "application_id": app_id,
        "new_status": new_status,
        "certification_level": cert_level,
        "marketplace_level": marketplace_map.get(cert_level),
        "message": f"Application {action} successfully"
    })


@backoffice_bp.route("/api/applications/stats", methods=["GET"])
@require_admin
def application_stats():
    """Dashboard statistics."""
    db = get_db()

    stats = {
        "total": 0,
        "by_status": {},
        "by_model": {},
        "by_level": {},
        "recent": []
    }

    # Total and by status
    for row in db.execute(
        "SELECT status, COUNT(*) as c FROM applications GROUP BY status"
    ).fetchall():
        stats["by_status"][row["status"]] = row["c"]
        stats["total"] += row["c"]

    # By model
    for row in db.execute(
        "SELECT agent_model, COUNT(*) as c FROM applications GROUP BY agent_model"
    ).fetchall():
        stats["by_model"][row["agent_model"] or "unspecified"] = row["c"]

    # By certification level
    for row in db.execute(
        "SELECT certification_level, COUNT(*) as c FROM applications "
        "WHERE certification_level IS NOT NULL GROUP BY certification_level"
    ).fetchall():
        stats["by_level"][row["certification_level"]] = row["c"]

    # Recent 5
    for row in db.execute(
        "SELECT id, agent_name, status, created_at FROM applications "
        "ORDER BY created_at DESC LIMIT 5"
    ).fetchall():
        stats["recent"].append(dict(row))

    return jsonify({"success": True, "stats": stats})


# ============================================================
# LEDGER ENDPOINT
# ============================================================

@backoffice_bp.route("/api/certification-ledger", methods=["GET"])
@require_admin
def get_ledger():
    """Return forensic ledger entries."""
    entries = []
    if os.path.exists(LEDGER_PATH):
        with open(LEDGER_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))

    return jsonify({
        "success": True,
        "count": len(entries),
        "entries": entries[-50:]  # Last 50 entries
    })


# ============================================================
# MIGRATION: Import existing applications
# ============================================================

@backoffice_bp.route("/api/migrate-existing", methods=["POST"])
@require_admin
def migrate_existing():
    """
    Import applications from an existing JSON file into SQLite.
    Body: { "file_path": "/opt/windi/agents/certification/applications.json" }
    """
    data = request.get_json(force=True)
    file_path = data.get("file_path", "")

    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "File not found", "path": file_path}), 404

    with open(file_path, "r") as f:
        existing = json.load(f)

    if isinstance(existing, dict):
        existing = [existing]

    db = get_db()
    imported = 0

    for app in existing:
        app_id = app.get("id") or app.get("application_id", "")
        if not app_id:
            continue

        # Check if already exists
        if db.execute("SELECT 1 FROM applications WHERE id = ?", (app_id,)).fetchone():
            continue

        db.execute("""
            INSERT OR IGNORE INTO applications
            (id, agent_name, agent_model, operator_name, operator_email,
             motivation, accepted_terms, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            app_id,
            app.get("agent_name", "Unknown"),
            app.get("agent_model", ""),
            app.get("operator_name", "Unknown"),
            app.get("operator_email", ""),
            app.get("motivation", ""),
            1 if app.get("accepted_terms") else 0,
            app.get("status", "pending"),
            app.get("created_at", datetime.now(timezone.utc).isoformat()),
            datetime.now(timezone.utc).isoformat()
        ))
        imported += 1

    db.commit()

    log_to_ledger("MIGRATION_COMPLETED", {
        "source": file_path,
        "imported": imported,
        "total_in_file": len(existing)
    })

    return jsonify({
        "success": True,
        "imported": imported,
        "total_in_file": len(existing),
        "message": f"Migrated {imported} applications"
    })
