#!/usr/bin/env python3
"""
WSG v0.2.0 — Link Integrity Checker
"Observar. Registrar. CURAR. Dissuadir."

Module 2: Scans all served pages and detects dead links.

Constitutional Alignment:
- Flags dead links for HUMAN review (I9 safe)
- Does not autonomously delete content
- Advisory only — human decides removal/redirect

Author: WINDI Publishing House
Version: 0.2.0
Date: 10 Feb 2026
"""

import os
import re
import json
import time
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from urllib.parse import urljoin, urlparse
import urllib.request
import urllib.error
from html.parser import HTMLParser


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

WSG_PAGES_TO_SCAN: List[str] = [
    "https://master.windia4desk.tech/",
    "https://master.windia4desk.tech/protocol.html",
    "https://master.windia4desk.tech/docs/",
    "https://admin.windia4desk.tech/",
    "https://clone.windia4desk.tech/",
    # Local development
    "http://localhost:8085/",
    "http://localhost:8080/",
]

# Links matching these patterns are ignored
IGNORE_PATTERNS: List[str] = [
    r"^mailto:",
    r"^tel:",
    r"^javascript:",
    r"^#",
    r"^data:",
    r"\.pdf$",  # PDFs are validated separately
]


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

class LinkStatus(Enum):
    """Status of a checked link."""
    OK = "ok"
    BROKEN = "broken"
    REDIRECT = "redirect"
    TIMEOUT = "timeout"
    IGNORED = "ignored"
    EXTERNAL_BROKEN = "external_broken"


@dataclass
class LinkCheckResult:
    """Result of checking a single link."""
    url: str
    status: LinkStatus
    http_code: Optional[int] = None
    redirect_url: Optional[str] = None
    source_page: str = ""
    element_type: str = ""  # 'href', 'src', 'action'
    is_internal: bool = True
    error: Optional[str] = None
    response_time_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class LinkIntegrityReport:
    """Complete report of link integrity scan."""
    report_id: str
    scan_date: str
    pages_scanned: int
    total_links: int
    ok_count: int
    broken_count: int
    external_broken_count: int
    redirect_count: int
    timeout_count: int
    ignored_count: int
    broken_links: List[Dict[str, Any]]
    external_broken_links: List[Dict[str, Any]]
    scan_duration_seconds: float
    hash: str = ""

    def __post_init__(self):
        if not self.hash:
            content = f"{self.report_id}|{self.scan_date}|{self.total_links}|{self.broken_count}"
            self.hash = f"sha256:{hashlib.sha256(content.encode()).hexdigest()[:16]}"


# ═══════════════════════════════════════════════════════════════════════════════
# HTML LINK EXTRACTOR
# ═══════════════════════════════════════════════════════════════════════════════

class LinkExtractor(HTMLParser):
    """Extract all links (href, src) from HTML."""

    def __init__(self):
        super().__init__()
        self.links: List[Tuple[str, str]] = []  # (url, element_type)

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        attrs_dict = dict(attrs)

        # Extract href from <a>, <link>, <area>
        if tag in ("a", "link", "area") and "href" in attrs_dict:
            href = attrs_dict["href"]
            if href:
                self.links.append((href, "href"))

        # Extract src from <img>, <script>, <iframe>, <video>, <audio>, <source>
        if tag in ("img", "script", "iframe", "video", "audio", "source") and "src" in attrs_dict:
            src = attrs_dict["src"]
            if src:
                self.links.append((src, "src"))

        # Extract action from <form>
        if tag == "form" and "action" in attrs_dict:
            action = attrs_dict["action"]
            if action:
                self.links.append((action, "action"))

        # Extract srcset from <img>, <source>
        if tag in ("img", "source") and "srcset" in attrs_dict:
            srcset = attrs_dict["srcset"]
            if srcset:
                # Parse srcset: "url1 1x, url2 2x"
                for part in srcset.split(","):
                    url = part.strip().split()[0]
                    if url:
                        self.links.append((url, "srcset"))


def extract_links_from_html(html: str) -> List[Tuple[str, str]]:
    """
    Extract all links from HTML content.

    Args:
        html: HTML content string

    Returns:
        List of (url, element_type) tuples
    """
    parser = LinkExtractor()
    try:
        parser.feed(html)
    except Exception:
        pass
    return parser.links


# ═══════════════════════════════════════════════════════════════════════════════
# LINK INTEGRITY CHECKER
# ═══════════════════════════════════════════════════════════════════════════════

class LinkIntegrityChecker:
    """
    WSG Link Integrity Checker — Detect and report dead links.

    Cycle:
    1. Daily scan (or on-deploy)
    2. Extract all href and src from each page
    3. Verify each link (HEAD request)
    4. If 404/502:
       a) Internal link → FLAG for removal + generate Receipt
       b) External link → FLAG as "external_broken"
    5. Report in /opt/windi/guard/reports/link_integrity_YYYYMMDD.json

    Auto-repair options (advisory only — human decides):
    - Remove <a> with dead href from served HTML (via nginx sub_filter)
    - Or redirect to /404-governance.html with explanation
    """

    def __init__(
        self,
        pages: Optional[List[str]] = None,
        reports_dir: str = "/opt/windi/guard/reports",
        timeout: int = 10,
        ignore_patterns: Optional[List[str]] = None,
        log_level: int = logging.INFO,
    ):
        self.pages = pages or WSG_PAGES_TO_SCAN
        self.reports_dir = reports_dir
        self.timeout = timeout
        self.ignore_patterns = [re.compile(p) for p in (ignore_patterns or IGNORE_PATTERNS)]
        self.checked_urls: Set[str] = set()
        self.results: List[LinkCheckResult] = []

        # Setup logging
        self.logger = logging.getLogger("WSG.LinkChecker")
        self.logger.setLevel(log_level)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                "[%(asctime)s] WSG-LINK %(levelname)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))
            self.logger.addHandler(handler)

        os.makedirs(self.reports_dir, exist_ok=True)

    def _should_ignore(self, url: str) -> bool:
        """Check if URL should be ignored."""
        for pattern in self.ignore_patterns:
            if pattern.search(url):
                return True
        return False

    def _is_internal(self, url: str, base_url: str) -> bool:
        """Check if URL is internal (same domain)."""
        parsed_url = urlparse(url)
        parsed_base = urlparse(base_url)

        # Relative URLs are internal
        if not parsed_url.netloc:
            return True

        # Check domain match
        return parsed_url.netloc == parsed_base.netloc

    def _normalize_url(self, url: str, base_url: str) -> str:
        """Normalize URL to absolute form."""
        return urljoin(base_url, url)

    def check_link(self, url: str, source_page: str, element_type: str) -> LinkCheckResult:
        """
        Check if a link is valid.

        Args:
            url: URL to check
            source_page: Page where link was found
            element_type: Type of element (href, src, action)

        Returns:
            LinkCheckResult with status
        """
        # Normalize URL
        full_url = self._normalize_url(url, source_page)

        # Check if should ignore
        if self._should_ignore(url):
            return LinkCheckResult(
                url=full_url,
                status=LinkStatus.IGNORED,
                source_page=source_page,
                element_type=element_type,
            )

        # Check if already checked
        if full_url in self.checked_urls:
            return LinkCheckResult(
                url=full_url,
                status=LinkStatus.OK,  # Assume OK if already checked
                source_page=source_page,
                element_type=element_type,
            )

        self.checked_urls.add(full_url)
        is_internal = self._is_internal(full_url, source_page)

        start_time = time.time()

        try:
            # Use HEAD request to minimize bandwidth
            req = urllib.request.Request(full_url, method="HEAD")
            req.add_header("User-Agent", "WSG-LinkChecker/0.2.0")

            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                response_time = (time.time() - start_time) * 1000
                http_code = response.status

                # Check for redirects
                if response.url != full_url:
                    return LinkCheckResult(
                        url=full_url,
                        status=LinkStatus.REDIRECT,
                        http_code=http_code,
                        redirect_url=response.url,
                        source_page=source_page,
                        element_type=element_type,
                        is_internal=is_internal,
                        response_time_ms=round(response_time, 2),
                    )

                return LinkCheckResult(
                    url=full_url,
                    status=LinkStatus.OK,
                    http_code=http_code,
                    source_page=source_page,
                    element_type=element_type,
                    is_internal=is_internal,
                    response_time_ms=round(response_time, 2),
                )

        except urllib.error.HTTPError as e:
            response_time = (time.time() - start_time) * 1000
            status = LinkStatus.BROKEN if is_internal else LinkStatus.EXTERNAL_BROKEN

            return LinkCheckResult(
                url=full_url,
                status=status,
                http_code=e.code,
                source_page=source_page,
                element_type=element_type,
                is_internal=is_internal,
                error=f"HTTP {e.code}: {e.reason}",
                response_time_ms=round(response_time, 2),
            )

        except urllib.error.URLError as e:
            response_time = (time.time() - start_time) * 1000
            status = LinkStatus.BROKEN if is_internal else LinkStatus.EXTERNAL_BROKEN

            return LinkCheckResult(
                url=full_url,
                status=status,
                source_page=source_page,
                element_type=element_type,
                is_internal=is_internal,
                error=str(e.reason),
                response_time_ms=round(response_time, 2),
            )

        except TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return LinkCheckResult(
                url=full_url,
                status=LinkStatus.TIMEOUT,
                source_page=source_page,
                element_type=element_type,
                is_internal=is_internal,
                error="Request timed out",
                response_time_ms=round(response_time, 2),
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return LinkCheckResult(
                url=full_url,
                status=LinkStatus.BROKEN if is_internal else LinkStatus.EXTERNAL_BROKEN,
                source_page=source_page,
                element_type=element_type,
                is_internal=is_internal,
                error=str(e),
                response_time_ms=round(response_time, 2),
            )

    def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch HTML content of a page.

        Args:
            url: Page URL to fetch

        Returns:
            HTML content or None if fetch failed
        """
        try:
            req = urllib.request.Request(url, method="GET")
            req.add_header("User-Agent", "WSG-LinkChecker/0.2.0")

            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                return response.read().decode("utf-8", errors="ignore")

        except Exception as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            return None

    def scan_page(self, page_url: str) -> List[LinkCheckResult]:
        """
        Scan a single page for broken links.

        Args:
            page_url: URL of page to scan

        Returns:
            List of link check results
        """
        self.logger.info(f"Scanning: {page_url}")

        html = self.fetch_page(page_url)
        if not html:
            return []

        links = extract_links_from_html(html)
        results = []

        for url, element_type in links:
            result = self.check_link(url, page_url, element_type)
            results.append(result)

            # Log broken links
            if result.status in (LinkStatus.BROKEN, LinkStatus.EXTERNAL_BROKEN):
                icon = "🔴" if result.is_internal else "🟠"
                self.logger.warning(f"{icon} Broken: {result.url} (from {page_url})")

        return results

    def scan_all(self) -> LinkIntegrityReport:
        """
        Scan all configured pages for broken links.

        Returns:
            LinkIntegrityReport with full scan results
        """
        start_time = time.time()
        self.checked_urls.clear()
        self.results.clear()

        pages_scanned = 0

        for page_url in self.pages:
            page_results = self.scan_page(page_url)
            self.results.extend(page_results)
            pages_scanned += 1

        # Compile report
        scan_duration = time.time() - start_time

        broken_links = [asdict(r) for r in self.results if r.status == LinkStatus.BROKEN]
        external_broken = [asdict(r) for r in self.results if r.status == LinkStatus.EXTERNAL_BROKEN]

        report = LinkIntegrityReport(
            report_id=f"WSG-LINK-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            scan_date=datetime.now(timezone.utc).isoformat(),
            pages_scanned=pages_scanned,
            total_links=len(self.results),
            ok_count=sum(1 for r in self.results if r.status == LinkStatus.OK),
            broken_count=len(broken_links),
            external_broken_count=len(external_broken),
            redirect_count=sum(1 for r in self.results if r.status == LinkStatus.REDIRECT),
            timeout_count=sum(1 for r in self.results if r.status == LinkStatus.TIMEOUT),
            ignored_count=sum(1 for r in self.results if r.status == LinkStatus.IGNORED),
            broken_links=broken_links,
            external_broken_links=external_broken,
            scan_duration_seconds=round(scan_duration, 2),
        )

        # Save report
        self._save_report(report)

        # Log summary
        self.logger.info(
            f"Scan complete: {report.total_links} links checked, "
            f"{report.broken_count} broken, {report.external_broken_count} external broken "
            f"({scan_duration:.1f}s)"
        )

        return report

    def _save_report(self, report: LinkIntegrityReport) -> str:
        """Save report to reports directory."""
        filename = f"link_integrity_{datetime.now().strftime('%Y%m%d')}.json"
        filepath = os.path.join(self.reports_dir, filename)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(asdict(report), f, indent=2, ensure_ascii=False)
            self.logger.info(f"Report saved: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Failed to save report: {e}")
            return ""

    def get_repair_suggestions(self) -> List[Dict[str, Any]]:
        """
        Generate repair suggestions for broken links.

        Returns:
            List of repair suggestions (advisory only — human decides)
        """
        suggestions = []

        for result in self.results:
            if result.status == LinkStatus.BROKEN:
                suggestions.append({
                    "url": result.url,
                    "source_page": result.source_page,
                    "element_type": result.element_type,
                    "suggestion": "remove_or_redirect",
                    "actions": [
                        f"Remove link from {result.source_page}",
                        "Redirect to /404-governance.html",
                        "Update link to valid destination",
                    ],
                    "requires": "human_approval",
                })

        return suggestions


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Run link checker as standalone CLI."""
    import argparse

    parser = argparse.ArgumentParser(
        description="WSG Link Integrity Checker v0.2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--scan-all", action="store_true", help="Scan all configured pages")
    parser.add_argument("--scan", type=str, help="Scan specific page URL")
    parser.add_argument("--check", type=str, help="Check specific link URL")
    parser.add_argument("--suggestions", action="store_true", help="Show repair suggestions")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    checker = LinkIntegrityChecker(log_level=log_level)

    if args.scan_all:
        report = checker.scan_all()
        print(f"\n📊 Scan Report: {report.report_id}")
        print(f"   Pages scanned: {report.pages_scanned}")
        print(f"   Total links: {report.total_links}")
        print(f"   ✅ OK: {report.ok_count}")
        print(f"   🔴 Broken: {report.broken_count}")
        print(f"   🟠 External broken: {report.external_broken_count}")
        print(f"   ⏱️ Duration: {report.scan_duration_seconds}s")

        if report.broken_links:
            print("\n🔴 Broken Links:")
            for link in report.broken_links[:10]:
                print(f"   • {link['url']}")
                print(f"     └─ from: {link['source_page']}")

    elif args.scan:
        results = checker.scan_page(args.scan)
        broken = [r for r in results if r.status in (LinkStatus.BROKEN, LinkStatus.EXTERNAL_BROKEN)]
        print(f"Checked {len(results)} links, {len(broken)} broken")

    elif args.check:
        result = checker.check_link(args.check, "manual", "manual")
        status_icon = "✅" if result.status == LinkStatus.OK else "❌"
        print(f"{status_icon} {result.url}: {result.status.value}")
        if result.error:
            print(f"   └─ {result.error}")

    elif args.suggestions:
        checker.scan_all()
        suggestions = checker.get_repair_suggestions()
        print(f"\n🔧 Repair Suggestions ({len(suggestions)} items):")
        for s in suggestions[:10]:
            print(f"\n   URL: {s['url']}")
            print(f"   From: {s['source_page']}")
            print(f"   Actions:")
            for action in s['actions']:
                print(f"     • {action}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
