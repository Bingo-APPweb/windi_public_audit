# W-CANVAS-001 — Tutorial: Dual Engine v1.3.0

**Version:** 1.0
**Author:** Liga IA+H
**Date:** 21 Mar 2026
**Audience:** Developers / API Integration

---

## Overview

W-CANVAS-001 is WINDI's visual generation engine running on `:8091`. Version 1.3.0 introduces a **Dual Engine Architecture**:

| Engine | Output | Use Case |
|--------|--------|----------|
| **Engine A** | Mermaid/SVG | Flowcharts, timelines, architecture diagrams |
| **Engine B** | HTML Dashboard | KPI cards, tables, charts (Chart.js) |

Both engines share the same endpoint (`/canvas/generate`) and are routed automatically based on `canvas_type`.

---

## Quick Start

### Health Check

```bash
curl -s http://localhost:8091/canvas/status | jq
```

**Response:**
```json
{
  "agent": "W-CANVAS-001",
  "version": "1.3.0",
  "status": "operational",
  "canvas_types": ["diagram", "flowchart", "chart", "infographic", "architecture", "timeline", "dashboard"],
  "engines": {"A": "Mermaid/SVG", "B": "HTML Dashboard"},
  "formats": ["svg", "mermaid", "html"]
}
```

---

## Engine A — Mermaid Renderer

### Supported Types

| Type | Description |
|------|-------------|
| `flowchart` | Process flows, decision trees |
| `architecture` | System diagrams |
| `diagram` | Generic diagrams |
| `timeline` | Chronological visualizations |
| `sequence` | Sequence diagrams |
| `mindmap` | Mind maps |

### Request Schema

```bash
curl -s -X POST http://localhost:8091/canvas/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Flowchart: user submits form, system validates, if valid save to DB else show error",
    "canvas_type": "flowchart",
    "format": "mermaid",
    "theme": "dark_gold",
    "tier": "MED",
    "wallet_id": "WALLET-XXX",
    "seal_to_ledger": true
  }'
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `prompt` | string | **Yes** | — | Natural language description |
| `canvas_type` | string | No | `flowchart` | See supported types above |
| `format` | string | No | `svg` | `svg` or `mermaid` |
| `theme` | string | No | `institutional` | `klar`, `noir`, `dark_gold`, `sovereign` |
| `tier` | string | No | `MED` | `FREE`, `MED`, `HIGH` |
| `wallet_id` | string | No | `null` | User DID for attribution |
| `seal_to_ledger` | bool | No | `true` | Seal to Forensic Ledger |

### Response (Engine A)

```json
{
  "success": true,
  "canvas_id": "5590F44AAB0E4180",
  "canvas_type": "flowchart",
  "format": "mermaid",
  "content": "flowchart TD\n    A([User]) --> B[Submit Form]\n    B --> C{Valid?}\n    C -->|Yes| D[Save to DB]\n    C -->|No| E[Show Error]",
  "content_hash": "106e8c7a27be79...",
  "generated_at": "2026-03-21T18:28:58.136751+00:00",
  "agent": "W-CANVAS-001",
  "version": "1.3.0",
  "sealed": true,
  "receipt_id": "WINDI-CANVAS-5590F44AAB0E4180-20260321182858",
  "verify_url": "https://windi-domain.com/verify-public/?id=WINDI-CANVAS-...",
  "sovereignty": {
    "model": "gemini-2.5-flash",
    "tier": "MED",
    "tokens_budget": 600,
    "cost_est_usd": 0.000045,
    "was_local": false
  }
}
```

### Themes

| Theme | Background | Accent | Best For |
|-------|------------|--------|----------|
| `klar` | Light (#FAFAF8) | Gold (#8B7424) | Print, presentations |
| `noir` | Dark (#0A0A10) | Gold (#C9A84C) | Default, dark mode |
| `dark_gold` | Black (#0F0B05) | Gold (#D4A017) | Elegant, premium |
| `sovereign` | Deep blue (#080B12) | Blue (#3A7FD4) | Institutional, signed docs |

### Sanitizer (v1.3.0)

Engine A includes `sanitize_mermaid()` which:
- Removes diacritics outside quotes (`ã` → `a`, `ç` → `c`)
- Removes `?` and `!` outside quotes (parser-breaking)
- Preserves content inside `"..."` or `'...'`
- Preserves Mermaid directives (`%%{...}%%`)

This prevents parser errors from non-ASCII input.

---

## Engine B — HTML Dashboard Renderer

### Activation

Engine B is activated when `canvas_type` equals `"dashboard"`.

### Request Schema

```bash
curl -s -X POST http://localhost:8091/canvas/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Dashboard WINDI governance: 4 KPIs (soberania, docs, SGE, uptime), agent status table, bar chart docs/week",
    "canvas_type": "dashboard",
    "theme": "dark_gold",
    "tier": "HIGH",
    "wallet_id": "WALLET-XXX"
  }'
```

### Response (Engine B)

```json
{
  "success": true,
  "canvas_id": "73D042078CC442CA",
  "canvas_type": "dashboard",
  "format": "html",
  "engine": "B",
  "render_type": "html",
  "html": "<!DOCTYPE html><html>...",
  "content": "<!DOCTYPE html><html>...",
  "content_hash": "57f0ec190bbe1fca...",
  "generated_at": "2026-03-21T18:33:52.491679+00:00",
  "message": "Dashboard generated via Engine B."
}
```

### JSON Schema (LLM Output)

Engine B instructs the LLM to return structured JSON:

```json
{
  "title": "Dashboard Title (max 60 chars)",
  "subtitle": "Context or description (max 80 chars)",
  "kpis": [
    {
      "label": "Soberania",
      "value": "93.3",
      "unit": "%",
      "trend": "up",
      "trend_value": "+0.3%",
      "color": "gold"
    }
  ],
  "table": {
    "headers": ["Agent", "Status", "Requests"],
    "rows": [
      ["W-LEGAL-001", "Online", "3,421"],
      ["W-NOTARY-001", "Online", "1,847"]
    ]
  },
  "chart": {
    "type": "bar",
    "title": "Documents per Day",
    "labels": ["Mon", "Tue", "Wed", "Thu", "Fri"],
    "datasets": [
      {"label": "Docs", "data": [142, 198, 167, 234, 289]}
    ]
  },
  "status_items": [
    {"name": "W-CANVAS-001", "status": "online", "detail": "Engine B Active"}
  ]
}
```

### KPI Colors

| Color | Use Case |
|-------|----------|
| `gold` | Primary metrics, brand |
| `teal` | Secondary metrics |
| `blue` | Technical metrics |
| `green` | Positive indicators |
| `red` | Alerts, negative |
| `purple` | Special/premium |

### Status Values

| Status | Color | Meaning |
|--------|-------|---------|
| `online` | Green | Operational |
| `standby` | Yellow | Waiting/Idle |
| `offline` | Red | Not running |
| `warning` | Orange | Degraded |

### Chart Types

| Type | Description |
|------|-------------|
| `bar` | Vertical bars |
| `line` | Line graph with tension |
| `donut` | Doughnut/pie chart |

### Frontend Rendering

Engine B returns HTML that should be rendered in a sandboxed iframe:

```javascript
if (data.engine === 'B' && data.render_type === 'html') {
  container.innerHTML = `<iframe
    srcdoc="${data.html.replace(/"/g, '&quot;')}"
    style="width:100%;height:500px;border:none;"
    sandbox="allow-scripts"></iframe>`;
}
```

---

## Sovereignty Gate

The Sovereignty Gate routes requests based on complexity and tier:

### Tier Routing

| Tier | Engine A Model | Engine B Model | Token Budget |
|------|----------------|----------------|--------------|
| `FREE` | `local_template` | Fallback HTML | 0 |
| `MED` | `gemini-2.5-flash` | `gemini-2.5-flash` | ~600 |
| `HIGH` | `gemini-2.5-pro` | `gemini-2.5-pro` | ~2000 |

### Local Templates (FREE Tier)

Engine A includes pre-built Mermaid templates for common WINDI diagrams:

| Template Key | Description |
|--------------|-------------|
| `windi_pipeline` | User → Document → Ledger flow |
| `agentes_windi` | Constitutional Agent constellation |
| `did_flow` | DID creation and verification |
| `constellation` | Agent mindmap |
| `document_seal` | Sealing sequence diagram |
| `windi_evolution` | WINDI timeline |

Trigger by including keywords like "windi pipeline", "agentes", "did", etc.

### Cost Estimation

```
FREE tier:  $0.00 (100% local)
MED tier:   ~$0.00004 per render (Flash)
HIGH tier:  ~$0.00025 per render (Pro)
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | For MED/HIGH | — | Google Gemini API key |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` | Default model |
| `LEDGER_URL` | No | `http://127.0.0.1:8101` | Forensic Ledger endpoint |

### Setup

```bash
# Add API key to environment
echo "GEMINI_API_KEY=your-key-here" >> /opt/windi/agents/constitutional-agent/.env

# Restart sandbox (nohup, NOT systemd)
cd /opt/windi/agents/constitutional-agent
kill $(pgrep -f "agent.py")
sleep 2
nohup python3 agent.py --port 8091 > /opt/windi/logs/sandbox-core.log 2>&1 &

# Verify
curl -s http://localhost:8091/canvas/status | jq '.model'
```

---

## Examples

### Example 1: Simple Flowchart (FREE)

```bash
curl -s -X POST http://localhost:8091/canvas/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"windi pipeline","canvas_type":"flowchart","tier":"FREE"}' \
  | jq '{canvas_id, sovereignty}'
```

### Example 2: Architecture Diagram (MED)

```bash
curl -s -X POST http://localhost:8091/canvas/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Architecture: React frontend connects to Flask API, API talks to PostgreSQL and Redis, external calls to Gemini API",
    "canvas_type": "architecture",
    "theme": "noir",
    "tier": "MED"
  }' | jq '.content'
```

### Example 3: Governance Dashboard (HIGH)

```bash
curl -s -X POST http://localhost:8091/canvas/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Executive dashboard: 6 KPIs (revenue, users, uptime, latency, errors, satisfaction), status of 5 microservices, line chart showing traffic over 7 days",
    "canvas_type": "dashboard",
    "theme": "sovereign",
    "tier": "HIGH",
    "wallet_id": "WALLET-EXEC-001"
  }' | jq '{engine, render_type, content_hash}'
```

### Example 4: Render in Browser

```html
<div id="canvas-container"></div>
<script>
async function renderCanvas(prompt, type) {
  const res = await fetch('/canvas/generate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({prompt, canvas_type: type, theme: 'dark_gold'})
  });
  const data = await res.json();

  if (data.engine === 'B') {
    // Dashboard: use iframe
    document.getElementById('canvas-container').innerHTML =
      `<iframe srcdoc="${data.html.replace(/"/g, '&quot;')}"
              style="width:100%;height:500px;border:none;"></iframe>`;
  } else {
    // Mermaid: use mermaid.js
    document.getElementById('canvas-container').innerHTML =
      `<div class="mermaid">${data.content}</div>`;
    mermaid.init(undefined, '.mermaid');
  }
}

// Usage
renderCanvas('dashboard with 4 KPIs', 'dashboard');
renderCanvas('flowchart approval process', 'flowchart');
</script>
```

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `GEMINI_API_KEY not configured` | Missing API key | Set env variable |
| `SOVEREIGN_REQUIRES_DID` | Sovereign theme without wallet_id | Provide wallet_id |
| `Visualization engine error: 503` | Gemini API down | Wait or use FREE tier |

### Fallback Behavior

- **Engine A** without API key: Returns local template if available
- **Engine B** without API key: Returns demo dashboard HTML

---

## Invariants

| Invariant | Application |
|-----------|-------------|
| **I9** | Human approval required before Ledger seal |
| **I10** | LLM sovereignty — fallback if external unavailable |
| **I11** | Forensic evidence — all sealed canvases are immutable |
| **I12** | Language sovereignty — respects user's language |

---

## Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/canvas/status` | GET | Health check and capabilities |
| `/canvas/generate` | POST | Generate visualization |
| `/canvas/themes` | GET | List available themes |
| `/canvas/types` | GET | List available types |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.3.0 | 21 Mar 2026 | Dual Engine (A+B), sanitizer, dashboard HTML |
| 1.2.0 | 21 Mar 2026 | Sovereignty Gate v1.0, local templates |
| 1.1.0 | 20 Mar 2026 | Gemini integration, theme system |
| 1.0.0 | 19 Mar 2026 | Initial release |

---

*Liga IA+H — Kempten, Bavaria · 2026*
*"AI processes. Human decides. WINDI guarantees."*
