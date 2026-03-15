"""
WINDI Pioneer Program Landing — Application Server
===================================================
Serves the Pioneer Program landing page and handles applications.

Port: 8120
Endpoints:
  GET  /pioneer/           → Landing page
  POST /api/pioneer/apply  → Submit application
  GET  /api/pioneer/stats  → Application stats
"""

import os
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import uvicorn

# ═══════════════════════════════════════════════════════════════════════════════
# Config
# ═══════════════════════════════════════════════════════════════════════════════

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "applications.db"
PORT = int(os.environ.get("PIONEER_PORT", 8120))

# ═══════════════════════════════════════════════════════════════════════════════
# Database
# ═══════════════════════════════════════════════════════════════════════════════

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            profession TEXT NOT NULL,
            location TEXT NOT NULL,
            filter_answer TEXT NOT NULL,
            linkedin TEXT,
            status TEXT DEFAULT 'pending',
            reviewed_at TEXT,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ═══════════════════════════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════════════════════════

class PioneerApplication(BaseModel):
    name: str
    email: str
    profession: str
    location: str
    filter_answer: str
    linkedin: str = None

# ═══════════════════════════════════════════════════════════════════════════════
# App
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="WINDI Pioneer Program",
    description="Pioneer Program application server",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)

# ═══════════════════════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/pioneer/", response_class=HTMLResponse)
@app.get("/pioneer", response_class=HTMLResponse)
async def landing_page():
    """Serve the Pioneer Program landing page."""
    html_path = APP_DIR / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(), status_code=200)
    return HTMLResponse(content="<h1>Coming Soon</h1>", status_code=200)


@app.get("/pioneer/manifesto/", response_class=HTMLResponse)
@app.get("/pioneer/manifesto", response_class=HTMLResponse)
async def manifesto_page():
    """Serve the Pioneer Manifesto — O Fim da Internet de Plástico."""
    html_path = APP_DIR / "manifesto.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(), status_code=200)
    return HTMLResponse(content="<h1>Manifesto Coming Soon</h1>", status_code=200)


@app.post("/api/pioneer/apply")
async def submit_application(application: PioneerApplication):
    """Submit a Pioneer Program application."""
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO applications (created_at, name, email, profession, location, filter_answer, linkedin)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            application.name,
            application.email,
            application.profession,
            application.location,
            application.filter_answer,
            application.linkedin
        ))
        conn.commit()

        # Log to file for backup
        log_path = APP_DIR / "applications.log"
        with open(log_path, "a") as f:
            f.write(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "name": application.name,
                "email": application.email,
                "profession": application.profession,
                "location": application.location,
                "filter_answer": application.filter_answer[:200] + "..." if len(application.filter_answer) > 200 else application.filter_answer,
                "linkedin": application.linkedin
            }) + "\n")

        return JSONResponse({
            "ok": True,
            "message": "Application received. We'll review and respond within 48 hours."
        })

    except sqlite3.IntegrityError:
        return JSONResponse({
            "ok": False,
            "error": "This email has already submitted an application."
        }, status_code=400)
    finally:
        conn.close()


@app.get("/api/pioneer/stats")
async def application_stats():
    """Get application statistics."""
    conn = get_db()
    try:
        total = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM applications WHERE status = 'pending'").fetchone()[0]
        approved = conn.execute("SELECT COUNT(*) FROM applications WHERE status = 'approved'").fetchone()[0]

        return JSONResponse({
            "ok": True,
            "total_applications": total,
            "pending": pending,
            "approved": approved
        })
    finally:
        conn.close()


@app.get("/api/pioneer/applications")
async def list_applications(status: str = None):
    """List applications (admin endpoint)."""
    conn = get_db()
    try:
        if status:
            rows = conn.execute(
                "SELECT * FROM applications WHERE status = ? ORDER BY created_at DESC",
                (status,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM applications ORDER BY created_at DESC"
            ).fetchall()

        return JSONResponse({
            "ok": True,
            "applications": [dict(row) for row in rows]
        })
    finally:
        conn.close()


@app.get("/health")
async def health():
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "service": "WINDI Pioneer Program",
        "port": PORT,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║     WINDI Pioneer Program — Application Server               ║
║     Port: {PORT}                                                ║
║     "AI processes. Human decides. WINDI guarantees."         ║
╚══════════════════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
