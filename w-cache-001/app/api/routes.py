# ═══════════════════════════════════════════════
# W-CACHE-001 · API ROUTES
# FastAPI endpoints for Verifiable Cache Layer
# ═══════════════════════════════════════════════

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.session import get_db
from services.cache_service import CacheService
from core.types import (
    CacheReadRequest, CacheWriteRequest,
    InvalidateRequest, PromoteRequest
)

router = APIRouter()


def get_cache_service(db: Session = Depends(get_db)) -> CacheService:
    """Dependency injection for cache service"""
    return CacheService(db)


# ──────────────────────────────────────────────
# READ
# ──────────────────────────────────────────────

@router.post("/get")
def get_cache(
    request: CacheReadRequest,
    service: CacheService = Depends(get_cache_service)
):
    """
    Get cache entry with temporal validation.

    Returns hit only if entry exists, is fresh, and temporally consistent.
    """
    result = service.get(request)
    return result.model_dump()


# ──────────────────────────────────────────────
# WRITE
# ──────────────────────────────────────────────

@router.post("/entries")
def put_cache(
    request: CacheWriteRequest,
    service: CacheService = Depends(get_cache_service)
):
    """
    Create or update cache entry.

    Requires timeline metadata (timeline_id, state_version, state_hash).
    """
    result = service.put(request)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


# ──────────────────────────────────────────────
# INVALIDATE
# ──────────────────────────────────────────────

@router.post("/invalidate")
def invalidate_cache(
    request: InvalidateRequest,
    service: CacheService = Depends(get_cache_service)
):
    """
    Invalidate cache entries by filter.

    🔥 RULE: Never deletes. Only marks status as INVALIDATED.
    """
    result = service.invalidate(request)
    return result


# ──────────────────────────────────────────────
# REVOKE
# ──────────────────────────────────────────────

@router.post("/revoke")
def revoke_cache(
    cache_id: str,
    reason: str,
    service: CacheService = Depends(get_cache_service)
):
    """
    Revoke a specific cache entry.

    Stronger than invalidate - used for security/governance scenarios.
    """
    result = service.revoke(cache_id, reason)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


# ──────────────────────────────────────────────
# PROMOTE (L2 → L3)
# ──────────────────────────────────────────────

@router.post("/promote")
def promote_to_proven(
    request: PromoteRequest,
    service: CacheService = Depends(get_cache_service)
):
    """
    Promote cache entry to L3_PROVEN.

    Links entry to receipt and optionally anchors provenance to ledger.
    """
    result = service.promote_to_proven(request)
    if not result.get("ok"):
        raise HTTPException(
            status_code=400,
            detail=result.get("reason") or result.get("error") or "PROMOTION_FAILED"
        )
    return result


# ──────────────────────────────────────────────
# METRICS
# ──────────────────────────────────────────────

@router.get("/metrics")
def get_metrics(
    service: CacheService = Depends(get_cache_service)
):
    """
    Get cache metrics.

    Includes:
    - Hit/miss rates
    - Entry counts by tier
    - Temporal mismatch rates
    - Integrity metrics
    """
    return service.get_metrics()


# ──────────────────────────────────────────────
# HEALTH
# ──────────────────────────────────────────────

@router.get("/health")
def health_check(
    service: CacheService = Depends(get_cache_service)
):
    """Health check endpoint"""
    return service.health()


# ──────────────────────────────────────────────
# EVENTS (for NOIR Dashboard)
# ──────────────────────────────────────────────

@router.get("/events")
def get_events(
    limit: int = 20,
    service: CacheService = Depends(get_cache_service)
):
    """
    Get recent cache events for dashboard.

    Returns promotion, hit, miss, and failure events.
    """
    return service.get_events(limit=limit)
