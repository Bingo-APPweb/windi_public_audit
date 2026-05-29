#!/usr/bin/env python3
"""
W-GENERATOR-001 — Sovereign Content Generation Abstraction
===========================================================
Port: 8198
Version: 0.1.0
Sealed: 2026-05-29
Invariants: I9, I9-G, I11, I14

"A invocacao de geradores de conteudo e ferramenta tecnica.
 O selo do resultado e acto humano."

Architecture:
    USER REQUEST --> W-GENERATOR-001 --> ADAPTER (SORA/Runway/...) --> B4 GATE --> I9 GATE --> LEDGER

DOORs (Adapters):
    - DOOR_SORA: OpenAI SORA video generation
    - DOOR_RUNWAY: Runway Gen-3 video generation
    - DOOR_KLING: (future) Kling AI
    - DOOR_GROK: (future) GROK Images
    - DOOR_MIDJOURNEY: (future) Midjourney
    - DOOR_LOCAL: (future) Self-hosted Stable Diffusion
"""

import os
import sys
import json
import hashlib
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum

# ============================================================
# CONFIGURATION
# ============================================================

PORT = 8198
VERSION = "0.1.0"
SERVICE_NAME = "W-GENERATOR-001"

logging.basicConfig(
    level=logging.INFO,
    format=f'[{SERVICE_NAME}] %(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(SERVICE_NAME)

app = Flask(__name__)

# ============================================================
# ENUMS & TYPES
# ============================================================

class GeneratorType(Enum):
    SORA = "sora"
    RUNWAY = "runway"
    KLING = "kling"
    GROK = "grok"
    MIDJOURNEY = "midjourney"
    LOCAL = "local"
    AUTO = "auto"  # Routing decides

class ContentType(Enum):
    VIDEO = "video"
    IMAGE = "image"
    ANIMATION = "animation"

class GenerationStatus(Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    AWAITING_B4 = "awaiting_b4"
    AWAITING_I9 = "awaiting_i9"

# ============================================================
# ABSTRACT ADAPTER (DOOR Interface)
# ============================================================

class GeneratorAdapter(ABC):
    """
    Abstract DOOR interface for content generators.
    Each adapter implements this interface to integrate a new generator.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.name: str = "abstract"
        self.supports: List[ContentType] = []
        self.cost_per_second: float = 0.0
        self.quality_tier: int = 1  # 1-5, 5 being highest

    @abstractmethod
    def generate(self, prompt: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content from prompt. Returns generation job info."""
        pass

    @abstractmethod
    def check_status(self, job_id: str) -> Dict[str, Any]:
        """Check status of generation job."""
        pass

    @abstractmethod
    def download(self, job_id: str) -> bytes:
        """Download generated content."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if adapter is operational."""
        pass

    def get_info(self) -> Dict[str, Any]:
        """Return adapter metadata."""
        return {
            "name": self.name,
            "supports": [t.value for t in self.supports],
            "cost_per_second": self.cost_per_second,
            "quality_tier": self.quality_tier,
            "operational": self.health_check()
        }

# ============================================================
# DOOR: SORA ADAPTER
# ============================================================

class SoraAdapter(GeneratorAdapter):
    """
    DOOR_SORA: OpenAI SORA video generation
    Status: ACTIVE
    """

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "sora"
        self.supports = [ContentType.VIDEO]
        self.cost_per_second = 0.33  # ~$20/min
        self.quality_tier = 5
        self.base_url = "https://api.openai.com/v1"

    def generate(self, prompt: str, params: Dict[str, Any]) -> Dict[str, Any]:
        # Placeholder - actual implementation requires OpenAI SORA API
        logger.info(f"[DOOR_SORA] Generate request: {prompt[:50]}...")
        return {
            "job_id": f"sora_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "status": GenerationStatus.PENDING.value,
            "adapter": self.name,
            "message": "SORA generation queued"
        }

    def check_status(self, job_id: str) -> Dict[str, Any]:
        return {"job_id": job_id, "status": "pending", "adapter": self.name}

    def download(self, job_id: str) -> bytes:
        return b""

    def health_check(self) -> bool:
        return bool(self.api_key)

# ============================================================
# DOOR: RUNWAY ADAPTER
# ============================================================

class RunwayAdapter(GeneratorAdapter):
    """
    DOOR_RUNWAY: Runway Gen-3 video generation
    Status: ACTIVE (key: WINDIHIOS-001)
    """

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "runway"
        self.supports = [ContentType.VIDEO, ContentType.IMAGE]
        self.cost_per_second = 0.17  # ~$10/min
        self.quality_tier = 4
        self.base_url = "https://api.dev.runwayml.com/v1"

    def generate(self, prompt: str, params: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[DOOR_RUNWAY] Generate request: {prompt[:50]}...")
        return {
            "job_id": f"runway_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "status": GenerationStatus.PENDING.value,
            "adapter": self.name,
            "message": "Runway generation queued"
        }

    def check_status(self, job_id: str) -> Dict[str, Any]:
        return {"job_id": job_id, "status": "pending", "adapter": self.name}

    def download(self, job_id: str) -> bytes:
        return b""

    def health_check(self) -> bool:
        return bool(self.api_key)

# ============================================================
# DOOR: FUTURE ADAPTERS (Stubs)
# ============================================================

class KlingAdapter(GeneratorAdapter):
    """DOOR_KLING: Kling AI - FUTURE"""
    def __init__(self, api_key: str = ""):
        super().__init__(api_key)
        self.name = "kling"
        self.supports = [ContentType.VIDEO]
        self.cost_per_second = 0.08
        self.quality_tier = 4

    def generate(self, prompt: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"error": "DOOR_KLING not yet implemented", "status": "unavailable"}

    def check_status(self, job_id: str) -> Dict[str, Any]:
        return {"error": "DOOR_KLING not yet implemented"}

    def download(self, job_id: str) -> bytes:
        return b""

    def health_check(self) -> bool:
        return False

class GrokAdapter(GeneratorAdapter):
    """DOOR_GROK: GROK Images (xAI) - FUTURE"""
    def __init__(self, api_key: str = ""):
        super().__init__(api_key)
        self.name = "grok"
        self.supports = [ContentType.IMAGE]
        self.cost_per_second = 0.01
        self.quality_tier = 3

    def generate(self, prompt: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"error": "DOOR_GROK not yet implemented", "status": "unavailable"}

    def check_status(self, job_id: str) -> Dict[str, Any]:
        return {"error": "DOOR_GROK not yet implemented"}

    def download(self, job_id: str) -> bytes:
        return b""

    def health_check(self) -> bool:
        return False

class MidjourneyAdapter(GeneratorAdapter):
    """DOOR_MIDJOURNEY: Midjourney - FUTURE"""
    def __init__(self, api_key: str = ""):
        super().__init__(api_key)
        self.name = "midjourney"
        self.supports = [ContentType.IMAGE]
        self.cost_per_second = 0.05
        self.quality_tier = 5

    def generate(self, prompt: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"error": "DOOR_MIDJOURNEY not yet implemented", "status": "unavailable"}

    def check_status(self, job_id: str) -> Dict[str, Any]:
        return {"error": "DOOR_MIDJOURNEY not yet implemented"}

    def download(self, job_id: str) -> bytes:
        return b""

    def health_check(self) -> bool:
        return False

class LocalAdapter(GeneratorAdapter):
    """DOOR_LOCAL: Self-hosted Stable Diffusion - FUTURE (requires GPU)"""
    def __init__(self, api_key: str = ""):
        super().__init__(api_key)
        self.name = "local"
        self.supports = [ContentType.IMAGE]
        self.cost_per_second = 0.0  # Free after hardware
        self.quality_tier = 3

    def generate(self, prompt: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"error": "DOOR_LOCAL not yet implemented (requires GPU)", "status": "unavailable"}

    def check_status(self, job_id: str) -> Dict[str, Any]:
        return {"error": "DOOR_LOCAL not yet implemented"}

    def download(self, job_id: str) -> bytes:
        return b""

    def health_check(self) -> bool:
        return False

# ============================================================
# GENERATOR REGISTRY
# ============================================================

class GeneratorRegistry:
    """
    Central registry for all generator DOORs.
    Handles routing and adapter selection.
    """

    def __init__(self):
        self.adapters: Dict[str, GeneratorAdapter] = {}
        self._load_adapters()

    def _load_adapters(self):
        """Load all available adapters with their API keys."""

        # DOOR_SORA
        sora_key = os.getenv("OPENAI_API_KEY", "")
        if sora_key:
            self.adapters["sora"] = SoraAdapter(sora_key)
            logger.info("[REGISTRY] DOOR_SORA loaded")

        # DOOR_RUNWAY
        runway_key = os.getenv("RUNWAY_API_KEY", "")
        if runway_key:
            self.adapters["runway"] = RunwayAdapter(runway_key)
            logger.info("[REGISTRY] DOOR_RUNWAY loaded (WINDIHIOS-001)")

        # Future DOORs (stubs)
        self.adapters["kling"] = KlingAdapter()
        self.adapters["grok"] = GrokAdapter()
        self.adapters["midjourney"] = MidjourneyAdapter()
        self.adapters["local"] = LocalAdapter()

        logger.info(f"[REGISTRY] {len(self.adapters)} DOORs registered")

    def get_adapter(self, name: str) -> Optional[GeneratorAdapter]:
        """Get adapter by name."""
        return self.adapters.get(name)

    def get_active_adapters(self) -> List[str]:
        """List all operational adapters."""
        return [name for name, adapter in self.adapters.items() if adapter.health_check()]

    def get_all_info(self) -> Dict[str, Any]:
        """Get info on all adapters."""
        return {name: adapter.get_info() for name, adapter in self.adapters.items()}

    def auto_select(self, content_type: ContentType, quality_min: int = 3, cost_max: float = 1.0) -> Optional[str]:
        """
        Auto-select best adapter based on criteria.
        Future: intelligent routing based on cost/quality/availability.
        """
        candidates = []
        for name, adapter in self.adapters.items():
            if not adapter.health_check():
                continue
            if content_type not in adapter.supports:
                continue
            if adapter.quality_tier < quality_min:
                continue
            if adapter.cost_per_second > cost_max:
                continue
            candidates.append((name, adapter.quality_tier, adapter.cost_per_second))

        if not candidates:
            return None

        # Sort by quality (desc), then cost (asc)
        candidates.sort(key=lambda x: (-x[1], x[2]))
        return candidates[0][0]

# Global registry
registry = GeneratorRegistry()

# ============================================================
# API ENDPOINTS
# ============================================================

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "service": SERVICE_NAME,
        "version": VERSION,
        "status": "operational",
        "port": PORT,
        "timestamp": datetime.now().isoformat(),
        "active_doors": registry.get_active_adapters()
    })

@app.route("/doors", methods=["GET"])
def list_doors():
    """List all DOORs (adapters) and their status."""
    return jsonify({
        "service": SERVICE_NAME,
        "doors": registry.get_all_info(),
        "active": registry.get_active_adapters(),
        "total": len(registry.adapters)
    })

@app.route("/generate", methods=["POST"])
def generate():
    """
    Generate content through specified or auto-selected DOOR.

    Body:
    {
        "prompt": "A woman in a garden...",
        "door": "runway" | "sora" | "auto",
        "content_type": "video" | "image",
        "params": { ... },
        "workflow_id": "optional-tracking-id"
    }

    I9-G: CCode can invoke this endpoint within approved workflow.
          Result still requires human approval before seal.
    """
    data = request.get_json()

    if not data or "prompt" not in data:
        return jsonify({"error": "prompt required", "invariant": "I14"}), 400

    prompt = data["prompt"]
    door_name = data.get("door", "auto")
    content_type_str = data.get("content_type", "video")
    params = data.get("params", {})
    workflow_id = data.get("workflow_id", f"wf_{datetime.now().strftime('%Y%m%d%H%M%S')}")

    try:
        content_type = ContentType(content_type_str)
    except ValueError:
        return jsonify({"error": f"Invalid content_type: {content_type_str}"}), 400

    # Select adapter
    if door_name == "auto":
        door_name = registry.auto_select(content_type)
        if not door_name:
            return jsonify({
                "error": "No suitable DOOR available for this request",
                "content_type": content_type_str,
                "active_doors": registry.get_active_adapters()
            }), 503

    adapter = registry.get_adapter(door_name)
    if not adapter:
        return jsonify({"error": f"DOOR not found: {door_name}"}), 404

    if not adapter.health_check():
        return jsonify({"error": f"DOOR not operational: {door_name}"}), 503

    # Generate
    result = adapter.generate(prompt, params)
    result["workflow_id"] = workflow_id
    result["door_used"] = door_name
    result["i9_note"] = "Result awaits B4 validation and human approval before seal"

    logger.info(f"[GENERATE] {door_name} | {workflow_id} | {prompt[:30]}...")

    return jsonify(result)

@app.route("/status/<job_id>", methods=["GET"])
def check_status(job_id: str):
    """Check status of generation job."""
    # Extract adapter from job_id prefix
    parts = job_id.split("_")
    if len(parts) < 2:
        return jsonify({"error": "Invalid job_id format"}), 400

    door_name = parts[0]
    adapter = registry.get_adapter(door_name)
    if not adapter:
        return jsonify({"error": f"DOOR not found: {door_name}"}), 404

    return jsonify(adapter.check_status(job_id))

@app.route("/i9-g", methods=["GET"])
def i9g_doctrine():
    """Display I9-G doctrine for transparency."""
    return jsonify({
        "invariant": "I9-G",
        "name": "Generator Invocation Principle",
        "doctrine": "A invocacao de geradores de conteudo e ferramenta tecnica. O selo do resultado e acto humano.",
        "corollaries": {
            "C1": "CCode pode invocar qualquer gerador dentro de workflow aprovado",
            "C2": "A escolha de qual gerador usar e optimizacao tecnica, nao governanca",
            "C3": "O utilizador externo tem soberania sobre o resultado, nao sobre a infra",
            "C4": "B4 permanece gate obrigatorio entre geracao e proposta",
            "C5": "Selo final requer human_approved=true (I9 intacto)"
        },
        "sealed": "2026-05-29",
        "approved_by": "Human Dragon"
    })

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    # Load .env
    from dotenv import load_dotenv
    env_path = "/opt/windi/.env"
    if os.path.exists(env_path):
        load_dotenv(env_path)
        logger.info(f"[INIT] Loaded {env_path}")

    # Reload registry with env vars loaded
    registry = GeneratorRegistry()

    logger.info(f"[INIT] {SERVICE_NAME} v{VERSION} starting on port {PORT}")
    logger.info(f"[INIT] Active DOORs: {registry.get_active_adapters()}")

    app.run(host="127.0.0.1", port=PORT, debug=False)
