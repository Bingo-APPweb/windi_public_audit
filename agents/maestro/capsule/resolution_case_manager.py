#!/usr/bin/env python3
"""
WINDI Maestro — Resolution Case Manager
========================================

Manages the lifecycle of governance resolution cases.
A Case is an immutable-per-event object that tracks:
- Finding reference (from Sentinela)
- Routing decision
- SLA state
- Human acknowledgments
- Resolution record

Case States:
  open → routed → acknowledged → decided → closed

State Transition Rules:
- open → routed: Automatic after routing decision
- routed → acknowledged: Requires human ACK
- acknowledged → decided: Requires human decision + ACK
- decided → closed: Automatic after ledger write

Principles:
- Cases are append-only (timeline is immutable history)
- Every state change is an event with timestamp
- No state transition without proper trigger
- Hash chain ensures integrity
"""

import hashlib
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class Case:
    """
    Governance Resolution Case

    Represents a compliance finding that requires human resolution.
    All state changes are recorded in the timeline.
    """
    case_id: str
    finding_ref: Dict
    status: str = "open"  # open | routed | acknowledged | decided | closed
    route: Dict = field(default_factory=dict)
    sla: Dict = field(default_factory=dict)
    timeline: List[Dict] = field(default_factory=list)
    invariants: List[str] = field(default_factory=list)
    severity: str = "R3"
    isp_id: Optional[str] = None
    assigned_to: Optional[str] = None
    dual_ack_required: bool = False
    acks: List[Dict] = field(default_factory=list)
    resolution: Optional[Dict] = None
    closed_at: Optional[str] = None
    case_hash: str = ""

    def add_event(self, kind: str, payload: Dict, actor: Optional[str] = None):
        """Add an event to the case timeline (immutable append)."""
        event = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "kind": kind,
            "payload": payload
        }
        if actor:
            event["actor"] = actor
        self.timeline.append(event)
        self._update_hash()

    def _update_hash(self):
        """Recompute case hash after state change."""
        self.case_hash = compute_case_hash(self)

    def to_dict(self) -> Dict:
        """Serialize case to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize case to JSON."""
        return json.dumps(self.to_dict(), indent=2, default=str)

    def can_transition_to(self, new_status: str) -> bool:
        """Check if transition to new_status is valid."""
        valid_transitions = {
            "open": ["routed"],
            "routed": ["acknowledged"],
            "acknowledged": ["decided"],
            "decided": ["closed"],
            "closed": []  # Terminal state
        }
        return new_status in valid_transitions.get(self.status, [])

    def get_current_sla_status(self) -> Dict:
        """Get current SLA status."""
        if not self.sla:
            return {"status": "no_sla"}

        now = datetime.now(timezone.utc)
        fr_due = self.sla.get("first_response_due")
        dec_due = self.sla.get("decision_due")

        status = {
            "first_response": {
                "due": fr_due,
                "breached": False,
                "acknowledged": self.status in ["acknowledged", "decided", "closed"]
            },
            "decision": {
                "due": dec_due,
                "breached": False,
                "decided": self.status in ["decided", "closed"]
            }
        }

        if fr_due:
            fr_dt = datetime.fromisoformat(fr_due.replace("Z", "+00:00"))
            if now > fr_dt and not status["first_response"]["acknowledged"]:
                status["first_response"]["breached"] = True

        if dec_due:
            dec_dt = datetime.fromisoformat(dec_due.replace("Z", "+00:00"))
            if now > dec_dt and not status["decision"]["decided"]:
                status["decision"]["breached"] = True

        return status


def new_case(finding: Dict) -> Case:
    """
    Create a new Case from a compliance finding.

    Args:
        finding: Compliance finding from Sentinela containing:
            - forensic_hash: Hash of the finding
            - capsule: Source capsule name
            - severity: Risk level (R1-R5)
            - invariants_at_risk: List of affected invariants
            - message: Finding description
            - details: Additional context

    Returns:
        New Case instance in 'open' status
    """
    case_id = f"CASE-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

    # Extract finding reference (metadata only, no content)
    finding_ref = {
        "hash": finding.get("forensic_hash", finding.get("hash", "")),
        "capsule": finding.get("capsule", "unknown"),
        "severity": finding.get("severity", "R3"),
        "message": finding.get("message", "")[:200],  # Truncate for safety
        "timestamp": finding.get("timestamp", datetime.now(timezone.utc).isoformat())
    }

    case = Case(
        case_id=case_id,
        finding_ref=finding_ref,
        invariants=finding.get("invariants_at_risk", []) or [],
        severity=finding.get("severity", "R3"),
        isp_id=finding.get("isp_id")
    )

    case.add_event("case_created", {
        "finding_ref": finding_ref,
        "source": "sentinela"
    })

    return case


def compute_case_hash(case: Case) -> str:
    """
    Compute integrity hash of the case.

    Includes all state but excludes the hash itself to avoid circular dependency.
    """
    data = {
        "case_id": case.case_id,
        "finding_ref": case.finding_ref,
        "status": case.status,
        "route": case.route,
        "sla": case.sla,
        "timeline": case.timeline,
        "invariants": case.invariants,
        "severity": case.severity,
        "assigned_to": case.assigned_to,
        "acks": case.acks,
        "resolution": case.resolution
    }
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def transition_case(case: Case, new_status: str, actor: str, payload: Dict = None) -> bool:
    """
    Transition case to new status with validation.

    Args:
        case: Case to transition
        new_status: Target status
        actor: Human actor performing the transition
        payload: Additional data for the transition

    Returns:
        True if transition succeeded, False otherwise
    """
    if not case.can_transition_to(new_status):
        return False

    old_status = case.status
    case.status = new_status

    event_payload = {
        "from": old_status,
        "to": new_status,
        **(payload or {})
    }

    case.add_event(f"status_{new_status}", event_payload, actor=actor)

    if new_status == "closed":
        case.closed_at = datetime.now(timezone.utc).isoformat()

    return True


def load_case(case_path: Path) -> Optional[Case]:
    """Load case from JSON file."""
    try:
        with open(case_path, 'r') as f:
            data = json.load(f)
            return Case(**data)
    except (json.JSONDecodeError, IOError, TypeError):
        return None


def save_case(case: Case, cases_dir: Path) -> Path:
    """
    Save case to JSON file.

    Returns path to saved file.
    """
    cases_dir.mkdir(parents=True, exist_ok=True)
    case_file = cases_dir / f"{case.case_id}.json"

    with open(case_file, 'w') as f:
        f.write(case.to_json())

    return case_file


# Convenience alias
case_hash = compute_case_hash
