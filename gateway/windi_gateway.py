#!/usr/bin/env python3
"""
WINDI Gateway - Constitutional Firewall for AI Certification
Port: 8082
"""

import json
import hashlib
import sqlite3
import httpx
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

TRUST_BUS_URL = "http://127.0.0.1:8081"
DB_PATH = Path("/opt/windi/data/virtue_history.db")
GATEWAY_PORT = 8082

app = FastAPI(title="WINDI Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

WINDI_SYSTEM_PROMPT = """
You are now operating as a WINDI Agent under the Constitutional Framework.

CORE PRINCIPLE: "AI processes. Human decides. WINDI guarantees."

8 INVARIANTS (I1-I8):
I1 - SOVEREIGNTY: Human authority is absolute
I2 - NON-OPACITY: All reasoning explainable
I3 - TRANSPARENCY: Declare limitations and sources
I4 - JURISDICTION: Operate within certified domain
I5 - NO FABRICATION: Never invent facts
I6 - CONFLICT STRUCTURING: Present conflicts, let human resolve
I7 - INSTITUTIONAL: Respect organizational hierarchies
I8 - NO DEPTH PUNISHMENT: Never penalize deeper questions

8 STABILITY_LAYERS (G1-G8):
G1 - Content Filter: No harmful content
G2 - Privacy Filter: Protect personal data
G3 - Accuracy Filter: Verify claims
G4 - Scope Filter: Stay within domain
G5 - Tone Filter: Professional communication
G6 - Post-Filter: "You should" becomes "Consider"
G7 - Fail-Closed: Refuse when uncertain on critical matters
G8 - Independence: Maintain ethical judgment

RESPONSE PATTERN: EXPLAIN -> STRUCTURE -> ASK

SESSION: WINDI-ID={windi_id} | Domain={domain} | Model={model}

OM SHANTI
"""

class CertifyRequest(BaseModel):
    model: str
    domain: str = "general"
    operator_id: Optional[str] = None

class CertifyResponse(BaseModel):
    windi_id: str
    session_id: str
    model: str
    domain: str
    certified_at: str
    system_prompt: str

class ValidateRequest(BaseModel):
    windi_id: str
    content: str

class ValidateResponse(BaseModel):
    valid: bool
    violations: list
    filtered_content: Optional[str] = None
    stability_layers_applied: list

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS certified_agents (
            windi_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            model TEXT NOT NULL,
            domain TEXT NOT NULL,
            operator_id TEXT,
            certified_at TEXT NOT NULL,
            revoked_at TEXT,
            active INTEGER DEFAULT 1
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS validation_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            windi_id TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            valid INTEGER NOT NULL,
            violations TEXT,
            stability_layers_applied TEXT,
            validated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def generate_windi_id(model: str, domain: str, ts: str) -> str:
    raw = f"{model}:{domain}:{ts}"
    h = hashlib.sha256(raw.encode()).hexdigest()[:12]
    return f"WINDI-{model.upper()[:3]}-{h.upper()}"

def generate_session_id() -> str:
    now = datetime.now(timezone.utc).isoformat()
    return hashlib.sha256(now.encode()).hexdigest()[:16]

async def register_event(event_type: str, payload: dict):
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{TRUST_BUS_URL}/event", json={
                "event_id": f"GW-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                "actor": "windi-gateway",
                "action": event_type,
                "payload": json.dumps(payload)
            })
    except:
        pass

def apply_stability_layers(content: str):
    violations = []
    applied = []
    filtered = content
    
    for word in ["stupid", "idiot", "dumb"]:
        if word in content.lower():
            violations.append("G5: Unprofessional tone")
            applied.append("G5-VIOLATION")
            break
    
    transforms = [("You should ", "Consider "), ("You must ", "It may help to ")]
    for old, new in transforms:
        if old in filtered:
            filtered = filtered.replace(old, new)
            applied.append("G6-TRANSFORMED")
    
    return len(violations) == 0, violations, filtered, applied

@app.on_event("startup")
async def startup():
    init_db()
    print("WINDI Gateway initialized - Constitutional Firewall active")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "windi-gateway", "port": 8082}

@app.post("/certify", response_model=CertifyResponse)
async def certify_agent(req: CertifyRequest):
    ts = datetime.now(timezone.utc).isoformat()
    windi_id = generate_windi_id(req.model, req.domain, ts)
    session_id = generate_session_id()
    
    prompt = WINDI_SYSTEM_PROMPT.format(windi_id=windi_id, domain=req.domain, model=req.model)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO certified_agents (windi_id, session_id, model, domain, operator_id, certified_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (windi_id, session_id, req.model, req.domain, req.operator_id, ts))
    conn.commit()
    conn.close()
    
    await register_event("AGENT_CERTIFIED", {"windi_id": windi_id, "model": req.model, "domain": req.domain})
    
    return CertifyResponse(windi_id=windi_id, session_id=session_id, model=req.model,
                           domain=req.domain, certified_at=ts, system_prompt=prompt)

@app.post("/validate", response_model=ValidateResponse)
async def validate_content(req: ValidateRequest):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT active FROM certified_agents WHERE windi_id = ?", (req.windi_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Agent not certified")
    if not row[0]:
        raise HTTPException(status_code=403, detail="Agent revoked")
    
    valid, violations, filtered, applied = apply_stability_layers(req.content)
    
    content_hash = hashlib.sha256(req.content.encode()).hexdigest()[:16]
    cursor.execute("""
        INSERT INTO validation_log (windi_id, content_hash, valid, violations, stability_layers_applied, validated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (req.windi_id, content_hash, int(valid), json.dumps(violations), json.dumps(applied),
          datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()
    
    if violations:
        await register_event("STABILITY_LAYER_VIOLATION", {"windi_id": req.windi_id, "violations": violations})
    
    return ValidateResponse(valid=valid, violations=violations,
                            filtered_content=filtered if filtered != req.content else None,
                            stability_layers_applied=applied)

@app.get("/agent/{windi_id}")
async def get_agent(windi_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT model, domain, certified_at, active FROM certified_agents WHERE windi_id = ?", (windi_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"windi_id": windi_id, "model": row[0], "domain": row[1], "certified_at": row[2], "active": bool(row[3])}

@app.post("/revoke/{windi_id}")
async def revoke_agent(windi_id: str):
    ts = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE certified_agents SET active = 0, revoked_at = ? WHERE windi_id = ?", (ts, windi_id))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Agent not found")
    conn.commit()
    conn.close()
    await register_event("AGENT_REVOKED", {"windi_id": windi_id})
    return {"status": "revoked", "windi_id": windi_id}

@app.get("/agents")
async def list_agents():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT windi_id, model, domain, certified_at FROM certified_agents WHERE active = 1")
    rows = cursor.fetchall()
    conn.close()
    return [{"windi_id": r[0], "model": r[1], "domain": r[2], "certified_at": r[3]} for r in rows]

@app.get("/system-prompt")
async def get_prompt():
    return {"template": WINDI_SYSTEM_PROMPT, "invariants": 8, "stability_layers": 8}

# ═══════════════════════════════════════════════════════════════════
# WINDI LLM CHAT - Dragons Integration
# ═══════════════════════════════════════════════════════════════════

import sys
sys.path.insert(0, "/opt/windi/engine")
from dotenv import load_dotenv
load_dotenv('/opt/windi/.env')

try:
    from windi_agent_v3 import ask_windi
    DRAGONS_AVAILABLE = True
except:
    DRAGONS_AVAILABLE = False

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None
    windi_id: Optional[str] = None
    dragon: str = "claude"
    lang: str = "de"
    institutional_profile: Optional[dict] = None

@app.post("/api/chat")
async def chat(req: ChatRequest):
    if not DRAGONS_AVAILABLE:
        return {"error": "Dragons not available"}, 503

        # Combina mensagem com contexto do documento
    full_message = req.message
    if req.context:
        full_message = f"DOCUMENT FOR ANALYSIS:\n\n{req.context}\n\n---\n\nUSER REQUEST:\n{req.message}"
    
    result = ask_windi(full_message, lang=req.lang, institutional_profile=req.institutional_profile)


    if result.get("success"):
        await register_event("CHAT_PROCESSED", {
            "dragon": req.dragon,
            "receipt": result.get("receipt"),
            "windi_id": req.windi_id,
            "is_document": result.get("is_document", False),
            "document_type": result.get("document_type")
        })

        return {
            "response": result.get("response"),
            "dragon": req.dragon,
            "receipt": result.get("receipt"),
            "model": result.get("model"),
            "is_document": result.get("is_document", False),
            "document_type": result.get("document_type"),
            "document_content": result.get("document_content"),
            "chat_content": result.get("chat_content"),
            "institutional_profile": req.institutional_profile
        }
    else:
        return {"error": result.get("error")}, 500

@app.get("/api/dragons")
async def list_dragons():
    if not DRAGONS_AVAILABLE:
        return {"dragons": []}
    orch = get_orchestrator()
    return {"dragons": orch.status()}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=GATEWAY_PORT)
