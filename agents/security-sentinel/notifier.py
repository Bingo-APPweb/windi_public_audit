"""
W-SEC-001 Security Sentinel — Notification Dispatcher
Sends alerts to Telegram (and Email in future).

Anti-noise features:
- Only high/critical severity
- Debounce: 60s for same incident
- Idempotency via notification key
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Set
from collections import deque

from webhooks import (
    WebhookEvent,
    WebhookConfig,
    get_telegram_config,
    is_telegram_configured,
    build_webhook_payload,
    build_notification_key,
    should_notify_severity,
)
from templates import get_formatted_message

logger = logging.getLogger("w-sec-001.notifier")

# Debounce cache: notif_key -> last_sent_at
SENT_NOTIFICATIONS: Dict[str, datetime] = {}
DEBOUNCE_SECONDS = 60  # Minimum time between same notifications

# Recent notification log (for debugging/display)
NOTIFICATION_LOG: deque = deque(maxlen=100)

# Lock for thread safety
_lock = asyncio.Lock()


async def should_send(notif_key: str, debounce_seconds: int = DEBOUNCE_SECONDS) -> bool:
    """
    Check if notification should be sent based on debounce rules.
    Returns True if notification should be sent.
    """
    async with _lock:
        now = datetime.now(timezone.utc)

        if notif_key in SENT_NOTIFICATIONS:
            last_sent = SENT_NOTIFICATIONS[notif_key]
            elapsed = (now - last_sent).total_seconds()

            if elapsed < debounce_seconds:
                logger.debug(f"Debounce: {notif_key} sent {elapsed:.0f}s ago, skipping")
                return False

        return True


async def mark_sent(notif_key: str):
    """Mark notification as sent for debounce tracking."""
    async with _lock:
        SENT_NOTIFICATIONS[notif_key] = datetime.now(timezone.utc)

        # Cleanup old entries (older than 1 hour)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        old_keys = [k for k, v in SENT_NOTIFICATIONS.items() if v < cutoff]
        for k in old_keys:
            del SENT_NOTIFICATIONS[k]


async def send_telegram(
    chat_id: str,
    bot_token: str,
    message: str,
    parse_mode: str = "Markdown",
) -> Dict[str, Any]:
    """
    Send message to Telegram chat.

    Returns:
        Response dict with ok, message_id, or error.
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                data = await resp.json()

                if data.get("ok"):
                    return {
                        "ok": True,
                        "message_id": data.get("result", {}).get("message_id"),
                    }
                else:
                    logger.error(f"Telegram API error: {data}")
                    return {
                        "ok": False,
                        "error": data.get("description", "Unknown error"),
                    }
    except asyncio.TimeoutError:
        logger.error("Telegram API timeout")
        return {"ok": False, "error": "Timeout"}
    except Exception as e:
        logger.error(f"Telegram send error: {e}")
        return {"ok": False, "error": str(e)}


async def notify_incident(
    event: WebhookEvent,
    incident: Any,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Send notification for an incident event.

    Applies anti-noise rules:
    - Only high/critical severity (unless SEALED event)
    - Debounce same incident/event combo

    Args:
        event: The webhook event type
        incident: SecIncident object
        extra: Optional extra payload data

    Returns:
        Dict with ok, channel, and details
    """
    results = {
        "ok": False,
        "event": event.value,
        "incident_id": incident.incident_id,
        "channels": [],
    }

    # Check Telegram configuration
    if not is_telegram_configured():
        logger.warning("Telegram not configured, skipping notification")
        results["skipped"] = "telegram_not_configured"
        return results

    config = get_telegram_config()

    # Check severity threshold (SEALED events always notify)
    if event != WebhookEvent.INCIDENT_SEALED:
        if not should_notify_severity(incident.severity, config.min_severity):
            logger.debug(f"Severity {incident.severity} below threshold {config.min_severity}")
            results["skipped"] = "below_severity_threshold"
            return results

    # Check event is enabled
    if event not in config.events:
        logger.debug(f"Event {event.value} not in enabled events")
        results["skipped"] = "event_not_enabled"
        return results

    # Build notification key for debounce
    notif_key = build_notification_key(event, incident.incident_id)

    # Check debounce (shorter for SEALED events - they're important)
    debounce = 30 if event == WebhookEvent.INCIDENT_SEALED else DEBOUNCE_SECONDS

    if not await should_send(notif_key, debounce):
        results["skipped"] = "debounced"
        return results

    # Build payload
    payload = build_webhook_payload(event, incident, extra)

    # Format message
    message = get_formatted_message(event, payload)

    # Send to Telegram
    tg_result = await send_telegram(
        chat_id=config.chat_id,
        bot_token=config.bot_token,
        message=message,
    )

    if tg_result.get("ok"):
        await mark_sent(notif_key)

        # Log successful notification
        log_entry = {
            "time": datetime.now(timezone.utc).isoformat(),
            "event": event.value,
            "incident_id": incident.incident_id,
            "severity": incident.severity,
            "channel": "telegram",
            "message_id": tg_result.get("message_id"),
        }
        NOTIFICATION_LOG.append(log_entry)

        results["ok"] = True
        results["channels"].append({
            "channel": "telegram",
            "ok": True,
            "message_id": tg_result.get("message_id"),
        })
    else:
        results["channels"].append({
            "channel": "telegram",
            "ok": False,
            "error": tg_result.get("error"),
        })

    return results


async def notify_incident_created(incident: Any) -> Dict[str, Any]:
    """Convenience: Notify on incident creation."""
    return await notify_incident(WebhookEvent.INCIDENT_CREATED, incident)


async def notify_incident_escalated(incident: Any) -> Dict[str, Any]:
    """Convenience: Notify when incident is escalated."""
    return await notify_incident(WebhookEvent.INCIDENT_ESCALATED, incident)


async def notify_distributed_detected(incident: Any) -> Dict[str, Any]:
    """Convenience: Notify when distributed attack is detected."""
    return await notify_incident(WebhookEvent.INCIDENT_DISTRIBUTED, incident)


async def notify_case_created(incident: Any) -> Dict[str, Any]:
    """Convenience: Notify when case is created."""
    return await notify_incident(WebhookEvent.CASE_CREATED, incident)


async def notify_case_approved(incident: Any) -> Dict[str, Any]:
    """Convenience: Notify when case is approved."""
    return await notify_incident(WebhookEvent.CASE_APPROVED, incident)


async def notify_incident_sealed(incident: Any) -> Dict[str, Any]:
    """Convenience: Notify when incident is sealed to Ledger."""
    return await notify_incident(WebhookEvent.INCIDENT_SEALED, incident)


def get_notification_log() -> list:
    """Get recent notification log entries."""
    return list(NOTIFICATION_LOG)


def get_notification_stats() -> Dict[str, Any]:
    """Get notification statistics."""
    return {
        "pending_debounce": len(SENT_NOTIFICATIONS),
        "log_entries": len(NOTIFICATION_LOG),
        "telegram_configured": is_telegram_configured(),
    }
