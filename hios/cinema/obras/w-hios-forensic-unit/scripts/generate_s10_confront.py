#!/usr/bin/env python3
"""
GENERATE S10-CONFRONT — Disambiguation Gate Stress Test
========================================================
First multi-face attribution test of SPINE-CAST Phase 2.

Par tested: Alejandro × Couto (0.4498 inter-anchor — tightest pair)
Goal: Prove attribution works when two distinct faces share same frame

Classification: FORENSE (both faces measurable)
Gate: Disambiguation Gate (G-ATT-1)
Doctrine: DOCTRINE-HIOS-ATTESTATION-001

Anti-Movement Medicine applied:
- "Already in frame, does not enter"
- "Camera locked, no orbit, no angle change"
- "Near-frontal, head stays toward lens"
- "He does NOT move"
- "Face always 70%+ visible"

Liga IA+H: Human Dragon (I9) + Guardian (Witness) + CCode (Architect)
Date: 10 Jun 2026
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
OUTPUT_DIR = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/shots/s10-confront")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# === S10-CONFRONT PROMPT — Anti-Movement Medicine ===
# Both faces clearly visible and measurable
# LIMIT: 1000 chars
PROMPT = """Medium shot, corporate boardroom. Two men in dark suits.

LEFT SIDE — ALEJANDRO: 43-year-old European-Latin executive, sharp angular features, dark hair cleanly styled short with gel, piercing dark brown eyes, smooth clean-shaven skin, charcoal grey Italian suit with white shirt. ALREADY SEATED at table, facing camera 3/4 profile. He does NOT move. Face 70%+ visible.

RIGHT SIDE — COUTO: 45-year-old European corporate man, slicked-back grey hair, sharp jawline, clean-shaven, cold dark brown eyes, black cashmere overcoat. ALREADY STANDING behind table, near-frontal to camera. He does NOT move. Face 70%+ visible.

Power dynamic: Alejandro seated (principal), Couto standing (subordinate reporting).

Camera LOCKED. No orbit. No angle change. Professional lighting. Cinematic 4K."""

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def extract_frames(video_path: Path, output_dir: Path, num_frames: int = 5) -> list:
    """Extract frames for measurement."""
    output_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", "fps=1", "-frames:v", str(num_frames),
        str(output_dir / "frame_%02d.png")
    ], capture_output=True)
    return sorted(output_dir.glob("frame_*.png"))

def main():
    log("=" * 70)
    log("S10-CONFRONT GENERATION — DISAMBIGUATION GATE STRESS TEST")
    log("=" * 70)
    log("Classification: FORENSE (both faces measurable)")
    log("Gate: Disambiguation Gate (G-ATT-1)")
    log("Par tested: Alejandro × Couto (0.4498 inter-anchor)")
    log("Doctrine: DOCTRINE-HIOS-ATTESTATION-001")
    log("=" * 70)

    shot_id = f"S10-CONFRONT_v1"
    video_path = OUTPUT_DIR / f"{shot_id}.mp4"
    frames_dir = OUTPUT_DIR / f"{shot_id}_frames"

    log(f"Generating: {shot_id}")
    log(f"Prompt ({len(PROMPT)} chars):")
    print(PROMPT)
    print()

    client = RunwayML()

    try:
        log("Submitting text-to-video request to Runway Gen-4...")

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
                    log("Extracting frames for disambiguation measurement...")
                    frames = extract_frames(video_path, frames_dir)
                    log(f"Extracted {len(frames)} frames")

                    # Save manifest
                    manifest = {
                        "shot_id": shot_id,
                        "classification": "FORENSE",
                        "gate": "DISAMBIGUATION_GATE",
                        "par_tested": "Alejandro × Couto",
                        "inter_anchor_similarity": 0.4498,
                        "prompt": PROMPT,
                        "video_path": str(video_path),
                        "frames_dir": str(frames_dir),
                        "n_frames": len(frames),
                        "task_id": task.id,
                        "timestamp": datetime.now().isoformat(),
                        "doctrine": "DOCTRINE-HIOS-ATTESTATION-001",
                        "anti_movement_medicine": [
                            "Already in frame",
                            "Camera locked",
                            "Near-frontal",
                            "Does NOT move",
                            "Face 70%+ visible"
                        ],
                        "expected_measurement": {
                            "faces": 2,
                            "left_face": {"anchor": "Alejandro", "min_sim": 0.65},
                            "right_face": {"anchor": "Couto", "min_sim": 0.65},
                            "separation_threshold": 0.50
                        }
                    }
                    manifest_path = OUTPUT_DIR / f"{shot_id}_manifest.json"
                    with open(manifest_path, "w") as f:
                        json.dump(manifest, f, indent=2)
                    log(f"Manifest: {manifest_path}")

                    log("=" * 70)
                    log("GENERATION COMPLETE")
                    log("")
                    log("NEXT: Run Disambiguation Gate measurement:")
                    log("")
                    log("  python3 production/disambiguation_gate.py \\")
                    log(f"    --video {video_path} \\")
                    log(f"    --shot-id {shot_id} \\")
                    log("    --anchor-a anchors/alejandro.valenzuela.anchor.v1.embedding.npy \\")
                    log("    --anchor-b anchors/marcus.couto.anchor.v1.embedding.npy \\")
                    log("    --name-a Alejandro --name-b Couto \\")
                    log(f"    --output {OUTPUT_DIR / f'{shot_id}_disambiguation.json'}")
                    log("=" * 70)
                    return 0

            elif status == "FAILED":
                log(f"GENERATION FAILED: {task_status}")
                # Save failure manifest
                failure = {
                    "shot_id": shot_id,
                    "status": "GENERATION_FAILED",
                    "task_id": task.id,
                    "task_status": str(task_status),
                    "timestamp": datetime.now().isoformat()
                }
                with open(OUTPUT_DIR / f"{shot_id}_FAILED.json", "w") as f:
                    json.dump(failure, f, indent=2)
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
