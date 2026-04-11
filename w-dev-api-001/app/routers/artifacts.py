"""
POST /v1/artifacts          — Register artifact by metadata
POST /v1/artifacts/upload   — Upload binary file
GET  /v1/artifacts/{id}     — Get artifact details
"""
import hashlib
import json
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
from app.deps.auth import validate_api_key, require_scope
from app.db.session import get_conn
from app.schemas.common import ok, fail, now_iso

router = APIRouter(tags=["Artifacts"])

UPLOAD_DIR = os.environ.get("WDEV_UPLOAD_DIR", "/opt/windi/data/wdev_uploads")


class ArtifactContent(BaseModel):
    mime_type: str
    sha256: str
    size_bytes: Optional[int] = None
    filename: Optional[str] = None


class ArtifactCreate(BaseModel):
    type: str = "document"
    title: Optional[str] = None
    did: str
    content: ArtifactContent
    metadata: Optional[dict] = None


@router.post("/artifacts", status_code=201)
async def create_artifact(body: ArtifactCreate, key: dict = Depends(validate_api_key)):
    """Register artifact by metadata (hash already known)"""
    require_scope(key, "seal:create")

    artifact_id = f"art_{uuid.uuid4().hex[:16]}"
    created_at = now_iso()

    conn = get_conn()
    conn.execute("""
        INSERT INTO artifacts
        (artifact_id, type, title, did, mime_type, sha256, size_bytes, storage_key, status, metadata, created_by_key, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        artifact_id,
        body.type,
        body.title or body.content.filename or artifact_id,
        body.did,
        body.content.mime_type,
        body.content.sha256,
        body.content.size_bytes,
        None,  # No storage for metadata-only
        "created",
        json.dumps(body.metadata) if body.metadata else None,
        key.get("key_id"),
        created_at
    ))
    conn.commit()
    conn.close()

    return ok({
        "artifact_id": artifact_id,
        "type": body.type,
        "title": body.title,
        "did": body.did,
        "sha256": body.content.sha256,
        "status": "created",
        "created_at": created_at
    })


@router.post("/artifacts/upload", status_code=201)
async def upload_artifact(
    file: UploadFile = File(...),
    did: str = Form(...),
    type: str = Form("document"),
    title: str = Form(None),
    key: dict = Depends(validate_api_key)
):
    """Upload binary file"""
    require_scope(key, "seal:create")

    # Read and hash
    content = await file.read()
    sha256 = hashlib.sha256(content).hexdigest()
    size_bytes = len(content)

    artifact_id = f"art_{uuid.uuid4().hex[:16]}"
    created_at = now_iso()

    # Store file
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename or "")[1] or ""
    storage_key = f"{artifact_id}{ext}"
    file_path = os.path.join(UPLOAD_DIR, storage_key)

    with open(file_path, "wb") as f:
        f.write(content)

    conn = get_conn()
    conn.execute("""
        INSERT INTO artifacts
        (artifact_id, type, title, did, mime_type, sha256, size_bytes, storage_key, status, metadata, created_by_key, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        artifact_id,
        type,
        title or file.filename or artifact_id,
        did,
        file.content_type or "application/octet-stream",
        sha256,
        size_bytes,
        storage_key,
        "created",
        None,
        key.get("key_id"),
        created_at
    ))
    conn.commit()
    conn.close()

    return ok({
        "artifact_id": artifact_id,
        "sha256": sha256,
        "size_bytes": size_bytes,
        "storage_key": storage_key,
        "status": "created",
        "created_at": created_at
    })


@router.get("/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str, key: dict = Depends(validate_api_key)):
    """Get artifact details"""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM artifacts WHERE artifact_id = ?", (artifact_id,)
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(404, detail=fail("ARTIFACT_NOT_FOUND", f"Artifact '{artifact_id}' not found"))

    return ok(dict(row))
