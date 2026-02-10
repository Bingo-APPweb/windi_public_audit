#!/usr/bin/env python3
"""
WSG v0.2.0 — i18n Consistency Guard
"Observar. Registrar. CURAR. Dissuadir."

Module 4: Detects pages with incomplete or inconsistent i18n.

Constitutional Alignment:
- Reports gaps only — HUMAN translates (I9 safe)
- Does not auto-translate
- Does not make content decisions

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
from enum import Enum
from html.parser import HTMLParser
import urllib.request


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

REQUIRED_LANGUAGES: List[str] = ["de", "en", "pt"]

class I18nPattern(Enum):
    """i18n implementation patterns in WINDI codebase."""
    CANONICAL = "data_attributes"      # data-de, data-en, data-pt (master pattern)
    ACCEPTED = "translations_object"   # translations{} object (admin pattern)
    DEPRECATED = "manual_getelementbyid"  # getElementById manual swap
    UNKNOWN = "unknown"


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class I18nElement:
    """An element with i18n content."""
    element_id: str
    element_tag: str
    languages_found: List[str]
    languages_missing: List[str]
    pattern: I18nPattern
    line_number: int = 0


@dataclass
class I18nPageReport:
    """i18n audit for a single page."""
    page_url: str
    pattern_detected: I18nPattern
    total_elements: int
    complete_elements: int
    incomplete_elements: int
    missing_translations: List[Dict[str, Any]]
    coverage: Dict[str, float]  # {'de': 100%, 'en': 100%, 'pt': 98%}


@dataclass
class I18nAuditReport:
    """Complete i18n audit report."""
    report_id: str
    audit_date: str
    pages_audited: int
    total_elements: int
    complete_count: int
    incomplete_count: int
    overall_coverage: Dict[str, float]
    pages: List[Dict[str, Any]]
    migration_suggestions: List[str]
    hash: str = ""

    def __post_init__(self):
        if not self.hash:
            content = f"{self.report_id}|{self.audit_date}|{self.incomplete_count}"
            self.hash = f"sha256:{hashlib.sha256(content.encode()).hexdigest()[:16]}"


# ═══════════════════════════════════════════════════════════════════════════════
# HTML PARSER FOR i18n
# ═══════════════════════════════════════════════════════════════════════════════

class I18nExtractor(HTMLParser):
    """Extract i18n elements from HTML."""

    def __init__(self, required_languages: List[str]):
        super().__init__()
        self.required_languages = required_languages
        self.elements: List[I18nElement] = []
        self.current_line = 1
        self.pattern_detected: I18nPattern = I18nPattern.UNKNOWN

        # Track data-{lang} pattern
        self.data_attr_elements: List[I18nElement] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        attrs_dict = dict(attrs)

        # Check for data-{lang} attributes (CANONICAL pattern)
        lang_attrs = {}
        for lang in self.required_languages:
            data_attr = f"data-{lang}"
            if data_attr in attrs_dict:
                lang_attrs[lang] = attrs_dict[data_attr]

        if lang_attrs:
            self.pattern_detected = I18nPattern.CANONICAL

            languages_found = list(lang_attrs.keys())
            languages_missing = [l for l in self.required_languages if l not in lang_attrs]

            element_id = attrs_dict.get('id', f'anonymous-{len(self.elements)}')

            self.elements.append(I18nElement(
                element_id=element_id,
                element_tag=tag,
                languages_found=languages_found,
                languages_missing=languages_missing,
                pattern=I18nPattern.CANONICAL,
                line_number=self.getpos()[0],
            ))

    def handle_data(self, data: str):
        # Track line numbers
        self.current_line += data.count('\n')


def detect_translations_object(content: str) -> Tuple[bool, Dict[str, int]]:
    """
    Detect translations{} object pattern.

    Args:
        content: HTML/JS content

    Returns:
        Tuple of (pattern_found, {lang: count})
    """
    # Pattern: const translations = { de: {...}, en: {...}, pt: {...} }
    pattern = re.compile(
        r'(?:const|let|var)\s+translations\s*=\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}',
        re.DOTALL
    )

    match = pattern.search(content)
    if not match:
        return False, {}

    translations_block = match.group(1)

    # Count keys per language
    lang_counts: Dict[str, int] = {}
    for lang in REQUIRED_LANGUAGES:
        # Find lang: { ... }
        lang_pattern = re.compile(rf'{lang}\s*:\s*\{{([^}}]+)\}}')
        lang_match = lang_pattern.search(translations_block)
        if lang_match:
            # Count keys
            keys = re.findall(r'[\w_]+\s*:', lang_match.group(1))
            lang_counts[lang] = len(keys)

    return bool(lang_counts), lang_counts


def detect_getelementbyid_pattern(content: str) -> bool:
    """
    Detect deprecated getElementById i18n pattern.

    Args:
        content: HTML/JS content

    Returns:
        True if deprecated pattern detected
    """
    # Pattern: document.getElementById(...).innerText = translations[lang][...]
    patterns = [
        r'getElementById\(["\'][^"\']+["\']\)\.(?:innerText|textContent)\s*=\s*translations',
        r'getElementById\(["\'][^"\']+["\']\)\.(?:innerText|textContent)\s*=\s*\w+\[lang\]',
    ]

    for pattern in patterns:
        if re.search(pattern, content):
            return True

    return False


# ═══════════════════════════════════════════════════════════════════════════════
# i18n CONSISTENCY GUARD
# ═══════════════════════════════════════════════════════════════════════════════

class I18nConsistencyGuard:
    """
    WSG i18n Consistency Guard — Detect incomplete/inconsistent translations.

    Cycle:
    1. Scan each HTML
    2. Detect which i18n pattern is used
    3. Verify ALL visible texts have translations for all 3 languages
    4. If language missing:
       a) FLAG: "[PAGE] missing PT translation for element #xyz"
       b) Coverage report: "master/: DE=100% EN=100% PT=98%"
    5. Migration suggestion: "admin/ uses pattern 2, recommend migration to pattern 1"

    i18n Patterns (in order of preference):
    1. CANONICAL: data-{lang} attributes (master pattern)
    2. ACCEPTED: translations{} object (admin pattern)
    3. DEPRECATED: getElementById manual
    """

    def __init__(
        self,
        required_languages: Optional[List[str]] = None,
        reports_dir: str = "/opt/windi/guard/reports",
        log_level: int = logging.INFO,
    ):
        self.required_languages = required_languages or REQUIRED_LANGUAGES
        self.reports_dir = reports_dir
        self.page_reports: List[I18nPageReport] = []

        # Setup logging
        self.logger = logging.getLogger("WSG.I18nGuard")
        self.logger.setLevel(log_level)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                "[%(asctime)s] WSG-I18N %(levelname)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))
            self.logger.addHandler(handler)

        os.makedirs(self.reports_dir, exist_ok=True)

    def audit_page(self, page_url: str) -> I18nPageReport:
        """
        Audit a single page for i18n completeness.

        Args:
            page_url: URL or file path of page to audit

        Returns:
            I18nPageReport with audit results
        """
        self.logger.info(f"Auditing i18n: {page_url}")

        content = self._fetch_content(page_url)
        if not content:
            return I18nPageReport(
                page_url=page_url,
                pattern_detected=I18nPattern.UNKNOWN,
                total_elements=0,
                complete_elements=0,
                incomplete_elements=0,
                missing_translations=[],
                coverage={lang: 0.0 for lang in self.required_languages},
            )

        # Detect pattern used
        pattern = self._detect_pattern(content)
        self.logger.debug(f"Detected pattern: {pattern.value}")

        elements: List[I18nElement] = []
        lang_totals: Dict[str, int] = {lang: 0 for lang in self.required_languages}
        lang_found: Dict[str, int] = {lang: 0 for lang in self.required_languages}

        if pattern == I18nPattern.CANONICAL:
            # Parse with data-{lang} extractor
            parser = I18nExtractor(self.required_languages)
            try:
                parser.feed(content)
                elements = parser.elements
            except Exception as e:
                self.logger.error(f"Parse error: {e}")

            # Calculate coverage
            for elem in elements:
                for lang in self.required_languages:
                    lang_totals[lang] += 1
                    if lang in elem.languages_found:
                        lang_found[lang] += 1

        elif pattern == I18nPattern.ACCEPTED:
            # Parse translations{} object
            has_obj, lang_counts = detect_translations_object(content)
            if has_obj:
                max_keys = max(lang_counts.values()) if lang_counts else 0
                for lang in self.required_languages:
                    lang_totals[lang] = max_keys
                    lang_found[lang] = lang_counts.get(lang, 0)

                    if lang_found[lang] < max_keys:
                        elements.append(I18nElement(
                            element_id="translations_object",
                            element_tag="script",
                            languages_found=[l for l in self.required_languages if l in lang_counts],
                            languages_missing=[l for l in self.required_languages if lang_counts.get(l, 0) < max_keys],
                            pattern=I18nPattern.ACCEPTED,
                        ))

        # Calculate coverage percentages
        coverage = {}
        for lang in self.required_languages:
            if lang_totals[lang] > 0:
                coverage[lang] = round((lang_found[lang] / lang_totals[lang]) * 100, 1)
            else:
                coverage[lang] = 100.0  # No elements = 100% coverage

        # Find missing translations
        missing_translations = []
        for elem in elements:
            if elem.languages_missing:
                missing_translations.append({
                    'element_id': elem.element_id,
                    'element_tag': elem.element_tag,
                    'missing_languages': elem.languages_missing,
                    'line_number': elem.line_number,
                })
                self.logger.warning(
                    f"Missing {elem.languages_missing} for #{elem.element_id}"
                )

        complete_count = sum(1 for e in elements if not e.languages_missing)
        incomplete_count = len(elements) - complete_count

        return I18nPageReport(
            page_url=page_url,
            pattern_detected=pattern,
            total_elements=len(elements),
            complete_elements=complete_count,
            incomplete_elements=incomplete_count,
            missing_translations=missing_translations,
            coverage=coverage,
        )

    def _detect_pattern(self, content: str) -> I18nPattern:
        """Detect which i18n pattern the page uses."""
        # Check for CANONICAL pattern (data-{lang} attributes)
        canonical_pattern = re.compile(r'data-(?:de|en|pt)\s*=\s*["\']')
        if canonical_pattern.search(content):
            return I18nPattern.CANONICAL

        # Check for ACCEPTED pattern (translations object)
        has_obj, _ = detect_translations_object(content)
        if has_obj:
            return I18nPattern.ACCEPTED

        # Check for DEPRECATED pattern
        if detect_getelementbyid_pattern(content):
            return I18nPattern.DEPRECATED

        return I18nPattern.UNKNOWN

    def _fetch_content(self, url_or_path: str) -> Optional[str]:
        """Fetch content from URL or file path."""
        if url_or_path.startswith(('http://', 'https://')):
            try:
                req = urllib.request.Request(url_or_path)
                req.add_header("User-Agent", "WSG-I18nGuard/0.2.0")
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

    def audit_all(self, pages: List[str]) -> I18nAuditReport:
        """
        Audit all pages for i18n consistency.

        Args:
            pages: List of URLs or file paths

        Returns:
            I18nAuditReport with complete audit results
        """
        self.page_reports.clear()

        for page in pages:
            report = self.audit_page(page)
            self.page_reports.append(report)

        # Calculate overall coverage
        total_by_lang: Dict[str, int] = {lang: 0 for lang in self.required_languages}
        found_by_lang: Dict[str, int] = {lang: 0 for lang in self.required_languages}

        for pr in self.page_reports:
            for lang in self.required_languages:
                total_by_lang[lang] += pr.total_elements
                found_by_lang[lang] += int(pr.total_elements * pr.coverage.get(lang, 100) / 100)

        overall_coverage = {}
        for lang in self.required_languages:
            if total_by_lang[lang] > 0:
                overall_coverage[lang] = round((found_by_lang[lang] / total_by_lang[lang]) * 100, 1)
            else:
                overall_coverage[lang] = 100.0

        # Generate migration suggestions
        migration_suggestions = self._generate_migration_suggestions()

        # Totals
        total_elements = sum(pr.total_elements for pr in self.page_reports)
        complete_count = sum(pr.complete_elements for pr in self.page_reports)
        incomplete_count = sum(pr.incomplete_elements for pr in self.page_reports)

        report = I18nAuditReport(
            report_id=f"WSG-I18N-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            audit_date=datetime.now(timezone.utc).isoformat(),
            pages_audited=len(pages),
            total_elements=total_elements,
            complete_count=complete_count,
            incomplete_count=incomplete_count,
            overall_coverage=overall_coverage,
            pages=[asdict(pr) for pr in self.page_reports],
            migration_suggestions=migration_suggestions,
        )

        # Patch: convert Enum to string for JSON serialization
        for page in report.pages:
            if isinstance(page.get('pattern_detected'), I18nPattern):
                page['pattern_detected'] = page['pattern_detected'].value

        self._save_report(report)

        self.logger.info(
            f"i18n Audit complete: {report.pages_audited} pages, "
            f"{report.incomplete_count} incomplete elements, "
            f"Coverage: DE={overall_coverage.get('de', 0)}% EN={overall_coverage.get('en', 0)}% PT={overall_coverage.get('pt', 0)}%"
        )

        return report

    def _generate_migration_suggestions(self) -> List[str]:
        """Generate suggestions for i18n pattern migration."""
        suggestions = []

        # Group pages by pattern
        patterns_used: Dict[I18nPattern, List[str]] = {}
        for pr in self.page_reports:
            pattern = pr.pattern_detected
            if pattern not in patterns_used:
                patterns_used[pattern] = []
            patterns_used[pattern].append(pr.page_url)

        # Suggest migration from deprecated patterns
        if I18nPattern.DEPRECATED in patterns_used:
            pages = patterns_used[I18nPattern.DEPRECATED]
            suggestions.append(
                f"DEPRECATED: {len(pages)} page(s) use getElementById pattern. "
                "Recommend migration to data-{{lang}} attributes (CANONICAL)."
            )

        if I18nPattern.ACCEPTED in patterns_used and I18nPattern.CANONICAL in patterns_used:
            suggestions.append(
                f"Mixed patterns detected: {len(patterns_used.get(I18nPattern.ACCEPTED, []))} page(s) use translations{{}}, "
                f"{len(patterns_used.get(I18nPattern.CANONICAL, []))} use data-{{lang}}. "
                "Consider standardizing on CANONICAL pattern."
            )

        if I18nPattern.UNKNOWN in patterns_used:
            pages = patterns_used[I18nPattern.UNKNOWN]
            suggestions.append(
                f"UNKNOWN: {len(pages)} page(s) have no detectable i18n pattern. "
                "Review for hardcoded strings."
            )

        # Coverage suggestions
        for pr in self.page_reports:
            for lang, cov in pr.coverage.items():
                if cov < 100:
                    suggestions.append(
                        f"{pr.page_url}: {lang.upper()} coverage is {cov}%. "
                        f"Missing translations for {pr.incomplete_elements} element(s)."
                    )

        if not suggestions:
            suggestions.append("All pages have complete i18n coverage across DE/EN/PT.")

        return suggestions

    def _save_report(self, report: I18nAuditReport) -> str:
        """Save report to reports directory."""
        filename = f"i18n_audit_{datetime.now().strftime('%Y%m%d')}.json"
        filepath = os.path.join(self.reports_dir, filename)

        try:
            # Convert to dict and handle Enum serialization
            report_dict = asdict(report)
            for page in report_dict.get('pages', []):
                if 'pattern_detected' in page and isinstance(page['pattern_detected'], I18nPattern):
                    page['pattern_detected'] = page['pattern_detected'].value

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report_dict, f, indent=2, ensure_ascii=False, default=str)
            self.logger.info(f"Report saved: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Failed to save report: {e}")
            return ""


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Run i18n guard as standalone CLI."""
    import argparse

    parser = argparse.ArgumentParser(
        description="WSG i18n Consistency Guard v0.2.0",
    )

    parser.add_argument("--audit", type=str, nargs='+', help="Audit specific page(s)")
    parser.add_argument("--coverage", action="store_true", help="Show coverage summary only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    guard = I18nConsistencyGuard(log_level=log_level)

    if args.audit:
        report = guard.audit_all(args.audit)

        print(f"\n📊 i18n Audit Report: {report.report_id}")
        print(f"   Pages audited: {report.pages_audited}")
        print(f"   Total elements: {report.total_elements}")
        print(f"   Complete: {report.complete_count}")
        print(f"   Incomplete: {report.incomplete_count}")

        print(f"\n   Overall Coverage:")
        for lang, cov in report.overall_coverage.items():
            status = "✅" if cov == 100 else "⚠️" if cov >= 90 else "❌"
            print(f"     {status} {lang.upper()}: {cov}%")

        if report.migration_suggestions:
            print(f"\n   Suggestions:")
            for s in report.migration_suggestions[:5]:
                print(f"     • {s}")

    elif args.coverage:
        # Quick coverage check
        print("i18n Coverage Summary (use --audit for full report)")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
