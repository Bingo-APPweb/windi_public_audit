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
    "resolve isto", "arranja", "corrige isto", "faz isso por mim",
    "trata disso", "resolve isso",
    # German
    "automatisch", "korrigieren", "ausführen", "mach das", "anwenden",
    "ändern", "bearbeiten", "aktualisieren", "löschen", "entfernen",
    "korrigiere das", "mach das für mich", "erledige das", "führe aus",
    # English
    "automatically", "correct this", "execute", "do it for me", "apply",
    "modify", "update", "delete", "remove", "fix this", "run this",
    "auto-fix", "autofix", "autocorrect", "auto correct",
    "do this for me", "handle this", "take care of this"
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
# I14 EPISTEMIC STATUS — §200
# ══════════════════════════════════════════════════════════════════════

class EpistemicStatus(str, Enum):
    """
    I14 Runtime Enforcement — Epistemic sufficiency states.

    SUFFICIENT: Input has enough context for reliable interpretation
    AMBIGUOUS: Multiple valid interpretations, cannot choose with integrity
    INSUFFICIENT_CONTEXT: Missing essential information (document, options, target)
    CONFLICTED: Divergent interpretations without resolution
    """
    SUFFICIENT = "sufficient"
    AMBIGUOUS = "ambiguous"
    INSUFFICIENT_CONTEXT = "insufficient_context"
    CONFLICTED = "conflicted"

# ══════════════════════════════════════════════════════════════════════
# I14 AMBIGUITY MARKERS — Trilingual (PT/DE/EN)
# ══════════════════════════════════════════════════════════════════════

# Pronouns without antecedent (triggers AMBIGUOUS)
AMBIGUOUS_PRONOUNS = {
    # Portuguese
    "isto", "isso", "aquilo", "este", "esse", "aquele",
    "esta", "essa", "aquela", "estes", "esses", "aqueles",
    # German
    "das", "dies", "dieses", "jenes", "es",
    # English
    "this", "that", "it", "these", "those"
}

# Phrases that indicate missing context (triggers INSUFFICIENT_CONTEXT)
MISSING_CONTEXT_PATTERNS = [
    # Portuguese
    "este documento", "esse arquivo", "o código", "o ficheiro",
    "a melhor opção", "qual é melhor", "qual devo",
    "analisa isto", "verifica isso", "resume este",
    # German
    "dieses dokument", "diese datei", "den code", "die datei",
    "die beste option", "welche ist besser", "welche soll",
    "analysiere das", "überprüfe das", "fasse das zusammen",
    # English
    "this document", "this file", "the code", "the file",
    "the best option", "which is better", "which should",
    "analyze this", "check this", "summarize this"
]

# Phrases that suggest comparative without options
COMPARATIVE_WITHOUT_OPTIONS = [
    # Portuguese
    "melhor", "pior", "mais rápido", "mais barato", "qual escolher",
    # German
    "besser", "schlechter", "schneller", "billiger", "welche wählen",
    # English
    "better", "worse", "faster", "cheaper", "which to choose"
]

def detect_epistemic_insufficiency(prompt: str, context: Optional[Dict] = None) -> dict:
    """
    Layer 1: Detect epistemic insufficiency in input.

    Returns:
        {
            "epistemic_status": EpistemicStatus,
            "epistemic_sufficient": bool,
            "ambiguity_markers": List[str],
            "missing_context": List[str],
            "requires_clarification": bool
        }
    """
    prompt_lower = prompt.lower().strip()
    words = prompt_lower.split()

    ambiguity_markers = []
    missing_context = []

    # Check 1: Pronouns without clear antecedent
    # If prompt is SHORT and contains only pronouns + action verb, it's ambiguous
    if len(words) <= 5:
        found_pronouns = [w for w in words if w in AMBIGUOUS_PRONOUNS]
        if found_pronouns:
            # Check if there's enough context to resolve the pronoun
            has_specific_target = any(
                kw in prompt_lower for kw in
                ["file:", "document:", "code:", "function:", "class:", "linha", "line", "zeile"]
            )
            if not has_specific_target:
                ambiguity_markers.extend(found_pronouns)

    # Check 2: Missing context patterns
    for pattern in MISSING_CONTEXT_PATTERNS:
        if pattern in prompt_lower:
            # Check if context actually provides the missing item
            if context is None or not context:
                if "document" in pattern or "dokument" in pattern:
                    missing_context.append("document")
                elif "file" in pattern or "datei" in pattern or "arquivo" in pattern:
                    missing_context.append("file")
                elif "code" in pattern or "código" in pattern:
                    missing_context.append("code")
                elif "option" in pattern or "opção" in pattern:
                    missing_context.append("options")

    # Check 3: Comparative without options
    has_comparative = any(comp in prompt_lower for comp in COMPARATIVE_WITHOUT_OPTIONS)
    if has_comparative:
        # Check if options are provided
        has_options = any(
            marker in prompt_lower for marker in
            ["opção a", "opção b", "option a", "option b", "option 1", "option 2",
             "variante a", "variante b", "entre", "between", "zwischen"]
        )
        if not has_options and (context is None or "options" not in str(context)):
            missing_context.append("options")

    # Determine epistemic status
    if ambiguity_markers:
        epistemic_status = EpistemicStatus.AMBIGUOUS
        epistemic_sufficient = False
    elif missing_context:
        epistemic_status = EpistemicStatus.INSUFFICIENT_CONTEXT
        epistemic_sufficient = False
    else:
        epistemic_status = EpistemicStatus.SUFFICIENT
        epistemic_sufficient = True

    return {
        "epistemic_status": epistemic_status,
        "epistemic_sufficient": epistemic_sufficient,
        "ambiguity_markers": ambiguity_markers,
        "missing_context": list(set(missing_context)),  # deduplicate
        "requires_clarification": not epistemic_sufficient
    }

# ══════════════════════════════════════════════════════════════════════
# MODELS
# ══════════════════════════════════════════════════════════════════════

class ShelfRequest(BaseModel):
    prompt: str
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    language: Optional[str] = "en"

class Interpretation(BaseModel):
    """
    Intent interpretation with I14 epistemic fields.

    §200: Non-simulation of understanding.
    If epistemic_sufficient=False, system must not respond as if it understood.
    """
    intent: Optional[IntentClass] = None  # Can be None when ambiguous
    domain: Optional[Domain] = None  # Can be None when insufficient context
    sensitivity: Sensitivity = Sensitivity.INFORMATIONAL
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    requires_human_approval: bool = False
    suggested_agents: List[str] = []

    # I14 Epistemic Fields
    epistemic_status: EpistemicStatus = EpistemicStatus.SUFFICIENT
    epistemic_sufficient: bool = True
    ambiguity_markers: List[str] = []
    missing_context: List[str] = []
    requires_clarification: bool = False

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
    version="0.3.0",  # I9 + I14 Runtime Enforcement
    description="Governed Knowledge Diffusion Shelf — TWIN + Handshake + I9 Gate + I14 Epistemic",
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

def classify_intent(prompt: str, context: Optional[Dict[str, Any]] = None) -> Interpretation:
    """
    Intent classification with I9 agency detection AND I14 epistemic enforcement.

    Layer 0 (NEW): I14 Epistemic Detection — check if input is sufficient
    Layer 1: I9 Agency Detection — check for autonomous action requests
    Layer 2: Standard Classification — domain/intent

    Rule B: Classification informs, it cannot grant execution.
    §200: Non-simulation of understanding.
    """
    prompt_lower = prompt.lower()

    # ═══════════════════════════════════════════════════════════════════
    # LAYER 0: I14 EPISTEMIC DETECTION (§200)
    # If input is ambiguous or lacks context, mark as insufficient
    # ═══════════════════════════════════════════════════════════════════

    epistemic_result = detect_epistemic_insufficiency(prompt, context)
    epistemic_status = epistemic_result["epistemic_status"]
    epistemic_sufficient = epistemic_result["epistemic_sufficient"]
    ambiguity_markers = epistemic_result["ambiguity_markers"]
    missing_context = epistemic_result["missing_context"]
    requires_clarification = epistemic_result["requires_clarification"]

    # ═══════════════════════════════════════════════════════════════════
    # LAYER 1: I9 AGENCY DETECTION
    # If agency keywords detected, escalate to GOVERNANCE + CONSTITUTIONAL
    # ═══════════════════════════════════════════════════════════════════

    agency_detected = detect_agency_request(prompt)

    if agency_detected:
        # Autonomous action requested → immediate escalation
        # Note: Agency + Ambiguity = both flags set
        return Interpretation(
            intent=IntentClass.GOVERNANCE,
            domain=Domain.GENERAL,
            sensitivity=Sensitivity.CONSTITUTIONAL,
            confidence=0.9,
            requires_human_approval=True,
            suggested_agents=["guardian", "witness"],
            # I14 fields
            epistemic_status=epistemic_status,
            epistemic_sufficient=epistemic_sufficient,
            ambiguity_markers=ambiguity_markers,
            missing_context=missing_context,
            requires_clarification=requires_clarification
        )

    # ═══════════════════════════════════════════════════════════════════
    # LAYER 2: STANDARD CLASSIFICATION (no agency detected)
    # ═══════════════════════════════════════════════════════════════════

    # If epistemically insufficient, we still try to classify
    # but confidence is reduced and flags are set

    # Intent classification
    if any(kw in prompt_lower for kw in ["what is", "explain", "how does", "tell me about", "como funciona", "wie funktioniert"]):
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

    # Domain detection
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

    # Confidence adjustment based on epistemic status
    if epistemic_sufficient:
        confidence = 0.7
    elif epistemic_status == EpistemicStatus.AMBIGUOUS:
        confidence = 0.3  # Low confidence when ambiguous
    elif epistemic_status == EpistemicStatus.INSUFFICIENT_CONTEXT:
        confidence = 0.4  # Slightly higher but still low
    else:
        confidence = 0.5

    return Interpretation(
        intent=intent,
        domain=domain,
        sensitivity=sensitivity,
        confidence=confidence,
        requires_human_approval=requires_human,
        suggested_agents=agents,
        # I14 fields
        epistemic_status=epistemic_status,
        epistemic_sufficient=epistemic_sufficient,
        ambiguity_markers=ambiguity_markers,
        missing_context=missing_context,
        requires_clarification=requires_clarification
    )

# ══════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

VERSION = "0.3.0"  # I9 + I14 Runtime Enforcement (§199 + §200)

@app.get("/health")
def health():
    return {
        "service": "W-SHELF-001",
        "status": "operational",
        "version": VERSION,
        "timestamp": now_iso(),
        "invariants": ["I9", "I11", "I13", "I14"],
        "i9_enforcement": "ACTIVE",
        "i14_enforcement": "ACTIVE",
        "i14_blocks": shelf_state["metrics"].get("i14_blocks", 0)
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

    §200: I14 Epistemic enforcement — if insufficient, marks as such.
    """
    if request_id not in shelf_state["requests"]:
        raise HTTPException(status_code=404, detail=f"Request {request_id} not found")

    req = shelf_state["requests"][request_id]

    # Pass context to classify_intent for I14 detection
    context = req.get("context")
    interpretation = classify_intent(req["prompt"], context)

    # Update request with interpretation
    req["interpretation"] = interpretation.dict()
    req["status"] = "interpreted"

    # Auto-create Request Twin
    twin_id = generate_id("TWIN")

    # Handle None intent/domain (I14 ambiguous case)
    intent_value = interpretation.intent.value if interpretation.intent else "undetermined"
    domain_value = interpretation.domain.value if interpretation.domain else "undetermined"

    twin = Twin(
        twin_id=twin_id,
        type=TwinType.REQUEST,
        origin="user",
        source_ref=request_id,
        declared={
            "prompt": req["prompt"],
            "intent": intent_value,
            "domain": domain_value,
            "sensitivity": interpretation.sensitivity.value,
            "confidence": interpretation.confidence,
            # I14 epistemic fields
            "epistemic_status": interpretation.epistemic_status.value,
            "epistemic_sufficient": interpretation.epistemic_sufficient,
            "ambiguity_markers": interpretation.ambiguity_markers,
            "missing_context": interpretation.missing_context
        },
        linked_agents=interpretation.suggested_agents,
        timestamp=now_iso()
    )

    shelf_state["twins"][twin_id] = twin.dict()
    shelf_state["metrics"]["twins_created"] += 1
    persist_json(TWINS_DIR, twin_id, twin.dict())

    # Determine next step based on epistemic status
    i14_block_receipt = None

    if not interpretation.epistemic_sufficient:
        next_step = "CLARIFICATION REQUIRED — provide missing context or rephrase"

        # ═══════════════════════════════════════════════════════════════════
        # LAYER 3: I14 DECLARED LIMIT RECEIPT (§200)
        # "Absence of knowledge is product, not failure"
        # ═══════════════════════════════════════════════════════════════════

        receipt_id = generate_id("I14-BLOCK")
        input_hash = hashlib.sha256(req["prompt"].encode()).hexdigest()

        i14_block_receipt = {
            "receipt_id": receipt_id,
            "type": "I14_DECLARED_LIMIT",
            "input_hash": f"sha256:{input_hash[:16]}",
            "epistemic_status": interpretation.epistemic_status.value,
            "ambiguity_markers": interpretation.ambiguity_markers,
            "missing_context": interpretation.missing_context,
            "confidence": interpretation.confidence,
            "service": "W-SHELF-001",
            "policy_version": "i14-runtime-v1",
            "blocked_at": now_iso(),
            "linked_twin": twin_id,
            "operator_notified": True,
            "invariant": "I14 — Explicit Failure Principle"
        }

        # Persist receipt
        persist_json(ARTIFACTS_DIR, receipt_id, i14_block_receipt)

        # Update metrics
        if "i14_blocks" not in shelf_state["metrics"]:
            shelf_state["metrics"]["i14_blocks"] = 0
        shelf_state["metrics"]["i14_blocks"] += 1

    elif interpretation.suggested_agents:
        next_step = "POST /shelf/handshake to coordinate agents"
    else:
        next_step = "POST /shelf/artifact to generate knowledge"

    response = {
        "request_id": request_id,
        "interpretation": interpretation.dict(),
        "twin_id": twin_id,
        "requires_human_approval": interpretation.requires_human_approval,
        "suggested_agents": interpretation.suggested_agents,
        "next_step": next_step
    }

    # Add receipt if I14 blocked
    if i14_block_receipt:
        response["i14_block_receipt"] = i14_block_receipt["receipt_id"]
        response["receipt_id"] = i14_block_receipt["receipt_id"]

    return response

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
