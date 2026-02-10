"""
WINDI PixWindi — Image Processor
=================================
Perspective correction, de-skewing, and adaptive thresholding
for handwritten document capture.

Pipeline:
1. Load image and detect document boundaries
2. Apply perspective transform to flatten
3. De-skew to align text horizontally
4. Adaptive thresholding to separate ink from background
5. Noise reduction while preserving calligraphy detail

"From napkin angle to notarized alignment."
"""

import hashlib
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime, timezone


@dataclass
class ProcessedImage:
    """Result of image processing pipeline."""
    original_size: Tuple[int, int]
    processed_size: Tuple[int, int]
    skew_angle: float               # Detected skew in degrees
    perspective_corrected: bool
    threshold_method: str
    processing_hash: str            # Hash of processing parameters
    quality_score: float            # 0.0-1.0
    pixels: List[List[int]]         # Processed pixel data (0-255)
    binary_mask: List[List[int]]    # Binary ink/background mask


class ImageProcessor:
    """
    Process handwritten document images for forensic analysis.

    Handles:
    - Irregular surfaces (napkins, crumpled paper)
    - Various lighting conditions
    - Perspective distortion from mobile capture
    - Ink color variations
    """

    # Processing parameters
    DEFAULT_TARGET_WIDTH = 2000
    SKEW_DETECTION_SAMPLES = 100
    PERSPECTIVE_MARGIN = 0.05

    def __init__(self):
        """Initialize processor with optional PIL/OpenCV support."""
        self._pil_available = False
        self._cv2_available = False

        try:
            from PIL import Image, ImageFilter, ImageOps
            self._pil_available = True
            self._Image = Image
            self._ImageFilter = ImageFilter
            self._ImageOps = ImageOps
        except ImportError:
            pass

        try:
            import cv2
            self._cv2_available = True
            self._cv2 = cv2
        except ImportError:
            pass

    def process(
        self,
        image_data: bytes,
        auto_perspective: bool = True,
        auto_deskew: bool = True,
        threshold_method: str = "adaptive"
    ) -> ProcessedImage:
        """
        Full processing pipeline for document image.

        Args:
            image_data: Raw image bytes
            auto_perspective: Auto-detect and correct perspective
            auto_deskew: Auto-detect and correct skew
            threshold_method: "adaptive", "otsu", or "simple"

        Returns:
            ProcessedImage with processed data
        """
        # Load image
        pixels, original_size = self._load_image(image_data)

        if pixels is None:
            raise ValueError("Failed to decode image")

        height, width = len(pixels), len(pixels[0])
        skew_angle = 0.0
        perspective_corrected = False

        # Perspective correction
        if auto_perspective:
            corners = self._detect_document_corners(pixels)
            if corners:
                pixels = self._apply_perspective_transform(pixels, corners)
                perspective_corrected = True
                height, width = len(pixels), len(pixels[0])

        # De-skew
        if auto_deskew:
            skew_angle = self._detect_skew_angle(pixels)
            if abs(skew_angle) > 0.5:  # Only correct if > 0.5 degrees
                pixels = self._rotate_image(pixels, -skew_angle)
                height, width = len(pixels), len(pixels[0])

        # Adaptive thresholding
        binary_mask = self._apply_threshold(pixels, method=threshold_method)

        # Calculate quality score
        quality_score = self._calculate_quality_score(pixels, binary_mask)

        # Generate processing hash
        processing_hash = self._generate_processing_hash(
            original_size, (width, height), skew_angle,
            perspective_corrected, threshold_method
        )

        return ProcessedImage(
            original_size=original_size,
            processed_size=(width, height),
            skew_angle=skew_angle,
            perspective_corrected=perspective_corrected,
            threshold_method=threshold_method,
            processing_hash=processing_hash,
            quality_score=quality_score,
            pixels=pixels,
            binary_mask=binary_mask
        )

    def _load_image(self, image_data: bytes) -> Tuple[Optional[List[List[int]]], Tuple[int, int]]:
        """Load image and convert to grayscale pixel array."""
        if self._pil_available:
            try:
                import io
                img = self._Image.open(io.BytesIO(image_data))
                img = img.convert('L')  # Grayscale
                width, height = img.size

                pixels = []
                for y in range(height):
                    row = []
                    for x in range(width):
                        row.append(img.getpixel((x, y)))
                    pixels.append(row)

                return pixels, (width, height)
            except Exception:
                pass

        return None, (0, 0)

    def _detect_document_corners(
        self,
        pixels: List[List[int]]
    ) -> Optional[List[Tuple[int, int]]]:
        """
        Detect document corners for perspective correction.

        Returns list of 4 corners: [top-left, top-right, bottom-right, bottom-left]
        or None if corners cannot be reliably detected.
        """
        height = len(pixels)
        width = len(pixels[0]) if height > 0 else 0

        if height < 100 or width < 100:
            return None

        # Edge detection using simple gradient
        edges = self._detect_edges(pixels)

        # Find contours (simplified: look for rectangular region)
        corners = self._find_largest_rectangle(edges)

        return corners

    def _detect_edges(self, pixels: List[List[int]]) -> List[List[int]]:
        """Simple edge detection using Sobel-like gradients."""
        height = len(pixels)
        width = len(pixels[0])

        edges = [[0] * width for _ in range(height)]

        for y in range(1, height - 1):
            for x in range(1, width - 1):
                # Sobel X
                gx = (
                    -pixels[y-1][x-1] + pixels[y-1][x+1]
                    -2*pixels[y][x-1] + 2*pixels[y][x+1]
                    -pixels[y+1][x-1] + pixels[y+1][x+1]
                )

                # Sobel Y
                gy = (
                    -pixels[y-1][x-1] - 2*pixels[y-1][x] - pixels[y-1][x+1]
                    +pixels[y+1][x-1] + 2*pixels[y+1][x] + pixels[y+1][x+1]
                )

                magnitude = int(min(255, (gx**2 + gy**2) ** 0.5))
                edges[y][x] = magnitude

        return edges

    def _find_largest_rectangle(
        self,
        edges: List[List[int]]
    ) -> Optional[List[Tuple[int, int]]]:
        """
        Find the largest rectangular region in edge map.

        Simplified approach: scan for document boundaries.
        """
        height = len(edges)
        width = len(edges[0])

        # Threshold edges
        threshold = 50
        edge_points = []
        for y in range(height):
            for x in range(width):
                if edges[y][x] > threshold:
                    edge_points.append((x, y))

        if len(edge_points) < 100:
            return None

        # Find bounding box of edge points (simplified)
        xs = [p[0] for p in edge_points]
        ys = [p[1] for p in edge_points]

        margin_x = width // 20
        margin_y = height // 20

        min_x = max(margin_x, min(xs))
        max_x = min(width - margin_x, max(xs))
        min_y = max(margin_y, min(ys))
        max_y = min(height - margin_y, max(ys))

        # Return corners
        return [
            (min_x, min_y),  # top-left
            (max_x, min_y),  # top-right
            (max_x, max_y),  # bottom-right
            (min_x, max_y),  # bottom-left
        ]

    def _apply_perspective_transform(
        self,
        pixels: List[List[int]],
        corners: List[Tuple[int, int]]
    ) -> List[List[int]]:
        """
        Apply perspective transform to flatten document.

        Uses bilinear interpolation for quality.
        """
        if len(corners) != 4:
            return pixels

        # Calculate target dimensions (use bounding box of corners)
        xs = [c[0] for c in corners]
        ys = [c[1] for c in corners]

        target_width = max(xs) - min(xs)
        target_height = max(ys) - min(ys)

        if target_width < 100 or target_height < 100:
            return pixels

        # Source corners
        src = corners

        # Destination corners (rectangle)
        dst = [
            (0, 0),
            (target_width - 1, 0),
            (target_width - 1, target_height - 1),
            (0, target_height - 1)
        ]

        # Compute perspective transform matrix (simplified)
        # For full accuracy, use OpenCV or implement full perspective matrix
        # Here we use bilinear interpolation as approximation

        result = [[128] * target_width for _ in range(target_height)]

        for y in range(target_height):
            for x in range(target_width):
                # Map destination to source using bilinear interpolation
                u = x / (target_width - 1) if target_width > 1 else 0
                v = y / (target_height - 1) if target_height > 1 else 0

                # Bilinear interpolation of source coordinates
                src_x = (
                    (1 - u) * (1 - v) * src[0][0] +
                    u * (1 - v) * src[1][0] +
                    u * v * src[2][0] +
                    (1 - u) * v * src[3][0]
                )
                src_y = (
                    (1 - u) * (1 - v) * src[0][1] +
                    u * (1 - v) * src[1][1] +
                    u * v * src[2][1] +
                    (1 - u) * v * src[3][1]
                )

                # Sample source pixel
                sx, sy = int(src_x), int(src_y)
                if 0 <= sy < len(pixels) and 0 <= sx < len(pixels[0]):
                    result[y][x] = pixels[sy][sx]

        return result

    def _detect_skew_angle(self, pixels: List[List[int]]) -> float:
        """
        Detect document skew angle using projection profile.

        Returns angle in degrees.
        """
        height = len(pixels)
        width = len(pixels[0])

        if height < 50 or width < 50:
            return 0.0

        # Binary threshold for text detection
        threshold = self._otsu_threshold(pixels)
        binary = [[1 if p < threshold else 0 for p in row] for row in pixels]

        # Test angles from -10 to +10 degrees
        best_angle = 0.0
        best_variance = 0.0

        for angle_deg in range(-100, 101, 5):  # -10 to +10 in 0.5 degree steps
            angle = angle_deg / 10.0
            # Calculate horizontal projection after rotation
            rotated = self._rotate_image(binary, angle)
            projection = [sum(row) for row in rotated]

            # Variance of projection (higher = better alignment)
            mean_proj = sum(projection) / len(projection)
            variance = sum((p - mean_proj) ** 2 for p in projection) / len(projection)

            if variance > best_variance:
                best_variance = variance
                best_angle = angle

        return best_angle

    def _rotate_image(
        self,
        pixels: List[List[int]],
        angle_degrees: float
    ) -> List[List[int]]:
        """Rotate image by given angle (in degrees)."""
        if abs(angle_degrees) < 0.1:
            return pixels

        height = len(pixels)
        width = len(pixels[0])

        # Convert to radians
        angle_rad = math.radians(angle_degrees)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        # Center of image
        cx, cy = width / 2, height / 2

        # Calculate new dimensions
        new_width = int(abs(width * cos_a) + abs(height * sin_a))
        new_height = int(abs(width * sin_a) + abs(height * cos_a))

        new_cx, new_cy = new_width / 2, new_height / 2

        # Create rotated image
        result = [[255] * new_width for _ in range(new_height)]

        for y in range(new_height):
            for x in range(new_width):
                # Inverse transform
                src_x = (x - new_cx) * cos_a + (y - new_cy) * sin_a + cx
                src_y = -(x - new_cx) * sin_a + (y - new_cy) * cos_a + cy

                sx, sy = int(src_x), int(src_y)
                if 0 <= sy < height and 0 <= sx < width:
                    result[y][x] = pixels[sy][sx]

        return result

    def _apply_threshold(
        self,
        pixels: List[List[int]],
        method: str = "adaptive"
    ) -> List[List[int]]:
        """
        Apply thresholding to separate ink from background.

        Methods:
        - "simple": Fixed threshold at 128
        - "otsu": Otsu's automatic threshold
        - "adaptive": Local adaptive thresholding
        """
        height = len(pixels)
        width = len(pixels[0])

        if method == "simple":
            return [[0 if p < 128 else 255 for p in row] for row in pixels]

        elif method == "otsu":
            threshold = self._otsu_threshold(pixels)
            return [[0 if p < threshold else 255 for p in row] for row in pixels]

        else:  # adaptive
            return self._adaptive_threshold(pixels)

    def _otsu_threshold(self, pixels: List[List[int]]) -> int:
        """Calculate Otsu's optimal threshold."""
        # Build histogram
        histogram = [0] * 256
        total_pixels = 0

        for row in pixels:
            for p in row:
                histogram[p] += 1
                total_pixels += 1

        # Calculate Otsu threshold
        sum_total = sum(i * histogram[i] for i in range(256))
        sum_background = 0
        weight_background = 0
        max_variance = 0
        threshold = 128

        for t in range(256):
            weight_background += histogram[t]
            if weight_background == 0:
                continue

            weight_foreground = total_pixels - weight_background
            if weight_foreground == 0:
                break

            sum_background += t * histogram[t]

            mean_background = sum_background / weight_background
            mean_foreground = (sum_total - sum_background) / weight_foreground

            variance = weight_background * weight_foreground * (mean_background - mean_foreground) ** 2

            if variance > max_variance:
                max_variance = variance
                threshold = t

        return threshold

    def _adaptive_threshold(
        self,
        pixels: List[List[int]],
        block_size: int = 31,
        constant: int = 10
    ) -> List[List[int]]:
        """
        Apply adaptive thresholding using local mean.

        For each pixel, threshold is the local mean minus constant.
        This handles varying illumination across the document.
        """
        height = len(pixels)
        width = len(pixels[0])

        result = [[255] * width for _ in range(height)]
        half_block = block_size // 2

        for y in range(height):
            for x in range(width):
                # Calculate local mean
                total = 0
                count = 0

                for dy in range(-half_block, half_block + 1):
                    for dx in range(-half_block, half_block + 1):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < height and 0 <= nx < width:
                            total += pixels[ny][nx]
                            count += 1

                local_mean = total / count if count > 0 else 128
                threshold = local_mean - constant

                result[y][x] = 0 if pixels[y][x] < threshold else 255

        return result

    def _calculate_quality_score(
        self,
        pixels: List[List[int]],
        binary: List[List[int]]
    ) -> float:
        """
        Calculate image quality score based on:
        - Contrast
        - Sharpness
        - Ink density
        """
        height = len(pixels)
        width = len(pixels[0])

        # Contrast (standard deviation of pixel values)
        flat = [p for row in pixels for p in row]
        mean = sum(flat) / len(flat)
        std = (sum((p - mean) ** 2 for p in flat) / len(flat)) ** 0.5
        contrast_score = min(1.0, std / 80)  # Normalize to 0-1

        # Ink density (ratio of dark pixels)
        ink_pixels = sum(1 for row in binary for p in row if p == 0)
        total_pixels = height * width
        ink_ratio = ink_pixels / total_pixels

        # Ideal ink ratio is around 10-30%
        if 0.1 <= ink_ratio <= 0.3:
            density_score = 1.0
        elif ink_ratio < 0.1:
            density_score = ink_ratio / 0.1
        else:
            density_score = max(0, 1 - (ink_ratio - 0.3) / 0.7)

        # Sharpness (edge energy)
        edges = self._detect_edges(pixels)
        edge_energy = sum(e for row in edges for e in row) / total_pixels
        sharpness_score = min(1.0, edge_energy / 30)

        # Combined score
        return (contrast_score * 0.3 + density_score * 0.3 + sharpness_score * 0.4)

    def _generate_processing_hash(
        self,
        original_size: Tuple[int, int],
        processed_size: Tuple[int, int],
        skew_angle: float,
        perspective_corrected: bool,
        threshold_method: str
    ) -> str:
        """Generate hash of processing parameters for audit trail."""
        data = {
            "original_size": original_size,
            "processed_size": processed_size,
            "skew_angle": round(skew_angle, 2),
            "perspective_corrected": perspective_corrected,
            "threshold_method": threshold_method,
            "processor_version": "1.0.0"
        }

        data_str = str(sorted(data.items()))
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def process_document_image(
    image_path: str,
    auto_correct: bool = True
) -> ProcessedImage:
    """
    Process document image from file path.

    Args:
        image_path: Path to image file
        auto_correct: Apply automatic corrections

    Returns:
        ProcessedImage with processed data
    """
    with open(image_path, 'rb') as f:
        image_data = f.read()

    processor = ImageProcessor()
    return processor.process(
        image_data,
        auto_perspective=auto_correct,
        auto_deskew=auto_correct
    )


def enhance_for_ocr(image_data: bytes) -> bytes:
    """
    Enhance image specifically for OCR processing.

    Returns processed image as PNG bytes.
    """
    processor = ImageProcessor()
    result = processor.process(image_data, threshold_method="adaptive")

    # Convert binary mask to PNG bytes
    try:
        from PIL import Image
        import io

        height = len(result.binary_mask)
        width = len(result.binary_mask[0])

        img = Image.new('L', (width, height))
        for y in range(height):
            for x in range(width):
                img.putpixel((x, y), result.binary_mask[y][x])

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    except Exception:
        return image_data
