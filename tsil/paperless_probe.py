#!/usr/bin/env python3
"""Probe all possible Paperless.io document creation schemas"""
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
            return {"ok": True, "data": json.loads(resp.read())}
    except urllib.error.HTTPError as e:
        return {"ok": False, "code": e.code, "msg": e.read().decode()[:400]}

# Part 1: Probe related endpoints
print("=== Probing endpoints ===")
endpoints = [
    "/blobs", "/submissions", "/documents/create",
    "/templates/36347/documents", "/templates/36347/submissions",
    "/participation_flows", "/webhooks",
]
for ep in endpoints:
    r = api_call(ep)
    status = "OK" if r["ok"] else f"ERR {r['code']}"
    detail = json.dumps(r.get("data", r.get("msg", "")), default=str)[:120]
    print(f"  GET {ep}: {status} -> {detail}")

# Part 2: Try POST to /documents with template-based schemas
print("\n=== POST /documents schemas ===")
schemas = [
    ("from_template", {"from_template": {"template_id": 36347, "participants": [{"email": "jober@windi-domain.com", "first_name": "Jober", "last_name": "Correa"}]}}),
    ("flat_with_id", {"id": 36347, "participants": [{"email": "jober@windi-domain.com"}]}),
    ("data_wrapper", {"data": {"template_id": 36347, "participants": [{"email": "jober@windi-domain.com"}]}}),
    ("draft", {"draft": True, "template_id": 36347}),
]
for name, body in schemas:
    r = api_call("/documents", "POST", body)
    status = "OK" if r["ok"] else f"ERR {r['code']}"
    detail = json.dumps(r.get("data", r.get("msg", "")), default=str)[:200]
    print(f"  {name}: {status} -> {detail}")

# Part 3: Try POST to /templates/36347/documents
print("\n=== POST /templates/36347/documents ===")
r = api_call("/templates/36347/documents", "POST", {
    "participants": [{"email": "jober@windi-domain.com", "first_name": "Jober", "last_name": "Correa"}]
})
print(f"  Result: {'OK' if r['ok'] else 'ERR ' + str(r.get('code', ''))}")
print(f"  {json.dumps(r.get('data', r.get('msg', '')), default=str)[:500]}")

# Part 4: Try POST to /submissions
print("\n=== POST /submissions ===")
r = api_call("/submissions", "POST", {
    "template_id": 36347,
    "participants": [{"email": "jober@windi-domain.com", "first_name": "Jober", "last_name": "Correa"}]
})
print(f"  Result: {'OK' if r['ok'] else 'ERR ' + str(r.get('code', ''))}")
print(f"  {json.dumps(r.get('data', r.get('msg', '')), default=str)[:500]}")
