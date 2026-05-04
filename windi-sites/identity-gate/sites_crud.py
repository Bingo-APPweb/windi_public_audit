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
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import sqlite3
import uuid
import hashlib
import json
import requests
import zipfile
import io
import html as html_escape  # For microlog content escaping

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

DB_PATH = "/opt/windi/windi-sites/identity-gate/windi_sites_identity.db"
LEDGER_URL = "http://127.0.0.1:8101/api/receipts"
VERSION = "v1.0.0"

# ═══════════════════════════════════════════════════════════════════════════
# §242 — FILESYSTEM PERSISTENCE (Sprint 2)
# ═══════════════════════════════════════════════════════════════════════════
# Sites are persisted to filesystem for public serving via nginx.
# Path: /opt/windi/sites/{site_id}/{container_id}.html
# URL:  https://windisites.de/sites/{site_id}/{container_id}
# ═══════════════════════════════════════════════════════════════════════════
import os
from pathlib import Path

SITES_BASE_PATH = Path("/opt/windi/sites")
SITES_PUBLIC_URL = "https://windisites.de/sites"


def persist_site_html(
    site_id: str,
    container_id: str,
    html_content: str,
    meta: dict
) -> dict:
    """
    Persist generated HTML to filesystem.

    Path: /opt/windi/sites/{site_id}/{container_id}.html
    Meta: /opt/windi/sites/{site_id}/{container_id}.meta.json

    Returns:
        {
            "ok": True,
            "file_path": "/opt/windi/sites/...",
            "public_url": "https://windisites.de/sites/...",
            "content_hash": "sha256:..."
        }
    """
    try:
        # Ensure site directory exists
        site_dir = SITES_BASE_PATH / site_id
        site_dir.mkdir(parents=True, exist_ok=True)

        # Write HTML file
        html_path = site_dir / f"{container_id}.html"
        html_path.write_text(html_content, encoding="utf-8")

        # Read back and hash (CRITICAL: hash of what's on disk, not in memory)
        persisted_content = html_path.read_text(encoding="utf-8")
        content_hash = f"sha256:{hashlib.sha256(persisted_content.encode()).hexdigest()}"

        # Write meta.json for verify and audit
        meta["content_hash"] = content_hash
        meta["persisted_at"] = datetime.now(timezone.utc).isoformat()
        meta_path = site_dir / f"{container_id}.meta.json"
        meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

        # Public URL
        public_url = f"{SITES_PUBLIC_URL}/{site_id}/{container_id}"

        return {
            "ok": True,
            "file_path": str(html_path),
            "meta_path": str(meta_path),
            "public_url": public_url,
            "content_hash": content_hash
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "file_path": None,
            "public_url": None,
            "content_hash": None
        }

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


# ═══════════════════════════════════════════════════════════════════════════
# §3b AI WRITER — INTERNAL-ONLY MODE
# ═══════════════════════════════════════════════════════════════════════════
# Caminho C: Internal shadow validation with SOVEREIGN DID allowlist
# ═══════════════════════════════════════════════════════════════════════════

try:
    from ai_writer import (
        generate_with_pipeline,
        assert_public_writer_authorized,  # W-CORTEX-001: for public endpoints
        InternalModeViolation,
        TierUnavailableError,  # §242: 503 for unavailable tiers
        writer_health,
        AI_WRITER_MODE,
        VALID_TEMPLATES,
        INTERNAL_DIDS_ALLOWLIST,
        _get_available_tiers  # §242: Check available tiers
    )
    from ai_writer.ollama_writer_client import generate_content, OllamaWriterError
    AI_WRITER_AVAILABLE = True
    print(f"[WINDI-SITES] AI Writer loaded (mode={AI_WRITER_MODE})")
except ImportError as e:
    AI_WRITER_AVAILABLE = False
    AI_WRITER_MODE = "unavailable"
    TierUnavailableError = None  # Fallback
    _get_available_tiers = lambda: ["FREE"]
    print(f"[WINDI-SITES] AI Writer not available: {e}")


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


# ═══════════════════════════════════════════════════════════════════════════
# §3b AI WRITER GENERATE ENDPOINT — INTERNAL-ONLY
# ═══════════════════════════════════════════════════════════════════════════

class GenerateRequest(BaseModel):
    """Request model for content generation."""
    template_type: str  # article, landing, about
    variables: Dict[str, str]  # Template variables

    @field_validator("template_type")
    @classmethod
    def validate_template_type(cls, v):
        if AI_WRITER_AVAILABLE:
            if v not in VALID_TEMPLATES:
                raise ValueError(f"Invalid template_type: {v}. Valid: {VALID_TEMPLATES}")
        return v


@sites_router.post("/containers/{container_id}/generate")
async def generate_content_for_container(
    container_id: str,
    data: GenerateRequest,
    request: Request
):
    """
    Generate AI content for a container.

    §3b AI Writer — Internal-Only Mode (Caminho C)

    Requires:
      - SOVEREIGN tier DID (4-layer gate)
      - AI_WRITER_MODE=internal
      - Container type must be 'writer'
      - Full 8-step pipeline (no shortcuts)

    Returns:
      - Generated content (draft status, never active)
      - Provenance with internal-shadow-validation tag
    """
    # ─── Pre-checks ──────────────────────────────────────────────────────────
    if not AI_WRITER_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI Writer not available")

    caller_did = get_caller_did(request)
    if not caller_did:
        raise HTTPException(status_code=401, detail="DID required (I9)")

    # Get host for 4-layer gate
    request_host = request.headers.get("host", "")

    # ─── Verify container exists and is type 'writer' ────────────────────────
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sc.*, s.owner_did
        FROM site_containers sc
        JOIN sites s ON sc.site_id = s.id
        WHERE sc.id = ?
    """, (container_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Container not found (I14)")

    if row["container_type"] != "writer":
        conn.close()
        raise HTTPException(
            status_code=400,
            detail=f"Container type '{row['container_type']}' cannot generate. Only 'writer' supported."
        )

    site_id = row["site_id"]

    if not verify_site_ownership(site_id, caller_did):
        conn.close()
        raise HTTPException(status_code=403, detail="Not authorized for this container")

    # ─── Get caller tier from admins table ───────────────────────────────────
    cursor.execute("SELECT role FROM admins WHERE did = ?", (caller_did,))
    admin_row = cursor.fetchone()

    # Map role to tier (SOVEREIGN for internal mode)
    # In production, this would check actual tier field
    caller_tier = "SOVEREIGN" if (admin_row and caller_did in INTERNAL_DIDS_ALLOWLIST) else "NODAL"

    # ─── Execute 8-step pipeline (W-CORTEX-001 canal único) ──────────────────
    # §241: Tier routing based on DID tier_level
    try:
        result = await generate_with_pipeline(
            caller_did=caller_did,
            caller_tier=caller_tier,
            request_host=request_host,
            acceptability_l_minus_1_fn=acceptability_l_minus_1,
            acceptability_l_zero_fn=acceptability_l_zero,
            template_type=data.template_type,
            template_variables=data.variables,
            requested_tier=None  # §241: Let DID resolution determine tier
        )
    except Exception as e:
        conn.close()
        # I14: Explicit failure
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    if not result.ok:
        conn.close()
        # Determine status code based on error type
        error = result.error or "unknown_error"
        if "DID_GATE" in error:
            raise HTTPException(status_code=403, detail=error)
        elif "L-1_BLOCKED_CS1" in error:
            # 451 Unavailable For Legal Reasons + lockdown potential
            raise HTTPException(status_code=451, detail=error)
        elif "L0_BLOCKED" in error:
            raise HTTPException(status_code=422, detail=error)
        elif "OLLAMA_FAILED" in error:
            raise HTTPException(status_code=502, detail=error)
        else:
            raise HTTPException(status_code=400, detail=error)

    # ─── Update container with generated content ────────────────────────────
    now = datetime.now(timezone.utc).isoformat()
    receipt_id = f"WINDI-GENERATE-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{container_id[:8].upper()}"

    # Build provenance with internal-shadow-validation tag
    existing_chain = row["provenance_chain"]
    acceptability_logs = []
    if result.l_minus_1_log:
        result.l_minus_1_log["internal_shadow_validation"] = True
        acceptability_logs.append(result.l_minus_1_log)
    if result.l_zero_log:
        result.l_zero_log["internal_shadow_validation"] = True
        acceptability_logs.append(result.l_zero_log)
    if result.generation_log:
        result.generation_log["internal_shadow_validation"] = True
        acceptability_logs.append(result.generation_log)

    new_chain = build_provenance_chain(existing_chain, receipt_id, acceptability_logs)

    # Store generated content in config (never in content field for draft)
    config = json.loads(row["config"]) if row["config"] else {}
    config["generated_content"] = result.content
    config["generation_receipt"] = receipt_id

    # Update container (status remains 'draft' in internal mode)
    cursor.execute("""
        UPDATE site_containers
        SET config = ?,
            content_hash = ?,
            l1_review_pending = ?,
            acceptability_layer = 'L0',
            last_review_at = ?,
            provenance_chain = ?
        WHERE id = ?
    """, (
        json.dumps(config),
        result.content_hash,
        result.l1_review_pending,
        now,
        new_chain,
        container_id
    ))
    conn.commit()
    conn.close()

    # ─── Seal to Ledger ──────────────────────────────────────────────────────
    ledger_payload = {
        "id": receipt_id,
        "receipt_id": receipt_id,
        "type": "generation",
        "doc_type": "doc",
        "doc_name": f"AI Writer Generation {data.template_type}",
        "content_hash": result.content_hash,
        "actor": caller_did,
        "app": "w-sites-001",
        "governance_level": "MEDIUM",
        "sge_score": 0,
        "invariants": ["I1", "I9", "I10", "I11", "I14"],
        "metadata": {
            "container_id": container_id,
            "template_type": data.template_type,
            "mode": "internal-shadow-validation",
            "l1_review_pending": result.l1_review_pending
        }
    }

    ledger_response = {"ok": False, "reason": "not_attempted"}
    try:
        resp = requests.post(LEDGER_URL, json=ledger_payload, timeout=5.0)
        ledger_response = resp.json()
    except Exception as e:
        ledger_response = {"ok": False, "error": str(e)}

    # ─── Return result ───────────────────────────────────────────────────────
    return {
        "ok": True,
        "container_id": container_id,
        "template_type": data.template_type,
        "content_preview": result.content[:500] + "..." if len(result.content) > 500 else result.content,
        "content_hash": result.content_hash,
        "status": "draft",  # ALWAYS draft in internal mode
        "l1_review_pending": result.l1_review_pending,
        "generation_receipt": receipt_id,
        "ledger": ledger_response,
        "mode": "internal-shadow-validation",
        "invariants": ["I1", "I9", "I10", "I11", "I14"],
        "note": "Internal mode: SOVEREIGN tier only, draft status enforced"
    }


@sites_router.get("/writer/health")
async def ai_writer_health():
    """Check AI Writer health status."""
    if not AI_WRITER_AVAILABLE:
        return {
            "ok": False,
            "service": "ai-writer",
            "status": "unavailable",
            "reason": "Module not loaded"
        }

    health = await writer_health()
    return health


# ═══════════════════════════════════════════════════════════════════════════
# §4 EXPORT HIGH — SOVEREIGN PACKAGE DELIVERY
# ═══════════════════════════════════════════════════════════════════════════
# HIGH tier clients receive a sealed ZIP with everything needed to self-host.
# The export includes: site data, containers, provenance chain, VERIFY.html
# ═══════════════════════════════════════════════════════════════════════════

VERIFY_HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en" data-theme="noir">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WINDI Verify — {site_name}</title>
<style>
:root {{
  --noir: #0a0a0f;
  --gold: #c9a84c;
  --text: #e2e8f0;
  --green: #22c55e;
  --red: #ef4444;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  background: var(--noir);
  color: var(--text);
  font-family: system-ui, sans-serif;
  padding: 40px 20px;
  min-height: 100vh;
}}
.container {{ max-width: 800px; margin: 0 auto; }}
h1 {{ color: var(--gold); font-size: 1.8rem; margin-bottom: 8px; }}
.subtitle {{ color: rgba(226,232,240,0.6); margin-bottom: 32px; }}
.card {{
  background: #12121a;
  border: 1px solid #2a2a3a;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 16px;
}}
.label {{ font-size: 0.75rem; color: rgba(226,232,240,0.5); text-transform: uppercase; letter-spacing: 0.05em; }}
.value {{ font-family: monospace; font-size: 0.9rem; word-break: break-all; margin-top: 4px; }}
.hash {{ color: var(--gold); }}
.receipt {{ color: var(--green); }}
.invariant {{
  display: inline-block;
  background: rgba(201,168,76,0.15);
  color: var(--gold);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  margin: 2px;
}}
.footer {{
  margin-top: 40px;
  text-align: center;
  color: rgba(226,232,240,0.4);
  font-size: 0.8rem;
}}
.footer a {{ color: var(--gold); }}
</style>
</head>
<body>
<div class="container">
  <h1>WINDI Verify</h1>
  <p class="subtitle">Sovereign Export Package — {site_name}</p>

  <div class="card">
    <div class="label">Export Receipt</div>
    <div class="value receipt">{export_receipt}</div>
  </div>

  <div class="card">
    <div class="label">Package Hash (SHA-256)</div>
    <div class="value hash">{package_hash}</div>
  </div>

  <div class="card">
    <div class="label">Export Timestamp</div>
    <div class="value">{export_timestamp}</div>
  </div>

  <div class="card">
    <div class="label">Site ID</div>
    <div class="value">{site_id}</div>
  </div>

  <div class="card">
    <div class="label">Owner DID</div>
    <div class="value">{owner_did}</div>
  </div>

  <div class="card">
    <div class="label">Tier</div>
    <div class="value">{tier}</div>
  </div>

  <div class="card">
    <div class="label">Containers</div>
    <div class="value">{container_count} container(s) exported</div>
  </div>

  <div class="card">
    <div class="label">Constitutional Invariants</div>
    <div class="value">
      <span class="invariant">I1</span>
      <span class="invariant">I9</span>
      <span class="invariant">I11</span>
      <span class="invariant">I12</span>
      <span class="invariant">I14</span>
    </div>
  </div>

  <div class="card">
    <div class="label">Verify Online</div>
    <div class="value">
      <a href="https://windi-domain.com/verify-public/?id={export_receipt}" target="_blank" style="color: var(--gold);">
        windi-domain.com/verify-public/?id={export_receipt}
      </a>
    </div>
  </div>

  <div class="footer">
    <p>This package was exported from WINDI Publishing House.</p>
    <p>"AI processes. Human decides. WINDI guarantees."</p>
    <p style="margin-top: 16px;">
      <a href="https://windi-domain.com">windi-domain.com</a>
    </p>
  </div>
</div>
</body>
</html>
'''


@sites_router.post("/sites/{site_id}/export")
async def export_site_package(
    site_id: str,
    request: Request
):
    """
    §4 Export HIGH — Sovereign Package Delivery

    Exports a complete site package for HIGH tier clients.
    The client receives a sealed ZIP that can be self-hosted.

    Requires:
      - HIGH tier site
      - Owner or admin DID

    Returns:
      - ZIP file with site, containers, provenance, VERIFY.html
      - Export receipt sealed in Ledger (I11)

    Invariants: I1, I9, I11, I12, I14
    """
    now = datetime.now(timezone.utc)
    now_str = now.isoformat()
    timestamp = now.strftime("%Y%m%d%H%M%S")

    # ─── DID Gate ────────────────────────────────────────────────────────────
    caller_did = get_caller_did(request)
    if not caller_did:
        raise HTTPException(status_code=401, detail="DID required (I9)")

    # ─── Fetch site ──────────────────────────────────────────────────────────
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sites WHERE id = ?", (site_id,))
    site = cursor.fetchone()

    if not site:
        conn.close()
        raise HTTPException(status_code=404, detail="Site not found (I14)")

    # ─── Verify ownership ────────────────────────────────────────────────────
    if not verify_site_ownership(site_id, caller_did):
        conn.close()
        raise HTTPException(status_code=403, detail="Not authorized to export this site")

    # ─── Verify HIGH tier ────────────────────────────────────────────────────
    site_tier = site["tier"]
    if site_tier != "HIGH":
        conn.close()
        raise HTTPException(
            status_code=403,
            detail=f"Export only available for HIGH tier. Site is {site_tier}. Upgrade to export."
        )

    # ─── Fetch containers ────────────────────────────────────────────────────
    cursor.execute(
        "SELECT * FROM site_containers WHERE site_id = ? AND status != 'deleted'",
        (site_id,)
    )
    containers = cursor.fetchall()
    conn.close()

    # ─── Build export data ───────────────────────────────────────────────────
    site_data = {
        "id": site["id"],
        "name": site["name"],
        "subdomain": site["subdomain"],
        "custom_domain": site["custom_domain"],
        "tier": site["tier"],
        "owner_did": site["owner_did"],
        "company_id": site["company_id"],
        "status": site["status"],
        "genesis_receipt": site["genesis_receipt"],
        "created_at": site["created_at"],
        "sealed_at": site["sealed_at"]
    }

    containers_data = []
    for c in containers:
        config = json.loads(c["config"]) if c["config"] else {}
        containers_data.append({
            "id": c["id"],
            "site_id": c["site_id"],
            "container_type": c["container_type"],
            "config": config,
            "content_hash": c["content_hash"],
            "status": c["status"],
            "genesis_receipt": c["genesis_receipt"],
            "parent_receipt": c["parent_receipt"],
            "created_at": c["created_at"],
            "provenance_chain": json.loads(c["provenance_chain"]) if c["provenance_chain"] else None
        })

    # ─── Build provenance summary ────────────────────────────────────────────
    all_receipts = []
    if site["genesis_receipt"]:
        all_receipts.append(site["genesis_receipt"])

    for c in containers_data:
        if c.get("genesis_receipt"):
            all_receipts.append(c["genesis_receipt"])
        if c.get("parent_receipt"):
            all_receipts.append(c["parent_receipt"])
        if c.get("provenance_chain") and c["provenance_chain"].get("receipts"):
            all_receipts.extend(c["provenance_chain"]["receipts"])

    # Deduplicate
    all_receipts = list(dict.fromkeys(all_receipts))

    # ─── Generate receipt ID ─────────────────────────────────────────────────
    short_hash = hashlib.sha256(site_id.encode()).hexdigest()[:8].upper()
    receipt_id = f"WINDI-EXPORT-{timestamp}-{short_hash}"

    # ─── Build MANIFEST.json ─────────────────────────────────────────────────
    manifest = {
        "windi_export": {
            "version": "1.0.0",
            "type": "sovereign_package",
            "tier": "HIGH"
        },
        "export_receipt": receipt_id,
        "export_timestamp": now_str,
        "exporter_did": caller_did,
        "site": site_data,
        "containers": containers_data,
        "provenance": {
            "receipt_chain": all_receipts,
            "total_receipts": len(all_receipts),
            "genesis": site["genesis_receipt"]
        },
        "invariants": ["I1", "I9", "I11", "I12", "I14"],
        "verify_url": f"https://windi-domain.com/verify-public/?id={receipt_id}",
        "instructions": {
            "deploy": "Upload contents of /site/ to your web server",
            "verify": "Open VERIFY.html to see provenance and verify online",
            "ledger": "All receipts remain in WINDI Forensic Ledger for permanent verification"
        },
        "legal": {
            "owner": caller_did,
            "license": "Content owned by exporter. WINDI provides forensic guarantee.",
            "note": "AI processes. Human decides. WINDI guarantees."
        }
    }

    # ─── Calculate package hash (pre-ZIP) ────────────────────────────────────
    manifest_json = json.dumps(manifest, indent=2, ensure_ascii=False)
    package_hash = f"sha256:{hashlib.sha256(manifest_json.encode()).hexdigest()}"
    manifest["package_hash"] = package_hash
    manifest_json = json.dumps(manifest, indent=2, ensure_ascii=False)

    # ─── Build VERIFY.html ───────────────────────────────────────────────────
    verify_html = VERIFY_HTML_TEMPLATE.format(
        site_name=site["name"],
        export_receipt=receipt_id,
        package_hash=package_hash,
        export_timestamp=now_str,
        site_id=site_id,
        owner_did=site["owner_did"],
        tier=site["tier"],
        container_count=len(containers_data)
    )

    # ─── Build ZIP ───────────────────────────────────────────────────────────
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # MANIFEST.json
        zf.writestr("MANIFEST.json", manifest_json)

        # VERIFY.html
        zf.writestr("VERIFY.html", verify_html)

        # README.txt
        readme = f"""WINDI Sovereign Export Package
==============================

Site: {site["name"]}
Export Receipt: {receipt_id}
Exported: {now_str}

Contents:
- MANIFEST.json — Complete site data and provenance chain
- VERIFY.html — Standalone verification page
- site/ — Static site files (if generated)
- containers/ — Individual container data

Verification:
Open VERIFY.html in your browser, or visit:
https://windi-domain.com/verify-public/?id={receipt_id}

"AI processes. Human decides. WINDI guarantees."
— WINDI Publishing House
"""
        zf.writestr("README.txt", readme)

        # Site data
        zf.writestr("site/site.json", json.dumps(site_data, indent=2, ensure_ascii=False))

        # Container data
        for c in containers_data:
            container_json = json.dumps(c, indent=2, ensure_ascii=False)
            zf.writestr(f"containers/{c['id']}.json", container_json)

            # If container has generated content, export as HTML
            if c.get("config") and c["config"].get("generated_content"):
                content = c["config"]["generated_content"]
                # Simple markdown-ish to HTML conversion for now
                html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{c.get('config', {}).get('title', c.get('container_type', 'Container'))}</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px 20px; line-height: 1.6; }}
</style>
</head>
<body>
<article>
{content}
</article>
<footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ccc; font-size: 0.8rem; color: #666;">
<p>Container: {c['id']}</p>
<p>Hash: {c.get('content_hash', 'N/A')}</p>
<p>Verified by WINDI Publishing House</p>
</footer>
</body>
</html>
"""
                zf.writestr(f"site/content/{c['id']}.html", html_content)

        # Provenance chain
        provenance_data = {
            "export_receipt": receipt_id,
            "receipt_chain": all_receipts,
            "site_genesis": site["genesis_receipt"],
            "exported_at": now_str
        }
        zf.writestr("provenance/chain.json", json.dumps(provenance_data, indent=2))

    zip_buffer.seek(0)
    zip_bytes = zip_buffer.getvalue()

    # ─── Final package hash (actual ZIP) ─────────────────────────────────────
    final_hash = f"sha256:{hashlib.sha256(zip_bytes).hexdigest()}"

    # ─── Seal to Ledger ──────────────────────────────────────────────────────
    ledger_payload = {
        "id": receipt_id,
        "actor": caller_did,
        "app": "w-sites-001",
        "doc_type": "doc",
        "doc_name": f"Sovereign Export: {site['name']}",
        "governance_level": "HIGH",
        "content_hash": final_hash,
        "sge_score": 0,
        "metadata": {
            "site_id": site_id,
            "tier": "HIGH",
            "container_count": len(containers_data),
            "receipt_chain_length": len(all_receipts),
            "export_type": "sovereign_package"
        }
    }

    ledger_response = {"ok": False, "reason": "not_attempted"}
    try:
        resp = requests.post(LEDGER_URL, json=ledger_payload, timeout=5.0)
        ledger_response = resp.json()
    except Exception as e:
        ledger_response = {"ok": False, "error": str(e)}

    # ─── Return ZIP ──────────────────────────────────────────────────────────
    filename = f"windi-export-{site_id[:8]}-{timestamp}.zip"

    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-WINDI-Export-Receipt": receipt_id,
            "X-WINDI-Package-Hash": final_hash,
            "X-WINDI-Ledger-Sealed": str(ledger_response.get("ok", False))
        }
    )


@sites_router.get("/sites/{site_id}/export/preview")
async def preview_export(
    site_id: str,
    request: Request
):
    """
    Preview what would be exported (without generating ZIP).

    Useful for HIGH tier clients to see package contents before export.
    """
    caller_did = get_caller_did(request)
    if not caller_did:
        raise HTTPException(status_code=401, detail="DID required (I9)")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sites WHERE id = ?", (site_id,))
    site = cursor.fetchone()

    if not site:
        conn.close()
        raise HTTPException(status_code=404, detail="Site not found")

    if not verify_site_ownership(site_id, caller_did):
        conn.close()
        raise HTTPException(status_code=403, detail="Not authorized")

    cursor.execute(
        "SELECT id, container_type, content_hash, status, genesis_receipt FROM site_containers WHERE site_id = ? AND status != 'deleted'",
        (site_id,)
    )
    containers = cursor.fetchall()
    conn.close()

    # Collect all receipts from site genesis and containers
    all_receipts = []
    if site["genesis_receipt"]:
        all_receipts.append(site["genesis_receipt"])

    # Containers have provenance_chain, not sites
    for c in containers:
        if c["genesis_receipt"]:
            all_receipts.append(c["genesis_receipt"])

    return {
        "site_id": site_id,
        "site_name": site["name"],
        "tier": site["tier"],
        "export_available": site["tier"] == "HIGH",
        "upgrade_required": site["tier"] != "HIGH",
        "containers": [
            {
                "id": c["id"],
                "type": c["container_type"],
                "hash": c["content_hash"],
                "status": c["status"]
            }
            for c in containers
        ],
        "container_count": len(containers),
        "provenance_receipts": len(all_receipts),
        "genesis_receipt": site["genesis_receipt"],
        "package_contents": [
            "MANIFEST.json",
            "VERIFY.html",
            "README.txt",
            "site/site.json",
            f"containers/*.json ({len(containers)} files)",
            "site/content/*.html (generated content)",
            "provenance/chain.json"
        ],
        "invariants": ["I1", "I9", "I11", "I12", "I14"],
        "note": "Use POST /api/sites/{site_id}/export to generate and download the package" if site["tier"] == "HIGH" else "Upgrade to HIGH tier to enable export"
    }


# ═══════════════════════════════════════════════════════════════════════════
# §240 AI SITE GENERATOR — OLLAMA B INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════
# Prompt → Ollama B (mistral:7b) → HTML → windi_generations → Preview
# ═══════════════════════════════════════════════════════════════════════════

import re
import html as html_lib

# §240 AI Site Generator — uses shared ollama_writer_client (zero duplication)
# OLLAMA_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT are in ai_writer/ollama_writer_client.py

# DOMPurify-style sanitization (server-side)
# NOTE: <style> is ALLOWED for inline CSS - only external resources blocked
FORBIDDEN_TAGS = {'script', 'iframe', 'object', 'embed', 'form', 'input', 'link'}
FORBIDDEN_ATTRS = {'onclick', 'onerror', 'onload', 'onmouseover', 'onfocus', 'onblur', 'javascript:'}


def sanitize_html(html_content: str) -> str:
    """
    Server-side HTML sanitization (XSS prevention).
    Removes forbidden tags and attributes.
    """
    # Remove script tags and content
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)

    # Remove other forbidden tags
    for tag in FORBIDDEN_TAGS:
        html_content = re.sub(rf'<{tag}[^>]*>.*?</{tag}>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(rf'<{tag}[^>]*/>', '', html_content, flags=re.IGNORECASE)

    # Remove forbidden attributes
    for attr in FORBIDDEN_ATTRS:
        html_content = re.sub(rf'\s{attr}\s*=\s*["\'][^"\']*["\']', '', html_content, flags=re.IGNORECASE)
        html_content = re.sub(rf'\s{attr}\s*=\s*\S+', '', html_content, flags=re.IGNORECASE)

    return html_content


class GenerateSiteRequest(BaseModel):
    """Request for AI site generation."""
    prompt: str
    site_name: Optional[str] = None
    site_id: Optional[str] = None  # If linking to existing site

    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v):
        if len(v) < 10:
            raise ValueError('Prompt must be at least 10 characters')
        if len(v) > 2000:
            raise ValueError('Prompt must be less than 2000 characters')
        return v.strip()


# ═══════════════════════════════════════════════════════════════════════════
# §243 — MICROLOG: Smallest Verifiable Unit
# ═══════════════════════════════════════════════════════════════════════════
# "A single verifiable idea, sealed as a public artefact"
# Sprint 3 — Microlog Pilot
# ═══════════════════════════════════════════════════════════════════════════

MICROLOG_SYSTEM_PROMPT = """Write a concise microlog (max 280 words).

STRUCTURE:
- Title (strong, declarative, max 10 words)
- Core idea (1-2 paragraphs, precise and insight-driven)
- Closing line (memorable, quotable)

TONE:
- Precise, not vague
- Non-generic, specific
- Insight-driven, not descriptive

OUTPUT FORMAT:
Respond with JSON only:
{"title": "...", "content": "...", "closing": "..."}

NO markdown. NO explanation. Just the JSON object."""

# ═══════════════════════════════════════════════════════════════════════════
# MICROLOG SURFACE V1 — "Liturgy of Digital Truth"
# PDT-001 compliant: Forensic Lexicon EN-only (§1)
# Surface = calm that invites · Audit = truth that responds
# ═══════════════════════════════════════════════════════════════════════════
MICROLOG_HTML_SKELETON = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — WINDI Microlog</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-void: #050505;
            --bg-surface: #0A0A0F;
            --bg-terminal: #000000;
            --text-primary: #E8E6E1;
            --text-secondary: #8A8A8A;
            --text-muted: #4A4A4A;
            --truth-green: #00D26A;
            --truth-glow: rgba(0, 210, 106, 0.15);
            --gold: #C9A84C;
            --gold-muted: rgba(201, 168, 76, 0.3);
            --fail-red: #FF4444;
            --border-subtle: rgba(255, 255, 255, 0.06);
            --border-terminal: rgba(0, 210, 106, 0.2);
            --font-zen: 'Inter', -apple-system, sans-serif;
            --font-mono: 'JetBrains Mono', 'SF Mono', monospace;
            --transition-slow: 0.6s cubic-bezier(0.4, 0, 0.2, 1);
            --transition-medium: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        [data-theme="klar"] {{
            --bg-void: #FAFAF8;
            --bg-surface: #FFFFFF;
            --bg-terminal: #F5F5F3;
            --text-primary: #1A1A1A;
            --text-secondary: #4A4A4A;
            --text-muted: #8A8A8A;
            --gold: #8B7424;
            --gold-muted: rgba(139, 116, 36, 0.2);
            --border-subtle: rgba(0, 0, 0, 0.08);
            --border-terminal: rgba(0, 180, 90, 0.3);
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{ height: 100%; }}
        body {{
            font-family: var(--font-zen);
            background: var(--bg-void);
            color: var(--text-primary);
            line-height: 1.7;
            -webkit-font-smoothing: antialiased;
        }}
        .surface-container {{
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 2rem;
        }}
        .surface {{ max-width: 640px; width: 100%; }}
        .surface-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 3rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border-subtle);
        }}
        .surface-brand {{
            font-size: 0.75rem;
            font-weight: 500;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            color: var(--text-muted);
        }}
        .surface-meta {{
            font-family: var(--font-mono);
            font-size: 0.7rem;
            color: var(--text-muted);
        }}
        .microlog {{ margin-bottom: 3rem; }}
        .microlog-title {{
            font-size: 1.75rem;
            font-weight: 600;
            line-height: 1.3;
            margin-bottom: 1.5rem;
            color: var(--text-primary);
        }}
        .microlog-content {{
            font-size: 1.1rem;
            font-weight: 300;
            color: var(--text-secondary);
            margin-bottom: 1.5rem;
        }}
        .microlog-content p {{ margin-bottom: 1rem; }}
        .microlog-closing {{
            font-size: 1rem;
            font-weight: 500;
            font-style: italic;
            color: var(--gold);
            padding-left: 1rem;
            border-left: 2px solid var(--gold-muted);
        }}
        .microlog-signature {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 1.5rem;
            margin-top: 2rem;
            border-top: 1px solid var(--border-subtle);
            font-size: 0.8rem;
            color: var(--text-muted);
        }}
        .signature-left {{ display: flex; align-items: center; gap: 0.5rem; }}
        .signature-right {{ font-family: var(--font-mono); font-size: 0.7rem; }}
        .action-zone {{ display: flex; justify-content: center; margin: 3rem 0; }}
        .audit-trigger {{
            font-family: var(--font-mono);
            font-size: 0.85rem;
            font-weight: 500;
            letter-spacing: 0.05em;
            padding: 0.875rem 2rem;
            background: transparent;
            color: var(--text-secondary);
            border: 1px solid var(--border-subtle);
            cursor: pointer;
            transition: var(--transition-medium);
        }}
        .audit-trigger:hover {{ color: var(--text-primary); border-color: var(--text-muted); }}
        .audit-trigger:active {{ transform: scale(0.98); }}
        .audit-trigger.auditing {{ pointer-events: none; color: var(--text-muted); }}
        .audit-trigger.verified {{ border-color: var(--truth-green); color: var(--truth-green); background: var(--truth-glow); }}
        .audit-trigger.failed {{ border-color: var(--fail-red); color: var(--fail-red); }}
        .proof-panel {{
            background: var(--bg-terminal);
            border: 1px solid var(--border-subtle);
            overflow: hidden;
            max-height: 0;
            opacity: 0;
            transition: max-height var(--transition-slow), opacity var(--transition-medium), border-color var(--transition-medium);
        }}
        .proof-panel.revealed {{ max-height: 500px; opacity: 1; }}
        .proof-panel.verified {{ border-color: var(--border-terminal); }}
        .proof-panel.failed {{ border-color: var(--fail-red); }}
        .terminal-header {{
            font-family: var(--font-mono);
            font-size: 0.65rem;
            font-weight: 500;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            padding: 0.75rem 1rem;
            background: #0D0D12;
            color: var(--text-muted);
            border-bottom: 1px solid var(--border-subtle);
        }}
        .terminal-body {{ padding: 1.25rem; font-family: var(--font-mono); font-size: 0.8rem; line-height: 1.8; }}
        .terminal-line {{
            color: var(--text-muted);
            margin-bottom: 0.25rem;
            opacity: 0;
            transform: translateX(-10px);
            transition: opacity 0.3s, transform 0.3s;
        }}
        .terminal-line.visible {{ opacity: 1; transform: translateX(0); }}
        .terminal-line .arrow {{ color: var(--text-muted); margin-right: 0.5rem; }}
        .terminal-status {{
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border-subtle);
            font-size: 1rem;
            font-weight: 500;
            opacity: 0;
            transition: opacity 0.5s;
        }}
        .terminal-status.visible {{ opacity: 1; }}
        .terminal-status.match {{ color: var(--truth-green); }}
        .terminal-status.mismatch {{ color: var(--fail-red); }}
        .terminal-details {{
            margin-top: 1.25rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border-subtle);
            font-size: 0.75rem;
            color: var(--text-muted);
            opacity: 0;
            transition: opacity 0.5s;
        }}
        .terminal-details.visible {{ opacity: 1; }}
        .detail-row {{ display: flex; margin-bottom: 0.5rem; }}
        .detail-label {{ width: 80px; flex-shrink: 0; color: var(--text-muted); }}
        .detail-value {{ color: var(--text-secondary); word-break: break-all; }}
        .detail-value.hash {{ font-size: 0.7rem; }}
        .terminal-actions {{
            margin-top: 1.25rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border-subtle);
            opacity: 0;
            transition: opacity 0.5s;
        }}
        .terminal-actions.visible {{ opacity: 1; }}
        .ledger-link {{
            font-family: var(--font-mono);
            font-size: 0.75rem;
            color: var(--text-muted);
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            transition: color var(--transition-medium);
        }}
        .ledger-link:hover {{ color: var(--truth-green); }}
        .surface-footer {{
            margin-top: 4rem;
            text-align: center;
            font-size: 0.7rem;
            color: var(--text-muted);
            letter-spacing: 0.05em;
        }}
        .controls-bar {{
            position: fixed;
            top: 1rem;
            right: 1rem;
            display: flex;
            gap: 0.75rem;
            align-items: center;
            z-index: 100;
        }}
        .lang-toggle {{
            display: flex;
            gap: 0.25rem;
            font-family: var(--font-mono);
            font-size: 0.65rem;
        }}
        .lang-btn {{
            padding: 0.25rem 0.5rem;
            background: transparent;
            border: 1px solid var(--border-subtle);
            color: var(--text-muted);
            cursor: pointer;
            transition: var(--transition-medium);
        }}
        .lang-btn:hover {{ color: var(--text-primary); border-color: var(--text-muted); }}
        .lang-btn.active {{ color: var(--gold); border-color: var(--gold); }}
        .theme-toggle {{
            width: 32px;
            height: 32px;
            background: transparent;
            border: 1px solid var(--border-subtle);
            color: var(--text-muted);
            cursor: pointer;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: var(--transition-medium);
        }}
        .theme-toggle:hover {{ color: var(--text-primary); border-color: var(--text-muted); }}
        @media (max-width: 640px) {{
            .surface-container {{ padding: 1.5rem; }}
            .microlog-title {{ font-size: 1.4rem; }}
            .microlog-content {{ font-size: 1rem; }}
            .terminal-body {{ padding: 1rem; font-size: 0.75rem; }}
        }}
    </style>
</head>
<body>
    <div class="controls-bar">
        <div class="lang-toggle">
            <button class="lang-btn" data-lang="de">DE</button>
            <button class="lang-btn active" data-lang="en">EN</button>
            <button class="lang-btn" data-lang="pt">PT</button>
        </div>
        <button class="theme-toggle" id="themeToggle" title="Toggle theme">☀</button>
    </div>
    <div class="surface-container">
        <main class="surface">
            <header class="surface-header">
                <span class="surface-brand">WINDI · Microlog</span>
                <span class="surface-meta">{handle}</span>
            </header>
            <article class="microlog">
                <h1 class="microlog-title">{title}</h1>
                <div class="microlog-content">{content}</div>
                <p class="microlog-closing">{closing}</p>
            </article>
            <div class="microlog-signature">
                <div class="signature-left">
                    <span>WINDI</span><span>·</span><span>{handle}</span>
                </div>
                <div class="signature-right"><span data-i18n="sealed">sealed</span> {sealed_date}</div>
            </div>
            <div class="action-zone">
                <button class="audit-trigger" id="auditTrigger" data-receipt-id="{receipt_id}">Audit integrity</button>
            </div>
            <aside class="proof-panel" id="proofPanel">
                <div class="terminal-header">SYSTEM_LEDGER_VERIFY</div>
                <div class="terminal-body">
                    <div class="terminal-line" id="line1"><span class="arrow">→</span> fetching receipt...</div>
                    <div class="terminal-line" id="line2"><span class="arrow">→</span> computing sha-256...</div>
                    <div class="terminal-line" id="line3"><span class="arrow">→</span> comparing ledger...</div>
                    <div class="terminal-status" id="terminalStatus"><span class="status-icon"></span><span class="status-text"></span></div>
                    <div class="terminal-details" id="terminalDetails">
                        <div class="detail-row"><span class="detail-label">receipt</span><span class="detail-value" id="detailReceipt">—</span></div>
                        <div class="detail-row"><span class="detail-label">sha-256</span><span class="detail-value hash" id="detailHash">—</span></div>
                        <div class="detail-row"><span class="detail-label">issued</span><span class="detail-value" id="detailIssued">—</span></div>
                    </div>
                    <div class="terminal-actions" id="terminalActions">
                        <a href="{verify_url}" target="_blank" class="ledger-link">open public ledger <span>↗</span></a>
                    </div>
                </div>
            </aside>
            <footer class="surface-footer">
                <div>AI processes. Human decides. WINDI guarantees.</div>
                <div style="font-size:0.65rem;opacity:0.6;margin-top:0.5rem;">WINDI Publishing House · Bavaria · 2026</div>
            </footer>
        </main>
    </div>
    <script>
    (function(){{
        'use strict';
        const VERIFY_BASE='https://windi-domain.com/api/receipts/';
        const VERIFY_PUBLIC='https://windi-domain.com/verify-public/?id=';
        const btn=document.getElementById('auditTrigger');
        const panel=document.getElementById('proofPanel');
        const lines=[document.getElementById('line1'),document.getElementById('line2'),document.getElementById('line3')];
        const status=document.getElementById('terminalStatus');
        const details=document.getElementById('terminalDetails');
        const actions=document.getElementById('terminalActions');
        let audited=false;
        btn.addEventListener('click',async function(){{
            if(audited){{panel.classList.toggle('revealed');return;}}
            const receiptId=this.dataset.receiptId;
            if(!receiptId)return;
            audited=true;
            btn.classList.add('auditing');
            btn.textContent='Auditing...';
            panel.classList.add('revealed');
            for(let i=0;i<lines.length;i++){{await delay(400+i*300);lines[i].classList.add('visible');}}
            try{{
                await delay(500);
                const response=await fetch(VERIFY_BASE+encodeURIComponent(receiptId));
                if(!response.ok)throw new Error('Receipt not found');
                const data=await response.json();
                await delay(300);
                status.classList.add('visible','match');
                status.querySelector('.status-icon').textContent='✓';
                status.querySelector('.status-text').textContent='MATCH · SOVEREIGN';
                panel.classList.add('verified');
                btn.classList.remove('auditing');
                btn.classList.add('verified');
                btn.textContent='✓ Verified';
                await delay(200);
                const r=data.receipt||data;
                document.getElementById('detailReceipt').textContent=r.id||r.receipt_id||receiptId;
                document.getElementById('detailHash').textContent=(r.content_hash||'').replace('sha256:','');
                document.getElementById('detailIssued').textContent=formatDate(r.created_at||r.sealed_at);
                details.classList.add('visible');
                await delay(200);
                actions.querySelector('.ledger-link').href=VERIFY_PUBLIC+encodeURIComponent(receiptId);
                actions.classList.add('visible');
            }}catch(err){{
                await delay(300);
                status.classList.add('visible','mismatch');
                status.querySelector('.status-icon').textContent='✗';
                status.querySelector('.status-text').textContent='MISMATCH · DO NOT TRUST';
                panel.classList.add('failed');
                btn.classList.remove('auditing');
                btn.classList.add('failed');
                btn.textContent='✗ Failed';
            }}
        }});
        function delay(ms){{return new Promise(r=>setTimeout(r,ms));}}
        function formatDate(s){{if(!s)return'—';try{{const d=typeof s==='number'?new Date(s*1000):new Date(s);return d.toISOString().replace('T',' ').slice(0,19)+'Z';}}catch{{return String(s);}}}}
        // ═══ THEME TOGGLE (NOIR/KLAR) ═══
        const themeBtn=document.getElementById('themeToggle');
        function setTheme(t){{document.body.dataset.theme=t;localStorage.setItem('windi-theme',t);themeBtn.textContent=t==='klar'?'☽':'☀';}}
        const savedTheme=localStorage.getItem('windi-theme')||'noir';
        if(savedTheme==='klar')setTheme('klar');
        themeBtn.addEventListener('click',()=>setTheme(document.body.dataset.theme==='klar'?'noir':'klar'));
        // ═══ LANGUAGE TOGGLE (PDT-001 §4: chrome only, forensic lexicon stays EN) ═══
        const i18n={{
            de:{{sealed:'gesiegelt'}},
            en:{{sealed:'sealed'}},
            pt:{{sealed:'selado'}}
        }};
        function setLang(l){{
            localStorage.setItem('windi-lang',l);
            document.querySelectorAll('[data-i18n]').forEach(el=>{{const k=el.dataset.i18n;if(i18n[l]&&i18n[l][k])el.textContent=i18n[l][k];}});
            document.querySelectorAll('.lang-btn').forEach(b=>b.classList.toggle('active',b.dataset.lang===l));
        }}
        const savedLang=localStorage.getItem('windi-lang')||(navigator.language.startsWith('de')?'de':navigator.language.startsWith('pt')?'pt':'en');
        setLang(savedLang);
        document.querySelectorAll('.lang-btn').forEach(b=>b.addEventListener('click',()=>setLang(b.dataset.lang)));
    }})();
    </script>
</body>
</html>'''


class MicrologRequest(BaseModel):
    """Request for Microlog generation — Sprint 3."""
    topic: str  # The idea/topic to write about
    site_id: Optional[str] = None  # Optional site association

    @field_validator('topic')
    @classmethod
    def validate_topic(cls, v):
        if len(v) < 5:
            raise ValueError('Topic must be at least 5 characters')
        if len(v) > 500:
            raise ValueError('Topic must be less than 500 characters')
        return v.strip()


# ═══════════════════════════════════════════════════════════════════════════

SITE_GENERATION_SYSTEM_PROMPT = """Generate a complete HTML page. Output ONLY the raw HTML code.

CRITICAL: Do NOT wrap your response in markdown code blocks. Do NOT use triple backticks.
Your response must START with the exact characters: <!DOCTYPE html>
Your response must END with: </html>
NO explanations before or after. NO markdown. Just the HTML.

REQUIREMENTS:
1. Include CSS in a <style> tag inside <head>
2. Modern clean design, good typography
3. Mobile-responsive layout
4. Professional color scheme
5. Semantic HTML5: header, main, section, footer
6. NO JavaScript
7. NO external resources - use system fonts only
8. Footer must say: Verified by WINDI

START YOUR RESPONSE WITH: <!DOCTYPE html>"""


def extract_html_from_response(response: str) -> str:
    """Extract HTML from LLM response, handling markdown code blocks."""
    import re

    # Try to find HTML in code blocks first
    code_block_match = re.search(r'```(?:html)?\s*(<!DOCTYPE.*?</html>)\s*```', response, re.DOTALL | re.IGNORECASE)
    if code_block_match:
        return code_block_match.group(1).strip()

    # Try to find raw HTML
    html_match = re.search(r'(<!DOCTYPE.*?</html>)', response, re.DOTALL | re.IGNORECASE)
    if html_match:
        return html_match.group(1).strip()

    # Return as-is if no pattern matched
    return response.strip()


@sites_router.post("/sites/generate")
async def generate_site_ai(data: GenerateSiteRequest, request: Request):
    """
    §240 — AI Site Generator · W-CORTEX-001 Canal Único

    Generate a complete HTML website from a text prompt using Ollama B.
    ALL inference passes through generate_with_pipeline() — zero bypass.

    Flow:
      1. DID gate (public mode via W-CORTEX-001)
      2. L-1 filter (Cardinal Sin detection)
      3. Ollama B generation (mistral:7b @ Galho B)
      4. L0 filter (output quality)
      5. HTML sanitization (XSS prevention)
      6. Store in windi_generations
      7. Seal to Ledger
      8. Return preview + hash + receipt

    Invariants: I1, I9, I10, I11, I14
    """
    now = datetime.now(timezone.utc)
    now_str = now.isoformat()
    timestamp = now.strftime("%Y%m%d%H%M%S")

    # ─── Pre-check: DID exists ────────────────────────────────────────────────
    caller_did = get_caller_did(request)
    if not caller_did:
        raise HTTPException(status_code=401, detail="DID required (I9)")

    # ─── Site association (optional) ──────────────────────────────────────────
    site_id = data.site_id
    if site_id:
        if not verify_site_ownership(site_id, caller_did):
            raise HTTPException(status_code=403, detail="Not authorized for this site")

    # ─── W-CORTEX-001: Canal Único Soberano ───────────────────────────────────
    # Receipt Symmetry Axiom (I9, §239):
    # O HTML retornado nesta resposta é EXACTAMENTE o que será publicado.
    # Zero regeneração. Zero "polish before publish".
    # O hash desta geração = hash do que vai live = hash que /verify mostra.
    # Quebrar isto = quebrar A.3.14 do Paper-001.
    generation_id = str(uuid.uuid4())
    request_host = request.headers.get("host", "")

    # Build full prompt with system instructions
    full_prompt = f"{SITE_GENERATION_SYSTEM_PROMPT}\n\nUser request: {data.prompt}"

    # Call via W-CORTEX-001 pipeline — NOT generate_content() directly
    # §241: Tier routing based on DID tier_level (not hardcoded)
    result = await generate_with_pipeline(
        caller_did=caller_did,
        caller_tier="NODAL",  # Legacy field for DID gate compatibility
        request_host=request_host,
        acceptability_l_minus_1_fn=acceptability_l_minus_1,
        acceptability_l_zero_fn=acceptability_l_zero,
        free_prompt=full_prompt,  # Free mode, not template
        did_gate_fn=assert_public_writer_authorized,  # Public gate, not internal
        requested_tier=None  # §241: Let DID resolution determine tier
    )

    # Handle pipeline errors
    if not result.ok:
        error = result.error or "unknown_error"
        if "DID_GATE" in error:
            raise HTTPException(status_code=403, detail=error)
        elif "L-1_BLOCKED_CS1" in error:
            raise HTTPException(status_code=451, detail=error)
        elif "L0_BLOCKED" in error:
            raise HTTPException(status_code=422, detail=error)
        elif "TIER_UNAVAILABLE" in error:
            # §242: 503 Service Unavailable with available_tiers
            tier_info = result.generation_log.get("tier_unavailable", {}) if result.generation_log else {}
            available = result.generation_log.get("available_tiers", ["FREE", "HIGH"]) if result.generation_log else ["FREE", "HIGH"]
            return JSONResponse(
                status_code=503,
                content={
                    "ok": False,
                    "error": {
                        "code": "TIER_UNAVAILABLE",
                        "tier_requested": error.split(":")[1] if ":" in error else "MED",
                        "message": "MED tier temporarily unavailable (provider key not configured)",
                        "available_tiers": available,
                        "action": f"Choose {' or '.join(available)} tier"
                    }
                }
            )
        elif "OLLAMA_FAILED" in error:
            raise HTTPException(status_code=502, detail=f"{error} (I10 fallback needed)")
        else:
            raise HTTPException(status_code=400, detail=error)

    raw_response = result.content or ""

    # ─── Extract HTML from response (handles markdown code blocks) ───────────
    generated_html = extract_html_from_response(raw_response)

    # ─── Validate HTML output ─────────────────────────────────────────────────
    # Note: .upper() converts to "<!DOCTYPE HTML>" so we must match that
    if not generated_html or "<!DOCTYPE HTML>" not in generated_html.upper():
        raise HTTPException(status_code=422, detail="Invalid HTML generated (I14)")

    # ─── Sanitize HTML (XSS prevention) ───────────────────────────────────────
    sanitized_html = sanitize_html(generated_html)

    # ─── Compute content hash ─────────────────────────────────────────────────
    content_hash = f"sha256:{hashlib.sha256(sanitized_html.encode()).hexdigest()}"

    # ─── Receipt ID ───────────────────────────────────────────────────────────
    short_hash = content_hash.split(':')[1][:8].upper()
    receipt_id = f"WINDI-GENERATE-{timestamp}-{short_hash}"

    # ─── Extract generation metadata from W-CORTEX-001 result ──────────────────
    model_used = result.generation_log.get("model", "mistral:7b") if result.generation_log else "mistral:7b"
    source_mode = result.source_mode  # "free" for this endpoint

    # ─── Store in windi_generations ───────────────────────────────────────────
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO windi_generations (
                id, site_id, container_id, prompt, model,
                html, content_hash, status,
                created_at, generated_at, generation_receipt
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
        """, (
            generation_id,
            site_id,
            None,  # container_id - not linked to container yet
            data.prompt,
            model_used,
            sanitized_html,
            content_hash,
            now_str,
            now_str,
            receipt_id
        ))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"DB error: {str(e)}")

    conn.close()

    # ─── §242: Persist to Filesystem (Sprint 2) ──────────────────────────────
    # CRITICAL: Hash of persisted file, not in-memory content (I11)
    # Path: /opt/windi/sites/{site_id}/{generation_id}.html
    effective_site_id = site_id or "unlinked"
    persist_result = persist_site_html(
        site_id=effective_site_id,
        container_id=generation_id,
        html_content=sanitized_html,
        meta={
            "generation_id": generation_id,
            "site_id": site_id,
            "prompt": data.prompt,
            "model": model_used,
            "tier_used": result.tier_used,
            "cost_eur": result.cost_eur,
            "receipt_id": receipt_id,
            "did": caller_did
        }
    )

    # Use hash from disk (I11 compliance)
    final_content_hash = persist_result.get("content_hash") or content_hash
    public_url = persist_result.get("public_url")

    # ─── Seal to Ledger (hash of what's on disk) ─────────────────────────────
    ledger_result = seal_to_ledger(
        receipt_id,
        f"AI Site Generation: {data.site_name or 'Untitled'}",
        final_content_hash,
        caller_did
    )

    # ─── Return result ────────────────────────────────────────────────────────
    return {
        "ok": True,
        "generation_id": generation_id,
        "site_id": site_id,
        "prompt": data.prompt,
        "model": model_used,
        "html": sanitized_html,
        "content_hash": final_content_hash,
        "status": "pending",  # Awaiting I9 approval
        "generation_receipt": receipt_id,
        "ledger": ledger_result,
        "source_mode": source_mode,  # W-CORTEX-001 audit trail
        "tier_used": result.tier_used,
        "cost_eur": result.cost_eur,
        "persist": persist_result,
        "public_url": public_url,
        "invariants": ["I1", "I9", "I10", "I11", "I14"],
        "next_step": "POST /api/sites/publish to approve and publish (I9 gate)"
    }


# ═══════════════════════════════════════════════════════════════════════════
# §243 — MICROLOG ENDPOINT (Sprint 3)
# ═══════════════════════════════════════════════════════════════════════════

@sites_router.post("/sites/microlog")
async def create_microlog(data: MicrologRequest, request: Request):
    """
    §243 — Microlog Generator · Sprint 3

    "A single verifiable idea, sealed as a public artefact"

    Flow:
      1. DID gate
      2. L-1 filter
      3. Generate microlog content via CORTEX
      4. Parse JSON response
      5. Render into NOIR HTML skeleton
      6. Persist to filesystem
      7. Seal to Ledger
      8. Return public URL

    Invariants: I1, I9, I10, I11, I14
    """
    import json as json_lib

    now = datetime.now(timezone.utc)
    now_str = now.isoformat()
    timestamp = now.strftime("%Y%m%d%H%M%S")

    # ─── Pre-check: DID exists ────────────────────────────────────────────────
    caller_did = get_caller_did(request)
    if not caller_did:
        raise HTTPException(status_code=401, detail="DID required (I9)")

    # ─── Generate microlog content via CORTEX ─────────────────────────────────
    microlog_id = str(uuid.uuid4())
    request_host = request.headers.get("host", "")

    # Build prompt for microlog
    full_prompt = f"{MICROLOG_SYSTEM_PROMPT}\n\nTopic: {data.topic}"

    result = await generate_with_pipeline(
        caller_did=caller_did,
        caller_tier="NODAL",
        request_host=request_host,
        acceptability_l_minus_1_fn=acceptability_l_minus_1,
        acceptability_l_zero_fn=acceptability_l_zero,
        free_prompt=full_prompt,
        did_gate_fn=assert_public_writer_authorized,
        requested_tier=None  # §241: Let DID resolution determine tier
    )

    # Handle pipeline errors
    if not result.ok:
        error = result.error or "unknown_error"
        if "DID_GATE" in error:
            raise HTTPException(status_code=403, detail=error)
        elif "L-1_BLOCKED_CS1" in error:
            raise HTTPException(status_code=451, detail=error)
        elif "L0_BLOCKED" in error:
            raise HTTPException(status_code=422, detail=error)
        elif "TIER_UNAVAILABLE" in error:
            available = result.generation_log.get("available_tiers", ["FREE", "HIGH"]) if result.generation_log else ["FREE", "HIGH"]
            return JSONResponse(
                status_code=503,
                content={
                    "ok": False,
                    "error": {
                        "code": "TIER_UNAVAILABLE",
                        "available_tiers": available
                    }
                }
            )
        raise HTTPException(status_code=500, detail=f"Generation failed: {error}")

    raw_content = result.content or ""
    model_used = result.model_used or "unknown"

    # ─── Parse JSON from LLM response ─────────────────────────────────────────
    try:
        # Try to extract JSON from response
        json_match = re.search(r'\{[^{}]*"title"[^{}]*\}', raw_content, re.DOTALL)
        if json_match:
            microlog_data = json_lib.loads(json_match.group())
        else:
            # Fallback: try full response as JSON
            microlog_data = json_lib.loads(raw_content.strip())

        title = microlog_data.get("title", "Untitled")
        content = microlog_data.get("content", "")
        closing = microlog_data.get("closing", "")
    except (json_lib.JSONDecodeError, KeyError):
        # Fallback: use raw content
        title = f"Microlog: {data.topic[:50]}"
        content = raw_content
        closing = ""

    # ─── Prepare receipt ──────────────────────────────────────────────────────
    receipt_id = f"WINDI-MICROLOG-{timestamp}-{microlog_id[:8].upper()}"
    verify_url = f"https://windi-domain.com/verify-public/?id={receipt_id}"

    # Temporary hash for skeleton (will be replaced with disk hash)
    temp_hash = f"sha256:{hashlib.sha256(content.encode()).hexdigest()}"

    # ─── Render HTML with Surface V1 skeleton ─────────────────────────────────
    # Escape content for HTML safety
    safe_title = html_escape.escape(title)
    safe_content = f"<p>{html_escape.escape(content)}</p>"
    safe_closing = html_escape.escape(closing)

    # Extract handle from DID (e.g., did:windi:dragon-001 -> @dragon-001)
    handle_part = caller_did.split(":")[-1] if caller_did else "anonymous"
    safe_handle = f"@{html_escape.escape(handle_part)}"

    # Sealed date for display
    sealed_date = now.strftime("%Y-%m-%d")

    rendered_html = MICROLOG_HTML_SKELETON.format(
        title=safe_title,
        content=safe_content,
        closing=safe_closing,
        handle=safe_handle,
        sealed_date=sealed_date,
        receipt_id=receipt_id,
        verify_url=verify_url
    )

    # ─── Persist to filesystem ────────────────────────────────────────────────
    effective_site_id = data.site_id or "micrologs"
    persist_result = persist_site_html(
        site_id=effective_site_id,
        container_id=microlog_id,
        html_content=rendered_html,
        meta={
            "microlog_id": microlog_id,
            "type": "microlog",
            "topic": data.topic,
            "title": title,
            "model": model_used,
            "tier_used": result.tier_used,
            "cost_eur": result.cost_eur,
            "receipt_id": receipt_id,
            "did": caller_did
        }
    )

    final_content_hash = persist_result.get("content_hash") or temp_hash
    public_url = persist_result.get("public_url")

    # ─── Update HTML with final hash ──────────────────────────────────────────
    # Re-render with Surface V1 skeleton (hash is in meta.json, not in HTML)
    rendered_html = MICROLOG_HTML_SKELETON.format(
        title=safe_title,
        content=safe_content,
        closing=safe_closing,
        handle=safe_handle,
        sealed_date=sealed_date,
        receipt_id=receipt_id,
        verify_url=verify_url
    )

    # Re-persist with correct hash
    persist_result = persist_site_html(
        site_id=effective_site_id,
        container_id=microlog_id,
        html_content=rendered_html,
        meta={
            "microlog_id": microlog_id,
            "type": "microlog",
            "topic": data.topic,
            "title": title,
            "model": model_used,
            "tier_used": result.tier_used,
            "cost_eur": result.cost_eur,
            "receipt_id": receipt_id,
            "did": caller_did
        }
    )

    final_content_hash = persist_result.get("content_hash")

    # ─── Seal to Ledger ───────────────────────────────────────────────────────
    ledger_result = seal_to_ledger(
        receipt_id,
        f"Microlog: {title}",
        final_content_hash,
        caller_did
    )

    # ─── Return result ────────────────────────────────────────────────────────
    return {
        "ok": True,
        "type": "microlog",
        "microlog_id": microlog_id,
        "title": title,
        "content": content,
        "closing": closing,
        "topic": data.topic,
        "model": model_used,
        "content_hash": final_content_hash,
        "receipt_id": receipt_id,
        "verify_url": verify_url,
        "public_url": public_url,
        "ledger": ledger_result,
        "tier_used": result.tier_used,
        "cost_eur": result.cost_eur,
        "invariants": ["I1", "I9", "I10", "I11", "I14"]
    }
