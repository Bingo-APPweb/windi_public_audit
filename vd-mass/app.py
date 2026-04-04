"""
W-VD-MASS-001 — WINDI Video Mass Processing Engine
Policy-based automation for batch video sealing

Port: 8131
Protocol: I9-P (Policy-based I9)

"Humano define critérios. Sistema executa em batch. Excepções escalam."

Liga IA+H · Kempten, Bavaria · 2026
Human Dragon + Guardian + Architect + Witness
"AI processes. Human decides. WINDI guarantees."
"""

import os
import sys
import uuid
import json
import sqlite3
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List
from functools import wraps

from flask import Flask, request, jsonify, g

# Configuration
PORT = int(os.environ.get("VD_MASS_PORT", 8131))
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

# Paths
BASE_DIR = Path("/opt/windi/vd-mass")
DATA_DIR = Path("/opt/windi/data")
LOG_DIR = Path("/opt/windi/logs")
DB_PATH = DATA_DIR / "vd_mass.db"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("w-vd-mass-001")

# Flask App
app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False


# ═══════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════

def get_db():
    """Get database connection."""
    if "db" not in g:
        g.db = sqlite3.connect(str(DB_PATH))
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    """Close database connection."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Initialize database schema."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Policies table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS policies (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            version TEXT DEFAULT '1.0',
            author_did TEXT NOT NULL,
            status TEXT DEFAULT 'draft',
            criteria TEXT NOT NULL,
            scope TEXT NOT NULL,
            exception_protocol TEXT,
            valid_until TEXT NOT NULL,
            activated_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            ledger_hash TEXT
        )
    """)

    # Batches table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS batches (
            id TEXT PRIMARY KEY,
            policy_id TEXT NOT NULL,
            submitted_by TEXT NOT NULL,
            submitted_at TEXT DEFAULT (datetime('now')),
            status TEXT DEFAULT 'pending',
            total_items INTEGER DEFAULT 0,
            conformes INTEGER DEFAULT 0,
            exceptions INTEGER DEFAULT 0,
            completed_at TEXT,
            FOREIGN KEY (policy_id) REFERENCES policies(id)
        )
    """)

    # Batch items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS batch_items (
            id TEXT PRIMARY KEY,
            batch_id TEXT NOT NULL,
            artifact_url TEXT NOT NULL,
            artifact_hash TEXT,
            criteria_results TEXT,
            verdict TEXT,
            seal_hash TEXT,
            seal_mode TEXT DEFAULT 'Policy-I9-P',
            sealed_at TEXT,
            human_decision TEXT,
            human_did TEXT,
            human_decided_at TEXT,
            FOREIGN KEY (batch_id) REFERENCES batches(id)
        )
    """)

    # Internal ledger for Policy-I9-P seals
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS internal_ledger (
            id TEXT PRIMARY KEY,
            seal_type TEXT NOT NULL,
            artifact_hash TEXT,
            policy_id TEXT,
            payload TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_policies_status ON policies(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_batches_status ON batches(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_verdict ON batch_items(verdict)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_batch ON batch_items(batch_id)")

    conn.commit()
    conn.close()
    log.info("Database initialized")


# ═══════════════════════════════════════════════════════════════
# POLICY ENGINE
# ═══════════════════════════════════════════════════════════════

SUPPORTED_CRITERIA = {
    "file_type": "extension permitida",
    "min_resolution": "resolução mínima em p",
    "max_duration_seconds": "duração máxima",
    "origin_domain": "domínio de origem",
    "has_hash": "artefacto tem hash SHA-256",
    "timestamp_valid": "timestamp dentro de janela"
}


def validate_criteria(criteria: List[Dict]) -> tuple[bool, str]:
    """Validate criteria list."""
    if not criteria:
        return False, "Criteria list cannot be empty"

    for c in criteria:
        if "type" not in c:
            return False, f"Criterion missing 'type': {c}"
        if c["type"] not in SUPPORTED_CRITERIA:
            return False, f"Unsupported criterion type: {c['type']}"
        if "value" not in c:
            return False, f"Criterion missing 'value': {c}"

    return True, "OK"


def check_criterion(criterion: Dict, artifact: Dict) -> tuple[bool, str]:
    """Check single criterion against artifact metadata."""
    ctype = criterion["type"]
    cvalue = criterion["value"]

    if ctype == "file_type":
        ext = artifact.get("extension", "").lower()
        allowed = [v.lower() for v in cvalue] if isinstance(cvalue, list) else [cvalue.lower()]
        if ext in allowed:
            return True, "pass"
        return False, f"extension '{ext}' not in {allowed}"

    elif ctype == "min_resolution":
        resolution = artifact.get("resolution", 0)
        if resolution >= cvalue:
            return True, "pass"
        return False, f"resolution {resolution}p < {cvalue}p"

    elif ctype == "max_duration_seconds":
        duration = artifact.get("duration_seconds", 0)
        if duration <= cvalue:
            return True, "pass"
        return False, f"duration {duration}s > {cvalue}s"

    elif ctype == "origin_domain":
        origin = artifact.get("origin_domain", "")
        allowed = cvalue if isinstance(cvalue, list) else [cvalue]
        if origin in allowed:
            return True, "pass"
        return False, f"origin '{origin}' not in {allowed}"

    elif ctype == "has_hash":
        has_hash = bool(artifact.get("hash"))
        if has_hash == cvalue:
            return True, "pass"
        return False, f"has_hash={has_hash}, expected={cvalue}"

    elif ctype == "timestamp_valid":
        # Check if artifact timestamp is within allowed window
        artifact_ts = artifact.get("timestamp")
        if not artifact_ts:
            return False, "no timestamp provided"

        max_age = cvalue.get("max_age_hours", 48)
        try:
            ts = datetime.fromisoformat(artifact_ts.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            age_hours = (now - ts).total_seconds() / 3600
            if age_hours <= max_age:
                return True, "pass"
            return False, f"age {age_hours:.1f}h > {max_age}h"
        except Exception as e:
            return False, f"invalid timestamp: {e}"

    return False, f"unknown criterion type: {ctype}"


def evaluate_artifact(policy: Dict, artifact: Dict) -> Dict:
    """Evaluate artifact against policy criteria."""
    criteria = json.loads(policy["criteria"]) if isinstance(policy["criteria"], str) else policy["criteria"]

    results = {}
    all_pass = True

    for criterion in criteria:
        passed, detail = check_criterion(criterion, artifact)
        results[criterion["type"]] = {
            "pass": passed,
            "detail": detail
        }
        if not passed:
            all_pass = False

    return {
        "verdict": "conforme" if all_pass else "exception",
        "criteria_results": results,
        "all_pass": all_pass
    }


def generate_seal(artifact_hash: str, policy: Dict, criteria_results: Dict) -> Dict:
    """Generate Policy-I9-P seal payload."""
    seal_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    return {
        "seal_id": seal_id,
        "seal_mode": "Policy-I9-P",
        "artifact_hash": artifact_hash,
        "policy_id": policy["id"],
        "policy_version": policy["version"],
        "author_did": policy["author_did"],
        "criteria_checked": list(criteria_results.keys()),
        "criteria_results": {k: v["pass"] for k, v in criteria_results.items()},
        "sealed_at": now,
        "policy_valid_until": policy["valid_until"]
    }


# ═══════════════════════════════════════════════════════════════
# ROUTES — Health & Metrics
# ═══════════════════════════════════════════════════════════════

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "W-VD-MASS-001",
        "version": "1.0.0",
        "port": PORT,
        "protocol": "I9-P",
        "db_path": str(DB_PATH),
        "db_exists": DB_PATH.exists()
    })


@app.route("/metrics", methods=["GET"])
def metrics():
    """Metrics endpoint."""
    db = get_db()
    cursor = db.cursor()

    # Policy counts
    cursor.execute("SELECT status, COUNT(*) FROM policies GROUP BY status")
    policy_counts = {row[0]: row[1] for row in cursor.fetchall()}

    # Batch counts
    cursor.execute("SELECT status, COUNT(*) FROM batches GROUP BY status")
    batch_counts = {row[0]: row[1] for row in cursor.fetchall()}

    # Item counts
    cursor.execute("SELECT verdict, COUNT(*) FROM batch_items GROUP BY verdict")
    item_counts = {row[0]: row[1] for row in cursor.fetchall()}

    # Pending exceptions
    cursor.execute("""
        SELECT COUNT(*) FROM batch_items
        WHERE verdict = 'exception' AND human_decision IS NULL
    """)
    pending_exceptions = cursor.fetchone()[0]

    return jsonify({
        "service": "W-VD-MASS-001",
        "policies": policy_counts,
        "batches": batch_counts,
        "items": item_counts,
        "pending_exceptions": pending_exceptions,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


# ═══════════════════════════════════════════════════════════════
# ROUTES — Policy Management
# ═══════════════════════════════════════════════════════════════

@app.route("/policy/create", methods=["POST"])
def policy_create():
    """Create new I9-P Policy."""
    data = request.get_json()

    # Validate required fields
    required = ["name", "author_did", "valid_until", "criteria"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    # Validate criteria
    valid, msg = validate_criteria(data["criteria"])
    if not valid:
        return jsonify({"error": msg}), 400

    # Validate valid_until
    try:
        valid_date = datetime.fromisoformat(data["valid_until"])
        if valid_date < datetime.now(timezone.utc):
            return jsonify({"error": "valid_until must be in the future"}), 400
    except:
        return jsonify({"error": "Invalid valid_until format (use ISO date)"}), 400

    # Generate policy
    policy_id = str(uuid.uuid4())

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO policies (id, name, version, author_did, criteria, scope, exception_protocol, valid_until)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        policy_id,
        data["name"],
        data.get("version", "1.0"),
        data["author_did"],
        json.dumps(data["criteria"]),
        json.dumps(data.get("scope", {})),
        data.get("exception_protocol"),
        data["valid_until"]
    ))

    db.commit()
    log.info(f"Policy created: {policy_id} by {data['author_did']}")

    return jsonify({
        "status": "created",
        "policy_id": policy_id,
        "name": data["name"],
        "author_did": data["author_did"],
        "valid_until": data["valid_until"],
        "criteria_count": len(data["criteria"])
    }), 201


@app.route("/policy/<policy_id>", methods=["GET"])
def policy_get(policy_id: str):
    """Get policy details."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM policies WHERE id = ?", (policy_id,))
    row = cursor.fetchone()

    if not row:
        return jsonify({"error": "Policy not found"}), 404

    return jsonify({
        "id": row["id"],
        "name": row["name"],
        "version": row["version"],
        "author_did": row["author_did"],
        "status": row["status"],
        "criteria": json.loads(row["criteria"]),
        "scope": json.loads(row["scope"]) if row["scope"] else {},
        "exception_protocol": row["exception_protocol"],
        "valid_until": row["valid_until"],
        "activated_at": row["activated_at"],
        "created_at": row["created_at"],
        "ledger_hash": row["ledger_hash"]
    })


@app.route("/policy/<policy_id>/validate", methods=["POST"])
def policy_validate(policy_id: str):
    """Validate artifact against policy."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM policies WHERE id = ?", (policy_id,))
    policy = cursor.fetchone()

    if not policy:
        return jsonify({"error": "Policy not found"}), 404

    if policy["status"] != "active":
        return jsonify({"error": f"Policy not active (status: {policy['status']})"}), 400

    artifact = request.get_json()
    if not artifact:
        return jsonify({"error": "Artifact data required"}), 400

    result = evaluate_artifact(dict(policy), artifact)

    return jsonify({
        "policy_id": policy_id,
        "policy_name": policy["name"],
        "artifact": artifact,
        "verdict": result["verdict"],
        "criteria_results": result["criteria_results"]
    })


@app.route("/policy/<policy_id>/activate", methods=["POST"])
def policy_activate(policy_id: str):
    """Activate policy (signs in internal ledger)."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM policies WHERE id = ?", (policy_id,))
    policy = cursor.fetchone()

    if not policy:
        return jsonify({"error": "Policy not found"}), 404

    if policy["status"] == "active":
        return jsonify({"error": "Policy already active"}), 400

    if policy["status"] == "revoked":
        return jsonify({"error": "Cannot activate revoked policy"}), 400

    # Generate ledger hash
    now = datetime.now(timezone.utc)
    payload = {
        "type": "policy_activation",
        "policy_id": policy_id,
        "policy_name": policy["name"],
        "author_did": policy["author_did"],
        "criteria": json.loads(policy["criteria"]),
        "valid_until": policy["valid_until"],
        "activated_at": now.isoformat()
    }
    ledger_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    # Update policy
    cursor.execute("""
        UPDATE policies SET status = 'active', activated_at = ?, ledger_hash = ?
        WHERE id = ?
    """, (now.isoformat(), ledger_hash, policy_id))

    # Record in internal ledger
    cursor.execute("""
        INSERT INTO internal_ledger (id, seal_type, policy_id, payload)
        VALUES (?, 'policy_activation', ?, ?)
    """, (str(uuid.uuid4()), policy_id, json.dumps(payload)))

    db.commit()
    log.info(f"Policy activated: {policy_id}, hash: {ledger_hash[:16]}...")

    return jsonify({
        "status": "activated",
        "policy_id": policy_id,
        "ledger_hash": ledger_hash,
        "activated_at": now.isoformat()
    })


@app.route("/policy/list", methods=["GET"])
def policy_list():
    """List policies."""
    status_filter = request.args.get("status")

    db = get_db()
    cursor = db.cursor()

    if status_filter:
        cursor.execute("SELECT * FROM policies WHERE status = ? ORDER BY created_at DESC", (status_filter,))
    else:
        cursor.execute("SELECT * FROM policies ORDER BY created_at DESC")

    policies = []
    for row in cursor.fetchall():
        policies.append({
            "id": row["id"],
            "name": row["name"],
            "status": row["status"],
            "author_did": row["author_did"],
            "valid_until": row["valid_until"],
            "created_at": row["created_at"]
        })

    return jsonify({
        "count": len(policies),
        "policies": policies
    })


# ═══════════════════════════════════════════════════════════════
# ROUTES — Batch Processing
# ═══════════════════════════════════════════════════════════════

@app.route("/batch/submit", methods=["POST"])
def batch_submit():
    """Submit batch for processing."""
    data = request.get_json()

    required = ["policy_id", "submitted_by", "items"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    if not data["items"]:
        return jsonify({"error": "Items list cannot be empty"}), 400

    db = get_db()
    cursor = db.cursor()

    # Verify policy exists and is active
    cursor.execute("SELECT * FROM policies WHERE id = ?", (data["policy_id"],))
    policy = cursor.fetchone()

    if not policy:
        return jsonify({"error": "Policy not found"}), 404

    if policy["status"] != "active":
        return jsonify({"error": f"Policy not active (status: {policy['status']})"}), 400

    # Check policy validity
    valid_until = datetime.fromisoformat(policy["valid_until"])
    if valid_until < datetime.now(timezone.utc):
        return jsonify({"error": "Policy has expired"}), 400

    # Create batch
    batch_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO batches (id, policy_id, submitted_by, total_items)
        VALUES (?, ?, ?, ?)
    """, (batch_id, data["policy_id"], data["submitted_by"], len(data["items"])))

    # Process items
    conformes = 0
    exceptions = 0

    for item in data["items"]:
        item_id = str(uuid.uuid4())
        artifact_url = item.get("url", item.get("path", ""))
        artifact_hash = item.get("hash")

        # Evaluate against policy
        result = evaluate_artifact(dict(policy), item)
        verdict = result["verdict"]
        criteria_results = result["criteria_results"]

        seal_hash = None
        sealed_at = None

        if verdict == "conforme":
            # Generate automatic seal
            seal = generate_seal(artifact_hash or "", dict(policy), criteria_results)
            seal_hash = hashlib.sha256(json.dumps(seal, sort_keys=True).encode()).hexdigest()
            sealed_at = seal["sealed_at"]

            # Record in internal ledger
            cursor.execute("""
                INSERT INTO internal_ledger (id, seal_type, artifact_hash, policy_id, payload)
                VALUES (?, 'artifact_seal', ?, ?, ?)
            """, (seal["seal_id"], artifact_hash, data["policy_id"], json.dumps(seal)))

            conformes += 1
            log.info(f"Item sealed: {artifact_hash[:16] if artifact_hash else 'no-hash'}... (Policy-I9-P)")
        else:
            exceptions += 1
            log.info(f"Item exception: {artifact_url} -> {[k for k,v in criteria_results.items() if not v['pass']]}")

        cursor.execute("""
            INSERT INTO batch_items (id, batch_id, artifact_url, artifact_hash, criteria_results, verdict, seal_hash, sealed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item_id, batch_id, artifact_url, artifact_hash,
            json.dumps(criteria_results), verdict, seal_hash, sealed_at
        ))

    # Update batch counts
    cursor.execute("""
        UPDATE batches SET conformes = ?, exceptions = ?, status = 'done', completed_at = ?
        WHERE id = ?
    """, (conformes, exceptions, datetime.now(timezone.utc).isoformat(), batch_id))

    db.commit()
    log.info(f"Batch completed: {batch_id}, conformes={conformes}, exceptions={exceptions}")

    return jsonify({
        "status": "completed",
        "batch_id": batch_id,
        "policy_id": data["policy_id"],
        "total_items": len(data["items"]),
        "conformes": conformes,
        "exceptions": exceptions,
        "seal_mode": "Policy-I9-P"
    })


@app.route("/batch/<batch_id>/status", methods=["GET"])
def batch_status(batch_id: str):
    """Get batch status."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM batches WHERE id = ?", (batch_id,))
    batch = cursor.fetchone()

    if not batch:
        return jsonify({"error": "Batch not found"}), 404

    return jsonify({
        "batch_id": batch["id"],
        "policy_id": batch["policy_id"],
        "submitted_by": batch["submitted_by"],
        "submitted_at": batch["submitted_at"],
        "status": batch["status"],
        "total_items": batch["total_items"],
        "conformes": batch["conformes"],
        "exceptions": batch["exceptions"],
        "completed_at": batch["completed_at"]
    })


@app.route("/batch/<batch_id>/results", methods=["GET"])
def batch_results(batch_id: str):
    """Get batch results."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM batches WHERE id = ?", (batch_id,))
    batch = cursor.fetchone()

    if not batch:
        return jsonify({"error": "Batch not found"}), 404

    cursor.execute("SELECT * FROM batch_items WHERE batch_id = ?", (batch_id,))
    items = []
    for row in cursor.fetchall():
        items.append({
            "id": row["id"],
            "artifact_url": row["artifact_url"],
            "artifact_hash": row["artifact_hash"],
            "verdict": row["verdict"],
            "criteria_results": json.loads(row["criteria_results"]) if row["criteria_results"] else {},
            "seal_hash": row["seal_hash"],
            "sealed_at": row["sealed_at"],
            "human_decision": row["human_decision"],
            "human_did": row["human_did"]
        })

    return jsonify({
        "batch_id": batch_id,
        "status": batch["status"],
        "total_items": batch["total_items"],
        "conformes": batch["conformes"],
        "exceptions": batch["exceptions"],
        "items": items
    })


# ═══════════════════════════════════════════════════════════════
# ROUTES — Exception Queue
# ═══════════════════════════════════════════════════════════════

@app.route("/queue/exceptions", methods=["GET"])
def queue_exceptions():
    """List pending exceptions."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT bi.*, b.policy_id, p.name as policy_name
        FROM batch_items bi
        JOIN batches b ON bi.batch_id = b.id
        JOIN policies p ON b.policy_id = p.id
        WHERE bi.verdict = 'exception' AND bi.human_decision IS NULL
        ORDER BY bi.rowid DESC
    """)

    exceptions = []
    for row in cursor.fetchall():
        exceptions.append({
            "id": row["id"],
            "batch_id": row["batch_id"],
            "policy_id": row["policy_id"],
            "policy_name": row["policy_name"],
            "artifact_url": row["artifact_url"],
            "artifact_hash": row["artifact_hash"],
            "criteria_results": json.loads(row["criteria_results"]) if row["criteria_results"] else {},
            "failed_criteria": [k for k, v in json.loads(row["criteria_results"]).items() if not v["pass"]] if row["criteria_results"] else []
        })

    return jsonify({
        "count": len(exceptions),
        "exceptions": exceptions
    })


@app.route("/queue/<item_id>/decide", methods=["POST"])
def queue_decide(item_id: str):
    """Human decision on exception."""
    data = request.get_json()

    if "decision" not in data:
        return jsonify({"error": "Missing 'decision' field (approve/reject)"}), 400

    if data["decision"] not in ["approve", "reject"]:
        return jsonify({"error": "Decision must be 'approve' or 'reject'"}), 400

    if "human_did" not in data:
        return jsonify({"error": "Missing 'human_did' field"}), 400

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM batch_items WHERE id = ?", (item_id,))
    item = cursor.fetchone()

    if not item:
        return jsonify({"error": "Item not found"}), 404

    if item["verdict"] != "exception":
        return jsonify({"error": "Item is not an exception"}), 400

    if item["human_decision"]:
        return jsonify({"error": "Decision already made"}), 400

    now = datetime.now(timezone.utc).isoformat()

    seal_hash = None
    if data["decision"] == "approve":
        # Generate manual approval seal
        seal = {
            "seal_id": str(uuid.uuid4()),
            "seal_mode": "Human-Override-I9",
            "artifact_hash": item["artifact_hash"],
            "original_verdict": "exception",
            "human_decision": "approve",
            "human_did": data["human_did"],
            "decided_at": now
        }
        seal_hash = hashlib.sha256(json.dumps(seal, sort_keys=True).encode()).hexdigest()

        # Record in internal ledger
        cursor.execute("""
            INSERT INTO internal_ledger (id, seal_type, artifact_hash, payload)
            VALUES (?, 'human_override', ?, ?)
        """, (seal["seal_id"], item["artifact_hash"], json.dumps(seal)))

    cursor.execute("""
        UPDATE batch_items SET human_decision = ?, human_did = ?, human_decided_at = ?, seal_hash = ?
        WHERE id = ?
    """, (data["decision"], data["human_did"], now, seal_hash, item_id))

    db.commit()
    log.info(f"Exception decided: {item_id} -> {data['decision']} by {data['human_did']}")

    return jsonify({
        "status": "decided",
        "item_id": item_id,
        "decision": data["decision"],
        "human_did": data["human_did"],
        "seal_hash": seal_hash,
        "decided_at": now
    })


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    log.info(f"W-VD-MASS-001 starting on port {PORT}")
    log.info(f"Protocol: I9-P (Policy-based I9)")
    log.info(f"DB: {DB_PATH}")

    init_db()

    app.run(host="127.0.0.1", port=PORT, debug=DEBUG)
