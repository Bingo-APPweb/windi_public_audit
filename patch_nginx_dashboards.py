#!/usr/bin/env python3
"""
WINDI Portal - Dashboard nginx patcher
Replaces API proxy routes with static dashboard aliases
Run with: sudo python3 patch_nginx_dashboards.py
"""

import re
import shutil
from datetime import datetime
from pathlib import Path

NGINX_CONF = "/etc/nginx/sites-enabled/windi-domain.com"
BACKUP_DIR = Path("/home/windi")

# Routes to replace: (path, alias_dir)
REPLACEMENTS = {
    "/legal/": "/opt/windi/legal-dashboard/",
    "/notary/": "/opt/windi/notary-dashboard/",
    "/sec/": "/opt/windi/sec-dashboard/",
    "/vd-cut/": "/opt/windi/vdcut-dashboard/",
    "/vd-mass/": "/opt/windi/vdmass-dashboard/",
    "/joe/": "/opt/windi/joe-dashboard/",
    "/watch/": "/opt/windi/watch-info/",
}

# New routes to add
NEW_ROUTES = """
    # Forensic Ledger Info Page
    location /ledger/ {
        alias /opt/windi/ledger-info/;
        index index.html;
        try_files $uri $uri/ /ledger/index.html;
    }
    location = /ledger { return 301 /ledger/; }

    # Audit Dashboard
    location /audit-dash/ {
        alias /opt/windi/audit-dashboard/;
        index index.html;
        try_files $uri $uri/ /audit-dash/index.html;
    }
    location = /audit-dash { return 301 /audit-dash/; }

"""

def create_static_block(path: str, alias: str) -> str:
    """Create a static file serving block"""
    clean_path = path.strip('/')
    return f"""    location {path} {{
        alias {alias};
        index index.html;
        try_files $uri $uri/ /{clean_path}/index.html;
    }}
"""

def main():
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║       WINDI PORTAL - DASHBOARD NGINX PATCHER (Python)             ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print()

    # Backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"nginx-backup-py-{timestamp}.conf"
    shutil.copy(NGINX_CONF, backup_path)
    print(f"[1] Backup created: {backup_path}")

    # Read config
    with open(NGINX_CONF, 'r') as f:
        content = f.read()

    print("[2] Processing replacements...")

    # Process each replacement
    for path, alias in REPLACEMENTS.items():
        # Pattern to match the entire location block
        # Handles both "location /path/ {" and "location ^~ /path/ {"
        pattern = rf'(    location\s+\^?~?\s*{re.escape(path)}\s*\{{[^}}]+\}})'

        match = re.search(pattern, content, re.DOTALL)
        if match:
            old_block = match.group(1)
            new_block = create_static_block(path, alias)
            content = content.replace(old_block, new_block)
            print(f"    ✓ Replaced {path}")
        else:
            print(f"    ⚠ Not found: {path}")

    # Fix fediverse route
    print("[3] Fixing fediverse route...")
    content = content.replace(
        "proxy_pass http://127.0.0.1:8142/fediverse/;",
        "proxy_pass http://127.0.0.1:8142/;"
    )
    print("    ✓ Fixed /fediverse/ proxy path")

    # Add new routes before wcache
    print("[4] Adding new routes...")
    wcache_marker = "    location /wcache/ {"
    if wcache_marker in content:
        content = content.replace(wcache_marker, NEW_ROUTES + wcache_marker)
        print("    ✓ Added /ledger/ and /audit-dash/ routes")
    else:
        print("    ⚠ Could not find wcache marker")

    # Write new config
    with open(NGINX_CONF, 'w') as f:
        f.write(content)
    print("[5] Config written")

    # Test
    print("[6] Testing nginx config...")
    import subprocess
    result = subprocess.run(['nginx', '-t'], capture_output=True, text=True)

    if result.returncode == 0:
        print("    ✅ nginx config OK")

        # Reload
        print("[7] Reloading nginx...")
        subprocess.run(['systemctl', 'reload', 'nginx'])
        print("    ✅ nginx reloaded")

        # Test URLs
        print()
        print("[8] Testing routes...")
        import urllib.request

        for route in ['legal', 'notary', 'sec', 'vd-cut', 'vd-mass', 'joe', 'watch', 'fediverse', 'ledger', 'audit-dash']:
            url = f"https://windi-domain.com/{route}/"
            try:
                req = urllib.request.Request(url, method='HEAD')
                with urllib.request.urlopen(req, timeout=5) as resp:
                    status = resp.status
            except Exception as e:
                status = str(e)[:30]

            mark = "✅" if status == 200 else "❌"
            print(f"    {mark} /{route}/ → {status}")

        print()
        print("╔════════════════════════════════════════════════════════════════════╗")
        print("║                    ✅ PATCH COMPLETE                               ║")
        print("╚════════════════════════════════════════════════════════════════════╝")
    else:
        print("    ❌ nginx config ERROR - restoring backup")
        print(result.stderr)
        shutil.copy(backup_path, NGINX_CONF)
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
