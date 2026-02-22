import json, hashlib, threading, time, urllib.request, urllib.error
from datetime import datetime

LEDGER_URL = "http://localhost:8101/api/receipts"
MAX_RETRIES = 3
RETRY_DELAYS = [30, 60, 120]

class LedgerSync:
    """Async non-blocking Ledger sync with retry."""

    def __init__(self):
        self._pending = []
        self._stats = {"success": 0, "pending": 0, "failed": 0}

    def sync_render(self, result, spec, tier="FREE", account_id="anonymous"):
        """Fire-and-forget sync to Ledger. Never blocks download."""
        receipt = self._build_receipt(result, spec, tier, account_id)
        thread = threading.Thread(target=self._sync_with_retry, args=(receipt,), daemon=True)
        thread.start()
        return {"status": "PENDING", "receipt_preview": receipt["content_hash"][:16]}

    def _build_receipt(self, result, spec, tier, account_id):
        spec_str = json.dumps(spec, sort_keys=True, ensure_ascii=False) if isinstance(spec, dict) else str(spec)
        spec_hash = hashlib.sha256(spec_str.encode()).hexdigest()
        return {
            "doc_type": "RENDERED_DOCUMENT",
            "content_hash": result.get("content_hash", ""),
            "spec_hash": spec_hash,
            "bundle_hash": result.get("bundle_hash", ""),
            "metadata": {
                "format": result.get("format", "unknown"),
                "renderer_version": "1.0.0",
                "template_id": spec.get("template_id", "default") if isinstance(spec, dict) else "default",
                "tier": tier,
                "account_id": account_id,
                "file_size_bytes": result.get("size_bytes", 0),
                "render_ms": result.get("render_ms", 0),
                "filename": result.get("filename", ""),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            "governance": {
                "sge_score": spec.get("sge_score", 0.0) if isinstance(spec, dict) else 0.0,
                "risk_level": "R1",
                "validation": "auto"
            }
        }

    def _sync_with_retry(self, receipt):
        self._stats["pending"] += 1
        for attempt in range(MAX_RETRIES):
            try:
                data = json.dumps(receipt).encode()
                req = urllib.request.Request(
                    LEDGER_URL,
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status in (200, 201):
                        self._stats["pending"] -= 1
                        self._stats["success"] += 1
                        return {"status": "SEALED", "attempt": attempt + 1}
            except (urllib.error.URLError, urllib.error.HTTPError, Exception) as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAYS[attempt])
                else:
                    self._stats["pending"] -= 1
                    self._stats["failed"] += 1
                    self._pending.append({
                        "receipt": receipt,
                        "error": str(e),
                        "failed_at": datetime.utcnow().isoformat()
                    })
                    return {"status": "UNSEALED", "error": str(e)}
        return {"status": "UNSEALED"}

    def get_stats(self):
        return {
            "ledger_sync": {
                "success": self._stats["success"],
                "pending": self._stats["pending"],
                "failed": self._stats["failed"],
                "unsent_queue": len(self._pending)
            }
        }

    def retry_pending(self):
        """Retry all failed syncs."""
        retrying = list(self._pending)
        self._pending.clear()
        results = []
        for item in retrying:
            r = self._sync_with_retry(item["receipt"])
            results.append(r)
        return {"retried": len(retrying), "results": results}

_ledger_sync = None
def get_ledger_sync():
    global _ledger_sync
    if _ledger_sync is None:
        _ledger_sync = LedgerSync()
    return _ledger_sync
