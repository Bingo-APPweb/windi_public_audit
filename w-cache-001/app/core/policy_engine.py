# ═══════════════════════════════════════════════
# W-CACHE-002 · POLICY ENGINE
# Runtime governance for cache promotion decisions
# ═══════════════════════════════════════════════
#
# INVARIANTS:
# - I9: System suggests, human decides
# - I11: Proof anchoring requires governance
# - I14: Explicit denial, never silent bypass
#
# "Speed without governance is noise.
#  Speed with governance is power."
# ═══════════════════════════════════════════════

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PolicyResult:
    """Result of policy evaluation"""
    allow: bool
    mode: str  # REFERENTIAL | ANCHORED | DENY
    reason: str
    requires_human: bool = False


def evaluate_promotion_policy(
    entry,
    context: Dict[str, Any]
) -> PolicyResult:
    """
    Evaluate if a cache entry can be promoted to L3_PROVEN.

    🔥 CORE PRINCIPLE:
    - promote() does NOT decide alone
    - promote() asks policy
    - promote() executes decision

    Args:
        entry: Cache entry being promoted
        context: Runtime context including:
            - human_approved: bool
            - actor_did: str
            - promotion_reason: str
            - anchor_to_ledger: bool

    Returns:
        PolicyResult with allow/deny and reasoning
    """
    namespace = entry.namespace

    # ──────────────────────────────────────────────
    # VERIFY NAMESPACE → Auto-allowed (safe)
    # ──────────────────────────────────────────────
    if namespace and namespace.startswith("verify."):
        return PolicyResult(
            allow=True,
            mode="REFERENTIAL",
            reason="VERIFY_SAFE_AUTO",
            requires_human=False
        )

    # ──────────────────────────────────────────────
    # ENTERPRISE NAMESPACE → Requires human approval
    # ──────────────────────────────────────────────
    if namespace and namespace.startswith("enterprise."):
        human_approved = context.get("human_approved", False)

        if not human_approved:
            return PolicyResult(
                allow=False,
                mode="DENY",
                reason="HUMAN_APPROVAL_REQUIRED",
                requires_human=True
            )

        return PolicyResult(
            allow=True,
            mode="ANCHORED",
            reason="APPROVED_DECISION",
            requires_human=False
        )

    # ──────────────────────────────────────────────
    # LEGAL NAMESPACE → Always requires human + anchor
    # ──────────────────────────────────────────────
    if namespace and namespace.startswith("legal."):
        human_approved = context.get("human_approved", False)
        anchor_requested = context.get("anchor_to_ledger", False)

        if not human_approved:
            return PolicyResult(
                allow=False,
                mode="DENY",
                reason="LEGAL_REQUIRES_HUMAN_APPROVAL",
                requires_human=True
            )

        if not anchor_requested:
            return PolicyResult(
                allow=False,
                mode="DENY",
                reason="LEGAL_REQUIRES_LEDGER_ANCHOR",
                requires_human=False
            )

        return PolicyResult(
            allow=True,
            mode="ANCHORED",
            reason="LEGAL_APPROVED_AND_ANCHORED",
            requires_human=False
        )

    # ──────────────────────────────────────────────
    # TRAVEL NAMESPACE → Auto-allowed (user content)
    # ──────────────────────────────────────────────
    if namespace and namespace.startswith("travel."):
        return PolicyResult(
            allow=True,
            mode="REFERENTIAL",
            reason="TRAVEL_USER_CONTENT",
            requires_human=False
        )

    # ──────────────────────────────────────────────
    # CACHE/SYSTEM NAMESPACE → Internal, auto-allowed
    # ──────────────────────────────────────────────
    if namespace and namespace.startswith(("cache.", "system.")):
        return PolicyResult(
            allow=True,
            mode="REFERENTIAL",
            reason="INTERNAL_SYSTEM",
            requires_human=False
        )

    # ──────────────────────────────────────────────
    # DEFAULT → Deny unknown namespaces (I14)
    # ──────────────────────────────────────────────
    return PolicyResult(
        allow=False,
        mode="DENY",
        reason="NO_POLICY_FOR_NAMESPACE",
        requires_human=False
    )


def get_policy_registry() -> Dict[str, Dict[str, Any]]:
    """
    Return the current policy registry for dashboard display.

    Future: This will be loaded from YAML/JSON config.
    """
    return {
        "verify.*": {
            "auto_allow": True,
            "mode": "REFERENTIAL",
            "requires_human": False,
            "description": "Verification receipts - safe for auto-promotion"
        },
        "enterprise.*": {
            "auto_allow": False,
            "mode": "ANCHORED",
            "requires_human": True,
            "description": "Enterprise decisions - human approval required"
        },
        "legal.*": {
            "auto_allow": False,
            "mode": "ANCHORED",
            "requires_human": True,
            "description": "Legal documents - human approval + ledger anchor required"
        },
        "travel.*": {
            "auto_allow": True,
            "mode": "REFERENTIAL",
            "requires_human": False,
            "description": "Travel content - user-owned, auto-promotion"
        },
        "cache.*": {
            "auto_allow": True,
            "mode": "REFERENTIAL",
            "requires_human": False,
            "description": "Internal cache operations"
        },
        "system.*": {
            "auto_allow": True,
            "mode": "REFERENTIAL",
            "requires_human": False,
            "description": "System operations"
        },
        "default": {
            "auto_allow": False,
            "mode": "DENY",
            "requires_human": False,
            "description": "Unknown namespaces - denied by default (I14)"
        }
    }
