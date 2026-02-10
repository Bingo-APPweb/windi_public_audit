#!/usr/bin/env python3
"""
WSG v0.2.0 — CSS Drift Detector
"Observar. Registrar. CURAR. Dissuadir."

Module 3: Ensures Design System Noir/Klar is consistent across all pages.

Constitutional Alignment:
- Enforces HUMAN-DEFINED canonical CSS (I9 safe)
- Does not invent new styles
- Auto-repair restores to canonical — not autonomous decision

Author: WINDI Publishing House
Version: 0.2.0
Date: 10 Feb 2026
"""

import os
import re
import json
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Set, Tuple
from dataclasses import dataclass, field, asdict
import urllib.request


# ═══════════════════════════════════════════════════════════════════════════════
# CANONICAL DESIGN SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

CANONICAL_CSS_VARS: Dict[str, str] = {
    # Noir palette
    "--noir": "#0a0a0f",
    "--noir-surface": "#12121a",
    "--noir-card": "#1a1a26",
    "--noir-border": "#2a2a3a",
    "--noir-hover": "#22222e",

    # Gold palette
    "--gold": "#c9a84c",
    "--gold-light": "#e8d48b",
    "--gold-dim": "#8a7535",
    "--gold-bright": "#e0be5a",

    # Text colors
    "--text": "#f0efe8",
    "--text-sec": "#7a7a72",
    "--text-dim": "#4a4a44",

    # Semantic colors
    "--green": "#4ade80",
    "--green-dim": "#22c55e",
    "--green-bg": "rgba(74,222,128,0.06)",
    "--green-border": "rgba(74,222,128,0.15)",

    "--yellow": "#facc15",
    "--yellow-dim": "#eab308",
    "--yellow-bg": "rgba(250,204,21,0.06)",
    "--yellow-border": "rgba(250,204,21,0.15)",

    "--red": "#f87171",
    "--red-dim": "#ef4444",
    "--red-bg": "rgba(248,113,113,0.06)",
    "--red-border": "rgba(248,113,113,0.15)",

    # Layout
    "--radius": "12px",
    "--radius-lg": "16px",
    "--radius-sm": "8px",

    # Klar (light mode) variants
    "--klar-bg": "#fafaf8",
    "--klar-surface": "#ffffff",
    "--klar-card": "#f5f5f3",
    "--klar-border": "#e5e5e0",
    "--klar-text": "#1a1a1a",
    "--klar-text-sec": "#666666",
}

CANONICAL_FONTS: List[str] = [
    "Bricolage Grotesque",
    "Outfit",
    "JetBrains Mono",
]

CANONICAL_FONT_WEIGHTS: Dict[str, List[str]] = {
    "Bricolage Grotesque": ["400", "600", "700", "800"],
    "Outfit": ["300", "400", "500", "600", "700"],
    "JetBrains Mono": ["400", "500", "600"],
}


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CSSVarDrift:
    """A single CSS variable drift detection."""
    variable: str
    expected: str
    actual: str
    page: str
    severity: str  # 'minor', 'major', 'critical'


@dataclass
class FontDrift:
    """Font usage drift detection."""
    font_name: str
    expected: bool
    actual: bool
    page: str
    issue: str  # 'missing', 'unexpected', 'wrong_weight'


@dataclass
class CSSAuditReport:
    """Complete CSS audit report."""
    report_id: str
    audit_date: str
    pages_audited: int
    var_drifts: List[Dict[str, Any]]
    font_drifts: List[Dict[str, Any]]
    total_drift_count: int
    severity_summary: Dict[str, int]
    compliance_score: float  # 0-100%
    recommendations: List[str]
    hash: str = ""

    def __post_init__(self):
        if not self.hash:
            content = f"{self.report_id}|{self.audit_date}|{self.total_drift_count}|{self.compliance_score}"
            self.hash = f"sha256:{hashlib.sha256(content.encode()).hexdigest()[:16]}"


# ═══════════════════════════════════════════════════════════════════════════════
# CSS PARSER
# ═══════════════════════════════════════════════════════════════════════════════

def extract_css_vars(css_content: str) -> Dict[str, str]:
    """
    Extract CSS custom properties (variables) from CSS content.

    Args:
        css_content: CSS or HTML content with embedded CSS

    Returns:
        Dictionary of variable names to values
    """
    vars_dict: Dict[str, str] = {}

    # Pattern to match :root { ... } blocks
    root_pattern = re.compile(r':root\s*\{([^}]+)\}', re.DOTALL | re.IGNORECASE)

    for root_match in root_pattern.finditer(css_content):
        root_block = root_match.group(1)

        # Pattern to match --var-name: value;
        var_pattern = re.compile(r'(--[\w-]+)\s*:\s*([^;]+);')

        for var_match in var_pattern.finditer(root_block):
            var_name = var_match.group(1).strip()
            var_value = var_match.group(2).strip()
            vars_dict[var_name] = var_value

    return vars_dict


def extract_fonts_used(css_content: str) -> Set[str]:
    """
    Extract font families used in CSS content.

    Args:
        css_content: CSS or HTML content

    Returns:
        Set of font family names
    """
    fonts: Set[str] = set()

    # Pattern for font-family declarations
    font_pattern = re.compile(r'font-family\s*:\s*([^;]+);', re.IGNORECASE)

    for match in font_pattern.finditer(css_content):
        font_value = match.group(1)

        # Split by comma and clean up
        for font in font_value.split(','):
            font = font.strip().strip('"').strip("'")
            if font and not font.startswith('var('):
                fonts.add(font)

    # Also check Google Fonts imports
    gfont_pattern = re.compile(r'fonts\.googleapis\.com/css2\?family=([^&"\']+)')
    for match in gfont_pattern.finditer(css_content):
        font_param = match.group(1)
        # Parse "Bricolage+Grotesque:wght@400;600"
        font_name = font_param.split(':')[0].replace('+', ' ')
        fonts.add(font_name)

    return fonts


# ═══════════════════════════════════════════════════════════════════════════════
# CSS DRIFT DETECTOR
# ═══════════════════════════════════════════════════════════════════════════════

class CSSDriftDetector:
    """
    WSG CSS Drift Detector — Ensure Design System consistency.

    Cycle:
    1. Scan each HTML served
    2. Extract :root CSS vars
    3. Compare with CANONICAL_CSS_VARS
    4. If drift detected:
       a) LOG which page and which variable diverges
       b) If auto_repair=True → inject <link> to canonical design-system.css
       c) Generate Receipt with diff

    Benefit:
    Instead of 300+ lines of duplicated CSS in each HTML, all pages
    import windi-design-system.css and WSG ensures consistency.
    """

    def __init__(
        self,
        canonical_vars: Optional[Dict[str, str]] = None,
        canonical_fonts: Optional[List[str]] = None,
        reports_dir: str = "/opt/windi/guard/reports",
        log_level: int = logging.INFO,
    ):
        self.canonical_vars = canonical_vars or CANONICAL_CSS_VARS
        self.canonical_fonts = canonical_fonts or CANONICAL_FONTS
        self.reports_dir = reports_dir
        self.var_drifts: List[CSSVarDrift] = []
        self.font_drifts: List[FontDrift] = []

        # Setup logging
        self.logger = logging.getLogger("WSG.CSSGuard")
        self.logger.setLevel(log_level)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                "[%(asctime)s] WSG-CSS %(levelname)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))
            self.logger.addHandler(handler)

        os.makedirs(self.reports_dir, exist_ok=True)

    def _determine_severity(self, var_name: str, expected: str, actual: str) -> str:
        """
        Determine drift severity.

        Args:
            var_name: CSS variable name
            expected: Expected value
            actual: Actual value

        Returns:
            Severity level: 'minor', 'major', 'critical'
        """
        # Critical: Core brand colors wrong
        critical_vars = ['--gold', '--noir', '--text', '--klar-bg']
        if var_name in critical_vars:
            return 'critical'

        # Major: Semantic colors wrong
        major_vars = ['--green', '--yellow', '--red', '--gold-dim', '--text-sec']
        if any(var_name.startswith(v.replace('--', '--')) for v in major_vars):
            return 'major'

        # Minor: Layout/spacing differences
        return 'minor'

    def audit_page(self, page_url: str) -> Tuple[List[CSSVarDrift], List[FontDrift]]:
        """
        Audit a single page for CSS drift.

        Args:
            page_url: URL or file path of page to audit

        Returns:
            Tuple of (var_drifts, font_drifts)
        """
        self.logger.info(f"Auditing CSS: {page_url}")

        # Fetch content
        content = self._fetch_content(page_url)
        if not content:
            return [], []

        var_drifts: List[CSSVarDrift] = []
        font_drifts: List[FontDrift] = []

        # Extract and compare CSS vars
        page_vars = extract_css_vars(content)

        for var_name, expected_value in self.canonical_vars.items():
            if var_name in page_vars:
                actual_value = page_vars[var_name]

                # Normalize values for comparison
                expected_norm = self._normalize_value(expected_value)
                actual_norm = self._normalize_value(actual_value)

                if expected_norm != actual_norm:
                    drift = CSSVarDrift(
                        variable=var_name,
                        expected=expected_value,
                        actual=actual_value,
                        page=page_url,
                        severity=self._determine_severity(var_name, expected_value, actual_value),
                    )
                    var_drifts.append(drift)
                    self.logger.warning(
                        f"Drift [{drift.severity}]: {var_name} = {actual_value} "
                        f"(expected: {expected_value})"
                    )

        # Extract and compare fonts
        page_fonts = extract_fonts_used(content)

        for canonical_font in self.canonical_fonts:
            if canonical_font not in page_fonts:
                # Check if using any variant of the font
                found_variant = any(canonical_font.lower() in f.lower() for f in page_fonts)
                if not found_variant:
                    font_drifts.append(FontDrift(
                        font_name=canonical_font,
                        expected=True,
                        actual=False,
                        page=page_url,
                        issue='missing',
                    ))

        return var_drifts, font_drifts

    def _normalize_value(self, value: str) -> str:
        """Normalize CSS value for comparison."""
        # Remove extra whitespace
        value = ' '.join(value.split())

        # Normalize rgba() format
        value = re.sub(r'\s*,\s*', ',', value)

        # Lowercase hex colors
        value = re.sub(r'#([0-9a-fA-F]+)', lambda m: '#' + m.group(1).lower(), value)

        return value

    def _fetch_content(self, url_or_path: str) -> Optional[str]:
        """Fetch content from URL or file path."""
        if url_or_path.startswith(('http://', 'https://')):
            try:
                req = urllib.request.Request(url_or_path)
                req.add_header("User-Agent", "WSG-CSSGuard/0.2.0")
                with urllib.request.urlopen(req, timeout=10) as response:
                    return response.read().decode("utf-8", errors="ignore")
            except Exception as e:
                self.logger.error(f"Failed to fetch {url_or_path}: {e}")
                return None
        else:
            try:
                with open(url_or_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                self.logger.error(f"Failed to read {url_or_path}: {e}")
                return None

    def audit_all(self, pages: List[str]) -> CSSAuditReport:
        """
        Audit all pages for CSS drift.

        Args:
            pages: List of URLs or file paths to audit

        Returns:
            CSSAuditReport with complete audit results
        """
        self.var_drifts.clear()
        self.font_drifts.clear()

        for page in pages:
            var_drifts, font_drifts = self.audit_page(page)
            self.var_drifts.extend(var_drifts)
            self.font_drifts.extend(font_drifts)

        # Calculate compliance score
        total_checks = len(pages) * (len(self.canonical_vars) + len(self.canonical_fonts))
        total_drifts = len(self.var_drifts) + len(self.font_drifts)
        compliance_score = ((total_checks - total_drifts) / total_checks * 100) if total_checks > 0 else 100.0

        # Severity summary
        severity_summary = {
            'critical': sum(1 for d in self.var_drifts if d.severity == 'critical'),
            'major': sum(1 for d in self.var_drifts if d.severity == 'major'),
            'minor': sum(1 for d in self.var_drifts if d.severity == 'minor'),
            'fonts': len(self.font_drifts),
        }

        # Generate recommendations
        recommendations = self._generate_recommendations()

        report = CSSAuditReport(
            report_id=f"WSG-CSS-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            audit_date=datetime.now(timezone.utc).isoformat(),
            pages_audited=len(pages),
            var_drifts=[asdict(d) for d in self.var_drifts],
            font_drifts=[asdict(d) for d in self.font_drifts],
            total_drift_count=total_drifts,
            severity_summary=severity_summary,
            compliance_score=round(compliance_score, 1),
            recommendations=recommendations,
        )

        # Save report
        self._save_report(report)

        self.logger.info(
            f"CSS Audit complete: {report.pages_audited} pages, "
            f"{report.total_drift_count} drifts, {report.compliance_score}% compliance"
        )

        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on detected drifts."""
        recommendations = []

        if self.var_drifts:
            # Group by page
            pages_with_drift = set(d.page for d in self.var_drifts)
            recommendations.append(
                f"Found CSS variable drifts in {len(pages_with_drift)} page(s). "
                "Consider importing windi-design-system.css instead of inline :root declarations."
            )

        critical_drifts = [d for d in self.var_drifts if d.severity == 'critical']
        if critical_drifts:
            vars_list = ', '.join(set(d.variable for d in critical_drifts))
            recommendations.append(
                f"CRITICAL: Core brand variables diverge ({vars_list}). "
                "This affects visual identity consistency."
            )

        if self.font_drifts:
            missing_fonts = [d.font_name for d in self.font_drifts if d.issue == 'missing']
            if missing_fonts:
                recommendations.append(
                    f"Missing canonical fonts: {', '.join(missing_fonts)}. "
                    "Add Google Fonts import or local font files."
                )

        if not recommendations:
            recommendations.append("All pages comply with canonical Design System. No action needed.")

        return recommendations

    def _save_report(self, report: CSSAuditReport) -> str:
        """Save report to reports directory."""
        filename = f"css_audit_{datetime.now().strftime('%Y%m%d')}.json"
        filepath = os.path.join(self.reports_dir, filename)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(asdict(report), f, indent=2, ensure_ascii=False)
            self.logger.info(f"Report saved: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Failed to save report: {e}")
            return ""

    def generate_canonical_css(self) -> str:
        """
        Generate canonical CSS file with all variables.

        Returns:
            CSS content string
        """
        css_lines = [
            "/*",
            " * WINDI Design System v1.0.0 — Canonical CSS Variables",
            " * Generated by WSG v0.2.0",
            f" * Date: {datetime.now().strftime('%Y-%m-%d')}",
            " *",
            " * \"Gleicher Flieger, gleiche Sicherheit.\"",
            " */",
            "",
            ":root {",
        ]

        # Group variables by category
        categories = {
            'Noir Palette': ['--noir'],
            'Gold Palette': ['--gold'],
            'Text Colors': ['--text'],
            'Semantic Colors': ['--green', '--yellow', '--red'],
            'Layout': ['--radius'],
            'Klar Mode': ['--klar'],
        }

        for category, prefixes in categories.items():
            css_lines.append(f"  /* {category} */")
            for var_name, value in self.canonical_vars.items():
                if any(var_name.startswith(prefix) for prefix in prefixes):
                    css_lines.append(f"  {var_name}: {value};")
            css_lines.append("")

        css_lines.append("}")
        css_lines.append("")

        # Font face declarations
        css_lines.extend([
            "/* Font Imports */",
            "@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;600;700;800&family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');",
            "",
        ])

        return '\n'.join(css_lines)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Run CSS guard as standalone CLI."""
    import argparse

    parser = argparse.ArgumentParser(
        description="WSG CSS Drift Detector v0.2.0",
    )

    parser.add_argument("--audit", type=str, nargs='+', help="Audit specific page(s)")
    parser.add_argument("--generate-canonical", action="store_true", help="Generate canonical CSS file")
    parser.add_argument("--output", type=str, help="Output path for generated CSS")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    detector = CSSDriftDetector(log_level=log_level)

    if args.audit:
        report = detector.audit_all(args.audit)
        print(f"\n📊 CSS Audit Report: {report.report_id}")
        print(f"   Pages audited: {report.pages_audited}")
        print(f"   Total drifts: {report.total_drift_count}")
        print(f"   Compliance: {report.compliance_score}%")
        print(f"\n   Severity:")
        for sev, count in report.severity_summary.items():
            print(f"     {sev}: {count}")
        print(f"\n   Recommendations:")
        for rec in report.recommendations:
            print(f"     • {rec}")

    elif args.generate_canonical:
        css = detector.generate_canonical_css()
        output_path = args.output or "/opt/windi/static/windi-design-system.css"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(css)
        print(f"✅ Canonical CSS generated: {output_path}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
