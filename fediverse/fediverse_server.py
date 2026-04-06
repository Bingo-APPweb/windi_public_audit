"""
W-FEDIVERSE-001 — Embaixada de Vidro (Glass Embassy)
Multi-Protocol Truth Distribution · Mastodon + BlueSky

Port: 8142
Liga IA+H · Kempten, Bavaria · 2026
"AI processes. Human decides. WINDI guarantees."

Architecture:
- Mastodon: ActivityPub API (OAuth2)
- BlueSky: AT Protocol (XRPC/App Passwords)
- Parallel broadcast for censorship resistance
- Same verify link, multiple distribution channels

"Se uma rede tentar silenciar, a outra mantém viva."
"""

import os
import json
import asyncio
import logging
import httpx
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv(Path(__file__).parent / ".env")
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configuration
PORT = int(os.environ.get("FEDIVERSE_PORT", 8142))
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

# Mastodon Configuration
MASTODON_INSTANCE = os.environ.get("MASTODON_INSTANCE", "https://mastodon.social")
MASTODON_ACCESS_TOKEN = os.environ.get("MASTODON_ACCESS_TOKEN", "")
MASTODON_HANDLE = os.environ.get("MASTODON_HANDLE", "@windi@mastodon.social")

# BlueSky Configuration
BLUESKY_SERVICE = os.environ.get("BLUESKY_SERVICE", "https://bsky.social")
BLUESKY_HANDLE = os.environ.get("BLUESKY_HANDLE", "windi.bsky.social")
BLUESKY_APP_PASSWORD = os.environ.get("BLUESKY_APP_PASSWORD", "")

# Logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
log = logging.getLogger("w-fediverse-001")

# FastAPI App
app = FastAPI(
    title="W-FEDIVERSE-001",
    description="Glass Embassy — Multi-Protocol Truth Distribution",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Data Models =====

@dataclass
class FederationResult:
    """Result of a federation broadcast."""
    platform: str
    success: bool
    post_url: Optional[str] = None
    post_id: Optional[str] = None
    error: Optional[str] = None


@dataclass
class BroadcastResult:
    """Combined result of multi-platform broadcast."""
    receipt_id: str
    verify_url: str
    platforms: List[Dict[str, Any]]
    broadcast_at: str
    total_reach: int  # Estimated federated reach
    success_count: int
    failure_count: int


class PublishRequest(BaseModel):
    """Request to publish to Fediverse."""
    receipt_id: str
    verify_url: str
    title: Optional[str] = "WINDI Verified"
    description: Optional[str] = None
    media_path: Optional[str] = None  # Path to video/image
    platforms: List[str] = ["mastodon", "bluesky"]  # Which platforms to publish to


# ===== Mastodon (ActivityPub) Bridge =====

class MastodonBridge:
    """
    Mastodon API Bridge using ActivityPub.

    Features:
    - OAuth2 authentication
    - Media upload (images/videos)
    - Status posting with CW (Content Warning) option
    - Federation across all Mastodon instances
    """

    def __init__(self, instance: str, access_token: str):
        self.instance = instance.rstrip("/")
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}"
        } if access_token else {}

    async def upload_media(self, file_path: Path, description: str = "") -> Optional[str]:
        """Upload media to Mastodon, return media_id."""
        if not self.access_token:
            log.warning("Mastodon: No access token, skipping media upload")
            return None

        if not file_path.exists():
            log.error(f"Mastodon: Media file not found: {file_path}")
            return None

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                with open(file_path, "rb") as f:
                    files = {"file": (file_path.name, f, "video/mp4")}
                    data = {"description": description[:1500]}  # Mastodon limit

                    response = await client.post(
                        f"{self.instance}/api/v2/media",
                        headers=self.headers,
                        files=files,
                        data=data
                    )

                    if response.status_code in [200, 202]:
                        result = response.json()
                        media_id = result.get("id")
                        log.info(f"Mastodon: Media uploaded: {media_id}")
                        return media_id
                    else:
                        log.error(f"Mastodon media upload failed: {response.status_code} - {response.text[:200]}")
                        return None

        except Exception as e:
            log.error(f"Mastodon media upload error: {e}")
            return None

    async def post_status(
        self,
        text: str,
        media_ids: Optional[List[str]] = None,
        content_warning: Optional[str] = None,
        visibility: str = "public"
    ) -> FederationResult:
        """
        Post a status to Mastodon.

        visibility options: public, unlisted, private, direct
        """
        if not self.access_token:
            return FederationResult(
                platform="mastodon",
                success=False,
                error="No access token configured"
            )

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                payload = {
                    "status": text,
                    "visibility": visibility
                }

                if media_ids:
                    payload["media_ids"] = media_ids

                if content_warning:
                    payload["spoiler_text"] = content_warning

                response = await client.post(
                    f"{self.instance}/api/v1/statuses",
                    headers=self.headers,
                    json=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    post_url = result.get("url")
                    post_id = result.get("id")
                    log.info(f"Mastodon: Posted successfully: {post_url}")

                    return FederationResult(
                        platform="mastodon",
                        success=True,
                        post_url=post_url,
                        post_id=post_id
                    )
                else:
                    error_msg = response.text[:200]
                    log.error(f"Mastodon post failed: {response.status_code} - {error_msg}")
                    return FederationResult(
                        platform="mastodon",
                        success=False,
                        error=error_msg
                    )

        except Exception as e:
            log.error(f"Mastodon post error: {e}")
            return FederationResult(
                platform="mastodon",
                success=False,
                error=str(e)
            )


# ===== BlueSky (AT Protocol) Bridge =====

class BlueSkyBridge:
    """
    BlueSky API Bridge using AT Protocol.

    Features:
    - App Password authentication
    - Blob upload for media
    - Post creation with facets (links, mentions)
    - Future: Labeler integration for truth verification
    """

    def __init__(self, service: str, handle: str, app_password: str):
        self.service = service.rstrip("/")
        self.handle = handle
        self.app_password = app_password
        self.session = None
        self.did = None

    async def create_session(self) -> bool:
        """Authenticate and create a session."""
        if not self.app_password:
            log.warning("BlueSky: No app password configured")
            return False

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.service}/xrpc/com.atproto.server.createSession",
                    json={
                        "identifier": self.handle,
                        "password": self.app_password
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    self.session = {
                        "accessJwt": result.get("accessJwt"),
                        "refreshJwt": result.get("refreshJwt")
                    }
                    self.did = result.get("did")
                    log.info(f"BlueSky: Session created for {self.handle}")
                    return True
                else:
                    log.error(f"BlueSky auth failed: {response.status_code} - {response.text[:200]}")
                    return False

        except Exception as e:
            log.error(f"BlueSky auth error: {e}")
            return False

    async def upload_blob(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Upload a blob (media) to BlueSky."""
        if not self.session:
            if not await self.create_session():
                return None

        if not file_path.exists():
            log.error(f"BlueSky: File not found: {file_path}")
            return None

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                with open(file_path, "rb") as f:
                    content = f.read()

                # Determine MIME type
                mime_type = "video/mp4" if file_path.suffix.lower() == ".mp4" else "image/jpeg"

                response = await client.post(
                    f"{self.service}/xrpc/com.atproto.repo.uploadBlob",
                    headers={
                        "Authorization": f"Bearer {self.session['accessJwt']}",
                        "Content-Type": mime_type
                    },
                    content=content
                )

                if response.status_code == 200:
                    result = response.json()
                    blob = result.get("blob")
                    log.info(f"BlueSky: Blob uploaded: {blob}")
                    return blob
                else:
                    log.error(f"BlueSky blob upload failed: {response.status_code}")
                    return None

        except Exception as e:
            log.error(f"BlueSky blob upload error: {e}")
            return None

    async def create_post(
        self,
        text: str,
        blob: Optional[Dict[str, Any]] = None,
        alt_text: str = ""
    ) -> FederationResult:
        """Create a post on BlueSky."""
        if not self.session:
            if not await self.create_session():
                return FederationResult(
                    platform="bluesky",
                    success=False,
                    error="Authentication failed"
                )

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Build record
                now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                record = {
                    "$type": "app.bsky.feed.post",
                    "text": text,
                    "createdAt": now
                }

                # Add embed if blob provided
                if blob:
                    record["embed"] = {
                        "$type": "app.bsky.embed.images",
                        "images": [{
                            "alt": alt_text or "WINDI Verified Content",
                            "image": blob
                        }]
                    }

                # Detect and add link facets
                facets = self._extract_link_facets(text)
                if facets:
                    record["facets"] = facets

                response = await client.post(
                    f"{self.service}/xrpc/com.atproto.repo.createRecord",
                    headers={
                        "Authorization": f"Bearer {self.session['accessJwt']}"
                    },
                    json={
                        "repo": self.did,
                        "collection": "app.bsky.feed.post",
                        "record": record
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    uri = result.get("uri")
                    cid = result.get("cid")

                    # Build post URL
                    post_id = uri.split("/")[-1] if uri else ""
                    post_url = f"https://bsky.app/profile/{self.handle}/post/{post_id}"

                    log.info(f"BlueSky: Posted successfully: {post_url}")

                    return FederationResult(
                        platform="bluesky",
                        success=True,
                        post_url=post_url,
                        post_id=post_id
                    )
                else:
                    error_msg = response.text[:200]
                    log.error(f"BlueSky post failed: {response.status_code} - {error_msg}")
                    return FederationResult(
                        platform="bluesky",
                        success=False,
                        error=error_msg
                    )

        except Exception as e:
            log.error(f"BlueSky post error: {e}")
            return FederationResult(
                platform="bluesky",
                success=False,
                error=str(e)
            )

    def _extract_link_facets(self, text: str) -> List[Dict[str, Any]]:
        """Extract URLs from text and create facets for BlueSky."""
        import re
        facets = []
        url_pattern = r'https?://[^\s]+'

        for match in re.finditer(url_pattern, text):
            start = match.start()
            end = match.end()
            url = match.group()

            # Convert to byte positions
            byte_start = len(text[:start].encode('utf-8'))
            byte_end = len(text[:end].encode('utf-8'))

            facets.append({
                "index": {
                    "byteStart": byte_start,
                    "byteEnd": byte_end
                },
                "features": [{
                    "$type": "app.bsky.richtext.facet#link",
                    "uri": url
                }]
            })

        return facets


# ===== Broadcast Engine =====

async def broadcast_truth(
    receipt_id: str,
    verify_url: str,
    title: str = "WINDI Verified",
    description: Optional[str] = None,
    media_path: Optional[str] = None,
    platforms: List[str] = ["mastodon", "bluesky"]
) -> BroadcastResult:
    """
    Broadcast verified content to multiple Fediverse platforms.

    Clarity Infinity format:
    🛡️ WINDI VERIFIED
    [Media]
    Receipt: {receipt_id}
    👉 VERIFY: {verify_url}
    #WINDIVerified #ForensicTruth
    """
    start_time = datetime.now(timezone.utc)
    results = []

    # Build Clarity Infinity post text
    post_text = f"""🛡️ WINDI VERIFIED

{title}

Receipt: {receipt_id}

👉 VERIFY: {verify_url}

#WINDIVerified #ForensicTruth #DigitalSovereignty"""

    # Mastodon
    if "mastodon" in platforms and MASTODON_ACCESS_TOKEN:
        mastodon = MastodonBridge(MASTODON_INSTANCE, MASTODON_ACCESS_TOKEN)

        media_id = None
        if media_path:
            media_id = await mastodon.upload_media(
                Path(media_path),
                description=f"WINDI Verified: {receipt_id}"
            )

        result = await mastodon.post_status(
            text=post_text,
            media_ids=[media_id] if media_id else None,
            content_warning="Forensic Evidence" if description and "forensic" in description.lower() else None
        )
        results.append(asdict(result))

    elif "mastodon" in platforms:
        results.append(asdict(FederationResult(
            platform="mastodon",
            success=False,
            error="Not configured (MASTODON_ACCESS_TOKEN missing)"
        )))

    # BlueSky
    if "bluesky" in platforms and BLUESKY_APP_PASSWORD:
        bluesky = BlueSkyBridge(BLUESKY_SERVICE, BLUESKY_HANDLE, BLUESKY_APP_PASSWORD)

        blob = None
        if media_path:
            blob = await bluesky.upload_blob(Path(media_path))

        result = await bluesky.create_post(
            text=post_text[:300],  # BlueSky has 300 char limit
            blob=blob,
            alt_text=f"WINDI Verified: {receipt_id}"
        )
        results.append(asdict(result))

    elif "bluesky" in platforms:
        results.append(asdict(FederationResult(
            platform="bluesky",
            success=False,
            error="Not configured (BLUESKY_APP_PASSWORD missing)"
        )))

    # Calculate stats
    success_count = sum(1 for r in results if r.get("success"))
    failure_count = len(results) - success_count

    # Estimated reach (very rough estimate)
    # Mastodon: ~1000 followers potential reach
    # BlueSky: ~500 followers potential reach
    estimated_reach = 0
    for r in results:
        if r.get("success"):
            if r.get("platform") == "mastodon":
                estimated_reach += 1000
            elif r.get("platform") == "bluesky":
                estimated_reach += 500

    return BroadcastResult(
        receipt_id=receipt_id,
        verify_url=verify_url,
        platforms=results,
        broadcast_at=start_time.isoformat(),
        total_reach=estimated_reach,
        success_count=success_count,
        failure_count=failure_count
    )


# ===== API Endpoints =====

@app.get("/")
async def root():
    return {
        "service": "W-FEDIVERSE-001",
        "version": "1.0.0",
        "description": "Glass Embassy — Multi-Protocol Truth Distribution",
        "status": "operational",
        "doctrine": "Se uma rede tentar silenciar, a outra mantém viva."
    }


@app.get("/fediverse/health")
async def health():
    """Health check with platform status."""
    return {
        "status": "healthy",
        "service": "W-FEDIVERSE-001",
        "version": "1.0.0",
        "platforms": {
            "mastodon": {
                "configured": bool(MASTODON_ACCESS_TOKEN),
                "instance": MASTODON_INSTANCE,
                "handle": MASTODON_HANDLE
            },
            "bluesky": {
                "configured": bool(BLUESKY_APP_PASSWORD),
                "service": BLUESKY_SERVICE,
                "handle": BLUESKY_HANDLE
            }
        },
        "capabilities": [
            "multi_platform_broadcast",
            "media_upload",
            "clarity_infinity_format",
            "parallel_distribution"
        ]
    }


@app.post("/fediverse/publish")
async def publish_to_fediverse(request: PublishRequest):
    """
    Publish verified content to Fediverse platforms.

    I9 Gate: This endpoint should only be called AFTER human approval.
    The receipt_id must exist in the Ledger.
    """
    log.info(f"Publishing to Fediverse: {request.receipt_id}")

    result = await broadcast_truth(
        receipt_id=request.receipt_id,
        verify_url=request.verify_url,
        title=request.title,
        description=request.description,
        media_path=request.media_path,
        platforms=request.platforms
    )

    # Build response
    response = {
        "success": result.success_count > 0,
        "receipt_id": result.receipt_id,
        "verify_url": result.verify_url,
        "broadcast_at": result.broadcast_at,
        "platforms": result.platforms,
        "summary": {
            "success_count": result.success_count,
            "failure_count": result.failure_count,
            "estimated_reach": result.total_reach
        }
    }

    # Build human-friendly message
    success_platforms = [p["platform"] for p in result.platforms if p.get("success")]
    failed_platforms = [p["platform"] for p in result.platforms if not p.get("success")]

    if success_platforms:
        response["message"] = f"🌐 Verdade federada em: {', '.join(success_platforms)}"
        response["links"] = {
            p["platform"]: p["post_url"]
            for p in result.platforms
            if p.get("success") and p.get("post_url")
        }

    if failed_platforms:
        response["warnings"] = [
            f"{p['platform']}: {p.get('error', 'Unknown error')}"
            for p in result.platforms
            if not p.get("success")
        ]

    return response


@app.get("/fediverse/platforms")
async def list_platforms():
    """List available and configured platforms."""
    return {
        "platforms": [
            {
                "id": "mastodon",
                "name": "Mastodon (ActivityPub)",
                "protocol": "ActivityPub",
                "configured": bool(MASTODON_ACCESS_TOKEN),
                "features": ["federation", "media_upload", "content_warning", "hashtags"]
            },
            {
                "id": "bluesky",
                "name": "BlueSky (AT Protocol)",
                "protocol": "AT Protocol",
                "configured": bool(BLUESKY_APP_PASSWORD),
                "features": ["decentralized", "media_upload", "link_facets", "future_labels"]
            }
        ],
        "future": [
            {
                "id": "ipfs",
                "name": "IPFS Pin",
                "protocol": "IPFS",
                "status": "planned",
                "description": "Permanent content-addressed storage"
            }
        ]
    }


# ===== Main =====

if __name__ == "__main__":
    import uvicorn
    log.info(f"Starting W-FEDIVERSE-001 on port {PORT}")
    log.info(f"Mastodon: {'CONFIGURED' if MASTODON_ACCESS_TOKEN else 'NOT CONFIGURED'}")
    log.info(f"BlueSky: {'CONFIGURED' if BLUESKY_APP_PASSWORD else 'NOT CONFIGURED'}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
