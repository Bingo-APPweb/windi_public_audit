#!/usr/bin/env python3
"""
RE-RENDER COUTO S10-01 v2 — Fix Cartoon Background
===================================================
Problem: v1 has cartoon background, needs photorealistic.
Solution: Emphasize real corporate environment in prompt.

METHOD-001: No affirmations. Only numbers.

Liga IA+H: Human Dragon (I9) + CCode
Date: 09 Jun 2026
"""

import sys
import json
import time
import base64
import subprocess
from pathlib import Path
from datetime import datetime

import requests
import numpy as np

ANCHOR_PATH = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/marcus.couto.anchor.v1.png")
ANCHOR_NPY = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/marcus.couto.anchor.v1.embedding.npy")
OUTPUT_DIR = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/shots/couto")
PUBLIC_DIR = Path("/opt/windi/static/docs/hios-forensic/couto-shots-v1")

API_BASE = "https://api.dev.runwayml.com/v1"
API_VERSION = "2024-11-06"

# v2 prompt with photorealistic background emphasis
S10_V2_PROMPT = """Medium shot of a man in his mid-40s with slicked-back grey hair, completely clean-shaven, sharp angular jaw, wearing a perfectly tailored dark European suit, white shirt. He holds a corporate tablet in both hands, already positioned. Near-frontal framing, head and body perfectly still. Eyes scan the tablet with methodical precision. Expression: efficient, emotionless corporate facade.

PHOTOREALISTIC ENVIRONMENT: Real modern corporate penthouse office, 42nd floor Frankfurt. Floor-to-ceiling glass windows with REAL Frankfurt skyline visible - actual skyscrapers, Commerzbank Tower, European Central Bank. Harsh natural daylight creating dramatic shadows. Brushed steel and glass furniture. NO cartoon, NO stylized, NO illustration - pure cinematic photorealism.

Camera locked. Cinematic 4K, corporate thriller aesthetic, shallow depth of field on face with real bokeh on city background."""

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")
    sys.stdout.flush()

def load_api_key():
    for line in Path("/opt/windi/.env").read_text().splitlines():
        if line.startswith("RUNWAY_API_KEY="):
            return line.strip().split("=", 1)[1]
    return None

def load_anchor_base64():
    with open(ANCHOR_PATH, "rb") as f:
        return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"

def submit_job(api_key, prompt, image_data):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Runway-Version": API_VERSION,
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gen4_turbo",
        "promptImage": image_data,
        "promptText": prompt,
        "duration": 5,
        "ratio": "1280:720"
    }
    resp = requests.post(f"{API_BASE}/image_to_video", headers=headers, json=payload, timeout=60)
    if resp.status_code in [200, 201]:
        return resp.json().get("id")
    log(f"ERROR: {resp.status_code} - {resp.text[:200]}")
    return None

def poll_job(api_key, task_id, max_wait=300):
    headers = {"Authorization": f"Bearer {api_key}", "X-Runway-Version": API_VERSION}
    start = time.time()
    while time.time() - start < max_wait:
        resp = requests.get(f"{API_BASE}/tasks/{task_id}", headers=headers, timeout=30)
        result = resp.json()
        status = result.get("status", "unknown")
        if status == "SUCCEEDED":
            return result
        elif status == "FAILED":
            log(f"FAILED: {result.get('failureCode')}")
            return None
        log(f"{status} ({int(time.time()-start)}s)")
        time.sleep(10)
    return None

def download_video(result, filename):
    outputs = result.get("output", [])
    if not outputs:
        return None
    output_path = OUTPUT_DIR / filename
    resp = requests.get(outputs[0], timeout=120)
    if resp.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(resp.content)
        return output_path
    return None

def extract_frames(video_path, shot_id):
    frames_dir = OUTPUT_DIR / f"{shot_id}_frames"
    frames_dir.mkdir(exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", "fps=1", "-frames:v", "5",
        str(frames_dir / "frame_%02d.png")
    ], capture_output=True)
    return sorted(frames_dir.glob("frame_*.png"))

def measure_frames(frames, anchor_embed, app):
    import cv2
    measurements = []
    for frame_path in frames:
        img = cv2.imread(str(frame_path))
        faces = app.get(img)
        if faces:
            face = max(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]))
            sim = float(np.dot(anchor_embed.flatten(), face.embedding) / (
                np.linalg.norm(anchor_embed) * np.linalg.norm(face.embedding)
            ))
            measurements.append({"frame": frame_path.name, "sim": round(sim, 4)})
            log(f"  {frame_path.name}: {sim:.4f}")
        else:
            measurements.append({"frame": frame_path.name, "sim": None})
            log(f"  {frame_path.name}: NO_FACE")
    return measurements

def main():
    log("=" * 60)
    log("RE-RENDER COUTO S10-01 v2 — Fix Cartoon Background")
    log("=" * 60)

    api_key = load_api_key()
    if not api_key:
        log("FATAL: No API key")
        return

    # Load ArcFace
    sys.path.insert(0, '/opt/windi/venv-poe/lib/python3.11/site-packages')
    import cv2
    from insightface.app import FaceAnalysis
    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))
    anchor_embed = np.load(ANCHOR_NPY)
    log("ArcFace loaded")

    image_data = load_anchor_base64()
    log(f"Anchor: {ANCHOR_PATH.name}")
    log(f"Prompt: {S10_V2_PROMPT[:80]}...")

    task_id = submit_job(api_key, S10_V2_PROMPT, image_data)
    if not task_id:
        log("FATAL: Submit failed")
        return

    log(f"Task: {task_id}")
    result = poll_job(api_key, task_id)
    if not result:
        log("FATAL: Generation failed")
        return

    video_path = download_video(result, "S10-01_v2.mp4")
    if not video_path:
        log("FATAL: Download failed")
        return

    log(f"Video: {video_path.name}")

    # Extract and measure
    frames = extract_frames(video_path, "S10-01_v2")
    log(f"Measuring {len(frames)} frames:")
    measurements = measure_frames(frames, anchor_embed, app)

    sims = [m["sim"] for m in measurements if m["sim"] is not None]
    avg = sum(sims) / len(sims) if sims else 0
    min_sim = min(sims) if sims else 0
    max_sim = max(sims) if sims else 0

    threshold = 0.75
    passed = avg >= threshold

    log("")
    log("=" * 60)
    log(f"S10-01_v2 MEASUREMENT")
    log("=" * 60)
    profile = " → ".join([f"{s:.2f}" for s in sims])
    log(f"Profile: {profile}")
    log(f"Avg: {avg:.4f} | Min: {min_sim:.4f} | Max: {max_sim:.4f}")
    log(f"[{'PASS' if passed else 'FAIL'}] avg={avg:.4f} vs >= {threshold} (margin: {avg-threshold:+.4f})")

    # Copy to public
    import shutil
    public_path = PUBLIC_DIR / "S10-01_v2.mp4"
    shutil.copy(video_path, public_path)
    log(f"\nPublic URL: https://windi-domain.com/docs/hios-forensic/couto-shots-v1/S10-01_v2.mp4")

if __name__ == "__main__":
    main()
