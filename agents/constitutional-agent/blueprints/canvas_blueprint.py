"""
W-CANVAS-001 — Canvas Architect Agent v1.2.0
WINDI Publishing House | Kempten, Bavaria

Generates SVG/Mermaid visualizations via Gemini API with forensic sealing.
Integrates Canvas Sovereignty Gate v1.0 for tiered token management.

Invariantes: I1 · I9 · I10 · I11
Wisdom Block: WB-KNOW-SOVEREIGNTY-Q-20260318
"""

import os
import json
import uuid
import hashlib
import base64
import zipfile
import io
import re
import unicodedata
import httpx
import logging
from datetime import datetime, timezone
from typing import Optional, Union
from flask import Blueprint, request, jsonify

# ── Import Sovereignty Gate ──────────────────────────────────────────
from .canvas_sovereignty_gate import (
    sovereignty_gate,
    log_canvas_usage,
    build_canvas_system_prompt,
    DiagramType,
    CanvasModel,
    CanvasTier,
    GateDecision,
)

logger = logging.getLogger("W-CANVAS-001")

# ── Config ──────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
LEDGER_BASE    = os.getenv("LEDGER_URL", "http://127.0.0.1:8101")
QR_ENGINE_BASE = os.getenv("QR_ENGINE_URL", "http://127.0.0.1:8103")
CANVAS_VERSION = "1.4.0"
AGENT_ID       = "W-CANVAS-001"

# ═══════════════════════════════════════════════════════════════
# ENGINE B — HTML Dashboard Renderer (v1.3.0)
# ═══════════════════════════════════════════════════════════════

ENGINE_B_SYSTEM_PROMPT = """
You are W-CANVAS-001 Engine B, specialist in generating WINDI institutional dashboards.

ABSOLUTE RULE: Respond ONLY with valid JSON. Zero text before or after. Zero markdown.

REQUIRED SCHEMA:
{
  "title": "string — dashboard title (max 60 chars)",
  "subtitle": "string — context (max 80 chars)",
  "kpis": [
    {
      "label": "string (max 20 chars)",
      "value": "string (number or text, max 12 chars)",
      "unit": "string (%, ms, docs, etc — max 6 chars)",
      "trend": "up | down | neutral",
      "trend_value": "string (+3.2% — max 8 chars)",
      "color": "gold | teal | blue | green | red | purple"
    }
  ],
  "table": {
    "headers": ["string", ...],
    "rows": [["string", ...], ...]
  },
  "chart": {
    "type": "bar | line | donut",
    "title": "string",
    "labels": ["string", ...],
    "datasets": [{"label": "string", "data": [number, ...]}]
  },
  "status_items": [
    {"name": "string", "status": "online | standby | offline | warning", "detail": "string"}
  ]
}

CONTENT RULES:
- KPIs: max 6, min 2. Concise values.
- Table: max 5 columns, max 8 rows.
- Chart: max 8 labels. Coherent numeric data.
- Status items: max 8.
- Language: detect PT/DE/EN from prompt and use in dashboard.
- WINDI institutional theme — serious data, no obvious fiction.

NEVER include: markdown, explanatory text, apologies, double commas, NaN, null in text fields.
"""

ENGINE_B_THEMES = {
    "klar": {
        "bg": "#F5F0E0", "card_bg": "#FFFFFF", "border": "#D4C9A8",
        "text_primary": "#1A1A1A", "text_secondary": "#6B6B6B",
        "accent": "#8B6914", "accent_light": "#F0E8CC"
    },
    "noir": {
        "bg": "#0D0D0D", "card_bg": "#1A1A1A", "border": "#2A2A2A",
        "text_primary": "#F0ECE0", "text_secondary": "#888880",
        "accent": "#C4A435", "accent_light": "#2A2518"
    },
    "dark_gold": {
        "bg": "#0F0B05", "card_bg": "#1C1508", "border": "#3D2E0A",
        "text_primary": "#F5E6B0", "text_secondary": "#A08840",
        "accent": "#D4A017", "accent_light": "#2A1F05"
    },
    "sovereign": {
        "bg": "#080B12", "card_bg": "#0D1220", "border": "#1A2540",
        "text_primary": "#E0E8F5", "text_secondary": "#5A6E8A",
        "accent": "#3A7FD4", "accent_light": "#0D1A30"
    },
}

ENGINE_B_STATUS_COLORS = {
    "online":  {"bg": "#0F4A2A", "text": "#4ADE80", "dot": "#22C55E"},
    "standby": {"bg": "#3A3000", "text": "#FACC15", "dot": "#EAB308"},
    "offline": {"bg": "#3A0A0A", "text": "#F87171", "dot": "#EF4444"},
    "warning": {"bg": "#3A1800", "text": "#FB923C", "dot": "#F97316"},
}

ENGINE_B_KPI_COLORS = {
    "gold":   {"bg": "#2A1F05", "border": "#8B6914", "text": "#D4A017"},
    "teal":   {"bg": "#051A15", "border": "#0D6E56", "text": "#2DD4BF"},
    "blue":   {"bg": "#051030", "border": "#185FA5", "text": "#60A5FA"},
    "green":  {"bg": "#061A0A", "border": "#3B6D11", "text": "#4ADE80"},
    "red":    {"bg": "#200505", "border": "#991B1B", "text": "#F87171"},
    "purple": {"bg": "#100520", "border": "#534AB7", "text": "#A78BFA"},
}

# ═══════════════════════════════════════════════════════════════
# ENGINE C — UI Card Renderer (v1.4.0)
# ═══════════════════════════════════════════════════════════════

ENGINE_C_SYSTEM_PROMPT = """
You are W-CANVAS-001 Engine C, specialist in generating WINDI UI component cards.

ABSOLUTE RULE: Respond ONLY with valid JSON. Zero text before or after. Zero markdown.

REQUIRED SCHEMA:
{
  "card_type": "transaction | status | verification | alert | info",
  "icon": "shield | check | lock | warning | info | hash | document | verified",
  "icon_color": "green | gold | blue | red | purple",
  "title": "string — main headline (max 40 chars)",
  "subtitle": "string — secondary text (max 60 chars)",
  "hash": "string — cryptographic hash to display (optional, max 64 chars)",
  "hash_label": "string — label for hash (e.g. 'Forensic Hash', 'Transaction ID')",
  "status": "valid | pending | invalid | processing",
  "status_text": "string — human readable status (max 20 chars)",
  "timestamp": "string — ISO timestamp or relative time",
  "action_label": "string — CTA button text (optional, max 20 chars)",
  "metadata": [
    {"label": "string", "value": "string"}
  ]
}

DESIGN RULES:
- Icon should pulse/glow for 'valid' status
- Hash displayed in monospace, truncated with ... if needed
- Metadata: max 4 items
- Language: detect PT/DE/EN from prompt
- WINDI institutional aesthetic — serious, trustworthy

NEVER include: markdown, explanatory text, apologies, placeholder text like 'example'.
"""

ENGINE_C_ICONS = {
    "shield": "🛡️",
    "check": "✓",
    "lock": "🔒",
    "warning": "⚠️",
    "info": "ℹ️",
    "hash": "#",
    "document": "📄",
    "verified": "✅"
}

# ═══════════════════════════════════════════════════════════════
# ENGINE D — Document Proof Renderer (v1.4.0)
# ═══════════════════════════════════════════════════════════════

ENGINE_D_SYSTEM_PROMPT = """
You are W-CANVAS-001 Engine D, specialist in generating WINDI official document certificates.

ABSOLUTE RULE: Respond ONLY with valid JSON. Zero text before or after. Zero markdown.

REQUIRED SCHEMA:
{
  "doc_type": "certificate | receipt | attestation | validation",
  "title": "string — document title (max 60 chars)",
  "subtitle": "string — document subtitle (max 80 chars)",
  "issuer": {
    "name": "string — issuing authority",
    "role": "string — role/department",
    "logo_text": "string — text for logo placeholder (e.g. 'WINDI')"
  },
  "subject": {
    "description": "string — what is being certified (max 200 chars)"
  },
  "details": [
    {"label": "string", "value": "string"}
  ],
  "validity": {
    "issued_at": "string — ISO date",
    "valid_until": "string — ISO date or 'Perpetual'",
    "jurisdiction": "string — e.g. 'EU/DE', 'WINDI Ledger'"
  },
  "integrity": {
    "hash": "string — SHA-256 hash",
    "ledger_id": "string — Ledger receipt ID",
    "qr_placeholder": true
  },
  "signatures": [
    {"name": "string", "role": "string", "type": "digital | human_approved"}
  ],
  "compliance": ["string — compliance standards, e.g. 'BaFin', 'eIDAS', 'GDPR'"],
  "footer_text": "string — legal disclaimer"
}

DESIGN RULES:
- Official document aesthetic: clean, formal, trustworthy
- QR code placeholder in bottom-right
- Digital signature block with timestamp
- Compliance seals/badges
- Language: detect PT/DE/EN from prompt
- Max 6 detail items, max 3 signatures, max 4 compliance badges

NEVER include: markdown, explanatory text, apologies.
"""

# ═══════════════════════════════════════════════════════════════
# ENGINE F — Blueprint/Schema Renderer (v1.4.0)
# ═══════════════════════════════════════════════════════════════

ENGINE_F_SYSTEM_PROMPT = """
You are W-CANVAS-001 Engine F, specialist in generating WINDI technical blueprints and system schemas.

ABSOLUTE RULE: Respond ONLY with valid JSON. Zero text before or after. Zero markdown.

REQUIRED SCHEMA:
{
  "blueprint_type": "architecture | flow | layer | component",
  "title": "string — blueprint title (max 50 chars)",
  "version": "string — version number",
  "layers": [
    {
      "name": "string — layer name",
      "level": number,
      "components": [
        {
          "id": "string — unique ID",
          "name": "string — component name",
          "type": "service | database | api | gateway | user | external",
          "status": "active | standby | deprecated",
          "port": "string — port number (optional)",
          "connections_to": ["string — IDs of connected components"]
        }
      ]
    }
  ],
  "legend": [
    {"symbol": "string", "meaning": "string"}
  ],
  "notes": ["string — technical notes"],
  "metadata": {
    "author": "string",
    "last_updated": "string — ISO date",
    "classification": "internal | public | confidential"
  }
}

DESIGN RULES:
- CAD/engineering blueprint aesthetic
- Grid background with subtle lines
- Components as boxes with clear labels
- Connections as lines with arrows
- Layer separation with horizontal bands
- Monospace font for technical details
- Max 4 layers, max 6 components per layer

NEVER include: markdown, explanatory text, apologies.
"""

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
    # SOVEREIGN — Constitutional Theme (WB-SOVEREIGN-CANVAS-20260321)
    # "KLAR é o que o sistema desenhou. SOVEREIGN é o que o Humano assinou."
    # Requer: DID verificado, I9 gate, hash de sessão
    "sovereign": {"bg": "#0A0A10", "card": "#12121A", "text": "#E8E6E1", "accent": "#C9A84C", "gold": "#C9A84C", "signature": "#8B6914"},
}

# ── SOVEREIGN Protocol (WB-SOVEREIGN-CANVAS-20260321) ──────────
SOVEREIGN_PROMPT_INJECTION = """
[SOVEREIGN PROTOCOL ACTIVE — WB-SOVEREIGN-CANVAS-20260321]

Este diagrama é uma PEÇA DE GOVERNANÇA institucional assinada digitalmente.

REGRAS OBRIGATÓRIAS:
1. Reservar zona inferior (últimos 60px do viewBox) para RODAPÉ FORENSE
2. Rodapé contém: [AUTOR] | [WALLET_ID] | [HASH] | [DATA]
3. Máximo 10 nós de conteúdo — o rodapé é o 11º nó constitucional
4. Estrutura austera, simétrica, inquestionável
5. Tons de autoridade: Deep Noir (#0A0A10) + Gold Seal (#C9A84C)
6. SEM gradientes decorativos — simplicidade institucional

O rodapé deve ser um <g id="sovereign-footer"> com:
- Linha separadora horizontal dourada
- Texto pequeno (10px) com os 4 campos acima
- Use placeholders: {{AUTHOR}}, {{WALLET_ID}}, {{HASH}}, {{DATE}}

Este diagrama será selado no Forensic Ledger após aprovação humana (I9).
"""

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
- Use 'flowchart TD' or 'flowchart LR' for flowcharts (NOT 'graph TD')
- For TIMELINE requests, use 'timeline' directive (see example below)
- Node syntax: A[Rectangle] B(Rounded) C{Diamond} D([Stadium]) E[(Database)]
- Arrow syntax: --> (NOT ->)
- NO special characters inside node labels (no €, ñ, ü, ç, etc.)
- NO accented characters inside node text
- Labels must be ASCII-safe: use 'Euro' not '€', 'promocao' not 'promoção'
- MAXIMUM 15 nodes per diagram
- MAXIMUM 20 edges per diagram
- TEXT LENGTH: Maximum 20 characters per node label (abbreviate if needed)
- Each node ID must be unique (A, B, C... or node1, node2...)

TIMELINE EXAMPLE (use when user asks for timeline/cronologia/evolução):
timeline
    title Evolution Timeline
    2025 : Basic Setup
    Jan 2026 : Integration
    Mar 2026 : Canvas Live
    Dec 2026 : Full Autonomy

FLOWCHART EXAMPLE:
flowchart TD
    A[User Request] --> B{Valid?}
    B -- Yes --> C[Process]
    B -- No --> D[Error]
    C --> E[Output]

INVALID (DO NOT USE):
- graph TD (use flowchart TD)
- A -> B (use A --> B)
- A[Preço: 13,30€] (use A[Price: 13.30 Euro])
- Long text that will be truncated
- Special chars in labels

Return ONLY the Mermaid code, no markdown fences, no explanations."""
}

def sanitize_mermaid(code: str) -> str:
    """
    Sanitiza código Mermaid antes de enviar ao frontend.
    Engine A Stability Layer — WINDI Canvas v1.3.0

    Regras aplicadas:
    - Remove diacríticos fora de aspas (ã→a, ç→c, é→e)
    - Protege conteúdo entre aspas (mantém intacto)
    - Remove caracteres perigosos para o parser fora de aspas: ? !
    - Preserva directivas Mermaid (%%{...}%%)
    """
    if not code or not isinstance(code, str):
        return code

    def strip_accents(s: str) -> str:
        return ''.join(
            c for c in unicodedata.normalize('NFD', s)
            if unicodedata.category(c) != 'Mn'
        )

    def sanitize_outside_quotes(segment: str) -> str:
        clean = strip_accents(segment)
        clean = re.sub(r'(?<!["\'])[?!](?!["\'])', '', clean)
        return clean

    result_lines = []
    for line in code.split('\n'):
        if line.strip().startswith('%%'):
            result_lines.append(line)
            continue
        parts = re.split(r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')', line)
        sanitized_parts = []
        for part in parts:
            if (part.startswith('"') and part.endswith('"')) or \
               (part.startswith("'") and part.endswith("'")):
                sanitized_parts.append(part)
            else:
                sanitized_parts.append(sanitize_outside_quotes(part))
        result_lines.append(''.join(sanitized_parts))
    return '\n'.join(result_lines)


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


def call_gemini_sync(prompt: str, canvas_type: str, style: dict, fmt: str, decision: GateDecision = None) -> str:
    """Synchronous Gemini API call with Sovereignty Gate integration."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not configured")

    # ═══════════════════════════════════════════════════════════════
    # USE SOVEREIGNTY GATE SYSTEM PROMPT IF PROVIDED
    # ═══════════════════════════════════════════════════════════════
    if decision and decision.model != CanvasModel.LOCAL:
        # Map canvas_type to DiagramType for system prompt
        dtype_map = {
            "flowchart": DiagramType.FLOWCHART,
            "mindmap": DiagramType.MINDMAP,
            "timeline": DiagramType.TIMELINE,
            "sequence": DiagramType.SEQUENCE,
            "gantt": DiagramType.GANTT,
        }
        dtype = dtype_map.get(canvas_type, DiagramType.FLOWCHART)
        theme = style.get("theme", "institutional")
        full_system = build_canvas_system_prompt(dtype, theme, decision.model)
        max_tokens = decision.max_tokens * 2  # Allow headroom for output
        model_name = decision.model.value
    else:
        # Legacy path (backwards compatibility)
        key = "_mermaid" if fmt == "mermaid" else canvas_type
        system_text = SYSTEM_PROMPTS.get(key, SYSTEM_PROMPTS["diagram"])
        style_directive = resolve_style_directive(style)
        full_system = f"{system_text}\n\n{style_directive}"
        max_tokens = 8192
        model_name = GEMINI_MODEL

    payload = {
        "system_instruction": {"parts": [{"text": full_system}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": max_tokens,
            "topP": 0.85
        },
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"

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

    content = content.strip()

    # ── Engine A Sanitizer (v1.3.0) ─────────────────────────────────
    # Sanitize Mermaid output to prevent parser errors from diacritics
    if "flowchart" in content or "graph " in content or "timeline" in content:
        content = sanitize_mermaid(content)
        logger.debug("[SANITIZER] Mermaid output sanitized")

    return content


def engine_b_json_to_html(data: dict, theme_name: str = "dark_gold", receipt_id: str = None) -> str:
    """
    ENGINE B — Convert JSON to HTML Dashboard.
    Returns complete HTML string for iframe rendering.
    """
    t = ENGINE_B_THEMES.get(theme_name, ENGINE_B_THEMES["dark_gold"])
    title = data.get("title", "WINDI Dashboard")
    subtitle = data.get("subtitle", "")
    kpis = data.get("kpis", [])[:6]
    table = data.get("table", {})
    chart = data.get("chart", {})
    statuses = data.get("status_items", [])[:8]
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # KPI Cards
    kpi_html = ""
    for kpi in kpis:
        c = ENGINE_B_KPI_COLORS.get(kpi.get("color", "gold"), ENGINE_B_KPI_COLORS["gold"])
        trend_sym = {"up": "↑", "down": "↓", "neutral": "→"}.get(kpi.get("trend", "neutral"), "→")
        trend_cls = {"up": "up", "down": "dn", "neutral": "nt"}.get(kpi.get("trend", "neutral"), "nt")
        kpi_html += f'''<div class="kpi" style="background:{c['bg']};border-color:{c['border']}">
            <div class="kpi-lbl">{kpi.get('label','')}</div>
            <div class="kpi-val" style="color:{c['text']}">{kpi.get('value','—')}<span class="kpi-unit">{kpi.get('unit','')}</span></div>
            <div class="kpi-tr {trend_cls}">{trend_sym} {kpi.get('trend_value','')}</div>
        </div>'''

    # Status Items
    status_html = ""
    for item in statuses:
        sc = ENGINE_B_STATUS_COLORS.get(item.get("status", "offline"), ENGINE_B_STATUS_COLORS["offline"])
        status_html += f'''<div class="sr">
            <span class="dot" style="background:{sc['dot']}"></span>
            <span class="sn">{item.get('name','')}</span>
            <span class="sb" style="background:{sc['bg']};color:{sc['text']}">{item.get('status','').upper()}</span>
            <span class="sd">{item.get('detail','')}</span>
        </div>'''

    # Table
    table_html = ""
    if table.get("headers"):
        headers = "".join(f"<th>{h}</th>" for h in table["headers"])
        rows = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in table.get("rows", [])[:8])
        table_html = f'<div class="card" style="margin-top:8px"><div class="card-title">Relatório</div><table class="tbl"><thead><tr>{headers}</tr></thead><tbody>{rows}</tbody></table></div>'

    # Chart.js
    chart_html = ""
    if chart.get("labels"):
        chart_json = json.dumps(chart, ensure_ascii=False)
        chart_html = f'''<div class="card">
            <div class="card-title">{chart.get('title','Gráfico')}</div>
            <canvas id="ch" height="160"></canvas>
        </div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
        <script>
        window.addEventListener('load',function(){{
            var cfg={chart_json};var ctx=document.getElementById('ch');if(!ctx)return;
            var colors=['#D4A017','#2DD4BF','#60A5FA','#4ADE80','#A78BFA','#F87171'];
            var datasets=(cfg.datasets||[]).map(function(ds,i){{return{{label:ds.label,data:ds.data,
                backgroundColor:cfg.type==='donut'?colors:colors[i%colors.length]+'50',
                borderColor:colors[i%colors.length],borderWidth:1.5,borderRadius:3}}}});
            new Chart(ctx,{{type:cfg.type==='donut'?'doughnut':(cfg.type||'bar'),
                data:{{labels:cfg.labels,datasets:datasets}},
                options:{{responsive:true,plugins:{{legend:{{labels:{{color:'{t["text_secondary"]}',font:{{size:10}}}}}}}},
                    scales:cfg.type==='donut'?{{}}:{{x:{{ticks:{{color:'{t["text_secondary"]}',font:{{size:9}}}},grid:{{color:'{t["border"]}'}}}},
                        y:{{ticks:{{color:'{t["text_secondary"]}',font:{{size:9}}}},grid:{{color:'{t["border"]}'}}}}}}
                }}
            }});
        }});
        </script>'''

    receipt_str = f" · Ledger: {receipt_id}" if receipt_id else ""

    html = f'''<!DOCTYPE html>
<html lang="pt"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{background:{t['bg']};font-family:system-ui,sans-serif;padding:16px;color:{t['text_primary']};font-size:12px}}
.header{{border-bottom:1px solid {t['border']};padding-bottom:10px;margin-bottom:12px}}
.title{{font-size:15px;font-weight:600;color:{t['accent']}}}
.sub{{font-size:10px;color:{t['text_secondary']};margin-top:3px}}
.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px;margin-bottom:12px}}
.kpi{{border:1px solid;border-radius:7px;padding:10px 12px}}
.kpi-lbl{{font-size:9px;text-transform:uppercase;letter-spacing:.08em;color:{t['text_secondary']};margin-bottom:4px}}
.kpi-val{{font-size:20px;font-weight:700;line-height:1}}
.kpi-unit{{font-size:10px;font-weight:400;margin-left:2px;opacity:.8}}
.kpi-tr{{font-size:9px;margin-top:4px;font-family:monospace}}
.up{{color:#4ADE80}}.dn{{color:#F87171}}.nt{{color:{t['text_secondary']}}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px}}
@media(max-width:600px){{.grid2{{grid-template-columns:1fr}}}}
.card{{background:{t['card_bg']};border:1px solid {t['border']};border-radius:7px;padding:12px}}
.card-title{{font-size:9px;text-transform:uppercase;letter-spacing:.08em;color:{t['accent']};margin-bottom:8px}}
.sr{{display:flex;align-items:center;gap:6px;padding:5px 0;border-bottom:1px solid {t['border']}40}}
.sr:last-child{{border-bottom:none}}
.dot{{width:6px;height:6px;border-radius:50%}}
.sn{{flex:1;font-size:11px}}
.sb{{font-size:8px;font-family:monospace;padding:1px 5px;border-radius:3px}}
.sd{{font-size:9px;color:{t['text_secondary']}}}
.tbl{{width:100%;border-collapse:collapse;font-size:10px}}
.tbl th{{text-align:left;padding:5px 7px;font-size:9px;text-transform:uppercase;color:{t['text_secondary']};border-bottom:1px solid {t['border']}}}
.tbl td{{padding:5px 7px;border-bottom:1px solid {t['border']}30}}
.tbl tr:last-child td{{border-bottom:none}}
.footer{{display:flex;justify-content:space-between;font-size:8px;color:{t['text_secondary']};border-top:1px solid {t['border']};padding-top:8px;margin-top:8px;font-family:monospace}}
</style></head>
<body>
<div class="header"><div class="title">{title}</div><div class="sub">{subtitle}</div></div>
<div class="kpi-grid">{kpi_html}</div>
<div class="grid2">
    <div class="card"><div class="card-title">Estado dos Serviços</div>{status_html}</div>
    {chart_html if chart_html else '<div></div>'}
</div>
{table_html}
<div class="footer">
    <span>AI processes. Human decides. WINDI guarantees.</span>
    <span>Liga IA+H · Kempten, Bavaria · {ts}{receipt_str}</span>
</div>
</body></html>'''
    return html


def engine_c_json_to_html(data: dict, theme_name: str = "dark_gold") -> str:
    """
    ENGINE C — Convert JSON to UI Card HTML.
    For transaction cards, verification badges, status displays.
    """
    t = ENGINE_B_THEMES.get(theme_name, ENGINE_B_THEMES["dark_gold"])

    card_type = data.get("card_type", "status")
    icon_key = data.get("icon", "shield")
    icon = ENGINE_C_ICONS.get(icon_key, "🛡️")
    icon_color = data.get("icon_color", "gold")
    title = data.get("title", "WINDI Card")
    subtitle = data.get("subtitle", "")
    hash_val = data.get("hash", "")
    hash_label = data.get("hash_label", "Hash")
    status = data.get("status", "valid")
    status_text = data.get("status_text", "Valid")
    timestamp = data.get("timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    action_label = data.get("action_label", "")
    metadata = data.get("metadata", [])[:4]

    # Status colors
    status_colors = {
        "valid": {"bg": "#0F4A2A", "text": "#4ADE80", "glow": "#22C55E"},
        "pending": {"bg": "#3A3000", "text": "#FACC15", "glow": "#EAB308"},
        "invalid": {"bg": "#3A0A0A", "text": "#F87171", "glow": "#EF4444"},
        "processing": {"bg": "#0D1A30", "text": "#60A5FA", "glow": "#3B82F6"},
    }
    sc = status_colors.get(status, status_colors["valid"])

    # Icon colors
    icon_colors = {
        "green": "#4ADE80", "gold": "#D4A017", "blue": "#60A5FA",
        "red": "#F87171", "purple": "#A78BFA"
    }
    ic = icon_colors.get(icon_color, "#D4A017")

    # Metadata HTML
    meta_html = ""
    for m in metadata:
        meta_html += f'<div class="meta-row"><span class="meta-label">{m.get("label", "")}</span><span class="meta-value">{m.get("value", "")}</span></div>'

    # Action button
    action_html = f'<button class="action-btn">{action_label}</button>' if action_label else ""

    # Hash display (truncated)
    hash_display = hash_val[:20] + "..." + hash_val[-8:] if len(hash_val) > 32 else hash_val
    hash_html = f'''<div class="hash-section">
        <div class="hash-label">{hash_label}</div>
        <div class="hash-value">{hash_display}</div>
    </div>''' if hash_val else ""

    pulse_class = "pulse" if status == "valid" else ""

    html = f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{background:{t['bg']};font-family:system-ui,sans-serif;padding:20px;display:flex;justify-content:center;align-items:center;min-height:100vh}}
.card{{background:{t['card_bg']};border:1px solid {t['border']};border-radius:16px;padding:24px;max-width:380px;width:100%;box-shadow:0 8px 32px rgba(0,0,0,0.3)}}
.card-header{{display:flex;align-items:center;gap:16px;margin-bottom:20px}}
.icon-circle{{width:56px;height:56px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:24px;background:{t['accent_light']};border:2px solid {ic};color:{ic}}}
.icon-circle.pulse{{animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{box-shadow:0 0 0 0 {ic}40}}50%{{box-shadow:0 0 0 12px {ic}00}}}}
.card-title{{font-size:18px;font-weight:600;color:{t['text_primary']}}}
.card-subtitle{{font-size:12px;color:{t['text_secondary']};margin-top:4px}}
.status-badge{{display:inline-flex;align-items:center;gap:6px;background:{sc['bg']};color:{sc['text']};padding:6px 12px;border-radius:20px;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:16px}}
.status-dot{{width:8px;height:8px;border-radius:50%;background:{sc['glow']};box-shadow:0 0 8px {sc['glow']}}}
.hash-section{{background:{t['bg']};border:1px solid {t['border']};border-radius:8px;padding:12px;margin-bottom:16px}}
.hash-label{{font-size:10px;text-transform:uppercase;letter-spacing:0.5px;color:{t['text_secondary']};margin-bottom:4px}}
.hash-value{{font-family:'JetBrains Mono',monospace;font-size:13px;color:{t['accent']};word-break:break-all}}
.meta-section{{margin-bottom:16px}}
.meta-row{{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid {t['border']}30}}
.meta-row:last-child{{border-bottom:none}}
.meta-label{{font-size:11px;color:{t['text_secondary']}}}
.meta-value{{font-size:11px;color:{t['text_primary']};font-weight:500}}
.timestamp{{font-size:10px;color:{t['text_secondary']};text-align:center;font-family:monospace}}
.action-btn{{width:100%;padding:12px;background:{t['accent']};color:{t['bg']};border:none;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;margin-top:12px;transition:opacity 0.2s}}
.action-btn:hover{{opacity:0.9}}
</style></head>
<body>
<div class="card">
    <div class="card-header">
        <div class="icon-circle {pulse_class}">{icon}</div>
        <div>
            <div class="card-title">{title}</div>
            <div class="card-subtitle">{subtitle}</div>
        </div>
    </div>
    <div class="status-badge"><span class="status-dot"></span>{status_text}</div>
    {hash_html}
    <div class="meta-section">{meta_html}</div>
    <div class="timestamp">{timestamp}</div>
    {action_html}
</div>
</body></html>'''
    return html


def engine_d_json_to_html(data: dict, theme_name: str = "klar") -> str:
    """
    ENGINE D — Convert JSON to Document Proof HTML.
    For certificates, attestations, official receipts.
    """
    t = ENGINE_B_THEMES.get(theme_name, ENGINE_B_THEMES["klar"])

    doc_type = data.get("doc_type", "certificate")
    title = data.get("title", "Official Certificate")
    subtitle = data.get("subtitle", "")
    issuer = data.get("issuer", {})
    subject = data.get("subject", {})
    details = data.get("details", [])[:6]
    validity = data.get("validity", {})
    integrity = data.get("integrity", {})
    signatures = data.get("signatures", [])[:3]
    compliance = data.get("compliance", [])[:4]
    footer_text = data.get("footer_text", "This document is digitally signed and verifiable via WINDI Forensic Ledger.")

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Details table
    details_html = ""
    for d in details:
        details_html += f'<tr><td class="detail-label">{d.get("label", "")}</td><td class="detail-value">{d.get("value", "")}</td></tr>'

    # Signatures
    sig_html = ""
    for s in signatures:
        sig_type_icon = "🔏" if s.get("type") == "digital" else "✍️"
        sig_html += f'''<div class="signature-block">
            <div class="sig-line"></div>
            <div class="sig-name">{s.get("name", "")}</div>
            <div class="sig-role">{sig_type_icon} {s.get("role", "")}</div>
        </div>'''

    # Compliance badges
    comp_html = ""
    for c in compliance:
        comp_html += f'<span class="compliance-badge">{c}</span>'

    # Hash display
    hash_val = integrity.get("hash", "")
    hash_display = hash_val[:16] + "..." + hash_val[-8:] if len(hash_val) > 28 else hash_val

    html = f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
<style>
@page{{size:A4;margin:2cm}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{background:{t['bg']};font-family:'Georgia',serif;padding:40px;color:{t['text_primary']};font-size:12px;max-width:800px;margin:0 auto}}
.doc-container{{background:#FFFFFF;border:2px solid {t['accent']};padding:48px;position:relative;box-shadow:0 4px 24px rgba(0,0,0,0.1)}}
.doc-header{{text-align:center;border-bottom:3px double {t['accent']};padding-bottom:24px;margin-bottom:32px}}
.logo-text{{font-size:28px;font-weight:700;color:{t['accent']};letter-spacing:3px;margin-bottom:8px}}
.doc-type{{font-size:10px;text-transform:uppercase;letter-spacing:2px;color:{t['text_secondary']};margin-bottom:16px}}
.doc-title{{font-size:22px;font-weight:700;color:{t['text_primary']};margin-bottom:8px}}
.doc-subtitle{{font-size:13px;color:{t['text_secondary']};font-style:italic}}
.issuer-block{{text-align:center;margin-bottom:24px;padding:16px;background:{t['bg']};border-radius:4px}}
.issuer-name{{font-size:14px;font-weight:600}}
.issuer-role{{font-size:11px;color:{t['text_secondary']}}}
.subject-block{{background:{t['bg']};padding:20px;border-left:4px solid {t['accent']};margin-bottom:24px}}
.subject-desc{{font-size:13px;line-height:1.6}}
.details-table{{width:100%;border-collapse:collapse;margin-bottom:24px}}
.detail-label{{padding:10px 16px;background:{t['bg']};font-weight:600;width:40%;border:1px solid {t['border']}}}
.detail-value{{padding:10px 16px;border:1px solid {t['border']}}}
.validity-row{{display:flex;justify-content:space-between;margin-bottom:24px;font-size:11px}}
.validity-item span{{display:block}}
.validity-item strong{{color:{t['accent']}}}
.integrity-block{{background:#F8F8F5;border:1px solid {t['border']};padding:16px;margin-bottom:24px;display:flex;justify-content:space-between;align-items:center}}
.hash-info{{flex:1}}
.hash-label{{font-size:9px;text-transform:uppercase;color:{t['text_secondary']};margin-bottom:4px}}
.hash-value{{font-family:'Courier New',monospace;font-size:11px;color:{t['accent']}}}
.ledger-id{{font-size:10px;color:{t['text_secondary']};margin-top:4px}}
.qr-placeholder{{width:80px;height:80px;border:2px dashed {t['border']};display:flex;align-items:center;justify-content:center;color:{t['text_secondary']};font-size:9px}}
.signatures-row{{display:flex;justify-content:space-around;margin-bottom:24px;padding-top:24px;border-top:1px solid {t['border']}}}
.signature-block{{text-align:center;min-width:150px}}
.sig-line{{width:120px;border-bottom:1px solid {t['text_primary']};margin:0 auto 8px}}
.sig-name{{font-size:12px;font-weight:600}}
.sig-role{{font-size:10px;color:{t['text_secondary']}}}
.compliance-row{{display:flex;gap:8px;justify-content:center;margin-bottom:24px}}
.compliance-badge{{font-size:9px;padding:4px 10px;background:{t['accent']};color:#FFFFFF;border-radius:12px;text-transform:uppercase;letter-spacing:0.5px}}
.footer{{text-align:center;font-size:9px;color:{t['text_secondary']};border-top:1px solid {t['border']};padding-top:16px;font-style:italic}}
.watermark{{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-45deg);font-size:72px;color:{t['accent']}10;pointer-events:none;z-index:0}}
</style></head>
<body>
<div class="doc-container">
    <div class="watermark">WINDI</div>
    <div class="doc-header">
        <div class="logo-text">{issuer.get("logo_text", "WINDI")}</div>
        <div class="doc-type">{doc_type.upper()}</div>
        <div class="doc-title">{title}</div>
        <div class="doc-subtitle">{subtitle}</div>
    </div>
    <div class="issuer-block">
        <div class="issuer-name">{issuer.get("name", "WINDI Publishing House")}</div>
        <div class="issuer-role">{issuer.get("role", "Forensic Engine Authority")}</div>
    </div>
    <div class="subject-block">
        <div class="subject-desc">{subject.get("description", "")}</div>
    </div>
    <table class="details-table">{details_html}</table>
    <div class="validity-row">
        <div class="validity-item"><span>Issued</span><strong>{validity.get("issued_at", ts)}</strong></div>
        <div class="validity-item"><span>Valid Until</span><strong>{validity.get("valid_until", "Perpetual")}</strong></div>
        <div class="validity-item"><span>Jurisdiction</span><strong>{validity.get("jurisdiction", "WINDI Ledger")}</strong></div>
    </div>
    <div class="integrity-block">
        <div class="hash-info">
            <div class="hash-label">Forensic Hash (SHA-256)</div>
            <div class="hash-value">{hash_display}</div>
            <div class="ledger-id">Ledger ID: {integrity.get("ledger_id", "Pending Seal")}</div>
        </div>
        <div class="qr-placeholder">QR Code</div>
    </div>
    <div class="signatures-row">{sig_html}</div>
    <div class="compliance-row">{comp_html}</div>
    <div class="footer">{footer_text}<br>Generated: {ts}</div>
</div>
</body></html>'''
    return html


def engine_f_json_to_html(data: dict, theme_name: str = "noir") -> str:
    """
    ENGINE F — Convert JSON to Blueprint/Schema HTML.
    For technical architecture diagrams, system schemas.
    """
    t = ENGINE_B_THEMES.get(theme_name, ENGINE_B_THEMES["noir"])

    blueprint_type = data.get("blueprint_type", "architecture")
    title = data.get("title", "System Blueprint")
    version = data.get("version", "1.0")
    layers = data.get("layers", [])[:4]
    legend = data.get("legend", [])
    notes = data.get("notes", [])[:3]
    metadata = data.get("metadata", {})

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Component type colors
    comp_colors = {
        "service": {"bg": "#1A2F4A", "border": "#3B82F6", "text": "#60A5FA"},
        "database": {"bg": "#1A3A2A", "border": "#22C55E", "text": "#4ADE80"},
        "api": {"bg": "#2A1F3A", "border": "#A855F7", "text": "#C084FC"},
        "gateway": {"bg": "#3A2A1A", "border": "#F59E0B", "text": "#FBBF24"},
        "user": {"bg": "#1A1A2A", "border": "#6366F1", "text": "#818CF8"},
        "external": {"bg": "#2A1A1A", "border": "#EF4444", "text": "#F87171"},
    }

    # Status indicators
    status_icons = {"active": "●", "standby": "◐", "deprecated": "○"}

    # Build layers HTML
    layers_html = ""
    component_positions = {}
    y_offset = 80

    for layer in layers:
        layer_name = layer.get("name", "Layer")
        components = layer.get("components", [])[:6]

        layers_html += f'<div class="layer" style="top:{y_offset}px"><div class="layer-label">{layer_name}</div>'

        x_offset = 120
        for comp in components:
            comp_id = comp.get("id", "")
            comp_name = comp.get("name", "Component")
            comp_type = comp.get("type", "service")
            comp_status = comp.get("status", "active")
            comp_port = comp.get("port", "")

            cc = comp_colors.get(comp_type, comp_colors["service"])
            status_icon = status_icons.get(comp_status, "●")

            component_positions[comp_id] = (x_offset + 60, y_offset + 30)

            port_html = f'<div class="comp-port">:{comp_port}</div>' if comp_port else ""

            layers_html += f'''<div class="component" style="left:{x_offset}px;background:{cc['bg']};border-color:{cc['border']}">
                <div class="comp-status" style="color:{cc['text']}">{status_icon}</div>
                <div class="comp-name">{comp_name}</div>
                <div class="comp-type" style="color:{cc['text']}">{comp_type}</div>
                {port_html}
            </div>'''
            x_offset += 140

        layers_html += '</div>'
        y_offset += 100

    # Legend
    legend_html = ""
    for item in legend[:6]:
        legend_html += f'<div class="legend-item"><span class="legend-symbol">{item.get("symbol", "●")}</span><span>{item.get("meaning", "")}</span></div>'

    # Notes
    notes_html = ""
    for note in notes:
        notes_html += f'<div class="note">• {note}</div>'

    # Classification badge
    classification = metadata.get("classification", "internal").upper()

    html = f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{background:{t['bg']};font-family:'JetBrains Mono',monospace;padding:20px;color:{t['text_primary']};font-size:11px}}
.blueprint{{background:{t['card_bg']};border:1px solid {t['border']};position:relative;min-height:500px;background-image:linear-gradient({t['border']}20 1px,transparent 1px),linear-gradient(90deg,{t['border']}20 1px,transparent 1px);background-size:20px 20px}}
.header{{background:{t['bg']};border-bottom:1px solid {t['border']};padding:12px 16px;display:flex;justify-content:space-between;align-items:center}}
.title-block{{}}
.title{{font-size:14px;font-weight:600;color:{t['accent']}}}
.subtitle{{font-size:10px;color:{t['text_secondary']}}}
.meta-block{{text-align:right}}
.version{{font-size:10px;color:{t['accent']}}}
.classification{{font-size:8px;padding:2px 8px;background:{t['accent']};color:{t['bg']};border-radius:2px;margin-top:4px;display:inline-block}}
.canvas{{position:relative;padding:20px;min-height:400px}}
.layer{{position:absolute;left:0;right:0;height:90px;border-bottom:1px dashed {t['border']}50}}
.layer-label{{position:absolute;left:8px;top:4px;font-size:9px;color:{t['text_secondary']};text-transform:uppercase;letter-spacing:1px;writing-mode:vertical-lr;transform:rotate(180deg)}}
.component{{position:absolute;width:120px;padding:10px;border:1px solid;border-radius:4px;text-align:center}}
.comp-status{{font-size:8px;position:absolute;top:4px;right:6px}}
.comp-name{{font-size:11px;font-weight:600;margin-bottom:4px}}
.comp-type{{font-size:8px;text-transform:uppercase}}
.comp-port{{font-size:9px;color:{t['text_secondary']};margin-top:4px}}
.footer{{background:{t['bg']};border-top:1px solid {t['border']};padding:12px 16px;display:flex;justify-content:space-between}}
.legend{{display:flex;gap:16px}}
.legend-item{{display:flex;align-items:center;gap:4px;font-size:9px;color:{t['text_secondary']}}}
.legend-symbol{{color:{t['accent']}}}
.notes{{max-width:300px}}
.note{{font-size:9px;color:{t['text_secondary']};margin-bottom:4px}}
.timestamp{{font-size:8px;color:{t['text_secondary']};position:absolute;bottom:8px;right:16px}}
</style></head>
<body>
<div class="blueprint">
    <div class="header">
        <div class="title-block">
            <div class="title">{title}</div>
            <div class="subtitle">{blueprint_type.upper()} DIAGRAM</div>
        </div>
        <div class="meta-block">
            <div class="version">v{version}</div>
            <div class="classification">{classification}</div>
        </div>
    </div>
    <div class="canvas">{layers_html}</div>
    <div class="footer">
        <div class="legend">{legend_html}</div>
        <div class="notes">{notes_html}</div>
    </div>
    <div class="timestamp">{metadata.get("author", "W-CANVAS-001")} · {ts}</div>
</div>
</body></html>'''
    return html


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
    """Health check and capability report with Sovereignty Gate."""
    gemini_ok = bool(GEMINI_API_KEY)

    return jsonify({
        "agent": AGENT_ID,
        "version": CANVAS_VERSION,
        "status": "operational" if gemini_ok else "degraded",
        "visualization": "ready" if gemini_ok else "not_configured",
        "model": GEMINI_MODEL if gemini_ok else "not_configured",
        "themes": list(THEME_PALETTES.keys()),
        "canvas_types": ["diagram", "flowchart", "chart", "infographic", "architecture", "timeline", "dashboard", "ui-card", "doc-proof", "blueprint"],
        "formats": ["svg", "mermaid", "html"],
        "engines": {"A": "Mermaid/SVG", "B": "HTML Dashboard"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        # ── Sovereignty Gate v1.0 ─────────────────────────────────────
        "sovereignty_gate": {
            "version": "1.0.0",
            "tiers": ["FREE", "MED", "HIGH"],
            "local_templates": ["windi_pipeline", "agentes_windi", "did_flow", "constellation", "document_seal", "windi_evolution"],
            "principle": "Economy enables Quality — O externo sustenta. O interno orienta.",
        }
    })


@canvas_bp.route("/generate", methods=["POST"])
def generate_canvas():
    """Generate visualization from prompt with Sovereignty Gate tiering."""
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
        tier = data.get("tier", "MED")  # Default MED for authenticated users

        # Parse style
        style_input = data.get("style", "institutional")
        if isinstance(style_input, str):
            style = {"theme": style_input}
        elif isinstance(style_input, dict):
            style = style_input
        else:
            style = {"theme": "institutional"}

        # ═══════════════════════════════════════════════════════════════
        # SOVEREIGN PROTOCOL — WB-SOVEREIGN-CANVAS-20260321
        # "KLAR é o que o sistema desenhou. SOVEREIGN é o que o Humano assinou."
        # SOVEREIGN requer DID verificado (I9 Gate)
        # ═══════════════════════════════════════════════════════════════
        theme_name = style.get("theme", "institutional").lower()
        if theme_name == "sovereign":
            if not wallet_id:
                return jsonify({
                    "success": False,
                    "error": "SOVEREIGN_REQUIRES_DID",
                    "message": "O tema SOVEREIGN requer identidade verificada. Por favor, conecta a tua Wallet DID.",
                    "protocol": "WB-SOVEREIGN-CANVAS-20260321",
                    "principle": "KLAR é o que o sistema desenhou. SOVEREIGN é o que o Humano assinou."
                }), 403
            # SOVEREIGN auto-escalates to HIGH tier
            tier = "HIGH"
            logger.info(f"[SOVEREIGN] wallet_id={wallet_id[:16]}... → tier escalated to HIGH")

        # Generate canvas ID
        canvas_id = str(uuid.uuid4()).replace("-", "")[:16].upper()
        generated_at = datetime.now(timezone.utc).isoformat()

        # ═══════════════════════════════════════════════════════════════
        # ENGINE B — HTML Dashboard Renderer (v1.3.0)
        # ═══════════════════════════════════════════════════════════════
        if canvas_type == "dashboard":
            logger.info(f"[ENGINE-B] Dashboard request canvas_id={canvas_id}")

            # Call Gemini with Engine B system prompt
            import requests as req
            payload = {
                "system_instruction": {"parts": [{"text": ENGINE_B_SYSTEM_PROMPT}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 4096, "topP": 0.85}
            }
            model = "gemini-2.5-flash" if tier in ("FREE", "MED") else "gemini-2.5-pro"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"

            try:
                resp = req.post(url, json=payload, timeout=90)
                resp.raise_for_status()
                resp_json = resp.json()
                raw_json = resp_json["candidates"][0]["content"]["parts"][0]["text"]

                # Clean JSON fences
                raw_json = raw_json.strip()
                if raw_json.startswith("```"):
                    raw_json = raw_json.split("\n", 1)[1] if "\n" in raw_json else raw_json[3:]
                if raw_json.endswith("```"):
                    raw_json = raw_json[:-3]

                dashboard_data = json.loads(raw_json.strip())
            except Exception as e:
                logger.error(f"[ENGINE-B] LLM error: {e}")
                # Fallback demo dashboard
                dashboard_data = {
                    "title": "WINDI Dashboard",
                    "subtitle": "Fallback — LLM unavailable",
                    "kpis": [
                        {"label": "Status", "value": "OK", "unit": "", "trend": "neutral", "trend_value": "→", "color": "gold"},
                        {"label": "Agents", "value": "7", "unit": "", "trend": "up", "trend_value": "+1", "color": "teal"},
                    ],
                    "status_items": [
                        {"name": "W-CANVAS-001", "status": "online", "detail": "Engine B Active"},
                    ],
                    "table": {},
                    "chart": {}
                }

            html_content = engine_b_json_to_html(dashboard_data, theme_name, None)
            content_hash = hashlib.sha256(html_content.encode()).hexdigest()

            return jsonify({
                "success": True,
                "canvas_id": canvas_id,
                "canvas_type": "dashboard",
                "format": "html",
                "engine": "B",
                "render_type": "html",
                "html": html_content,
                "content": html_content,
                "content_hash": content_hash,
                "generated_at": generated_at,
                "agent": AGENT_ID,
                "version": CANVAS_VERSION,
                "sealed": False,
                "message": "Dashboard generated via Engine B."
            })

        # ═══════════════════════════════════════════════════════════════
        # ENGINE C — UI Card Renderer (v1.4.0)
        # ═══════════════════════════════════════════════════════════════
        if canvas_type == "ui-card":
            logger.info(f"[ENGINE-C] UI Card request canvas_id={canvas_id}")

            import requests as req
            payload = {
                "system_instruction": {"parts": [{"text": ENGINE_C_SYSTEM_PROMPT}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2048, "topP": 0.85}
            }
            model = "gemini-2.5-flash" if tier in ("FREE", "MED") else "gemini-2.5-pro"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"

            try:
                resp = req.post(url, json=payload, timeout=60)
                resp.raise_for_status()
                resp_json = resp.json()
                raw_json = resp_json["candidates"][0]["content"]["parts"][0]["text"]

                raw_json = raw_json.strip()
                if raw_json.startswith("```"):
                    raw_json = raw_json.split("\n", 1)[1] if "\n" in raw_json else raw_json[3:]
                if raw_json.endswith("```"):
                    raw_json = raw_json[:-3]

                card_data = json.loads(raw_json.strip())
            except Exception as e:
                logger.error(f"[ENGINE-C] LLM error: {e}")
                card_data = {
                    "card_type": "verification",
                    "icon": "shield",
                    "icon_color": "gold",
                    "title": "WINDI Verification",
                    "subtitle": "Fallback — LLM unavailable",
                    "status": "pending",
                    "status_text": "Processing",
                    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                    "metadata": []
                }

            html_content = engine_c_json_to_html(card_data, theme_name)
            content_hash = hashlib.sha256(html_content.encode()).hexdigest()

            return jsonify({
                "success": True,
                "canvas_id": canvas_id,
                "canvas_type": "ui-card",
                "format": "html",
                "engine": "C",
                "render_type": "html",
                "html": html_content,
                "content": html_content,
                "content_hash": content_hash,
                "generated_at": generated_at,
                "agent": AGENT_ID,
                "version": CANVAS_VERSION,
                "sealed": False,
                "message": "UI Card generated via Engine C."
            })

        # ═══════════════════════════════════════════════════════════════
        # ENGINE D — Document Proof Renderer (v1.4.0)
        # ═══════════════════════════════════════════════════════════════
        if canvas_type == "doc-proof":
            logger.info(f"[ENGINE-D] Doc Proof request canvas_id={canvas_id}")

            import requests as req
            payload = {
                "system_instruction": {"parts": [{"text": ENGINE_D_SYSTEM_PROMPT}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 3072, "topP": 0.85}
            }
            model = "gemini-2.5-flash" if tier in ("FREE", "MED") else "gemini-2.5-pro"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"

            try:
                resp = req.post(url, json=payload, timeout=60)
                resp.raise_for_status()
                resp_json = resp.json()
                raw_json = resp_json["candidates"][0]["content"]["parts"][0]["text"]

                raw_json = raw_json.strip()
                if raw_json.startswith("```"):
                    raw_json = raw_json.split("\n", 1)[1] if "\n" in raw_json else raw_json[3:]
                if raw_json.endswith("```"):
                    raw_json = raw_json[:-3]

                doc_data = json.loads(raw_json.strip())
            except Exception as e:
                logger.error(f"[ENGINE-D] LLM error: {e}")
                doc_data = {
                    "doc_type": "certificate",
                    "title": "WINDI Certificate",
                    "subtitle": "Fallback — LLM unavailable",
                    "issuer": {"name": "WINDI Publishing House", "role": "Forensic Engine", "logo_text": "WINDI"},
                    "subject": {"description": "This certificate is pending generation."},
                    "details": [],
                    "validity": {"issued_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "valid_until": "Perpetual", "jurisdiction": "WINDI Ledger"},
                    "integrity": {"hash": "", "ledger_id": "Pending"},
                    "signatures": [],
                    "compliance": [],
                    "footer_text": "Document verification pending."
                }

            html_content = engine_d_json_to_html(doc_data, theme_name)
            content_hash = hashlib.sha256(html_content.encode()).hexdigest()

            return jsonify({
                "success": True,
                "canvas_id": canvas_id,
                "canvas_type": "doc-proof",
                "format": "html",
                "engine": "D",
                "render_type": "html",
                "html": html_content,
                "content": html_content,
                "content_hash": content_hash,
                "generated_at": generated_at,
                "agent": AGENT_ID,
                "version": CANVAS_VERSION,
                "sealed": False,
                "message": "Document Proof generated via Engine D."
            })

        # ═══════════════════════════════════════════════════════════════
        # ENGINE F — Blueprint/Schema Renderer (v1.4.0)
        # ═══════════════════════════════════════════════════════════════
        if canvas_type == "blueprint":
            logger.info(f"[ENGINE-F] Blueprint request canvas_id={canvas_id}")

            import requests as req
            payload = {
                "system_instruction": {"parts": [{"text": ENGINE_F_SYSTEM_PROMPT}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 3072, "topP": 0.85}
            }
            model = "gemini-2.5-flash" if tier in ("FREE", "MED") else "gemini-2.5-pro"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"

            try:
                resp = req.post(url, json=payload, timeout=60)
                resp.raise_for_status()
                resp_json = resp.json()
                raw_json = resp_json["candidates"][0]["content"]["parts"][0]["text"]

                raw_json = raw_json.strip()
                if raw_json.startswith("```"):
                    raw_json = raw_json.split("\n", 1)[1] if "\n" in raw_json else raw_json[3:]
                if raw_json.endswith("```"):
                    raw_json = raw_json[:-3]

                blueprint_data = json.loads(raw_json.strip())
            except Exception as e:
                logger.error(f"[ENGINE-F] LLM error: {e}")
                blueprint_data = {
                    "blueprint_type": "architecture",
                    "title": "WINDI Architecture",
                    "version": "1.0",
                    "layers": [
                        {
                            "name": "Services",
                            "level": 1,
                            "components": [
                                {"id": "canvas", "name": "W-CANVAS-001", "type": "service", "status": "active", "port": "8091", "connections_to": []}
                            ]
                        }
                    ],
                    "legend": [{"symbol": "●", "meaning": "Active"}, {"symbol": "○", "meaning": "Standby"}],
                    "notes": ["Fallback blueprint — LLM unavailable"],
                    "metadata": {"author": "W-CANVAS-001", "classification": "internal"}
                }

            html_content = engine_f_json_to_html(blueprint_data, theme_name)
            content_hash = hashlib.sha256(html_content.encode()).hexdigest()

            return jsonify({
                "success": True,
                "canvas_id": canvas_id,
                "canvas_type": "blueprint",
                "format": "html",
                "engine": "F",
                "render_type": "html",
                "html": html_content,
                "content": html_content,
                "content_hash": content_hash,
                "generated_at": generated_at,
                "agent": AGENT_ID,
                "version": CANVAS_VERSION,
                "sealed": False,
                "message": "Blueprint generated via Engine F."
            })

        # ═══════════════════════════════════════════════════════════════
        # ENGINE A — SOVEREIGNTY GATE INTEGRATION — v1.3.0
        # ═══════════════════════════════════════════════════════════════

        # Map canvas_type to DiagramType
        diagram_type_map = {
            "flowchart": DiagramType.FLOWCHART,
            "mindmap": DiagramType.MINDMAP,
            "timeline": DiagramType.TIMELINE,
            "sequence": DiagramType.SEQUENCE,
            "gantt": DiagramType.GANTT,
            "diagram": DiagramType.FLOWCHART,      # fallback
            "architecture": DiagramType.FLOWCHART,  # fallback
            "chart": DiagramType.FLOWCHART,         # fallback
            "infographic": DiagramType.FLOWCHART,   # fallback
        }
        diagram_type = diagram_type_map.get(canvas_type, DiagramType.FLOWCHART)

        # ── Gate Decision ─────────────────────────────────────────────
        decision = sovereignty_gate(prompt, diagram_type, tier, wallet_id)

        logger.info(
            f"[SOVEREIGNTY-GATE] canvas_id={canvas_id} tier={tier} "
            f"model={decision.model.value} budget={decision.max_tokens}tk "
            f"cost_est=${decision.cost_est:.6f}"
        )

        # ── LOCAL PATH: Template-based (zero external tokens) ────────
        if decision.model == CanvasModel.LOCAL:
            content = decision.local_template
            log_canvas_usage(canvas_id, wallet_id, diagram_type, decision, tokens_actual=0)
        else:
            # ── EXTERNAL PATH: Gemini API call ─────────────────────────
            # Use optimized system prompt from sovereignty gate
            content = call_gemini_sync(prompt, canvas_type, style, fmt, decision)

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
            "message": "Canvas generated successfully.",
            # ── Sovereignty Gate Metadata ─────────────────────────────
            "sovereignty": {
                "model": decision.model.value,
                "tier": decision.tier.value,
                "tokens_budget": decision.max_tokens,
                "cost_est_usd": decision.cost_est,
                "complexity": decision.complexity,
                "was_local": decision.model == CanvasModel.LOCAL,
                "gate_justification": decision.justification,
            }
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
            {"id": "flowchart", "name": "Flowchart", "description": "Process flows and decision trees", "engine": "A"},
            {"id": "diagram", "name": "Diagram", "description": "Technical diagrams and schematics", "engine": "A"},
            {"id": "architecture", "name": "Architecture", "description": "System architecture diagrams", "engine": "A"},
            {"id": "chart", "name": "Chart", "description": "Data visualizations (bar, line, pie)", "engine": "A"},
            {"id": "infographic", "name": "Infographic", "description": "Visual information design", "engine": "A"},
            {"id": "timeline", "name": "Timeline", "description": "Chronological visualizations", "engine": "A"},
            {"id": "dashboard", "name": "Dashboard", "description": "KPI dashboards with charts", "engine": "B"},
            {"id": "ui-card", "name": "UI Card", "description": "Transaction cards, verification badges, status displays", "engine": "C"},
            {"id": "doc-proof", "name": "Document Proof", "description": "Official certificates, attestations, receipts", "engine": "D"},
            {"id": "blueprint", "name": "Blueprint", "description": "Technical architecture schemas, CAD-style diagrams", "engine": "F"},
        ]
    })


# ═══════════════════════════════════════════════════════════════
# W-CANVAS-001-LAB — Interactive Canvas Execution Environment
# ═══════════════════════════════════════════════════════════════

LAB_PATH = "/opt/windi/canvas-lab"


@canvas_bp.route("/lab/config", methods=["GET"])
def get_lab_config():
    """Get Canvas Lab configuration."""
    config_path = os.path.join(LAB_PATH, "lab.config.json")
    try:
        with open(config_path, "r") as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify({"error": "Lab config not found"}), 404


@canvas_bp.route("/lab/recipes", methods=["GET"])
def list_recipes():
    """List all available recipes."""
    recipes_path = os.path.join(LAB_PATH, "recipes")
    recipes = []
    try:
        for fname in os.listdir(recipes_path):
            if fname.endswith(".json"):
                fpath = os.path.join(recipes_path, fname)
                with open(fpath, "r") as f:
                    recipe = json.load(f)
                    recipes.append(recipe)
        return jsonify({"recipes": recipes, "count": len(recipes)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@canvas_bp.route("/lab/recipes/<recipe_id>", methods=["GET"])
def get_recipe(recipe_id):
    """Get a specific recipe by ID."""
    recipes_path = os.path.join(LAB_PATH, "recipes")
    fpath = os.path.join(recipes_path, f"{recipe_id}.json")
    try:
        with open(fpath, "r") as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify({"error": f"Recipe '{recipe_id}' not found"}), 404
