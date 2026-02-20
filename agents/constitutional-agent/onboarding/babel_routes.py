#!/usr/bin/env python3
"""
WINDI Agent API Routes for a4Desk BABEL Integration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

These routes extend the Constitutional Agent API (port 8091)
to accept document events from a4Desk BABEL (port 8085).

Routes:
  POST /api/v1/babel/event     — Receive document event
  POST /api/v1/babel/analyze   — Analyze document content
  GET  /api/v1/babel/status    — Bridge status
  GET  /api/v1/babel/pending   — Pending escalations
  POST /api/v1/babel/decide    — Submit human decision
"""

# NOTE: These routes are designed to be imported into the main Agent API.
# They define the interface contract between BABEL and the Agent.

BABEL_ROUTES = {
    "POST /api/v1/babel/event": {
        "description": "Receive a document lifecycle event from a4Desk",
        "body": {
            "event_type": "doc.created | doc.modified | doc.sealed | doc.submitted | doc.evidence_added",
            "document": {
                "content": "string — document text content",
                "type": "CONTRACT | INVOICE | APPROVAL | REPORT | ...",
                "isp_profile": "string — ISP profile name (optional)",
                "metadata": "dict — additional metadata",
            },
        },
        "response": {
            "event_id": "string",
            "sge_result": "dict — SGE analysis",
            "escalation": "dict | null — if risk >= R3",
            "processing_halted": "bool — true if waiting for human",
        },
    },
    "POST /api/v1/babel/analyze": {
        "description": "Analyze document content through SGE without lifecycle event",
        "body": {
            "content": "string — document text",
            "type": "string — document type",
            "isp_profile": "string — ISP profile (optional)",
        },
        "response": {
            "risk_level": "R0-R5",
            "risk_score": "int (0-100)",
            "layers": "dict — layer-by-layer findings",
            "flags": "list — governance flags",
            "human_decision_required": "bool — always true for R3+",
        },
    },
    "GET /api/v1/babel/status": {
        "description": "Get BABEL Bridge operational status",
        "response": {
            "bridge": "operational | degraded | offline",
            "sge_connected": "bool",
            "events_processed": "int",
            "pending_escalations": "int",
        },
    },
    "GET /api/v1/babel/pending": {
        "description": "List all pending escalations awaiting human decision",
        "response": {
            "pending": "list of escalation records",
        },
    },
    "POST /api/v1/babel/decide": {
        "description": "Submit human decision for a pending escalation",
        "body": {
            "escalation_id": "string — ESC-W001-...",
            "decision": "APPROVED | REJECTED | MODIFIED | DEFERRED | OVERRIDDEN | ESCALATED",
            "reason": "string — why this decision",
        },
        "response": {
            "escalation_id": "string",
            "decision_recorded": "bool",
            "virtue_receipt": "dict — generated receipt",
        },
    },
}


def get_route_manifest() -> dict:
    """Return the complete route manifest for documentation."""
    return {
        "name": "BABEL Integration Routes",
        "version": "1.0.0",
        "base_path": "/api/v1/babel",
        "agent_port": 8091,
        "babel_port": 8085,
        "routes": BABEL_ROUTES,
        "principle": "AI processes. Human decides. WINDI guarantees.",
        "i9": "No route auto-applies decisions. All R3+ require human action.",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(get_route_manifest(), indent=2))
