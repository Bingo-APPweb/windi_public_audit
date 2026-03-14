from flask import Blueprint, jsonify
from datetime import datetime, timezone

hub_blueprint = Blueprint('hub', __name__)

AGENT_REGISTRY = [
    {"id": "W-LEGAL-001",  "version": "v0.2.0", "domain": "legal",         "endpoints": 22,  "pipeline": None,                             "wave": None,   "invariant": None},
    {"id": "W-NOTARY-001", "version": "v1.0.0", "domain": "notary",        "endpoints": None,"pipeline": None,                             "wave": None,   "invariant": None},
    {"id": "W-COMPLY-001", "version": "v1.0.0", "domain": "compliance",    "endpoints": None,"pipeline": None,                             "wave": None,   "invariant": None},
    {"id": "W-COMM-001",   "version": "v2.0.0", "domain": "communication", "endpoints": 8,   "pipeline": None,                             "wave": None,   "invariant": None},
    {"id": "W-JOURN-001",  "version": "v1.0.0", "domain": "journalism",    "endpoints": None,"pipeline": ["J1","J2","J3","J4","J5","J6"],  "wave": None,   "invariant": None},
    {"id": "W-AUDIT-001",  "version": "v1.0.0", "domain": "audit",         "endpoints": None,"pipeline": None,                             "wave": None,   "invariant": None},
    {"id": "W-ACCT-001",   "version": "v1.0.0", "domain": "accounting",    "endpoints": None,"pipeline": None,                             "wave": "Wave3","invariant": "C6"},
]

@hub_blueprint.route('/agents/status', methods=['GET'])
def agents_status():
    ts = datetime.now(timezone.utc).isoformat()
    agents_out = []
    for a in AGENT_REGISTRY:
        entry = {
            "id": a["id"],
            "version": a["version"],
            "status": "active",
            "domain": a["domain"],
            "last_check": ts
        }
        if a["endpoints"] is not None:
            entry["endpoints"] = a["endpoints"]
        if a["pipeline"] is not None:
            entry["pipeline"] = a["pipeline"]
        if a["wave"] is not None:
            entry["wave"] = a["wave"]
        if a["invariant"] is not None:
            entry["invariant"] = a["invariant"]
        agents_out.append(entry)

    return jsonify({
        "status": "ok",
        "constellation": {
            "core": ":8091",
            "hub": "Dragon Hub v1.0 (a65e766)",
            "timestamp": ts
        },
        "agents": agents_out,
        "summary": {
            "total": len(agents_out),
            "active": len(agents_out),
            "inactive": 0
        }
    })
