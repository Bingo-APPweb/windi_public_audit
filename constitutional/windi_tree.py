"""
windi_tree.py — DECRETO-001 Living Tree Implementation (Backend)
Canonical module for WINDI organ interconnection

USAGE:
    from windi_tree import WindiTree, cross_validate_did, get_organ_navigation

Liga IA+H · 12 Abril 2026
"""

import logging
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum

import httpx

log = logging.getLogger("windi.tree")


# ═══════════════════════════════════════════════════════════════════════════
# DECREE-001 — Organ Registry
# ═══════════════════════════════════════════════════════════════════════════

class OrganTier(Enum):
    ORGAN = "organ"        # Main products (Enterprise, LAW, Travel)
    ROOT = "root"          # Foundation services (Wallet, Security)
    LEAF = "leaf"          # Utility services (Verify, Dev-API)
    DEPRECATED = "deprecated"  # Legacy (Desktop GEN7)


@dataclass
class WindiOrgan:
    route: str
    name: str
    port: int
    tier: OrganTier
    icon: str
    health_endpoint: str = "/health"


# The Living Tree — All WINDI Organs
WINDI_TREE: Dict[str, WindiOrgan] = {
    "/enterprise/": WindiOrgan("/enterprise/", "W-Enterprise", 8150, OrganTier.ORGAN, "⬡"),
    "/law/": WindiOrgan("/law/", "WINDI-LAW", 8122, OrganTier.ORGAN, "⚖"),
    "/travel/": WindiOrgan("/travel/", "WINDI Travel", 8126, OrganTier.ORGAN, "🌍"),
    "/wallet/": WindiOrgan("/wallet/", "WINDI Wallet", 8099, OrganTier.ROOT, "🪪"),
    "/sec/dashboard/": WindiOrgan("/sec/dashboard/", "W-SEC-001", 8144, OrganTier.ROOT, "🛡"),
    "/verify-public/": WindiOrgan("/verify-public/", "Verify Public", 8145, OrganTier.LEAF, "✓"),
    "/dev-api/": WindiOrgan("/dev-api/", "W-DEV-API", 8200, OrganTier.LEAF, "⚡"),
    "/desktop/": WindiOrgan("/desktop/", "GEN7 (LEGACY)", 8119, OrganTier.DEPRECATED, "⚠"),
}

# Identity Gates for DID cross-validation (Article 4)
IDENTITY_GATES = [
    ("http://localhost:8122", "/identity/"),   # WINDI-LAW (primary)
    ("http://localhost:8099", "/api/wallet/identity/"),  # Wallet
    ("http://localhost:8096", "/session/validate/"),  # W-SESSION-001
]

DEFAULT_ORIGIN = "/enterprise/"


# ═══════════════════════════════════════════════════════════════════════════
# Article 2 — Origin Detection (Backend)
# ═══════════════════════════════════════════════════════════════════════════

def detect_origin_from_request(request) -> str:
    """
    Detect user origin from HTTP request.
    Checks: query param → header → referrer → default
    """
    # 1. Query param ?return=
    return_param = request.query_params.get("return", "")
    if return_param.startswith("/") and is_valid_organ(return_param):
        return return_param

    # 2. X-Windi-Origin header
    header_origin = request.headers.get("X-Windi-Origin", "")
    if header_origin.startswith("/") and is_valid_organ(header_origin):
        return header_origin

    # 3. Referrer
    referrer = request.headers.get("Referer", "")
    if "windi-domain.com" in referrer:
        try:
            from urllib.parse import urlparse
            path = urlparse(referrer).path
            for route, organ in WINDI_TREE.items():
                if path.startswith(route) and organ.tier != OrganTier.DEPRECATED:
                    return route
        except:
            pass

    # 4. Default
    return DEFAULT_ORIGIN


def is_valid_organ(path: str) -> bool:
    """Check if path is a valid, non-deprecated organ."""
    for route, organ in WINDI_TREE.items():
        if path.startswith(route) and organ.tier != OrganTier.DEPRECATED:
            return True
    return False


def build_return_url(target_route: str, current_route: str) -> str:
    """Build URL with return parameter."""
    if "?" in target_route:
        return f"{target_route}&return={current_route}"
    return f"{target_route}?return={current_route}"


# ═══════════════════════════════════════════════════════════════════════════
# Article 3 — Navigation
# ═══════════════════════════════════════════════════════════════════════════

def get_organ_navigation(current_route: str = None) -> List[Dict[str, Any]]:
    """
    Get navigation links to other organs.
    Excludes current organ and deprecated organs.
    """
    nav = []
    for route, organ in WINDI_TREE.items():
        if organ.tier == OrganTier.DEPRECATED:
            continue
        if current_route and route == current_route:
            continue
        nav.append({
            "route": route,
            "name": organ.name,
            "icon": organ.icon,
            "tier": organ.tier.value,
        })
    return nav


def get_server_operations_nav() -> List[Dict[str, Any]]:
    """Get canonical Server Operations navigation."""
    return [
        {"route": "/sec/dashboard/", "name": "W-SEC-001 · NOIR OPS", "icon": "🛡"},
        {"route": "/dev-api/", "name": "W-DEV-API · Developers", "icon": "⚡"},
        {"route": "/verify-public/", "name": "Verify Public", "icon": "✓"},
    ]


# ═══════════════════════════════════════════════════════════════════════════
# Article 4 — DID Cross-Validation
# ═══════════════════════════════════════════════════════════════════════════

async def cross_validate_did(did: str) -> Optional[Dict[str, Any]]:
    """
    Cross-validate DID across all WINDI identity gates.
    Returns validation result from first gate that recognizes the DID.

    DECREE-001 Article 4: "One DID, one identity, the whole tree."
    """
    if not did or not did.startswith("did:windi:"):
        return None

    for gate_url, endpoint in IDENTITY_GATES:
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                url = f"{gate_url}{endpoint}{did}"
                r = await client.get(url)

                if r.status_code == 200:
                    data = r.json()
                    log.info(f"[WindiTree] DID validated at {gate_url}: {did[:25]}...")
                    return {
                        "valid": True,
                        "did": did,
                        "source": gate_url,
                        "data": data,
                    }
        except Exception as e:
            log.debug(f"[WindiTree] Gate {gate_url} unavailable: {e}")
            continue

    log.warning(f"[WindiTree] DID not found in any gate: {did[:25]}...")
    return None


def validate_did_format(did: str) -> bool:
    """Validate DID format without network calls."""
    if not did:
        return False
    if not did.startswith("did:windi:"):
        return False
    if len(did) < 20:
        return False
    return True


# ═══════════════════════════════════════════════════════════════════════════
# Article 7 — Tree Health Check
# ═══════════════════════════════════════════════════════════════════════════

async def check_tree_health() -> Dict[str, Any]:
    """
    Check health of all organs in the Living Tree.
    Returns comprehensive health report.
    """
    results = {
        "decree": "DECREE-001-LIVING-TREE",
        "version": "1.0.0",
        "status": "healthy",
        "organs": {},
        "warnings": [],
    }

    healthy_count = 0
    total_count = 0

    for route, organ in WINDI_TREE.items():
        if organ.tier == OrganTier.DEPRECATED:
            continue

        total_count += 1
        organ_status = {
            "name": organ.name,
            "port": organ.port,
            "tier": organ.tier.value,
            "healthy": False,
        }

        try:
            async with httpx.AsyncClient(timeout=3) as client:
                url = f"http://localhost:{organ.port}{organ.health_endpoint}"
                r = await client.get(url)
                organ_status["healthy"] = r.status_code == 200
                if r.status_code == 200:
                    healthy_count += 1
        except:
            results["warnings"].append(f"{organ.name} unreachable on :{organ.port}")

        results["organs"][route] = organ_status

    # Overall status
    if healthy_count == total_count:
        results["status"] = "healthy"
    elif healthy_count > total_count // 2:
        results["status"] = "degraded"
    else:
        results["status"] = "critical"

    results["healthy_organs"] = healthy_count
    results["total_organs"] = total_count

    return results


# ═══════════════════════════════════════════════════════════════════════════
# FastAPI Router (optional)
# ═══════════════════════════════════════════════════════════════════════════

def create_tree_router():
    """Create FastAPI router for tree health endpoints."""
    from fastapi import APIRouter
    from fastapi.responses import JSONResponse

    router = APIRouter(prefix="/api/tree", tags=["Living-Tree"])

    @router.get("/health")
    async def tree_health():
        """DECREE-001 Article 7: Tree health check."""
        report = await check_tree_health()
        status_code = 200 if report["status"] == "healthy" else 503
        return JSONResponse(content=report, status_code=status_code)

    @router.get("/organs")
    async def list_organs():
        """List all organs in the Living Tree."""
        return {
            "decree": "DECREE-001-LIVING-TREE",
            "organs": [
                {
                    "route": route,
                    "name": organ.name,
                    "port": organ.port,
                    "tier": organ.tier.value,
                    "icon": organ.icon,
                }
                for route, organ in WINDI_TREE.items()
            ]
        }

    @router.get("/navigation")
    async def get_navigation(current: str = None):
        """Get navigation links for an organ."""
        return {
            "server_operations": get_server_operations_nav(),
            "other_organs": get_organ_navigation(current),
        }

    return router
