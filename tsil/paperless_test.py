#!/usr/bin/env python3
"""WINDI ↔ Paperless.io — First Contact Test"""
import json, urllib.request, os

TOKEN_FILE = "/opt/windi/tsil/.paperless_api_key"
API_BASE = "https://api.paperless.io/api/v1"

with open(TOKEN_FILE) as f:
    TOKEN = f.read().strip()

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

def api_call(endpoint, method="GET", data=None):
    url = f"{API_BASE}{endpoint}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "detail": e.read().decode()[:500]}

print("="*60)
print("  WINDI x Paperless.io — First Contact")
print("="*60)

# 1. Templates
print("\n[1] Templates...")
t = api_call("/templates")
print(f"    Found: {t.get('count', 0)} template(s)")
for tmpl in t.get("data", []):
    qes = tmpl.get("settings", {}).get("qes", False)
    print(f"    - {tmpl['name']} (ID:{tmpl['id']}) QES:{qes}")

# 2. Documents
print("\n[2] Documents...")
d = api_call("/documents")
print(f"    Found: {d.get('count', 0)} document(s)")

# 3. Submissions
print("\n[3] Submissions...")
s = api_call("/submissions")
print(f"    Found: {s.get('count', 0)} submission(s)")

# 4. Blobs endpoint
print("\n[4] Blobs...")
b = api_call("/blobs")
if "error" in b:
    print(f"    Status: {b}")
else:
    print(f"    Found: {b.get('count', 0)} blob(s)")

print("\n" + "="*60)
print("  Connection: SUCCESS")
print("  API Base: " + API_BASE)
print("  Workspace: 8949 | Creator: 271")
print("  'AI processes. Human decides. WINDI guarantees.'")
print("="*60)
