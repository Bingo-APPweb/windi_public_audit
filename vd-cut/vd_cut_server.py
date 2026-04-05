"""
W-VD-CUT-001 — WINDI Video Cut Engine
Micro-story processor for mobile-first video sealing

Port: 8128
"Client handles preview. Server executes EDL."

Liga IA+H · Kempten, Bavaria · 2026
Human Dragon + Guardian + Architect + Witness
"AI processes. Human decides. WINDI guarantees."
"""

import os
import sys
import uuid
import json
import sqlite3
import hashlib
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Configuration
PORT = int(os.environ.get("VD_CUT_PORT", 8128))
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

# Paths
BASE_DIR = Path("/opt/windi/vd-cut")
MEDIA_DIR = Path("/opt/windi/media/vd-cut")
DB_PATH = BASE_DIR / "vd_cut.db"

INCOMING_DIR = MEDIA_DIR / "incoming"
PROCESSING_DIR = MEDIA_DIR / "processing"
EXPORTS_DIR = MEDIA_DIR / "exports"
THUMBS_DIR = MEDIA_DIR / "thumbs"
TEMP_DIR = MEDIA_DIR / "temp"
SEALED_DIR = MEDIA_DIR / "sealed"
VAULT_PATH = Path("/opt/windi/forensic-vault/vd-cut")

# Operational Limits
MAX_DURATION_SECONDS = 120  # 2 minutes
MAX_FILE_SIZE_MB = 250
MAX_CONCURRENT_JOBS = 1
MAX_QUEUED_PER_USER = 1
ORIGINAL_RETENTION_HOURS = 720   # 30 dias — tempo real para decisão humana
SEALED_RETENTION_DAYS = 30       # exports editáveis antes do vault definitivo

# Logging
log_level = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=log_level,
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("w-vd-cut-001")

# Reduce noise
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


# ----- Database -----

def get_db():
    """Get database connection."""
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database from migration."""
    migration_path = BASE_DIR / "db" / "migrations" / "001_initial_schema.sql"
    if not migration_path.exists():
        log.error(f"Migration not found: {migration_path}")
        return False

    try:
        with open(migration_path) as f:
            schema = f.read()

        conn = get_db()
        conn.executescript(schema)
        conn.commit()
        conn.close()
        log.info("Database initialized")
        return True
    except Exception as e:
        log.error(f"Database init failed: {e}")
        return False


# ----- Pydantic Models -----

class EDLSegment(BaseModel):
    in_point: float  # seconds
    out_point: float  # seconds


class EDLRequest(BaseModel):
    project_id: str
    source_asset: str
    edl: list[EDLSegment]
    format: str = "9:16"
    resolution: str = "1080x1920"
    preset: str = "story_clean"
    filters: Optional[Dict[str, Any]] = None
    bts: bool = False
    audio_normalize: bool = True


class SealRequest(BaseModel):
    project_id: str
    export_id: str
    wallet_id: str
    human_approved: bool = False  # I9 gate


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    port: int
    ffmpeg_available: bool
    active_jobs: int
    queued_jobs: int


class JoeClip(BaseModel):
    asset_id: str
    in_ms: int = 0
    out_ms: int
    order: int = 1
    label: Optional[str] = None


class JoeSequence(BaseModel):
    story_id: Optional[str] = None
    clips: list[JoeClip]
    preset: str = "story_clean"


class JoeRenderRequest(BaseModel):
    project_id: str
    actor_did: str
    sequence: JoeSequence
    auto_seal: bool = False  # I9: default False


class FrameSealRequest(BaseModel):
    """Request to seal specific frames (edit points) to Ledger."""
    video_path: str               # Path to video file
    actor_did: str                # WINDI DID
    edit_points: list[int]        # Frame indices to seal
    fps: float = 25.0             # Video FPS
    source_hash: Optional[str] = None  # Pre-computed hash (optional)


class FrameVerifyRequest(BaseModel):
    """Request to verify a frame against expected hash."""
    video_path: str
    frame_index: int
    expected_hash: str


# ----- Lifespan -----

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    log.info("=" * 50)
    log.info("W-VD-CUT-001 — WINDI Video Cut Engine")
    log.info("=" * 50)
    log.info(f"Port: {PORT}")
    log.info(f"Database: {DB_PATH}")
    log.info(f"Media: {MEDIA_DIR}")
    log.info("=" * 50)

    # Initialize database
    init_db()

    # Check FFmpeg
    from services.ffmpeg_service import check_ffmpeg
    if check_ffmpeg():
        log.info("FFmpeg: AVAILABLE")
    else:
        log.warning("FFmpeg: NOT AVAILABLE - encoding will fail")

    yield

    log.info("W-VD-CUT-001 shutting down")


# ----- FastAPI App -----

app = FastAPI(
    title="W-VD-CUT-001",
    description="WINDI Video Cut Engine",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files for V.I.R. reports
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/vd-cut/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ----- Utility Functions -----

def generate_project_id() -> str:
    """Generate unique project ID."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"VDCUT-{ts}-{uuid.uuid4().hex[:8].upper()}"


def generate_asset_id() -> str:
    """Generate unique asset ID."""
    return f"ASSET-{uuid.uuid4().hex[:12].upper()}"


def generate_job_id() -> str:
    """Generate unique job ID."""
    return f"JOB-{uuid.uuid4().hex[:12].upper()}"


def generate_export_id() -> str:
    """Generate unique export ID."""
    return f"EXPORT-{uuid.uuid4().hex[:12].upper()}"


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return f"sha256:{sha256.hexdigest()}"


def get_job_counts() -> tuple[int, int]:
    """Get (active, queued) job counts."""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM video_jobs WHERE status = 'ACTIVE'")
        active = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM video_jobs WHERE status = 'QUEUED'")
        queued = cursor.fetchone()[0]

        conn.close()
        return (active, queued)
    except Exception:
        return (0, 0)


# ----- Endpoints -----

@app.get("/vd-cut/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    from services.ffmpeg_service import check_ffmpeg

    active, queued = get_job_counts()

    return HealthResponse(
        status="healthy",
        service="W-VD-CUT-001",
        version="1.0.0",
        port=PORT,
        ffmpeg_available=check_ffmpeg(),
        active_jobs=active,
        queued_jobs=queued
    )


@app.post("/vd-cut/intake")
async def intake_video(
    video: UploadFile = File(...),
    did: str = Form(...),
    telegram_id: Optional[int] = Form(None),
    title: Optional[str] = Form(None)
):
    """
    Receive video file and create project.

    Validates:
    - File size (max 250MB)
    - Duration (max 2 minutes) - checked after FFprobe
    - Creates project + asset records

    Returns project_id and asset_id for subsequent operations.
    """
    from services.ffmpeg_service import probe_video

    # Validate file size
    file_size = 0
    temp_path = TEMP_DIR / f"{uuid.uuid4().hex}.tmp"

    try:
        with open(temp_path, "wb") as f:
            while chunk := await video.read(1024 * 1024):  # 1MB chunks
                file_size += len(chunk)
                if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                    temp_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum: {MAX_FILE_SIZE_MB}MB"
                    )
                f.write(chunk)

        # Probe video
        probe_result = await probe_video(temp_path)

        if probe_result.get("error"):
            temp_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=400,
                detail=f"Invalid video file: {probe_result.get('message')}"
            )

        # Check duration
        duration = probe_result.get("duration", 0)
        if duration > MAX_DURATION_SECONDS:
            temp_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=400,
                detail=f"Video too long. Maximum: {MAX_DURATION_SECONDS} seconds"
            )

        # Create project
        project_id = generate_project_id()
        asset_id = generate_asset_id()

        # Move to incoming directory
        incoming_path = INCOMING_DIR / f"{asset_id}.mp4"
        temp_path.rename(incoming_path)

        # Compute hash
        content_hash = compute_file_hash(incoming_path)

        # Calculate expiry
        expires_at = datetime.now(timezone.utc) + timedelta(hours=ORIGINAL_RETENTION_HOURS)

        # Store in database
        conn = get_db()
        cursor = conn.cursor()

        # Insert project
        cursor.execute("""
            INSERT INTO video_projects (id, wallet_id, telegram_id, title, status)
            VALUES (?, ?, ?, ?, 'CREATED')
        """, (project_id, did, telegram_id, title or video.filename))

        # Insert asset
        cursor.execute("""
            INSERT INTO video_assets
            (id, project_id, original_filename, stored_path, file_size,
             duration_seconds, width, height, codec, fps, content_hash, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            asset_id, project_id, video.filename, str(incoming_path), file_size,
            duration, probe_result.get("width"), probe_result.get("height"),
            probe_result.get("codec"), probe_result.get("fps"),
            content_hash, expires_at.isoformat()
        ))

        conn.commit()
        conn.close()

        log.info(f"Video intake: project={project_id}, asset={asset_id}, duration={duration:.1f}s")

        return {
            "project_id": project_id,
            "asset_id": asset_id,
            "duration": duration,
            "width": probe_result.get("width"),
            "height": probe_result.get("height"),
            "file_size": file_size,
            "content_hash": content_hash,
            "expires_at": expires_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        temp_path.unlink(missing_ok=True)
        log.error(f"Intake error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/vd-cut/job/create")
async def create_job(edl: EDLRequest, background_tasks: BackgroundTasks):
    """
    Create encoding job from EDL.

    Validates:
    - Project and asset exist
    - User hasn't exceeded queue limit
    - EDL is valid

    Starts background processing if queue has capacity.
    """
    from services.queue_service import can_queue_job, process_job

    # Validate project exists
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM video_projects WHERE id = ?", (edl.project_id,))
    project = cursor.fetchone()

    if not project:
        conn.close()
        raise HTTPException(status_code=404, detail="Project not found")

    cursor.execute("SELECT * FROM video_assets WHERE id = ?", (edl.source_asset,))
    asset = cursor.fetchone()

    if not asset:
        conn.close()
        raise HTTPException(status_code=404, detail="Asset not found")

    # Check queue limits
    wallet_id = project["wallet_id"]
    if not can_queue_job(wallet_id):
        conn.close()
        raise HTTPException(
            status_code=429,
            detail=f"Queue limit reached. Max {MAX_QUEUED_PER_USER} jobs per user."
        )

    # Create job
    job_id = generate_job_id()
    edl_json = json.dumps([{"in": s.in_point, "out": s.out_point} for s in edl.edl])

    cursor.execute("""
        INSERT INTO video_jobs
        (id, project_id, asset_id, edl_json, preset, status)
        VALUES (?, ?, ?, ?, ?, 'QUEUED')
    """, (job_id, edl.project_id, edl.source_asset, edl_json, edl.preset))

    conn.commit()
    conn.close()

    log.info(f"Job created: {job_id} for project {edl.project_id}")

    # Start processing in background
    background_tasks.add_task(process_job, job_id)

    return {
        "job_id": job_id,
        "project_id": edl.project_id,
        "status": "QUEUED",
        "preset": edl.preset
    }


@app.get("/vd-cut/job/{job_id}")
async def get_job_status(job_id: str):
    """Get job status and progress."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT j.*, e.id as export_id, e.output_path, e.thumbnail_path, e.content_hash
        FROM video_jobs j
        LEFT JOIN video_exports e ON e.job_id = j.id
        WHERE j.id = ?
    """, (job_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Job not found")

    result = {
        "job_id": row["id"],
        "project_id": row["project_id"],
        "status": row["status"],
        "progress": row["progress_percent"],
        "preset": row["preset"],
        "created_at": row["created_at"],
        "started_at": row["started_at"],
        "completed_at": row["completed_at"]
    }

    if row["status"] == "FAILED":
        result["error"] = row["error_message"]

    if row["export_id"]:
        result["export"] = {
            "id": row["export_id"],
            "content_hash": row["content_hash"],
            "thumbnail_available": bool(row["thumbnail_path"])
        }

    return result


def archive_to_vault(export_path: str, receipt_id: str) -> str:
    """
    Archive sealed export to Forensic Vault for permanent storage.

    I11 COMPLIANCE: Vault preserves the file, Ledger preserves the hash.
    Two independent systems ensuring evidence permanence.

    Args:
        export_path: Path to sealed export file
        receipt_id: Ledger receipt ID for naming

    Returns:
        Path to archived file in Vault
    """
    import shutil

    source = Path(export_path)
    if not source.exists():
        log.warning(f"Vault archive skipped: file not found {export_path}")
        return None

    # Ensure vault directory exists
    VAULT_PATH.mkdir(parents=True, exist_ok=True)

    # Format: WINDI-VDCUT-20260405-XXXXX_original.mp4
    dest = VAULT_PATH / f"{receipt_id}_{source.name}"

    try:
        shutil.copy2(source, dest)
        log.info(f"Vault archived: {receipt_id} -> {dest}")
        return str(dest)
    except Exception as e:
        log.error(f"Vault archive failed: {e}")
        return None


@app.post("/vd-cut/seal")
async def seal_export(request: SealRequest):
    """
    Seal export to Ledger.

    I9 GATE: human_approved MUST be True.
    I11: Only content_hash goes to Ledger, never raw video.

    Returns receipt_id and verify_url.
    """
    from services.seal_service import seal_to_ledger

    # I9 GATE - CRITICAL
    if not request.human_approved:
        raise HTTPException(
            status_code=403,
            detail="I9 VIOLATION: human_approved must be true before seal"
        )

    # Validate export exists
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT e.*, p.wallet_id, p.title
        FROM video_exports e
        JOIN video_projects p ON e.project_id = p.id
        WHERE e.id = ? AND e.project_id = ?
    """, (request.export_id, request.project_id))

    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Export not found")

    # Verify wallet matches
    if row["wallet_id"] != request.wallet_id:
        conn.close()
        raise HTTPException(status_code=403, detail="Wallet mismatch")

    # Check if already sealed
    cursor.execute("""
        SELECT * FROM video_receipts
        WHERE export_id = ? AND status = 'SEALED'
    """, (request.export_id,))

    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=409, detail="Already sealed")

    # Create pending receipt
    cursor.execute("""
        INSERT INTO video_receipts
        (project_id, export_id, wallet_id, content_hash, human_approved, approved_at, status)
        VALUES (?, ?, ?, ?, 1, ?, 'APPROVED')
    """, (
        request.project_id, request.export_id, request.wallet_id,
        row["content_hash"], datetime.now(timezone.utc).isoformat()
    ))

    pending_id = cursor.lastrowid
    conn.commit()

    # Seal to Ledger
    seal_result = await seal_to_ledger(
        wallet_id=request.wallet_id,
        content_hash=row["content_hash"],
        project_id=request.project_id,
        title=row["title"],
        duration=row["duration_seconds"],
        resolution=f"{row['width']}x{row['height']}"
    )

    if seal_result.get("error"):
        cursor.execute("""
            UPDATE video_receipts SET status = 'FAILED' WHERE id = ?
        """, (pending_id,))
        conn.commit()
        conn.close()
        raise HTTPException(
            status_code=503,
            detail=f"Ledger seal failed: {seal_result.get('message')}"
        )

    # Update receipt with Ledger info
    cursor.execute("""
        UPDATE video_receipts
        SET receipt_id = ?, verify_url = ?, sealed_at = ?, status = 'SEALED'
        WHERE id = ?
    """, (
        seal_result.get("receipt_id"),
        seal_result.get("verify_url"),
        datetime.now(timezone.utc).isoformat(),
        pending_id
    ))

    # Update project status
    cursor.execute("""
        UPDATE video_projects SET status = 'SEALED', updated_at = ? WHERE id = ?
    """, (datetime.now(timezone.utc).isoformat(), request.project_id))

    # Move export to sealed directory
    from pathlib import Path
    export_path = Path(row["output_path"])
    if export_path.exists():
        sealed_path = SEALED_DIR / export_path.name
        export_path.rename(sealed_path)

        cursor.execute("""
            UPDATE video_exports SET output_path = ? WHERE id = ?
        """, (str(sealed_path), request.export_id))

    conn.commit()
    conn.close()

    log.info(f"Export sealed: {request.export_id} -> {seal_result.get('receipt_id')}")

    # Archive to Forensic Vault for permanent storage (I11)
    vault_path = None
    if export_path.exists() or sealed_path.exists():
        archive_source = sealed_path if sealed_path.exists() else export_path
        vault_path = archive_to_vault(str(archive_source), seal_result.get("receipt_id"))

    return {
        "sealed": True,
        "receipt_id": seal_result.get("receipt_id"),
        "verify_url": seal_result.get("verify_url"),
        "content_hash": row["content_hash"],
        "project_id": request.project_id,
        "export_id": request.export_id,
        "vault_archived": vault_path is not None,
        "vault_path": vault_path
    }


@app.get("/vd-cut/project/{project_id}")
async def get_project(project_id: str):
    """Get project info with assets, jobs, and receipts."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM video_projects WHERE id = ?", (project_id,))
    project = cursor.fetchone()

    if not project:
        conn.close()
        raise HTTPException(status_code=404, detail="Project not found")

    cursor.execute("SELECT * FROM video_assets WHERE project_id = ?", (project_id,))
    assets = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT * FROM video_jobs WHERE project_id = ?", (project_id,))
    jobs = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT * FROM video_exports WHERE project_id = ?", (project_id,))
    exports = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT * FROM video_receipts WHERE project_id = ?", (project_id,))
    receipts = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "project": dict(project),
        "assets": assets,
        "jobs": jobs,
        "exports": exports,
        "receipts": receipts
    }


@app.get("/vd-cut/media/{export_id}")
async def download_export(export_id: str):
    """Download exported video file."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM video_exports WHERE id = ?", (export_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Export not found")

    file_path = Path(row["output_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        file_path,
        media_type="video/mp4",
        filename=f"{export_id}.mp4"
    )


@app.get("/vd-cut/thumb/{export_id}")
async def get_thumbnail(export_id: str):
    """Get thumbnail for export."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT thumbnail_path FROM video_exports WHERE id = ?", (export_id,))
    row = cursor.fetchone()
    conn.close()

    if not row or not row["thumbnail_path"]:
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    thumb_path = Path(row["thumbnail_path"])
    if not thumb_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail file not found")

    return FileResponse(
        thumb_path,
        media_type="image/jpeg",
        filename=f"{export_id}_thumb.jpg"
    )


@app.get("/vd-cut/preview/{export_id}")
async def get_preview(export_id: str):
    """
    Get full-size preview frame for export.

    Unlike thumbnail (320x568), preview preserves original resolution.
    Generated on-demand and cached in /previews/ directory.

    Use this for detailed inspection in dashboard.
    Use /thumb/ for thread lists and quick loading.
    """
    from services.ffmpeg_service import generate_preview

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT output_path FROM video_exports WHERE id = ?", (export_id,))
    row = cursor.fetchone()
    conn.close()

    if not row or not row["output_path"]:
        raise HTTPException(status_code=404, detail="Export not found")

    video_path = Path(row["output_path"])
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    # Preview cache directory
    preview_dir = MEDIA_DIR / "previews"
    preview_dir.mkdir(exist_ok=True)
    preview_path = preview_dir / f"{export_id}_preview.jpg"

    # Generate if not cached
    if not preview_path.exists():
        result = await generate_preview(
            video_path=video_path,
            output_path=preview_path,
            timestamp=1.0
        )
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result.get("message"))

    return FileResponse(
        preview_path,
        media_type="image/jpeg",
        filename=f"{export_id}_preview.jpg"
    )


# ----- JOE Bridge Endpoint -----

@app.post("/vd-cut/joe/render")
async def joe_render(request: JoeRenderRequest):
    """
    Entry point for W-JOE-001 Director de Transmissao.

    Receives JOE sequence -> converts to EDL -> renders -> returns job info.

    I9 COMPLIANCE:
        Seal does NOT happen here.
        Human must confirm via separate POST /vd-cut/seal endpoint.
        auto_seal parameter exists but requires upstream human confirmation.

    Flow:
        JOE sequence -> sequence_to_edl -> /job/create -> poll -> result
                                                              |
                                                    (seal is separate)

    Returns:
        {
            "status": "rendered",
            "job_id": "...",
            "export_id": "...",
            "preview_url": "...",
            "download_url": "...",
            "seal_pending": true,
            "seal_action": "POST /vd-cut/seal with human_approved=true",
            "invariant": "I9"
        }
    """
    from services.joe_bridge import bridge

    # Convert Pydantic to dict for bridge
    sequence_dict = {
        "story_id": request.sequence.story_id,
        "clips": [
            {
                "asset_id": clip.asset_id,
                "in_ms": clip.in_ms,
                "out_ms": clip.out_ms,
                "order": clip.order,
                "label": clip.label
            }
            for clip in request.sequence.clips
        ],
        "preset": request.sequence.preset
    }

    log.info(f"JOE render request: project={request.project_id}, clips={len(request.sequence.clips)}")

    result = await bridge.render_sequence(
        sequence=sequence_dict,
        project_id=request.project_id,
        actor_did=request.actor_did,
        auto_seal=request.auto_seal  # I9: passed through but humano must confirm upstream
    )

    if result.get("status") == "failed":
        log.error(f"JOE render failed: {result.get('error')}")
        return JSONResponse(
            status_code=400,
            content={
                "status": "failed",
                "error": result.get("error"),
                "stage": result.get("stage"),
                "detail": result.get("detail")
            }
        )

    if result.get("status") == "timeout":
        log.warning(f"JOE render timeout: job={result.get('job_id')}")
        return JSONResponse(
            status_code=408,
            content={
                "status": "timeout",
                "job_id": result.get("job_id"),
                "message": "Encoding took too long. Check job status manually.",
                "check_url": f"/vd-cut/job/{result.get('job_id')}"
            }
        )

    return {
        "status": "rendered",
        "job_id": result.get("job_id"),
        "export_id": result.get("export_id"),
        "content_hash": result.get("content_hash"),
        "preview_url": result.get("preview_url"),
        "download_url": result.get("download_url"),
        "story_id": result.get("story_id"),
        "preset": result.get("preset"),
        "seal_pending": result.get("seal_pending", True),
        "seal_action": result.get("seal_action"),
        "next_step": "POST /vd-cut/seal with human_approved=true to finalize",
        "invariant": "I9 · humano confirma antes do seal"
    }


# ----- Frame Integrity Engine -----

@app.post("/vd-cut/seal-frames")
async def seal_edit_frames(request: FrameSealRequest):
    """
    Seal edit points (frame-level) to Ledger.

    "Deepfake Killer" — Each edit point is sealed with hash chain.
    Any subsequent alteration invalidates the chain.

    I9 COMPLIANCE:
    This endpoint requires explicit human invocation.
    Each frame seal is a conscious decision.
    Never auto-seal entire timeline.

    I11 COMPLIANCE:
    Only frame hashes go to Ledger, never raw frame data.

    Args:
        video_path: Path to video file (in /opt/windi/media/vd-cut/)
        actor_did: WINDI DID of actor
        edit_points: List of frame indices to seal
        fps: Video frames per second

    Returns:
        EditManifest with all sealed frames and chain info
    """
    from services.frame_integrity_engine import FrameIntegrityEngine

    # Validate video path exists
    video_path = Path(request.video_path)
    if not video_path.exists():
        # Try relative to media directory
        video_path = MEDIA_DIR / request.video_path
        if not video_path.exists():
            raise HTTPException(status_code=404, detail="Video not found")

    if not request.edit_points:
        raise HTTPException(status_code=400, detail="edit_points required")

    log.info(f"Frame seal request: {len(request.edit_points)} edit points, actor={request.actor_did}")

    try:
        engine = FrameIntegrityEngine(
            video_path=str(video_path),
            actor_did=request.actor_did,
            source_hash=request.source_hash
        )

        manifest = await engine.seal_edit_points(
            edit_points=request.edit_points,
            fps=request.fps
        )

        return {
            "status": "sealed",
            "manifest_version": manifest.manifest_version,
            "source_video": manifest.source_video,
            "source_hash": manifest.source_hash,
            "edit_points_sealed": len(manifest.edit_points),
            "chain_root": manifest.chain_root,
            "chain_tip": manifest.chain_tip,
            "manifest_receipt": manifest.manifest_receipt,
            "verify_url": manifest.verify_url,
            "edit_points": manifest.edit_points,
            "invariants": manifest.windi_invariants
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        log.error(f"Frame seal error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/vd-cut/verify-frame")
async def verify_frame_integrity(request: FrameVerifyRequest):
    """
    Verify a frame against expected hash.

    Deepfake detection: if current frame hash doesn't match
    sealed hash, video was tampered.

    Args:
        video_path: Path to video file
        frame_index: Frame to verify
        expected_hash: Hash from sealed FrameSeal

    Returns:
        Verification result with match status
    """
    from services.frame_integrity_engine import verify_single_frame

    video_path = Path(request.video_path)
    if not video_path.exists():
        video_path = MEDIA_DIR / request.video_path
        if not video_path.exists():
            raise HTTPException(status_code=404, detail="Video not found")

    try:
        result = await verify_single_frame(
            video_path=str(video_path),
            frame_index=request.frame_index,
            expected_hash=request.expected_hash
        )

        return result

    except Exception as e:
        log.error(f"Frame verify error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/vd-cut/frame-hash/{export_id}/{frame_index}")
async def get_frame_hash(export_id: str, frame_index: int):
    """
    Compute hash of a specific frame from an export.

    Useful for building verification chains without sealing.
    """
    from services.frame_integrity_engine import FrameIntegrityEngine

    # Find export path
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT output_path FROM video_exports WHERE id = ?", (export_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Export not found")

    video_path = Path(row["output_path"])
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    try:
        engine = FrameIntegrityEngine(
            video_path=str(video_path),
            actor_did="frame_hash_query"
        )

        fps = await engine.get_video_fps()
        frame_hash = await engine.compute_frame_hash(frame_index)
        timestamp_ms = engine.get_frame_timestamp(frame_index, fps)

        return {
            "export_id": export_id,
            "frame_index": frame_index,
            "timestamp_ms": timestamp_ms,
            "frame_hash": frame_hash,
            "source_hash": engine.source_hash,
            "fps": fps
        }

    except Exception as e:
        log.error(f"Frame hash error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ----- Transcription (Whisper) -----

class TranscribeRequest(BaseModel):
    """Request for video transcription."""
    video_path: str
    model: str = "base"  # tiny/base/small/medium
    language: Optional[str] = None  # auto-detect if None


class TextToCutRequest(BaseModel):
    """Find timestamps for selected text."""
    transcription: Dict[str, Any]
    selected_text: str


class LegalOverlayRequest(BaseModel):
    """Add legal watermark to video."""
    input_path: str
    output_path: str
    case_ref: str
    court: Optional[str] = None
    timestamp: Optional[str] = None


@app.post("/vd-cut/transcribe")
async def transcribe_video_endpoint(request: TranscribeRequest):
    """
    Transcribe video audio with word-level timestamps.

    Uses OpenAI Whisper (local, no cloud dependency).

    Models:
    - tiny: 39M, ~32x realtime, basic accuracy
    - base: 74M, ~16x realtime, good accuracy (default)
    - small: 244M, ~6x realtime, better accuracy
    - medium: 769M, ~2x realtime, high accuracy

    Returns segments with timestamps for cut-by-text feature.

    Invariants: None (read-only operation)
    """
    from services.transcribe_service import transcribe_video

    video_path = Path(request.video_path)
    if not video_path.exists():
        # Try relative to media dir
        video_path = MEDIA_DIR / request.video_path
        if not video_path.exists():
            raise HTTPException(status_code=404, detail="Video not found")

    log.info(f"Transcription request: {video_path.name}, model={request.model}")

    result = await transcribe_video(
        video_path=video_path,
        model_name=request.model,
        language=request.language
    )

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result.get("message"))

    return result


@app.post("/vd-cut/text-to-cuts")
async def text_to_cuts_endpoint(request: TextToCutRequest):
    """
    Find video timestamps for selected text.

    Workflow:
    1. POST /vd-cut/transcribe → get transcription with timestamps
    2. User selects text portion in UI
    3. POST /vd-cut/text-to-cuts → get start/end timestamps
    4. Use timestamps for FFmpeg cut

    Returns list of matching segments with timestamps.
    """
    from services.transcribe_service import text_to_cuts

    matches = text_to_cuts(
        transcription=request.transcription,
        selected_text=request.selected_text
    )

    return {
        "query": request.selected_text,
        "matches": matches,
        "count": len(matches)
    }


@app.post("/vd-cut/legal-overlay")
async def legal_overlay_endpoint(request: LegalOverlayRequest):
    """
    Add legal watermark overlay to video.

    Overlay includes:
    - Case reference number
    - Court name (optional)
    - UTC timestamp

    Semi-transparent background, bottom-left position.

    Invariants: None (creates new file, doesn't modify original)
    """
    from services.transcribe_service import add_legal_overlay

    input_path = Path(request.input_path)
    if not input_path.exists():
        input_path = MEDIA_DIR / request.input_path
        if not input_path.exists():
            raise HTTPException(status_code=404, detail="Input video not found")

    output_path = Path(request.output_path)
    if not output_path.parent.exists():
        output_path = EXPORTS_DIR / output_path.name

    log.info(f"Legal overlay request: {request.case_ref}")

    result = await add_legal_overlay(
        input_path=input_path,
        output_path=output_path,
        case_ref=request.case_ref,
        court=request.court,
        timestamp=request.timestamp
    )

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result.get("message"))

    return result


@app.get("/vd-cut/transcribe/models")
async def list_transcribe_models():
    """
    List available Whisper models.

    Returns model names with size and speed info.
    """
    from services.transcribe_service import MODELS, DEFAULT_MODEL

    return {
        "models": MODELS,
        "default": DEFAULT_MODEL,
        "note": "First transcription with a model will download it (~1-2 min)"
    }


# ----- Distribution (W-DIST-001) -----

class DistributeRequest(BaseModel):
    """Request for distributing a communiqué."""
    communique: Dict[str, Any]
    channel: str  # "telegram" or "email"
    options: Optional[Dict[str, Any]] = None


@app.post("/comm/distribute")
async def distribute_communique(request: DistributeRequest):
    """
    Distribute a sealed communiqué via W-DIST-001.

    Channels:
    - telegram: Opens Telegram share (client-side redirect)
    - email: Sends SMTP email with verify link

    Args:
        communique: Dict with receipt_id, evidence_verify_url, title_*
        channel: Distribution channel name
        options: Channel-specific options (e.g., {to: "email@...", lang: "de"})

    Returns:
        Distribution result from W-DIST-001
    """
    import sys
    sys.path.insert(0, '/opt/windi/communique')

    try:
        from channels import channel_email

        if request.channel == "email":
            options = request.options or {}
            result = channel_email.send(
                communique=request.communique,
                to=options.get("to"),
                lang=options.get("lang", "de"),
                attach_jmpg=options.get("attach_jmpg", False)
            )
            return result

        elif request.channel == "telegram":
            # Telegram is handled client-side via URL scheme
            return {
                "success": True,
                "channel": "telegram",
                "message": "Telegram share handled client-side"
            }

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown channel: {request.channel}. Available: email, telegram"
            )

    except ImportError as e:
        log.error(f"Distribution import error: {e}")
        raise HTTPException(status_code=500, detail=f"Distribution channel not available: {e}")
    except Exception as e:
        log.error(f"Distribution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/comm/channels")
async def list_distribution_channels():
    """
    List available distribution channels.

    Returns channel names and their status.
    """
    import sys
    sys.path.insert(0, '/opt/windi/communique')

    channels = []

    # Check email
    try:
        from channels import channel_email
        info = channel_email.get_info()
        channels.append({
            "name": "email",
            "available": info.get("configured", False),
            "smtp_host": info.get("smtp_host"),
            "from": info.get("from")
        })
    except ImportError:
        channels.append({"name": "email", "available": False, "error": "not installed"})

    # Check telegram
    try:
        from channels import channel_telegram
        channels.append({
            "name": "telegram",
            "available": True,
            "note": "Client-side via URL scheme"
        })
    except ImportError:
        channels.append({"name": "telegram", "available": False, "error": "not installed"})

    return {"channels": channels}


# ----- Test Dashboard -----

@app.get("/vd-cut/test/", response_class=HTMLResponse)
async def test_dashboard():
    """
    Serve the VD-CUT Test Dashboard.

    Interactive HTML page for testing:
    - Upload video → /vd-cut/intake
    - Create sequence → /joe/render
    - Poll progress → /vd-cut/job/{id}
    - Preview + Download
    - Seal (I9) → /vd-cut/seal
    """
    dashboard_path = BASE_DIR / "test_dashboard.html"
    if not dashboard_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard not found")

    return HTMLResponse(content=dashboard_path.read_text(), status_code=200)


# ----- Run Server -----

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="info")
