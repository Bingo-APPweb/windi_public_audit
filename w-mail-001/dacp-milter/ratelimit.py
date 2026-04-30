"""
W-MAIL-DACP-MILTER — Rate Limiter
Spec: §227 Section 8 (Edge case #9)
"""

import os
import time
from threading import Lock
from typing import Dict, Tuple


class TokenBucket:
    """Token bucket rate limiter per from_hash"""

    def __init__(self, rate: int = 100, period: int = 60):
        """
        Args:
            rate: Maximum tokens (emails) per period
            period: Period in seconds
        """
        self.rate = rate
        self.period = period
        self._lock = Lock()
        self._buckets: Dict[str, Tuple[float, float]] = {}  # from_hash -> (tokens, last_update)

    def _cleanup_old_buckets(self) -> None:
        """Remove buckets that haven't been used in 2 periods"""
        now = time.time()
        cutoff = now - (self.period * 2)
        old_keys = [k for k, (_, t) in self._buckets.items() if t < cutoff]
        for k in old_keys:
            del self._buckets[k]

    def allow(self, from_hash: str) -> bool:
        """
        Check if request is allowed under rate limit.

        Returns:
            True if allowed, False if rate limited
        """
        with self._lock:
            now = time.time()

            # Periodic cleanup
            if len(self._buckets) > 10000:
                self._cleanup_old_buckets()

            if from_hash not in self._buckets:
                # New sender, start with full bucket minus 1
                self._buckets[from_hash] = (self.rate - 1, now)
                return True

            tokens, last_update = self._buckets[from_hash]

            # Refill tokens based on elapsed time
            elapsed = now - last_update
            refill = elapsed * (self.rate / self.period)
            tokens = min(self.rate, tokens + refill)

            if tokens >= 1:
                # Allow and consume a token
                self._buckets[from_hash] = (tokens - 1, now)
                return True
            else:
                # Rate limited
                self._buckets[from_hash] = (tokens, now)
                return False

    def get_stats(self) -> Dict[str, int]:
        """Get rate limiter statistics"""
        with self._lock:
            return {
                'active_buckets': len(self._buckets),
                'rate_per_min': self.rate,
            }


# Singleton instance
_limiter: TokenBucket = None


def get_limiter() -> TokenBucket:
    """Get or create rate limiter singleton"""
    global _limiter
    if _limiter is None:
        rate = int(os.environ.get('RATE_LIMIT_PER_MIN', '100'))
        _limiter = TokenBucket(rate=rate, period=60)
    return _limiter


def is_allowed(from_hash: str) -> bool:
    """Check if request is allowed"""
    return get_limiter().allow(from_hash)
