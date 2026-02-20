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
    get_wallet_by_id, freeze_context, get_wallet_stats
)
from wallet_bridge import on_lead_approved

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
def endpoint_stats():
    return jsonify(get_wallet_stats())


@app.route("/api/wallet/health", methods=["GET"])
@app.route("/health", methods=["GET"])
def endpoint_health():
    try:
        stats = get_wallet_stats()
        return jsonify({
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
        })
    except Exception as e:
        return jsonify({"status": "degraded", "error": str(e)}), 503


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
    print("    POST /api/wallet/bridge/approve")
    print("    GET  /health")
    print()
    print("  AI processes. Human decides. WINDI guarantees.")
    print("=" * 60)
    print()

    app.run(host="0.0.0.0", port=port, debug=False)
