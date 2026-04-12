# ═══════════════════════════════════════════════════════════════════════════
#  agent_transfer_protocol.py — IAT-001
#  VERA · Inter-Agent Transfer Protocol
#  REGO v1.2 · R11 — Recepção de Contexto Inter-Agente
#  Liga IA+H · Human Dragon · 12 Abril 2026
#
#  Princípio R11: "Recebo contexto. Não recebo ordens."
#
#  Agentes que injectam contexto em VERA:
#    GUARDIAN  → riscos legais activos, GDPR flags, citações
#    ARCHITECT → documentos activos, workflow state, decisões abertas
#    WITNESS   → alertas live, anomalias, último seal
#
#  Endpoints expostos em :8150/vera/context/
# ═══════════════════════════════════════════════════════════════════════════

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict, Any
from datetime import datetime, timezone, timedelta
import hashlib
import logging
from collections import deque

log = logging.getLogger("vera.iat001")

# ─── CONTEXT STORE (in-memory, DID-scoped) ───────────────────────────────
# Holds the last N context packets per officer DID
# In production: back with Redis or SQLite for persistence
_context_store: Dict[str, deque] = {}
_MAX_CONTEXT_PER_DID = 20

def _get_store(did: str) -> deque:
    if did not in _context_store:
        _context_store[did] = deque(maxlen=_MAX_CONTEXT_PER_DID)
    return _context_store[did]

# ─── MODELS ──────────────────────────────────────────────────────────────
AgentName = Literal["GUARDIAN", "ARCHITECT", "WITNESS"]
ContextType = Literal[
    "legal_risk",
    "gdpr_flag",
    "article_citation",
    "pending_approval",
    "active_document",
    "workflow_state",
    "open_decision",
    "module_progress",
    "live_alert",
    "anomaly_score",
    "seal_event",
    "obs_timeline",
    "instructor_hint",
    "degraded_capability",
]

class AgentContextPacket(BaseModel):
    """Context packet sent by an agent to VERA."""
    agent:        AgentName
    context_type: ContextType
    officer_did:  str
    payload:      Dict[str, Any]
    priority:     Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM"
    ttl_seconds:  int = 300
    source_module: Optional[str] = None
    timestamp_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class AgentContextResponse(BaseModel):
    accepted:     bool
    packet_id:    str
    vera_summary: str
    queued_for:   str

class VERAContextSnapshot(BaseModel):
    """Full context snapshot for VERA instructor at query time."""
    officer_did:       str
    snapshot_time:     str
    guardian_context:  List[Dict[str, Any]]
    architect_context: List[Dict[str, Any]]
    witness_context:   List[Dict[str, Any]]
    active_alerts:     List[Dict[str, Any]]
    pending_approvals: List[Dict[str, Any]]
    active_documents:  List[Dict[str, Any]]
    module_progress:   Dict[str, Any]
    instructor_hints:  List[str]

# ─── INTERNAL HELPERS ────────────────────────────────────────────────────
def _ttl_to_iso(ttl_seconds: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    return exp.isoformat()

def _summarise_packet(packet: AgentContextPacket) -> str:
    summaries = {
        "legal_risk":        f"Risco legal registado por {packet.agent}",
        "gdpr_flag":         f"Flag GDPR detectada por {packet.agent}",
        "article_citation":  f"Citação legal injectada por {packet.agent}",
        "pending_approval":  f"Aprovação pendente notificada por {packet.agent}",
        "active_document":   f"Documento activo registado por {packet.agent}",
        "workflow_state":    f"Estado de workflow actualizado por {packet.agent}",
        "open_decision":     f"Decisão aberta registada por {packet.agent}",
        "module_progress":   f"Progresso de módulo actualizado por {packet.agent}",
        "live_alert":        f"Alerta live injectado por {packet.agent}",
        "anomaly_score":     f"Score de anomalia actualizado por {packet.agent}",
        "seal_event":        f"Evento de seal registado por {packet.agent}",
        "obs_timeline":      f"Timeline de observação injectada por {packet.agent}",
        "instructor_hint":   f"Hint de instrução enviado por {packet.agent}",
        "degraded_capability": f"Capacidade degradada reportada por {packet.agent}",
    }
    return summaries.get(packet.context_type, f"Contexto {packet.context_type} de {packet.agent}")

def _extract_by_type(packets: List[Dict[str, Any]], types: List[str]) -> List[Dict[str, Any]]:
    return [p["payload"] for p in packets if p.get("context_type") in types]

def _merge_module_progress(architect_packets: List[Dict[str, Any]]) -> Dict[str, Any]:
    progress = {}
    for p in architect_packets:
        if p.get("context_type") == "module_progress":
            progress.update(p.get("payload", {}))
    return progress

def _extract_hints(all_packets: List[Dict[str, Any]]) -> List[str]:
    hints = []
    for p in all_packets:
        if p.get("context_type") == "instructor_hint":
            hint = p.get("payload", {}).get("hint", "")
            if hint:
                hints.append(hint)
    return hints

async def _audit_log(packet_id: str, packet: AgentContextPacket):
    """Background audit logging. I14: every injection is traceable."""
    log.info(
        f"IAT-001 AUDIT | {packet_id} | agent={packet.agent} "
        f"type={packet.context_type} priority={packet.priority} "
        f"did={packet.officer_did[:20]}..."
    )

# ─── ROUTER ──────────────────────────────────────────────────────────────
def create_context_router() -> APIRouter:
    router = APIRouter(prefix="/vera/context", tags=["IAT-001"])

    @router.post("/inject", response_model=AgentContextResponse)
    async def inject_context(
        packet: AgentContextPacket,
        background_tasks: BackgroundTasks
    ):
        """
        IAT-001 main injection endpoint.
        Agents push context here. VERA stores and synthesises.

        R11: VERA receives context, never orders.
        I9:  Context enriches — never triggers autonomous action.
        I14: All context stored explicitly, nothing silently discarded.
        """
        # Validate DID
        if not packet.officer_did or len(packet.officer_did) < 10:
            raise HTTPException(400, "Invalid officer_did — DID required for context injection [I14]")

        # Generate packet ID
        raw = f"{packet.agent}:{packet.context_type}:{packet.officer_did}:{packet.timestamp_utc}"
        packet_id = "IAT-" + hashlib.sha256(raw.encode()).hexdigest()[:12].upper()

        # Store in DID-scoped context store
        store = _get_store(packet.officer_did)
        stored = {
            "packet_id":    packet_id,
            "agent":        packet.agent,
            "context_type": packet.context_type,
            "payload":      packet.payload,
            "priority":     packet.priority,
            "source_module": packet.source_module,
            "timestamp_utc": packet.timestamp_utc,
            "expires_at":   _ttl_to_iso(packet.ttl_seconds),
            "consumed":     False,
        }
        store.append(stored)

        # Async: log to audit trail
        background_tasks.add_task(_audit_log, packet_id, packet)

        # Generate VERA summary for acknowledgement
        summary = _summarise_packet(packet)

        log.info(f"IAT-001 received: {packet_id} from {packet.agent} for {packet.officer_did[:20]}...")

        return AgentContextResponse(
            accepted=True,
            packet_id=packet_id,
            vera_summary=summary,
            queued_for=packet.officer_did,
        )

    @router.get("/snapshot/{officer_did}", response_model=VERAContextSnapshot)
    async def get_context_snapshot(officer_did: str):
        """
        Returns the full context snapshot for a given officer DID.
        Called by VERA instructor at every query to build situational awareness.
        R1: VERA sempre tem contexto. Nunca responde sem saber o estado do desk.
        """
        store = _get_store(officer_did)
        now_iso = datetime.now(timezone.utc).isoformat()

        # Filter non-expired packets
        live = [p for p in store if p.get("expires_at", "9999") > now_iso]

        guardian  = [p for p in live if p["agent"] == "GUARDIAN"]
        architect = [p for p in live if p["agent"] == "ARCHITECT"]
        witness   = [p for p in live if p["agent"] == "WITNESS"]

        # Extract structured fields
        active_alerts     = _extract_by_type(witness,   ["live_alert"])
        pending_approvals = _extract_by_type(guardian,  ["pending_approval"])
        active_documents  = _extract_by_type(architect, ["active_document"])
        module_progress   = _merge_module_progress(architect)
        instructor_hints  = _extract_hints(live)

        return VERAContextSnapshot(
            officer_did       = officer_did,
            snapshot_time     = now_iso,
            guardian_context  = [p["payload"] for p in guardian],
            architect_context = [p["payload"] for p in architect],
            witness_context   = [p["payload"] for p in witness],
            active_alerts     = active_alerts,
            pending_approvals = pending_approvals,
            active_documents  = active_documents,
            module_progress   = module_progress,
            instructor_hints  = instructor_hints,
        )

    @router.delete("/clear/{officer_did}")
    async def clear_context(officer_did: str):
        """
        Clear all context for a DID. Called on session end.
        I14: Cleared explicitly, never silently.
        """
        if officer_did in _context_store:
            count = len(_context_store[officer_did])
            del _context_store[officer_did]
            log.info(f"Context cleared for {officer_did[:20]}: {count} packets removed")
            return {"cleared": True, "packets_removed": count}
        return {"cleared": False, "packets_removed": 0}

    @router.get("/health")
    async def iat_health():
        return {
            "status":       "operational",
            "protocol":     "IAT-001",
            "constitution": "REGO v1.2 · R11",
            "active_dids":  len(_context_store),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
        }

    return router


# ─── AGENT HELPER CLIENTS ────────────────────────────────────────────────
# Use these from other agents to inject context into VERA

import httpx

VERA_CONTEXT_ENDPOINT = "http://localhost:8150/vera/context/inject"

async def guardian_inject(officer_did: str, context_type: str, payload: Dict[str, Any], priority: str = "MEDIUM"):
    """Called by Guardian agent to push legal/compliance context to VERA."""
    packet = {
        "agent": "GUARDIAN",
        "context_type": context_type,
        "officer_did": officer_did,
        "payload": payload,
        "priority": priority,
        "source_module": "guardian",
    }
    async with httpx.AsyncClient(timeout=5) as c:
        r = await c.post(VERA_CONTEXT_ENDPOINT, json=packet)
        return r.json()

async def architect_inject(officer_did: str, context_type: str, payload: Dict[str, Any], priority: str = "MEDIUM"):
    """Called by Architect agent to push structural/workflow context to VERA."""
    packet = {
        "agent": "ARCHITECT",
        "context_type": context_type,
        "officer_did": officer_did,
        "payload": payload,
        "priority": priority,
        "source_module": "architect",
    }
    async with httpx.AsyncClient(timeout=5) as c:
        r = await c.post(VERA_CONTEXT_ENDPOINT, json=packet)
        return r.json()

async def witness_inject(officer_did: str, context_type: str, payload: Dict[str, Any], priority: str = "MEDIUM"):
    """Called by Witness agent to push observation/alert context to VERA."""
    packet = {
        "agent": "WITNESS",
        "context_type": context_type,
        "officer_did": officer_did,
        "payload": payload,
        "priority": priority,
        "source_module": "witness",
    }
    async with httpx.AsyncClient(timeout=5) as c:
        r = await c.post(VERA_CONTEXT_ENDPOINT, json=packet)
        return r.json()
