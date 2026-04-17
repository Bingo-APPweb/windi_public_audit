# ═══════════════════════════════════════════════════════════════════════════
#  vera_cache.py — W-CACHE-001 Integration for VERA
#  §189 — Cache Layer for AI Compliance Secretary
#  Port: :8160 (W-CACHE-001) ↔ :8150 (W-ENTERPRISE-001)
#  Liga IA+H · Human Dragon · 17 Abril 2026
#
#  CACHE TIERS:
#    L1_EPHEMERAL    — <60s, volatile (not used by VERA)
#    L2_DETERMINISTIC — 1-24h, same input = same output
#    L3_PROVEN       — Linked to Ledger receipt, immutable until PHO
#
#  VERA CACHE POLICY:
#    /constitution → L3_PROVEN (static, PHO-sealed)
#    /brief        → L2_DETERMINISTIC (1h TTL, daily invalidation)
#    /chat Q&A     → L2_DETERMINISTIC (24h TTL, general questions only)
#    /seal-opinion → NEVER CACHE (unique decisions, direct to Ledger)
# ═══════════════════════════════════════════════════════════════════════════

import httpx
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any

# ─── CACHE CONFIG ─────────────────────────────────────────────────────────────
CACHE_BASE_URL = "http://127.0.0.1:8160/api/cache/v1"
CACHE_NAMESPACE = "vera"
CACHE_TIMEOUT = 5.0  # 5s timeout for cache calls

# Timeline tracking for temporal consistency
VERA_TIMELINE_ID = "vera-enterprise-001"
VERA_STATE_VERSION = 1  # Increment on constitution changes

# ─── HELPER FUNCTIONS ─────────────────────────────────────────────────────────

def _hash_content(content: Any) -> str:
    """Generate SHA-256 hash of content for cache key and integrity."""
    if isinstance(content, dict):
        content = json.dumps(content, sort_keys=True)
    return hashlib.sha256(str(content).encode()).hexdigest()[:16]


def _make_cache_key(endpoint: str, params: Dict[str, Any]) -> str:
    """Generate deterministic cache key from endpoint and params."""
    param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return f"{endpoint}:{_hash_content(param_str)}"


async def _cache_get(key: str) -> Optional[Dict]:
    """
    Try to get cached response.
    Returns None on miss or error (fail-open pattern).
    """
    try:
        async with httpx.AsyncClient(timeout=CACHE_TIMEOUT) as client:
            response = await client.post(
                f"{CACHE_BASE_URL}/get",
                json={
                    "namespace": CACHE_NAMESPACE,
                    "key": key,
                    "timeline_id": VERA_TIMELINE_ID,
                    "state_version": VERA_STATE_VERSION
                }
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("hit") and data.get("status") == "FRESH":
                    return data.get("value")
    except Exception:
        pass  # Fail-open: cache miss → compute fresh
    return None


async def _cache_put(
    key: str,
    value: Dict,
    tier: str = "L2_DETERMINISTIC",
    ttl_seconds: int = 3600,
    scope: str = "GLOBAL"
) -> bool:
    """
    Store response in cache.
    Returns True on success, False on error (non-blocking).
    """
    try:
        state_hash = _hash_content(value)
        async with httpx.AsyncClient(timeout=CACHE_TIMEOUT) as client:
            response = await client.post(
                f"{CACHE_BASE_URL}/entries",
                json={
                    "namespace": CACHE_NAMESPACE,
                    "key": key,
                    "value": value,
                    "tier": tier,
                    "scope": scope,
                    "ttl_seconds": ttl_seconds,
                    "sensitivity": "LOW",
                    "timeline_id": VERA_TIMELINE_ID,
                    "state_version": VERA_STATE_VERSION,
                    "state_hash": state_hash
                }
            )
            return response.status_code == 200
    except Exception:
        return False


async def _cache_invalidate(key_pattern: str) -> bool:
    """Invalidate cache entries matching pattern."""
    try:
        async with httpx.AsyncClient(timeout=CACHE_TIMEOUT) as client:
            response = await client.post(
                f"{CACHE_BASE_URL}/invalidate",
                json={
                    "namespace": CACHE_NAMESPACE,
                    "key_pattern": key_pattern,
                    "reason": "manual_invalidation"
                }
            )
            return response.status_code == 200
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════════════════
# PUBLIC API — Cache-Aware VERA Functions
# ═══════════════════════════════════════════════════════════════════════════

async def get_cached_constitution() -> Optional[Dict]:
    """
    Get constitution from L3 cache.
    Constitution is static — only invalidated on PHO seal (Pilar XX).
    """
    cache_key = "constitution:v1.1"
    return await _cache_get(cache_key)


async def cache_constitution(constitution: Dict) -> bool:
    """
    Cache constitution at L3_PROVEN tier.
    TTL: 30 days (effectively permanent until PHO invalidation).
    """
    cache_key = "constitution:v1.1"
    return await _cache_put(
        key=cache_key,
        value=constitution,
        tier="L3_PROVEN",
        ttl_seconds=30 * 24 * 3600,  # 30 days
        scope="GLOBAL"
    )


async def get_cached_brief(language: str) -> Optional[Dict]:
    """
    Get daily brief from L2 cache.
    Cache key includes language and date for daily invalidation.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cache_key = f"brief:{language}:{today}"
    return await _cache_get(cache_key)


async def cache_brief(language: str, brief: Dict) -> bool:
    """
    Cache daily brief at L2 tier.
    TTL: 1 hour (but key includes date, so auto-invalidates next day).
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cache_key = f"brief:{language}:{today}"
    return await _cache_put(
        key=cache_key,
        value=brief,
        tier="L2_DETERMINISTIC",
        ttl_seconds=3600,  # 1 hour
        scope="GLOBAL"
    )


# ─── Q&A CACHE (GENERAL QUESTIONS ONLY) ───────────────────────────────────────

# Questions safe to cache (general compliance knowledge)
CACHEABLE_PATTERNS = [
    "what is eu ai act",
    "what is gdpr",
    "what is dora",
    "what is nis2",
    "what is ovs",
    "what is pho",
    "what is w-enterprise",
    "o que é",
    "was ist",
    "explain",
    "erkläre",
    "explica"
]

# Questions NEVER cacheable (context-specific)
UNCACHEABLE_PATTERNS = [
    "my",
    "our",
    "meu",
    "minha",
    "nosso",
    "nossa",
    "mein",
    "meine",
    "unser",
    "unsere",
    "decision",
    "seal",
    "approve",
    "sign"
]


def is_cacheable_question(question: str) -> bool:
    """
    Determine if a question can be cached.
    Only general knowledge Q&A is cacheable.
    Context-specific or DID-bound queries are NEVER cached.
    """
    q_lower = question.lower()

    # Check for uncacheable patterns first
    if any(p in q_lower for p in UNCACHEABLE_PATTERNS):
        return False

    # Check for cacheable patterns
    return any(p in q_lower for p in CACHEABLE_PATTERNS)


def normalize_question(question: str) -> str:
    """Normalize question for cache key generation."""
    import re
    # Remove punctuation, lowercase, strip whitespace
    normalized = re.sub(r'[^\w\s]', '', question.lower().strip())
    # Remove extra whitespace
    normalized = ' '.join(normalized.split())
    return normalized


async def get_cached_qa(question: str, language: str) -> Optional[Dict]:
    """
    Get cached Q&A response for general questions.
    Returns None for context-specific queries (never cached).
    """
    if not is_cacheable_question(question):
        return None

    normalized = normalize_question(question)
    cache_key = f"qa:{language}:{_hash_content(normalized)}"
    return await _cache_get(cache_key)


async def cache_qa(question: str, language: str, response: Dict) -> bool:
    """
    Cache Q&A response at L2 tier.
    Only caches if question passes cacheability check.
    TTL: 24 hours.
    """
    if not is_cacheable_question(question):
        return False

    normalized = normalize_question(question)
    cache_key = f"qa:{language}:{_hash_content(normalized)}"
    return await _cache_put(
        key=cache_key,
        value=response,
        tier="L2_DETERMINISTIC",
        ttl_seconds=24 * 3600,  # 24 hours
        scope="GLOBAL"
    )


# ─── CACHE METRICS ────────────────────────────────────────────────────────────

async def get_vera_cache_metrics() -> Dict:
    """Get VERA-specific cache metrics from W-CACHE-001."""
    try:
        async with httpx.AsyncClient(timeout=CACHE_TIMEOUT) as client:
            response = await client.get(f"{CACHE_BASE_URL}/metrics")
            if response.status_code == 200:
                metrics = response.json()
                # Filter for VERA namespace
                return {
                    "namespace": CACHE_NAMESPACE,
                    "status": "connected",
                    "metrics": metrics
                }
    except Exception as e:
        return {
            "namespace": CACHE_NAMESPACE,
            "status": "disconnected",
            "error": str(e)
        }


# ─── INVALIDATION TRIGGERS ────────────────────────────────────────────────────

async def invalidate_constitution_cache():
    """
    Invalidate constitution cache.
    Called when Pilar XX (Constitutional Update) PHO is sealed.
    """
    return await _cache_invalidate("constitution:*")


async def invalidate_brief_cache(language: Optional[str] = None):
    """
    Invalidate brief cache.
    Called at start of new day or when desk state changes significantly.
    """
    if language:
        return await _cache_invalidate(f"brief:{language}:*")
    return await _cache_invalidate("brief:*")


async def invalidate_qa_cache():
    """
    Invalidate all Q&A cache.
    Called when REGO constitution is updated or regulatory changes occur.
    """
    return await _cache_invalidate("qa:*")
