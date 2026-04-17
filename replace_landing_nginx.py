#!/usr/bin/env python3
"""
WINDI Infra Surgeon — Enterprise Landing Nginx Replacement
Replaces dead proxy (:8107) with static landing page.

SEALED: 2026-04-17 — INFRA-SURGEON-001
"""

import sys
import subprocess
from datetime import datetime
from pathlib import Path

# ── Configuration ────────────────────────────────────────────
NGINX_CONFIG = "/etc/nginx/sites-enabled/windi-domain.com"
BACKUP_DIR = "/opt/windi/backups"
LANDING_PATH = "/opt/windi/landing-enterprise"

# Old block to replace (lines 631-644)
OLD_BLOCK = """    location / {
        proxy_pass http://windi_landing;
        proxy_http_version 1.1;
    }

    location ^~ /personal/ {
        proxy_pass http://windi_landing;
        proxy_http_version 1.1;
    }

    location ^~ /org/ {
        proxy_pass http://windi_landing;
        proxy_http_version 1.1;
    }"""

# New block (static landing + redirects)
NEW_BLOCK = """    # ── W-Enterprise Landing (LIVE) ─────────────────────────
    location / {
        root /opt/windi/landing-enterprise;
        index index.html;
        try_files $uri $uri/ /index.html;
        add_header X-WINDI-Service "enterprise-landing" always;
    }

    # NOTE: /personal/ e /org/ deprecated — redirect para landing
    location ^~ /personal/ {
        return 301 /;
    }

    location ^~ /org/ {
        return 301 /;
    }"""


def run(cmd, check=True, capture=True):
    """Execute shell command."""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=capture,
        text=True,
        check=False
    )
    if check and result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        print(f"   stderr: {result.stderr}")
        sys.exit(1)
    return result


def main():
    print("═══ WINDI INFRA SURGEON — ENTERPRISE LANDING DEPLOY ═══\n")

    # ── Step 1: Verify landing page exists ──────────────────
    print("STEP 1/5: Verify landing page...")
    landing_html = Path(LANDING_PATH) / "index.html"
    if not landing_html.exists():
        print(f"❌ Landing page not found: {landing_html}")
        sys.exit(1)
    size = landing_html.stat().st_size
    print(f"   ✅ Found: {landing_html} ({size} bytes)")

    # ── Step 2: Backup nginx config ─────────────────────────
    print("\nSTEP 2/5: Backup nginx config...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{BACKUP_DIR}/pre_enterprise_landing_nginx_{timestamp}.conf"

    run(f"cp {NGINX_CONFIG} {backup_path}")
    print(f"   ✅ Backup: {backup_path}")

    # ── Step 3: Read and validate current config ────────────
    print("\nSTEP 3/5: Validate current config...")
    with open(NGINX_CONFIG, 'r') as f:
        content = f.read()

    if OLD_BLOCK not in content:
        print("❌ Old block not found in config!")
        print("   Config may have been modified. Manual intervention required.")
        sys.exit(1)
    print("   ✅ Old block found")

    # ── Step 4: Replace block ───────────────────────────────
    print("\nSTEP 4/5: Replace proxy block with static landing...")
    new_content = content.replace(OLD_BLOCK, NEW_BLOCK)

    with open(NGINX_CONFIG, 'w') as f:
        f.write(new_content)
    print("   ✅ Config rewritten")

    # ── Step 5: Test nginx config ───────────────────────────
    print("\nSTEP 5/5: Test nginx config...")
    result = run("sudo nginx -t", check=False)

    if result.returncode != 0:
        print("❌ nginx -t FAILED! Rolling back...")
        run(f"cp {backup_path} {NGINX_CONFIG}")
        print(f"   ✅ Rollback complete. Config restored from backup.")
        print(f"\n   Error output:\n{result.stderr}")
        sys.exit(1)

    print("   ✅ nginx -t passed")

    # ── Success banner ──────────────────────────────────────
    print("\n" + "═" * 55)
    print("✅ NGINX CONFIG REPLACEMENT COMPLETE")
    print("═" * 55)
    print(f"\nBackup:  {backup_path}")
    print(f"Landing: {landing_html}")
    print("\n⏳ READY FOR RELOAD — Awaiting human approval:")
    print("   sudo systemctl reload nginx")
    print("\nExpected outcome:")
    print("   https://windi-domain.com/          → HTTP 200")
    print("   https://windi-domain.com/personal/ → HTTP 301")
    print("   https://windi-domain.com/org/      → HTTP 301")
    print("═" * 55)


if __name__ == "__main__":
    main()
