"""File-based WINDI-HIOS generation motor.

The first motor is intentionally plain: jobs, briefs, outputs and manifests on
disk. Providers generate media; WINDI-HIOS owns provenance and gates.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_WORKSPACE = Path("w_hios_motor_workspace")
DEFAULT_IMAGE_MODEL = "black-forest-labs/FLUX.1-schnell"
PROFILE_VALUES = {"preview", "standard", "identity_i2v", "high_fidelity"}
JOB_STATES = ("pending", "running", "done", "failed")
FAILURE_CLASSES = {
    "V2_TRACEABILITY_FAIL": "Output, manifest, hash or provider response could not be traced.",
    "V3_SCOPE_VIOLATION": "Output violates the requested world, scope or forbidden elements.",
    "V4_MECHANICAL_RULE": "Worker, provider, configuration, network or runtime failure.",
    "V5A_BRIEF_AMBIGUITY": "Brief is underspecified or internally ambiguous.",
    "V5B_MOTOR_LIMITATION": "Motor repeatedly cannot satisfy a valid brief.",
    "V8_CERTIFICATE_FAIL": "Downstream verification or certificate gate failed.",
}


class MotorError(RuntimeError):
    """Raised when the motor cannot complete a job."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def json_dump(data: dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def json_load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def init_workspace(workspace: Path | str = DEFAULT_WORKSPACE) -> Path:
    root = Path(workspace)
    for rel in (
        "briefs",
        "jobs/pending",
        "jobs/running",
        "jobs/done",
        "jobs/failed",
        "manifests",
        "outputs",
        "logs",
    ):
        (root / rel).mkdir(parents=True, exist_ok=True)
    return root


def new_job_id(prefix: str = "W-MOTOR-JOB") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{prefix}-{stamp}-{secrets.token_hex(2).upper()}"


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _initial_provider_provenance(provider: str) -> dict[str, Any]:
    return {
        "provider": provider,
        "adapter": None,
        "endpoint_host": None,
        "endpoint_sha256": None,
        "token_configured": False,
        "secret_written_to_manifest": False,
    }


def _dry_run_provider_provenance(provider: str) -> dict[str, Any]:
    return {
        "provider": provider,
        "adapter": "dry-run",
        "endpoint_host": None,
        "endpoint_sha256": None,
        "token_configured": False,
        "secret_written_to_manifest": False,
        "note": "No provider call was made.",
    }


def classify_failure(exc: Exception) -> dict[str, Any]:
    message = str(exc)
    exc_type = exc.__class__.__name__

    if "Prompt cannot be empty" in message or "Invalid profile" in message:
        code = "V5A_BRIEF_AMBIGUITY"
        stage = "brief_validation"
        retryable = False
    elif "Could not extract image artifact" in message or "not JSON or image data" in message:
        code = "V2_TRACEABILITY_FAIL"
        stage = "provider_response_ingest"
        retryable = True
    elif "certificate" in message.lower() or "gate" in message.lower():
        code = "V8_CERTIFICATE_FAIL"
        stage = "verification"
        retryable = False
    elif "Provider" in exc_type or "HTTP" in message or "request failed" in message or "Missing WHIOS" in message:
        code = "V4_MECHANICAL_RULE"
        stage = "provider_runtime"
        retryable = "Missing WHIOS" not in message
    elif "not implemented" in message:
        code = "V4_MECHANICAL_RULE"
        stage = "worker_selection"
        retryable = False
    else:
        code = "V5B_MOTOR_LIMITATION"
        stage = "unknown"
        retryable = True

    return {
        "code": code,
        "label": FAILURE_CLASSES[code],
        "stage": stage,
        "retryable": retryable,
        "source_error_type": exc_type,
    }


def create_image_job(
    *,
    prompt: str,
    workspace: Path | str = DEFAULT_WORKSPACE,
    project: str = "w-hios",
    scene: str = "playground",
    shot: str = "",
    profile: str = "preview",
    provider: str = "ionos",
    model: str = DEFAULT_IMAGE_MODEL,
    size: str = "1024x1024",
    seed: int | None = None,
) -> tuple[dict[str, Any], Path]:
    if profile not in PROFILE_VALUES:
        raise MotorError(f"Invalid profile '{profile}'. Use one of: {', '.join(sorted(PROFILE_VALUES))}")
    if not prompt.strip():
        raise MotorError("Prompt cannot be empty.")

    root = init_workspace(workspace)
    job_id = new_job_id()
    created_at = utc_now()

    brief_text = "\n".join(
        [
            f"# W-HIOS Motor Brief {job_id}",
            "",
            "```yaml",
            f"job_id: {job_id}",
            "doc_type: motor_brief",
            "status: CANDIDATE",
            f"created_at: {created_at}",
            f"project: {project}",
            f"scene: {scene}",
            f"profile: {profile}",
            "boundary: no receipt, no seal, no identity verdict",
            "```",
            "",
            "## Prompt",
            "",
            prompt.strip(),
            "",
        ]
    )
    brief_path = root / "briefs" / f"{job_id}.md"
    brief_path.write_text(brief_text, encoding="utf-8")

    job = {
        "schema_version": "w-hios.motor.job.v1",
        "job_id": job_id,
        "created_at": created_at,
        "updated_at": created_at,
        "status": "PENDING",
        "kind": "image_generation",
        "project": project,
        "scene": scene,
        "shot": shot,
        "profile": profile,
        "provider": provider,
        "brief": {
            "path": rel(brief_path, root),
            "sha256": sha256_file(brief_path),
            "prompt_sha256": sha256_bytes(prompt.strip().encode("utf-8")),
        },
        "input_assets": [],
        "model": {
            "id": model,
            "engine": "text-to-image",
            "provider": provider,
        },
        "settings": {
            "size": size,
            "seed": seed,
            "n": 1,
        },
        "worker": {
            "worker_id": "UNCLAIMED",
            "location": "UNCLAIMED",
        },
        "provider_provenance": _initial_provider_provenance(provider),
        "output": {
            "path": None,
            "sha256": None,
            "mime_type": None,
            "kind": None,
        },
        "gates": {
            "ingest": "PENDING",
            "G1": "PENDING",
            "G2": "PENDING",
            "G3": "PENDING",
            "verdict": "PENDING",
        },
        "boundary": {
            "receipt": "none",
            "seal": "none",
            "identity_verdict": "none",
        },
        "ledger_anchor": {
            "status": "NOT_ANCHORED",
            "target": "forensic-ledger",
            "reason": "Local motor birth; Ledger anchoring is a later explicit step.",
        },
        "failure": None,
    }
    job_path = root / "jobs" / "pending" / f"{job_id}.json"
    json_dump(job, job_path)
    return job, job_path


def list_jobs(workspace: Path | str = DEFAULT_WORKSPACE) -> list[dict[str, Any]]:
    root = init_workspace(workspace)
    items: list[dict[str, Any]] = []
    for state in JOB_STATES:
        for path in sorted((root / "jobs" / state).glob("*.json")):
            job = json_load(path)
            job["_state"] = state
            job["_path"] = rel(path, root)
            items.append(job)
    return items


def _next_pending_path(root: Path) -> Path | None:
    pending = sorted((root / "jobs" / "pending").glob("*.json"))
    return pending[0] if pending else None


def _claim_job(root: Path, pending_path: Path) -> tuple[dict[str, Any], Path]:
    job = json_load(pending_path)
    running_path = root / "jobs" / "running" / pending_path.name
    pending_path.replace(running_path)
    job["status"] = "RUNNING"
    job["updated_at"] = utc_now()
    job["worker"] = {
        "worker_id": "local-file-worker",
        "location": "local",
    }
    json_dump(job, running_path)
    return job, running_path


def _write_manifest(root: Path, job: dict[str, Any], status: str, extra: dict[str, Any]) -> Path:
    manifest = {
        "schema_version": "w-hios.motor.manifest.v1",
        "job_id": job["job_id"],
        "generated_at": utc_now(),
        "status": status,
        "project": job["project"],
        "scene": job["scene"],
        "profile": job["profile"],
        "provider": job["provider"],
        "model": job["model"],
        "settings": job["settings"],
        "provider_provenance": job.get("provider_provenance", _initial_provider_provenance(job["provider"])),
        "brief": job["brief"],
        "input_assets": job["input_assets"],
        "output": job["output"],
        "gates": job["gates"],
        "boundary": job["boundary"],
        "ledger_anchor": job.get("ledger_anchor"),
        "failure": job.get("failure"),
        **extra,
    }
    path = root / "manifests" / f"{job['job_id']}.manifest.json"
    json_dump(manifest, path)
    return path


def _finish_job(root: Path, running_path: Path, job: dict[str, Any], state: str) -> Path:
    job["updated_at"] = utc_now()
    job["status"] = state.upper()
    done_path = root / "jobs" / state / running_path.name
    json_dump(job, running_path)
    running_path.replace(done_path)
    return done_path


def _dry_run_output(root: Path, job: dict[str, Any]) -> dict[str, Any]:
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
    out_path = root / "outputs" / f"{job['job_id']}.dry-run.json"
    out_path.write_bytes(data)
    return {
        "path": rel(out_path, root),
        "sha256": sha256_file(out_path),
        "mime_type": "application/json",
        "kind": "dry_run_manifest",
    }


def run_next_job(
    *,
    workspace: Path | str = DEFAULT_WORKSPACE,
    provider: str = "ionos",
    dry_run: bool = False,
) -> tuple[dict[str, Any], Path]:
    """Run the next pending job with the specified provider.

    MULTI-PROVIDER SUPPORT (2026-07-09):
        - ionos:     Text-to-image (FLUX) — backgrounds, props, new characters
        - runway:    Image-to-video (Gen-4) — STUB, requires API key
        - openart:   Face swap — STUB, requires API key
        - local-gpu: Self-hosted — STUB, requires GPU hardware
        - dry-run:   Testing only, no actual generation

    Args:
        workspace: Path to motor workspace
        provider: Provider name (ionos, runway, openart, local-gpu, dry-run)
        dry_run: If True, use dry-run provider regardless of provider arg

    Returns:
        Tuple of (job dict, manifest path)

    Raises:
        MotorError: If no pending jobs or provider fails
    """
    from .providers import get_provider, ProviderError, ProviderNotConfigured, ProviderNotImplemented

    root = init_workspace(workspace)
    pending_path = _next_pending_path(root)
    if pending_path is None:
        raise MotorError("No pending jobs found.")

    job, running_path = _claim_job(root, pending_path)
    job["provider"] = provider
    job["model"]["provider"] = provider
    job["provider_provenance"] = _initial_provider_provenance(provider)

    try:
        # Select provider
        if dry_run:
            adapter = get_provider("dry-run")
        else:
            adapter = get_provider(provider)

        # Generate
        job["provider_provenance"] = adapter.provenance()
        output = adapter.generate(job, root)
        extra = {"dry_run": dry_run, "provider_used": adapter.name}

        job["output"] = output
        job["gates"]["ingest"] = "PASS"
        manifest_path = _write_manifest(root, job, "DONE", extra)
        _finish_job(root, running_path, job, "done")
        return job, manifest_path

    except (ProviderNotConfigured, ProviderNotImplemented) as exc:
        # Provider-specific configuration/implementation errors
        failure_class = classify_failure(exc)
        job["error"] = {
            "type": exc.__class__.__name__,
            "message": str(exc),
        }
        job["failure"] = {
            **failure_class,
            "message": str(exc),
            "classified_at": utc_now(),
        }
        manifest_path = _write_manifest(
            root,
            job,
            "FAILED",
            {
                "error": job["error"],
                "failure_class": job["failure"],
            },
        )
        _finish_job(root, running_path, job, "failed")
        raise MotorError(f"Job {job['job_id']} failed. Manifest: {manifest_path}") from exc

    except Exception as exc:
        failure_class = classify_failure(exc)
        job["error"] = {
            "type": exc.__class__.__name__,
            "message": str(exc),
        }
        job["failure"] = {
            **failure_class,
            "message": str(exc),
            "classified_at": utc_now(),
        }
        manifest_path = _write_manifest(
            root,
            job,
            "FAILED",
            {
                "error": job["error"],
                "failure_class": job["failure"],
            },
        )
        _finish_job(root, running_path, job, "failed")
        raise MotorError(f"Job {job['job_id']} failed. Manifest: {manifest_path}") from exc
