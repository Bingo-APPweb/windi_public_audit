"""
W-INTENT-CMD — Director-as-a-Service
Orquestração por Intenção · O Cérebro do WINDI

Port: 8141
Liga IA+H · Kempten, Bavaria · 2026
"AI processes. Human decides. WINDI guarantees."

Architecture:
- Receives intent (natural language or structured command)
- Parses into processing recipe (DSL)
- Chains services: CLASSIFY → VISION → OBS-GATE → LEDGER
- I9 Gate: Always returns to human for final approval

"O Dragão está a aprender a dar ordens."
"""

import os
import json
import httpx
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configuration
PORT = int(os.environ.get("INTENT_CMD_PORT", 8141))
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

# Service URLs
VD_CUT_URL = os.environ.get("VD_CUT_URL", "http://localhost:8128")
LEDGER_URL = os.environ.get("LEDGER_URL", "http://localhost:8101")

# Logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
log = logging.getLogger("w-intent-cmd")

# FastAPI App
app = FastAPI(
    title="W-INTENT-CMD",
    description="Director-as-a-Service · Orquestração por Intenção",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Intent Vocabulary (DSL) =====

@dataclass
class IntentDefinition:
    """Definition of a recognized intent."""
    id: str
    triggers: List[str]  # Natural language triggers
    description: str
    services: List[str]  # Services to chain
    scene: Optional[str] = None  # Default scene template
    requires_i9: bool = True  # Always true for now


INTENT_VOCABULARY: Dict[str, IntentDefinition] = {
    "pitch_berlin": IntentDefinition(
        id="pitch_berlin",
        triggers=["pitch", "berlim", "berlin", "investidor", "investor", "apresentação"],
        description="Prepara vídeo para Pitch de Investidor (Berlim Q2 2026)",
        services=["classify", "vision", "compose"],
        scene="berlin_pitch",
        requires_i9=True
    ),
    "forensic_seal": IntentDefinition(
        id="forensic_seal",
        triggers=["forense", "forensic", "prova", "evidence", "legal", "tribunal"],
        description="Análise forense completa com selo de prova",
        services=["classify", "vision", "compose"],
        scene="forensic",
        requires_i9=True
    ),
    "quick_verify": IntentDefinition(
        id="quick_verify",
        triggers=["verifica", "verify", "check", "autêntico", "authentic"],
        description="Verificação rápida de autenticidade",
        services=["vision"],
        scene=None,
        requires_i9=False  # Only analysis, no seal
    ),
    "broadcast_ready": IntentDefinition(
        id="broadcast_ready",
        triggers=["tv", "broadcast", "transmissão", "televisão"],
        description="Prepara vídeo para transmissão TV",
        services=["classify", "vision", "compose"],
        scene="broadcast",
        requires_i9=True
    ),
    "social_share": IntentDefinition(
        id="social_share",
        triggers=["social", "instagram", "tiktok", "redes", "partilhar", "share"],
        description="Prepara vídeo para redes sociais",
        services=["compose"],
        scene="social",
        requires_i9=True
    ),
    "clean_seal": IntentDefinition(
        id="clean_seal",
        triggers=["simples", "simple", "clean", "minimo", "minimal", "qr"],
        description="Selo mínimo com QR de verificação",
        services=["compose"],
        scene="clean",
        requires_i9=True
    )
}


# ===== Request/Response Models =====

class IntentRequest(BaseModel):
    """Request to execute an intent."""
    intent: Optional[str] = None  # Intent ID or natural language
    asset_id: str
    project_id: str
    params: Optional[Dict[str, Any]] = None  # Additional parameters
    dry_run: bool = False  # If true, only parse and return plan


class IntentParseRequest(BaseModel):
    """Request to parse natural language into intent."""
    text: str


@dataclass
class ExecutionStep:
    """A step in the execution plan."""
    service: str
    endpoint: str
    status: str  # pending, running, completed, failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class ExecutionPlan:
    """Complete execution plan for an intent."""
    intent_id: str
    intent_description: str
    asset_id: str
    project_id: str
    scene: Optional[str]
    steps: List[Dict[str, Any]]
    requires_i9: bool
    created_at: str


# ===== Intent Parsing =====

def parse_intent(text: str) -> Optional[IntentDefinition]:
    """
    Parse natural language text into a recognized intent.

    Uses simple keyword matching. Future: LLM-based parsing.
    """
    text_lower = text.lower()

    # Score each intent by trigger matches
    best_match = None
    best_score = 0

    for intent_id, intent_def in INTENT_VOCABULARY.items():
        score = sum(1 for trigger in intent_def.triggers if trigger in text_lower)
        if score > best_score:
            best_score = score
            best_match = intent_def

    return best_match if best_score > 0 else None


def get_intent_by_id(intent_id: str) -> Optional[IntentDefinition]:
    """Get intent definition by ID."""
    return INTENT_VOCABULARY.get(intent_id)


# ===== Service Calls =====

async def call_classify(asset_id: str, project_id: str) -> Dict[str, Any]:
    """Call W-CLASSIFY-001 for content classification."""
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{VD_CUT_URL}/vd-cut/classify",
            data={"project_id": project_id, "asset_id": asset_id}
        )
        if response.status_code != 200:
            raise Exception(f"Classify failed: {response.text}")
        return response.json()


async def call_vision(asset_id: str, project_id: str) -> Dict[str, Any]:
    """Call W-VISION-001 for forensic analysis."""
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{VD_CUT_URL}/vd-cut/describe",
            data={"project_id": project_id, "asset_id": asset_id}
        )
        if response.status_code != 200:
            raise Exception(f"Vision failed: {response.text}")
        return response.json()


async def call_compose(
    asset_id: str,
    project_id: str,
    scene: str,
    verdict: str = "WINDI VERIFIED"
) -> Dict[str, Any]:
    """Call W-OBS-GATE for video composition."""
    async with httpx.AsyncClient(timeout=300) as client:
        response = await client.post(
            f"{VD_CUT_URL}/vd-cut/compose",
            data={
                "project_id": project_id,
                "asset_id": asset_id,
                "scene": scene,
                "verdict": verdict
            }
        )
        if response.status_code != 200:
            raise Exception(f"Compose failed: {response.text}")
        return response.json()


# ===== Execution Engine =====

async def execute_intent(
    intent: IntentDefinition,
    asset_id: str,
    project_id: str,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute an intent by chaining the required services.

    Returns execution results for I9 Gate approval.
    """
    start_time = datetime.now(timezone.utc)
    results = {
        "intent_id": intent.id,
        "intent_description": intent.description,
        "asset_id": asset_id,
        "project_id": project_id,
        "scene": intent.scene,
        "steps": [],
        "requires_i9": intent.requires_i9,
        "started_at": start_time.isoformat()
    }

    # Determine verdict based on params or default
    verdict = "WINDI VERIFIED"
    if params:
        if params.get("price"):
            verdict = f"VERIFIED · {params['price']}"
        if params.get("city"):
            verdict = f"{verdict} · {params['city']}"

    # Execute each service in the chain
    for service in intent.services:
        step = {"service": service, "status": "running"}

        try:
            if service == "classify":
                log.info(f"Executing CLASSIFY for {asset_id}")
                result = await call_classify(asset_id, project_id)
                step["status"] = "completed"
                step["result"] = {
                    "recommendations": len(result.get("recommendations", [])),
                    "metadata": result.get("metadata_summary", {}),
                    "can_proceed": result.get("can_proceed_to_seal", True)
                }

            elif service == "vision":
                log.info(f"Executing VISION for {asset_id}")
                result = await call_vision(asset_id, project_id)
                step["status"] = "completed"
                step["result"] = {
                    "manipulation_score": result.get("manipulation_score", 0),
                    "sensor_consistency": result.get("sensor_consistency", 0),
                    "verdict": result.get("verdict", "UNKNOWN"),
                    "sampled_frames": result.get("sampled_frames", 0)
                }
                # Update verdict based on vision analysis
                if result.get("verdict") == "LIKELY_AUTHENTIC":
                    verdict = f"AUTHENTIC · {verdict}"
                elif result.get("verdict") == "REVIEW_RECOMMENDED":
                    verdict = f"REVIEW · {verdict}"

            elif service == "compose":
                log.info(f"Executing COMPOSE ({intent.scene}) for {asset_id}")
                result = await call_compose(
                    asset_id, project_id,
                    intent.scene or "clean",
                    verdict
                )
                step["status"] = "completed"
                step["result"] = {
                    "output_path": result.get("output_path"),
                    "output_hash": result.get("output_hash"),
                    "overlays_applied": result.get("overlays_applied", []),
                    "receipt_id": result.get("receipt_id"),
                    "verify_url": result.get("verify_url"),
                    "composition_ms": result.get("composition_ms")
                }

        except Exception as e:
            log.error(f"Service {service} failed: {e}")
            step["status"] = "failed"
            step["error"] = str(e)

        results["steps"].append(step)

        # Stop on failure
        if step["status"] == "failed":
            break

    # Calculate total time
    end_time = datetime.now(timezone.utc)
    results["completed_at"] = end_time.isoformat()
    results["total_ms"] = (end_time - start_time).total_seconds() * 1000

    # Determine overall status
    failed_steps = [s for s in results["steps"] if s["status"] == "failed"]
    if failed_steps:
        results["status"] = "failed"
        results["error"] = failed_steps[0].get("error")
    else:
        results["status"] = "ready_for_i9" if intent.requires_i9 else "completed"

    # Add I9 prompt if required
    if intent.requires_i9 and results["status"] == "ready_for_i9":
        compose_step = next((s for s in results["steps"] if s["service"] == "compose"), None)
        if compose_step and compose_step.get("result"):
            results["i9_prompt"] = {
                "message": f"Comandante, o vídeo está pronto para '{intent.description}'. Autoriza o selo?",
                "preview_path": compose_step["result"].get("output_path"),
                "receipt_id": compose_step["result"].get("receipt_id"),
                "verify_url": compose_step["result"].get("verify_url"),
                "actions": ["SEAL", "DISCARD", "EDIT"]
            }

    return results


# ===== API Endpoints =====

@app.get("/")
async def root():
    return {
        "service": "W-INTENT-CMD",
        "version": "1.0.0",
        "description": "Director-as-a-Service · Orquestração por Intenção",
        "status": "operational",
        "doctrine": "AI processes. Human decides. WINDI guarantees."
    }


@app.get("/intent-cmd/health")
async def health():
    """Health check for W-INTENT-CMD."""
    return {
        "status": "healthy",
        "service": "W-INTENT-CMD",
        "version": "1.0.0",
        "port": PORT,
        "vocabulary_size": len(INTENT_VOCABULARY),
        "services_chained": ["W-CLASSIFY-001", "W-VISION-001", "W-OBS-GATE"],
        "i9_gate": "ALWAYS_ACTIVE"
    }


@app.get("/intent-cmd/vocabulary")
async def get_vocabulary():
    """List all recognized intents."""
    return {
        "service": "W-INTENT-CMD",
        "intents": [
            {
                "id": intent.id,
                "triggers": intent.triggers,
                "description": intent.description,
                "services": intent.services,
                "scene": intent.scene,
                "requires_i9": intent.requires_i9
            }
            for intent in INTENT_VOCABULARY.values()
        ]
    }


@app.post("/intent-cmd/parse")
async def parse_intent_endpoint(request: IntentParseRequest):
    """
    Parse natural language into a recognized intent.

    Returns the matched intent and execution plan preview.
    """
    intent = parse_intent(request.text)

    if not intent:
        return {
            "matched": False,
            "input": request.text,
            "suggestion": "Tenta: 'pitch', 'forense', 'verify', 'broadcast', 'social', 'clean'"
        }

    return {
        "matched": True,
        "input": request.text,
        "intent": {
            "id": intent.id,
            "description": intent.description,
            "services": intent.services,
            "scene": intent.scene,
            "requires_i9": intent.requires_i9
        }
    }


@app.post("/intent-cmd/execute")
async def execute_intent_endpoint(request: IntentRequest):
    """
    Execute an intent on an asset.

    Chains the required services and returns results for I9 approval.

    I9 GATE: This endpoint does NOT auto-seal. It prepares everything
    and returns to the human for final approval.
    """
    # Resolve intent
    intent = None

    if request.intent:
        # Try as intent ID first
        intent = get_intent_by_id(request.intent)

        # If not found, try parsing as natural language
        if not intent:
            intent = parse_intent(request.intent)

    if not intent:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Intent not recognized",
                "input": request.intent,
                "available_intents": list(INTENT_VOCABULARY.keys())
            }
        )

    # Dry run - just return the plan
    if request.dry_run:
        return {
            "dry_run": True,
            "intent": {
                "id": intent.id,
                "description": intent.description,
                "services": intent.services,
                "scene": intent.scene
            },
            "asset_id": request.asset_id,
            "project_id": request.project_id,
            "steps_planned": [
                {"service": s, "status": "planned"}
                for s in intent.services
            ],
            "requires_i9": intent.requires_i9
        }

    # Execute the intent
    log.info(f"Executing intent '{intent.id}' for asset {request.asset_id}")

    results = await execute_intent(
        intent=intent,
        asset_id=request.asset_id,
        project_id=request.project_id,
        params=request.params
    )

    log.info(f"Intent '{intent.id}' completed with status: {results['status']}")

    return results


@app.post("/intent-cmd/cmd/{command}")
async def shorthand_command(
    command: str,
    asset_id: str,
    project_id: str
):
    """
    Shorthand command endpoint for quick execution.

    Usage: POST /intent-cmd/cmd/pitch?asset_id=X&project_id=Y
    """
    # Map shorthand to intent
    shorthand_map = {
        "pitch": "pitch_berlin",
        "forense": "forensic_seal",
        "forensic": "forensic_seal",
        "verify": "quick_verify",
        "tv": "broadcast_ready",
        "social": "social_share",
        "clean": "clean_seal"
    }

    intent_id = shorthand_map.get(command.lower())
    if not intent_id:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Unknown command: {command}",
                "available": list(shorthand_map.keys())
            }
        )

    intent = get_intent_by_id(intent_id)

    log.info(f"Shorthand command '{command}' -> intent '{intent_id}'")

    results = await execute_intent(
        intent=intent,
        asset_id=asset_id,
        project_id=project_id
    )

    return results


# ===== Main =====

if __name__ == "__main__":
    import uvicorn
    log.info(f"Starting W-INTENT-CMD on port {PORT}")
    log.info(f"Vocabulary: {len(INTENT_VOCABULARY)} intents")
    log.info("I9 Gate: ALWAYS ACTIVE")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
