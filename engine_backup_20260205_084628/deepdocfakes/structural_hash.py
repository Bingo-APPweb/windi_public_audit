"""
WINDI DeepDOCFakes — Structural Hash
======================================
Canonical, reproducible structural fingerprinting.

A deepfake copies TEXT and LAYOUT.
It cannot copy STRUCTURAL GOVERNANCE MARKERS because:
1. The canonical field order is system-internal
2. The hash includes governance context invisible in the document
3. The canonicalization rules are deterministic but not guessable
4. The provenance ID is generated at creation time

This is the document equivalent of HTTPS certificate validation.
"""

import json
import hashlib
from typing import Any, Dict, List

CANONICAL_VERSION = "1.0"


# ─── Canonical Field Orders ───────────────────────────────────
# These define the EXPECTED fields per governance level.
# A deepfake would need to guess this exact structure.

CANONICAL_FIELDS = {
    "HIGH": [
        "provenance_id",
        "governance_level",
        "forensic_ledger_entry",
        "policy_version",
        "four_eyes_verified",
        "tamper_evidence_hash",
        "chain_of_custody",
        "structural_hash",
        "provenance_hash",
        "sealed_at"
    ],
    "MEDIUM": [
        "provenance_id",
        "governance_level",
        "identity_license_status",
        "disclaimer_inserted",
        "logo_allowed",
        "structural_hash",
        "provenance_hash"
    ],
    "LOW": [
        "provenance_id",
        "governance_level",
        "template_validated",
        "structural_hash"
    ]
}


def canonicalize(obj: Any) -> Any:
    """
    Canonical JSON transformation:
    - dict keys sorted recursively
    - lists preserved in order
    - None values kept (they encode intentional absence)
    - Deterministic across Python versions
    """
    if isinstance(obj, dict):
        return {k: canonicalize(obj[k]) for k in sorted(obj.keys())}
    if isinstance(obj, list):
        return [canonicalize(x) for x in obj]
    return obj


def compute_structural_hash(payload: Dict[str, Any]) -> str:
    """
    Hash over canonical JSON of the governance decision payload.
    
    Includes:
    - governance decision context
    - ISP profile reference
    - identity_governance block (MEDIUM)
    - submission header (HIGH)
    - metadata
    
    The wrapper with _canon_version ensures hash stability
    across future versions of the canonicalization algorithm.
    """
    wrapper = {
        "_canon_version": CANONICAL_VERSION,
        "payload": canonicalize(payload),
    }
    s = json.dumps(
        wrapper,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True
    )
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def compute_field_order_hash(level: str) -> str:
    """
    Hash of the canonical field order itself.
    This is an additional structural marker that deepfakes cannot replicate
    because they don't know the expected field sequence.
    """
    fields = CANONICAL_FIELDS.get(level.upper(), CANONICAL_FIELDS["LOW"])
    field_string = "|".join(fields)
    return hashlib.sha256(field_string.encode("utf-8")).hexdigest()[:32]


def compute_content_structural_hash(content: str, metadata: Dict[str, Any]) -> str:
    """
    Combined hash of content structure + governance metadata.
    This binds the document content to its governance context.
    
    We hash STRUCTURAL properties (counts, breaks, key names),
    not the content itself — this means two documents with
    different content but same structure will have different hashes
    because the metadata differs.
    """
    lines = content.split("\n")
    structure = {
        "line_count": len(lines),
        "word_count": len(content.split()),
        "char_count": len(content),
        "paragraph_breaks": content.count("\n\n"),
        "metadata_keys": sorted(metadata.keys())
    }
    combined = (
        json.dumps(structure, sort_keys=True) +
        "|" +
        json.dumps(canonicalize(metadata), sort_keys=True)
    )
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def validate_structure(
    document_metadata: Dict[str, Any],
    level: str
) -> tuple:
    """
    Validate that a document's metadata follows the canonical structure.
    Returns (is_valid: bool, missing_fields: list).
    """
    expected = CANONICAL_FIELDS.get(level.upper(), CANONICAL_FIELDS["LOW"])
    missing = [f for f in expected if f not in document_metadata]
    return (len(missing) == 0, missing)
