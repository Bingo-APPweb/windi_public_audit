#!/usr/bin/env python3
"""
CALIBRATE MARGIN — Frame de Bancada para SHOT-GRAMMAR-003
==========================================================

Compõe dois CLOSEs selados lado a lado e mede a margem real de atribuição.
Este frame é instrumento de bancada — nunca entra no filme.

Par testado: Alejandro × Couto (inter-anchor 0.4498 — par mais apertado)

Liga IA+H: Human Dragon (I9) · Guardian (Witness) · CCode (Architect)
Date: 10 Jun 2026
"""

import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from PIL import Image

# Add insightface path
sys.path.insert(0, '/home/windi/.local/lib/python3.11/site-packages')

from insightface.app import FaceAnalysis

# === PATHS ===
BASE = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit")
OUTPUT_DIR = BASE / "production" / "calibration"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Best frames from sealed shots
ALEJANDRO_FRAME = BASE / "shots/alejandro/S10-01_v1_frames/frame_01.png"  # 0.9938
COUTO_FRAME = BASE / "shots/couto/S10-01_v2_frames/frame_01.png"          # 0.8738

# Anchors
ALEJANDRO_ANCHOR = BASE / "anchors/alejandro.valenzuela.anchor.v1.embedding.npy"
COUTO_ANCHOR = BASE / "anchors/marcus.couto.anchor.v1.embedding.npy"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def cosine_similarity(a, b):
    """Compute cosine similarity between two embeddings."""
    a = np.array(a).flatten()
    b = np.array(b).flatten()
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def compose_frames(left_path: Path, right_path: Path, output_path: Path) -> Image.Image:
    """Compose two frames side by side."""
    left = Image.open(left_path)
    right = Image.open(right_path)

    # Resize to same height
    target_height = min(left.height, right.height)
    left_ratio = target_height / left.height
    right_ratio = target_height / right.height

    left_resized = left.resize((int(left.width * left_ratio), target_height), Image.Resampling.LANCZOS)
    right_resized = right.resize((int(right.width * right_ratio), target_height), Image.Resampling.LANCZOS)

    # Compose side by side with 20px gap
    gap = 20
    total_width = left_resized.width + gap + right_resized.width
    composed = Image.new('RGB', (total_width, target_height), (0, 0, 0))
    composed.paste(left_resized, (0, 0))
    composed.paste(right_resized, (left_resized.width + gap, 0))

    composed.save(output_path)
    log(f"Composed frame saved: {output_path}")
    log(f"Dimensions: {total_width}x{target_height}")

    return composed

def main():
    log("=" * 70)
    log("MARGIN CALIBRATION — SHOT-GRAMMAR-003")
    log("=" * 70)
    log("Frame de bancada: dois CLOSEs selados lado a lado")
    log("Par: Alejandro × Couto (inter-anchor 0.4498)")
    log("=" * 70)

    # Step 1: Compose frames
    composed_path = OUTPUT_DIR / "calibration_frame_alejandro_couto.png"
    log("\n[STEP 1] Composing frames...")
    compose_frames(ALEJANDRO_FRAME, COUTO_FRAME, composed_path)

    # Step 2: Load anchors
    log("\n[STEP 2] Loading anchors...")
    alejandro_emb = np.load(ALEJANDRO_ANCHOR)
    couto_emb = np.load(COUTO_ANCHOR)

    # Verify inter-anchor similarity
    inter_anchor = cosine_similarity(alejandro_emb, couto_emb)
    log(f"Inter-anchor similarity: {inter_anchor:.4f}")
    log(f"Expected: ~0.4498")

    # Step 3: Initialize face detector
    log("\n[STEP 3] Initializing ArcFace...")
    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))

    # Step 4: Detect faces in composed frame
    log("\n[STEP 4] Detecting faces in composed frame...")
    composed_img = np.array(Image.open(composed_path).convert('RGB'))
    faces = app.get(composed_img)

    log(f"Faces detected: {len(faces)}")

    if len(faces) != 2:
        log(f"ERROR: Expected 2 faces, got {len(faces)}")
        return 1

    # Sort faces by x position (left to right)
    faces = sorted(faces, key=lambda f: f.bbox[0])

    # Step 5: Measure each face against both anchors
    log("\n[STEP 5] Measuring attribution...")

    results = []
    for i, face in enumerate(faces):
        position = "LEFT" if i == 0 else "RIGHT"
        emb = face.embedding

        sim_alejandro = cosine_similarity(emb, alejandro_emb)
        sim_couto = cosine_similarity(emb, couto_emb)

        # Attribution
        if sim_alejandro > sim_couto:
            attributed = "Alejandro"
            confidence = sim_alejandro
            separation = sim_couto
        else:
            attributed = "Couto"
            confidence = sim_couto
            separation = sim_alejandro

        margin = confidence - separation

        log(f"\n  {position} FACE (index {i}):")
        log(f"    Position: x={face.bbox[0]:.0f}")
        log(f"    sim_Alejandro: {sim_alejandro:.4f}")
        log(f"    sim_Couto:     {sim_couto:.4f}")
        log(f"    Attributed to: {attributed}")
        log(f"    Confidence:    {confidence:.4f}")
        log(f"    Separation:    {separation:.4f}")
        log(f"    MARGIN:        {margin:.4f}")

        results.append({
            "position": position,
            "face_index": i,
            "bbox_x": float(face.bbox[0]),
            "sim_alejandro": round(sim_alejandro, 4),
            "sim_couto": round(sim_couto, 4),
            "attributed_to": attributed,
            "confidence": round(confidence, 4),
            "separation": round(separation, 4),
            "margin": round(margin, 4)
        })

    # Step 6: Calculate aggregate margin
    margins = [r["margin"] for r in results]
    avg_margin = sum(margins) / len(margins)
    min_margin = min(margins)

    log("\n" + "=" * 70)
    log("CALIBRATION RESULTS")
    log("=" * 70)
    log(f"LEFT face:  Margin = {results[0]['margin']:.4f}")
    log(f"RIGHT face: Margin = {results[1]['margin']:.4f}")
    log(f"")
    log(f"Average Margin: {avg_margin:.4f}")
    log(f"Minimum Margin: {min_margin:.4f}")
    log(f"")
    log(f"PROVISIONAL value was: 0.15")
    log(f"MEASURED value is:     {min_margin:.4f}")
    log("=" * 70)

    # Step 7: Validate attribution
    left_expected = "Alejandro"  # Left frame was Alejandro
    right_expected = "Couto"     # Right frame was Couto

    left_correct = results[0]["attributed_to"] == left_expected
    right_correct = results[1]["attributed_to"] == right_expected

    log("\nATTRIBUTION VALIDATION:")
    log(f"  LEFT  (expected {left_expected}): {results[0]['attributed_to']} → {'✅ CORRECT' if left_correct else '❌ WRONG'}")
    log(f"  RIGHT (expected {right_expected}): {results[1]['attributed_to']} → {'✅ CORRECT' if right_correct else '❌ WRONG'}")

    gate_pass = left_correct and right_correct and min_margin > 0
    log(f"\nGATE STATUS: {'✅ PASS' if gate_pass else '❌ FAIL'}")

    # Step 8: Save results
    calibration_result = {
        "calibration_id": f"MARGIN-CAL-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "par_tested": "Alejandro × Couto",
        "inter_anchor_similarity": round(inter_anchor, 4),
        "source_frames": {
            "left": str(ALEJANDRO_FRAME),
            "right": str(COUTO_FRAME)
        },
        "composed_frame": str(composed_path),
        "faces_detected": len(faces),
        "results": results,
        "calibration": {
            "provisional_margin": 0.15,
            "measured_avg_margin": round(avg_margin, 4),
            "measured_min_margin": round(min_margin, 4),
            "recommended_threshold": round(min_margin * 0.8, 4),  # 80% of minimum as safety
            "gate_status": "PASS" if gate_pass else "FAIL",
            "attribution_correct": left_correct and right_correct
        },
        "doctrine": "SHOT-GRAMMAR-003",
        "gate": "G-SG3-4 (margin calibration)"
    }

    result_path = OUTPUT_DIR / "MARGIN-CALIBRATION-RESULT.json"
    with open(result_path, "w") as f:
        json.dump(calibration_result, f, indent=2)

    log(f"\nResults saved: {result_path}")

    # Summary for Memory Loop
    log("\n" + "=" * 70)
    log("RECOMMENDATION FOR SHOT-GRAMMAR-003")
    log("=" * 70)
    log(f"Replace MARGIN ≥0.15 (PROVISIONAL) with:")
    log(f"        MARGIN ≥{round(min_margin * 0.8, 2)} (MEASURED)")
    log(f"")
    log(f"Based on: {composed_path.name}")
    log(f"Par: Alejandro × Couto (inter-anchor {inter_anchor:.4f})")
    log("=" * 70)

    return 0

if __name__ == "__main__":
    sys.exit(main())
