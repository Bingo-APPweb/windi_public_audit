"""
WINDI Product Template — Activates a new product in 1 hour

Copy this file and customize for your product.
All products share the WINDI Core Protocol.

"Cada produto é um idioma. O CORE é a gramática."

Liga IA+H · Kempten, Bavaria · 2026

Usage:
    1. Copy this file to /opt/windi/{your-product}/
    2. Rename to {your_product}_server.py
    3. Customize PRODUCT_CONFIG
    4. Implement your specific endpoints
    5. Run: python3 {your_product}_server.py
"""

import os
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import uvicorn

# Import WINDI Core SDK
import sys
sys.path.insert(0, "/opt/windi/sdk")
from windi_core import seal, ledger, render_jmpg, distribute
from windi_core.models import WindiProduct

# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOMIZE THIS SECTION FOR YOUR PRODUCT
# ═══════════════════════════════════════════════════════════════════════════════

PRODUCT_CONFIG = WindiProduct(
    name="WINDI Example Product",
    code="EXAMPLE",  # Will appear in receipts: WINDI-EXAMPLE-20260405...
    port=8199,       # Choose an available port
    description="Template for new WINDI products",
    artifact_types=["application/pdf", "image/jpeg", "image/png"],
)

# ═══════════════════════════════════════════════════════════════════════════════
# Standard Setup (usually no changes needed)
# ═══════════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
log = logging.getLogger(f"W-{PRODUCT_CONFIG.code}-001")

app = FastAPI(
    title=f"W-{PRODUCT_CONFIG.code}-001",
    description=PRODUCT_CONFIG.description,
    version="1.0.0",
)

MEDIA_DIR = Path(f"/opt/windi/media/{PRODUCT_CONFIG.code.lower()}")
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Models (customize as needed)
# ═══════════════════════════════════════════════════════════════════════════════

class SealRequest(BaseModel):
    artifact_id: str
    wallet_id: str
    title: Optional[str] = None
    human_approved: bool = True  # I9: Must be True


class SealResponse(BaseModel):
    ok: bool
    receipt_id: Optional[str] = None
    verify_url: Optional[str] = None
    jmpg_url: Optional[str] = None
    error: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Standard Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": f"W-{PRODUCT_CONFIG.code}-001",
        "product": PRODUCT_CONFIG.name,
        "port": PRODUCT_CONFIG.port,
        "invariants": PRODUCT_CONFIG.invariants,
    }


@app.post("/upload")
async def upload_artifact(
    file: UploadFile = File(...),
    wallet_id: str = "anonymous",
):
    """Upload an artifact for processing."""
    # Validate file type
    if file.content_type not in PRODUCT_CONFIG.artifact_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {PRODUCT_CONFIG.artifact_types}"
        )

    # Generate artifact ID
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    artifact_id = f"{PRODUCT_CONFIG.code}-{timestamp}-{os.urandom(4).hex().upper()}"

    # Save file
    artifact_path = MEDIA_DIR / f"{artifact_id}_{file.filename}"
    content = await file.read()
    artifact_path.write_bytes(content)

    log.info(f"Artifact uploaded: {artifact_id} ({len(content)} bytes)")

    return {
        "ok": True,
        "artifact_id": artifact_id,
        "filename": file.filename,
        "size": len(content),
        "path": str(artifact_path),
    }


@app.post("/seal", response_model=SealResponse)
async def seal_artifact(request: SealRequest):
    """
    Seal an artifact using WINDI Core Protocol.

    This is where the magic happens:
    1. Compute hash (seal)
    2. Anchor to Ledger (I11)
    3. Render proof card (JMPG)
    """
    # I9: Human approval check
    if not request.human_approved:
        return SealResponse(
            ok=False,
            error="I9 violation: human_approved must be True"
        )

    # Find artifact
    artifact_files = list(MEDIA_DIR.glob(f"{request.artifact_id}_*"))
    if not artifact_files:
        return SealResponse(ok=False, error=f"Artifact not found: {request.artifact_id}")

    artifact_path = artifact_files[0]
    log.info(f"Sealing artifact: {artifact_path}")

    # 1. SEAL — Compute hash
    seal_result = await seal(
        artifact_path,
        wallet_id=request.wallet_id,
        human_approved=True,
        title=request.title,
    )

    if not seal_result.ok:
        return SealResponse(ok=False, error=seal_result.error)

    # 2. LEDGER — Anchor eternally
    receipt = await ledger(
        seal_result,
        doc_type=PRODUCT_CONFIG.code.lower(),
        doc_name=request.title or artifact_path.name,
        app=f"W-{PRODUCT_CONFIG.code}-001",
    )

    if not receipt.ok:
        return SealResponse(ok=False, error=receipt.error)

    log.info(f"Sealed: {receipt.receipt_id}")

    # 3. RENDER — Create proof card
    jmpg = await render_jmpg(
        receipt.receipt_id,
        title=request.title,
        source_app=PRODUCT_CONFIG.code,
    )

    return SealResponse(
        ok=True,
        receipt_id=receipt.receipt_id,
        verify_url=receipt.verify_url,
        jmpg_url=jmpg.image_url if jmpg.ok else None,
    )


@app.post("/distribute")
async def distribute_proof(
    receipt_id: str,
    chat_id: str,
    title: Optional[str] = None,
    lang: str = "EN",
):
    """Distribute proof card via Telegram."""
    result = await distribute(
        receipt_id,
        channel="telegram",
        chat_id=chat_id,
        title=title,
        lang=lang,
    )

    return {
        "ok": result.ok,
        "channel": result.channel,
        "message_id": result.message_id,
        "error": result.error,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# YOUR CUSTOM ENDPOINTS GO HERE
# ═══════════════════════════════════════════════════════════════════════════════

# Example: Add product-specific processing
# @app.post("/process")
# async def process_artifact(artifact_id: str):
#     """Your custom processing logic."""
#     pass


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    log.info("=" * 60)
    log.info(f"W-{PRODUCT_CONFIG.code}-001 — {PRODUCT_CONFIG.name}")
    log.info("=" * 60)
    log.info(f"Port: {PRODUCT_CONFIG.port}")
    log.info(f"Invariants: {PRODUCT_CONFIG.invariants}")
    log.info(f"Media: {MEDIA_DIR}")
    log.info("=" * 60)

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=PRODUCT_CONFIG.port,
        log_level="info",
    )
