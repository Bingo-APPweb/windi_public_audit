#!/usr/bin/env python3
"""
W-SERVICE-CONTROL Link Auditor
Scans all service URLs and detects broken links

Usage: python3 audit_links.py [--fix]
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
SERVICE_CONTROL_API = "http://localhost:8170/api/services"
BASE_URL = "http://127.0.0.1"  # Through nginx
HOST_HEADER = "windi-domain.com"
PUBLIC_URL = "https://windi-domain.com"

# Known URL mappings (incorrect -> correct)
URL_FIXES = {
    "/telegram/": "https://t.me/windi_nomad_bot",  # Bot, not web UI
    "/vdcut-dash/": "/vd-cut/",
    "/joe-dash/": "/joe/",
    "/vdmass-dash/": "/vd-mass/",
    "/sec-dash/": "/sec/",
    "/audit-dash/": "/audit/",
}

# Services without web UI (bots, APIs only)
NO_WEB_UI = [
    "windi-nomad-bot",  # Telegram bot
    "windi-dispatch",   # API gateway
]

def test_url(url, timeout=5):
    """Test if a URL is accessible."""
    if url.startswith("https://t.me/"):
        return {"status": "external", "url": url, "note": "Telegram bot link"}

    if not url.startswith("http"):
        full_url = BASE_URL + url
    else:
        full_url = url

    headers = {"Host": HOST_HEADER}

    try:
        r = requests.get(full_url, timeout=timeout, allow_redirects=True, headers=headers)
        content_type = r.headers.get('content-type', '')

        # Check for JSON error responses
        if 'application/json' in content_type:
            try:
                data = r.json()
                if 'error' in data or 'detail' in data:
                    return {
                        "status": "error",
                        "code": r.status_code,
                        "error": data.get('error') or data.get('detail'),
                        "url": url
                    }
            except:
                pass

        if r.status_code == 200:
            # Check if it's actually HTML content
            if 'text/html' in content_type or '<!DOCTYPE' in r.text[:100]:
                return {"status": "ok", "code": 200, "url": url}
            else:
                return {"status": "ok", "code": 200, "url": url, "note": "API endpoint"}
        elif r.status_code in [301, 302, 307, 308]:
            return {"status": "redirect", "code": r.status_code, "url": url}
        else:
            return {"status": "error", "code": r.status_code, "url": url}

    except requests.exceptions.ConnectionError:
        return {"status": "offline", "error": "Connection refused", "url": url}
    except requests.exceptions.Timeout:
        return {"status": "timeout", "error": "Request timed out", "url": url}
    except Exception as e:
        return {"status": "error", "error": str(e)[:50], "url": url}

def get_services():
    """Fetch all services from Service Control API."""
    try:
        r = requests.get(SERVICE_CONTROL_API, timeout=5)
        return r.json().get("services", [])
    except Exception as e:
        print(f"❌ Failed to fetch services: {e}")
        return []

def suggest_fix(service_name, url, result):
    """Suggest a fix for broken URL."""
    # Check known fixes
    if url in URL_FIXES:
        return URL_FIXES[url]

    # Check if service has no web UI
    if service_name in NO_WEB_UI:
        return None  # Remove URL or use external link

    # Try common patterns
    patterns_to_try = [
        url.replace("-dash/", "/"),
        url.replace("dash/", "/"),
        "/" + service_name.replace("windi-", "") + "/",
    ]

    for pattern in patterns_to_try:
        if pattern != url:
            test = test_url(pattern)
            if test["status"] == "ok":
                return pattern

    return None

def main():
    fix_mode = "--fix" in sys.argv

    print("=" * 60)
    print("W-SERVICE-CONTROL Link Auditor")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    print()

    services = get_services()
    if not services:
        print("No services found!")
        return

    print(f"Scanning {len(services)} services...\n")

    results = {
        "ok": [],
        "error": [],
        "offline": [],
        "no_url": [],
        "external": []
    }

    fixes_needed = []

    for svc in services:
        name = svc.get("service", svc.get("name", "unknown"))
        display = svc.get("display", name)
        url = svc.get("url", "")
        port = svc.get("port", "?")

        if not url:
            results["no_url"].append({"name": name, "display": display, "port": port})
            continue

        result = test_url(url)
        result["name"] = name
        result["display"] = display
        result["port"] = port
        result["original_url"] = url

        if result["status"] == "ok":
            results["ok"].append(result)
            print(f"  ✅ {display} ({url})")
        elif result["status"] == "external":
            results["external"].append(result)
            print(f"  🔗 {display} → {url}")
        elif result["status"] == "offline":
            results["offline"].append(result)
            print(f"  ⬛ {display} ({url}) - OFFLINE")
        else:
            results["error"].append(result)
            error_msg = result.get("error", f"HTTP {result.get('code', '?')}")
            print(f"  ❌ {display} ({url}) - {error_msg}")

            # Try to find a fix
            fix = suggest_fix(name, url, result)
            if fix:
                fixes_needed.append({
                    "name": name,
                    "display": display,
                    "current": url,
                    "suggested": fix
                })
                print(f"     💡 Suggested fix: {fix}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  ✅ Working:    {len(results['ok'])}")
    print(f"  🔗 External:   {len(results['external'])}")
    print(f"  ❌ Broken:     {len(results['error'])}")
    print(f"  ⬛ Offline:    {len(results['offline'])}")
    print(f"  ⚪ No URL:     {len(results['no_url'])}")
    print()

    if fixes_needed:
        print("=" * 60)
        print("FIXES AVAILABLE")
        print("=" * 60)
        for fix in fixes_needed:
            print(f"  {fix['display']}:")
            print(f"    Current:   {fix['current']}")
            print(f"    Suggested: {fix['suggested']}")
            print()

        if fix_mode:
            print("Applying fixes to /opt/windi/service-control/app.py...")
            apply_fixes(fixes_needed)
        else:
            print("Run with --fix to apply these fixes automatically")

    # Return results for programmatic use
    return results, fixes_needed

def apply_fixes(fixes):
    """Apply URL fixes to service-control/app.py"""
    app_path = "/opt/windi/service-control/app.py"

    try:
        with open(app_path, 'r') as f:
            content = f.read()

        modified = False
        for fix in fixes:
            old = f'"url": "{fix["current"]}"'
            new = f'"url": "{fix["suggested"]}"'
            if old in content:
                content = content.replace(old, new)
                print(f"  ✓ Fixed {fix['display']}: {fix['current']} → {fix['suggested']}")
                modified = True
            else:
                # Try without spaces
                old = f'"url":"{fix["current"]}"'
                new = f'"url":"{fix["suggested"]}"'
                if old in content:
                    content = content.replace(old, new)
                    print(f"  ✓ Fixed {fix['display']}")
                    modified = True

        if modified:
            with open(app_path, 'w') as f:
                f.write(content)
            print("\n✅ Fixes applied. Restart service-control to take effect.")
            print("   pkill -f 'service-control/app.py' && cd /opt/windi/service-control && python3 app.py &")
        else:
            print("\n⚠️ No fixes were applied (patterns not found)")

    except Exception as e:
        print(f"\n❌ Failed to apply fixes: {e}")

if __name__ == "__main__":
    main()
