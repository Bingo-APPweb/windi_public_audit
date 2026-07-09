"""Provider adapters for W-HIOS motor jobs.

MULTI-PROVIDER ARCHITECTURE (2026-07-09)
========================================

Providers are external services that generate media. Each provider has:
- A unique name (ionos, runway, openart, local-gpu)
- A capability set (image, video, face-swap)
- An adapter class that implements the generate() method

The motor orchestrates; providers execute.

Provider Registry:
    PROVIDER_REGISTRY = {
        "ionos": IonosImageProvider,      # Text-to-image (FLUX)
        "runway": RunwayVideoProvider,    # Image-to-video (Gen-4)
        "openart": OpenArtProvider,       # Face swap
        "local-gpu": LocalGPUProvider,    # Future self-hosted
        "dry-run": DryRunProvider,        # Testing only
    }

Usage:
    provider = get_provider("ionos")
    output = provider.generate(job, workspace)
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import urllib.error
import urllib.request
from urllib.parse import urlparse
from pathlib import Path
from typing import Any, Protocol, Type

from .engine import rel, sha256_file


# =============================================================================
# PROVIDER PROTOCOL (Interface)
# =============================================================================

class ProviderProtocol(Protocol):
    """Protocol that all providers must implement."""

    name: str
    capabilities: list[str]

    def provenance(self) -> dict[str, Any]:
        """Return provenance metadata (no secrets)."""
        ...

    def generate(self, job: dict[str, Any], workspace: Path) -> dict[str, Any]:
        """Generate media and return output metadata."""
        ...


class ProviderError(RuntimeError):
    """Raised when an external provider cannot return a usable artifact."""


class ProviderNotConfigured(ProviderError):
    """Raised when a provider is missing required configuration."""


class ProviderNotImplemented(ProviderError):
    """Raised when a provider is not yet implemented."""


# =============================================================================
# BASE PROVIDER
# =============================================================================

class BaseProvider:
    """Base class with common provider utilities."""

    name: str = "base"
    capabilities: list[str] = []

    def _read_prompt(self, job: dict[str, Any], workspace: Path) -> str:
        """Extract prompt from brief file."""
        brief_path = workspace / job["brief"]["path"]
        text = brief_path.read_text(encoding="utf-8", errors="replace")
        marker = "## Prompt"
        if marker in text:
            return text.split(marker, 1)[1].strip()
        return text.strip()

    def _save_image_bytes(
        self,
        job: dict[str, Any],
        workspace: Path,
        image_bytes: bytes,
        mime_type: str,
        raw_path: Path,
    ) -> dict[str, Any]:
        """Save image bytes to disk and return output metadata."""
        suffix = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/webp": ".webp",
        }.get(mime_type.lower().split(";", 1)[0], ".bin")
        out_path = workspace / "outputs" / f"{job['job_id']}{suffix}"
        out_path.write_bytes(image_bytes)
        return {
            "path": rel(out_path, workspace),
            "sha256": sha256_file(out_path),
            "mime_type": mime_type,
            "kind": "image_file",
            "provider_raw_response": rel(raw_path, workspace),
            "provider_raw_response_sha256": sha256_file(raw_path),
        }

    def _save_video_bytes(
        self,
        job: dict[str, Any],
        workspace: Path,
        video_bytes: bytes,
        mime_type: str,
        raw_path: Path,
    ) -> dict[str, Any]:
        """Save video bytes to disk and return output metadata."""
        suffix = {
            "video/mp4": ".mp4",
            "video/webm": ".webm",
            "video/quicktime": ".mov",
        }.get(mime_type.lower().split(";", 1)[0], ".bin")
        out_path = workspace / "outputs" / f"{job['job_id']}{suffix}"
        out_path.write_bytes(video_bytes)
        return {
            "path": rel(out_path, workspace),
            "sha256": sha256_file(out_path),
            "mime_type": mime_type,
            "kind": "video_file",
            "provider_raw_response": rel(raw_path, workspace),
            "provider_raw_response_sha256": sha256_file(raw_path),
        }


# =============================================================================
# IONOS PROVIDER (Text-to-Image)
# =============================================================================

class IonosImageProvider(BaseProvider):
    """IONOS AI Model Hub image provider adapter.

    Capabilities:
        - Text-to-image generation (FLUX.1-schnell, FLUX.2-klein)
        - NO image-to-image
        - NO video generation
        - NO face consistency

    Use for:
        - Backgrounds, props, storyboards
        - New character conceptualization
        - Assets without face continuity

    Do NOT use for:
        - Character continuity (use runway/openart)
        - Video generation
        - Replicating existing anchors
    """

    name = "ionos-ai-model-hub"
    capabilities = ["text-to-image"]

    def __init__(self, endpoint: str | None = None, token: str | None = None, timeout: int = 300):
        self.endpoint = endpoint or os.environ.get("WHIOS_IONOS_IMAGE_ENDPOINT", "")
        self.token = (
            token
            or os.environ.get("WHIOS_IONOS_API_TOKEN", "")
            or os.environ.get("IONOS_API_TOKEN", "")
        )
        self.timeout = timeout
        if not self.endpoint:
            raise ProviderNotConfigured("Missing WHIOS_IONOS_IMAGE_ENDPOINT.")
        if not self.token:
            raise ProviderNotConfigured("Missing WHIOS_IONOS_API_TOKEN or IONOS_API_TOKEN.")

    def provenance(self) -> dict[str, Any]:
        parsed = urlparse(self.endpoint)
        endpoint_host = parsed.netloc or None
        endpoint_hash = hashlib.sha256(self.endpoint.encode("utf-8")).hexdigest()
        return {
            "provider": "ionos",
            "adapter": self.name,
            "endpoint_host": endpoint_host,
            "endpoint_sha256": endpoint_hash,
            "token_configured": bool(self.token),
            "secret_written_to_manifest": False,
            "capabilities": self.capabilities,
        }

    def generate(self, job: dict[str, Any], workspace: Path) -> dict[str, Any]:
        job["provider_provenance"] = self.provenance()
        payload = {
            "model": job["model"]["id"],
            "prompt": self._read_prompt(job, workspace),
            "size": job["settings"]["size"],
            "n": job["settings"].get("n", 1),
            "response_format": "b64_json",
        }
        if job["settings"].get("seed") is not None:
            payload["seed"] = job["settings"]["seed"]

        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/json,image/*",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
                content_type = response.headers.get("Content-Type", "application/octet-stream")
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise ProviderError(f"IONOS HTTP {exc.code}: {error_body[:1000]}") from exc
        except urllib.error.URLError as exc:
            raise ProviderError(f"IONOS request failed: {exc}") from exc

        raw_path = workspace / "outputs" / f"{job['job_id']}.ionos.response"
        if "json" in content_type:
            raw_path = raw_path.with_suffix(".json")
        raw_path.write_bytes(raw)

        if content_type.startswith("image/"):
            return self._save_image_bytes(job, workspace, raw, content_type, raw_path)

        try:
            response_json = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ProviderError(f"IONOS response was not JSON or image data. Raw: {raw_path}") from exc

        extracted = self._extract_image(response_json)
        if extracted["kind"] == "image_bytes":
            return self._save_image_bytes(
                job,
                workspace,
                extracted["data"],
                extracted["mime_type"],
                raw_path,
            )
        if extracted["kind"] == "remote_image_url":
            url_path = workspace / "outputs" / f"{job['job_id']}.url.txt"
            url_path.write_text(extracted["url"] + "\n", encoding="utf-8")
            return {
                "path": rel(url_path, workspace),
                "sha256": sha256_file(url_path),
                "mime_type": "text/uri-list",
                "kind": "remote_image_url",
                "provider_raw_response": rel(raw_path, workspace),
                "provider_raw_response_sha256": sha256_file(raw_path),
            }

        raise ProviderError(f"Could not extract image artifact from IONOS response. Raw: {raw_path}")

    def _extract_image(self, data: dict[str, Any]) -> dict[str, Any]:
        candidates: list[Any] = []
        if isinstance(data.get("data"), list):
            candidates.extend(data["data"])
        if isinstance(data.get("images"), list):
            candidates.extend(data["images"])
        candidates.extend([data.get("image"), data.get("b64_json"), data.get("url")])

        for item in candidates:
            if isinstance(item, dict):
                if item.get("b64_json"):
                    return {
                        "kind": "image_bytes",
                        "data": base64.b64decode(item["b64_json"]),
                        "mime_type": "image/png",
                    }
                if item.get("url"):
                    return {"kind": "remote_image_url", "url": item["url"]}
                if item.get("image"):
                    parsed = self._parse_image_string(item["image"])
                    if parsed:
                        return parsed
            elif isinstance(item, str):
                parsed = self._parse_image_string(item)
                if parsed:
                    return parsed
        return {"kind": "none"}

    def _parse_image_string(self, value: str) -> dict[str, Any] | None:
        if value.startswith("http://") or value.startswith("https://"):
            return {"kind": "remote_image_url", "url": value}
        if value.startswith("data:image/"):
            header, encoded = value.split(",", 1)
            mime_type = header.split(";", 1)[0].removeprefix("data:")
            return {
                "kind": "image_bytes",
                "data": base64.b64decode(encoded),
                "mime_type": mime_type,
            }
        try:
            decoded = base64.b64decode(value, validate=True)
        except Exception:
            return None
        return {
            "kind": "image_bytes",
            "data": decoded,
            "mime_type": "image/png",
        }


# =============================================================================
# RUNWAY PROVIDER (Image-to-Video) — STUB
# =============================================================================

class RunwayVideoProvider(BaseProvider):
    """Runway Gen-4 video provider adapter.

    Capabilities:
        - Image-to-video generation
        - Maintains visual consistency from reference image
        - Motion with identity preservation

    Use for:
        - Video from anchor images
        - Character animation with face continuity
        - Scene movement

    Status: STUB — Requires API key configuration

    Future env vars:
        WHIOS_RUNWAY_API_KEY
        WHIOS_RUNWAY_API_ENDPOINT (default: https://api.runwayml.com/v1)
    """

    name = "runway-gen4"
    capabilities = ["image-to-video", "face-consistency"]

    def __init__(self, api_key: str | None = None, timeout: int = 600):
        self.api_key = api_key or os.environ.get("WHIOS_RUNWAY_API_KEY", "")
        self.endpoint = os.environ.get(
            "WHIOS_RUNWAY_API_ENDPOINT",
            "https://api.runwayml.com/v1"
        )
        self.timeout = timeout

    def provenance(self) -> dict[str, Any]:
        return {
            "provider": "runway",
            "adapter": self.name,
            "endpoint_host": "api.runwayml.com",
            "endpoint_sha256": hashlib.sha256(self.endpoint.encode()).hexdigest(),
            "token_configured": bool(self.api_key),
            "secret_written_to_manifest": False,
            "capabilities": self.capabilities,
        }

    def generate(self, job: dict[str, Any], workspace: Path) -> dict[str, Any]:
        if not self.api_key:
            raise ProviderNotConfigured(
                "Runway provider requires WHIOS_RUNWAY_API_KEY. "
                "Get your key at https://runwayml.com/api"
            )

        # TODO: Implement Runway Gen-4 API integration
        # 1. Read anchor image from job["input_assets"]
        # 2. POST to /generations/image-to-video
        # 3. Poll for completion
        # 4. Download and save video

        raise ProviderNotImplemented(
            "Runway provider is not yet implemented. "
            "Use 'ionos' for images or generate manually via runwayml.com"
        )


# =============================================================================
# OPENART PROVIDER (Face Swap) — STUB
# =============================================================================

class OpenArtProvider(BaseProvider):
    """OpenArt face swap provider adapter.

    Capabilities:
        - Face swap in existing images/videos
        - Maintains anchor identity across media

    Use for:
        - Applying character anchor to generated content
        - Post-processing IONOS outputs with correct face
        - Video face replacement

    Status: STUB — Requires API key configuration

    Future env vars:
        WHIOS_OPENART_API_KEY
    """

    name = "openart-faceswap"
    capabilities = ["face-swap", "face-consistency"]

    def __init__(self, api_key: str | None = None, timeout: int = 300):
        self.api_key = api_key or os.environ.get("WHIOS_OPENART_API_KEY", "")
        self.endpoint = "https://openart.ai/api/v1"
        self.timeout = timeout

    def provenance(self) -> dict[str, Any]:
        return {
            "provider": "openart",
            "adapter": self.name,
            "endpoint_host": "openart.ai",
            "endpoint_sha256": hashlib.sha256(self.endpoint.encode()).hexdigest(),
            "token_configured": bool(self.api_key),
            "secret_written_to_manifest": False,
            "capabilities": self.capabilities,
        }

    def generate(self, job: dict[str, Any], workspace: Path) -> dict[str, Any]:
        if not self.api_key:
            raise ProviderNotConfigured(
                "OpenArt provider requires WHIOS_OPENART_API_KEY. "
                "Get your key at https://openart.ai/api"
            )

        # TODO: Implement OpenArt face swap API integration
        # 1. Read source image and anchor face from job["input_assets"]
        # 2. POST to face swap endpoint
        # 3. Download and save result

        raise ProviderNotImplemented(
            "OpenArt provider is not yet implemented. "
            "Use manually via openart.ai"
        )


# =============================================================================
# LOCAL GPU PROVIDER — STUB
# =============================================================================

class LocalGPUProvider(BaseProvider):
    """Local GPU provider for self-hosted models.

    Capabilities:
        - Text-to-image (FLUX, Stable Diffusion)
        - Full control over generation
        - No external API calls

    Requirements:
        - NVIDIA GPU with 12GB+ VRAM
        - CUDA drivers installed
        - PyTorch with CUDA support
        - diffusers library

    Status: STUB — Requires GPU hardware

    Future env vars:
        WHIOS_LOCAL_GPU_MODEL (default: stabilityai/stable-diffusion-xl-base-1.0)
        WHIOS_LOCAL_GPU_DEVICE (default: cuda:0)
    """

    name = "local-gpu"
    capabilities = ["text-to-image", "local"]

    def __init__(self):
        self.model_id = os.environ.get(
            "WHIOS_LOCAL_GPU_MODEL",
            "stabilityai/stable-diffusion-xl-base-1.0"
        )
        self.device = os.environ.get("WHIOS_LOCAL_GPU_DEVICE", "cuda:0")

    def provenance(self) -> dict[str, Any]:
        return {
            "provider": "local-gpu",
            "adapter": self.name,
            "endpoint_host": "localhost",
            "endpoint_sha256": None,
            "token_configured": False,
            "secret_written_to_manifest": False,
            "capabilities": self.capabilities,
            "model_id": self.model_id,
            "device": self.device,
        }

    def generate(self, job: dict[str, Any], workspace: Path) -> dict[str, Any]:
        # Check for GPU
        try:
            import torch
            if not torch.cuda.is_available():
                raise ProviderNotConfigured(
                    "Local GPU provider requires NVIDIA GPU with CUDA. "
                    "This server has no GPU available."
                )
        except ImportError:
            raise ProviderNotConfigured(
                "Local GPU provider requires PyTorch with CUDA support. "
                "Install with: pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118"
            )

        # TODO: Implement local generation
        # 1. Load model with diffusers
        # 2. Generate image
        # 3. Save to workspace

        raise ProviderNotImplemented(
            "Local GPU provider is not yet implemented. "
            "Use 'ionos' for cloud generation."
        )


# =============================================================================
# DRY-RUN PROVIDER
# =============================================================================

class DryRunProvider(BaseProvider):
    """Dry-run provider for testing without actual generation."""

    name = "dry-run"
    capabilities = ["testing"]

    def provenance(self) -> dict[str, Any]:
        return {
            "provider": "dry-run",
            "adapter": self.name,
            "endpoint_host": None,
            "endpoint_sha256": None,
            "token_configured": False,
            "secret_written_to_manifest": False,
            "capabilities": self.capabilities,
            "note": "No provider call was made.",
        }

    def generate(self, job: dict[str, Any], workspace: Path) -> dict[str, Any]:
        payload = {
            "dry_run": True,
            "job_id": job["job_id"],
            "provider": job["provider"],
            "model": job["model"]["id"],
            "size": job["settings"]["size"],
            "brief_sha256": job["brief"]["sha256"],
            "boundary": "plumbing proof only; no media generated",
        }
        data = json.dumps(payload, indent=2, ensure_ascii=True).encode("utf-8")
        out_path = workspace / "outputs" / f"{job['job_id']}.dry-run.json"
        out_path.write_bytes(data)
        return {
            "path": rel(out_path, workspace),
            "sha256": sha256_file(out_path),
            "mime_type": "application/json",
            "kind": "dry_run_manifest",
        }


# =============================================================================
# PROVIDER REGISTRY
# =============================================================================

PROVIDER_REGISTRY: dict[str, Type[BaseProvider]] = {
    "ionos": IonosImageProvider,
    "runway": RunwayVideoProvider,
    "openart": OpenArtProvider,
    "local-gpu": LocalGPUProvider,
    "dry-run": DryRunProvider,
}


def get_provider(name: str) -> BaseProvider:
    """Get a provider instance by name.

    Args:
        name: Provider name (ionos, runway, openart, local-gpu, dry-run)

    Returns:
        Provider instance

    Raises:
        ProviderError: If provider is unknown
    """
    if name not in PROVIDER_REGISTRY:
        available = ", ".join(sorted(PROVIDER_REGISTRY.keys()))
        raise ProviderError(f"Unknown provider '{name}'. Available: {available}")

    return PROVIDER_REGISTRY[name]()


def list_providers() -> dict[str, dict[str, Any]]:
    """List all available providers and their capabilities."""
    result = {}
    for name, cls in PROVIDER_REGISTRY.items():
        result[name] = {
            "name": cls.name,
            "capabilities": cls.capabilities,
            "class": cls.__name__,
        }
    return result
