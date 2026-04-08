"""
W-SEC-001 Security Sentinel — Notification Templates
Telegram and Email message formatting.
"""

from typing import Dict, Any
from webhooks import WebhookEvent


# Severity to emoji mapping
SEVERITY_EMOJI = {
    "low": "🟢",
    "medium": "🟡",
    "high": "🟠",
    "critical": "🔴",
}

# Status to emoji mapping
STATUS_EMOJI = {
    "open": "🔓",
    "investigating": "🔍",
    "approved": "✅",
    "sealed": "🔏",
    "closed": "📁",
}

# Event to header mapping
EVENT_HEADERS = {
    WebhookEvent.INCIDENT_CREATED: "🚨 NEW SECURITY INCIDENT",
    WebhookEvent.INCIDENT_ESCALATED: "⚠️ INCIDENT ESCALATED",
    WebhookEvent.INCIDENT_DISTRIBUTED: "🌐 DISTRIBUTED ATTACK DETECTED",
    WebhookEvent.CASE_CREATED: "📋 CASE CREATED",
    WebhookEvent.CASE_APPROVED: "✅ CASE APPROVED",
    WebhookEvent.INCIDENT_SEALED: "🔏 INCIDENT SEALED",
}


def format_telegram_message(event: WebhookEvent, payload: Dict[str, Any]) -> str:
    """
    Format webhook payload as Telegram message.

    Uses Markdown formatting supported by Telegram.
    """
    inc = payload.get("incident", {})
    links = payload.get("links", {})
    seal = payload.get("seal", {})
    case = payload.get("case", {})

    severity = inc.get("severity", "unknown")
    severity_emoji = SEVERITY_EMOJI.get(severity, "⚪")
    status = inc.get("status", "unknown")
    status_emoji = STATUS_EMOJI.get(status, "❓")
    header = EVENT_HEADERS.get(event, "🔔 SECURITY ALERT")

    # Build message parts
    lines = []

    # Header with severity indicator
    if severity == "critical":
        lines.append(f"*{header}* 🔴🔴🔴")
    elif severity == "high":
        lines.append(f"*{header}* 🟠🟠")
    else:
        lines.append(f"*{header}*")

    lines.append("")

    # Incident info
    lines.append(f"📌 *{inc.get('title', 'Unknown')}*")
    lines.append("")
    lines.append(f"🔸 Severity: {severity_emoji} `{severity.upper()}`")
    lines.append(f"🔸 Status: {status_emoji} {status}")
    lines.append(f"🔸 Events: `{inc.get('event_count', 0)}`")
    lines.append(f"🔸 Sources: `{inc.get('actor_count', 0)}`")
    lines.append(f"🔸 Confidence: `{inc.get('confidence', 0):.0%}`")
    lines.append(f"🔸 Vector: `{inc.get('primary_vector', 'unknown')}`")

    # Affected assets
    assets = inc.get("affected_assets", [])
    if assets:
        lines.append(f"🔸 Assets: `{', '.join(assets[:3])}`")

    lines.append("")

    # Summary (truncate if too long)
    summary = inc.get("summary", "")
    if summary:
        if len(summary) > 200:
            summary = summary[:197] + "..."
        lines.append(f"_{summary}_")
        lines.append("")

    # Case info if present
    if case.get("case_id"):
        lines.append(f"📋 Case: `{case['case_id']}`")

    # Seal info if present
    if seal.get("receipt_id"):
        lines.append(f"🔏 Receipt: `{seal['receipt_id']}`")
        if seal.get("verify_url"):
            lines.append(f"🔗 [Verify Seal]({seal['verify_url']})")

    # Links
    lines.append("")
    if links.get("dashboard"):
        lines.append(f"📊 [View Dashboard]({links['dashboard']})")

    # Footer with timestamp
    lines.append("")
    lines.append(f"⏰ {payload.get('sent_at', 'unknown')[:19]}")
    lines.append("—")
    lines.append("_W-SEC-001 Security Sentinel_")

    return "\n".join(lines)


def format_critical_alert(payload: Dict[str, Any]) -> str:
    """
    Special format for CRITICAL severity alerts.
    More prominent, urgent styling.
    """
    inc = payload.get("incident", {})
    links = payload.get("links", {})

    lines = [
        "🚨🚨🚨 *CRITICAL SECURITY ALERT* 🚨🚨🚨",
        "",
        f"🔴 *{inc.get('title', 'Unknown Threat')}*",
        "",
        "━━━━━━━━━━━━━━━━━━━━━",
        f"⚡ Events: `{inc.get('event_count', 0)}`",
        f"👥 Sources: `{inc.get('actor_count', 0)}`",
        f"🎯 Vector: `{inc.get('primary_vector', 'unknown')}`",
        f"📍 Assets: `{', '.join(inc.get('affected_assets', [])[:3])}`",
        "━━━━━━━━━━━━━━━━━━━━━",
        "",
    ]

    # Summary
    summary = inc.get("summary", "")
    if summary:
        if len(summary) > 150:
            summary = summary[:147] + "..."
        lines.append(f"_{summary}_")
        lines.append("")

    # Action required
    lines.extend([
        "⚠️ *IMMEDIATE ACTION REQUIRED*",
        "",
        f"📊 [Open Dashboard]({links.get('dashboard', '#')})",
        "",
        "—",
        "_W-SEC-001 · WINDI Security_",
    ])

    return "\n".join(lines)


def format_sealed_notification(payload: Dict[str, Any]) -> str:
    """
    Special format for SEALED incidents.
    Emphasizes the cryptographic proof.
    """
    inc = payload.get("incident", {})
    seal = payload.get("seal", {})

    severity_emoji = SEVERITY_EMOJI.get(inc.get("severity", "medium"), "⚪")

    lines = [
        "🔏 *INCIDENT SEALED TO LEDGER*",
        "",
        f"📌 {inc.get('title', 'Unknown')}",
        f"🔸 Severity: {severity_emoji} `{inc.get('severity', 'unknown').upper()}`",
        f"🔸 Events: `{inc.get('event_count', 0)}`",
        "",
        "━━━━━━━━━━━━━━━━━━━━━",
        f"📜 Receipt: `{seal.get('receipt_id', 'N/A')}`",
        "━━━━━━━━━━━━━━━━━━━━━",
        "",
    ]

    if seal.get("verify_url"):
        lines.append(f"✅ [Verify on Ledger]({seal['verify_url']})")
        lines.append("")

    lines.extend([
        "—",
        "_Cryptographic proof anchored._",
        "_W-SEC-001 · I11 Forensic Integrity_",
    ])

    return "\n".join(lines)


def format_distributed_alert(payload: Dict[str, Any]) -> str:
    """
    Special format for distributed attack detection.
    """
    inc = payload.get("incident", {})
    links = payload.get("links", {})

    severity_emoji = SEVERITY_EMOJI.get(inc.get("severity", "high"), "🟠")

    lines = [
        "🌐 *DISTRIBUTED ATTACK DETECTED*",
        "",
        f"{severity_emoji} *{inc.get('title', 'Multi-Source Attack')}*",
        "",
        f"👥 *{inc.get('actor_count', 0)} unique sources*",
        f"⚡ {inc.get('event_count', 0)} total events",
        f"🎯 Vector: `{inc.get('primary_vector', 'unknown')}`",
        "",
    ]

    # Summary
    summary = inc.get("summary", "")
    if summary:
        if len(summary) > 180:
            summary = summary[:177] + "..."
        lines.append(f"_{summary}_")
        lines.append("")

    lines.extend([
        f"📊 [View Attack Map]({links.get('dashboard', '#')})",
        "",
        "—",
        "_W-SEC-001 · Behavioral Correlation_",
    ])

    return "\n".join(lines)


def get_formatted_message(event: WebhookEvent, payload: Dict[str, Any]) -> str:
    """
    Get the appropriate formatted message for an event.
    Chooses special formats for critical/sealed/distributed events.
    """
    inc = payload.get("incident", {})
    severity = inc.get("severity", "medium")

    # Use special formats for specific scenarios
    if event == WebhookEvent.INCIDENT_SEALED:
        return format_sealed_notification(payload)

    if event == WebhookEvent.INCIDENT_DISTRIBUTED:
        return format_distributed_alert(payload)

    if severity == "critical":
        return format_critical_alert(payload)

    # Default format for other events
    return format_telegram_message(event, payload)
