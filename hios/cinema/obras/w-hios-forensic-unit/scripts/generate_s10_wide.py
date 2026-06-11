#!/usr/bin/env python3
"""
GENERATE S10-WIDE — Establishing Shot (VISIBILITY)
===================================================
First relation scene of Phase 2.
Couto reports to Alejandro on rooftop penthouse.

Classification: VISIBILITY (not FORENSE)
Gate: Visual HD approval, NOT cosine measurement
Approach: A (silhouettes/backs, no forensic faces)

Principle (sealed 09 Jun 2026):
"WIDE da Fase 2 sem rostos forenses até a Disambiguation Gate estar testada"

The relation lives in the CUT, not in the composition.
- WIDE: geography + body relation
- CLOSE: identity (already sealed)

Liga IA+H: Human Dragon (I9) + Guardian (Witness) + CCode (Architect)
Date: 09 Jun 2026
"""
import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Set API key
os.environ["RUNWAYML_API_SECRET"] = os.getenv(
    "RUNWAY_API_KEY",
    "key_3831dff2c3ffdbda5363f300b320422be856d0acd6f99459baa6ed9c869b125f2dc9a6d25a4e282bb453b7890946cfb685153faa4fb027d60fa50b29616d0d85"
)

from runwayml import RunwayML

# === PATHS ===
OUTPUT_DIR = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/shots/s10-wide")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# === S10-WIDE PROMPT — Approach A (Silhouettes) ===
# Bodies legible, faces NOT legible
# Power dynamic through posture, not facial expression
# LIMIT: 1000 chars
PROMPT = """Wide shot. Luxury corporate penthouse, floor-to-ceiling windows, daylight flooding in. City skyline behind.

Two men in dark suits:
- FOREGROUND: Man in cashmere overcoat seen from BEHIND. Grey hair at back of head. Standing, holding tablet.
- BACKGROUND: Seated figure in leather chair, silhouetted against window. Face in shadow or turned away.

Power dynamic: subordinate standing, superior seated. Corporate thriller.

Camera locked. Noir lighting. Bodies legible, faces NOT visible. Cinematic 4K."""

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def extract_frames(video_path: Path, output_dir: Path, num_frames: int = 5) -> list:
    """Extract frames for visual verification."""
    output_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", "fps=1", "-frames:v", str(num_frames),
        str(output_dir / "frame_%02d.png")
    ], capture_output=True)
    return sorted(output_dir.glob("frame_*.png"))

def main():
    log("=" * 60)
    log("S10-WIDE GENERATION — VISIBILITY SHOT")
    log("Classification: VISIBILITY (not FORENSE)")
    log("Gate: Visual HD approval, NOT cosine measurement")
    log("Approach: A (silhouettes/backs, no forensic faces)")
    log("=" * 60)

    shot_id = f"S10-WIDE_v1"
    video_path = OUTPUT_DIR / f"{shot_id}.mp4"
    frames_dir = OUTPUT_DIR / f"{shot_id}_frames"

    log(f"Generating: {shot_id}")
    log(f"Prompt ({len(PROMPT)} chars):")
    print(PROMPT[:300] + "...")

    client = RunwayML()

    try:
        log("Submitting text-to-video request...")

        # Text-to-video (no first-frame reference)
        task = client.text_to_video.create(
            model="gen4.5",
            prompt_text=PROMPT,
            ratio="1280:720",  # 16:9 landscape
            duration=5
        )

        log(f"Task created: {task.id}")
        log("Waiting for generation...")

        start_time = time.time()
        max_wait = 300  # 5 minutes

        while time.time() - start_time < max_wait:
            task_status = client.tasks.retrieve(task.id)
            status = task_status.status
            elapsed = int(time.time() - start_time)

            log(f"Status: {status} ({elapsed}s elapsed)")

            if status == "SUCCEEDED":
                output_url = task_status.output[0] if task_status.output else None

                if output_url:
                    log(f"Downloading from: {output_url[:50]}...")
                    import requests
                    resp = requests.get(output_url, timeout=60)
                    video_path.write_bytes(resp.content)
                    log(f"Saved: {video_path}")

                    # Extract frames
                    log("Extracting frames for visual verification...")
                    frames = extract_frames(video_path, frames_dir)
                    log(f"Extracted {len(frames)} frames")

                    # Save manifest
                    manifest = {
                        "shot_id": shot_id,
                        "classification": "VISIBILITY",
                        "gate": "VISUAL_HD",
                        "approach": "A (silhouettes/backs)",
                        "prompt": PROMPT,
                        "video_path": str(video_path),
                        "frames_dir": str(frames_dir),
                        "n_frames": len(frames),
                        "task_id": task.id,
                        "timestamp": datetime.now().isoformat(),
                        "note": "NO COSINE MEASUREMENT - Visual HD gate only"
                    }
                    manifest_path = OUTPUT_DIR / f"{shot_id}_manifest.json"
                    with open(manifest_path, "w") as f:
                        json.dump(manifest, f, indent=2)
                    log(f"Manifest: {manifest_path}")

                    log("=" * 60)
                    log("GENERATION COMPLETE")
                    log("")
                    log("NEXT: Visual HD Gate (Human Dragon approval)")
                    log("CRITERIA:")
                    log("  - Bodies legible")
                    log("  - Faces NOT forensic (backs/shadow/profile)")
                    log("  - Power dynamic visible (standing vs seated)")
                    log("  - Geography clear (penthouse, windows, skyline)")
                    log("=" * 60)
                    return 0

            elif status == "FAILED":
                log(f"GENERATION FAILED: {task_status}")
                return 1

            time.sleep(10)

        log("TIMEOUT - generation took too long")
        return 1

    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
