"""
WINDI WALLET — Standalone Service v1.0.0
=========================================
Serviço Flask independente na porta 8098.
Não depende da Governance API (HTTPServer puro).

Endpoints:
    POST /api/wallet/provision
    GET  /api/wallet/me
    POST /api/wallet/context/<id>/freeze
    GET  /api/wallet/stats
    GET  /api/wallet/health
    POST /api/wallet/clone/register
    GET  /api/wallet/clone/verify/<agent_id>
    GET  /api/wallet/clone/status
    POST /api/wallet/bridge/approve
    GET  /api/wallet/bridge/health
    GET  /health

Port: 8098 (configurável via WALLET_PORT env)

Three Dragons Protocol: AI processes. Human decides. WINDI guarantees.
(c) 2026 WINDI Publishing House — Kempten, Bavaria
"""

import os
import sys
import json
from datetime import datetime, timezone

# Garantir que o diretório do wallet está no path
WALLET_DIR = os.path.dirname(os.path.abspath(__file__))
if WALLET_DIR not in sys.path:
    sys.path.insert(0, WALLET_DIR)

from flask import Flask, request, jsonify
from wallet_provisioning import (
    init_db, provision_wallet, get_wallet_by_email,
    get_wallet_by_id, freeze_context, get_wallet_stats,
    register_clone_wallet, verify_clone_wallet, get_clone_status,
    record_trust_event
)
from wallet_bridge import on_lead_approved

# ─── API Role Gating ────────────────────────────────────────────────────────
# Security layer: filter data based on request role
# Roles: public (default), admin (requires X-WINDI-Admin-Key header)

ADMIN_KEY = os.environ.get("WINDI_ADMIN_KEY", "windi-admin-2026-pioneer")

def get_request_role():
    """Determine request role from headers."""
    admin_key = request.headers.get("X-WINDI-Admin-Key", "")
    if admin_key == ADMIN_KEY:
        return "admin"
    return "public"

def filter_stats_by_role(stats: dict, role: str) -> dict:
    """Filter stats based on role. Public sees minimal data."""
    if role == "admin":
        return stats  # Full access

    # Public role: only safe, non-sensitive data
    return {
        "total_pioneers": stats.get("total_humans", 0),
        "seats_remaining": max(0, 100 - stats.get("total_humans", 0)),
        "ledger_receipts": stats.get("total_ledger_links", 0),
        "status": "operational"
    }

def filter_health_by_role(health: dict, role: str) -> dict:
    """Filter health data based on role."""
    if role == "admin":
        return health  # Full access

    # Public role: minimal health info
    return {
        "status": health.get("status", "healthy"),
        "service": "WINDI WALLET",
        "pioneers": health.get("humans", 0)
    }

# ─── App ─────────────────────────────────────────────────────────────────────

app = Flask(__name__)
# ── Auth Patch (2026-02-16) ──
from wallet_auth_patch import register_auth
register_auth(app)
# ── End Auth Patch ──

# Inicializar DB no startup
init_db()

# ─── WALLET Endpoints ────────────────────────────────────────────────────────

@app.route("/api/wallet/provision", methods=["POST"])
def endpoint_provision():
    data = request.get_json(force=True)
    try:
        result = provision_wallet(data)
        code = 200 if result.get("idempotent") else 201
        return jsonify(result), code
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/wallet/me", methods=["GET"])
def endpoint_me():
    email = request.args.get("email")
    wallet_id = request.args.get("wallet_id")
    if wallet_id:
        result = get_wallet_by_id(wallet_id)
    elif email:
        result = get_wallet_by_email(email)
    else:
        return jsonify({"error": "email or wallet_id required"}), 400
    if not result:
        return jsonify({"error": "wallet not found"}), 404
    return jsonify(result)


@app.route("/api/wallet/check-email", methods=["GET"])
def endpoint_check_email():
    """
    Verifica se email já está registado.
    Usado no frontend para redirecionar para login se já existe.
    """
    email = request.args.get("email", "").strip().lower()
    if not email:
        return jsonify({"error": "email required"}), 400

    result = get_wallet_by_email(email)
    if result:
        return jsonify({
            "exists": True,
            "display_name": result.get("display_name"),
            "wallet_id": result.get("contexts", [{}])[0].get("wallet_id") if result.get("contexts") else None
        })
    else:
        return jsonify({"exists": False})


@app.route("/api/wallet/context/<context_id>/freeze", methods=["POST"])
def endpoint_freeze(context_id):
    data = request.get_json(force=True) if request.data else {}
    actor = data.get("actor", "system")
    reason = data.get("reason", "")
    try:
        result = freeze_context(context_id, actor, reason)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/wallet/stats", methods=["GET"])
@app.route("/stats", methods=["GET"])  # nginx proxy fallback
def endpoint_stats():
    role = get_request_role()
    stats = get_wallet_stats()
    filtered = filter_stats_by_role(stats, role)
    return jsonify(filtered)


@app.route("/api/wallet/health", methods=["GET"])
@app.route("/health", methods=["GET"])
def endpoint_health():
    role = get_request_role()
    try:
        stats = get_wallet_stats()
        full_health = {
            "status": "healthy",
            "service": "WINDI WALLET v1.0.0",
            "protocol": "Three Dragons v1.1 — I9 Active",
            "port": int(os.environ.get("WALLET_PORT", 8098)),
            "crypto": "Ed25519 (PyNaCl)" if stats.get("has_nacl") else "fallback",
            "uuid": "v7" if stats.get("has_uuid7") else "v4",
            "humans": stats["total_humans"],
            "contexts_active": stats["active_contexts"],
            "contexts_frozen": stats["frozen_contexts"],
            "ledger_links": stats["total_ledger_links"],
            "avg_trust": stats["avg_trust_score"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return jsonify(filter_health_by_role(full_health, role))
    except Exception as e:
        return jsonify({"status": "degraded", "error": str(e)}), 503


# ─── Clone Wallet Endpoints (Phase 2 Bridge) ─────────────────────────────────

@app.route("/api/wallet/clone/register", methods=["POST"])
def endpoint_clone_register():
    """Register a commissioned clone wallet."""
    data = request.get_json(force=True)
    try:
        result = register_clone_wallet(data)
        code = 200 if result.get("idempotent") else 201
        return jsonify(result), code
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/wallet/clone/verify/<agent_id>", methods=["GET"])
def endpoint_clone_verify(agent_id):
    """Verify and return clone wallet data for Tab Wallet display."""
    result = verify_clone_wallet(agent_id)
    if not result:
        return jsonify({"error": "clone not found", "agent_id": agent_id}), 404
    return jsonify(result)


@app.route("/api/wallet/clone/status", methods=["GET"])
def endpoint_clone_status():
    """Get status of all commissioned clones."""
    return jsonify(get_clone_status())


# ─── Trust Events Endpoint (G4 FASE 2) ───────────────────────────────────────

@app.route("/api/wallet/trust/event", methods=["POST"])
def endpoint_trust_event():
    """
    Record a trust event and update trust score.
    Called after successful Ledger seal.

    Request:
        {
            wallet_id: str,
            event_type: str (e.g., 'receipt_created'),
            signal: int (+1 for positive events),
            receipt_id: Optional[str]
        }

    Response:
        {
            ok: true,
            event_id: str,
            trust_score: int (0-100),
            trust_level: int (1-5)
        }
    """
    data = request.get_json(force=True)
    try:
        result = record_trust_event(data)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Bridge Endpoints ────────────────────────────────────────────────────────

@app.route("/api/wallet/bridge/approve", methods=["POST"])
def bridge_approve():
    data = request.get_json(force=True)
    if not data.get("lead_id"):
        return jsonify({"error": "lead_id required"}), 400
    result = on_lead_approved(data)
    if result and result.get("status") == "ok":
        code = 200 if result.get("idempotent") else 201
        return jsonify(result), code
    return jsonify(result or {"error": "provision failed"}), 500


@app.route("/api/wallet/bridge/health", methods=["GET"])
def bridge_health():
    return jsonify({
        "status": "healthy",
        "module": "WALLET Bridge v1.0.0",
    })


# ─── Waitlist Endpoint (v1.1.0-W) ────────────────────────────────────────────

WAITLIST_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "genesis_waitlist.json")

def load_waitlist():
    """Load waitlist from file."""
    try:
        if os.path.exists(WAITLIST_FILE):
            with open(WAITLIST_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"[Waitlist] Load error: {e}")
    return {"entries": [], "count": 0}

def save_waitlist(data):
    """Save waitlist to file."""
    try:
        os.makedirs(os.path.dirname(WAITLIST_FILE), exist_ok=True)
        with open(WAITLIST_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"[Waitlist] Save error: {e}")
        return False

@app.route("/api/wallet/waitlist", methods=["POST"])
def endpoint_waitlist_join():
    """Add email to Genesis waitlist."""
    data = request.get_json(force=True)
    email = data.get("email", "").strip().lower()

    if not email or "@" not in email:
        return jsonify({"error": "valid email required"}), 400

    waitlist = load_waitlist()

    # Check if already on waitlist
    existing = [e for e in waitlist["entries"] if e["email"] == email]
    if existing:
        return jsonify({
            "status": "already_registered",
            "email": email,
            "position": existing[0].get("position", len(waitlist["entries"])),
            "timestamp": existing[0].get("timestamp")
        }), 200

    # Add to waitlist
    entry = {
        "email": email,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": data.get("source", "genesis"),
        "lang": data.get("lang", "en"),
        "position": len(waitlist["entries"]) + 1
    }
    waitlist["entries"].append(entry)
    waitlist["count"] = len(waitlist["entries"])

    if save_waitlist(waitlist):
        print(f"[Waitlist] New entry: {email} (position {entry['position']})")
        return jsonify({
            "status": "added",
            "email": email,
            "position": entry["position"],
            "total_waiting": waitlist["count"]
        }), 201
    else:
        return jsonify({"error": "failed to save"}), 500

@app.route("/api/wallet/waitlist", methods=["GET"])
def endpoint_waitlist_list():
    """Get waitlist (admin only)."""
    role = get_request_role()
    if role != "admin":
        return jsonify({"error": "admin access required"}), 403

    waitlist = load_waitlist()
    return jsonify({
        "count": waitlist["count"],
        "entries": waitlist["entries"]
    })


# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("WALLET_PORT", 8098))

    print()
    print("=" * 60)
    print("  WINDI WALLET Service v1.0.0")
    print(f"  Port: {port}")
    print(f"  DB: {os.environ.get('WALLET_DB_PATH', '/opt/windi/data/wallet.db')}")
    print()
    print("  Endpoints:")
    print("    POST /api/wallet/provision")
    print("    GET  /api/wallet/me?email=...&wallet_id=...")
    print("    POST /api/wallet/context/<id>/freeze")
    print("    GET  /api/wallet/stats")
    print("    GET  /api/wallet/health")
    print("    POST /api/wallet/clone/register")
    print("    GET  /api/wallet/clone/verify/<agent_id>")
    print("    GET  /api/wallet/clone/status")
    print("    POST /api/wallet/bridge/approve")
    print("    GET  /health")
    print()
    print("  AI processes. Human decides. WINDI guarantees.")
    print("=" * 60)
    print()

    app.run(host="0.0.0.0", port=port, debug=False)
