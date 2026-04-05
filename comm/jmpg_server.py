#!/usr/bin/env python3
"""
W-JMPG-001 — JPEG Manifest Proof Graphic Server
§134-137 · Liga IA+H · Kempten, Bavaria · 05 Abril 2026

Port: 8132
Endpoints:
  POST /comm/render/jmpg - Render a proof card
  GET  /comm/render/jmpg/{receipt_id} - Get existing or render new
  GET  /comm/jmpg/{filename} - Serve rendered images
  POST /comm/distribute - Distribute proof card (Telegram - PRIVATE chats)
  POST /comm/communique - Send institutional communiqué (§136 - PRIVATE)
  POST /comm/publish - §137 PUBLIC distribution (LINK ONLY - §122.4 compliant)
  GET  /comm/health - Health check

"Não publicamos conteúdo. Emitimos prova."
"O canal Telegram não transmite ficheiros. Transmite acesso."
"""

import os
import logging
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv
import httpx

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

from jmpg_renderer import render_jmpg, OUTPUT_DIR, PROFILES

# Load environment from nomad-bot (shares Telegram token)
load_dotenv("/opt/windi/nomad-bot/.env")

# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

PORT = 8132
SERVICE_NAME = "W-JMPG-001"
VERSION = "1.3.0"  # §137 Medium-Agnostic Distribution

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}" if TELEGRAM_BOT_TOKEN else None

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(SERVICE_NAME)


# ═══════════════════════════════════════════════════════════════════════════════
# Telegram Distribution (§135)
# ═══════════════════════════════════════════════════════════════════════════════

def build_telegram_caption(receipt_id: str, verify_url: str, title: Optional[str] = None) -> str:
    """Build HTML caption for Telegram photo."""
    title_text = title or "Sealed content"
    return f"""🎥 <b>WINDI Proof Card</b>

{title_text}

<b>Receipt:</b>
<code>{receipt_id}</code>

🔐 <a href="{verify_url}">Verify authenticity</a>

<i>Protocol: .jmpg v1</i>"""


# ══════════════════════════════════════════════════════════════════���════════════
# Communiqué Generator (§136)
# ═══════════════════════════════════════════════════════════════════════════════

COMMUNIQUE_TEMPLATES = {
    "PT": """📢 <b>WINDI Communiqué</b>

{title}

Este conteúdo foi registado e selado no WINDI Forensic Ledger.
Verificável publicamente com integridade criptográfica garantida.

<b>Receipt:</b>
<code>{receipt_id}</code>

🔐 <a href="{verify_url}">Verificar autenticidade</a>

<i>Protocol: .jmpg v1 · Liga IA+H</i>""",

    "EN": """📢 <b>WINDI Communiqué</b>

{title}

This content has been sealed in the WINDI Forensic Ledger.
Publicly verifiable with guaranteed cryptographic integrity.

<b>Receipt:</b>
<code>{receipt_id}</code>

🔐 <a href="{verify_url}">Verify authenticity</a>

<i>Protocol: .jmpg v1 · Liga IA+H</i>""",

    "DE": """📢 <b>WINDI Communiqué</b>

{title}

Dieser Inhalt wurde im WINDI Forensic Ledger versiegelt.
Öffentlich verifizierbar mit garantierter kryptographischer Integrität.

<b>Receipt:</b>
<code>{receipt_id}</code>

🔐 <a href="{verify_url}">Authentizität verifizieren</a>

<i>Protocol: .jmpg v1 · Liga IA+H</i>""",
}

DEFAULT_TITLES = {
    "PT": "Momento registado com prova pública.",
    "EN": "Moment sealed with public proof.",
    "DE": "Moment mit öffentlichem Nachweis versiegelt.",
}


# ═══════════════════════════════════════════════════════════════════════════════
# §137 — Public Distribution Templates (LINK ONLY)
# ═══════════════════════════════════════════════════════════════════════════════

PUBLIC_TEMPLATES = {
    "PT": """🔐 <b>WINDI — Verified Truth</b>

{title}

Prova selada e verificável independentemente.

🔗 <a href="{verify_url}">Verificar autenticidade</a>

#WINDIProof #VerifiedTruth""",

    "EN": """🔐 <b>WINDI — Verified Truth</b>

{title}

Sealed proof. Independently verifiable.

🔗 <a href="{verify_url}">Verify authenticity</a>

#WINDIProof #VerifiedTruth""",

    "DE": """🔐 <b>WINDI — Verified Truth</b>

{title}

Versiegelte Beweis. Unabhängig verifizierbar.

🔗 <a href="{verify_url}">Authentizität verifizieren</a>

#WINDIProof #VerifiedTruth""",
}


def generate_public_post(
    receipt_id: str,
    verify_url: str,
    lang: str = "EN",
    title: Optional[str] = None,
) -> str:
    """
    Generate public post text (§137 compliant).

    The medium points to the proof. It never carries the proof.
    """
    lang = lang.upper()
    if lang not in PUBLIC_TEMPLATES:
        lang = "EN"

    title_text = title or DEFAULT_TITLES.get(lang, DEFAULT_TITLES["EN"])

    return PUBLIC_TEMPLATES[lang].format(
        title=title_text,
        verify_url=verify_url,
    )


def generate_communique(
    receipt_id: str,
    verify_url: str,
    lang: str = "EN",
    title: Optional[str] = None,
) -> str:
    """Generate institutional communiqué text."""
    lang = lang.upper()
    if lang not in COMMUNIQUE_TEMPLATES:
        lang = "EN"

    title_text = title or DEFAULT_TITLES.get(lang, DEFAULT_TITLES["EN"])

    return COMMUNIQUE_TEMPLATES[lang].format(
        title=title_text,
        receipt_id=receipt_id,
        verify_url=verify_url,
    )


async def send_telegram_photo(
    chat_id: str,
    photo_path: str,
    caption: str,
    reply_to_message_id: Optional[int] = None,
) -> dict:
    """
    Send photo to Telegram chat using sendPhoto API.

    WARNING: Use only for PRIVATE chats where hash integrity
    is not critical. For PUBLIC distribution, use send_telegram_link()
    per §122.4 (Telegram transcodes images, breaking SHA-256).
    """
    if not TELEGRAM_API_URL:
        return {"ok": False, "error": "Telegram not configured"}

    url = f"{TELEGRAM_API_URL}/sendPhoto"

    try:
        async with httpx.AsyncClient() as client:
            with open(photo_path, "rb") as photo:
                files = {"photo": photo}
                data = {
                    "chat_id": chat_id,
                    "caption": caption,
                    "parse_mode": "HTML",
                }
                if reply_to_message_id:
                    data["reply_to_message_id"] = reply_to_message_id

                response = await client.post(url, data=data, files=files, timeout=30.0)
                result = response.json()

                if result.get("ok"):
                    log.info(f"Telegram photo sent to {chat_id}")
                else:
                    log.error(f"Telegram error: {result}")

                return result

    except Exception as e:
        log.error(f"Telegram send failed: {e}")
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════���═══════
# §137 — Medium-Agnostic Distribution (§122.4 Compliant)
# ═══════════════════════════════════════════════════════════════════════════════

async def send_telegram_link(
    chat_id: str,
    text: str,
    reply_to_message_id: Optional[int] = None,
    disable_web_page_preview: bool = False,
) -> dict:
    """
    Send text message to Telegram (LINK ONLY — no files).

    §122.4 Compliant: Telegram = interface, not file transport.
    The medium points to the proof. It never carries the proof.
    """
    if not TELEGRAM_API_URL:
        return {"ok": False, "error": "Telegram not configured"}

    url = f"{TELEGRAM_API_URL}/sendMessage"

    try:
        async with httpx.AsyncClient() as client:
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": disable_web_page_preview,
            }
            if reply_to_message_id:
                data["reply_to_message_id"] = reply_to_message_id

            response = await client.post(url, json=data, timeout=30.0)
            result = response.json()

            if result.get("ok"):
                log.info(f"Telegram link sent to {chat_id}")
            else:
                log.error(f"Telegram error: {result}")

            return result

    except Exception as e:
        log.error(f"Telegram send failed: {e}")
        return {"ok": False, "error": str(e)}

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


class DistributeRequest(BaseModel):
    receipt_id: str
    channel: str = "telegram"
    chat_id: Optional[str] = None
    title: Optional[str] = None
    reply_to_message_id: Optional[int] = None


class DistributeResponse(BaseModel):
    ok: bool
    channel: str
    receipt_id: str
    image_url: Optional[str] = None
    telegram_result: Optional[dict] = None
    error: Optional[str] = None


class CommuniqueRequest(BaseModel):
    receipt_id: str
    lang: str = "EN"
    channel: str = "telegram"
    chat_id: Optional[str] = None
    title: Optional[str] = None
    reply_to_message_id: Optional[int] = None


class CommuniqueResponse(BaseModel):
    ok: bool
    receipt_id: str
    lang: str
    channel: str
    image_url: Optional[str] = None
    communique_text: Optional[str] = None
    telegram_result: Optional[dict] = None
    error: Optional[str] = None


class PublishRequest(BaseModel):
    """§137 Public Distribution — Link Only (§122.4 Compliant)"""
    receipt_id: str
    lang: str = "EN"
    channel: str = "telegram"
    chat_id: str  # Required — typically the public channel
    title: Optional[str] = None


class PublishResponse(BaseModel):
    """§137 Response — No files transmitted"""
    ok: bool
    receipt_id: str
    lang: str
    channel: str
    verify_url: str
    jmpg_url: str
    post_text: str
    telegram_result: Optional[dict] = None
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
        "telegram_configured": TELEGRAM_BOT_TOKEN is not None,
        "channels": ["telegram"],
        "distribution_modes": {
            "private": "/comm/distribute, /comm/communique (sendPhoto)",
            "public": "/comm/publish (sendMessage - LINK ONLY, §122.4)",
        },
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
# Distribution Endpoint (§135)
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/comm/distribute", response_model=DistributeResponse)
async def distribute_proof_card(request: DistributeRequest):
    """
    Distribute a proof card via specified channel.

    Channels:
    - telegram: Send photo to Telegram chat (requires chat_id)

    The JMPG is auto-rendered if not already existing.
    """
    log.info(f"Distribute request: {request.receipt_id} via {request.channel}")

    # Build verify URL
    verify_url = f"https://windi-domain.com/verify-public/?id={request.receipt_id}"

    # Check/render JMPG
    filename = f"{request.receipt_id}_telegram_square.jpg"
    image_path = OUTPUT_DIR / filename

    if not image_path.exists():
        log.info(f"Auto-rendering JMPG for distribution: {request.receipt_id}")
        result = render_jmpg(
            receipt_id=request.receipt_id,
            profile="telegram_square",
            title=request.title,
        )
        if not result["ok"]:
            return DistributeResponse(
                ok=False,
                channel=request.channel,
                receipt_id=request.receipt_id,
                error=f"Render failed: {result.get('error')}",
            )
        image_path = Path(result["image_path"])

    image_url = f"https://windi-domain.com/comm/jmpg/{filename}"

    # Distribute based on channel
    if request.channel == "telegram":
        if not request.chat_id:
            return DistributeResponse(
                ok=False,
                channel="telegram",
                receipt_id=request.receipt_id,
                error="chat_id required for Telegram distribution",
            )

        if not TELEGRAM_BOT_TOKEN:
            return DistributeResponse(
                ok=False,
                channel="telegram",
                receipt_id=request.receipt_id,
                error="Telegram not configured (missing BOT_TOKEN)",
            )

        # Build caption
        caption = build_telegram_caption(
            receipt_id=request.receipt_id,
            verify_url=verify_url,
            title=request.title,
        )

        # Send photo
        telegram_result = await send_telegram_photo(
            chat_id=request.chat_id,
            photo_path=str(image_path),
            caption=caption,
            reply_to_message_id=request.reply_to_message_id,
        )

        return DistributeResponse(
            ok=telegram_result.get("ok", False),
            channel="telegram",
            receipt_id=request.receipt_id,
            image_url=image_url,
            telegram_result=telegram_result,
            error=telegram_result.get("error") if not telegram_result.get("ok") else None,
        )

    else:
        return DistributeResponse(
            ok=False,
            channel=request.channel,
            receipt_id=request.receipt_id,
            error=f"Unknown channel: {request.channel}. Supported: telegram",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Communiqué Endpoint (§136)
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/comm/communique", response_model=CommuniqueResponse)
async def send_communique(request: CommuniqueRequest):
    """
    Send an institutional communiqué with proof card.

    This is the official WINDI communication format:
    - Institutional language (PT/EN/DE)
    - JMPG proof card attached
    - Cryptographic verification link

    "Não publicamos conteúdo. Emitimos prova."
    """
    log.info(f"Communiqué request: {request.receipt_id} lang={request.lang} via {request.channel}")

    # Build verify URL
    verify_url = f"https://windi-domain.com/verify-public/?id={request.receipt_id}"

    # Check/render JMPG
    filename = f"{request.receipt_id}_telegram_square.jpg"
    image_path = OUTPUT_DIR / filename

    if not image_path.exists():
        log.info(f"Auto-rendering JMPG for communiqué: {request.receipt_id}")
        result = render_jmpg(
            receipt_id=request.receipt_id,
            profile="telegram_square",
            title=request.title,
        )
        if not result["ok"]:
            return CommuniqueResponse(
                ok=False,
                receipt_id=request.receipt_id,
                lang=request.lang,
                channel=request.channel,
                error=f"Render failed: {result.get('error')}",
            )
        image_path = Path(result["image_path"])

    image_url = f"https://windi-domain.com/comm/jmpg/{filename}"

    # Generate communiqué text
    communique_text = generate_communique(
        receipt_id=request.receipt_id,
        verify_url=verify_url,
        lang=request.lang,
        title=request.title,
    )

    # Distribute based on channel
    if request.channel == "telegram":
        if not request.chat_id:
            return CommuniqueResponse(
                ok=False,
                receipt_id=request.receipt_id,
                lang=request.lang,
                channel="telegram",
                communique_text=communique_text,
                error="chat_id required for Telegram distribution",
            )

        if not TELEGRAM_BOT_TOKEN:
            return CommuniqueResponse(
                ok=False,
                receipt_id=request.receipt_id,
                lang=request.lang,
                channel="telegram",
                error="Telegram not configured (missing BOT_TOKEN)",
            )

        # Send photo with communiqué caption
        telegram_result = await send_telegram_photo(
            chat_id=request.chat_id,
            photo_path=str(image_path),
            caption=communique_text,
            reply_to_message_id=request.reply_to_message_id,
        )

        return CommuniqueResponse(
            ok=telegram_result.get("ok", False),
            receipt_id=request.receipt_id,
            lang=request.lang,
            channel="telegram",
            image_url=image_url,
            communique_text=communique_text,
            telegram_result=telegram_result,
            error=telegram_result.get("error") if not telegram_result.get("ok") else None,
        )

    else:
        return CommuniqueResponse(
            ok=False,
            receipt_id=request.receipt_id,
            lang=request.lang,
            channel=request.channel,
            communique_text=communique_text,
            error=f"Unknown channel: {request.channel}. Supported: telegram",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# §137 — Public Distribution (§122.4 Compliant — LINK ONLY)
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/comm/publish", response_model=PublishResponse)
async def publish_to_channel(request: PublishRequest):
    """
    §137 — Medium-Agnostic Truth Distribution (§122.4 Compliant)

    SENDS LINK ONLY — NO FILES.

    This endpoint is for PUBLIC distribution where hash integrity matters.
    Telegram transcodes images, breaking SHA-256 verification.

    The medium POINTS to the proof. It never CARRIES the proof.

    "O canal Telegram não transmite ficheiros. Transmite acesso."
    """
    log.info(f"§137 Publish: {request.receipt_id} lang={request.lang} to {request.chat_id}")

    # Build URLs
    verify_url = f"https://windi-domain.com/verify-public/?id={request.receipt_id}"
    filename = f"{request.receipt_id}_telegram_square.jpg"
    jmpg_url = f"https://windi-domain.com/comm/jmpg/{filename}"

    # Ensure JMPG exists (renders if needed — but we DON'T send it)
    image_path = OUTPUT_DIR / filename
    if not image_path.exists():
        log.info(f"Pre-rendering JMPG for public access: {request.receipt_id}")
        result = render_jmpg(
            receipt_id=request.receipt_id,
            profile="telegram_square",
            title=request.title,
        )
        if not result["ok"]:
            return PublishResponse(
                ok=False,
                receipt_id=request.receipt_id,
                lang=request.lang,
                channel=request.channel,
                verify_url=verify_url,
                jmpg_url=jmpg_url,
                post_text="",
                error=f"JMPG render failed: {result.get('error')}",
            )

    # Generate public post text (contains ONLY the link)
    post_text = generate_public_post(
        receipt_id=request.receipt_id,
        verify_url=verify_url,
        lang=request.lang,
        title=request.title,
    )

    # Distribute based on channel
    if request.channel == "telegram":
        if not TELEGRAM_BOT_TOKEN:
            return PublishResponse(
                ok=False,
                receipt_id=request.receipt_id,
                lang=request.lang,
                channel="telegram",
                verify_url=verify_url,
                jmpg_url=jmpg_url,
                post_text=post_text,
                error="Telegram not configured (missing BOT_TOKEN)",
            )

        # §122.4: Send LINK ONLY — no files
        # disable_web_page_preview=False so Telegram shows preview of verify page
        telegram_result = await send_telegram_link(
            chat_id=request.chat_id,
            text=post_text,
            disable_web_page_preview=False,  # Let Telegram preview the verify link
        )

        return PublishResponse(
            ok=telegram_result.get("ok", False),
            receipt_id=request.receipt_id,
            lang=request.lang,
            channel="telegram",
            verify_url=verify_url,
            jmpg_url=jmpg_url,
            post_text=post_text,
            telegram_result=telegram_result,
            error=telegram_result.get("error") if not telegram_result.get("ok") else None,
        )

    else:
        return PublishResponse(
            ok=False,
            receipt_id=request.receipt_id,
            lang=request.lang,
            channel=request.channel,
            verify_url=verify_url,
            jmpg_url=jmpg_url,
            post_text=post_text,
            error=f"Unknown channel: {request.channel}. Supported: telegram",
        )


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
