# ═══════════════════════════════════════════════
# W-CACHE-001 · CACHE SERVICE
# Core business logic with temporal consistency
# ═══════════════════════════════════════════════

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session

from core.key import generate_cache_key
from core.config import DEFAULT_TTL
from core.types import (
    CacheReadRequest, CacheWriteRequest, CacheReadResult,
    InvalidateRequest, PromoteRequest, ProofMetadata
)
from repository.cache_repository import CacheRepository
from services.temporal import validate_temporal_consistency, validate_tier_requirements
from services.ledger_adapter import LedgerAdapter
from core.policy_engine import evaluate_promotion_policy


class CacheService:
    """
    Core cache service with temporal consistency and proof support.

    🔥 INVARIANTS:
    - I11: Cache never substitutes proof
    - I9: Cache doesn't auto-escalate decisions
    - I14: Cache miss = explicit, never silent
    """

    def __init__(self, db: Session):
        self.repo = CacheRepository(db)
        self.ledger = LedgerAdapter()

    # ──────────────────────────────────────────────
    # GET (with temporal validation)
    # ──────────────────────────────────────────────

    def get(self, request: CacheReadRequest) -> CacheReadResult:
        """
        Get cache entry with full temporal validation.

        Returns hit only if:
        1. Entry exists
        2. Entry is FRESH
        3. Entry is not expired
        4. Temporal consistency is valid
        """
        # Generate key
        key = generate_cache_key(
            namespace=request.namespace,
            tier=request.tier,
            input_hash=request.input_hash,
            context_hash=request.context_hash,
            policy_hash=request.policy_hash,
            actor_did=request.actor_did,
            tenant_id=request.tenant_id,
            timeline_id=request.timeline_id,
            state_version=request.state_version
        )

        # Find entry
        entry = self.repo.find_by_key(key)

        if not entry:
            self.repo.log_miss(
                namespace=request.namespace,
                tier=request.tier,
                reason="NOT_FOUND",
                actor_did=request.actor_did,
                timeline_id=request.timeline_id
            )
            return CacheReadResult(hit=False, miss_reason="NOT_FOUND")

        # Check status
        if entry.status == "REVOKED":
            return CacheReadResult(hit=False, miss_reason="REVOKED")

        if entry.status == "INVALIDATED":
            return CacheReadResult(hit=False, miss_reason="INVALIDATED")

        if entry.status == "SUPERSEDED":
            return CacheReadResult(hit=False, miss_reason="SUPERSEDED")

        # Check expiration
        if entry.expires_at and datetime.utcnow() > entry.expires_at:
            self.repo.mark_expired(entry)
            return CacheReadResult(hit=False, miss_reason="EXPIRED")

        # 🔥 TEMPORAL VALIDATION (critical differentiator)
        temporal_result = validate_temporal_consistency(entry, request)
        if not temporal_result.valid:
            self.repo.log_miss(
                namespace=request.namespace,
                tier=request.tier,
                reason=temporal_result.reason,
                actor_did=request.actor_did,
                timeline_id=request.timeline_id
            )
            return CacheReadResult(
                hit=False,
                miss_reason=f"TEMPORAL:{temporal_result.reason}"
            )

        # Success - increment hit
        self.repo.increment_hit(entry)

        return CacheReadResult(
            hit=True,
            cache_id=entry.id,
            tier=entry.tier,
            status=entry.status,
            value=entry.value,
            proof=ProofMetadata(
                has_receipt=entry.proof_has_receipt,
                receipt_id=entry.proof_receipt_id,
                ledger_id=entry.proof_ledger_id,
                verify_url=entry.proof_verify_url,
                anchored_at=entry.proof_anchored_at.isoformat() if entry.proof_anchored_at else None
            )
        )

    # ──────────────────────────────────────────────
    # PUT (with tier validation)
    # ──────────────────────────────────────────────

    def put(self, request: CacheWriteRequest) -> Dict[str, Any]:
        """
        Create or update cache entry.

        Validates:
        - Timeline metadata is present
        - Tier requirements are met
        """
        # Generate key
        key = generate_cache_key(
            namespace=request.namespace,
            tier=request.tier,
            input_hash=request.input_hash,
            context_hash=request.context_hash,
            policy_hash=request.policy_hash,
            actor_did=request.actor_did,
            tenant_id=request.tenant_id,
            timeline_id=request.timeline.timeline_id,
            state_version=request.timeline.state_version
        )

        # Calculate TTL
        ttl = request.ttl_seconds or DEFAULT_TTL.get(request.tier, 300)
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)

        # Validate tier requirements
        tier_valid = validate_tier_requirements(
            tier=request.tier,
            context_hash=request.context_hash,
            proof_has_receipt=False  # New entries start without proof
        )
        if not tier_valid.valid:
            return {"ok": False, "error": tier_valid.reason}

        # Build entry data
        entry_data = {
            "id": str(uuid.uuid4()),
            "key": key,
            "namespace": request.namespace,
            "tier": request.tier,
            "scope": request.scope,
            "sensitivity": request.sensitivity,
            "status": "FRESH",
            "value": request.value,
            "actor_did": request.actor_did,
            "tenant_id": request.tenant_id,
            "input_hash": request.input_hash,
            "context_hash": request.context_hash,
            "policy_hash": request.policy_hash,
            "content_hash": request.content_hash,
            "timeline_id": request.timeline.timeline_id,
            "state_version": request.timeline.state_version,
            "state_hash": request.timeline.state_hash,
            "parent_hash": request.timeline.parent_hash,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "hit_count": 0,
            "proof_has_receipt": False,
            "metadata_json": request.metadata
        }

        # Upsert
        entry = self.repo.upsert(entry_data)

        return {
            "ok": True,
            "cache_id": entry.id,
            "key": key,
            "status": "FRESH",
            "expires_at": expires_at.isoformat()
        }

    # ──────────────────────────────────────────────
    # INVALIDATE
    # ──────────────────────────────────────────────

    def invalidate(self, request: InvalidateRequest) -> Dict[str, Any]:
        """
        Invalidate cache entries by filter.

        🔥 RULE: Never delete. Only mark status.
        """
        count = self.repo.invalidate_by_filter(
            reason=request.reason,
            namespace=request.namespace,
            scope=request.scope,
            actor_did=request.actor_did,
            tenant_id=request.tenant_id,
            timeline_id=request.timeline_id,
            case_id=request.case_id
        )

        return {
            "ok": True,
            "invalidated_count": count,
            "reason": request.reason
        }

    # ──────────────────────────────────────────────
    # REVOKE (stronger than invalidate)
    # ──────────────────────────────────────────────

    def revoke(self, cache_id: str, reason: str) -> Dict[str, Any]:
        """
        Revoke a specific cache entry.

        Used for security/governance scenarios.
        """
        entry = self.repo.find_by_id(cache_id)
        if not entry:
            return {"ok": False, "error": "NOT_FOUND"}

        self.repo.revoke(entry, reason)

        return {
            "ok": True,
            "cache_id": cache_id,
            "status": "REVOKED",
            "reason": reason
        }

    # ──────────────────────────────────────────────
    # PROMOTE TO PROVEN (L2 → L3)
    # ──────────────────────────────────────────────

    def promote_to_proven(self, request: PromoteRequest) -> Dict[str, Any]:
        """
        Promote cache entry from L2 to L3_PROVEN.

        🔥 CRITICAL: This is where cache becomes VERIFIED.
        Entry gets linked to receipt/ledger with proof metadata.

        Validations:
        - Entry must exist
        - Entry must be L2_DETERMINISTIC
        - Entry must be in admissible status (not REVOKED/INVALIDATED/etc)
        - Entry must not already be proven
        - content_hash is required
        - Either receipt_id OR anchor_to_ledger must be provided
        """
        cache_id = request.cache_id
        receipt_id = request.receipt_id
        content_hash = request.content_hash
        actor_did = request.actor_did
        verify_url = request.verify_url
        anchor_to_ledger = request.anchor_to_ledger
        promotion_reason = request.promotion_reason

        # 1. Find entry
        entry = self.repo.find_by_id(cache_id)
        if not entry:
            return {"ok": False, "reason": "CACHE_ENTRY_NOT_FOUND"}

        # 1.5 🔥 POLICY CHECK (W-CACHE-002)
        # promote() does NOT decide alone → asks policy → executes decision
        policy_context = {
            "human_approved": request.human_approved,
            "actor_did": actor_did,
            "anchor_to_ledger": anchor_to_ledger,
            "promotion_reason": promotion_reason
        }

        policy_result = evaluate_promotion_policy(entry, policy_context)

        if not policy_result.allow:
            # Log denial event for NOIR dashboard
            self.repo.log_event(
                cache_id=entry.id,
                event_type="PROMOTION_DENIED",
                reason=policy_result.reason,
                payload={
                    "namespace": entry.namespace,
                    "policy_mode": policy_result.mode,
                    "requires_human": policy_result.requires_human
                }
            )
            return {
                "ok": False,
                "reason": policy_result.reason,
                "policy_mode": policy_result.mode,
                "requires_human": policy_result.requires_human
            }

        # 2. Check tier - only L2 can be promoted
        if entry.tier != "L2_DETERMINISTIC":
            return {"ok": False, "reason": "ONLY_L2_CAN_BE_PROMOTED"}

        # 3. Check status - must be admissible
        if entry.status in ["REVOKED", "INVALIDATED", "EXPIRED", "SUPERSEDED"]:
            return {"ok": False, "reason": "ENTRY_NOT_ADMISSIBLE_FOR_PROMOTION"}

        # 4. Check if already proven
        if getattr(entry, "proof_has_receipt", False):
            return {"ok": False, "reason": "ENTRY_ALREADY_PROVEN"}

        # 5. Validate content_hash
        if not content_hash:
            return {"ok": False, "reason": "CONTENT_HASH_REQUIRED"}

        # 6. Validate receipt source
        if not receipt_id and not anchor_to_ledger:
            return {"ok": False, "reason": "RECEIPT_OR_LEDGER_ANCHOR_REQUIRED"}

        ledger_result = None

        # 7. Anchor to ledger if requested OR if policy requires it
        # 🔥 W-CACHE-002: Policy mode ANCHORED forces ledger anchor
        should_anchor = anchor_to_ledger or policy_result.mode == "ANCHORED"
        if should_anchor:
            ledger_result = self.ledger.anchor_cache_promotion(
                entry=entry,
                actor_did=actor_did,
                receipt_id=receipt_id,
                content_hash=content_hash,
                promotion_reason=promotion_reason
            )

            if not ledger_result.get("ok"):
                # Log failure event
                self.repo.log_event(
                    cache_id=entry.id,
                    event_type="PROMOTION_FAILED",
                    reason="LEDGER_ANCHOR_FAILED",
                    payload=ledger_result
                )
                return {
                    "ok": False,
                    "reason": "LEDGER_ANCHOR_FAILED",
                    "detail": ledger_result
                }

        # 8. Determine final values
        final_receipt_id = receipt_id or (ledger_result.get("ledger_id") if ledger_result else None)
        final_verify_url = verify_url or (ledger_result.get("verify_url") if ledger_result else f"https://windi-domain.com/verify/{final_receipt_id}")
        final_ledger_id = ledger_result.get("ledger_id") if ledger_result else final_receipt_id

        # 9. Update entry to L3_PROVEN
        self.repo.promote_to_proven(
            entry=entry,
            receipt_id=final_receipt_id,
            ledger_id=final_ledger_id,
            verify_url=final_verify_url
        )

        # Also update content_hash
        self.repo.update(entry, {"content_hash": content_hash})

        # 10. Log promotion event
        self.repo.log_event(
            cache_id=entry.id,
            event_type="PROMOTE_TO_PROVEN",
            reason=promotion_reason,
            payload={
                "from_tier": "L2_DETERMINISTIC",
                "to_tier": "L3_PROVEN",
                "receipt_id": final_receipt_id,
                "ledger_id": final_ledger_id,
                "verify_url": final_verify_url,
                "content_hash": content_hash
            }
        )

        return {
            "ok": True,
            "cache_id": entry.id,
            "from_tier": "L2_DETERMINISTIC",
            "to_tier": "L3_PROVEN",
            "proof": {
                "has_receipt": True,
                "receipt_id": final_receipt_id,
                "ledger_id": final_ledger_id,
                "verify_url": final_verify_url
            }
        }

    # ──────────────────────────────────────────────
    # METRICS
    # ──────────────────────────────────────────────

    def get_metrics(self) -> Dict[str, Any]:
        """Get cache metrics for dashboard"""
        stats = self.repo.get_stats()
        events = self.repo.get_recent_events(limit=1000)

        # Calculate hit/miss rates from events
        hits = sum(1 for e in events if e.event_type == "HIT")
        misses = sum(1 for e in events if e.event_type == "MISS")
        total = hits + misses

        hit_rate = hits / total if total > 0 else 0
        miss_rate = misses / total if total > 0 else 0

        # Count temporal mismatches
        temporal_misses = sum(
            1 for e in events
            if e.event_type == "MISS" and e.reason and "TEMPORAL" in e.reason
        )

        # Count promotions
        promotion_count = sum(1 for e in events if e.event_type == "PROMOTE_TO_PROVEN")
        promotion_failures = sum(1 for e in events if e.event_type == "PROMOTION_FAILED")

        return {
            "ok": True,
            "global": {
                "hit_rate": round(hit_rate, 3),
                "miss_rate": round(miss_rate, 3),
                "total_entries": stats["total_entries"],
                "fresh_entries": stats["fresh_entries"],
                "proven_entries": stats["proven_entries"],
                "promotion_count": promotion_count,
                "promotion_failures": promotion_failures
            },
            "by_tier": stats["by_tier"],
            "integrity": {
                "temporal_mismatches": temporal_misses,
                "temporal_mismatch_rate": round(temporal_misses / total, 3) if total > 0 else 0
            }
        }

    # ──────────────────────────────────────────────
    # HEALTH
    # ──────────────────────────────────────────────

    def health(self) -> Dict[str, Any]:
        """Health check"""
        ledger_ok = self.ledger.health_check()

        return {
            "ok": True,
            "service": "W-CACHE-001",
            "version": "1.0.0",
            "stores": {
                "database": "healthy",
                "ledger_link": "healthy" if ledger_ok else "degraded"
            }
        }

    # ──────────────────────────────────────────────
    # EVENTS (for NOIR Dashboard)
    # ──────────────────────────────────────────────

    def get_events(self, limit: int = 20) -> Dict[str, Any]:
        """Get recent events for NOIR dashboard"""
        events = self.repo.get_recent_events(limit=limit)

        return {
            "ok": True,
            "events": [
                {
                    "id": e.id,
                    "cache_id": e.cache_id,
                    "event_type": e.event_type,
                    "reason": e.reason,
                    "created_at": e.created_at.isoformat() if e.created_at else None
                }
                for e in events
            ],
            "count": len(events)
        }
