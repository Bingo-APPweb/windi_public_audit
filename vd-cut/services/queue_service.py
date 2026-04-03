"""
W-VD-CUT-001 — Job Queue Service
Manages encoding job queue with limits

Limits:
- Max 1 concurrent job
- Max 1 queued job per user
- Retry up to 2 times on failure

Liga IA+H · Kempten, Bavaria · 2026
"""

import asyncio
import sqlite3
import logging
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger("w-vd-cut-001.queue")

# Configuration
MAX_CONCURRENT_JOBS = 1
MAX_QUEUED_PER_USER = 1
MAX_RETRIES = 2

# Paths
DB_PATH = Path("/opt/windi/vd-cut/vd_cut.db")
MEDIA_DIR = Path("/opt/windi/media/vd-cut")
INCOMING_DIR = MEDIA_DIR / "incoming"
PROCESSING_DIR = MEDIA_DIR / "processing"
EXPORTS_DIR = MEDIA_DIR / "exports"
THUMBS_DIR = MEDIA_DIR / "thumbs"

# Lock for job processing
_processing_lock = asyncio.Lock()


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def can_queue_job(wallet_id: str) -> bool:
    """
    Check if user can queue a new job.
    Returns False if:
    - User already has MAX_QUEUED_PER_USER jobs queued
    - System has MAX_CONCURRENT_JOBS active jobs
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Check user's queued jobs
        cursor.execute("""
            SELECT COUNT(*) FROM video_jobs j
            JOIN video_projects p ON j.project_id = p.id
            WHERE p.wallet_id = ? AND j.status = 'QUEUED'
        """, (wallet_id,))
        user_queued = cursor.fetchone()[0]

        # Check system active jobs
        cursor.execute("SELECT COUNT(*) FROM video_jobs WHERE status = 'ACTIVE'")
        active_jobs = cursor.fetchone()[0]

        conn.close()

        if user_queued >= MAX_QUEUED_PER_USER:
            log.warning(f"Queue limit reached for {wallet_id}: {user_queued} queued")
            return False

        return True

    except Exception as e:
        log.error(f"Queue check error: {e}")
        return False


def get_next_queued_job() -> Optional[dict]:
    """Get next queued job in FIFO order."""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT j.*, a.stored_path as input_path, p.wallet_id
            FROM video_jobs j
            JOIN video_assets a ON j.asset_id = a.id
            JOIN video_projects p ON j.project_id = p.id
            WHERE j.status = 'QUEUED'
            ORDER BY j.created_at ASC
            LIMIT 1
        """)

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    except Exception as e:
        log.error(f"Get next job error: {e}")
        return None


def count_active_jobs() -> int:
    """Count currently active jobs."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM video_jobs WHERE status = 'ACTIVE'")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0


def update_job_status(
    job_id: str,
    status: str,
    progress: int = None,
    error_message: str = None
):
    """Update job status in database."""
    try:
        conn = get_db()
        cursor = conn.cursor()

        updates = ["status = ?"]
        params = [status]

        if progress is not None:
            updates.append("progress_percent = ?")
            params.append(progress)

        if error_message:
            updates.append("error_message = ?")
            params.append(error_message)

        if status == "ACTIVE":
            updates.append("started_at = ?")
            params.append(datetime.now(timezone.utc).isoformat())

        if status in ("COMPLETED", "FAILED"):
            updates.append("completed_at = ?")
            params.append(datetime.now(timezone.utc).isoformat())

        params.append(job_id)

        cursor.execute(f"""
            UPDATE video_jobs SET {', '.join(updates)} WHERE id = ?
        """, params)

        conn.commit()
        conn.close()

    except Exception as e:
        log.error(f"Update job status error: {e}")


def create_export_record(
    job_id: str,
    project_id: str,
    output_path: str,
    thumbnail_path: str,
    file_size: int,
    duration: float,
    width: int,
    height: int,
    content_hash: str
) -> str:
    """Create export record in database."""
    import uuid

    export_id = f"EXPORT-{uuid.uuid4().hex[:12].upper()}"

    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO video_exports
            (id, job_id, project_id, output_path, thumbnail_path,
             file_size, duration_seconds, width, height, content_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            export_id, job_id, project_id, output_path, thumbnail_path,
            file_size, duration, width, height, content_hash
        ))

        conn.commit()
        conn.close()

        return export_id

    except Exception as e:
        log.error(f"Create export error: {e}")
        return None


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return f"sha256:{sha256.hexdigest()}"


async def process_job(job_id: str):
    """
    Process a single encoding job.
    Called as background task from /job/create endpoint.
    """
    from services.ffmpeg_service import encode_video, generate_thumbnail

    async with _processing_lock:
        # Check if we can process (limit concurrent jobs)
        if count_active_jobs() >= MAX_CONCURRENT_JOBS:
            log.info(f"Job {job_id} waiting: max concurrent jobs reached")
            # Will be picked up by next available slot
            return

        # Get job details
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT j.*, a.stored_path as input_path, p.wallet_id, p.title
            FROM video_jobs j
            JOIN video_assets a ON j.asset_id = a.id
            JOIN video_projects p ON j.project_id = p.id
            WHERE j.id = ?
        """, (job_id,))

        job = cursor.fetchone()
        conn.close()

        if not job:
            log.error(f"Job not found: {job_id}")
            return

        if job["status"] != "QUEUED":
            log.info(f"Job {job_id} not queued (status={job['status']}), skipping")
            return

        # Mark as active
        update_job_status(job_id, "ACTIVE", progress=0)

        log.info(f"Processing job {job_id} for project {job['project_id']}")

        try:
            # Parse EDL
            edl = json.loads(job["edl_json"])

            # Prepare paths
            input_path = Path(job["input_path"])
            output_filename = f"{job['project_id']}_{job_id}.mp4"
            output_path = EXPORTS_DIR / output_filename
            thumb_path = THUMBS_DIR / f"{job_id}_thumb.jpg"

            # Progress callback
            async def on_progress(percent: int):
                update_job_status(job_id, "ACTIVE", progress=percent)

            # Encode video
            encode_result = await encode_video(
                input_path=input_path,
                output_path=output_path,
                edl=edl,
                preset_name=job["preset"],
                progress_callback=on_progress
            )

            if encode_result.get("error"):
                # Check retry count
                retry_count = job["retry_count"] or 0
                if retry_count < MAX_RETRIES:
                    # Retry
                    conn = get_db()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE video_jobs
                        SET status = 'QUEUED', retry_count = ?
                        WHERE id = ?
                    """, (retry_count + 1, job_id))
                    conn.commit()
                    conn.close()

                    log.warning(f"Job {job_id} failed, retrying ({retry_count + 1}/{MAX_RETRIES})")
                    return

                # Max retries reached
                update_job_status(
                    job_id, "FAILED",
                    progress=0,
                    error_message=encode_result.get("message", "Unknown error")
                )
                log.error(f"Job {job_id} failed after {MAX_RETRIES} retries")
                return

            # Generate thumbnail
            thumb_result = await generate_thumbnail(
                video_path=output_path,
                output_path=thumb_path,
                timestamp=1.0
            )

            thumbnail_path = str(thumb_path) if thumb_result.get("success") else None

            # Compute content hash for export
            content_hash = compute_file_hash(output_path)

            # Create export record
            export_id = create_export_record(
                job_id=job_id,
                project_id=job["project_id"],
                output_path=str(output_path),
                thumbnail_path=thumbnail_path,
                file_size=encode_result["file_size"],
                duration=encode_result["duration"],
                width=encode_result["width"],
                height=encode_result["height"],
                content_hash=content_hash
            )

            # Update project status
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE video_projects
                SET status = 'COMPLETED', updated_at = ?
                WHERE id = ?
            """, (datetime.now(timezone.utc).isoformat(), job["project_id"]))
            conn.commit()
            conn.close()

            # Mark job complete
            update_job_status(job_id, "COMPLETED", progress=100)

            log.info(f"Job {job_id} completed: export={export_id}")

        except Exception as e:
            log.error(f"Job {job_id} error: {e}")
            update_job_status(
                job_id, "FAILED",
                error_message=str(e)
            )


async def process_queue():
    """
    Process pending jobs in queue.
    Called periodically or when capacity becomes available.
    """
    while True:
        if count_active_jobs() >= MAX_CONCURRENT_JOBS:
            await asyncio.sleep(5)
            continue

        job = get_next_queued_job()
        if not job:
            await asyncio.sleep(5)
            continue

        await process_job(job["id"])
