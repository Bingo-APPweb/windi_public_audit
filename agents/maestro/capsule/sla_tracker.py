#!/usr/bin/env python3
"""
WINDI Maestro — SLA Tracker
===========================

Tracks SLA compliance for governance resolution cases.
Computes deadlines based on severity and ISP tier.
Detects breaches and triggers escalation.

SLA Components:
- first_response: Time until case is acknowledged
- decision: Time until case is decided/resolved

Breach Detection:
- Continuous monitoring of active cases
- Automatic escalation on breach
- Notification at configurable thresholds

Principles:
- SLA is computed at case creation and immutable
- Breach detection is deterministic
- All SLA events are recorded in case timeline
"""

import yaml
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger("WINDI.Maestro.SLA")


def load_sla(path: str) -> Dict:
    """
    Load SLA policies from YAML file.

    Returns the 'sla' section of the configuration.
    """
    with open(path, "r") as f:
        config = yaml.safe_load(f)
    logger.info(f"Loaded SLA policies from {path}")
    return config.get("sla", {})


def load_sla_config(path: str) -> Dict:
    """Load full SLA configuration including tier multipliers."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


def compute_deadlines(
    severity: str,
    sla_cfg: Dict,
    created_iso: str,
    isp_tier: Optional[str] = None,
    tier_multipliers: Optional[Dict] = None
) -> Dict:
    """
    Compute SLA deadlines for a case.

    Args:
        severity: Case severity (R1-R5)
        sla_cfg: SLA configuration (severity → minutes)
        created_iso: Case creation timestamp (ISO 8601)
        isp_tier: Optional ISP tier for multiplier
        tier_multipliers: Optional tier multiplier configuration

    Returns:
        Dict with:
        - created: Creation timestamp
        - first_response_due: Deadline for first response
        - decision_due: Deadline for decision
        - severity: Applied severity level
        - tier: Applied tier (if any)
    """
    # Parse creation timestamp
    created = datetime.fromisoformat(created_iso.replace("Z", "+00:00"))
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)

    # Get SLA rule for severity (fallback to R3)
    rule = sla_cfg.get(severity, sla_cfg.get("R3", {
        "first_response_minutes": 240,
        "decision_minutes": 1440
    }))

    fr_minutes = rule.get("first_response_minutes", 240)
    dec_minutes = rule.get("decision_minutes", 1440)

    # Apply tier multiplier if available
    if isp_tier and tier_multipliers:
        multiplier = tier_multipliers.get(isp_tier, {})
        fr_mult = multiplier.get("first_response", 1.0)
        dec_mult = multiplier.get("decision", 1.0)
        fr_minutes = int(fr_minutes * fr_mult)
        dec_minutes = int(dec_minutes * dec_mult)

    # Compute deadlines
    fr_due = created + timedelta(minutes=fr_minutes)
    dec_due = created + timedelta(minutes=dec_minutes)

    return {
        "created": created.isoformat(),
        "first_response_due": fr_due.isoformat(),
        "decision_due": dec_due.isoformat(),
        "first_response_minutes": fr_minutes,
        "decision_minutes": dec_minutes,
        "severity": severity,
        "tier": isp_tier
    }


def is_breached(now_iso: str, deadline_iso: str) -> bool:
    """
    Check if a deadline has been breached.

    Args:
        now_iso: Current timestamp (ISO 8601)
        deadline_iso: Deadline timestamp (ISO 8601)

    Returns:
        True if deadline has passed
    """
    now = datetime.fromisoformat(now_iso.replace("Z", "+00:00"))
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    deadline = datetime.fromisoformat(deadline_iso.replace("Z", "+00:00"))
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)

    return now > deadline


def get_sla_status(
    sla: Dict,
    current_status: str,
    now: Optional[datetime] = None
) -> Dict:
    """
    Get comprehensive SLA status for a case.

    Args:
        sla: Case SLA configuration
        current_status: Current case status
        now: Optional current time (defaults to now)

    Returns:
        Dict with status for each SLA component
    """
    if now is None:
        now = datetime.now(timezone.utc)

    fr_due = sla.get("first_response_due")
    dec_due = sla.get("decision_due")

    # Determine if SLA components are satisfied
    fr_satisfied = current_status in ["acknowledged", "decided", "closed"]
    dec_satisfied = current_status in ["decided", "closed"]

    result = {
        "first_response": {
            "due": fr_due,
            "satisfied": fr_satisfied,
            "breached": False,
            "remaining_minutes": None
        },
        "decision": {
            "due": dec_due,
            "satisfied": dec_satisfied,
            "breached": False,
            "remaining_minutes": None
        },
        "overall": "on_track"
    }

    # Check first response
    if fr_due:
        fr_dt = datetime.fromisoformat(fr_due.replace("Z", "+00:00"))
        if not fr_satisfied:
            if now > fr_dt:
                result["first_response"]["breached"] = True
                result["overall"] = "breached"
            else:
                remaining = (fr_dt - now).total_seconds() / 60
                result["first_response"]["remaining_minutes"] = int(remaining)

    # Check decision
    if dec_due:
        dec_dt = datetime.fromisoformat(dec_due.replace("Z", "+00:00"))
        if not dec_satisfied:
            if now > dec_dt:
                result["decision"]["breached"] = True
                result["overall"] = "breached"
            else:
                remaining = (dec_dt - now).total_seconds() / 60
                result["decision"]["remaining_minutes"] = int(remaining)

    return result


def check_notification_threshold(
    sla: Dict,
    current_status: str,
    thresholds: List[Dict],
    now: Optional[datetime] = None
) -> Optional[Dict]:
    """
    Check if any notification threshold has been crossed.

    Args:
        sla: Case SLA configuration
        current_status: Current case status
        thresholds: List of threshold configurations
        now: Optional current time

    Returns:
        Threshold configuration if crossed, None otherwise
    """
    if now is None:
        now = datetime.now(timezone.utc)

    # Determine which SLA component to check
    if current_status in ["open", "routed"]:
        due_key = "first_response_due"
        start_key = "created"
    elif current_status in ["acknowledged"]:
        due_key = "decision_due"
        start_key = "created"  # Decision SLA starts at creation
    else:
        return None  # Already satisfied

    due_iso = sla.get(due_key)
    start_iso = sla.get(start_key)

    if not due_iso or not start_iso:
        return None

    due = datetime.fromisoformat(due_iso.replace("Z", "+00:00"))
    start = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))

    total_duration = (due - start).total_seconds()
    elapsed = (now - start).total_seconds()

    if total_duration <= 0:
        return None

    percent_consumed = (elapsed / total_duration) * 100

    # Find highest threshold crossed
    crossed = None
    for threshold in sorted(thresholds, key=lambda t: t.get("percent", 0)):
        if percent_consumed >= threshold.get("percent", 0):
            crossed = threshold

    return crossed


def get_breach_cases(cases: List[Dict], now: Optional[datetime] = None) -> List[Tuple[Dict, str]]:
    """
    Find all cases with SLA breaches.

    Args:
        cases: List of case dictionaries
        now: Optional current time

    Returns:
        List of (case, breach_type) tuples
    """
    if now is None:
        now = datetime.now(timezone.utc)

    breaches = []

    for case in cases:
        status = case.get("status")
        sla = case.get("sla", {})

        if status == "closed":
            continue

        sla_status = get_sla_status(sla, status, now)

        if sla_status["first_response"]["breached"]:
            breaches.append((case, "first_response"))
        elif sla_status["decision"]["breached"]:
            breaches.append((case, "decision"))

    return breaches
