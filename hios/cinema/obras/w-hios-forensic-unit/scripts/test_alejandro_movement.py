#!/usr/bin/env python3
"""
ALEJANDRO MOVEMENT TEST — Conversation Simulation
METHOD-001: No affirmations. Only numbers.
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

ANCHOR_PATH = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/alejandro.valenzuela.anchor.v1.png")
ANCHOR_NPY = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/alejandro.valenzuela.anchor.v1.embedding.npy")
OUTPUT_DIR = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/shots/alejandro")
PUBLIC_DIR = Path("/opt/windi/static/docs/hios-forensic/alejandro-shots-v1")

API_BASE = "https://api.dev.runwayml.com/v1"
API_VERSION = "2024-11-06"

# Shortened prompt (<1000 chars)
MOVEMENT_PROMPT = """Close-up of a man, early 40s, dark brown hair with grey at temples, slicked back. Strong jaw, penetrating brown eyes, cold intelligence. Impeccable dark navy Italian suit, white shirt, silk tie.

Head turns naturally side to side, eyes scanning left and right as if in conversation. VC smile that never reaches the eyes. Subtle nods of acknowledgment. Near-frontal maintained.

42nd floor Frankfurt penthouse, floor-to-ceiling windows, harsh daylight shadows. Camera follows smoothly. Cinematic 4K, corporate thriller, shallow depth of field."""

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
            det = float(face.det_score)
            measurements.append({"frame": frame_path.name, "sim": round(sim, 4), "det": round(det, 4)})
            log(f"  {frame_path.name}: sim={sim:.4f} det={det:.4f}")
        else:
            measurements.append({"frame": frame_path.name, "sim": None, "det": None})
            log(f"  {frame_path.name}: NO_FACE")
    return measurements

def main():
    log("=" * 60)
    log("ALEJANDRO MOVEMENT TEST — Conversation Simulation")
    log("=" * 60)

    api_key = load_api_key()
    if not api_key:
        log("FATAL: No API key")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, '/opt/windi/venv-poe/lib/python3.11/site-packages')
    import cv2
    from insightface.app import FaceAnalysis
    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))
    anchor_embed = np.load(ANCHOR_NPY)
    log("ArcFace loaded")

    image_data = load_anchor_base64()
    log(f"Anchor: {ANCHOR_PATH.name}")

    task_id = submit_job(api_key, MOVEMENT_PROMPT, image_data)
    if not task_id:
        log("FATAL: Submit failed")
        return

    log(f"Task: {task_id}")
    result = poll_job(api_key, task_id)
    if not result:
        log("FATAL: Generation failed")
        return

    video_path = download_video(result, "alejandro_movement_test.mp4")
    if not video_path:
        log("FATAL: Download failed")
        return

    log(f"Video: {video_path.name}")

    frames = extract_frames(video_path, "alejandro_movement_test")
    log(f"Measuring {len(frames)} frames:")
    measurements = measure_frames(frames, anchor_embed, app)

    sims = [m["sim"] for m in measurements if m["sim"] is not None]
    avg = sum(sims) / len(sims) if sims else 0
    min_sim = min(sims) if sims else 0
    max_sim = max(sims) if sims else 0

    log("")
    log("=" * 60)
    log("ALEJANDRO MOVEMENT TEST — MEASUREMENT")
    log("=" * 60)
    profile = " → ".join([f"{s:.2f}" for s in sims])
    log(f"Profile: {profile}")
    log(f"Avg: {avg:.4f} | Min: {min_sim:.4f} | Max: {max_sim:.4f}")
    
    if min_sim >= 0.75:
        verdict = "FORENSE"
    elif min_sim >= 0.65:
        verdict = "GEOMETRY"
    elif avg >= 0.65:
        verdict = "MARGINAL"
    else:
        verdict = "FAIL"
    
    log(f"VERDICT: {verdict}")
    log("=" * 60)

    import shutil
    public_path = PUBLIC_DIR / "alejandro_movement_test.mp4"
    shutil.copy(video_path, public_path)
    log(f"\nPublic URL: https://windi-domain.com/docs/hios-forensic/alejandro-shots-v1/alejandro_movement_test.mp4")

    result_data = {
        "test": "movement",
        "character": "Alejandro Valenzuela",
        "anchor": str(ANCHOR_PATH),
        "measurements": measurements,
        "avg": round(avg, 4),
        "min": round(min_sim, 4),
        "max": round(max_sim, 4),
        "verdict": verdict,
        "timestamp": datetime.now().isoformat()
    }
    with open(OUTPUT_DIR / "alejandro_movement_test.json", "w") as f:
        json.dump(result_data, f, indent=2)

if __name__ == "__main__":
    main()
