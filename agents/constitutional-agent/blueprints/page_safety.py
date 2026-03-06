"""
WINDI Page Safety Filter — W-PAGE-001 Component
=================================================

Validates HTML output for security vulnerabilities before rendering.
Part of the Constitutional Agent's Page Generator module.

FORBIDDEN:
- eval(), document.write(), innerHTML injection
- External scripts (except approved domains)
- Inline event handlers (onclick, onerror, etc.)
- javascript: URIs, data: URIs

Principle: "AI processes. Human decides. WINDI guarantees."

Version: 0.1.0
Component: W-PAGE-001
"""

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urlparse

__version__ = "0.1.0"
__component__ = "W-PAGE-001-SAFETY"


# ═══════════════════════════════════════════════════════════════
#  SAFETY CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# Patterns that are NEVER allowed in generated HTML
FORBIDDEN_PATTERNS = [
    (r'eval\s*\(', "eval() execution"),
    (r'document\.write\s*\(', "document.write() injection"),
    (r'\.innerHTML\s*=', "innerHTML assignment"),
    (r'\.outerHTML\s*=', "outerHTML assignment"),
    (r'insertAdjacentHTML\s*\(', "insertAdjacentHTML injection"),
    (r'<script\s+src\s*=\s*["\'](?!https?://(fonts\.googleapis\.com|fonts\.gstatic\.com))', "unauthorized external script"),
    (r'javascript\s*:', "javascript: URI"),
    (r'data\s*:\s*text/html', "data:text/html URI"),
    (r'on(click|load|error|mouseover|mouseout|focus|blur|change|submit|keydown|keyup|keypress)\s*=\s*["\']', "inline event handler"),
    (r'<iframe\s', "iframe element"),
    (r'<object\s', "object element"),
    (r'<embed\s', "embed element"),
    (r'<form\s+action\s*=\s*["\'](?!#)', "form with external action"),
    (r'expression\s*\(', "CSS expression"),
    (r'@import\s+["\'](?!https?://(fonts\.googleapis\.com))', "unauthorized CSS import"),
]

# Domains allowed for external resources
ALLOWED_EXTERNAL_DOMAINS = [
    'fonts.googleapis.com',
    'fonts.gstatic.com',
]

# Maximum allowed HTML size (10MB)
MAX_HTML_SIZE = 10 * 1024 * 1024


# ═══════════════════════════════════════════════════════════════
#  RESULT TYPES
# ═══════════════════════════════════════════════════════════════

@dataclass
class SafetyViolation:
    """A single safety violation found in the HTML."""
    pattern: str
    description: str
    line_number: Optional[int] = None
    context: Optional[str] = None


@dataclass
class SafetyResult:
    """Result of safety verification."""
    passed: bool
    violations: List[SafetyViolation]
    checked_at: str
    html_size: int
    checks_performed: int
    version: str = __version__

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "violations": [
                {
                    "pattern": v.pattern,
                    "description": v.description,
                    "line_number": v.line_number,
                    "context": v.context,
                }
                for v in self.violations
            ],
            "checked_at": self.checked_at,
            "html_size": self.html_size,
            "checks_performed": self.checks_performed,
            "version": self.version,
        }


# ═══════════════════════════════════════════════════════════════
#  SAFETY FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return None


def find_line_number(html: str, match_start: int) -> int:
    """Find line number for a match position."""
    return html[:match_start].count('\n') + 1


def get_context(html: str, match_start: int, match_end: int, context_size: int = 50) -> str:
    """Get context around a match."""
    start = max(0, match_start - context_size)
    end = min(len(html), match_end + context_size)
    context = html[start:end]
    if start > 0:
        context = "..." + context
    if end < len(html):
        context = context + "..."
    return context.replace('\n', ' ').strip()


def verify(html: str) -> SafetyResult:
    """
    Verify HTML content for safety violations.

    Args:
        html: The HTML content to verify

    Returns:
        SafetyResult with passed=True if safe, False if violations found
    """
    violations = []
    checked_at = datetime.now(timezone.utc).isoformat()

    # Check size limit
    html_size = len(html.encode('utf-8'))
    if html_size > MAX_HTML_SIZE:
        violations.append(SafetyViolation(
            pattern="size_limit",
            description=f"HTML exceeds maximum size ({html_size} > {MAX_HTML_SIZE})",
        ))

    # Check forbidden patterns
    for pattern, description in FORBIDDEN_PATTERNS:
        for match in re.finditer(pattern, html, re.IGNORECASE):
            violations.append(SafetyViolation(
                pattern=pattern,
                description=description,
                line_number=find_line_number(html, match.start()),
                context=get_context(html, match.start(), match.end()),
            ))

    # Check external scripts
    script_pattern = r'<script[^>]+src\s*=\s*["\']([^"\']+)["\']'
    for match in re.finditer(script_pattern, html, re.IGNORECASE):
        src = match.group(1)
        domain = extract_domain(src)
        if domain and domain not in ALLOWED_EXTERNAL_DOMAINS:
            violations.append(SafetyViolation(
                pattern="unauthorized_external_script",
                description=f"External script from unauthorized domain: {domain}",
                line_number=find_line_number(html, match.start()),
                context=get_context(html, match.start(), match.end()),
            ))

    # Check external stylesheets
    link_pattern = r'<link[^>]+href\s*=\s*["\']([^"\']+)["\'][^>]+rel\s*=\s*["\']stylesheet["\']'
    link_pattern_alt = r'<link[^>]+rel\s*=\s*["\']stylesheet["\'][^>]+href\s*=\s*["\']([^"\']+)["\']'

    for pattern in [link_pattern, link_pattern_alt]:
        for match in re.finditer(pattern, html, re.IGNORECASE):
            href = match.group(1)
            domain = extract_domain(href)
            if domain and domain not in ALLOWED_EXTERNAL_DOMAINS:
                violations.append(SafetyViolation(
                    pattern="unauthorized_external_stylesheet",
                    description=f"External stylesheet from unauthorized domain: {domain}",
                    line_number=find_line_number(html, match.start()),
                    context=get_context(html, match.start(), match.end()),
                ))

    return SafetyResult(
        passed=len(violations) == 0,
        violations=violations,
        checked_at=checked_at,
        html_size=html_size,
        checks_performed=len(FORBIDDEN_PATTERNS) + 2,  # patterns + scripts + stylesheets
        version=__version__,
    )


def verify_quick(html: str) -> bool:
    """
    Quick safety check - returns True if safe, False otherwise.
    Use verify() for detailed violation information.
    """
    result = verify(html)
    return result.passed


# ═══════════════════════════════════════════════════════════════
#  HTML SANITIZATION (optional, for cleanup)
# ═══════════════════════════════════════════════════════════════

def sanitize_html(html: str) -> str:
    """
    Remove potentially dangerous elements from HTML.
    NOTE: This is a fallback - properly generated HTML should not need this.

    Use with caution - may break legitimate functionality.
    """
    # Remove script tags (except inline safe scripts)
    html = re.sub(r'<script\s+src\s*=[^>]*>.*?</script>', '', html, flags=re.IGNORECASE | re.DOTALL)

    # Remove inline event handlers
    html = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)

    # Remove javascript: URIs
    html = re.sub(r'href\s*=\s*["\']javascript:[^"\']*["\']', 'href="#"', html, flags=re.IGNORECASE)

    # Remove iframes, objects, embeds
    html = re.sub(r'<(iframe|object|embed)[^>]*>.*?</\1>', '', html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r'<(iframe|object|embed)[^>]*/>', '', html, flags=re.IGNORECASE)

    return html


# ═══════════════════════════════════════════════════════════════
#  TEST / DEMO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Test safe HTML
    safe_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <link href="https://fonts.googleapis.com/css2?family=Inter&display=swap" rel="stylesheet">
        <style>body { font-family: Inter; }</style>
    </head>
    <body>
        <h1>Safe Page</h1>
        <button class="w-btn">Click me</button>
    </body>
    </html>
    """

    result = verify(safe_html)
    print(f"Safe HTML: passed={result.passed}, violations={len(result.violations)}")

    # Test unsafe HTML
    unsafe_html = """
    <script>eval('alert(1)')</script>
    <div onclick="alert('xss')">Click me</div>
    <a href="javascript:void(0)">Link</a>
    <script src="https://evil.com/script.js"></script>
    """

    result = verify(unsafe_html)
    print(f"Unsafe HTML: passed={result.passed}, violations={len(result.violations)}")
    for v in result.violations:
        print(f"  - {v.description} (line {v.line_number})")
