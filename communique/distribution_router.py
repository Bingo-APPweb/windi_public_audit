"""
W-DIST-001 — Distribution Router
==================================

Sovereign Distribution Layer for WINDI Communiqués.

Routes sealed communiqués to multiple channels:
- Telegram (via NOMAD-BOT token)
- Email (future)
- Signal (future)
- X/Twitter (future)

Principle: "A verdade já não fica no sistema. Agora ela circula."

Liga IA+H · Kempten, Bavaria · 2026
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

log = logging.getLogger("w-dist-001")

# Channel registry
CHANNELS: Dict[str, Any] = {}


def register_channel(name: str, handler) -> None:
    """
    Register a distribution channel.

    Args:
        name: Channel identifier (e.g., "telegram", "email")
        handler: Module with send() function
    """
    CHANNELS[name] = handler
    log.info(f"[W-DIST-001] Registered channel: {name}")


def unregister_channel(name: str) -> None:
    """Remove a channel from registry."""
    if name in CHANNELS:
        del CHANNELS[name]
        log.info(f"[W-DIST-001] Unregistered channel: {name}")


def list_channels() -> List[dict]:
    """List all registered channels with their info."""
    result = []
    for name, handler in CHANNELS.items():
        info = {"name": name, "available": True}
        if hasattr(handler, "get_info"):
            info.update(handler.get_info())
        result.append(info)
    return result


def distribute(
    communique: dict,
    channels: List[str],
    options: dict = None
) -> dict:
    """
    Distribute a sealed communiqué to multiple channels.

    Args:
        communique: Communiqué dict with evidence_* fields
        channels: List of channel names to distribute to
        options: Per-channel options (e.g., {"telegram": {"chat_id": "..."}})

    Returns:
        Distribution results for all channels
    """
    options = options or {}
    results = []
    success_count = 0
    error_count = 0

    com_id = communique.get("id", "UNKNOWN")
    log.info(f"[W-DIST-001] Distributing {com_id} to {len(channels)} channels: {channels}")

    for channel_name in channels:
        handler = CHANNELS.get(channel_name)

        if not handler:
            log.warning(f"[W-DIST-001] Channel not found: {channel_name}")
            results.append({
                "channel": channel_name,
                "success": False,
                "error": "channel_not_registered",
                "message": f"Channel '{channel_name}' is not registered"
            })
            error_count += 1
            continue

        try:
            # Get channel-specific options
            channel_opts = options.get(channel_name, {})

            # Call channel's send function
            if hasattr(handler, "send"):
                result = handler.send(communique, **channel_opts)
            else:
                raise AttributeError(f"Channel {channel_name} has no send() function")

            result["channel"] = channel_name
            results.append(result)

            if result.get("success"):
                success_count += 1
                log.info(f"[W-DIST-001] {channel_name}: sent successfully")
            else:
                error_count += 1
                log.warning(f"[W-DIST-001] {channel_name}: send failed - {result.get('error')}")

        except Exception as e:
            log.error(f"[W-DIST-001] {channel_name}: exception - {e}")
            results.append({
                "channel": channel_name,
                "success": False,
                "error": "exception",
                "message": str(e)
            })
            error_count += 1

    return {
        "communique_id": com_id,
        "channels_requested": len(channels),
        "success_count": success_count,
        "error_count": error_count,
        "results": results,
        "distributed_at": datetime.now(timezone.utc).isoformat()
    }


def distribute_single(
    communique: dict,
    channel: str,
    **kwargs
) -> dict:
    """
    Distribute to a single channel (convenience function).

    Args:
        communique: Communiqué dict
        channel: Channel name
        **kwargs: Channel-specific options

    Returns:
        Single channel result
    """
    result = distribute(communique, [channel], {channel: kwargs})
    if result["results"]:
        return result["results"][0]
    return {"success": False, "error": "no_result"}


# ══════════════════════════════════════════════════════════════
# AUTO-REGISTER CHANNELS
# ══════════════════════════════════════════════════════════════

def init_channels():
    """Initialize and register available channels."""
    # Telegram
    try:
        from channels import channel_telegram
        register_channel("telegram", channel_telegram)
    except ImportError as e:
        log.warning(f"[W-DIST-001] Could not load telegram channel: {e}")

    # Email
    try:
        from channels import channel_email
        register_channel("email", channel_email)
    except ImportError as e:
        log.warning(f"[W-DIST-001] Could not load email channel: {e}")

    # Signal (future)
    # try:
    #     from channels import channel_signal
    #     register_channel("signal", channel_signal)
    # except ImportError:
    #     pass


# Initialize on import
init_channels()


# ══════════════════════════════════════════════════════════════
# MODULE INFO
# ══════════════════════════════════════════════════════════════

__version__ = "1.0.0"
__agent_id__ = "W-DIST-001"
__agent_name__ = "Sovereign Distribution Layer"

def get_status() -> dict:
    """Get distribution router status."""
    return {
        "agent_id": __agent_id__,
        "agent_name": __agent_name__,
        "version": __version__,
        "channels": list_channels(),
        "principle": "A verdade já não fica no sistema. Agora ela circula."
    }
