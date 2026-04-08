"""
W-SEC-001 Security Sentinel — Schemas
Canonical data structures for security events, incidents, and seals.
"""

from datetime import datetime
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

# Type definitions
Severity = Literal["low", "medium", "high", "critical"]
IncidentStatus = Literal["open", "investigating", "approved", "sealed", "closed"]


class Actor(BaseModel):
    """Observable actor attributes (hashed or raw depending on context)."""
    ip: Optional[str] = None
    ip_hash: Optional[str] = None
    user_id: Optional[str] = None
    did: Optional[str] = None
    session_id: Optional[str] = None
    user_agent: Optional[str] = None
    user_agent_hash: Optional[str] = None


class Target(BaseModel):
    """Target of the security event."""
    service: str
    endpoint: Optional[str] = None
    method: Optional[str] = None
    resource_id: Optional[str] = None


class RequestMeta(BaseModel):
    """Request metadata (hashed for privacy)."""
    request_id: Optional[str] = None
    headers_hash: Optional[str] = None
    body_hash: Optional[str] = None
    query_hash: Optional[str] = None


class Threat(BaseModel):
    """Threat classification."""
    family: str  # abuse, intrusion, exfiltration, tampering
    vector: str  # api_flood, credential_stuffing, injection, etc.
    technique: Optional[str] = None
    indicator_hash: Optional[str] = None


class Evidence(BaseModel):
    """Evidence bundle reference."""
    raw_ref: Optional[str] = None
    excerpt: Optional[str] = None
    attachments: List[str] = Field(default_factory=list)


class Disposition(BaseModel):
    """What happened to the request."""
    blocked: bool = False
    allowed: bool = False
    degraded: bool = False


class SecEvent(BaseModel):
    """
    SEC-EVT — Atomic security event.

    Distinct from ForensicEntry (governance audit).
    This captures operational security signals.
    """
    event_id: str
    timestamp: datetime
    source: str  # originating service
    sensor: str  # detection mechanism
    event_type: str  # rate_limit_exceeded, token_invalid, etc.
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    actor: Actor
    target: Target
    request: Optional[RequestMeta] = None
    threat: Threat
    evidence: Optional[Evidence] = None
    disposition: Optional[Disposition] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class SecIncident(BaseModel):
    """
    SEC-INCIDENT — Correlated security case.

    Groups multiple SEC-EVTs into a single investigable unit.
    """
    incident_id: str
    opened_at: datetime
    updated_at: datetime
    status: IncidentStatus = "open"
    title: str
    summary: str
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    event_count: int
    correlation_key: str
    primary_vector: str
    affected_assets: List[str] = Field(default_factory=list)
    actors: List[Dict[str, Any]] = Field(default_factory=list)
    first_event_id: str
    last_event_id: str
    recommended_action: Optional[str] = None
    maestro_case_id: Optional[str] = None
    ledger_receipt_id: Optional[str] = None
    event_ids: List[str] = Field(default_factory=list)
    resolution: Optional[str] = None
    closed_by: Optional[str] = None
    closed_at: Optional[datetime] = None


class SecSeal(BaseModel):
    """
    SEC-SEAL — Canonical envelope for ledger anchoring.
    """
    seal_type: str = "SEC-SEAL"
    created_at: datetime
    incident_id: str
    canonical_hash: str
    event_count: int
    severity: Severity
    confidence: float
    source_service: str = "w-sec-001"
    payload_version: str = "1.0.0"


# API Response models
class EventResponse(BaseModel):
    ok: bool
    event_id: str
    incident_id: str
    correlated: bool


class BatchEventResponse(BaseModel):
    ok: bool
    accepted: int
    rejected: int
    incident_ids: List[str]


class SealResponse(BaseModel):
    ok: bool
    incident_id: str
    ledger_receipt_id: str
    verify_url: Optional[str] = None


class CloseIncidentRequest(BaseModel):
    resolution: str
    closed_by: str
    notes: Optional[str] = None


class IncidentListResponse(BaseModel):
    items: List[SecIncident]
    count: int
