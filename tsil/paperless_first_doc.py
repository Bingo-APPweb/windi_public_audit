#!/usr/bin/env python3
"""WINDI — First Document via Paperless API"""
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
            return {"success": True, "data": json.loads(resp.read())}
    except urllib.error.HTTPError as e:
        return {"success": False, "error": e.code, "detail": e.read().decode()[:500]}

# Create document from template 36347 (Demo Paperless Dokument)
print("Creating first WINDI governance document...")
result = api_call("/documents", "POST", {
    "template_id": 36347,
    "document_name": "WINDI Governance First Contact",
    "participants": [
        {
            "email": "jober@windi-domain.com",
            "first_name": "Jober",
            "last_name": "Moegele Correa",
            "role": "signer"
        }
    ]
})

print(json.dumps(result, indent=2, default=str)[:1000])
