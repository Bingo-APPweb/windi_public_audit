#!/usr/bin/env python3
"""
§295 Render Validation — SPINE-CAST Gate
=========================================
Valida cenas renderizadas ANTES de selar no Ledger.

Para S14/S15: Validação manual (UI text check)
Para S16/S20: SPINE-CAST automático + validação manual

Uso:
    python3 validate_s295_render.py S16 /path/to/S16_render.mp4
    python3 validate_s295_render.py S20 /path/to/S20_render.mp4

Requer:
- Server B acessível via SSH (85.215.131.0)
- Âncoras em anchors/cast/
- ffmpeg para extração de frames

Liga IA+H · WINDI Publishing House · 30 Mai 2026
"""
import subprocess
import sys
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime

# Paths
ANCHORS_DIR = Path("/opt/windi/hios/cinema/obras/o-peso-do-eco/anchors/cast")
PRODUCTION_DIR = Path("/opt/windi/hios/cinema/obras/o-peso-do-eco/production")
SERVER_B = "windi@85.215.131.0"
SPINE_CAST_PATH = "/opt/windi/hios/visual/producer/hybrid-pipeline/b4"

# Thresholds (de spine.py)
THRESHOLD_OP = 0.65      # Operacional
THRESHOLD_FORENSE = 0.75 # Forense

# Cenas e requisitos
SCENE_REQUIREMENTS = {
    "S14": {
        "characters": [],
        "ui_checks": ["ÜBEREINSTIMMUNG GEFUNDEN", "Elisa Weber"],
        "spine_cast": False,
    },
    "S15": {
        "characters": [],
        "ui_checks": ["WINDI FORENSIC LEDGER", "INTEGRITÄT VERIFIZIERT 100%", "receipt", "hash"],
        "spine_cast": False,
    },
    "S16": {
        "characters": ["helena"],
        "ui_checks": ["dark sedan visible on monitor"],
        "continuity": ["navy coat", "blonde hair pulled back"],
        "spine_cast": True,
    },
    "S20": {
        "characters": ["helena"],
        "ui_checks": ["Integrität 100%", "courtroom display"],
        "continuity": ["navy coat", "dark oak", "DE flag", "Bavaria flag"],
        "spine_cast": True,
    },
}


def sha256_file(filepath: str) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def extract_frames(video_path: str, output_dir: str, fps: int = 1) -> list[str]:
    """Extract frames from video at specified fps."""
    os.makedirs(output_dir, exist_ok=True)
    pattern = os.path.join(output_dir, "frame_%03d.png")

    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"fps={fps}",
        "-y", pattern
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] ffmpeg failed: {result.stderr}")
        return []

    frames = sorted(Path(output_dir).glob("frame_*.png"))
    return [str(f) for f in frames]


def run_spine_cast_on_server_b(frame_path: str, anchor_name: str) -> dict:
    """
    Run SPINE-CAST validation on Server B.
    Returns dict with cosine score and verdict.
    """
    # Copy frame to Server B
    remote_frame = f"/tmp/validate_{os.path.basename(frame_path)}"
    scp_cmd = ["scp", "-q", frame_path, f"{SERVER_B}:{remote_frame}"]
    subprocess.run(scp_cmd, capture_output=True)

    # Get local anchor path
    anchor_path = ANCHORS_DIR / f"{anchor_name}.anchor.v1.CURRENT.npy"
    if not anchor_path.exists():
        return {"error": f"Anchor not found: {anchor_path}"}

    # Copy anchor to Server B
    remote_anchor = f"/tmp/validate_{anchor_name}_anchor.npy"
    scp_cmd = ["scp", "-q", str(anchor_path), f"{SERVER_B}:{remote_anchor}"]
    subprocess.run(scp_cmd, capture_output=True)

    # Run embedding + comparison on Server B
    remote_script = f"""
import sys
sys.path.insert(0, '{SPINE_CAST_PATH}')
import numpy as np
from spine import cosine, classify

# Load anchor
anchor = np.load('{remote_anchor}')

# Extract face embedding from frame using InsightFace
try:
    from insightface.app import FaceAnalysis
    app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
    app.prepare(ctx_id=0)

    import cv2
    img = cv2.imread('{remote_frame}')
    faces = app.get(img)

    if not faces:
        print('NO_FACE')
    else:
        # Get largest face
        largest = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
        emb = largest.embedding

        cos_score = cosine(emb, anchor)
        verdict = classify(cos_score)
        print(f'COSINE:{{cos_score:.4f}}')
        print(f'VERDICT:{{verdict.value}}')
except Exception as e:
    print(f'ERROR:{{e}}')
"""

    ssh_cmd = ["ssh", SERVER_B, f"python3 -c \"{remote_script}\""]
    result = subprocess.run(ssh_cmd, capture_output=True, text=True)

    # Parse output
    output = result.stdout.strip()
    if "NO_FACE" in output:
        return {"cosine": None, "verdict": "NO_FACE", "status": "FAIL"}
    elif "ERROR" in output:
        return {"error": output, "status": "FAIL"}
    else:
        lines = output.split('\n')
        cosine_val = None
        verdict = None
        for line in lines:
            if line.startswith("COSINE:"):
                cosine_val = float(line.split(":")[1])
            elif line.startswith("VERDICT:"):
                verdict = line.split(":")[1]

        if cosine_val is not None:
            status = "PASS" if cosine_val >= THRESHOLD_OP else "FAIL"
            return {"cosine": cosine_val, "verdict": verdict, "status": status}
        else:
            return {"error": "Could not parse output", "raw": output, "status": "FAIL"}


def validate_scene(scene_id: str, video_path: str) -> dict:
    """
    Validate a rendered scene against §295 requirements.
    Returns validation report dict.
    """
    if scene_id not in SCENE_REQUIREMENTS:
        return {"error": f"Unknown scene: {scene_id}"}

    reqs = SCENE_REQUIREMENTS[scene_id]
    report = {
        "scene": scene_id,
        "video": video_path,
        "video_hash": sha256_file(video_path),
        "timestamp": datetime.now().isoformat(),
        "checks": {},
        "spine_cast": {},
        "overall_status": "PENDING",
    }

    # Extract frames
    frames_dir = f"/tmp/s295_validate_{scene_id}"
    frames = extract_frames(video_path, frames_dir)
    report["frames_extracted"] = len(frames)

    if not frames:
        report["overall_status"] = "FAIL"
        report["error"] = "No frames extracted"
        return report

    # SPINE-CAST validation (for S16, S20)
    if reqs["spine_cast"] and reqs["characters"]:
        for char in reqs["characters"]:
            # Test middle frame for face validation
            middle_frame = frames[len(frames) // 2]
            result = run_spine_cast_on_server_b(middle_frame, char)
            report["spine_cast"][char] = result

    # Manual checks (logged but not automated)
    report["manual_checks_required"] = {
        "ui_checks": reqs.get("ui_checks", []),
        "continuity": reqs.get("continuity", []),
    }

    # Determine overall status
    if reqs["spine_cast"]:
        # Must pass SPINE-CAST for character scenes
        all_pass = all(
            r.get("status") == "PASS"
            for r in report["spine_cast"].values()
        )
        if all_pass:
            report["overall_status"] = "SPINE_CAST_PASS — Manual review required"
        else:
            report["overall_status"] = "FAIL — SPINE-CAST did not pass"
    else:
        report["overall_status"] = "UI_ONLY — Manual review required"

    return report


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 validate_s295_render.py <scene_id> <video_path>")
        print("       scene_id: S14, S15, S16, or S20")
        sys.exit(1)

    scene_id = sys.argv[1].upper()
    video_path = sys.argv[2]

    if not os.path.exists(video_path):
        print(f"[ERROR] Video not found: {video_path}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"§295 RENDER VALIDATION — {scene_id}")
    print(f"{'='*60}")
    print(f"Video: {video_path}")
    print(f"Hash: {sha256_file(video_path)[:16]}...")
    print()

    report = validate_scene(scene_id, video_path)

    # Print results
    print(f"Frames extracted: {report.get('frames_extracted', 0)}")
    print()

    if report.get("spine_cast"):
        print("SPINE-CAST Results:")
        for char, result in report["spine_cast"].items():
            if "cosine" in result and result["cosine"] is not None:
                print(f"  {char}: {result['cosine']:.4f} → {result['verdict']} ({result['status']})")
            else:
                print(f"  {char}: {result}")
        print()

    print(f"Manual checks required:")
    for check_type, checks in report.get("manual_checks_required", {}).items():
        if checks:
            print(f"  {check_type}:")
            for c in checks:
                print(f"    □ {c}")
    print()

    print(f"OVERALL STATUS: {report['overall_status']}")
    print(f"{'='*60}\n")

    # Save report
    report_path = PRODUCTION_DIR / f"validation_{scene_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"Report saved: {report_path}")

    # Exit code
    if "PASS" in report["overall_status"]:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
