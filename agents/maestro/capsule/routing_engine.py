#!/usr/bin/env python3
"""
WINDI Maestro — Routing Engine
==============================

Deterministic routing of cases to human authorities.
Routing decisions are based on:
- Severity level (R1-R5)
- Invariants at risk (I1-I9)
- ISP tier (tier1/tier2/tier3)

The routing matrix is YAML-based and fully auditable.
No heuristics, no ML — pure rule matching.

Routing Priority:
1. Specific invariant matches (I9 > I1 > others)
2. Severity matches (R5 > R4 > R3 > R2 > R1)
3. Default fallback

Principles:
- DETERMINISTIC: Same input always produces same route
- AUDITABLE: Every routing decision is traceable to a rule
- NO AD-HOC: Routing follows ISP-defined authority chains only
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("WINDI.Maestro.Routing")


def load_routing_matrix(path: str) -> Dict:
    """
    Load routing matrix from YAML file.

    Args:
        path: Path to routing_matrix.yaml

    Returns:
        Parsed routing configuration
    """
    with open(path, "r") as f:
        config = yaml.safe_load(f)
    logger.info(f"Loaded routing matrix from {path}")
    return config


def _severity_ge(a: str, b: str) -> bool:
    """
    Check if severity a >= severity b.

    Severity order: R0 < R1 < R2 < R3 < R4 < R5
    """
    order = {f"R{i}": i for i in range(6)}
    return order.get(a, 0) >= order.get(b, 0)


def _invariants_match(rule_invariants: List[str], case_invariants: List[str]) -> bool:
    """Check if any rule invariant matches case invariants."""
    if not rule_invariants:
        return False
    return any(inv in case_invariants for inv in rule_invariants)


def pick_route(
    routing_cfg: Dict,
    severity: str,
    invariants: List[str],
    isp_tier: Optional[str] = None
) -> Dict:
    """
    Pick the appropriate route for a case.

    Evaluates rules in order, returns first match.
    If no match, returns default route.

    Args:
        routing_cfg: Loaded routing configuration
        severity: Case severity (R1-R5)
        invariants: List of invariants at risk
        isp_tier: Optional ISP tier for route customization

    Returns:
        Route configuration dict with:
        - role: Target role for assignment
        - channel: Notification channel
        - require_dual_ack: Whether dual acknowledgment is required
        - rule_matched: Which rule was matched (for audit)
    """
    routes = routing_cfg.get("routes", [])

    for idx, rule in enumerate(routes):
        match = rule.get("match", {})

        # Check severity match
        sev_min = match.get("severity_min")
        if sev_min and not _severity_ge(severity, sev_min):
            continue

        # Check invariant match
        inv_any = match.get("invariants_any")
        if inv_any and not _invariants_match(inv_any, invariants):
            continue

        # Check ISP tier match if specified
        tier_match = match.get("isp_tier")
        if tier_match and isp_tier and tier_match != isp_tier:
            continue

        # All conditions met — return this route
        route = rule["route_to"].copy()
        route["rule_matched"] = f"rule_{idx}"
        route["match_criteria"] = match

        logger.info(
            f"Route matched: rule_{idx} → {route.get('role')} "
            f"(severity={severity}, invariants={invariants})"
        )

        return route

    # No rule matched — use default
    default = routing_cfg.get("default", {}).copy()
    default["rule_matched"] = "default"
    default["match_criteria"] = None

    logger.info(
        f"Route default: {default.get('role')} "
        f"(severity={severity}, invariants={invariants})"
    )

    return default


def explain_route(route: Dict) -> str:
    """
    Generate human-readable explanation of routing decision.

    For I6 (Right to Explanation) compliance.
    """
    rule = route.get("rule_matched", "unknown")
    criteria = route.get("match_criteria")
    role = route.get("role", "unknown")
    channel = route.get("channel", "standard")
    dual = route.get("require_dual_ack", False)

    explanation = f"Case routed to '{role}' via '{channel}' channel.\n"

    if criteria:
        if criteria.get("severity_min"):
            explanation += f"- Matched severity >= {criteria['severity_min']}\n"
        if criteria.get("invariants_any"):
            explanation += f"- Matched invariants: {criteria['invariants_any']}\n"
    else:
        explanation += "- No specific rule matched; using default routing.\n"

    if dual:
        explanation += "- Dual acknowledgment REQUIRED (four-eyes principle).\n"

    explanation += f"- Rule applied: {rule}"

    return explanation


def get_escalation_target(
    routing_cfg: Dict,
    current_role: str
) -> Optional[str]:
    """
    Get next role in escalation hierarchy.

    Args:
        routing_cfg: Routing configuration with role_hierarchy
        current_role: Current assigned role

    Returns:
        Next role in hierarchy, or None if already at top
    """
    hierarchy = routing_cfg.get("role_hierarchy", [])

    if not hierarchy:
        return None

    try:
        current_idx = hierarchy.index(current_role)
        if current_idx < len(hierarchy) - 1:
            return hierarchy[current_idx + 1]
    except ValueError:
        pass

    return None


def get_channel_config(routing_cfg: Dict, channel: str) -> Dict:
    """Get configuration for a notification channel."""
    channels = routing_cfg.get("channels", {})
    return channels.get(channel, {})
