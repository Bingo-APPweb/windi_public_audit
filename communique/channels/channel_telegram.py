"""
W-DIST-001 — Telegram Distribution Channel
============================================

Sends WINDI Communiqués to Telegram via Bot API.

Uses NOMAD-BOT token for authentication.
Supports sending .jmpg as document + caption with verify URL.

"A verdade já não fica no sistema. Agora ela circula."

Liga IA+H · Kempten, Bavaria · 2026
"""

import os
import logging
import requests
from datetime import datetime, timezone
from typing import Optional
from dotenv import load_dotenv

# Load NOMAD-BOT environment
load_dotenv("/opt/windi/nomad-bot/.env")

log = logging.getLogger("w-dist-telegram")

# Configuration
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Default broadcast channel (WINDI Official)
DEFAULT_CHAT_ID = os.environ.get("WINDI_BROADCAST_CHAT_ID")


def build_caption(communique: dict, lang: str = "en") -> str:
    """
    Build caption for Telegram message.

    §138 Architect Doctrine:
    - 30% less text, 2x clarity on Verify
    - One dominant language per post
    - "Verify" must feel inevitable
    - Breathing room = authority

    "confiança substitui curiosidade"
    """
    title = communique.get(f"title_{lang}") or communique.get("title_de") or communique.get("title_en") or "WINDI"
    receipt_id = communique.get("receipt_id") or communique.get("evidence_jmpg_id") or "PENDING"
    verify_url = communique.get("evidence_verify_url") or f"https://windi-domain.com/verify-public/?id={receipt_id}"

    # §138 Refined: Less text, Verify as magnetic destination
    caption = f"""*{title}*

`{receipt_id}`

👉 *[VERIFY]({verify_url})*
"""
    return caption


def build_caption_collage(collage_id: str, timestamp_a: str = "", timestamp_b: str = "") -> str:
    """
    §138 Sovereign Collage caption.

    Architect Doctrine: Image speaks, text whispers, Verify shouts.
    """
    verify_url = f"https://windi-domain.com/verify-public/?id={collage_id}"

    # Minimal: Let the video speak
    if timestamp_a and timestamp_b:
        caption = f"""*{timestamp_a}* ↔ *{timestamp_b}*

`{collage_id}`

👉 *[VERIFY]({verify_url})*
"""
    else:
        caption = f"""`{collage_id}`

👉 *[VERIFY]({verify_url})*
"""
    return caption


def build_caption_minimal(communique: dict) -> str:
    """Build minimal caption (for when full caption exceeds Telegram limits)."""
    receipt_id = communique.get("receipt_id") or communique.get("evidence_jmpg_id") or "PENDING"
    verify_url = communique.get("evidence_verify_url") or f"https://windi-domain.com/verify-public/?id={receipt_id}"

    return f"🔐 WINDI Communiqué | Receipt: {receipt_id}\n🔗 {verify_url}"


def send_document(
    chat_id: str,
    document_path: str,
    caption: str,
    filename: str = None
) -> dict:
    """
    Send a document (e.g., .jmpg file) to Telegram chat.

    Args:
        chat_id: Telegram chat/channel ID
        document_path: Path to file on disk
        caption: Message caption (Markdown supported)
        filename: Override filename in Telegram

    Returns:
        Telegram API response
    """
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not configured")

    if not os.path.exists(document_path):
        raise FileNotFoundError(f"Document not found: {document_path}")

    url = f"{TELEGRAM_API}/sendDocument"

    with open(document_path, "rb") as f:
        files = {"document": (filename or os.path.basename(document_path), f)}
        data = {
            "chat_id": chat_id,
            "caption": caption[:1024],  # Telegram limit
            "parse_mode": "Markdown"
        }

        response = requests.post(url, files=files, data=data, timeout=30)

    if response.status_code != 200:
        log.error(f"Telegram sendDocument failed: {response.text}")
        raise Exception(f"Telegram API error: {response.status_code}")

    return response.json()


def send_message(
    chat_id: str,
    text: str,
    parse_mode: str = "Markdown"
) -> dict:
    """
    Send a text message to Telegram chat.

    Args:
        chat_id: Telegram chat/channel ID
        text: Message text
        parse_mode: Markdown or HTML

    Returns:
        Telegram API response
    """
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not configured")

    url = f"{TELEGRAM_API}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": text[:4096],  # Telegram limit
        "parse_mode": parse_mode
    }

    response = requests.post(url, json=data, timeout=10)

    if response.status_code != 200:
        log.error(f"Telegram sendMessage failed: {response.text}")
        raise Exception(f"Telegram API error: {response.status_code}")

    return response.json()


def resolve_jmpg_path(communique: dict) -> Optional[str]:
    """
    Resolve the path to the .jmpg file for a communiqué.

    Checks multiple possible locations:
    1. /opt/windi/communique/jmpg/{communique_id}.jmpg
    2. /opt/windi/communique/jmpg/{jmpg_id}.jmpg
    """
    com_id = communique.get("id")
    jmpg_id = communique.get("evidence_jmpg_id")

    # Try communique ID first (our convention)
    if com_id:
        path = f"/opt/windi/communique/jmpg/{com_id}.jmpg"
        if os.path.exists(path):
            return path

    # Try JMPG ID
    if jmpg_id:
        path = f"/opt/windi/communique/jmpg/{jmpg_id}.jmpg"
        if os.path.exists(path):
            return path

    return None


def resolve_proof_card_path(communique: dict) -> Optional[str]:
    """
    Resolve the path to the visual proof card PNG.
    """
    com_id = communique.get("id")
    if com_id:
        path = f"/opt/windi/communique/jmpg/{com_id}.png"
        if os.path.exists(path):
            return path
    return None


def generate_proof_card(communique: dict) -> Optional[str]:
    """
    Generate visual proof card if it doesn't exist.
    Returns path to PNG or None on failure.
    """
    import subprocess

    com_id = communique.get("id")
    if not com_id:
        return None

    output_path = f"/opt/windi/communique/jmpg/{com_id}.png"

    # Check if already exists
    if os.path.exists(output_path):
        return output_path

    # Generate using proof_renderer
    try:
        import json
        import tempfile

        # Write communiqué to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(communique, f)
            temp_path = f.name

        # Run renderer
        result = subprocess.run(
            ["/opt/windi/venv/bin/python3", "/opt/windi/communique/proof_renderer.py", temp_path, output_path],
            capture_output=True,
            timeout=30
        )

        os.unlink(temp_path)  # Clean up

        if result.returncode == 0 and os.path.exists(output_path):
            log.info(f"Generated proof card: {output_path}")
            return output_path
        else:
            log.warning(f"Proof card generation failed: {result.stderr.decode()}")
            return None

    except Exception as e:
        log.warning(f"Proof card generation error: {e}")
        return None


def send_photo(
    chat_id: str,
    photo_path: str,
    caption: str
) -> dict:
    """
    Send a photo to Telegram chat.
    """
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not configured")

    if not os.path.exists(photo_path):
        raise FileNotFoundError(f"Photo not found: {photo_path}")

    url = f"{TELEGRAM_API}/sendPhoto"

    with open(photo_path, "rb") as f:
        files = {"photo": f}
        data = {
            "chat_id": chat_id,
            "caption": caption[:1024],
            "parse_mode": "Markdown"
        }

        response = requests.post(url, files=files, data=data, timeout=30)

    if response.status_code != 200:
        log.error(f"Telegram sendPhoto failed: {response.text}")
        raise Exception(f"Telegram API error: {response.status_code}")

    return response.json()


def send(communique: dict, chat_id: str = None, jmpg_path: str = None) -> dict:
    """
    Main distribution function for Telegram channel.

    Sends communiqué as document (.jmpg) with caption.
    If no .jmpg available, sends text-only message.

    Args:
        communique: Communiqué dict with evidence_* fields
        chat_id: Target chat/channel ID (uses default if not provided)
        jmpg_path: Path to .jmpg file (auto-resolved if not provided)

    Returns:
        Distribution result dict
    """
    target_chat = chat_id or DEFAULT_CHAT_ID

    if not target_chat:
        return {
            "success": False,
            "error": "no_chat_id",
            "message": "No chat_id provided and no default configured"
        }

    # Build caption
    caption = build_caption(communique)

    # Check if we have a JMPG to send
    jmpg_id = communique.get("evidence_jmpg_id")

    # PRIORITY 1: Try to send visual proof card (PNG) as photo
    proof_card_path = resolve_proof_card_path(communique)
    if not proof_card_path:
        # Generate on-demand
        proof_card_path = generate_proof_card(communique)

    if proof_card_path and os.path.exists(proof_card_path):
        try:
            result = send_photo(
                chat_id=target_chat,
                photo_path=proof_card_path,
                caption=caption
            )

            return {
                "success": True,
                "channel": "telegram",
                "type": "photo",
                "chat_id": target_chat,
                "message_id": result.get("result", {}).get("message_id"),
                "jmpg_id": jmpg_id,
                "proof_card": proof_card_path,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            log.warning(f"Telegram photo send failed, trying document: {e}")

    # PRIORITY 2: Try to send .jmpg as document
    if not jmpg_path:
        jmpg_path = resolve_jmpg_path(communique)

    if jmpg_path and os.path.exists(jmpg_path):
        try:
            result = send_document(
                chat_id=target_chat,
                document_path=jmpg_path,
                caption=caption,
                filename=f"{jmpg_id}.jmpg" if jmpg_id else None
            )

            return {
                "success": True,
                "channel": "telegram",
                "type": "document",
                "chat_id": target_chat,
                "message_id": result.get("result", {}).get("message_id"),
                "jmpg_id": jmpg_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            log.error(f"Telegram document send failed: {e}")

    # PRIORITY 3: Send text-only message
    try:
        result = send_message(
            chat_id=target_chat,
            text=caption
        )

        return {
            "success": True,
            "channel": "telegram",
            "type": "text",
            "chat_id": target_chat,
            "message_id": result.get("result", {}).get("message_id"),
            "jmpg_id": jmpg_id,
            "note": "text_only_no_visual",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        log.error(f"Telegram send failed: {e}")
        return {
            "success": False,
            "channel": "telegram",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Channel registration interface
CHANNEL_NAME = "telegram"
CHANNEL_VERSION = "1.0.0"

def get_info() -> dict:
    """Return channel information for router."""
    return {
        "name": CHANNEL_NAME,
        "version": CHANNEL_VERSION,
        "configured": TELEGRAM_TOKEN is not None,
        "default_chat": DEFAULT_CHAT_ID,
        "capabilities": ["document", "text", "markdown"]
    }
