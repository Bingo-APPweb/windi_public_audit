"""
W-SEC-001 Security Sentinel — FastAPI Application
Port: 8144

Endpoints:
- POST /sec/events          — Ingest security event
- POST /sec/events/batch    — Ingest batch of events
- GET  /sec/incidents       — List incidents
- GET  /sec/incidents/{id}  — Get incident details
- POST /sec/incidents/{id}/seal  — Seal and anchor to ledger
- POST /sec/incidents/{id}/close — Close incident
- GET  /health              — Health check
- GET  /metrics             — Basic metrics
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
import os

from config import SERVICE_NAME, SERVICE_VERSION, SERVICE_PORT
from schemas import (
    SecEvent,
    SecIncident,
    EventResponse,
    BatchEventResponse,
    SealResponse,
    CloseIncidentRequest,
    IncidentListResponse,
)
from storage import storage
from security_sentinel import ingest_event, close_incident, seal_incident
from canonicalize import canonical_json, sha256_hex
from ledger_client import anchor_security_incident, build_ledger_payload, verify_ledger_health
from geo_resolver import enrich_incidents_geo, get_cached_geo_points


app = FastAPI(
    title="W-SEC-001 Security Sentinel",
    description="Security Evidence Architecture for WINDI Core",
    version=SERVICE_VERSION,
)

# CORS for internal services
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Background task for geo enrichment
geo_enrichment_task = None


async def geo_enrichment_loop():
    """Background task to periodically enrich IPs with geo data."""
    while True:
        try:
            incidents = storage.list_incidents(limit=50)
            if incidents:
                await enrich_incidents_geo(incidents)
        except Exception:
            pass
        await asyncio.sleep(10)  # Run every 10 seconds


@app.on_event("startup")
async def startup_event():
    """Start background geo enrichment task."""
    global geo_enrichment_task
    geo_enrichment_task = asyncio.create_task(geo_enrichment_loop())


@app.on_event("shutdown")
async def shutdown_event():
    """Cancel background task on shutdown."""
    global geo_enrichment_task
    if geo_enrichment_task:
        geo_enrichment_task.cancel()


@app.get("/health")
async def health():
    """Health check endpoint."""
    ledger_ok = await verify_ledger_health()
    stats = storage.stats()

    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "port": SERVICE_PORT,
        "time": datetime.now(timezone.utc).isoformat(),
        "ledger_connected": ledger_ok,
        "storage": stats,
    }


@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint."""
    stats = storage.stats()
    incidents = storage.list_incidents(limit=1000)

    by_severity = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    by_status = {"open": 0, "investigating": 0, "sealed": 0, "closed": 0}

    for inc in incidents:
        by_severity[inc.severity] = by_severity.get(inc.severity, 0) + 1
        by_status[inc.status] = by_status.get(inc.status, 0) + 1

    return {
        "service": SERVICE_NAME,
        "events_total": stats["events"],
        "incidents_total": stats["incidents"],
        "incidents_by_severity": by_severity,
        "incidents_by_status": by_status,
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/sec/events", response_model=EventResponse)
async def post_event(event: SecEvent):
    """
    Ingest a single security event.

    The event will be correlated into an existing incident
    or create a new incident.
    """
    incident, was_correlated = await ingest_event(event)

    return EventResponse(
        ok=True,
        event_id=event.event_id,
        incident_id=incident.incident_id,
        correlated=was_correlated,
    )


@app.post("/sec/events/batch", response_model=BatchEventResponse)
async def post_events_batch(events: List[SecEvent]):
    """
    Ingest a batch of security events.

    Events are processed sequentially for proper correlation.
    """
    accepted = 0
    rejected = 0
    incident_ids = set()

    for event in events:
        try:
            incident, _ = await ingest_event(event)
            incident_ids.add(incident.incident_id)
            accepted += 1
        except Exception:
            rejected += 1

    return BatchEventResponse(
        ok=True,
        accepted=accepted,
        rejected=rejected,
        incident_ids=list(incident_ids),
    )


@app.get("/sec/incidents", response_model=IncidentListResponse)
async def list_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50
):
    """
    List security incidents with optional filters.
    """
    items = storage.list_incidents(status=status, severity=severity, limit=limit)

    return IncidentListResponse(
        items=items,
        count=len(items),
    )


@app.get("/sec/incidents/{incident_id}", response_model=SecIncident)
async def get_incident(incident_id: str):
    """
    Get detailed information about an incident.
    """
    incident = storage.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    return incident


@app.get("/sec/incidents/{incident_id}/events")
async def get_incident_events(incident_id: str):
    """
    Get all events associated with an incident.
    """
    incident = storage.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    events = storage.get_events_for_incident(incident_id)

    return {
        "incident_id": incident_id,
        "events": events,
        "count": len(events),
    }


@app.post("/sec/incidents/{incident_id}/seal", response_model=SealResponse)
async def seal_incident_endpoint(incident_id: str):
    """
    Seal an incident and anchor to Forensic Ledger.

    This creates a permanent, verifiable record of the security incident.
    """
    incident = storage.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if incident.status == "sealed":
        raise HTTPException(
            status_code=400,
            detail=f"Incident already sealed. Receipt: {incident.ledger_receipt_id}"
        )

    # Build canonical payload for hashing
    now = datetime.now(timezone.utc)
    payload_data = {
        "type": "security_incident",
        "incident_id": incident.incident_id,
        "severity": incident.severity,
        "confidence": incident.confidence,
        "event_count": incident.event_count,
        "summary": incident.summary,
        "primary_vector": incident.primary_vector,
        "affected_assets": incident.affected_assets,
        "created_at": now.isoformat(),
    }

    # Compute canonical hash
    canonical = canonical_json(payload_data)
    canonical_hash = sha256_hex(canonical)

    # Build ledger payload
    ledger_payload = build_ledger_payload(
        incident_id=incident.incident_id,
        canonical_hash=canonical_hash,
        severity=incident.severity,
        confidence=incident.confidence,
        event_count=incident.event_count,
        summary=incident.summary,
        created_at=now.isoformat(),
    )

    # Anchor to ledger
    try:
        ledger_resp = await anchor_security_incident(ledger_payload)
        receipt_id = ledger_resp.get("receipt_id", f"WINDI-SEC-{now.strftime('%Y%m%d%H%M%S')}")
    except Exception as e:
        # Graceful degradation — mark sealed locally even if ledger unavailable
        receipt_id = f"WINDI-SEC-LOCAL-{now.strftime('%Y%m%d%H%M%S')}-{canonical_hash[:8].upper()}"

    # Update incident
    incident.status = "sealed"
    incident.ledger_receipt_id = receipt_id
    incident.updated_at = now
    storage.store_incident(incident)

    return SealResponse(
        ok=True,
        incident_id=incident.incident_id,
        ledger_receipt_id=receipt_id,
        verify_url=f"https://windi-domain.com/verify-public/?id={receipt_id}",
    )


@app.post("/sec/incidents/{incident_id}/close")
async def close_incident_endpoint(incident_id: str, req: CloseIncidentRequest):
    """
    Close an incident with resolution.

    Resolutions:
    - confirmed_attack: Real attack, response taken
    - false_positive: Not a real threat
    - duplicate: Merged with another incident
    - resolved: Issue addressed
    - accepted_risk: Known risk, no action needed
    """
    incident = await close_incident(
        incident_id=incident_id,
        resolution=req.resolution,
        closed_by=req.closed_by,
        notes=req.notes,
    )

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    return {
        "ok": True,
        "incident_id": incident_id,
        "status": "closed",
        "resolution": req.resolution,
        "closed_by": req.closed_by,
    }


@app.post("/sec/incidents/{incident_id}/investigate")
async def mark_investigating(incident_id: str):
    """
    Mark an incident as under investigation.
    """
    incident = storage.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.status = "investigating"
    incident.updated_at = datetime.now(timezone.utc)
    storage.store_incident(incident)

    return {
        "ok": True,
        "incident_id": incident_id,
        "status": "investigating",
    }


@app.post("/sec/incidents/{incident_id}/create-case")
async def create_case(incident_id: str):
    """
    Create a governance case from a security incident.

    This materializes the incident into a formal case that requires
    human decision (I9 compliance).

    When Maestro is available, forwards to Maestro.
    Otherwise, creates case locally with case_id.
    """
    incident = storage.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if incident.maestro_case_id:
        return {
            "ok": True,
            "incident_id": incident_id,
            "case_id": incident.maestro_case_id,
            "message": "Case already exists",
        }

    # Generate case ID
    now = datetime.now(timezone.utc)
    case_id = f"SEC-CASE-{now.strftime('%Y%m%d%H%M%S')}-{incident_id[-6:].upper()}"

    # Try Maestro first (graceful degradation)
    maestro_ok = False
    try:
        from maestro_client import create_security_case
        resp = await create_security_case(
            incident_id=incident.incident_id,
            title=incident.title,
            summary=incident.summary,
            severity=incident.severity,
            confidence=incident.confidence,
            event_count=incident.event_count,
            primary_vector=incident.primary_vector,
            affected_assets=incident.affected_assets,
            recommended_action=incident.recommended_action or "review",
        )
        if resp.get("case_id"):
            case_id = resp["case_id"]
            maestro_ok = True
    except Exception:
        pass  # Graceful degradation — use local case

    # Update incident with case reference
    incident.maestro_case_id = case_id
    incident.status = "investigating"
    incident.updated_at = now
    storage.store_incident(incident)

    return {
        "ok": True,
        "incident_id": incident_id,
        "case_id": case_id,
        "maestro_integrated": maestro_ok,
        "message": f"Case created: {case_id}",
        "next_action": "Human review required (I9)",
    }


@app.post("/sec/incidents/{incident_id}/approve")
async def approve_incident(incident_id: str):
    """
    Human approval of incident response.

    This is the I9 gate — human decides, system executes.
    After approval, incident can be sealed to Ledger.
    """
    incident = storage.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Mark as human-approved
    incident.status = "approved"
    incident.updated_at = datetime.now(timezone.utc)
    storage.store_incident(incident)

    return {
        "ok": True,
        "incident_id": incident_id,
        "status": "approved",
        "case_id": incident.maestro_case_id,
        "message": "Human approved. Ready to seal.",
        "next_action": "Call /seal to anchor to Ledger",
    }


@app.post("/sec/incidents/{incident_id}/reject")
async def reject_incident(incident_id: str):
    """
    Human rejection of incident (false positive).

    Marks incident as closed without sealing.
    """
    incident = storage.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.status = "closed"
    incident.resolution = "false_positive"
    incident.updated_at = datetime.now(timezone.utc)
    storage.store_incident(incident)

    return {
        "ok": True,
        "incident_id": incident_id,
        "status": "closed",
        "resolution": "false_positive",
        "message": "Marked as false positive. Not sealed.",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SSE STREAM — Real-time Dashboard Feed + Live Intelligence
# ═══════════════════════════════════════════════════════════════════════════════

# Timeline buffer — last 60 seconds of activity
TIMELINE_BUFFER = []
MAX_TIMELINE = 60


def build_heatmap(incidents) -> dict:
    """Build IP intensity heatmap from incident actors."""
    heatmap = {}
    for inc in incidents:
        for actor in inc.actors:
            ip = actor.get("ip") or actor.get("ip_hash", "unknown")
            if ip and ip != "unknown":
                heatmap[ip] = heatmap.get(ip, 0) + inc.event_count
    return heatmap


def get_recent_events(limit: int = 30) -> list:
    """Get recent events for replay visualization."""
    events = storage.list_events(limit=limit)
    return [
        {
            "id": e.event_id[-8:],
            "type": e.event_type,
            "time": e.timestamp.isoformat() if e.timestamp else None,
            "ip": e.actor.ip or e.actor.ip_hash or "?",
            "severity": e.severity,
        }
        for e in events
    ]


async def incident_stream():
    """
    Server-Sent Events stream for real-time dashboard updates.
    Now includes: heatmap, timeline, and replay data.
    """
    global TIMELINE_BUFFER
    last_hash = ""

    while True:
        try:
            incidents = storage.list_incidents(limit=50)
            stats = storage.stats()
            now = datetime.now(timezone.utc)

            # Build heatmap from actors
            heatmap = build_heatmap(incidents)

            # Update timeline buffer
            TIMELINE_BUFFER.append({
                "t": now.isoformat(),
                "events": stats["events"],
                "incidents": stats["incidents"],
            })
            if len(TIMELINE_BUFFER) > MAX_TIMELINE:
                TIMELINE_BUFFER.pop(0)

            # Get recent events for replay
            recent_events = get_recent_events(30)

            # Get geo points (uses cache, enrichment happens in background)
            geo_points = get_cached_geo_points(incidents)

            data = {
                "time": now.isoformat(),
                "events_total": stats["events"],
                "incidents_total": stats["incidents"],
                "incidents": [
                    {
                        "id": inc.incident_id,
                        "title": inc.title,
                        "severity": inc.severity,
                        "status": inc.status,
                        "count": inc.event_count,
                        "confidence": inc.confidence,
                        "vector": inc.primary_vector,
                        "action": inc.recommended_action,
                        "updated": inc.updated_at.isoformat() if inc.updated_at else None,
                        "receipt": inc.ledger_receipt_id,
                        "case_id": inc.maestro_case_id,
                    }
                    for inc in incidents
                ],
                # Live Intelligence layers
                "heatmap": heatmap,
                "timeline": list(TIMELINE_BUFFER),
                "recent_events": recent_events,
                "geo": geo_points,
            }

            # Always emit for timeline animation (remove hash check)
            yield f"data: {json.dumps(data)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

        await asyncio.sleep(1)


@app.get("/sec/stream")
async def stream_incidents():
    """
    SSE endpoint for real-time incident streaming.
    Connect with EventSource in browser.
    """
    return StreamingResponse(
        incident_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


# ═══════════════════════════════════════════════════════════════════════════════
# STATIC FILES — Dashboard NOIR
# ═══════════════════════════════════════════════════════════════════════════════

# Mount static files for dashboard
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/dashboard", StaticFiles(directory=static_dir, html=True), name="dashboard")


# Run with: uvicorn app:app --host 0.0.0.0 --port 8144
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
