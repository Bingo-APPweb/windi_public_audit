"""
WINDI PixWindi Engine
======================
Forensic Capture & Anti-Deep Fake Accreditation Module

Pipeline:
1. Sensor DNA Extraction (PRNU analysis)
2. Image Processing (perspective, thresholding)
3. Semiotic Analysis (calligraphy vectors)
4. Forensic PDF Generation (dual-panel a4Desk)

"From napkin to notarized — with cryptographic proof."

Version: 1.0.0
Date: 10-Feb-2026
Division: WINDI Document Security Division
"""

from .pixwindi_engine import PixWindiEngine, process_handwritten_document
from .prnu_extractor import PRNUExtractor, SensorDNA
from .image_processor import ImageProcessor
from .semiotic_analyzer import SemioticAnalyzer, CalligraphyVector
from .forensic_pdf import ForensicPDFGenerator

__version__ = "1.0.0"
__all__ = [
    "PixWindiEngine",
    "process_handwritten_document",
    "PRNUExtractor",
    "SensorDNA",
    "ImageProcessor",
    "SemioticAnalyzer",
    "CalligraphyVector",
    "ForensicPDFGenerator"
]
