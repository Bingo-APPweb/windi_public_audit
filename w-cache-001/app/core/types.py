# ═══════════════════════════════════════════════
# W-CACHE-001 · CORE TYPES v1.0
# Verifiable Cache Layer for Regulated Systems
# ═══════════════════════════════════════════════

from pydantic import BaseModel
from typing import Optional, Dict, Any, Literal
from datetime import datetime


# ──────────────────────────────────────────────
# ENUMS
# ──────────────────────────────────────────────

CacheTier = Literal[
    "L1_EPHEMERAL",
    "L2_DETERMINISTIC",
    "L3_PROVEN",
    "L4_POLICY"
]

CacheStatus = Literal[
    "FRESH",
    "STALE",
    "INVALIDATED",
    "REVOKED",
    "EXPIRED",
    "SUPERSEDED"
]

CacheScope = Literal[
    "GLOBAL",
    "TENANT",
    "ACTOR",
    "DID",
    "CASE",
    "DOCUMENT",
    "RECEIPT"
]

CacheSensitivity = Literal[
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL"
]


# ──────────────────────────────────────────────
# 🧬 TEMPORAL LAYER
# ──────────────────────────────────────────────

class TimelineMetadata(BaseModel):
    timeline_id: str
    state_version: int
    state_hash: str
    parent_hash: Optional[str] = None


# ──────────────────────────────────────────────
# 🔐 PROOF LAYER
# ──────────────────────────────────────────────

class ProofMetadata(BaseModel):
    has_receipt: bool = False
    receipt_id: Optional[str] = None
    ledger_id: Optional[str] = None
    verify_url: Optional[str] = None
    anchored_at: Optional[str] = None


# ──────────────────────────────────────────────
# 🧾 CACHE ENTRY (CANÔNICO)
# ──────────────────────────────────────────────

class CacheEntry(BaseModel):
    cache_id: str
    tier: CacheTier
    namespace: str
    key: str

    value: Dict[str, Any]

    status: CacheStatus
    scope: CacheScope
    sensitivity: CacheSensitivity

    # identidade
    actor_did: Optional[str] = None
    tenant_id: Optional[str] = None

    # domínio
    case_id: Optional[str] = None
    document_id: Optional[str] = None
    receipt_id: Optional[str] = None

    # hashes estruturais
    input_hash: Optional[str] = None
    context_hash: Optional[str] = None
    policy_hash: Optional[str] = None
    content_hash: Optional[str] = None

    # tempo
    created_at: datetime
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    ttl_seconds: Optional[int] = None

    # métricas
    hit_count: int = 0
    last_hit_at: Optional[datetime] = None

    # estado evolutivo
    invalidation_reason: Optional[str] = None
    invalidated_at: Optional[datetime] = None
    superseded_by: Optional[str] = None

    # 🧬 TEMPORAL
    timeline: TimelineMetadata

    # 🔐 PROOF
    proof: ProofMetadata

    metadata: Optional[Dict[str, Any]] = None


# ──────────────────────────────────────────────
# REQUEST/RESPONSE DTOs
# ──────────────────────────────────────────────

class CacheReadRequest(BaseModel):
    namespace: str
    tier: CacheTier
    scope: CacheScope

    actor_did: Optional[str] = None
    tenant_id: Optional[str] = None

    input_hash: Optional[str] = None
    context_hash: Optional[str] = None
    policy_hash: Optional[str] = None

    timeline_id: str
    state_version: int


class CacheWriteRequest(BaseModel):
    namespace: str
    tier: CacheTier
    scope: CacheScope
    sensitivity: CacheSensitivity = "MEDIUM"

    value: Dict[str, Any]

    actor_did: Optional[str] = None
    tenant_id: Optional[str] = None

    input_hash: Optional[str] = None
    context_hash: Optional[str] = None
    policy_hash: Optional[str] = None
    content_hash: Optional[str] = None

    ttl_seconds: int = 300

    timeline: TimelineMetadata

    metadata: Optional[Dict[str, Any]] = None


class CacheReadResult(BaseModel):
    hit: bool
    cache_id: Optional[str] = None
    tier: Optional[CacheTier] = None
    status: Optional[CacheStatus] = None
    value: Optional[Dict[str, Any]] = None
    proof: Optional[ProofMetadata] = None
    miss_reason: Optional[str] = None


class InvalidateRequest(BaseModel):
    namespace: Optional[str] = None
    scope: Optional[CacheScope] = None
    actor_did: Optional[str] = None
    tenant_id: Optional[str] = None
    case_id: Optional[str] = None
    timeline_id: Optional[str] = None
    reason: str


class PromoteRequest(BaseModel):
    cache_id: str
    receipt_id: Optional[str] = None
    content_hash: str
    actor_did: Optional[str] = None
    verify_url: Optional[str] = None
    anchor_to_ledger: bool = False
    promotion_reason: str = "MANUAL_PROMOTION"
