#!/usr/bin/env python3
"""Discover Paperless API schema"""
import json, urllib.request

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
        return {"error": e.code, "detail": e.read().decode()[:800]}

# 1. Get full template detail to see participation_flow
print("=== Template 36347 detail ===")
t = api_call("/templates/36347")
print(json.dumps(t, indent=2, default=str, ensure_ascii=False)[:2000])

# 2. Try different doc creation schemas
print("\n=== Try schema: name + template_id ===")
r1 = api_call("/documents", "POST", {"name": "WINDI Test", "template_id": 36347})
print(json.dumps(r1, indent=2, default=str)[:500])

# 3. Try with just template
print("\n=== Try schema: template only ===")
r2 = api_call("/documents", "POST", {"template": {"id": 36347}})
print(json.dumps(r2, indent=2, default=str)[:500])

# 4. Check OpenAPI spec
print("\n=== OpenAPI spec ===")
spec = api_call("/openapi.json")
if "error" in spec:
    spec = api_call("/swagger.json")
if "error" in spec:
    spec = api_call("/docs")
print(json.dumps(spec, indent=2, default=str)[:500])
