"""
CSS Guardian — Post-Processor for W-SITES-001
§249 WINDI Generation Grammar · Safety Net

Normalizes LLM output to KLAR/NOIR design system.
Even the best prompt escapes sometimes — this catches failures silently.

Invariants: I11 (forensic integrity), I14 (explicit failure)
Liga IA+H · Kempten, Bavaria · 2026
"""

import re
from typing import Tuple, List

# ═══════════════════════════════════════════════════════════════
# KLAR/NOIR PALETTE
# ═══════════════════════════════════════════════════════════════

VALID_COLORS = {
    "#F5F0E0",  # klar
    "#EBE5D2",  # klar-edge
    "#080808",  # noir
    "#2A2A2A",  # noir-soft
    "#8B6914",  # gold
    "#D4C896",  # gold-faint
    "#ffffff",  # white (allowed for contrast)
    "#000000",  # black (alias for noir)
    "transparent",
    "inherit",
    "currentColor",
}

# Colors to replace → target
COLOR_REPLACEMENTS = {
    # Purples/Violets
    r"#[89ab][0-9a-f][0-9a-f][0-9a-f]ff": "#8B6914",  # purple-ish → gold
    r"#[cdef][0-9a-f][0-9a-f][0-9a-f]ff": "#D4C896",  # light purple → gold-faint
    r"purple": "#8B6914",
    r"violet": "#8B6914",
    r"indigo": "#8B6914",

    # Pinks/Magentas
    r"#[ef][0-9a-f][48][0-9a-f][89ab][0-9a-f]": "#8B6914",  # pink-ish → gold
    r"pink": "#D4C896",
    r"magenta": "#8B6914",
    r"fuchsia": "#8B6914",

    # Cyans/Teals
    r"cyan": "#8B6914",
    r"teal": "#2A2A2A",
    r"turquoise": "#8B6914",

    # Blues (except very dark)
    r"#[0-5][0-9a-f][0-9a-f][0-9a-f]ff": "#8B6914",  # medium blue → gold
    r"blue": "#8B6914",
    r"navy": "#080808",

    # Bright greens
    r"lime": "#8B6914",
    r"#[0-9][0-9]ff[0-9][0-9]": "#8B6914",  # bright green → gold

    # Oranges/Reds (keep gold-adjacent)
    r"orange": "#8B6914",
    r"red": "#8B6914",
}

# ═══════════════════════════════════════════════════════════════
# PATTERN REMOVALS
# ═══════════════════════════════════════════════════════════════

GRADIENT_PATTERN = re.compile(
    r'(linear-gradient|radial-gradient|conic-gradient)\s*\([^)]+\)',
    re.IGNORECASE
)

BORDER_RADIUS_PATTERN = re.compile(
    r'border-radius\s*:\s*[^;0]+;',
    re.IGNORECASE
)

ANIMATION_PATTERN = re.compile(
    r'(animation|transition)\s*:\s*[^;]*[3-9]\d{2,}ms[^;]*;',
    re.IGNORECASE
)

BOX_SHADOW_COLORED_PATTERN = re.compile(
    r'box-shadow\s*:[^;]*(rgba?\s*\([^)]+\)|#[0-9a-f]{3,8})[^;]*;',
    re.IGNORECASE
)

EXTERNAL_IMPORT_PATTERN = re.compile(
    r'@import\s+url\s*\([^)]+\)\s*;',
    re.IGNORECASE
)

EXTERNAL_FONT_PATTERN = re.compile(
    r"@import\s+['\"]https?://[^'\"]+['\"];",
    re.IGNORECASE
)


def normalize_gradients(css: str) -> Tuple[str, int]:
    """Replace all gradients with solid klar background."""
    count = len(GRADIENT_PATTERN.findall(css))
    css = GRADIENT_PATTERN.sub('var(--klar)', css)
    return css, count


def normalize_border_radius(css: str) -> Tuple[str, int]:
    """Force all border-radius to 0 (institutional = sharp)."""
    matches = BORDER_RADIUS_PATTERN.findall(css)
    count = len([m for m in matches if '0' not in m])
    css = BORDER_RADIUS_PATTERN.sub('border-radius: 0;', css)
    return css, count


def normalize_colors(css: str) -> Tuple[str, int]:
    """Replace forbidden colors with palette equivalents."""
    count = 0
    for pattern, replacement in COLOR_REPLACEMENTS.items():
        matches = re.findall(pattern, css, re.IGNORECASE)
        count += len(matches)
        css = re.sub(pattern, replacement, css, flags=re.IGNORECASE)
    return css, count


def remove_external_imports(css: str) -> Tuple[str, int]:
    """Remove @import for GDPR compliance."""
    count = len(EXTERNAL_IMPORT_PATTERN.findall(css)) + len(EXTERNAL_FONT_PATTERN.findall(css))
    css = EXTERNAL_IMPORT_PATTERN.sub('/* external import removed for GDPR */', css)
    css = EXTERNAL_FONT_PATTERN.sub('/* external font removed for GDPR */', css)
    return css, count


def normalize_animations(css: str) -> Tuple[str, int]:
    """Cap animations at 200ms."""
    count = len(ANIMATION_PATTERN.findall(css))
    # Replace long durations with 200ms
    css = re.sub(r'(\d{3,})ms', lambda m: '200ms' if int(m.group(1)) > 200 else m.group(0), css)
    return css, count


# ═══════════════════════════════════════════════════════════════
# CANONICAL CSS INJECTION
# ═══════════════════════════════════════════════════════════════

CANONICAL_CSS_OVERRIDE = """
/* §249 WINDI Generation Grammar — Canonical Override */
:root {
  --klar: #F5F0E0 !important;
  --klar-edge: #EBE5D2 !important;
  --noir: #080808 !important;
  --noir-soft: #2A2A2A !important;
  --gold: #8B6914 !important;
  --gold-faint: #D4C896 !important;
  --line: #2A2A2A !important;
}
body {
  background: var(--klar) !important;
  color: var(--noir) !important;
}
h1, h2, h3, h4, h5, h6 {
  font-family: 'Bricolage Grotesque', Georgia, 'Times New Roman', serif !important;
}
code, pre, .proof-grid, .proof-label, .proof-minimal {
  font-family: 'JetBrains Mono', 'Courier New', monospace !important;
}
"""


def inject_canonical_css(html: str) -> str:
    """Inject canonical CSS override at end of <style> block."""
    # Find the closing </style> tag
    style_close = html.rfind('</style>')
    if style_close == -1:
        return html

    # Insert canonical CSS before </style>
    return html[:style_close] + CANONICAL_CSS_OVERRIDE + html[style_close:]


# ═══════════════════════════════════════════════════════════════
# FORENSIC VALIDATION
# ═══════════════════════════════════════════════════════════════

FORENSIC_TRIGGERS = [
    'ledger', 'recibo', 'receipt', 'verificação', 'verify',
    'imutável', 'immutable', 'forense', 'forensic',
    'auditoria', 'audit', 'windi', 'compliance', 'governance'
]

FORENSIC_BLOCK_PATTERN = re.compile(
    r'<section[^>]*class=["\'][^"\']*forensic-proof[^"\']*["\'][^>]*>',
    re.IGNORECASE
)

MINIMAL_PROOF_PATTERN = re.compile(
    r'WINDI-SITES-001-[A-F0-9]{8}',
    re.IGNORECASE
)


def requires_full_forensic(prompt: str) -> bool:
    """Check if prompt triggers full forensic block requirement."""
    prompt_lower = prompt.lower()
    return any(trigger in prompt_lower for trigger in FORENSIC_TRIGGERS)


def has_forensic_block(html: str) -> bool:
    """Check if HTML contains full forensic proof block."""
    return bool(FORENSIC_BLOCK_PATTERN.search(html))


def has_minimal_proof(html: str) -> bool:
    """Check if HTML contains minimal proof line."""
    return bool(MINIMAL_PROOF_PATTERN.search(html))


def validate_forensic(html: str, prompt: str) -> Tuple[bool, str]:
    """
    Validate forensic requirements.

    Returns:
        (is_valid, error_message)
    """
    # Minimal proof is ALWAYS required (rule 3C)
    if not has_minimal_proof(html):
        return False, "FORENSIC_MISSING: Minimal proof line required in footer (rule 3C)"

    # Full block required if prompt triggers it
    if requires_full_forensic(prompt) and not has_forensic_block(html):
        return False, f"FORENSIC_INCOMPLETE: Full proof block required (prompt contains trigger words)"

    return True, ""


# ═══════════════════════════════════════════════════════════════
# MAIN GUARDIAN FUNCTION
# ═══════════════════════════════════════════════════════════════

def guard_html(html: str, prompt: str = "") -> Tuple[str, dict]:
    """
    Apply CSS Guardian post-processing to generated HTML.

    Args:
        html: Generated HTML content
        prompt: Original user prompt (for forensic validation)

    Returns:
        Tuple of (processed_html, report)
        Report contains corrections made and any validation errors.
    """
    report = {
        "corrections": [],
        "warnings": [],
        "errors": [],
        "forensic_valid": True,
    }

    # Extract CSS from HTML
    style_match = re.search(r'<style[^>]*>(.*?)</style>', html, re.DOTALL | re.IGNORECASE)
    if not style_match:
        report["warnings"].append("No <style> block found — cannot normalize CSS")
        return html, report

    css = style_match.group(1)
    original_css = css

    # Apply normalizations
    css, gradient_count = normalize_gradients(css)
    if gradient_count:
        report["corrections"].append(f"Removed {gradient_count} gradient(s)")

    css, radius_count = normalize_border_radius(css)
    if radius_count:
        report["corrections"].append(f"Normalized {radius_count} border-radius to 0")

    css, color_count = normalize_colors(css)
    if color_count:
        report["corrections"].append(f"Replaced {color_count} forbidden color(s)")

    css, import_count = remove_external_imports(css)
    if import_count:
        report["corrections"].append(f"Removed {import_count} external import(s) for GDPR")

    css, animation_count = normalize_animations(css)
    if animation_count:
        report["corrections"].append(f"Capped {animation_count} animation duration(s)")

    # Replace CSS in HTML
    if css != original_css:
        html = html.replace(original_css, css)

    # Inject canonical CSS override
    html = inject_canonical_css(html)
    report["corrections"].append("Injected canonical CSS override")

    # Validate forensic requirements
    forensic_valid, forensic_error = validate_forensic(html, prompt)
    if not forensic_valid:
        report["forensic_valid"] = False
        report["errors"].append(forensic_error)

    return html, report


# ═══════════════════════════════════════════════════════════════
# CLI TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    test_html = """<!DOCTYPE html>
<html>
<head>
<style>
body { background: linear-gradient(to right, #a855f7, #ec4899); }
.card { border-radius: 16px; }
h1 { color: purple; }
</style>
</head>
<body>
<h1>Test</h1>
<footer>Verified by WINDI<br>WINDI-SITES-001-12345678</footer>
</body>
</html>"""

    processed, report = guard_html(test_html, "test prompt")

    print("=== CSS Guardian Test ===")
    print(f"Corrections: {report['corrections']}")
    print(f"Warnings: {report['warnings']}")
    print(f"Errors: {report['errors']}")
    print(f"Forensic Valid: {report['forensic_valid']}")
    print("\n=== Processed HTML ===")
    print(processed[:500] + "..." if len(processed) > 500 else processed)
