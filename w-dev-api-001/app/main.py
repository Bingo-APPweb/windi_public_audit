"""
W-DEV-API-001 — WINDI Developer API v1
Port: 8200
Invariants: I9 (human confirmation required for seals)
"""
import os
import time
import uuid
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import health, auth, artifacts, seals, receipts, verify, keys
from app.db.session import init_db

# ── App ───────────────────────────────────────────────────
app = FastAPI(
    title="WINDI Developer API",
    version="1.0.0",
    description="seal · ledger · verify · distribute",
    docs_url="/v1/docs",
    redoc_url="/v1/redoc",
    openapi_url="/v1/openapi.json",
    root_path="/dev-api",
)

# ── CORS ──────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://windi-domain.com",
        "http://localhost:3000",
        "http://localhost:8200"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request ID Middleware ─────────────────────────────────
@app.middleware("http")
async def inject_request_id(request: Request, call_next):
    request_id = request.headers.get("X-WINDI-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
    request.state.request_id = request_id
    request.state.started_at = time.time()

    response = await call_next(request)

    response.headers["X-WINDI-Request-ID"] = request_id
    elapsed = time.time() - request.state.started_at
    response.headers["X-Response-Time"] = f"{elapsed*1000:.2f}ms"

    return response


# ── Routers ───────────────────────────────────────────────
app.include_router(health.router, prefix="/v1")
app.include_router(auth.router, prefix="/v1")
app.include_router(artifacts.router, prefix="/v1")
app.include_router(seals.router, prefix="/v1")
app.include_router(receipts.router, prefix="/v1")
app.include_router(verify.router, prefix="/v1")
app.include_router(keys.router, prefix="/v1")

# ── Static Pages ──────────────────────────────────────────
static_dir = "/opt/windi/w-dev-api-001/static"
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")


# ── Root ──────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "service": "W-DEV-API-001",
        "version": "1.0.0",
        "docs": "/v1/docs",
        "health": "/v1/health",
        "landing": "/static/index.html"
    }


# ── Startup ───────────────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    init_db()
    print(f"[W-DEV-API-001] 🟢 LIVE on :8200 — {datetime.now(timezone.utc).isoformat()}")


# ── Run ───────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8200, reload=False)
