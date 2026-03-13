import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional
import httpx

log = logging.getLogger("windi.verify.engine")

# ═══════════════════════════════════════════════════════════════════════════════
# JMPG Proof Extractor — Compatible with IrmaEncoder APP1 format
# ═══════════════════════════════════════════════════════════════════════════════

WINDI_SIGNATURE = "WINDI-SOVEREIGN-PROOF"

def extract_jmpg_proof(content: bytes) -> Optional[dict]:
    """
    Extract WINDI proof from .jmpg file (APP1 segment after SOI).
    Compatible with IrmaEncoder.injectProof() format.

    Returns proof dict if valid WINDI .jmpg, None otherwise.
    """
    if len(content) < 10:
        return None

    # Check JPEG magic bytes (SOI)
    if content[0] != 0xFF or content[1] != 0xD8:
        return None

    # Check for APP1 marker right after SOI
    if content[2] != 0xFF or content[3] != 0xE1:
        return None

    # Read APP1 segment length (big-endian)
    length = (content[4] << 8) | content[5]

    # Extract data (length includes the 2 length bytes)
    data_start = 6
    data_end = 6 + length - 2

    if data_end > len(content):
        return None

    try:
        proof_string = content[data_start:data_end].decode('utf-8')
        proof = json.loads(proof_string)

        # Validate WINDI signature
        if proof.get('windi_proof') == WINDI_SIGNATURE:
            log.info(f"[JMPG] Valid proof extracted: anchor={proof.get('ledger_anchor')}")
            return proof
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        log.debug(f"[JMPG] Not a WINDI .jmpg: {e}")

    return None


def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

class VerifyEngine:
    def __init__(self, ledger_url, agents_url, timeout=5.0):
        self.ledger_url = ledger_url.rstrip("/")
        self.agents_url = agents_url.rstrip("/")
        self.timeout = httpx.Timeout(timeout)

    async def verify_qr(self, qr_data):
        checked_at = now_iso()
        receipt_id, qr_hash = None, None
        try:
            if qr_data.startswith("WINDI:") and "|" in qr_data:
                parts = qr_data[6:].split("|", 1)
                receipt_id = parts[0]
                qr_hash = parts[1] if len(parts) > 1 else None
        except Exception:
            pass
        if qr_hash:
            ledger_ok = await self._check_ledger(qr_hash)
        elif receipt_id:
            meta = await self._resolve_document(receipt_id)
            qr_hash = meta.get("hash") if meta else None
            ledger_ok = await self._check_ledger(qr_hash) if qr_hash else False
        else:
            return self._error(None, checked_at, "Invalid QR format.")
        status = "verified" if ledger_ok else "not_found"
        return {"status":status,"document_id":receipt_id,"hash":qr_hash,"integrity":"valid" if ledger_ok else "unknown","signature":"unknown","ledger_anchor":ledger_ok,"timestamp":None,"checked_at":checked_at,"message":self._status_message(status),"cached":False}

    async def verify_document_id(self, document_id):
        checked_at = now_iso()
        meta = await self._resolve_document(document_id)
        if not meta:
            return self._not_found(document_id, checked_at)
        doc_hash = meta.get("hash") or meta.get("sha256") or meta.get("document_hash")
        if not doc_hash:
            return self._error(document_id, checked_at, "Document found but hash missing.")
        # _resolve_document already confirmed existence in Ledger
        # _check_ledger by hash as secondary confirmation (best-effort)
        ledger_ok = await self._check_ledger_by_id(document_id) or await self._check_ledger(doc_hash)
        status = "verified" if ledger_ok else "not_found"
        return {"status":status,"document_id":document_id,"hash":doc_hash,"integrity":"valid" if ledger_ok else "unknown","signature":"unknown","ledger_anchor":ledger_ok,"timestamp":meta.get("created_at") or meta.get("timestamp"),"checked_at":checked_at,"message":self._status_message(status),"cached":False}

    async def verify_hash(self, sha256_hash):
        checked_at = now_iso()
        ledger_ok = await self._check_ledger(sha256_hash)
        meta = await self._ledger_hash_meta(sha256_hash) if ledger_ok else None
        status = "verified" if ledger_ok else "not_found"
        return {"status":status,"document_id":meta.get("document_id") if meta else None,"hash":sha256_hash,"integrity":"valid" if ledger_ok else "unknown","signature":"unknown","ledger_anchor":ledger_ok,"timestamp":meta.get("created_at") if meta else None,"checked_at":checked_at,"message":self._status_message(status),"cached":False}

    async def get_timeline(self, document_id):
        checked_at = now_iso()
        meta = await self._resolve_document(document_id)
        events = []
        if meta:
            for event, key in [("creation","created_at"),("signature","signed_at"),("ledger_anchor","ledger_at")]:
                if meta.get(key):
                    events.append({"event":event,"timestamp":meta[key]})
        return {"document_id":document_id,"timeline":events,"checked_at":checked_at}

    async def _check_ledger_by_id(self, document_id):
        """Check ledger by receipt_id directly — fastest path."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.get(f"{self.ledger_url}/api/verify/{document_id}")
                if r.status_code == 200:
                    d = r.json()
                    if d.get("ok") or d.get("status") in ("verified","sealed"):
                        return True
        except Exception:
            pass
        return False

    async def _resolve_document(self, document_id):
        urls = [f"{self.ledger_url}/api/receipts/{document_id}",f"{self.ledger_url}/api/verify/{document_id}",f"{self.agents_url}/document/{document_id}"]
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for url in urls:
                try:
                    r = await client.get(url)
                    if r.status_code == 200:
                        d = r.json()
                        if d.get("ok") or d.get("status") == "sealed":
                            # /api/receipts/ nests data inside "receipt"
                            rec = d.get("receipt") or d
                            ts = rec.get("created_at") or rec.get("registered_at")
                            return {
                                "hash": rec.get("content_hash"),
                                "sha256": rec.get("content_hash"),
                                "document_id": rec.get("id", document_id),
                                "created_at": datetime.utcfromtimestamp(ts).isoformat()+"Z" if ts else None,
                                "status": rec.get("status"),
                                "governance_level": rec.get("governance_level"),
                                "sge_score": rec.get("sge_score"),
                            }
                        return d
                except Exception:
                    pass
        return None

    async def _check_ledger(self, sha256_hash):
        if not sha256_hash:
            return False
        urls = [f"{self.ledger_url}/api/verify/{sha256_hash}",f"{self.ledger_url}/api/receipts/{sha256_hash}",f"{self.ledger_url}/ledger/hash/{sha256_hash}"]
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for url in urls:
                try:
                    r = await client.get(url)
                    if r.status_code == 200:
                        d = r.json()
                        if d.get("ok") or d.get("found") or d.get("exists") or d.get("verified") or d.get("status") in ("verified","sealed"):
                            return True
                except Exception:
                    pass
        return False

    async def _ledger_hash_meta(self, sha256_hash):
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for url in [f"{self.ledger_url}/api/verify/{sha256_hash}",f"{self.ledger_url}/api/receipts/{sha256_hash}"]:
                try:
                    r = await client.get(url)
                    if r.status_code == 200:
                        return r.json()
                except Exception:
                    pass
        return None

    def _not_found(self, document_id, checked_at):
        return {"status":"not_found","document_id":document_id,"hash":None,"integrity":"unknown","signature":"unknown","ledger_anchor":False,"timestamp":None,"checked_at":checked_at,"message":"Document not found in WINDI system.","cached":False}

    def _error(self, document_id, checked_at, message):
        return {"status":"error","document_id":document_id,"hash":None,"integrity":"unknown","signature":"unknown","ledger_anchor":False,"timestamp":None,"checked_at":checked_at,"message":message,"cached":False}

    def _status_message(self, status):
        return {"verified":"Document authentic. Integrity confirmed by WINDI Forensic Ledger.","not_found":"Document not found in WINDI system.","tampered":"WARNING: Signature invalid. Possible tampering.","error":"Verification could not be completed."}.get(status,"Unknown status.")
