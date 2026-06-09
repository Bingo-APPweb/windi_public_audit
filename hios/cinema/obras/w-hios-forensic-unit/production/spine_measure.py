#!/usr/bin/env python3
"""
SPINE_MEASURE — Canonical Measurement Module
=============================================
METHOD-001: Measure Before Affirm
No affirmations. Only numbers.

Usage:
    from spine_measure import SpineMeasure

    sm = SpineMeasure(anchor_embedding_path)
    result = sm.measure_video(video_path, shot_id, threshold)
    sm.print_report(result)

Liga IA+H · WINDI Publishing House · 09 Jun 2026
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


class SpineMeasure:
    """
    Canonical measurement class for WINDI-HIOS production.
    Implements METHOD-001: Measure Before Affirm.
    """

    def __init__(self, anchor_embedding_path: str):
        """
        Initialize with anchor embedding.

        Args:
            anchor_embedding_path: Path to .npy file with anchor embedding
        """
        self.anchor_path = Path(anchor_embedding_path)
        self.anchor_embed = np.load(self.anchor_path)

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

    def extract_frames(self, video_path: Path, output_dir: Path, num_frames: int = 5) -> List[Path]:
        """
        Extract frames from video.

        Args:
            video_path: Path to video file
            output_dir: Directory for extracted frames
            num_frames: Number of frames to extract

        Returns:
            List of frame paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            "ffmpeg", "-y", "-i", str(video_path),
            "-vf", "fps=1", "-frames:v", str(num_frames),
            str(output_dir / "frame_%02d.png")
        ], capture_output=True)
        return sorted(output_dir.glob("frame_*.png"))

    def measure_frame(self, frame_path: Path) -> Dict:
        """
        Measure single frame against anchor.

        Args:
            frame_path: Path to frame image

        Returns:
            Dict with similarity, detection_score, or error
        """
        import cv2
        img = cv2.imread(str(frame_path))
        faces = self.app.get(img)

        if not faces:
            return {
                "frame": frame_path.name,
                "similarity": None,
                "detection_score": None,
                "error": "NO_FACE"
            }

        # Get largest face
        face = max(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]))

        # Calculate cosine similarity
        sim = float(np.dot(self.anchor_embed.flatten(), face.embedding) / (
            np.linalg.norm(self.anchor_embed) * np.linalg.norm(face.embedding)
        ))

        return {
            "frame": frame_path.name,
            "similarity": round(sim, 4),
            "detection_score": round(float(face.det_score), 4)
        }

    def measure_frames(self, frames: List[Path]) -> List[Dict]:
        """
        Measure multiple frames.

        Args:
            frames: List of frame paths

        Returns:
            List of measurement dicts
        """
        return [self.measure_frame(f) for f in frames]

    def calculate_stats(self, measurements: List[Dict]) -> Dict:
        """
        Calculate statistics from measurements.

        Args:
            measurements: List of measurement dicts

        Returns:
            Dict with avg, min, max, profile, verdict
        """
        sims = [m["similarity"] for m in measurements if m["similarity"] is not None]

        if not sims:
            return {
                "frames_measured": 0,
                "avg": None,
                "min": None,
                "max": None,
                "profile": [],
                "verdict": "NO_FACES"
            }

        avg = sum(sims) / len(sims)
        min_sim = min(sims)
        max_sim = max(sims)

        # Determine verdict
        if min_sim >= 0.75:
            verdict = "FORENSE"
        elif min_sim >= 0.65:
            verdict = "OPERATIONAL"
        elif avg >= 0.65:
            verdict = "MARGINAL"
        else:
            verdict = "FAIL"

        # Detect collapse
        collapses = []
        for i in range(1, len(sims)):
            if sims[i-1] > 0.7 and sims[i] < 0.5:
                collapses.append({
                    "at_frame": i + 1,
                    "from": sims[i-1],
                    "to": sims[i]
                })

        return {
            "frames_measured": len(sims),
            "avg": round(avg, 4),
            "min": round(min_sim, 4),
            "max": round(max_sim, 4),
            "range": round(max_sim - min_sim, 4),
            "profile": sims,
            "verdict": verdict,
            "collapses": collapses
        }

    def measure_video(
        self,
        video_path: str,
        shot_id: str,
        threshold: float,
        frames_dir: Optional[str] = None
    ) -> Dict:
        """
        Complete measurement pipeline for a video.
        METHOD-001: Generate → Extract → Measure → Report (atomic)

        Args:
            video_path: Path to video file
            shot_id: Shot identifier (e.g., "S02-01_v1")
            threshold: Required threshold for this shot
            frames_dir: Optional directory for frames (auto-generated if None)

        Returns:
            Complete result dict with all measurements and verdict
        """
        video_path = Path(video_path)

        if frames_dir is None:
            frames_dir = video_path.parent / f"{shot_id}_frames"
        else:
            frames_dir = Path(frames_dir)

        # Extract frames
        frames = self.extract_frames(video_path, frames_dir)

        # Measure all frames
        measurements = self.measure_frames(frames)

        # Calculate stats
        stats = self.calculate_stats(measurements)

        # Determine pass/fail against threshold
        passed = stats["min"] is not None and stats["min"] >= threshold
        margin = round(stats["min"] - threshold, 4) if stats["min"] else None

        return {
            "shot_id": shot_id,
            "video": str(video_path),
            "anchor": str(self.anchor_path),
            "threshold": threshold,
            "measurements": measurements,
            "stats": stats,
            "passed": passed,
            "margin": margin,
            "timestamp": datetime.now().isoformat()
        }

    def print_report(self, result: Dict) -> None:
        """
        Print formatted measurement report.
        No affirmations. Only numbers.

        Args:
            result: Result dict from measure_video
        """
        stats = result["stats"]
        print("")
        print("=" * 60)
        print(f"MEASUREMENT REPORT — {result['shot_id']}")
        print("=" * 60)
        print(f"Video: {Path(result['video']).name}")
        print(f"Anchor: {Path(result['anchor']).name}")
        print(f"Threshold: >= {result['threshold']}")
        print("")

        # Frame-by-frame
        print("Frame-by-Frame:")
        print("-" * 40)
        for m in result["measurements"]:
            if m["similarity"] is not None:
                print(f"  {m['frame']}: sim={m['similarity']:.4f} det={m['detection_score']:.4f}")
            else:
                print(f"  {m['frame']}: {m.get('error', 'ERROR')}")
        print("")

        # Stats
        print("Statistics:")
        print("-" * 40)
        print(f"  Frames measured: {stats['frames_measured']}/5")
        print(f"  Average: {stats['avg']}")
        print(f"  Min: {stats['min']}")
        print(f"  Max: {stats['max']}")
        print(f"  Range: {stats['range']}")
        print("")

        # Profile
        if stats["profile"]:
            profile_str = " → ".join([f"{s:.2f}" for s in stats["profile"]])
            print(f"Profile: {profile_str}")
            print("")

        # Collapses
        if stats["collapses"]:
            print("WARNINGS:")
            for c in stats["collapses"]:
                print(f"  COLLAPSE at frame {c['at_frame']}: {c['from']:.2f} → {c['to']:.2f}")
            print("")

        # Verdict
        emoji = "PASS" if result["passed"] else "FAIL"
        print(f"[{emoji}] VERDICT: {stats['verdict']}")
        print(f"         min={stats['min']} vs threshold={result['threshold']} (margin: {result['margin']:+.4f})")
        print("=" * 60)

    def save_result(self, result: Dict, output_path: str) -> None:
        """
        Save result to JSON file.

        Args:
            result: Result dict
            output_path: Path for JSON output
        """
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2, default=str)


def measure_and_report(
    video_path: str,
    anchor_embedding: str,
    shot_id: str,
    threshold: float,
    save_json: bool = True
) -> Dict:
    """
    Convenience function for one-shot measurement.
    METHOD-001 compliant: measure and report atomically.

    Args:
        video_path: Path to video
        anchor_embedding: Path to anchor .npy
        shot_id: Shot identifier
        threshold: Required threshold
        save_json: Whether to save JSON result

    Returns:
        Complete result dict
    """
    sm = SpineMeasure(anchor_embedding)
    result = sm.measure_video(video_path, shot_id, threshold)
    sm.print_report(result)

    if save_json:
        json_path = Path(video_path).parent / f"{shot_id}_measurement.json"
        sm.save_result(result, str(json_path))

    return result


# === CLI ===
if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python spine_measure.py <video> <anchor.npy> <shot_id> <threshold>")
        print("Example: python spine_measure.py S02-01_v1.mp4 anchor.npy S02-01_v1 0.75")
        sys.exit(1)

    video = sys.argv[1]
    anchor = sys.argv[2]
    shot_id = sys.argv[3]
    threshold = float(sys.argv[4])

    result = measure_and_report(video, anchor, shot_id, threshold)
    sys.exit(0 if result["passed"] else 1)
