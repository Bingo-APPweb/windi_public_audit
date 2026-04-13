# ═══════════════════════════════════════════════
# W-CACHE-001 · CACHE REPOSITORY
# Data access layer with audit logging
# ═══════════════════════════════════════════════

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from db.models import CacheEntryModel, CacheEventModel


class CacheRepository:
    """
    Repository for cache entries.

    🔥 RULE: Never delete entries. Only update status.
    """

    def __init__(self, db: Session):
        self.db = db

    # ──────────────────────────────────────────────
    # READ OPERATIONS
    # ──────────────────────────────────────────────

    def find_by_key(self, key: str) -> Optional[CacheEntryModel]:
        """Find cache entry by computed key"""
        return self.db.query(CacheEntryModel).filter_by(key=key).first()

    def find_by_id(self, cache_id: str) -> Optional[CacheEntryModel]:
        """Find cache entry by ID"""
        return self.db.query(CacheEntryModel).filter_by(id=cache_id).first()

    def find_by_namespace(
        self,
        namespace: str,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[CacheEntryModel]:
        """Find entries by namespace"""
        query = self.db.query(CacheEntryModel).filter_by(namespace=namespace)
        if status:
            query = query.filter_by(status=status)
        return query.limit(limit).all()

    def find_by_timeline(
        self,
        timeline_id: str,
        status: Optional[str] = None
    ) -> List[CacheEntryModel]:
        """Find all entries in a timeline"""
        query = self.db.query(CacheEntryModel).filter_by(timeline_id=timeline_id)
        if status:
            query = query.filter_by(status=status)
        return query.all()

    def find_expired(self, limit: int = 100) -> List[CacheEntryModel]:
        """Find expired entries that need status update"""
        now = datetime.utcnow()
        return self.db.query(CacheEntryModel).filter(
            and_(
                CacheEntryModel.expires_at < now,
                CacheEntryModel.status == "FRESH"
            )
        ).limit(limit).all()

    # ──────────────────────────────────────────────
    # WRITE OPERATIONS
    # ──────────────────────────────────────────────

    def create(self, entry_data: Dict[str, Any]) -> CacheEntryModel:
        """Create new cache entry"""
        entry = CacheEntryModel(**entry_data)
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)

        # Log event
        self._log_event("CREATE", entry)

        return entry

    def upsert(self, entry_data: Dict[str, Any]) -> CacheEntryModel:
        """Create or update cache entry"""
        existing = self.find_by_key(entry_data.get("key", ""))

        if existing:
            # Update existing
            for k, v in entry_data.items():
                if k != "id" and hasattr(existing, k):
                    setattr(existing, k, v)
            existing.updated_at = datetime.utcnow()
            existing.status = "FRESH"
            self.db.commit()
            self._log_event("UPDATE", existing)
            return existing
        else:
            # Create new
            return self.create(entry_data)

    def update(self, entry: CacheEntryModel, data: Dict[str, Any]) -> CacheEntryModel:
        """Update cache entry"""
        for k, v in data.items():
            if hasattr(entry, k):
                setattr(entry, k, v)
        entry.updated_at = datetime.utcnow()
        self.db.commit()
        return entry

    def increment_hit(self, entry: CacheEntryModel) -> None:
        """Increment hit counter"""
        entry.hit_count += 1
        entry.last_hit_at = datetime.utcnow()
        self.db.commit()
        self._log_event("HIT", entry)

    # ──────────────────────────────────────────────
    # STATUS OPERATIONS (never delete!)
    # ──────────────────────────────────────────────

    def invalidate(
        self,
        entry: CacheEntryModel,
        reason: str
    ) -> CacheEntryModel:
        """Mark entry as invalidated"""
        entry.status = "INVALIDATED"
        entry.invalidation_reason = reason
        entry.invalidated_at = datetime.utcnow()
        entry.updated_at = datetime.utcnow()
        self.db.commit()
        self._log_event("INVALIDATE", entry, reason=reason)
        return entry

    def revoke(
        self,
        entry: CacheEntryModel,
        reason: str
    ) -> CacheEntryModel:
        """Mark entry as revoked (stronger than invalidate)"""
        entry.status = "REVOKED"
        entry.invalidation_reason = reason
        entry.invalidated_at = datetime.utcnow()
        entry.updated_at = datetime.utcnow()
        self.db.commit()
        self._log_event("REVOKE", entry, reason=reason)
        return entry

    def supersede(
        self,
        entry: CacheEntryModel,
        new_entry_id: str,
        reason: str = "SUPERSEDED_BY_NEW_ENTRY"
    ) -> CacheEntryModel:
        """Mark entry as superseded by another entry"""
        entry.status = "SUPERSEDED"
        entry.superseded_by = new_entry_id
        entry.invalidation_reason = reason
        entry.invalidated_at = datetime.utcnow()
        entry.updated_at = datetime.utcnow()
        self.db.commit()
        self._log_event("SUPERSEDE", entry, reason=reason)
        return entry

    def mark_expired(self, entry: CacheEntryModel) -> CacheEntryModel:
        """Mark entry as expired"""
        entry.status = "EXPIRED"
        entry.updated_at = datetime.utcnow()
        self.db.commit()
        self._log_event("EXPIRE", entry)
        return entry

    # ──────────────────────────────────────────────
    # BULK OPERATIONS
    # ──────────────────────────────────────────────

    def invalidate_by_filter(
        self,
        reason: str,
        namespace: Optional[str] = None,
        scope: Optional[str] = None,
        actor_did: Optional[str] = None,
        tenant_id: Optional[str] = None,
        timeline_id: Optional[str] = None,
        case_id: Optional[str] = None
    ) -> int:
        """Invalidate multiple entries by filter"""
        query = self.db.query(CacheEntryModel).filter(
            CacheEntryModel.status == "FRESH"
        )

        if namespace:
            query = query.filter(CacheEntryModel.namespace == namespace)
        if scope:
            query = query.filter(CacheEntryModel.scope == scope)
        if actor_did:
            query = query.filter(CacheEntryModel.actor_did == actor_did)
        if tenant_id:
            query = query.filter(CacheEntryModel.tenant_id == tenant_id)
        if timeline_id:
            query = query.filter(CacheEntryModel.timeline_id == timeline_id)
        if case_id:
            query = query.filter(CacheEntryModel.case_id == case_id)

        now = datetime.utcnow()
        count = query.update({
            "status": "INVALIDATED",
            "invalidation_reason": reason,
            "invalidated_at": now,
            "updated_at": now
        })

        self.db.commit()
        return count

    # ──────────────────────────────────────────────
    # PROMOTION (L2 → L3)
    # ──────────────────────────────────────────────

    def promote_to_proven(
        self,
        entry: CacheEntryModel,
        receipt_id: str,
        ledger_id: str,
        verify_url: str
    ) -> CacheEntryModel:
        """Promote entry to L3_PROVEN with proof metadata"""
        entry.tier = "L3_PROVEN"
        entry.proof_has_receipt = True
        entry.proof_receipt_id = receipt_id
        entry.proof_ledger_id = ledger_id
        entry.proof_verify_url = verify_url
        entry.proof_anchored_at = datetime.utcnow()
        entry.updated_at = datetime.utcnow()
        self.db.commit()
        self._log_event("PROMOTE", entry, reason=f"promoted_to_L3:{receipt_id}")
        return entry

    # ──────────────────────────────────────────────
    # METRICS
    # ──────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.db.query(CacheEntryModel).count()
        fresh = self.db.query(CacheEntryModel).filter_by(status="FRESH").count()
        proven = self.db.query(CacheEntryModel).filter_by(tier="L3_PROVEN").count()

        by_tier = {}
        for tier in ["L1_EPHEMERAL", "L2_DETERMINISTIC", "L3_PROVEN", "L4_POLICY"]:
            by_tier[tier] = self.db.query(CacheEntryModel).filter_by(tier=tier).count()

        return {
            "total_entries": total,
            "fresh_entries": fresh,
            "proven_entries": proven,
            "by_tier": by_tier
        }

    # ──────────────────────────────────────────────
    # EVENT LOGGING
    # ──────────────────────────────────────────────

    def _log_event(
        self,
        event_type: str,
        entry: CacheEntryModel,
        reason: Optional[str] = None
    ) -> None:
        """Log cache event for audit trail"""
        event = CacheEventModel(
            id=str(uuid.uuid4()),
            cache_id=entry.id,
            event_type=event_type,
            namespace=entry.namespace,
            tier=entry.tier,
            actor_did=entry.actor_did,
            tenant_id=entry.tenant_id,
            timeline_id=entry.timeline_id,
            reason=reason,
            created_at=datetime.utcnow()
        )
        self.db.add(event)
        # Don't commit here - let the calling method handle commit

    def log_miss(
        self,
        namespace: str,
        tier: str,
        reason: str,
        actor_did: Optional[str] = None,
        timeline_id: Optional[str] = None
    ) -> None:
        """Log cache miss event"""
        event = CacheEventModel(
            id=str(uuid.uuid4()),
            event_type="MISS",
            namespace=namespace,
            tier=tier,
            actor_did=actor_did,
            timeline_id=timeline_id,
            reason=reason,
            created_at=datetime.utcnow()
        )
        self.db.add(event)
        self.db.commit()

    def log_event(
        self,
        cache_id: str,
        event_type: str,
        reason: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log cache event with optional payload for audit trail"""
        event = CacheEventModel(
            id=str(uuid.uuid4()),
            cache_id=cache_id,
            event_type=event_type,
            reason=reason,
            metadata_json=payload,
            created_at=datetime.utcnow()
        )
        self.db.add(event)
        self.db.commit()

    def get_recent_events(self, limit: int = 100) -> List[CacheEventModel]:
        """Get recent events for monitoring"""
        return self.db.query(CacheEventModel).order_by(
            CacheEventModel.created_at.desc()
        ).limit(limit).all()
