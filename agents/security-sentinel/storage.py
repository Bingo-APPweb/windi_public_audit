"""
W-SEC-001 Security Sentinel — Storage
MVP: In-memory storage. Phase B: SQLite.
"""

from typing import Dict, List, Optional
from datetime import datetime
from schemas import SecEvent, SecIncident


class SecurityStorage:
    """
    In-memory storage for MVP.

    Thread-safe operations would be needed for production.
    SQLite migration planned for Phase B.
    """

    def __init__(self):
        self.events: Dict[str, SecEvent] = {}
        self.incidents: Dict[str, SecIncident] = {}
        self.correlation_index: Dict[str, str] = {}  # correlation_key -> incident_id
        self.event_to_incident: Dict[str, str] = {}  # event_id -> incident_id

    def store_event(self, event: SecEvent) -> None:
        """Store a security event."""
        self.events[event.event_id] = event

    def get_event(self, event_id: str) -> Optional[SecEvent]:
        """Retrieve a security event."""
        return self.events.get(event_id)

    def store_incident(self, incident: SecIncident) -> None:
        """Store or update an incident."""
        self.incidents[incident.incident_id] = incident

    def get_incident(self, incident_id: str) -> Optional[SecIncident]:
        """Retrieve an incident."""
        return self.incidents.get(incident_id)

    def get_incident_by_correlation_key(self, key: str) -> Optional[SecIncident]:
        """Find incident by correlation key."""
        incident_id = self.correlation_index.get(key)
        if incident_id:
            return self.incidents.get(incident_id)
        return None

    def set_correlation_index(self, key: str, incident_id: str) -> None:
        """Map correlation key to incident."""
        self.correlation_index[key] = incident_id

    def link_event_to_incident(self, event_id: str, incident_id: str) -> None:
        """Track which incident an event belongs to."""
        self.event_to_incident[event_id] = incident_id

    def list_incidents(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50
    ) -> List[SecIncident]:
        """List incidents with optional filters."""
        items = list(self.incidents.values())

        if status:
            items = [x for x in items if x.status == status]
        if severity:
            items = [x for x in items if x.severity == severity]

        # Sort by updated_at descending
        items = sorted(items, key=lambda x: x.updated_at, reverse=True)

        return items[:limit]

    def get_events_for_incident(self, incident_id: str) -> List[SecEvent]:
        """Get all events for an incident."""
        incident = self.incidents.get(incident_id)
        if not incident:
            return []

        return [
            self.events[eid]
            for eid in incident.event_ids
            if eid in self.events
        ]

    def list_events(self, limit: int = 30) -> List[SecEvent]:
        """List most recent events for replay visualization."""
        items = list(self.events.values())
        # Sort by timestamp descending
        items = sorted(items, key=lambda x: x.timestamp, reverse=True)
        return items[:limit]

    def stats(self) -> Dict[str, int]:
        """Storage statistics."""
        return {
            "events": len(self.events),
            "incidents": len(self.incidents),
            "correlation_keys": len(self.correlation_index),
        }


# Global storage instance (MVP)
storage = SecurityStorage()
