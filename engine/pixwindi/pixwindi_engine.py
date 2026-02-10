"""
WINDI PixWindi Engine — Main Orchestrator
==========================================
Forensic Capture & Anti-Deep Fake Accreditation Pipeline

Orchestrates:
1. Sensor DNA Extraction (PRNU + Ink Coherence)
2. Image Processing (Perspective, De-skew, Threshold)
3. Semiotic Analysis (Calligraphy Vectors + Signature)
4. Forensic PDF Generation (Dual-panel a4Desk)

Entry point for processing handwritten documents from mobile capture.

"From napkin to notarized — the complete pipeline."
"""

import hashlib
import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timezone

from .prnu_extractor import PRNUExtractor, InkCoherenceAnalyzer, SensorDNA
from .image_processor import ImageProcessor, ProcessedImage
from .semiotic_analyzer import SemioticAnalyzer, CalligraphyVector, SemioticSignature
from .forensic_pdf import ForensicPDFGenerator, ForensicMetadata, ForensicPDF


@dataclass
class PixWindiResult:
    """Complete result of PixWindi processing pipeline."""
    # Status
    success: bool
    error: Optional[str]

    # Input info
    source_filename: str
    source_size_bytes: int
    capture_timestamp: str

    # Anti-deepfake results
    sensor_dna: Optional[SensorDNA]
    ink_coherence: Optional[Dict[str, Any]]
    is_authentic: bool
    anti_deepfake_score: int

    # Processing results
    processed_image: Optional[ProcessedImage]

    # Semiotic results
    calligraphy_vector: Optional[CalligraphyVector]
    semiotic_signature: Optional[SemioticSignature]

    # Output
    forensic_pdf: Optional[ForensicPDF]
    submission_id: str
    receipt_hash: str

    # Governance
    governance_level: str
    windi_identity: Optional[str]

    # Timing
    processing_started: str
    processing_completed: str
    processing_duration_ms: int

    def to_dict(self) -> Dict[str, Any]:
        """Serialize result for storage/transmission."""
        result = {
            "success": self.success,
            "error": self.error,
            "source_filename": self.source_filename,
            "source_size_bytes": self.source_size_bytes,
            "capture_timestamp": self.capture_timestamp,
            "is_authentic": self.is_authentic,
            "anti_deepfake_score": self.anti_deepfake_score,
            "submission_id": self.submission_id,
            "receipt_hash": self.receipt_hash,
            "governance_level": self.governance_level,
            "windi_identity": self.windi_identity,
            "processing_started": self.processing_started,
            "processing_completed": self.processing_completed,
            "processing_duration_ms": self.processing_duration_ms
        }

        if self.sensor_dna:
            result["sensor_dna"] = self.sensor_dna.to_dict()

        if self.ink_coherence:
            result["ink_coherence"] = self.ink_coherence

        if self.semiotic_signature:
            result["semiotic_signature"] = self.semiotic_signature.to_dict()

        if self.forensic_pdf:
            result["forensic_pdf"] = {
                "document_hash": self.forensic_pdf.document_hash,
                "receipt_hash": self.forensic_pdf.receipt_hash,
                "generated_at": self.forensic_pdf.generated_at
            }

        return result


class PixWindiEngine:
    """
    Main orchestrator for PixWindi forensic document processing.

    Pipeline stages:
    1. VALIDATE: Check input and extract metadata
    2. AUTHENTICATE: PRNU extraction + Ink coherence analysis
    3. PROCESS: Perspective correction + De-skew + Threshold
    4. ANALYZE: Calligraphy vectors + Semiotic signature
    5. GENERATE: Forensic PDF with QR receipt

    Each stage is logged and can be audited independently.
    """

    VERSION = "1.0.0"

    # Minimum requirements
    MIN_IMAGE_SIZE = 100 * 100  # 100x100 pixels minimum
    MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB maximum

    # Authenticity thresholds
    AUTHENTICITY_THRESHOLD = 0.6
    ANTI_DEEPFAKE_THRESHOLD = 40

    def __init__(
        self,
        governance_level: str = "MEDIUM",
        windi_identity: Optional[str] = None
    ):
        """
        Initialize engine.

        Args:
            governance_level: WINDI governance level (LOW/MEDIUM/HIGH)
            windi_identity: Optional WINDI Identity to bind documents to
        """
        self.governance_level = governance_level
        self.windi_identity = windi_identity

        # Initialize sub-modules
        self.prnu_extractor = PRNUExtractor()
        self.ink_analyzer = InkCoherenceAnalyzer()
        self.image_processor = ImageProcessor()
        self.semiotic_analyzer = SemioticAnalyzer()
        self.pdf_generator = ForensicPDFGenerator()

    def process(
        self,
        image_data: bytes,
        filename: str = "document.jpg",
        metadata: Dict[str, Any] = None,
        reject_synthetic: bool = True,
        generate_pdf: bool = True
    ) -> PixWindiResult:
        """
        Process handwritten document through full pipeline.

        Args:
            image_data: Raw image bytes
            filename: Source filename
            metadata: Optional EXIF/capture metadata
            reject_synthetic: If True, reject images classified as synthetic
            generate_pdf: If True, generate forensic PDF

        Returns:
            PixWindiResult with complete processing results
        """
        start_time = datetime.now(timezone.utc)
        start_ts = start_time.isoformat()

        # Generate submission ID
        submission_id = self._generate_submission_id(image_data, start_time)

        try:
            # Stage 1: Validate input
            validation_error = self._validate_input(image_data)
            if validation_error:
                return self._error_result(
                    validation_error, filename, len(image_data),
                    start_ts, submission_id
                )

            # Stage 2: Anti-deepfake authentication
            sensor_dna = self.prnu_extractor.extract(image_data, metadata)
            ink_coherence = self.ink_analyzer.analyze(image_data)

            # Determine authenticity
            is_authentic = self._evaluate_authenticity(sensor_dna, ink_coherence)
            anti_deepfake_score = sensor_dna.anti_deepfake_score

            # Reject synthetic if configured
            if reject_synthetic and not is_authentic:
                if anti_deepfake_score < self.ANTI_DEEPFAKE_THRESHOLD:
                    return self._error_result(
                        f"Image rejected: Anti-deepfake score {anti_deepfake_score} "
                        f"below threshold {self.ANTI_DEEPFAKE_THRESHOLD}",
                        filename, len(image_data), start_ts, submission_id,
                        sensor_dna=sensor_dna,
                        ink_coherence=ink_coherence
                    )

            # Stage 3: Image processing
            processed = self.image_processor.process(
                image_data,
                auto_perspective=True,
                auto_deskew=True,
                threshold_method="adaptive"
            )

            # Stage 4: Semiotic analysis
            calligraphy_vector = self.semiotic_analyzer.analyze(
                processed.binary_mask,
                processed.pixels
            )
            semiotic_signature = self.semiotic_analyzer.generate_signature(
                calligraphy_vector,
                self.windi_identity
            )

            # Stage 5: Generate forensic PDF
            forensic_pdf = None
            if generate_pdf:
                forensic_metadata = ForensicMetadata(
                    source_filename=filename,
                    capture_timestamp=metadata.get("capture_time", start_ts) if metadata else start_ts,
                    capture_device=metadata.get("device") if metadata else None,
                    capture_location=metadata.get("location") if metadata else None,
                    processing_timestamp=datetime.now(timezone.utc).isoformat(),
                    processing_hash=processed.processing_hash,
                    skew_correction=processed.skew_angle,
                    perspective_corrected=processed.perspective_corrected,
                    prnu_hash=sensor_dna.prnu_hash,
                    origin_classification=sensor_dna.origin_classification.value,
                    anti_deepfake_score=anti_deepfake_score,
                    ink_coherence_score=ink_coherence.get("coherence_score", 0.0),
                    semiotic_signature=semiotic_signature.signature_hash,
                    calligraphy_hash=semiotic_signature.calligraphy_hash,
                    governance_level=self.governance_level,
                    windi_identity=self.windi_identity,
                    submission_id=submission_id
                )

                forensic_pdf = self.pdf_generator.generate(
                    processed.pixels,
                    image_data,
                    forensic_metadata
                )

            # Calculate timing
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            # Build receipt hash
            receipt_hash = self._generate_receipt_hash(
                submission_id,
                sensor_dna,
                semiotic_signature,
                forensic_pdf
            )

            return PixWindiResult(
                success=True,
                error=None,
                source_filename=filename,
                source_size_bytes=len(image_data),
                capture_timestamp=start_ts,
                sensor_dna=sensor_dna,
                ink_coherence=ink_coherence,
                is_authentic=is_authentic,
                anti_deepfake_score=anti_deepfake_score,
                processed_image=processed,
                calligraphy_vector=calligraphy_vector,
                semiotic_signature=semiotic_signature,
                forensic_pdf=forensic_pdf,
                submission_id=submission_id,
                receipt_hash=receipt_hash,
                governance_level=self.governance_level,
                windi_identity=self.windi_identity,
                processing_started=start_ts,
                processing_completed=end_time.isoformat(),
                processing_duration_ms=duration_ms
            )

        except Exception as e:
            return self._error_result(
                f"Processing error: {str(e)}",
                filename, len(image_data), start_ts, submission_id
            )

    def _validate_input(self, image_data: bytes) -> Optional[str]:
        """Validate input image data."""
        if not image_data:
            return "Empty image data"

        if len(image_data) > self.MAX_IMAGE_SIZE:
            return f"Image too large: {len(image_data)} bytes (max {self.MAX_IMAGE_SIZE})"

        # Check for valid image header
        headers = {
            b'\xff\xd8\xff': 'JPEG',
            b'\x89PNG': 'PNG',
            b'GIF8': 'GIF',
            b'RIFF': 'WEBP',
        }

        valid_format = False
        for header, fmt in headers.items():
            if image_data[:len(header)] == header:
                valid_format = True
                break

        if not valid_format:
            return "Invalid image format (supported: JPEG, PNG, GIF, WEBP)"

        return None

    def _evaluate_authenticity(
        self,
        sensor_dna: SensorDNA,
        ink_coherence: Dict[str, Any]
    ) -> bool:
        """
        Evaluate overall authenticity of document.

        Combines PRNU analysis and ink coherence for final verdict.
        """
        prnu_authentic = sensor_dna.is_authentic
        ink_authentic = ink_coherence.get("is_physical", False)
        ink_score = ink_coherence.get("coherence_score", 0.0)

        # Combined evaluation
        if prnu_authentic and ink_authentic:
            return True
        elif prnu_authentic and ink_score >= self.AUTHENTICITY_THRESHOLD:
            return True
        elif ink_authentic and sensor_dna.confidence >= 0.6:
            return True

        return False

    def _generate_submission_id(
        self,
        image_data: bytes,
        timestamp: datetime
    ) -> str:
        """Generate unique submission ID."""
        date_str = timestamp.strftime("%Y%m%d")
        content_hash = hashlib.sha256(image_data).hexdigest()[:8].upper()
        return f"PIX-{date_str}-{content_hash}"

    def _generate_receipt_hash(
        self,
        submission_id: str,
        sensor_dna: SensorDNA,
        semiotic_signature: SemioticSignature,
        forensic_pdf: Optional[ForensicPDF]
    ) -> str:
        """Generate receipt hash (Recibo de Virtude)."""
        data = {
            "submission_id": submission_id,
            "prnu_hash": sensor_dna.prnu_hash,
            "semiotic_signature": semiotic_signature.signature_hash,
            "document_hash": forensic_pdf.document_hash if forensic_pdf else None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()

    def _error_result(
        self,
        error: str,
        filename: str,
        size: int,
        start_ts: str,
        submission_id: str,
        sensor_dna: SensorDNA = None,
        ink_coherence: Dict = None
    ) -> PixWindiResult:
        """Create error result."""
        end_time = datetime.now(timezone.utc)

        return PixWindiResult(
            success=False,
            error=error,
            source_filename=filename,
            source_size_bytes=size,
            capture_timestamp=start_ts,
            sensor_dna=sensor_dna,
            ink_coherence=ink_coherence,
            is_authentic=False,
            anti_deepfake_score=0,
            processed_image=None,
            calligraphy_vector=None,
            semiotic_signature=None,
            forensic_pdf=None,
            submission_id=submission_id,
            receipt_hash="",
            governance_level=self.governance_level,
            windi_identity=self.windi_identity,
            processing_started=start_ts,
            processing_completed=end_time.isoformat(),
            processing_duration_ms=0
        )


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def process_handwritten_document(
    image_path: str,
    governance_level: str = "MEDIUM",
    windi_identity: Optional[str] = None,
    output_pdf_path: Optional[str] = None
) -> PixWindiResult:
    """
    Process a handwritten document image.

    This is the main entry point for processing handwritten captures.

    Args:
        image_path: Path to input image file
        governance_level: WINDI governance level
        windi_identity: Optional WINDI Identity to bind
        output_pdf_path: Optional path to save forensic PDF

    Returns:
        PixWindiResult with complete processing results

    Example:
        result = process_handwritten_document(
            "/path/to/napkin_photo.jpg",
            governance_level="MEDIUM",
            windi_identity="WINDI-USER-ABC123"
        )

        if result.success:
            print(f"Submission ID: {result.submission_id}")
            print(f"Anti-deepfake score: {result.anti_deepfake_score}")
            print(f"Receipt: {result.receipt_hash}")
    """
    # Load image
    with open(image_path, 'rb') as f:
        image_data = f.read()

    filename = os.path.basename(image_path)

    # Extract EXIF metadata if available
    metadata = _extract_exif_metadata(image_data)

    # Process
    engine = PixWindiEngine(
        governance_level=governance_level,
        windi_identity=windi_identity
    )

    result = engine.process(
        image_data,
        filename=filename,
        metadata=metadata
    )

    # Save PDF if requested
    if output_pdf_path and result.success and result.forensic_pdf:
        with open(output_pdf_path, 'wb') as f:
            f.write(result.forensic_pdf.pdf_bytes)

    return result


def _extract_exif_metadata(image_data: bytes) -> Optional[Dict[str, Any]]:
    """Extract EXIF metadata from image."""
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
        import io

        img = Image.open(io.BytesIO(image_data))
        exif = img._getexif()

        if not exif:
            return None

        metadata = {}
        for tag_id, value in exif.items():
            tag = TAGS.get(tag_id, tag_id)
            metadata[tag] = str(value) if not isinstance(value, (int, float)) else value

        return metadata

    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# CLI TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("WINDI PixWindi Engine v1.0.0")
    print("Forensic Capture & Anti-Deep Fake Accreditation")
    print("=" * 70)
    print()
    print("Usage:")
    print("  from pixwindi import process_handwritten_document")
    print()
    print("  result = process_handwritten_document(")
    print("      'napkin_photo.jpg',")
    print("      governance_level='MEDIUM',")
    print("      output_pdf_path='forensic_output.pdf'")
    print("  )")
    print()
    print("Pipeline stages:")
    print("  1. VALIDATE   - Check input format and size")
    print("  2. AUTHENTICATE - PRNU extraction + Ink coherence")
    print("  3. PROCESS    - Perspective + De-skew + Threshold")
    print("  4. ANALYZE    - Calligraphy vectors + Semiotic signature")
    print("  5. GENERATE   - Forensic PDF with QR receipt")
    print()
    print("\"From napkin to notarized — with cryptographic proof.\"")
    print("=" * 70)
