#!/usr/bin/env python3
"""
WINDI Maestro — Command Center Client
======================================

Interface to the WINDI Command Center for human operator notifications.
Notifications are ADVISORY ONLY — they inform, never block.

Notification Channels:
- urgent: Immediate attention required (R4-R5)
- standard: Normal priority queue
- batch: Aggregated digest (low priority)

Notification Types:
- case_assigned: New case routed to role
- ack_required: Awaiting human acknowledgment
- sla_warning: SLA threshold approaching
- sla_breach: SLA has been breached
- escalation_required: Case needs escalation

Principles:
- ADVISORY ONLY: Notifications inform, never block workflow
- ROLE-BASED: Notify role, not specific person
- IDEMPOTENT: Same notification can be sent multiple times safely
- ZERO-CONTENT: Only case metadata, never document content
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger("WINDI.Maestro.CommandCenter")


class NotificationChannel(Enum):
    URGENT = "urgent"
    STANDARD = "standard"
    BATCH = "batch"


class NotificationType(Enum):
    CASE_ASSIGNED = "case_assigned"
    ACK_REQUIRED = "ack_required"
    SLA_WARNING = "sla_warning"
    SLA_BREACH = "sla_breach"
    ESCALATION_REQUIRED = "escalation_required"
    DUAL_ACK_PENDING = "dual_ack_pending"


# Notification queue (in production, this would be a message queue)
DEFAULT_NOTIFICATION_PATH = Path("/opt/windi/data/notifications/maestro_queue.jsonl")


def notify_operator(
    notification_type: str,
    target_role: str,
    case_summary: Dict,
    channel: str = "standard",
    priority: int = 5,
    notification_path: Optional[Path] = None
) -> Dict:
    """
    Send notification to Command Center.

    Args:
        notification_type: Type of notification
        target_role: Role to notify (not specific person)
        case_summary: Case metadata for notification
        channel: Notification channel (urgent/standard/batch)
        priority: Priority level (1-10, 1 = highest)
        notification_path: Optional custom notification queue path

    Returns:
        Notification record with ID
    """
    path = notification_path or DEFAULT_NOTIFICATION_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).isoformat()

    notification = {
        "notification_id": f"NOTIF-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{hash(timestamp) % 10000:04d}",
        "type": notification_type,
        "target_role": target_role,
        "channel": channel,
        "priority": priority,
        "case_summary": {
            "case_id": case_summary.get("case_id"),
            "severity": case_summary.get("severity"),
            "invariants": case_summary.get("invariants", []),
            "status": case_summary.get("status"),
            "sla_status": case_summary.get("sla_status")
        },
        "created_at": timestamp,
        "delivered": False,
        "acknowledged": False
    }

    # Write to queue
    with open(path, 'a') as f:
        f.write(json.dumps(notification, default=str) + "\n")

    logger.info(
        f"Notification queued: type={notification_type} "
        f"role={target_role} case={case_summary.get('case_id')}"
    )

    return notification


def notify_case_assigned(
    case: Dict,
    route: Dict,
    notification_path: Optional[Path] = None
) -> Dict:
    """Notify role of new case assignment."""
    channel = route.get("channel", "standard")
    priority = _severity_to_priority(case.get("severity", "R3"))

    return notify_operator(
        NotificationType.CASE_ASSIGNED.value,
        route.get("role"),
        case,
        channel=channel,
        priority=priority,
        notification_path=notification_path
    )


def notify_ack_required(
    case: Dict,
    ack_type: str = "acknowledge",
    notification_path: Optional[Path] = None
) -> Dict:
    """Notify that human ACK is required."""
    return notify_operator(
        NotificationType.ACK_REQUIRED.value,
        case.get("assigned_to") or case.get("route", {}).get("role"),
        {**case, "ack_type": ack_type},
        channel="standard",
        priority=_severity_to_priority(case.get("severity", "R3")),
        notification_path=notification_path
    )


def notify_sla_warning(
    case: Dict,
    sla_component: str,
    remaining_minutes: int,
    threshold_percent: int,
    notification_path: Optional[Path] = None
) -> Dict:
    """Notify of approaching SLA deadline."""
    case_with_sla = {
        **case,
        "sla_status": {
            "component": sla_component,
            "remaining_minutes": remaining_minutes,
            "threshold_percent": threshold_percent
        }
    }

    # Urgent if very close to breach
    channel = "urgent" if threshold_percent >= 90 else "standard"

    return notify_operator(
        NotificationType.SLA_WARNING.value,
        case.get("assigned_to") or case.get("route", {}).get("role"),
        case_with_sla,
        channel=channel,
        priority=2 if threshold_percent >= 90 else 4,
        notification_path=notification_path
    )


def notify_sla_breach(
    case: Dict,
    breach_type: str,
    notification_path: Optional[Path] = None
) -> Dict:
    """Notify of SLA breach (urgent)."""
    case_with_breach = {
        **case,
        "sla_status": {
            "breached": True,
            "breach_type": breach_type
        }
    }

    return notify_operator(
        NotificationType.SLA_BREACH.value,
        case.get("assigned_to") or case.get("route", {}).get("role"),
        case_with_breach,
        channel="urgent",
        priority=1,
        notification_path=notification_path
    )


def notify_dual_ack_pending(
    case: Dict,
    first_acker: str,
    notification_path: Optional[Path] = None
) -> Dict:
    """Notify that second ACK is needed for dual-ACK requirement."""
    case_with_dual = {
        **case,
        "dual_ack": {
            "first_acker": first_acker,
            "awaiting_second": True
        }
    }

    return notify_operator(
        NotificationType.DUAL_ACK_PENDING.value,
        case.get("route", {}).get("role"),
        case_with_dual,
        channel="urgent",
        priority=2,
        notification_path=notification_path
    )


def notify_escalation_required(
    case: Dict,
    reason: str,
    target_role: str,
    notification_path: Optional[Path] = None
) -> Dict:
    """Notify of required escalation."""
    case_with_escalation = {
        **case,
        "escalation": {
            "reason": reason,
            "target_role": target_role
        }
    }

    return notify_operator(
        NotificationType.ESCALATION_REQUIRED.value,
        target_role,
        case_with_escalation,
        channel="urgent",
        priority=1,
        notification_path=notification_path
    )


def _severity_to_priority(severity: str) -> int:
    """Map severity to notification priority (1-10)."""
    mapping = {
        "R5": 1,
        "R4": 2,
        "R3": 5,
        "R2": 7,
        "R1": 9
    }
    return mapping.get(severity, 5)


def get_pending_notifications(
    role: Optional[str] = None,
    notification_path: Optional[Path] = None
) -> List[Dict]:
    """
    Get pending notifications, optionally filtered by role.

    Args:
        role: Filter by target role (None = all)
        notification_path: Optional custom path

    Returns:
        List of pending notifications
    """
    path = notification_path or DEFAULT_NOTIFICATION_PATH

    if not path.exists():
        return []

    pending = []

    try:
        with open(path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    notif = json.loads(line)

                    # Skip delivered/acknowledged
                    if notif.get("delivered") and notif.get("acknowledged"):
                        continue

                    # Filter by role if specified
                    if role and notif.get("target_role") != role:
                        continue

                    pending.append(notif)

                except json.JSONDecodeError:
                    continue

    except IOError:
        return []

    # Sort by priority then timestamp
    pending.sort(key=lambda n: (n.get("priority", 10), n.get("created_at", "")))

    return pending


def mark_notification_delivered(
    notification_id: str,
    notification_path: Optional[Path] = None
) -> bool:
    """Mark notification as delivered (for integration tracking)."""
    # In production, this would update the notification record
    # For now, just log
    logger.info(f"Notification delivered: {notification_id}")
    return True


def mark_notification_acknowledged(
    notification_id: str,
    acknowledged_by: str,
    notification_path: Optional[Path] = None
) -> bool:
    """Mark notification as acknowledged by operator."""
    logger.info(f"Notification acknowledged: {notification_id} by {acknowledged_by}")
    return True
