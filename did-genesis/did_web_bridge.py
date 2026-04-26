#!/usr/bin/env python3
"""
§207 DID Web Bridge — W3C Compliant DID Document Server
=======================================================
Serves W3C DID-CORE 1.1 compliant DID Documents via HTTPS.

did:web Method:
- did:web:windi-domain.com → /.well-known/did.json
- did:web:windi-domain.com:u:dragon-001 → /u/dragon-001/did.json

This bridge wraps the existing DID-Genesis and outputs W3C format.

Liga IA+H · Kempten, Bavaria · 26 Apr 2026
"""

import json
import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

# ═══════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════

DB_PATH = Path(__file__).parent / "did_genesis.db"
DOMAIN = "windi-domain.com"

# W3C JSON-LD Contexts
W3C_CONTEXTS = [
    "https://www.w3.org/ns/did/v1",
    "https://w3id.org/security/suites/ed25519-2020/v1",
    f"https://{DOMAIN}/ns/windi/v1"
]

# DID Tier to Service mapping
TIER_SERVICES = {
    "SEED": [
        {"id": "#verify", "type": "VerificationService", "serviceEndpoint": f"https://{DOMAIN}/verify-public/"}
    ],
    "NODAL": [
        {"id": "#verify", "type": "VerificationService", "serviceEndpoint": f"https://{DOMAIN}/verify-public/"},
        {"id": "#wallet", "type": "WalletService", "serviceEndpoint": f"https://{DOMAIN}/wallet/"},
        {"id": "#travel", "type": "TravelService", "serviceEndpoint": f"https://{DOMAIN}/travel/"}
    ],
    "SOVEREIGN": [
        {"id": "#verify", "type": "VerificationService", "serviceEndpoint": f"https://{DOMAIN}/verify-public/"},
        {"id": "#wallet", "type": "WalletService", "serviceEndpoint": f"https://{DOMAIN}/wallet/"},
        {"id": "#travel", "type": "TravelService", "serviceEndpoint": f"https://{DOMAIN}/travel/"},
        {"id": "#law", "type": "LegalService", "serviceEndpoint": f"https://{DOMAIN}/law/"},
        {"id": "#enterprise", "type": "EnterpriseService", "serviceEndpoint": f"https://{DOMAIN}/enterprise/"}
    ],
    "ORACLE": [
        {"id": "#verify", "type": "VerificationService", "serviceEndpoint": f"https://{DOMAIN}/verify-public/"},
        {"id": "#desktop", "type": "DesktopService", "serviceEndpoint": f"https://{DOMAIN}/desktop/"},
        {"id": "#enterprise", "type": "EnterpriseService", "serviceEndpoint": f"https://{DOMAIN}/enterprise/"},
        {"id": "#ledger", "type": "ForensicLedger", "serviceEndpoint": f"https://{DOMAIN}/api/receipts/"},
        {"id": "#admin", "type": "AdminService", "serviceEndpoint": f"https://{DOMAIN}/portal/"}
    ]
}


# ═══════════════════════════════════════════════════════════════════════════
# DID DOCUMENT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

def generate_mock_public_key(did: str) -> str:
    """
    Generate a mock Ed25519 public key for demonstration.

    NOTE: This is NOT a real Ed25519 key. For production, use:
    - PyNaCl for real Ed25519 key generation
    - Store actual public keys in database

    TODO-SOVEREIGN: Replace with real Ed25519 keys in §207-F2
    """
    # Generate deterministic "multibase" format key (z = base58btc)
    hash_bytes = hashlib.sha256(f"windi-mock-key:{did}".encode()).digest()
    # Multibase z prefix + mock base58 encoding (simplified)
    import base64
    mock_key = "z" + base64.b64encode(hash_bytes).decode().replace("+", "").replace("/", "")[:43]
    return mock_key


def get_identity_from_db(sovereign_name: str) -> Optional[Dict[str, Any]]:
    """Fetch identity from DID-Genesis database."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Try sovereign_name first
        cursor.execute("""
            SELECT did, sovereign_name, display_name, email, role, tier, status, created_at
            FROM identities
            WHERE LOWER(sovereign_name) = ? AND status = 'active'
        """, (sovereign_name.lower(),))
        row = cursor.fetchone()

        # Try alias if not found
        if not row:
            cursor.execute("""
                SELECT i.did, i.sovereign_name, i.display_name, i.email, i.role, i.tier, i.status, i.created_at
                FROM did_aliases a
                JOIN identities i ON i.did = a.canonical_did
                WHERE LOWER(a.alias_actor) = ? AND a.status = 'active' AND i.status = 'active'
            """, (sovereign_name.lower(),))
            row = cursor.fetchone()

        conn.close()

        if row:
            return dict(row)
        return None
    except Exception as e:
        return None


def build_did_document(identity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build W3C DID-CORE 1.1 compliant DID Document.

    Reference: https://www.w3.org/TR/did-core/
    """
    did = identity["did"]
    sovereign_name = identity.get("sovereign_name") or did.split(":")[-1]
    tier = identity.get("tier", "SEED")
    created_at = identity.get("created_at", datetime.now(timezone.utc).isoformat())

    # did:web format
    did_web = f"did:web:{DOMAIN}:u:{sovereign_name}"

    # Generate mock public key (TODO: replace with real Ed25519)
    public_key = generate_mock_public_key(did)
    key_id = f"{did_web}#keys-1"

    # Build services based on tier
    services = []
    for svc in TIER_SERVICES.get(tier, TIER_SERVICES["SEED"]):
        services.append({
            "id": f"{did_web}{svc['id']}",
            "type": svc["type"],
            "serviceEndpoint": svc["serviceEndpoint"]
        })

    # W3C DID Document
    doc = {
        "@context": W3C_CONTEXTS,
        "id": did_web,
        "alsoKnownAs": [did],  # Link to original did:windi
        "controller": did_web,
        "verificationMethod": [
            {
                "id": key_id,
                "type": "Ed25519VerificationKey2020",
                "controller": did_web,
                "publicKeyMultibase": public_key
            }
        ],
        "authentication": [key_id],
        "assertionMethod": [key_id],
        "capabilityInvocation": [key_id],
        "capabilityDelegation": [key_id],
        "service": services,
        "created": created_at,
        "updated": datetime.now(timezone.utc).isoformat()
    }

    # Add WINDI-specific metadata (allowed by W3C spec)
    doc["_windi"] = {
        "sovereign_name": sovereign_name,
        "display_name": identity.get("display_name", ""),
        "tier": tier,
        "role": identity.get("role", "user"),
        "original_did": did,
        "genesis_source": "W-DID-GENESIS",
        "bridge_version": "§207"
    }

    return doc


# ═══════════════════════════════════════════════════════════════════════════
# FASTAPI ROUTER
# ═══════════════════════════════════════════════════════════════════════════

def create_did_web_router() -> APIRouter:
    """Create FastAPI router for did:web endpoints."""

    router = APIRouter(tags=["DID-Web-Bridge"])

    @router.get("/.well-known/did.json")
    async def domain_did_document():
        """
        Domain-level DID Document.
        did:web:windi-domain.com → /.well-known/did.json

        Returns the WINDI Publishing House organizational DID.
        """
        org_doc = {
            "@context": W3C_CONTEXTS,
            "id": f"did:web:{DOMAIN}",
            "controller": f"did:web:{DOMAIN}",
            "verificationMethod": [
                {
                    "id": f"did:web:{DOMAIN}#org-key-1",
                    "type": "Ed25519VerificationKey2020",
                    "controller": f"did:web:{DOMAIN}",
                    "publicKeyMultibase": generate_mock_public_key(f"did:web:{DOMAIN}")
                }
            ],
            "authentication": [f"did:web:{DOMAIN}#org-key-1"],
            "assertionMethod": [f"did:web:{DOMAIN}#org-key-1"],
            "service": [
                {
                    "id": f"did:web:{DOMAIN}#genesis",
                    "type": "DIDGenesisService",
                    "serviceEndpoint": f"https://{DOMAIN}/api/genesis/"
                },
                {
                    "id": f"did:web:{DOMAIN}#ledger",
                    "type": "ForensicLedger",
                    "serviceEndpoint": f"https://{DOMAIN}/api/receipts/"
                },
                {
                    "id": f"did:web:{DOMAIN}#verify",
                    "type": "VerificationService",
                    "serviceEndpoint": f"https://{DOMAIN}/verify-public/"
                }
            ],
            "_windi": {
                "organization": "WINDI Publishing House",
                "location": "Kempten, Bavaria, Deutschland",
                "founder": "did:web:windi-domain.com:u:dragon-001",
                "decree": "DECRETO-001 Art.4",
                "bridge_version": "§207"
            },
            "created": "2026-01-01T00:00:00Z",
            "updated": datetime.now(timezone.utc).isoformat()
        }

        return JSONResponse(
            content=org_doc,
            media_type="application/did+ld+json"
        )

    @router.get("/u/{sovereign_name}/did.json")
    async def user_did_document(sovereign_name: str):
        """
        User-level DID Document.
        did:web:windi-domain.com:u:dragon-001 → /u/dragon-001/did.json

        Returns W3C DID-CORE 1.1 compliant DID Document.
        """
        # Fetch from Genesis
        identity = get_identity_from_db(sovereign_name)

        if not identity:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "DID not found",
                    "did_web": f"did:web:{DOMAIN}:u:{sovereign_name}",
                    "resolution_url": f"https://{DOMAIN}/u/{sovereign_name}/did.json",
                    "hint": "Use sovereign_name (e.g., dragon-001)"
                }
            )

        # Build W3C compliant document
        doc = build_did_document(identity)

        return JSONResponse(
            content=doc,
            media_type="application/did+ld+json"
        )

    @router.get("/api/did-web/resolve/{did_path:path}")
    async def resolve_did_web(did_path: str):
        """
        Universal DID resolver endpoint.
        Accepts: did:web:windi-domain.com:u:dragon-001
        Returns: DID Document
        """
        # Parse did:web
        if not did_path.startswith("did:web:"):
            raise HTTPException(400, "Invalid DID format. Use did:web:...")

        parts = did_path.replace("did:web:", "").split(":")

        if len(parts) == 1 and parts[0] == DOMAIN:
            # Domain DID
            return await domain_did_document()
        elif len(parts) == 3 and parts[0] == DOMAIN and parts[1] == "u":
            # User DID
            return await user_did_document(parts[2])
        else:
            raise HTTPException(400, f"Cannot resolve: {did_path}")

    @router.get("/api/did-web/health")
    async def did_web_health():
        """Health check for DID Web Bridge."""
        return {
            "service": "DID-Web-Bridge",
            "version": "§207",
            "status": "operational",
            "spec": "W3C DID-CORE 1.1",
            "method": "did:web",
            "domain": DOMAIN,
            "endpoints": {
                "domain_did": f"https://{DOMAIN}/.well-known/did.json",
                "user_did_pattern": f"https://{DOMAIN}/u/{{sovereign_name}}/did.json",
                "resolver": f"https://{DOMAIN}/api/did-web/resolve/{{did}}"
            },
            "conformance": {
                "json_ld": True,
                "verification_method": True,
                "authentication": True,
                "service": True,
                "note": "Mock Ed25519 keys - production requires real key generation"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    return router


# ═══════════════════════════════════════════════════════════════════════════
# STANDALONE TEST
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Test document generation
    identity = get_identity_from_db("dragon-001")
    if identity:
        doc = build_did_document(identity)
        print(json.dumps(doc, indent=2))
    else:
        print("Identity not found")
