#!/usr/bin/env python3
"""
MEASURE COUTO MOVEMENT TEST — Frame-by-Frame Forensic
======================================================
Measure the movement test video against anchor.
No affirmations. Only numbers.

Liga IA+H: Human Dragon (I9) + CCode
Date: 09 Jun 2026
"""

import sys
import json
from pathlib import Path
from datetime import datetime

import numpy as np

ANCHOR_NPY = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/marcus.couto.anchor.v1.embedding.npy")
FRAMES_DIR = Path("/opt/windi/static/docs/hios-forensic/couto-anchor-review/movement-test-frames")
OUTPUT_DIR = Path("/opt/windi/static/docs/hios-forensic/couto-anchor-review")

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")
    sys.stdout.flush()

def main():
    log("=" * 60)
    log("MEASURE COUTO MOVEMENT TEST — Frame-by-Frame")
    log("=" * 60)

    # Load ArcFace
    sys.path.insert(0, '/opt/windi/venv-poe/lib/python3.11/site-packages')
    import cv2
    from insightface.app import FaceAnalysis

    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))

    anchor_embed = np.load(ANCHOR_NPY)
    log(f"Anchor embedding loaded: {ANCHOR_NPY.name}")
    log("")

    frames = sorted(FRAMES_DIR.glob("frame_*.png"))
    measurements = []

    for frame_path in frames:
        img = cv2.imread(str(frame_path))
        faces = app.get(img)

        if faces:
            face = max(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]))
            sim = float(np.dot(anchor_embed.flatten(), face.embedding) / (
                np.linalg.norm(anchor_embed) * np.linalg.norm(face.embedding)
            ))
            det_score = float(face.det_score)
            measurements.append({
                "frame": frame_path.name,
                "similarity": round(sim, 4),
                "detection_score": round(det_score, 4)
            })
            log(f"{frame_path.name}: sim={sim:.4f} det={det_score:.4f}")
        else:
            measurements.append({
                "frame": frame_path.name,
                "similarity": None,
                "detection_score": None,
                "error": "NO_FACE"
            })
            log(f"{frame_path.name}: NO_FACE")

    # Calculate stats
    sims = [m["similarity"] for m in measurements if m["similarity"] is not None]

    if sims:
        avg = sum(sims) / len(sims)
        min_sim = min(sims)
        max_sim = max(sims)

        log("")
        log("=" * 60)
        log("MEASUREMENT RESULTS — COUTO MOVEMENT TEST")
        log("=" * 60)
        log(f"Frames measured: {len(sims)}/5")
        log(f"Average similarity: {avg:.4f}")
        log(f"Min similarity: {min_sim:.4f}")
        log(f"Max similarity: {max_sim:.4f}")
        log(f"Range: {max_sim - min_sim:.4f}")
        log("")

        # Profile analysis
        profile = " -> ".join([f"{m['similarity']:.2f}" for m in measurements if m['similarity']])
        log(f"Profile: {profile}")

        # Verdicts
        log("")
        if min_sim >= 0.75:
            log("VERDICT: FORENSE (all frames >= 0.75)")
        elif min_sim >= 0.65:
            log("VERDICT: OPERATIONAL (all frames >= 0.65)")
        elif avg >= 0.65:
            log("VERDICT: MARGINAL (avg >= 0.65 but some frames below)")
        else:
            log("VERDICT: FAIL (identity not preserved)")

        # Collapse detection
        for i in range(1, len(sims)):
            if sims[i-1] > 0.7 and sims[i] < 0.5:
                log(f"WARNING: COLLAPSE at frame {i+1}: {sims[i-1]:.2f} -> {sims[i]:.2f}")

    # Save results
    result = {
        "test": "couto-movement-test",
        "timestamp": datetime.now().isoformat(),
        "anchor": str(ANCHOR_NPY),
        "measurements": measurements,
        "stats": {
            "frames_measured": len(sims),
            "avg_similarity": round(avg, 4) if sims else None,
            "min_similarity": round(min_sim, 4) if sims else None,
            "max_similarity": round(max_sim, 4) if sims else None
        }
    }

    output_path = OUTPUT_DIR / "movement-test-measurement.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    log(f"\nResults saved: {output_path}")

if __name__ == "__main__":
    main()
