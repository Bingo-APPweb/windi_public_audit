#!/usr/bin/env python3
"""
SPINE-CAST Scene Measurement Script
=====================================
W-HIOS FORENSIC UNIT · O Peso do Eco

Constitutional Bindings: I9, I11, I14, I19
Pre-flight: Declares both receipts before any measurement

Usage:
    .venv/bin/python measure_scene.py --scene 7 --frames /path/to/frames/

Requirements:
    - Run from: /home/windi/hios/visual/producer/hybrid-pipeline/
    - Uses: .venv with insightface 1.0.1
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

import numpy as np

# === LOCKED RECEIPTS (Pre-flight declaration) ===
THRESHOLD_RECEIPT = "WINDI-SPINE-THRESHOLD-20260604150425"
MODEL_LOCK_RECEIPT = "WINDI-SPINE-MODEL-LOCK-20260604173447"

# === LOCKED THRESHOLDS ===
THRESHOLD_FORENSE = 0.75
THRESHOLD_OPERACIONAL = 0.65
IDENTITY_FLOOR = 0.65

# === LOCKED MODEL ===
EXPECTED_MODEL = "buffalo_l"
EXPECTED_RECOGNITION = "w600k_r50.onnx"
EXPECTED_RECOGNITION_HASH = "4c06341c33c2ca1f86781dab0e829f88ad5b64be9fba56e56bc9ebdefc619e43"

# === ANCHOR PATHS ===
ANCHOR_DIR = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/anchors")

# Scene 7 cast
SCENE_7_CAST = ["marcus.vance", "helena.meyer.junior", "lucas.silva"]

# Scene 11 cast (adversarial)
SCENE_11_CAST = ["marcus.couto", "alejandro.valenzuela", "lucas.silva"]


def load_anchors(cast_list: list) -> dict:
    """Load anchor embeddings for specified cast."""
    anchors = {}
    for char in cast_list:
        npy_path = ANCHOR_DIR / f"{char}.anchor.v1.embedding.npy"
        if npy_path.exists():
            emb = np.load(npy_path)
            # Normalize
            emb = emb / np.linalg.norm(emb)
            anchors[char] = emb
        else:
            raise FileNotFoundError(f"Anchor not found: {npy_path}")
    return anchors


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two embeddings."""
    return float(np.dot(a, b))


def classify(score: float) -> str:
    """Classify score according to locked thresholds."""
    if score >= THRESHOLD_FORENSE:
        return "FORENSE"
    elif score >= THRESHOLD_OPERACIONAL:
        return "OPERACIONAL"
    else:
        return "REJECT"


def verify_model(app) -> bool:
    """Verify the loaded model matches the locked hashes."""
    import hashlib

    model_path = Path.home() / ".insightface/models/buffalo_l/w600k_r50.onnx"
    if not model_path.exists():
        print(f"ERROR: Recognition model not found at {model_path}")
        return False

    with open(model_path, "rb") as f:
        actual_hash = hashlib.sha256(f.read()).hexdigest()

    if actual_hash != EXPECTED_RECOGNITION_HASH:
        print(f"ERROR: Model hash mismatch!")
        print(f"  Expected: {EXPECTED_RECOGNITION_HASH}")
        print(f"  Actual:   {actual_hash}")
        return False

    return True


def preflight_check():
    """Mandatory pre-flight: declare receipts and verify model."""
    print("=" * 60)
    print("SPINE-CAST PRE-FLIGHT CHECK")
    print("=" * 60)
    print()
    print("RECEIPT DECLARATIONS (Gemini checklist):")
    print(f"  threshold_receipt: {THRESHOLD_RECEIPT}")
    print(f"  model_lock_receipt: {MODEL_LOCK_RECEIPT}")
    print()
    print("LOCKED THRESHOLDS:")
    print(f"  FORENSE:      >= {THRESHOLD_FORENSE}")
    print(f"  OPERACIONAL:  >= {THRESHOLD_OPERACIONAL}")
    print(f"  IDENTITY_FLOOR: {IDENTITY_FLOOR}")
    print()
    print("LOCKED MODEL:")
    print(f"  Pack: {EXPECTED_MODEL}")
    print(f"  Recognition: {EXPECTED_RECOGNITION}")
    print(f"  Hash: {EXPECTED_RECOGNITION_HASH[:16]}...")
    print()

    return True


def measure_frame(app, frame_path: Path, anchors: dict) -> dict:
    """Measure a single frame against all anchors."""
    import cv2

    img = cv2.imread(str(frame_path))
    if img is None:
        return {"error": f"Could not read image: {frame_path}"}

    faces = app.get(img)

    if len(faces) == 0:
        return {"error": "FAIL_NO_FACE", "frame": str(frame_path)}

    results = []
    for i, face in enumerate(faces):
        emb = face.embedding
        emb = emb / np.linalg.norm(emb)

        scores = {}
        for char, anchor in anchors.items():
            sim = cosine_similarity(emb, anchor)
            scores[char] = {
                "similarity": round(sim, 4),
                "classification": classify(sim)
            }

        # Attribution: assign to highest similarity if above floor
        best_char = max(scores.keys(), key=lambda c: scores[c]["similarity"])
        best_score = scores[best_char]["similarity"]

        if best_score >= IDENTITY_FLOOR:
            attribution = best_char
        else:
            attribution = "UNIDENTIFIED"

        results.append({
            "face_index": i,
            "attribution": attribution,
            "scores": scores,
            "det_score": round(float(face.det_score), 4)
        })

    return {
        "frame": str(frame_path),
        "faces_detected": len(faces),
        "results": results
    }


def main():
    parser = argparse.ArgumentParser(description="SPINE-CAST Scene Measurement")
    parser.add_argument("--scene", type=int, required=True, help="Scene number (7 or 11)")
    parser.add_argument("--frames", type=str, required=True, help="Path to frame images")
    parser.add_argument("--output", type=str, help="Output JSON path")
    args = parser.parse_args()

    # Pre-flight (mandatory)
    if not preflight_check():
        sys.exit(1)

    # Select cast
    if args.scene == 7:
        cast = SCENE_7_CAST
        scene_type = "PILOT"
    elif args.scene == 11:
        cast = SCENE_11_CAST
        scene_type = "ADVERSARIAL"
    else:
        print(f"ERROR: Scene {args.scene} not configured")
        sys.exit(1)

    print(f"SCENE {args.scene} ({scene_type})")
    print(f"  Cast: {', '.join(cast)}")
    print()

    # Load InsightFace
    print("Loading InsightFace...")
    from insightface.app import FaceAnalysis
    app = FaceAnalysis(name=EXPECTED_MODEL, providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))

    # Verify model
    print("Verifying model hash...")
    if not verify_model(app):
        print("ERROR: Model verification failed. Measurement rejected.")
        sys.exit(1)
    print("Model verified ✓")
    print()

    # Load anchors
    print("Loading anchors...")
    anchors = load_anchors(cast)
    print(f"  Loaded: {list(anchors.keys())}")
    print()

    # Find frames
    frame_dir = Path(args.frames)
    if not frame_dir.exists():
        print(f"ERROR: Frame directory not found: {frame_dir}")
        sys.exit(1)

    frames = sorted(frame_dir.glob("*.png")) + sorted(frame_dir.glob("*.jpg"))
    if not frames:
        print(f"ERROR: No frames found in {frame_dir}")
        sys.exit(1)

    print(f"Found {len(frames)} frames")
    print()
    print("=" * 60)
    print("MEASUREMENTS")
    print("=" * 60)

    # Measure
    measurements = []
    for frame_path in frames:
        result = measure_frame(app, frame_path, anchors)
        measurements.append(result)

        # Print summary
        if "error" in result:
            print(f"  {frame_path.name}: {result['error']}")
        else:
            for r in result["results"]:
                best = r["attribution"]
                best_score = r["scores"].get(best, {}).get("similarity", 0) if best != "UNIDENTIFIED" else 0
                classification = r["scores"].get(best, {}).get("classification", "N/A") if best != "UNIDENTIFIED" else "N/A"
                print(f"  {frame_path.name} face{r['face_index']}: {best} ({best_score:.4f}) [{classification}]")

    # Output
    output = {
        "scene": args.scene,
        "scene_type": scene_type,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "threshold_receipt": THRESHOLD_RECEIPT,
        "model_lock_receipt": MODEL_LOCK_RECEIPT,
        "thresholds": {
            "FORENSE": THRESHOLD_FORENSE,
            "OPERACIONAL": THRESHOLD_OPERACIONAL,
            "IDENTITY_FLOOR": IDENTITY_FLOOR
        },
        "model": {
            "pack": EXPECTED_MODEL,
            "recognition": EXPECTED_RECOGNITION,
            "recognition_hash": EXPECTED_RECOGNITION_HASH
        },
        "cast": cast,
        "frames_measured": len(frames),
        "measurements": measurements
    }

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    forense_count = 0
    operacional_count = 0
    reject_count = 0
    fail_no_face = 0

    for m in measurements:
        if "error" in m:
            if m["error"] == "FAIL_NO_FACE":
                fail_no_face += 1
            continue
        for r in m["results"]:
            if r["attribution"] != "UNIDENTIFIED":
                cls = r["scores"][r["attribution"]]["classification"]
                if cls == "FORENSE":
                    forense_count += 1
                elif cls == "OPERACIONAL":
                    operacional_count += 1
                else:
                    reject_count += 1

    print(f"  FORENSE:      {forense_count}")
    print(f"  OPERACIONAL:  {operacional_count}")
    print(f"  REJECT:       {reject_count}")
    print(f"  FAIL_NO_FACE: {fail_no_face}")

    # Save output
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(f"scene{args.scene}_measurement_{datetime.now().strftime('%Y%m%d%H%M%S')}.json")

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print()
    print(f"Output saved to: {output_path}")

    # Final verdict
    print()
    print("=" * 60)
    total = forense_count + operacional_count + reject_count
    if total > 0:
        forense_pct = forense_count / total * 100
        if forense_pct >= 80:
            print("VERDICT: FORENSE READY ✓")
        elif forense_pct >= 50:
            print("VERDICT: OPERACIONAL (some faces need review)")
        else:
            print("VERDICT: REVIEW REQUIRED (high reject rate)")
    else:
        print("VERDICT: NO FACES MEASURED")


if __name__ == "__main__":
    main()
