"""
W-MAIL-DACP-MILTER — Ledger Client
Spec: §227 Section 9
Invariants: I11 (Permanence), I14 (Explicit Failure)
"""

import os
import logging
import requests
from datetime import datetime
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# Default to public nginx proxy (container can't reach localhost:8101)
LEDGER_URL = os.environ.get('LEDGER_URL', 'https://windi-domain.com')
LEDGER_TIMEOUT = int(os.environ.get('LEDGER_TIMEOUT', '10'))
MILTER_VERSION = "1.0.0"


class LedgerError(Exception):
    """Raised when Ledger seal fails (triggers I14 tempfail)"""
    pass


class LedgerClient:
    """Client for sealing proofs to the Forensic Ledger"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or LEDGER_URL
        # nginx proxy already routes /api/receipts to Ledger
        self.endpoint = f"{self.base_url}/api/receipts/"

    def health_check(self) -> bool:
        """Check if Ledger is reachable via /api/receipts endpoint"""
        try:
            # Use /api/receipts/ instead of /health (nginx proxy doesn't expose /health)
            resp = requests.get(
                f"{self.base_url}/api/receipts/",
                timeout=5
            )
            return resp.status_code in (200, 201)
        except Exception as e:
            logger.warning(f"Ledger health check failed: {e}")
            return False

    def seal(
        self,
        proof_id: str,
        from_hash: str,
        to_hashes: List[str],
        subject_hash: str,
        body_hash: str,
        dkim_selector: str,
        domain: str,
        actor: str
    ) -> Dict[str, Any]:
        """
        Seal a DACP proof to the Forensic Ledger.

        Spec: §227 Section 9
        I14: Raises LedgerError on failure (never silent passthrough)
        """
        sealed_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        payload = {
            "id": proof_id,
            "doc_name": f"DACP Email Proof - {proof_id}",
            "doc_type": "doc",  # Email proofs are generic documents
            "app": "w-mail-001-dacp",
            "actor": actor,
            "governance_level": "LOW",
            "sge_score": 10,
            "content_hash": f"sha256:{body_hash}",
            "invariants": ["I9", "I11", "I14"],
            "stage": "C6",
            "human_approved": True,
            "metadata": {
                "schema": "windi-mail-dacp-v1",
                "from_hash": from_hash,
                "to_hashes": to_hashes,
                "subject_hash": subject_hash,
                "dkim_selector": dkim_selector,
                "domain": domain,
                "sealed_at": sealed_at,
                "milter_version": MILTER_VERSION
            }
        }

        try:
            resp = requests.post(
                self.endpoint,
                json=payload,
                timeout=LEDGER_TIMEOUT
            )

            if resp.status_code not in (200, 201):
                logger.error(f"Ledger seal failed: {resp.status_code} - {resp.text}")
                raise LedgerError(f"Ledger returned {resp.status_code}: {resp.text}")

            result = resp.json()
            if not result.get('ok'):
                error = result.get('error', 'Unknown error')
                logger.error(f"Ledger seal rejected: {error}")
                raise LedgerError(f"Ledger rejected seal: {error}")

            logger.info(f"Sealed proof {proof_id} to Ledger")
            return result

        except requests.exceptions.Timeout:
            logger.error("Ledger seal timeout")
            raise LedgerError("Ledger timeout - I14 tempfail")

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Ledger connection error: {e}")
            raise LedgerError(f"Ledger unreachable - I14 tempfail: {e}")

        except Exception as e:
            logger.error(f"Ledger seal error: {e}")
            raise LedgerError(f"Ledger error - I14 tempfail: {e}")


# Singleton instance
_client: Optional[LedgerClient] = None


def get_client() -> LedgerClient:
    """Get or create Ledger client singleton"""
    global _client
    if _client is None:
        _client = LedgerClient()
    return _client


def seal_proof(
    proof_id: str,
    from_hash: str,
    to_hashes: List[str],
    subject_hash: str,
    body_hash: str,
    dkim_selector: str,
    domain: str,
    actor: str
) -> Dict[str, Any]:
    """Convenience function for sealing proofs"""
    return get_client().seal(
        proof_id=proof_id,
        from_hash=from_hash,
        to_hashes=to_hashes,
        subject_hash=subject_hash,
        body_hash=body_hash,
        dkim_selector=dkim_selector,
        domain=domain,
        actor=actor
    )


def is_ledger_reachable() -> bool:
    """Check if Ledger is reachable"""
    return get_client().health_check()
