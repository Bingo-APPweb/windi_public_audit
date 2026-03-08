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
from fastapi.responses import FileResponse, JSONResponse
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


@app.get("/verify-public/{doc_id}")
async def verify_direct_url(doc_id: str):
    """URL limpa: /verify-public/VR-BABEL-0001 — serve UI com auto-verify."""
    index = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return JSONResponse({"id": doc_id})

if __name__ == "__main__":
    import uvicorn
    log.info(f"WINDI Verify Public Agent v1.0.1 — port {PORT}")
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
