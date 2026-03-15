#!/usr/bin/env python3
"""
WINDI Desktop GEN 7 — Smart Zones Gateway (FastAPI)
====================================================
Port: 8109 (staging) → 8100 (production swap)

Smart Zones:
- D1: Agent Corps (Constellation)
- D2: Sovereign Editor (Canvas/Code)
- D3: Governance Glass (Forensics)

Principle: "AI processes. Human decides. WINDI guarantees."
"""

import os
import json
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# === Configuration ===
PORT = int(os.getenv("PORT", "8119"))
DRAGON_URL = os.getenv("DRAGON_URL", "http://localhost:8108")
LEDGER_URL = os.getenv("LEDGER_URL", "http://localhost:8101")
SANDBOX_URL = os.getenv("SANDBOX_URL", "http://localhost:8091")
STATIC_DIR = Path(os.getenv("STATIC_DIR", "/opt/windi/desktop-gen7/frontend"))
LOG_DIR = Path(os.getenv("LOG_DIR", "/opt/windi/logs"))

# Agent Corps endpoints for health checks
AGENT_CORPS = {
    "W-COMM-001": {"port": 8091, "health": "/communique/health", "name": "Communique"},
    "W-LEGAL-001": {"port": 8091, "health": "/legal/health", "name": "Justica"},
    "W-NOTARY-001": {"port": 8091, "health": "/notary/health", "name": "Notarial"},
    "W-JOURN-001": {"port": 8091, "health": "/journalist/health", "name": "Journalist"},
    "W-AUDIT-001": {"port": 8091, "health": "/audit/health", "name": "Auditor"},
    "W-COMPLY-001": {"port": 8091, "health": "/compliance/health", "name": "Compliance"},
    "W-ACCT-001": {"port": 8091, "health": "/accounting/health", "name": "Accountant"},
    "GROVE-ARENA": {"port": 8091, "health": "/grove/health", "name": "Grove Arena"},
}

# Core services for ecosystem health
CORE_SERVICES = {
    "dragon": {"url": f"{DRAGON_URL}/health", "critical": True},
    "ledger": {"url": f"{LEDGER_URL}/health", "critical": True},
    "sandbox": {"url": f"{SANDBOX_URL}/agent/health", "critical": True},
}

# Uptime tracking
GEN7_START_TIME = time.time()


# === Pydantic Models ===
class KeyValidateRequest(BaseModel):
    key_type: str  # "anthropic" | "openai" | "mistral"
    key_prefix: str  # First 8 chars only for validation


class OneTouchRequest(BaseModel):
    intent: str
    wallet_id: str
    agent: Optional[str] = None
    doc_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class OneTouchResponse(BaseModel):
    session_id: str
    stage: str
    agent: str
    message: str
    next_step: str


# === Lifespan ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[GEN7] Desktop GEN 7 Gateway starting on :{PORT}")
    print(f"[GEN7] Dragon: {DRAGON_URL}")
    print(f"[GEN7] Ledger: {LEDGER_URL}")
    print(f"[GEN7] Sandbox: {SANDBOX_URL}")
    yield
    print("[GEN7] Shutting down...")


# === App ===
app = FastAPI(
    title="WINDI Desktop GEN 7",
    description="Smart Zones Gateway — AI processes. Human decides. WINDI guarantees.",
    version="7.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Health ===
@app.get("/health")
async def health():
    """GEN 7 health check with ecosystem status."""
    ecosystem = {}

    async with httpx.AsyncClient(timeout=3.0) as client:
        # Check core services
        for name, cfg in CORE_SERVICES.items():
            try:
                r = await client.get(cfg["url"])
                ecosystem[name] = {
                    "status": "UP" if r.status_code == 200 else "DEGRADED",
                    "code": r.status_code,
                    "critical": cfg["critical"],
                }
            except Exception:
                ecosystem[name] = {
                    "status": "DOWN",
                    "code": 0,
                    "critical": cfg["critical"],
                }

    # Count status
    up_count = sum(1 for s in ecosystem.values() if s["status"] == "UP")
    critical_down = any(
        s["status"] == "DOWN" and s["critical"]
        for s in ecosystem.values()
    )

    return {
        "service": "windi-desktop-gen7",
        "version": "7.0.0",
        "status": "degraded" if critical_down else "operational",
        "principle": "AI processes. Human decides. WINDI guarantees.",
        "port": PORT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ecosystem": {
            "services": ecosystem,
            "total": len(ecosystem),
            "up": up_count,
        },
        "smart_zones": {
            "D1": "Agent Corps",
            "D2": "Sovereign Editor",
            "D3": "Governance Glass",
        },
    }


# === API Keys Validation ===
@app.post("/api/keys/validate")
async def validate_api_key(req: KeyValidateRequest):
    """
    Validate API key format (not the actual key).
    Keys are NEVER sent to this endpoint - only prefix for format check.
    """
    valid_prefixes = {
        "anthropic": ["sk-ant-"],
        "openai": ["sk-"],
        "mistral": ["mistral-"],
    }

    if req.key_type not in valid_prefixes:
        raise HTTPException(400, f"Unknown key type: {req.key_type}")

    is_valid = any(
        req.key_prefix.startswith(prefix)
        for prefix in valid_prefixes[req.key_type]
    )

    return {
        "key_type": req.key_type,
        "format_valid": is_valid,
        "message": "Format validated" if is_valid else "Invalid key prefix",
        "note": "This validates format only. Actual key validation happens server-side.",
    }


# === Dragon Status (Pulse) ===
@app.get("/api/dragon/status")
async def dragon_status():
    """
    Dragon Pulse — proxy health status from :8108.
    Used by Command Bar indicator.
    """
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            r = await client.get(f"{DRAGON_URL}/health")
            if r.status_code == 200:
                data = r.json()
                return {
                    "pulse": "ACTIVE",
                    "dragon_version": data.get("version", "unknown"),
                    "model": data.get("model", "unknown"),
                    "latency_ms": r.elapsed.total_seconds() * 1000,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            else:
                return {
                    "pulse": "DEGRADED",
                    "code": r.status_code,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
        except httpx.TimeoutException:
            return {
                "pulse": "TIMEOUT",
                "message": "Dragon not responding",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            return {
                "pulse": "DOWN",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }


# === Institutional Status Panel ===
@app.get("/api/status")
async def institutional_status():
    """
    Institutional Status Panel — aggregates all WINDI services.
    Used by /status.html for live dashboard.
    """
    async def probe(url: str, timeout: float = 3.0) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(url, timeout=timeout)
                data = r.json() if r.status_code == 200 else {}
                return {"ok": r.status_code == 200, "data": data, "ms": int(r.elapsed.total_seconds() * 1000)}
        except Exception as e:
            return {"ok": False, "data": {}, "ms": -1, "error": str(e)}

    uptime_s = int(time.time() - GEN7_START_TIME)
    uptime_h = f"{uptime_s // 3600}h {(uptime_s % 3600) // 60}m"

    dragon = await probe(f"{DRAGON_URL}/health")
    ledger = await probe(f"{LEDGER_URL}/health")
    sandbox = await probe(f"{SANDBOX_URL}/agent/health")

    # Receipt count from Ledger /health
    receipt_count = ledger["data"].get("receipts") if ledger["ok"] else None

    return {
        "gen7": {
            "version": "7.0.0",
            "status": "operational",
            "uptime": uptime_h,
            "uptime_s": uptime_s,
            "smart_zones": {"D1": True, "D2": True, "D3": True}
        },
        "dragon": {
            "ok": dragon["ok"],
            "version": dragon["data"].get("version", "—"),
            "ms": dragon["ms"]
        },
        "ledger": {
            "ok": ledger["ok"],
            "receipts": receipt_count,
            "ms": ledger["ms"]
        },
        "sandbox": {
            "ok": sandbox["ok"],
            "agents": len(AGENT_CORPS),
            "ms": sandbox["ms"]
        },
        "timestamp": int(time.time()),
        "principle": "AI processes. Human decides. WINDI guarantees."
    }


# === One Touch Execute ===
@app.post("/api/onetouch/execute", response_model=OneTouchResponse)
async def onetouch_execute(req: OneTouchRequest):
    """
    One Touch Pipeline — single entry point for all document operations.

    Phase 1: Intent Capture
    Phase 2: Agent Routing (auto-detect or explicit)
    Phase 3: Bridge Session Creation
    Phase 4: Return session for Canvas materialization
    """
    # Phase 1: Intent received
    intent_hash = hashlib.sha256(req.intent.encode()).hexdigest()[:8]

    # Phase 2: Agent routing
    agent = req.agent
    if not agent:
        # Auto-detect based on intent keywords
        intent_lower = req.intent.lower()
        if any(kw in intent_lower for kw in ["contrato", "contract", "legal", "jurídico"]):
            agent = "W-LEGAL-001"
        elif any(kw in intent_lower for kw in ["certidão", "certificate", "notarial", "seal", "selar", "forense", "evidência", "hash", "ledger"]):
            agent = "W-NOTARY-001"
        elif any(kw in intent_lower for kw in ["artigo", "article", "publicar", "editorial"]):
            agent = "W-JOURN-001"
        elif any(kw in intent_lower for kw in ["fatura", "invoice", "fiscal", "financeiro", "imposto", "tax", "elster", "buchung"]):
            agent = "W-ACCT-001"
        elif any(kw in intent_lower for kw in ["audit", "auditoria", "verificar", "compliance", "relatório"]):
            agent = "W-AUDIT-001"
        else:
            agent = "W-COMM-001"  # Default: Communique

    # Phase 3: Create bridge session
    bridge_map = {
        "W-COMM-001": "/communique/bridge/open",
        "W-LEGAL-001": "/legal/bridge/open",
        "W-NOTARY-001": "/notary/bridge/open",
        "W-JOURN-001": "/journalist/bridge/open",
        "W-ACCT-001": "/accounting/bridge/open",
        "W-AUDIT-001": "/audit/bridge/open",
    }

    bridge_endpoint = bridge_map.get(agent, "/communique/bridge/open")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.post(
                f"{SANDBOX_URL}{bridge_endpoint}",
                json={
                    "wallet_id": req.wallet_id,
                    "doc_type": req.doc_type or "document",
                    "title": req.intent[:50],
                    "metadata": req.metadata or {},
                },
            )

            if r.status_code in (200, 201):
                data = r.json()
                return OneTouchResponse(
                    session_id=data.get("session_id", f"OT-{intent_hash}"),
                    stage=data.get("stage", "C1"),
                    agent=agent,
                    message=data.get("message", f"Sessão criada via {agent}"),
                    next_step=f"Aguarda conteúdo em D2 (Sovereign Editor)",
                )
            else:
                raise HTTPException(r.status_code, f"Bridge error: {r.text}")

        except httpx.TimeoutException:
            raise HTTPException(504, "Bridge timeout")
        except Exception as e:
            raise HTTPException(500, str(e))


# === Agent Corps Status ===
@app.get("/api/agents/status")
async def agents_status():
    """
    Agent Corps Constellation — health of all 8 agents.
    Used by D1 (Agent Corps) zone.
    """
    agents = {}

    async with httpx.AsyncClient(timeout=3.0) as client:
        for agent_id, cfg in AGENT_CORPS.items():
            url = f"http://localhost:{cfg['port']}{cfg['health']}"
            try:
                r = await client.get(url)
                if r.status_code == 200:
                    data = r.json()
                    agents[agent_id] = {
                        "name": cfg["name"],
                        "status": data.get("status", "UP"),
                        "version": data.get("version", "unknown"),
                        "latency_ms": round(r.elapsed.total_seconds() * 1000, 1),
                    }
                else:
                    agents[agent_id] = {
                        "name": cfg["name"],
                        "status": "DEGRADED",
                        "code": r.status_code,
                    }
            except Exception:
                agents[agent_id] = {
                    "name": cfg["name"],
                    "status": "DOWN",
                }

    # Summary
    live = sum(1 for a in agents.values() if a["status"] in ["UP", "GREEN"])

    return {
        "constellation": "WINDI Agent Corps",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": len(agents),
            "live": live,
            "status": "FULL" if live == len(agents) else "PARTIAL",
        },
        "agents": agents,
    }


# === Static Files ===
@app.get("/")
async def root():
    """Serve main index.html"""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "WINDI Desktop GEN 7", "status": "frontend pending"}


@app.get("/status.html")
async def status_page():
    """Serve institutional status dashboard"""
    status_path = STATIC_DIR / "status.html"
    if status_path.exists():
        return FileResponse(status_path)
    return JSONResponse({"error": "status.html not found"}, status_code=404)


# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR / "static"), name="static")


# === Main ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
