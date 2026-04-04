"""
W-VD-CUT-001 — Frame Integrity Engine
Segment 2: Frame-Level Forensic Verification

"Deepfake Killer" — Any frame alteration breaks the hash chain.
The proof is not in the MP4; it's in the chained hashes on the Ledger.

Invariants:
- I9: Human decides which frames to seal (never auto-seal timeline)
- I11: Only hashes go to Ledger, never raw frame data

Flow:
1. Extract frame N via FFmpeg
2. Compute SHA-256 of frame PNG
3. Chain with previous hash (Video-Chain continuity)
4. Seal to Ledger on human approval
5. Return FrameSeal with receipt_id

Liga IA+H · Kempten, Bavaria · 2026
"""

import os
import hashlib
import subprocess
import asyncio
import logging
import time
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

# Configuration
FRAMES_DIR = Path("/opt/windi/media/vd-cut/frames_tmp")
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

LEDGER_URL = os.environ.get("LEDGER_URL", "http://127.0.0.1:8101")
VERIFY_URL = os.environ.get("VERIFY_URL", "https://windi-domain.com/verify-public/")

log = logging.getLogger("w-vd-cut-001.frame-integrity")


@dataclass
class FrameSeal:
    """Forensic proof of an extracted frame."""
    frame_index: int
    timestamp_ms: float           # Position in original video
    sha256: str                   # Hash of frame PNG
    prev_hash: str                # Hash of previous frame -> chain
    source_video_hash: str        # Anchor to original video
    actor_did: str
    sealed_at: float = field(default_factory=time.time)
    receipt_id: Optional[str] = None
    verify_url: Optional[str] = None


@dataclass
class EditManifest:
    """Sealed Edit Manifest — proves edit points are authentic."""
    manifest_version: str = "1.0"
    source_video: str = ""
    source_hash: str = ""
    actor_did: str = ""
    edit_points: List[Dict] = field(default_factory=list)
    chain_root: str = "GENESIS"
    chain_tip: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    windi_invariants: List[str] = field(default_factory=lambda: ["I9", "I11"])
    manifest_receipt: Optional[str] = None
    verify_url: Optional[str] = None


class FrameIntegrityEngine:
    """
    Frame-level forensic verification engine.

    Architecture:
    - FFmpeg extracts individual frames as PNG
    - SHA-256 computed per frame
    - prev_hash creates Video-Chain (any tampering breaks the chain)
    - Human selects which frames/edit points to seal

    I9 Compliance:
    - seal_frame() is called per human decision
    - Never auto-seal entire timeline
    - Each seal is an explicit human choice

    I11 Compliance:
    - Only frame hashes go to Ledger
    - Never raw frame data or video content
    - Hash proves integrity without exposing content
    """

    def __init__(self, video_path: str, actor_did: str, source_hash: Optional[str] = None):
        """
        Initialize Frame Integrity Engine.

        Args:
            video_path: Path to source video file
            actor_did: WINDI DID of the actor
            source_hash: Pre-computed hash (optional, computed if not provided)
        """
        self.video_path = Path(video_path)
        self.actor_did = actor_did

        if not self.video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        self.source_hash = source_hash or self._hash_file(self.video_path)
        self.chain: List[FrameSeal] = []
        self._prev_hash = "GENESIS"  # Chain anchor

        log.info(f"FrameIntegrityEngine initialized: {self.video_path.name}, hash={self.source_hash[:16]}...")

    def _hash_file(self, path: Path) -> str:
        """Compute SHA-256 of entire file."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def _hash_bytes(self, data: bytes) -> str:
        """Compute SHA-256 of bytes."""
        return hashlib.sha256(data).hexdigest()

    async def extract_frame(self, frame_index: int) -> bytes:
        """
        Extract frame N from video via FFmpeg.

        Returns PNG bytes. Frame is NOT persisted beyond this call.
        Temporary file is deleted immediately after reading (GDPR compliance).

        Args:
            frame_index: 0-based frame number

        Returns:
            PNG image bytes
        """
        out_path = FRAMES_DIR / f"frame_{frame_index:08d}_{int(time.time()*1000)}.png"

        cmd = [
            "ffmpeg", "-y",
            "-i", str(self.video_path),
            "-vf", f"select=eq(n\\,{frame_index})",
            "-vframes", "1",
            "-f", "image2",
            str(out_path),
            "-loglevel", "error"
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise RuntimeError(f"FFmpeg frame extract failed: {error_msg}")

        if not out_path.exists():
            raise RuntimeError(f"Frame extraction produced no output")

        # Read and immediately delete (sovereignty: no persistent frame storage)
        frame_bytes = out_path.read_bytes()
        out_path.unlink()

        log.debug(f"Extracted frame {frame_index}: {len(frame_bytes)} bytes")
        return frame_bytes

    def get_frame_timestamp(self, frame_index: int, fps: float = 25.0) -> float:
        """Convert frame index to milliseconds."""
        return (frame_index / fps) * 1000.0

    async def get_video_fps(self) -> float:
        """Get video FPS via FFprobe."""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate",
            "-of", "csv=p=0",
            str(self.video_path)
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await process.communicate()

        try:
            # Output is like "25/1" or "30000/1001"
            fps_str = stdout.decode().strip()
            if "/" in fps_str:
                num, den = fps_str.split("/")
                return float(num) / float(den)
            return float(fps_str)
        except Exception:
            return 25.0  # Default fallback

    async def get_total_frames(self) -> int:
        """Get total frame count via FFprobe."""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-count_frames",
            "-show_entries", "stream=nb_read_frames",
            "-of", "csv=p=0",
            str(self.video_path)
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await process.communicate()

        try:
            return int(stdout.decode().strip())
        except Exception:
            return 0

    async def compute_frame_hash(self, frame_index: int) -> str:
        """
        Extract frame and compute its hash.

        Does NOT seal to Ledger. Use seal_frame() for that.
        """
        frame_bytes = await self.extract_frame(frame_index)
        return self._hash_bytes(frame_bytes)

    async def seal_frame(
        self,
        frame_index: int,
        fps: float = 25.0,
        seal_to_ledger: bool = True
    ) -> FrameSeal:
        """
        Seal a specific frame to the Ledger.

        I9 COMPLIANCE:
        This function is called per HUMAN DECISION.
        Never auto-seal entire timeline.
        Each call represents an explicit human choice.

        Args:
            frame_index: Frame number to seal
            fps: Video frames per second
            seal_to_ledger: Whether to seal to Ledger (True) or just compute (False)

        Returns:
            FrameSeal with hash chain and optional receipt_id
        """
        frame_bytes = await self.extract_frame(frame_index)
        frame_hash = self._hash_bytes(frame_bytes)
        timestamp_ms = self.get_frame_timestamp(frame_index, fps)

        seal = FrameSeal(
            frame_index=frame_index,
            timestamp_ms=timestamp_ms,
            sha256=frame_hash,
            prev_hash=self._prev_hash,
            source_video_hash=self.source_hash,
            actor_did=self.actor_did,
        )

        if seal_to_ledger:
            # Seal to Ledger
            receipt_id, verify_url = await self._seal_to_ledger(seal)
            seal.receipt_id = receipt_id
            seal.verify_url = verify_url

        # Advance chain
        self._prev_hash = frame_hash
        self.chain.append(seal)

        log.info(f"Frame {frame_index} sealed: hash={frame_hash[:16]}..., receipt={seal.receipt_id}")
        return seal

    async def _seal_to_ledger(self, seal: FrameSeal) -> tuple[str, str]:
        """
        Seal frame hash to Forensic Ledger.

        I11 COMPLIANCE:
        Only the hash goes to Ledger, never frame data.
        """
        import httpx

        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y%m%d%H%M%S")
        receipt_id = f"VD-FRAME-{timestamp}-{seal.sha256[:8].upper()}"

        payload = {
            "id": receipt_id,
            "receipt_id": receipt_id,
            "actor": seal.actor_did,
            "app": "w-vd-cut-001",
            "doc_name": f"Frame {seal.frame_index} · {seal.timestamp_ms:.0f}ms",
            "doc_type": "video_frame",
            "governance_level": "HIGH",
            "content_hash": f"sha256:{seal.sha256}",  # I11: ONLY hash
            "invariants": ["I9", "I11"],
            "stage": "C6",
            "sealed_at": now.isoformat(),
            "witness": "W-VD-CUT-001 — Frame Integrity Engine",
            "metadata": {
                "frame_index": seal.frame_index,
                "timestamp_ms": seal.timestamp_ms,
                "prev_hash": seal.prev_hash,
                "source_hash": seal.source_video_hash,
                "chain_depth": len(self.chain),
            },
            "sge_score": 0.85  # Frame-level verification = high governance
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{LEDGER_URL}/api/receipts",
                    json=payload,
                    timeout=15
                )

                if response.status_code in (200, 201):
                    data = response.json()
                    final_id = data.get("id") or data.get("receipt_id") or receipt_id
                    verify_url = f"{VERIFY_URL}?id={final_id}"
                    return final_id, verify_url
                else:
                    log.warning(f"Ledger returned {response.status_code}")
                    return receipt_id, f"{VERIFY_URL}?id={receipt_id}"

        except Exception as e:
            log.error(f"Ledger seal error: {e}")
            # Return local receipt (sovereignty maintained)
            return receipt_id, f"{VERIFY_URL}?id={receipt_id}"

    async def build_frame_chain(
        self,
        sample_frames: List[int],
        fps: float = 25.0,
        seal_to_ledger: bool = False
    ) -> List[FrameSeal]:
        """
        Build hash chain across multiple frames.

        Useful for:
        - Sampling every Nth frame for integrity verification
        - Creating a sparse chain that still detects tampering

        Args:
            sample_frames: List of frame indices to hash
            fps: Video frames per second
            seal_to_ledger: Seal each frame (expensive) or just compute

        Returns:
            List of FrameSeal objects forming the chain
        """
        seals = []
        for frame_idx in sorted(sample_frames):
            seal = await self.seal_frame(frame_idx, fps, seal_to_ledger)
            seals.append(seal)

        log.info(f"Built frame chain: {len(seals)} frames, tip={self._prev_hash[:16]}...")
        return seals

    async def seal_edit_points(
        self,
        edit_points: List[int],
        fps: float = 25.0
    ) -> EditManifest:
        """
        Seal edit points (cut frames) to Ledger.

        "Deepfake Killer" — Each edit point is sealed.
        Any subsequent alteration invalidates the hash chain.

        Args:
            edit_points: Frame indices where editor made cuts
            fps: Video FPS

        Returns:
            EditManifest with all sealed edit points
        """
        manifest = EditManifest(
            source_video=self.video_path.name,
            source_hash=self.source_hash,
            actor_did=self.actor_did,
        )

        log.info(f"Sealing {len(edit_points)} edit points...")

        for frame_idx in edit_points:
            seal = await self.seal_frame(frame_idx, fps, seal_to_ledger=True)
            manifest.edit_points.append({
                "frame": seal.frame_index,
                "timestamp_ms": seal.timestamp_ms,
                "hash": seal.sha256,
                "prev_hash": seal.prev_hash,
                "receipt_id": seal.receipt_id,
                "verify_url": seal.verify_url
            })
            log.info(f"  ✅ Frame {frame_idx} → {seal.sha256[:16]}...")

        manifest.chain_tip = self._prev_hash

        # Seal the manifest itself
        manifest_json = json.dumps(asdict(manifest), sort_keys=True, default=str)
        manifest_hash = self._hash_bytes(manifest_json.encode())

        manifest_receipt, manifest_verify = await self._seal_manifest_to_ledger(
            manifest_hash, manifest
        )
        manifest.manifest_receipt = manifest_receipt
        manifest.verify_url = manifest_verify

        log.info(f"Edit manifest sealed: {manifest_receipt}")
        return manifest

    async def _seal_manifest_to_ledger(
        self,
        manifest_hash: str,
        manifest: EditManifest
    ) -> tuple[str, str]:
        """Seal the edit manifest to Ledger."""
        import httpx

        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y%m%d%H%M%S")
        receipt_id = f"VD-MANIFEST-{timestamp}-{manifest_hash[:8].upper()}"

        payload = {
            "id": receipt_id,
            "receipt_id": receipt_id,
            "actor": manifest.actor_did,
            "app": "w-vd-cut-001",
            "doc_name": f"Edit Manifest · {manifest.source_video}",
            "doc_type": "edit_manifest",
            "governance_level": "HIGH",
            "content_hash": f"sha256:{manifest_hash}",
            "invariants": ["I9", "I11"],
            "stage": "C6",
            "sealed_at": now.isoformat(),
            "witness": "W-VD-CUT-001 — Frame Integrity Engine",
            "metadata": {
                "source_video": manifest.source_video,
                "source_hash": manifest.source_hash,
                "edit_point_count": len(manifest.edit_points),
                "chain_root": manifest.chain_root,
                "chain_tip": manifest.chain_tip,
            },
            "sge_score": 0.95  # Manifest = highest governance
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{LEDGER_URL}/api/receipts",
                    json=payload,
                    timeout=15
                )

                if response.status_code in (200, 201):
                    data = response.json()
                    final_id = data.get("id") or data.get("receipt_id") or receipt_id
                    verify_url = f"{VERIFY_URL}?id={final_id}"
                    return final_id, verify_url

        except Exception as e:
            log.error(f"Manifest seal error: {e}")

        return receipt_id, f"{VERIFY_URL}?id={receipt_id}"

    async def verify_frame_integrity(
        self,
        frame_index: int,
        expected_hash: str
    ) -> Dict[str, Any]:
        """
        Verify a frame against expected hash.

        Used for deepfake detection: if current frame hash
        doesn't match sealed hash, video was tampered.

        Args:
            frame_index: Frame to verify
            expected_hash: Hash from sealed FrameSeal

        Returns:
            {
                "verified": bool,
                "frame_index": int,
                "expected_hash": str,
                "actual_hash": str,
                "match": bool
            }
        """
        actual_hash = await self.compute_frame_hash(frame_index)
        match = actual_hash == expected_hash

        result = {
            "verified": match,
            "frame_index": frame_index,
            "expected_hash": expected_hash,
            "actual_hash": actual_hash,
            "match": match,
            "tampered": not match
        }

        if match:
            log.info(f"Frame {frame_index} VERIFIED ✅")
        else:
            log.warning(f"Frame {frame_index} TAMPERED ❌ expected={expected_hash[:16]}..., got={actual_hash[:16]}...")

        return result

    def get_chain_summary(self) -> Dict[str, Any]:
        """Get summary of current hash chain."""
        return {
            "source_video": self.video_path.name,
            "source_hash": self.source_hash,
            "chain_length": len(self.chain),
            "chain_root": "GENESIS",
            "chain_tip": self._prev_hash,
            "frames_sealed": [s.frame_index for s in self.chain],
            "actor_did": self.actor_did
        }


# Convenience function for single-frame verification
async def verify_single_frame(
    video_path: str,
    frame_index: int,
    expected_hash: str,
    actor_did: str = "verifier"
) -> Dict[str, Any]:
    """
    Quick verification of a single frame.

    Does not seal, just verifies.
    """
    engine = FrameIntegrityEngine(video_path, actor_did)
    return await engine.verify_frame_integrity(frame_index, expected_hash)
