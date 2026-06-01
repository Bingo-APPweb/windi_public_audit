#!/usr/bin/env python3
"""
SPINE ArcFace Validation — Vast.ai Job
=======================================

WINDI-HIOS Cinema · TEST-SPINE-001

Purpose: Validate identity preservation between Elisa anchor and SORA 2 generated frames.

Usage on Vast.ai:
    pip install insightface onnxruntime opencv-python numpy
    python3 spine_arcface_validate.py

Input:
    - frames/frame_01.png ... frame_05.png (SORA 2 output)
    - elisa.anchor.v2.CURRENT.npy (canonical embedding)

Output:
    - SPINE_VALIDATION_REPORT.json
    - Console summary with PASS/FAIL verdict

Thresholds:
    - 0.65 = Operational (identity preserved for production)
    - 0.75 = Forensic (identity confirmed for legal/audit)

Liga IA+H · WINDI Publishing House · 01 Jun 2026
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime

# Configuration
FRAMES_DIR = Path("frames")
ANCHOR_FILE = Path("elisa.anchor.v2.CURRENT.npy")
THRESHOLD_OPERATIONAL = 0.65
THRESHOLD_FORENSIC = 0.75

def load_arcface():
    """Load ArcFace model (buffalo_l)."""
    try:
        from insightface.app import FaceAnalysis
        print("Loading ArcFace model (buffalo_l)...")
        app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
        app.prepare(ctx_id=0, det_size=(640, 640))
        print("✅ ArcFace loaded")
        return app
    except ImportError:
        print("❌ insightface not installed")
        print("   pip install insightface onnxruntime opencv-python")
        sys.exit(1)


def load_anchor():
    """Load canonical Elisa embedding."""
    if not ANCHOR_FILE.exists():
        print(f"❌ Anchor not found: {ANCHOR_FILE}")
        sys.exit(1)

    anchor = np.load(ANCHOR_FILE)
    print(f"✅ Anchor loaded: {anchor.shape}")
    return anchor


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two embeddings."""
    a_flat = a.flatten()
    b_flat = b.flatten()
    return float(np.dot(a_flat, b_flat) / (np.linalg.norm(a_flat) * np.linalg.norm(b_flat)))


def validate_frames(app, anchor: np.ndarray) -> dict:
    """Validate all frames against anchor."""
    import cv2

    results = {
        "timestamp": datetime.now().isoformat(),
        "test_id": "TEST-SPINE-001",
        "anchor_file": str(ANCHOR_FILE),
        "thresholds": {
            "operational": THRESHOLD_OPERATIONAL,
            "forensic": THRESHOLD_FORENSIC
        },
        "frames": [],
        "summary": {}
    }

    frames = sorted(FRAMES_DIR.glob("frame_*.png"))

    if not frames:
        print(f"❌ No frames found in {FRAMES_DIR}")
        return results

    print(f"\n🔬 Validating {len(frames)} frames...")
    print("=" * 60)

    similarities = []

    for frame_path in frames:
        frame_result = {
            "file": frame_path.name,
            "face_detected": False,
            "similarity": None,
            "operational_pass": False,
            "forensic_pass": False
        }

        # Load frame
        img = cv2.imread(str(frame_path))
        if img is None:
            print(f"   {frame_path.name}: ❌ Could not load")
            results["frames"].append(frame_result)
            continue

        # Detect faces
        faces = app.get(img)

        if not faces:
            print(f"   {frame_path.name}: ⚠️  No face detected")
            results["frames"].append(frame_result)
            continue

        frame_result["face_detected"] = True

        # Get largest face
        face = max(faces, key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]))
        frame_embed = face.embedding

        # Calculate similarity
        sim = cosine_similarity(anchor, frame_embed)
        frame_result["similarity"] = round(sim, 4)
        frame_result["operational_pass"] = sim >= THRESHOLD_OPERATIONAL
        frame_result["forensic_pass"] = sim >= THRESHOLD_FORENSIC

        similarities.append(sim)

        # Status indicator
        if sim >= THRESHOLD_FORENSIC:
            status = "✅ FORENSIC"
        elif sim >= THRESHOLD_OPERATIONAL:
            status = "🟢 OPERATIONAL"
        else:
            status = "❌ FAIL"

        print(f"   {frame_path.name}: {sim:.4f} {status}")
        results["frames"].append(frame_result)

    # Summary
    print("=" * 60)

    if similarities:
        avg_sim = sum(similarities) / len(similarities)
        min_sim = min(similarities)
        max_sim = max(similarities)

        op_passes = sum(1 for s in similarities if s >= THRESHOLD_OPERATIONAL)
        forensic_passes = sum(1 for s in similarities if s >= THRESHOLD_FORENSIC)

        results["summary"] = {
            "total_frames": len(frames),
            "faces_detected": len(similarities),
            "average_similarity": round(avg_sim, 4),
            "min_similarity": round(min_sim, 4),
            "max_similarity": round(max_sim, 4),
            "operational_passes": op_passes,
            "forensic_passes": forensic_passes,
            "operational_rate": round(op_passes / len(similarities), 2) if similarities else 0,
            "forensic_rate": round(forensic_passes / len(similarities), 2) if similarities else 0
        }

        print(f"\n📊 SUMMARY")
        print(f"   Frames analyzed: {len(similarities)}/{len(frames)}")
        print(f"   Average similarity: {avg_sim:.4f}")
        print(f"   Range: [{min_sim:.4f} - {max_sim:.4f}]")
        print(f"   Operational passes: {op_passes}/{len(similarities)} ({results['summary']['operational_rate']*100:.0f}%)")
        print(f"   Forensic passes: {forensic_passes}/{len(similarities)} ({results['summary']['forensic_rate']*100:.0f}%)")

        # Final verdict
        print("\n" + "=" * 60)
        print("🎯 SPINE COMPATIBILITY VERDICT")
        print("=" * 60)

        if avg_sim >= THRESHOLD_FORENSIC and results["summary"]["forensic_rate"] >= 0.8:
            verdict = "FORENSIC_COMPATIBLE"
            print("🟢 SORA 2 × SPINE: FORENSIC COMPATIBLE")
            print("   Elisa identity preserved at forensic threshold")
            print("   Suitable for production AND verification")
        elif avg_sim >= THRESHOLD_OPERATIONAL and results["summary"]["operational_rate"] >= 0.6:
            verdict = "OPERATIONAL_COMPATIBLE"
            print("🟡 SORA 2 × SPINE: OPERATIONAL COMPATIBLE")
            print("   Elisa identity preserved at operational threshold")
            print("   Suitable for production, minor drift detected")
        else:
            verdict = "INCOMPATIBLE"
            print("🔴 SORA 2 × SPINE: INCOMPATIBLE")
            print("   Identity drift exceeds acceptable threshold")
            print("   Re-anchor or use different generator recommended")

        results["summary"]["verdict"] = verdict
    else:
        results["summary"]["verdict"] = "NO_FACES"
        print("🔴 No faces detected in any frame")

    return results


def main():
    print("=" * 60)
    print("SPINE ArcFace Validation — WINDI-HIOS Cinema")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Test ID: TEST-SPINE-001")
    print()

    # Load model
    app = load_arcface()

    # Load anchor
    anchor = load_anchor()

    # Validate
    results = validate_frames(app, anchor)

    # Save report
    report_path = Path("SPINE_VALIDATION_REPORT.json")
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n📄 Report saved: {report_path}")
    print("=" * 60)

    # Exit code based on verdict
    verdict = results.get("summary", {}).get("verdict", "UNKNOWN")
    if verdict == "FORENSIC_COMPATIBLE":
        sys.exit(0)
    elif verdict == "OPERATIONAL_COMPATIBLE":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
