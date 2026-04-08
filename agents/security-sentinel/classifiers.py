"""
W-SEC-001 Security Sentinel — Classifiers
Severity escalation and action recommendation logic.
"""

from typing import Optional
from config import (
    CRITICAL_ENDPOINTS,
    HIGH_PRIORITY_EVENT_TYPES,
    ESCALATION_THRESHOLD,
    CRITICAL_THRESHOLD,
)
from schemas import SecEvent, Severity


SEVERITY_ORDER = ["low", "medium", "high", "critical"]


def escalate_severity(
    base: Severity,
    event_count: int,
    endpoint: Optional[str] = None,
    event_type: Optional[str] = None
) -> Severity:
    """
    Escalate severity based on:
    - Event count thresholds
    - Critical endpoint targeting
    - High-priority event types
    """
    idx = SEVERITY_ORDER.index(base)

    # Escalate for high event count
    if event_count >= CRITICAL_THRESHOLD:
        idx = min(idx + 2, len(SEVERITY_ORDER) - 1)
    elif event_count >= ESCALATION_THRESHOLD:
        idx = min(idx + 1, len(SEVERITY_ORDER) - 1)

    # Escalate for critical endpoints
    if endpoint and endpoint in CRITICAL_ENDPOINTS:
        idx = min(idx + 1, len(SEVERITY_ORDER) - 1)

    # Escalate for high-priority event types
    if event_type and event_type in HIGH_PRIORITY_EVENT_TYPES:
        idx = min(idx + 1, len(SEVERITY_ORDER) - 1)

    return SEVERITY_ORDER[idx]


def recommended_action(event: SecEvent, event_count: int) -> str:
    """
    Recommend response action based on event characteristics.

    Actions are recommendations — I9 requires human approval for execution.
    """
    # Immediate block recommendations
    if event.event_type in {"token_replay_detected", "seal_forgery_attempt", "ledger_tamper_attempt"}:
        return "immediate_block_and_escalate"

    if event.event_type in {"forbidden_endpoint_access", "constitutional_violation_attempt"}:
        return "temporary_block_and_review"

    # Count-based recommendations
    if event_count >= CRITICAL_THRESHOLD:
        return "block_and_seal"

    if event_count >= ESCALATION_THRESHOLD:
        return "throttle_and_investigate"

    if event_count >= 10:
        return "monitor_closely"

    return "observe"


def compute_confidence(
    base_confidence: float,
    event_count: int,
    multi_sensor: bool = False
) -> float:
    """
    Adjust confidence based on corroborating signals.

    More events = higher confidence.
    Multiple sensors confirming = +0.1.
    """
    confidence = base_confidence

    # Boost for multiple events
    if event_count >= 10:
        confidence += 0.05
    if event_count >= 25:
        confidence += 0.05
    if event_count >= 100:
        confidence += 0.05

    # Boost for multi-sensor confirmation
    if multi_sensor:
        confidence += 0.1

    return min(1.0, confidence)


def classify_threat_family(event_type: str) -> str:
    """
    Map event type to threat family.
    """
    abuse_types = {
        "rate_limit_exceeded",
        "api_flood",
        "burst_replay",
    }

    intrusion_types = {
        "token_invalid",
        "token_replay_detected",
        "forbidden_endpoint_access",
        "device_binding_mismatch",
        "credential_stuffing",
        "bruteforce_auth",
    }

    tampering_types = {
        "merkle_integrity_failed",
        "seal_forgery_attempt",
        "ledger_tamper_attempt",
        "constitutional_violation_attempt",
        "hash_manipulation",
    }

    injection_types = {
        "input_validation_failed",
        "path_traversal_attempt",
        "payload_injection",
        "sql_injection_attempt",
        "xss_attempt",
    }

    if event_type in abuse_types:
        return "abuse"
    if event_type in intrusion_types:
        return "intrusion"
    if event_type in tampering_types:
        return "tampering"
    if event_type in injection_types:
        return "injection"

    return "unknown"
