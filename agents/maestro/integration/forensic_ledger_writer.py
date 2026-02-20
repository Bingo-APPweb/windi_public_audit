#!/usr/bin/env python3
"""
WINDI Maestro — Forensic Ledger Writer
=======================================

Writes case lifecycle events to the immutable forensic ledger.
Every case state transition is recorded for full auditability.

Event Types:
- case_created: New case opened from finding
- case_routed: Routing decision recorded
- case_acknowledged: Human first response ACK
- case_decided: Human decision recorded
- case_closed: Resolution complete
- sla_breach: SLA threshold crossed
- escalation: Case escalated to higher authority

Principles:
- APPEND-ONLY: No updates, no deletes
- ZERO-CONTENT: Only hashes, metadata, never document content
- TIMESTAMPED: UTC timestamps, immutable
- HASH-CHAINED: Each entry links to previous
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger("WINDI.Maestro.Ledger")

# Ledger file location (configurable)
DEFAULT_LEDGER_PATH = Path("/opt/windi/data/ledger/maestro_events.jsonl")


def compute_event_hash(event: Dict, prev_hash: str) -> str:
    """
    Compute hash for ledger event (hash chain).

    Args:
        event: Event data to hash
        prev_hash: Previous event hash for chaining

    Returns:
        SHA-256 hash of event
    """
    data = {
        "prev": prev_hash,
        "event": event
    }
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def get_last_hash(ledger_path: Path) -> str:
    """
    Get hash of last event in ledger.

    Returns genesis hash if ledger is empty.
    """
    genesis = "GENESIS_MAESTRO_" + hashlib.sha256(b"WINDI_MAESTRO_LEDGER_V1").hexdigest()[:32]

    if not ledger_path.exists():
        return genesis

    try:
        with open(ledger_path, 'r') as f:
            last_line = None
            for line in f:
                if line.strip():
                    last_line = line

            if last_line:
                entry = json.loads(last_line)
                return entry.get("event_hash", genesis)
    except (json.JSONDecodeError, IOError):
        pass

    return genesis


def write_case_event(
    case_id: str,
    event_type: str,
    payload: Dict,
    actor: Optional[str] = None,
    ledger_path: Optional[Path] = None
) -> Dict:
    """
    Write case event to forensic ledger.

    Args:
        case_id: Case identifier
        event_type: Type of event (case_created, case_routed, etc.)
        payload: Event payload (metadata only, no content)
        actor: Human actor (if applicable)
        ledger_path: Optional custom ledger path

    Returns:
        Ledger entry with event_hash
    """
    path = ledger_path or DEFAULT_LEDGER_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    # Get previous hash for chaining
    prev_hash = get_last_hash(path)

    # Build event
    timestamp = datetime.now(timezone.utc).isoformat()

    event = {
        "case_id": case_id,
        "event_type": event_type,
        "timestamp_utc": timestamp,
        "payload": payload
    }

    if actor:
        event["actor"] = actor

    # Compute hash
    event_hash = compute_event_hash(event, prev_hash)

    # Build ledger entry
    entry = {
        "event_hash": event_hash,
        "prev_hash": prev_hash,
        "event": event
    }

    # Append to ledger
    with open(path, 'a') as f:
        f.write(json.dumps(entry, default=str) + "\n")

    logger.info(
        f"Ledger write: case={case_id} type={event_type} hash={event_hash[:16]}..."
    )

    return entry


def write_routing_event(
    case_id: str,
    route: Dict,
    actor: str = "system",
    ledger_path: Optional[Path] = None
) -> Dict:
    """Write routing decision to ledger."""
    payload = {
        "route_to_role": route.get("role"),
        "channel": route.get("channel"),
        "rule_matched": route.get("rule_matched"),
        "dual_ack_required": route.get("require_dual_ack", False)
    }
    return write_case_event(case_id, "case_routed", payload, actor, ledger_path)


def write_ack_event(
    case_id: str,
    ack: Dict,
    ledger_path: Optional[Path] = None
) -> Dict:
    """Write human acknowledgment to ledger."""
    payload = {
        "action": ack.get("action"),
        "ack_token": ack.get("ack_token"),
        "human_id": ack.get("human_id")
    }
    return write_case_event(
        case_id,
        "case_acknowledged",
        payload,
        ack.get("human_id"),
        ledger_path
    )


def write_decision_event(
    case_id: str,
    decision_ack: Dict,
    ledger_path: Optional[Path] = None
) -> Dict:
    """Write human decision to ledger."""
    details = decision_ack.get("details", {})
    payload = {
        "decision": details.get("decision"),
        "ack_token": decision_ack.get("ack_token"),
        "overrides_ai": details.get("overrides_ai", False),
        "i9_compliant": decision_ack.get("i9_compliant", True)
    }
    return write_case_event(
        case_id,
        "case_decided",
        payload,
        decision_ack.get("human_id"),
        ledger_path
    )


def write_sla_breach_event(
    case_id: str,
    breach_type: str,
    sla: Dict,
    ledger_path: Optional[Path] = None
) -> Dict:
    """Write SLA breach to ledger."""
    payload = {
        "breach_type": breach_type,
        "deadline": sla.get(f"{breach_type}_due"),
        "severity": sla.get("severity")
    }
    return write_case_event(case_id, "sla_breach", payload, ledger_path=ledger_path)


def write_escalation_event(
    case_id: str,
    escalation_ack: Dict,
    ledger_path: Optional[Path] = None
) -> Dict:
    """Write escalation to ledger."""
    details = escalation_ack.get("details", {})
    payload = {
        "reason": details.get("reason"),
        "target_role": details.get("target_role"),
        "ack_token": escalation_ack.get("ack_token")
    }
    return write_case_event(
        case_id,
        "escalation",
        payload,
        escalation_ack.get("human_id"),
        ledger_path
    )


def verify_chain_integrity(ledger_path: Optional[Path] = None) -> Dict:
    """
    Verify integrity of ledger hash chain.

    Returns:
        Dict with valid status and any issues found
    """
    path = ledger_path or DEFAULT_LEDGER_PATH

    if not path.exists():
        return {"valid": True, "entries": 0, "issues": []}

    issues = []
    entry_count = 0
    expected_prev = get_last_hash(Path("/dev/null"))  # Genesis

    try:
        with open(path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue

                try:
                    entry = json.loads(line)
                    entry_count += 1

                    # Verify prev_hash chain
                    if entry.get("prev_hash") != expected_prev:
                        if line_num > 1:  # Skip genesis check
                            issues.append(
                                f"Line {line_num}: prev_hash mismatch"
                            )

                    # Verify event_hash computation
                    computed = compute_event_hash(
                        entry.get("event", {}),
                        entry.get("prev_hash", "")
                    )
                    if computed != entry.get("event_hash"):
                        issues.append(
                            f"Line {line_num}: event_hash invalid"
                        )

                    expected_prev = entry.get("event_hash", "")

                except json.JSONDecodeError:
                    issues.append(f"Line {line_num}: invalid JSON")

    except IOError as e:
        issues.append(f"Read error: {e}")

    return {
        "valid": len(issues) == 0,
        "entries": entry_count,
        "issues": issues
    }
