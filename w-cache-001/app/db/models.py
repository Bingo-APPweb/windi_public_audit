# ═══════════════════════════════════════════════
# W-CACHE-001 · SQLAlchemy MODELS
# Persistent cache with temporal + proof layers
# ═══════════════════════════════════════════════

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, JSON, Index, Text
)
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class CacheEntryModel(Base):
    """
    Cache entry with full temporal and proof tracking.

    🔥 INVARIANTS:
    - timeline_id, state_version, state_hash are REQUIRED
    - L3_PROVEN entries MUST have proof_has_receipt=True
    - Entries are NEVER deleted, only marked INVALIDATED/REVOKED/SUPERSEDED
    """
    __tablename__ = "cache_entries"

    id = Column(String(36), primary_key=True)
    key = Column(String(64), unique=True, nullable=False, index=True)

    # Classification
    namespace = Column(String(128), nullable=False)
    tier = Column(String(20), nullable=False)
    scope = Column(String(20), nullable=False)
    sensitivity = Column(String(20), nullable=False, default="MEDIUM")

    # Identity
    actor_did = Column(String(128), nullable=True)
    tenant_id = Column(String(64), nullable=True)

    # Domain
    case_id = Column(String(64), nullable=True)
    document_id = Column(String(64), nullable=True)
    receipt_id = Column(String(128), nullable=True)

    # Hashes
    input_hash = Column(String(64), nullable=True)
    context_hash = Column(String(64), nullable=True)
    policy_hash = Column(String(64), nullable=True)
    content_hash = Column(String(64), nullable=True)

    # Value (JSON)
    value = Column(JSON, nullable=False)

    # Status
    status = Column(String(20), nullable=False, default="FRESH")
    hit_count = Column(Integer, default=0)
    last_hit_at = Column(DateTime, nullable=True)

    # Invalidation tracking
    invalidation_reason = Column(String(256), nullable=True)
    invalidated_at = Column(DateTime, nullable=True)
    superseded_by = Column(String(36), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    # 🧬 TEMPORAL LAYER (CRITICAL)
    timeline_id = Column(String(128), nullable=False)
    state_version = Column(Integer, nullable=False)
    state_hash = Column(String(64), nullable=False)
    parent_hash = Column(String(64), nullable=True)

    # 🔐 PROOF LAYER
    proof_has_receipt = Column(Boolean, default=False)
    proof_receipt_id = Column(String(128), nullable=True)
    proof_ledger_id = Column(String(128), nullable=True)
    proof_verify_url = Column(String(256), nullable=True)
    proof_anchored_at = Column(DateTime, nullable=True)

    # Metadata
    metadata_json = Column(JSON, nullable=True)

    # Indices for common queries
    __table_args__ = (
        Index("ix_namespace_tier", "namespace", "tier"),
        Index("ix_actor_did", "actor_did"),
        Index("ix_tenant_id", "tenant_id"),
        Index("ix_timeline_id", "timeline_id"),
        Index("ix_receipt_id", "receipt_id"),
        Index("ix_status", "status"),
        Index("ix_expires_at", "expires_at"),
    )

    def to_dict(self):
        """Convert to dictionary for API response"""
        return {
            "cache_id": self.id,
            "key": self.key,
            "namespace": self.namespace,
            "tier": self.tier,
            "scope": self.scope,
            "sensitivity": self.sensitivity,
            "status": self.status,
            "value": self.value,
            "actor_did": self.actor_did,
            "tenant_id": self.tenant_id,
            "input_hash": self.input_hash,
            "context_hash": self.context_hash,
            "hit_count": self.hit_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "timeline": {
                "timeline_id": self.timeline_id,
                "state_version": self.state_version,
                "state_hash": self.state_hash,
                "parent_hash": self.parent_hash
            },
            "proof": {
                "has_receipt": self.proof_has_receipt,
                "receipt_id": self.proof_receipt_id,
                "ledger_id": self.proof_ledger_id,
                "verify_url": self.proof_verify_url,
                "anchored_at": self.proof_anchored_at.isoformat() if self.proof_anchored_at else None
            }
        }


class CacheEventModel(Base):
    """
    Event log for cache operations.
    Supports audit trail and metrics.
    """
    __tablename__ = "cache_events"

    id = Column(String(36), primary_key=True)
    cache_id = Column(String(36), nullable=True)
    event_type = Column(String(32), nullable=False)  # HIT, MISS, CREATE, INVALIDATE, REVOKE, PROMOTE
    namespace = Column(String(128), nullable=True)
    tier = Column(String(20), nullable=True)

    # Context
    actor_did = Column(String(128), nullable=True)
    tenant_id = Column(String(64), nullable=True)
    timeline_id = Column(String(128), nullable=True)

    # Details
    reason = Column(String(256), nullable=True)
    metadata_json = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_event_type", "event_type"),
        Index("ix_event_created", "created_at"),
        Index("ix_event_namespace", "namespace"),
    )
