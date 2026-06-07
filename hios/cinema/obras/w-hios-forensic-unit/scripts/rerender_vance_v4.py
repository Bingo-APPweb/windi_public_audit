#!/usr/bin/env python3
"""
RE-RENDER VANCE v4 — Anti-Movement Medicine
============================================
S11-01: "already in frame, does not enter" (fix entrada = rotação)
S14-01: "near-frontal, head stays toward lens" (fix profile = perda de rosto)

Diagnóstico Guardian 07 Jun:
- S11-01 frame 2 colapso 0.96→0.05 = entrada em cena = rotação garantida
- S14-01 frames 3-4 colapso = profile/three-quarter + janela puxa olhar

Thresholds inalterados (decisão HD):
- S11-01: ≥0.70 (adversarial)
- S14-01: ≥0.75 (FORENSIC)
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

ANCHOR_PATH = Path("/opt/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/marcus.vance.anchor.canonical.png")
ANCHOR_NPY = Path("/opt/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/marcus.vance.anchor.canonical.npy")
OUTPUT_DIR = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/shots/vance")

API_BASE = "https://api.dev.runwayml.com/v1"
API_VERSION = "2024-11-06"

# === V4 PROMPTS — Anti-Movement Medicine ===
RERENDER_SHOTS = [
    {
        "id": "S11-01_v4",
        "threshold": 0.70,
        "diagnosis": "Frame 2 colapso 0.96→0.05 — entrada em cena = rotação",
        "fix": "Already in frame, does not enter",
        "prompt": "50s man with grey ponytail, short beard, dark coat. Standing on rooftop terrace, ALREADY IN FRAME, facing camera. He does NOT enter — he is already present. Slight expression only, no head turn. Camera locked, no orbit. Face front-facing throughout. Overcast soft light. Cinematic 4K."
    },
    {
        "id": "S14-01_v4",
        "threshold": 0.75,
        "diagnosis": "Frames 3-4 colapso — profile + janela puxa olhar",
        "fix": "Near-frontal, head stays toward lens",
        "prompt": "50s man with grey ponytail, short beard, dark coat. Standing near window, body angled slightly but FACE TURNED BACK TOWARD CAMERA, near-frontal. Camera locked. He looks out only with his EYES, head stays toward lens. Generic city skyline soft-focus behind. Golden hour light on face. Cinematic 4K."
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

def submit_job(api_key, shot, image_data):
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
    log(f"  Prompt: {shot['prompt'][:80]}...")
    resp = requests.post(f"{API_BASE}/image_to_video", headers=headers, json=payload, timeout=60)
    if resp.status_code in [200, 201]:
        return resp.json().get("id")
    log(f"  ERROR: {resp.status_code} - {resp.text[:100]}")
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
            log(f"  FAILED: {result.get('failureCode')}")
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
    log("=" * 65)
    log("RE-RENDER VANCE v4 — Anti-Movement Medicine")
    log("Guardian Diagnosis Applied")
    log("=" * 65)

    api_key = load_api_key()
    if not api_key:
        log("FATAL: No API key")
        return

    image_data = load_anchor_base64()

    sys.path.insert(0, '/opt/windi/venv-poe/lib/python3.11/site-packages')
    import cv2
    from insightface.app import FaceAnalysis
    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))
    anchor_embed = np.load(ANCHOR_NPY)
    log("ArcFace loaded\n")

    results = []
    run_id = datetime.now().strftime("%Y%m%d%H%M%S")

    for i, shot in enumerate(RERENDER_SHOTS):
        log(f"[{i+1}/2] {shot['id']} (≥{shot['threshold']})")
        log(f"  Diagnosis: {shot['diagnosis']}")
        log(f"  Fix: {shot['fix']}")

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

        log(f"  Video: {video_path.name}")
        frames = extract_frames(video_path, shot["id"])
        log(f"  Measuring {len(frames)} frames:")

        measurements = measure_frames(frames, anchor_embed, app)
        sims = [m["sim"] for m in measurements if m["sim"] is not None]
        avg = sum(sims) / len(sims) if sims else 0
        passed = avg >= shot["threshold"]
        margin = round(avg - shot["threshold"], 4)

        emoji = "✅" if passed else "❌"
        log(f"  {emoji} avg={avg:.4f} vs ≥{shot['threshold']} (margin: {margin:+.4f})")

        # Profile analysis
        if sims:
            profile = "→".join([f"{s:.2f}" for s in sims])
            log(f"  Profile: {profile}")

            # Detect collapse
            for j in range(1, len(sims)):
                if sims[j-1] > 0.7 and sims[j] < 0.3:
                    log(f"  ⚠️ COLLAPSE at frame {j+1}: {sims[j-1]:.2f}→{sims[j]:.2f}")

        results.append({
            "shot": shot["id"],
            "avg_similarity": round(avg, 4),
            "threshold": shot["threshold"],
            "passed": passed,
            "margin": margin,
            "measurements": measurements,
            "diagnosis": shot["diagnosis"],
            "fix": shot["fix"]
        })

        time.sleep(2)

    # Final
    log("\n" + "=" * 65)
    log("FINAL REPORT — v4 Anti-Movement")
    log("=" * 65)

    for r in results:
        if "avg_similarity" in r:
            emoji = "✅" if r["passed"] else "❌"
            log(f"{emoji} {r['shot']}: {r['avg_similarity']:.4f} vs ≥{r['threshold']} (margin: {r['margin']:+.4f})")
        else:
            log(f"❌ {r['shot']}: {r['status']}")

    passed_count = sum(1 for r in results if r.get("passed"))
    log(f"\nPASSED: {passed_count}/2")

    manifest_path = OUTPUT_DIR / f"VANCE_V4_ANTIMOVEMENT_{run_id}.json"
    with open(manifest_path, "w") as f:
        json.dump({
            "run_id": run_id,
            "version": "v4-anti-movement",
            "guardian_diagnosis": "07 Jun 2026",
            "results": results
        }, f, indent=2)
    log(f"Manifest: {manifest_path}")

if __name__ == "__main__":
    main()
