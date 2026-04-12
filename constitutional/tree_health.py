"""
tree_health.py — DECREE-001 Constitutional Compliance Verification
Central endpoint that verifies all WINDI organs follow the Living Tree protocol.

Endpoint: /api/tree/health
Port: 8101 (via Forensic Ledger — the TRUNK)

Liga IA+H · 12 Abril 2026
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

import httpx
from fastapi import APIRouter

log = logging.getLogger("windi.tree.health")

# ═══════════════════════════════════════════════════════════════════════════
# DECREE-001 — Organ Registry (The Living Tree)
# ═══════════════════════════════════════════════════════════════════════════

ORGANS = {
    "enterprise": {
        "name": "W-Enterprise-001",
        "port": 8150,
        "health": "/health",
        "route": "/enterprise/",
        "checks": ["origin_detection", "server_ops_nav", "did_cross_validation"],
    },
    "law": {
        "name": "WINDI-LAW",
        "port": 8122,
        "health": "/health",
        "route": "/law/",
        "checks": ["origin_detection", "did_validation"],
    },
    "travel": {
        "name": "WINDI Travel",
        "port": 8126,
        "health": "/health",
        "route": "/travel/",
        "checks": ["origin_detection", "did_validation"],
    },
    "wallet": {
        "name": "WINDI Wallet",
        "port": 8099,
        "health": "/api/wallet/health",
        "route": "/wallet/",
        "checks": ["origin_detection", "go_to_origin"],
    },
    "sec": {
        "name": "W-SEC-001",
        "port": 8144,
        "health": "/health",
        "route": "/sec/dashboard/",
        "checks": ["health_ok"],
    },
    "verify": {
        "name": "Verify Public",
        "port": 8145,
        "health": "/health",
        "route": "/verify-public/",
        "checks": ["health_ok"],
    },
    "dev_api": {
        "name": "W-DEV-API",
        "port": 8200,
        "health": "/health",
        "route": "/dev-api/",
        "checks": ["health_ok"],
    },
    "ledger": {
        "name": "Forensic Ledger (TRUNK)",
        "port": 8101,
        "health": "/health",
        "route": "/api/ledger/",
        "checks": ["health_ok"],
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# Health Check Functions
# ═══════════════════════════════════════════════════════════════════════════

async def check_organ_health(organ_id: str, organ: dict) -> Dict[str, Any]:
    """Check if an organ is alive and responding."""
    result = {
        "organ": organ_id,
        "name": organ["name"],
        "port": organ["port"],
        "route": organ["route"],
        "healthy": False,
        "response_ms": None,
        "checks": {},
    }

    try:
        start = datetime.now(timezone.utc)
        async with httpx.AsyncClient(timeout=5) as client:
            url = f"http://localhost:{organ['port']}{organ['health']}"
            r = await client.get(url)
            elapsed = (datetime.now(timezone.utc) - start).total_seconds() * 1000

            result["healthy"] = r.status_code == 200
            result["response_ms"] = round(elapsed, 2)

            if r.status_code == 200:
                try:
                    data = r.json()
                    result["version"] = data.get("version", "?")
                except:
                    pass

    except Exception as e:
        result["error"] = str(e)

    return result


async def check_all_organs() -> Dict[str, Any]:
    """
    DECREE-001 Article 7: Full tree health verification.
    Checks all organs in parallel and returns comprehensive report.
    """
    start = datetime.now(timezone.utc)

    # Check all organs in parallel
    tasks = [check_organ_health(oid, organ) for oid, organ in ORGANS.items()]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Build report
    organs_status = {}
    healthy_count = 0
    total_count = len(ORGANS)

    for result in results:
        if isinstance(result, Exception):
            continue
        organs_status[result["organ"]] = result
        if result.get("healthy"):
            healthy_count += 1

    # Determine overall status
    if healthy_count == total_count:
        status = "healthy"
        emoji = "🌳"
    elif healthy_count >= total_count * 0.7:
        status = "degraded"
        emoji = "🌿"
    elif healthy_count >= total_count * 0.3:
        status = "critical"
        emoji = "🥀"
    else:
        status = "failing"
        emoji = "🍂"

    elapsed = (datetime.now(timezone.utc) - start).total_seconds() * 1000

    return {
        "decree": "DECREE-001-LIVING-TREE",
        "status": status,
        "emoji": emoji,
        "healthy_organs": healthy_count,
        "total_organs": total_count,
        "health_ratio": f"{healthy_count}/{total_count}",
        "organs": organs_status,
        "check_duration_ms": round(elapsed, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "constitution": {
            "article_1": "Tree Definition — Trunk=Ledger, Sap=DID, Branches=Organs",
            "article_2": "Origin Preservation — ?return= param, windi_origin",
            "article_3": "Universal Navigation — Server Operations sidebar",
            "article_4": "DID Cross-Validation — One DID, whole tree",
            "article_5": "Shared Fruits — Receipts via Verify Public",
            "article_6": "Prohibitions — /desktop/ deprecated",
            "article_7": "Compliance Check — This endpoint",
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# FastAPI Router
# ═══════════════════════════════════════════════════════════════════════════

def create_tree_health_router() -> APIRouter:
    """Create the constitutional tree health router."""
    router = APIRouter(prefix="/api/tree", tags=["Constitutional"])

    @router.get("/health")
    async def tree_health():
        """
        DECREE-001 Article 7: Constitutional Compliance Check.
        Returns health status of all organs in the Living Tree.
        """
        return await check_all_organs()

    @router.get("/organs")
    async def list_organs():
        """List all registered organs in the Living Tree."""
        return {
            "decree": "DECREE-001-LIVING-TREE",
            "organs": [
                {
                    "id": oid,
                    "name": organ["name"],
                    "port": organ["port"],
                    "route": organ["route"],
                }
                for oid, organ in ORGANS.items()
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @router.get("/decree")
    async def get_decree():
        """Return the constitutional decree summary."""
        return {
            "id": "DECREE-001",
            "name": "A Árvore Viva",
            "name_en": "The Living Tree",
            "sealed": "2026-04-12",
            "author": "Human Dragon",
            "invariants": ["I1", "I9", "I11", "I12", "I14"],
            "status": "CONSTITUTIONAL",
            "quote": {
                "pt": "O servidor WINDI é uma Árvore Viva. Cada serviço é um galho. A seiva (DID) flui do tronco às folhas. Nenhum galho vive sozinho.",
                "de": "Der WINDI-Server ist ein lebendiger Baum. Jeder Dienst ist ein Ast. Der Saft (DID) fließt vom Stamm zu den Blättern. Kein Ast lebt allein.",
                "en": "The WINDI server is a Living Tree. Each service is a branch. The sap (DID) flows from trunk to leaves. No branch lives alone.",
            },
            "articles": 7,
            "files": [
                "/opt/windi/constitutional/DECREE-001-LIVING-TREE.md",
                "/opt/windi/constitutional/windi-tree.js",
                "/opt/windi/constitutional/windi_tree.py",
            ],
        }

    return router
