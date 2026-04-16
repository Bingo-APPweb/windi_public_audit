"""
W-SOCIAL-001 · Embedded Probe §01
Verified Professional Presence Infrastructure

Port: :8133
Invariants: I-SOC-001, I-SOC-002, I-SOC-003

"O humano define a lei narrativa. A IA amplifica a voz. O WINDI prova a autoria."
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import hashlib
import uuid
import httpx
import os

app = FastAPI(
    title="W-SOCIAL-001",
    description="Verified Professional Presence Infrastructure",
    version="0.1.0"
)

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

LEDGER_URL = os.getenv("LEDGER_URL", "http://127.0.0.1:8101/api/receipts")
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://127.0.0.1:8130/gateway/call")

# In-memory storage for PoC (SQLite in production)
intakes: Dict[str, dict] = {}
compilations: Dict[str, dict] = {}
publications: Dict[str, dict] = {}

# ═══════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════

class IntakeRequest(BaseModel):
    """I-SOC-001: Provenance Invariant - content must have traceable origin"""
    actor_did: str
    source_type: str  # law_document, enterprise_insight, travel_observation
    source_id: str
    source_title: str
    content_hash: str
    excerpt: str
    doc_type: Optional[str] = "general"
    jurisdiction: Optional[str] = "EU"

class CompileRequest(BaseModel):
    """Transform intake into channel-ready content"""
    intake_id: str
    channels: List[str] = ["linkedin"]
    tone_profile: str = "sophisticated_humility"
    constraints: Optional[Dict[str, Any]] = None

class ApproveRequest(BaseModel):
    """I-SOC-002: Human Seal Invariant - final approval is human act"""
    compile_id: str
    actor_did: str
    channel: str
    approved: bool
    human_checks: Dict[str, bool]

# ═══════════════════════════════════════════════════════════════
# COMPILE PROMPTS
# ═══════════════════════════════════════════════════════════════

COMPILE_SYSTEM = """You are a professional content compiler for W-SOCIAL-001.
Your role is to transform professional work output into LinkedIn posts.

TONE: Sophisticated Humility
- Share insights, not proclamations
- "I've been analyzing..." not "The truth is..."
- First person, professional voice
- Actionable takeaways

CONSTRAINTS:
- Max 3000 characters for LinkedIn
- No confidential information
- No client names unless explicitly approved
- No hyperbole or clickbait
- Include the key insight from the source

OUTPUT: Return ONLY the post text, ready to publish. No explanations."""

def build_compile_prompt(intake: dict, channel: str) -> str:
    return f"""Transform this professional work excerpt into a {channel} post:

SOURCE TYPE: {intake['source_type']}
DOCUMENT: {intake['source_title']}
JURISDICTION: {intake.get('jurisdiction', 'EU')}

EXCERPT:
{intake['excerpt']}

Generate a {channel} post (max 3000 chars) that:
1. Shares the key insight from this work
2. Uses first person professional voice
3. Provides actionable context
4. Ends with a thought-provoking observation

Remember: This is real professional work, not synthetic content. Honour the author's expertise."""

# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.get("/", response_class=RedirectResponse)
async def root():
    """Redirect to probe UI"""
    return RedirectResponse(url="/social/static/probe.html")

@app.get("/social/", response_class=RedirectResponse)
async def social_root():
    """Redirect /social/ to probe UI (nginx prefix passthrough)"""
    return RedirectResponse(url="/social/static/probe.html")

@app.get("/social/health")
async def health():
    """Health check"""
    return {
        "service": "W-SOCIAL-001",
        "version": "0.1.0",
        "status": "operational",
        "invariants": ["I-SOC-001", "I-SOC-002", "I-SOC-003"],
        "intakes": len(intakes),
        "compilations": len(compilations),
        "publications": len(publications),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.post("/social/intake")
async def create_intake(req: IntakeRequest):
    """
    I-SOC-001: Provenance Invariant
    Receive authority atom from source module (LAW, Enterprise, Travel)
    """
    # Generate intake ID
    intake_id = f"WI-{uuid.uuid4().hex[:12].upper()}"

    # Verify provenance
    if not req.source_id or not req.excerpt:
        raise HTTPException(
            status_code=400,
            detail="I-SOC-001 VIOLATION: No traceable origin provided"
        )

    # Store intake
    intake = {
        "intake_id": intake_id,
        "actor_did": req.actor_did,
        "source_type": req.source_type,
        "source_id": req.source_id,
        "source_title": req.source_title,
        "content_hash": req.content_hash,
        "excerpt": req.excerpt,
        "doc_type": req.doc_type,
        "jurisdiction": req.jurisdiction,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "status": "captured"
    }
    intakes[intake_id] = intake

    return {
        "intake_id": intake_id,
        "status": "captured",
        "invariant_check": {
            "I-SOC-001": "PASS",
            "reason": "Traceable origin verified"
        },
        "source_ref": req.source_id
    }

@app.post("/social/compile")
async def compile_content(req: CompileRequest):
    """
    Compile intake into channel-ready content
    Uses W-GATEWAY (MED tier) for cost efficiency
    """
    # Get intake
    intake = intakes.get(req.intake_id)
    if not intake:
        raise HTTPException(status_code=404, detail="Intake not found")

    # Build compilation for each channel
    compilations_result = {}

    for channel in req.channels:
        compile_id = f"WC-{uuid.uuid4().hex[:12].upper()}"

        # Call W-GATEWAY for compilation
        prompt = build_compile_prompt(intake, channel)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    GATEWAY_URL,
                    json={
                        "prompt": prompt,
                        "system": COMPILE_SYSTEM,
                        "tier": "MED",  # Cost-efficient
                        "task_type": "social_compile"
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    compiled_text = data.get("response", "")
                else:
                    # Fallback: use excerpt directly
                    compiled_text = f"Insight from my recent work on {intake['source_title']}:\n\n{intake['excerpt'][:500]}..."
        except Exception as e:
            # Fallback on error
            compiled_text = f"Insight from my recent work on {intake['source_title']}:\n\n{intake['excerpt'][:500]}..."

        # Calculate hash of compiled content
        compiled_hash = hashlib.sha256(compiled_text.encode()).hexdigest()[:16].upper()

        # Store compilation
        compilation = {
            "compile_id": compile_id,
            "intake_id": req.intake_id,
            "channel": channel,
            "tone_profile": req.tone_profile,
            "compiled_text": compiled_text,
            "compiled_hash": compiled_hash,
            "char_count": len(compiled_text),
            "created_at": datetime.utcnow().isoformat() + "Z",
            "status": "pending_approval"
        }
        compilations[compile_id] = compilation
        compilations_result[channel] = {
            "compile_id": compile_id,
            "text": compiled_text,
            "char_count": len(compiled_text),
            "hash": compiled_hash
        }

    return {
        "intake_id": req.intake_id,
        "compilations": compilations_result,
        "status": "awaiting_human_approval",
        "next_step": "POST /social/approve"
    }

@app.post("/social/approve")
async def approve_publication(req: ApproveRequest):
    """
    I-SOC-002: Human Seal Invariant
    Final publication approval is a sovereign human act
    """
    # Get compilation
    compilation = compilations.get(req.compile_id)
    if not compilation:
        raise HTTPException(status_code=404, detail="Compilation not found")

    # Verify all human checks
    required_checks = ["reflects_author", "no_confidential", "ledger_consent"]
    for check in required_checks:
        if not req.human_checks.get(check):
            raise HTTPException(
                status_code=400,
                detail=f"I-SOC-002 VIOLATION: Human check '{check}' not confirmed"
            )

    if not req.approved:
        compilation["status"] = "rejected"
        return {"status": "rejected", "compile_id": req.compile_id}

    # Generate seal ID
    seal_id = f"WSC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{compilation['compiled_hash']}"

    # Create publication record
    publication = {
        "seal_id": seal_id,
        "compile_id": req.compile_id,
        "intake_id": compilation["intake_id"],
        "actor_did": req.actor_did,
        "channel": req.channel,
        "compiled_text": compilation["compiled_text"],
        "compiled_hash": compilation["compiled_hash"],
        "human_checks": req.human_checks,
        "approved_at": datetime.utcnow().isoformat() + "Z",
        "governance_mode": "EXPLICIT_HUMAN_APPROVAL",
        "status": "sealed"
    }

    # Seal to Forensic Ledger
    intake = intakes.get(compilation["intake_id"], {})
    ledger_receipt = {
        "id": seal_id,
        "actor": req.actor_did,
        "app": "w-social-001",
        "doc_name": intake.get("source_title", "Social Publication"),
        "doc_type": "social_publication",
        "content_hash": f"sha256:{compilation['compiled_hash']}",
        "governance_level": "EXPLICIT_HUMAN_APPROVAL",
        "source_ref": intake.get("source_id", ""),
        "channel": req.channel,
        "sge_score": 0
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(LEDGER_URL, json=ledger_receipt)
            if response.status_code in [200, 201]:
                publication["ledger_anchor"] = True
            else:
                publication["ledger_anchor"] = False
    except:
        publication["ledger_anchor"] = False

    publications[seal_id] = publication
    compilation["status"] = "published"

    return {
        "seal_id": seal_id,
        "status": "sealed",
        "verify_url": f"https://windi-domain.com/social/verify/{seal_id}",
        "invariant_check": {
            "I-SOC-002": "PASS",
            "I-SOC-003": "PASS" if publication["ledger_anchor"] else "PENDING"
        },
        "channel": req.channel,
        "ledger_anchor": publication["ledger_anchor"]
    }

@app.get("/social/verify/{seal_id}")
async def verify_publication(seal_id: str):
    """
    I-SOC-003: Verification Invariant
    Public proof of publication - no sensitive data exposed
    """
    publication = publications.get(seal_id)
    if not publication:
        raise HTTPException(status_code=404, detail="Publication not found")

    return {
        "seal_id": seal_id,
        "status": "VERIFIED",
        "actor_did": publication["actor_did"],
        "published_at": publication["approved_at"],
        "channel": publication["channel"],
        "governance_mode": publication["governance_mode"],
        "content_hash": f"sha256:{publication['compiled_hash']}",
        "ledger_anchor": publication.get("ledger_anchor", False),
        # NEVER expose: compiled_text, intake excerpt, actor name
    }

@app.get("/social/history/{actor_did}")
async def get_history(actor_did: str):
    """Get publication history for an actor"""
    actor_publications = [
        {
            "seal_id": p["seal_id"],
            "channel": p["channel"],
            "published_at": p["approved_at"],
            "content_hash": p["compiled_hash"]
        }
        for p in publications.values()
        if p["actor_did"] == actor_did
    ]
    return {
        "actor_did": actor_did,
        "publication_count": len(actor_publications),
        "publications": actor_publications
    }

# Mount static files
app.mount("/social/static", StaticFiles(directory="/opt/windi/w-social-001/static"), name="social-static")

# ═══════════════════════════════════════════════════════════════
# STARTUP
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8133)
