"""
WINDI Canonicalization Module v0.1
Cryptographic integrity layer for WINDI envelopes.

"AI processes. Human decides. WINDI guarantees."

This module provides:
- Canonical JSON (C14N) serialization
- SHA-256 hashing
- Governance digest computation
- Document hash binding
- Structural signatures (HMAC)
"""

import json
import hashlib
import hmac
from typing import Any, Dict
from datetime import datetime, timezone


def canonical_json(data: Dict[str, Any]) -> bytes:
    """
    Deterministic JSON serialization.
    - UTF-8 encoding
    - Sorted keys
    - No whitespace
    - Consistent separators
    
    This ensures the same object always produces the same hash.
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    """Compute SHA-256 hash and return as hex string."""
    return hashlib.sha256(data).hexdigest()


def governance_digest(governance_obj: Dict[str, Any]) -> str:
    """
    Compute hash of governance metadata.
    The governance object is canonicalized before hashing.
    """
    return sha256_hex(canonical_json(governance_obj))


def document_hash(governance_digest_hex: str, body_sha256_hex: str) -> str:
    """
    Compute document hash that binds governance to content.
    doc_hash = SHA256(governance_digest + body_sha256)
    
    This creates an immutable mathematical link between:
    - WHO issued it (issuer_id)
    - WITH WHAT intent (intent_code)
    - UNDER WHICH policy (policy_reference)
    - WHEN (timestamp)
    - AND the actual content (body)
    """
    combined = (governance_digest_hex + body_sha256_hex).encode("utf-8")
    return sha256_hex(combined)


def hmac_sha256_hex(secret_key: bytes, message: bytes) -> str:
    """Compute HMAC-SHA256 and return as hex string."""
    return hmac.new(secret_key, message, hashlib.sha256).hexdigest()


def structural_signature(secret_key: bytes, doc_hash_hex: str) -> str:
    """
    Compute structural signature using HMAC.
    struct_sig = HMAC-SHA256(issuer_secret, doc_hash)
    
    This proves the issuer identity without revealing the secret.
    """
    return hmac_sha256_hex(secret_key, doc_hash_hex.encode("utf-8"))


def build_windi_envelope(
    document_id: str,
    version_id: str,
    content_type: str,
    body_bytes: bytes,
    issuer_id: str,
    responsible_actor_id: str,
    intent_code: str,
    policy_reference: str,
    issuer_secret: bytes,
    jurisdictions: list = None,
    additional_governance: dict = None
) -> Dict[str, Any]:
    """
    Build a complete WINDI v0.1 envelope.
    
    Args:
        document_id: Unique document identifier
        version_id: Version of this document
        content_type: MIME type (e.g., "application/pdf")
        body_bytes: Raw document content
        issuer_id: Identity of the issuing entity
        responsible_actor_id: Human responsible for this document
        intent_code: Purpose code (e.g., "publish.certificate")
        policy_reference: Governing policy (e.g., "eu.ai.act.article.52")
        issuer_secret: Secret key for HMAC signature
        jurisdictions: List of applicable jurisdictions
        additional_governance: Extra governance fields
    
    Returns:
        Complete WINDI envelope as dict
    """
    if jurisdictions is None:
        jurisdictions = ["DE", "EU"]
    
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Build governance object
    governance = {
        "issuer_id": issuer_id,
        "responsible_actor_id": responsible_actor_id,
        "intent_code": intent_code,
        "policy_reference": policy_reference,
        "jurisdictions": jurisdictions,
        "timestamp_issued": timestamp
    }
    
    if additional_governance:
        governance.update(additional_governance)
    
    # Compute integrity chain
    body_sha = sha256_hex(body_bytes)
    gov_digest = governance_digest(governance)
    doc_hash = document_hash(gov_digest, body_sha)
    struct_sig = structural_signature(issuer_secret, doc_hash)
    
    # Build envelope
    envelope = {
        "schema": "windi.envelope",
        "schema_version": "0.1",
        "document": {
            "document_id": document_id,
            "version_id": version_id,
            "content_type": content_type,
            "body_sha256": body_sha
        },
        "governance": governance,
        "integrity": {
            "governance_digest": gov_digest,
            "doc_hash": doc_hash,
            "struct_sig": struct_sig,
            "algo": "sha256+hmac-sha256"
        }
    }
    
    return envelope


def verify_envelope_integrity(envelope: Dict[str, Any], body_bytes: bytes = None) -> Dict[str, Any]:
    """
    Verify a WINDI envelope's integrity.
    
    Args:
        envelope: The WINDI envelope to verify
        body_bytes: Optional body content to verify body_sha256
    
    Returns:
        Verification report with computed values and match status
    """
    report = {
        "ok": True,
        "checks": {},
        "computed": {},
        "notes": []
    }
    
    # Schema checks
    report["checks"]["schema"] = (envelope.get("schema") == "windi.envelope")
    report["checks"]["schema_version"] = (envelope.get("schema_version") == "0.1")
    
    if not report["checks"]["schema"] or not report["checks"]["schema_version"]:
        report["ok"] = False
        report["notes"].append("Schema/version mismatch")
    
    gov = envelope.get("governance", {})
    integ = envelope.get("integrity", {})
    doc = envelope.get("document", {})
    
    # Compute governance digest
    computed_gov_digest = governance_digest(gov)
    report["computed"]["governance_digest"] = computed_gov_digest
    
    claimed_gov_digest = integ.get("governance_digest")
    if claimed_gov_digest:
        report["checks"]["governance_digest_match"] = (claimed_gov_digest == computed_gov_digest)
        if not report["checks"]["governance_digest_match"]:
            report["ok"] = False
    
    # Verify body hash if content provided
    if body_bytes:
        computed_body_sha = sha256_hex(body_bytes)
        report["computed"]["body_sha256"] = computed_body_sha
        claimed_body_sha = doc.get("body_sha256")
        if claimed_body_sha:
            report["checks"]["body_sha256_match"] = (claimed_body_sha == computed_body_sha)
            if not report["checks"]["body_sha256_match"]:
                report["ok"] = False
    else:
        report["computed"]["body_sha256"] = doc.get("body_sha256", "NOT_PROVIDED")
    
    # Compute document hash
    body_sha_for_doc_hash = report["computed"]["body_sha256"]
    if body_sha_for_doc_hash and body_sha_for_doc_hash != "NOT_PROVIDED":
        computed_doc_hash = document_hash(computed_gov_digest, body_sha_for_doc_hash)
        report["computed"]["doc_hash"] = computed_doc_hash
        
        claimed_doc_hash = integ.get("doc_hash")
        if claimed_doc_hash:
            report["checks"]["doc_hash_match"] = (claimed_doc_hash == computed_doc_hash)
            if not report["checks"]["doc_hash_match"]:
                report["ok"] = False
    
    # Note: struct_sig verification requires issuer_secret (not done here)
    report["notes"].append("struct_sig verification requires issuer_secret")
    
    return report


# ═══════════════════════════════════════════════════════════════════════════════
# CLI / TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("WINDI Canonicalization Module v0.1")
    print("=" * 60)
    
    # Test envelope creation
    test_content = b"Test document content for WINDI verification"
    test_secret = b"test_issuer_secret_key"
    
    envelope = build_windi_envelope(
        document_id="TEST-DOC-001",
        version_id="v1",
        content_type="text/plain",
        body_bytes=test_content,
        issuer_id="windi.publishing.de",
        responsible_actor_id="cgo.jober",
        intent_code="test.verification",
        policy_reference="internal.test",
        issuer_secret=test_secret
    )
    
    print("\nGenerated Envelope:")
    print(json.dumps(envelope, indent=2))
    
    print("\nVerification:")
    report = verify_envelope_integrity(envelope, test_content)
    print(json.dumps(report, indent=2))
    
    print("\n" + "=" * 60)
    print("Module ready for integration")
    print("=" * 60)
