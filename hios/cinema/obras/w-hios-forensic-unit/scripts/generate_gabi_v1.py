#!/usr/bin/env python3
"""
GENERATE GABI SANTOS v1 — First Character Female
=================================================
S00-01: Sorriso para o filho (FORENSE >= 0.75)
S01-01: Rosto determinado no reflexo (OPERACIONAL >= 0.65)
S03-01: Dignidade soberana (FORENSE >= 0.75)
S04-01: Rosto apos a queda (FORENSE >= 0.75)

Method: Anti-Movement Medicine
- Already in frame
- Near-frontal, head stays toward lens
- Camera locked
- Light moves, not subject

Liga IA+H: Human Dragon (I9) + CCode (Architect)
Date: 07 Jun 2026
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
ANCHOR_PATH = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/gabi.santos.anchor.v1.png")
ANCHOR_NPY = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/gabi.santos.anchor.v1.embedding.npy")
OUTPUT_DIR = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/shots/gabi")

API_BASE = "https://api.dev.runwayml.com/v1"
API_VERSION = "2024-11-06"

# === GABI SHOTS — Anti-Movement Medicine ===
GABI_SHOTS = [
    {
        "id": "S00-01_v1",
        "scene": 0,
        "description": "Sorriso para o filho",
        "threshold": 0.75,
        "tier": "FORENSE",
        "prompt": """A 33-year-old Brazilian woman with warm olive skin and dark wavy hair to her shoulders. She is ALREADY SEATED, looking at her phone screen with a genuine warm smile. Soft indirect warm lighting from above. Near-frontal angle, head stays toward lens. Eyes bright with affection.

Camera locked. The phone screen casts a subtle glow on her face. She does not move. Only the light breathes.

Intimate, human, photorealistic. 50mm lens. Sharp focus on face. Cinematic 4K."""
    },
    {
        "id": "S01-01_v1",
        "scene": 1,
        "description": "Rosto determinado (reflexo)",
        "threshold": 0.65,
        "tier": "OPERACIONAL",
        "prompt": """A 33-year-old Brazilian woman with warm olive skin and dark wavy hair. She is ALREADY AT A TERMINAL, near-frontal, looking at a screen. Cool blue-white light from multiple monitors reflects on her face. Expression of cold determination, almost sacrificial resolve.

Camera locked. Code lines scroll on screen, casting moving light across her still face. She does not move. Only the light moves.

Corporate NOIR atmosphere. Photorealistic. 50mm lens. Sharp focus. Cinematic 4K."""
    },
    {
        "id": "S03-01_v1",
        "scene": 3,
        "description": "Dignidade soberana",
        "threshold": 0.75,
        "tier": "FORENSE",
        "prompt": """A 33-year-old Brazilian woman with warm olive skin and dark wavy hair. She STANDS near-frontal, head toward lens, with sovereign dignity. No fear in her expression. Serene, almost peaceful defiance. Minimal corporate lighting from above, glass wall behind her.

Camera locked. She is completely still. Ambient light shifts subtly through the glass. She does not move.

Final human moment. Photorealistic. 50mm lens. Sharp focus on face. Cinematic 4K."""
    },
    {
        "id": "S04-01_v1",
        "scene": 4,
        "description": "Rosto apos a queda",
        "threshold": 0.75,
        "tier": "FORENSE",
        "prompt": """A 33-year-old Brazilian woman with warm olive skin and dark wavy hair. She lies still, eyes open, near-frontal angle from above. No violence visible. Expression of strange peace, dignity preserved. Cold ambient night light from above. Glass fragments catch light nearby.

Camera locked, looking down. She does not move. Scattered light from broken glass creates subtle sparkles around her still face.

This is the mother who promised to see her son's dragon drawing. Photorealistic. 50mm lens. Sharp focus on face. Respectful framing. Cinematic 4K."""
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
    log("GENERATE GABI SANTOS v1 — First Female Character")
    log("Anti-Movement Medicine Applied")
    log("=" * 65)

    # Verify anchor exists
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

    total = len(GABI_SHOTS)
    for i, shot in enumerate(GABI_SHOTS):
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
        passed = avg >= shot["threshold"]
        margin = round(avg - shot["threshold"], 4)

        emoji = "PASS" if passed else "FAIL"
        log(f"  [{emoji}] avg={avg:.4f} vs >= {shot['threshold']} (margin: {margin:+.4f})")

        # Profile analysis
        if sims:
            profile = " -> ".join([f"{s:.2f}" for s in sims])
            log(f"  Profile: {profile}")

            # Detect collapse
            for j in range(1, len(sims)):
                if sims[j-1] > 0.7 and sims[j] < 0.3:
                    log(f"  WARNING: COLLAPSE at frame {j+1}: {sims[j-1]:.2f} -> {sims[j]:.2f}")

        results.append({
            "shot": shot["id"],
            "scene": shot["scene"],
            "description": shot["description"],
            "tier": shot["tier"],
            "avg_similarity": round(avg, 4),
            "threshold": shot["threshold"],
            "passed": passed,
            "margin": margin,
            "measurements": measurements
        })

        time.sleep(2)

    # Final Report
    log("\n" + "=" * 65)
    log("FINAL REPORT — GABI SANTOS v1")
    log("=" * 65)

    for r in results:
        if "avg_similarity" in r:
            emoji = "PASS" if r["passed"] else "FAIL"
            log(f"[{emoji}] {r['shot']} ({r['tier']}): {r['avg_similarity']:.4f} vs >= {r['threshold']} (margin: {r['margin']:+.4f})")
        else:
            log(f"[FAIL] {r['shot']}: {r['status']}")

    passed_count = sum(1 for r in results if r.get("passed"))
    log(f"\nPASSED: {passed_count}/{total}")

    # Save manifest
    manifest_path = OUTPUT_DIR / f"GABI_V1_RESULTS_{run_id}.json"
    with open(manifest_path, "w") as f:
        json.dump({
            "run_id": run_id,
            "character": "Gabi Santos",
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

if __name__ == "__main__":
    main()
