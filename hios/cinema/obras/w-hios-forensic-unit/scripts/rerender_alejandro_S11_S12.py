#!/usr/bin/env python3
"""
RE-RENDER ALEJANDRO S11 + S12
=============================
S11: Isolate completely - no confrontation reference
S12: Anti-Movement reinforced - head locked

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

# FIXED PROMPTS - completely isolated, no other people
RERENDER_SHOTS = [
    {
        "id": "S11-01_v2",
        "scene": 11,
        "description": "Defiant reaction - completely isolated",
        "threshold": 0.75,
        "prompt": """Close-up portrait of a man, early 40s, dark brown hair with grey at temples slicked back. Strong angular jaw, cold brown eyes. Dark navy Italian suit, white shirt, no tie visible.

Expression already formed: arrogant defiance, controlled superiority. Jaw tensed. Eyes fixed forward with territorial challenge. Near-frontal, head perfectly still, locked in position.

SOLO SUBJECT. No other people. Plain office background, soft lighting. Camera locked. Cinematic 4K, shallow depth of field on face."""
    },
    {
        "id": "S12-01_v2",
        "scene": 12,
        "description": "Cold command - head locked",
        "threshold": 0.75,
        "prompt": """Close-up portrait of a man, early 40s, dark brown hair with grey at temples. Angular jaw, ice-cold brown eyes. Dark suit, white shirt.

Expression already formed: absolute authority, cold command. Eyes narrowed, predatory. Head perfectly still, locked, no rotation. Near-frontal framing maintained throughout.

SOLO SUBJECT. Evening light, dramatic shadows. Camera locked, no movement. Cinematic 4K, shallow depth of field."""
    }
]

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
        log(f"  {status} ({int(time.time()-start)}s)")
        time.sleep(10)
    return None

def download_video(result, shot_id):
    outputs = result.get("output", [])
    if not outputs:
        return None
    output_path = OUTPUT_DIR / f"{shot_id}.mp4"
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
            # Get LARGEST face (should be the main subject)
            face = max(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]))
            sim = float(np.dot(anchor_embed.flatten(), face.embedding) / (
                np.linalg.norm(anchor_embed) * np.linalg.norm(face.embedding)
            ))
            measurements.append({"frame": frame_path.name, "sim": round(sim, 4)})
            log(f"    {frame_path.name}: {sim:.4f}")
        else:
            measurements.append({"frame": frame_path.name, "sim": None})
            log(f"    {frame_path.name}: NO_FACE")
    return measurements

def main():
    log("=" * 60)
    log("RE-RENDER ALEJANDRO S11 + S12")
    log("S11: Isolated (no confrontation)")
    log("S12: Anti-Movement reinforced")
    log("=" * 60)

    api_key = load_api_key()
    if not api_key:
        log("FATAL: No API key")
        return

    sys.path.insert(0, '/opt/windi/venv-poe/lib/python3.11/site-packages')
    import cv2
    from insightface.app import FaceAnalysis
    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))
    anchor_embed = np.load(ANCHOR_NPY)
    log("ArcFace loaded")

    image_data = load_anchor_base64()
    results = []

    for shot in RERENDER_SHOTS:
        log(f"\n{shot['id']} — {shot['description']}")
        
        task_id = submit_job(api_key, shot["prompt"], image_data)
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

        log(f"  Video: {video_path.name}")
        frames = extract_frames(video_path, shot["id"])
        log(f"  Measuring {len(frames)} frames:")

        measurements = measure_frames(frames, anchor_embed, app)
        sims = [m["sim"] for m in measurements if m["sim"] is not None]
        avg = sum(sims) / len(sims) if sims else 0
        min_sim = min(sims) if sims else 0
        max_sim = max(sims) if sims else 0
        passed = min_sim >= shot["threshold"]
        margin = round(min_sim - shot["threshold"], 4)

        profile = " → ".join([f"{s:.2f}" for s in sims])
        log(f"  Profile: {profile}")
        log(f"  [{'PASS' if passed else 'FAIL'}] min={min_sim:.4f} avg={avg:.4f} (margin: {margin:+.4f})")

        results.append({
            "shot": shot["id"],
            "avg": round(avg, 4),
            "min": round(min_sim, 4),
            "max": round(max_sim, 4),
            "passed": passed,
            "margin": margin,
            "measurements": measurements
        })

        # Copy to public
        import shutil
        shutil.copy(video_path, PUBLIC_DIR / f"{shot['id']}.mp4")

        time.sleep(2)

    # Summary
    log("\n" + "=" * 60)
    log("RE-RENDER SUMMARY")
    log("=" * 60)
    for r in results:
        if "avg" in r:
            emoji = "PASS" if r["passed"] else "FAIL"
            log(f"[{emoji}] {r['shot']}: min={r['min']:.4f} avg={r['avg']:.4f} (margin: {r['margin']:+.4f})")
        else:
            log(f"[FAIL] {r['shot']}: {r['status']}")

    passed_count = sum(1 for r in results if r.get("passed"))
    log(f"\nPASSED: {passed_count}/{len(RERENDER_SHOTS)}")

if __name__ == "__main__":
    main()
