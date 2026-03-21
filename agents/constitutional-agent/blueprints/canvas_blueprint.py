"""
W-CANVAS-001 — Canvas Architect Agent v1.1.0
WINDI Publishing House | Kempten, Bavaria

Generates SVG visualizations via Gemini API with forensic sealing.
"""

import os
import json
import uuid
import hashlib
import base64
import zipfile
import io
import httpx
import logging
from datetime import datetime, timezone
from typing import Optional, Union
from flask import Blueprint, request, jsonify

logger = logging.getLogger("W-CANVAS-001")

# ── Config ──────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
LEDGER_BASE    = os.getenv("LEDGER_URL", "http://127.0.0.1:8101")
QR_ENGINE_BASE = os.getenv("QR_ENGINE_URL", "http://127.0.0.1:8103")
CANVAS_VERSION = "1.1.0"
AGENT_ID       = "W-CANVAS-001"

canvas_bp = Blueprint("canvas", __name__, url_prefix="/canvas")

# ── Theme Palettes ─────────────────────────────────────────────
THEME_PALETTES = {
    "institutional": {"bg": "#F5F0E0", "card": "#FDFBF5", "text": "#2C2924", "accent": "#00BCD4", "gold": "#8B6914"},
    "dark": {"bg": "#0E0E14", "card": "#16161F", "text": "#E2E2EA", "accent": "#00BCD4", "gold": "#D4A843"},
    "dark_gold": {"bg": "#0A0A0A", "card": "#111111", "text": "#FFFFFF", "accent": "#D4A843", "gold": "#FFD700"},
    "minimal": {"bg": "#FFFFFF", "card": "#F8F8F8", "text": "#1A1A1A", "accent": "#333333", "gold": "#888888"},
    "technical": {"bg": "#0D1117", "card": "#161B22", "text": "#C9D1D9", "accent": "#58A6FF", "gold": "#F0E68C"},
    "noir": {"bg": "#0A0A10", "card": "#12121A", "text": "#E8E6E1", "accent": "#C9A84C", "gold": "#C9A84C"},
    "klar": {"bg": "#FAFAF8", "card": "#FFFFFF", "text": "#1A1A1A", "accent": "#8B7424", "gold": "#8B7424"},
}

# ── System Prompts ─────────────────────────────────────────────
SYSTEM_PROMPTS = {
    "flowchart": """Generate clean SVG flowcharts following these rules:
- Use rounded-rect for start/end nodes
- Use rect for process nodes
- Use diamond for decision nodes
- Use directional arrows with arrowheads
- SVG must have viewBox="0 0 900 600"
- Return ONLY the SVG code, no markdown fences, no explanation.""",

    "diagram": """Generate technical SVG diagrams:
- Clear visual hierarchy
- Proper spacing and alignment
- SVG must have viewBox="0 0 900 600"
- Return ONLY the SVG code, no markdown fences.""",

    "architecture": """Generate system architecture SVG diagrams:
- Show components as boxes with labels
- Show connections with arrows
- Use layers for different tiers (frontend, backend, database)
- SVG must have viewBox="0 0 1000 650"
- Return ONLY the SVG code, no markdown fences.""",

    "chart": """Generate data visualization SVG charts:
- Support bar, line, pie chart types
- Include axis labels and legends
- SVG must have viewBox="0 0 800 500"
- Return ONLY the SVG code, no markdown fences.""",

    "infographic": """Generate infographic SVG designs:
- Use icons and visual metaphors
- Clear information hierarchy
- SVG must have viewBox="0 0 800 700"
- Return ONLY the SVG code, no markdown fences.""",

    "timeline": """Generate timeline SVG visualizations:
- Horizontal or vertical timeline
- Clear date/event markers
- SVG must have viewBox="0 0 1000 400"
- Return ONLY the SVG code, no markdown fences.""",

    "_mermaid": """Generate valid Mermaid v10 diagram syntax.

CRITICAL RULES (Mermaid v10 strict):
- Use 'flowchart TD' or 'flowchart LR' (NOT 'graph TD')
- Node syntax: A[Rectangle] B(Rounded) C{Diamond} D([Stadium]) E[(Database)]
- Arrow syntax: --> (NOT ->)
- NO special characters inside node labels (no €, ñ, ü, ç, etc.)
- NO accented characters inside node text
- Labels must be ASCII-safe: use 'Euro' not '€', 'promocao' not 'promoção'
- MAXIMUM 15 nodes per diagram
- MAXIMUM 20 edges per diagram
- Each node ID must be unique (A, B, C... or node1, node2...)
- Subgraphs: subgraph Title ... end

VALID EXAMPLE:
flowchart TD
    A[User Request] --> B{Valid?}
    B -- Yes --> C[Process]
    B -- No --> D[Error]
    C --> E[Output]

INVALID (DO NOT USE):
- graph TD (use flowchart TD)
- A -> B (use A --> B)
- A[Preço: 13,30€] (use A[Price: 13.30 Euro])
- Special chars in labels

Return ONLY the Mermaid code, no markdown fences, no explanations."""
}

def resolve_style_directive(style: dict) -> str:
    """Build style directive for Gemini prompt."""
    theme_name = style.get("theme", "institutional")
    palette = THEME_PALETTES.get(theme_name, THEME_PALETTES["institutional"]).copy()

    # Allow overrides
    if style.get("background"):
        palette["bg"] = style["background"]
    if style.get("accent"):
        palette["accent"] = style["accent"]
    if style.get("gold"):
        palette["gold"] = style["gold"]

    font_family = style.get("font", "Bricolage Grotesque, sans-serif")

    return f"""STRICT colour palette (use these exact colours):
  background: {palette['bg']}
  card/container fill: {palette['card']}
  text: {palette['text']}
  accent/highlight: {palette['accent']}
  gold/brand: {palette['gold']}
Font family: {font_family}
Style: Clean, modern, professional. No gradients unless specifically requested."""


def call_gemini_sync(prompt: str, canvas_type: str, style: dict, fmt: str) -> str:
    """Synchronous Gemini API call."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not configured")

    key = "_mermaid" if fmt == "mermaid" else canvas_type
    system_text = SYSTEM_PROMPTS.get(key, SYSTEM_PROMPTS["diagram"])
    style_directive = resolve_style_directive(style)
    full_system = f"{system_text}\n\n{style_directive}"

    payload = {
        "system_instruction": {"parts": [{"text": full_system}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 8192,
            "topP": 0.85
        },
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

    import requests
    resp = requests.post(url, json=payload, timeout=90)

    if resp.status_code != 200:
        logger.error(f"Gemini API error: {resp.status_code} - {resp.text[:200]}")
        raise ValueError(f"Visualization engine error: {resp.status_code}")

    resp_json = resp.json()

    # === CANVAS SOVEREIGNTY METRICS ===
    try:
        usage = resp_json.get("usageMetadata", {})
        prompt_tokens = usage.get("promptTokenCount", 0)
        output_tokens = usage.get("candidatesTokenCount", 0)
        total_tokens = usage.get("totalTokenCount", prompt_tokens + output_tokens)
        # Gemini Flash pricing: $0.075/1M input, $0.30/1M output
        cost_usd = (prompt_tokens * 0.000000075) + (output_tokens * 0.0000003)
        sovereignty_log = (f"[CANVAS-SOVEREIGNTY] model={GEMINI_MODEL} type={canvas_type} "
                          f"prompt_tokens={prompt_tokens} output_tokens={output_tokens} "
                          f"total={total_tokens} cost_usd=${cost_usd:.6f}")
        logger.info(sovereignty_log)
        print(sovereignty_log, flush=True)
        # Write to dedicated metrics log
        with open("/opt/windi/logs/canvas-sovereignty.log", "a") as f:
            from datetime import datetime
            f.write(f"{datetime.now().isoformat()} {sovereignty_log}\n")
    except Exception as e:
        logger.warning(f"[CANVAS-SOVEREIGNTY] Token metrics unavailable: {e}")

    try:
        content = resp_json["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        logger.error(f"Gemini response parse error: {e}")
        raise ValueError("Visualization engine: unexpected response format.")

    # Clean markdown fences
    for fence in ("```svg", "```mermaid", "```xml", "```"):
        if content.startswith(fence):
            content = content[len(fence):]
    if content.endswith("```"):
        content = content[:-3]

    return content.strip()


def create_wcav_package(canvas_id: str, svg_content: str, metadata: dict) -> str:
    """Create .wcav package (ZIP with SVG + manifest) and return base64."""
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add SVG
        zf.writestr(f"{canvas_id}.svg", svg_content)

        # Add manifest
        manifest = {
            "canvas_id": canvas_id,
            "version": CANVAS_VERSION,
            "agent": AGENT_ID,
            "created_at": metadata.get("generated_at"),
            "content_hash": metadata.get("content_hash"),
            "canvas_type": metadata.get("canvas_type"),
            "format": "wcav-1.0"
        }
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))

    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')


# ── Endpoints ──────────────────────────────────────────────────

@canvas_bp.route("/status", methods=["GET"])
def canvas_status():
    """Health check and capability report."""
    gemini_ok = bool(GEMINI_API_KEY)

    return jsonify({
        "agent": AGENT_ID,
        "version": CANVAS_VERSION,
        "status": "operational" if gemini_ok else "degraded",
        "visualization": "ready" if gemini_ok else "not_configured",
        "model": GEMINI_MODEL if gemini_ok else "not_configured",
        "themes": list(THEME_PALETTES.keys()),
        "canvas_types": ["diagram", "flowchart", "chart", "infographic", "architecture", "timeline"],
        "formats": ["svg", "mermaid"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@canvas_bp.route("/generate", methods=["POST"])
def generate_canvas():
    """Generate visualization from prompt."""
    try:
        data = request.get_json() or {}

        prompt = data.get("prompt", "").strip()
        if not prompt:
            return jsonify({"success": False, "error": "prompt is required"}), 400

        canvas_type = data.get("canvas_type", "flowchart")
        fmt = data.get("format", "svg")
        wallet_id = data.get("wallet_id")
        seal_to_ledger = data.get("seal_to_ledger", True)
        pack_wcav = data.get("pack_wcav", True)

        # Parse style
        style_input = data.get("style", "institutional")
        if isinstance(style_input, str):
            style = {"theme": style_input}
        elif isinstance(style_input, dict):
            style = style_input
        else:
            style = {"theme": "institutional"}

        # Generate canvas ID
        canvas_id = str(uuid.uuid4()).replace("-", "")[:16].upper()
        generated_at = datetime.now(timezone.utc).isoformat()

        # Call Gemini
        content = call_gemini_sync(prompt, canvas_type, style, fmt)
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        response = {
            "success": True,
            "canvas_id": canvas_id,
            "canvas_type": canvas_type,
            "format": fmt,
            "content": content,
            "content_hash": content_hash,
            "generated_at": generated_at,
            "agent": AGENT_ID,
            "version": CANVAS_VERSION,
            "sealed": False,
            "receipt_id": None,
            "verify_url": None,
            "qr_data": None,
            "wcav_b64": None,
            "wcav_filename": None,
            "message": "Canvas generated successfully."
        }

        # Package as .wcav if requested
        if pack_wcav and fmt == "svg":
            wcav_b64 = create_wcav_package(canvas_id, content, {
                "generated_at": generated_at,
                "content_hash": content_hash,
                "canvas_type": canvas_type
            })
            response["wcav_b64"] = wcav_b64
            response["wcav_filename"] = f"WINDI-CANVAS-{canvas_id}.wcav"

        # Seal to Ledger if requested
        if seal_to_ledger:
            try:
                receipt_id = f"WINDI-CANVAS-{canvas_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

                ledger_payload = {
                    "receipt_id": receipt_id,
                    "actor": wallet_id or "anonymous",
                    "app": "canvas-gen7",
                    "doc_name": f"Canvas {canvas_type}",
                    "doc_type": "canvas",
                    "content_hash": content_hash,
                    "invariants": ["I9", "I11"],
                    "stage": "C6",
                    "metadata": {
                        "canvas_id": canvas_id,
                        "canvas_type": canvas_type,
                        "agent": AGENT_ID,
                        "version": CANVAS_VERSION
                    }
                }

                import requests
                ledger_resp = requests.post(
                    f"{LEDGER_BASE}/api/receipts",
                    json=ledger_payload,
                    timeout=10
                )

                if ledger_resp.status_code in (200, 201):
                    response["sealed"] = True
                    response["receipt_id"] = receipt_id
                    response["verify_url"] = f"https://windi-domain.com/verify-public/?id={receipt_id}"
                    response["message"] = "Canvas generated and sealed to Ledger."
                    logger.info(f"Canvas {canvas_id} sealed: {receipt_id}")
                else:
                    logger.warning(f"Ledger seal failed: {ledger_resp.status_code}")

            except Exception as e:
                logger.warning(f"Ledger seal error: {e}")

        return jsonify(response)

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 503
    except Exception as e:
        logger.exception("Canvas generation error")
        return jsonify({"success": False, "error": "Internal error"}), 500


@canvas_bp.route("/themes", methods=["GET"])
def list_themes():
    """List available themes with previews."""
    return jsonify({
        "themes": THEME_PALETTES,
        "default": "institutional"
    })


@canvas_bp.route("/types", methods=["GET"])
def list_canvas_types():
    """List available canvas types."""
    return jsonify({
        "types": [
            {"id": "flowchart", "name": "Flowchart", "description": "Process flows and decision trees"},
            {"id": "diagram", "name": "Diagram", "description": "Technical diagrams and schematics"},
            {"id": "architecture", "name": "Architecture", "description": "System architecture diagrams"},
            {"id": "chart", "name": "Chart", "description": "Data visualizations (bar, line, pie)"},
            {"id": "infographic", "name": "Infographic", "description": "Visual information design"},
            {"id": "timeline", "name": "Timeline", "description": "Chronological visualizations"},
        ]
    })
