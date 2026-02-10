"""
WINDI PixWindi — PRNU Extractor (Sensor DNA)
=============================================
Photo Response Non-Uniformity analysis for Anti-Deep Fake validation.

PRINCIPLE:
Every physical camera sensor has unique imperfections in its silicon.
These create a "fingerprint" that is:
- Unique per device (like human DNA)
- Present in every photo taken
- Impossible to replicate via AI generation

A synthetic/AI-generated image has:
- No PRNU pattern (or artificial one)
- Statistical noise that follows different distributions
- Lack of physical sensor artifacts

This module extracts and analyzes the PRNU pattern to determine
if an image originated from a physical camera or synthetic source.

References:
- Lukáš, J., Fridrich, J., & Goljan, M. (2006). "Digital camera identification"
- Chen, M., et al. (2008). "Determining Image Origin and Integrity Using Sensor Noise"
"""

import hashlib
import json
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timezone
from enum import Enum


class ImageOrigin(Enum):
    """Classification of image origin."""
    PHYSICAL_CAMERA = "physical_camera"
    SYNTHETIC_AI = "synthetic_ai"
    SCANNER = "scanner"
    SCREENSHOT = "screenshot"
    UNKNOWN = "unknown"


@dataclass
class SensorDNA:
    """
    Sensor fingerprint extracted from image.

    This is the "DNA" of the camera that took the photo.
    A deepfake cannot replicate this because it requires
    knowledge of the specific sensor's physical imperfections.
    """
    prnu_hash: str               # Hash of PRNU pattern
    noise_variance: float        # Statistical variance of noise residue
    noise_skewness: float        # Distribution skewness (AI tends toward 0)
    noise_kurtosis: float        # Distribution "tailedness"
    high_freq_energy: float      # Energy in high-frequency components
    correlation_strength: float  # How strongly pattern matches known cameras
    origin_classification: ImageOrigin
    confidence: float            # 0.0-1.0 confidence in classification
    analysis_timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage."""
        result = asdict(self)
        result["origin_classification"] = self.origin_classification.value
        return result

    @property
    def is_authentic(self) -> bool:
        """Returns True if image likely from physical source."""
        return (
            self.origin_classification in [ImageOrigin.PHYSICAL_CAMERA, ImageOrigin.SCANNER]
            and self.confidence >= 0.7
        )

    @property
    def anti_deepfake_score(self) -> int:
        """Score 0-100 for anti-deepfake resilience."""
        if self.origin_classification == ImageOrigin.SYNTHETIC_AI:
            return 0

        base_score = int(self.confidence * 60)

        # Bonus for strong PRNU characteristics
        if self.noise_variance > 0.001:
            base_score += 10
        if abs(self.noise_skewness) > 0.1:
            base_score += 10
        if self.high_freq_energy > 0.05:
            base_score += 10
        if self.correlation_strength > 0.5:
            base_score += 10

        return min(100, base_score)


class PRNUExtractor:
    """
    Extracts Photo Response Non-Uniformity patterns from images.

    PRNU is caused by:
    1. Pixel Response Non-Uniformity (manufacturing variations)
    2. Photo-Response Non-Uniformity (sensitivity differences)
    3. Dark signal non-uniformity

    These combine to create a unique "sensor fingerprint" that
    persists across all images from that sensor.
    """

    # Thresholds for classification (empirically derived)
    VARIANCE_THRESHOLD_PHYSICAL = 0.0005
    VARIANCE_THRESHOLD_SYNTHETIC = 0.00001
    SKEWNESS_THRESHOLD = 0.05
    HIGH_FREQ_THRESHOLD = 0.02

    def __init__(self, use_numpy: bool = True):
        """
        Initialize extractor.

        Args:
            use_numpy: If True, use numpy for calculations (faster).
                      If False, use pure Python (no dependencies).
        """
        self.use_numpy = use_numpy
        self._np = None

        if use_numpy:
            try:
                import numpy as np
                self._np = np
            except ImportError:
                self.use_numpy = False

    def extract(self, image_data: bytes, metadata: Dict[str, Any] = None) -> SensorDNA:
        """
        Extract PRNU pattern and sensor DNA from image.

        Args:
            image_data: Raw image bytes (JPEG, PNG, etc.)
            metadata: Optional EXIF/XMP metadata dict

        Returns:
            SensorDNA with analysis results
        """
        # Decode image to pixel values
        pixels = self._decode_image(image_data)

        if pixels is None:
            return self._unknown_result("Failed to decode image")

        # Extract noise residue (PRNU pattern)
        noise_residue = self._extract_noise_residue(pixels)

        # Calculate statistical features
        variance = self._calculate_variance(noise_residue)
        skewness = self._calculate_skewness(noise_residue)
        kurtosis = self._calculate_kurtosis(noise_residue)
        high_freq = self._calculate_high_freq_energy(noise_residue)

        # Generate PRNU hash (fingerprint)
        prnu_hash = self._hash_prnu_pattern(noise_residue)

        # Classify origin based on features
        origin, confidence = self._classify_origin(
            variance, skewness, kurtosis, high_freq, metadata
        )

        # Check for known camera correlation (if database available)
        correlation = self._check_camera_correlation(prnu_hash)

        return SensorDNA(
            prnu_hash=prnu_hash,
            noise_variance=variance,
            noise_skewness=skewness,
            noise_kurtosis=kurtosis,
            high_freq_energy=high_freq,
            correlation_strength=correlation,
            origin_classification=origin,
            confidence=confidence,
            analysis_timestamp=datetime.now(timezone.utc).isoformat()
        )

    def _decode_image(self, image_data: bytes) -> Optional[List[List[float]]]:
        """
        Decode image bytes to grayscale pixel values.

        Returns 2D array of pixel intensities normalized to [0, 1].
        """
        try:
            # Try PIL/Pillow first
            from PIL import Image
            import io

            img = Image.open(io.BytesIO(image_data))
            img = img.convert('L')  # Convert to grayscale

            if self.use_numpy and self._np:
                pixels = self._np.array(img, dtype=float) / 255.0
                return pixels.tolist()
            else:
                width, height = img.size
                pixels = []
                for y in range(height):
                    row = []
                    for x in range(width):
                        row.append(img.getpixel((x, y)) / 255.0)
                    pixels.append(row)
                return pixels

        except Exception:
            return None

    def _extract_noise_residue(self, pixels: List[List[float]]) -> List[List[float]]:
        """
        Extract noise residue by subtracting denoised version.

        The noise residue contains the PRNU pattern.
        Method: Original - Denoised = Noise (includes PRNU)

        We use a simple Gaussian-like blur for denoising.
        More sophisticated methods (wavelet, BM3D) improve accuracy.
        """
        height = len(pixels)
        width = len(pixels[0]) if height > 0 else 0

        if height < 3 or width < 3:
            return pixels

        # Simple 3x3 averaging filter for denoising
        denoised = []
        for y in range(height):
            row = []
            for x in range(width):
                if 0 < y < height - 1 and 0 < x < width - 1:
                    # Average of 3x3 neighborhood
                    total = 0.0
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            total += pixels[y + dy][x + dx]
                    row.append(total / 9.0)
                else:
                    row.append(pixels[y][x])
            denoised.append(row)

        # Noise residue = original - denoised
        noise = []
        for y in range(height):
            row = []
            for x in range(width):
                row.append(pixels[y][x] - denoised[y][x])
            noise.append(row)

        return noise

    def _calculate_variance(self, noise: List[List[float]]) -> float:
        """Calculate variance of noise residue."""
        values = [v for row in noise for v in row]
        n = len(values)
        if n < 2:
            return 0.0

        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / (n - 1)
        return variance

    def _calculate_skewness(self, noise: List[List[float]]) -> float:
        """
        Calculate skewness of noise distribution.

        Physical sensors tend to have slight asymmetry.
        AI-generated noise tends toward symmetric (skewness ~ 0).
        """
        values = [v for row in noise for v in row]
        n = len(values)
        if n < 3:
            return 0.0

        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / n
        std = variance ** 0.5

        if std < 1e-10:
            return 0.0

        skewness = sum((v - mean) ** 3 for v in values) / (n * std ** 3)
        return skewness

    def _calculate_kurtosis(self, noise: List[List[float]]) -> float:
        """
        Calculate kurtosis (excess) of noise distribution.

        Measures "tailedness" — physical noise often has heavier tails
        than synthetic Gaussian noise.
        """
        values = [v for row in noise for v in row]
        n = len(values)
        if n < 4:
            return 0.0

        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / n

        if variance < 1e-20:
            return 0.0

        fourth_moment = sum((v - mean) ** 4 for v in values) / n
        kurtosis = fourth_moment / (variance ** 2) - 3  # Excess kurtosis
        return kurtosis

    def _calculate_high_freq_energy(self, noise: List[List[float]]) -> float:
        """
        Estimate high-frequency energy in noise pattern.

        Physical PRNU has characteristic high-frequency components
        from pixel-level sensor variations. AI noise tends to be smoother.

        We use Laplacian-like edge detection as proxy for HF energy.
        """
        height = len(noise)
        width = len(noise[0]) if height > 0 else 0

        if height < 3 or width < 3:
            return 0.0

        total_energy = 0.0
        count = 0

        for y in range(1, height - 1):
            for x in range(1, width - 1):
                # Simplified Laplacian: center - average of neighbors
                center = noise[y][x]
                neighbors = (
                    noise[y-1][x] + noise[y+1][x] +
                    noise[y][x-1] + noise[y][x+1]
                ) / 4.0
                laplacian = abs(center - neighbors)
                total_energy += laplacian ** 2
                count += 1

        return total_energy / count if count > 0 else 0.0

    def _hash_prnu_pattern(self, noise: List[List[float]]) -> str:
        """
        Generate hash fingerprint of PRNU pattern.

        This creates a reproducible identifier for the sensor's
        unique noise pattern.
        """
        # Quantize noise values to reduce sensitivity to compression
        quantized = []
        for row in noise:
            for v in row:
                # Map to integer bins
                bin_value = int((v + 0.1) * 1000) % 256
                quantized.append(bin_value)

        # Sample subset for efficiency (every Nth value)
        sample_rate = max(1, len(quantized) // 10000)
        sampled = quantized[::sample_rate]

        # Hash the sampled pattern
        data = bytes(sampled[:10000])  # Cap at 10K bytes
        return hashlib.sha256(data).hexdigest()[:24]

    def _classify_origin(
        self,
        variance: float,
        skewness: float,
        kurtosis: float,
        high_freq: float,
        metadata: Dict[str, Any] = None
    ) -> Tuple[ImageOrigin, float]:
        """
        Classify image origin based on extracted features.

        Returns (classification, confidence).
        """
        confidence_factors = []

        # Variance analysis
        if variance > self.VARIANCE_THRESHOLD_PHYSICAL:
            confidence_factors.append(("physical", 0.3))
        elif variance < self.VARIANCE_THRESHOLD_SYNTHETIC:
            confidence_factors.append(("synthetic", 0.4))
        else:
            confidence_factors.append(("uncertain", 0.1))

        # Skewness analysis (physical sensors have asymmetric noise)
        if abs(skewness) > self.SKEWNESS_THRESHOLD:
            confidence_factors.append(("physical", 0.2))
        else:
            confidence_factors.append(("synthetic", 0.15))

        # High-frequency energy (physical has more HF content)
        if high_freq > self.HIGH_FREQ_THRESHOLD:
            confidence_factors.append(("physical", 0.25))
        else:
            confidence_factors.append(("synthetic", 0.2))

        # Kurtosis (physical often has heavier tails)
        if kurtosis > 0.5 or kurtosis < -0.5:
            confidence_factors.append(("physical", 0.15))
        else:
            confidence_factors.append(("synthetic", 0.1))

        # Metadata analysis
        if metadata:
            if self._has_camera_metadata(metadata):
                confidence_factors.append(("physical", 0.2))
            if self._has_ai_generator_markers(metadata):
                confidence_factors.append(("synthetic", 0.5))

        # Aggregate scores
        physical_score = sum(cf[1] for cf in confidence_factors if cf[0] == "physical")
        synthetic_score = sum(cf[1] for cf in confidence_factors if cf[0] == "synthetic")

        if physical_score > synthetic_score:
            confidence = min(0.95, physical_score / (physical_score + synthetic_score + 0.1))
            return ImageOrigin.PHYSICAL_CAMERA, confidence
        elif synthetic_score > physical_score:
            confidence = min(0.95, synthetic_score / (physical_score + synthetic_score + 0.1))
            return ImageOrigin.SYNTHETIC_AI, confidence
        else:
            return ImageOrigin.UNKNOWN, 0.5

    def _has_camera_metadata(self, metadata: Dict[str, Any]) -> bool:
        """Check for typical camera EXIF markers."""
        camera_markers = ["Make", "Model", "ExposureTime", "FNumber", "ISO", "FocalLength"]
        return any(marker in metadata for marker in camera_markers)

    def _has_ai_generator_markers(self, metadata: Dict[str, Any]) -> bool:
        """Check for AI generator signatures."""
        ai_markers = ["AI Generated", "Stable Diffusion", "DALL-E", "Midjourney", "ComfyUI"]
        metadata_str = json.dumps(metadata).lower()
        return any(marker.lower() in metadata_str for marker in ai_markers)

    def _check_camera_correlation(self, prnu_hash: str) -> float:
        """
        Check correlation against known camera database.

        This would query a registry of known PRNU patterns.
        For now, returns 0.0 (no correlation check).
        Future: integrate with WINDI Camera Registry.
        """
        # TODO: Implement camera registry lookup
        return 0.0


class InkCoherenceAnalyzer:
    """
    Analyzes ink-on-paper coherence for handwritten documents.

    Physical ink on paper fiber creates characteristic patterns:
    - Gradient bleeding at edges
    - Fiber absorption variations
    - Microscopic texture interactions

    AI-generated "handwriting" lacks these physical signatures.
    """

    def analyze(self, image_data: bytes) -> Dict[str, Any]:
        """
        Analyze ink coherence on paper fiber.

        Returns metrics indicating physical vs. synthetic origin.
        """
        pixels = self._decode_to_grayscale(image_data)

        if pixels is None:
            return {"error": "Failed to decode image", "coherence_score": 0.0}

        # Edge gradient analysis
        edge_gradient = self._analyze_edge_gradients(pixels)

        # Fiber texture detection
        fiber_texture = self._detect_fiber_texture(pixels)

        # Ink bleeding pattern
        ink_bleed = self._analyze_ink_bleeding(pixels)

        # Composite coherence score
        coherence_score = (
            edge_gradient * 0.4 +
            fiber_texture * 0.3 +
            ink_bleed * 0.3
        )

        return {
            "coherence_score": coherence_score,
            "edge_gradient_score": edge_gradient,
            "fiber_texture_score": fiber_texture,
            "ink_bleed_score": ink_bleed,
            "is_physical": coherence_score > 0.6,
            "confidence": min(0.95, coherence_score)
        }

    def _decode_to_grayscale(self, image_data: bytes) -> Optional[List[List[float]]]:
        """Decode image to grayscale pixel array."""
        try:
            from PIL import Image
            import io

            img = Image.open(io.BytesIO(image_data))
            img = img.convert('L')

            width, height = img.size
            pixels = []
            for y in range(height):
                row = []
                for x in range(width):
                    row.append(img.getpixel((x, y)) / 255.0)
                pixels.append(row)
            return pixels
        except Exception:
            return None

    def _analyze_edge_gradients(self, pixels: List[List[float]]) -> float:
        """
        Analyze gradient smoothness at ink edges.

        Physical ink has gradual gradients from bleeding.
        Digital/AI has sharp or artificially smooth edges.
        """
        height = len(pixels)
        width = len(pixels[0]) if height > 0 else 0

        if height < 5 or width < 5:
            return 0.5

        gradient_scores = []

        for y in range(2, height - 2):
            for x in range(2, width - 2):
                # Detect edge pixels (significant intensity change)
                center = pixels[y][x]
                neighbors = [
                    pixels[y-1][x], pixels[y+1][x],
                    pixels[y][x-1], pixels[y][x+1]
                ]

                max_diff = max(abs(center - n) for n in neighbors)

                if max_diff > 0.2:  # Edge detected
                    # Check for natural gradient (not too sharp, not too smooth)
                    gradient_variance = sum((center - n) ** 2 for n in neighbors) / 4

                    # Physical ink: moderate gradient variance
                    if 0.01 < gradient_variance < 0.15:
                        gradient_scores.append(1.0)
                    elif gradient_variance >= 0.15:
                        # Too sharp (possibly digital)
                        gradient_scores.append(0.3)
                    else:
                        # Too smooth (possibly AI smoothed)
                        gradient_scores.append(0.4)

        if not gradient_scores:
            return 0.5

        return sum(gradient_scores) / len(gradient_scores)

    def _detect_fiber_texture(self, pixels: List[List[float]]) -> float:
        """
        Detect paper fiber texture in background areas.

        Real paper has microscopic fiber texture.
        AI-generated backgrounds tend to be unnaturally smooth or
        have artificial texture patterns.
        """
        height = len(pixels)
        width = len(pixels[0]) if height > 0 else 0

        if height < 10 or width < 10:
            return 0.5

        # Sample background regions (lighter areas)
        background_variances = []

        for y in range(5, height - 5, 20):
            for x in range(5, width - 5, 20):
                # Check if this is a background region
                region_mean = 0.0
                count = 0
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        region_mean += pixels[y + dy][x + dx]
                        count += 1
                region_mean /= count

                if region_mean > 0.7:  # Likely background (light area)
                    # Calculate local variance (texture indicator)
                    variance = 0.0
                    for dy in range(-2, 3):
                        for dx in range(-2, 3):
                            variance += (pixels[y + dy][x + dx] - region_mean) ** 2
                    variance /= count
                    background_variances.append(variance)

        if not background_variances:
            return 0.5

        avg_variance = sum(background_variances) / len(background_variances)

        # Physical paper: small but non-zero variance
        if 0.0001 < avg_variance < 0.01:
            return 0.9
        elif avg_variance < 0.0001:
            return 0.3  # Too smooth (AI)
        else:
            return 0.5  # Too noisy (could be either)

    def _analyze_ink_bleeding(self, pixels: List[List[float]]) -> float:
        """
        Analyze ink bleeding patterns.

        Physical ink bleeds into paper fiber in characteristic ways.
        The bleeding is influenced by:
        - Paper fiber direction
        - Ink viscosity
        - Writing pressure

        AI cannot replicate these physical interactions accurately.
        """
        # Simplified: Look for asymmetric bleeding at dark/light boundaries
        height = len(pixels)
        width = len(pixels[0]) if height > 0 else 0

        if height < 10 or width < 10:
            return 0.5

        bleed_asymmetries = []

        for y in range(3, height - 3):
            for x in range(3, width - 3):
                if pixels[y][x] < 0.3:  # Dark pixel (ink)
                    # Check bleeding in all directions
                    bleeds = []
                    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        bleed_distance = 0
                        for d in range(1, 4):
                            ny, nx = y + dy * d, x + dx * d
                            if 0 <= ny < height and 0 <= nx < width:
                                if pixels[ny][nx] < 0.5:
                                    bleed_distance += 1
                                else:
                                    break
                        bleeds.append(bleed_distance)

                    # Asymmetry indicates physical bleeding
                    if len(set(bleeds)) > 1:  # Not all same
                        asymmetry = max(bleeds) - min(bleeds)
                        if asymmetry > 0:
                            bleed_asymmetries.append(1.0)
                        else:
                            bleed_asymmetries.append(0.5)

        if not bleed_asymmetries:
            return 0.5

        return sum(bleed_asymmetries) / len(bleed_asymmetries)


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def extract_sensor_dna(image_path: str) -> SensorDNA:
    """
    Extract sensor DNA from image file.

    Args:
        image_path: Path to image file

    Returns:
        SensorDNA analysis result
    """
    with open(image_path, 'rb') as f:
        image_data = f.read()

    extractor = PRNUExtractor()
    return extractor.extract(image_data)


def validate_physical_origin(image_path: str) -> Dict[str, Any]:
    """
    Validate that image originated from physical camera.

    Returns comprehensive anti-deepfake analysis.
    """
    with open(image_path, 'rb') as f:
        image_data = f.read()

    # PRNU analysis
    prnu_extractor = PRNUExtractor()
    sensor_dna = prnu_extractor.extract(image_data)

    # Ink coherence analysis
    ink_analyzer = InkCoherenceAnalyzer()
    ink_result = ink_analyzer.analyze(image_data)

    # Combined verdict
    is_authentic = sensor_dna.is_authentic and ink_result.get("is_physical", False)

    combined_confidence = (
        sensor_dna.confidence * 0.6 +
        ink_result.get("confidence", 0.5) * 0.4
    )

    return {
        "is_authentic": is_authentic,
        "combined_confidence": combined_confidence,
        "anti_deepfake_score": sensor_dna.anti_deepfake_score,
        "sensor_dna": sensor_dna.to_dict(),
        "ink_coherence": ink_result,
        "verdict": "PHYSICAL_ORIGIN" if is_authentic else "SYNTHETIC_OR_UNKNOWN",
        "analysis_timestamp": datetime.now(timezone.utc).isoformat()
    }
