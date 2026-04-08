"""
W-SEC-001 Client — Universal Security Event Emitter
=====================================================
Fire-and-forget, non-blocking, fail-silent.

Usage:
    from shared.sec_client import emit_security_event

    emit_security_event({
        "event_id": "sec_evt_xxx",
        "timestamp": "2026-04-08T12:00:00Z",
        "source": "my-service",
        ...
    })

Guarantees:
    - Never blocks the main request
    - Timeout: 2 seconds max
    - Silent failure (W-SEC down = no impact)
    - Fire-and-forget pattern
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from uuid import uuid4

logger = logging.getLogger("w-sec-client")

SEC_URL = "http://127.0.0.1:8144/sec/events"
SEC_TIMEOUT = 2.0


def _get_timestamp() -> str:
    """ISO timestamp in UTC."""
    return datetime.now(timezone.utc).isoformat()


def _generate_event_id() -> str:
    """Generate unique event ID."""
    return f"sec_evt_{uuid4().hex[:12]}"


async def _send_async(event: Dict[str, Any]) -> None:
    """
    Async send to W-SEC-001.
    Silent on failure.
    """
    try:
        import httpx
        async with httpx.AsyncClient(timeout=SEC_TIMEOUT) as client:
            await client.post(SEC_URL, json=event)
    except Exception as e:
        logger.debug(f"W-SEC unreachable: {e}")


def _send_sync(event: Dict[str, Any]) -> None:
    """
    Sync send to W-SEC-001.
    Used when no event loop is running.
    """
    try:
        import httpx
        with httpx.Client(timeout=SEC_TIMEOUT) as client:
            client.post(SEC_URL, json=event)
    except Exception as e:
        logger.debug(f"W-SEC unreachable: {e}")


def emit_security_event(event: Dict[str, Any]) -> None:
    """
    Fire-and-forget security event emitter.

    NEVER breaks the main request flow.
    NEVER raises exceptions.
    NEVER blocks longer than 2 seconds.

    Args:
        event: SEC-EVT compliant dictionary
    """
    try:
        import asyncio

        # Ensure required fields
        if "event_id" not in event:
            event["event_id"] = _generate_event_id()
        if "timestamp" not in event:
            event["timestamp"] = _get_timestamp()

        # Try async first (non-blocking)
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context — create task
            loop.create_task(_send_async(event))
        except RuntimeError:
            # No running loop — use sync in thread
            import threading
            thread = threading.Thread(target=_send_sync, args=(event,), daemon=True)
            thread.start()

    except Exception as e:
        # NEVER propagate exceptions
        logger.debug(f"W-SEC emit failed: {e}")


def make_event(
    *,
    source: str,
    sensor: str,
    event_type: str,
    severity: str,
    confidence: float,
    # Actor
    ip: Optional[str] = None,
    session_id: Optional[str] = None,
    user_agent: Optional[str] = None,
    did: Optional[str] = None,
    # Target
    service: str,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    # Threat
    family: str,
    vector: str,
    # Evidence
    excerpt: Optional[str] = None,
    # Disposition
    blocked: bool = False,
) -> Dict[str, Any]:
    """
    Factory function to create SEC-EVT compliant event.

    Returns a dictionary ready for emit_security_event().
    """
    return {
        "event_id": _generate_event_id(),
        "timestamp": _get_timestamp(),
        "source": source,
        "sensor": sensor,
        "event_type": event_type,
        "severity": severity,
        "confidence": confidence,
        "actor": {
            "ip": ip,
            "session_id": session_id,
            "user_agent": user_agent,
            "did": did,
        },
        "target": {
            "service": service,
            "endpoint": endpoint,
            "method": method,
        },
        "threat": {
            "family": family,
            "vector": vector,
        },
        "evidence": {
            "excerpt": excerpt,
        } if excerpt else None,
        "disposition": {
            "blocked": blocked,
            "allowed": not blocked,
            "degraded": False,
        },
        "meta": {
            "environment": "production",
            "version": "1.0.0",
        },
    }


# Convenience functions for common event types

def emit_rate_limit_exceeded(
    *,
    ip: str,
    session_id: Optional[str] = None,
    user_agent: Optional[str] = None,
    service: str,
    endpoint: str,
    method: str = "POST",
    count: int = 0,
    window_seconds: int = 1,
) -> None:
    """Emit rate limit exceeded event."""
    event = make_event(
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
        excerpt=f"Rate limit exceeded: {count} requests in {window_seconds}s on {endpoint}",
        blocked=True,
    )
    emit_security_event(event)


def emit_token_invalid(
    *,
    ip: str,
    user_agent: Optional[str] = None,
    service: str,
    endpoint: str,
    error_code: str,
) -> None:
    """Emit token validation failure event."""
    # Determine severity based on error type
    high_severity_codes = {"invalid_signature", "corrupt_payload"}
    severity = "high" if error_code in high_severity_codes else "low"

    event = make_event(
        source=service,
        sensor="token_validator",
        event_type="token_invalid",
        severity=severity,
        confidence=0.90,
        ip=ip,
        user_agent=user_agent,
        service=service,
        endpoint=endpoint,
        method="POST",
        family="intrusion",
        vector="credential_stuffing",
        excerpt=f"Token validation failed: {error_code}",
        blocked=True,
    )
    emit_security_event(event)


def emit_constitutional_violation(
    *,
    ip: Optional[str] = None,
    session_id: Optional[str] = None,
    did: Optional[str] = None,
    service: str,
    operation: str,
    invariant: str,
    error_message: str,
) -> None:
    """Emit constitutional invariant violation attempt."""
    event = make_event(
        source=service,
        sensor="constitutional_gate",
        event_type="constitutional_violation_attempt",
        severity="high",
        confidence=0.95,
        ip=ip,
        session_id=session_id,
        did=did,
        service=service,
        endpoint=operation,
        method="INTERNAL",
        family="governance",
        vector="invariant_bypass",
        excerpt=f"Attempted violation of {invariant}: {error_message}",
        blocked=True,
    )
    emit_security_event(event)


def emit_device_binding_mismatch(
    *,
    ip: str,
    session_id: str,
    did: str,
    user_agent: Optional[str] = None,
    service: str,
) -> None:
    """Emit device binding mismatch event."""
    event = make_event(
        source=service,
        sensor="device_binding",
        event_type="device_binding_mismatch",
        severity="medium",
        confidence=0.88,
        ip=ip,
        session_id=session_id,
        did=did,
        user_agent=user_agent,
        service=service,
        endpoint="/session/verify",
        method="GET",
        family="intrusion",
        vector="session_hijack",
        excerpt="Device fingerprint mismatch detected",
        blocked=True,
    )
    emit_security_event(event)
