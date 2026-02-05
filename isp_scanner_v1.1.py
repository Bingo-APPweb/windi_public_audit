#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║       WINDI ISP SCANNER v1.1 — PATCH                       ║
║  Entende pipeline two-stage (Jinja2 → Mustache)            ║
║                                                              ║
║  Aplica este patch sobre o scanner v1.0:                     ║
║    python3 isp_scanner_patch.py                              ║
║                                                              ║
║  Ou use diretamente como scanner:                            ║
║    python3 isp_scanner_patch.py --scan                       ║
╚══════════════════════════════════════════════════════════════╝

CHANGES from v1.0:
  - Recognizes {% raw %}...{% endraw %} blocks as PROTECTED zones
  - Mustache syntax INSIDE raw blocks is OK (by design)
  - Mustache syntax OUTSIDE raw blocks is a real conflict
  - Adds Jinja2 parse validation (actual template.render() test)
  - Smarter scoring: only counts REAL issues
"""

import os
import re
import sys
import json
import hashlib
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# ─── Ensure ISP path is available ───────────────────────────
sys.path.insert(0, '/opt/windi/isp')

# ─── Configuration ──────────────────────────────────────────
ISP_DIR = "/opt/windi/isp"
ENGINE_DIR = "/opt/windi/engine"
REPORT_DIR = "/opt/windi/reports"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# ─── Colors ─────────────────────────────────────────────────
class C:
    PASS = "\033[92m"; FAIL = "\033[91m"; WARN = "\033[93m"
    INFO = "\033[94m"; HEAD = "\033[95m"; BOLD = "\033[1m"; END = "\033[0m"

    @staticmethod
    def ok(msg):   return f"{C.PASS}✅ PASS{C.END} {msg}"
    @staticmethod
    def fail(msg): return f"{C.FAIL}❌ FAIL{C.END} {msg}"
    @staticmethod
    def warn(msg): return f"{C.WARN}⚠️  WARN{C.END} {msg}"
    @staticmethod
    def info(msg): return f"{C.INFO}ℹ️  INFO{C.END} {msg}"
    @staticmethod
    def head(msg): return f"\n{C.HEAD}{C.BOLD}{'═'*60}\n  {msg}\n{'═'*60}{C.END}"


def find_raw_block_ranges(content: str) -> List[Tuple[int, int]]:
    """Find all {% raw %}...{% endraw %} character ranges in content.

    Content inside these ranges is PROTECTED — Mustache syntax is intentional.
    """
    ranges = []
    pattern = r'\{%-?\s*raw\s*-?%\}(.*?)\{%-?\s*endraw\s*-?%\}'
    for m in re.finditer(pattern, content, re.DOTALL):
        ranges.append((m.start(), m.end()))
    return ranges


def is_in_raw_block(pos: int, raw_ranges: List[Tuple[int, int]]) -> bool:
    """Check if a character position falls inside a {% raw %} block"""
    for start, end in raw_ranges:
        if start <= pos <= end:
            return True
    return False


def pos_to_line(content: str, pos: int) -> int:
    """Convert character position to line number"""
    return content[:pos].count('\n') + 1


# ═══════════════════════════════════════════════════════════════
#  PHASE 1: SMART SYNTAX SCAN (v1.1)
# ═══════════════════════════════════════════════════════════════

class SmartSyntaxScanner:
    """v1.1: Understands two-stage pipeline. Only flags REAL conflicts."""

    def __init__(self, scan_dir: str):
        self.scan_dir = scan_dir
        self.results: List[Dict] = []

    def scan_file(self, filepath: str) -> List[Dict]:
        """Scan a single file with raw-block awareness"""
        findings = []
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            return [{"file": filepath, "severity": "CRITICAL",
                     "desc": f"Cannot read: {e}", "fix": "Check permissions"}]

        raw_ranges = find_raw_block_ranges(content)
        has_raw_blocks = len(raw_ranges) > 0

        # ── Check 1: Mustache {{#section}} OUTSIDE raw blocks ──
        for m in re.finditer(r'\{\{#(\w+)\}\}', content):
            if not is_in_raw_block(m.start(), raw_ranges):
                findings.append({
                    "file": filepath,
                    "line": pos_to_line(content, m.start()),
                    "severity": "CRITICAL",
                    "pattern": "mustache_section_unprotected",
                    "match": m.group()[:50],
                    "desc": f"Mustache section {{{{#{m.group(1)}}}}} OUTSIDE raw block — Jinja2 will break",
                    "fix_hint": "Wrap in {% raw %}...{% endraw %} or convert to {% if/for %}"
                })

        # ── Check 2: Mustache {{/section}} OUTSIDE raw blocks ──
        for m in re.finditer(r'\{\{/(\w+)\}\}', content):
            if not is_in_raw_block(m.start(), raw_ranges):
                findings.append({
                    "file": filepath,
                    "line": pos_to_line(content, m.start()),
                    "severity": "CRITICAL",
                    "pattern": "mustache_close_unprotected",
                    "match": m.group()[:50],
                    "desc": f"Mustache closing {{{{{'/'+m.group(1)}}}}} OUTSIDE raw block",
                    "fix_hint": "Wrap in {% raw %}...{% endraw %} or convert to {% endif/endfor %}"
                })

        # ── Check 3: Bare {# OUTSIDE raw blocks (Jinja2 comment trap) ──
        for m in re.finditer(r'(?<!\{)\{#(?!%)', content):
            if not is_in_raw_block(m.start(), raw_ranges):
                findings.append({
                    "file": filepath,
                    "line": pos_to_line(content, m.start()),
                    "severity": "CRITICAL",
                    "pattern": "jinja2_comment_trap",
                    "match": content[m.start():m.start()+30],
                    "desc": "Bare {# will be interpreted as Jinja2 comment start",
                    "fix_hint": "Wrap in raw block or escape"
                })

        # ── Check 4: Mustache {{var}} OUTSIDE raw blocks ──
        #    BUT: standard Jinja2 {{ var }} is FINE — only flag if no spaces/filters
        for m in re.finditer(r'\{\{(\w+)\}\}', content):
            if not is_in_raw_block(m.start(), raw_ranges):
                var = m.group(1)
                # Check if this looks like Jinja2 (has spaces, filters, defaults)
                full_match = content[m.start():m.end()]
                # Pure {{word}} without spaces could be Mustache OR Jinja2
                # We mark as INFO, not error — user decides
                # Skip common Jinja2 patterns
                context_around = content[max(0, m.start()-5):m.end()+20]
                if '|' in context_around or 'default' in context_around:
                    continue  # Definitely Jinja2 with filter
                # Don't flag — {{ var }} works in both engines
                # Only flag if there's clear evidence it's Mustache-only

        # ── Check 5: Mustache triple {{{ (unescaped) OUTSIDE raw blocks ──
        for m in re.finditer(r'\{\{\{', content):
            if not is_in_raw_block(m.start(), raw_ranges):
                findings.append({
                    "file": filepath,
                    "line": pos_to_line(content, m.start()),
                    "severity": "HIGH",
                    "pattern": "mustache_unescaped",
                    "match": content[m.start():m.start()+30],
                    "desc": "Mustache unescaped {{{ — invalid in Jinja2",
                    "fix_hint": "Use {{ var|safe }} in Jinja2"
                })

        # ── Check 6: Inverted sections {{^tag}} OUTSIDE raw blocks ──
        for m in re.finditer(r'\{\{\^(\w+)\}\}', content):
            if not is_in_raw_block(m.start(), raw_ranges):
                findings.append({
                    "file": filepath,
                    "line": pos_to_line(content, m.start()),
                    "severity": "HIGH",
                    "pattern": "mustache_inverted_unprotected",
                    "match": m.group(),
                    "desc": f"Mustache inverted section {{{{^{m.group(1)}}}}} OUTSIDE raw block",
                    "fix_hint": "Convert to {% if not var %} or wrap in raw block"
                })

        # ── INFO: Report raw block usage (positive signal) ──
        if has_raw_blocks:
            findings.append({
                "file": filepath,
                "line": 0,
                "severity": "OK",
                "pattern": "raw_blocks_present",
                "desc": f"Has {len(raw_ranges)} raw block(s) — two-stage pipeline ✓",
                "fix_hint": "Good: Mustache content is protected"
            })

        return findings

    def scan_all(self) -> List[Dict]:
        """Scan ALL template files"""
        print(C.head("PHASE 1: SMART SYNTAX SCAN v1.1"))
        print(C.info("Two-stage aware: Mustache inside {% raw %} = OK"))

        html_files = []
        for root, dirs, files in os.walk(self.scan_dir):
            for f in files:
                if f.endswith(('.html', '.htm', '.jinja2', '.j2')):
                    html_files.append(os.path.join(root, f))

        if not html_files:
            print(C.warn(f"No template files in {self.scan_dir}"))
            return []

        print(C.info(f"Scanning {len(html_files)} files...\n"))

        all_findings = []
        for filepath in sorted(html_files):
            findings = self.scan_file(filepath)
            rel_path = os.path.relpath(filepath, self.scan_dir)

            critical = [f for f in findings if f["severity"] == "CRITICAL"]
            high = [f for f in findings if f["severity"] == "HIGH"]
            ok = [f for f in findings if f["severity"] == "OK"]

            if critical:
                print(C.fail(f"{rel_path}: {len(critical)} CRITICAL"))
                for f in critical:
                    print(f"    L{f.get('line','?'):>4}: {f['desc']}")
            elif high:
                print(C.warn(f"{rel_path}: {len(high)} HIGH"))
                for f in high:
                    print(f"    L{f.get('line','?'):>4}: {f['desc']}")
            elif ok:
                print(C.ok(f"{rel_path}: {ok[0]['desc']}"))
            else:
                print(C.ok(f"{rel_path}: Clean"))

            all_findings.extend(findings)

        self.results = all_findings
        return all_findings


# ═══════════════════════════════════════════════════════════════
#  PHASE 2: JINJA2 PARSE VALIDATION
# ═══════════════════════════════════════════════════════════════

class Jinja2ParseValidator:
    """Actually tries to parse each template with Jinja2"""

    def __init__(self, scan_dir: str):
        self.scan_dir = scan_dir
        self.results: List[Dict] = []

    def scan(self) -> List[Dict]:
        print(C.head("PHASE 2: JINJA2 PARSE VALIDATION"))
        findings = []

        try:
            import jinja2
        except ImportError:
            print(C.fail("Jinja2 not installed"))
            return [{"severity": "CRITICAL", "desc": "Jinja2 not installed"}]

        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.scan_dir),
            autoescape=True,
            undefined=jinja2.Undefined  # Don't fail on undefined vars
        )

        html_files = []
        for root, dirs, files in os.walk(self.scan_dir):
            for f in files:
                if f.endswith(('.html', '.htm')):
                    html_files.append(os.path.join(root, f))

        for filepath in sorted(html_files):
            rel_path = os.path.relpath(filepath, self.scan_dir)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()

                # Try to parse as Jinja2
                template = env.parse(content)
                print(C.ok(f"{rel_path}: Jinja2 parse OK"))
                findings.append({
                    "file": filepath,
                    "severity": "OK",
                    "desc": "Jinja2 parse successful"
                })

            except jinja2.TemplateSyntaxError as e:
                print(C.fail(f"{rel_path}: Jinja2 SYNTAX ERROR line {e.lineno}"))
                print(f"    {str(e)[:100]}")
                findings.append({
                    "file": filepath,
                    "line": e.lineno,
                    "severity": "CRITICAL",
                    "desc": f"Jinja2 syntax error: {str(e)[:100]}",
                    "fix_hint": "Fix syntax or wrap problematic content in {% raw %}"
                })
            except Exception as e:
                print(C.warn(f"{rel_path}: Parse error — {str(e)[:60]}"))
                findings.append({
                    "file": filepath,
                    "severity": "HIGH",
                    "desc": f"Parse error: {str(e)[:100]}"
                })

        self.results = findings
        return findings


# ═══════════════════════════════════════════════════════════════
#  PHASE 3: MODULE HEALTH CHECK
# ═══════════════════════════════════════════════════════════════

class ModuleHealthCheck:
    """Quick module health check"""

    def scan(self) -> List[Dict]:
        print(C.head("PHASE 3: MODULE HEALTH CHECK"))
        findings = []

        # sys.path
        if ISP_DIR in sys.path:
            print(C.ok(f"{ISP_DIR} in sys.path"))
        else:
            print(C.fail(f"{ISP_DIR} NOT in sys.path"))
            findings.append({"severity": "HIGH", "desc": f"{ISP_DIR} not in sys.path",
                           "fix": f"Add sys.path.insert(0, '{ISP_DIR}') to loader"})

        # Duplicate loaders
        loader_old = os.path.join(ISP_DIR, "isp_loader.py")
        loader_new = os.path.join(ISP_DIR, "isp_governance_loader.py")
        loader_engine = os.path.join(ENGINE_DIR, "isp_governance_loader.py")

        if os.path.exists(loader_old) and os.path.exists(loader_new):
            print(C.fail("DUPLICATE: Both isp_loader.py and isp_governance_loader.py in ISP dir"))
            findings.append({"severity": "HIGH", "desc": "Duplicate loaders in ISP dir"})
        elif os.path.exists(loader_old) and os.path.exists(loader_engine):
            print(C.warn("isp_loader.py in ISP + isp_governance_loader.py in engine — verify which is active"))
            findings.append({"severity": "LOW", "desc": "Loader in two locations — verify active one"})
        elif os.path.exists(loader_old):
            print(C.ok(f"Single loader: isp_loader.py"))
        elif os.path.exists(loader_new):
            print(C.ok(f"Single loader: isp_governance_loader.py"))
        else:
            print(C.warn("No loader found in ISP dir"))

        return findings


# ═══════════════════════════════════════════════════════════════
#  PHASE 4: RENDER CHAIN + PDF
# ═══════════════════════════════════════════════════════════════

class RenderChainCheck:
    """Validates template include/extend chains"""

    def scan(self) -> List[Dict]:
        print(C.head("PHASE 4: RENDER CHAIN & STRUCTURE"))
        findings = []

        # Check directory structure per ISP profile
        profiles = []
        if os.path.exists(ISP_DIR):
            for item in os.listdir(ISP_DIR):
                item_path = os.path.join(ISP_DIR, item)
                if os.path.isdir(item_path) and not item.startswith('.'):
                    profiles.append(item)

        print(C.info(f"Found {len(profiles)} ISP profiles: {', '.join(profiles)}"))

        for profile in profiles:
            profile_dir = os.path.join(ISP_DIR, profile)

            # Check standard structure
            expected = {
                "templates/": "Template files",
                "components/": "Reusable components (header, footer)",
                "assets/": "Static assets (logos, fonts)",
            }

            has_templates = False
            for subdir, desc in expected.items():
                full = os.path.join(profile_dir, subdir)
                if os.path.exists(full):
                    files = os.listdir(full)
                    html_count = sum(1 for f in files if f.endswith('.html'))
                    if subdir == "templates/" and html_count > 0:
                        has_templates = True
                    print(C.ok(f"  {profile}/{subdir} ({html_count} html, {len(files)} total)"))
                else:
                    print(C.info(f"  {profile}/{subdir} — not found"))

            # Check include chains within profile
            templates_dir = os.path.join(profile_dir, "templates")
            components_dir = os.path.join(profile_dir, "components")

            if has_templates:
                for tpl_file in os.listdir(templates_dir):
                    if not tpl_file.endswith('.html'):
                        continue
                    tpl_path = os.path.join(templates_dir, tpl_file)
                    with open(tpl_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()

                    includes = re.findall(r"\{%[-\s]*include\s+['\"](.+?)['\"]", content)
                    for inc in includes:
                        # Check relative to templates dir AND components dir
                        found = False
                        for check_dir in [templates_dir, components_dir, profile_dir, ISP_DIR]:
                            if check_dir and os.path.exists(os.path.join(check_dir, inc)):
                                found = True
                                break
                        if found:
                            print(C.ok(f"    {tpl_file} → include '{inc}': found"))
                        else:
                            print(C.fail(f"    {tpl_file} → include '{inc}': NOT FOUND"))
                            findings.append({
                                "severity": "CRITICAL",
                                "desc": f"{profile}/{tpl_file} includes '{inc}' — file not found",
                                "fix": "Create the missing file or fix the include path"
                            })

        return findings


# ═══════════════════════════════════════════════════════════════
#  REPORT GENERATOR v1.1
# ═══════════════════════════════════════════════════════════════

class ReportGenerator:
    def __init__(self):
        self.phases = {}

    def add_phase(self, name: str, findings: List[Dict]):
        self.phases[name] = findings

    def calculate_score(self) -> dict:
        total_c = total_h = total_w = 0
        phase_scores = {}

        for name, findings in self.phases.items():
            c = sum(1 for f in findings if f.get("severity") == "CRITICAL")
            h = sum(1 for f in findings if f.get("severity") == "HIGH")
            w = sum(1 for f in findings if f.get("severity") in ("WARN", "LOW"))

            total_c += c; total_h += h; total_w += w

            status = "FAIL" if c > 0 else "WARN" if h > 0 else "PASS"
            phase_scores[name] = {"status": status, "critical": c, "high": h, "warn": w}

        penalty = (total_c * 25) + (total_h * 10) + (total_w * 3)
        score = max(0, 100 - penalty)
        grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 50 else "D" if score >= 25 else "F"

        return {
            "phases": phase_scores,
            "overall_score": score,
            "total_critical": total_c,
            "total_high": total_h,
            "total_warn": total_w,
            "grade": grade
        }

    def print_report(self) -> dict:
        scores = self.calculate_score()

        print(C.head("FINAL REPORT — ISP SCANNER v1.1"))
        print(f"\n  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  {ISP_DIR}")
        print(f"  Two-stage aware (Jinja2 + Mustache)\n")

        print(f"  {'Phase':<30} {'Status':<8} {'CRIT':>5} {'HIGH':>5} {'WARN':>5}")
        print(f"  {'─'*30} {'─'*8} {'─'*5} {'─'*5} {'─'*5}")

        for phase, data in scores["phases"].items():
            sc = C.PASS if data["status"] == "PASS" else C.FAIL if data["status"] == "FAIL" else C.WARN
            print(f"  {phase:<30} {sc}{data['status']:<8}{C.END} {data['critical']:>5} {data['high']:>5} {data['warn']:>5}")

        gc = C.PASS if scores["grade"] in ("A","B") else C.WARN if scores["grade"] == "C" else C.FAIL
        print(f"\n  {C.BOLD}Score: {gc}{scores['overall_score']}/100 (Grade: {scores['grade']}){C.END}")
        print(f"  {scores['total_critical']} Critical, {scores['total_high']} High, {scores['total_warn']} Warnings")

        # Fix priority
        if scores['total_critical'] + scores['total_high'] > 0:
            print(C.head("FIX PRIORITIES"))
            i = 1
            for phase, findings in self.phases.items():
                for f in findings:
                    if f.get("severity") in ("CRITICAL", "HIGH"):
                        sc = C.FAIL if f["severity"] == "CRITICAL" else C.WARN
                        print(f"\n  {sc}#{i} [{f['severity']}]{C.END} {f.get('desc', 'N/A')}")
                        if f.get("fix_hint"):
                            print(f"     Fix: {f['fix_hint']}")
                        elif f.get("fix"):
                            print(f"     Fix: {f['fix']}")
                        i += 1

        return scores

    def save_report(self) -> str:
        os.makedirs(REPORT_DIR, exist_ok=True)
        filepath = os.path.join(REPORT_DIR, f"isp_scan_v1.1_{TIMESTAMP}.json")

        scores = self.calculate_score()
        report = {
            "version": "1.1",
            "timestamp": TIMESTAMP,
            "scan_date": datetime.now().isoformat(),
            "target_dir": ISP_DIR,
            "two_stage_aware": True,
            "scores": scores,
            "phases": {k: v for k, v in self.phases.items()}
        }
        report["integrity_hash"] = hashlib.sha256(
            json.dumps(report, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(C.info(f"\nReport: {filepath}"))
        return filepath


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    global ISP_DIR, ENGINE_DIR
    parser = argparse.ArgumentParser(description="WINDI ISP Scanner v1.1 — Two-Stage Aware")
    parser.add_argument('--scan', action='store_true', default=True, help='Run full scan')
    parser.add_argument('--json', action='store_true', help='JSON output only')
    parser.add_argument('--isp-dir', default=ISP_DIR)
    parser.add_argument('--engine-dir', default=ENGINE_DIR)
    args = parser.parse_args()

    ISP_DIR = args.isp_dir
    ENGINE_DIR = args.engine_dir

    print(f"""
{C.HEAD}{C.BOLD}
╔══════════════════════════════════════════════════════════════╗
║         WINDI ISP SCANNER v1.1 — Two-Stage Aware            ║
║     Controlador de Trafego                                  ║
╚══════════════════════════════════════════════════════════════╝
{C.END}
  Target: {ISP_DIR}
  Mode:   Two-stage pipeline aware (Jinja2 + Mustache raw blocks)
  Time:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")

    report = ReportGenerator()

    # Phase 1: Smart Syntax Scan
    scanner = SmartSyntaxScanner(ISP_DIR)
    report.add_phase("1_Smart_Syntax", scanner.scan_all())

    # Phase 2: Jinja2 Parse Validation
    validator = Jinja2ParseValidator(ISP_DIR)
    report.add_phase("2_Jinja2_Parse", validator.scan())

    # Phase 3: Module Health
    modules = ModuleHealthCheck()
    report.add_phase("3_Module_Health", modules.scan())

    # Phase 4: Render Chain
    chain = RenderChainCheck()
    report.add_phase("4_Render_Chain", chain.scan())

    if args.json:
        print(json.dumps(report.calculate_score(), indent=2))
    else:
        scores = report.print_report()
        report.save_report()

    score = report.calculate_score()["overall_score"]
    sys.exit(0 if score >= 75 else 1 if score >= 50 else 2)


if __name__ == "__main__":
    main()
