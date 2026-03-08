#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════════
  WINDI POTT ENGINE — P3 Creator Governance Federation
  Port: 8114

  CONSTITUTIONAL PRINCIPLES:
  - Data boundaries: audiência NUNCA cruza entre Potts
  - Attribution 85/15: toda receita via Pott registada com split justo
  - Exit freedom: /leave leva conteúdo (criador retém sempre)
  - Receipts: toda acção gera Virtue Receipt no Ledger

  Verticals: cooking | education | music | local | tech | art | fitness | business
═══════════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import hashlib
import json
from datetime import datetime
from typing import Optional, List, Dict
from contextlib import asynccontextmanager

# Add current directory for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

import models

# ═══════════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════════

VERSION = "1.0.0"
PORT = int(os.environ.get("POTT_PORT", 8114))
LEDGER_URL = os.environ.get("LEDGER_URL", "http://localhost:8101")

VERTICALS = ["cooking", "education", "music", "local", "tech", "art", "fitness", "business"]

# ═══════════════════════════════════════════════════════════════════════════════════
# LEDGER INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════════

async def register_ledger(event_type: str, data: Dict) -> Optional[str]:
    """Register event to Forensic Ledger, return receipt ID."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{LEDGER_URL}/entry",
                json={
                    "type": f"pott_{event_type}",
                    "namespace": "pott",
                    "data": {
                        **data,
                        "timestamp": datetime.utcnow().isoformat(),
                        "engine_version": VERSION
                    }
                }
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("receipt_id") or result.get("id")
    except Exception as e:
        print(f"[POTT] Ledger registration failed: {e}")
    return None


def generate_pott_id(name: str, curator_did: str) -> str:
    """Generate unique Pott ID."""
    ts = datetime.utcnow().strftime("%Y%m%d")
    h = hashlib.sha256(f"{name}{curator_did}{ts}".encode()).hexdigest()[:8]
    return f"POTT-{ts}-{h.upper()}"


# ═══════════════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════════════════════════

class PottCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    vertical: str = Field(..., description="cooking|education|music|local|tech|art|fitness|business")
    curator_did: str = Field(..., min_length=32)
    description: str = Field(default="", max_length=500)
    split_creator: float = Field(default=0.85, ge=0.5, le=0.95)
    split_pott: float = Field(default=0.15, ge=0.05, le=0.5)
    rules: Dict = Field(default_factory=dict)


class JoinRequest(BaseModel):
    creator_did: str = Field(..., min_length=32)
    role: str = Field(default="member", pattern="^(member|moderator)$")


class CurateRequest(BaseModel):
    trigger_id: str = Field(..., min_length=8)
    trigger_seal: str = Field(default="")
    creator_did: str = Field(..., min_length=32)
    curator_did: str = Field(..., min_length=32)
    action: str = Field(default="featured", pattern="^(featured|pinned|removed)$")
    position: int = Field(default=0, ge=0)


class RevenueEvent(BaseModel):
    trigger_id: str = Field(..., min_length=8)
    creator_did: str = Field(..., min_length=32)
    amount: float = Field(..., gt=0)
    source: str = Field(default="direct")


# ═══════════════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await models.init_db()
    print(f"[POTT] Database initialized: {models.DB_PATH}")
    yield


app = FastAPI(
    title="WINDI Pott Engine",
    description="P3 Creator Governance Federation — 85/15 Split, Data Boundaries, Exit Freedom",
    version=VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://admin.windia4desk.tech", "http://localhost:8108"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════════════
# HEALTH & STATUS
# ═══════════════════════════════════════════════════════════════════════════════════

@app.get("/")
@app.get("/health")
async def health():
    """Health check with governance principles."""
    return {
        "service": "pott-engine",
        "version": VERSION,
        "status": "healthy",
        "port": PORT,
        "db": models.DB_PATH,
        "verticals": VERTICALS,
        "governance": {
            "default_split": {"creator": 0.85, "pott": 0.15},
            "data_boundaries": True,
            "exit_freedom": True,
            "ledger_receipts": True
        }
    }


# ═══════════════════════════════════════════════════════════════════════════════════
# POTT CRUD ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════════

@app.post("/api/pott/create")
async def create_pott(data: PottCreate):
    """Create a new Pott federation. Registers to Ledger."""
    # Validate vertical
    if data.vertical not in VERTICALS:
        raise HTTPException(400, f"Invalid vertical. Must be one of: {', '.join(VERTICALS)}")

    # Validate split totals to 1.0
    if abs((data.split_creator + data.split_pott) - 1.0) > 0.001:
        raise HTTPException(400, "split_creator + split_pott must equal 1.0")

    # Generate ID
    pott_id = generate_pott_id(data.name, data.curator_did)

    # Register to Ledger
    ledger_receipt = await register_ledger("create", {
        "pott_id": pott_id,
        "name": data.name,
        "vertical": data.vertical,
        "curator_did": data.curator_did,
        "split": {"creator": data.split_creator, "pott": data.split_pott}
    })

    # Create in database
    result = await models.create_pott(
        pott_id=pott_id,
        name=data.name,
        vertical=data.vertical,
        curator_did=data.curator_did,
        description=data.description,
        split_creator=data.split_creator,
        split_pott=data.split_pott,
        rules=data.rules,
        ledger_receipt=ledger_receipt
    )

    return {
        "success": True,
        "pott": result,
        "ledger_receipt": ledger_receipt,
        "governance": "Data boundaries active. Exit freedom guaranteed."
    }


@app.get("/api/pott/{pott_id}")
async def get_pott(pott_id: str):
    """Get Pott details with members and featured content."""
    pott = await models.get_pott(pott_id)
    if not pott:
        raise HTTPException(404, "Pott not found")
    return {"success": True, "pott": pott}


@app.get("/api/pott/discover")
async def discover_potts(
    vertical: Optional[str] = Query(None, description="Filter by vertical"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Discover public Potts."""
    if vertical and vertical not in VERTICALS:
        raise HTTPException(400, f"Invalid vertical. Must be one of: {', '.join(VERTICALS)}")

    potts = await models.list_potts(vertical=vertical, limit=limit, offset=offset)
    return {
        "success": True,
        "potts": potts,
        "count": len(potts),
        "verticals": VERTICALS
    }


# ═══════════════════════════════════════════════════════════════════════════════════
# MEMBERSHIP ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════════

@app.post("/api/pott/{pott_id}/join")
async def join_pott(pott_id: str, data: JoinRequest):
    """Join a Pott federation."""
    # Verify pott exists
    pott = await models.get_pott(pott_id)
    if not pott:
        raise HTTPException(404, "Pott not found")

    if pott["status"] != "active":
        raise HTTPException(400, "Pott is not accepting members")

    # Register to Ledger
    ledger_receipt = await register_ledger("join", {
        "pott_id": pott_id,
        "creator_did": data.creator_did,
        "role": data.role
    })

    result = await models.join_pott(
        pott_id=pott_id,
        creator_did=data.creator_did,
        role=data.role,
        ledger_receipt=ledger_receipt
    )

    if "error" in result:
        raise HTTPException(400, result["error"])

    return {
        "success": True,
        **result,
        "ledger_receipt": ledger_receipt,
        "split": {"creator": pott["split_creator"], "pott": pott["split_pott"]}
    }


@app.post("/api/pott/{pott_id}/leave")
async def leave_pott(pott_id: str, creator_did: str = Header(..., alias="X-Creator-DID")):
    """Leave a Pott. Exit freedom: creator retains all content."""
    # Register to Ledger
    ledger_receipt = await register_ledger("leave", {
        "pott_id": pott_id,
        "creator_did": creator_did
    })

    result = await models.leave_pott(
        pott_id=pott_id,
        creator_did=creator_did,
        ledger_receipt=ledger_receipt
    )

    if "error" in result:
        raise HTTPException(400, result["error"])

    return {
        "success": True,
        **result,
        "ledger_receipt": ledger_receipt,
        "governance": "Exit freedom: all your content remains yours."
    }


# ═══════════════════════════════════════════════════════════════════════════════════
# CURATION & FEED ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════════

@app.get("/api/pott/{pott_id}/feed")
async def get_feed(
    pott_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get curated feed for a Pott. Data boundaries enforced."""
    pott = await models.get_pott(pott_id)
    if not pott:
        raise HTTPException(404, "Pott not found")

    feed = await models.get_feed(pott_id, limit=limit, offset=offset)

    return {
        "success": True,
        "pott_id": pott_id,
        "pott_name": pott["name"],
        "vertical": pott["vertical"],
        "feed": feed,
        "count": len(feed),
        "governance": "Data boundaries: this feed is exclusive to this Pott."
    }


@app.post("/api/pott/{pott_id}/curate")
async def curate_trigger(pott_id: str, data: CurateRequest):
    """Curate a trigger (feature, pin, remove). Curator/moderator only."""
    pott = await models.get_pott(pott_id)
    if not pott:
        raise HTTPException(404, "Pott not found")

    # Register to Ledger
    ledger_receipt = await register_ledger("curate", {
        "pott_id": pott_id,
        "trigger_id": data.trigger_id,
        "action": data.action,
        "curator_did": data.curator_did
    })

    result = await models.curate_trigger(
        pott_id=pott_id,
        trigger_id=data.trigger_id,
        trigger_seal=data.trigger_seal,
        creator_did=data.creator_did,
        curator_did=data.curator_did,
        action=data.action,
        position=data.position,
        ledger_receipt=ledger_receipt
    )

    if "error" in result:
        raise HTTPException(403, result["error"])

    return {
        "success": True,
        **result,
        "ledger_receipt": ledger_receipt
    }


# ═══════════════════════════════════════════════════════════════════════════════════
# METRICS & REVENUE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════════

@app.get("/api/pott/{pott_id}/metrics")
async def get_metrics(pott_id: str, days: int = Query(30, ge=1, le=365)):
    """Get aggregated metrics for a Pott."""
    metrics = await models.get_metrics(pott_id, days=days)
    if not metrics:
        raise HTTPException(404, "Pott not found")

    return {"success": True, **metrics}


@app.post("/api/pott/{pott_id}/revenue")
async def record_revenue(pott_id: str, data: RevenueEvent):
    """Record a revenue event. Automatic 85/15 split."""
    pott = await models.get_pott(pott_id)
    if not pott:
        raise HTTPException(404, "Pott not found")

    # Use pott's configured split
    split_creator = pott["split_creator"]
    split_pott = pott["split_pott"]

    # Register to Ledger
    ledger_receipt = await register_ledger("revenue", {
        "pott_id": pott_id,
        "trigger_id": data.trigger_id,
        "creator_did": data.creator_did,
        "amount": data.amount,
        "split": {"creator": split_creator, "pott": split_pott}
    })

    result = await models.record_revenue(
        pott_id=pott_id,
        trigger_id=data.trigger_id,
        creator_did=data.creator_did,
        amount_total=data.amount,
        split_creator=split_creator,
        split_pott=split_pott,
        source=data.source,
        ledger_receipt=ledger_receipt
    )

    return {
        "success": True,
        **result,
        "ledger_receipt": ledger_receipt,
        "governance": f"Attribution: {int(split_creator*100)}/{int(split_pott*100)} split enforced."
    }


# ═══════════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("  WINDI POTT ENGINE — P3 Creator Governance Federation")
    print("=" * 70)
    print(f"\n  Port: {PORT}")
    print(f"  DB: {models.DB_PATH}")
    print(f"  Ledger: {LEDGER_URL}")
    print(f"  Version: {VERSION}")
    print("\n  Governance Principles:")
    print("  - Data boundaries: audiência NUNCA cruza")
    print("  - Attribution 85/15: toda receita registada")
    print("  - Exit freedom: /leave leva conteúdo")
    print("  - Receipts: toda acção gera Virtue Receipt")
    print(f"\n  Verticals: {', '.join(VERTICALS)}")
    print("\n  Endpoints:")
    print("    POST /api/pott/create         — Create Pott")
    print("    GET  /api/pott/{id}           — Pott details")
    print("    GET  /api/pott/discover       — List public Potts")
    print("    POST /api/pott/{id}/join      — Join Pott")
    print("    POST /api/pott/{id}/leave     — Leave (exit freedom)")
    print("    GET  /api/pott/{id}/feed      — Curated feed")
    print("    POST /api/pott/{id}/curate    — Feature/pin/remove")
    print("    GET  /api/pott/{id}/metrics   — Stats")
    print("    POST /api/pott/{id}/revenue   — Record payment")
    print("    GET  /health                  — Status")
    print("\n" + "=" * 70)
    print(f"  Human decides. Pott federates. → http://localhost:{PORT}/")
    print("=" * 70 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=PORT)
