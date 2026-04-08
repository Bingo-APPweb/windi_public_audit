"""
W-SEC-001 Security Sentinel — Webhook Configuration
Manages webhook registrations and event definitions.
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel


class WebhookEvent(str, Enum):
    """Events that trigger webhook notifications."""
    INCIDENT_CREATED = "incident_created"
    INCIDENT_ESCALATED = "incident_escalated"
    INCIDENT_DISTRIBUTED = "incident_distributed_detected"
    CASE_CREATED = "case_created"
    CASE_APPROVED = "case_approved"
    INCIDENT_SEALED = "incident_sealed"


class WebhookChannel(str, Enum):
    """Supported notification channels."""
    TELEGRAM = "telegram"
    EMAIL = "email"  # Future


class WebhookConfig(BaseModel):
    """Webhook configuration for a channel."""
    channel: WebhookChannel
    enabled: bool = True
    chat_id: Optional[str] = None  # For Telegram
    bot_token: Optional[str] = None  # For Telegram
    email_to: Optional[List[str]] = None  # For Email (future)
    events: List[WebhookEvent] = []
    min_severity: str = "high"  # Only notify for high/critical


# Default configuration from environment
DEFAULT_TELEGRAM_CONFIG = WebhookConfig(
    channel=WebhookChannel.TELEGRAM,
    enabled=os.getenv("SEC_TELEGRAM_ENABLED", "true").lower() == "true",
    chat_id=os.getenv("SEC_TELEGRAM_CHAT_ID"),
    bot_token=os.getenv("SEC_TELEGRAM_BOT_TOKEN"),
    events=[
        WebhookEvent.INCIDENT_CREATED,
        WebhookEvent.INCIDENT_ESCALATED,
        WebhookEvent.INCIDENT_DISTRIBUTED,
        WebhookEvent.CASE_CREATED,
        WebhookEvent.CASE_APPROVED,
        WebhookEvent.INCIDENT_SEALED,
    ],
    min_severity="high",
)


def get_telegram_config() -> WebhookConfig:
    """Get Telegram webhook configuration."""
    return DEFAULT_TELEGRAM_CONFIG


def is_telegram_configured() -> bool:
    """Check if Telegram is properly configured."""
    cfg = get_telegram_config()
    return bool(cfg.enabled and cfg.chat_id and cfg.bot_token)


def build_webhook_payload(
    event: WebhookEvent,
    incident: Any,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build canonical webhook payload.

    Schema:
    {
        "event": "incident_created",
        "version": "1.0.0",
        "sent_at": "2026-04-08T...",
        "incident": { ... },
        "links": { ... },
        "seal": { ... } (if sealed)
    }
    """
    now = datetime.now(timezone.utc)

    payload = {
        "event": event.value,
        "version": "1.0.0",
        "sent_at": now.isoformat(),
        "incident": {
            "id": incident.incident_id,
            "title": incident.title,
            "summary": incident.summary,
            "severity": incident.severity,
            "confidence": incident.confidence,
            "status": incident.status,
            "event_count": incident.event_count,
            "primary_vector": incident.primary_vector,
            "affected_assets": incident.affected_assets,
            "actor_count": len(incident.actors),
            "opened_at": incident.opened_at.isoformat() if incident.opened_at else None,
            "updated_at": incident.updated_at.isoformat() if incident.updated_at else None,
        },
        "links": {
            "dashboard": f"https://windi-domain.com/sec/dashboard/index.html#inc_{incident.incident_id}",
            "api": f"https://windi-domain.com/sec/incidents/{incident.incident_id}",
        },
    }

    # Add seal info if present
    if incident.ledger_receipt_id:
        payload["seal"] = {
            "receipt_id": incident.ledger_receipt_id,
            "verify_url": f"https://windi-domain.com/verify-public/?id={incident.ledger_receipt_id}",
        }

    # Add case info if present
    if incident.maestro_case_id:
        payload["case"] = {
            "case_id": incident.maestro_case_id,
        }

    # Merge extra data
    if extra:
        payload.update(extra)

    return payload


def build_notification_key(event: WebhookEvent, incident_id: str) -> str:
    """
    Build idempotency key for deduplication.
    Format: {event}:{incident_id}:{hour_bucket}
    """
    now = datetime.now(timezone.utc)
    hour_bucket = now.strftime("%Y%m%d%H")
    return f"{event.value}:{incident_id}:{hour_bucket}"


def should_notify_severity(incident_severity: str, min_severity: str) -> bool:
    """Check if incident severity meets minimum threshold."""
    severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    return severity_order.get(incident_severity, 0) >= severity_order.get(min_severity, 0)
