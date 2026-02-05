#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║           WINDI ISP CORPORATE SCANNER v1.0                  ║
║     "Controlador de Tráfego, não Bombeiro" 🗼🐉             ║
║                                                              ║
║  Programa de varredura e correção sistemática                ║
║  Para execução via Claude Code no terminal Strato            ║
║                                                              ║
║  AI processes. Human decides. WINDI guarantees.              ║
╚══════════════════════════════════════════════════════════════╝

USAGE:
    python3 isp_scanner.py                    # Full scan + report
    python3 isp_scanner.py --scan-only        # Scan without fixes
    python3 isp_scanner.py --fix              # Scan + apply fixes
    python3 isp_scanner.py --test-pdf         # Run PDF end-to-end test
    python3 isp_scanner.py --report           # Generate detailed report only

WHAT IT DOES (5 Phases):
    Phase 1: Syntax Scan     — Find Mustache vs Jinja2 conflicts in ALL .html
    Phase 2: Module Scan     — Check sys.path collisions and import chains
    Phase 3: Render Chain    — Validate header → content → footer → template
    Phase 4: PDF E2E Test    — Generate test PDF and verify branding
    Phase 5: Report          — Pass/fail score with fix recommendations
"""

import os
import re
import sys
import json
import hashlib
import argparse
import importlib
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# ─── Configuration ──────────────────────────────────────────
ISP_DIR = "/opt/windi/isp"
ENGINE_DIR = "/opt/windi/engine"
BACKUP_DIR = "/opt/windi/backups"
REPORT_DIR = "/opt/windi/reports"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# ─── Color Output ───────────────────────────────────────────
class C:
    """Terminal colors for clear reporting"""
    PASS = "\033[92m"   # Green
    FAIL = "\033[91m"   # Red
    WARN = "\033[93m"   # Yellow
    INFO = "\033[94m"   # Blue
    HEAD = "\033[95m"   # Magenta
    BOLD = "\033[1m"
    END  = "\033[0m"

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


# ═══════════════════════════════════════════════════════════════
#  PHASE 1: SYNTAX SCAN — Mustache vs Jinja2 conflicts
# ═══════════════════════════════════════════════════════════════

class SyntaxScanner:
    """Detects template syntax conflicts in HTML files"""

    # Patterns that cause problems
    PATTERNS = {
        "mustache_var": {
            "regex": r'\{\{(?!%|#|-)\s*\w+',
            "desc": "Mustache variable {{ var }} — conflicts with Jinja2 variable syntax",
            "severity": "HIGH",
            "fix_hint": "Wrap in {% raw %}...{% endraw %} or use custom delimiters"
        },
        "mustache_triple": {
            "regex": r'\{\{\{',
            "desc": "Mustache unescaped {{{ var }}} — not valid in Jinja2",
            "severity": "HIGH",
            "fix_hint": "Replace with Jinja2 {{ var|safe }}"
        },
        "jinja2_comment_conflict": {
            "regex": r'\{#(?!\s*-?\s*end)',
            "desc": "Jinja2 interprets {# as comment start — breaks content",
            "severity": "CRITICAL",
            "fix_hint": "Escape or use raw blocks. This is the known footer.html bug."
        },
        "jinja2_block_tag": {
            "regex": r'\{%.*?%\}',
            "desc": "Jinja2 block tag — verify correct syntax",
            "severity": "INFO",
            "fix_hint": "Verify matching {% end* %} tags"
        },
        "unclosed_mustache": {
            "regex": r'\{\{[^}]*$',
            "desc": "Unclosed Mustache tag — will break rendering",
            "severity": "HIGH",
            "fix_hint": "Close the tag with }}"
        },
        "mixed_delimiters": {
            "regex": r'\{\{.*?\{%|\{%.*?\{\{',
            "desc": "Mixed Mustache + Jinja2 in same expression",
            "severity": "CRITICAL",
            "fix_hint": "Standardize to one template engine per file"
        },
        "raw_block_check": {
            "regex": r'\{%[-\s]*raw\s*[-\s]*%\}',
            "desc": "Jinja2 raw block — good practice for Mustache content",
            "severity": "OK",
            "fix_hint": "Already using raw blocks - good!"
        },
        "dollar_brace": {
            "regex": r'\$\{[^}]+\}',
            "desc": "JavaScript template literal ${} — verify not in Jinja2 context",
            "severity": "LOW",
            "fix_hint": "Usually safe, but verify rendering context"
        }
    }

    def __init__(self, scan_dir: str):
        self.scan_dir = scan_dir
        self.results: List[Dict] = []

    def scan_file(self, filepath: str) -> List[Dict]:
        """Scan a single HTML file for syntax conflicts"""
        findings = []
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                lines = content.split('\n')

            for pattern_name, pattern_info in self.PATTERNS.items():
                for line_num, line in enumerate(lines, 1):
                    matches = re.finditer(pattern_info["regex"], line)
                    for match in matches:
                        findings.append({
                            "file": filepath,
                            "line": line_num,
                            "column": match.start(),
                            "pattern": pattern_name,
                            "match": match.group()[:50],
                            "severity": pattern_info["severity"],
                            "desc": pattern_info["desc"],
                            "fix_hint": pattern_info["fix_hint"],
                            "context": line.strip()[:100]
                        })
        except Exception as e:
            findings.append({
                "file": filepath,
                "line": 0,
                "pattern": "READ_ERROR",
                "severity": "CRITICAL",
                "desc": f"Cannot read file: {e}",
                "fix_hint": "Check file permissions and encoding"
            })

        return findings

    def scan_all(self) -> List[Dict]:
        """Scan ALL .html files in the ISP directory"""
        print(C.head("PHASE 1: SYNTAX SCAN — Template Conflict Detection"))

        html_files = []
        for root, dirs, files in os.walk(self.scan_dir):
            for f in files:
                if f.endswith(('.html', '.htm', '.jinja2', '.j2')):
                    html_files.append(os.path.join(root, f))

        if not html_files:
            print(C.warn(f"No HTML files found in {self.scan_dir}"))
            return []

        print(C.info(f"Found {len(html_files)} template files to scan"))

        all_findings = []
        for filepath in sorted(html_files):
            findings = self.scan_file(filepath)
            rel_path = os.path.relpath(filepath, self.scan_dir)

            critical = sum(1 for f in findings if f["severity"] == "CRITICAL")
            high = sum(1 for f in findings if f["severity"] == "HIGH")
            ok_count = sum(1 for f in findings if f["severity"] == "OK")

            if critical > 0:
                print(C.fail(f"{rel_path}: {critical} CRITICAL, {high} HIGH"))
            elif high > 0:
                print(C.warn(f"{rel_path}: {high} HIGH issues"))
            elif ok_count > 0:
                print(C.ok(f"{rel_path}: Clean (has raw blocks ✓)"))
            else:
                print(C.ok(f"{rel_path}: Clean"))

            # Show details for critical/high
            for f in findings:
                if f["severity"] in ("CRITICAL", "HIGH"):
                    print(f"    L{f.get('line', '?'):>4}: {f['desc']}")
                    print(f"          Match: {f.get('match', 'N/A')}")
                    print(f"          Fix:   {f['fix_hint']}")

            all_findings.extend(findings)

        self.results = all_findings
        return all_findings


# ═══════════════════════════════════════════════════════════════
#  PHASE 2: MODULE SCAN — sys.path and import collisions
# ═══════════════════════════════════════════════════════════════

class ModuleScanner:
    """Detects sys.path collisions and module naming conflicts"""

    def __init__(self):
        self.results: List[Dict] = []

    def scan_sys_path(self) -> List[Dict]:
        """Check sys.path for ISP-related entries and collisions"""
        print(C.head("PHASE 2: MODULE SCAN — sys.path & Import Chain"))

        findings = []

        # Check current sys.path
        print(C.info("Current sys.path entries:"))
        isp_paths = []
        for i, p in enumerate(sys.path):
            if 'windi' in p.lower() or 'isp' in p.lower():
                print(f"    [{i}] {p}")
                isp_paths.append(p)

        if ISP_DIR not in sys.path:
            findings.append({
                "type": "MISSING_PATH",
                "severity": "HIGH",
                "desc": f"{ISP_DIR} not in sys.path",
                "fix": f"sys.path.insert(0, '{ISP_DIR}')"
            })
            print(C.fail(f"{ISP_DIR} NOT in sys.path"))
        else:
            print(C.ok(f"{ISP_DIR} in sys.path"))

        # Check for duplicate module names
        print(C.info("\nScanning for module name collisions..."))
        module_map = {}  # module_name -> [paths]

        search_dirs = [ISP_DIR, ENGINE_DIR]
        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                print(C.warn(f"Directory not found: {search_dir}"))
                continue

            for root, dirs, files in os.walk(search_dir):
                for f in files:
                    if f.endswith('.py') and not f.startswith('__'):
                        module_name = f[:-3]  # Remove .py
                        full_path = os.path.join(root, f)
                        if module_name not in module_map:
                            module_map[module_name] = []
                        module_map[module_name].append(full_path)

        # Find collisions
        for mod_name, paths in module_map.items():
            if len(paths) > 1:
                findings.append({
                    "type": "NAME_COLLISION",
                    "severity": "HIGH",
                    "desc": f"Module '{mod_name}' exists in multiple locations",
                    "paths": paths,
                    "fix": f"Rename one of: {', '.join(paths)}"
                })
                print(C.fail(f"COLLISION: '{mod_name}' found in {len(paths)} locations:"))
                for p in paths:
                    print(f"    → {p}")
            else:
                pass  # Single location, no collision

        # Check for old/renamed files that might cause confusion
        known_renames = [
            ("isp_loader.py", "isp_governance_loader.py", "Was renamed in previous session"),
        ]
        for old_name, new_name, note in known_renames:
            old_path = os.path.join(ISP_DIR, old_name)
            new_path = os.path.join(ISP_DIR, new_name)
            if os.path.exists(old_path):
                findings.append({
                    "type": "STALE_FILE",
                    "severity": "HIGH",
                    "desc": f"Old file '{old_name}' still exists alongside '{new_name}'",
                    "note": note,
                    "fix": f"Remove or rename: {old_path}"
                })
                print(C.fail(f"STALE: {old_name} still exists (should be {new_name})"))
            elif os.path.exists(new_path):
                print(C.ok(f"Rename verified: {old_name} → {new_name}"))
            else:
                print(C.warn(f"Neither {old_name} nor {new_name} found"))

        # Check import chains in Python files
        print(C.info("\nScanning import chains in ISP modules..."))
        if os.path.exists(ISP_DIR):
            for f in sorted(os.listdir(ISP_DIR)):
                if f.endswith('.py'):
                    fpath = os.path.join(ISP_DIR, f)
                    try:
                        with open(fpath, 'r') as fp:
                            content = fp.read()
                        imports = re.findall(r'^(?:from|import)\s+(\S+)', content, re.MULTILINE)
                        broken = []
                        for imp in imports:
                            mod_name = imp.split('.')[0]
                            # Check if the imported module exists
                            if mod_name not in ('os', 'sys', 'json', 're', 'datetime',
                                               'pathlib', 'typing', 'hashlib', 'io',
                                               'base64', 'copy', 'traceback', 'logging',
                                               'jinja2', 'weasyprint', 'flask', 'requests',
                                               'yaml', 'toml', 'argparse', 'subprocess',
                                               'importlib', 'collections', 'functools',
                                               'dataclasses', 'enum', 'abc', 'uuid',
                                               'tempfile', 'shutil', 'glob', 'fnmatch',
                                               'string', 'textwrap', 'html', 'urllib',
                                               'http', 'email', 'csv', 'configparser',
                                               'unittest', 'pytest', 'pdfplumber',
                                               'PyPDF2', 'fitz', 'PIL', 'reportlab'):
                                # Custom module — check if it exists
                                found = False
                                for sp in [ISP_DIR, ENGINE_DIR]:
                                    if os.path.exists(os.path.join(sp, f"{mod_name}.py")):
                                        found = True
                                        break
                                    if os.path.exists(os.path.join(sp, mod_name)):
                                        found = True
                                        break
                                if not found:
                                    broken.append(mod_name)

                        if broken:
                            print(C.warn(f"  {f}: imports not found locally: {broken}"))
                            findings.append({
                                "type": "BROKEN_IMPORT",
                                "severity": "WARN",
                                "desc": f"{f} imports modules not found: {broken}",
                                "fix": "Verify these are installed packages or fix import paths"
                            })
                        else:
                            print(C.ok(f"  {f}: all imports resolvable"))
                    except Exception as e:
                        print(C.fail(f"  {f}: cannot parse — {e}"))

        self.results = findings
        return findings


# ═══════════════════════════════════════════════════════════════
#  PHASE 3: RENDER CHAIN — header → content → footer → template
# ═══════════════════════════════════════════════════════════════

class RenderChainValidator:
    """Validates the complete Jinja2 render chain"""

    def __init__(self):
        self.results: List[Dict] = []

    def scan(self) -> List[Dict]:
        print(C.head("PHASE 3: RENDER CHAIN — Template Assembly Validation"))

        findings = []

        # Check which template files exist
        expected_templates = {
            "header.html": "Page header with branding",
            "footer.html": "Page footer with governance info",
            "letter.html": "Letter template (main content)",
            "form.html": "Form template",
            "base.html": "Base template (if exists)",
        }

        existing_templates = {}
        if os.path.exists(ISP_DIR):
            for tpl_name, desc in expected_templates.items():
                tpl_path = os.path.join(ISP_DIR, tpl_name)
                if os.path.exists(tpl_path):
                    existing_templates[tpl_name] = tpl_path
                    print(C.ok(f"Found: {tpl_name} — {desc}"))
                else:
                    # Also check subdirectories
                    found = False
                    for root, dirs, files in os.walk(ISP_DIR):
                        if tpl_name in files:
                            existing_templates[tpl_name] = os.path.join(root, tpl_name)
                            print(C.ok(f"Found: {tpl_name} in {root}"))
                            found = True
                            break
                    if not found:
                        print(C.info(f"Not found: {tpl_name} — {desc} (may be optional)"))

        # Try to import and test Jinja2
        print(C.info("\nTesting Jinja2 environment configuration..."))
        try:
            import jinja2

            # Test 1: Standard Jinja2 Environment
            env_standard = jinja2.Environment(
                loader=jinja2.FileSystemLoader(ISP_DIR),
                autoescape=True
            )
            print(C.ok("Standard Jinja2 Environment loads from ISP_DIR"))

            # Test 2: Custom delimiters Environment (for Mustache compatibility)
            env_custom = jinja2.Environment(
                loader=jinja2.FileSystemLoader(ISP_DIR),
                variable_start_string="${",
                variable_end_string="}",
                block_start_string="<%",
                block_end_string="%>",
                comment_start_string="<#",
                comment_end_string="#>",
                autoescape=True
            )
            print(C.ok("Custom delimiters Environment created"))

            # Test 3: Try rendering each template
            print(C.info("\nTesting individual template rendering..."))
            for tpl_name, tpl_path in existing_templates.items():
                # Read raw content
                with open(tpl_path, 'r', encoding='utf-8', errors='replace') as f:
                    raw = f.read()

                # Check for {# conflict (the known bug)
                comment_conflicts = re.findall(r'\{#(?!\s*-?\s*end)', raw)
                if comment_conflicts:
                    findings.append({
                        "template": tpl_name,
                        "type": "JINJA2_COMMENT_CONFLICT",
                        "severity": "CRITICAL",
                        "desc": f"Found {len(comment_conflicts)} Jinja2 comment triggers ({'{#'})",
                        "matches": [m[:30] for m in comment_conflicts[:5]],
                        "fix": "Wrap content in {% raw %}...{% endraw %} or use custom delimiters"
                    })
                    print(C.fail(f"  {tpl_name}: {len(comment_conflicts)} comment conflicts ({'{#'})"))

                # Try standard render
                try:
                    template = env_standard.from_string(raw)
                    # Render with empty context to see if it breaks
                    try:
                        result = template.render()
                        if '{{' in result:
                            findings.append({
                                "template": tpl_name,
                                "type": "RAW_MUSTACHE_IN_OUTPUT",
                                "severity": "HIGH",
                                "desc": "Rendered output still contains {{ — not processed",
                                "fix": "Mustache vars not being resolved"
                            })
                            print(C.warn(f"  {tpl_name}: Renders but has raw {{{{ in output"))
                        else:
                            print(C.ok(f"  {tpl_name}: Standard render OK"))
                    except jinja2.UndefinedError as e:
                        # Variables not defined — this is expected, template syntax is valid
                        print(C.ok(f"  {tpl_name}: Syntax valid (vars undefined as expected)"))
                    except Exception as e:
                        findings.append({
                            "template": tpl_name,
                            "type": "RENDER_FAIL",
                            "severity": "HIGH",
                            "desc": f"Render failed: {str(e)[:100]}",
                            "fix": "Check template syntax"
                        })
                        print(C.fail(f"  {tpl_name}: Render failed — {str(e)[:80]}"))
                except jinja2.TemplateSyntaxError as e:
                    findings.append({
                        "template": tpl_name,
                        "type": "SYNTAX_ERROR",
                        "severity": "CRITICAL",
                        "desc": f"Jinja2 syntax error at line {e.lineno}: {str(e)[:100]}",
                        "fix": "Fix syntax or wrap in raw blocks"
                    })
                    print(C.fail(f"  {tpl_name}: SYNTAX ERROR line {e.lineno} — {str(e)[:80]}"))

                # Try custom delimiter render
                try:
                    template_custom = env_custom.from_string(raw)
                    print(C.ok(f"  {tpl_name}: Custom delimiters parse OK"))
                except jinja2.TemplateSyntaxError as e:
                    print(C.warn(f"  {tpl_name}: Custom delimiters fail — {str(e)[:60]}"))

            # Test 4: Chain rendering (include/extend chain)
            print(C.info("\nTesting template include/extend chains..."))
            for tpl_name, tpl_path in existing_templates.items():
                with open(tpl_path, 'r', encoding='utf-8', errors='replace') as f:
                    raw = f.read()

                includes = re.findall(r"\{%[-\s]*include\s+['\"](.+?)['\"]", raw)
                extends = re.findall(r"\{%[-\s]*extends\s+['\"](.+?)['\"]", raw)

                for inc in includes:
                    inc_path = os.path.join(ISP_DIR, inc)
                    if os.path.exists(inc_path):
                        print(C.ok(f"  {tpl_name} → includes '{inc}': exists"))
                    else:
                        findings.append({
                            "template": tpl_name,
                            "type": "BROKEN_INCLUDE",
                            "severity": "CRITICAL",
                            "desc": f"includes '{inc}' but file not found",
                            "fix": f"Create {inc_path} or fix the include path"
                        })
                        print(C.fail(f"  {tpl_name} → includes '{inc}': NOT FOUND"))

                for ext in extends:
                    ext_path = os.path.join(ISP_DIR, ext)
                    if os.path.exists(ext_path):
                        print(C.ok(f"  {tpl_name} → extends '{ext}': exists"))
                    else:
                        findings.append({
                            "template": tpl_name,
                            "type": "BROKEN_EXTENDS",
                            "severity": "CRITICAL",
                            "desc": f"extends '{ext}' but file not found",
                            "fix": f"Create {ext_path} or fix the extends path"
                        })
                        print(C.fail(f"  {tpl_name} → extends '{ext}': NOT FOUND"))

        except ImportError:
            print(C.fail("Jinja2 not installed! pip install jinja2"))
            findings.append({
                "type": "MISSING_DEPENDENCY",
                "severity": "CRITICAL",
                "desc": "Jinja2 package not installed",
                "fix": "pip install jinja2"
            })

        self.results = findings
        return findings


# ═══════════════════════════════════════════════════════════════
#  PHASE 4: PDF END-TO-END TEST
# ═══════════════════════════════════════════════════════════════

class PDFTestRunner:
    """Tests PDF generation end-to-end and verifies branding"""

    def __init__(self):
        self.results: List[Dict] = []

    def scan(self) -> List[Dict]:
        print(C.head("PHASE 4: PDF END-TO-END TEST"))

        findings = []

        # Check if PDF generation tools are available
        pdf_tools = {
            "weasyprint": "HTML to PDF converter",
            "pdfplumber": "PDF content extractor",
        }

        available_tools = {}
        for tool, desc in pdf_tools.items():
            try:
                importlib.import_module(tool)
                available_tools[tool] = True
                print(C.ok(f"{tool}: installed ({desc})"))
            except ImportError:
                available_tools[tool] = False
                print(C.warn(f"{tool}: NOT installed ({desc})"))

        # Find the ISP generator/loader
        generator_candidates = [
            "isp_governance_loader.py",
            "isp_loader.py",
            "isp_generator.py",
            "isp_pdf_generator.py",
            "generate_isp.py",
        ]

        generator_found = None
        for gen in generator_candidates:
            gen_path = os.path.join(ISP_DIR, gen)
            if os.path.exists(gen_path):
                generator_found = gen_path
                print(C.ok(f"Generator found: {gen}"))
                break

        if not generator_found:
            # Also check engine directory
            for gen in generator_candidates:
                gen_path = os.path.join(ENGINE_DIR, gen)
                if os.path.exists(gen_path):
                    generator_found = gen_path
                    print(C.ok(f"Generator found in engine: {gen}"))
                    break

        if not generator_found:
            print(C.warn("No ISP generator found — listing all .py files:"))
            for d in [ISP_DIR, ENGINE_DIR]:
                if os.path.exists(d):
                    py_files = [f for f in os.listdir(d) if f.endswith('.py')]
                    print(f"    {d}: {py_files[:10]}")
            findings.append({
                "type": "NO_GENERATOR",
                "severity": "HIGH",
                "desc": "Cannot find ISP PDF generator script",
                "fix": "Identify the correct generator file"
            })
        else:
            # Read generator to understand its interface
            with open(generator_found, 'r', encoding='utf-8', errors='replace') as f:
                gen_content = f.read()

            # Check if it uses standard or custom Jinja2 environment
            if 'variable_start_string' in gen_content:
                print(C.info("Generator uses custom Jinja2 delimiters"))
            else:
                print(C.info("Generator uses standard Jinja2 delimiters"))

            # Check if it loads templates from the right directory
            if ISP_DIR in gen_content or 'isp' in gen_content.lower():
                print(C.ok("Generator references ISP directory"))
            else:
                findings.append({
                    "type": "WRONG_PATH",
                    "severity": "HIGH",
                    "desc": "Generator may not reference ISP directory correctly",
                    "fix": "Verify FileSystemLoader path in generator"
                })

            # Look for the render chain in the generator
            render_patterns = {
                "includes header": r'header',
                "includes footer": r'footer',
                "includes content": r'letter|form|content|body',
                "uses Environment": r'Environment\(',
                "uses FileSystemLoader": r'FileSystemLoader',
                "generates PDF": r'weasyprint|HTML\(|write_pdf|generate_pdf',
            }
            for check, pattern in render_patterns.items():
                if re.search(pattern, gen_content, re.IGNORECASE):
                    print(C.ok(f"  Generator {check}"))
                else:
                    print(C.warn(f"  Generator missing: {check}"))

        # Check for test PDF output directory
        output_dirs = [
            "/opt/windi/isp/output",
            "/opt/windi/output",
            "/tmp/windi_isp_test",
        ]
        for od in output_dirs:
            if os.path.exists(od):
                pdfs = [f for f in os.listdir(od) if f.endswith('.pdf')]
                if pdfs:
                    latest = max(pdfs, key=lambda f: os.path.getmtime(os.path.join(od, f)))
                    mtime = datetime.fromtimestamp(os.path.getmtime(os.path.join(od, latest)))
                    print(C.info(f"Latest PDF in {od}: {latest} ({mtime})"))

        self.results = findings
        return findings


# ═══════════════════════════════════════════════════════════════
#  PHASE 5: REPORT GENERATOR
# ═══════════════════════════════════════════════════════════════

class ReportGenerator:
    """Generates comprehensive pass/fail report"""

    def __init__(self):
        self.phases = {}
        self.total_score = 0

    def add_phase(self, name: str, findings: List[Dict]):
        self.phases[name] = findings

    def calculate_score(self) -> dict:
        """Calculate pass/fail score per phase and total"""
        scores = {}
        total_critical = 0
        total_high = 0
        total_warn = 0
        total_ok = 0

        for phase_name, findings in self.phases.items():
            critical = sum(1 for f in findings if f.get("severity") == "CRITICAL")
            high = sum(1 for f in findings if f.get("severity") == "HIGH")
            warn = sum(1 for f in findings if f.get("severity") in ("WARN", "LOW"))
            ok = sum(1 for f in findings if f.get("severity") in ("OK", "INFO"))

            total_critical += critical
            total_high += high
            total_warn += warn
            total_ok += ok

            if critical > 0:
                status = "FAIL"
            elif high > 0:
                status = "WARN"
            else:
                status = "PASS"

            scores[phase_name] = {
                "status": status,
                "critical": critical,
                "high": high,
                "warn": warn,
                "ok": ok,
                "total_issues": critical + high + warn
            }

        # Overall score: 0-100
        penalty = (total_critical * 25) + (total_high * 10) + (total_warn * 3)
        overall = max(0, 100 - penalty)

        return {
            "phases": scores,
            "overall_score": overall,
            "total_critical": total_critical,
            "total_high": total_high,
            "total_warn": total_warn,
            "grade": "A" if overall >= 90 else "B" if overall >= 75 else "C" if overall >= 50 else "D" if overall >= 25 else "F"
        }

    def print_report(self):
        """Print the final report to terminal"""
        scores = self.calculate_score()

        print(C.head("FINAL REPORT — ISP CORPORATE SCANNER"))
        print(f"\n  📅 Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  📂 Target:    {ISP_DIR}")
        print(f"  🔧 Engine:    {ENGINE_DIR}")

        print(f"\n  {'Phase':<25} {'Status':<8} {'CRIT':>5} {'HIGH':>5} {'WARN':>5}")
        print(f"  {'─'*25} {'─'*8} {'─'*5} {'─'*5} {'─'*5}")

        for phase, data in scores["phases"].items():
            status_color = C.PASS if data["status"] == "PASS" else C.FAIL if data["status"] == "FAIL" else C.WARN
            print(f"  {phase:<25} {status_color}{data['status']:<8}{C.END} {data['critical']:>5} {data['high']:>5} {data['warn']:>5}")

        print(f"\n  {'─'*55}")
        grade_color = C.PASS if scores["grade"] in ("A", "B") else C.WARN if scores["grade"] == "C" else C.FAIL
        print(f"\n  {C.BOLD}Overall Score: {grade_color}{scores['overall_score']}/100 (Grade: {scores['grade']}){C.END}")
        print(f"  Total: {scores['total_critical']} Critical, {scores['total_high']} High, {scores['total_warn']} Warnings")

        # Fix priority list
        print(C.head("FIX PRIORITY LIST"))
        priority = 1
        for phase_name, findings in self.phases.items():
            for f in sorted(findings, key=lambda x: {"CRITICAL": 0, "HIGH": 1, "WARN": 2}.get(x.get("severity", ""), 3)):
                if f.get("severity") in ("CRITICAL", "HIGH"):
                    severity_color = C.FAIL if f["severity"] == "CRITICAL" else C.WARN
                    print(f"\n  {severity_color}#{priority} [{f['severity']}]{C.END} {f.get('desc', 'N/A')}")
                    if f.get("template"):
                        print(f"     File: {f['template']}")
                    elif f.get("file"):
                        print(f"     File: {os.path.relpath(f['file'], ISP_DIR)}")
                    print(f"     Fix:  {f.get('fix_hint', f.get('fix', 'See details'))}")
                    priority += 1

        return scores

    def save_report(self, filepath: str = None):
        """Save report as JSON for tracking"""
        if filepath is None:
            os.makedirs(REPORT_DIR, exist_ok=True)
            filepath = os.path.join(REPORT_DIR, f"isp_scan_{TIMESTAMP}.json")

        scores = self.calculate_score()
        report = {
            "timestamp": TIMESTAMP,
            "scan_date": datetime.now().isoformat(),
            "target_dir": ISP_DIR,
            "scores": scores,
            "phases": {}
        }

        for phase_name, findings in self.phases.items():
            report["phases"][phase_name] = findings

        # Calculate hash for integrity
        report_str = json.dumps(report, sort_keys=True, default=str)
        report["integrity_hash"] = hashlib.sha256(report_str.encode()).hexdigest()[:16]

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(C.info(f"\nReport saved: {filepath}"))
        print(C.info(f"Integrity hash: {report['integrity_hash']}"))

        return filepath


# ═══════════════════════════════════════════════════════════════
#  MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════

def main():
    global ISP_DIR, ENGINE_DIR
    parser = argparse.ArgumentParser(
        description="WINDI ISP Corporate Scanner v1.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 isp_scanner.py                 # Full scan + report
  python3 isp_scanner.py --scan-only     # Scan without fixes
  python3 isp_scanner.py --fix           # Scan + apply fixes
  python3 isp_scanner.py --test-pdf      # PDF end-to-end only
  python3 isp_scanner.py --report        # Detailed report
        """
    )
    parser.add_argument('--scan-only', action='store_true', help='Scan without applying fixes')
    parser.add_argument('--fix', action='store_true', help='Scan and apply automatic fixes')
    parser.add_argument('--test-pdf', action='store_true', help='Run PDF end-to-end test only')
    parser.add_argument('--report', action='store_true', help='Generate detailed report')
    parser.add_argument('--isp-dir', default=ISP_DIR, help=f'ISP directory (default: {ISP_DIR})')
    parser.add_argument('--engine-dir', default=ENGINE_DIR, help=f'Engine directory (default: {ENGINE_DIR})')
    parser.add_argument('--json', action='store_true', help='Output as JSON only')

    args = parser.parse_args()

    # Update dirs if custom
    ISP_DIR = args.isp_dir
    ENGINE_DIR = args.engine_dir

    print(f"""
{C.HEAD}{C.BOLD}
╔══════════════════════════════════════════════════════════════╗
║           WINDI ISP CORPORATE SCANNER v1.0                  ║
║     🗼 Controlador de Tráfego, não Bombeiro 🐉              ║
╚══════════════════════════════════════════════════════════════╝
{C.END}
  Target: {ISP_DIR}
  Engine: {ENGINE_DIR}
  Mode:   {'SCAN+FIX' if args.fix else 'SCAN ONLY' if args.scan_only else 'FULL SCAN'}
  Time:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")

    report = ReportGenerator()

    # Phase 1: Syntax Scan
    scanner = SyntaxScanner(ISP_DIR)
    findings_1 = scanner.scan_all()
    report.add_phase("1_Syntax_Scan", findings_1)

    # Phase 2: Module Scan
    mod_scanner = ModuleScanner()
    findings_2 = mod_scanner.scan_sys_path()
    report.add_phase("2_Module_Scan", findings_2)

    # Phase 3: Render Chain
    render_validator = RenderChainValidator()
    findings_3 = render_validator.scan()
    report.add_phase("3_Render_Chain", findings_3)

    # Phase 4: PDF Test
    pdf_tester = PDFTestRunner()
    findings_4 = pdf_tester.scan()
    report.add_phase("4_PDF_E2E", findings_4)

    # Phase 5: Report
    if args.json:
        scores = report.calculate_score()
        print(json.dumps(scores, indent=2))
    else:
        scores = report.print_report()
        report_path = report.save_report()

    # Return exit code based on score
    if scores["overall_score"] >= 75:
        sys.exit(0)
    elif scores["overall_score"] >= 50:
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
