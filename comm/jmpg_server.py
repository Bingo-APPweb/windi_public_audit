#!/usr/bin/env python3
"""
W-JMPG-001 — JPEG Manifest Proof Graphic Server
§134 · Liga IA+H · Kempten, Bavaria · 05 Abril 2026

Port: 8132
Endpoints:
  POST /comm/render/jmpg - Render a proof card
  GET  /comm/render/jmpg/{receipt_id} - Get existing or render new
  GET  /comm/jmpg/{filename} - Serve rendered images
  GET  /comm/health - Health check
"""

import os
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

from jmpg_renderer import render_jmpg, OUTPUT_DIR, PROFILES

# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

PORT = 8132
SERVICE_NAME = "W-JMPG-001"
VERSION = "1.0.0"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(SERVICE_NAME)

# ═══════════════════════════════════════════════════════════════════════════════
# FastAPI App
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title=SERVICE_NAME,
    description="JPEG Manifest Proof Graphic Renderer",
    version=VERSION,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════════════════════════

class RenderRequest(BaseModel):
    receipt_id: str
    profile: str = "telegram_square"
    title: Optional[str] = None
    subtitle: Optional[str] = None
    source_app: Optional[str] = None
    content_hash: Optional[str] = None


class RenderResponse(BaseModel):
    ok: bool
    receipt_id: Optional[str] = None
    profile: Optional[str] = None
    image_path: Optional[str] = None
    image_url: Optional[str] = None
    verify_url: Optional[str] = None
    error: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/comm/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": VERSION,
        "port": PORT,
        "profiles": list(PROFILES.keys()),
        "output_dir": str(OUTPUT_DIR),
    }


@app.post("/comm/render/jmpg", response_model=RenderResponse)
async def render_proof_card(request: RenderRequest):
    """
    Render a JMPG proof card from receipt_id.

    Profiles:
    - telegram_square: 1080x1080 (default)
    - telegram_landscape: 1600x900
    - story_vertical: 1080x1920
    """
    log.info(f"Render request: {request.receipt_id} profile={request.profile}")

    result = render_jmpg(
        receipt_id=request.receipt_id,
        profile=request.profile,
        title=request.title,
        subtitle=request.subtitle,
        source_app=request.source_app,
        content_hash=request.content_hash,
    )

    if result["ok"]:
        # Build public URL
        filename = Path(result["image_path"]).name
        image_url = f"https://windi-domain.com/comm/jmpg/{filename}"

        log.info(f"Rendered: {result['image_path']}")

        return RenderResponse(
            ok=True,
            receipt_id=result["receipt_id"],
            profile=result["profile"],
            image_path=result["image_path"],
            image_url=image_url,
            verify_url=result["verify_url"],
        )
    else:
        log.error(f"Render failed: {result.get('error')}")
        return RenderResponse(ok=False, error=result.get("error"))


@app.get("/comm/render/jmpg/{receipt_id}")
async def get_or_render(
    receipt_id: str,
    profile: str = "telegram_square",
    title: Optional[str] = None,
):
    """
    Get existing JMPG or render a new one.
    Returns the image file directly.
    """
    # Check if already exists
    filename = f"{receipt_id}_{profile}.jpg"
    existing = OUTPUT_DIR / filename

    if not existing.exists():
        # Render new
        log.info(f"Rendering new: {receipt_id}")
        result = render_jmpg(
            receipt_id=receipt_id,
            profile=profile,
            title=title,
        )
        if not result["ok"]:
            raise HTTPException(status_code=500, detail=result.get("error"))

    # Return the image
    return FileResponse(
        str(existing),
        media_type="image/jpeg",
        filename=filename,
    )


@app.get("/comm/jmpg/{filename}")
async def serve_image(filename: str):
    """Serve a rendered JMPG image."""
    filepath = OUTPUT_DIR / filename

    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    if not filepath.suffix.lower() in [".jpg", ".jpeg"]:
        raise HTTPException(status_code=400, detail="Invalid file type")

    return FileResponse(
        str(filepath),
        media_type="image/jpeg",
        filename=filename,
    )


@app.get("/comm/profiles")
async def list_profiles():
    """List available render profiles."""
    return {
        "profiles": {
            name: {"width": dims[0], "height": dims[1]}
            for name, dims in PROFILES.items()
        }
    }


@app.get("/comm/list")
async def list_rendered():
    """List all rendered JMPG files."""
    files = list(OUTPUT_DIR.glob("*.jpg"))
    return {
        "count": len(files),
        "files": [
            {
                "filename": f.name,
                "size": f.stat().st_size,
                "url": f"https://windi-domain.com/comm/jmpg/{f.name}",
            }
            for f in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[:50]
        ],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    log.info("=" * 50)
    log.info(f"{SERVICE_NAME} — WINDI JMPG Renderer")
    log.info("=" * 50)
    log.info(f"Port: {PORT}")
    log.info(f"Output: {OUTPUT_DIR}")
    log.info(f"Profiles: {list(PROFILES.keys())}")
    log.info("=" * 50)

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=PORT,
        log_level="info",
    )
