"""
WINDI DeepDOCFakes — PDF Metadata Embed
==========================================
Embeds provenance data into PDF custom metadata fields.

A deepfake copies the VISIBLE document.
It does NOT copy internal XMP/metadata fields.

This module writes provenance markers into PDF metadata that:
1. Are invisible to the reader
2. Can be extracted and verified programmatically
3. Create a structural binding between PDF and governance record
4. Survive copy/paste of content but not of the PDF itself

Requires: pikepdf (pip install pikepdf)

Note: This module provides the DATA PREPARATION layer.
Actual PDF writing is handled by the document generation pipeline.
For systems without pikepdf, the metadata dict can be embedded
via other PDF libraries (reportlab, fpdf2, etc.).
"""

import json
from typing import Any, Dict, Optional
from datetime import datetime, timezone


# WINDI XMP Namespace (custom)
WINDI_XMP_NS = "http://windi.pub/ns/provenance/1.0/"
WINDI_XMP_PREFIX = "windi"


def build_pdf_metadata(
    provenance_record: Dict[str, Any],
    include_full_record: bool = False
) -> Dict[str, str]:
    """
    Build a flat dict of metadata fields suitable for PDF embedding.
    
    For HIGH: full provenance embedded.
    For MEDIUM: structural hash + identity governance.
    For LOW: provenance ID + structural hash only.
    
    Args:
        provenance_record: The full provenance record dict
        include_full_record: If True, embed the entire record as JSON
    
    Returns:
        Dict of string key-value pairs for PDF metadata fields
    """
    crypto = provenance_record.get("cryptographic_proof", {})
    gov = provenance_record.get("governance_context", {})
    resilience = provenance_record.get("deepfake_resilience", {})
    verification = provenance_record.get("verification", {})
    level = gov.get("level", "LOW")
    
    metadata = {
        # Always present
        f"{WINDI_XMP_PREFIX}:ProvenanceID": provenance_record.get("provenance_id", ""),
        f"{WINDI_XMP_PREFIX}:Protocol": "WINDI-SOF-v1",
        f"{WINDI_XMP_PREFIX}:GovernanceLevel": level,
        f"{WINDI_XMP_PREFIX}:StructuralHash": crypto.get("structural_hash", ""),
        f"{WINDI_XMP_PREFIX}:CreatedAt": provenance_record.get("created_at", ""),
        f"{WINDI_XMP_PREFIX}:System": "WINDI Publishing House",
        f"{WINDI_XMP_PREFIX}:Jurisdiction": "DE",
    }
    
    # MEDIUM additions
    if level in ("MEDIUM", "HIGH"):
        metadata[f"{WINDI_XMP_PREFIX}:ProvenanceHash"] = crypto.get("provenance_hash", "")
        metadata[f"{WINDI_XMP_PREFIX}:HashChain"] = crypto.get("hash_chain", "")
        metadata[f"{WINDI_XMP_PREFIX}:PolicyVersion"] = gov.get("policy_version", "")
        metadata[f"{WINDI_XMP_PREFIX}:ISPProfile"] = gov.get("isp_profile", "")
        metadata[f"{WINDI_XMP_PREFIX}:ResilienceScore"] = str(resilience.get("score", 0))
        metadata[f"{WINDI_XMP_PREFIX}:VerifyURL"] = verification.get("verify_url", "")
        
        # Identity governance fields
        identity = provenance_record.get("identity_governance", {})
        if identity:
            metadata[f"{WINDI_XMP_PREFIX}:IdentityLicense"] = identity.get("license_status", "none")
            metadata[f"{WINDI_XMP_PREFIX}:IdentityControlled"] = str(identity.get("identity_controlled", False))
    
    # HIGH additions
    if level == "HIGH":
        metadata[f"{WINDI_XMP_PREFIX}:ContentStructuralHash"] = crypto.get("content_structural_hash", "") or ""
        metadata[f"{WINDI_XMP_PREFIX}:SubmissionID"] = provenance_record.get("submission_id", "")
        metadata[f"{WINDI_XMP_PREFIX}:ConfigHash"] = gov.get("config_hash", "")
        metadata[f"{WINDI_XMP_PREFIX}:Organization"] = gov.get("organization", "")
        metadata[f"{WINDI_XMP_PREFIX}:ResilienceRating"] = resilience.get("rating", "")
    
    # Optional: full record as JSON blob
    if include_full_record:
        metadata[f"{WINDI_XMP_PREFIX}:FullRecord"] = json.dumps(
            provenance_record, ensure_ascii=False
        )
    
    return metadata


def build_xmp_xml(metadata: Dict[str, str]) -> str:
    """
    Build XMP XML block for embedding in PDF.
    
    This generates a standards-compliant XMP metadata block
    using the WINDI custom namespace.
    
    Note: For production use, consider using python-xmp-toolkit
    or pikepdf's XMP support for full standards compliance.
    """
    lines = [
        '<?xpacket begin="\xef\xbb\xbf" id="W5M0MpCehiHzreSzNTczkc9d"?>',
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">',
        '  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">',
        '    <rdf:Description',
        f'      xmlns:{WINDI_XMP_PREFIX}="{WINDI_XMP_NS}"',
        '      rdf:about="">',
    ]
    
    for key, value in sorted(metadata.items()):
        # Escape XML special characters
        safe_value = (
            str(value)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
        lines.append(f'      <{key}>{safe_value}</{key}>')
    
    lines.extend([
        '    </rdf:Description>',
        '  </rdf:RDF>',
        '</x:xmpmeta>',
        '<?xpacket end="w"?>'
    ])
    
    return "\n".join(lines)


def extract_windi_metadata(pdf_metadata: Dict[str, str]) -> Dict[str, str]:
    """
    Extract WINDI provenance fields from PDF metadata.
    
    Args:
        pdf_metadata: Raw PDF metadata dict (from pikepdf, PyPDF2, etc.)
    
    Returns:
        Dict containing only WINDI provenance fields
    """
    windi_fields = {}
    prefix = f"{WINDI_XMP_PREFIX}:"
    
    for key, value in pdf_metadata.items():
        if key.startswith(prefix):
            field_name = key[len(prefix):]
            windi_fields[field_name] = value
    
    return windi_fields


def verify_pdf_provenance(windi_metadata: Dict[str, str]) -> Dict[str, Any]:
    """
    Quick verification of WINDI metadata extracted from a PDF.
    
    Checks:
    1. Required fields present
    2. Protocol matches
    3. Governance level valid
    4. Hash fields non-empty
    
    For full verification, use verify_engine.verify_by_submission_id()
    with the extracted submission_id and decision_payload.
    """
    result = {
        "pdf_provenance_present": False,
        "checks": {}
    }
    
    if not windi_metadata:
        return result
    
    result["pdf_provenance_present"] = True
    
    # Required fields
    required = ["ProvenanceID", "Protocol", "GovernanceLevel", "StructuralHash"]
    for field in required:
        result["checks"][f"field_{field}"] = field in windi_metadata
    
    # Protocol
    result["checks"]["protocol_valid"] = windi_metadata.get("Protocol") == "WINDI-SOF-v1"
    
    # Governance level
    result["checks"]["level_valid"] = windi_metadata.get("GovernanceLevel") in ("HIGH", "MEDIUM", "LOW")
    
    # Hash non-empty
    result["checks"]["hash_present"] = bool(windi_metadata.get("StructuralHash"))
    
    all_passed = all(result["checks"].values())
    result["status"] = "PRESENT_VALID" if all_passed else "PRESENT_INCOMPLETE"
    
    return result
