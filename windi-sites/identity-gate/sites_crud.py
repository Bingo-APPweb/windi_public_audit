"""
W-SITES-001 — Sites & Containers CRUD
=====================================
§235 Genesis Schema + §236 CRUD + L-1/L0 Scaffolding

Port: :8192 (via identity_gate.py router)
Invariants: I1, I9, I11, I12, I14

Endpoints:
  POST   /api/sites                      → Create site
  GET    /api/sites                      → List sites (by company DID)
  GET    /api/sites/{id}                 → Get site
  PATCH  /api/sites/{id}                 → Update site
  DELETE /api/sites/{id}                 → Suspend site (soft delete)

  POST   /api/sites/{site_id}/containers → Create container (nested)
  GET    /api/sites/{site_id}/containers → List containers of site
  GET    /api/containers/{id}            → Get container
  PATCH  /api/containers/{id}            → Update container (triggers L0)
  DELETE /api/containers/{id}            → Suspend container (soft delete)

  GET    /api/containers/{id}/provenance → I11 provenance chain

Liga IA+H · Kempten, Bavaria · 2026
"AI processes. Human decides. WINDI guarantees."
"""

from fastapi import APIRouter, HTTPException, Request, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import sqlite3
import uuid
import hashlib
import json
import requests

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

DB_PATH = "/opt/windi/windi-sites/identity-gate/windi_sites_identity.db"
LEDGER_URL = "http://127.0.0.1:8101/api/receipts"
VERSION = "v1.0.0"

# Valid container types (§B-CONTRACT-001 MAKEUP Catalog)
VALID_CONTAINER_TYPES = {"writer", "translator", "image", "seo"}

# Valid tiers (§B-CONTRACT-001 Art. 1.2)
VALID_TIERS = {"FREE", "MED", "HIGH"}

# ═══════════════════════════════════════════════════════════════════════════
# §C-ACCEPTABILITY-001 — L-1/L0 RUNTIME (§3a ACTIVATED)
# ═══════════════════════════════════════════════════════════════════════════
# Runtime replaces pass-through stubs. Interfaces remain frozen.
# ═══════════════════════════════════════════════════════════════════════════

try:
    from acceptability import acceptability_l_minus_1, acceptability_l_zero, should_flag_for_l1_review
    ACCEPTABILITY_RUNTIME = True
    print("[WINDI-SITES] §C-ACCEPTABILITY runtime loaded (L-1/L0 active)")
except ImportError as e:
    # Fallback to pass-through if runtime not available
    ACCEPTABILITY_RUNTIME = False
    print(f"[WINDI-SITES] §C-ACCEPTABILITY runtime not available, using pass-through: {e}")

    async def acceptability_l_minus_1(payload: dict) -> tuple[bool, dict]:
        """L-1: Pass-through fallback."""
        return (True, {
            "layer": "L-1",
            "mode": "pass-through-fallback",
            "blocked": False,
            "ts": datetime.now(timezone.utc).isoformat()
        })

    async def acceptability_l_zero(content: dict) -> tuple[bool, dict]:
        """L0: Pass-through fallback."""
        return (True, {
            "layer": "L0",
            "mode": "pass-through-fallback",
            "blocked": False,
            "ts": datetime.now(timezone.utc).isoformat()
        })

    def should_flag_for_l1_review(log_entry: dict) -> bool:
        """L1 review flag fallback."""
        return False


def build_provenance_chain(
    existing_chain: Optional[str],
    new_receipt: str,
    acceptability_logs: List[dict]
) -> str:
    """
    Build I11-compliant provenance chain.

    Args:
        existing_chain: JSON string of existing chain (or None)
        new_receipt: New receipt ID to add
        acceptability_logs: List of L-1/L0 log entries

    Returns:
        JSON string of updated provenance chain
    """
    if existing_chain:
        chain = json.loads(existing_chain)
    else:
        chain = {"receipts": [], "acceptability_log": []}

    chain["receipts"].append(new_receipt)
    chain["acceptability_log"].extend(acceptability_logs)

    return json.dumps(chain)


# ═══════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════════════════

class SiteCreate(BaseModel):
    """Create a new site."""
    name: str
    subdomain: Optional[str] = None  # FREE tier
    custom_domain: Optional[str] = None  # MED tier
    tier: str = "FREE"

    @field_validator('tier')
    @classmethod
    def validate_tier(cls, v):
        if v not in VALID_TIERS:
            raise ValueError(f'Invalid tier: {v}. Must be one of {VALID_TIERS}')
        return v

    @field_validator('subdomain')
    @classmethod
    def validate_subdomain(cls, v):
        if v and not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Subdomain must be alphanumeric with optional hyphens/underscores')
        return v.lower() if v else None


class SiteUpdate(BaseModel):
    """Update site fields."""
    name: Optional[str] = None
    subdomain: Optional[str] = None
    custom_domain: Optional[str] = None
    tier: Optional[str] = None
    status: Optional[str] = None


class ContainerCreate(BaseModel):
    """Create a new container."""
    container_type: str
    config: Optional[Dict[str, Any]] = None

    @field_validator('container_type')
    @classmethod
    def validate_type(cls, v):
        if v not in VALID_CONTAINER_TYPES:
            raise ValueError(f'Invalid container_type: {v}. Must be one of {VALID_CONTAINER_TYPES}')
        return v


class ContainerUpdate(BaseModel):
    """Update container fields."""
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    content_hash: Optional[str] = None  # Updated when content changes


# ═══════════════════════════════════════════════════════════════════════════
# DATABASE HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def get_db():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def seal_to_ledger(receipt_id: str, doc_name: str, content_hash: str, actor: str) -> dict:
    """Seal a receipt to the Forensic Ledger."""
    try:
        resp = requests.post(
            LEDGER_URL,
            json={
                "id": receipt_id,
                "actor": actor,
                "app": "w-sites-001",
                "doc_name": doc_name,
                "doc_type": "doc",
                "governance_level": "MED",
                "content_hash": content_hash,
                "sge_score": 0
            },
            timeout=5
        )
        return resp.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# IDENTITY GATE HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def get_caller_did(request: Request) -> Optional[str]:
    """Extract caller DID from request headers or cookies."""
    # Check header first (API calls)
    did = request.headers.get("X-WINDI-DID")
    if did:
        return did

    # Check cookie (browser)
    did = request.cookies.get("windi_did")
    return did


def verify_site_ownership(site_id: str, caller_did: str) -> bool:
    """Verify that caller owns the site or is admin of owning company."""
    conn = get_db()
    cursor = conn.cursor()

    # Check if caller is site owner
    cursor.execute(
        "SELECT owner_did, company_id FROM sites WHERE id = ?",
        (site_id,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False

    owner_did, company_id = row["owner_did"], row["company_id"]

    # Direct ownership
    if owner_did == caller_did:
        conn.close()
        return True

    # Admin of company
    cursor.execute(
        "SELECT 1 FROM admins WHERE company_id = ? AND did = ?",
        (company_id, caller_did)
    )
    is_admin = cursor.fetchone() is not None
    conn.close()

    return is_admin


def verify_company_membership(company_id: str, caller_did: str) -> bool:
    """Verify that caller is admin of the company."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM admins WHERE company_id = ? AND did = ?",
        (company_id, caller_did)
    )
    result = cursor.fetchone() is not None
    conn.close()
    return result


def get_company_for_did(did: str) -> Optional[str]:
    """Get company_id for a DID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT company_id FROM admins WHERE did = ?", (did,))
    row = cursor.fetchone()
    conn.close()
    return row["company_id"] if row else None


# ═══════════════════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════════════════

sites_router = APIRouter(prefix="/api", tags=["sites"])


# ═══════════════════════════════════════════════════════════════════════════
# SITES ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@sites_router.post("/sites")
async def create_site(data: SiteCreate, request: Request):
    """
    Create a new site.

    Requires: NODAL or SOVEREIGN DID of the company
    """
    caller_did = get_caller_did(request)
    if not caller_did:
        raise HTTPException(status_code=401, detail="DID required (I9)")

    # Get company for this DID
    company_id = get_company_for_did(caller_did)
    if not company_id:
        raise HTTPException(status_code=403, detail="DID not associated with any company")

    # L-1 filter (Cardinal Sin detection)
    l1_allowed, l1_log = await acceptability_l_minus_1(data.model_dump())
    if not l1_allowed:
        # Extract reason: CS detection uses cs_id/cs_name, general uses reason
        reason = l1_log.get('cs_id') or l1_log.get('cs_name') or l1_log.get('reason', 'policy_violation')
        raise HTTPException(status_code=400, detail=f"L-1 blocked: {reason}")

    now = datetime.now(timezone.utc).isoformat()
    site_id = str(uuid.uuid4())
    receipt_id = f"WINDI-SITE-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{site_id[:8].upper()}"

    # Content hash for Ledger
    content = f"{site_id}:{data.name}:{data.tier}:{now}"
    content_hash = f"sha256:{hashlib.sha256(content.encode()).hexdigest()}"

    # Build initial provenance chain
    provenance = build_provenance_chain(None, receipt_id, [l1_log])

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO sites (id, company_id, owner_did, name, subdomain, custom_domain, tier, status, genesis_receipt, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)
        """, (
            site_id, company_id, caller_did, data.name,
            data.subdomain, data.custom_domain, data.tier,
            receipt_id, now
        ))
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        if "subdomain" in str(e):
            raise HTTPException(status_code=409, detail="Subdomain already taken")
        if "custom_domain" in str(e):
            raise HTTPException(status_code=409, detail="Custom domain already registered")
        raise HTTPException(status_code=400, detail=str(e))

    conn.close()

    # Seal to Ledger
    ledger_result = seal_to_ledger(receipt_id, f"Site: {data.name}", content_hash, caller_did)

    return {
        "ok": True,
        "site_id": site_id,
        "genesis_receipt": receipt_id,
        "tier": data.tier,
        "status": "draft",
        "ledger": ledger_result,
        "provenance": json.loads(provenance),
        "invariants": ["I1", "I9", "I11"]
    }


@sites_router.get("/sites")
async def list_sites(request: Request):
    """
    List sites for the caller's company.

    Requires: DID associated with a company
    """
    caller_did = get_caller_did(request)
    if not caller_did:
        raise HTTPException(status_code=401, detail="DID required (I9)")

    company_id = get_company_for_did(caller_did)
    if not company_id:
        raise HTTPException(status_code=403, detail="DID not associated with any company")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, subdomain, custom_domain, tier, status, genesis_receipt, created_at, sealed_at
        FROM sites
        WHERE company_id = ? AND status != 'suspended'
        ORDER BY created_at DESC
    """, (company_id,))

    sites = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {
        "ok": True,
        "company_id": company_id,
        "count": len(sites),
        "sites": sites
    }


@sites_router.get("/sites/{site_id}")
async def get_site(site_id: str, request: Request):
    """
    Get site details.

    Requires: DID that owns the site or is admin of owning company
    """
    caller_did = get_caller_did(request)
    if not caller_did:
        raise HTTPException(status_code=401, detail="DID required (I9)")

    if not verify_site_ownership(site_id, caller_did):
        raise HTTPException(status_code=403, detail="Not authorized for this site")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sites WHERE id = ?", (site_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Site not found (I14)")

    return {
        "ok": True,
        "site": dict(row)
    }


@sites_router.patch("/sites/{site_id}")
async def update_site(site_id: str, data: SiteUpdate, request: Request):
    """
    Update site fields.

    Requires: DID that owns the site
    """
    caller_did = get_caller_did(request)
    if not caller_did:
        raise HTTPException(status_code=401, detail="DID required (I9)")

    if not verify_site_ownership(site_id, caller_did):
        raise HTTPException(status_code=403, detail="Not authorized for this site")

    # L0 filter (pass-through)
    l0_allowed, l0_log = await acceptability_l_zero(data.model_dump(exclude_none=True))
    if not l0_allowed:
        raise HTTPException(status_code=400, detail=f"L0 blocked: {l0_log.get('reason')}")

    # Build update query dynamically
    updates = []
    values = []
    for field, value in data.model_dump(exclude_none=True).items():
        updates.append(f"{field} = ?")
        values.append(value)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update (I14)")

    values.append(site_id)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE sites SET {', '.join(updates)} WHERE id = ?",
        values
    )
    conn.commit()

    # Fetch updated site
    cursor.execute("SELECT * FROM sites WHERE id = ?", (site_id,))
    row = cursor.fetchone()
    conn.close()

    return {
        "ok": True,
        "site": dict(row),
        "acceptability": l0_log
    }


@sites_router.delete("/sites/{site_id}")
async def suspend_site(site_id: str, request: Request):
    """
    Suspend a site (soft delete per I11).

    Requires: DID that owns the site
    """
    caller_did = get_caller_did(request)
    if not caller_did:
        raise HTTPException(status_code=401, detail="DID required (I9)")

    if not verify_site_ownership(site_id, caller_did):
        raise HTTPException(status_code=403, detail="Not authorized for this site")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE sites SET status = 'suspended' WHERE id = ?",
        (site_id,)
    )
    conn.commit()
    conn.close()

    return {
        "ok": True,
        "site_id": site_id,
        "status": "suspended",
        "note": "Soft delete per I11 — evidence preserved in Ledger"
    }


# ═══════════════════════════════════════════════════════════════════════════
# CONTAINERS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@sites_router.post("/sites/{site_id}/containers")
async def create_container(site_id: str, data: ContainerCreate, request: Request):
    """
    Create a new container for a site.

    Requires: DID that owns the site
    Triggers: L-1 filter (pass-through)
    """
    caller_did = get_caller_did(request)
    if not caller_did:
        raise HTTPException(status_code=401, detail="DID required (I9)")

    if not verify_site_ownership(site_id, caller_did):
        raise HTTPException(status_code=403, detail="Not authorized for this site")

    # L-1 filter (Cardinal Sin detection)
    l1_allowed, l1_log = await acceptability_l_minus_1(data.model_dump())
    if not l1_allowed:
        # Extract reason: CS detection uses cs_id/cs_name, general uses reason
        reason = l1_log.get('cs_id') or l1_log.get('cs_name') or l1_log.get('reason', 'policy_violation')
        raise HTTPException(status_code=400, detail=f"L-1 blocked: {reason}")

    now = datetime.now(timezone.utc).isoformat()
    container_id = str(uuid.uuid4())
    receipt_id = f"WINDI-CONTAINER-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{container_id[:8].upper()}"

    # Content hash for Ledger
    content = f"{container_id}:{site_id}:{data.container_type}:{now}"
    content_hash = f"sha256:{hashlib.sha256(content.encode()).hexdigest()}"

    # Get site's genesis receipt for chain
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT genesis_receipt FROM sites WHERE id = ?", (site_id,))
    site_row = cursor.fetchone()
    if not site_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Site not found (I14)")

    parent_receipt = site_row["genesis_receipt"]

    # Build provenance chain
    provenance = build_provenance_chain(None, receipt_id, [l1_log])

    try:
        cursor.execute("""
            INSERT INTO site_containers (
                id, site_id, container_type, config, status,
                l1_review_pending, acceptability_layer, genesis_receipt,
                parent_receipt, provenance_chain, created_at
            ) VALUES (?, ?, ?, ?, 'draft', FALSE, ?, ?, ?, ?, ?)
        """, (
            container_id, site_id, data.container_type,
            json.dumps(data.config) if data.config else None,
            l1_log["layer"],
            receipt_id, parent_receipt, provenance, now
        ))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=str(e))

    conn.close()

    # Seal to Ledger
    ledger_result = seal_to_ledger(
        receipt_id,
        f"Container: {data.container_type}",
        content_hash,
        caller_did
    )

    return {
        "ok": True,
        "container_id": container_id,
        "site_id": site_id,
        "container_type": data.container_type,
        "genesis_receipt": receipt_id,
        "parent_receipt": parent_receipt,
        "status": "draft",
        "ledger": ledger_result,
        "provenance": json.loads(provenance),
        "invariants": ["I1", "I9", "I11"]
    }


@sites_router.get("/sites/{site_id}/containers")
async def list_containers(site_id: str, request: Request):
    """
    List containers for a site.

    Requires: DID that owns the site or is admin of owning company
    """
    caller_did = get_caller_did(request)
    if not caller_did:
        raise HTTPException(status_code=401, detail="DID required (I9)")

    if not verify_site_ownership(site_id, caller_did):
        raise HTTPException(status_code=403, detail="Not authorized for this site")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, container_type, config, content_hash, status,
               l1_review_pending, acceptability_layer, genesis_receipt,
               parent_receipt, created_at, sealed_at
        FROM site_containers
        WHERE site_id = ? AND status != 'suspended'
        ORDER BY created_at DESC
    """, (site_id,))

    containers = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {
        "ok": True,
        "site_id": site_id,
        "count": len(containers),
        "containers": containers
    }


@sites_router.get("/containers/{container_id}")
async def get_container(container_id: str, request: Request):
    """
    Get container details.

    Requires: DID that owns the parent site
    """
    caller_did = get_caller_did(request)
    if not caller_did:
        raise HTTPException(status_code=401, detail="DID required (I9)")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM site_containers WHERE id = ?", (container_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Container not found (I14)")

    site_id = row["site_id"]
    conn.close()

    if not verify_site_ownership(site_id, caller_did):
        raise HTTPException(status_code=403, detail="Not authorized for this container")

    return {
        "ok": True,
        "container": dict(row)
    }


@sites_router.patch("/containers/{container_id}")
async def update_container(container_id: str, data: ContainerUpdate, request: Request):
    """
    Update container fields.

    Requires: DID that owns the parent site
    Triggers: L0 filter (pass-through)
    """
    caller_did = get_caller_did(request)
    if not caller_did:
        raise HTTPException(status_code=401, detail="DID required (I9)")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT site_id, provenance_chain, genesis_receipt FROM site_containers WHERE id = ?", (container_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Container not found (I14)")

    site_id = row["site_id"]
    existing_chain = row["provenance_chain"]
    genesis_receipt = row["genesis_receipt"]

    if not verify_site_ownership(site_id, caller_did):
        conn.close()
        raise HTTPException(status_code=403, detail="Not authorized for this container")

    # L0 filter (pass-through)
    l0_allowed, l0_log = await acceptability_l_zero(data.model_dump(exclude_none=True))
    if not l0_allowed:
        conn.close()
        raise HTTPException(status_code=400, detail=f"L0 blocked: {l0_log.get('reason')}")

    # Generate update receipt
    now = datetime.now(timezone.utc).isoformat()
    update_receipt = f"WINDI-CONTAINER-UPD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{container_id[:8].upper()}"

    # Update provenance chain
    new_chain = build_provenance_chain(existing_chain, update_receipt, [l0_log])

    # Build update query dynamically
    updates = ["provenance_chain = ?", "acceptability_layer = ?", "last_review_at = ?"]
    values = [new_chain, l0_log["layer"], now]

    for field, value in data.model_dump(exclude_none=True).items():
        if field == "config":
            updates.append(f"{field} = ?")
            values.append(json.dumps(value))
        else:
            updates.append(f"{field} = ?")
            values.append(value)

    values.append(container_id)

    cursor.execute(
        f"UPDATE site_containers SET {', '.join(updates)} WHERE id = ?",
        values
    )
    conn.commit()

    # Fetch updated container
    cursor.execute("SELECT * FROM site_containers WHERE id = ?", (container_id,))
    updated = cursor.fetchone()
    conn.close()

    # Seal update to Ledger
    content = f"{container_id}:update:{now}"
    content_hash = f"sha256:{hashlib.sha256(content.encode()).hexdigest()}"
    ledger_result = seal_to_ledger(update_receipt, "Container Update", content_hash, caller_did)

    return {
        "ok": True,
        "container": dict(updated),
        "update_receipt": update_receipt,
        "ledger": ledger_result,
        "acceptability": l0_log
    }


@sites_router.delete("/containers/{container_id}")
async def suspend_container(container_id: str, request: Request):
    """
    Suspend a container (soft delete per I11).

    Requires: DID that owns the parent site
    """
    caller_did = get_caller_did(request)
    if not caller_did:
        raise HTTPException(status_code=401, detail="DID required (I9)")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT site_id FROM site_containers WHERE id = ?", (container_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Container not found (I14)")

    site_id = row["site_id"]

    if not verify_site_ownership(site_id, caller_did):
        conn.close()
        raise HTTPException(status_code=403, detail="Not authorized for this container")

    cursor.execute(
        "UPDATE site_containers SET status = 'suspended' WHERE id = ?",
        (container_id,)
    )
    conn.commit()
    conn.close()

    return {
        "ok": True,
        "container_id": container_id,
        "status": "suspended",
        "note": "Soft delete per I11 — evidence preserved in Ledger"
    }


# ═══════════════════════════════════════════════════════════════════════════
# PROVENANCE ENDPOINT (I11)
# ═══════════════════════════════════════════════════════════════════════════

@sites_router.get("/containers/{container_id}/provenance")
async def get_provenance(container_id: str, request: Request):
    """
    Get complete provenance chain for a container.

    I11 compliance: Full audit trail of all operations.
    """
    caller_did = get_caller_did(request)
    if not caller_did:
        raise HTTPException(status_code=401, detail="DID required (I9)")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, site_id, container_type, genesis_receipt, parent_receipt, provenance_chain, created_at, sealed_at
        FROM site_containers
        WHERE id = ?
    """, (container_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Container not found (I14)")

    site_id = row["site_id"]

    if not verify_site_ownership(site_id, caller_did):
        conn.close()
        raise HTTPException(status_code=403, detail="Not authorized for this container")

    # Parse provenance chain
    chain = json.loads(row["provenance_chain"]) if row["provenance_chain"] else {"receipts": [], "acceptability_log": []}

    conn.close()

    return {
        "ok": True,
        "container_id": container_id,
        "container_type": row["container_type"],
        "genesis_receipt": row["genesis_receipt"],
        "parent_receipt": row["parent_receipt"],
        "created_at": row["created_at"],
        "sealed_at": row["sealed_at"],
        "chain": chain,
        "invariant": "I11 — Permanência de Evidência Criptográfica"
    }
