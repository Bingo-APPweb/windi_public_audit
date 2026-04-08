"""
W-SEC-001 Security Sentinel — Sensor Helpers
Factory functions for creating security events from various sources.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from schemas import SecEvent, Actor, Target, Threat, RequestMeta, Evidence, Disposition


def make_sec_event(
    *,
    source: str,
    sensor: str,
    event_type: str,
    severity: str,
    confidence: float,
    # Actor
    ip: Optional[str] = None,
    ip_hash: Optional[str] = None,
    user_id: Optional[str] = None,
    did: Optional[str] = None,
    session_id: Optional[str] = None,
    user_agent: Optional[str] = None,
    user_agent_hash: Optional[str] = None,
    # Target
    service: str,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    resource_id: Optional[str] = None,
    # Threat
    family: str,
    vector: str,
    technique: Optional[str] = None,
    # Request
    request_id: Optional[str] = None,
    headers_hash: Optional[str] = None,
    body_hash: Optional[str] = None,
    query_hash: Optional[str] = None,
    # Evidence
    excerpt: Optional[str] = None,
    raw_ref: Optional[str] = None,
    # Disposition
    blocked: bool = False,
    allowed: bool = False,
    degraded: bool = False,
    # Meta
    environment: str = "production",
    tags: Optional[list] = None,
) -> SecEvent:
    """
    Factory function to create a SEC-EVT from sensor data.

    Usage in hooks:

        from sensors import make_sec_event

        evt = make_sec_event(
            source="constitutional-agent",
            sensor="rate_limiter",
            event_type="rate_limit_exceeded",
            severity="medium",
            confidence=0.82,
            ip=client_ip,
            session_id=session_id,
            user_agent=user_agent,
            service="w-gateway-001",
            endpoint="/gateway/call",
            method="POST",
            family="abuse",
            vector="api_flood",
            excerpt="Rate limit exceeded on critical endpoint"
        )

        # Send to W-SEC-001
        await send_to_sentinel(evt)
    """
    return SecEvent(
        event_id=f"sec_evt_{uuid4().hex[:12]}",
        timestamp=datetime.now(timezone.utc),
        source=source,
        sensor=sensor,
        event_type=event_type,
        severity=severity,
        confidence=confidence,
        actor=Actor(
            ip=ip,
            ip_hash=ip_hash,
            user_id=user_id,
            did=did,
            session_id=session_id,
            user_agent=user_agent,
            user_agent_hash=user_agent_hash,
        ),
        target=Target(
            service=service,
            endpoint=endpoint,
            method=method,
            resource_id=resource_id,
        ),
        request=RequestMeta(
            request_id=request_id,
            headers_hash=headers_hash,
            body_hash=body_hash,
            query_hash=query_hash,
        ) if any([request_id, headers_hash, body_hash, query_hash]) else None,
        threat=Threat(
            family=family,
            vector=vector,
            technique=technique,
        ),
        evidence=Evidence(
            excerpt=excerpt,
            raw_ref=raw_ref,
        ) if excerpt or raw_ref else None,
        disposition=Disposition(
            blocked=blocked,
            allowed=allowed,
            degraded=degraded,
        ),
        meta={
            "environment": environment,
            "version": "1.0.0",
            "tags": tags or [],
        },
    )


# Pre-configured event creators for common scenarios

def rate_limit_event(
    *,
    ip: str,
    session_id: Optional[str],
    user_agent: str,
    service: str,
    endpoint: str,
    method: str,
    count: int,
    window_seconds: int,
) -> SecEvent:
    """Create event for rate limit exceeded."""
    return make_sec_event(
        source=service,
        sensor="rate_limiter",
        event_type="rate_limit_exceeded",
        severity="medium",
        confidence=0.85,
        ip=ip,
        session_id=session_id,
        user_agent=user_agent,
        service=service,
        endpoint=endpoint,
        method=method,
        family="abuse",
        vector="api_flood",
        technique="burst_replay",
        excerpt=f"Rate limit exceeded: {count} requests in {window_seconds}s",
        blocked=True,
    )


def token_invalid_event(
    *,
    ip: str,
    user_agent: str,
    service: str,
    endpoint: str,
    reason: str,
) -> SecEvent:
    """Create event for invalid token."""
    return make_sec_event(
        source=service,
        sensor="token_validator",
        event_type="token_invalid",
        severity="low",
        confidence=0.90,
        ip=ip,
        user_agent=user_agent,
        service=service,
        endpoint=endpoint,
        method="POST",
        family="intrusion",
        vector="credential_stuffing",
        excerpt=f"Token validation failed: {reason}",
        blocked=True,
    )


def token_replay_event(
    *,
    ip: str,
    session_id: str,
    user_agent: str,
    service: str,
    endpoint: str,
) -> SecEvent:
    """Create event for token replay detection."""
    return make_sec_event(
        source=service,
        sensor="token_validator",
        event_type="token_replay_detected",
        severity="high",
        confidence=0.95,
        ip=ip,
        session_id=session_id,
        user_agent=user_agent,
        service=service,
        endpoint=endpoint,
        method="POST",
        family="intrusion",
        vector="token_replay",
        technique="session_hijack_attempt",
        excerpt="Token replay detected — possible session hijack",
        blocked=True,
    )


def constitutional_violation_event(
    *,
    ip: str,
    did: Optional[str],
    session_id: Optional[str],
    service: str,
    endpoint: str,
    invariant: str,
    action_attempted: str,
) -> SecEvent:
    """Create event for constitutional invariant violation attempt."""
    return make_sec_event(
        source=service,
        sensor="constitutional_gate",
        event_type="constitutional_violation_attempt",
        severity="high",
        confidence=0.92,
        ip=ip,
        did=did,
        session_id=session_id,
        user_agent="unknown",
        service=service,
        endpoint=endpoint,
        method="POST",
        family="tampering",
        vector="invariant_bypass",
        technique=f"attempted_violation_{invariant}",
        excerpt=f"Attempted violation of {invariant}: {action_attempted}",
        blocked=True,
    )


def device_binding_mismatch_event(
    *,
    ip: str,
    did: str,
    session_id: str,
    user_agent: str,
    expected_device_hash: str,
    actual_device_hash: str,
) -> SecEvent:
    """Create event for device binding mismatch."""
    return make_sec_event(
        source="sovereign_session",
        sensor="device_binding",
        event_type="device_binding_mismatch",
        severity="medium",
        confidence=0.88,
        ip=ip,
        did=did,
        session_id=session_id,
        user_agent=user_agent,
        service="w-session-001",
        endpoint="/session/verify",
        method="GET",
        family="intrusion",
        vector="session_hijack",
        technique="device_spoof",
        excerpt=f"Device binding mismatch: expected {expected_device_hash[:8]}..., got {actual_device_hash[:8]}...",
        blocked=True,
    )


def merkle_integrity_event(
    *,
    service: str,
    expected_root: str,
    actual_root: str,
) -> SecEvent:
    """Create event for Merkle tree integrity failure."""
    return make_sec_event(
        source=service,
        sensor="integrity_watchdog",
        event_type="merkle_integrity_failed",
        severity="critical",
        confidence=0.99,
        ip="internal",
        service=service,
        endpoint="/internal/integrity",
        method="GET",
        family="tampering",
        vector="ledger_tamper",
        technique="merkle_manipulation",
        excerpt=f"Merkle root mismatch: expected {expected_root[:16]}..., got {actual_root[:16]}...",
        blocked=False,  # This is detection, not prevention
    )
