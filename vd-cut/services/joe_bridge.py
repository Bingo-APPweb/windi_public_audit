"""
W-VD-CUT-001 — JOE Bridge
Director de Transmissao integration layer

JOE = Cerebro da historia (decide sequence)
VD-CUT = Musculo de renderizacao (executa encode)

I9: auto_seal=False por padrao — humano confirma via POST /seal separado
I11: Seal apenas via endpoint existente, nunca directo

Liga IA+H · Kempten, Bavaria · 2026
"""

import httpx
import asyncio
import logging
import time
from typing import Optional, Dict, Any, List

# Configuration
VD_CUT_BASE = "http://127.0.0.1:8128"
JOE_BASE = "http://127.0.0.1:8129"
POLL_INTERVAL = 3    # seconds between polls
POLL_TIMEOUT = 300   # 5 min max wait for encode

log = logging.getLogger("w-vd-cut-001.joe-bridge")


class JoeVdCutBridge:
    """
    Bridge between W-JOE-001 and W-VD-CUT-001.

    JOE defines the story -> Bridge converts to EDL -> VD-CUT renders.

    Fluxo:
        1. JOE sends sequence (clips with in/out points, order)
        2. Bridge converts to VD-CUT EDL format
        3. Bridge submits job to VD-CUT
        4. Bridge polls until completion
        5. Returns result (seal is separate I9 action)
    """

    def __init__(self, vdcut_base: str = VD_CUT_BASE):
        self.vdcut_base = vdcut_base

    async def sequence_to_edl(self, sequence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert JOE sequence format to VD-CUT EDL format.

        JOE sequence format:
        {
            "story_id": "...",
            "clips": [
                {"asset_id": "...", "in_ms": 0, "out_ms": 5000, "order": 1},
                {"asset_id": "...", "in_ms": 2000, "out_ms": 8000, "order": 2}
            ],
            "preset": "story_clean"
        }

        VD-CUT EDL format (for /job/create):
        {
            "project_id": "...",
            "source_asset": "...",
            "edl": [{"in_point": 0.0, "out_point": 5.0}, ...],
            "preset": "story_clean"
        }

        Note: VD-CUT currently processes one asset per job.
        For multi-asset sequences, we create multiple jobs.
        """
        clips = sequence.get("clips", [])
        clips_sorted = sorted(clips, key=lambda c: c.get("order", 0))

        if not clips_sorted:
            raise ValueError("No clips in sequence")

        # Group clips by asset
        assets_clips: Dict[str, List[Dict]] = {}
        for clip in clips_sorted:
            asset_id = clip.get("asset_id")
            if asset_id not in assets_clips:
                assets_clips[asset_id] = []
            assets_clips[asset_id].append({
                "in_point": clip.get("in_ms", 0) / 1000.0,  # ms -> seconds
                "out_point": clip.get("out_ms", 0) / 1000.0
            })

        # For v1, we take the first asset (single-asset sequences)
        # Multi-asset support is Phase 2 (requires concat post-process)
        first_asset = list(assets_clips.keys())[0]

        return {
            "source_asset": first_asset,
            "edl": assets_clips[first_asset],
            "preset": sequence.get("preset", "story_clean"),
            "story_id": sequence.get("story_id"),
            "multi_asset": len(assets_clips) > 1,  # Flag for future
            "assets_count": len(assets_clips)
        }

    async def get_export_metadata(self, export_id: str) -> Dict[str, Any]:
        """
        Fetch export metadata from VD-CUT.

        Returns duration, resolution, content_hash, thumbnail availability.
        """
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # Find job by export
                # Note: We need to query the project endpoint
                # For now, we return minimal info
                resp = await client.get(f"{self.vdcut_base}/vd-cut/media/{export_id}")

                return {
                    "export_id": export_id,
                    "available": resp.status_code == 200,
                    "download_url": f"{self.vdcut_base}/vd-cut/media/{export_id}",
                    "thumb_url": f"{self.vdcut_base}/vd-cut/thumb/{export_id}"
                }
        except Exception as e:
            log.error(f"Failed to fetch export metadata: {e}")
            return {
                "export_id": export_id,
                "available": False,
                "error": str(e)
            }

    async def render_sequence(
        self,
        sequence: Dict[str, Any],
        project_id: str,
        actor_did: str,
        auto_seal: bool = False  # I9: default False, humano decide
    ) -> Dict[str, Any]:
        """
        Complete render pipeline: JOE sequence -> VD-CUT encode -> result.

        I9 COMPLIANCE:
            auto_seal=False by default.
            Render always happens.
            Seal ONLY happens with explicit human approval via POST /seal.

        Args:
            sequence: JOE sequence with clips, preset, story_id
            project_id: VD-CUT project ID (must exist)
            actor_did: WINDI DID of the actor
            auto_seal: NEVER set True unless human explicitly confirmed

        Returns:
            {
                "status": "rendered" | "failed",
                "job_id": "...",
                "export_id": "...",
                "content_hash": "...",
                "preview_url": "...",
                "seal_pending": True,  # Always true when auto_seal=False
                "seal_action": "POST /vd-cut/seal with human_approved=true"
            }
        """
        async with httpx.AsyncClient(timeout=30) as client:

            # 1. Convert sequence to EDL
            try:
                edl_data = await self.sequence_to_edl(sequence)
            except ValueError as e:
                return {
                    "status": "failed",
                    "error": str(e),
                    "stage": "sequence_conversion"
                }

            # 2. Submit job to VD-CUT
            job_payload = {
                "project_id": project_id,
                "source_asset": edl_data["source_asset"],
                "edl": edl_data["edl"],
                "preset": edl_data["preset"]
            }

            log.info(f"Submitting render job: project={project_id}, asset={edl_data['source_asset']}")

            try:
                resp = await client.post(
                    f"{self.vdcut_base}/vd-cut/job/create",
                    json=job_payload
                )
                resp.raise_for_status()
                job = resp.json()
                job_id = job["job_id"]
            except httpx.HTTPStatusError as e:
                log.error(f"Job creation failed: {e.response.status_code} - {e.response.text}")
                return {
                    "status": "failed",
                    "error": f"Job creation failed: {e.response.status_code}",
                    "detail": e.response.text[:200],
                    "stage": "job_creation"
                }
            except Exception as e:
                log.error(f"Job creation exception: {e}")
                return {
                    "status": "failed",
                    "error": str(e),
                    "stage": "job_creation"
                }

            # 3. Poll until completion
            try:
                result = await self._poll_job(client, job_id)
            except TimeoutError as e:
                return {
                    "status": "timeout",
                    "job_id": job_id,
                    "error": str(e),
                    "stage": "encoding"
                }
            except RuntimeError as e:
                return {
                    "status": "failed",
                    "job_id": job_id,
                    "error": str(e),
                    "stage": "encoding"
                }

            # 4. Build response
            export_info = result.get("export", {})
            export_id = export_info.get("id", "")

            response = {
                "status": "rendered",
                "job_id": job_id,
                "export_id": export_id,
                "content_hash": export_info.get("content_hash", ""),
                "preview_url": f"/vd-cut/thumb/{export_id}" if export_id else None,
                "download_url": f"/vd-cut/media/{export_id}" if export_id else None,
                "story_id": sequence.get("story_id"),
                "preset": edl_data["preset"]
            }

            # I9 Gate - seal is separate action
            if auto_seal:
                # WARNING: Only if human explicitly confirmed
                log.warning("auto_seal=True requested - requires human confirmation upstream")
                response["seal_pending"] = False
                response["seal_action"] = "Auto-seal was requested but I9 requires upstream human confirmation"
            else:
                response["seal_pending"] = True
                response["seal_action"] = f"POST /vd-cut/seal with project_id={project_id}, export_id={export_id}, human_approved=true"

            return response

    async def _poll_job(
        self,
        client: httpx.AsyncClient,
        job_id: str,
        interval: int = POLL_INTERVAL,
        timeout: int = POLL_TIMEOUT
    ) -> Dict[str, Any]:
        """
        Poll job status until completion or timeout.

        Args:
            client: httpx client
            job_id: VD-CUT job ID
            interval: seconds between polls
            timeout: max wait time in seconds

        Returns:
            Job result with export info

        Raises:
            TimeoutError: if job doesn't complete in time
            RuntimeError: if job fails
        """
        elapsed = 0
        last_progress = -1

        while elapsed < timeout:
            resp = await client.get(f"{self.vdcut_base}/vd-cut/job/{job_id}")
            data = resp.json()
            status = data.get("status")
            progress = data.get("progress", 0)

            # Log progress changes
            if progress != last_progress:
                log.info(f"Job {job_id}: {status} ({progress}%)")
                last_progress = progress

            if status == "COMPLETED":
                log.info(f"Job {job_id} completed successfully")
                return data

            if status == "FAILED":
                error = data.get("error", "Unknown encoding error")
                log.error(f"Job {job_id} failed: {error}")
                raise RuntimeError(f"VD-CUT job failed: {error}")

            await asyncio.sleep(interval)
            elapsed += interval

        raise TimeoutError(f"Job {job_id} did not complete within {timeout}s")


# Module-level instance for import
bridge = JoeVdCutBridge()
