"""
W-COMM-001 — Canonical Publishing Engine
WINDI Publishing House | Kempten, Bavaria

Transforms communications into structured, sealed, verifiable artifacts.

Invariants:
C1 — Every communication has unique ID
C2 — Every communication has deterministic hash
C3 — Seal is optional but natively supported
C4 — Channel renders derive from same payload
C5 — Verify is public and channel-independent
C6 — API does not do cold outreach automation

Version: 1.0.0
Date: 21-03-2026
"""

import os
import json
import hashlib
import logging
from datetime import datetime, timezone
from typing import Literal, Optional
from pathlib import Path
import httpx
from flask import Blueprint, request, jsonify
from pydantic import BaseModel, Field

logger = logging.getLogger("W-COMM-001")

comm_bp = Blueprint("comm", __name__, url_prefix="/comm")

# ── Config ──────────────────────────────────────────────────────
COMM_STORAGE_PATH = Path("/opt/windi/comm")
LEDGER_BASE = os.getenv("LEDGER_URL", "http://127.0.0.1:8101")

# ── Trilingual Templates ────────────────────────────────────────
# Semantic translations (not literal) preserving force and native tone

I18N_TEMPLATES = {
    "origin_built_in": {
        "EN": "Built in",
        "DE": "Entwickelt in",
        "PT": "Construído em"
    },
    "cta_see_live": {
        "EN": "See it live:",
        "DE": "Live ansehen:",
        "PT": "Veja ao vivo:"
    },
    "location": {
        "EN": "Kempten, Bavaria",
        "DE": "Kempten, Bayern",
        "PT": "Kempten, Baviera"
    }
}

# ── Pydantic Models ─────────────────────────────────────────────

class IntegrityBlock(BaseModel):
    hash: str = ""
    signature: Optional[str] = None
    sealed: bool = False
    ledger_receipt_id: Optional[str] = None


class CommOrigin(BaseModel):
    publisher: str = "WINDI Publishing House"
    location: str = "Kempten, Bavaria"
    system: str = "WINDI GEN7"


class CommMetadata(BaseModel):
    created_at: str
    created_by: str = "system"
    locale: str = "en"
    tags: list[str] = []


class CommPayload(BaseModel):
    id: str
    version: str = "1.0"
    type: Literal["announcement", "update", "release", "statement"]
    status: Literal["draft", "sealed", "published"] = "draft"
    language: Literal["EN", "DE", "PT"]
    title: str
    summary: str
    body: str
    audience: list[str] = []
    channels: list[str] = []
    links: dict[str, str] = {}
    origin: CommOrigin = Field(default_factory=CommOrigin)
    metadata: CommMetadata
    integrity: IntegrityBlock = Field(default_factory=IntegrityBlock)


class CommGenerateRequest(BaseModel):
    type: Literal["announcement", "update", "release", "statement"] = "announcement"
    language: Literal["EN", "DE", "PT"] = "EN"
    title: str
    summary: str
    body: str
    audience: list[str] = []
    channels: list[str] = Field(default=["linkedin", "x", "web"])
    links: dict[str, str] = {}
    tags: list[str] = []
    seal: bool = False
    created_by: str = "system"


# ── Core Functions ──────────────────────────────────────────────

def generate_comm_id() -> str:
    """Generate unique COMM ID: COMM-YYYYMMDD-XXXX"""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")

    # Find next sequence number for today
    existing = list(COMM_STORAGE_PATH.glob(f"COMM-{date_str}-*.json"))
    seq = len(existing) + 1

    return f"COMM-{date_str}-{seq:04d}"


def canonicalize_payload(payload: dict) -> str:
    """Create canonical JSON representation for hashing."""
    # Remove integrity block for hashing (it contains the hash itself)
    payload_copy = payload.copy()
    if "integrity" in payload_copy:
        payload_copy["integrity"] = {
            "hash": "",
            "signature": None,
            "sealed": False,
            "ledger_receipt_id": None
        }

    # Sort keys and serialize with consistent formatting
    return json.dumps(payload_copy, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def compute_payload_hash(payload: dict) -> str:
    """Compute SHA-256 hash of canonical payload."""
    canonical = canonicalize_payload(payload)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def save_payload(payload: CommPayload) -> Path:
    """Save payload to local storage."""
    filepath = COMM_STORAGE_PATH / f"{payload.id}.json"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(payload.model_dump(), f, indent=2, ensure_ascii=False)
    return filepath


def load_payload(comm_id: str) -> Optional[CommPayload]:
    """Load payload from local storage."""
    filepath = COMM_STORAGE_PATH / f"{comm_id}.json"
    if not filepath.exists():
        return None

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return CommPayload(**data)


# ── Renderers ───────────────────────────────────────────────────

def render_for_linkedin(payload: CommPayload) -> str:
    """Render payload for LinkedIn (long form with CTA)."""
    lines = []

    # Body (already formatted)
    lines.append(payload.body)

    # Links
    if payload.links.get("primary"):
        lines.append("")
        cta = {
            "EN": "See it live:",
            "DE": "Live ansehen:",
            "PT": "Veja ao vivo:"
        }.get(payload.language, "See it live:")
        lines.append(f"{cta} {payload.links['primary']}")

    # Origin (localized)
    lines.append("")
    built_in = I18N_TEMPLATES["origin_built_in"].get(payload.language, "Built in")
    lines.append(f"{built_in} {payload.origin.location}")
    lines.append(payload.origin.system)

    # Tags as hashtags
    if payload.metadata.tags:
        lines.append("")
        hashtags = " ".join([f"#{tag.replace(' ', '')}" for tag in payload.metadata.tags])
        lines.append(hashtags)

    return "\n".join(lines)


def render_for_x(payload: CommPayload) -> str:
    """Render payload for X/Twitter (280 char limit)."""
    # Use summary + primary link
    text = payload.summary

    if payload.links.get("primary"):
        text += f" {payload.links['primary']}"

    # Truncate if needed (leave room for link)
    if len(text) > 280:
        text = text[:277] + "..."

    return text


def render_for_web(payload: CommPayload) -> dict:
    """Render payload for web (structured)."""
    return {
        "title": payload.title,
        "summary": payload.summary,
        "body": payload.body,
        "links": payload.links,
        "published_at": payload.metadata.created_at,
        "publisher": payload.origin.publisher,
        "location": payload.origin.location,
        "verify_url": f"https://windi-domain.com/comm/{payload.id}/verify"
    }


def render_payload(payload: CommPayload) -> dict:
    """Render payload for all channels."""
    return {
        "linkedin": render_for_linkedin(payload),
        "x": render_for_x(payload),
        "web": render_for_web(payload)
    }


# ── Ledger Integration ──────────────────────────────────────────

def seal_to_ledger(payload: CommPayload) -> dict:
    """Seal payload to Forensic Ledger."""
    try:
        ledger_payload = {
            "receipt_id": f"WINDI-{payload.id}",
            "actor": payload.metadata.created_by,
            "app": "comm-engine",
            "doc_name": payload.title,
            "doc_type": f"comm_{payload.type}",
            "content_hash": payload.integrity.hash,
            "invariants": ["C1", "C2", "C3"],
            "stage": "C6",
            "metadata": {
                "comm_id": payload.id,
                "language": payload.language,
                "channels": payload.channels,
                "summary": payload.summary[:100]
            }
        }

        resp = httpx.post(
            f"{LEDGER_BASE}/api/receipts",
            json=ledger_payload,
            timeout=5.0
        )

        if resp.status_code in (200, 201):
            ledger_data = resp.json()
            return {
                "success": True,
                "receipt_id": ledger_data.get("receipt_id", f"WINDI-{payload.id}"),
                "sealed_at": datetime.now(timezone.utc).isoformat()
            }
        else:
            return {
                "success": False,
                "error": f"Ledger returned {resp.status_code}"
            }

    except Exception as e:
        logger.exception("Failed to seal to Ledger")
        return {
            "success": False,
            "error": str(e)
        }


# ═══════════════════════════════════════════════════════════════
# API Endpoints
# ═══════════════════════════════════════════════════════════════

@comm_bp.route("/health", methods=["GET"])
def health():
    """COMM API health check."""
    return jsonify({
        "agent": "W-COMM-001",
        "status": "healthy",
        "version": "1.0.0",
        "storage": str(COMM_STORAGE_PATH)
    })


@comm_bp.route("/generate", methods=["POST"])
def generate():
    """Generate canonical COMM payload from input."""
    try:
        data = request.json
        req = CommGenerateRequest(**data)

        # Generate ID
        comm_id = generate_comm_id()

        # Build payload
        payload = CommPayload(
            id=comm_id,
            type=req.type,
            language=req.language,
            title=req.title,
            summary=req.summary,
            body=req.body,
            audience=req.audience,
            channels=req.channels,
            links=req.links,
            metadata=CommMetadata(
                created_at=datetime.now(timezone.utc).isoformat(),
                created_by=req.created_by,
                locale=req.language.lower(),
                tags=req.tags
            )
        )

        # Compute hash
        payload_dict = payload.model_dump()
        content_hash = compute_payload_hash(payload_dict)
        payload.integrity.hash = content_hash

        # Seal if requested
        if req.seal:
            seal_result = seal_to_ledger(payload)
            if seal_result["success"]:
                payload.integrity.sealed = True
                payload.integrity.ledger_receipt_id = seal_result["receipt_id"]
                payload.status = "sealed"

        # Save payload
        save_payload(payload)

        # Render for channels
        rendered = render_payload(payload)

        return jsonify({
            "success": True,
            "payload": payload.model_dump(),
            "rendered": rendered
        })

    except Exception as e:
        logger.exception("Failed to generate COMM")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


@comm_bp.route("/generate-multilang", methods=["POST"])
def generate_multilang():
    """Generate trilingual COMM payloads (EN + DE + PT) from single input.

    Each language version gets its own ID and hash while sharing
    the same base content structure.
    """
    try:
        data = request.json

        # Validate required fields
        required = ["title", "summary", "body"]
        for field in required:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400

        # Content must be provided per language
        content = data.get("content", {})
        if not content:
            # If no per-language content, use default (assumes EN input)
            content = {
                "EN": {
                    "title": data["title"],
                    "summary": data["summary"],
                    "body": data["body"]
                }
            }

        # Generate base ID
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        existing = list(COMM_STORAGE_PATH.glob(f"COMM-{date_str}-*.json"))
        base_seq = len(existing) + 1
        base_id = f"COMM-{date_str}-{base_seq:04d}"

        results = {}
        payloads = {}

        for lang in ["EN", "DE", "PT"]:
            lang_content = content.get(lang, content.get("EN", {}))

            if not lang_content:
                continue

            comm_id = f"{base_id}-{lang}"

            # Build payload for this language
            payload = CommPayload(
                id=comm_id,
                type=data.get("type", "announcement"),
                language=lang,
                title=lang_content.get("title", data.get("title", "")),
                summary=lang_content.get("summary", data.get("summary", "")),
                body=lang_content.get("body", data.get("body", "")),
                audience=data.get("audience", []),
                channels=data.get("channels", ["linkedin", "x", "web"]),
                links=data.get("links", {}),
                origin=CommOrigin(
                    location=I18N_TEMPLATES["location"].get(lang, "Kempten, Bavaria")
                ),
                metadata=CommMetadata(
                    created_at=datetime.now(timezone.utc).isoformat(),
                    created_by=data.get("created_by", "system"),
                    locale=lang.lower(),
                    tags=data.get("tags", [])
                )
            )

            # Compute hash
            payload_dict = payload.model_dump()
            content_hash = compute_payload_hash(payload_dict)
            payload.integrity.hash = content_hash

            # Save payload
            save_payload(payload)

            # Render for channels
            rendered = render_payload(payload)

            payloads[lang] = payload.model_dump()
            results[lang] = {
                "id": comm_id,
                "hash": content_hash,
                "rendered": rendered
            }

        return jsonify({
            "success": True,
            "base_id": base_id,
            "languages": list(results.keys()),
            "payloads": payloads,
            "results": results
        })

    except Exception as e:
        logger.exception("Failed to generate multilang COMM")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


@comm_bp.route("/<comm_id>", methods=["GET"])
def get_comm(comm_id: str):
    """Get COMM payload by ID."""
    payload = load_payload(comm_id)

    if not payload:
        return jsonify({
            "success": False,
            "error": "COMM not found"
        }), 404

    return jsonify({
        "success": True,
        "payload": payload.model_dump()
    })


@comm_bp.route("/<comm_id>/seal", methods=["POST"])
def seal_comm(comm_id: str):
    """Seal existing COMM to Ledger."""
    payload = load_payload(comm_id)

    if not payload:
        return jsonify({
            "success": False,
            "error": "COMM not found"
        }), 404

    if payload.integrity.sealed:
        return jsonify({
            "success": False,
            "error": "COMM already sealed",
            "ledger_receipt_id": payload.integrity.ledger_receipt_id
        }), 400

    # Seal to Ledger
    seal_result = seal_to_ledger(payload)

    if seal_result["success"]:
        payload.integrity.sealed = True
        payload.integrity.ledger_receipt_id = seal_result["receipt_id"]
        payload.status = "sealed"
        save_payload(payload)

        return jsonify({
            "success": True,
            "id": comm_id,
            "sealed": True,
            "hash": payload.integrity.hash,
            "ledger_receipt_id": seal_result["receipt_id"],
            "verify_url": f"https://windi-domain.com/comm/{comm_id}/verify"
        })
    else:
        return jsonify({
            "success": False,
            "error": seal_result.get("error", "Seal failed")
        }), 500


@comm_bp.route("/<comm_id>/verify", methods=["GET"])
def verify_comm(comm_id: str):
    """Public verification endpoint for COMM."""
    payload = load_payload(comm_id)

    if not payload:
        return jsonify({
            "success": False,
            "error": "COMM not found"
        }), 404

    # Recompute hash to verify integrity
    payload_dict = payload.model_dump()
    current_hash = compute_payload_hash(payload_dict)
    hash_valid = current_hash == payload.integrity.hash

    return jsonify({
        "id": payload.id,
        "title": payload.title,
        "type": payload.type,
        "language": payload.language,
        "publisher": payload.origin.publisher,
        "location": payload.origin.location,
        "created_at": payload.metadata.created_at,
        "hash": payload.integrity.hash,
        "hash_valid": hash_valid,
        "sealed": payload.integrity.sealed,
        "ledger_receipt_id": payload.integrity.ledger_receipt_id,
        "status": "verified" if hash_valid else "tampered"
    })


@comm_bp.route("/<comm_id>/render", methods=["GET"])
def render_comm(comm_id: str):
    """Get rendered version for specific channel."""
    channel = request.args.get("channel", "linkedin")

    payload = load_payload(comm_id)

    if not payload:
        return jsonify({
            "success": False,
            "error": "COMM not found"
        }), 404

    rendered = render_payload(payload)

    if channel not in rendered:
        return jsonify({
            "success": False,
            "error": f"Unknown channel: {channel}"
        }), 400

    return jsonify({
        "success": True,
        "channel": channel,
        "content": rendered[channel]
    })


@comm_bp.route("/list", methods=["GET"])
def list_comms():
    """List all COMM payloads."""
    comms = []

    for filepath in COMM_STORAGE_PATH.glob("COMM-*.json"):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            comms.append({
                "id": data["id"],
                "title": data["title"],
                "type": data["type"],
                "language": data["language"],
                "status": data["status"],
                "created_at": data["metadata"]["created_at"],
                "sealed": data["integrity"]["sealed"]
            })
        except Exception:
            continue

    # Sort by created_at descending
    comms.sort(key=lambda x: x["created_at"], reverse=True)

    return jsonify({
        "success": True,
        "count": len(comms),
        "comms": comms
    })
