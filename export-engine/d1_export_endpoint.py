"""
WINDI M3 Export API Endpoint
=============================
Drop-in addition to d1_api.py (FastAPI on :8100)

Add this import and route to your existing D1 API:

    from windi_export_engine import export_document_pdf
    # Then add the /api/export route below

Or run standalone for testing:
    python3 d1_export_endpoint.py
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import hashlib
from datetime import datetime, timezone

# Import the export engine
from windi_export_engine import export_document_pdf

# ═══════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════

class ExportRequest(BaseModel):
    """Request body for PDF export."""
    doc_title: str = "Untitled Document"
    doc_content_html: str = ""
    receipt_id: str = ""
    content_hash: str = ""
    timestamp: str = ""
    status: str = "REGISTERED"
    sge_score: Optional[str] = None
    risk_level: Optional[str] = None
    include_seal: bool = True
    include_receipt_block: bool = True


class ExportResponse(BaseModel):
    """Response metadata (when not returning raw PDF)."""
    success: bool
    filename: str
    size_bytes: int
    receipt_id: str


# ═══════════════════════════════════════════════════════════════
# STANDALONE APP (for testing — in production, merge into d1_api.py)
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title="WINDI M3 Export Engine",
    version="1.0.0",
    description="Server-side PDF export with Dynamic Header Seal",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://admin.windia4desk.tech",
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════


@app.get("/health")
async def health_root():
    return {"status": "sovereign", "engine": "export", "port": 8103, "version": "M3"}

@app.get("/api/export/health")
async def export_health():
    """Health check for the export engine."""
    return {
        "service": "WINDI M3 Export Engine",
        "version": "1.0.0",
        "status": "operational",
        "capabilities": ["pdf"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/export/pdf")
async def export_pdf(req: ExportRequest):
    """
    Generate a WINDI-branded PDF with Dynamic Header Seal.

    Returns the PDF as a binary response for direct download.
    """
    try:
        # Build receipt data dict
        receipt_data = {
            "receipt_id": req.receipt_id,
            "content_hash": req.content_hash,
            "timestamp": req.timestamp or datetime.now(timezone.utc).isoformat(),
            "status": req.status,
        }
        if req.sge_score:
            receipt_data["sge_score"] = req.sge_score
        if req.risk_level:
            receipt_data["risk_level"] = req.risk_level

        # Generate PDF
        pdf_bytes = export_document_pdf(
            doc_content_html=req.doc_content_html,
            receipt_data=receipt_data,
            doc_title=req.doc_title,
            include_seal=req.include_seal,
            include_receipt_block=req.include_receipt_block,
        )

        # Build filename from receipt_id
        safe_title = "".join(c if c.isalnum() or c in "._- " else "_"
                             for c in req.doc_title[:40]).strip()
        filename = f"WINDI_{safe_title}_{req.receipt_id}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-WINDI-Receipt": req.receipt_id,
                "X-WINDI-Hash": req.content_hash[:16] if req.content_hash else "",
                "X-WINDI-Engine": "M3-Export-v1.0",
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Export failed: {str(e)}",
        )


@app.post("/api/export/pdf/meta")
async def export_pdf_meta(req: ExportRequest):
    """
    Same as /api/export/pdf but returns metadata only (for pre-flight checks).
    """
    content_size = len(req.doc_content_html.encode('utf-8'))
    return ExportResponse(
        success=True,
        filename=f"WINDI_{req.receipt_id}.pdf",
        size_bytes=content_size,
        receipt_id=req.receipt_id,
    )


# ═══════════════════════════════════════════════════════════════
# STANDALONE RUNNER
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    print("🐉 WINDI M3 Export Engine starting on :8103...")
    uvicorn.run(app, host="0.0.0.0", port=8103)
