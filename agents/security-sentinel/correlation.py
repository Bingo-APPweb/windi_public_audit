"""
W-SEC-001 Security Sentinel — Correlation Engine
Groups related security events into incidents.

Two-level correlation:
- Level 1 (Technical): Same actor attacking → single incident
- Level 2 (Behavioral): Multiple actors, same target/pattern → distributed attack
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from config import CORRELATION_WINDOW_SECONDS
from canonicalize import hash_for_indicator
from schemas import SecEvent


# Attack patterns that should be correlated behaviorally (distributed attacks)
DISTRIBUTED_PATTERNS = {
    "api_flood",
    "credential_stuffing",
    "brute_force",
    "rate_limit_exceeded",
    "enumeration",
    "scanning",
}


def get_time_bucket(timestamp: datetime, bucket_minutes: int = 5) -> str:
    """
    Get time bucket for behavioral correlation.
    Groups events into N-minute windows.
    """
    # Round down to nearest bucket
    minutes = (timestamp.hour * 60 + timestamp.minute) // bucket_minutes * bucket_minutes
    hour = minutes // 60
    minute = minutes % 60
    return f"{timestamp.strftime('%Y%m%d')}_{hour:02d}{minute:02d}"


def build_behavioral_key(event: SecEvent) -> str:
    """
    Build behavioral correlation key for distributed attacks.

    Groups by:
    - Target endpoint/service
    - Event type
    - Threat vector
    - Time window (5-minute buckets)

    This aggregates multi-IP attacks into single incidents.
    """
    endpoint = event.target.endpoint or event.target.service
    event_type = event.event_type
    vector = event.threat.vector
    time_bucket = get_time_bucket(event.timestamp)

    return hash_for_indicator(endpoint, event_type, vector, time_bucket)


def build_technical_key(event: SecEvent) -> str:
    """
    Build technical correlation key for targeted attacks.

    Groups by:
    - Actor identifier (DID > session_id > IP)
    - User agent
    - Target endpoint
    - Event type

    This groups repeated attacks from same actor.
    """
    actor_key = (
        event.actor.did
        or event.actor.session_id
        or event.actor.ip_hash
        or event.actor.ip
        or "unknown_actor"
    )

    ua = event.actor.user_agent_hash or event.actor.user_agent or "unknown_ua"
    endpoint = event.target.endpoint or event.target.service
    event_type = event.event_type

    return hash_for_indicator(actor_key, ua, endpoint, event_type)


def is_distributed_pattern(event: SecEvent) -> bool:
    """
    Check if event type indicates a potentially distributed attack.
    """
    return (
        event.threat.vector in DISTRIBUTED_PATTERNS
        or event.event_type in DISTRIBUTED_PATTERNS
    )


def build_correlation_key(event: SecEvent) -> Tuple[str, str]:
    """
    Build correlation key from event attributes.

    Returns:
        Tuple of (primary_key, key_type)
        - key_type: "behavioral" for distributed attacks, "technical" for targeted

    Strategy:
    - Distributed attack patterns → behavioral key (groups multi-IP)
    - Targeted attacks → technical key (groups same actor)
    """
    if is_distributed_pattern(event):
        return build_behavioral_key(event), "behavioral"
    else:
        return build_technical_key(event), "technical"


def build_actor_fingerprint(event: SecEvent) -> str:
    """
    Build actor fingerprint for tracking across incidents.

    Less specific than correlation key — identifies the actor,
    not the specific attack pattern.
    """
    actor_key = (
        event.actor.did
        or event.actor.session_id
        or event.actor.ip_hash
        or event.actor.ip
        or "unknown"
    )

    ua = event.actor.user_agent_hash or event.actor.user_agent or "unknown"

    return hash_for_indicator(actor_key, ua)


def within_correlation_window(
    old_timestamp: datetime,
    new_timestamp: datetime,
    window_seconds: Optional[int] = None
) -> bool:
    """
    Check if two events are within the correlation window.

    Events outside the window start new incidents.
    """
    window = window_seconds or CORRELATION_WINDOW_SECONDS
    delta = abs((new_timestamp - old_timestamp).total_seconds())
    return delta <= window


def should_merge_events(
    existing_timestamp: datetime,
    new_event: SecEvent,
    correlation_key: str,
    existing_key: str
) -> bool:
    """
    Determine if a new event should merge into an existing incident.

    Conditions:
    1. Same correlation key
    2. Within time window
    """
    if correlation_key != existing_key:
        return False

    return within_correlation_window(existing_timestamp, new_event.timestamp)


def extract_unique_actors(events: list) -> list:
    """
    Extract unique actors from a list of events.

    Returns list of actor dictionaries with identifying information.
    """
    seen = set()
    actors = []

    for event in events:
        fingerprint = build_actor_fingerprint(event)
        if fingerprint not in seen:
            seen.add(fingerprint)
            actors.append({
                "ip": event.actor.ip,
                "ip_hash": event.actor.ip_hash,
                "did": event.actor.did,
                "session_id": event.actor.session_id,
                "fingerprint": fingerprint,
            })

    return actors
