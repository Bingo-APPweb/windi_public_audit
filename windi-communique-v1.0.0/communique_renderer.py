#!/usr/bin/env python3
"""
WINDI Communiqué Engine — HTML Renderer
=========================================
Generates trilingual (DE/EN/PT) HTML pages with Noir/Klar theme toggle.
Design system: WINDI Noir (dark + gold) / Klar (light).
Fonts: Bricolage Grotesque + Outfit + JetBrains Mono.
"""

import html as html_lib
from datetime import datetime


BASE_DOMAIN = "windi-domain.com"

IMPACT_COLORS = {
    "LOW": "#27AE60",
    "MED": "#F39C12",
    "HIGH": "#E74C3C",
    "CRIT": "#8E44AD"
}

IMPACT_LABELS = {
    "LOW": {"de": "Niedrig", "en": "Low", "pt": "Baixo"},
    "MED": {"de": "Mittel", "en": "Medium", "pt": "Médio"},
    "HIGH": {"de": "Hoch", "en": "High", "pt": "Alto"},
    "CRIT": {"de": "Kritisch", "en": "Critical", "pt": "Crítico"}
}

CATEGORY_LABELS = {
    "LAUNCH": {"de": "Markteinführung", "en": "Launch", "pt": "Lançamento"},
    "UPDATE": {"de": "Aktualisierung", "en": "Update", "pt": "Atualização"},
    "ALERT": {"de": "Warnung", "en": "Alert", "pt": "Alerta"},
    "GOVERNANCE": {"de": "Governance", "en": "Governance", "pt": "Governança"},
    "REPORT": {"de": "Bericht", "en": "Report", "pt": "Relatório"}
}

STATUS_LABELS = {
    "PUBLISHED": {"de": "Verifiziert", "en": "Verified", "pt": "Verificado", "icon": "🟢"},
    "ARCHIVED": {"de": "Archiviert", "en": "Archived", "pt": "Arquivado", "icon": "📁"},
    "REVOKED": {"de": "Widerrufen", "en": "Revoked", "pt": "Revogado", "icon": "🔴"}
}


def e(text):
    """HTML-escape text."""
    if text is None:
        return ""
    return html_lib.escape(str(text))


def base_head(title="WINDI Communiqué"):
    """Common HTML head with WINDI design system."""
    return f"""<!DOCTYPE html>
<html lang="de" data-theme="dark" data-lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;600;700&family=Outfit:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {{
  --gold: #C9A84C;
  --gold-dim: #8B7535;
  --noir-bg: #0D0D0D;
  --noir-surface: #1A1A1A;
  --noir-card: #222222;
  --noir-border: #333333;
  --noir-text: #E8E8E8;
  --noir-muted: #999999;
  --klar-bg: #FAFAF8;
  --klar-surface: #FFFFFF;
  --klar-card: #F5F5F0;
  --klar-border: #E0E0D8;
  --klar-text: #1A1A1A;
  --klar-muted: #666666;
}}
[data-theme="dark"] {{
  --bg: var(--noir-bg); --surface: var(--noir-surface); --card: var(--noir-card);
  --border: var(--noir-border); --text: var(--noir-text); --muted: var(--noir-muted);
}}
[data-theme="light"] {{
  --bg: var(--klar-bg); --surface: var(--klar-surface); --card: var(--klar-card);
  --border: var(--klar-border); --text: var(--klar-text); --muted: var(--klar-muted);
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: 'Outfit', sans-serif; background: var(--bg); color: var(--text);
  line-height: 1.7; min-height: 100vh;
}}
.container {{ max-width: 800px; margin: 0 auto; padding: 24px 20px; }}

/* Header */
.header {{
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 0; border-bottom: 2px solid var(--gold); margin-bottom: 32px;
}}
.header-brand {{ display: flex; align-items: center; gap: 12px; text-decoration: none; color: var(--text); }}
.header-logo {{
  width: 40px; height: 40px; background: var(--gold); color: var(--noir-bg);
  display: flex; align-items: center; justify-content: center;
  font-family: 'Bricolage Grotesque', serif; font-weight: 700; font-size: 20px;
  border-radius: 4px;
}}
.header-title {{ font-family: 'Bricolage Grotesque', serif; font-weight: 700; font-size: 18px; }}
.header-subtitle {{ font-size: 11px; color: var(--muted); letter-spacing: 2px; text-transform: uppercase; }}
.controls {{ display: flex; gap: 8px; align-items: center; }}
.controls button, .controls select {{
  background: var(--card); color: var(--text); border: 1px solid var(--border);
  padding: 6px 12px; border-radius: 4px; font-size: 12px; cursor: pointer;
  font-family: 'JetBrains Mono', monospace;
}}
.controls button:hover {{ border-color: var(--gold); }}

/* Status badge */
.status-badge {{
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 12px; border-radius: 16px; font-size: 12px; font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
}}
.status-verified {{ background: rgba(39,174,96,0.15); color: #27AE60; border: 1px solid rgba(39,174,96,0.3); }}
.status-archived {{ background: rgba(149,165,166,0.15); color: #95A5A6; border: 1px solid rgba(149,165,166,0.3); }}
.status-revoked {{ background: rgba(231,76,60,0.15); color: #E74C3C; border: 1px solid rgba(231,76,60,0.3); }}

/* Meta bar */
.meta-bar {{
  display: flex; gap: 16px; flex-wrap: wrap; padding: 12px 16px;
  background: var(--card); border-radius: 6px; margin: 16px 0;
  font-size: 13px; font-family: 'JetBrains Mono', monospace;
}}
.meta-item {{ display: flex; align-items: center; gap: 6px; }}
.impact-dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}

/* Title */
.com-title {{
  font-family: 'Bricolage Grotesque', serif; font-size: 28px; font-weight: 700;
  line-height: 1.3; margin: 24px 0 8px;
}}
.com-id {{ font-family: 'JetBrains Mono', monospace; font-size: 13px; color: var(--muted); }}

/* Body */
.com-body {{ margin: 24px 0; font-size: 16px; line-height: 1.8; }}
.com-body p {{ margin-bottom: 16px; }}

/* Seal block */
.seal-block {{
  border-top: 2px solid var(--gold); margin-top: 40px; padding-top: 24px;
  display: grid; grid-template-columns: auto 1fr; gap: 24px; align-items: start;
}}
.qr-placeholder {{
  width: 100px; height: 100px; background: var(--card); border: 1px solid var(--border);
  display: flex; align-items: center; justify-content: center; border-radius: 6px;
  font-size: 11px; color: var(--muted); text-align: center;
}}
.seal-info {{ font-size: 13px; }}
.seal-info .author {{ font-family: 'Bricolage Grotesque', serif; font-weight: 600; font-size: 16px; }}
.seal-info .role {{ color: var(--muted); margin-bottom: 8px; }}
.seal-info .hash {{
  font-family: 'JetBrains Mono', monospace; font-size: 11px;
  color: var(--gold); word-break: break-all;
}}

/* Actions */
.actions {{ display: flex; gap: 12px; margin: 24px 0; flex-wrap: wrap; }}
.action-btn {{
  display: inline-flex; align-items: center; gap: 6px; padding: 10px 20px;
  background: var(--card); color: var(--text); border: 1px solid var(--border);
  border-radius: 6px; text-decoration: none; font-size: 13px;
  font-family: 'Outfit', sans-serif; transition: all 0.2s;
}}
.action-btn:hover {{ border-color: var(--gold); color: var(--gold); }}
.action-btn.primary {{ background: var(--gold); color: var(--noir-bg); border-color: var(--gold); font-weight: 600; }}
.action-btn.primary:hover {{ background: var(--gold-dim); }}

/* Feed card */
.feed-card {{
  padding: 20px; background: var(--card); border: 1px solid var(--border);
  border-radius: 8px; margin-bottom: 16px; transition: border-color 0.2s;
  text-decoration: none; display: block; color: var(--text);
}}
.feed-card:hover {{ border-color: var(--gold); }}
.feed-card-title {{ font-family: 'Bricolage Grotesque', serif; font-weight: 600; font-size: 18px; margin-bottom: 8px; }}
.feed-card-meta {{ font-size: 12px; color: var(--muted); font-family: 'JetBrains Mono', monospace; }}

/* Footer */
.footer {{
  margin-top: 48px; padding-top: 16px; border-top: 1px solid var(--border);
  text-align: center; font-size: 12px; color: var(--muted);
}}
.footer .principle {{ color: var(--gold); font-style: italic; margin-top: 4px; }}

/* Trilingual toggle */
[data-lang="de"] [data-en], [data-lang="de"] [data-pt] {{ display: none; }}
[data-lang="en"] [data-de], [data-lang="en"] [data-pt] {{ display: none; }}
[data-lang="pt"] [data-de], [data-lang="pt"] [data-en] {{ display: none; }}

@media (max-width: 600px) {{
  .com-title {{ font-size: 22px; }}
  .seal-block {{ grid-template-columns: 1fr; }}
  .meta-bar {{ flex-direction: column; gap: 8px; }}
}}
</style>
</head>
<body>
"""


def base_scripts():
    """Theme and language toggle scripts."""
    return """
<script>
function toggleTheme() {
  const html = document.documentElement;
  html.dataset.theme = html.dataset.theme === 'dark' ? 'light' : 'dark';
  localStorage.setItem('windi-theme', html.dataset.theme);
}
function setLang(lang) {
  document.documentElement.dataset.lang = lang;
  localStorage.setItem('windi-lang', lang);
}
// Restore preferences
(function() {
  const t = localStorage.getItem('windi-theme');
  const l = localStorage.getItem('windi-lang');
  if (t) document.documentElement.dataset.theme = t;
  if (l) document.documentElement.dataset.lang = l;
})();
</script>
"""


def render_header(back_url=None):
    """Render page header with controls."""
    back = ""
    if back_url:
        back = f'<a href="{back_url}" style="color:var(--muted);text-decoration:none;font-size:13px;">← Back</a>'

    return f"""
<div class="container">
  <div class="header">
    <a href="/communique/feed" class="header-brand">
      <div class="header-logo">W</div>
      <div>
        <div class="header-title">WINDI COMMUNIQUÉ</div>
        <div class="header-subtitle">Verified Institutional Communications</div>
      </div>
    </a>
    <div class="controls">
      {back}
      <button onclick="setLang('de')">DE</button>
      <button onclick="setLang('en')">EN</button>
      <button onclick="setLang('pt')">PT</button>
      <button onclick="toggleTheme()">◐</button>
    </div>
  </div>
"""


def render_footer():
    """Render page footer."""
    return """
  <div class="footer">
    <div>WINDI Publishing House · Kempten, Bavaria</div>
    <div class="principle">"AI processes. Human decides. WINDI guarantees."</div>
  </div>
</div>
""" + base_scripts() + "</body></html>"


def trilingual_span(de, en=None, pt=None):
    """Generate trilingual span elements."""
    en = en or de
    pt = pt or de
    return f'<span data-de>{e(de)}</span><span data-en>{e(en)}</span><span data-pt>{e(pt)}</span>'


def format_body(text):
    """Convert plain text/markdown body to HTML paragraphs."""
    if not text:
        return ""
    paragraphs = text.strip().split("\n\n")
    result = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        # Simple markdown-like bold
        p = p.replace("**", "<strong>").replace("**", "</strong>")
        lines = p.split("\n")
        result.append(f"<p>{e('<br>'.join(lines))}</p>")
    return "\n".join(result)


def render_communique_page(com):
    """Render full HTML page for a single communiqué."""
    com_id = com["id"]
    status = com.get("status", "PUBLISHED")
    category = com.get("category", "UPDATE")
    impact = com.get("impact_level", "MED")
    impact_color = IMPACT_COLORS.get(impact, "#F39C12")

    status_class = {
        "PUBLISHED": "status-verified",
        "ARCHIVED": "status-archived",
        "REVOKED": "status-revoked"
    }.get(status, "status-verified")

    status_info = STATUS_LABELS.get(status, STATUS_LABELS["PUBLISHED"])

    title_de = com.get("title_de") or "Ohne Titel"
    title_en = com.get("title_en") or title_de
    title_pt = com.get("title_pt") or title_de

    html = base_head(f"{com_id} — WINDI Communiqué")
    html += render_header(back_url="/communique/feed")

    # Status + ID
    html += f"""
  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
    <span class="com-id">{e(com_id)}</span>
    <span class="status-badge {status_class}">
      {status_info['icon']}
      {trilingual_span(status_info['de'], status_info['en'], status_info['pt'])}
    </span>
  </div>
"""

    # Title
    html += f"""
  <h1 class="com-title">
    {trilingual_span(title_de, title_en, title_pt)}
  </h1>
"""

    # Meta bar
    cat_label = CATEGORY_LABELS.get(category, {"de": category, "en": category, "pt": category})
    imp_label = IMPACT_LABELS.get(impact, {"de": impact, "en": impact, "pt": impact})
    pub_date = com.get("published_at", "")[:10] if com.get("published_at") else "—"

    html += f"""
  <div class="meta-bar">
    <div class="meta-item">
      📂 {trilingual_span(cat_label['de'], cat_label['en'], cat_label['pt'])}
    </div>
    <div class="meta-item">
      <span class="impact-dot" style="background:{impact_color}"></span>
      {trilingual_span(imp_label['de'], imp_label['en'], imp_label['pt'])}
    </div>
    <div class="meta-item">📅 {e(pub_date)}</div>
  </div>
"""

    # Body (trilingual)
    body_de = com.get("body_de") or ""
    body_en = com.get("body_en") or body_de
    body_pt = com.get("body_pt") or body_de

    html += f"""
  <div class="com-body">
    <div data-de>{format_body(body_de)}</div>
    <div data-en>{format_body(body_en)}</div>
    <div data-pt>{format_body(body_pt)}</div>
  </div>
"""

    # Seal block
    content_hash = com.get("content_hash", "—")
    receipt_id = com.get("receipt_id", "—")
    verify_url = f"https://{BASE_DOMAIN}/communique/{com_id}/verify"

    html += f"""
  <div class="seal-block">
    <div class="qr-placeholder">
      <div>🔐<br><small>QR</small></div>
    </div>
    <div class="seal-info">
      <div class="author">{e(com.get('author_name', ''))}</div>
      <div class="role">{e(com.get('author_role', ''))}</div>
      <div style="margin-top:8px;">
        <div style="color:var(--muted);font-size:12px;">Receipt</div>
        <div class="hash">{e(receipt_id)}</div>
      </div>
      <div style="margin-top:8px;">
        <div style="color:var(--muted);font-size:12px;">Content Hash (SHA-256)</div>
        <div class="hash">{e(content_hash)}</div>
      </div>
    </div>
  </div>
"""

    # Action buttons
    html += f"""
  <div class="actions">
    <a href="/communique/{e(com_id)}/verify" class="action-btn primary">
      🔍 {trilingual_span('Verifizieren', 'Verify', 'Verificar')}
    </a>
    <a href="/communique/{e(com_id)}/pdf" class="action-btn">
      📄 PDF
    </a>
  </div>
"""

    html += render_footer()
    return html


def render_feed_page(communiques):
    """Render public feed page listing published communiqués."""
    html = base_head("WINDI Communiqués — Feed")
    html += render_header()

    if not communiques:
        html += """
  <div style="text-align:center;padding:48px 0;color:var(--muted);">
    <div style="font-size:48px;margin-bottom:16px;">🛡️</div>
    <div data-de>Noch keine Communiqués veröffentlicht.</div>
    <div data-en>No communiqués published yet.</div>
    <div data-pt>Nenhum communiqué publicado ainda.</div>
  </div>
"""
    else:
        for com in communiques:
            com_id = com["id"]
            category = com.get("category", "UPDATE")
            impact = com.get("impact_level", "MED")
            impact_color = IMPACT_COLORS.get(impact, "#F39C12")
            pub_date = com.get("published_at", "")[:10] if com.get("published_at") else "—"

            title_de = com.get("title_de") or "Ohne Titel"
            title_en = com.get("title_en") or title_de
            title_pt = com.get("title_pt") or title_de

            cat_label = CATEGORY_LABELS.get(category, {"de": category, "en": category, "pt": category})

            html += f"""
  <a href="/communique/{e(com_id)}" class="feed-card">
    <div class="feed-card-title">
      {trilingual_span(title_de, title_en, title_pt)}
    </div>
    <div class="feed-card-meta">
      🟢 {e(com_id)} ·
      📂 {trilingual_span(cat_label['de'], cat_label['en'], cat_label['pt'])} ·
      <span class="impact-dot" style="background:{impact_color};vertical-align:middle;"></span> {impact} ·
      📅 {e(pub_date)}
    </div>
  </a>
"""

    html += render_footer()
    return html


def render_verify_page(com, verification_data):
    """Render HTML verification page (future use)."""
    html = base_head(f"Verify — {com['id']}")
    html += render_header(back_url=f"/communique/{com['id']}")
    html += f"""
  <h2 style="font-family:'Bricolage Grotesque',serif;">
    🔍 {trilingual_span('Verifizierung', 'Verification', 'Verificação')}
  </h2>
  <pre style="background:var(--card);padding:16px;border-radius:8px;overflow-x:auto;font-family:'JetBrains Mono',monospace;font-size:12px;">
{json.dumps(verification_data, indent=2, ensure_ascii=False) if verification_data else '{}'}
  </pre>
"""
    html += render_footer()
    return html
