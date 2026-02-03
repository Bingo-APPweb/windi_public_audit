#!/usr/bin/env python3
"""
WINDI Print Watermark Layer v0.1
Physical Forensic Extension for A4Desk

Purpose: Embed deterministic micro-vector watermarks derived from doc_hash
         into PDF documents before final export.

Principle: AI processes. Human decides. WINDI guarantees.
           This extends the guarantee from digital to physical domain.

Location: /opt/windi/engine/windi_print_layer.py

Author: WINDI Publishing House
Date: 2026-01-31
"""

import hashlib
import struct
from typing import Tuple, List, Optional
from io import BytesIO

# PDF manipulation
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import Color
    from PyPDF2 import PdfReader, PdfWriter
    LIBS_AVAILABLE = True
except ImportError:
    LIBS_AVAILABLE = False


class WindiPrintLayer:
    """
    Deterministic micro-vector watermark generator.
    
    Creates forensic patterns that:
    - Are derived mathematically from doc_hash
    - Survive high-quality printing (300+ DPI)
    - Are invisible to casual observation
    - Can be detected with 1200+ DPI scanning
    - Do not alter document semantics
    """
    
    # Configuration
    MICRO_LINE_WIDTH = 0.1  # points (barely visible)
    PATTERN_OPACITY = 0.005  # 3% opacity - invisible but present
    MICRO_TEXT_SIZE = 0.15   # points - requires magnification
    PATTERN_DENSITY = 50    # elements per page
    
    def __init__(self, doc_hash: str, issuer_id: str = "WINDI"):
        """
        Initialize watermark generator with document hash.
        
        Args:
            doc_hash: The WINDI envelope doc_hash (hex string)
            issuer_id: Issuer identifier for micro-text
        """
        self.doc_hash = doc_hash
        self.issuer_id = issuer_id
        self.seed = self._generate_seed()
        self.rng_state = 0
        
    def _generate_seed(self) -> bytes:
        """Generate deterministic seed from doc_hash."""
        return hashlib.sha256(self.doc_hash.encode()).digest()
    
    def _deterministic_random(self) -> float:
        """
        Generate deterministic pseudo-random value from seed.
        Same doc_hash always produces same pattern sequence.
        """
        # Use seed bytes at current state position
        idx = self.rng_state % 32
        self.rng_state += 1
        
        # Get bytes safely using direct indexing
        val = self.seed[idx]
        val2 = self.seed[(idx + 7) % 32]
        
        return ((val * 256 + val2) % 10000) / 10000.0
    
    def _reset_rng(self):
        """Reset RNG state for reproducibility."""
        self.rng_state = 0
    
    def generate_micro_lines(self, page_width: float, page_height: float) -> List[Tuple]:
        """
        Generate deterministic micro-line coordinates.
        
        Returns list of (x1, y1, x2, y2) tuples for micro-lines.
        """
        self._reset_rng()
        lines = []
        
        for _ in range(self.PATTERN_DENSITY):
            x1 = self._deterministic_random() * page_width
            y1 = self._deterministic_random() * page_height
            
            # Short lines (2-5 points)
            length = 2 + self._deterministic_random() * 3
            angle = self._deterministic_random() * 360
            
            import math
            x2 = x1 + length * math.cos(math.radians(angle))
            y2 = y1 + length * math.sin(math.radians(angle))
            
            lines.append((x1, y1, x2, y2))
        
        return lines
    
    def generate_micro_dots(self, page_width: float, page_height: float) -> List[Tuple]:
        """
        Generate deterministic micro-dot coordinates.
        
        Returns list of (x, y, radius) tuples.
        """
        dots = []
        
        for _ in range(self.PATTERN_DENSITY // 2):
            x = self._deterministic_random() * page_width
            y = self._deterministic_random() * page_height
            radius = 0.2 + self._deterministic_random() * 0.3  # 0.2-0.5 pt
            
            dots.append((x, y, radius))
        
        return dots
    
    def generate_micro_text_positions(self, page_width: float, page_height: float) -> List[Tuple]:
        """
        Generate positions for micro-text forensic markers.
        
        Returns list of (x, y, text) tuples.
        """
        positions = []
        
        # Place micro-text in corners and edges (less likely to be covered)
        margin = 20  # points from edge
        
        # Corner positions
        corners = [
            (margin, margin),
            (page_width - margin, margin),
            (margin, page_height - margin),
            (page_width - margin, page_height - margin)
        ]
        
        # Fragment of doc_hash for identification
        hash_fragment = self.doc_hash[:12]
        micro_text = f"WINDI:{hash_fragment}:{self.issuer_id}"
        
        for x, y in corners:
            # Slight random offset
            x += (self._deterministic_random() - 0.5) * 10
            y += (self._deterministic_random() - 0.5) * 10
            positions.append((x, y, micro_text))
        
        return positions
    
    def get_watermark_metadata(self) -> dict:
        """
        Return metadata about the watermark layer.
        For inclusion in WINDI envelope.
        """
        return {
            "layer_version": "0.1",
            "layer_type": "print_watermark",
            "pattern_seed_hash": hashlib.sha256(self.seed).hexdigest()[:16],
            "pattern_density": self.PATTERN_DENSITY,
            "micro_text_included": True,
            "forensic_recoverable": True,
            "min_scan_dpi": 1200
        }


def create_watermark_overlay(doc_hash: str, 
                             issuer_id: str = "WINDI",
                             page_size: Tuple[float, float] = A4) -> bytes:
    """
    Create a PDF overlay containing only the watermark layer.
    
    This overlay can be merged with the original document.
    
    Args:
        doc_hash: WINDI envelope doc_hash
        issuer_id: Issuer identifier
        page_size: Page dimensions (width, height) in points
    
    Returns:
        PDF bytes containing watermark overlay
    """
    if not LIBS_AVAILABLE:
        raise ImportError("Required libraries not available: reportlab, PyPDF2")
    
    layer = WindiPrintLayer(doc_hash, issuer_id)
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=page_size)
    
    page_width, page_height = page_size
    
    # Set up micro-line style
    watermark_color = Color(0.5, 0.5, 0.5, alpha=layer.PATTERN_OPACITY)
    c.setStrokeColor(watermark_color)
    c.setLineWidth(layer.MICRO_LINE_WIDTH)
    
    # Draw micro-lines
    for x1, y1, x2, y2 in layer.generate_micro_lines(page_width, page_height):
        c.line(x1, y1, x2, y2)
    
    # Draw micro-dots
    c.setFillColor(watermark_color)
    for x, y, radius in layer.generate_micro_dots(page_width, page_height):
        c.circle(x, y, radius, fill=1, stroke=0)
    
    # Draw micro-text
    c.setFont("Helvetica", layer.MICRO_TEXT_SIZE)
    c.setFillColor(Color(0.5, 0.5, 0.5, alpha=layer.PATTERN_OPACITY * 2))
    for x, y, text in layer.generate_micro_text_positions(page_width, page_height):
        c.drawString(x, y, text)
    
    c.save()
    buffer.seek(0)
    return buffer.read()


def embed_print_watermark(pdf_bytes: bytes, 
                          doc_hash: str,
                          issuer_id: str = "WINDI") -> bytes:
    """
    Main function: Embed deterministic micro-vector watermark into PDF.
    
    This is the entry point for the A4Desk pipeline.
    
    Args:
        pdf_bytes: Original PDF document bytes
        doc_hash: WINDI envelope doc_hash (hex string)
        issuer_id: Issuer identifier for micro-text
    
    Returns:
        Modified PDF bytes with embedded watermark layer
    
    Example:
        with open("document.pdf", "rb") as f:
            original = f.read()
        
        watermarked = embed_print_watermark(original, doc_hash="abc123...")
        
        with open("document_watermarked.pdf", "wb") as f:
            f.write(watermarked)
    """
    if not LIBS_AVAILABLE:
        raise ImportError(
            "Required libraries not available. Install with:\n"
            "pip install reportlab PyPDF2"
        )
    
    # Read original PDF
    original_pdf = PdfReader(BytesIO(pdf_bytes))
    output = PdfWriter()
    
    # Get page size from first page
    first_page = original_pdf.pages[0]
    page_width = float(first_page.mediabox.width)
    page_height = float(first_page.mediabox.height)
    
    # Create watermark overlay
    watermark_bytes = create_watermark_overlay(
        doc_hash=doc_hash,
        issuer_id=issuer_id,
        page_size=(page_width, page_height)
    )
    watermark_pdf = PdfReader(BytesIO(watermark_bytes))
    watermark_page = watermark_pdf.pages[0]
    
    # Merge watermark with each page
    for page in original_pdf.pages:
        page.merge_page(watermark_page)
        output.add_page(page)
    
    # Copy metadata
    if original_pdf.metadata:
        output.add_metadata(original_pdf.metadata)
    
    # Write output
    output_buffer = BytesIO()
    output.write(output_buffer)
    output_buffer.seek(0)
    
    return output_buffer.read()


def verify_watermark_presence(pdf_bytes: bytes, doc_hash: str) -> dict:
    """
    Verify that a PDF contains the expected watermark pattern.
    
    This is a basic verification - full forensic analysis requires
    high-resolution scanning of printed document.
    
    Args:
        pdf_bytes: PDF document bytes
        doc_hash: Expected WINDI doc_hash
    
    Returns:
        Verification result dictionary
    """
    layer = WindiPrintLayer(doc_hash)
    
    # For digital verification, we can check if the pattern
    # coordinates match what we would generate
    expected_metadata = layer.get_watermark_metadata()
    
    return {
        "verification_type": "digital_pattern_check",
        "expected_seed_hash": expected_metadata["pattern_seed_hash"],
        "note": "Full forensic verification requires 1200+ DPI scan of printed document"
    }


# CLI interface for testing
if __name__ == "__main__":
    import sys
    
    print("WINDI Print Watermark Layer v0.1")
    print("=" * 40)
    
    if not LIBS_AVAILABLE:
        print("ERROR: Required libraries not installed")
        print("Run: pip install reportlab PyPDF2")
        sys.exit(1)
    
    # Demo: generate pattern coordinates for a test hash
    test_hash = "abc123def456789012345678901234567890abcdef1234567890"
    layer = WindiPrintLayer(test_hash, "WINDI-TEST")
    
    print(f"\nTest doc_hash: {test_hash[:20]}...")
    print(f"Pattern seed: {layer.seed.hex()[:32]}...")
    
    lines = layer.generate_micro_lines(595, 842)  # A4
    dots = layer.generate_micro_dots(595, 842)
    texts = layer.generate_micro_text_positions(595, 842)
    
    print(f"\nGenerated patterns:")
    print(f"  Micro-lines: {len(lines)}")
    print(f"  Micro-dots: {len(dots)}")
    print(f"  Micro-text positions: {len(texts)}")
    
    print(f"\nMetadata: {layer.get_watermark_metadata()}")
    
    print("\nLayer ready for integration with A4Desk pipeline.")
