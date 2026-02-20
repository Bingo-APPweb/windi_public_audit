#!/usr/bin/env python3
"""
WINDI Maestro — Human Acknowledgment Protocol
==============================================

Handles human acknowledgments (ACKs) for case state transitions.
Every case state change requires a valid human ACK.

ACK Types:
- acknowledge: Human confirms receipt of case
- decide: Human records resolution decision
- close: Human confirms case closure
- escalate: Human requests escalation

ACK Token:
- Deterministic hash of case_id + human_id + action + nonce
- Can be replaced by PKI/signature in production

Dual ACK:
- Required for R4-R5 severity
- Two different humans must ACK
- Separation of duties enforced

Principles:
- NO STATE CHANGE without human ACK
- ACK is immutable record
- Dual ACK for critical decisions (four-eyes)
- I9 compliance: Every decision has accountable human
"""

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Dict, List, Optional


def generate_nonce() -> str:
    """Generate cryptographic nonce for ACK token."""
    return secrets.token_hex(16)


def make_ack_token(
    case_id: str,
    human_id: str,
    action: str,
    nonce: str,
    timestamp: Optional[str] = None
) -> str:
    """
    Create deterministic ACK token.

    In production, this could be replaced by digital signature.

    Args:
        case_id: Case identifier
        human_id: Human actor identifier (email, ID, etc.)
        action: ACK action type
        nonce: Cryptographic nonce
        timestamp: Optional timestamp (uses now if not provided)

    Returns:
        SHA-256 hash token
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()

    data = f"{case_id}|{human_id}|{action}|{nonce}|{timestamp}"
    return hashlib.sha256(data.encode()).hexdigest()


def verify_ack_token(
    token: str,
    case_id: str,
    human_id: str,
    action: str,
    nonce: str,
    timestamp: str
) -> bool:
    """Verify an ACK token is valid."""
    expected = make_ack_token(case_id, human_id, action, nonce, timestamp)
    return secrets.compare_digest(token, expected)


def ack_record(
    case_id: str,
    human_id: str,
    action: str,
    ack_token: str,
    details: Optional[Dict] = None
) -> Dict:
    """
    Create an ACK record for storage.

    Args:
        case_id: Case identifier
        human_id: Human actor identifier
        action: ACK action (acknowledge, decide, close, escalate)
        ack_token: ACK token
        details: Optional additional details

    Returns:
        ACK record dict
    """
    record = {
        "case_id": case_id,
        "human_id": human_id,
        "action": action,
        "ack_token": ack_token,
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }

    if details:
        record["details"] = details

    return record


def validate_ack(
    ack: Dict,
    case_id: str,
    expected_action: str
) -> Dict:
    """
    Validate an ACK record.

    Returns validation result with status and any issues.
    """
    result = {
        "valid": True,
        "issues": []
    }

    # Check case_id matches
    if ack.get("case_id") != case_id:
        result["valid"] = False
        result["issues"].append("Case ID mismatch")

    # Check action matches
    if ack.get("action") != expected_action:
        result["valid"] = False
        result["issues"].append(f"Expected action '{expected_action}', got '{ack.get('action')}'")

    # Check human_id is present
    if not ack.get("human_id"):
        result["valid"] = False
        result["issues"].append("Missing human_id")

    # Check token is present
    if not ack.get("ack_token"):
        result["valid"] = False
        result["issues"].append("Missing ack_token")

    # Check timestamp is present and valid
    ts = ack.get("timestamp_utc")
    if not ts:
        result["valid"] = False
        result["issues"].append("Missing timestamp")
    else:
        try:
            datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            result["valid"] = False
            result["issues"].append("Invalid timestamp format")

    return result


def check_dual_ack(acks: List[Dict], required_action: str) -> Dict:
    """
    Check if dual ACK requirement is satisfied.

    Two different humans must have ACKed the same action.

    Args:
        acks: List of ACK records
        required_action: Action that requires dual ACK

    Returns:
        Dict with satisfied status and actor list
    """
    # Filter ACKs for the required action
    matching_acks = [
        ack for ack in acks
        if ack.get("action") == required_action
    ]

    # Get unique human actors
    actors = set()
    for ack in matching_acks:
        human_id = ack.get("human_id")
        if human_id:
            actors.add(human_id)

    return {
        "required": True,
        "satisfied": len(actors) >= 2,
        "ack_count": len(matching_acks),
        "unique_actors": list(actors),
        "missing": max(0, 2 - len(actors))
    }


def create_decision_ack(
    case_id: str,
    human_id: str,
    decision: str,
    rationale: str,
    overrides_ai: bool = False,
    ai_recommendation: Optional[str] = None
) -> Dict:
    """
    Create a decision ACK with full context.

    This is the primary record of human decision for I9 compliance.

    Args:
        case_id: Case identifier
        human_id: Decision maker identifier
        decision: The decision made (resolve, dismiss, escalate, etc.)
        rationale: Human-provided reasoning
        overrides_ai: Whether this overrides AI recommendation
        ai_recommendation: Original AI recommendation (if any)

    Returns:
        Complete decision ACK record
    """
    nonce = generate_nonce()
    timestamp = datetime.now(timezone.utc).isoformat()

    token = make_ack_token(case_id, human_id, "decide", nonce, timestamp)

    details = {
        "decision": decision,
        "rationale": rationale,
        "overrides_ai": overrides_ai
    }

    if overrides_ai and ai_recommendation:
        details["ai_recommendation"] = ai_recommendation
        details["override_documented"] = True

    return {
        "case_id": case_id,
        "human_id": human_id,
        "action": "decide",
        "ack_token": token,
        "nonce": nonce,
        "timestamp_utc": timestamp,
        "details": details,
        "i9_compliant": True,
        "human_sovereignty_exercised": True
    }


def create_escalation_ack(
    case_id: str,
    human_id: str,
    escalation_reason: str,
    target_role: str
) -> Dict:
    """Create an escalation ACK record."""
    nonce = generate_nonce()
    timestamp = datetime.now(timezone.utc).isoformat()

    token = make_ack_token(case_id, human_id, "escalate", nonce, timestamp)

    return {
        "case_id": case_id,
        "human_id": human_id,
        "action": "escalate",
        "ack_token": token,
        "nonce": nonce,
        "timestamp_utc": timestamp,
        "details": {
            "reason": escalation_reason,
            "target_role": target_role
        }
    }
