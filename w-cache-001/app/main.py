# ═══════════════════════════════════════════════
# W-CACHE-001 · MAIN
# Verifiable Cache Layer for Regulated Systems
# Port: 8160
# ═══════════════════════════════════════════════

import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from api.routes import router
from db.session import init_db
from core.config import SERVICE_PORT, SERVICE_HOST

# ──────────────────────────────────────────────
# APP SETUP
# ──────────────────────────────────────────────

app = FastAPI(
    title="W-CACHE-001",
    description="Verifiable Cache Layer for Regulated Systems",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/cache/v1")


# ──────────────────────────────────────────────
# ROOT ENDPOINTS
# ──────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "service": "W-CACHE-001",
        "version": "1.0.0",
        "description": "Verifiable Cache Layer",
        "api": "/api/cache/v1",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    return {"ok": True, "service": "W-CACHE-001"}


@app.get("/noir")
def noir_dashboard():
    """NOIR Control Dashboard - System consciousness interface"""
    return FileResponse("/opt/windi/w-cache-001/app/static/noir.html")


# Mount static files
app.mount("/static", StaticFiles(directory="/opt/windi/w-cache-001/app/static"), name="static")


# ──────────────────────────────────────────────
# STARTUP
# ──────────────────────────────────────────────

@app.on_event("startup")
def startup():
    """Initialize database on startup"""
    # Create data directory
    os.makedirs("/opt/windi/w-cache-001/data", exist_ok=True)

    # Initialize database tables
    init_db()
    print("✅ W-CACHE-001 database initialized")


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=SERVICE_HOST,
        port=SERVICE_PORT,
        reload=False,
        log_level="info"
    )
