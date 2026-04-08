"""
W-SEC-001 Security Sentinel — Core Engine
Event ingestion, correlation, and incident management.
"""

from datetime import datetime, timezone
from typing import Optional, Tuple
from uuid import uuid4

from schemas import SecEvent, SecIncident
from storage import storage
from correlation import (
    build_correlation_key,
    build_actor_fingerprint,
    within_correlation_window,
)
from classifiers import (
    escalate_severity,
    recommended_action,
    compute_confidence,
)
from config import CORRELATION_WINDOW_SECONDS


def generate_incident_id() -> str:
    """Generate unique incident ID."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    suffix = uuid4().hex[:6]
    return f"sec_inc_{ts}_{suffix}"


class IngestResult:
    """Result of event ingestion with metadata for notifications."""
    def __init__(
        self,
        incident: SecIncident,
        was_correlated: bool,
        is_new: bool = False,
        was_escalated: bool = False,
        is_distributed: bool = False,
        previous_severity: Optional[str] = None,
    ):
        self.incident = incident
        self.was_correlated = was_correlated
        self.is_new = is_new
        self.was_escalated = was_escalated
        self.is_distributed = is_distributed
        self.previous_severity = previous_severity


async def ingest_event(event: SecEvent) -> Tuple[SecIncident, bool, Optional[IngestResult]]:
    """
    Ingest a security event and correlate into incident.

    Two-level correlation:
    - Behavioral: Distributed attacks (multi-IP) → grouped by pattern
    - Technical: Targeted attacks → grouped by actor

    Returns:
        Tuple of (incident, was_correlated, ingest_result)
        - was_correlated=True if event merged into existing incident
        - was_correlated=False if new incident created
        - ingest_result contains metadata for notification decisions
    """
    # Store the event
    storage.store_event(event)

    # Build correlation key (now returns tuple)
    key, key_type = build_correlation_key(event)

    # Check for existing incident
    existing = storage.get_incident_by_correlation_key(key)

    if existing and within_correlation_window(existing.updated_at, event.timestamp):
        # Track previous state for escalation detection
        previous_severity = existing.severity
        previous_actor_count = len(existing.actors)

        # Merge into existing incident
        incident = merge_event_into_incident(existing, event, key_type)
        storage.store_incident(incident)
        storage.link_event_to_incident(event.event_id, incident.incident_id)

        # Detect escalation
        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        was_escalated = severity_order.get(incident.severity, 0) > severity_order.get(previous_severity, 0)

        # Detect new distributed attack (went from 1 to >1 actors)
        is_distributed = (
            key_type == "behavioral" and
            previous_actor_count == 1 and
            len(incident.actors) > 1
        )

        result = IngestResult(
            incident=incident,
            was_correlated=True,
            is_new=False,
            was_escalated=was_escalated,
            is_distributed=is_distributed,
            previous_severity=previous_severity,
        )

        return incident, True, result

    # Create new incident
    incident = create_incident_from_event(event, key, key_type)
    storage.store_incident(incident)
    storage.set_correlation_index(key, incident.incident_id)
    storage.link_event_to_incident(event.event_id, incident.incident_id)

    result = IngestResult(
        incident=incident,
        was_correlated=False,
        is_new=True,
        was_escalated=False,
        is_distributed=(key_type == "behavioral"),
        previous_severity=None,
    )

    return incident, False, result


def merge_event_into_incident(
    incident: SecIncident,
    event: SecEvent,
    key_type: str = "technical"
) -> SecIncident:
    """
    Merge a new event into an existing incident.

    Updates:
    - Timestamps
    - Event count
    - Severity (may escalate)
    - Confidence
    - Recommended action
    - Title (for distributed attacks with multiple actors)
    """
    incident.updated_at = event.timestamp
    incident.event_count += 1
    incident.last_event_id = event.event_id
    incident.event_ids.append(event.event_id)

    # Escalate severity if needed
    incident.severity = escalate_severity(
        incident.severity,
        incident.event_count,
        event.target.endpoint,
        event.event_type
    )

    # Update confidence
    incident.confidence = compute_confidence(
        max(incident.confidence, event.confidence),
        incident.event_count
    )

    # Update recommended action
    incident.recommended_action = recommended_action(event, incident.event_count)

    # Update actors if new actor
    actor_fp = build_actor_fingerprint(event)
    existing_fps = [a.get("fingerprint") for a in incident.actors]
    if actor_fp not in existing_fps:
        incident.actors.append({
            "ip": event.actor.ip,
            "ip_hash": event.actor.ip_hash,
            "did": event.actor.did,
            "session_id": event.actor.session_id,
            "fingerprint": actor_fp,
        })

    # Update affected assets
    if event.target.service not in incident.affected_assets:
        incident.affected_assets.append(event.target.service)

    # Update title for distributed attacks showing actor count
    if key_type == "behavioral" and len(incident.actors) > 1:
        endpoint = event.target.endpoint or event.target.service
        incident.title = f"DISTRIBUTED: {event.event_type} against {endpoint} ({len(incident.actors)} sources)"
        # Update summary with pattern analysis
        incident.summary = (
            f"Distributed attack pattern detected. "
            f"{incident.event_count} events from {len(incident.actors)} unique sources. "
            f"Vector: {event.threat.vector}. Sensor: {event.sensor}."
        )

    return incident


def create_incident_from_event(
    event: SecEvent,
    correlation_key: str,
    key_type: str = "technical"
) -> SecIncident:
    """
    Create a new incident from a security event.

    key_type determines labeling:
    - "behavioral": Potential distributed attack
    - "technical": Targeted attack from single actor
    """
    actor_fp = build_actor_fingerprint(event)
    endpoint = event.target.endpoint or event.target.service

    # Title and summary based on correlation type
    if key_type == "behavioral":
        title = f"{event.event_type} against {endpoint}"
        summary = (
            f"Potential distributed attack pattern. "
            f"Vector: {event.threat.vector}. Sensor: {event.sensor}."
        )
    else:
        title = f"{event.event_type} against {endpoint}"
        summary = f"Security event detected by {event.sensor} sensor from {event.source}"

    return SecIncident(
        incident_id=generate_incident_id(),
        opened_at=event.timestamp,
        updated_at=event.timestamp,
        status="open",
        title=title,
        summary=summary,
        severity=event.severity,
        confidence=event.confidence,
        event_count=1,
        correlation_key=correlation_key,
        primary_vector=event.threat.vector,
        affected_assets=[event.target.service],
        actors=[{
            "ip": event.actor.ip,
            "ip_hash": event.actor.ip_hash,
            "did": event.actor.did,
            "session_id": event.actor.session_id,
            "fingerprint": actor_fp,
        }],
        first_event_id=event.event_id,
        last_event_id=event.event_id,
        recommended_action=recommended_action(event, 1),
        event_ids=[event.event_id],
    )


async def close_incident(
    incident_id: str,
    resolution: str,
    closed_by: str,
    notes: Optional[str] = None
) -> Optional[SecIncident]:
    """
    Close an incident with resolution.
    """
    incident = storage.get_incident(incident_id)
    if not incident:
        return None

    incident.status = "closed"
    incident.resolution = resolution
    incident.closed_by = closed_by
    incident.closed_at = datetime.now(timezone.utc)
    incident.updated_at = datetime.now(timezone.utc)

    if notes:
        incident.summary = f"{incident.summary} | Resolution: {resolution}. {notes}"
    else:
        incident.summary = f"{incident.summary} | Resolution: {resolution}"

    storage.store_incident(incident)
    return incident


async def seal_incident(incident_id: str) -> Optional[SecIncident]:
    """
    Mark incident as sealed (ready for ledger anchoring).
    """
    incident = storage.get_incident(incident_id)
    if not incident:
        return None

    incident.status = "sealed"
    incident.updated_at = datetime.now(timezone.utc)

    storage.store_incident(incident)
    return incident
