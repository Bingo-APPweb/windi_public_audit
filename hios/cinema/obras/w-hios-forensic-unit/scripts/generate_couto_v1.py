#!/usr/bin/env python3
"""
GENERATE MARCUS COUTO v1 — The Caretaker
=========================================
S02-01: Corridor - observes Gabi through glass (FORENSE >= 0.75) — predator still
S03-01: Confronts Gabi - "acabou a auditoria" (FORENSE >= 0.75)
S03-02: Advances toward Gabi - physical threat (GEOMETRY >= 0.65)
S10-01: Rooftop with tablet - reports to Alejandro (FORENSE >= 0.75) — head fixed
S11-01: Steps forward - "caso está fechado" (GEOMETRY >= 0.65)
S12-01: Looks out window - "cinco anos" (GEOMETRY >= 0.65) — profile confirmed by test
S13-01: Tribunal - fear in eyes (FORENSE >= 0.75)

Method: Anti-Movement Medicine + METHOD-001 (Measure Before Affirm)
- Already in frame
- Near-frontal, head stays toward lens
- Camera locked
- Light moves, not subject
- NO AFFIRMATIONS. ONLY NUMBERS.

Liga IA+H: Human Dragon (I9) + CCode (Architect)
Date: 09 Jun 2026
Revised: 09 Jun 2026 — METHOD-001 integrated, thresholds corrected per Guardian
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
ANCHOR_PATH = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/marcus.couto.anchor.v1.png")
ANCHOR_NPY = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/marcus.couto.anchor.v1.embedding.npy")
OUTPUT_DIR = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/shots/couto")

API_BASE = "https://api.dev.runwayml.com/v1"
API_VERSION = "2024-11-06"

# === COUTO SHOTS — Anti-Movement Medicine ===
COUTO_SHOTS = [
    {
        "id": "S02-01_v1",
        "scene": 2,
        "description": "Corridor - observes Gabi through glass",
        "threshold": 0.75,
        "tier": "FORENSE",  # Predator still = high threshold
        "prompt": """A man in his mid-40s with slicked-back grey hair, clean-shaven, sharp angular jaw, wearing a dark cashmere overcoat over white shirt and black tie. He stands still in a dark corporate corridor at night, near-frontal framing, head perfectly still. His calculating dark eyes scan methodically left to right, watching through frosted glass. Predatory patience. Micro-expression: lips slightly compressed. Ambient office lights flicker subtly on his face. Breathing visible in chest. Camera locked. Cinematic 4K, shallow depth of field."""
    },
    {
        "id": "S03-01_v1",
        "scene": 3,
        "description": "Confrontation - acabou a auditoria",
        "threshold": 0.75,
        "tier": "FORENSE",
        "prompt": """Close-up portrait of a man in his mid-40s with slicked-back grey hair, completely clean-shaven, pronounced angular jaw, cold calculating dark eyes. Wearing dark cashmere overcoat, white shirt, black tie. Expression already formed: cold bureaucratic courtesy masking total emptiness. Near-frontal, head locked still. Eyes fixed forward with predatory stillness. Subtle ambient light from office windows plays across his face. Visible micro-tension in jaw muscles. Camera locked. Cinematic 4K, dramatic corporate lighting."""
    },
    {
        "id": "S03-02_v1",
        "scene": 3,
        "description": "Physical threat - advances",
        "threshold": 0.65,
        "tier": "OPERACIONAL",
        "prompt": """Medium shot of a man in his mid-40s with slicked-back grey hair, clean-shaven, angular jaw, wearing dark cashmere overcoat over white shirt. He stands perfectly still after having stepped forward, body already in threatening proximity position. Near-frontal framing, head locked. Expression: cold intimidation already formed. Dark calculating eyes fixed on target. Ambient light shifts subtly across his face from window reflections. Visible breathing in shoulders. Camera locked, stable. Cinematic 4K, tense corporate thriller lighting."""
    },
    {
        "id": "S10-01_v1",
        "scene": 10,
        "description": "Rooftop - reports to Alejandro",
        "threshold": 0.75,
        "tier": "FORENSE",  # Standing with tablet, head fixed
        "prompt": """Medium shot of a man in his mid-40s with slicked-back grey hair, completely clean-shaven, sharp angular jaw, wearing a perfectly tailored dark European suit, white shirt. He holds a corporate tablet in both hands, already positioned. Near-frontal framing, head and body perfectly still. Eyes scan the tablet with methodical precision. Expression: efficient, emotionless corporate facade. Harsh daylight from floor-to-ceiling windows creates dramatic shadows. Frankfurt skyline visible behind. Camera locked. Cinematic 4K, corporate thriller aesthetic."""
    },
    {
        "id": "S11-01_v1",
        "scene": 11,
        "description": "Confrontation with Interpol",
        "threshold": 0.65,
        "tier": "OPERACIONAL",
        "prompt": """Medium close-up of a man in his mid-40s with slicked-back grey hair, clean-shaven, angular jaw, cold dark eyes. Wearing dark suit, white shirt. He stands in a challenging posture, body already positioned forward, near-frontal framing. Head locked perfectly still. Expression already formed: controlled aggression beneath bureaucratic mask. Eyes fixed with predatory focus. Harsh daylight creates dramatic shadows across his face. Subtle jaw muscle tension visible. Breathing visible in chest. Camera locked. Cinematic 4K, tense standoff lighting."""
    },
    {
        "id": "S12-01_v1",
        "scene": 12,
        "description": "Window introspection - cinco anos",
        "threshold": 0.65,
        "tier": "GEOMETRY",  # Profile confirmed by movement test (0.7555)
        "prompt": """Profile-to-three-quarter shot of a man in his mid-40s with slicked-back grey hair, completely clean-shaven, angular jaw. Wearing dark suit. He stands at floor-to-ceiling window, already positioned, gazing out at Frankfurt skyline below. Head perfectly still, locked in contemplation. Expression already formed: subtle crack in the mask, hint of concern in the eyes. Natural daylight illuminates his profile. Subtle reflection visible in glass. Breathing visible in shoulders. Camera locked. Cinematic 4K, contemplative corporate thriller lighting."""
    },
    {
        "id": "S13-01_v1",
        "scene": 13,
        "description": "Tribunal - fear in eyes",
        "threshold": 0.75,
        "tier": "FORENSE",
        "prompt": """Close-up portrait of a man in his mid-40s with slicked-back grey hair, completely clean-shaven, pronounced angular jaw. Wearing impeccable dark suit, white shirt. Seated in courtroom, near-frontal framing, head perfectly still. Expression already formed: attempt at composure failing, fear visible in the dark eyes. The mask cracking. Micro-expression: subtle tension around mouth, eyes slightly wider than normal. Warm institutional lighting from wood-paneled courtroom. Camera locked. Cinematic 4K, dramatic courtroom lighting."""
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
    log("GENERATE MARCUS COUTO v1 — The Caretaker")
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

    total = len(COUTO_SHOTS)
    for i, shot in enumerate(COUTO_SHOTS):
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
        passed = avg >= shot["threshold"]
        margin = round(avg - shot["threshold"], 4)

        # GEOMETRY shots require at least 1 frame >= 0.75 (anchor-frame rule)
        anchor_frame_ok = True
        if shot["tier"] == "GEOMETRY":
            anchor_frame_ok = max_sim >= 0.75
            if not anchor_frame_ok:
                log(f"  WARNING: GEOMETRY shot lacks anchor-frame >= 0.75 (max={max_sim:.4f})")
                passed = False  # Fail GEOMETRY without identity anchor

        emoji = "PASS" if passed else "FAIL"
        log(f"  [{emoji}] avg={avg:.4f} vs >= {shot['threshold']} (margin: {margin:+.4f})")
        if shot["tier"] == "GEOMETRY":
            log(f"  GEOMETRY anchor-frame: max={max_sim:.4f} {'✓' if anchor_frame_ok else '✗'} (need >= 0.75)")

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
    log("FINAL REPORT — MARCUS COUTO v1")
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
    manifest_path = OUTPUT_DIR / f"COUTO_V1_RESULTS_{run_id}.json"
    with open(manifest_path, "w") as f:
        json.dump({
            "run_id": run_id,
            "character": "Marcus Couto",
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
