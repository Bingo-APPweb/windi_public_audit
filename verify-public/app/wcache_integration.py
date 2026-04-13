# ═══════════════════════════════════════════════
# W-CACHE-001 INTEGRATION FOR VERIFY-PUBLIC
# Auto-promotion flow: L3 → L2 → Ledger → L2 → L3
# ═══════════════════════════════════════════════

import logging
import requests
from typing import Optional, Dict, Any

log = logging.getLogger("windi.verify.wcache")

WCACHE_URL = "http://127.0.0.1:8160/api/cache/v1"
WCACHE_TIMEOUT = 2  # Fast - cache must be fast


# ═══════════════════════════════════════════════
# CORE OPERATIONS
# ═══════════════════════════════════════════════

def wcache_get(payload: dict) -> Dict[str, Any]:
    """Get from W-CACHE-001"""
    try:
        r = requests.post(f"{WCACHE_URL}/get", json=payload, timeout=WCACHE_TIMEOUT)
        return r.json()
    except Exception as e:
        log.debug(f"[WCACHE] get error (non-blocking): {e}")
        return {"hit": False}


def wcache_put(payload: dict) -> Optional[Dict[str, Any]]:
    """Put to W-CACHE-001"""
    try:
        r = requests.post(f"{WCACHE_URL}/entries", json=payload, timeout=WCACHE_TIMEOUT)
        return r.json()
    except Exception as e:
        log.debug(f"[WCACHE] put error (non-blocking): {e}")
        return None


def wcache_promote(payload: dict) -> Optional[Dict[str, Any]]:
    """Promote L2 → L3 in W-CACHE-001"""
    try:
        r = requests.post(f"{WCACHE_URL}/promote", json=payload, timeout=3)
        return r.json()
    except Exception as e:
        log.debug(f"[WCACHE] promote error (non-blocking): {e}")
        return None


def wcache_health() -> Dict[str, Any]:
    """Check W-CACHE-001 health"""
    try:
        r = requests.get(f"{WCACHE_URL}/health", timeout=1)
        if r.status_code == 200:
            return {"ok": True, "wcache": "healthy"}
        return {"ok": False, "wcache": "unhealthy"}
    except Exception:
        return {"ok": False, "wcache": "unavailable"}


# ═══════════════════════════════════════════════
# VERIFY INTEGRATION
# ═══════════════════════════════════════════════

def verify_with_cache(receipt_id: str, ledger_fetcher) -> Dict[str, Any]:
    """
    Verify receipt with W-CACHE-001 integration.

    Flow:
    1. Try L3_PROVEN (fastest - already verified)
    2. Try L2_DETERMINISTIC (cached but not promoted)
    3. Fallback to ledger
    4. Save to L2
    5. Promote to L3 (referential, no ledger anchor)

    Args:
        receipt_id: The receipt ID to verify
        ledger_fetcher: Function that fetches from ledger: fn(receipt_id) -> dict or None

    Returns:
        Receipt data or error dict
    """
    timeline_id = f"RECEIPT:{receipt_id}"
    state_version = 1

    # ═══ 1. Try L3_PROVEN (fastest path) ═══
    cached = wcache_get({
        "namespace": "verify.receipt",
        "tier": "L3_PROVEN",
        "scope": "RECEIPT",
        "timeline_id": timeline_id,
        "state_version": state_version,
        "input_hash": receipt_id
    })

    if cached.get("hit"):
        log.info(f"[WCACHE] L3 HIT: {receipt_id}")
        result = cached.get("value", {})
        result["_cache"] = "L3_PROVEN"
        return result

    # ═══ 2. Try L2_DETERMINISTIC ═══
    cached = wcache_get({
        "namespace": "verify.receipt",
        "tier": "L2_DETERMINISTIC",
        "scope": "RECEIPT",
        "timeline_id": timeline_id,
        "state_version": state_version,
        "input_hash": receipt_id
    })

    if cached.get("hit"):
        log.info(f"[WCACHE] L2 HIT: {receipt_id}")
        result = cached.get("value", {})
        result["_cache"] = "L2_DETERMINISTIC"
        return result

    # ═══ 3. Fallback → Ledger ═══
    log.info(f"[WCACHE] MISS - fetching from ledger: {receipt_id}")
    receipt = ledger_fetcher(receipt_id)

    if not receipt:
        return None

    # ═══ 4. Save to L2 ═══
    content_hash = receipt.get("content_hash") or f"sha256:{receipt_id}"

    created = wcache_put({
        "namespace": "verify.receipt",
        "tier": "L2_DETERMINISTIC",
        "scope": "RECEIPT",
        "sensitivity": "MEDIUM",
        "input_hash": receipt_id,
        "content_hash": content_hash,
        "timeline": {
            "timeline_id": timeline_id,
            "state_version": state_version,
            "state_hash": content_hash
        },
        "value": receipt
    })

    cache_id = created.get("cache_id") if created else None

    # ═══ 5. Promote to L3 (referential - no ledger anchor) ═══
    if cache_id:
        promo = wcache_promote({
            "cache_id": cache_id,
            "receipt_id": receipt_id,
            "content_hash": content_hash,
            "verify_url": f"https://windi-domain.com/verify/{receipt_id}",
            "anchor_to_ledger": False,
            "promotion_reason": "VERIFY_AUTO_PROMOTION"
        })
        if promo and promo.get("ok"):
            log.info(f"[WCACHE] Auto-promoted to L3: {receipt_id}")

    receipt["_cache"] = "LEDGER_FETCH"
    return receipt


# ═══════════════════════════════════════════════
# LEGACY COMPATIBILITY (drop-in replacement)
# ═══════════════════════════════════════════════

def cache_get(key: str) -> Optional[Dict[str, Any]]:
    """
    Legacy drop-in replacement for simple cache_get().
    Maps old key format to W-CACHE-001.
    """
    if key.startswith("doc:"):
        receipt_id = key[4:]
        cached = wcache_get({
            "namespace": "verify.receipt",
            "tier": "L3_PROVEN",
            "scope": "RECEIPT",
            "timeline_id": f"RECEIPT:{receipt_id}",
            "state_version": 1,
            "input_hash": receipt_id
        })
        if cached.get("hit"):
            return cached.get("value")

        # Try L2
        cached = wcache_get({
            "namespace": "verify.receipt",
            "tier": "L2_DETERMINISTIC",
            "scope": "RECEIPT",
            "timeline_id": f"RECEIPT:{receipt_id}",
            "state_version": 1,
            "input_hash": receipt_id
        })
        if cached.get("hit"):
            return cached.get("value")

    return None


def cache_set(key: str, value: Dict[str, Any], ttl: int = 300) -> None:
    """
    Legacy drop-in replacement for simple cache_set().
    Stores in W-CACHE-001 L2 and auto-promotes to L3.
    """
    if key.startswith("doc:"):
        receipt_id = key[4:]
        content_hash = value.get("content_hash") or f"sha256:{receipt_id}"

        created = wcache_put({
            "namespace": "verify.receipt",
            "tier": "L2_DETERMINISTIC",
            "scope": "RECEIPT",
            "sensitivity": "MEDIUM",
            "input_hash": receipt_id,
            "content_hash": content_hash,
            "ttl_seconds": ttl,
            "timeline": {
                "timeline_id": f"RECEIPT:{receipt_id}",
                "state_version": 1,
                "state_hash": content_hash
            },
            "value": value
        })

        # Auto-promote
        if created and created.get("cache_id"):
            wcache_promote({
                "cache_id": created["cache_id"],
                "receipt_id": receipt_id,
                "content_hash": content_hash,
                "verify_url": f"https://windi-domain.com/verify/{receipt_id}",
                "anchor_to_ledger": False,
                "promotion_reason": "VERIFY_AUTO_PROMOTION"
            })
