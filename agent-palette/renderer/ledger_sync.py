import json, hashlib, threading, time, urllib.request, urllib.error, uuid
from datetime import datetime, timezone

LEDGER_URL = "http://localhost:8101/api/receipts"

# Tier → Governance Level mapping
TIER_TO_LEVEL = {"FREE": "LOW", "MED": "MED", "HIGH": "HIGH", "ANON": "LOW"}

# Palette doc_type → Ledger doc_type (valid: doc, xlsx, pptx, jmpg, communique, compliance_passport)
DOC_TYPE_MAP = {
    "memo": "doc", "letter": "doc", "note": "doc", "email": "doc",
    "report": "doc", "contract": "doc", "invoice": "doc", "protocol": "doc",
    "analysis": "doc", "presentation": "pptx", "security_advisory": "doc",
    "governance_decision": "doc", "certificate": "doc", "document": "doc",
    "rechnung": "doc", "brief": "doc", "vertrag": "doc", "bericht": "doc",
    "xlsx": "xlsx", "pptx": "pptx", "jmpg": "jmpg", "communique": "communique",
}
MAX_RETRIES = 3
RETRY_DELAYS = [30, 60, 120]

class LedgerSync:
    """Async non-blocking Ledger sync with retry."""

    def __init__(self):
        self._pending = []
        self._stats = {"success": 0, "pending": 0, "failed": 0}

    def sync_render(self, result, spec, tier="FREE", account_id="anonymous",
                    content_hash=None, receipt_id=None, governance_level=None, serial=None):
        """Fire-and-forget sync to Ledger. Never blocks download.

        Args:
            result: Render result dict
            spec: Request spec dict
            tier: User tier (FREE/MED/HIGH)
            account_id: User account ID
            content_hash: Pre-computed SHA-256 hash (from N2, ensures same hash in footer and Ledger)
            receipt_id: Pre-generated receipt ID (from N2, ensures same ID in footer and Ledger)
            governance_level: Pre-computed governance level (from N2)
            serial: WINDI serial number from N3 (e.g., WINDI-2026-0001)
        """
        receipt = self._build_receipt(result, spec, tier, account_id,
                                      content_hash, receipt_id, governance_level, serial)
        thread = threading.Thread(target=self._sync_with_retry, args=(receipt,), daemon=True)
        thread.start()
        return {"status": "PENDING", "receipt_preview": receipt["content_hash"][:16]}

    def _build_receipt(self, result, spec, tier, account_id,
                        pre_hash=None, pre_receipt_id=None, pre_gov_level=None, serial=None):
        """Build Ledger-compliant Virtue Receipt with all required fields.

        Args:
            result: Render result dict
            spec: Request spec dict
            tier: User tier
            account_id: User account ID
            pre_hash: Pre-computed content hash (from N2 seal injection)
            pre_receipt_id: Pre-generated receipt ID (from N2)
            pre_gov_level: Pre-computed governance level (from N2)
            serial: WINDI serial number from N3 (e.g., WINDI-2026-0001)
        """
        spec_str = json.dumps(spec, sort_keys=True, ensure_ascii=False) if isinstance(spec, dict) else str(spec)
        spec_hash = hashlib.sha256(spec_str.encode()).hexdigest()

        # Extract doc info from spec/intent
        intent = spec.get("intent", {}) if isinstance(spec, dict) else {}
        doc_type = intent.get("doc_type", spec.get("doc_type", "document")) if isinstance(spec, dict) else "document"
        doc_name = result.get("filename", f"WINDI_{doc_type}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}")

        # Use pre-computed governance level or derive from tier
        governance_level = pre_gov_level if pre_gov_level else TIER_TO_LEVEL.get(tier, "LOW")

        # Extract SGE score (check multiple locations)
        sge_score = 0.0
        if isinstance(spec, dict):
            sge = spec.get("sge", {})
            sge_score = sge.get("score", sge.get("sge_score", spec.get("sge_score", 0.0)))

        # Use pre-generated receipt ID or generate new one
        receipt_id = pre_receipt_id if pre_receipt_id else f"VR-PAL-{uuid.uuid4().hex[:12]}"

        # Build tags list with optional serial tag
        tags = ["palette-render", f"tier-{tier.lower()}", f"format-{result.get('format', 'unknown')}"]
        if serial:
            tags.append(f"serial-{serial}")

        receipt = {
            # Required fields for Ledger
            "id": receipt_id,
            "actor": "agent-palette",
            "app": "agent-palette",
            "doc_name": doc_name,
            "doc_type": DOC_TYPE_MAP.get(doc_type.lower(), "doc"),
            # Use pre-computed hash from N2 (ensures footer hash = ledger hash)
            "content_hash": pre_hash if pre_hash else result.get("content_hash", ""),
            "governance_level": governance_level,
            "sge_score": float(sge_score),
            # Optional but useful
            "bundle_hash": result.get("bundle_hash", ""),
            "tags": tags,
            "metadata": {
                "spec_hash": spec_hash,
                "format": result.get("format", "unknown"),
                "renderer_version": "1.0.0",
                "template_id": intent.get("template_id", "default"),
                "tier": tier,
                "account_id": account_id,
                "file_size_bytes": result.get("size_bytes", 0),
                "render_ms": result.get("render_ms", 0),
                "filename": result.get("filename", ""),
                "language": intent.get("language", "de"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

        # N3: Add serial field if provided
        if serial:
            receipt["serial"] = serial

        return receipt

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
                        "failed_at": datetime.now(timezone.utc).isoformat()
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
