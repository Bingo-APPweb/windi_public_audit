#!/usr/bin/env python3
"""
JOEY-F2F-001 — Frame-to-Frame Continuity Measurement
======================================================
Testing Joey method: Does F2F cosine add value beyond anchor cosine?

Two questions (orthogonal):
- Anchor cosine: "Is this frame the character?" → IDENTITY
- F2F cosine: "Is this frame continuous with previous?" → CONTINUITY

Classification:
- STABLE: all f2f >= 0.90, no delta > 0.05
- MICRO-JITTER: f2f >= 0.80 but has delta > 0.05
- TEMPORAL-DRIFT: f2f between 0.60-0.80
- COLLAPSE: any f2f < 0.60

Liga IA+H · WINDI Publishing House · 09 Jun 2026
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

import numpy as np

sys.path.insert(0, '/opt/windi/venv-poe/lib/python3.11/site-packages')


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    return float(np.dot(a.flatten(), b.flatten()) / (
        np.linalg.norm(a) * np.linalg.norm(b)
    ))


class JoeyF2FMeasure:
    """
    Frame-to-Frame continuity measurement.
    Tests whether F2F metric reveals information anchor-cosine misses.
    """

    def __init__(self, anchor_embedding_path: str):
        self.anchor_embed = np.load(anchor_embedding_path)
        self._app = None

    @property
    def app(self):
        """Lazy load ArcFace model."""
        if self._app is None:
            from insightface.app import FaceAnalysis
            self._app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
            self._app.prepare(ctx_id=0, det_size=(640, 640))
        return self._app

    def extract_embedding(self, frame_path: Path) -> Tuple[np.ndarray, float]:
        """Extract face embedding from frame."""
        import cv2
        img = cv2.imread(str(frame_path))
        faces = self.app.get(img)

        if not faces:
            return None, 0.0

        face = max(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]))
        return face.embedding, float(face.det_score)

    def measure_shot_f2f(self, frames_dir: str, shot_id: str) -> Dict:
        """
        Measure both anchor-cosine and F2F-cosine for a shot.

        Returns dict with:
        - anchor_cosines: list of (frame vs anchor)
        - f2f_cosines: list of (frame[i] vs frame[i-1])
        - deltas: list of (f2f[i] - f2f[i-1])
        - worst_transition: (index, value)
        - classification: STABLE/MICRO-JITTER/TEMPORAL-DRIFT/COLLAPSE
        """
        frames_path = Path(frames_dir)
        frames = sorted(frames_path.glob("frame_*.png"))

        if not frames:
            return {"error": "NO_FRAMES_FOUND", "shot_id": shot_id}

        # Extract all embeddings
        embeddings = []
        det_scores = []
        for f in frames:
            emb, det = self.extract_embedding(f)
            embeddings.append(emb)
            det_scores.append(det)

        # Calculate anchor cosines
        anchor_cosines = []
        for i, emb in enumerate(embeddings):
            if emb is not None:
                sim = cosine_similarity(emb, self.anchor_embed)
                anchor_cosines.append({
                    "frame": frames[i].name,
                    "anchor_sim": round(sim, 4),
                    "det_score": round(det_scores[i], 4)
                })
            else:
                anchor_cosines.append({
                    "frame": frames[i].name,
                    "anchor_sim": None,
                    "det_score": None,
                    "error": "NO_FACE"
                })

        # Calculate F2F cosines (frame[i] vs frame[i-1])
        f2f_cosines = []
        f2f_deltas = []
        for i in range(1, len(embeddings)):
            if embeddings[i] is not None and embeddings[i-1] is not None:
                sim = cosine_similarity(embeddings[i], embeddings[i-1])
                f2f_cosines.append({
                    "transition": f"{frames[i-1].name} → {frames[i].name}",
                    "f2f_sim": round(sim, 4)
                })
            else:
                f2f_cosines.append({
                    "transition": f"{frames[i-1].name} → {frames[i].name}",
                    "f2f_sim": None,
                    "error": "MISSING_FACE"
                })

        # Calculate deltas between consecutive F2F values
        f2f_values = [x["f2f_sim"] for x in f2f_cosines if x["f2f_sim"] is not None]
        for i in range(1, len(f2f_values)):
            f2f_deltas.append(round(abs(f2f_values[i] - f2f_values[i-1]), 4))

        # Find worst transition
        valid_f2f = [(i, x["f2f_sim"]) for i, x in enumerate(f2f_cosines) if x["f2f_sim"] is not None]
        if valid_f2f:
            worst_idx, worst_val = min(valid_f2f, key=lambda x: x[1])
            worst_transition = {
                "index": worst_idx,
                "transition": f2f_cosines[worst_idx]["transition"],
                "f2f_sim": worst_val
            }
        else:
            worst_transition = None

        # Classify continuity
        if not f2f_values:
            classification = "NO_DATA"
        elif min(f2f_values) < 0.60:
            classification = "COLLAPSE"
        elif min(f2f_values) < 0.80:
            classification = "TEMPORAL-DRIFT"
        elif f2f_deltas and max(f2f_deltas) > 0.05:
            classification = "MICRO-JITTER"
        else:
            classification = "STABLE"

        # Calculate stats
        anchor_values = [x["anchor_sim"] for x in anchor_cosines if x["anchor_sim"] is not None]

        return {
            "shot_id": shot_id,
            "frames_dir": str(frames_path),
            "n_frames": len(frames),
            "anchor_cosines": anchor_cosines,
            "anchor_stats": {
                "avg": round(sum(anchor_values)/len(anchor_values), 4) if anchor_values else None,
                "min": round(min(anchor_values), 4) if anchor_values else None,
                "max": round(max(anchor_values), 4) if anchor_values else None,
                "range": round(max(anchor_values) - min(anchor_values), 4) if anchor_values else None
            },
            "f2f_cosines": f2f_cosines,
            "f2f_stats": {
                "avg": round(sum(f2f_values)/len(f2f_values), 4) if f2f_values else None,
                "min": round(min(f2f_values), 4) if f2f_values else None,
                "max": round(max(f2f_values), 4) if f2f_values else None,
                "range": round(max(f2f_values) - min(f2f_values), 4) if f2f_values else None
            },
            "f2f_deltas": f2f_deltas,
            "max_delta": max(f2f_deltas) if f2f_deltas else None,
            "worst_transition": worst_transition,
            "classification": classification,
            "timestamp": datetime.now().isoformat()
        }

    def print_report(self, result: Dict) -> None:
        """Print formatted F2F report."""
        print("")
        print("=" * 70)
        print(f"JOEY-F2F-001 MEASUREMENT REPORT — {result['shot_id']}")
        print("=" * 70)
        print(f"Frames: {result['n_frames']}")
        print("")

        # Anchor cosines
        print("ANCHOR COSINES (frame vs anchor):")
        print("-" * 50)
        for ac in result["anchor_cosines"]:
            if ac["anchor_sim"] is not None:
                print(f"  {ac['frame']}: {ac['anchor_sim']:.4f}")
            else:
                print(f"  {ac['frame']}: {ac.get('error', 'ERROR')}")
        print(f"  Stats: avg={result['anchor_stats']['avg']} min={result['anchor_stats']['min']} range={result['anchor_stats']['range']}")
        print("")

        # F2F cosines
        print("F2F COSINES (frame[i] vs frame[i-1]):")
        print("-" * 50)
        for f2f in result["f2f_cosines"]:
            if f2f["f2f_sim"] is not None:
                print(f"  {f2f['transition']}: {f2f['f2f_sim']:.4f}")
            else:
                print(f"  {f2f['transition']}: {f2f.get('error', 'ERROR')}")
        print(f"  Stats: avg={result['f2f_stats']['avg']} min={result['f2f_stats']['min']} range={result['f2f_stats']['range']}")
        print("")

        # Deltas
        if result["f2f_deltas"]:
            print(f"F2F DELTAS: {result['f2f_deltas']}")
            print(f"MAX DELTA: {result['max_delta']}")
            print("")

        # Worst transition
        if result["worst_transition"]:
            wt = result["worst_transition"]
            print(f"WORST TRANSITION: {wt['transition']} at {wt['f2f_sim']:.4f}")
            print("")

        # Classification
        emoji_map = {
            "STABLE": "STABLE",
            "MICRO-JITTER": "MICRO-JITTER",
            "TEMPORAL-DRIFT": "TEMPORAL-DRIFT",
            "COLLAPSE": "COLLAPSE"
        }
        print("=" * 70)
        print(f"CLASSIFICATION: [{result['classification']}]")
        print("=" * 70)
        print("")

    def save_result(self, result: Dict, output_path: str) -> None:
        """Save result to JSON."""
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2, default=str)


def run_joey_f2f(
    frames_dir: str,
    anchor_embedding: str,
    shot_id: str,
    save_json: bool = True
) -> Dict:
    """
    Run JOEY-F2F-001 measurement.
    """
    jf = JoeyF2FMeasure(anchor_embedding)
    result = jf.measure_shot_f2f(frames_dir, shot_id)
    jf.print_report(result)

    if save_json:
        json_path = Path(frames_dir).parent / f"{shot_id}_joey_f2f.json"
        jf.save_result(result, str(json_path))
        print(f"Saved: {json_path}")

    return result


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python joey_f2f_measure.py <frames_dir> <anchor.npy> <shot_id>")
        print("Example: python joey_f2f_measure.py S05-01_v1_frames/ helena.npy S05-01_v1")
        sys.exit(1)

    frames_dir = sys.argv[1]
    anchor = sys.argv[2]
    shot_id = sys.argv[3]

    run_joey_f2f(frames_dir, anchor, shot_id)
