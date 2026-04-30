"""
W-MAIL-DACP-MILTER — Metrics Module
Spec: §227 Section 13
"""

import time
from threading import Lock
from typing import Dict


class Metrics:
    """Thread-safe metrics counters for DACP milter"""

    def __init__(self):
        self._lock = Lock()
        self._start_time = time.time()
        self._counters: Dict[str, int] = {
            'sealed_total': 0,
            'bypassed_already_sealed_total': 0,
            'bypassed_encrypted_total': 0,
            'bypassed_dsn_total': 0,
            'bypassed_internal_total': 0,
            'resealed_forwarded_total': 0,
            'tempfail_ledger_total': 0,
            'tempfail_ratelimit_total': 0,
            'errors_total': 0,
        }
        self._processing_times: list = []

    def increment(self, name: str, value: int = 1) -> None:
        """Increment a counter"""
        with self._lock:
            if name in self._counters:
                self._counters[name] += value

    def record_processing_time(self, seconds: float) -> None:
        """Record email processing time"""
        with self._lock:
            self._processing_times.append(seconds)
            # Keep only last 1000 samples
            if len(self._processing_times) > 1000:
                self._processing_times = self._processing_times[-1000:]

    def get_counters(self) -> Dict[str, int]:
        """Get all counters"""
        with self._lock:
            return dict(self._counters)

    def get_uptime(self) -> float:
        """Get uptime in seconds"""
        return time.time() - self._start_time

    def get_processing_histogram(self) -> Dict[str, float]:
        """Get processing time statistics"""
        with self._lock:
            if not self._processing_times:
                return {'count': 0, 'avg': 0, 'min': 0, 'max': 0}
            return {
                'count': len(self._processing_times),
                'avg': sum(self._processing_times) / len(self._processing_times),
                'min': min(self._processing_times),
                'max': max(self._processing_times),
            }

    def to_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        with self._lock:
            for name, value in self._counters.items():
                lines.append(f"windi_dacp_{name} {value}")

            # Processing histogram summary
            if self._processing_times:
                lines.append(f"windi_dacp_processing_seconds_count {len(self._processing_times)}")
                lines.append(f"windi_dacp_processing_seconds_sum {sum(self._processing_times):.6f}")

        lines.append(f"windi_dacp_uptime_seconds {self.get_uptime():.0f}")
        return '\n'.join(lines) + '\n'


# Singleton instance
_metrics: Metrics = None


def get_metrics() -> Metrics:
    """Get or create metrics singleton"""
    global _metrics
    if _metrics is None:
        _metrics = Metrics()
    return _metrics


# Convenience functions
def increment(name: str, value: int = 1) -> None:
    get_metrics().increment(name, value)


def record_processing_time(seconds: float) -> None:
    get_metrics().record_processing_time(seconds)
