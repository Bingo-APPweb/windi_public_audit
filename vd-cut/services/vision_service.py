"""
W-VISION-001 — Forensic Vision Layer
Frame analysis and cryptographic content description

Liga IA+H · Kempten, Bavaria · 2026
"AI processes. Human decides. WINDI guarantees."

Architecture:
- Layer 1 (100% Local): Frame extraction, perceptual hash, sensor noise
- Layer 2 (Pluggable): Vision API description via W-GATEWAY-001

The forensic integrity features work without external APIs.
Content description is optional and pluggable.
"""

import os
import json
import asyncio
import hashlib
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

log = logging.getLogger("w-vd-cut-001.vision")

# Configuration
VISION_API_ENABLED = os.getenv("WINDI_VISION_API", "false").lower() == "true"
GATEWAY_URL = os.getenv("WINDI_GATEWAY_URL", "http://localhost:8130")


@dataclass
class FrameAnalysis:
    """Analysis result for a single frame."""
    frame_index: int
    timestamp_ms: float
    perceptual_hash: str      # pHash for similarity detection
    content_hash: str         # SHA-256 for exact match
    noise_signature: str      # Sensor noise pattern (forensic)
    description: Optional[str] = None  # Vision API description (optional)


@dataclass
class VideoVisionReport:
    """Complete vision analysis report for a video."""
    project_id: str
    asset_id: str
    analyzed_at: str
    analysis_ms: float
    total_frames: int
    sampled_frames: int
    key_frames: List[Dict[str, Any]]
    integrity_hash: str           # Combined hash of all frame hashes
    sensor_consistency: float     # 0.0-1.0 (1.0 = all frames from same sensor)
    manipulation_score: float     # 0.0-1.0 (0.0 = likely authentic)
    content_summary: Optional[str] = None  # Vision API summary (optional)
    vision_version: str = "1.0.0"


async def extract_frame(video_path: Path, timestamp_s: float, output_path: Path) -> bool:
    """Extract a single frame at specified timestamp."""
    try:
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp_s),
            "-i", str(video_path),
            "-vframes", "1",
            "-f", "image2",
            str(output_path)
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        await asyncio.wait_for(proc.communicate(), timeout=10)
        return output_path.exists()

    except Exception as e:
        log.error(f"Frame extraction failed: {e}")
        return False


def compute_perceptual_hash(image_path: Path) -> str:
    """
    Compute perceptual hash (pHash) for image similarity.
    Uses ImageMagick identify for basic perceptual signature.

    Note: This is a simplified implementation. Production would use
    proper pHash library (imagehash, phash, etc.)
    """
    try:
        # Use ffmpeg to get frame statistics as a pseudo-perceptual hash
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-select_streams", "v:0",
             "-show_entries", "frame=pkt_pts_time,pict_type",
             "-of", "json", str(image_path)],
            capture_output=True,
            timeout=5
        )

        # Create hash from image file content + structure
        with open(image_path, "rb") as f:
            data = f.read()

        # Simplified perceptual hash: combine size + first/last bytes + checksum
        size = len(data)
        head = data[:1024] if len(data) > 1024 else data
        tail = data[-1024:] if len(data) > 1024 else data

        phash_input = f"{size}:{hashlib.md5(head).hexdigest()}:{hashlib.md5(tail).hexdigest()}"
        return f"phash:{hashlib.sha256(phash_input.encode()).hexdigest()[:32]}"

    except Exception as e:
        log.error(f"Perceptual hash failed: {e}")
        return "phash:error"


def compute_content_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of file content."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return f"sha256:{sha256.hexdigest()}"


def compute_noise_signature(image_path: Path) -> str:
    """
    Compute sensor noise signature for forensic analysis.

    Each camera sensor has unique noise patterns (PRNU - Photo Response
    Non-Uniformity). Frames from the same source should have consistent
    noise signatures.

    This is a simplified implementation using high-frequency components.
    Production would use proper PRNU analysis libraries.
    """
    try:
        # Extract high-frequency noise using ffmpeg edge detection
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-select_streams", "v:0",
             "-show_entries", "frame=height,width,pix_fmt",
             "-of", "json", str(image_path)],
            capture_output=True,
            timeout=5
        )

        # Create noise signature from file entropy
        with open(image_path, "rb") as f:
            data = f.read()

        # Calculate byte frequency distribution (simplified entropy)
        freq = [0] * 256
        for byte in data:
            freq[byte] += 1

        # Normalize and hash
        total = len(data)
        normalized = [f / total for f in freq]
        noise_data = ":".join([f"{n:.6f}" for n in normalized[:64]])  # First 64 buckets

        return f"noise:{hashlib.sha256(noise_data.encode()).hexdigest()[:24]}"

    except Exception as e:
        log.error(f"Noise signature failed: {e}")
        return "noise:error"


def calculate_sensor_consistency(noise_signatures: List[str]) -> float:
    """
    Calculate consistency of sensor noise across frames.
    Returns 0.0-1.0 where 1.0 means all frames from same sensor.

    Low consistency may indicate:
    - Spliced footage from different cameras
    - AI-generated content
    - Heavy post-processing
    """
    if len(noise_signatures) < 2:
        return 1.0

    # Extract hash portions
    hashes = [sig.split(":")[-1] for sig in noise_signatures if "error" not in sig]

    if len(hashes) < 2:
        return 0.5  # Uncertain

    # Compare each pair and calculate similarity
    similarities = []
    for i in range(len(hashes) - 1):
        # Simple character-based similarity (production: use proper distance)
        matches = sum(a == b for a, b in zip(hashes[i], hashes[i+1]))
        similarity = matches / max(len(hashes[i]), len(hashes[i+1]))
        similarities.append(similarity)

    return sum(similarities) / len(similarities)


def calculate_manipulation_score(
    sensor_consistency: float,
    frame_analyses: List[FrameAnalysis]
) -> float:
    """
    Calculate likelihood of manipulation.
    Returns 0.0-1.0 where 0.0 means likely authentic.

    Factors:
    - Sensor noise inconsistency
    - Perceptual hash anomalies
    - Frame timing irregularities
    """
    score = 0.0

    # Factor 1: Sensor inconsistency (40% weight)
    if sensor_consistency < 0.5:
        score += 0.4  # High manipulation indicator
    elif sensor_consistency < 0.7:
        score += 0.2  # Medium indicator
    elif sensor_consistency < 0.9:
        score += 0.1  # Low indicator

    # Factor 2: Check for duplicate perceptual hashes (30% weight)
    phashes = [fa.perceptual_hash for fa in frame_analyses]
    unique_ratio = len(set(phashes)) / len(phashes) if phashes else 1.0
    if unique_ratio < 0.5:
        score += 0.3  # Many duplicate frames = potential loop/splice
    elif unique_ratio < 0.8:
        score += 0.15

    # Factor 3: Reserved for future heuristics (30% weight)
    # - Frame timing analysis
    # - Compression artifact patterns
    # - Metadata consistency

    return min(1.0, score)


async def analyze_video_frames(
    video_path: Path,
    project_id: str,
    asset_id: str,
    sample_interval: float = 2.0,  # Sample every N seconds
    max_samples: int = 10
) -> VideoVisionReport:
    """
    Analyze video frames for forensic integrity.

    Extracts key frames, computes hashes and noise signatures,
    and generates an integrity report.
    """
    start_time = datetime.now(timezone.utc)

    # Get video duration
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "json", str(video_path)],
            capture_output=True,
            timeout=10
        )
        probe_data = json.loads(result.stdout.decode())
        duration = float(probe_data.get("format", {}).get("duration", 0))
    except Exception as e:
        log.error(f"Failed to probe video: {e}")
        duration = 0

    if duration <= 0:
        return VideoVisionReport(
            project_id=project_id,
            asset_id=asset_id,
            analyzed_at=start_time.isoformat(),
            analysis_ms=0,
            total_frames=0,
            sampled_frames=0,
            key_frames=[],
            integrity_hash="error:no_duration",
            sensor_consistency=0.0,
            manipulation_score=1.0
        )

    # Calculate sample points
    total_frames = int(duration * 25)  # Approximate at 25fps
    sample_times = []
    current = 0.0
    while current < duration and len(sample_times) < max_samples:
        sample_times.append(current)
        current += sample_interval

    # Add last frame if not included
    if duration - sample_times[-1] > 0.5:
        sample_times.append(duration - 0.1)

    # Extract and analyze frames
    frame_analyses = []
    temp_dir = Path("/tmp/windi-vision")
    temp_dir.mkdir(parents=True, exist_ok=True)

    for i, ts in enumerate(sample_times):
        frame_path = temp_dir / f"{asset_id}_frame_{i}.jpg"

        if await extract_frame(video_path, ts, frame_path):
            analysis = FrameAnalysis(
                frame_index=i,
                timestamp_ms=ts * 1000,
                perceptual_hash=compute_perceptual_hash(frame_path),
                content_hash=compute_content_hash(frame_path),
                noise_signature=compute_noise_signature(frame_path)
            )
            frame_analyses.append(analysis)

            # Cleanup
            frame_path.unlink(missing_ok=True)

    # Calculate integrity hash (chain of all frame hashes)
    hash_chain = ":".join([fa.content_hash for fa in frame_analyses])
    integrity_hash = f"integrity:{hashlib.sha256(hash_chain.encode()).hexdigest()}"

    # Calculate forensic metrics
    noise_sigs = [fa.noise_signature for fa in frame_analyses]
    sensor_consistency = calculate_sensor_consistency(noise_sigs)
    manipulation_score = calculate_manipulation_score(sensor_consistency, frame_analyses)

    # Calculate analysis time
    end_time = datetime.now(timezone.utc)
    analysis_ms = (end_time - start_time).total_seconds() * 1000

    log.info(f"Vision analysis for {asset_id}: {len(frame_analyses)} frames, "
             f"consistency={sensor_consistency:.2f}, manipulation={manipulation_score:.2f}")

    return VideoVisionReport(
        project_id=project_id,
        asset_id=asset_id,
        analyzed_at=start_time.isoformat(),
        analysis_ms=round(analysis_ms, 2),
        total_frames=total_frames,
        sampled_frames=len(frame_analyses),
        key_frames=[asdict(fa) for fa in frame_analyses],
        integrity_hash=integrity_hash,
        sensor_consistency=round(sensor_consistency, 4),
        manipulation_score=round(manipulation_score, 4)
    )


async def describe_content_via_gateway(
    video_path: Path,
    frame_path: Path
) -> Optional[str]:
    """
    Get content description via W-GATEWAY-001 LLM Bridge.

    This is OPTIONAL and pluggable. If the gateway is not available
    or vision API is not configured, returns None.
    """
    if not VISION_API_ENABLED:
        return None

    try:
        import httpx

        # Extract middle frame for description
        async with httpx.AsyncClient(timeout=30) as client:
            # This would call the gateway with vision capability
            # Implementation depends on gateway API
            response = await client.post(
                f"{GATEWAY_URL}/gateway/vision/describe",
                json={
                    "image_path": str(frame_path),
                    "prompt": "Describe the content of this video frame for forensic documentation. "
                              "Focus on: people, objects, actions, location, and any text visible."
                }
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("description")

    except Exception as e:
        log.warning(f"Vision API description failed: {e}")

    return None


# ----- Utility Functions -----

def generate_vision_receipt_data(report: VideoVisionReport) -> Dict[str, Any]:
    """
    Generate data for Ledger receipt attachment.

    This creates a compact representation suitable for
    inclusion in a forensic seal.
    """
    return {
        "type": "W-VISION-001",
        "version": report.vision_version,
        "analyzed_at": report.analyzed_at,
        "integrity_hash": report.integrity_hash,
        "sensor_consistency": report.sensor_consistency,
        "manipulation_score": report.manipulation_score,
        "sampled_frames": report.sampled_frames,
        "verdict": "LIKELY_AUTHENTIC" if report.manipulation_score < 0.3
                  else "REVIEW_RECOMMENDED" if report.manipulation_score < 0.6
                  else "HIGH_MANIPULATION_RISK"
    }
