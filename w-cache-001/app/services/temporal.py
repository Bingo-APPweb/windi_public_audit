# ═══════════════════════════════════════════════
# W-CACHE-001 · TEMPORAL CONSISTENCY SERVICE
# Ensures cache entries belong to valid timeline
# ═══════════════════════════════════════════════

from typing import Optional
from db.models import CacheEntryModel
from core.types import CacheReadRequest


class TemporalValidationResult:
    """Result of temporal validation"""
    def __init__(self, valid: bool, reason: Optional[str] = None):
        self.valid = valid
        self.reason = reason


def validate_temporal_consistency(
    entry: CacheEntryModel,
    request: CacheReadRequest
) -> TemporalValidationResult:
    """
    Validate that cache entry is temporally consistent with request.

    🔥 CRITICAL: This is where WINDI cache differs from traditional cache.

    Rules:
    1. Timeline must match exactly
    2. State version must be >= request version (can use newer)
    3. Context hash must match if provided
    4. Policy hash must match if provided
    """

    # Rule 1: Timeline must match
    if entry.timeline_id != request.timeline_id:
        return TemporalValidationResult(
            valid=False,
            reason=f"TIMELINE_MISMATCH:{entry.timeline_id}!={request.timeline_id}"
        )

    # Rule 2: State version check
    # Entry can be from same or newer state, but not older
    if entry.state_version < request.state_version:
        return TemporalValidationResult(
            valid=False,
            reason=f"STATE_VERSION_OLD:{entry.state_version}<{request.state_version}"
        )

    # Rule 3: Context hash (if provided in request)
    if request.context_hash and entry.context_hash:
        if entry.context_hash != request.context_hash:
            return TemporalValidationResult(
                valid=False,
                reason="CONTEXT_MISMATCH"
            )

    # Rule 4: Policy hash (if provided in request)
    if request.policy_hash and entry.policy_hash:
        if entry.policy_hash != request.policy_hash:
            return TemporalValidationResult(
                valid=False,
                reason="POLICY_MISMATCH"
            )

    return TemporalValidationResult(valid=True)


def validate_tier_requirements(
    tier: str,
    context_hash: Optional[str],
    proof_has_receipt: bool
) -> TemporalValidationResult:
    """
    Validate tier-specific requirements.

    Rules:
    - L2+: context_hash recommended
    - L3: proof_has_receipt REQUIRED
    """

    if tier == "L3_PROVEN" and not proof_has_receipt:
        return TemporalValidationResult(
            valid=False,
            reason="L3_REQUIRES_PROOF"
        )

    return TemporalValidationResult(valid=True)


def should_refresh_entry(
    entry: CacheEntryModel,
    current_state_version: int
) -> bool:
    """
    Determine if entry should be refreshed based on temporal state.

    Returns True if:
    - Entry is stale
    - Current state has advanced significantly
    """
    if entry.status != "FRESH":
        return True

    # If state has advanced more than 5 versions, suggest refresh
    version_gap = current_state_version - entry.state_version
    if version_gap > 5:
        return True

    return False
