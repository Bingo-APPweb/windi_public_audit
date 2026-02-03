"""
WINDI DeepDOCFakes — Verify Engine
=====================================
Document provenance verification.

Returns one of three statuses:
    VALID    — Record found, structural hash matches, provenance chain intact
    UNKNOWN  — Record not found in WINDI registry
    TAMPERED — Record found but hash mismatch detected

Verification checks:
    1. Record exists in provenance index
    2. Structural hash matches recomputed hash
    3. Hash chain is consistent
    4. System identity matches known WINDI installations
    5. Governance context is complete and valid
"""

import os
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from .structural_hash import compute_structural_hash

PROV_DIR = os.environ.get("WINDI_PROVENANCE_DIR", "/opt/windi/provenance")
RECORDS_DIR = os.path.join(PROV_DIR, "records")
INDEX_FILE = os.path.join(PROV_DIR, "index.json")

# Known WINDI installations (for system identity verification)
KNOWN_SYSTEMS = [
    "WINDI Publishing House"
]


class VerificationStatus(str, Enum):
    VALID = "VALID"
    UNKNOWN = "UNKNOWN"
    TAMPERED = "TAMPERED"


def _load_index() -> Dict[str, Any]:
    if not os.path.exists(INDEX_FILE):
        return {}
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {}


def _load_record(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_by_submission_id(
    submission_id: str,
    decision_payload: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Verify a document's provenance by submission ID.
    
    If decision_payload is provided, recomputes the structural hash
    and compares it to the stored hash (full verification).
    
    If decision_payload is None, only checks registry presence
    and record integrity (partial verification).
    
    Args:
        submission_id: The document's submission/provenance ID
        decision_payload: The governance decision payload to verify against
    
    Returns:
        Verification result with status, checks, and details
    """
    result = {
        "submission_id": submission_id,
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "protocol": "WINDI-SOF-v1",
        "checks": {}
    }
    
    # Check 1: Index lookup
    idx = _load_index()
    entry = idx.get(submission_id)
    
    if not entry:
        result["status"] = VerificationStatus.UNKNOWN
        result["reason"] = "submission_id_not_found_in_index"
        result["checks"]["registry_match"] = False
        return result
    
    result["checks"]["registry_match"] = True
    
    # Check 2: Record file exists
    record_path = entry.get("record_path")
    if not record_path:
        result["status"] = VerificationStatus.UNKNOWN
        result["reason"] = "record_path_missing_in_index"
        result["checks"]["record_exists"] = False
        return result
    
    record = _load_record(record_path)
    if not record:
        result["status"] = VerificationStatus.UNKNOWN
        result["reason"] = "record_file_missing"
        result["checks"]["record_exists"] = False
        return result
    
    result["checks"]["record_exists"] = True
    
    # Check 3: System identity
    system = record.get("system_identity", {}).get("system", "")
    result["checks"]["system_identity"] = system in KNOWN_SYSTEMS
    
    # Check 4: Governance context completeness
    gov = record.get("governance_context", {})
    result["checks"]["governance_level_valid"] = gov.get("level") in ("HIGH", "MEDIUM", "LOW")
    result["checks"]["policy_version_present"] = bool(gov.get("policy_version"))
    
    # Check 5: Hash chain integrity
    crypto = record.get("cryptographic_proof", {})
    stored_structural = crypto.get("structural_hash", "")
    stored_provenance = crypto.get("provenance_hash", "")
    expected_chain = f"{stored_structural[:16]}→{stored_provenance[:16]}"
    result["checks"]["hash_present"] = bool(stored_structural and stored_provenance)
    result["checks"]["hash_chain_valid"] = crypto.get("hash_chain") == expected_chain
    
    # Check 6: Structural hash verification (if payload provided)
    if decision_payload is not None:
        recomputed = compute_structural_hash(decision_payload)
        result["checks"]["structural_hash_match"] = (recomputed == stored_structural)
        
        if recomputed != stored_structural:
            result["status"] = VerificationStatus.TAMPERED
            result["reason"] = "structural_hash_mismatch"
            result["expected_hash"] = stored_structural
            result["computed_hash"] = recomputed
            result["governance_context"] = gov
            return result
    
    # Check 7: Protocol version
    result["checks"]["protocol_valid"] = record.get("_protocol") == "WINDI-SOF-v1"
    
    # All critical checks
    critical = [
        result["checks"].get("registry_match", False),
        result["checks"].get("record_exists", False),
        result["checks"].get("system_identity", False),
        result["checks"].get("hash_present", False),
        result["checks"].get("hash_chain_valid", False),
    ]
    
    # Add structural match if it was tested
    if "structural_hash_match" in result["checks"]:
        critical.append(result["checks"]["structural_hash_match"])
    
    if all(critical):
        result["status"] = VerificationStatus.VALID
        result["reason"] = "all_checks_passed"
    else:
        failed = [k for k, v in result["checks"].items() if v is False]
        result["status"] = VerificationStatus.TAMPERED
        result["reason"] = f"checks_failed: {', '.join(failed)}"
    
    # Include governance context and resilience in result
    result["governance_context"] = gov
    result["deepfake_resilience"] = record.get("deepfake_resilience", {})
    
    passed = sum(1 for v in result["checks"].values() if v is True)
    total = len(result["checks"])
    result["checks_summary"] = f"{passed}/{total} passed"
    
    return result


def verify_by_hash(provenance_hash_prefix: str) -> Dict[str, Any]:
    """
    Verify by provenance hash prefix (first 32 chars).
    Useful when only the hash is available (e.g., from PDF metadata).
    """
    idx = _load_index()
    
    for submission_id, entry in idx.items():
        stored_hash = entry.get("structural_hash", "")
        if stored_hash.startswith(provenance_hash_prefix):
            return verify_by_submission_id(submission_id)
    
    return {
        "status": VerificationStatus.UNKNOWN,
        "reason": f"no_record_matching_hash_prefix: {provenance_hash_prefix[:16]}...",
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "protocol": "WINDI-SOF-v1"
    }
