"""
§166 Integration Patches
W-ENTERPRISE-001 (:8150) + WINDI-LAW (:8122)
Add these functions to the respective backends.
"""

import httpx
from typing import Optional
import logging

CANVAS_URL = "http://127.0.0.1:8155"

# ══════════════════════════════════════════════════════════════════════════════
# PATCH A — W-ENTERPRISE-001 · enterprise_main_patch.py
# Add to the existing REP generation flow (DocGen module)
# ══════════════════════════════════════════════════════════════════════════════

async def enterprise_generate_cover(
    title: str,
    subtitle: str = "Risk Evidence Package",
    theme: str = "NOIR",
    actor: str = "enterprise-docgen",
) -> Optional[dict]:
    """
    Generate a visual cover for REP / PHO packages.
    Called before DOCX assembly in the Enterprise DocGen module.
    Returns: { "download_url": str, "sha256": str, "job_id": str }
    """
    spec = {
        "title": title,
        "theme": theme,
        "format": "png",
        "show_seal": True,
        "seal_text": "WINDI Enterprise · PHO",
        "doc_type": "enterprise_rep",
        "governance_level": "HIGH",
        "actor": actor,
        "app": "W-ENTERPRISE-001",
        "seal_to_ledger": True,
        "shapes": [
            # Left accent bar
            {"kind": "rect", "x": 0.0, "y": 0.0, "w": 0.06, "h": 1.0,
             "color": "accent", "opacity": 1.0, "filled": True},
            # Top header band
            {"kind": "rect", "x": 0.06, "y": 0.0, "w": 0.94, "h": 0.32,
             "color": "surface", "opacity": 1.0, "filled": True},
            # Diagonal slash accent
            {"kind": "line", "x": 0.06, "y": 0.32, "w": 0.15, "h": 0.0,
             "color": "accent", "opacity": 0.6, "stroke_width": 3},
        ],
        "texts": [
            {"content": "WINDI ENTERPRISE",
             "x": 0.55, "y": 0.16, "size": "xl", "style": "bold", "opacity": 1.0},
            {"content": subtitle,
             "x": 0.55, "y": 0.25, "size": "md", "style": "regular", "opacity": 0.7},
            {"content": title,
             "x": 0.55, "y": 0.55, "size": "lg", "style": "bold", "opacity": 0.95},
            {"content": "PHO · EU AI Act Art. 14 · WINDI §166",
             "x": 0.55, "y": 0.88, "size": "xs", "style": "mono", "opacity": 0.45},
        ]
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{CANVAS_URL}/canvas/render", json=spec)
            if r.status_code == 200:
                return r.json()
    except Exception as e:
        # Offline-graceful: return None, continue without cover
        logging.getLogger("enterprise").warning(f"Canvas offline: {e}")
    return None


async def enterprise_generate_pho_cert(
    actor_name: str,
    decision_summary: str,
    doc_id: str,
) -> Optional[dict]:
    """
    Generate PHO Certificate visual for compliance dossier.
    """
    spec = {
        "title": f"PHO-{doc_id}",
        "theme": "KLAR",
        "format": "png",
        "show_seal": True,
        "seal_text": f"PHO · {doc_id}",
        "doc_type": "pho_cert",
        "governance_level": "HIGH",
        "actor": actor_name,
        "app": "W-ENTERPRISE-001",
        "shapes": [
            {"kind": "rect", "x": 0.03, "y": 0.03, "w": 0.94, "h": 0.94,
             "color": "accent", "opacity": 0.06, "filled": True},
            {"kind": "rect", "x": 0.05, "y": 0.05, "w": 0.9, "h": 0.9,
             "color": "border", "opacity": 0.4, "filled": False, "stroke_width": 2},
            {"kind": "diamond", "x": 0.42, "y": 0.1, "w": 0.16, "h": 0.14,
             "color": "accent", "opacity": 0.8, "filled": True},
        ],
        "texts": [
            {"content": "PROOF OF HUMAN OVERSIGHT",
             "x": 0.5, "y": 0.34, "size": "lg", "style": "bold", "opacity": 1.0},
            {"content": "EU AI Act · Article 14",
             "x": 0.5, "y": 0.47, "size": "md", "style": "mono", "opacity": 0.65},
            {"content": decision_summary[:60],
             "x": 0.5, "y": 0.60, "size": "sm", "style": "regular", "opacity": 0.7},
            {"content": f"Operator: {actor_name}",
             "x": 0.5, "y": 0.72, "size": "xs", "style": "mono", "opacity": 0.5},
        ]
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{CANVAS_URL}/canvas/render", json=spec)
            if r.status_code == 200:
                return r.json()
    except Exception as e:
        logging.getLogger("enterprise").warning(f"Canvas offline: {e}")
    return None


# ══════════════════════════════════════════════════════════════════════════════
# PATCH B — WINDI-LAW · law_canvas_patch.py
# Add to ai_draft.py or as separate import
# ══════════════════════════════════════════════════════════════════════════════

async def law_generate_document_cover(
    doc_title: str,
    jurisdiction: str,
    doc_type: str,
    actor: str = "windi-law",
) -> Optional[dict]:
    """
    Generate a branded cover image for legal documents.
    Insert as first page in DOCX export or as cover PNG attachment.

    Usage in ai_draft.py:
        cover = await law_generate_document_cover(title, jurisdiction, doc_type)
        if cover:
            doc_data["cover_url"] = cover["download_url"]
            doc_data["cover_sha256"] = cover["sha256"]
    """
    spec = {
        "title": doc_title,
        "theme": "KLAR",
        "format": "png",
        "show_seal": True,
        "seal_text": "WINDI-LAW · Sealed",
        "doc_type": "law_cover",
        "governance_level": "HIGH",
        "actor": actor,
        "app": "W-DRAGON-001",
        "seal_to_ledger": True,
        "grid_opacity": 0.04,
        "shapes": [
            # Subtle parchment layer
            {"kind": "rect", "x": 0.06, "y": 0.06, "w": 0.88, "h": 0.88,
             "color": "surface", "opacity": 0.5, "filled": True},
            # Gold horizontal rule — top
            {"kind": "line", "x": 0.1, "y": 0.20, "w": 0.8, "h": 0.001,
             "color": "accent", "opacity": 0.7, "stroke_width": 2},
            # Gold horizontal rule — bottom
            {"kind": "line", "x": 0.1, "y": 0.80, "w": 0.8, "h": 0.001,
             "color": "accent", "opacity": 0.7, "stroke_width": 2},
        ],
        "texts": [
            # Ghost watermark
            {"content": "WINDI-LAW",
             "x": 0.5, "y": 0.14, "size": "hero", "style": "bold", "opacity": 0.07},
            # Main title
            {"content": doc_title[:50],
             "x": 0.5, "y": 0.48, "size": "xl", "style": "bold", "opacity": 1.0},
            # Jurisdiction
            {"content": jurisdiction,
             "x": 0.5, "y": 0.60, "size": "md", "style": "mono", "opacity": 0.6},
            # Doc type
            {"content": doc_type.upper(),
             "x": 0.5, "y": 0.70, "size": "sm", "style": "regular", "opacity": 0.5},
        ]
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{CANVAS_URL}/canvas/render", json=spec)
            if r.status_code == 200:
                return r.json()
    except Exception as e:
        logging.getLogger("windi-law").warning(f"Canvas offline: {e}")
    return None
