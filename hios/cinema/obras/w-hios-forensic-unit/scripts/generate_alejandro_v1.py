#!/usr/bin/env python3
"""
GENERATE ALEJANDRO VALENZUELA v1 — The Architect
=================================================
S10-01: Close receiving report (reaction) — FORENSE >= 0.75
S11-01: Close confronted by Interpol (tension) — FORENSE >= 0.75
S12-01: Close ordering the hunt (command) — FORENSE >= 0.75

Method: Anti-Movement Medicine + METHOD-001 (Measure Before Affirm)
- Already in frame
- Near-frontal, head stays toward lens
- Camera locked
- Light moves, not subject
- NO AFFIRMATIONS. ONLY NUMBERS.

Liga IA+H: Human Dragon (I9) + CCode (Architect)
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

# === PATHS ===
ANCHOR_PATH = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/alejandro.valenzuela.anchor.v1.png")
ANCHOR_NPY = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/alejandro.valenzuela.anchor.v1.embedding.npy")
OUTPUT_DIR = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/shots/alejandro")
PUBLIC_DIR = Path("/opt/windi/static/docs/hios-forensic/alejandro-shots-v1")

API_BASE = "https://api.dev.runwayml.com/v1"
API_VERSION = "2024-11-06"

# === ALEJANDRO SHOTS — Anti-Movement Medicine ===
ALEJANDRO_SHOTS = [
    {
        "id": "S10-01_v1",
        "scene": 10,
        "description": "Receiving report - calculating reaction",
        "threshold": 0.75,
        "tier": "FORENSE",
        "prompt": """Close-up of a man, early 40s, dark brown hair with grey at temples slicked back. Strong angular jaw, penetrating brown eyes with cold intelligence. Impeccable dark navy Italian suit, white shirt, subtle silk tie.

Expression already formed: calculating attention, processing information. Eyes fixed forward with predatory focus. The VC smile absent - pure business mode. Near-frontal, head perfectly still.

42nd floor Frankfurt penthouse, harsh daylight from windows creates dramatic shadows. Camera locked. Cinematic 4K, corporate thriller, shallow depth of field."""
    },
    {
        "id": "S11-01_v1",
        "scene": 11,
        "description": "Confronted by Interpol - controlled tension",
        "threshold": 0.75,
        "tier": "FORENSE",
        "prompt": """Close-up of a man, early 40s, dark brown hair greying at temples, slicked back with gel. Strong jaw, cold brown eyes. Dark navy Italian suit, white shirt.

Expression already formed: arrogant defiance beneath composed mask. Jaw slightly tensed. Eyes fixed with territorial challenge. The smile of a man who believes he's untouchable. Near-frontal, head locked still.

Harsh daylight creates dramatic shadows across his face. Subtle tension in neck muscles. Camera locked. Cinematic 4K, tense confrontation lighting."""
    },
    {
        "id": "S12-01_v1",
        "scene": 12,
        "description": "Ordering the hunt - cold command",
        "threshold": 0.75,
        "tier": "FORENSE",
        "prompt": """Close-up of a man, early 40s, dark brown hair with distinguished grey at temples. Angular jaw, penetrating brown eyes now ice-cold. Impeccable dark suit, white shirt.

Expression already formed: cold command, absolute authority. Eyes narrowed with predatory intent. Lips slightly parted as if giving orders. The mask of civility stripped away. Near-frontal, head perfectly still.

Evening light through penthouse windows, Frankfurt skyline behind. Dramatic shadows. Camera locked. Cinematic 4K, thriller climax aesthetic."""
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
    resp = requests.post(f"{API_BASE}/image_to_video", headers=headers, json=payload, timeout=60)
    if resp.status_code in [200, 201]:
        return resp.json().get("id")
    log(f"  ERROR: {resp.status_code} - {resp.text[:200]}")
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
    log("GENERATE ALEJANDRO VALENZUELA v1 — The Architect")
    log("Anti-Movement Medicine Applied")
    log("=" * 65)

    if not ANCHOR_PATH.exists():
        log(f"FATAL: Anchor not found: {ANCHOR_PATH}")
        return
    if not ANCHOR_NPY.exists():
        log(f"FATAL: Embedding not found: {ANCHOR_NPY}")
        return

    log(f"Anchor: {ANCHOR_PATH.name}")
    log(f"Embedding: {ANCHOR_NPY.name}")

    api_key = load_api_key()
    if not api_key:
        log("FATAL: No API key in /opt/windi/.env")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    image_data = load_anchor_base64()

    # Load ArcFace
    sys.path.insert(0, '/opt/windi/venv-poe/lib/python3.11/site-packages')
    import cv2
    from insightface.app import FaceAnalysis
    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))
    anchor_embed = np.load(ANCHOR_NPY)
    log("ArcFace loaded\n")

    results = []
    run_id = datetime.now().strftime("%Y%m%d%H%M%S")

    total = len(ALEJANDRO_SHOTS)
    for i, shot in enumerate(ALEJANDRO_SHOTS):
        log(f"[{i+1}/{total}] {shot['id']} — {shot['description']}")
        log(f"  Scene: {shot['scene']} | Tier: {shot['tier']} | Threshold: >= {shot['threshold']}")

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
        min_sim = min(sims) if sims else 0
        max_sim = max(sims) if sims else 0
        passed = min_sim >= shot["threshold"]
        margin = round(min_sim - shot["threshold"], 4)

        emoji = "PASS" if passed else "FAIL"
        log(f"  [{emoji}] avg={avg:.4f} min={min_sim:.4f} vs >= {shot['threshold']} (margin: {margin:+.4f})")

        # Profile analysis
        if sims:
            profile = " → ".join([f"{s:.2f}" for s in sims])
            log(f"  Profile: {profile}")

        results.append({
            "shot": shot["id"],
            "scene": shot["scene"],
            "description": shot["description"],
            "tier": shot["tier"],
            "avg_similarity": round(avg, 4),
            "min_similarity": round(min_sim, 4),
            "max_similarity": round(max_sim, 4),
            "threshold": shot["threshold"],
            "passed": passed,
            "margin": margin,
            "measurements": measurements
        })

        # Copy to public
        import shutil
        public_path = PUBLIC_DIR / f"{shot['id']}.mp4"
        shutil.copy(video_path, public_path)
        log(f"  Public: {shot['id']}.mp4")

        time.sleep(2)

    # Final Report
    log("\n" + "=" * 65)
    log("FINAL REPORT — ALEJANDRO VALENZUELA v1")
    log("=" * 65)

    for r in results:
        if "avg_similarity" in r:
            emoji = "PASS" if r["passed"] else "FAIL"
            log(f"[{emoji}] {r['shot']} ({r['tier']}): min={r['min_similarity']:.4f} avg={r['avg_similarity']:.4f} vs >= {r['threshold']} (margin: {r['margin']:+.4f})")
        else:
            log(f"[FAIL] {r['shot']}: {r['status']}")

    passed_count = sum(1 for r in results if r.get("passed"))
    log(f"\nPASSED: {passed_count}/{total}")

    # Save manifest
    manifest_path = OUTPUT_DIR / f"ALEJANDRO_V1_RESULTS_{run_id}.json"
    with open(manifest_path, "w") as f:
        json.dump({
            "run_id": run_id,
            "character": "Alejandro Valenzuela",
            "version": "v1",
            "method": "Anti-Movement Medicine",
            "anchor": str(ANCHOR_PATH),
            "results": results
        }, f, indent=2)
    log(f"Manifest: {manifest_path}")

    # Summary
    log("\n" + "=" * 65)
    if passed_count == total:
        log("ALL SHOTS PASSED — Ready for Human Dragon approval (I9)")
    else:
        failed = [r["shot"] for r in results if not r.get("passed", False)]
        log(f"SHOTS NEED RE-RENDER: {', '.join(failed)}")
    log("=" * 65)

    # Public URLs
    log("\nPublic URLs:")
    for shot in ALEJANDRO_SHOTS:
        log(f"  https://windi-domain.com/docs/hios-forensic/alejandro-shots-v1/{shot['id']}.mp4")

if __name__ == "__main__":
    main()
