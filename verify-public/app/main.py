import os
import hashlib
import logging
import time
import sys
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
import re
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(__file__))
from verify_engine import VerifyEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [VERIFY] %(levelname)s %(message)s", handlers=[logging.StreamHandler(), logging.FileHandler("/opt/windi/logs/verify-public.log")])
log = logging.getLogger("windi.verify")

PORT          = int(os.getenv("VERIFY_PORT", 8114))
LEDGER_URL    = os.getenv("LEDGER_URL", "http://localhost:8101")
AGENTS_URL    = os.getenv("AGENTS_URL", "http://localhost:8091")
MAX_FILE_SIZE = 10 * 1024 * 1024
CACHE_TTL     = 60
_cache: dict  = {}

def cache_get(key):
    e = _cache.get(key)
    if e and time.time() < e[1]:
        return e[0]
    return None

def cache_set(key, value):
    _cache[key] = (value, time.time() + CACHE_TTL)
    if len(_cache) > 1000:
        now = time.time()
        for k in [k for k, v in list(_cache.items()) if now >= v[1]]:
            del _cache[k]

def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

app = FastAPI(title="WINDI Verify Public Agent", version="1.0.1", docs_url="/verify-public/docs", redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET","POST"], allow_headers=["*"])
engine = VerifyEngine(ledger_url=LEDGER_URL, agents_url=AGENTS_URL, timeout=5.0)

WEB_DIR = os.path.join(os.path.dirname(__file__), "..", "web")
if os.path.isdir(WEB_DIR):
    app.mount("/verify-public/static", StaticFiles(directory=WEB_DIR), name="static")

DOCS_DIR = os.path.join(WEB_DIR, "docs")
if os.path.isdir(DOCS_DIR):
    app.mount("/verify-public/docs", StaticFiles(directory=DOCS_DIR), name="docs")

class VerifyResult(BaseModel):
    status: str
    document_id: Optional[str] = None
    hash: Optional[str] = None
    integrity: str
    signature: str
    ledger_anchor: bool
    timestamp: Optional[str] = None
    checked_at: str
    message: str
    cached: bool = False

@app.get("/health")
@app.get("/verify-public/health")
async def health():
    return {"service":"windi-verify-public","version":"1.0.1","status":"operational","cache_entries":len(_cache),"port":PORT,"timestamp":now_iso()}

@app.get("/verify-public/")
async def ui_root():
    index = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return JSONResponse({"service":"WINDI Verify Public","version":"1.0.1"})

@app.get("/verify-public/document/{document_id}", response_model=VerifyResult)
async def verify_by_id(document_id: str):
    c = cache_get(f"doc:{document_id}")
    if c: return {**c, "cached": True}
    r = await engine.verify_document_id(document_id)
    cache_set(f"doc:{document_id}", r)
    return r

@app.get("/verify-public/hash/{sha256_hash}", response_model=VerifyResult)
async def verify_by_hash(sha256_hash: str):
    c = cache_get(f"hash:{sha256_hash}")
    if c: return {**c, "cached": True}
    r = await engine.verify_hash(sha256_hash)
    cache_set(f"hash:{sha256_hash}", r)
    return r

@app.get("/verify-public/qr/{qr_data:path}", response_model=VerifyResult)
async def verify_by_qr(qr_data: str):
    c = cache_get(f"qr:{qr_data}")
    if c: return {**c, "cached": True}
    r = await engine.verify_qr(qr_data)
    cache_set(f"qr:{qr_data}", r)
    return r

@app.post("/verify-public/file", response_model=VerifyResult)
async def verify_file(file: UploadFile = File(...)):
    content = await file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Max 10MB.")
    sha256 = hashlib.sha256(content).hexdigest()
    c = cache_get(f"hash:{sha256}")
    if c: return {**c, "cached": True}
    r = await engine.verify_hash(sha256)
    cache_set(f"hash:{sha256}", r)
    return r

@app.get("/verify-public/timeline/{document_id}")
async def verify_timeline(document_id: str):
    return await engine.get_timeline(document_id)


async def get_document_metadata(doc_id: str) -> dict:
    """Fetch document metadata from Ledger for OG tags."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            # Try Ledger receipt endpoint
            r = await client.get(f"{LEDGER_URL}/api/receipts/{doc_id}")
            if r.status_code == 200:
                data = r.json()
                return {
                    "title": data.get("doc_title") or data.get("title") or doc_id,
                    "doc_type": data.get("doc_type", "Document"),
                    "created_at": data.get("created_at", data.get("ts", "")),
                    "issuer": data.get("issuer") or data.get("actor") or "WINDI",
                    "status": "verified"
                }
    except Exception as e:
        log.warning(f"[OG] Failed to fetch metadata for {doc_id}: {e}")
    return {"title": doc_id, "doc_type": "Document", "created_at": "", "issuer": "WINDI", "status": "pending"}


def inject_og_tags(html: str, doc_id: str, meta: dict) -> str:
    """Inject dynamic OG tags into HTML for social sharing."""
    title = f"✓ {meta['title']} — WINDI Verified"
    description = f"Document {doc_id} authenticated by WINDI Forensic Ledger. Type: {meta['doc_type']}. Issuer: {meta['issuer']}. Integrity confirmed."
    url = f"https://windi-domain.com/verify-public/{doc_id}"

    # Replace OG tags
    html = re.sub(
        r'<meta property="og:title" content="[^"]*"/>',
        f'<meta property="og:title" content="{title}"/>',
        html
    )
    html = re.sub(
        r'<meta property="og:description" content="[^"]*"/>',
        f'<meta property="og:description" content="{description}"/>',
        html
    )
    html = re.sub(
        r'<meta property="og:url" content="[^"]*"/>',
        f'<meta property="og:url" content="{url}"/>',
        html
    )
    # Twitter cards
    html = re.sub(
        r'<meta name="twitter:title" content="[^"]*"/>',
        f'<meta name="twitter:title" content="{title}"/>',
        html
    )
    html = re.sub(
        r'<meta name="twitter:description" content="[^"]*"/>',
        f'<meta name="twitter:description" content="{description}"/>',
        html
    )
    # Page title
    html = re.sub(
        r'<title>[^<]*</title>',
        f'<title>{title}</title>',
        html
    )
    return html


# ═══════════════════════════════════════════════════════════════════════════════
# S3-2: WICK VIEW — HTML render with OG tags + embedded Verify
# URL: windi-domain.com/wick/{artifact_id}
# Decisão Human Dragon 2026-03-08: Privado por defeito
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/wick/view/{artifact_id}")
async def wick_artifact_view(artifact_id: str):
    """S3-2: HTML view for WICK artifacts with OG tags.
    URL: windi-domain.com/wick/view/{artifact_id}
    """
    # 1. Fetch artifact from Constitutional Agent
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"http://localhost:8091/wick/artifact/{artifact_id}")
            if r.status_code == 404:
                return HTMLResponse(
                    "<html><body style='font-family:system-ui;text-align:center;padding:60px;'>"
                    "<h1>🔍 Artifact not found</h1>"
                    f"<p>ID: <code>{artifact_id}</code></p>"
                    "<a href='/verify-public/'>Go to Verify</a>"
                    "</body></html>",
                    status_code=404
                )
            data = r.json()
    except Exception as e:
        log.error(f"[WICK] Failed to fetch artifact {artifact_id}: {e}")
        return HTMLResponse(
            "<html><body style='font-family:system-ui;text-align:center;padding:60px;'>"
            "<h1>⚠️ Service unavailable</h1>"
            "<p>Please try again later.</p>"
            "</body></html>",
            status_code=503
        )

    artifact = data.get("artifact", {})

    # 2. Check visibility (private = 403, GDPR compliant)
    visibility = artifact.get("visibility", "private")
    if visibility == "private":
        return HTMLResponse(
            "<html><body style='font-family:system-ui;text-align:center;padding:60px;'>"
            "<h1>🔒 Private Artifact</h1>"
            "<p>This artifact is private. Only the owner can view it.</p>"
            "<p style='color:#666;font-size:14px;'>I12 — Web of Proofs · Privacy by Default</p>"
            "</body></html>",
            status_code=403
        )

    # 3. Build HTML with OG tags
    title = artifact.get("title", artifact_id)
    author = artifact.get("author_name", "WINDI")
    artifact_type = artifact.get("type", "document")
    created_at = artifact.get("created_at", "")[:10] if artifact.get("created_at") else ""
    page_url = artifact.get("page_url", "")
    verify_url = f"https://windi-domain.com/verify-public/?id={artifact_id}"
    wick_url = f"https://windi-domain.com/wick/{artifact_id}"

    # Escape HTML in title/author
    import html as html_escape
    title_safe = html_escape.escape(title)
    author_safe = html_escape.escape(author)

    html = f'''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>✓ {title_safe} — WINDI</title>

    <!-- OG Tags for Social Sharing -->
    <meta property="og:title" content="✓ {title_safe} — WINDI Verified"/>
    <meta property="og:description" content="Document by {author_safe}. Verified on WINDI Forensic Ledger. Type: {artifact_type}."/>
    <meta property="og:url" content="{wick_url}"/>
    <meta property="og:type" content="article"/>
    <meta property="og:image" content="https://windi-domain.com/verify-public/og-preview.png"/>

    <!-- Twitter Cards -->
    <meta name="twitter:card" content="summary"/>
    <meta name="twitter:title" content="✓ {title_safe} — WINDI Verified"/>
    <meta name="twitter:description" content="Document by {author_safe}. Verified on WINDI."/>

    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family: 'Bricolage Grotesque', system-ui, sans-serif; background: #FFFDF5; color: #1a1a1a; min-height: 100vh; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 40px 20px; }}
        header {{ border-bottom: 3px solid #C9A84C; padding-bottom: 20px; margin-bottom: 30px; }}
        .badge {{ display: inline-block; background: #C9A84C; color: #fff; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; margin-bottom: 12px; }}
        h1 {{ font-size: 28px; font-weight: 800; margin-bottom: 8px; }}
        .meta {{ color: #666; font-size: 14px; }}
        .meta span {{ margin-right: 16px; }}
        .card {{ background: #fff; border: 1px solid #e0e0e0; border-radius: 12px; padding: 24px; margin-bottom: 20px; }}
        .card h2 {{ font-size: 16px; font-weight: 700; margin-bottom: 12px; color: #C9A84C; }}
        .info-grid {{ display: grid; grid-template-columns: 120px 1fr; gap: 8px; font-size: 14px; }}
        .info-grid dt {{ color: #666; }}
        .info-grid dd {{ font-family: 'JetBrains Mono', monospace; word-break: break-all; }}
        .actions {{ display: flex; gap: 12px; flex-wrap: wrap; margin-top: 30px; }}
        .btn {{ display: inline-flex; align-items: center; gap: 8px; padding: 14px 24px; border-radius: 10px; font-size: 14px; font-weight: 700; text-decoration: none; transition: transform 0.2s; }}
        .btn:hover {{ transform: translateY(-2px); }}
        .btn-primary {{ background: #C9A84C; color: #fff; }}
        .btn-secondary {{ background: #fff; color: #1a1a1a; border: 2px solid #e0e0e0; }}
        footer {{ margin-top: 60px; padding-top: 20px; border-top: 1px solid #e0e0e0; text-align: center; color: #999; font-size: 12px; }}
        .dragon {{ font-size: 24px; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <span class="badge">🛡️ WICK Evidence Graph</span>
            <h1>{title_safe}</h1>
            <p class="meta">
                <span>👤 {author_safe}</span>
                <span>📄 {artifact_type}</span>
                {f'<span>📅 {created_at}</span>' if created_at else ''}
                <span>🔓 {visibility}</span>
            </p>
        </header>

        <div class="card">
            <h2>📋 Artifact Details</h2>
            <dl class="info-grid">
                <dt>ID:</dt>
                <dd>{artifact_id}</dd>
                <dt>Type:</dt>
                <dd>{artifact_type}</dd>
                <dt>Visibility:</dt>
                <dd>{visibility}</dd>
                <dt>Ledger Receipt:</dt>
                <dd>{artifact.get("ledger_receipt_id", "—")}</dd>
            </dl>
        </div>

        {f'<div class="card"><h2>🔗 Original Page</h2><p><a href="{page_url}" style="color:#C9A84C;">{page_url}</a></p></div>' if page_url else ''}

        <div class="actions">
            <a href="{verify_url}" class="btn btn-primary">🛡️ Verify on Ledger</a>
            {f'<a href="{page_url}" class="btn btn-secondary">📄 View Original</a>' if page_url else ''}
            <a href="/wick/feed" class="btn btn-secondary">📡 WICK Feed</a>
        </div>

        <footer>
            <p class="dragon">🐉</p>
            <p style="margin-top:8px;">AI processes. Human decides. WINDI guarantees.</p>
            <p style="margin-top:4px;">I12 — Web of Proofs · windi-domain.com</p>
        </footer>
    </div>
</body>
</html>'''

    return HTMLResponse(content=html, status_code=200)


@app.get("/verify-public/{doc_id}")
async def verify_direct_url(doc_id: str):
    """URL limpa: /verify-public/VR-BABEL-0001 — serve UI com OG tags dinâmicas."""
    index = os.path.join(WEB_DIR, "index.html")
    if not os.path.exists(index):
        return JSONResponse({"id": doc_id})

    # Skip SSR for static assets
    if doc_id in ["favicon.ico", "og-preview.png", "static"] or "." in doc_id:
        return FileResponse(index)

    # Fetch document metadata for OG tags
    meta = await get_document_metadata(doc_id)

    # Read and inject OG tags
    with open(index, "r", encoding="utf-8") as f:
        html = f.read()

    html = inject_og_tags(html, doc_id, meta)

    return HTMLResponse(content=html, status_code=200)

if __name__ == "__main__":
    import uvicorn
    log.info(f"WINDI Verify Public Agent v1.0.1 — port {PORT}")
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
