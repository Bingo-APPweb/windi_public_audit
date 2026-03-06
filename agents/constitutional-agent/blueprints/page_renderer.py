"""
WINDI Page Renderer — W-PAGE-001 Component
============================================

Renders HTML pages using WINDI UI components and design tokens.
Part of the Constitutional Agent's Page Generator module.

Components:
- windi-card, seal-badge, ledger-status
- sovereign-button, dragon-orb, verification-panel

Principle: "AI processes. Human decides. WINDI guarantees."

Version: 0.1.0
Component: W-PAGE-001
"""

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

__version__ = "0.1.0"
__component__ = "W-PAGE-001-RENDERER"
__template_version__ = "windi-ui-v1.0"


# ═══════════════════════════════════════════════════════════════
#  DESIGN TOKENS — WINDI UI v1.0
# ═══════════════════════════════════════════════════════════════

TOKENS_CSS = """
:root {
  /* Typography */
  --w-font-sans: "Bricolage Grotesque", ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
  --w-font-serif: "Cormorant Garamond", ui-serif, Georgia, serif;
  --w-font-mono: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;

  /* Spacing */
  --w-radius-xs: 8px;
  --w-radius-sm: 12px;
  --w-radius-md: 16px;
  --w-radius-lg: 20px;
  --w-radius-xl: 28px;

  --w-space-1: 4px;  --w-space-2: 8px;  --w-space-3: 12px;
  --w-space-4: 16px; --w-space-5: 20px; --w-space-6: 24px;
  --w-space-8: 32px; --w-space-10: 40px; --w-space-12: 48px;

  /* Effects */
  --w-border-1: 1px;
  --w-shadow-sm: 0 1px 2px rgba(0,0,0,0.08);
  --w-shadow-md: 0 8px 24px rgba(0,0,0,0.18);
  --w-shadow-lg: 0 16px 48px rgba(0,0,0,0.22);

  --w-ease: cubic-bezier(.2,.8,.2,1);
  --w-dur-fast: 120ms;
  --w-dur-med: 220ms;
  --w-dur-slow: 420ms;

  --w-focus-ring: 0 0 0 3px rgba(212,168,67,0.25);
  --w-gold: #D4A843;
}

/* NOIR Theme (default) */
:root, :root[data-theme="noir"] {
  --w-bg: #0E0E14;
  --w-surface: #16161F;
  --w-surface-2: #1C1C28;
  --w-border: #26263A;
  --w-text: #E2E2EA;
  --w-text-dim: #7A7A96;
  --w-text-muted: #A6A6C2;
  --w-link: var(--w-gold);
  --w-success: #5A9C69;
  --w-warning: var(--w-gold);
  --w-danger: #D25C5C;
  --w-sealed: #1B4332;
  --w-forensic: #2A6B4A;
}

/* KLAR Theme */
:root[data-theme="klar"] {
  --w-bg: #F5F0E0;
  --w-surface: #FDFBF5;
  --w-surface-2: #EDE8D8;
  --w-border: #DDD6C2;
  --w-text: #2C2924;
  --w-text-dim: #6B6560;
  --w-text-muted: #7E7772;
  --w-link: #8B6914;
  --w-success: #4A7C59;
  --w-warning: #B8860B;
  --w-danger: #A94442;
  --w-sealed: #1B4332;
  --w-forensic: #2A6B4A;
}

/* Base Reset */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--w-bg);
  color: var(--w-text);
  font-family: var(--w-font-sans);
  line-height: 1.6;
  min-height: 100vh;
}

.windi-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--w-space-8);
}

/* Utility Classes */
.windi-mono  { font-family: var(--w-font-mono); }
.windi-serif { font-family: var(--w-font-serif); }
.windi-dim   { color: var(--w-text-dim); }
.windi-muted { color: var(--w-text-muted); }
.windi-gold  { color: var(--w-gold); }
"""


# ═══════════════════════════════════════════════════════════════
#  COMPONENT CSS
# ═══════════════════════════════════════════════════════════════

COMPONENTS_CSS = """
/* ═══ windi-card ═══ */
.w-card {
  background: var(--w-surface);
  border: var(--w-border-1) solid var(--w-border);
  border-radius: var(--w-radius-lg);
  box-shadow: var(--w-shadow-sm);
  overflow: hidden;
}
.w-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--w-space-4);
  padding: var(--w-space-5);
  border-bottom: var(--w-border-1) solid var(--w-border);
  background: color-mix(in srgb, var(--w-surface) 92%, transparent);
}
.w-card__title { font-size: 18px; font-weight: 700; }
.w-card__subtitle { margin-top: 6px; font-size: 14px; color: var(--w-text-dim); }
.w-card__body { padding: var(--w-space-5); }
.w-card[data-elevation="md"] { box-shadow: var(--w-shadow-md); }
.w-card[data-elevation="lg"] { box-shadow: var(--w-shadow-lg); }

/* ═══ seal-badge ═══ */
.w-seal {
  display: inline-flex;
  gap: var(--w-space-3);
  align-items: center;
  padding: 10px 16px;
  border-radius: 999px;
  border: var(--w-border-1) solid var(--w-border);
  background: color-mix(in srgb, var(--w-surface) 86%, transparent);
  font-size: 12px;
}
.w-seal__dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: var(--w-success);
}
.w-seal__label { letter-spacing: .12em; color: var(--w-text-dim); }
.w-seal__status { font-weight: 700; }
.w-seal[data-status="pending"] .w-seal__dot { background: var(--w-warning); }
.w-seal[data-status="invalid"] .w-seal__dot { background: var(--w-danger); }
.w-seal[data-status="sealed"] .w-seal__dot {
  background: var(--w-forensic);
  box-shadow: 0 0 6px rgba(42,107,74,0.6);
}
.w-seal[data-status="verified"] .w-seal__dot {
  box-shadow: 0 0 6px rgba(90,156,105,0.5);
}

/* ═══ ledger-status ═══ */
.w-ledger {
  display: inline-flex;
  align-items: center;
  gap: var(--w-space-2);
  padding: 8px 14px;
  border-radius: 999px;
  border: var(--w-border-1) solid var(--w-border);
  background: color-mix(in srgb, var(--w-surface) 86%, transparent);
  font-size: 12px;
}
.w-ledger__icon { font-size: 14px; }
.w-ledger__label { letter-spacing: .12em; color: var(--w-text-dim); }
.w-ledger__state { font-weight: 700; }
.w-ledger__anchor { font-family: var(--w-font-mono); color: var(--w-text-dim); }
.w-ledger[data-verified="true"] .w-ledger__state { color: var(--w-success); }
.w-ledger[data-verified="false"] .w-ledger__state { color: var(--w-danger); }

/* ═══ sovereign-button ═══ */
.w-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--w-space-2);
  padding: 12px 20px;
  border-radius: 999px;
  border: var(--w-border-1) solid var(--w-border);
  background: var(--w-surface-2);
  color: var(--w-text);
  font-family: var(--w-font-sans);
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  transition: transform var(--w-dur-fast) var(--w-ease), background var(--w-dur-med) var(--w-ease);
}
.w-btn:hover { transform: translateY(-1px); }
.w-btn:active { transform: translateY(0); }
.w-btn[data-variant="primary"] {
  border-color: color-mix(in srgb, var(--w-gold) 70%, var(--w-border));
  background: color-mix(in srgb, var(--w-gold) 16%, var(--w-surface-2));
  color: var(--w-gold);
}
.w-btn[data-variant="ghost"] { background: transparent; }
.w-btn[data-variant="danger"] {
  border-color: color-mix(in srgb, var(--w-danger) 70%, var(--w-border));
  color: var(--w-danger);
}
.w-btn:disabled { opacity: .55; cursor: not-allowed; transform: none; }

/* ═══ dragon-orb ═══ */
.w-orb {
  display: inline-flex;
  align-items: center;
  gap: var(--w-space-3);
}
.w-orb__ring {
  width: 36px;
  height: 36px;
  border-radius: 999px;
  border: 2px solid color-mix(in srgb, var(--w-gold) 55%, var(--w-border));
  display: flex;
  align-items: center;
  justify-content: center;
}
.w-orb__core {
  width: 18px;
  height: 18px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--w-gold) 20%, var(--w-surface-2));
}
.w-orb__role { font-size: 12px; font-weight: 800; letter-spacing: .12em; color: var(--w-gold); }
.w-orb[data-role="ARCHITECT"] .w-orb__core { background: color-mix(in srgb, var(--w-gold) 25%, var(--w-surface-2)); }
.w-orb[data-role="GUARDIAN"] .w-orb__core { background: color-mix(in srgb, #4A90D9 20%, var(--w-surface-2)); }
.w-orb[data-role="WITNESS"] .w-orb__core { background: color-mix(in srgb, var(--w-success) 20%, var(--w-surface-2)); }
.w-orb[data-role="HUMAN"] .w-orb__core { background: color-mix(in srgb, #C084FC 20%, var(--w-surface-2)); }
.w-orb[data-role="GUARDIAN"] .w-orb__role { color: #4A90D9; }
.w-orb[data-role="WITNESS"] .w-orb__role { color: var(--w-success); }
.w-orb[data-role="HUMAN"] .w-orb__role { color: #C084FC; }

/* ═══ verification-panel ═══ */
.w-verify {
  background: var(--w-surface);
  border: var(--w-border-1) solid var(--w-border);
  border-radius: var(--w-radius-lg);
  padding: var(--w-space-5);
}
.w-verify__title { font-weight: 900; font-size: 18px; margin-bottom: var(--w-space-4); }
.w-verify__hash {
  font-family: var(--w-font-mono);
  font-size: 12px;
  padding: var(--w-space-3);
  background: var(--w-surface-2);
  border-radius: var(--w-radius-sm);
  word-break: break-all;
  color: var(--w-text-muted);
}
.w-verify__qr {
  width: 120px;
  height: 120px;
  background: white;
  border-radius: var(--w-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ═══ provenance-box ═══ */
.w-provenance {
  padding: var(--w-space-4);
  border-radius: var(--w-radius-sm);
  border: var(--w-border-1) solid color-mix(in srgb, var(--w-forensic) 50%, var(--w-border));
  background: color-mix(in srgb, var(--w-sealed) 40%, var(--w-surface));
  font-size: 11px;
  font-family: var(--w-font-mono);
  color: var(--w-text-muted);
  line-height: 2;
}
.w-provenance strong { color: var(--w-gold); font-weight: 700; }

/* ═══ Header & Footer ═══ */
.w-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--w-space-5) 0;
  border-bottom: var(--w-border-1) solid var(--w-border);
  margin-bottom: var(--w-space-8);
}
.w-header__logo {
  display: flex;
  align-items: center;
  gap: var(--w-space-3);
}
.w-header__mark {
  width: 40px;
  height: 40px;
  border-radius: var(--w-radius-sm);
  background: color-mix(in srgb, var(--w-gold) 18%, var(--w-surface-2));
  border: var(--w-border-1) solid color-mix(in srgb, var(--w-gold) 40%, var(--w-border));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}
.w-header__title { font-size: 16px; font-weight: 800; letter-spacing: .08em; }

.w-footer {
  margin-top: var(--w-space-12);
  padding-top: var(--w-space-5);
  border-top: var(--w-border-1) solid var(--w-border);
  font-size: 12px;
  color: var(--w-text-dim);
  text-align: center;
}
"""


# ═══════════════════════════════════════════════════════════════
#  DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════

@dataclass
class PagePlan:
    """Plan for page generation."""
    doc_type: str
    theme: str = "noir"
    components: List[str] = field(default_factory=list)
    title: str = ""
    description: str = ""
    tier: str = "MED"
    lang: str = "en"


@dataclass
class UIProvenance:
    """UI Provenance - chain of custody for the interface."""
    html_hash: str
    css_hash: str
    js_hash: str
    combined_hash: str
    content_hash: str
    size_bytes: int
    computed_at: str
    template_version: str = __template_version__
    generator: str = f"W-PAGE-001 v{__version__}"
    ledger_anchor: Optional[int] = None
    receipt_id: Optional[str] = None
    sealed_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "html_hash": self.html_hash,
            "css_hash": self.css_hash,
            "js_hash": self.js_hash,
            "combined_hash": self.combined_hash,
            "content_hash": self.content_hash,
            "size_bytes": self.size_bytes,
            "computed_at": self.computed_at,
            "template_version": self.template_version,
            "generator": self.generator,
            "ledger_anchor": self.ledger_anchor,
            "receipt_id": self.receipt_id,
            "sealed_at": self.sealed_at,
        }


@dataclass
class RenderedPage:
    """Result of page rendering."""
    html: str
    provenance: UIProvenance
    plan: PagePlan
    preview_id: str
    created_at: str


# ═══════════════════════════════════════════════════════════════
#  HASH FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def compute_sha256(content: str) -> str:
    """Compute SHA-256 hash of content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def extract_css(html: str) -> str:
    """Extract all CSS from HTML (style tags + inline styles)."""
    css_parts = []
    # Extract <style> content
    for match in re.finditer(r'<style[^>]*>(.*?)</style>', html, re.DOTALL | re.IGNORECASE):
        css_parts.append(match.group(1))
    # Extract inline styles
    for match in re.finditer(r'style\s*=\s*["\']([^"\']+)["\']', html, re.IGNORECASE):
        css_parts.append(match.group(1))
    return '\n'.join(css_parts)


def extract_js(html: str) -> str:
    """Extract all JavaScript from HTML."""
    js_parts = []
    for match in re.finditer(r'<script[^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE):
        content = match.group(1).strip()
        if content:  # Skip empty scripts (external src)
            js_parts.append(content)
    return '\n'.join(js_parts)


def extract_content(html: str) -> str:
    """Extract text content from HTML (for content_hash)."""
    # Remove tags
    text = re.sub(r'<[^>]+>', ' ', html)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def compute_provenance(html: str) -> UIProvenance:
    """Compute full UI Provenance for an HTML page."""
    css = extract_css(html)
    js = extract_js(html)
    content = extract_content(html)

    html_hash = compute_sha256(html)
    css_hash = compute_sha256(css) if css else "sha256:empty"
    js_hash = compute_sha256(js) if js else "sha256:empty"
    content_hash = compute_sha256(content)

    # Combined hash = hash of all hashes concatenated
    combined = f"{html_hash}:{css_hash}:{js_hash}"
    combined_hash = compute_sha256(combined)

    return UIProvenance(
        html_hash=f"sha256:{html_hash}",
        css_hash=f"sha256:{css_hash}" if css else "sha256:empty",
        js_hash=f"sha256:{js_hash}" if js else "sha256:empty",
        combined_hash=f"sha256:{combined_hash}",
        content_hash=f"sha256:{content_hash}",
        size_bytes=len(html.encode('utf-8')),
        computed_at=datetime.now(timezone.utc).isoformat(),
    )


# ═══════════════════════════════════════════════════════════════
#  PAGE TEMPLATE
# ═══════════════════════════════════════════════════════════════

def generate_page_html(
    title: str,
    body_content: str,
    theme: str = "noir",
    provenance: Optional[UIProvenance] = None,
    page_id: Optional[str] = None,
    include_fonts: bool = True,
) -> str:
    """
    Generate a complete WINDI page HTML.

    Args:
        title: Page title
        body_content: HTML content for the body
        theme: 'noir' or 'klar'
        provenance: UI Provenance object (for footer)
        page_id: Page ID (for meta tags)
        include_fonts: Whether to include Google Fonts link

    Returns:
        Complete HTML document string
    """
    fonts_link = ""
    if include_fonts:
        fonts_link = '''<link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,300;12..96,400;12..96,700;12..96,800&family=Cormorant+Garamond:wght@300;400;600;700&family=JetBrains+Mono:wght@300;400;700&display=swap" rel="stylesheet">'''

    provenance_block = ""
    if provenance:
        provenance_block = f'''
    <div class="w-provenance">
        <strong>ui_provenance</strong> · {provenance.template_version}<br>
        html_hash: {provenance.html_hash[:32]}...<br>
        combined_hash: {provenance.combined_hash[:32]}...<br>
        generator: {provenance.generator}<br>
        {"receipt_id: " + provenance.receipt_id + "<br>" if provenance.receipt_id else ""}
        invariant: <strong>C6 · I9 · I11</strong>
    </div>'''

    meta_tags = ""
    if page_id:
        meta_tags = f'''
    <meta name="windi:page-id" content="{page_id}">
    <meta name="windi:generator" content="W-PAGE-001 v{__version__}">'''

    return f'''<!DOCTYPE html>
<html lang="en" data-theme="{theme}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — WINDI</title>
    <meta name="generator" content="WINDI W-PAGE-001 v{__version__}">{meta_tags}
    {fonts_link}
    <style>
{TOKENS_CSS}
{COMPONENTS_CSS}
    </style>
</head>
<body>
    <div class="windi-page">
        <header class="w-header">
            <div class="w-header__logo">
                <div class="w-header__mark">🐉</div>
                <div class="w-header__title">WINDI</div>
            </div>
            <div class="w-orb" data-role="WITNESS">
                <div class="w-orb__ring"><div class="w-orb__core"></div></div>
                <span class="w-orb__role">VERIFIED</span>
            </div>
        </header>

        <main>
{body_content}
        </main>

        <footer class="w-footer">
            {provenance_block}
            <p style="margin-top: var(--w-space-4);">
                AI processes. Human decides. WINDI guarantees.<br>
                <span class="windi-dim">WINDI Publishing House · Kempten, Bavaria 🇩🇪</span>
            </p>
        </footer>
    </div>
</body>
</html>'''


# ═══════════════════════════════════════════════════════════════
#  COMPONENT RENDERERS
# ═══════════════════════════════════════════════════════════════

def render_card(title: str, subtitle: str = "", body: str = "", elevation: str = "sm") -> str:
    """Render a windi-card component."""
    return f'''
        <section class="w-card" data-elevation="{elevation}">
            <header class="w-card__header">
                <div>
                    <h2 class="w-card__title">{title}</h2>
                    {f'<p class="w-card__subtitle">{subtitle}</p>' if subtitle else ''}
                </div>
            </header>
            <div class="w-card__body">
                {body}
            </div>
        </section>'''


def render_seal_badge(status: str = "verified", hash_preview: str = "", timestamp: str = "") -> str:
    """Render a seal-badge component."""
    return f'''
        <div class="w-seal" data-status="{status}">
            <div class="w-seal__dot"></div>
            <div>
                <span class="w-seal__label">SEAL</span>
                <span class="w-seal__status">{status.upper()}</span>
                {f'<br><span class="windi-mono windi-dim" style="font-size:11px;">{hash_preview}</span>' if hash_preview else ''}
                {f'<br><span class="windi-dim" style="font-size:11px;">{timestamp}</span>' if timestamp else ''}
            </div>
        </div>'''


def render_ledger_status(verified: bool = True, anchor: Optional[int] = None) -> str:
    """Render a ledger-status component."""
    state = "ANCHORED" if verified else "UNVERIFIED"
    anchor_text = f"#{anchor}" if anchor else "#—"
    return f'''
        <div class="w-ledger" data-verified="{str(verified).lower()}">
            <span class="w-ledger__icon">⟡</span>
            <span class="w-ledger__label">LEDGER</span>
            <span class="w-ledger__state">{state}</span>
            <span class="w-ledger__anchor">{anchor_text}</span>
        </div>'''


def render_button(label: str, variant: str = "primary", disabled: bool = False) -> str:
    """Render a sovereign-button component."""
    disabled_attr = 'disabled' if disabled else ''
    return f'<button class="w-btn" data-variant="{variant}" {disabled_attr}>{label}</button>'


def render_dragon_orb(role: str = "WITNESS") -> str:
    """Render a dragon-orb component."""
    return f'''
        <div class="w-orb" data-role="{role}">
            <div class="w-orb__ring"><div class="w-orb__core"></div></div>
            <span class="w-orb__role">{role}</span>
        </div>'''


def render_verification_panel(page_id: str, hash_value: str, verify_url: str = "") -> str:
    """Render a verification-panel component."""
    return f'''
        <div class="w-verify">
            <h3 class="w-verify__title">Verify This Document</h3>
            <p style="margin-bottom: var(--w-space-4); color: var(--w-text-muted);">
                Document ID: <strong>{page_id}</strong>
            </p>
            <div class="w-verify__hash">
                {hash_value}
            </div>
            <p style="margin-top: var(--w-space-4); font-size: 13px; color: var(--w-text-dim);">
                Verify at: <a href="{verify_url}" style="color: var(--w-gold);">{verify_url}</a>
            </p>
        </div>'''


# ═══════════════════════════════════════════════════════════════
#  MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════

def render_page(plan: PagePlan, content_blocks: List[str], preview_id: str) -> RenderedPage:
    """
    Render a complete page from a plan and content blocks.

    Args:
        plan: PagePlan with configuration
        content_blocks: List of HTML content blocks
        preview_id: Unique preview ID

    Returns:
        RenderedPage with HTML and provenance
    """
    body_content = '\n'.join(content_blocks)

    # Generate HTML (without provenance first to compute hash)
    html_draft = generate_page_html(
        title=plan.title or "WINDI Document",
        body_content=body_content,
        theme=plan.theme,
        include_fonts=True,
    )

    # Compute provenance
    provenance = compute_provenance(html_draft)

    # Generate final HTML with provenance
    html_final = generate_page_html(
        title=plan.title or "WINDI Document",
        body_content=body_content,
        theme=plan.theme,
        provenance=provenance,
        page_id=preview_id,
        include_fonts=True,
    )

    # Recompute provenance for final HTML
    provenance = compute_provenance(html_final)

    return RenderedPage(
        html=html_final,
        provenance=provenance,
        plan=plan,
        preview_id=preview_id,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


# ═══════════════════════════════════════════════════════════════
#  TEST / DEMO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Demo: render a simple page
    plan = PagePlan(
        doc_type="demo",
        theme="noir",
        title="Demo Document",
        components=["windi-card", "seal-badge", "ledger-status"],
    )

    content = [
        render_card(
            title="Document Information",
            subtitle="Generated by W-PAGE-001",
            body=f'''
                <p>This is a demo document generated by the WINDI Page Renderer.</p>
                <div style="display: flex; gap: var(--w-space-4); margin-top: var(--w-space-4);">
                    {render_seal_badge("sealed", "sha256:abc123...", "2026-03-06")}
                    {render_ledger_status(True, 42883)}
                </div>
            ''',
        ),
    ]

    result = render_page(plan, content, "demo_preview_001")

    print(f"Generated page: {len(result.html)} bytes")
    print(f"Provenance:")
    print(f"  HTML hash: {result.provenance.html_hash[:40]}...")
    print(f"  Combined hash: {result.provenance.combined_hash[:40]}...")
    print(f"  Size: {result.provenance.size_bytes} bytes")
