# /opt/windi/brain/trust_bus.py
# WINDI Trust Bus - Interface Constitucional

from fastapi import FastAPI, HTTPException, Query
from typing import Optional
from brain.ledger import write_event, read_events, get_last_hash
from brain.invariants import enforce_all, InvariantViolation
from brain.models import TrustEvent

app = FastAPI(title="WINDI Trust Bus")


@app.post("/event")
def receive_event(event: TrustEvent):
    try:
        enforce_all(event)
        result = write_event(event)
        return {
            "status": "accepted",
            "event_id": event.event_id,
            "hash": result.get("hash")
        }
    except InvariantViolation as e:
        raise HTTPException(status_code=403, detail=str(e))


@app.get("/events")
def query_events(
    event_type: Optional[str] = Query(None),
    actor: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200)
):
    events = read_events(event_type=event_type, actor=actor, limit=limit)
    return {"count": len(events), "events": events}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "windi-brain",
        "mode": "local-only"
    }
