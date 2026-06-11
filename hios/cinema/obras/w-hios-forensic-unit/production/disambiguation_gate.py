#!/usr/bin/env python3
"""
DISAMBIGUATION_GATE — Multi-Face Attribution Module
====================================================
WINDI-HIOS Phase 2: From Identity to Attribution

Fase 1 perguntava: "Este rosto é esta âncora?"
Fase 2 pergunta:   "Quem é quem dentro do mesmo espaço?"

Usage:
    from disambiguation_gate import DisambiguationGate

    gate = DisambiguationGate(
        anchor_a_path="anchors/alejandro.valenzuela.anchor.v1.embedding.npy",
        anchor_b_path="anchors/marcus.couto.anchor.v1.embedding.npy",
        anchor_a_name="Alejandro",
        anchor_b_name="Couto"
    )
    result = gate.measure_frame(frame_path)
    result = gate.measure_video(video_path, shot_id)

Liga IA+H · WINDI Publishing House · 10 Jun 2026
DOCTRINE-HIOS-ATTESTATION-001 (G-ATT-1..5) applies.
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

import numpy as np

# Ensure InsightFace is available
sys.path.insert(0, '/opt/windi/venv-poe/lib/python3.11/site-packages')


class DisambiguationGate:
    """
    Multi-face attribution gate for WINDI-HIOS Phase 2.

    Measures all faces in a frame against multiple anchors and
    attributes each face to the closest anchor.

    Gate PASSES when:
    - Each face matches its expected anchor above threshold
    - Each face does NOT match the other anchor (separation confirmed)
    - Attribution is unambiguous (clear winner for each face)
    """

    # Thresholds
    MATCH_THRESHOLD = 0.65      # Minimum similarity to claim match
    SEPARATION_THRESHOLD = 0.50 # Maximum similarity to non-match anchor
    AMBIGUITY_MARGIN = 0.15     # Minimum difference between best and second match

    def __init__(
        self,
        anchor_a_path: str,
        anchor_b_path: str,
        anchor_a_name: str = "Anchor_A",
        anchor_b_name: str = "Anchor_B"
    ):
        """
        Initialize with two anchor embeddings.

        Args:
            anchor_a_path: Path to first anchor .npy embedding
            anchor_b_path: Path to second anchor .npy embedding
            anchor_a_name: Human-readable name for anchor A
            anchor_b_name: Human-readable name for anchor B
        """
        self.anchor_a_embed = np.load(anchor_a_path)
        self.anchor_b_embed = np.load(anchor_b_path)
        self.anchor_a_name = anchor_a_name
        self.anchor_b_name = anchor_b_name

        # Calculate inter-anchor distance (should be < 0.50 for disambiguation to work)
        self.inter_anchor_sim = float(np.dot(
            self.anchor_a_embed.flatten(),
            self.anchor_b_embed.flatten()
        ) / (
            np.linalg.norm(self.anchor_a_embed) *
            np.linalg.norm(self.anchor_b_embed)
        ))

        # Lazy load ArcFace
        self._app = None

    @property
    def app(self):
        """Lazy load ArcFace model."""
        if self._app is None:
            import cv2
            from insightface.app import FaceAnalysis
            self._app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
            self._app.prepare(ctx_id=0, det_size=(640, 640))
        return self._app

    def cosine_similarity(self, embed_a: np.ndarray, embed_b: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings."""
        return float(np.dot(embed_a.flatten(), embed_b.flatten()) / (
            np.linalg.norm(embed_a) * np.linalg.norm(embed_b)
        ))

    def extract_frames(self, video_path: Path, output_dir: Path, num_frames: int = 5) -> List[Path]:
        """Extract frames from video."""
        output_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            "ffmpeg", "-y", "-i", str(video_path),
            "-vf", "fps=1", "-frames:v", str(num_frames),
            str(output_dir / "frame_%02d.png")
        ], capture_output=True)
        return sorted(output_dir.glob("frame_*.png"))

    def measure_frame(self, frame_path: Path) -> Dict:
        """
        Measure all faces in a single frame against both anchors.

        Returns:
            Dict with:
            - faces: list of face measurements with attribution
            - gate_status: PASS/FAIL/AMBIGUOUS
            - attribution_matrix: full similarity matrix
        """
        import cv2
        img = cv2.imread(str(frame_path))
        faces = self.app.get(img)

        if not faces:
            return {
                "frame": frame_path.name,
                "faces_detected": 0,
                "gate_status": "NO_FACES",
                "faces": [],
                "attribution_matrix": []
            }

        # Sort faces by size (largest first) and position (left to right)
        faces_sorted = sorted(faces, key=lambda x: -(x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]))

        face_measurements = []
        attribution_matrix = []

        for i, face in enumerate(faces_sorted):
            # Calculate similarity to both anchors
            sim_a = self.cosine_similarity(face.embedding, self.anchor_a_embed)
            sim_b = self.cosine_similarity(face.embedding, self.anchor_b_embed)

            # Determine attribution
            if sim_a > sim_b:
                attributed_to = self.anchor_a_name
                best_sim = sim_a
                other_sim = sim_b
            else:
                attributed_to = self.anchor_b_name
                best_sim = sim_b
                other_sim = sim_a

            margin = best_sim - other_sim

            # Calculate face position (for spatial reasoning)
            bbox = face.bbox.tolist()
            center_x = (bbox[0] + bbox[2]) / 2
            center_y = (bbox[1] + bbox[3]) / 2

            face_data = {
                "face_index": i,
                "position": {"center_x": round(center_x, 1), "center_y": round(center_y, 1)},
                "bbox": [round(b, 1) for b in bbox],
                "detection_score": round(float(face.det_score), 4),
                f"sim_{self.anchor_a_name}": round(sim_a, 4),
                f"sim_{self.anchor_b_name}": round(sim_b, 4),
                "attributed_to": attributed_to,
                "attribution_confidence": round(best_sim, 4),
                "separation_from_other": round(other_sim, 4),
                "margin": round(margin, 4)
            }

            face_measurements.append(face_data)
            attribution_matrix.append({
                "face": i,
                self.anchor_a_name: round(sim_a, 4),
                self.anchor_b_name: round(sim_b, 4)
            })

        # Determine gate status
        gate_status = self._evaluate_gate(face_measurements)

        return {
            "frame": frame_path.name,
            "faces_detected": len(faces),
            "gate_status": gate_status,
            "faces": face_measurements,
            "attribution_matrix": attribution_matrix
        }

    def _evaluate_gate(self, faces: List[Dict]) -> str:
        """
        Evaluate disambiguation gate status.

        PASS: All faces clearly attributed, no conflicts
        AMBIGUOUS: Attribution unclear (low margin)
        CONFLICT: Two faces attributed to same anchor
        FAIL: Matches below threshold
        """
        if not faces:
            return "NO_FACES"

        # Check for conflicts (two faces attributed to same anchor)
        attributions = [f["attributed_to"] for f in faces]
        if len(attributions) != len(set(attributions)) and len(faces) > 1:
            return "CONFLICT"

        # Check thresholds
        all_above_match = all(f["attribution_confidence"] >= self.MATCH_THRESHOLD for f in faces)
        all_below_separation = all(f["separation_from_other"] <= self.SEPARATION_THRESHOLD for f in faces)
        all_clear_margin = all(f["margin"] >= self.AMBIGUITY_MARGIN for f in faces)

        if not all_above_match:
            return "FAIL_MATCH"

        if not all_below_separation:
            return "FAIL_SEPARATION"

        if not all_clear_margin:
            return "AMBIGUOUS"

        return "PASS"

    def measure_video(
        self,
        video_path: str,
        shot_id: str,
        expected_faces: int = 2,
        frames_dir: Optional[str] = None
    ) -> Dict:
        """
        Complete measurement pipeline for a video with multiple faces.

        Args:
            video_path: Path to video file
            shot_id: Shot identifier
            expected_faces: Expected number of faces per frame
            frames_dir: Optional directory for frames

        Returns:
            Dict with complete measurement results
        """
        video_path = Path(video_path)
        if frames_dir:
            output_dir = Path(frames_dir)
        else:
            output_dir = video_path.parent / f"{video_path.stem}_disambiguation_frames"

        # Extract frames
        frames = self.extract_frames(video_path, output_dir)

        if not frames:
            return {
                "shot_id": shot_id,
                "error": "NO_FRAMES_EXTRACTED",
                "timestamp": datetime.utcnow().isoformat()
            }

        # Measure each frame
        frame_results = [self.measure_frame(f) for f in frames]

        # Aggregate statistics
        gate_statuses = [r["gate_status"] for r in frame_results]
        faces_per_frame = [r["faces_detected"] for r in frame_results]

        # Overall gate status
        if all(s == "PASS" for s in gate_statuses):
            overall_status = "PASS"
        elif "CONFLICT" in gate_statuses:
            overall_status = "CONFLICT"
        elif "FAIL_MATCH" in gate_statuses or "FAIL_SEPARATION" in gate_statuses:
            overall_status = "FAIL"
        elif "AMBIGUOUS" in gate_statuses:
            overall_status = "AMBIGUOUS"
        else:
            overall_status = "INCOMPLETE"

        # Calculate per-anchor statistics across all frames
        anchor_stats = self._calculate_anchor_stats(frame_results)

        result = {
            "shot_id": shot_id,
            "video_path": str(video_path),
            "frames_dir": str(output_dir),
            "n_frames": len(frames),
            "timestamp": datetime.utcnow().isoformat(),
            "inter_anchor_similarity": round(self.inter_anchor_sim, 4),
            "thresholds": {
                "match": self.MATCH_THRESHOLD,
                "separation": self.SEPARATION_THRESHOLD,
                "ambiguity_margin": self.AMBIGUITY_MARGIN
            },
            "anchors": {
                "A": self.anchor_a_name,
                "B": self.anchor_b_name
            },
            "summary": {
                "overall_gate": overall_status,
                "gate_per_frame": gate_statuses,
                "faces_per_frame": faces_per_frame,
                "expected_faces": expected_faces,
                "frames_with_expected_faces": sum(1 for f in faces_per_frame if f == expected_faces)
            },
            "anchor_statistics": anchor_stats,
            "frame_details": frame_results,
            "doctrine": "DOCTRINE-HIOS-ATTESTATION-001",
            "gate": "G-ATT-1 (number with measurement run)"
        }

        return result

    def _calculate_anchor_stats(self, frame_results: List[Dict]) -> Dict:
        """Calculate per-anchor statistics across all frames."""
        stats = {
            self.anchor_a_name: {"sims": [], "separations": []},
            self.anchor_b_name: {"sims": [], "separations": []}
        }

        for fr in frame_results:
            for face in fr.get("faces", []):
                attr = face["attributed_to"]
                stats[attr]["sims"].append(face["attribution_confidence"])
                stats[attr]["separations"].append(face["separation_from_other"])

        result = {}
        for anchor, data in stats.items():
            if data["sims"]:
                result[anchor] = {
                    "avg_confidence": round(sum(data["sims"]) / len(data["sims"]), 4),
                    "min_confidence": round(min(data["sims"]), 4),
                    "max_confidence": round(max(data["sims"]), 4),
                    "avg_separation": round(sum(data["separations"]) / len(data["separations"]), 4),
                    "n_attributions": len(data["sims"])
                }
            else:
                result[anchor] = {"n_attributions": 0}

        return result

    def print_report(self, result: Dict):
        """Print human-readable report."""
        print("\n" + "="*70)
        print(f"DISAMBIGUATION GATE REPORT — {result['shot_id']}")
        print("="*70)

        print(f"\nAnchors: {result['anchors']['A']} vs {result['anchors']['B']}")
        print(f"Inter-anchor similarity: {result['inter_anchor_similarity']}")
        print(f"  (< 0.50 required for disambiguation to work)")

        print(f"\nFrames measured: {result['n_frames']}")
        print(f"Expected faces per frame: {result['summary']['expected_faces']}")
        print(f"Frames with expected faces: {result['summary']['frames_with_expected_faces']}/{result['n_frames']}")

        print(f"\n{'OVERALL GATE STATUS:':20} {result['summary']['overall_gate']}")
        print(f"{'Per-frame:':20} {result['summary']['gate_per_frame']}")

        print("\nAnchor Statistics:")
        for anchor, stats in result['anchor_statistics'].items():
            if stats.get('n_attributions', 0) > 0:
                print(f"  {anchor}:")
                print(f"    Attributions: {stats['n_attributions']}")
                print(f"    Confidence:   {stats['avg_confidence']:.4f} (min: {stats['min_confidence']:.4f}, max: {stats['max_confidence']:.4f})")
                print(f"    Separation:   {stats['avg_separation']:.4f} (from other anchor)")

        print("\n" + "="*70)
        print(f"Doctrine: {result['doctrine']}")
        print(f"Gate applied: {result['gate']}")
        print("="*70 + "\n")


# CLI usage
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="WINDI-HIOS Disambiguation Gate")
    parser.add_argument("--video", required=True, help="Path to video file")
    parser.add_argument("--shot-id", required=True, help="Shot identifier")
    parser.add_argument("--anchor-a", required=True, help="Path to anchor A embedding (.npy)")
    parser.add_argument("--anchor-b", required=True, help="Path to anchor B embedding (.npy)")
    parser.add_argument("--name-a", default="Anchor_A", help="Name for anchor A")
    parser.add_argument("--name-b", default="Anchor_B", help="Name for anchor B")
    parser.add_argument("--expected-faces", type=int, default=2, help="Expected faces per frame")
    parser.add_argument("--output", help="Output JSON path")

    args = parser.parse_args()

    gate = DisambiguationGate(
        anchor_a_path=args.anchor_a,
        anchor_b_path=args.anchor_b,
        anchor_a_name=args.name_a,
        anchor_b_name=args.name_b
    )

    result = gate.measure_video(
        video_path=args.video,
        shot_id=args.shot_id,
        expected_faces=args.expected_faces
    )

    gate.print_report(result)

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Results saved to: {args.output}")
