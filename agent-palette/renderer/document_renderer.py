#!/usr/bin/env python3
"""
WINDI Document Renderer Engine v1.0.0
"AI processes. Human decides. WINDI guarantees."

The HANDS of the Dragon — converts text + governance metadata into
real downloadable documents (.docx, .xlsx, .pptx, .pdf).

Architecture:
  Dragon API (text) → Renderer Engine → Binary File → Download + Ledger Hash
"""

import hashlib
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ── Renderer Imports (lazy-loaded for resilience) ──
RENDERERS = {}
RENDERER_STATUS = {}


def _load_renderers():
    """Lazy-load format renderers with graceful fallback."""
    global RENDERERS, RENDERER_STATUS

    try:
        from renderers.docx_renderer import render_docx
        RENDERERS["docx"] = render_docx
        RENDERER_STATUS["docx"] = "ready"
    except ImportError as e:
        RENDERER_STATUS["docx"] = f"unavailable: {e}"

    try:
        from renderers.xlsx_renderer import render_xlsx
        RENDERERS["xlsx"] = render_xlsx
        RENDERER_STATUS["xlsx"] = "ready"
    except ImportError as e:
        RENDERER_STATUS["xlsx"] = f"unavailable: {e}"

    try:
        from renderers.pptx_renderer import render_pptx
        RENDERERS["pptx"] = render_pptx
        RENDERER_STATUS["pptx"] = "ready"
    except ImportError as e:
        RENDERER_STATUS["pptx"] = f"unavailable: {e}"

    try:
        from renderers.pdf_renderer import render_pdf
        RENDERERS["pdf"] = render_pdf
        RENDERER_STATUS["pdf"] = "ready"
    except ImportError as e:
        RENDERER_STATUS["pdf"] = f"unavailable: {e}"


def init():
    """Initialize renderer engine."""
    _load_renderers()
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    return {
        "version": "1.0.0",
        "renderers": RENDERER_STATUS,
        "output_dir": str(output_dir),
        "ready": any(s == "ready" for s in RENDERER_STATUS.values()),
    }


def render_document(text, intent, isp=None, sge=None, receipt=None, tier="HIGH", user_input=""):
    """
    Main render function — converts text into a binary document file.

    Args:
        text (str): Document content from Dragon API (markdown/plain)
        intent (dict): Parsed intent with doc_type, language, formality, entities, etc.
        isp (dict|None): ISP profile data (branding, colors, logo path)
        sge (dict|None): SGE analysis results (score, risk, flags)
        receipt (dict|None): Forensic receipt data for embedding
        tier (str): User tier — FREE/MED/HIGH

    Returns:
        dict: {
            "success": bool,
            "filepath": str,          # Absolute path to generated file
            "filename": str,          # User-friendly filename
            "format": str,            # docx/xlsx/pptx/pdf
            "size_bytes": int,
            "content_hash": str,      # SHA-256 of file content
            "bundle_hash": str,       # SHA-256 of file + metadata
            "render_ms": int,         # Render time in ms
            "error": str|None,
        }
    """
    t0 = time.time()

    # Resolve format from intent
    doc_type = intent.get("doc_type", "note")
    fmt = _resolve_format(doc_type, tier, intent)
    language = intent.get("language", "de")

    # Check renderer availability
    if fmt not in RENDERERS:
        return _error_result(f"Renderer '{fmt}' not available: {RENDERER_STATUS.get(fmt, 'not loaded')}", fmt, t0)

    # Generate filename
    filename = _generate_filename(doc_type, language, fmt)
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    filepath = output_dir / filename

    # Build render context
    context = {
        "text": text,
        "user_input": user_input,
        "intent": intent,
        "doc_type": doc_type,
        "language": language,
        "formality": intent.get("formality", "formal"),
        "entities": intent.get("entities", {}),
        "urgency": intent.get("urgency", "normal"),
        "isp": isp or {},
        "sge": sge or {},
        "receipt": receipt,
        "tier": tier,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "windi_version": "1.0.0",
    }

    # Render
    try:
        renderer = RENDERERS[fmt]
        renderer(context, str(filepath))
    except Exception as e:
        return _error_result(f"Render failed: {e}", fmt, t0)

    # Compute hashes
    file_bytes = filepath.read_bytes()
    content_hash = hashlib.sha256(file_bytes).hexdigest()
    bundle_data = json.dumps({
        "content_hash": content_hash,
        "doc_type": doc_type,
        "format": fmt,
        "language": language,
        "tier": tier,
        "timestamp": context["timestamp"],
    }, sort_keys=True).encode()
    bundle_hash = hashlib.sha256(bundle_data).hexdigest()

    render_ms = int((time.time() - t0) * 1000)

    return {
        "success": True,
        "filepath": str(filepath),
        "filename": filename,
        "format": fmt,
        "size_bytes": len(file_bytes),
        "content_hash": content_hash,
        "bundle_hash": bundle_hash,
        "render_ms": render_ms,
        "error": None,
    }


def health():
    """Return renderer engine health status."""
    if not RENDERER_STATUS:
        _load_renderers()
    return {
        "engine": "WINDI Document Renderer",
        "version": "1.0.0",
        "renderers": RENDERER_STATUS,
        "ready_formats": [f for f, s in RENDERER_STATUS.items() if s == "ready"],
        "output_dir": str(Path(__file__).parent / "output"),
        "output_files": len(list((Path(__file__).parent / "output").glob("*"))) if (Path(__file__).parent / "output").exists() else 0,
    }


# ── Internal Helpers ──

FORMAT_MAP = {
    "invoice": "xlsx",
    "rechnung": "xlsx",
    "presentation": "pptx",
    "communique": "pdf",
    "governance_decision": "pdf",
    "certificate": "pdf",
    "security_advisory": "pdf",
}

TIER_FORMATS = {
    "FREE": ["docx", "pdf", "xlsx", "pptx"],
    "MED": ["docx", "pdf", "xlsx", "pptx"],
    "HIGH": ["docx", "pdf", "xlsx", "pptx", "jmpg"],
}


def _resolve_format(doc_type, tier, intent=None):
    """Determine output format from doc type, tier, and explicit intent.format."""
    allowed = TIER_FORMATS.get(tier, ["docx"])
    # 1. Respect explicit format from intent (user/UI chose this)
    if intent and isinstance(intent, dict):
        explicit = intent.get("format")
        if explicit in allowed:
            return explicit
    # 2. Fall back to doc_type → format mapping
    preferred = FORMAT_MAP.get(doc_type, "docx")
    return preferred if preferred in allowed else "docx"


def _generate_filename(doc_type, language, fmt):
    """Generate a clean, unique filename."""
    type_labels = {
        "letter": "Brief", "memo": "Memo", "report": "Bericht",
        "contract": "Vertrag", "invoice": "Rechnung", "note": "Notiz",
        "email": "Email", "protocol": "Protokoll", "analysis": "Analyse",
        "presentation": "Praesentation", "communique": "Communique",
        "security_advisory": "Security-Advisory", "governance_decision": "Beschluss",
        "certificate": "Bescheinigung",
    }
    label = type_labels.get(doc_type, doc_type.replace("_", "-").title())
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    short_id = uuid.uuid4().hex[:6]
    return f"WINDI_{label}_{date_str}_{short_id}.{fmt}"


def _error_result(error_msg, fmt, t0):
    """Build error result dict."""
    return {
        "success": False,
        "filepath": None,
        "filename": None,
        "format": fmt,
        "size_bytes": 0,
        "content_hash": None,
        "bundle_hash": None,
        "render_ms": int((time.time() - t0) * 1000),
        "error": error_msg,
    }


# ── CLI Test ──
if __name__ == "__main__":
    info = init()
    print(json.dumps(info, indent=2))
    print("\nHealth:")
    print(json.dumps(health(), indent=2))

    # Quick test render
    if "docx" in RENDERERS:
        result = render_document(
            text="# Test Document\n\nThis is a test paragraph.\n\n## Section 2\n\nMore content here.",
            intent={"doc_type": "memo", "language": "en", "formality": "formal"},
            tier="HIGH",
        )
        print("\nTest render:")
        print(json.dumps(result, indent=2))
