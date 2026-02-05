"""
WINDI DeepDOCFakes — Provenance Engine
========================================
Digital birth certificate generation for governed documents.

Each document receives a provenance record proving:
- WHO generated it (system identity)
- UNDER WHAT governance (policy, level, ISP profile)
- WITH WHAT identity controls (license status, disclaimers)
- WHEN and WHERE (timestamp, jurisdiction, server identity)

Storage:
    /opt/windi/provenance/records/{submission_id}.json
    /opt/windi/provenance/index.json
"""

import os
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .structural_hash import compute_structural_hash, compute_content_structural_hash

PROVENANCE_VERSION = "1.0.0"

# Storage paths (configurable via environment)
PROV_DIR = os.environ.get("WINDI_PROVENANCE_DIR", "/opt/windi/provenance")
RECORDS_DIR = os.path.join(PROV_DIR, "records")
INDEX_FILE = os.path.join(PROV_DIR, "index.json")

# System identity (fixed for this installation)
SYSTEM_IDENTITY = {
    "system": "WINDI Publishing House",
    "engine": "WINDI Governance Engine",
    "division": "Document Security Division",
    "version": PROVENANCE_VERSION,
    "jurisdiction": "DE — Federal Republic of Germany",
    "infrastructure": "Strato DE (German jurisdiction)",
    "server_id": os.environ.get("WINDI_SERVER_ID", "strato-kempten-01"),
    "protocol": "WINDI-SOF-v1"
}


# ─── Safe I/O ─────────────────────────────────────────────────

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_write_json(path: str, data: Any) -> None:
    """Atomic write: write to .tmp then rename."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def _load_index() -> Dict[str, Any]:
    if not os.path.exists(INDEX_FILE):
        return {}
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {}


def _update_index(
    submission_id: str,
    record_path: str,
    structural_hash: str,
    governance_level: str,
    resilience_score: int
) -> None:
    idx = _load_index()
    idx[submission_id] = {
        "record_path": record_path,
        "structural_hash": structural_hash,
        "governance_level": governance_level,
        "resilience_score": resilience_score,
        "updated_at": _utc_now(),
        "prov_version": PROVENANCE_VERSION,
    }
    _safe_write_json(INDEX_FILE, idx)


def _ensure_storage() -> None:
    """Create storage directories if they don't exist."""
    os.makedirs(RECORDS_DIR, exist_ok=True)


# ─── Build Provenance Record ─────────────────────────────────

def build_provenance_record(
    *,
    submission_id: Optional[str] = None,
    governance_level: str,
    policy_version: str = "2.2.0",
    config_hash: str = "",
    isp_profile: str = "",
    organization: str = "",
    metadata: Optional[Dict[str, Any]] = None,
    identity_governance: Optional[Dict[str, Any]] = None,
    content: Optional[str] = None,
    content_hash: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a complete provenance record for a document.
    
    For HIGH: submission_id required, full forensic trail.
    For MEDIUM: submission_id optional, identity governance included.
    For LOW: minimal provenance, structural hash only.
    
    Args:
        submission_id: Unique document/submission identifier
        governance_level: HIGH, MEDIUM, or LOW
        policy_version: Current governance policy version
        config_hash: Hash of the governance configuration used
        isp_profile: ISP profile slug (e.g., "bafin", "tuev")
        organization: Institution name
        metadata: Additional document metadata
        identity_governance: Identity governance block (MEDIUM)
        content: Document content (for structural content binding)
        content_hash: Pre-computed content hash (alternative to content)
    
    Returns:
        Complete provenance record dict
    """
    # Generate provenance ID
    provenance_id = f"WINDI-PROV-{uuid.uuid4().hex[:12].upper()}"
    
    if not submission_id:
        submission_id = f"AUTO-{provenance_id}"
    
    # Build decision payload (what gets structurally hashed)
    decision_payload = {
        "submission_id": submission_id,
        "governance_level": governance_level.upper(),
        "policy_version": policy_version,
        "config_hash": config_hash,
        "isp_profile": isp_profile,
        "organization": organization,
        "metadata": metadata or {},
        "identity_governance": identity_governance or {},
    }
    
    # Compute structural hash of the governance decision
    structural_hash = compute_structural_hash(decision_payload)
    
    # Compute content-structural binding if content provided
    content_structural_hash = None
    if content:
        content_structural_hash = compute_content_structural_hash(
            content, metadata or {}
        )
    
    # Compute provenance hash (hash of everything including structural hash)
    import hashlib
    provenance_hash_data = json.dumps({
        "provenance_id": provenance_id,
        "structural_hash": structural_hash,
        "content_structural_hash": content_structural_hash,
        "system": SYSTEM_IDENTITY["system"],
        "jurisdiction": SYSTEM_IDENTITY["jurisdiction"]
    }, sort_keys=True, ensure_ascii=False)
    provenance_hash = hashlib.sha256(provenance_hash_data.encode("utf-8")).hexdigest()
    
    # Compute resilience score
    from .deepfake_risk import compute_resilience_score, resilience_rating
    
    features = {
        "provenance_record": "required" if governance_level.upper() == "HIGH" else "optional",
        "registry": governance_level.upper() in ("HIGH", "MEDIUM"),
        "structural_hash": "strict",
        "embed_pdf_metadata": governance_level.upper() in ("HIGH", "MEDIUM"),
        "tamper_evidence": governance_level.upper() == "HIGH",
        "identity_governance": identity_governance is not None and len(identity_governance) > 0,
        "forensic_ledger": governance_level.upper() == "HIGH",
        "four_eyes": governance_level.upper() == "HIGH",
        "jurisdiction_bound": True,
    }
    
    resilience_score = compute_resilience_score(governance_level, features)
    
    # Assemble full record
    record = {
        # Header
        "_provenance_version": PROVENANCE_VERSION,
        "_protocol": "WINDI-SOF-v1",
        "provenance_id": provenance_id,
        "created_at": _utc_now(),
        
        # Document identity
        "submission_id": submission_id,
        "document_id": submission_id,  # alias for compatibility
        
        # Governance context
        "governance_context": {
            "level": governance_level.upper(),
            "isp_profile": isp_profile,
            "policy_version": policy_version,
            "config_hash": config_hash,
            "organization": organization,
        },
        
        # Identity governance (MEDIUM/HIGH)
        "identity_governance": identity_governance or {},
        
        # System identity
        "system_identity": SYSTEM_IDENTITY,
        
        # Cryptographic proof
        "cryptographic_proof": {
            "structural_hash": structural_hash,
            "provenance_hash": provenance_hash,
            "content_structural_hash": content_structural_hash,
            "content_hash": content_hash,
            "algorithm": "SHA-256",
            "hash_chain": f"{structural_hash[:16]}→{provenance_hash[:16]}"
        },
        
        # Deepfake resilience
        "deepfake_resilience": {
            "score": resilience_score,
            "rating": resilience_rating(resilience_score),
            "max_score": 100,
        },
        
        # Verification endpoint
        "verification": {
            "verify_url": f"/api/verify/{submission_id}",
            "verify_hash": provenance_hash[:32],
            "protocol": "WINDI-SOF-v1"
        },
        
        # Raw decision payload (for re-verification)
        "decision_payload": decision_payload,
    }
    
    return record


# ─── Persist & Load ──────────────────────────────────────────

def persist_provenance_record(record: Dict[str, Any]) -> Optional[str]:
    """
    Store provenance record to disk.
    
    For HIGH: always persisted (required).
    For MEDIUM: persisted if submission_id exists.
    For LOW: not persisted by default (metadata-only).
    
    Returns path to stored record, or None if not persisted.
    """
    submission_id = record.get("submission_id")
    if not submission_id:
        return None
    
    level = record.get("governance_context", {}).get("level", "LOW")
    
    # LOW: don't persist by default
    if level == "LOW" and not submission_id.startswith("FORCE-"):
        return None
    
    _ensure_storage()
    
    # Safe filename
    safe_id = submission_id.replace("/", "_").replace("\\", "_")
    fname = f"{safe_id}.json"
    path = os.path.join(RECORDS_DIR, fname)
    
    _safe_write_json(path, record)
    
    # Update index
    _update_index(
        submission_id=submission_id,
        record_path=path,
        structural_hash=record.get("cryptographic_proof", {}).get("structural_hash", ""),
        governance_level=level,
        resilience_score=record.get("deepfake_resilience", {}).get("score", 0)
    )
    
    return path


def load_provenance_record(submission_id: str) -> Optional[Dict[str, Any]]:
    """Load a provenance record by submission ID."""
    idx = _load_index()
    entry = idx.get(submission_id)
    if not entry:
        return None
    
    record_path = entry.get("record_path")
    if not record_path or not os.path.exists(record_path):
        return None
    
    with open(record_path, "r", encoding="utf-8") as f:
        return json.load(f)
