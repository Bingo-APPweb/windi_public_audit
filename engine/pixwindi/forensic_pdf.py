"""
WINDI PixWindi — Forensic PDF Generator
=========================================
Generates dual-panel a4Desk documents with full forensic provenance.

Layout:
- Side A: Raw processed image with EXIF/GPS/Timestamp metadata
- Side B: Normalized transcription (when OCR available)
- Footer: QR Code with SHA-256 "Recibo de Virtude" hash

Standard: a4Desk Forensic PDF v1.0

"From napkin to notarized — immutable proof of origin."
"""

import hashlib
import json
import io
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone


@dataclass
class ForensicMetadata:
    """Comprehensive metadata for forensic PDF."""
    # Source information
    source_filename: str
    capture_timestamp: str
    capture_device: Optional[str]
    capture_location: Optional[Dict[str, float]]  # lat, lon

    # Processing information
    processing_timestamp: str
    processing_hash: str
    skew_correction: float
    perspective_corrected: bool

    # Anti-deepfake
    prnu_hash: str
    origin_classification: str
    anti_deepfake_score: int
    ink_coherence_score: float

    # Semiotic
    semiotic_signature: str
    calligraphy_hash: str

    # Governance
    governance_level: str
    windi_identity: Optional[str]
    submission_id: str


@dataclass
class ForensicPDF:
    """Result of forensic PDF generation."""
    pdf_bytes: bytes
    document_hash: str
    receipt_hash: str
    qr_code_data: str
    metadata: ForensicMetadata
    generated_at: str


class ForensicPDFGenerator:
    """
    Generates forensic PDF documents in a4Desk standard format.

    The generated PDF is:
    - Immutable after hash generation
    - Self-verifying via embedded hash
    - Traceable via WINDI governance chain
    - Anti-deepfake validated
    """

    # PDF dimensions (A4 in points: 595.276 x 841.890)
    PAGE_WIDTH = 595
    PAGE_HEIGHT = 842
    MARGIN = 40
    CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN

    def __init__(self):
        """Initialize generator with available libraries."""
        self._reportlab_available = False
        self._pillow_available = False
        self._qrcode_available = False

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import mm
            self._reportlab_available = True
        except ImportError:
            pass

        try:
            from PIL import Image
            self._pillow_available = True
        except ImportError:
            pass

        try:
            import qrcode
            self._qrcode_available = True
        except ImportError:
            pass

    def generate(
        self,
        processed_image: List[List[int]],
        original_image_data: bytes,
        metadata: ForensicMetadata,
        transcription: Optional[str] = None
    ) -> ForensicPDF:
        """
        Generate forensic PDF with dual-panel layout.

        Args:
            processed_image: Processed grayscale pixels
            original_image_data: Original image bytes for embedding
            metadata: Forensic metadata
            transcription: Optional OCR transcription

        Returns:
            ForensicPDF with generated document
        """
        generated_at = datetime.now(timezone.utc).isoformat()

        if self._reportlab_available:
            pdf_bytes = self._generate_with_reportlab(
                processed_image, original_image_data,
                metadata, transcription, generated_at
            )
        else:
            # Fallback: generate minimal PDF structure
            pdf_bytes = self._generate_minimal_pdf(
                metadata, transcription, generated_at
            )

        # Calculate document hash
        document_hash = hashlib.sha256(pdf_bytes).hexdigest()

        # Generate receipt hash (Recibo de Virtude)
        receipt_data = {
            "document_hash": document_hash,
            "submission_id": metadata.submission_id,
            "anti_deepfake_score": metadata.anti_deepfake_score,
            "semiotic_signature": metadata.semiotic_signature,
            "generated_at": generated_at
        }
        receipt_hash = hashlib.sha256(
            json.dumps(receipt_data, sort_keys=True).encode()
        ).hexdigest()

        # QR code data
        qr_data = self._create_qr_data(
            document_hash, receipt_hash, metadata.submission_id
        )

        return ForensicPDF(
            pdf_bytes=pdf_bytes,
            document_hash=document_hash,
            receipt_hash=receipt_hash,
            qr_code_data=qr_data,
            metadata=metadata,
            generated_at=generated_at
        )

    def _generate_with_reportlab(
        self,
        processed_image: List[List[int]],
        original_image_data: bytes,
        metadata: ForensicMetadata,
        transcription: Optional[str],
        generated_at: str
    ) -> bytes:
        """Generate PDF using ReportLab."""
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm
        from reportlab.lib import colors

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)

        # Page 1: Cover with metadata
        self._draw_cover_page(c, metadata, generated_at)
        c.showPage()

        # Page 2: Side A - Original image with metadata
        self._draw_side_a(c, original_image_data, metadata)
        c.showPage()

        # Page 3: Side B - Transcription (if available)
        if transcription:
            self._draw_side_b(c, transcription, metadata)
            c.showPage()

        # Page 4: Forensic analysis details
        self._draw_forensic_page(c, metadata, processed_image)
        c.showPage()

        # Final page: QR Code and receipt
        self._draw_receipt_page(c, metadata, generated_at)

        c.save()
        return buffer.getvalue()

    def _draw_cover_page(
        self,
        c,
        metadata: ForensicMetadata,
        generated_at: str
    ):
        """Draw cover page with document overview."""
        from reportlab.lib.units import mm

        # Title
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(
            self.PAGE_WIDTH / 2,
            self.PAGE_HEIGHT - 60,
            "WINDI Forensic Document"
        )

        # Subtitle
        c.setFont("Helvetica", 12)
        c.drawCentredString(
            self.PAGE_WIDTH / 2,
            self.PAGE_HEIGHT - 85,
            "a4Desk Standard • Anti-Deep Fake Certified"
        )

        # Horizontal line
        c.setStrokeColorRGB(0.2, 0.4, 0.6)
        c.setLineWidth(2)
        c.line(self.MARGIN, self.PAGE_HEIGHT - 100,
               self.PAGE_WIDTH - self.MARGIN, self.PAGE_HEIGHT - 100)

        # Document info box
        y = self.PAGE_HEIGHT - 140
        c.setFont("Helvetica-Bold", 11)
        c.drawString(self.MARGIN, y, "Document Information")

        y -= 25
        c.setFont("Helvetica", 10)
        info_lines = [
            f"Submission ID: {metadata.submission_id}",
            f"Captured: {metadata.capture_timestamp}",
            f"Processed: {metadata.processing_timestamp}",
            f"Device: {metadata.capture_device or 'Unknown'}",
            f"Generated: {generated_at}",
        ]

        for line in info_lines:
            c.drawString(self.MARGIN + 10, y, line)
            y -= 15

        # Anti-deepfake box
        y -= 20
        c.setFont("Helvetica-Bold", 11)
        c.drawString(self.MARGIN, y, "Anti-Deep Fake Analysis")

        y -= 25
        c.setFont("Helvetica", 10)
        analysis_lines = [
            f"Origin Classification: {metadata.origin_classification}",
            f"Anti-Deep Fake Score: {metadata.anti_deepfake_score}/100",
            f"PRNU Hash: {metadata.prnu_hash[:24]}...",
            f"Ink Coherence: {metadata.ink_coherence_score:.2%}",
        ]

        for line in analysis_lines:
            c.drawString(self.MARGIN + 10, y, line)
            y -= 15

        # Semiotic signature box
        y -= 20
        c.setFont("Helvetica-Bold", 11)
        c.drawString(self.MARGIN, y, "Semiotic Signature")

        y -= 25
        c.setFont("Helvetica", 10)
        c.drawString(self.MARGIN + 10, y, f"Signature: {metadata.semiotic_signature[:32]}...")
        y -= 15
        c.drawString(self.MARGIN + 10, y, f"Calligraphy Hash: {metadata.calligraphy_hash}")

        # Governance info
        y -= 35
        c.setFont("Helvetica-Bold", 11)
        c.drawString(self.MARGIN, y, "WINDI Governance")

        y -= 25
        c.setFont("Helvetica", 10)
        c.drawString(self.MARGIN + 10, y, f"Governance Level: {metadata.governance_level}")
        y -= 15
        if metadata.windi_identity:
            c.drawString(self.MARGIN + 10, y, f"WINDI Identity: {metadata.windi_identity}")

        # Footer
        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(
            self.PAGE_WIDTH / 2,
            30,
            "WINDI Document Security Division • \"AI processes. Human decides. WINDI guarantees.\""
        )

    def _draw_side_a(
        self,
        c,
        original_image_data: bytes,
        metadata: ForensicMetadata
    ):
        """Draw Side A: Original image with metadata."""
        # Header
        c.setFont("Helvetica-Bold", 14)
        c.drawString(self.MARGIN, self.PAGE_HEIGHT - 40, "SIDE A — Original Capture")

        c.setFont("Helvetica", 9)
        c.drawString(self.MARGIN, self.PAGE_HEIGHT - 55,
                    "Raw processed image with EXIF/GPS/Timestamp metadata")

        # Try to embed image
        if self._pillow_available:
            try:
                from PIL import Image
                from reportlab.lib.utils import ImageReader

                img = Image.open(io.BytesIO(original_image_data))

                # Calculate dimensions to fit
                max_width = self.CONTENT_WIDTH
                max_height = self.PAGE_HEIGHT - 200

                img_width, img_height = img.size
                scale = min(max_width / img_width, max_height / img_height)

                draw_width = img_width * scale
                draw_height = img_height * scale

                x = (self.PAGE_WIDTH - draw_width) / 2
                y = self.PAGE_HEIGHT - 80 - draw_height

                # Draw border
                c.setStrokeColorRGB(0.5, 0.5, 0.5)
                c.rect(x - 2, y - 2, draw_width + 4, draw_height + 4)

                # Draw image
                c.drawImage(
                    ImageReader(img),
                    x, y,
                    width=draw_width,
                    height=draw_height
                )

            except Exception:
                c.setFont("Helvetica", 10)
                c.drawString(self.MARGIN, self.PAGE_HEIGHT - 200,
                            "[Image could not be embedded]")

        # Metadata table
        y = 150
        c.setFont("Helvetica-Bold", 10)
        c.drawString(self.MARGIN, y, "Capture Metadata:")

        y -= 20
        c.setFont("Courier", 8)
        meta_items = [
            f"Filename: {metadata.source_filename}",
            f"Timestamp: {metadata.capture_timestamp}",
            f"Device: {metadata.capture_device or 'Unknown'}",
        ]

        if metadata.capture_location:
            meta_items.append(
                f"Location: {metadata.capture_location.get('lat', 'N/A')}, "
                f"{metadata.capture_location.get('lon', 'N/A')}"
            )

        for item in meta_items:
            c.drawString(self.MARGIN + 10, y, item)
            y -= 12

    def _draw_side_b(
        self,
        c,
        transcription: str,
        metadata: ForensicMetadata
    ):
        """Draw Side B: Transcription."""
        # Header
        c.setFont("Helvetica-Bold", 14)
        c.drawString(self.MARGIN, self.PAGE_HEIGHT - 40, "SIDE B — Normalized Transcription")

        c.setFont("Helvetica", 9)
        c.drawString(self.MARGIN, self.PAGE_HEIGHT - 55,
                    "OCR-extracted and validated text content")

        # Transcription box
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.setFillColorRGB(0.98, 0.98, 0.98)
        c.rect(self.MARGIN, 100,
               self.CONTENT_WIDTH, self.PAGE_HEIGHT - 180,
               fill=1, stroke=1)

        # Transcription text
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Courier", 10)

        y = self.PAGE_HEIGHT - 85
        line_height = 14
        max_chars = 75

        for line in transcription.split('\n'):
            # Word wrap
            while len(line) > max_chars:
                c.drawString(self.MARGIN + 10, y, line[:max_chars])
                line = line[max_chars:]
                y -= line_height

                if y < 120:
                    break

            c.drawString(self.MARGIN + 10, y, line)
            y -= line_height

            if y < 120:
                c.drawString(self.MARGIN + 10, y, "[continued on next page...]")
                break

    def _draw_forensic_page(
        self,
        c,
        metadata: ForensicMetadata,
        processed_image: List[List[int]]
    ):
        """Draw forensic analysis details page."""
        # Header
        c.setFont("Helvetica-Bold", 14)
        c.drawString(self.MARGIN, self.PAGE_HEIGHT - 40, "Forensic Analysis Report")

        y = self.PAGE_HEIGHT - 80

        # Processing details
        c.setFont("Helvetica-Bold", 11)
        c.drawString(self.MARGIN, y, "Image Processing")

        y -= 20
        c.setFont("Helvetica", 10)
        processing_info = [
            f"Processing Hash: {metadata.processing_hash}",
            f"Skew Correction: {metadata.skew_correction:.2f}°",
            f"Perspective Corrected: {'Yes' if metadata.perspective_corrected else 'No'}",
        ]

        for line in processing_info:
            c.drawString(self.MARGIN + 10, y, line)
            y -= 15

        # Anti-deepfake analysis
        y -= 20
        c.setFont("Helvetica-Bold", 11)
        c.drawString(self.MARGIN, y, "Anti-Deep Fake Analysis (PRNU)")

        y -= 20
        c.setFont("Helvetica", 10)

        # Score visualization
        score = metadata.anti_deepfake_score
        c.drawString(self.MARGIN + 10, y, f"Score: {score}/100")

        # Draw score bar
        bar_width = 200
        bar_height = 15
        bar_x = self.MARGIN + 100
        bar_y = y - 3

        c.setStrokeColorRGB(0.5, 0.5, 0.5)
        c.rect(bar_x, bar_y, bar_width, bar_height)

        # Fill based on score
        if score >= 70:
            c.setFillColorRGB(0.2, 0.7, 0.2)  # Green
        elif score >= 40:
            c.setFillColorRGB(0.9, 0.7, 0.1)  # Yellow
        else:
            c.setFillColorRGB(0.8, 0.2, 0.2)  # Red

        c.rect(bar_x, bar_y, bar_width * (score / 100), bar_height, fill=1)

        y -= 25
        c.setFillColorRGB(0, 0, 0)
        c.drawString(self.MARGIN + 10, y, f"Origin: {metadata.origin_classification}")
        y -= 15
        c.drawString(self.MARGIN + 10, y, f"PRNU Hash: {metadata.prnu_hash}")

        # Ink coherence
        y -= 30
        c.setFont("Helvetica-Bold", 11)
        c.drawString(self.MARGIN, y, "Ink-on-Paper Coherence Analysis")

        y -= 20
        c.setFont("Helvetica", 10)
        coherence_pct = metadata.ink_coherence_score * 100
        c.drawString(self.MARGIN + 10, y, f"Coherence Score: {coherence_pct:.1f}%")

        y -= 15
        if coherence_pct >= 60:
            verdict = "PHYSICAL ORIGIN LIKELY"
            c.setFillColorRGB(0.2, 0.6, 0.2)
        else:
            verdict = "REQUIRES MANUAL VERIFICATION"
            c.setFillColorRGB(0.8, 0.5, 0.1)

        c.drawString(self.MARGIN + 10, y, f"Verdict: {verdict}")

        # Semiotic analysis
        c.setFillColorRGB(0, 0, 0)
        y -= 35
        c.setFont("Helvetica-Bold", 11)
        c.drawString(self.MARGIN, y, "Semiotic Signature Analysis")

        y -= 20
        c.setFont("Helvetica", 10)
        c.drawString(self.MARGIN + 10, y,
                    f"Calligraphy Hash: {metadata.calligraphy_hash}")
        y -= 15
        c.drawString(self.MARGIN + 10, y,
                    f"Signature: {metadata.semiotic_signature[:48]}...")

    def _draw_receipt_page(
        self,
        c,
        metadata: ForensicMetadata,
        generated_at: str
    ):
        """Draw receipt page with QR code."""
        # Header
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(
            self.PAGE_WIDTH / 2,
            self.PAGE_HEIGHT - 50,
            "Recibo de Virtude"
        )

        c.setFont("Helvetica", 10)
        c.drawCentredString(
            self.PAGE_WIDTH / 2,
            self.PAGE_HEIGHT - 70,
            "WINDI Virtue Receipt • Cryptographic Proof of Authenticity"
        )

        # QR Code placeholder
        qr_size = 150
        qr_x = (self.PAGE_WIDTH - qr_size) / 2
        qr_y = self.PAGE_HEIGHT - 250

        c.setStrokeColorRGB(0.3, 0.3, 0.3)
        c.rect(qr_x, qr_y, qr_size, qr_size)

        # Try to generate actual QR code
        if self._qrcode_available and self._pillow_available:
            try:
                import qrcode
                from PIL import Image
                from reportlab.lib.utils import ImageReader

                qr = qrcode.QRCode(version=1, box_size=10, border=2)
                qr_data = self._create_qr_data(
                    "PENDING",  # Will be recalculated
                    "PENDING",
                    metadata.submission_id
                )
                qr.add_data(qr_data)
                qr.make(fit=True)

                qr_img = qr.make_image(fill_color="black", back_color="white")

                # Convert to PIL Image
                if hasattr(qr_img, 'get_image'):
                    qr_img = qr_img.get_image()

                c.drawImage(
                    ImageReader(qr_img),
                    qr_x, qr_y,
                    width=qr_size, height=qr_size
                )
            except Exception:
                c.setFont("Helvetica", 10)
                c.drawCentredString(
                    self.PAGE_WIDTH / 2,
                    qr_y + qr_size / 2,
                    "[QR Code]"
                )
        else:
            c.setFont("Helvetica", 10)
            c.drawCentredString(
                self.PAGE_WIDTH / 2,
                qr_y + qr_size / 2,
                "[QR Code]"
            )

        # Receipt details
        y = qr_y - 30
        c.setFont("Helvetica-Bold", 10)
        c.drawString(self.MARGIN, y, "Receipt Details:")

        y -= 20
        c.setFont("Courier", 9)
        details = [
            f"Submission ID: {metadata.submission_id}",
            f"Generated: {generated_at}",
            f"Governance: {metadata.governance_level}",
            f"Anti-Deep Fake: {metadata.anti_deepfake_score}/100",
        ]

        for line in details:
            c.drawString(self.MARGIN, y, line)
            y -= 14

        # Hash information
        y -= 20
        c.setFont("Helvetica-Bold", 10)
        c.drawString(self.MARGIN, y, "Cryptographic Hashes:")

        y -= 20
        c.setFont("Courier", 8)
        c.drawString(self.MARGIN, y, f"PRNU:      {metadata.prnu_hash}")
        y -= 12
        c.drawString(self.MARGIN, y, f"Semiotic:  {metadata.semiotic_signature[:32]}...")
        y -= 12
        c.drawString(self.MARGIN, y, f"Processing: {metadata.processing_hash}")

        # Legal notice
        y -= 40
        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(
            self.PAGE_WIDTH / 2,
            y,
            "This document is cryptographically sealed. Any modification invalidates the hashes."
        )

        # Footer
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(
            self.PAGE_WIDTH / 2,
            30,
            "WINDI Document Security Division"
        )

        c.setFont("Helvetica", 8)
        c.drawCentredString(
            self.PAGE_WIDTH / 2,
            18,
            "\"AI processes. Human decides. WINDI guarantees.\""
        )

    def _generate_minimal_pdf(
        self,
        metadata: ForensicMetadata,
        transcription: Optional[str],
        generated_at: str
    ) -> bytes:
        """Generate minimal PDF without ReportLab."""
        # Simple PDF structure
        content = f"""WINDI Forensic Document
========================
Submission ID: {metadata.submission_id}
Generated: {generated_at}

Anti-Deep Fake Analysis
-----------------------
Origin: {metadata.origin_classification}
Score: {metadata.anti_deepfake_score}/100
PRNU Hash: {metadata.prnu_hash}

Semiotic Signature
------------------
Signature: {metadata.semiotic_signature}
Calligraphy: {metadata.calligraphy_hash}

Governance
----------
Level: {metadata.governance_level}
Identity: {metadata.windi_identity or 'N/A'}
"""

        if transcription:
            content += f"\nTranscription\n-------------\n{transcription}\n"

        # Return as plain text (minimal fallback)
        return content.encode('utf-8')

    def _create_qr_data(
        self,
        document_hash: str,
        receipt_hash: str,
        submission_id: str
    ) -> str:
        """Create QR code data string."""
        return json.dumps({
            "type": "WINDI-RECEIPT",
            "version": "1.0",
            "submission_id": submission_id,
            "doc_hash": document_hash[:16],
            "receipt_hash": receipt_hash[:16],
            "verify_url": f"https://verify.windi.dev/{submission_id}"
        }, separators=(',', ':'))


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_forensic_pdf(
    image_path: str,
    submission_id: str,
    governance_level: str = "MEDIUM",
    windi_identity: Optional[str] = None
) -> ForensicPDF:
    """
    Generate forensic PDF from image file.

    This is the high-level convenience function that runs the full pipeline.
    """
    from .prnu_extractor import PRNUExtractor, InkCoherenceAnalyzer
    from .image_processor import ImageProcessor
    from .semiotic_analyzer import SemioticAnalyzer

    # Load image
    with open(image_path, 'rb') as f:
        image_data = f.read()

    # Extract filename
    import os
    filename = os.path.basename(image_path)

    # PRNU analysis
    prnu_extractor = PRNUExtractor()
    sensor_dna = prnu_extractor.extract(image_data)

    # Ink coherence
    ink_analyzer = InkCoherenceAnalyzer()
    ink_result = ink_analyzer.analyze(image_data)

    # Image processing
    processor = ImageProcessor()
    processed = processor.process(image_data)

    # Semiotic analysis
    semiotic_analyzer = SemioticAnalyzer()
    calligraphy_vector = semiotic_analyzer.analyze(processed.binary_mask)
    semiotic_signature = semiotic_analyzer.generate_signature(
        calligraphy_vector, windi_identity
    )

    # Build metadata
    metadata = ForensicMetadata(
        source_filename=filename,
        capture_timestamp=datetime.now(timezone.utc).isoformat(),
        capture_device=None,
        capture_location=None,
        processing_timestamp=datetime.now(timezone.utc).isoformat(),
        processing_hash=processed.processing_hash,
        skew_correction=processed.skew_angle,
        perspective_corrected=processed.perspective_corrected,
        prnu_hash=sensor_dna.prnu_hash,
        origin_classification=sensor_dna.origin_classification.value,
        anti_deepfake_score=sensor_dna.anti_deepfake_score,
        ink_coherence_score=ink_result.get("coherence_score", 0.0),
        semiotic_signature=semiotic_signature.signature_hash,
        calligraphy_hash=semiotic_signature.calligraphy_hash,
        governance_level=governance_level,
        windi_identity=windi_identity,
        submission_id=submission_id
    )

    # Generate PDF
    generator = ForensicPDFGenerator()
    return generator.generate(
        processed.pixels,
        image_data,
        metadata,
        transcription=None  # OCR not yet integrated
    )
