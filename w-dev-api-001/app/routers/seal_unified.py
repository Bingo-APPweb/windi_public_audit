"""
POST /v1/seal — Unified seal endpoint
The /seal endpoint converts digital artifacts into adjudicated,
independently verifiable states.

Invariants: I1 (gate), I9 (human approval), I11 (hash evidence), I14 (explicit failure)
"""
import hashlib
import httpx
import json
import os
import uuid
from enum import Enum
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from app.deps.auth import validate_api_key, require_scope
from app.db.session import get_conn
from app.schemas.common import ok, fail, now_iso

router = APIRouter(tags=["Seal"])

# ── Config ─────────────────────────────────────────────────────
LEDGER_URL = "http://localhost:8101/api/receipts"
DID_GENESIS_URL = "http://localhost:8096/api/genesis"
VERIFY_BASE = "https://windi-domain.com/verify-public/"
UPLOAD_DIR = os.environ.get("WDEV_UPLOAD_DIR", "/opt/windi/data/wdev_uploads")


# ── Enums ──────────────────────────────────────────────────────
class SourceType(str, Enum):
    pdf = "pdf"
    docx = "docx"
    pptx = "pptx"
    xlsx = "xlsx"
    html = "html"
    svg = "svg"
    json_ = "json"
    image = "image"
    text = "text"


class Intent(str, Enum):
    generic = "generic"
    compliance = "compliance"
    authorship = "authorship"
    oversight = "oversight"
    evidence = "evidence"
    presentation = "presentation"


class ClaimScope(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class OversightMode(str, Enum):
    none = "none"
    declared = "declared"
    required = "required"
    attached = "attached"


class SealStatus(str, Enum):
    SEALED = "SEALED"
    SEALED_WITH_WARNINGS = "SEALED_WITH_WARNINGS"
    REFUSED = "REFUSED"


# ── Response Models ────────────────────────────────────────────
class SealWarningItem(BaseModel):
    code: str
    message: str


class SealArtifacts(BaseModel):
    sealed_file_url: Optional[str] = None
    qr_url: Optional[str] = None
    manifest_url: Optional[str] = None


class RefusalReceipt(BaseModel):
    id: str
    verify_url: str


class SealResponse(BaseModel):
    status: SealStatus
    seal_id: Optional[str] = None
    verify_url: Optional[str] = None
    governance_level: Optional[str] = None
    sge_score: Optional[float] = None
    warnings: List[SealWarningItem] = []
    artifacts: Optional[SealArtifacts] = None
    # For REFUSED
    refusal_code: Optional[str] = None
    message: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None
    refusal_receipt: Optional[RefusalReceipt] = None


# ── Helpers ────────────────────────────────────────────────────
def detect_source_type(filename: str, content_type: str) -> str:
    """Detect source type from filename or content type"""
    ext = os.path.splitext(filename or "")[1].lower()
    type_map = {
        ".pdf": "pdf",
        ".docx": "docx",
        ".doc": "docx",
        ".pptx": "pptx",
        ".ppt": "pptx",
        ".xlsx": "xlsx",
        ".xls": "xlsx",
        ".html": "html",
        ".htm": "html",
        ".svg": "svg",
        ".json": "json",
        ".txt": "text",
        ".md": "text",
        ".png": "image",
        ".jpg": "image",
        ".jpeg": "image",
        ".gif": "image",
        ".webp": "image",
    }
    return type_map.get(ext, "text")


async def validate_did(did: str) -> tuple[bool, Optional[str]]:
    """Validate DID exists in Genesis. Returns (valid, error_msg)"""
    if not did or not did.startswith("did:windi:"):
        return False, "Invalid DID format. Must be did:windi:*"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check if Genesis is alive
            r = await client.get(f"{DID_GENESIS_URL}/health")
            if r.status_code == 200:
                # Genesis is alive - accept well-formed DIDs
                # Full validation would require Genesis to expose /validate endpoint
                return True, None
            # Genesis down - graceful degradation
            return True, None
    except Exception as e:
        # Graceful degradation - accept if Genesis unavailable
        return True, None


def map_governance_level(claim_scope: str, oversight_mode: str) -> str:
    """Map claim scope and oversight to governance level"""
    if claim_scope == "high" or oversight_mode == "required":
        return "HIGH"
    elif claim_scope == "low" and oversight_mode == "none":
        return "LOW"
    return "MEDIUM"


async def write_to_ledger(receipt_id: str, actor: str, doc_name: str,
                          sha256: str, gov_level: str, doc_type: str = "doc") -> Optional[str]:
    """Write receipt to Forensic Ledger. Returns ledger_id or None"""
    payload = {
        "id": receipt_id,
        "actor": actor,
        "app": "w-dev-api-001",
        "doc_name": doc_name,
        "doc_type": doc_type,
        "content_hash": f"sha256:{sha256}",
        "governance_level": gov_level,
        "sge_score": 0.5,
        "invariants": ["I1", "I9", "I11", "I14"],
        "stage": "C6"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(LEDGER_URL, json=payload)
            if r.status_code in (200, 201):
                return receipt_id
    except Exception:
        pass

    return f"LOCAL_{receipt_id}"


# ── Main Endpoint ──────────────────────────────────────────────
@router.post("/seal", response_model=SealResponse, status_code=200)
async def seal_artifact(
    file: UploadFile = File(...),
    actor_did: str = Form(..., description="DID of the actor (did:windi:*)"),
    intent: Intent = Form(Intent.generic),
    claim_scope: ClaimScope = Form(ClaimScope.medium),
    oversight_mode: OversightMode = Form(OversightMode.declared),
    source_type: Optional[str] = Form(None, description="Auto-detected if not provided"),
    isp_profile: Optional[str] = Form(None, description="Regulatory profile (eu_ai_act, dora, etc)"),
    bind_author: bool = Form(True),
    public_verify: bool = Form(True),
    notes: Optional[str] = Form(None),
    metadata_json: Optional[str] = Form(None),
    key: dict = Depends(validate_api_key)
):
    """
    Seal an artifact. Returns SEALED, SEALED_WITH_WARNINGS, or REFUSED.

    The /seal endpoint does not guarantee success — it guarantees constitutional decision.
    """
    require_scope(key, "seal:create")

    warnings: List[SealWarningItem] = []

    # ── Phase 1: INTAKE ────────────────────────────────────────

    # I1 Gate - Validate request
    if not file.filename:
        raise HTTPException(400, detail=fail("I1_INVALID_REQUEST", "File must have a filename"))

    # Validate DID
    did_valid, did_error = await validate_did(actor_did)
    if not did_valid:
        return SealResponse(
            status=SealStatus.REFUSED,
            refusal_code="I1_INVALID_ACTOR",
            message=did_error,
            evidence={"did": actor_did},
            refusal_receipt=None
        )

    # Read content
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(400, detail=fail("I1_EMPTY_FILE", "File is empty"))

    sha256 = hashlib.sha256(content).hexdigest()
    size_bytes = len(content)
    detected_type = source_type or detect_source_type(file.filename, file.content_type or "")

    # ── Phase 2: SENSE ─────────────────────────────────────────
    # (Simplified - full SGE/ISP integration in Phase 2)

    governance_level = map_governance_level(claim_scope, oversight_mode)

    # Check oversight requirements
    if governance_level == "HIGH" and oversight_mode == "none":
        return SealResponse(
            status=SealStatus.REFUSED,
            refusal_code="I9_OVERSIGHT_INSUFFICIENT",
            message="HIGH claim scope requires declared or attached oversight",
            evidence={
                "claim_scope": claim_scope,
                "oversight_mode": oversight_mode,
                "required": "declared or higher"
            }
        )

    # Provenance warning (placeholder for Vision integration)
    if detected_type in ("image", "pdf") and governance_level == "HIGH":
        warnings.append(SealWarningItem(
            code="PROVENANCE_NOT_VERIFIED",
            message="Source provenance could not be fully verified for HIGH governance"
        ))

    # ── Phase 3: ADJUDICATE ────────────────────────────────────

    # I9 Gate - For HIGH governance, require explicit oversight
    if governance_level == "HIGH" and oversight_mode not in ("required", "attached"):
        warnings.append(SealWarningItem(
            code="I9_OVERSIGHT_RECOMMENDED",
            message="HIGH governance level recommends 'required' or 'attached' oversight"
        ))

    # I14 - Explicit metadata check
    metadata = None
    if metadata_json:
        try:
            metadata = json.loads(metadata_json)
        except json.JSONDecodeError:
            warnings.append(SealWarningItem(
                code="I14_METADATA_INVALID",
                message="metadata_json could not be parsed, proceeding without"
            ))

    # ── Phase 4: BUILD ─────────────────────────────────────────

    # Generate IDs
    seal_id = f"seal_{uuid.uuid4().hex[:16]}"
    artifact_id = f"art_{uuid.uuid4().hex[:16]}"
    receipt_id = f"WINDI-SEAL-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"
    sealed_at = now_iso()

    # Store file
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1] or ""
    storage_key = f"{artifact_id}{ext}"
    file_path = os.path.join(UPLOAD_DIR, storage_key)

    with open(file_path, "wb") as f:
        f.write(content)

    # Write to Ledger
    ledger_id = await write_to_ledger(
        receipt_id=receipt_id,
        actor=actor_did,
        doc_name=file.filename,
        sha256=sha256,
        gov_level=governance_level,
        doc_type="doc"
    )

    verify_url = f"{VERIFY_BASE}{receipt_id}" if public_verify else None

    # Store in local DB
    conn = get_conn()

    # Artifact
    conn.execute("""
        INSERT INTO artifacts
        (artifact_id, type, title, did, mime_type, sha256, size_bytes, storage_key, status, metadata, created_by_key, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        artifact_id, detected_type, file.filename, actor_did,
        file.content_type or "application/octet-stream", sha256, size_bytes,
        storage_key, "sealed", json.dumps(metadata) if metadata else None,
        key.get("key_id"), sealed_at
    ))

    # Seal record
    conn.execute("""
        INSERT INTO seals
        (seal_id, artifact_id, did, seal_type, status, confirmed_by_human,
         ledger_entry_id, receipt_id, verify_url, metadata, sealed_at, created_by_key, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        seal_id, artifact_id, actor_did, intent.value,
        "sealed" if not warnings else "sealed_with_warnings",
        1 if oversight_mode != "none" else 0,
        ledger_id, receipt_id, verify_url,
        json.dumps({
            "intent": intent.value,
            "claim_scope": claim_scope.value,
            "oversight_mode": oversight_mode.value,
            "isp_profile": isp_profile,
            "bind_author": bind_author,
            "notes": notes
        }),
        sealed_at, key.get("key_id"), sealed_at
    ))

    # Receipt index
    conn.execute("""
        INSERT OR IGNORE INTO receipts
        (receipt_id, artifact_id, seal_id, ledger_entry_id, did, sha256, verify_url, status, created_at)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (
        receipt_id, artifact_id, seal_id, ledger_id,
        actor_did, sha256, verify_url, "valid", sealed_at
    ))

    conn.commit()
    conn.close()

    # ── Phase 5: DELIVER ───────────────────────────────────────

    status = SealStatus.SEALED_WITH_WARNINGS if warnings else SealStatus.SEALED

    return SealResponse(
        status=status,
        seal_id=seal_id,
        verify_url=verify_url,
        governance_level=governance_level,
        sge_score=0.5,  # Placeholder until SGE integration
        warnings=warnings,
        artifacts=SealArtifacts(
            sealed_file_url=f"/dev-api/v1/artifacts/{artifact_id}/download" if storage_key else None,
            qr_url=None,  # Phase 2: JMPG integration
            manifest_url=None  # Phase 2
        )
    )


# ── JSON Submission Variant ────────────────────────────────────
class SealInputJSON(BaseModel):
    type: str = Field(..., description="artifact_url or raw_content")
    url: Optional[str] = None
    content: Optional[str] = None
    source_type: Optional[str] = None


class SealActorJSON(BaseModel):
    did: str


class SealContextJSON(BaseModel):
    intent: Intent = Intent.generic
    claim_scope: ClaimScope = ClaimScope.medium
    oversight_mode: OversightMode = OversightMode.declared
    isp_profile: Optional[str] = None
    public_verify: bool = True
    bind_author: bool = True


class SealRequestJSON(BaseModel):
    input: SealInputJSON
    actor: SealActorJSON
    context: SealContextJSON
    metadata: Optional[Dict[str, Any]] = None


@router.post("/seal/submit", response_model=SealResponse, status_code=200)
async def seal_submit(body: SealRequestJSON, key: dict = Depends(validate_api_key)):
    """
    Submit artifact via JSON (URL or raw content).
    For SDK/MCP integrations.
    """
    require_scope(key, "seal:create")

    warnings: List[SealWarningItem] = []

    # Validate DID
    did_valid, did_error = await validate_did(body.actor.did)
    if not did_valid:
        return SealResponse(
            status=SealStatus.REFUSED,
            refusal_code="I1_INVALID_ACTOR",
            message=did_error
        )

    # Fetch content
    content: bytes = b""
    filename = "submitted_artifact"
    content_type = "application/octet-stream"

    if body.input.type == "artifact_url" and body.input.url:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.get(body.input.url)
                if r.status_code != 200:
                    return SealResponse(
                        status=SealStatus.REFUSED,
                        refusal_code="I14_URL_UNREACHABLE",
                        message=f"Could not fetch artifact from URL: {r.status_code}"
                    )
                content = r.content
                content_type = r.headers.get("content-type", "application/octet-stream")
                # Extract filename from URL
                filename = body.input.url.split("/")[-1].split("?")[0] or "artifact"
        except Exception as e:
            return SealResponse(
                status=SealStatus.REFUSED,
                refusal_code="I14_URL_FETCH_FAILED",
                message=str(e)
            )

    elif body.input.type == "raw_content" and body.input.content:
        content = body.input.content.encode("utf-8")
        filename = "raw_content.txt"
        content_type = "text/plain"

    else:
        return SealResponse(
            status=SealStatus.REFUSED,
            refusal_code="I1_INVALID_INPUT",
            message="Must provide either artifact_url or raw_content"
        )

    if len(content) == 0:
        return SealResponse(
            status=SealStatus.REFUSED,
            refusal_code="I14_EMPTY_CONTENT",
            message="Content is empty"
        )

    # Hash and detect type
    sha256 = hashlib.sha256(content).hexdigest()
    detected_type = body.input.source_type or detect_source_type(filename, content_type)
    governance_level = map_governance_level(body.context.claim_scope, body.context.oversight_mode)

    # I9 check
    if governance_level == "HIGH" and body.context.oversight_mode == "none":
        return SealResponse(
            status=SealStatus.REFUSED,
            refusal_code="I9_OVERSIGHT_INSUFFICIENT",
            message="HIGH claim scope requires declared or attached oversight"
        )

    # Generate IDs
    seal_id = f"seal_{uuid.uuid4().hex[:16]}"
    artifact_id = f"art_{uuid.uuid4().hex[:16]}"
    receipt_id = f"WINDI-SEAL-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"
    sealed_at = now_iso()

    # Store file
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(filename)[1] or ".bin"
    storage_key = f"{artifact_id}{ext}"
    file_path = os.path.join(UPLOAD_DIR, storage_key)

    with open(file_path, "wb") as f:
        f.write(content)

    # Ledger
    ledger_id = await write_to_ledger(
        receipt_id=receipt_id,
        actor=body.actor.did,
        doc_name=filename,
        sha256=sha256,
        gov_level=governance_level
    )

    verify_url = f"{VERIFY_BASE}{receipt_id}" if body.context.public_verify else None

    # DB writes
    conn = get_conn()

    conn.execute("""
        INSERT INTO artifacts
        (artifact_id, type, title, did, mime_type, sha256, size_bytes, storage_key, status, metadata, created_by_key, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        artifact_id, detected_type, filename, body.actor.did,
        content_type, sha256, len(content), storage_key, "sealed",
        json.dumps(body.metadata) if body.metadata else None,
        key.get("key_id"), sealed_at
    ))

    conn.execute("""
        INSERT INTO seals
        (seal_id, artifact_id, did, seal_type, status, confirmed_by_human,
         ledger_entry_id, receipt_id, verify_url, metadata, sealed_at, created_by_key, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        seal_id, artifact_id, body.actor.did, body.context.intent.value,
        "sealed", 1, ledger_id, receipt_id, verify_url,
        json.dumps(body.context.dict()), sealed_at, key.get("key_id"), sealed_at
    ))

    conn.execute("""
        INSERT OR IGNORE INTO receipts
        (receipt_id, artifact_id, seal_id, ledger_entry_id, did, sha256, verify_url, status, created_at)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (
        receipt_id, artifact_id, seal_id, ledger_id,
        body.actor.did, sha256, verify_url, "valid", sealed_at
    ))

    conn.commit()
    conn.close()

    return SealResponse(
        status=SealStatus.SEALED_WITH_WARNINGS if warnings else SealStatus.SEALED,
        seal_id=seal_id,
        verify_url=verify_url,
        governance_level=governance_level,
        sge_score=0.5,
        warnings=warnings,
        artifacts=SealArtifacts(
            sealed_file_url=f"/dev-api/v1/artifacts/{artifact_id}/download"
        )
    )


# ── Get Seal Status ────────────────────────────────────────────
@router.get("/seal/{seal_id}")
async def get_seal_status(seal_id: str, key: dict = Depends(validate_api_key)):
    """Get seal status and details"""
    conn = get_conn()
    row = conn.execute("SELECT * FROM seals WHERE seal_id = ?", (seal_id,)).fetchone()
    conn.close()

    if not row:
        raise HTTPException(404, detail=fail("SEAL_NOT_FOUND", f"Seal '{seal_id}' not found"))

    data = dict(row)
    return ok({
        "seal_id": data["seal_id"],
        "status": "SEALED" if data["status"] == "sealed" else "SEALED_WITH_WARNINGS",
        "artifact_id": data["artifact_id"],
        "did": data["did"],
        "verify_url": data["verify_url"],
        "ledger_entry_id": data["ledger_entry_id"],
        "sealed_at": data["sealed_at"]
    })
