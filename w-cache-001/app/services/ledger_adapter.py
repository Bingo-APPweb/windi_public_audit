# ═══════════════════════════════════════════════
# W-CACHE-001 · LEDGER ADAPTER
# Integration with WINDI Forensic Ledger :8101
# ═══════════════════════════════════════════════

import requests
from typing import Optional, Dict, Any
from datetime import datetime

from core.config import LEDGER_URL
from db.models import CacheEntryModel


class LedgerAdapter:
    """
    Adapter for WINDI Forensic Ledger integration.

    Used for:
    - Anchoring cache provenance (L3 promotion)
    - Linking cache entries to receipts
    """

    def __init__(self, base_url: str = LEDGER_URL):
        self.base_url = base_url

    def anchor_cache_provenance(
        self,
        entry: CacheEntryModel,
        actor_did: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Anchor cache entry provenance to ledger.

        Creates a CACHE_PROVENANCE receipt linking:
        - cache_id
        - namespace
        - content_hash
        - timeline info

        Returns receipt data from ledger.
        """
        payload = {
            "actor": actor_did or entry.actor_did or "system",
            "app": "W-CACHE-001",
            "doc_name": f"cache-provenance:{entry.namespace}",
            "doc_type": "CACHE_PROVENANCE",
            "content_hash": entry.content_hash or entry.state_hash,
            "governance_level": "HIGH" if entry.sensitivity == "CRITICAL" else "MEDIUM",
            "metadata": {
                "cache_id": entry.id,
                "namespace": entry.namespace,
                "tier": entry.tier,
                "timeline_id": entry.timeline_id,
                "state_version": entry.state_version,
                "anchored_at": datetime.utcnow().isoformat()
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/receipts",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            # Return error structure - don't fail silently (I14)
            return {
                "ok": False,
                "error": str(e),
                "receipt_id": None
            }

    def anchor_cache_promotion(
        self,
        entry: CacheEntryModel,
        actor_did: Optional[str],
        receipt_id: Optional[str],
        content_hash: str,
        promotion_reason: str
    ) -> Dict[str, Any]:
        """
        Anchor cache promotion to ledger.

        Creates a CACHE_PROVENANCE receipt for L3 promotion.
        Returns ledger_id and verify_url on success.
        """
        try:
            # Generate receipt ID in WINDI format
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            hash_suffix = content_hash[-8:].upper() if content_hash else "00000000"
            receipt_id_gen = f"WINDI-WCACHE-{timestamp}-{hash_suffix}"

            payload = {
                "id": receipt_id_gen,
                "actor": actor_did or getattr(entry, "actor_did", None) or "did:windi:w-cache-001",
                "app": "W-CACHE-001",
                "doc_name": f"cache-promotion:{entry.namespace}",
                "doc_type": "doc",  # Ledger accepts: doc, communique, jmpg, pptx, web, slides
                "content_hash": content_hash,
                "governance_level": "HIGH",
                "sge_score": 0.98,
                "metadata": {
                    "cache_id": entry.id,
                    "namespace": entry.namespace,
                    "from_tier": entry.tier,
                    "to_tier": "L3_PROVEN",
                    "promotion_reason": promotion_reason,
                    "timeline_id": entry.timeline_id,
                    "state_version": entry.state_version,
                    "anchored_at": datetime.utcnow().isoformat()
                }
            }

            response = requests.post(
                f"{self.base_url}/api/receipts",
                json=payload,
                timeout=8
            )
            response.raise_for_status()
            data = response.json()

            ledger_id = data.get("id") or data.get("ledger_id") or data.get("receipt_id")
            return {
                "ok": True,
                "ledger_id": ledger_id,
                "verify_url": f"https://windi-domain.com/verify/{ledger_id}"
            }

        except Exception as e:
            return {
                "ok": False,
                "error": str(e)
            }

    def verify_receipt(self, receipt_id: str) -> Dict[str, Any]:
        """Verify a receipt exists and is valid"""
        try:
            response = requests.get(
                f"{self.base_url}/api/receipts/{receipt_id}",
                timeout=5
            )
            if response.status_code == 200:
                return {"ok": True, "receipt": response.json()}
            return {"ok": False, "error": "NOT_FOUND"}
        except requests.RequestException as e:
            return {"ok": False, "error": str(e)}

    def health_check(self) -> bool:
        """Check if ledger is available"""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=3
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
