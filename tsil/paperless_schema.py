#!/usr/bin/env python3
"""Discover Paperless.io document creation schema"""
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
        return {"error": e.code, "detail": e.read().decode()[:1500]}

# 1. Get create info for template 36347
print("=== Create info for template 36347 ===")
r = api_call("/templates/36347/create_info")
print(json.dumps(r, indent=2, default=str, ensure_ascii=False)[:3000])

# 2. Try participation_flows
print("\n=== Participation flow 1289008 ===")
r2 = api_call("/participation_flows/1289008")
print(json.dumps(r2, indent=2, default=str, ensure_ascii=False)[:2000])

# 3. Try OPTIONS on documents endpoint
print("\n=== Trying different schemas ===")
schemas = [
    {"participation_flow_id": 1289008, "participants": [{"email": "jober@windi-domain.com"}]},
    {"document": {"participation_flow_id": 1289008}, "participants": [{"email": "jober@windi-domain.com"}]},
    {"participation_flow": {"id": 1289008}, "participants": [{"email": "jober@windi-domain.com", "first_name": "Jober", "last_name": "Correa"}]},
]

for i, schema in enumerate(schemas):
    print(f"\n  Schema {i+1}: {list(schema.keys())}")
    r = api_call("/documents", "POST", schema)
    if r.get("error"):
        print(f"  Error {r['error']}: {r['detail'][:300]}")
    else:
        print(f"  SUCCESS: {json.dumps(r, indent=2, default=str)[:500]}")
        break
