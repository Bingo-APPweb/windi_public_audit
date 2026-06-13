#!/usr/bin/env python3
"""
GENERATE GABI-COZINHA v2 — Video-Native Re-generation
======================================================
Protocol: METHOD-HIOS-GENERATION-001
Pre-registro: WINDI-PREREGISTO-M2M3-20260613134915-f4b3b5f3

NATUREZA: Calibração + Correcção de Regime (NÃO validação Nv3)
- M1: Gate severo (PASS/FAIL)
- M2: Calibração (distribuição N vs N-1)
- M3: Calibração (005 vs 001, prova de regime)

Liga IA+H: Human Dragon (I9) + CCode (Architect)
Date: 13 Jun 2026
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
ANCHOR_PATH = Path("/opt/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/gabi.santos.anchor.v1.png")
ANCHOR_NPY = Path("/opt/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/gabi.santos.anchor.v1.embedding.npy")
OUTPUT_DIR = Path("/opt/windi/hios/cinema/produktion/gabi-cozinha/v2")

API_BASE = "https://api.dev.runwayml.com/v1"
API_VERSION = "2024-11-06"

# === FLOORS (from PRE-REGISTO) ===
FLOOR_GEOMETRIA = 0.65
FLOOR_EXPOSICAO = 0.55
THRESHOLD_FORENSE = 0.75

# === SHOTS TO GENERATE ===
# P1 = Âncora Frontal (GEOMETRIA)
# P3 = Sorriso Pousado (EXPOSIÇÃO)
# P5 = Erguer Telemóvel (GEOMETRIA)

SHOTS = [
    {
        "id": "P1_v2",
        "name": "Âncora Frontal",
        "floor": FLOOR_GEOMETRIA,
        "tier": "GEOMETRIA",
        "duration": 5,
        "prompt": """A 33-year-old Brazilian woman with warm olive skin and dark wavy hair
to her shoulders. She is already standing in a kitchen, near-frontal,
watching coffee drip into a ceramic cup. Expression tired but calm.
Eyes forward, neutral. Soft warm kitchen lighting from above.

She is barefoot. High heels placed beside the counter. A permanent
marker pen tucked securely behind her right ear, angled upward.
Phone on the table nearby, screen glowing faintly.

Camera locked. She is completely still. Only the light breathes.
Intimate, human, photorealistic. 50mm lens. Sharp focus on face."""
    },
    {
        "id": "P3_v2",
        "name": "Sorriso Pousado",
        "floor": FLOOR_EXPOSICAO,
        "tier": "EXPOSIÇÃO",
        "duration": 5,
        "prompt": """A 33-year-old Brazilian woman with warm olive skin and dark wavy hair
to her shoulders. She is already in a kitchen, near-frontal, holding
a ceramic coffee cup. Her expression is a genuine warm smile — full,
already formed, radiating maternal affection. Eyes bright with love.

Soft warm kitchen lighting from above. Subtle glow from phone screen
on table as fill light. The tiredness from before has vanished.

Camera locked. She is completely still. Only the light breathes.
Intimate, human, photorealistic. 50mm lens. Sharp focus on face."""
    },
    {
        "id": "P5_v2",
        "name": "Erguer Telemóvel",
        "floor": FLOOR_GEOMETRIA,
        "tier": "GEOMETRIA",
        "duration": 5,
        "prompt": """A 33-year-old Brazilian woman with warm olive skin and dark wavy hair
to her shoulders. She is already in a kitchen, near-frontal, holding
her phone at eye level. She looks at the phone screen with tender love.
Expression of gentle farewell — warm embrace energy.

The phone is raised to her face, not her face lowered to the phone.
Her posture remains upright, head toward lens. Soft warm kitchen
lighting from above. Phone screen adds subtle warm glow to her face.

Camera locked. She is completely still. Only the light breathes.
Intimate, human, photorealistic. 50mm lens. Sharp focus on face."""
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
        "duration": shot["duration"],
        "ratio": "1280:720"
    }
    log(f"  Prompt (first 100 chars): {shot['prompt'][:100]}...")
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


def download_video(result, shot_id, output_dir):
    outputs = result.get("output", [])
    if not outputs:
        return None
    output_path = output_dir / f"{shot_id}.mp4"
    resp = requests.get(outputs[0], timeout=120)
    if resp.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(resp.content)
        return output_path
    return None


def extract_frames(video_path, shot_id, output_dir):
    """Extract 5 keyframes from video."""
    frames_dir = output_dir / f"{shot_id}_frames"
    frames_dir.mkdir(exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", "fps=1", "-frames:v", "5",
        str(frames_dir / "frame_%02d.png")
    ], capture_output=True)
    return sorted(frames_dir.glob("frame_*.png"))


def get_embedding(app, img):
    """Extract embedding from image."""
    faces = app.get(img)
    if not faces:
        return None, None
    face = max(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]))
    emb = face.embedding / np.linalg.norm(face.embedding)
    return emb, face.det_score


def measure_m1(frames, anchor_embed, app, floor):
    """M1 — Identidade-Âncora (GATE SEVERO)."""
    import cv2
    measurements = []
    scores = []

    for frame_path in frames:
        img = cv2.imread(str(frame_path))
        emb, det = get_embedding(app, img)

        if emb is not None:
            sim = float(np.dot(anchor_embed.flatten(), emb))
            scores.append(sim)
            verdict = "FORENSE" if sim >= THRESHOLD_FORENSE else "PASS" if sim >= floor else "FAIL"
            measurements.append({
                "frame": frame_path.name,
                "sim": round(sim, 4),
                "det": round(det, 4) if det else None,
                "verdict": verdict
            })
            log(f"    M1 {frame_path.name}: {sim:.4f} [{verdict}]")
        else:
            measurements.append({
                "frame": frame_path.name,
                "sim": None,
                "verdict": "NO_FACE"
            })
            log(f"    M1 {frame_path.name}: NO_FACE")

    if scores:
        min_score = min(scores)
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        passed = min_score >= floor  # Mínimo severo

        return {
            "metric": "M1_identidade_ancora",
            "type": "GATE",
            "floor": floor,
            "min": round(min_score, 4),
            "avg": round(avg_score, 4),
            "max": round(max_score, 4),
            "passed": passed,
            "measurements": measurements
        }

    return {"metric": "M1", "type": "GATE", "passed": False, "error": "NO_FACES"}


def measure_m2(frames, app):
    """M2 — Continuidade-Vizinha (CALIBRAÇÃO)."""
    import cv2
    embeddings = []

    for frame_path in frames:
        img = cv2.imread(str(frame_path))
        emb, _ = get_embedding(app, img)
        embeddings.append((frame_path.name, emb))

    measurements = []
    scores = []

    for i in range(1, len(embeddings)):
        prev_name, prev_emb = embeddings[i-1]
        curr_name, curr_emb = embeddings[i]

        if prev_emb is not None and curr_emb is not None:
            sim = float(np.dot(prev_emb, curr_emb))
            scores.append(sim)
            measurements.append({
                "pair": f"{prev_name} -> {curr_name}",
                "sim": round(sim, 4)
            })
            log(f"    M2 {prev_name} -> {curr_name}: {sim:.4f}")
        else:
            measurements.append({
                "pair": f"{prev_name} -> {curr_name}",
                "sim": None,
                "error": "MISSING_FACE"
            })

    if scores:
        return {
            "metric": "M2_continuidade_vizinha",
            "type": "CALIBRATION",
            "note": "Expectativa: M2 > M1 (frames adjacentes mais parecidos)",
            "min": round(min(scores), 4),
            "avg": round(sum(scores) / len(scores), 4),
            "max": round(max(scores), 4),
            "measurements": measurements
        }

    return {"metric": "M2", "type": "CALIBRATION", "error": "INSUFFICIENT_DATA"}


def measure_m3(frames, app):
    """M3 — Reprodutibilidade (CALIBRAÇÃO + PROVA DE REGIME)."""
    import cv2

    if len(frames) < 2:
        return {"metric": "M3", "type": "CALIBRATION", "error": "NEED_2_FRAMES"}

    first_frame = frames[0]
    last_frame = frames[-1]

    img1 = cv2.imread(str(first_frame))
    img2 = cv2.imread(str(last_frame))

    emb1, _ = get_embedding(app, img1)
    emb2, _ = get_embedding(app, img2)

    if emb1 is not None and emb2 is not None:
        sim = float(np.dot(emb1, emb2))
        log(f"    M3 {first_frame.name} vs {last_frame.name}: {sim:.4f}")

        return {
            "metric": "M3_reprodutibilidade",
            "type": "CALIBRATION_REGIME_PROOF",
            "note": "Esperado ALTO (keyframes do mesmo vídeo). Se BAIXO → chaining falhou",
            "pair": f"{first_frame.name} vs {last_frame.name}",
            "sim": round(sim, 4),
            "regime_check": "VIDEO_NATIVE" if sim > 0.90 else "UNCERTAIN" if sim > 0.80 else "CHECK_CHAINING"
        }

    return {"metric": "M3", "type": "CALIBRATION", "error": "FACE_DETECTION_FAILED"}


def main():
    log("=" * 70)
    log("GABI-COZINHA v2 — Video-Native Re-generation")
    log("Protocol: METHOD-HIOS-GENERATION-001")
    log("Pre-registro: WINDI-PREREGISTO-M2M3-20260613134915-f4b3b5f3")
    log("Natureza: CALIBRAÇÃO + CORRECÇÃO DE REGIME (não validação Nv3)")
    log("=" * 70)

    api_key = load_api_key()
    if not api_key:
        log("FATAL: No API key in /opt/windi/.env")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    image_data = load_anchor_base64()
    log(f"Anchor: {ANCHOR_PATH.name}")

    # Load InsightFace
    sys.path.insert(0, '/opt/windi/venv-poe/lib/python3.11/site-packages')
    import cv2
    from insightface.app import FaceAnalysis
    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))
    anchor_embed = np.load(ANCHOR_NPY)
    log("ArcFace loaded\n")

    results = []
    run_id = datetime.now().strftime("%Y%m%d%H%M%S")

    total = len(SHOTS)
    for i, shot in enumerate(SHOTS):
        log(f"\n[{i+1}/{total}] {shot['id']} — {shot['name']}")
        log(f"  Tier: {shot['tier']} | Floor: {shot['floor']}")

        task_id = submit_job(api_key, shot, image_data)
        if not task_id:
            results.append({"shot": shot["id"], "status": "SUBMIT_FAILED"})
            continue

        log(f"  Task: {task_id}")
        result = poll_job(api_key, task_id)
        if not result:
            results.append({"shot": shot["id"], "status": "GENERATION_FAILED"})
            continue

        video_path = download_video(result, shot["id"], OUTPUT_DIR)
        if not video_path:
            results.append({"shot": shot["id"], "status": "DOWNLOAD_FAILED"})
            continue

        log(f"  Video: {video_path.name}")
        frames = extract_frames(video_path, shot["id"], OUTPUT_DIR)
        log(f"  Extracted {len(frames)} frames")

        # === THE 3 MEASUREMENTS ===
        log(f"\n  === MEASUREMENTS (M1 gate, M2/M3 calibration) ===")

        # M1 — Gate Severo
        m1 = measure_m1(frames, anchor_embed, app, shot["floor"])

        # M2 — Calibração
        m2 = measure_m2(frames, app)

        # M3 — Calibração + Prova de Regime
        m3 = measure_m3(frames, app)

        # Summary
        log(f"\n  === SUMMARY {shot['id']} ===")
        log(f"  M1 (GATE): {'PASS' if m1.get('passed') else 'FAIL'} | min={m1.get('min')} floor={shot['floor']}")
        log(f"  M2 (CALIB): avg={m2.get('avg')} | expectativa: > M1")
        log(f"  M3 (REGIME): sim={m3.get('sim')} | check={m3.get('regime_check')}")

        results.append({
            "shot": shot["id"],
            "name": shot["name"],
            "tier": shot["tier"],
            "floor": shot["floor"],
            "video": str(video_path),
            "frames_count": len(frames),
            "M1": m1,
            "M2": m2,
            "M3": m3,
            "overall_status": "M1_PASS" if m1.get("passed") else "M1_FAIL"
        })

        time.sleep(2)

    # === FINAL REPORT ===
    log("\n" + "=" * 70)
    log("FINAL REPORT — GABI-COZINHA v2 (Calibração + Correcção de Regime)")
    log("=" * 70)

    m1_passed = 0
    m2_values = []
    m3_values = []

    for r in results:
        if "M1" in r:
            status = "PASS" if r["M1"].get("passed") else "FAIL"
            if r["M1"].get("passed"):
                m1_passed += 1
            log(f"[{status}] {r['shot']} ({r['tier']}): M1={r['M1'].get('min')} floor={r['floor']}")

            if r["M2"].get("avg"):
                m2_values.append(r["M2"]["avg"])
            if r["M3"].get("sim"):
                m3_values.append(r["M3"]["sim"])
        else:
            log(f"[FAIL] {r['shot']}: {r.get('status', 'UNKNOWN')}")

    log(f"\nM1 Gate: {m1_passed}/{total} PASSED")

    if m2_values:
        log(f"M2 Calibration: avg={sum(m2_values)/len(m2_values):.4f} (across all shots)")
        log(f"  → Floor derivado para próxima run: {min(m2_values):.4f} (mínimo observado)")

    if m3_values:
        log(f"M3 Regime Proof: avg={sum(m3_values)/len(m3_values):.4f}")
        all_high = all(v > 0.90 for v in m3_values)
        log(f"  → Regime video-native: {'CONFIRMED' if all_high else 'NEEDS_REVIEW'}")

    # Save manifest
    manifest_path = OUTPUT_DIR / f"GABI_COZINHA_V2_{run_id}.json"
    with open(manifest_path, "w") as f:
        json.dump({
            "run_id": run_id,
            "protocol": "METHOD-HIOS-GENERATION-001",
            "pre_registro": "WINDI-PREREGISTO-M2M3-20260613134915-f4b3b5f3",
            "natureza": "CALIBRAÇÃO + CORRECÇÃO DE REGIME",
            "character": "Gabi Santos",
            "scene": "Cozinha",
            "results": results,
            "summary": {
                "M1_gate_passed": m1_passed,
                "M1_gate_total": total,
                "M2_calibration_avg": round(sum(m2_values)/len(m2_values), 4) if m2_values else None,
                "M2_floor_derivado": round(min(m2_values), 4) if m2_values else None,
                "M3_regime_avg": round(sum(m3_values)/len(m3_values), 4) if m3_values else None,
                "M3_regime_confirmed": all(v > 0.90 for v in m3_values) if m3_values else False
            },
            "conclusao_permitida": "regime corrigido; M1 gate; M2/M3 calibrados",
            "conclusao_proibida": "blocking validado (M2/M3 ainda não são gates)"
        }, f, indent=2)

    log(f"\nManifest: {manifest_path}")
    log("\n" + "=" * 70)
    log("NOTA: Esta é uma run de CALIBRAÇÃO, não validação Nv3.")
    log("Os frames devem ser revisados visualmente pelo Human Dragon.")
    log("=" * 70)


if __name__ == "__main__":
    main()
