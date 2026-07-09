#!/usr/bin/env python3
"""
W-GENERATOR-001 — Sovereign Content Generation Abstraction
===========================================================
Port: 8198
Version: 0.2.0
Updated: 2026-06-28
Invariants: I9, I9-G, I11, I14

"A invocacao de geradores de conteudo e ferramenta tecnica.
 O selo do resultado e acto humano."

Architecture:
    USER REQUEST --> W-GENERATOR-001 --> ADAPTER (SORA/Runway/...) --> B4 GATE --> I9 GATE --> LEDGER

DOORs (Adapters):
    - DOOR_RUNWAY: Runway Gen-4 Turbo (LIVE - Real API)
    - DOOR_SORA: OpenAI SORA video generation (stub)
    - DOOR_KLING: (future) Kling AI
    - DOOR_GROK: (future) GROK Images
    - DOOR_MIDJOURNEY: (future) Midjourney
    - DOOR_LOCAL: (future) Self-hosted Stable Diffusion

Endpoints:
    POST /generate        - Start generation job (async)
    POST /generate-sync   - Start and wait for completion (blocking)
    GET  /status/{job_id} - Check job status
    GET  /wait/{job_id}   - Wait for completion (blocking)
    GET  /download/{job_id} - Download output file
    GET  /doors           - List all adapters
    GET  /health          - Health check
"""

import os
import sys
import json
import hashlib
import logging
import time
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum

# ============================================================
# CONFIGURATION
# ============================================================

PORT = 8198
VERSION = "0.2.0"  # Real Runway API integration
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
# DOOR: RUNWAY ADAPTER — REAL API IMPLEMENTATION
# ============================================================

# Job storage for tracking Runway tasks
_runway_jobs: Dict[str, Dict[str, Any]] = {}

class RunwayAdapter(GeneratorAdapter):
    """
    DOOR_RUNWAY: Runway Gen-4 Turbo video generation
    Status: ACTIVE (key: WINDIHIOS-001)
    API: https://api.dev.runwayml.com/v1
    Docs: https://docs.dev.runwayml.com/

    Supports:
    - Image-to-Video: Animate a source image with motion
    - Text-to-Video: Generate video from text prompt (no source image)
    """

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "runway"
        self.supports = [ContentType.VIDEO, ContentType.IMAGE]
        self.cost_per_second = 0.17  # ~$10/min (5 credits/sec for Turbo)
        self.quality_tier = 4
        self.base_url = "https://api.dev.runwayml.com/v1"
        self.api_version = "2024-11-06"
        self.default_model = "gen4.5"  # gen4.5 (as of Jun 2026)
        self.default_duration = 5  # seconds
        self.default_ratio = "1280:720"  # 16:9 landscape

    def _get_headers(self) -> Dict[str, str]:
        """Build request headers with authentication."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-Runway-Version": self.api_version
        }

    def generate(self, prompt: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate video from image+prompt or text-only.

        params:
            - source_image_url: Public URL to source image (required for image-to-video)
            - duration: Video length in seconds (5 or 10)
            - ratio: Video dimensions ("1280:720", "720:1280", "1024:1024")
            - model: "gen4_turbo" or "gen4"
            - motion: Camera motion hint (informational, encoded in prompt)
        """
        logger.info(f"[DOOR_RUNWAY] Generate request: {prompt[:50]}...")

        source_image_url = params.get("source_image_url")
        duration = params.get("duration", self.default_duration)
        ratio = params.get("ratio", self.default_ratio)
        model = params.get("model", self.default_model)

        # Build request body
        body = {
            "promptText": prompt,
            "model": model,
            "duration": duration,
            "ratio": ratio
        }

        # Image-to-Video requires promptImage
        if source_image_url:
            body["promptImage"] = source_image_url
            endpoint = f"{self.base_url}/image_to_video"
            logger.info(f"[DOOR_RUNWAY] Image-to-Video: {source_image_url}")
        else:
            endpoint = f"{self.base_url}/text_to_video"
            logger.info(f"[DOOR_RUNWAY] Text-to-Video (no source image)")

        try:
            response = requests.post(
                endpoint,
                headers=self._get_headers(),
                json=body,
                timeout=30
            )

            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                task_id = data.get("id")

                # Store job for tracking
                job_id = f"runway_{task_id}"
                _runway_jobs[job_id] = {
                    "task_id": task_id,
                    "status": "PENDING",
                    "created_at": datetime.now().isoformat(),
                    "prompt": prompt[:100],
                    "source_image": source_image_url,
                    "output_url": None,
                    "error": None
                }

                logger.info(f"[DOOR_RUNWAY] Job created: {job_id}")

                return {
                    "job_id": job_id,
                    "task_id": task_id,
                    "status": GenerationStatus.PENDING.value,
                    "adapter": self.name,
                    "message": "Runway generation started",
                    "model": model,
                    "duration": duration,
                    "estimated_cost": f"${duration * self.cost_per_second:.2f}"
                }
            else:
                error_msg = response.text
                logger.error(f"[DOOR_RUNWAY] API error: {response.status_code} - {error_msg}")
                return {
                    "job_id": None,
                    "status": GenerationStatus.FAILED.value,
                    "adapter": self.name,
                    "error": f"API error {response.status_code}: {error_msg}"
                }

        except requests.exceptions.Timeout:
            logger.error("[DOOR_RUNWAY] Request timeout")
            return {
                "job_id": None,
                "status": GenerationStatus.FAILED.value,
                "adapter": self.name,
                "error": "Request timeout"
            }
        except Exception as e:
            logger.error(f"[DOOR_RUNWAY] Exception: {str(e)}")
            return {
                "job_id": None,
                "status": GenerationStatus.FAILED.value,
                "adapter": self.name,
                "error": str(e)
            }

    def check_status(self, job_id: str) -> Dict[str, Any]:
        """Poll Runway API for task status."""

        # Get stored job info
        job = _runway_jobs.get(job_id)
        if not job:
            return {"job_id": job_id, "status": "unknown", "error": "Job not found in local registry"}

        task_id = job.get("task_id")
        if not task_id:
            return {"job_id": job_id, "status": "error", "error": "No task_id stored"}

        try:
            response = requests.get(
                f"{self.base_url}/tasks/{task_id}",
                headers=self._get_headers(),
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "UNKNOWN")

                # Update stored job
                job["status"] = status

                result = {
                    "job_id": job_id,
                    "task_id": task_id,
                    "status": status.lower(),
                    "adapter": self.name,
                    "progress": data.get("progress", 0),
                    "created_at": job.get("created_at")
                }

                # If completed, extract output URL
                if status == "SUCCEEDED":
                    output = data.get("output", [])
                    if output and len(output) > 0:
                        output_url = output[0] if isinstance(output[0], str) else output[0].get("url")
                        job["output_url"] = output_url
                        result["output_url"] = output_url
                        result["status"] = "completed"
                        logger.info(f"[DOOR_RUNWAY] Job completed: {job_id} -> {output_url}")

                elif status == "FAILED":
                    error = data.get("failure", data.get("error", "Unknown error"))
                    job["error"] = error
                    result["error"] = error
                    result["status"] = "failed"
                    logger.error(f"[DOOR_RUNWAY] Job failed: {job_id} - {error}")

                elif status == "RUNNING":
                    result["status"] = "generating"

                return result
            else:
                return {
                    "job_id": job_id,
                    "status": "error",
                    "error": f"API returned {response.status_code}"
                }

        except Exception as e:
            logger.error(f"[DOOR_RUNWAY] Status check error: {str(e)}")
            return {
                "job_id": job_id,
                "status": "error",
                "error": str(e)
            }

    def download(self, job_id: str) -> bytes:
        """Download generated video content."""
        job = _runway_jobs.get(job_id)
        if not job:
            logger.error(f"[DOOR_RUNWAY] Download failed: job not found {job_id}")
            return b""

        output_url = job.get("output_url")
        if not output_url:
            # Try to refresh status first
            status = self.check_status(job_id)
            output_url = status.get("output_url")

        if not output_url:
            logger.error(f"[DOOR_RUNWAY] Download failed: no output URL for {job_id}")
            return b""

        try:
            response = requests.get(output_url, timeout=120)
            if response.status_code == 200:
                logger.info(f"[DOOR_RUNWAY] Downloaded {len(response.content)} bytes for {job_id}")
                return response.content
            else:
                logger.error(f"[DOOR_RUNWAY] Download failed: {response.status_code}")
                return b""
        except Exception as e:
            logger.error(f"[DOOR_RUNWAY] Download exception: {str(e)}")
            return b""

    def wait_for_completion(self, job_id: str, timeout: int = 300, poll_interval: int = 5) -> Dict[str, Any]:
        """
        Poll until job completes or times out.
        Returns final status with output_url if successful.
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self.check_status(job_id)
            current_status = status.get("status", "unknown")

            if current_status in ["completed", "failed", "error"]:
                return status

            logger.info(f"[DOOR_RUNWAY] Waiting... {job_id} is {current_status}")
            time.sleep(poll_interval)

        return {
            "job_id": job_id,
            "status": "timeout",
            "error": f"Job did not complete within {timeout} seconds"
        }

    def health_check(self) -> bool:
        """Verify API key is configured."""
        return bool(self.api_key) and len(self.api_key) > 10

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


@app.route("/wait/<job_id>", methods=["GET"])
def wait_for_job(job_id: str):
    """
    Wait for job completion (blocking).
    Query params:
        - timeout: Max wait time in seconds (default 300)
        - poll: Poll interval in seconds (default 5)
    """
    parts = job_id.split("_")
    if len(parts) < 2:
        return jsonify({"error": "Invalid job_id format"}), 400

    door_name = parts[0]
    adapter = registry.get_adapter(door_name)
    if not adapter:
        return jsonify({"error": f"DOOR not found: {door_name}"}), 404

    timeout = request.args.get("timeout", 300, type=int)
    poll_interval = request.args.get("poll", 5, type=int)

    # Only RunwayAdapter has wait_for_completion
    if hasattr(adapter, "wait_for_completion"):
        result = adapter.wait_for_completion(job_id, timeout, poll_interval)
        return jsonify(result)
    else:
        return jsonify(adapter.check_status(job_id))


@app.route("/download/<job_id>", methods=["GET"])
def download_job(job_id: str):
    """
    Download generated content.
    Returns the video/image bytes with appropriate content type.
    """
    from flask import Response

    parts = job_id.split("_")
    if len(parts) < 2:
        return jsonify({"error": "Invalid job_id format"}), 400

    door_name = parts[0]
    adapter = registry.get_adapter(door_name)
    if not adapter:
        return jsonify({"error": f"DOOR not found: {door_name}"}), 404

    content = adapter.download(job_id)
    if not content:
        return jsonify({"error": "Download failed or content not ready"}), 404

    # Determine content type (video for runway)
    content_type = "video/mp4"
    filename = f"{job_id}.mp4"

    return Response(
        content,
        mimetype=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.route("/generate-sync", methods=["POST"])
def generate_sync():
    """
    Generate and wait for completion (synchronous).
    Useful for single-call workflows.

    Body: Same as /generate plus:
        - timeout: Max wait time in seconds (default 300)
        - save_to: Optional local path to save output

    WARNING: This endpoint blocks until completion or timeout.
    For long videos, prefer /generate + polling /status.
    """
    data = request.get_json()

    if not data or "prompt" not in data:
        return jsonify({"error": "prompt required", "invariant": "I14"}), 400

    prompt = data["prompt"]
    door_name = data.get("door", "auto")
    content_type_str = data.get("content_type", "video")
    params = data.get("params", {})
    workflow_id = data.get("workflow_id", f"wf_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    timeout = data.get("timeout", 300)
    save_to = data.get("save_to")

    try:
        content_type = ContentType(content_type_str)
    except ValueError:
        return jsonify({"error": f"Invalid content_type: {content_type_str}"}), 400

    # Select adapter
    if door_name == "auto":
        door_name = registry.auto_select(content_type)
        if not door_name:
            return jsonify({
                "error": "No suitable DOOR available",
                "active_doors": registry.get_active_adapters()
            }), 503

    adapter = registry.get_adapter(door_name)
    if not adapter or not adapter.health_check():
        return jsonify({"error": f"DOOR not available: {door_name}"}), 503

    # Step 1: Generate
    gen_result = adapter.generate(prompt, params)
    if gen_result.get("status") == "failed":
        return jsonify(gen_result), 500

    job_id = gen_result.get("job_id")
    if not job_id:
        return jsonify({"error": "No job_id returned", "result": gen_result}), 500

    logger.info(f"[GENERATE-SYNC] Started {job_id}, waiting up to {timeout}s...")

    # Step 2: Wait for completion
    if hasattr(adapter, "wait_for_completion"):
        final_status = adapter.wait_for_completion(job_id, timeout=timeout)
    else:
        final_status = adapter.check_status(job_id)

    final_status["workflow_id"] = workflow_id
    final_status["door_used"] = door_name

    # Step 3: Optionally save to local file
    if save_to and final_status.get("status") == "completed":
        try:
            content = adapter.download(job_id)
            if content:
                # Ensure directory exists
                os.makedirs(os.path.dirname(save_to), exist_ok=True)
                with open(save_to, "wb") as f:
                    f.write(content)
                final_status["saved_to"] = save_to
                final_status["file_size"] = len(content)
                logger.info(f"[GENERATE-SYNC] Saved to {save_to}")
        except Exception as e:
            final_status["save_error"] = str(e)
            logger.error(f"[GENERATE-SYNC] Save failed: {e}")

    final_status["i9_note"] = "Result awaits human approval before Ledger seal"

    return jsonify(final_status)

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
