#!/usr/bin/env python3
"""
TEST-SPINE-001 — SORA 2 × SPINE Identity Preservation Test

Guardian Protocol:
  1. Submit Elisa anchor to SORA 2
  2. Generate simple scene (forest, phone, subtle movement)
  3. Extract frames
  4. Run ArcFace comparison against canonical anchor
  5. Measure: Does Elisa remain Elisa?

This test measures SPINE compatibility, not visual beauty.
"""

import os
import sys
import time
import json
import requests
import subprocess
from pathlib import Path
from datetime import datetime

# Paths
ANCHOR_IMAGE = "/opt/windi/hios/cinema/obras/o-peso-do-eco/_forense/obra2-v2/elisa_anchor_v2_1280x720.png"
ANCHOR_EMBED = "/opt/windi/hios/cinema/obras/o-peso-do-eco/anchors/cast_v2/elisa.anchor.v2.CURRENT.npy"
OUTPUT_DIR = Path("/opt/windi/hios/visual/producer/output/test_spine_001")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load API key
env_path = "/opt/windi/hios/.env.openai"
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.startswith("OPENAI_API_KEY="):
                os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip().strip('"')

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
BASE_URL = "https://api.openai.com/v1/videos"


def submit_spine_test():
    """Submit Elisa anchor with simple prompt."""

    print("=" * 70)
    print("TEST-SPINE-001 — SORA 2 × SPINE Identity Preservation")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Anchor: {ANCHOR_IMAGE}")
    print()

    if not Path(ANCHOR_IMAGE).exists():
        print(f"❌ Anchor not found: {ANCHOR_IMAGE}")
        return None

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

    # Guardian's recommended prompt: simple, measurable
    prompt = """Young woman standing in a forest clearing, looking at her mobile phone.
Subtle head movement, soft natural lighting.
She has dark hair, wears casual clothing.
Cinematic composition, shallow depth of field.
Calm, contemplative mood."""

    print("📤 Submitting SPINE test...")
    print(f"   Prompt: {prompt[:60]}...")
    print()

    with open(ANCHOR_IMAGE, "rb") as ref_file:
        files = {
            "model": (None, "sora-2"),
            "prompt": (None, prompt),
            "size": (None, "1280x720"),
            "seconds": (None, "8"),
            "input_reference": (
                Path(ANCHOR_IMAGE).name,
                ref_file,
                "image/png"
            )
        }

        response = requests.post(
            BASE_URL,
            headers=headers,
            files=files,
            timeout=60
        )

    print(f"📥 HTTP Status: {response.status_code}")

    try:
        data = response.json()
        print(json.dumps(data, indent=2))
    except:
        print(f"Raw: {response.text[:500]}")
        return None

    if response.status_code not in [200, 201, 202]:
        print(f"❌ API rejected request")
        return None

    job_id = data.get("id")
    print(f"\n🎫 Job ID: {job_id}")

    return job_id


def poll_completion(job_id: str, max_wait: int = 300):
    """Poll until completion or timeout."""

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    url = f"{BASE_URL}/{job_id}"

    print(f"\n⏳ Polling (max {max_wait}s)...")
    start = time.time()

    while time.time() - start < max_wait:
        response = requests.get(url, headers=headers, timeout=30)
        data = response.json()
        status = data.get("status", "unknown")
        progress = data.get("progress", 0)

        elapsed = int(time.time() - start)
        print(f"   [{elapsed:3d}s] {status} ({progress}%)", end="\r")

        if status in ["succeeded", "completed", "complete"]:
            print(f"\n✅ Completed in {elapsed}s")
            return True

        if status == "failed":
            error = data.get("error", "unknown")
            print(f"\n❌ Failed: {error}")
            return False

        time.sleep(5)

    print(f"\n⏱️ Timeout after {max_wait}s")
    return False


def download_video(job_id: str) -> Path:
    """Download generated video."""

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    url = f"{BASE_URL}/{job_id}/content"

    output_path = OUTPUT_DIR / f"elisa_spine_test_{datetime.now().strftime('%H%M%S')}.mp4"

    print(f"\n📥 Downloading to {output_path}...")
    response = requests.get(url, headers=headers, stream=True, timeout=120)

    if response.status_code != 200:
        print(f"❌ Download failed: {response.status_code}")
        return None

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"✅ Saved: {output_path.name} ({size_mb:.1f} MB)")

    return output_path


def extract_frames(video_path: Path) -> list:
    """Extract frames for ArcFace analysis."""

    frames_dir = OUTPUT_DIR / "frames"
    frames_dir.mkdir(exist_ok=True)

    print(f"\n🎞️ Extracting frames...")

    # Extract 5 frames at different points
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", "fps=1",  # 1 frame per second
        "-frames:v", "5",
        str(frames_dir / "frame_%02d.png")
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    frames = sorted(frames_dir.glob("frame_*.png"))
    print(f"   Extracted {len(frames)} frames")

    return frames


def run_arcface_comparison(frames: list):
    """Compare frames against Elisa anchor using ArcFace."""

    print(f"\n🔬 ArcFace Identity Analysis")
    print("=" * 50)

    # Check if we have the comparison script
    spine_script = Path("/opt/windi/hios/visual/producer/multi_anchor_test.py")

    if not spine_script.exists():
        print("⚠️ SPINE validation script not found")
        print("   Manual validation required")
        print(f"   Anchor: {ANCHOR_IMAGE}")
        print(f"   Frames: {[f.name for f in frames]}")
        return

    # Try to use insightface directly
    try:
        import numpy as np
        from insightface.app import FaceAnalysis

        print("Loading ArcFace model...")
        app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        app.prepare(ctx_id=0, det_size=(640, 640))

        # Load anchor embedding
        anchor_embed = np.load(ANCHOR_EMBED)
        print(f"Anchor embedding shape: {anchor_embed.shape}")

        import cv2

        results = []
        for frame_path in frames:
            img = cv2.imread(str(frame_path))
            faces = app.get(img)

            if not faces:
                print(f"   {frame_path.name}: No face detected")
                continue

            # Get embedding of largest face
            face = max(faces, key=lambda x: x.bbox[2] - x.bbox[0])
            frame_embed = face.embedding

            # Cosine similarity
            similarity = np.dot(anchor_embed.flatten(), frame_embed) / (
                np.linalg.norm(anchor_embed) * np.linalg.norm(frame_embed)
            )

            status = "✅ PASS" if similarity >= 0.65 else "❌ FAIL"
            results.append((frame_path.name, similarity, status))
            print(f"   {frame_path.name}: {similarity:.4f} {status}")

        print()
        print("=" * 50)
        print("SPINE COMPATIBILITY VERDICT")
        print("=" * 50)

        if not results:
            print("❌ No faces detected in any frame")
            return

        avg_sim = sum(r[1] for r in results) / len(results)
        passes = sum(1 for r in results if r[2] == "✅ PASS")

        print(f"Average similarity: {avg_sim:.4f}")
        print(f"Frames passed: {passes}/{len(results)}")
        print()

        if avg_sim >= 0.65 and passes >= len(results) * 0.6:
            print("🟢 SORA 2 × SPINE: COMPATIBLE")
            print("   Elisa identity preserved across frames")
        else:
            print("🟠 SORA 2 × SPINE: DEGRADED")
            print("   Identity drift detected")

    except ImportError:
        print("⚠️ insightface not available")
        print("   Run on Vast.ai for full SPINE validation")
        print(f"   Frames saved to: {OUTPUT_DIR / 'frames'}")


def main():
    # Step 1: Submit
    job_id = submit_spine_test()
    if not job_id:
        return

    # Step 2: Poll
    if not poll_completion(job_id, max_wait=300):
        print("\n⚠️ Job did not complete - check status manually")
        print(f"   Job ID: {job_id}")
        return

    # Step 3: Download
    video_path = download_video(job_id)
    if not video_path:
        return

    # Step 4: Extract frames
    frames = extract_frames(video_path)

    # Step 5: ArcFace validation
    run_arcface_comparison(frames)

    print()
    print("=" * 70)
    print("TEST-SPINE-001 Complete")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
