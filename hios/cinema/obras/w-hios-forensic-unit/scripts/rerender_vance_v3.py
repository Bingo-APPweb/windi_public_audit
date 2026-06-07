#!/usr/bin/env python3
"""
RE-RENDER VANCE v3 — 3 Shots Corrigidos
=======================================
S06-01: Light moves, not Vance (SPINE fix)
S11-01: Luz difusa (SPINE fix)
S14-01: Skyline universal (Jurisdição fix)

Thresholds de Aceitação (07 Jun 2026):
- S06-01: ≥0.65 (operacional padrão)
- S11-01: ≥0.70 (elevado — shot adversarial)
- S14-01: ≥0.75 (manter FORENSIC)

Constitutional: I9, I11, I14, I19
Decisão HD: 07 Jun 2026
Guardian + CCode: Prompts v2
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
ANCHOR_PATH = Path("/opt/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/marcus.vance.anchor.canonical.png")
ANCHOR_NPY = Path("/opt/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/marcus.vance.anchor.canonical.npy")
OUTPUT_DIR = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/shots/vance")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# === API ===
API_BASE = "https://api.dev.runwayml.com/v1"
API_VERSION = "2024-11-06"

# === RE-RENDER SHOTS (Prompts v2 — 07 Jun 2026) ===
RERENDER_SHOTS = [
    {
        "id": "S06-01_v3",
        "scene": 6,
        "original_problem": "SPINE fail (0.49)",
        "fix": "Light moves, not Vance",
        "threshold": 0.65,
        "threshold_type": "operacional",
        "prompt": """Marcus Vance, 50s man with salt-pepper hair in loose ponytail, short grey beard,
weathered face with small red mark on left forehead, blue-grey eyes.
Dark wool coat with silver pin on lapel. White shirt underneath.

SCENE: Vance stands completely still as soft light gradually reveals his face.
Camera locked on face throughout. LIGHT MOVES, NOT VANCE.
Lighting transitions slowly from rim light to soft frontal fill.
Vance does not turn, does not move — only the illumination changes.

CRITICAL FOR SPINE: Face always 70%+ visible. No extreme shadows.
Eyes visible throughout. Maintain consistent facial features entire shot.

Cinematic, 4K, shallow depth of field.
Mood: Contemplative revelation, weight of knowledge emerging into clarity."""
    },
    {
        "id": "S11-01_v3",
        "scene": 11,
        "original_problem": "SPINE fail (0.66 borderline)",
        "fix": "Luz difusa, não harsh sun",
        "threshold": 0.70,
        "threshold_type": "aceitação elevado (adversarial)",
        "prompt": """Marcus Vance, 50s man with salt-pepper hair in loose ponytail, short grey beard,
weathered face with small red mark on left forehead, blue-grey eyes.
Dark wool coat with silver pin on lapel.

SCENE: Vance enters a tense confrontation space. Modern rooftop terrace, daylight.
Camera follows him entering frame from left, settling on medium close-up.
He surveys the scene with controlled intensity.

LIGHTING: Bright daylight but DIFFUSED — overcast sky, not harsh direct sun.
Avoid harsh shadows on face. Soft fill from environment.

CRITICAL FOR SPINE: Face must remain consistently lit throughout.
No dramatic shadow changes. Maintain 80%+ face visibility at all times.

Cinematic, 4K.
Mood: Controlled tension, predator entering territory.
Location: Modern rooftop terrace, generic modern city — no specific landmarks."""
    },
    {
        "id": "S14-01_v3",
        "scene": 14,
        "original_problem": "NYC skyline (jurisdição)",
        "fix": "Skyline universal, soft focus",
        "threshold": 0.75,
        "threshold_type": "FORENSIC (manter)",
        "prompt": """Marcus Vance, 50s man with salt-pepper hair in loose ponytail, short grey beard,
weathered face with small red mark on left forehead, blue-grey eyes.
Dark wool coat with silver pin on lapel.

SCENE: Vance stands at floor-to-ceiling window, looking out pensively.
Camera captures him in profile/three-quarter view against the cityscape.

VIEW THROUGH WINDOW: Generic modern city skyline at dusk.
Deliberately non-specific — NO recognizable landmarks.
Modern glass and steel buildings, could be any major city.
NOT American art-deco. No Empire State silhouettes. No obvious US markers.
Cool blue tones, STRONG SOFT FOCUS on skyline.

LIGHTING: Golden hour, warm light on Vance's face from window.
Cool blue tones on the city outside. Vance sharp, skyline deliberately blurred.

Cinematic, 4K, shallow depth of field — face sharp, city atmospheric.
Mood: Solitary reflection, weight of responsibility. Any-city, anywhere."""
    }
]

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")
    sys.stdout.flush()

def load_api_key():
    env_file = Path("/opt/windi/.env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("RUNWAY_API_KEY="):
                return line.strip().split("=", 1)[1]
    return os.environ.get("RUNWAY_API_KEY")

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
            log(f"  Response: {resp.text[:200]}")
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
                log(f"  Job FAILED: {result.get('failure', 'unknown reason')}")
                return None

            elapsed = int(time.time() - start)
            log(f"  Status: {status} ({elapsed}s)")
            time.sleep(10)
        except Exception as e:
            log(f"  Poll error: {e}")
            time.sleep(10)

    log(f"  TIMEOUT after {max_wait}s")
    return None

def download_video(result: dict, shot_id: str) -> Path:
    outputs = result.get("output", [])
    if not outputs:
        log(f"  No output in result")
        return None

    video_url = outputs[0]
    output_path = OUTPUT_DIR / f"{shot_id}.mp4"

    try:
        resp = requests.get(video_url, timeout=120)
        if resp.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            return output_path
        else:
            log(f"  Download failed: HTTP {resp.status_code}")
    except Exception as e:
        log(f"  Download error: {e}")
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

def evaluate_shot(shot: dict, measurements: list) -> dict:
    """Evaluate shot against its specific threshold."""
    sims = [m["similarity"] for m in measurements if m["similarity"] is not None]

    if not sims:
        return {
            "avg_similarity": None,
            "n_frames": len(measurements),
            "n_measured": 0,
            "threshold": shot["threshold"],
            "threshold_type": shot["threshold_type"],
            "passed": False,
            "verdict": "NO_FACES"
        }

    avg = sum(sims) / len(sims)
    passed = avg >= shot["threshold"]

    return {
        "avg_similarity": round(avg, 4),
        "n_frames": len(measurements),
        "n_measured": len(sims),
        "threshold": shot["threshold"],
        "threshold_type": shot["threshold_type"],
        "passed": passed,
        "verdict": "PASS" if passed else "FAIL",
        "margin": round(avg - shot["threshold"], 4)
    }

def main():
    log("=" * 70)
    log("RE-RENDER VANCE v3 — 3 Shots Corrigidos")
    log("Prompts v2 (07 Jun 2026) — Guardian + CCode")
    log("=" * 70)

    api_key = load_api_key()
    if not api_key:
        log("FATAL: No RUNWAY_API_KEY in /opt/windi/.env")
        return

    log(f"API Key: {api_key[:20]}...{api_key[-8:]}")

    # Check anchor exists
    if not ANCHOR_PATH.exists():
        log(f"FATAL: Anchor not found: {ANCHOR_PATH}")
        return

    # Load anchor image
    log("Loading anchor image...")
    image_data = load_anchor_base64()
    log(f"Anchor: {ANCHOR_PATH.name}")

    # Check/create anchor embedding
    if not ANCHOR_NPY.exists():
        log("Creating anchor embedding...")
        sys.path.insert(0, '/opt/windi/venv-poe/lib/python3.11/site-packages')
        import cv2
        from insightface.app import FaceAnalysis
        app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        app.prepare(ctx_id=0, det_size=(640, 640))

        img = cv2.imread(str(ANCHOR_PATH))
        faces = app.get(img)
        if faces:
            anchor_embed = faces[0].embedding
            np.save(ANCHOR_NPY, anchor_embed)
            log(f"Anchor embedding saved: {ANCHOR_NPY.name}")
        else:
            log("FATAL: No face in anchor image")
            return

    # Load ArcFace
    log("Loading ArcFace model...")
    sys.path.insert(0, '/opt/windi/venv-poe/lib/python3.11/site-packages')
    import cv2
    from insightface.app import FaceAnalysis
    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))

    anchor_embed = np.load(ANCHOR_NPY)
    log(f"Anchor embedding loaded: {anchor_embed.shape}")

    # Process re-renders
    all_results = []
    run_id = datetime.now().strftime("%Y%m%d%H%M%S")

    log("\n" + "=" * 70)
    log("THRESHOLDS DE ACEITAÇÃO (Decisão HD 07 Jun)")
    log("=" * 70)
    for shot in RERENDER_SHOTS:
        log(f"  {shot['id']}: ≥{shot['threshold']} ({shot['threshold_type']})")
    log("=" * 70 + "\n")

    for i, shot in enumerate(RERENDER_SHOTS):
        log(f"\n[{i+1}/3] {shot['id']}")
        log(f"  Original problem: {shot['original_problem']}")
        log(f"  Fix: {shot['fix']}")
        log(f"  Threshold: ≥{shot['threshold']} ({shot['threshold_type']})")

        # Submit
        log("  Submitting to Runway Gen-4...")
        task_id = submit_job(api_key, shot, image_data)
        if not task_id:
            all_results.append({
                "shot_id": shot["id"],
                "status": "SUBMIT_FAILED",
                "evaluation": {"passed": False, "verdict": "SUBMIT_FAILED"}
            })
            continue

        log(f"  Task: {task_id}")

        # Poll
        log("  Waiting for completion...")
        result = poll_job(api_key, task_id)
        if not result:
            all_results.append({
                "shot_id": shot["id"],
                "task_id": task_id,
                "status": "GENERATION_FAILED",
                "evaluation": {"passed": False, "verdict": "GENERATION_FAILED"}
            })
            continue

        # Download
        log("  Downloading video...")
        video_path = download_video(result, shot["id"])
        if not video_path:
            all_results.append({
                "shot_id": shot["id"],
                "task_id": task_id,
                "status": "DOWNLOAD_FAILED",
                "evaluation": {"passed": False, "verdict": "DOWNLOAD_FAILED"}
            })
            continue

        log(f"  Saved: {video_path.name}")

        # Extract frames
        log("  Extracting frames...")
        frames = extract_frames(video_path, shot["id"])
        log(f"  Extracted: {len(frames)} frames")

        # Measure
        log("  Measuring against anchor...")
        measurements = measure_frames(frames, anchor_embed, app)

        # Evaluate against shot-specific threshold
        evaluation = evaluate_shot(shot, measurements)

        emoji = "✅" if evaluation["passed"] else "❌"
        log(f"  Result: avg={evaluation['avg_similarity']}, threshold={shot['threshold']}")
        log(f"  {emoji} VERDICT: {evaluation['verdict']} (margin: {evaluation.get('margin', 'N/A')})")

        shot_result = {
            "shot_id": shot["id"],
            "scene": shot["scene"],
            "original_problem": shot["original_problem"],
            "fix": shot["fix"],
            "run_id": run_id,
            "task_id": task_id,
            "video": str(video_path),
            "measurements": measurements,
            "evaluation": evaluation
        }
        all_results.append(shot_result)

        # Rate limit
        time.sleep(2)

    # Final report
    log("\n" + "=" * 70)
    log("FINAL REPORT — RE-RENDER v3")
    log("=" * 70)

    passed = 0
    failed = 0

    for r in all_results:
        ev = r.get("evaluation", {})
        emoji = "✅" if ev.get("passed") else "❌"
        avg = ev.get("avg_similarity", "N/A")
        threshold = ev.get("threshold", "N/A")
        verdict = ev.get("verdict", "UNKNOWN")

        log(f"{emoji} {r['shot_id']}: {avg} vs ≥{threshold} → {verdict}")

        if ev.get("passed"):
            passed += 1
        else:
            failed += 1

    log("-" * 70)
    log(f"PASSED: {passed}/3")
    log(f"FAILED: {failed}/3")
    log("=" * 70)

    # Save manifest
    manifest = {
        "pipeline": "VANCE-RERENDER-V3",
        "run_id": run_id,
        "decision_date": "2026-06-07",
        "decision_by": "Human Dragon",
        "reviewed_by": "Guardian + CCode",
        "doctrine": "Universal na ficção ≠ ambíguo na forense",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "shots": [
            {"id": s["id"], "threshold": s["threshold"], "type": s["threshold_type"]}
            for s in RERENDER_SHOTS
        ],
        "results": all_results
    }

    manifest_path = OUTPUT_DIR / f"VANCE_V3_RERENDER_{run_id}.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    log(f"\nManifest: {manifest_path}")
    log("=" * 70)
    log("PIPELINE COMPLETE")
    log("=" * 70)

if __name__ == "__main__":
    main()
