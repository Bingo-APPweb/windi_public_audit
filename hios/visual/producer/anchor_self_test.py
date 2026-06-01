#!/usr/bin/env python3
"""
ANCHOR SELF-TEST — Measuring anchor self-consistency
=====================================================
Test B: Frontal frame vs Anchor (pose-matched comparison)
Test C: Varied poses vs Anchor (robustness measurement)

Runs on Server B (85.215.131.0) with InsightFace buffalo_l.

Usage:
    # Test B: Helena Frame 5 vs Helena Anchor
    python anchor_self_test.py --test-b \
        /path/to/helena_v2_test_frames/frame_05.png \
        /path/to/helena.anchor.v2.CURRENT.npy

    # Test C: Marcus all frames vs Marcus Anchor
    python anchor_self_test.py --test-c \
        /path/to/marcus_v2_test_frames/ \
        /path/to/marcus.anchor.v2.CURRENT.npy

Author: Liga IA+H · WINDI Publishing House
Date: 2026-06-01
Protocol: GPT Advisor Pre-Multi-Anchor Tests
"""

import argparse
import sys
from pathlib import Path
import numpy as np

try:
    import cv2
    from insightface.app import FaceAnalysis
    HAS_INSIGHTFACE = True
except ImportError:
    HAS_INSIGHTFACE = False
    print("WARNING: InsightFace not available. Run on Server B.")


# Thresholds (LOCKED)
THRESHOLD_OP = 0.65
THRESHOLD_FORENSE = 0.75


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two embeddings."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0.0 or nb == 0.0:
        raise ValueError("I14: embedding with zero norm")
    return float(np.dot(a, b) / (na * nb))


def classify(score: float) -> str:
    """Classify score into verdict."""
    if score >= THRESHOLD_FORENSE:
        return "FORENSIC"
    if score >= THRESHOLD_OP:
        return "OPERATIONAL"
    return "FAIL"


def extract_embedding(image_path: Path, app: "FaceAnalysis") -> np.ndarray:
    """Extract face embedding from image using InsightFace."""
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    faces = app.get(img)
    if not faces:
        raise ValueError(f"No face detected in: {image_path}")

    # Use largest face
    largest = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0]) * (f.bbox[3]-f.bbox[1]))
    return largest.normed_embedding


def load_anchor(anchor_path: Path) -> np.ndarray:
    """Load anchor embedding from .npy file."""
    emb = np.load(str(anchor_path))
    return emb


def init_face_app() -> "FaceAnalysis":
    """Initialize InsightFace with buffalo_l model."""
    app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=0, det_size=(640, 640))
    return app


def test_b(frame_path: Path, anchor_path: Path):
    """
    Test B: Single frontal frame vs Anchor.
    Pose-matched comparison to establish baseline.
    """
    print("=" * 60)
    print("TEST B — Frontal Frame vs Anchor")
    print("=" * 60)
    print(f"Frame:  {frame_path.name}")
    print(f"Anchor: {anchor_path.name}")
    print("-" * 60)

    if not HAS_INSIGHTFACE:
        print("ERROR: InsightFace not available. Run on Server B.")
        sys.exit(1)

    app = init_face_app()

    # Load anchor
    anchor_emb = load_anchor(anchor_path)
    print(f"Anchor shape: {anchor_emb.shape}")

    # Extract frame embedding
    frame_emb = extract_embedding(frame_path, app)
    print(f"Frame shape:  {frame_emb.shape}")

    # Calculate cosine
    score = cosine(frame_emb, anchor_emb)
    verdict = classify(score)

    print("-" * 60)
    print(f"COSINE:  {score:.4f}")
    print(f"VERDICT: {verdict}")
    print("=" * 60)

    return score, verdict


def test_c(frames_dir: Path, anchor_path: Path):
    """
    Test C: All frames (varied poses) vs Anchor.
    Measures robustness across pose variation.
    """
    print("=" * 60)
    print("TEST C — Varied Poses vs Anchor")
    print("=" * 60)
    print(f"Frames: {frames_dir}")
    print(f"Anchor: {anchor_path.name}")
    print("-" * 60)

    if not HAS_INSIGHTFACE:
        print("ERROR: InsightFace not available. Run on Server B.")
        sys.exit(1)

    app = init_face_app()

    # Load anchor
    anchor_emb = load_anchor(anchor_path)
    print(f"Anchor shape: {anchor_emb.shape}")

    # Find all frames
    frames = sorted(frames_dir.glob("frame_*.png"))
    if not frames:
        print(f"ERROR: No frames found in {frames_dir}")
        sys.exit(1)

    print(f"Found {len(frames)} frames")
    print("-" * 60)

    results = []
    for frame_path in frames:
        try:
            frame_emb = extract_embedding(frame_path, app)
            score = cosine(frame_emb, anchor_emb)
            verdict = classify(score)
            results.append((frame_path.name, score, verdict))
            print(f"  {frame_path.name}: {score:.4f} ({verdict})")
        except Exception as e:
            print(f"  {frame_path.name}: ERROR - {e}")
            results.append((frame_path.name, None, "ERROR"))

    # Statistics
    valid_scores = [r[1] for r in results if r[1] is not None]
    if valid_scores:
        mean_score = np.mean(valid_scores)
        min_score = np.min(valid_scores)
        max_score = np.max(valid_scores)

        print("-" * 60)
        print("STATISTICS:")
        print(f"  Mean:   {mean_score:.4f} ({classify(mean_score)})")
        print(f"  Min:    {min_score:.4f} ({classify(min_score)})")
        print(f"  Max:    {max_score:.4f} ({classify(max_score)})")
        print(f"  Range:  {max_score - min_score:.4f}")

    # Count verdicts
    n_forensic = sum(1 for r in results if r[2] == "FORENSIC")
    n_operational = sum(1 for r in results if r[2] == "OPERATIONAL")
    n_fail = sum(1 for r in results if r[2] == "FAIL")
    n_error = sum(1 for r in results if r[2] == "ERROR")

    print(f"\nVERDICT DISTRIBUTION:")
    print(f"  FORENSIC:    {n_forensic}/{len(results)}")
    print(f"  OPERATIONAL: {n_operational}/{len(results)}")
    print(f"  FAIL:        {n_fail}/{len(results)}")
    if n_error > 0:
        print(f"  ERROR:       {n_error}/{len(results)}")

    print("=" * 60)

    return results


def cross_frame_test(frames_dir: Path):
    """
    Cross-frame consistency test (frames against each other).
    This measures consistency independent of anchor.
    """
    print("=" * 60)
    print("CROSS-FRAME CONSISTENCY TEST")
    print("=" * 60)
    print(f"Frames: {frames_dir}")
    print("-" * 60)

    if not HAS_INSIGHTFACE:
        print("ERROR: InsightFace not available. Run on Server B.")
        sys.exit(1)

    app = init_face_app()

    # Find all frames
    frames = sorted(frames_dir.glob("frame_*.png"))
    if len(frames) < 2:
        print(f"ERROR: Need at least 2 frames, found {len(frames)}")
        sys.exit(1)

    print(f"Found {len(frames)} frames")
    print("-" * 60)

    # Extract all embeddings
    embeddings = {}
    for frame_path in frames:
        try:
            embeddings[frame_path.name] = extract_embedding(frame_path, app)
        except Exception as e:
            print(f"  {frame_path.name}: ERROR - {e}")

    if len(embeddings) < 2:
        print("ERROR: Not enough valid embeddings")
        sys.exit(1)

    # Calculate pairwise cosines
    names = sorted(embeddings.keys())
    scores = []

    print("PAIRWISE COSINES:")
    for i, n1 in enumerate(names):
        for n2 in names[i+1:]:
            score = cosine(embeddings[n1], embeddings[n2])
            scores.append(score)
            print(f"  {n1} vs {n2}: {score:.4f}")

    # Statistics
    mean_score = np.mean(scores)
    min_score = np.min(scores)
    max_score = np.max(scores)

    print("-" * 60)
    print("CROSS-FRAME STATISTICS:")
    print(f"  Mean:   {mean_score:.4f} ({classify(mean_score)})")
    print(f"  Min:    {min_score:.4f}")
    print(f"  Max:    {max_score:.4f}")
    print(f"  Range:  {max_score - min_score:.4f}")
    print("=" * 60)

    return scores


def main():
    parser = argparse.ArgumentParser(description="Anchor Self-Test")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--test-b", nargs=2, metavar=("FRAME", "ANCHOR"),
                       help="Test B: single frame vs anchor")
    group.add_argument("--test-c", nargs=2, metavar=("FRAMES_DIR", "ANCHOR"),
                       help="Test C: all frames vs anchor")
    group.add_argument("--cross", metavar="FRAMES_DIR",
                       help="Cross-frame consistency test")

    args = parser.parse_args()

    if args.test_b:
        frame_path = Path(args.test_b[0])
        anchor_path = Path(args.test_b[1])
        test_b(frame_path, anchor_path)

    elif args.test_c:
        frames_dir = Path(args.test_c[0])
        anchor_path = Path(args.test_c[1])
        test_c(frames_dir, anchor_path)

    elif args.cross:
        frames_dir = Path(args.cross)
        cross_frame_test(frames_dir)


if __name__ == "__main__":
    main()
