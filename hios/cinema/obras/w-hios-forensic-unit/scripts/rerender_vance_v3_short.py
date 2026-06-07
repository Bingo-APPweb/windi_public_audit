#!/usr/bin/env python3
"""
RE-RENDER VANCE v3 (SHORT PROMPTS)
==================================
Prompts encurtados para evitar INTERNAL.BAD_OUTPUT.CODE01
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
import numpy as np

# === PATHS ===
ANCHOR_PATH = Path("/opt/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/marcus.vance.anchor.canonical.png")
ANCHOR_NPY = Path("/opt/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/marcus.vance.anchor.canonical.npy")
OUTPUT_DIR = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/shots/vance")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

API_BASE = "https://api.dev.runwayml.com/v1"
API_VERSION = "2024-11-06"

# === SHORT PROMPTS ===
RERENDER_SHOTS = [
    {
        "id": "S06-01_v3",
        "threshold": 0.65,
        "prompt": "50s man with grey ponytail, short beard, dark coat. Standing still as soft light reveals face. Camera locked on face. Light moves slowly from rim to frontal. Face always visible. Cinematic 4K."
    },
    {
        "id": "S11-01_v3",
        "threshold": 0.70,
        "prompt": "50s man with grey ponytail, short beard, dark coat. Entering rooftop terrace, medium close-up. Overcast daylight, diffused soft light. No harsh shadows on face. Face 80% visible. Cinematic 4K."
    },
    {
        "id": "S14-01_v3",
        "threshold": 0.75,
        "prompt": "50s man with grey ponytail, short beard, dark coat. Standing at window, profile view. Generic city skyline at dusk, strong soft focus. No landmarks visible. Golden hour light on face. Cinematic 4K."
    }
]

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")
    sys.stdout.flush()

def load_api_key():
    env_file = Path("/opt/windi/.env")
    for line in env_file.read_text().splitlines():
        if line.startswith("RUNWAY_API_KEY="):
            return line.strip().split("=", 1)[1]
    return None

def load_anchor_base64():
    with open(ANCHOR_PATH, "rb") as f:
        return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"

def submit_job(api_key: str, shot: dict, image_data: str) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Runway-Version": API_VERSION,
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gen4_turbo",
        "promptImage": image_data,
        "promptText": shot["prompt"],
        "duration": 5,
        "ratio": "1280:720"
    }

    log(f"  Prompt length: {len(shot['prompt'])} chars")

    resp = requests.post(f"{API_BASE}/image_to_video", headers=headers, json=payload, timeout=60)
    if resp.status_code in [200, 201]:
        return resp.json().get("id")
    log(f"  ERROR: HTTP {resp.status_code} - {resp.text[:200]}")
    return None

def poll_job(api_key: str, task_id: str, max_wait: int = 300) -> dict:
    headers = {"Authorization": f"Bearer {api_key}", "X-Runway-Version": API_VERSION}
    start = time.time()

    while time.time() - start < max_wait:
        resp = requests.get(f"{API_BASE}/tasks/{task_id}", headers=headers, timeout=30)
        result = resp.json()
        status = result.get("status", "unknown")

        if status == "SUCCEEDED":
            return result
        elif status == "FAILED":
            log(f"  FAILED: {result.get('failure')} ({result.get('failureCode')})")
            return None

        elapsed = int(time.time() - start)
        log(f"  Status: {status} ({elapsed}s)")
        time.sleep(10)

    return None

def download_video(result: dict, shot_id: str) -> Path:
    outputs = result.get("output", [])
    if not outputs:
        return None

    video_url = outputs[0]
    output_path = OUTPUT_DIR / f"{shot_id}.mp4"

    resp = requests.get(video_url, timeout=120)
    if resp.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(resp.content)
        return output_path
    return None

def extract_frames(video_path: Path, shot_id: str) -> list:
    frames_dir = OUTPUT_DIR / f"{shot_id}_frames"
    frames_dir.mkdir(exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", "fps=1", "-frames:v", "5",
        str(frames_dir / "frame_%02d.png")
    ], capture_output=True)
    return sorted(frames_dir.glob("frame_*.png"))

def measure_frames(frames: list, anchor_embed, app) -> float:
    import cv2
    sims = []
    for frame_path in frames:
        img = cv2.imread(str(frame_path))
        faces = app.get(img)
        if faces:
            face = max(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]))
            sim = float(np.dot(anchor_embed.flatten(), face.embedding) / (
                np.linalg.norm(anchor_embed) * np.linalg.norm(face.embedding)
            ))
            sims.append(sim)
            log(f"    {frame_path.name}: {sim:.4f}")
    return sum(sims) / len(sims) if sims else 0

def main():
    log("=" * 60)
    log("RE-RENDER VANCE v3 (SHORT PROMPTS)")
    log("=" * 60)

    api_key = load_api_key()
    if not api_key:
        log("FATAL: No API key")
        return

    image_data = load_anchor_base64()
    log(f"Anchor loaded ({len(image_data)} chars)")

    # Load ArcFace
    sys.path.insert(0, '/opt/windi/venv-poe/lib/python3.11/site-packages')
    import cv2
    from insightface.app import FaceAnalysis
    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))
    anchor_embed = np.load(ANCHOR_NPY)
    log("ArcFace loaded")

    results = []
    run_id = datetime.now().strftime("%Y%m%d%H%M%S")

    for i, shot in enumerate(RERENDER_SHOTS):
        log(f"\n[{i+1}/3] {shot['id']} (threshold ≥{shot['threshold']})")

        task_id = submit_job(api_key, shot, image_data)
        if not task_id:
            results.append({"shot": shot["id"], "status": "SUBMIT_FAILED"})
            continue

        log(f"  Task: {task_id}")
        result = poll_job(api_key, task_id)
        if not result:
            results.append({"shot": shot["id"], "status": "GENERATION_FAILED"})
            continue

        video_path = download_video(result, shot["id"])
        if not video_path:
            results.append({"shot": shot["id"], "status": "DOWNLOAD_FAILED"})
            continue

        log(f"  Downloaded: {video_path.name}")
        frames = extract_frames(video_path, shot["id"])
        log(f"  Frames: {len(frames)}")

        avg_sim = measure_frames(frames, anchor_embed, app)
        passed = avg_sim >= shot["threshold"]
        emoji = "✅" if passed else "❌"
        log(f"  {emoji} avg={avg_sim:.4f} vs ≥{shot['threshold']} → {'PASS' if passed else 'FAIL'}")

        results.append({
            "shot": shot["id"],
            "avg_similarity": round(avg_sim, 4),
            "threshold": shot["threshold"],
            "passed": passed
        })

        time.sleep(2)

    log("\n" + "=" * 60)
    log("FINAL REPORT")
    log("=" * 60)
    for r in results:
        if "avg_similarity" in r:
            emoji = "✅" if r["passed"] else "❌"
            log(f"{emoji} {r['shot']}: {r['avg_similarity']} vs ≥{r['threshold']}")
        else:
            log(f"❌ {r['shot']}: {r['status']}")

    # Save
    manifest_path = OUTPUT_DIR / f"VANCE_V3_SHORT_{run_id}.json"
    with open(manifest_path, "w") as f:
        json.dump({"run_id": run_id, "results": results}, f, indent=2)
    log(f"\nManifest: {manifest_path}")

if __name__ == "__main__":
    main()
