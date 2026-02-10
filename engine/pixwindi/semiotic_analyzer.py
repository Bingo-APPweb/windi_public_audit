"""
WINDI PixWindi — Semiotic Analyzer
===================================
Calligraphy vector extraction and semiotic signature generation.

Extracts:
- Stroke curvature patterns
- Simulated pressure distribution
- Writing velocity indicators
- Spatial rhythm metrics

Generates a unique "Semiotic Signature" that binds the
handwriting trace to a WINDI Identity.

"Each hand writes its own story in the geometry of strokes."
"""

import hashlib
import math
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime, timezone


@dataclass
class CalligraphyVector:
    """
    Vector representation of calligraphy characteristics.

    These features capture the unique "fingerprint" of handwriting
    that AI-generated text cannot replicate authentically.
    """
    # Curvature metrics
    avg_curvature: float          # Average stroke curvature
    curvature_variance: float     # Variation in curvature
    curvature_histogram: List[int]  # Distribution of curvature values

    # Pressure metrics (simulated from stroke width)
    avg_pressure: float           # Average simulated pressure
    pressure_variance: float      # Variation in pressure
    pressure_pattern: str         # "consistent", "variable", "rhythmic"

    # Velocity metrics (from stroke spacing/density)
    avg_velocity: float           # Average writing speed indicator
    velocity_variance: float      # Speed variation
    acceleration_events: int      # Number of acceleration changes

    # Spatial metrics
    line_spacing_avg: float       # Average spacing between lines
    word_spacing_avg: float       # Average spacing between words
    letter_spacing_avg: float     # Average spacing between letters
    baseline_deviation: float     # Deviation from horizontal baseline

    # Rhythm metrics
    stroke_rhythm_score: float    # Regularity of stroke rhythm
    spatial_rhythm_score: float   # Regularity of spatial distribution

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SemioticSignature:
    """
    Unique signature binding handwriting to WINDI Identity.

    This is the cryptographic link between the physical act of
    writing and the digital governance record.
    """
    signature_hash: str           # Primary signature hash
    calligraphy_hash: str         # Hash of calligraphy vectors
    spatial_hash: str             # Hash of spatial patterns
    timestamp: str                # Analysis timestamp
    confidence: float             # Confidence in signature validity
    bound_identity: Optional[str]  # WINDI Identity if linked

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SemioticAnalyzer:
    """
    Analyzes handwritten documents for semiotic features.

    The semiotic analysis captures the "meaning-making" aspects
    of handwriting that go beyond simple shape recognition:

    1. HOW was it written (speed, pressure, rhythm)
    2. WHAT spatial relationships exist (letter, word, line)
    3. WHERE does the writer deviate from norms

    These features are deeply personal and extremely difficult
    to forge or generate synthetically.
    """

    # Configuration
    MIN_STROKE_LENGTH = 5
    CURVATURE_BINS = 10
    PRESSURE_SMOOTHING = 3

    def __init__(self):
        """Initialize analyzer."""
        pass

    def analyze(
        self,
        binary_image: List[List[int]],
        grayscale_image: Optional[List[List[int]]] = None
    ) -> CalligraphyVector:
        """
        Extract calligraphy vectors from processed image.

        Args:
            binary_image: Binary mask (0=ink, 255=background)
            grayscale_image: Optional grayscale for pressure analysis

        Returns:
            CalligraphyVector with extracted features
        """
        # Extract strokes
        strokes = self._extract_strokes(binary_image)

        # Analyze curvature
        curvature_metrics = self._analyze_curvature(strokes)

        # Analyze pressure (from stroke width or grayscale)
        pressure_metrics = self._analyze_pressure(
            strokes, binary_image, grayscale_image
        )

        # Analyze velocity (from stroke characteristics)
        velocity_metrics = self._analyze_velocity(strokes)

        # Analyze spatial relationships
        spatial_metrics = self._analyze_spatial(binary_image, strokes)

        # Analyze rhythm
        rhythm_metrics = self._analyze_rhythm(strokes, spatial_metrics)

        return CalligraphyVector(
            avg_curvature=curvature_metrics["avg"],
            curvature_variance=curvature_metrics["variance"],
            curvature_histogram=curvature_metrics["histogram"],
            avg_pressure=pressure_metrics["avg"],
            pressure_variance=pressure_metrics["variance"],
            pressure_pattern=pressure_metrics["pattern"],
            avg_velocity=velocity_metrics["avg"],
            velocity_variance=velocity_metrics["variance"],
            acceleration_events=velocity_metrics["acceleration_events"],
            line_spacing_avg=spatial_metrics["line_spacing"],
            word_spacing_avg=spatial_metrics["word_spacing"],
            letter_spacing_avg=spatial_metrics["letter_spacing"],
            baseline_deviation=spatial_metrics["baseline_deviation"],
            stroke_rhythm_score=rhythm_metrics["stroke"],
            spatial_rhythm_score=rhythm_metrics["spatial"]
        )

    def generate_signature(
        self,
        calligraphy_vector: CalligraphyVector,
        windi_identity: Optional[str] = None
    ) -> SemioticSignature:
        """
        Generate semiotic signature from calligraphy vector.

        The signature uniquely identifies this handwriting sample
        and can be cryptographically bound to a WINDI Identity.
        """
        # Hash calligraphy features
        calligraphy_data = str(sorted(calligraphy_vector.to_dict().items()))
        calligraphy_hash = hashlib.sha256(calligraphy_data.encode()).hexdigest()[:24]

        # Hash spatial features separately
        spatial_data = {
            "line_spacing": calligraphy_vector.line_spacing_avg,
            "word_spacing": calligraphy_vector.word_spacing_avg,
            "letter_spacing": calligraphy_vector.letter_spacing_avg,
            "baseline_deviation": calligraphy_vector.baseline_deviation
        }
        spatial_hash = hashlib.sha256(
            str(sorted(spatial_data.items())).encode()
        ).hexdigest()[:24]

        # Combine for primary signature
        timestamp = datetime.now(timezone.utc).isoformat()

        combined = f"{calligraphy_hash}:{spatial_hash}:{timestamp}"
        if windi_identity:
            combined += f":{windi_identity}"

        signature_hash = hashlib.sha256(combined.encode()).hexdigest()

        # Calculate confidence
        confidence = self._calculate_signature_confidence(calligraphy_vector)

        return SemioticSignature(
            signature_hash=signature_hash,
            calligraphy_hash=calligraphy_hash,
            spatial_hash=spatial_hash,
            timestamp=timestamp,
            confidence=confidence,
            bound_identity=windi_identity
        )

    def _extract_strokes(
        self,
        binary_image: List[List[int]]
    ) -> List[List[Tuple[int, int]]]:
        """
        Extract individual strokes from binary image.

        Returns list of strokes, where each stroke is a list of (x, y) points.
        """
        height = len(binary_image)
        width = len(binary_image[0]) if height > 0 else 0

        if height < 10 or width < 10:
            return []

        # Find connected components (simplified flood fill approach)
        visited = [[False] * width for _ in range(height)]
        strokes = []

        for y in range(height):
            for x in range(width):
                if binary_image[y][x] == 0 and not visited[y][x]:
                    # Start new stroke
                    stroke = []
                    stack = [(x, y)]

                    while stack:
                        cx, cy = stack.pop()

                        if (0 <= cy < height and 0 <= cx < width and
                            not visited[cy][cx] and binary_image[cy][cx] == 0):

                            visited[cy][cx] = True
                            stroke.append((cx, cy))

                            # Add neighbors
                            for dy in [-1, 0, 1]:
                                for dx in [-1, 0, 1]:
                                    if dy != 0 or dx != 0:
                                        stack.append((cx + dx, cy + dy))

                    if len(stroke) >= self.MIN_STROKE_LENGTH:
                        strokes.append(stroke)

        return strokes

    def _analyze_curvature(
        self,
        strokes: List[List[Tuple[int, int]]]
    ) -> Dict[str, Any]:
        """Analyze curvature characteristics of strokes."""
        if not strokes:
            return {
                "avg": 0.0,
                "variance": 0.0,
                "histogram": [0] * self.CURVATURE_BINS
            }

        all_curvatures = []

        for stroke in strokes:
            if len(stroke) < 3:
                continue

            # Sort stroke points to get ordered path
            ordered = self._order_stroke_points(stroke)

            # Calculate curvature at each point
            for i in range(1, len(ordered) - 1):
                p1 = ordered[i - 1]
                p2 = ordered[i]
                p3 = ordered[i + 1]

                curvature = self._point_curvature(p1, p2, p3)
                all_curvatures.append(curvature)

        if not all_curvatures:
            return {
                "avg": 0.0,
                "variance": 0.0,
                "histogram": [0] * self.CURVATURE_BINS
            }

        avg = sum(all_curvatures) / len(all_curvatures)
        variance = sum((c - avg) ** 2 for c in all_curvatures) / len(all_curvatures)

        # Build histogram
        max_curv = max(all_curvatures) if all_curvatures else 1.0
        histogram = [0] * self.CURVATURE_BINS
        for c in all_curvatures:
            bin_idx = min(self.CURVATURE_BINS - 1, int(c / max_curv * (self.CURVATURE_BINS - 1)))
            histogram[bin_idx] += 1

        return {
            "avg": avg,
            "variance": variance,
            "histogram": histogram
        }

    def _order_stroke_points(
        self,
        stroke: List[Tuple[int, int]]
    ) -> List[Tuple[int, int]]:
        """Order stroke points to form a continuous path."""
        if len(stroke) <= 2:
            return stroke

        # Simple approach: sort by proximity starting from leftmost point
        ordered = []
        remaining = set(stroke)

        # Start with leftmost point
        current = min(remaining, key=lambda p: p[0])
        ordered.append(current)
        remaining.remove(current)

        while remaining:
            # Find closest unvisited point
            closest = min(remaining, key=lambda p:
                (p[0] - current[0]) ** 2 + (p[1] - current[1]) ** 2
            )
            ordered.append(closest)
            remaining.remove(closest)
            current = closest

        return ordered

    def _point_curvature(
        self,
        p1: Tuple[int, int],
        p2: Tuple[int, int],
        p3: Tuple[int, int]
    ) -> float:
        """
        Calculate curvature at p2 given three consecutive points.

        Uses the Menger curvature formula: k = 4A / (|p1-p2| * |p2-p3| * |p1-p3|)
        where A is the area of the triangle.
        """
        # Calculate distances
        d12 = ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2) ** 0.5
        d23 = ((p3[0] - p2[0]) ** 2 + (p3[1] - p2[1]) ** 2) ** 0.5
        d13 = ((p3[0] - p1[0]) ** 2 + (p3[1] - p1[1]) ** 2) ** 0.5

        # Calculate area using cross product
        area = abs(
            (p2[0] - p1[0]) * (p3[1] - p1[1]) -
            (p3[0] - p1[0]) * (p2[1] - p1[1])
        ) / 2.0

        # Calculate curvature
        denom = d12 * d23 * d13
        if denom < 1e-10:
            return 0.0

        return 4 * area / denom

    def _analyze_pressure(
        self,
        strokes: List[List[Tuple[int, int]]],
        binary_image: List[List[int]],
        grayscale_image: Optional[List[List[int]]]
    ) -> Dict[str, Any]:
        """
        Analyze pressure characteristics.

        Pressure is inferred from:
        1. Stroke width (wider = more pressure)
        2. Grayscale intensity (darker = more pressure)
        """
        pressures = []

        for stroke in strokes:
            # Estimate pressure from stroke width at each point
            for x, y in stroke:
                width = self._estimate_stroke_width(binary_image, x, y)
                pressures.append(width)

        if not pressures:
            return {
                "avg": 0.0,
                "variance": 0.0,
                "pattern": "unknown"
            }

        avg = sum(pressures) / len(pressures)
        variance = sum((p - avg) ** 2 for p in pressures) / len(pressures)

        # Determine pattern
        coef_variation = (variance ** 0.5) / avg if avg > 0 else 0

        if coef_variation < 0.2:
            pattern = "consistent"
        elif coef_variation > 0.5:
            pattern = "variable"
        else:
            pattern = "rhythmic"

        return {
            "avg": avg,
            "variance": variance,
            "pattern": pattern
        }

    def _estimate_stroke_width(
        self,
        binary_image: List[List[int]],
        x: int,
        y: int
    ) -> float:
        """Estimate stroke width at a given point."""
        height = len(binary_image)
        width_img = len(binary_image[0])

        # Count ink pixels in horizontal and vertical directions
        h_count = 0
        v_count = 0

        # Horizontal
        for dx in range(-20, 21):
            nx = x + dx
            if 0 <= nx < width_img and binary_image[y][nx] == 0:
                h_count += 1
            elif h_count > 0:
                break

        # Vertical
        for dy in range(-20, 21):
            ny = y + dy
            if 0 <= ny < height and binary_image[ny][x] == 0:
                v_count += 1
            elif v_count > 0:
                break

        return min(h_count, v_count)

    def _analyze_velocity(
        self,
        strokes: List[List[Tuple[int, int]]]
    ) -> Dict[str, Any]:
        """
        Analyze velocity characteristics.

        Velocity is inferred from stroke density and spacing.
        Fast writing tends to have more spacing between points.
        """
        velocities = []
        acceleration_events = 0

        for stroke in strokes:
            ordered = self._order_stroke_points(stroke)

            prev_velocity = None
            for i in range(1, len(ordered)):
                p1 = ordered[i - 1]
                p2 = ordered[i]

                # Distance represents "velocity" (higher = faster movement)
                dist = ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2) ** 0.5
                velocities.append(dist)

                # Check for acceleration
                if prev_velocity is not None:
                    if abs(dist - prev_velocity) > 2:
                        acceleration_events += 1

                prev_velocity = dist

        if not velocities:
            return {
                "avg": 0.0,
                "variance": 0.0,
                "acceleration_events": 0
            }

        avg = sum(velocities) / len(velocities)
        variance = sum((v - avg) ** 2 for v in velocities) / len(velocities)

        return {
            "avg": avg,
            "variance": variance,
            "acceleration_events": acceleration_events
        }

    def _analyze_spatial(
        self,
        binary_image: List[List[int]],
        strokes: List[List[Tuple[int, int]]]
    ) -> Dict[str, Any]:
        """Analyze spatial relationships in the handwriting."""
        height = len(binary_image)
        width = len(binary_image[0])

        # Calculate horizontal projection for line detection
        h_projection = [sum(1 for p in row if p == 0) for row in binary_image]

        # Find text lines (peaks in projection)
        lines = self._find_text_lines(h_projection)

        # Calculate metrics
        line_spacing = self._calculate_line_spacing(lines)
        word_spacing = self._estimate_word_spacing(binary_image)
        letter_spacing = self._estimate_letter_spacing(strokes)
        baseline_deviation = self._calculate_baseline_deviation(strokes, lines)

        return {
            "line_spacing": line_spacing,
            "word_spacing": word_spacing,
            "letter_spacing": letter_spacing,
            "baseline_deviation": baseline_deviation
        }

    def _find_text_lines(
        self,
        h_projection: List[int]
    ) -> List[int]:
        """Find y-coordinates of text lines from horizontal projection."""
        if not h_projection:
            return []

        threshold = max(h_projection) * 0.3
        lines = []
        in_line = False
        line_start = 0

        for y, count in enumerate(h_projection):
            if count > threshold and not in_line:
                in_line = True
                line_start = y
            elif count <= threshold and in_line:
                in_line = False
                lines.append((line_start + y) // 2)  # Center of line

        return lines

    def _calculate_line_spacing(self, lines: List[int]) -> float:
        """Calculate average spacing between text lines."""
        if len(lines) < 2:
            return 0.0

        spacings = [lines[i + 1] - lines[i] for i in range(len(lines) - 1)]
        return sum(spacings) / len(spacings)

    def _estimate_word_spacing(self, binary_image: List[List[int]]) -> float:
        """Estimate average word spacing from vertical projection gaps."""
        height = len(binary_image)
        width = len(binary_image[0])

        # Vertical projection
        v_projection = [
            sum(1 for row in binary_image if row[x] == 0)
            for x in range(width)
        ]

        # Find gaps (potential word boundaries)
        threshold = max(v_projection) * 0.1 if v_projection else 0
        gaps = []
        in_gap = False
        gap_start = 0

        for x, count in enumerate(v_projection):
            if count <= threshold and not in_gap:
                in_gap = True
                gap_start = x
            elif count > threshold and in_gap:
                in_gap = False
                gap_width = x - gap_start
                if gap_width > 10:  # Minimum gap for word boundary
                    gaps.append(gap_width)

        return sum(gaps) / len(gaps) if gaps else 0.0

    def _estimate_letter_spacing(
        self,
        strokes: List[List[Tuple[int, int]]]
    ) -> float:
        """Estimate average letter spacing from stroke positions."""
        if len(strokes) < 2:
            return 0.0

        # Get bounding boxes of strokes
        boxes = []
        for stroke in strokes:
            if stroke:
                xs = [p[0] for p in stroke]
                boxes.append((min(xs), max(xs)))

        # Sort by x position
        boxes.sort(key=lambda b: b[0])

        # Calculate gaps between consecutive strokes
        gaps = []
        for i in range(len(boxes) - 1):
            gap = boxes[i + 1][0] - boxes[i][1]
            if 0 < gap < 50:  # Reasonable letter gap
                gaps.append(gap)

        return sum(gaps) / len(gaps) if gaps else 0.0

    def _calculate_baseline_deviation(
        self,
        strokes: List[List[Tuple[int, int]]],
        lines: List[int]
    ) -> float:
        """Calculate how much writing deviates from horizontal baseline."""
        if not strokes or not lines:
            return 0.0

        # Find bottom of each stroke
        bottoms = []
        for stroke in strokes:
            if stroke:
                bottom_y = max(p[1] for p in stroke)
                bottoms.append(bottom_y)

        if not bottoms:
            return 0.0

        # Fit line through bottoms
        n = len(bottoms)
        xs = list(range(n))
        ys = bottoms

        # Simple linear regression
        mean_x = sum(xs) / n
        mean_y = sum(ys) / n

        numerator = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
        denominator = sum((xs[i] - mean_x) ** 2 for i in range(n))

        slope = numerator / denominator if denominator > 0 else 0

        # Slope represents baseline deviation (ideally 0 for horizontal)
        return abs(slope)

    def _analyze_rhythm(
        self,
        strokes: List[List[Tuple[int, int]]],
        spatial_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze rhythm characteristics of handwriting."""
        # Stroke rhythm: regularity of stroke sizes
        stroke_sizes = [len(s) for s in strokes]
        stroke_rhythm = 0.0

        if stroke_sizes:
            avg_size = sum(stroke_sizes) / len(stroke_sizes)
            variance = sum((s - avg_size) ** 2 for s in stroke_sizes) / len(stroke_sizes)
            coef_variation = (variance ** 0.5) / avg_size if avg_size > 0 else 1

            # Lower variation = more rhythmic
            stroke_rhythm = max(0, 1 - coef_variation)

        # Spatial rhythm: regularity of spacing
        spacings = [
            spatial_metrics.get("line_spacing", 0),
            spatial_metrics.get("word_spacing", 0),
            spatial_metrics.get("letter_spacing", 0)
        ]

        avg_spacing = sum(spacings) / len(spacings) if spacings else 0
        spacing_variance = sum((s - avg_spacing) ** 2 for s in spacings) / len(spacings) if spacings else 0

        spatial_rhythm = max(0, 1 - (spacing_variance ** 0.5) / (avg_spacing + 1))

        return {
            "stroke": stroke_rhythm,
            "spatial": spatial_rhythm
        }

    def _calculate_signature_confidence(
        self,
        vector: CalligraphyVector
    ) -> float:
        """Calculate confidence in the semiotic signature."""
        confidence = 0.5  # Base confidence

        # Higher variance = more distinctive = higher confidence
        if vector.curvature_variance > 0.01:
            confidence += 0.1

        # Consistent pressure pattern = higher confidence
        if vector.pressure_pattern in ["consistent", "rhythmic"]:
            confidence += 0.1

        # Acceleration events indicate natural writing
        if vector.acceleration_events > 5:
            confidence += 0.1

        # Good rhythm scores
        if vector.stroke_rhythm_score > 0.6:
            confidence += 0.1
        if vector.spatial_rhythm_score > 0.6:
            confidence += 0.1

        return min(0.95, confidence)


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def extract_calligraphy_vector(binary_mask: List[List[int]]) -> CalligraphyVector:
    """
    Extract calligraphy vector from binary image.

    Args:
        binary_mask: Binary image (0=ink, 255=background)

    Returns:
        CalligraphyVector with extracted features
    """
    analyzer = SemioticAnalyzer()
    return analyzer.analyze(binary_mask)


def generate_semiotic_signature(
    binary_mask: List[List[int]],
    windi_identity: Optional[str] = None
) -> SemioticSignature:
    """
    Generate semiotic signature for handwritten document.

    Args:
        binary_mask: Binary image
        windi_identity: Optional WINDI Identity to bind

    Returns:
        SemioticSignature
    """
    analyzer = SemioticAnalyzer()
    vector = analyzer.analyze(binary_mask)
    return analyzer.generate_signature(vector, windi_identity)
