#!/usr/bin/env python3
"""
WINDI Nginx Auto-Register — W-NGINX-001
========================================
Sistema de Contenção #3: Elimina Loop 1 (rotas esquecidas)

Detecta:
  - MISSING: rotas Flask que não têm location nginx
  - ORPHAN: locations nginx que não têm rota Flask correspondente

Uso:
    python3 nginx_audit.py              # Relatório completo
    python3 nginx_audit.py --generate   # Gera snippets nginx para rotas faltantes
    python3 nginx_audit.py --watch      # Modo daemon (futuro)

Criado: 2026-03-19
Liga IA+H — Kempten, Bavaria
"AI processes. Human decides. WINDI guarantees."
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────

NGINX_CONFIG = "/etc/nginx/sites-enabled/windi-domain.com"
SCAN_DIRS = [
    "/opt/windi/agents/constitutional-agent",
    "/opt/windi/desktop-gen7",
    "/opt/windi/ledger",
    "/opt/windi/dispatch",
    "/opt/windi/wallet",
    "/opt/windi/agent-palette",
    "/opt/windi/export-engine",
    "/opt/windi/verify-public",
    "/opt/windi/communique-engine",
    "/opt/windi/pioneer",
]

# Port mappings for upstream generation
PORT_MAP = {
    "constitutional-agent": 8091,
    "desktop-gen7": 8119,
    "ledger": 8101,
    "dispatch": 8121,
    "wallet": 8099,
    "dragon": 8108,
    "export": 8103,
    "verify": 8114,
}

# Routes to ignore (internal only, not exposed via nginx)
IGNORE_ROUTES = {
    "/health",
    "/agent/health",
    "/agent/status",
    "/agent/manifest",
}

# Nginx locations that are static aliases (not proxied to Flask)
STATIC_LOCATIONS = {
    "/jornal/",
    "/how-it-works/",
    "/keys/",
    "/verify-public/viewer/",
    "/verify-public/web/",
    "/library/",
    "/mobile/",
}


# ─────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────

@dataclass
class FlaskRoute:
    """A Flask route found in Python code."""
    path: str
    methods: List[str]
    file: str
    line: int
    service: str = ""


@dataclass
class NginxLocation:
    """An nginx location block."""
    path: str
    proxy_pass: str = ""
    is_static: bool = False
    line: int = 0


@dataclass
class AuditResult:
    """Result of nginx/Flask audit."""
    flask_routes: List[FlaskRoute] = field(default_factory=list)
    nginx_locations: List[NginxLocation] = field(default_factory=list)
    missing: List[FlaskRoute] = field(default_factory=list)  # In Flask, not in nginx
    orphan: List[NginxLocation] = field(default_factory=list)  # In nginx, no Flask
    timestamp: str = ""


# ─────────────────────────────────────────────────────────────
# FLASK ROUTE SCANNER
# ─────────────────────────────────────────────────────────────

def extract_flask_routes(directory: str) -> List[FlaskRoute]:
    """Scan Python files for Flask route decorators."""
    routes = []

    # Patterns for Flask routes
    patterns = [
        # @app.route("/path", methods=["GET", "POST"])
        r'@app\.route\(["\']([^"\']+)["\'](?:,\s*methods=\[([^\]]+)\])?',
        # @blueprint.route("/path")
        r'@\w+_bp\.route\(["\']([^"\']+)["\'](?:,\s*methods=\[([^\]]+)\])?',
        # @bp.route("/path")
        r'@bp\.route\(["\']([^"\']+)["\'](?:,\s*methods=\[([^\]]+)\])?',
    ]

    path = Path(directory)
    if not path.exists():
        return routes

    # Determine service name from directory
    service = path.name

    for py_file in path.rglob("*.py"):
        try:
            content = py_file.read_text(encoding='utf-8')
            lines = content.split('\n')

            for i, line in enumerate(lines, 1):
                for pattern in patterns:
                    match = re.search(pattern, line)
                    if match:
                        route_path = match.group(1)
                        methods_str = match.group(2) if match.lastindex >= 2 else None

                        if methods_str:
                            methods = [m.strip().strip('"\'') for m in methods_str.split(',')]
                        else:
                            methods = ["GET"]

                        routes.append(FlaskRoute(
                            path=route_path,
                            methods=methods,
                            file=str(py_file),
                            line=i,
                            service=service
                        ))
        except Exception as e:
            print(f"⚠️  Error reading {py_file}: {e}")

    return routes


# ─────────────────────────────────────────────────────────────
# NGINX PARSER
# ─────────────────────────────────────────────────────────────

def parse_nginx_locations(config_path: str) -> List[NginxLocation]:
    """Parse nginx config for location blocks."""
    locations = []

    try:
        with open(config_path, 'r') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        print(f"❌ Cannot read nginx config: {e}")
        return locations

    # Pattern for location blocks
    location_pattern = r'location\s+(=|~|~\*|\^~)?\s*([^\s{]+)'
    proxy_pattern = r'proxy_pass\s+([^;]+);'
    alias_pattern = r'alias\s+([^;]+);'

    current_location = None
    brace_depth = 0

    for i, line in enumerate(lines, 1):
        # Track location blocks
        loc_match = re.search(location_pattern, line)
        if loc_match:
            modifier = loc_match.group(1) or ""
            path = loc_match.group(2)
            current_location = NginxLocation(path=path, line=i)
            brace_depth = 0

        # Track braces
        brace_depth += line.count('{') - line.count('}')

        # Look for proxy_pass or alias inside location
        if current_location:
            proxy_match = re.search(proxy_pattern, line)
            alias_match = re.search(alias_pattern, line)

            if proxy_match:
                current_location.proxy_pass = proxy_match.group(1).strip()
            if alias_match:
                current_location.is_static = True

            # End of location block
            if brace_depth == 0 and '}' in line:
                locations.append(current_location)
                current_location = None

    return locations


# ─────────────────────────────────────────────────────────────
# AUDIT ENGINE
# ─────────────────────────────────────────────────────────────

def normalize_path(path: str) -> str:
    """Normalize path for comparison."""
    # Remove trailing slash, convert to lowercase
    return path.rstrip('/').lower()


def route_matches_location(route: FlaskRoute, location: NginxLocation) -> bool:
    """Check if a Flask route is covered by an nginx location."""
    route_norm = normalize_path(route.path)
    loc_norm = normalize_path(location.path)

    # Exact match
    if route_norm == loc_norm:
        return True

    # Location with ^~ prefix match
    if route_norm.startswith(loc_norm):
        return True

    # API routes often have prefixes
    if f"/api{route_norm}" == loc_norm or route_norm == f"/api{loc_norm}":
        return True

    return False


def run_audit() -> AuditResult:
    """Run full nginx/Flask audit."""
    result = AuditResult(timestamp=datetime.now().isoformat())

    # Collect Flask routes
    print("🔍 Scanning Flask routes...")
    for directory in SCAN_DIRS:
        routes = extract_flask_routes(directory)
        result.flask_routes.extend(routes)

    print(f"   Found {len(result.flask_routes)} Flask routes")

    # Parse nginx config
    print("🔍 Parsing nginx config...")
    result.nginx_locations = parse_nginx_locations(NGINX_CONFIG)
    print(f"   Found {len(result.nginx_locations)} nginx locations")

    # Find missing routes (in Flask, not in nginx)
    print("🔍 Checking for missing routes...")
    for route in result.flask_routes:
        # Skip ignored routes
        if route.path in IGNORE_ROUTES:
            continue

        # Check if any nginx location covers this route
        covered = False
        for location in result.nginx_locations:
            if route_matches_location(route, location):
                covered = True
                break

        if not covered:
            result.missing.append(route)

    # Find orphan locations (in nginx, no corresponding Flask route)
    # This is informational - static locations are expected
    for location in result.nginx_locations:
        if location.is_static or location.path in STATIC_LOCATIONS:
            continue

        # Check if any Flask route matches
        has_route = False
        for route in result.flask_routes:
            if route_matches_location(route, location):
                has_route = True
                break

        # Only flag as orphan if it's a proxy location with no matching route
        if not has_route and location.proxy_pass:
            result.orphan.append(location)

    return result


# ─────────────────────────────────────────────────────────────
# NGINX SNIPPET GENERATOR
# ─────────────────────────────────────────────────────────────

def generate_nginx_snippet(route: FlaskRoute) -> str:
    """Generate nginx location block for a missing route."""
    port = PORT_MAP.get(route.service, 8091)

    # Determine if it needs special handling
    needs_ws = "ws" in route.path.lower() or "socket" in route.path.lower()

    snippet = f"""
    # ── AUTO-GENERATED: {route.path} ({route.service}) ────────────
    location ^~ {route.path} {{
        proxy_pass http://127.0.0.1:{port}{route.path};
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;"""

    if needs_ws:
        snippet += """
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";"""

    snippet += """
        add_header X-WINDI-Service "auto-register" always;
    }
    # ── END AUTO-GENERATED ────────────────────────────────────
"""
    return snippet


# ─────────────────────────────────────────────────────────────
# REPORTER
# ─────────────────────────────────────────────────────────────

def print_report(result: AuditResult, generate: bool = False):
    """Print audit report."""
    print("\n" + "=" * 60)
    print("WINDI NGINX AUDIT — W-NGINX-001")
    print("=" * 60)
    print(f"Timestamp: {result.timestamp}")
    print(f"Flask Routes: {len(result.flask_routes)}")
    print(f"Nginx Locations: {len(result.nginx_locations)}")
    print()

    # Missing routes
    if result.missing:
        print("❌ MISSING ROUTES (Flask → nginx)")
        print("-" * 40)
        for route in result.missing:
            print(f"  {route.path}")
            print(f"    Methods: {', '.join(route.methods)}")
            print(f"    Source: {route.file}:{route.line}")
            print(f"    Service: {route.service}")
            print()

        if generate:
            print("\n📋 GENERATED NGINX SNIPPETS")
            print("-" * 40)
            for route in result.missing:
                print(generate_nginx_snippet(route))
    else:
        print("✅ All Flask routes have nginx coverage")

    print()

    # Orphan locations (informational)
    if result.orphan:
        print("⚠️  ORPHAN LOCATIONS (nginx without Flask)")
        print("-" * 40)
        for loc in result.orphan:
            print(f"  {loc.path}")
            print(f"    Proxy: {loc.proxy_pass}")
            print(f"    Line: {loc.line}")
            print()

    print("=" * 60)

    # Summary
    status = "✅ PASS" if not result.missing else "❌ FAIL"
    print(f"Status: {status}")
    print(f"Missing: {len(result.missing)} | Orphan: {len(result.orphan)}")
    print("=" * 60)


def save_report(result: AuditResult, path: str = "/opt/windi/contracts/nginx_audit_report.json"):
    """Save audit result as JSON."""
    data = {
        "timestamp": result.timestamp,
        "summary": {
            "flask_routes": len(result.flask_routes),
            "nginx_locations": len(result.nginx_locations),
            "missing": len(result.missing),
            "orphan": len(result.orphan),
            "status": "PASS" if not result.missing else "FAIL"
        },
        "missing": [
            {
                "path": r.path,
                "methods": r.methods,
                "file": r.file,
                "line": r.line,
                "service": r.service
            }
            for r in result.missing
        ],
        "orphan": [
            {
                "path": l.path,
                "proxy_pass": l.proxy_pass,
                "line": l.line
            }
            for l in result.orphan
        ]
    }

    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n📄 Report saved: {path}")


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    print("WINDI Nginx Auto-Register — W-NGINX-001")
    print("Sistema de Contenção #3")
    print("-" * 40)

    generate = "--generate" in sys.argv
    save = "--save" in sys.argv

    result = run_audit()
    print_report(result, generate=generate)

    if save:
        save_report(result)

    # Exit code for CI/CD
    sys.exit(0 if not result.missing else 1)
