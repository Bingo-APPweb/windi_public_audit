#!/usr/bin/env python3
"""
TEST-SPINE-002 — Runway Gen-4 × SPINE Identity Preservation Test

Same protocol as TEST-SPINE-001, but using Runway Gen-4 instead of SORA 2.

Usage:
    python3 test_spine_002_runway.py

Liga IA+H · WINDI Publishing House · 01 Jun 2026
"""

import os
import sys
import json
import time
import base64
import subprocess
from pathlib import Path
from datetime import datetime

import requests

# =============================================================================
# Configuration
# =============================================================================

ANCHOR_IMAGE = Path("/opt/windi/hios/cinema/obras/o-peso-do-eco/_forense/obra2-v2/elisa_anchor_v2_1280x720.png")
ANCHOR_EMBED = Path("/opt/windi/hios/cinema/obras/o-peso-do-eco/anchors/cast_v2/elisa.anchor.v2.CURRENT.npy")
OUTPUT_DIR = Path("/opt/windi/hios/visual/producer/output/test_spine_002_runway")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

API_BASE = "https://api.dev.runwayml.com/v1"
API_VERSION = "2024-11-06"

# Load API key
def load_api_key():
    env_file = Path("/opt/windi/.env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.startswith("RUNWAY_API_KEY="):
                    return line.strip().split("=", 1)[1]
    return os.environ.get("RUNWAY_API_KEY")


def load_image_base64(image_path: Path) -> str:
    """Load image and return base64 data URI."""
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{data}"


def submit_runway_job(api_key: str) -> str:
    """Submit Elisa anchor to Runway Gen-4."""

    print("=" * 70)
    print("TEST-SPINE-002 — Runway Gen-4 × SPINE Identity Preservation")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Anchor: {ANCHOR_IMAGE}")
    print()

    if not ANCHOR_IMAGE.exists():
        print(f"❌ Anchor not found: {ANCHOR_IMAGE}")
        return None

    # Same prompt as TEST-SPINE-001
    prompt = """Young woman standing in a forest clearing, looking at her mobile phone.
Subtle head movement, soft natural lighting.
She has dark hair, wears casual clothing.
Cinematic composition, shallow depth of field.
Calm, contemplative mood."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Runway-Version": API_VERSION,
        "Content-Type": "application/json",
    }

    image_data = load_image_base64(ANCHOR_IMAGE)

    payload = {
        "model": "gen4_turbo",
        "promptImage": image_data,
        "promptText": prompt,
        "duration": 5,  # Runway supports 5 or 10 seconds
        "ratio": "1280:720",
    }

    print("📤 Submitting Runway Gen-4 job...")
    print(f"   Model: gen4_turbo")
    print(f"   Duration: 5s")
    print(f"   Prompt: {prompt[:60]}...")
    print()

    url = f"{API_BASE}/image_to_video"

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

    print(f"📥 HTTP Status: {response.status_code}")

    if response.status_code == 401:
        print("❌ Authentication failed - check API key")
        return None

    if response.status_code not in [200, 201]:
        print(f"❌ API Error: {response.text[:500]}")
        return None

    result = response.json()
    task_id = result.get("id")

    print(f"✅ Job submitted: {task_id}")
    print(json.dumps(result, indent=2))

    return task_id


def poll_completion(api_key: str, task_id: str, max_wait: int = 600) -> dict:
    """Poll until completion."""

    url = f"{API_BASE}/tasks/{task_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Runway-Version": API_VERSION,
    }

    print(f"\n⏳ Polling (max {max_wait}s)...")
    start = time.time()

    while time.time() - start < max_wait:
        response = requests.get(url, headers=headers, timeout=30)
        result = response.json()
        status = result.get("status", "unknown")

        elapsed = int(time.time() - start)
        print(f"   [{elapsed:3d}s] {status}", end="\r")

        if status == "SUCCEEDED":
            print(f"\n✅ Completed in {elapsed}s")
            return result

        if status == "FAILED":
            print(f"\n❌ Failed: {result}")
            return None

        time.sleep(5)

    print(f"\n⏱️ Timeout after {max_wait}s")
    return None


def download_video(result: dict) -> Path:
    """Download generated video."""

    output_urls = result.get("output", [])
    if not output_urls:
        print("❌ No output URLs in result")
        return None

    video_url = output_urls[0]
    output_path = OUTPUT_DIR / f"elisa_runway_test_{datetime.now().strftime('%H%M%S')}.mp4"

    print(f"\n📥 Downloading to {output_path}...")

    response = requests.get(video_url, timeout=120)
    if response.status_code != 200:
        print(f"❌ Download failed: {response.status_code}")
        return None

    with open(output_path, "wb") as f:
        f.write(response.content)

    size_mb = len(response.content) / (1024 * 1024)
    print(f"✅ Saved: {output_path.name} ({size_mb:.1f} MB)")

    return output_path


def extract_frames(video_path: Path) -> list:
    """Extract frames for ArcFace analysis."""

    frames_dir = OUTPUT_DIR / "frames"
    frames_dir.mkdir(exist_ok=True)

    print(f"\n🎞️ Extracting frames...")

    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", "fps=1",
        "-frames:v", "5",
        str(frames_dir / "frame_%02d.png")
    ]

    subprocess.run(cmd, capture_output=True)

    frames = sorted(frames_dir.glob("frame_*.png"))
    print(f"   Extracted {len(frames)} frames")

    return frames


def run_arcface_validation(frames: list) -> dict:
    """Run ArcFace validation against Elisa anchor."""

    print(f"\n🔬 ArcFace Identity Analysis")
    print("=" * 50)

    try:
        import numpy as np
        import cv2
        sys.path.insert(0, '/opt/windi/venv-poe/lib/python3.11/site-packages')
        from insightface.app import FaceAnalysis

        print("Loading ArcFace model...")
        app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        app.prepare(ctx_id=0, det_size=(640, 640))

        anchor = np.load(ANCHOR_EMBED)
        print(f"✅ Anchor loaded: {anchor.shape}")

        results = []
        similarities = []

        for frame_path in frames:
            img = cv2.imread(str(frame_path))
            faces = app.get(img)

            if not faces:
                print(f"   {frame_path.name}: ⚠️  No face detected")
                results.append({"file": frame_path.name, "similarity": None, "status": "no_face"})
                continue

            face = max(faces, key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]))
            frame_embed = face.embedding

            sim = float(np.dot(anchor.flatten(), frame_embed) / (
                np.linalg.norm(anchor) * np.linalg.norm(frame_embed)
            ))

            similarities.append(sim)

            if sim >= 0.75:
                status = "✅ FORENSIC"
            elif sim >= 0.65:
                status = "🟢 OPERATIONAL"
            else:
                status = "❌ FAIL"

            print(f"   {frame_path.name}: {sim:.4f} {status}")
            results.append({"file": frame_path.name, "similarity": round(sim, 4), "status": status})

        # Summary
        print("=" * 50)

        if similarities:
            avg = sum(similarities) / len(similarities)
            op_passes = sum(1 for s in similarities if s >= 0.65)
            forensic_passes = sum(1 for s in similarities if s >= 0.75)

            print(f"\n📊 SUMMARY")
            print(f"   Frames analyzed: {len(similarities)}/{len(frames)}")
            print(f"   Average similarity: {avg:.4f}")
            print(f"   Range: [{min(similarities):.4f} - {max(similarities):.4f}]")
            print(f"   Operational passes: {op_passes}/{len(similarities)} ({op_passes/len(similarities)*100:.0f}%)")
            print(f"   Forensic passes: {forensic_passes}/{len(similarities)} ({forensic_passes/len(similarities)*100:.0f}%)")

            print("\n" + "=" * 50)
            print("🎯 SPINE COMPATIBILITY VERDICT")
            print("=" * 50)

            if avg >= 0.75 and forensic_passes >= len(similarities) * 0.8:
                verdict = "FORENSIC_COMPATIBLE"
                print("🟢 RUNWAY × SPINE: FORENSIC COMPATIBLE")
            elif avg >= 0.65 and op_passes >= len(similarities) * 0.6:
                verdict = "OPERATIONAL_COMPATIBLE"
                print("🟡 RUNWAY × SPINE: OPERATIONAL COMPATIBLE")
            else:
                verdict = "INCOMPATIBLE"
                print("🔴 RUNWAY × SPINE: INCOMPATIBLE")

            return {
                "frames": results,
                "average": round(avg, 4),
                "min": round(min(similarities), 4),
                "max": round(max(similarities), 4),
                "operational_passes": op_passes,
                "forensic_passes": forensic_passes,
                "verdict": verdict
            }

        return {"frames": results, "verdict": "NO_FACES"}

    except ImportError as e:
        print(f"⚠️ ArcFace not available: {e}")
        return None


def main():
    api_key = load_api_key()
    if not api_key:
        print("❌ RUNWAY_API_KEY not found")
        return

    print(f"🔑 API Key: {api_key[:20]}...{api_key[-8:]}")

    # Submit job
    task_id = submit_runway_job(api_key)
    if not task_id:
        return

    # Poll completion
    result = poll_completion(api_key, task_id)
    if not result:
        return

    # Download video
    video_path = download_video(result)
    if not video_path:
        return

    # Extract frames
    frames = extract_frames(video_path)

    # ArcFace validation
    validation = run_arcface_validation(frames)

    # Save report
    report = {
        "test_id": "TEST-SPINE-002",
        "generator": "runway-gen4-turbo",
        "timestamp": datetime.now().isoformat(),
        "video": str(video_path),
        "validation": validation
    }

    report_path = OUTPUT_DIR / "SPINE_VALIDATION_REPORT.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Report saved: {report_path}")
    print("=" * 70)
    print("TEST-SPINE-002 Complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
