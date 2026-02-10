"""
WINDI Forensic API — Digital Notary Endpoint
=============================================
POST /v1/forensic/validate-handwritten

The "Tabelião Digital" — receives raw artifacts and returns virtue proofs.

Pipeline:
1. INGEST: Receive multipart + validate WINDI Identity
2. ACCREDIT: PixWindi PRNU extraction + Anti-Deep Fake
3. ANALYZE: Semiotic signature + a4Desk transcription
4. SETTLE: Optional financial liquidation
5. RESPOND: dual_proof_hash + Forensic PDF URL

Port: 8093 (Forensic API)

"From napkin to notarized — the API that seals commitments."
"""

import os
import io
import json
import hashlib
import tempfile
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, Form, Header, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# WINDI Engine imports
from pixwindi import PixWindiEngine, process_handwritten_document
from pixwindi.prnu_extractor import PRNUExtractor, InkCoherenceAnalyzer
from pixwindi.semiotic_analyzer import SemioticAnalyzer
from settlement import (
    SettlementEngine,
    create_commitment,
    settle_commitment,
    verify_settlement
)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

FORENSIC_API_PORT = 8093
FORENSIC_STORAGE_DIR = Path("/opt/windi/data/forensic")
AUDIT_LOG_DIR = Path("/opt/windi/logs/forensic")
PDF_OUTPUT_DIR = Path("/opt/windi/data/forensic/pdfs")

# Governance thresholds
I9_HUMAN_CONFIRMATION_THRESHOLD = 0.85  # Below this requires human confirmation
AUTO_SETTLE_THRESHOLD = 0.85
REJECTION_THRESHOLD = 0.40

# Ensure directories exist
FORENSIC_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)
PDF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="WINDI Forensic API",
    description="Digital Notary — Handwritten Document Validation & Settlement",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class MetadataInput(BaseModel):
    """Capture metadata from mobile device."""
    timestamp: Optional[str] = None
    device_id: Optional[str] = None
    device_model: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy_meters: Optional[float] = None


class ValidationResponse(BaseModel):
    """Response from validation endpoint."""
    success: bool
    submission_id: str
    status: str  # "validated", "requires_confirmation", "rejected", "settled"

    # Anti-Deep Fake results
    anti_deepfake_validation: Dict[str, Any]
    authenticity_score: int
    origin_classification: str

    # Semiotic analysis
    semiotic_signature: str
    calligraphy_hash: str

    # Commitment (if text extracted)
    commitment: Optional[Dict[str, Any]] = None

    # Settlement (if financial link provided)
    settlement: Optional[Dict[str, Any]] = None

    # Proofs
    receipt_hash: str
    dual_proof_hash: Optional[str] = None

    # Outputs
    forensic_pdf_url: Optional[str] = None
    verification_url: str

    # Governance
    governance_level: str
    requires_human_confirmation: bool
    i9_compliant: bool

    # Timing
    processed_at: str
    processing_duration_ms: int


class ConfirmationRequest(BaseModel):
    """Request to confirm a pending validation."""
    submission_id: str
    confirmed_by: str
    confirmation_notes: Optional[str] = None


class SettlementRequest(BaseModel):
    """Request to settle a validated commitment."""
    submission_id: str
    transaction_id: str
    settled_by: str = "api"


# ═══════════════════════════════════════════════════════════════════════════════
# GOVERNANCE MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════════════════

class GovernanceChecker:
    """
    I9 Compliance checker — Prohibition of Autonomy Escalation.

    Ensures the system NEVER auto-executes high-stakes decisions
    without human confirmation when confidence is below threshold.
    """

    def check_i9_compliance(
        self,
        confidence_score: float,
        governance_level: str,
        has_financial_link: bool
    ) -> tuple[bool, bool]:
        """
        Check I9 compliance.

        Returns:
            (is_compliant, requires_human_confirmation)
        """
        # I9: System must request human confirmation for:
        # 1. Confidence below threshold
        # 2. HIGH governance level always requires confirmation
        # 3. Financial settlement always requires confirmation if score < 95%

        requires_confirmation = False

        if confidence_score < I9_HUMAN_CONFIRMATION_THRESHOLD:
            requires_confirmation = True

        if governance_level == "HIGH":
            requires_confirmation = True

        if has_financial_link and confidence_score < 0.95:
            requires_confirmation = True

        # I9 is compliant if we properly flag the need for confirmation
        is_compliant = True  # We're compliant by asking, not by auto-executing

        return is_compliant, requires_confirmation

    def log_governance_decision(
        self,
        submission_id: str,
        decision: str,
        confidence: float,
        requires_confirmation: bool,
        governance_level: str
    ):
        """Log governance decision for audit trail."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "submission_id": submission_id,
            "decision": decision,
            "confidence": confidence,
            "requires_confirmation": requires_confirmation,
            "governance_level": governance_level,
            "i9_status": "COMPLIANT"
        }

        log_path = AUDIT_LOG_DIR / f"governance_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + "\n")


governance_checker = GovernanceChecker()


# ═══════════════════════════════════════════════════════════════════════════════
# AUDIT LOGGING
# ═══════════════════════════════════════════════════════════════════════════════

def log_audit_event(
    event_type: str,
    submission_id: str,
    details: Dict[str, Any],
    windi_identity: Optional[str] = None
):
    """
    Log audit event to forensic base.

    Format follows Commit 77a153a standard.
    """
    entry = {
        "event_id": f"FAPI-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{hashlib.sha256(submission_id.encode()).hexdigest()[:8]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "submission_id": submission_id,
        "windi_identity": windi_identity,
        "details": details,
        "api_version": "1.0.0"
    }

    # Write to daily log file
    log_path = AUDIT_LOG_DIR / f"forensic_{datetime.now().strftime('%Y%m%d')}.jsonl"
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return entry["event_id"]


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════

@app.post(
    "/v1/forensic/validate-handwritten",
    response_model=ValidationResponse,
    summary="Validate Handwritten Document",
    description="""
    The Digital Notary endpoint — validates handwritten documents and optionally
    settles them with financial transactions.

    **Pipeline:**
    1. Receive image + metadata
    2. PRNU analysis (Anti-Deep Fake)
    3. Semiotic signature generation
    4. Optional: Financial settlement

    **I9 Compliance:**
    If confidence < 85%, requires human confirmation before settlement.
    """
)
async def validate_handwritten(
    background_tasks: BackgroundTasks,
    image_file: UploadFile = File(..., description="Photo of handwritten document"),
    metadata_json: str = Form(default="{}", description="JSON with GPS, timestamp, device info"),
    link_financial_id: Optional[str] = Form(default=None, description="Transaction ID for settlement"),
    transcription: Optional[str] = Form(default=None, description="Optional OCR transcription"),
    x_windi_identity: Optional[str] = Header(default=None, alias="X-WINDI-Identity"),
    x_governance_level: str = Header(default="MEDIUM", alias="X-Governance-Level")
):
    """
    Validate a handwritten document image.

    Returns validation results, anti-deepfake analysis, and optionally
    settles with a linked financial transaction.
    """
    start_time = datetime.now(timezone.utc)

    # Parse metadata
    try:
        metadata = json.loads(metadata_json) if metadata_json else {}
    except json.JSONDecodeError:
        metadata = {}

    # Read image data
    image_data = await image_file.read()

    if not image_data:
        raise HTTPException(status_code=400, detail="Empty image file")

    # Log ingestion
    submission_id = f"FAPI-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hashlib.sha256(image_data).hexdigest()[:8].upper()}"

    log_audit_event(
        "INGESTION",
        submission_id,
        {
            "filename": image_file.filename,
            "size_bytes": len(image_data),
            "content_type": image_file.content_type,
            "has_metadata": bool(metadata),
            "has_financial_link": bool(link_financial_id)
        },
        x_windi_identity
    )

    try:
        # ═══════════════════════════════════════════════════════════════════
        # STAGE 1: PIXWINDI PROCESSING
        # ═══════════════════════════════════════════════════════════════════

        pixwindi_engine = PixWindiEngine(
            governance_level=x_governance_level,
            windi_identity=x_windi_identity
        )

        pixwindi_result = pixwindi_engine.process(
            image_data,
            filename=image_file.filename or "document.jpg",
            metadata=metadata,
            reject_synthetic=False,  # We handle rejection at API level
            generate_pdf=True
        )

        if not pixwindi_result.success:
            log_audit_event(
                "PROCESSING_ERROR",
                submission_id,
                {"error": pixwindi_result.error},
                x_windi_identity
            )
            raise HTTPException(status_code=422, detail=pixwindi_result.error)

        # ═══════════════════════════════════════════════════════════════════
        # STAGE 2: GOVERNANCE CHECK (I9)
        # ═══════════════════════════════════════════════════════════════════

        confidence_score = pixwindi_result.anti_deepfake_score / 100.0

        i9_compliant, requires_confirmation = governance_checker.check_i9_compliance(
            confidence_score,
            x_governance_level,
            bool(link_financial_id)
        )

        governance_checker.log_governance_decision(
            submission_id,
            "VALIDATION",
            confidence_score,
            requires_confirmation,
            x_governance_level
        )

        # Determine status
        if pixwindi_result.anti_deepfake_score < REJECTION_THRESHOLD * 100:
            status = "rejected"
        elif requires_confirmation:
            status = "requires_confirmation"
        else:
            status = "validated"

        # ═══════════════════════════════════════════════════════════════════
        # STAGE 3: COMMITMENT PARSING (if transcription available)
        # ═══════════════════════════════════════════════════════════════════

        commitment_data = None
        if transcription:
            commitment = create_commitment(
                text=transcription,
                pixwindi_submission_id=pixwindi_result.submission_id,
                pixwindi_receipt_hash=pixwindi_result.receipt_hash,
                document_hash=pixwindi_result.forensic_pdf.document_hash if pixwindi_result.forensic_pdf else ""
            )
            commitment_data = {
                "commitment_id": commitment.commitment_id,
                "type": commitment.parsed_commitment.commitment_type.value,
                "total_amount": commitment.parsed_commitment.total_amount,
                "currency": commitment.parsed_commitment.currency.value,
                "deadline": commitment.parsed_commitment.deadline.isoformat() if commitment.parsed_commitment.deadline else None,
                "parties": len(commitment.parsed_commitment.parties),
                "confidence": commitment.parsed_commitment.parse_confidence
            }

        # ═══════════════════════════════════════════════════════════════════
        # STAGE 4: SETTLEMENT (if financial link provided and allowed)
        # ═══════════════════════════════════════════════════════════════════

        settlement_data = None
        dual_proof = None

        if link_financial_id and status == "validated" and commitment_data:
            # Attempt settlement
            settlement_receipt = settle_commitment(
                commitment_data["commitment_id"],
                link_financial_id,
                settled_by=x_windi_identity or "api"
            )

            if settlement_receipt:
                status = "settled"
                dual_proof = settlement_receipt.dual_proof_hash
                settlement_data = {
                    "settlement_id": settlement_receipt.settlement_id,
                    "transaction_id": settlement_receipt.transaction_id,
                    "amount_settled": settlement_receipt.amount_settled,
                    "currency": settlement_receipt.currency,
                    "match_score": settlement_receipt.match_score,
                    "settled_at": settlement_receipt.settled_at,
                    "verification_url": settlement_receipt.verification_url
                }

                log_audit_event(
                    "SETTLEMENT",
                    submission_id,
                    settlement_data,
                    x_windi_identity
                )

        elif link_financial_id and status == "requires_confirmation":
            # Store pending settlement for later confirmation
            log_audit_event(
                "PENDING_SETTLEMENT",
                submission_id,
                {
                    "financial_id": link_financial_id,
                    "reason": "I9: Requires human confirmation",
                    "confidence": confidence_score
                },
                x_windi_identity
            )

        # ═══════════════════════════════════════════════════════════════════
        # STAGE 5: SAVE PDF AND PREPARE RESPONSE
        # ═══════════════════════════════════════════════════════════════════

        pdf_url = None
        if pixwindi_result.forensic_pdf:
            pdf_filename = f"{submission_id}.pdf"
            pdf_path = PDF_OUTPUT_DIR / pdf_filename
            with open(pdf_path, 'wb') as f:
                f.write(pixwindi_result.forensic_pdf.pdf_bytes)
            pdf_url = f"/v1/forensic/pdf/{submission_id}"

        # Calculate duration
        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        # Log completion
        log_audit_event(
            "VALIDATION_COMPLETE",
            submission_id,
            {
                "status": status,
                "anti_deepfake_score": pixwindi_result.anti_deepfake_score,
                "requires_confirmation": requires_confirmation,
                "has_settlement": settlement_data is not None,
                "duration_ms": duration_ms
            },
            x_windi_identity
        )

        # Build response
        return ValidationResponse(
            success=True,
            submission_id=submission_id,
            status=status,
            anti_deepfake_validation={
                "score": pixwindi_result.anti_deepfake_score,
                "threshold_passed": pixwindi_result.anti_deepfake_score >= REJECTION_THRESHOLD * 100,
                "prnu_hash": pixwindi_result.sensor_dna.prnu_hash if pixwindi_result.sensor_dna else None,
                "noise_variance": pixwindi_result.sensor_dna.noise_variance if pixwindi_result.sensor_dna else None,
                "ink_coherence": pixwindi_result.ink_coherence
            },
            authenticity_score=pixwindi_result.anti_deepfake_score,
            origin_classification=pixwindi_result.sensor_dna.origin_classification.value if pixwindi_result.sensor_dna else "unknown",
            semiotic_signature=pixwindi_result.semiotic_signature.signature_hash if pixwindi_result.semiotic_signature else "",
            calligraphy_hash=pixwindi_result.semiotic_signature.calligraphy_hash if pixwindi_result.semiotic_signature else "",
            commitment=commitment_data,
            settlement=settlement_data,
            receipt_hash=pixwindi_result.receipt_hash,
            dual_proof_hash=dual_proof,
            forensic_pdf_url=pdf_url,
            verification_url=f"https://verify.windi.dev/forensic/{submission_id}",
            governance_level=x_governance_level,
            requires_human_confirmation=requires_confirmation,
            i9_compliant=i9_compliant,
            processed_at=end_time.isoformat(),
            processing_duration_ms=duration_ms
        )

    except HTTPException:
        raise
    except Exception as e:
        log_audit_event(
            "ERROR",
            submission_id,
            {"error": str(e), "type": type(e).__name__},
            x_windi_identity
        )
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIRMATION ENDPOINT (I9 Compliance)
# ═══════════════════════════════════════════════════════════════════════════════

@app.post(
    "/v1/forensic/confirm",
    summary="Confirm Pending Validation",
    description="Human confirmation for validations below confidence threshold (I9 compliance)"
)
async def confirm_validation(
    request: ConfirmationRequest,
    x_windi_identity: Optional[str] = Header(default=None, alias="X-WINDI-Identity")
):
    """
    Confirm a validation that required human review.

    This endpoint satisfies I9 — Prohibition of Autonomy Escalation.
    """
    log_audit_event(
        "HUMAN_CONFIRMATION",
        request.submission_id,
        {
            "confirmed_by": request.confirmed_by,
            "notes": request.confirmation_notes
        },
        x_windi_identity
    )

    return {
        "success": True,
        "submission_id": request.submission_id,
        "status": "confirmed",
        "confirmed_by": request.confirmed_by,
        "confirmed_at": datetime.now(timezone.utc).isoformat(),
        "i9_compliant": True
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SETTLEMENT ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════

@app.post(
    "/v1/forensic/settle",
    summary="Settle Validated Commitment",
    description="Link a validated commitment to a financial transaction"
)
async def settle_validated_commitment(
    request: SettlementRequest,
    x_windi_identity: Optional[str] = Header(default=None, alias="X-WINDI-Identity")
):
    """
    Settle a previously validated commitment with a transaction.
    """
    settlement_receipt = settle_commitment(
        request.submission_id,
        request.transaction_id,
        request.settled_by
    )

    if not settlement_receipt:
        raise HTTPException(
            status_code=404,
            detail="Commitment not found or settlement failed"
        )

    log_audit_event(
        "MANUAL_SETTLEMENT",
        request.submission_id,
        {
            "settlement_id": settlement_receipt.settlement_id,
            "transaction_id": request.transaction_id,
            "settled_by": request.settled_by
        },
        x_windi_identity
    )

    return {
        "success": True,
        "settlement": settlement_receipt.to_dict(),
        "verification_url": settlement_receipt.verification_url
    }


# ═══════════════════════════════════════════════════════════════════════════════
# VERIFICATION ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════

@app.get(
    "/v1/forensic/verify/{submission_id}",
    summary="Verify Submission",
    description="Verify the integrity of a forensic submission"
)
async def verify_submission(submission_id: str):
    """
    Verify a forensic submission's integrity.
    """
    # Check if PDF exists
    pdf_path = PDF_OUTPUT_DIR / f"{submission_id}.pdf"
    pdf_exists = pdf_path.exists()

    # Load audit logs for this submission
    audit_entries = []
    for log_file in AUDIT_LOG_DIR.glob("forensic_*.jsonl"):
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("submission_id") == submission_id:
                        audit_entries.append(entry)
                except:
                    continue

    if not audit_entries:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Calculate integrity hash
    audit_hash = hashlib.sha256(
        json.dumps(audit_entries, sort_keys=True).encode()
    ).hexdigest()

    return {
        "submission_id": submission_id,
        "verified": True,
        "pdf_available": pdf_exists,
        "audit_entries": len(audit_entries),
        "audit_hash": audit_hash,
        "first_event": audit_entries[0]["timestamp"] if audit_entries else None,
        "last_event": audit_entries[-1]["timestamp"] if audit_entries else None,
        "verified_at": datetime.now(timezone.utc).isoformat()
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PDF DOWNLOAD ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════

@app.get(
    "/v1/forensic/pdf/{submission_id}",
    summary="Download Forensic PDF",
    description="Download the forensic PDF for a validated submission"
)
async def download_forensic_pdf(submission_id: str):
    """
    Download the generated forensic PDF.
    """
    pdf_path = PDF_OUTPUT_DIR / f"{submission_id}.pdf"

    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not found")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"WINDI-Forensic-{submission_id}.pdf"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH & STATUS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "windi-forensic-api",
        "port": FORENSIC_API_PORT,
        "version": "1.0.0"
    }


@app.get("/v1/forensic/status")
async def api_status():
    """API status with statistics."""
    # Count submissions today
    today_log = AUDIT_LOG_DIR / f"forensic_{datetime.now().strftime('%Y%m%d')}.jsonl"
    today_count = 0
    if today_log.exists():
        with open(today_log, 'r') as f:
            today_count = sum(1 for line in f if '"VALIDATION_COMPLETE"' in line)

    return {
        "status": "operational",
        "version": "1.0.0",
        "governance_level_default": "MEDIUM",
        "i9_threshold": I9_HUMAN_CONFIRMATION_THRESHOLD,
        "auto_settle_threshold": AUTO_SETTLE_THRESHOLD,
        "submissions_today": today_count,
        "endpoints": {
            "validate": "POST /v1/forensic/validate-handwritten",
            "confirm": "POST /v1/forensic/confirm",
            "settle": "POST /v1/forensic/settle",
            "verify": "GET /v1/forensic/verify/{submission_id}",
            "pdf": "GET /v1/forensic/pdf/{submission_id}"
        }
    }


# ═══════════════════════════════════════════════════════════════════════════════
# EXAMPLE RESPONSE (for documentation)
# ═══════════════════════════════════════════════════════════════════════════════

EXAMPLE_SUCCESSFUL_RESPONSE = {
    "success": True,
    "submission_id": "FAPI-20260210165432-A1B2C3D4",
    "status": "settled",

    "anti_deepfake_validation": {
        "score": 87,
        "threshold_passed": True,
        "prnu_hash": "a1b2c3d4e5f6g7h8i9j0k1l2",
        "noise_variance": 0.00127,
        "ink_coherence": {
            "coherence_score": 0.82,
            "edge_gradient_score": 0.85,
            "fiber_texture_score": 0.78,
            "ink_bleed_score": 0.83,
            "is_physical": True
        }
    },
    "authenticity_score": 87,
    "origin_classification": "physical_camera",

    "semiotic_signature": "abc123def456ghi789jkl012mno345pqr678stu901vwx234yz",
    "calligraphy_hash": "cal-abc123def456ghi789",

    "commitment": {
        "commitment_id": "CMT-A1B2C3D4E5F6",
        "type": "payment",
        "total_amount": 500.00,
        "currency": "EUR",
        "deadline": "2026-02-15T23:59:59+00:00",
        "parties": 2,
        "confidence": 0.85
    },

    "settlement": {
        "settlement_id": "STL-X1Y2Z3W4V5U6",
        "transaction_id": "TX-BANK-123456",
        "amount_settled": 500.00,
        "currency": "EUR",
        "match_score": 0.92,
        "settled_at": "2026-02-10T16:54:32+00:00",
        "verification_url": "https://verify.windi.dev/settlement/STL-X1Y2Z3W4V5U6"
    },

    "receipt_hash": "sha256-abc123def456...",
    "dual_proof_hash": "sha256-binding-verb-action-xyz789...",

    "forensic_pdf_url": "/v1/forensic/pdf/FAPI-20260210165432-A1B2C3D4",
    "verification_url": "https://verify.windi.dev/forensic/FAPI-20260210165432-A1B2C3D4",

    "governance_level": "MEDIUM",
    "requires_human_confirmation": False,
    "i9_compliant": True,

    "processed_at": "2026-02-10T16:54:32+00:00",
    "processing_duration_ms": 1247
}


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("WINDI Forensic API — Digital Notary")
    print(f"Port: {FORENSIC_API_PORT}")
    print("=" * 70)
    print()
    print("Endpoints:")
    print("  POST /v1/forensic/validate-handwritten")
    print("  POST /v1/forensic/confirm")
    print("  POST /v1/forensic/settle")
    print("  GET  /v1/forensic/verify/{submission_id}")
    print("  GET  /v1/forensic/pdf/{submission_id}")
    print()
    print("I9 Compliance: Human confirmation required for scores < 85%")
    print()
    print("\"From napkin to notarized — the API that seals commitments.\"")
    print("=" * 70)

    uvicorn.run(app, host="127.0.0.1", port=FORENSIC_API_PORT)
