"""
W-DRAGON-001 — WINDI-SITES Integration Routes
FastAPI router for Dragon Shadow Forest endpoints

Port: :8122 (via WINDI-SITES identity_gate.py)
Invariants: I9 (Human Gate), I11 (Ledger Sovereignty), I14 (No Placeholders)

Endpoints:
  GET  /dragon/health         — Module health check
  POST /dragon/encode         — Encode content and return SVG + receipt
  POST /dragon/encode-pdf     — Encode PDF with dragon overlay
  GET  /dragon/verify/{id}    — Verify receipt with Ledger

Liga IA+H · Kempten, Bavaria · 2026
"""

import io
import base64
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Query, Request
from fastapi.responses import JSONResponse, Response, HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os

# Templates directory
TEMPLATES_DIR = "/opt/windi/windi-sites/identity-gate/templates"

from w_dragon_001 import (
    encode_document,
    verify_with_ledger,
    compute_hash,
    hash_to_bits,
    generate_svg_grid,
    generate_pdf_overlay,
    generate_pdf_overlay_forensic,
    merge_overlay_into_pdf,
    get_module_info,
    OPACITY_PRINT,
    OPACITY_SCREEN,
    PDF_SUPPORT,
    QR_SUPPORT,
    VERSION
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# ROUTER SETUP
# ═══════════════════════════════════════════════════════════════

dragon_router = APIRouter(prefix="/dragon", tags=["Dragon Shadow Forest"])


# ═══════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════

class EncodeRequest(BaseModel):
    """Request to encode content with Dragon Shadow Forest"""
    content: str  # Base64 encoded content
    doc_name: str = "Document"
    actor: str = "windi-dragon"
    register_ledger: bool = True
    svg_opacity: float = OPACITY_SCREEN


class EncodeResponse(BaseModel):
    """Response from encoding"""
    success: bool
    receipt_id: str
    content_hash: str
    svg_grid: str
    verify_url: str
    status: str
    message: str


class VerifyResponse(BaseModel):
    """Response from verification"""
    valid: bool
    receipt_id: str
    ledger_data: Optional[dict] = None
    message: str


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@dragon_router.get("/", response_class=HTMLResponse)
async def dragon_dashboard():
    """
    Dragon Shadow Forest Dashboard.
    Visual interface for encoding documents with dragon glyphs.
    Trilingual (DE|EN|PT) + NOIR/KLAR themes.
    """
    html_path = os.path.join(TEMPLATES_DIR, "dragon.html")
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    raise HTTPException(404, "Dashboard template not found")


@dragon_router.get("/howto", response_class=HTMLResponse)
async def dragon_howto():
    """
    Dragon Shadow Forest How-To Guide.
    Trilingual documentation (DE|EN|PT).
    """
    html_path = os.path.join(TEMPLATES_DIR, "dragon-howto.html")
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    raise HTTPException(404, "How-to template not found")


@dragon_router.get("/health")
async def dragon_health():
    """
    Health check for Dragon Shadow Forest module.

    Returns module info and status.
    """
    info = get_module_info()
    return JSONResponse(content={
        "status": "healthy",
        "module": info,
        "endpoints": {
            "dashboard": "/dragon/",
            "health": "/dragon/health",
            "encode": "/dragon/encode",
            "encode_pdf": "/dragon/encode-pdf",
            "verify": "/dragon/verify/{receipt_id}"
        }
    })


@dragon_router.post("/encode", response_model=EncodeResponse)
async def encode_content(request: EncodeRequest):
    """
    Encode content with Dragon Shadow Forest.

    Takes base64-encoded content and returns:
    - SVG grid visualization
    - Receipt ID
    - Content hash
    - Ledger registration status

    I9: Receipt registered at C5 (awaiting human approval)
    I11: Hash computed locally, verified by Ledger
    I14: No placeholders - all fields required
    """
    try:
        # Decode base64 content
        try:
            content = base64.b64decode(request.content)
        except Exception:
            raise HTTPException(400, "Invalid base64 content")

        if len(content) == 0:
            raise HTTPException(400, "Content cannot be empty (I14)")

        # Encode document
        result = await encode_document(
            content=content,
            doc_name=request.doc_name,
            actor=request.actor,
            generate_pdf=False,  # No PDF for basic encode
            svg_opacity=request.svg_opacity,
            register_ledger=request.register_ledger
        )

        return EncodeResponse(
            success=True,
            receipt_id=result.receipt.receipt_id,
            content_hash=result.receipt.content_hash,
            svg_grid=result.svg_grid,
            verify_url=result.verify_url,
            status=result.receipt.status,
            message=f"Dragon Shadow Forest encoded. Status: {result.receipt.status}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Encode error: {e}")
        raise HTTPException(500, f"Encoding failed: {str(e)}")


@dragon_router.post("/encode-pdf")
async def encode_pdf_document(
    pdf_file: UploadFile = File(..., description="PDF file to encode"),
    doc_name: str = Form("Document"),
    actor: str = Form("windi-dragon"),
    overlay_pages: str = Form("all", description="Pages to overlay: 'all', 'first', 'last', or '1,3,5'"),
    opacity: float = Form(OPACITY_PRINT, description="Dragon opacity (0.07 print, 0.18 screen)"),
    include_qr: bool = Form(True, description="Include visible QR code for easy verification"),
    include_microtext: bool = Form(True, description="Include micro-text (readable at 1200 DPI)"),
    register_ledger: bool = Form(True),
    return_format: str = Form("json", description="'json' for base64, 'pdf' for binary")
):
    """
    Encode PDF document with Dragon Shadow Forest overlay.

    FORENSIC FEATURES:
    - Dragon grid: invisible at 0.07 opacity, visible at 0.18
    - QR code: visible, bottom-right corner, links to verify URL
    - Micro-text: 3pt, receipt_id + hash, readable at 1200 DPI
    - PDF metadata: receipt_id, hash, verify URL in File → Properties

    WORKFLOW FOR LAWYERS:
    1. Open PDF → Properties → Custom → WINDI-Receipt
    2. OR scan QR code with phone → instant verification
    3. OR scan with 1200 DPI → read micro-text

    I9: Registered at C5 (human approval required for C6 seal)
    I11: Original hash preserved, overlay is separate layer
    I14: PDF must be valid, no empty files
    """
    if not PDF_SUPPORT:
        raise HTTPException(501, "PDF support not available. Install reportlab and PyPDF2.")

    # Validate file
    if not pdf_file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, "File must be a PDF")

    try:
        # Read PDF content
        pdf_content = await pdf_file.read()

        if len(pdf_content) == 0:
            raise HTTPException(400, "PDF file is empty (I14)")

        # Encode document (computes hash, registers with Ledger)
        result = await encode_document(
            content=pdf_content,
            doc_name=doc_name or pdf_file.filename,
            actor=actor,
            generate_pdf=False,  # We'll use forensic overlay instead
            pdf_opacity=opacity,
            register_ledger=register_ledger
        )

        # Generate forensic overlay (with QR + microtext)
        forensic_overlay = generate_pdf_overlay_forensic(
            bits=result.receipt.bits,
            receipt_id=result.receipt.receipt_id,
            content_hash=result.receipt.content_hash,
            verify_url=result.verify_url,
            opacity=opacity,
            include_qr=include_qr,
            include_microtext=include_microtext
        )

        if forensic_overlay is None:
            raise HTTPException(500, "Failed to generate forensic PDF overlay")

        # Merge overlay into original PDF (with metadata)
        merged_pdf = merge_overlay_into_pdf(
            original_pdf=pdf_content,
            overlay_pdf=forensic_overlay,
            pages=overlay_pages,
            receipt_id=result.receipt.receipt_id,
            content_hash=result.receipt.content_hash,
            verify_url=result.verify_url
        )

        # Return based on format
        if return_format == "pdf":
            return Response(
                content=merged_pdf,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="dsf_{result.receipt.receipt_id}.pdf"',
                    "X-DSF-Receipt-ID": result.receipt.receipt_id,
                    "X-DSF-Content-Hash": result.receipt.content_hash,
                    "X-DSF-Verify-URL": result.verify_url,
                    "X-DSF-QR-Included": str(include_qr and QR_SUPPORT).lower(),
                    "X-DSF-Forensic": "true"
                }
            )
        else:
            return JSONResponse(content={
                "success": True,
                "receipt_id": result.receipt.receipt_id,
                "content_hash": result.receipt.content_hash,
                "svg_grid": result.svg_grid,
                "pdf_base64": base64.b64encode(merged_pdf).decode('utf-8'),
                "verify_url": result.verify_url,
                "status": result.receipt.status,
                "overlay_pages": overlay_pages,
                "opacity": opacity,
                "forensic_features": {
                    "qr_code": include_qr and QR_SUPPORT,
                    "microtext": include_microtext,
                    "pdf_metadata": True
                },
                "message": f"PDF encoded with Dragon Shadow Forest (Forensic Mode). QR: {include_qr}, Microtext: {include_microtext}"
            })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF encode error: {e}")
        raise HTTPException(500, f"PDF encoding failed: {str(e)}")


@dragon_router.get("/verify/{receipt_id}")
async def verify_receipt(
    receipt_id: str,
    include_svg: bool = Query(False, description="Include SVG grid in response")
):
    """
    Verify Dragon Shadow Forest receipt with Forensic Ledger.

    I11 Compliance: Truth comes from Ledger, not local state.

    Returns:
    - valid: Whether receipt exists in Ledger
    - ledger_data: Full receipt data from Ledger
    - svg_grid: Optional SVG reconstruction
    """
    if not receipt_id.startswith("WINDI-DSF-"):
        raise HTTPException(400, "Invalid DSF receipt ID format. Expected WINDI-DSF-*")

    exists, ledger_data = await verify_with_ledger(receipt_id)

    response = {
        "valid": exists,
        "receipt_id": receipt_id,
        "message": "Receipt verified with Forensic Ledger" if exists else "Receipt not found in Ledger"
    }

    if exists and ledger_data:
        response["ledger_data"] = ledger_data

        # Optionally reconstruct SVG from hash
        if include_svg and "content_hash" in ledger_data:
            hash_hex = ledger_data["content_hash"].replace("sha256:", "")
            bits = hash_to_bits(hash_hex)
            response["svg_grid"] = generate_svg_grid(bits, opacity=OPACITY_SCREEN)

    return JSONResponse(content=response)


@dragon_router.post("/preview")
async def preview_hash(
    content: str = Form(..., description="Base64 encoded content"),
    opacity: float = Form(OPACITY_SCREEN)
):
    """
    Preview Dragon Shadow Forest without Ledger registration.

    Use for instant client-side preview before committing to Ledger.
    No receipt is created - this is visualization only.
    """
    try:
        decoded = base64.b64decode(content)
    except Exception:
        raise HTTPException(400, "Invalid base64 content")

    if len(decoded) == 0:
        raise HTTPException(400, "Content cannot be empty (I14)")

    content_hash = compute_hash(decoded)
    bits = hash_to_bits(content_hash)
    svg = generate_svg_grid(bits, opacity=opacity)

    return JSONResponse(content={
        "content_hash": content_hash,
        "svg_grid": svg,
        "preview_only": True,
        "message": "Preview only - not registered with Ledger. Use /encode to create receipt."
    })


# ═══════════════════════════════════════════════════════════════
# MODULE EXPORT
# ═══════════════════════════════════════════════════════════════

__all__ = ["dragon_router"]
