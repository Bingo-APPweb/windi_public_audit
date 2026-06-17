#!/usr/bin/env python3
"""
SPINE-CAST Run Measurement — Gabi Cozinha
==========================================
Protocol: WINDI-PROTOCOLO-RUN-SPINE-GABI-001-20260613
Decisions: D2=Frame-a-frame, D3=α+β, D4=Mínimo-severo, D5=Blocking

Usage:
    source /opt/windi/hios/visual/producer/venv_spine/bin/activate
    python measure_spine_run.py --anchor /path/to/anchor.png --frames /path/to/frames/

Liga IA+H · WINDI Publishing House · 13 Jun 2026
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

import numpy as np

# Import insightface
try:
    from insightface.app import FaceAnalysis
except ImportError:
    print("ERROR: insightface not installed. Run: pip install insightface")
    sys.exit(1)

# === LOCKED THRESHOLDS (from SHOT-GRAMMAR-002) ===
FLOOR_GEOMETRIA = 0.65
FLOOR_EXPOSICAO = 0.55
FLOOR_OCLUSAO = 0.60
THRESHOLD_FORENSE = 0.75
THRESHOLD_OPERACIONAL = 0.65


def load_face_analyzer():
    """Initialize InsightFace analyzer."""
    app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=0, det_size=(640, 640))
    return app


def get_embedding(app, image_path: Path):
    """Extract face embedding from image."""
    import cv2
    img = cv2.imread(str(image_path))
    if img is None:
        return None, None, "IMAGE_LOAD_FAILED"

    faces = app.get(img)
    if not faces:
        return None, None, "NO_FACE_DETECTED"

    # Use the largest face (highest det_score typically)
    face = max(faces, key=lambda f: f.det_score)
    embedding = face.embedding / np.linalg.norm(face.embedding)

    return embedding, face.det_score, "OK"


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity."""
    return float(np.dot(a, b))


def classify_score(score: float, floor: float) -> str:
    """Classify based on floor."""
    if score >= THRESHOLD_FORENSE:
        return "FORENSE"
    elif score >= floor:
        return "PASS"
    else:
        return "FAIL"


def main():
    parser = argparse.ArgumentParser(description="SPINE-CAST Run Measurement")
    parser.add_argument("--anchor", required=True, help="Path to anchor image")
    parser.add_argument("--frames", required=True, help="Path to frames directory")
    parser.add_argument("--floor", type=float, default=0.65, help="Floor threshold")
    parser.add_argument("--output", help="Output JSON path")
    args = parser.parse_args()

    anchor_path = Path(args.anchor)
    frames_dir = Path(args.frames)
    floor = args.floor

    print("=" * 70)
    print("SPINE-CAST RUN MEASUREMENT")
    print("=" * 70)
    print(f"Anchor:    {anchor_path.name}")
    print(f"Frames:    {frames_dir}")
    print(f"Floor:     {floor}")
    print(f"Protocol:  WINDI-PROTOCOLO-RUN-SPINE-GABI-001-20260613")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("-" * 70)

    # Initialize
    print("\nLoading InsightFace (buffalo_l)...")
    app = load_face_analyzer()

    # Load anchor embedding
    print(f"Loading anchor: {anchor_path.name}...")
    anchor_emb, anchor_det, anchor_status = get_embedding(app, anchor_path)
    if anchor_emb is None:
        print(f"ERROR: Failed to load anchor: {anchor_status}")
        sys.exit(1)
    print(f"Anchor det_score: {anchor_det:.4f}")

    # Find all frames
    frame_files = sorted(frames_dir.glob("*.png"))
    if not frame_files:
        frame_files = sorted(frames_dir.glob("*.jpg"))

    if not frame_files:
        print(f"ERROR: No frames found in {frames_dir}")
        sys.exit(1)

    print(f"\nMeasuring {len(frame_files)} frames (frame-a-frame)...\n")

    results = []
    scores = []

    for frame_path in frame_files:
        emb, det, status = get_embedding(app, frame_path)

        if emb is None:
            result = {
                "frame": frame_path.name,
                "status": status,
                "score": None,
                "det_score": None,
                "verdict": "FAILED_ABANDONED"
            }
        else:
            score = cosine_similarity(anchor_emb, emb)
            scores.append(score)
            verdict = classify_score(score, floor)
            if score < floor:
                verdict = "FAILED_MISMATCH"

            result = {
                "frame": frame_path.name,
                "status": "OK",
                "score": round(score, 4),
                "det_score": round(det, 4),
                "verdict": verdict
            }

        results.append(result)
        status_icon = "✅" if result["verdict"] not in ["FAILED_MISMATCH", "FAILED_ABANDONED"] else "❌"
        score_str = f"{result['score']:.4f}" if result['score'] else "N/A"
        print(f"  {status_icon} {frame_path.name}: {score_str} [{result['verdict']}]")

    # Aggregate
    print("\n" + "=" * 70)
    print("AGGREGATION (Mínimo Severo)")
    print("=" * 70)

    if scores:
        min_score = min(scores)
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)

        # Decisão 4: Mínimo severo — 1 frame abaixo = FAIL
        final_verdict = "PASS" if min_score >= floor else "FAILED_MISMATCH"

        print(f"Frames measured: {len(scores)}/{len(frame_files)}")
        print(f"Min score:       {min_score:.4f}")
        print(f"Avg score:       {avg_score:.4f}")
        print(f"Max score:       {max_score:.4f}")
        print(f"Floor:           {floor}")
        print(f"FINAL VERDICT:   {final_verdict}")
    else:
        min_score = avg_score = max_score = None
        final_verdict = "FAILED_ABANDONED"
        print("ERROR: No valid measurements")

    print("=" * 70)

    # Output
    output_data = {
        "protocol": "WINDI-PROTOCOLO-RUN-SPINE-GABI-001-20260613",
        "timestamp": datetime.now().isoformat(),
        "anchor": str(anchor_path),
        "frames_dir": str(frames_dir),
        "floor": floor,
        "aggregation": "minimum_severe",
        "frames_total": len(frame_files),
        "frames_measured": len(scores),
        "min_score": min_score,
        "avg_score": round(avg_score, 4) if avg_score else None,
        "max_score": max_score,
        "final_verdict": final_verdict,
        "frame_results": results
    }

    if args.output:
        output_path = Path(args.output)
        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)
        print(f"\nResults saved to: {output_path}")

    # Return exit code based on verdict
    sys.exit(0 if final_verdict == "PASS" else 1)


if __name__ == "__main__":
    main()
