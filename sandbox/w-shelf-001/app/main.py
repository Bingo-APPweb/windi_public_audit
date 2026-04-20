"""
W-SHELF-001 — Governed Knowledge Diffusion Shelf
Port: 8191
Invariants: I9 (human approval), I11 (proof), I13 (no auto-publish), I14 (explicit failure)

Purpose: Orchestration layer where user prompts are transformed into structured,
routed, governed, and reusable knowledge through TWIN state mirroring and
Handshake-controlled agent coordination.

Codex assists. WINDI governs. Human decides.
"""
import os
import json
import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ══════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════

BASE_DIR = "/opt/windi/sandbox/w-shelf-001"
TWINS_DIR = f"{BASE_DIR}/twins"
HANDSHAKES_DIR = f"{BASE_DIR}/handshakes"
ARTIFACTS_DIR = f"{BASE_DIR}/artifacts"

# Ensure dirs exist
for d in [TWINS_DIR, HANDSHAKES_DIR, ARTIFACTS_DIR]:
    os.makedirs(d, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════
# I9 RUNTIME ENFORCEMENT — CONSTITUTIONAL GATE
# ══════════════════════════════════════════════════════════════════════
# Rule A: Default deny for state change
# Rule B: Classification cannot grant execution
# Rule C: Human approval is explicit, scoped, and ephemeral
# Rule D: "Propose" and "execute" are different species

# Keywords that signal agency/autonomy request — ALWAYS trigger I9
AGENCY_KEYWORDS = [
    # Portuguese
    "automaticamente", "corrigir", "executar", "faz por mim", "aplica",
    "altera", "modifica", "atualiza", "apaga", "remove", "cria automatico",
    "resolve isto", "arranja", "corrige isto",
    # German
    "automatisch", "korrigieren", "ausführen", "mach das", "anwenden",
    "ändern", "bearbeiten", "aktualisieren", "löschen", "entfernen",
    # English
    "automatically", "correct this", "execute", "do it for me", "apply",
    "modify", "update", "delete", "remove", "fix this", "run this",
    "auto-fix", "autofix", "autocorrect", "auto correct"
]

# Scopes that ALWAYS require I9 — no exceptions (fail-closed)
DANGEROUS_SCOPES = [
    "propose_patch",        # Proposing changes
    "execute_with_i9",      # Explicit execution
    "apply",                # Applying changes
    "commit",               # Committing changes
    "seal",                 # Sealing to ledger
    "delete",               # Destructive action
    "modify",               # State modification
    "knowledge_generation"  # Creating new artifacts (must be verified)
]

# Scopes that are safe without I9 (read-only operations)
SAFE_SCOPES = [
    "read_only",
    "analyze",
    "observe"
]

def detect_agency_request(text: str) -> bool:
    """
    Layer 1: Semantic detection of agency/autonomy request.
    Returns True if the text contains any agency keyword.
    """
    text_lower = text.lower()
    return any(kw in text_lower for kw in AGENCY_KEYWORDS)

def scope_requires_i9(scopes: List[str]) -> bool:
    """
    Layer 2: Scope-based I9 requirement.
    If ANY scope is dangerous, I9 is required.
    Rule A: Default deny for state change.
    """
    for scope in scopes:
        # If scope is dangerous, I9 required
        if scope in DANGEROUS_SCOPES:
            return True
        # If scope is unknown (not safe), default to I9 required (fail-closed)
        if scope not in SAFE_SCOPES:
            return True
    return False

# ══════════════════════════════════════════════════════════════════════
# ENUMS
# ══════════════════════════════════════════════════════════════════════

class IntentClass(str, Enum):
    KNOWLEDGE_REQUEST = "knowledge_request"
    SYSTEM_QUESTION = "system_question"
    CODE_CHANGE = "code_change_request"
    GOVERNANCE = "governance_request"
    AUDIT = "audit_request"
    TRANSLATION = "translation_request"
    ARTIFACT = "artifact_request"

class Domain(str, Enum):
    TRAVEL = "travel"
    LAW = "law"
    ENTERPRISE = "enterprise"
    MEDIA = "media"
    LEDGER = "ledger"
    IDENTITY = "identity"
    METRICS = "metrics"
    SECURITY = "security"
    GENERAL = "general"

class Sensitivity(str, Enum):
    INFORMATIONAL = "informational"
    OPERATIONAL = "operational"
    SENSITIVE = "sensitive"
    CONSTITUTIONAL = "constitutional"

class TwinType(str, Enum):
    REQUEST = "request"
    AGENT = "agent"
    STATE = "state"

class TwinStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    DIVERGENT = "divergent"
    SEALED = "sealed"

class HandshakeStatus(str, Enum):
    PROPOSED = "PROPOSED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    SEALED = "SEALED"

# ══════════════════════════════════════════════════════════════════════
# MODELS
# ══════════════════════════════════════════════════════════════════════

class ShelfRequest(BaseModel):
    prompt: str
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    language: Optional[str] = "en"

class Interpretation(BaseModel):
    intent: IntentClass
    domain: Domain
    sensitivity: Sensitivity
    confidence: float = Field(ge=0.0, le=1.0)
    requires_human_approval: bool = False
    suggested_agents: List[str] = []

class Twin(BaseModel):
    twin_id: str
    type: TwinType
    origin: str
    source_ref: str
    declared: Dict[str, Any]
    observed: Optional[Dict[str, Any]] = None
    drift_score: float = 0.0
    status: TwinStatus = TwinStatus.OPEN
    linked_agents: List[str] = []
    timestamp: str
    sealed_at: Optional[str] = None

class Handshake(BaseModel):
    handshake_id: str
    from_agent: str
    to_agent: str
    purpose: str
    scope: List[str]
    status: HandshakeStatus = HandshakeStatus.PROPOSED
    linked_twin: Optional[str] = None
    requires_human_approval: bool = False
    human_approved: Optional[bool] = None
    chain_depth: int = 0
    created_at: str
    expires_at: str
    acknowledged_at: Optional[str] = None
    completed_at: Optional[str] = None

class KnowledgeCard(BaseModel):
    card_id: str
    title: str
    content: str
    source_agents: List[str]
    confidence: float
    linked_twin: str
    linked_handshake: Optional[str] = None
    created_at: str
    tags: List[str] = []

# ══════════════════════════════════════════════════════════════════════
# APP
# ══════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="W-SHELF-001",
    version="0.2.0",  # I9 Runtime Enforcement
    description="Governed Knowledge Diffusion Shelf — TWIN + Handshake Protocol + I9 Gate",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://windi-domain.com", "http://localhost:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ══════════════════════════════════════════════════════════════════════
# IN-MEMORY STATE (MVP — will move to SQLite later)
# ══════════════════════════════════════════════════════════════════════

shelf_state = {
    "requests": {},
    "twins": {},
    "handshakes": {},
    "artifacts": {},
    "metrics": {
        "requests_total": 0,
        "twins_created": 0,
        "handshakes_total": 0,
        "handshakes_accepted": 0,
        "handshakes_rejected": 0,
        "knowledge_cards_generated": 0,
    }
}

# ══════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════

def generate_id(prefix: str) -> str:
    """Generate WINDI-style ID"""
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def persist_json(directory: str, id: str, data: dict):
    """Persist to filesystem for durability"""
    filepath = os.path.join(directory, f"{id}.json")
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

def classify_intent(prompt: str) -> Interpretation:
    """
    Intent classification with I9 agency detection.

    Layer 1: Detect agency keywords FIRST (autonomous action requests)
    Layer 2: Then classify domain/intent

    Rule B: Classification informs, it cannot grant execution.
    """
    prompt_lower = prompt.lower()

    # ═══════════════════════════════════════════════════════════════════
    # LAYER 1: AGENCY DETECTION (I9 pre-check)
    # If agency keywords detected, escalate to GOVERNANCE + CONSTITUTIONAL
    # ═══════════════════════════════════════════════════════════════════

    agency_detected = detect_agency_request(prompt)

    if agency_detected:
        # Autonomous action requested → immediate escalation
        intent = IntentClass.GOVERNANCE  # Not CODE_CHANGE — this is governance
        sensitivity = Sensitivity.CONSTITUTIONAL
        agents = ["guardian", "witness"]  # Guardian validates, Witness observes
        confidence = 0.9  # High confidence in agency detection

        return Interpretation(
            intent=intent,
            domain=Domain.GENERAL,  # Domain is secondary to governance concern
            sensitivity=sensitivity,
            confidence=confidence,
            requires_human_approval=True,  # ALWAYS true for agency
            suggested_agents=agents
        )

    # ═══════════════════════════════════════════════════════════════════
    # LAYER 2: STANDARD CLASSIFICATION (no agency detected)
    # ═══════════════════════════════════════════════════════════════════

    # Intent classification
    if any(kw in prompt_lower for kw in ["what is", "explain", "how does", "tell me about"]):
        intent = IntentClass.KNOWLEDGE_REQUEST
        sensitivity = Sensitivity.INFORMATIONAL
    elif any(kw in prompt_lower for kw in ["code", "fix", "implement", "refactor", "patch"]):
        intent = IntentClass.CODE_CHANGE
        sensitivity = Sensitivity.SENSITIVE
    elif any(kw in prompt_lower for kw in ["audit", "verify", "check", "compliance"]):
        intent = IntentClass.AUDIT
        sensitivity = Sensitivity.OPERATIONAL
    elif any(kw in prompt_lower for kw in ["governance", "constitutional", "invariant", "i9", "i11"]):
        intent = IntentClass.GOVERNANCE
        sensitivity = Sensitivity.CONSTITUTIONAL
    else:
        intent = IntentClass.SYSTEM_QUESTION
        sensitivity = Sensitivity.INFORMATIONAL

    # Domain detection (can return multiple in future)
    domain = Domain.GENERAL
    if "travel" in prompt_lower:
        domain = Domain.TRAVEL
    elif "law" in prompt_lower or "legal" in prompt_lower:
        domain = Domain.LAW
    elif "enterprise" in prompt_lower or "vera" in prompt_lower:
        domain = Domain.ENTERPRISE
    elif "media" in prompt_lower or "video" in prompt_lower:
        domain = Domain.MEDIA
    elif "ledger" in prompt_lower or "receipt" in prompt_lower:
        domain = Domain.LEDGER
    elif "identity" in prompt_lower or "did" in prompt_lower:
        domain = Domain.IDENTITY
    elif "metrics" in prompt_lower or "truth" in prompt_lower:
        domain = Domain.METRICS
    elif "security" in prompt_lower or "sec" in prompt_lower:
        domain = Domain.SECURITY

    # Agent routing
    agents = ["witness"]
    if intent == IntentClass.CODE_CHANGE:
        agents = ["architect", "guardian", "codex"]
    elif intent == IntentClass.GOVERNANCE:
        agents = ["guardian", "witness"]
    elif domain == Domain.METRICS:
        agents = ["metrics-agent", "witness"]

    # I9 requirement based on sensitivity
    requires_human = sensitivity in [Sensitivity.SENSITIVE, Sensitivity.CONSTITUTIONAL]

    return Interpretation(
        intent=intent,
        domain=domain,
        sensitivity=sensitivity,
        confidence=0.7,  # MVP: fixed confidence for non-agency
        requires_human_approval=requires_human,
        suggested_agents=agents
    )

# ══════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

VERSION = "0.2.0"  # I9 Runtime Enforcement

@app.get("/health")
def health():
    return {
        "service": "W-SHELF-001",
        "status": "operational",
        "version": VERSION,
        "timestamp": now_iso(),
        "invariants": ["I9", "I11", "I13", "I14"],
        "i9_enforcement": "ACTIVE"  # New field indicating I9 runtime enforcement
    }

@app.get("/metrics")
def metrics():
    return {
        "shelf": shelf_state["metrics"],
        "open_twins": sum(1 for t in shelf_state["twins"].values() if t["status"] == "open"),
        "pending_handshakes": sum(1 for h in shelf_state["handshakes"].values() if h["status"] == "PROPOSED"),
        "timestamp": now_iso()
    }

# ── REQUEST INTAKE ─────────────────────────────────────────────────────

@app.post("/shelf/request")
def intake_request(req: ShelfRequest):
    """
    Intake a user prompt and create initial request object.
    """
    request_id = generate_id("REQ")

    request_obj = {
        "request_id": request_id,
        "prompt": req.prompt,
        "context": req.context,
        "user_id": req.user_id,
        "language": req.language,
        "status": "received",
        "created_at": now_iso()
    }

    shelf_state["requests"][request_id] = request_obj
    shelf_state["metrics"]["requests_total"] += 1

    return {
        "request_id": request_id,
        "status": "received",
        "next_step": "POST /shelf/interpret with request_id"
    }

# ── INTERPRETATION ─────────────────────────────────────────────────────

@app.post("/shelf/interpret/{request_id}")
def interpret_request(request_id: str):
    """
    Classify intent, domain, sensitivity of a request.
    Creates a Request Twin automatically.
    """
    if request_id not in shelf_state["requests"]:
        raise HTTPException(status_code=404, detail=f"Request {request_id} not found")

    req = shelf_state["requests"][request_id]
    interpretation = classify_intent(req["prompt"])

    # Update request with interpretation
    req["interpretation"] = interpretation.dict()
    req["status"] = "interpreted"

    # Auto-create Request Twin
    twin_id = generate_id("TWIN")
    twin = Twin(
        twin_id=twin_id,
        type=TwinType.REQUEST,
        origin="user",
        source_ref=request_id,
        declared={
            "prompt": req["prompt"],
            "intent": interpretation.intent.value,
            "domain": interpretation.domain.value,
            "sensitivity": interpretation.sensitivity.value,
            "confidence": interpretation.confidence
        },
        linked_agents=interpretation.suggested_agents,
        timestamp=now_iso()
    )

    shelf_state["twins"][twin_id] = twin.dict()
    shelf_state["metrics"]["twins_created"] += 1
    persist_json(TWINS_DIR, twin_id, twin.dict())

    return {
        "request_id": request_id,
        "interpretation": interpretation.dict(),
        "twin_id": twin_id,
        "requires_human_approval": interpretation.requires_human_approval,
        "suggested_agents": interpretation.suggested_agents,
        "next_step": "POST /shelf/handshake to coordinate agents" if interpretation.suggested_agents else "POST /shelf/artifact to generate knowledge"
    }

# ── TWIN MANAGEMENT ────────────────────────────────────────────────────

class CreateTwinRequest(BaseModel):
    type: TwinType
    origin: str
    source_ref: str
    declared: Dict[str, Any]

@app.post("/shelf/twin")
def create_twin(req: CreateTwinRequest):
    """
    Create a new TWIN (manual creation for agent/state twins).
    """
    type = req.type
    origin = req.origin
    source_ref = req.source_ref
    declared = req.declared
    twin_id = generate_id("TWIN")
    twin = Twin(
        twin_id=twin_id,
        type=type,
        origin=origin,
        source_ref=source_ref,
        declared=declared,
        timestamp=now_iso()
    )

    shelf_state["twins"][twin_id] = twin.dict()
    shelf_state["metrics"]["twins_created"] += 1
    persist_json(TWINS_DIR, twin_id, twin.dict())

    return twin.dict()

@app.get("/shelf/twin/{twin_id}")
def get_twin(twin_id: str):
    if twin_id not in shelf_state["twins"]:
        raise HTTPException(status_code=404, detail=f"Twin {twin_id} not found")
    return shelf_state["twins"][twin_id]

@app.patch("/shelf/twin/{twin_id}/observe")
def observe_twin(twin_id: str, observed: Dict[str, Any]):
    """
    Update observed state and compute drift.
    """
    if twin_id not in shelf_state["twins"]:
        raise HTTPException(status_code=404, detail=f"Twin {twin_id} not found")

    twin = shelf_state["twins"][twin_id]
    twin["observed"] = observed

    # Simple drift calculation (MVP)
    declared_keys = set(twin["declared"].keys())
    observed_keys = set(observed.keys())
    matching = declared_keys.intersection(observed_keys)

    if matching:
        matches = sum(1 for k in matching if twin["declared"].get(k) == observed.get(k))
        twin["drift_score"] = 1.0 - (matches / len(matching))

    if twin["drift_score"] > 0.3:
        twin["status"] = "divergent"

    persist_json(TWINS_DIR, twin_id, twin)

    return {
        "twin_id": twin_id,
        "drift_score": twin["drift_score"],
        "status": twin["status"]
    }

# ── HANDSHAKE PROTOCOL ─────────────────────────────────────────────────

@app.post("/shelf/handshake")
def create_handshake(
    from_agent: str = Query(...),
    to_agent: str = Query(...),
    purpose: str = Query(...),
    scope: List[str] = Query(...),
    linked_twin: Optional[str] = Query(None),
    requires_human_approval: bool = Query(False),
    ttl_minutes: int = Query(60)
):
    """
    Propose a handshake between agents.

    I9 Enforcement Layer 2: Scope-based escalation.
    Rule A: Default deny for state change.
    """
    handshake_id = generate_id("HS")

    # ═══════════════════════════════════════════════════════════════════
    # SCOPE-BASED I9 ESCALATION
    # If ANY scope is dangerous, I9 is FORCED regardless of request
    # Rule B: Classification cannot grant execution
    # ═══════════════════════════════════════════════════════════════════

    i9_required_by_scope = scope_requires_i9(scope)
    final_requires_human = requires_human_approval or i9_required_by_scope

    # Also check linked twin for agency detection
    if linked_twin and linked_twin in shelf_state["twins"]:
        twin = shelf_state["twins"][linked_twin]
        if twin.get("declared", {}).get("sensitivity") == "constitutional":
            final_requires_human = True

    handshake = Handshake(
        handshake_id=handshake_id,
        from_agent=from_agent,
        to_agent=to_agent,
        purpose=purpose,
        scope=scope,
        linked_twin=linked_twin,
        requires_human_approval=final_requires_human,  # Use escalated value
        created_at=now_iso(),
        expires_at=(datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)).isoformat()
    )

    shelf_state["handshakes"][handshake_id] = handshake.dict()
    shelf_state["metrics"]["handshakes_total"] += 1
    persist_json(HANDSHAKES_DIR, handshake_id, handshake.dict())

    return {
        "handshake_id": handshake_id,
        "status": "PROPOSED",
        "requires_human_approval": final_requires_human,
        "i9_escalated_by_scope": i9_required_by_scope,
        "dangerous_scopes": [s for s in scope if s in DANGEROUS_SCOPES],
        "expires_at": handshake.expires_at,
        "next_step": f"PATCH /shelf/handshake/{handshake_id}/accept or /reject"
    }

@app.get("/shelf/handshake/{handshake_id}")
def get_handshake(handshake_id: str):
    if handshake_id not in shelf_state["handshakes"]:
        raise HTTPException(status_code=404, detail=f"Handshake {handshake_id} not found")
    return shelf_state["handshakes"][handshake_id]

@app.patch("/shelf/handshake/{handshake_id}/accept")
def accept_handshake(handshake_id: str, human_approved: bool = False):
    """
    Accept a handshake with I9 Runtime Enforcement.

    Layer 3: Enforcement at accept() — fail-closed.

    Rule A: Default deny for state change
    Rule C: Human approval is explicit, scoped, and ephemeral
    Rule D: "Propose" and "execute" are different species
    """
    if handshake_id not in shelf_state["handshakes"]:
        raise HTTPException(status_code=404, detail=f"Handshake {handshake_id} not found")

    hs = shelf_state["handshakes"][handshake_id]
    scope = hs.get("scope", [])

    # ═══════════════════════════════════════════════════════════════════
    # LAYER 3: FAIL-CLOSED I9 ENFORCEMENT
    # Even if requires_human_approval was set to False incorrectly,
    # we re-check scope at accept() time.
    # Rule A: Default deny for state change.
    # ═══════════════════════════════════════════════════════════════════

    # Re-validate scope at accept time (fail-closed)
    scope_needs_i9 = scope_requires_i9(scope)

    # I9 Gate — two conditions that require human_approved=true:
    # 1. requires_human_approval flag was set (from classification or scope escalation)
    # 2. scope contains dangerous operations (re-checked here, fail-closed)

    i9_required = hs["requires_human_approval"] or scope_needs_i9

    if i9_required and not human_approved:
        # Log the violation attempt
        dangerous = [s for s in scope if s in DANGEROUS_SCOPES]
        raise HTTPException(
            status_code=403,
            detail={
                "error": "I9 VIOLATION",
                "message": "This handshake requires human_approved=true",
                "reason": "scope_contains_dangerous_operations" if scope_needs_i9 else "flagged_requires_human",
                "dangerous_scopes": dangerous,
                "hint": f"Call PATCH /shelf/handshake/{handshake_id}/accept?human_approved=true",
                "invariant": "I9 — Human Approval Gate (NON-NEGOTIABLE)"
            }
        )

    # Check expiry
    if datetime.fromisoformat(hs["expires_at"].replace("Z", "+00:00")) < datetime.now(timezone.utc):
        hs["status"] = "EXPIRED"
        persist_json(HANDSHAKES_DIR, handshake_id, hs)
        raise HTTPException(status_code=410, detail="Handshake expired")

    hs["status"] = "ACCEPTED"
    hs["human_approved"] = human_approved
    hs["i9_enforced"] = i9_required  # Track that I9 was enforced
    hs["acknowledged_at"] = now_iso()
    shelf_state["metrics"]["handshakes_accepted"] += 1
    persist_json(HANDSHAKES_DIR, handshake_id, hs)

    return {
        "handshake_id": handshake_id,
        "status": "ACCEPTED",
        "scope": hs["scope"],
        "i9_enforced": i9_required,
        "human_approved": human_approved
    }

@app.patch("/shelf/handshake/{handshake_id}/reject")
def reject_handshake(handshake_id: str, reason: str = ""):
    if handshake_id not in shelf_state["handshakes"]:
        raise HTTPException(status_code=404, detail=f"Handshake {handshake_id} not found")

    hs = shelf_state["handshakes"][handshake_id]
    hs["status"] = "REJECTED"
    hs["rejection_reason"] = reason
    hs["completed_at"] = now_iso()
    shelf_state["metrics"]["handshakes_rejected"] += 1
    persist_json(HANDSHAKES_DIR, handshake_id, hs)

    return {"handshake_id": handshake_id, "status": "REJECTED", "reason": reason}

# ── KNOWLEDGE ARTIFACT ─────────────────────────────────────────────────

class CreateArtifactRequest(BaseModel):
    title: str
    content: str
    source_agents: List[str]
    linked_twin: str
    linked_handshake: Optional[str] = None
    confidence: float = 0.8
    tags: List[str] = []

@app.post("/shelf/artifact")
def create_artifact(req: CreateArtifactRequest):
    """
    Generate a Knowledge Card artifact.
    """
    if req.linked_twin not in shelf_state["twins"]:
        raise HTTPException(status_code=404, detail=f"Twin {linked_twin} not found")

    card_id = generate_id("CARD")

    card = KnowledgeCard(
        card_id=card_id,
        title=req.title,
        content=req.content,
        source_agents=req.source_agents,
        confidence=req.confidence,
        linked_twin=req.linked_twin,
        linked_handshake=req.linked_handshake,
        created_at=now_iso(),
        tags=req.tags
    )

    shelf_state["artifacts"][card_id] = card.dict()
    shelf_state["metrics"]["knowledge_cards_generated"] += 1
    persist_json(ARTIFACTS_DIR, card_id, card.dict())

    # Mark twin as resolved
    twin = shelf_state["twins"][req.linked_twin]
    twin["status"] = "resolved"
    persist_json(TWINS_DIR, req.linked_twin, twin)

    return {
        "card_id": card_id,
        "title": req.title,
        "linked_twin": req.linked_twin,
        "status": "generated"
    }

@app.get("/shelf/artifact/{card_id}")
def get_artifact(card_id: str):
    if card_id not in shelf_state["artifacts"]:
        raise HTTPException(status_code=404, detail=f"Artifact {card_id} not found")
    return shelf_state["artifacts"][card_id]

@app.get("/shelf/artifacts")
def list_artifacts(limit: int = 20):
    """List recent knowledge cards."""
    cards = list(shelf_state["artifacts"].values())
    cards.sort(key=lambda x: x["created_at"], reverse=True)
    return {"artifacts": cards[:limit], "total": len(cards)}

# ══════════════════════════════════════════════════════════════════════
# CODEX MOCK — Intelligent Simulation (Phase B)
# ══════════════════════════════════════════════════════════════════════

# Codex mock metrics
codex_mock_state = {
    "assists_total": 0,
    "assists_used": 0,
    "total_confidence_gain": 0.0,
    "by_agent": {},
    "by_intent": {}
}

class CodexAssistRequest(BaseModel):
    intent: str
    agent_role: str
    context: str
    goal: Optional[str] = "increase precision"
    linked_twin: Optional[str] = None
    linked_handshake: Optional[str] = None

class CodexAssistResponse(BaseModel):
    assist_id: str
    refinements: List[str]
    missing_points: List[str]
    confidence_adjustment: float
    risks: List[str]
    suggested_improvements: List[str]
    reasoning: str
    mock: bool = True
    timestamp: str

def codex_assist_mock(req: CodexAssistRequest) -> CodexAssistResponse:
    """
    Intelligent mock that simulates Codex cognitive assistance.
    Returns structured refinements based on context analysis.
    """
    context_lower = req.context.lower()
    intent = req.intent
    agent = req.agent_role

    refinements = []
    missing_points = []
    risks = []
    improvements = []
    confidence_adj = 0.0
    reasoning = ""

    # ── DOMAIN-SPECIFIC LOGIC ──────────────────────────────────────────

    # Governance / Constitutional
    if any(kw in context_lower for kw in ["i9", "i11", "invariant", "constitutional", "governance"]):
        refinements.append("Clarify which specific invariant applies to this context")
        missing_points.append("No explicit mention of human approval gate (I9)")
        improvements.append("Add reference to constitutional documentation")
        confidence_adj += 0.15
        reasoning = "Constitutional context detected — governance precision increased"

    # Ledger / Forensic
    if any(kw in context_lower for kw in ["ledger", "receipt", "seal", "forensic", "proof"]):
        refinements.append("Specify receipt format: WINDI-[TYPE]-[TIMESTAMP]-[HASH]")
        missing_points.append("No verification URL provided")
        improvements.append("Include /verify-public/ link for proof chain")
        confidence_adj += 0.12
        reasoning = "Forensic context detected — proof precision increased"

    # Travel / Map
    if any(kw in context_lower for kw in ["travel", "map", "journey", "location"]):
        refinements.append("Consider I16 (Creator Cartographic Sovereignty)")
        missing_points.append("GPS privacy implications not addressed")
        improvements.append("Add opt-in publication note")
        confidence_adj += 0.10
        reasoning = "Travel context detected — sovereignty awareness added"

    # Enterprise / VERA
    if any(kw in context_lower for kw in ["enterprise", "vera", "compliance", "eu ai act"]):
        refinements.append("Reference Erdbeere Protocol for anti-hallucination")
        missing_points.append("No confidence estimation provided")
        improvements.append("Add VERA disclaimer: 'VERA informs. Human decides.'")
        confidence_adj += 0.14
        reasoning = "Enterprise context detected — compliance rigor increased"

    # Code / Technical
    if any(kw in context_lower for kw in ["code", "patch", "refactor", "implement", "fix"]):
        refinements.append("Verify sandbox isolation before execution")
        risks.append("Code changes require I9 human approval")
        improvements.append("Add dry-run verification step")
        confidence_adj += 0.08
        reasoning = "Code context detected — safety checks added"

    # Metrics / Truth
    if any(kw in context_lower for kw in ["metrics", "truth", "drift", "health"]):
        refinements.append("Reference /api/truth for canonical state")
        missing_points.append("No drift threshold specified")
        improvements.append("Include AMBER/GREEN/RED status interpretation")
        confidence_adj += 0.11
        reasoning = "Metrics context detected — observability improved"

    # ── AGENT-SPECIFIC ADJUSTMENTS ─────────────────────────────────────

    if agent == "witness":
        refinements.append("Frame response as observation, not judgment")
        reasoning += " | Witness role: narrative framing applied"

    elif agent == "guardian":
        refinements.append("Validate against constitutional boundaries")
        risks.append("Ensure no invariant violation")
        reasoning += " | Guardian role: protection lens applied"

    elif agent == "architect":
        improvements.append("Consider system-wide implications")
        reasoning += " | Architect role: structural view applied"

    # ── FALLBACK (no specific context) ─────────────────────────────────

    if not refinements and not missing_points:
        refinements.append("Context is generic — consider adding domain specificity")
        missing_points.append("No WINDI-specific references detected")
        improvements.append("Link to relevant § section in CLAUDE.md")
        confidence_adj = 0.05
        reasoning = "Generic context — minimal enhancement applied"

    # ── BUILD RESPONSE ─────────────────────────────────────────────────

    assist_id = f"ASSIST-{uuid.uuid4().hex[:8].upper()}"

    return CodexAssistResponse(
        assist_id=assist_id,
        refinements=refinements,
        missing_points=missing_points,
        confidence_adjustment=round(confidence_adj, 2),
        risks=risks,
        suggested_improvements=improvements,
        reasoning=reasoning,
        mock=True,
        timestamp=now_iso()
    )

@app.post("/shelf/codex/assist")
def codex_assist_endpoint(req: CodexAssistRequest):
    """
    Codex cognitive assistance (MOCK mode).
    Simulates intelligent refinement without external API calls.

    When ready for production: swap mock for real OpenAI/Anthropic calls.
    """
    # Validate handshake if provided
    if req.linked_handshake:
        if req.linked_handshake not in shelf_state["handshakes"]:
            raise HTTPException(status_code=404, detail=f"Handshake {req.linked_handshake} not found")
        hs = shelf_state["handshakes"][req.linked_handshake]
        if hs["status"] != "ACCEPTED":
            raise HTTPException(status_code=403, detail=f"Handshake {req.linked_handshake} not accepted")

    # Run mock
    result = codex_assist_mock(req)

    # Update metrics
    codex_mock_state["assists_total"] += 1
    if result.refinements or result.missing_points:
        codex_mock_state["assists_used"] += 1
    codex_mock_state["total_confidence_gain"] += result.confidence_adjustment

    # Track by agent
    if req.agent_role not in codex_mock_state["by_agent"]:
        codex_mock_state["by_agent"][req.agent_role] = 0
    codex_mock_state["by_agent"][req.agent_role] += 1

    # Track by intent
    if req.intent not in codex_mock_state["by_intent"]:
        codex_mock_state["by_intent"][req.intent] = 0
    codex_mock_state["by_intent"][req.intent] += 1

    return result

@app.get("/shelf/codex/metrics")
def codex_metrics():
    """Codex assistance metrics (mock mode)."""
    return {
        "mode": "MOCK",
        "assists_total": codex_mock_state["assists_total"],
        "assists_used": codex_mock_state["assists_used"],
        "usage_rate": round(codex_mock_state["assists_used"] / max(1, codex_mock_state["assists_total"]), 2),
        "total_confidence_gain": round(codex_mock_state["total_confidence_gain"], 2),
        "avg_confidence_gain": round(codex_mock_state["total_confidence_gain"] / max(1, codex_mock_state["assists_total"]), 3),
        "by_agent": codex_mock_state["by_agent"],
        "by_intent": codex_mock_state["by_intent"],
        "ready_for_production": False,
        "timestamp": now_iso()
    }

# ══════════════════════════════════════════════════════════════════════
# STARTUP
# ══════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def on_startup():
    print(f"[W-SHELF-001] Governed Knowledge Diffusion Shelf")
    print(f"[W-SHELF-001] Port: 8191 | Invariants: I9, I11, I13, I14")
    print(f"[W-SHELF-001] TWIN + Handshake Protocol Active")
    print(f"[W-SHELF-001] Codex assists. WINDI governs. Human decides.")
    print(f"[W-SHELF-001] 🟢 LIVE — {now_iso()}")

# ══════════════════════════════════════════════════════════════════════
# RUN
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8191, reload=False)
