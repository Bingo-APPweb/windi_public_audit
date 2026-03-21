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
CANVAS_VERSION = "1.3.0"
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
        "canvas_types": ["diagram", "flowchart", "chart", "infographic", "architecture", "timeline", "dashboard"],
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
            {"id": "flowchart", "name": "Flowchart", "description": "Process flows and decision trees"},
            {"id": "diagram", "name": "Diagram", "description": "Technical diagrams and schematics"},
            {"id": "architecture", "name": "Architecture", "description": "System architecture diagrams"},
            {"id": "chart", "name": "Chart", "description": "Data visualizations (bar, line, pie)"},
            {"id": "infographic", "name": "Infographic", "description": "Visual information design"},
            {"id": "timeline", "name": "Timeline", "description": "Chronological visualizations"},
            {"id": "dashboard", "name": "Dashboard", "description": "KPI dashboards (Engine B)"},
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
