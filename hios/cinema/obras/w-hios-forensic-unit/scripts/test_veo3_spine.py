#!/usr/bin/env python3
"""
TEST-SPINE-003 — Veo 3.1 × SPINE Identity Preservation Test
============================================================
Same protocol as TEST-SPINE-002 (Runway), but using Google Veo 3.1.

Usage:
    python3 test_veo3_spine.py

Liga IA+H · WINDI Publishing House · 05 Jun 2026
"""

import os
import sys
import json
import time
import base64
import subprocess
from pathlib import Path
from datetime import datetime

# =============================================================================
# Configuration
# =============================================================================

ANCHOR_IMAGE = Path("/opt/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/marcus.vance.anchor.v1.png")
ANCHOR_NPY = Path("/opt/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/marcus.vance.anchor.v1.embedding.npy")
OUTPUT_DIR = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/shots/veo3_test")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_api_key():
    env_file = Path("/opt/windi/.env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("VEO_API_KEY="):
                return line.strip().split("=", 1)[1]
    return os.environ.get("VEO_API_KEY")

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")
    sys.stdout.flush()

def test_veo3_api():
    """Test Veo 3 API with Vance anchor."""

    log("=" * 70)
    log("TEST-SPINE-003 — Veo 3.1 × SPINE Identity Preservation")
    log("=" * 70)

    api_key = load_api_key()
    if not api_key:
        log("FATAL: VEO_API_KEY not found in .env")
        return None

    log(f"API Key: {api_key[:20]}...{api_key[-8:]}")

    if not ANCHOR_IMAGE.exists():
        log(f"FATAL: Anchor not found: {ANCHOR_IMAGE}")
        return None

    # Install google-genai if needed
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        log("Installing google-genai...")
        subprocess.run([sys.executable, "-m", "pip", "install", "google-genai", "-q"])
        from google import genai
        from google.genai import types

    # Configure client
    log("Configuring Veo 3.1 client...")
    client = genai.Client(api_key=api_key)

    # Load anchor image
    log(f"Loading anchor: {ANCHOR_IMAGE.name}")
    with open(ANCHOR_IMAGE, "rb") as f:
        image_bytes = f.read()

    # Create image object for Veo (using correct format)
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')
    image_obj = types.Image(
        image_bytes=image_bytes,
        mime_type="image/png"
    )

    # Prompt for video generation
    prompt = """Middle-aged man with grey slicked-back hair, clean-shaven, dark suit.
Standing in office environment, subtle head turn, professional demeanor.
Cinematic lighting, 4K quality, minimal movement."""

    log(f"Prompt: {prompt[:60]}...")
    log("Submitting to Veo 3.1...")

    try:
        # Generate video from image
        operation = client.models.generate_videos(
            model="veo-3.1-generate-preview",
            prompt=prompt,
            image=image_obj,
        )

        log(f"Operation started: {operation.name if hasattr(operation, 'name') else 'unknown'}")

        # Poll for completion
        log("Waiting for completion (max 10 min)...")
        start_time = time.time()
        max_wait = 600  # 10 minutes

        while not operation.done:
            elapsed = int(time.time() - start_time)
            if elapsed > max_wait:
                log(f"TIMEOUT after {elapsed}s")
                return None

            log(f"  [{elapsed:3d}s] Processing...")
            time.sleep(10)
            operation = client.operations.get(operation)

        elapsed = int(time.time() - start_time)
        log(f"Completed in {elapsed}s")

        # Download video
        if hasattr(operation, 'response') and operation.response.generated_videos:
            video = operation.response.generated_videos[0]
            output_path = OUTPUT_DIR / f"veo3_vance_test_{datetime.now().strftime('%H%M%S')}.mp4"

            log(f"Downloading to {output_path}...")
            client.files.download(file=video.video)
            video.video.save(str(output_path))

            log(f"Saved: {output_path.name}")
            return output_path
        else:
            log("ERROR: No video in response")
            log(f"Response: {operation}")
            return None

    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

def extract_frames(video_path: Path) -> list:
    """Extract frames for ArcFace analysis."""
    frames_dir = OUTPUT_DIR / f"{video_path.stem}_frames"
    frames_dir.mkdir(exist_ok=True)

    log("Extracting frames...")
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", "fps=1", "-frames:v", "5",
        str(frames_dir / "frame_%02d.png")
    ]
    subprocess.run(cmd, capture_output=True)

    frames = sorted(frames_dir.glob("frame_*.png"))
    log(f"Extracted {len(frames)} frames")
    return frames

def run_arcface_validation(frames: list) -> dict:
    """Run ArcFace validation against Vance anchor."""

    log("=" * 50)
    log("ArcFace Identity Analysis")
    log("=" * 50)

    import numpy as np
    import cv2
    sys.path.insert(0, '/opt/windi/venv-poe/lib/python3.11/site-packages')
    from insightface.app import FaceAnalysis

    log("Loading ArcFace model...")
    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))

    anchor = np.load(ANCHOR_NPY)
    log(f"Anchor loaded: {anchor.shape}")

    results = []
    similarities = []

    for frame_path in frames:
        img = cv2.imread(str(frame_path))
        faces = app.get(img)

        if not faces:
            log(f"  {frame_path.name}: No face detected")
            results.append({"file": frame_path.name, "similarity": None, "status": "no_face"})
            continue

        face = max(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]))
        frame_embed = face.embedding
        det_score = float(face.det_score)

        sim = float(np.dot(anchor.flatten(), frame_embed) / (
            np.linalg.norm(anchor) * np.linalg.norm(frame_embed)
        ))

        similarities.append(sim)

        if sim >= 0.75:
            status = "FORENSIC"
            emoji = "✅"
        elif sim >= 0.65:
            status = "OPERATIONAL"
            emoji = "🟢"
        else:
            status = "FAIL"
            emoji = "❌"

        log(f"  {frame_path.name}: {sim:.4f} {emoji} {status}")
        results.append({
            "file": frame_path.name,
            "similarity": round(sim, 4),
            "det_score": round(det_score, 4),
            "status": status
        })

    # Summary
    log("=" * 50)

    if similarities:
        avg = sum(similarities) / len(similarities)
        forensic_passes = sum(1 for s in similarities if s >= 0.75)
        operational_passes = sum(1 for s in similarities if s >= 0.65)

        log(f"\nSUMMARY:")
        log(f"  Average: {avg:.4f}")
        log(f"  Range: [{min(similarities):.4f} - {max(similarities):.4f}]")
        log(f"  Operational (≥0.65): {operational_passes}/{len(similarities)}")
        log(f"  Forensic (≥0.75): {forensic_passes}/{len(similarities)}")

        log("\n" + "=" * 50)
        log("SPINE COMPATIBILITY VERDICT")
        log("=" * 50)

        if avg >= 0.75 and forensic_passes >= len(similarities) * 0.8:
            verdict = "FORENSIC_COMPATIBLE"
            log("🟢 VEO 3.1 × SPINE: FORENSIC COMPATIBLE")
        elif avg >= 0.65 and operational_passes >= len(similarities) * 0.6:
            verdict = "OPERATIONAL_COMPATIBLE"
            log("🟡 VEO 3.1 × SPINE: OPERATIONAL COMPATIBLE")
        else:
            verdict = "INCOMPATIBLE"
            log("🔴 VEO 3.1 × SPINE: INCOMPATIBLE")

        return {
            "frames": results,
            "average": round(avg, 4),
            "min": round(min(similarities), 4),
            "max": round(max(similarities), 4),
            "operational_passes": operational_passes,
            "forensic_passes": forensic_passes,
            "verdict": verdict
        }

    return {"frames": results, "verdict": "NO_FACES"}

def main():
    # Generate video
    video_path = test_veo3_api()

    if not video_path:
        log("Video generation failed")
        return

    # Extract frames
    frames = extract_frames(video_path)

    if not frames:
        log("No frames extracted")
        return

    # Validate with ArcFace
    validation = run_arcface_validation(frames)

    # Save report
    report = {
        "test_id": "TEST-SPINE-003",
        "generator": "veo-3.1-generate-preview",
        "timestamp": datetime.now().isoformat(),
        "anchor": str(ANCHOR_IMAGE),
        "video": str(video_path),
        "validation": validation
    }

    report_path = OUTPUT_DIR / f"VEO3_SPINE_REPORT_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    log(f"\nReport: {report_path}")
    log("=" * 70)
    log("TEST-SPINE-003 Complete")
    log("=" * 70)

if __name__ == "__main__":
    main()
