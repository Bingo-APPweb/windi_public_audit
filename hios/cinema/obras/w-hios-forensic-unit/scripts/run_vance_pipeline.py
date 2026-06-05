#!/usr/bin/env python3
"""
VANCE PIPELINE — Complete generation + validation pipeline
============================================================
1. Generate 10 IDENTITY shots via Runway Gen-4
2. Poll for completion
3. Download videos
4. Extract frames
5. Measure against anchor (ArcFace)
6. Output results with run_id and det_score

Constitutional bindings: I9, I11, I14, I19
Model lock: WINDI-SPINE-MODEL-LOCK-20260604173447
Anchor lock: WINDI-ANCHOR-VANCE-LOCK-20260605103558
"""

import os
import sys
import json
import time
import base64
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime

import requests
import numpy as np

# === PATHS ===
ANCHOR_PATH = Path("/opt/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/marcus.vance.anchor.v1.png")
ANCHOR_NPY = Path("/opt/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/marcus.vance.anchor.v1.embedding.npy")
OUTPUT_DIR = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/shots/vance")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# === API ===
API_BASE = "https://api.dev.runwayml.com/v1"
API_VERSION = "2024-11-06"

# Load API key
def load_api_key():
    env_file = Path("/opt/windi/.env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("RUNWAY_API_KEY="):
                return line.strip().split("=", 1)[1]
    return os.environ.get("RUNWAY_API_KEY")

# === VANCE SHOTS ===
VANCE_SHOTS = [
    {"id": "S06-01", "scene": 6, "emotional": False, "description": "Vance emerges from shadow",
     "prompt": "Middle-aged man with grey slicked-back hair, clean-shaven, dark suit, emerging from shadows into dim blue light. Interpol inspector, authoritative presence. Cinematic lighting, noir atmosphere, 4K."},
    {"id": "S06-02", "scene": 6, "emotional": True, "description": "Vance's face loses color",
     "prompt": "Middle-aged man with grey slicked-back hair, clean-shaven, dark suit, face draining of color in recognition. Shock and disbelief. Blue bunker lighting reflecting on face. Close-up, cinematic, 4K."},
    {"id": "S07-01", "scene": 7, "emotional": True, "description": "Vance's face — ancient pain",
     "prompt": "Middle-aged man with grey slicked-back hair, clean-shaven, dark suit, face showing deep ancient pain. Vulnerability beneath authority. Server room blue light. Close-up portrait, cinematic, 4K."},
    {"id": "S09-01", "scene": 9, "emotional": False, "description": "Vance at screen with team",
     "prompt": "Middle-aged man with grey slicked-back hair, clean-shaven, dark suit, standing at large screen with team. Professional intensity. Blue light from monitors. Medium shot, cinematic, 4K."},
    {"id": "S09-02", "scene": 9, "emotional": True, "description": "Vance's non-response",
     "prompt": "Middle-aged man with grey slicked-back hair, clean-shaven, dark suit, face showing weighted silence. Not speaking but communicating everything. Blue ambient light. Close-up, cinematic, 4K."},
    {"id": "S11-01", "scene": 11, "emotional": False, "description": "Vance enters confrontation",
     "prompt": "Middle-aged man with grey slicked-back hair, clean-shaven, dark suit, entering corporate office with authority. Interpol badge visible. Natural daylight through windows. Medium shot, cinematic, 4K."},
    {"id": "S14-01", "scene": 14, "emotional": False, "description": "Vance at window",
     "prompt": "Middle-aged man with grey slicked-back hair, clean-shaven, dark suit, standing at window looking at Frankfurt cityscape. Reflective moment. Golden hour light. Medium shot, cinematic, 4K."},
    {"id": "S14-02", "scene": 14, "emotional": True, "description": "Vance's weighted answer",
     "prompt": "Middle-aged man with grey slicked-back hair, clean-shaven, dark suit, face showing the weight of truth over survival. Deep conviction. Soft corridor light. Close-up portrait, cinematic, 4K."},
    {"id": "S15-01", "scene": 15, "emotional": True, "description": "Vance alone at monitor, red eyes",
     "prompt": "Middle-aged man with grey slicked-back hair, clean-shaven, dark suit, alone at monitor late at night, eyes red from exhaustion and emotion. Blue screen glow on face. Close-up, cinematic, 4K."},
    {"id": "S07-02", "scene": 7, "emotional": False, "description": "Vance observing analysis",
     "prompt": "Middle-aged man with grey slicked-back hair, clean-shaven, dark suit, watching analysis on screen with focused intensity. Professional observation. Blue bunker lighting. Medium close-up, cinematic, 4K."}
]

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")
    sys.stdout.flush()

def load_anchor_base64():
    with open(ANCHOR_PATH, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:image/png;base64,{data}"

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

    try:
        resp = requests.post(f"{API_BASE}/image_to_video", headers=headers, json=payload, timeout=60)
        if resp.status_code in [200, 201]:
            return resp.json().get("id")
        else:
            log(f"  ERROR submitting {shot['id']}: HTTP {resp.status_code}")
            return None
    except Exception as e:
        log(f"  ERROR submitting {shot['id']}: {e}")
        return None

def poll_job(api_key: str, task_id: str, max_wait: int = 300) -> dict:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Runway-Version": API_VERSION
    }
    start = time.time()

    while time.time() - start < max_wait:
        try:
            resp = requests.get(f"{API_BASE}/tasks/{task_id}", headers=headers, timeout=30)
            result = resp.json()
            status = result.get("status", "unknown")

            if status == "SUCCEEDED":
                return result
            elif status == "FAILED":
                return None

            time.sleep(5)
        except:
            time.sleep(5)

    return None

def download_video(result: dict, shot_id: str) -> Path:
    outputs = result.get("output", [])
    if not outputs:
        return None

    video_url = outputs[0]
    output_path = OUTPUT_DIR / f"{shot_id}.mp4"

    try:
        resp = requests.get(video_url, timeout=120)
        if resp.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            return output_path
    except:
        pass
    return None

def extract_frames(video_path: Path, shot_id: str) -> list:
    frames_dir = OUTPUT_DIR / f"{shot_id}_frames"
    frames_dir.mkdir(exist_ok=True)

    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", "fps=1", "-frames:v", "5",
        str(frames_dir / "frame_%02d.png")
    ]
    subprocess.run(cmd, capture_output=True)

    return sorted(frames_dir.glob("frame_*.png"))

def measure_frames(frames: list, anchor_embed: np.ndarray, app) -> list:
    import cv2
    results = []

    for frame_path in frames:
        img = cv2.imread(str(frame_path))
        faces = app.get(img)

        if not faces:
            results.append({
                "frame": frame_path.name,
                "similarity": None,
                "det_score": None,
                "n_faces": 0,
                "status": "NO_FACE"
            })
            continue

        # Get largest face
        face = max(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]))
        frame_embed = face.embedding
        det_score = float(face.det_score)

        # Cosine similarity
        sim = float(np.dot(anchor_embed.flatten(), frame_embed) / (
            np.linalg.norm(anchor_embed) * np.linalg.norm(frame_embed)
        ))

        status = "FORENSIC" if sim >= 0.75 else ("OPERATIONAL" if sim >= 0.65 else "FAIL")

        results.append({
            "frame": frame_path.name,
            "similarity": round(sim, 4),
            "det_score": round(det_score, 4),
            "n_faces": len(faces),
            "status": status
        })

    return results

def main():
    log("=" * 70)
    log("VANCE PIPELINE — 10 IDENTITY + 5 Emotional")
    log("Model Lock: WINDI-SPINE-MODEL-LOCK-20260604173447")
    log("Anchor Lock: WINDI-ANCHOR-VANCE-LOCK-20260605103558")
    log("=" * 70)

    api_key = load_api_key()
    if not api_key:
        log("FATAL: No API key")
        return

    log(f"API Key: {api_key[:20]}...{api_key[-8:]}")

    # Load anchor
    log("Loading anchor image...")
    image_data = load_anchor_base64()

    # Load ArcFace
    log("Loading ArcFace model...")
    sys.path.insert(0, '/opt/windi/venv-poe/lib/python3.11/site-packages')
    import cv2
    from insightface.app import FaceAnalysis
    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))

    anchor_embed = np.load(ANCHOR_NPY)
    log(f"Anchor loaded: {anchor_embed.shape}")

    # Process shots
    all_results = []
    run_id = datetime.now().strftime("%Y%m%d%H%M%S")

    for i, shot in enumerate(VANCE_SHOTS):
        log(f"\n[{i+1}/10] {shot['id']}: {shot['description']}")
        emoji = "⭐" if shot["emotional"] else "👤"
        log(f"  Type: {emoji} {'EMOTIONAL' if shot['emotional'] else 'IDENTITY'}")

        # Submit
        log("  Submitting to Runway...")
        task_id = submit_job(api_key, shot, image_data)
        if not task_id:
            all_results.append({"shot_id": shot["id"], "status": "SUBMIT_FAILED"})
            continue

        log(f"  Task: {task_id}")

        # Poll
        log("  Waiting for completion...")
        result = poll_job(api_key, task_id)
        if not result:
            all_results.append({"shot_id": shot["id"], "task_id": task_id, "status": "POLL_FAILED"})
            continue

        # Download
        log("  Downloading video...")
        video_path = download_video(result, shot["id"])
        if not video_path:
            all_results.append({"shot_id": shot["id"], "task_id": task_id, "status": "DOWNLOAD_FAILED"})
            continue

        log(f"  Saved: {video_path.name}")

        # Extract frames
        log("  Extracting frames...")
        frames = extract_frames(video_path, shot["id"])
        log(f"  Extracted: {len(frames)} frames")

        # Measure
        log("  Measuring against anchor...")
        measurements = measure_frames(frames, anchor_embed, app)

        # Summarize
        sims = [m["similarity"] for m in measurements if m["similarity"] is not None]
        if sims:
            avg = sum(sims) / len(sims)
            det_scores = [m["det_score"] for m in measurements if m["det_score"] is not None]
            avg_det = sum(det_scores) / len(det_scores) if det_scores else 0

            forensic = sum(1 for s in sims if s >= 0.75)
            operational = sum(1 for s in sims if s >= 0.65)

            status = "FORENSIC" if forensic >= len(sims) * 0.8 else (
                "OPERATIONAL" if operational >= len(sims) * 0.6 else "FAIL"
            )

            log(f"  Result: avg={avg:.4f}, det={avg_det:.4f}, status={status}")
        else:
            avg = 0
            avg_det = 0
            status = "NO_FACES"
            log(f"  Result: NO_FACES")

        shot_result = {
            "shot_id": shot["id"],
            "scene": shot["scene"],
            "emotional": shot["emotional"],
            "description": shot["description"],
            "run_id": run_id,
            "task_id": task_id,
            "video": str(video_path),
            "measurements": measurements,
            "summary": {
                "avg_similarity": round(avg, 4) if sims else None,
                "avg_det_score": round(avg_det, 4) if sims else None,
                "n_frames": len(frames),
                "n_measured": len(sims),
                "status": status
            }
        }
        all_results.append(shot_result)

        # Rate limit
        time.sleep(2)

    # Final report
    log("\n" + "=" * 70)
    log("FINAL REPORT")
    log("=" * 70)

    for r in all_results:
        if "summary" in r:
            s = r["summary"]
            emoji = "⭐" if r.get("emotional") else "👤"
            status_emoji = "✅" if s["status"] == "FORENSIC" else ("🟢" if s["status"] == "OPERATIONAL" else "❌")
            log(f"{emoji} {r['shot_id']}: {s['avg_similarity']:.4f} {status_emoji} {s['status']}")
        else:
            log(f"❌ {r.get('shot_id', 'unknown')}: {r.get('status', 'UNKNOWN')}")

    # Save manifest
    manifest = {
        "pipeline": "VANCE-IDENTITY-10",
        "run_id": run_id,
        "model_lock": "WINDI-SPINE-MODEL-LOCK-20260604173447",
        "anchor_lock": "WINDI-ANCHOR-VANCE-LOCK-20260605103558",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "thresholds": {"operational": 0.65, "forensic": 0.75},
        "results": all_results
    }

    manifest_path = OUTPUT_DIR / f"VANCE_RESULTS_{run_id}.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    log(f"\nManifest: {manifest_path}")
    log("=" * 70)
    log("PIPELINE COMPLETE")
    log("=" * 70)

if __name__ == "__main__":
    main()
