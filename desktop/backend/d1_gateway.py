#!/usr/bin/env python3
"""
WINDI D1 — API Gateway (FastAPI)
Bridges D1 Editor Core → Forensic Ledger (:8101)
Port: 8100

Principle: "AI processes. Human decides. WINDI guarantees."
"""

import os
import json
import hashlib
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional

# === Configuration ===
PORT = int(os.getenv("PORT", "8100"))
LEDGER_URL = os.getenv("LEDGER_URL", "http://localhost:8101")
DATA_DIR = Path(os.getenv("DATA_DIR", "/opt/windi/data"))
STATIC_DIR = Path(os.getenv("STATIC_DIR", "/opt/windi/desktop/frontend/dist"))
LOG_DIR = Path(os.getenv("LOG_DIR", "/opt/windi/logs"))

# Local document store (server-side sync backup)
DB_PATH = DATA_DIR / "d1_documents.db"

# === Database Setup ===
def init_db():
    """Initialize SQLite for server-side document backup + governance cache."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            doc_id TEXT PRIMARY KEY,
            title TEXT DEFAULT 'Untitled',
            content_hash TEXT,
            content_json TEXT,
            owner TEXT DEFAULT 'human-operator',
            created_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS governance_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id TEXT NOT NULL,
            action TEXT NOT NULL,
            integrity_hash TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            user_id TEXT DEFAULT 'human-operator',
            metadata_json TEXT,
            ledger_entry_id TEXT,
            ledger_synced INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_gov_doc ON governance_cache(doc_id);
        CREATE INDEX IF NOT EXISTS idx_gov_unsynced ON governance_cache(ledger_synced) WHERE ledger_synced = 0;
    """)
    conn.close()

# === Pydantic Models ===
class ReceiptRequest(BaseModel):
    doc_id: str
    action: str
    integrity_hash: str
    timestamp: str
    user_id: str = "human-operator"
    metadata: Optional[dict] = None

class DocumentSave(BaseModel):
    doc_id: str
    title: str = "Untitled"
    content: dict
    owner: str = "human-operator"

# === App ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print(f"[D1-GW] WINDI D1 Gateway starting on :{PORT}")
    print(f"[D1-GW] Ledger: {LEDGER_URL}")
    print(f"[D1-GW] Database: {DB_PATH}")
    yield
    print("[D1-GW] Shutting down.")

app = FastAPI(
    title="WINDI D1 — API Gateway",
    version="1.0.0-foundation",
    lifespan=lifespan,
)

# === Health ===
@app.get("/health")
async def health():
    ledger_ok = False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{LEDGER_URL}/health")
            ledger_ok = r.status_code == 200
    except Exception:
        pass
    return {
        "service": "windi-d1-gateway",
        "version": "1.0.0-foundation",
        "status": "operational",
        "ledger_connected": ledger_ok,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "principle": "AI processes. Human decides. WINDI guarantees.",
    }

# === B1: Governance Bridge — Receipts ===
@app.post("/api/ledger/receipts")
async def create_receipt(req: ReceiptRequest):
    """
    B1 Governance Bridge: receive Virtue Receipt from D1,
    cache locally, forward to Forensic Ledger (:8101)
    """
    metadata_json = json.dumps(req.metadata or {})
    ledger_entry_id = None
    ledger_synced = 0

    # Forward to Forensic Ledger
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            import uuid as _uuid
            receipt_id = f"VR-D1-{_uuid.uuid4().hex[:12]}"
            payload = {
                "id": receipt_id,
                "actor": req.user_id or "human-operator",
                "app": "desktop-d1",
                "doc_name": (req.metadata or {}).get("title", "Untitled Document"),
                "doc_type": "doc",
                "content_hash": req.integrity_hash,
                "governance_level": "LOW",
                "sge_score": 0.0,
                "status": "sealed",
                "tags": [req.action.lower(), "d1-foundation"],
                "flags": [],
                "metadata": {"d1_doc_id": req.doc_id, "d1_action": req.action, "d1_timestamp": req.timestamp, **(req.metadata or {})},
            }
            r = await client.post(f"{LEDGER_URL}/api/receipts", json=payload)
            if r.status_code in (200, 201):
                data = r.json()
                ledger_entry_id = data.get("entry_id") or data.get("id")
                ledger_synced = 1
                print(f"[B1] Receipt registered → Ledger entry: {ledger_entry_id}")
            else:
                print(f"[B1] Ledger returned {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"[B1] Ledger unreachable: {e} — caching locally")

    # Cache locally (resilience: works even when Ledger is down)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        INSERT INTO governance_cache (doc_id, action, integrity_hash, timestamp, user_id, metadata_json, ledger_entry_id, ledger_synced)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (req.doc_id, req.action, req.integrity_hash, req.timestamp, req.user_id, metadata_json, ledger_entry_id, ledger_synced))
    conn.commit()
    conn.close()

    return {
        "status": "registered" if ledger_synced else "cached",
        "entry_id": ledger_entry_id,
        "doc_id": req.doc_id,
        "action": req.action,
        "integrity_hash": req.integrity_hash,
    }

# === B1: Query receipts for a document ===
@app.get("/api/ledger/receipts")
async def get_receipts(doc_id: str = None, latest: bool = False):
    """Query governance receipts, optionally from Ledger."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    if doc_id:
        if latest:
            row = conn.execute(
                "SELECT * FROM governance_cache WHERE doc_id = ? ORDER BY timestamp DESC LIMIT 1",
                (doc_id,)
            ).fetchone()
            conn.close()
            if row:
                return dict(row)
            raise HTTPException(404, "No receipts found for this document")
        else:
            rows = conn.execute(
                "SELECT * FROM governance_cache WHERE doc_id = ? ORDER BY timestamp DESC",
                (doc_id,)
            ).fetchall()
            conn.close()
            return [dict(r) for r in rows]
    else:
        rows = conn.execute(
            "SELECT * FROM governance_cache ORDER BY timestamp DESC LIMIT 50"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

# === Document server-side sync (backup) ===
@app.post("/api/documents/sync")
async def sync_document(doc: DocumentSave):
    """Sync document from D1 (client-side) to server-side backup."""
    content_json = json.dumps(doc.content, separators=(',', ':'))
    content_hash = hashlib.sha256(content_json.encode()).hexdigest()
    now = datetime.now(timezone.utc).isoformat()

    conn = sqlite3.connect(str(DB_PATH))
    existing = conn.execute("SELECT doc_id FROM documents WHERE doc_id = ?", (doc.doc_id,)).fetchone()

    if existing:
        conn.execute("""
            UPDATE documents SET title=?, content_hash=?, content_json=?, updated_at=?
            WHERE doc_id=?
        """, (doc.title, content_hash, content_json, now, doc.doc_id))
    else:
        conn.execute("""
            INSERT INTO documents (doc_id, title, content_hash, content_json, owner, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (doc.doc_id, doc.title, content_hash, content_json, doc.owner, now, now))

    conn.commit()
    conn.close()
    return {"status": "synced", "doc_id": doc.doc_id, "hash": content_hash}

# === Reconciliation endpoint (for Witness stress tests) ===
@app.get("/api/reconcile")
async def reconcile(doc_id: str = None):
    """
    Reconciliation endpoint — compares local cache vs Ledger.
    Used by Witness 'Linhagem de Ferro' stress tests.
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    if doc_id:
        unsynced = conn.execute(
            "SELECT * FROM governance_cache WHERE doc_id = ? AND ledger_synced = 0",
            (doc_id,)
        ).fetchall()
    else:
        unsynced = conn.execute(
            "SELECT * FROM governance_cache WHERE ledger_synced = 0"
        ).fetchall()
    conn.close()

    # Attempt to sync unsynced receipts
    synced_count = 0
    failed = []
    async with httpx.AsyncClient(timeout=5.0) as client:
        for row in unsynced:
            try:
                payload = {
                    "doc_id": row["doc_id"],
                    "action": row["action"],
                    "integrity_hash": row["integrity_hash"],
                    "timestamp": row["timestamp"],
                    "user_id": row["user_id"],
                    "metadata": json.loads(row["metadata_json"] or "{}"),
                }
                r = await client.post(f"{LEDGER_URL}/api/receipts", json=payload)
                if r.status_code in (200, 201):
                    conn2 = sqlite3.connect(str(DB_PATH))
                    conn2.execute("UPDATE governance_cache SET ledger_synced = 1 WHERE id = ?", (row["id"],))
                    conn2.commit()
                    conn2.close()
                    synced_count += 1
                else:
                    failed.append(row["id"])
            except Exception:
                failed.append(row["id"])

    return {
        "status": "reconciliation_complete",
        "total_unsynced": len(unsynced),
        "newly_synced": synced_count,
        "still_pending": len(failed),
        "failed_ids": failed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

# === Unsynced receipts count (for Sentinel monitoring) ===
@app.get("/api/status")
async def api_status():
    conn = sqlite3.connect(str(DB_PATH))
    total = conn.execute("SELECT COUNT(*) FROM governance_cache").fetchone()[0]
    unsynced = conn.execute("SELECT COUNT(*) FROM governance_cache WHERE ledger_synced = 0").fetchone()[0]
    docs = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    conn.close()
    return {
        "service": "windi-d1-gateway",
        "receipts_total": total,
        "receipts_unsynced": unsynced,
        "documents_backed_up": docs,
        "health": "degraded" if unsynced > 10 else "healthy",
    }

# === Serve frontend static files (production) ===
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
else:
    @app.get("/")
    async def root():
        return {"message": "WINDI D1 Gateway — frontend not built yet. Run: cd frontend && npm run build"}


# ─── M3.2: Export Endpoint ───
@app.post("/api/export")
async def export_document(request: Request):
    """Export document to PDF, DOCX, MD, TXT, HTML."""
    import tempfile
    from fastapi.responses import FileResponse
    
    data = await request.json()
    fmt = data.get("format", "html")
    html = data.get("html", "")
    title = data.get("title", "Untitled")
    
    # Sanitize filename
    safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip()[:50] or "document"
    
    if fmt == "html":
        tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8")
        tmp.write(html)
        tmp.close()
        return FileResponse(tmp.name, filename=f"{safe_title}.html", media_type="text/html")
    
    elif fmt == "txt":
        import re
        text = re.sub(r"<[^>]+>", "", html)
        text = re.sub(r"\s+", " ", text).strip()
        tmp = tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8")
        tmp.write(text)
        tmp.close()
        return FileResponse(tmp.name, filename=f"{safe_title}.txt", media_type="text/plain")
    
    elif fmt == "md":
        # Use pandoc if available
        import subprocess as sp
        tmp_html = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8")
        tmp_html.write(html)
        tmp_html.close()
        tmp_md = tempfile.mktemp(suffix=".md")
        
        try:
            sp.run(["pandoc", "-f", "html", "-t", "markdown", "-o", tmp_md, tmp_html.name], 
                   check=True, timeout=10)
            return FileResponse(tmp_md, filename=f"{safe_title}.md", media_type="text/markdown")
        except Exception:
            # Fallback: basic strip
            import re
            text = re.sub(r"<[^>]+>", "", html)
            tmp_f = tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w", encoding="utf-8")
            tmp_f.write(text)
            tmp_f.close()
            return FileResponse(tmp_f.name, filename=f"{safe_title}.md", media_type="text/markdown")
    
    elif fmt == "pdf":
        import subprocess as sp
        tmp_html = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8")
        tmp_html.write(html)
        tmp_html.close()
        tmp_pdf = tempfile.mktemp(suffix=".pdf")
        
        try:
            # Try wkhtmltopdf first
            sp.run(["wkhtmltopdf", "--quiet", "--page-size", "A4", 
                    "--margin-top", "15mm", "--margin-bottom", "15mm",
                    "--margin-left", "20mm", "--margin-right", "20mm",
                    tmp_html.name, tmp_pdf], check=True, timeout=30)
            return FileResponse(tmp_pdf, filename=f"{safe_title}.pdf", media_type="application/pdf")
        except Exception:
            try:
                # Fallback: pandoc
                sp.run(["pandoc", "-f", "html", "-o", tmp_pdf, tmp_html.name],
                       check=True, timeout=30)
                return FileResponse(tmp_pdf, filename=f"{safe_title}.pdf", media_type="application/pdf")
            except Exception:
                raise HTTPException(status_code=500, detail="PDF export requires wkhtmltopdf or pandoc")
    
    elif fmt == "docx":
        import subprocess as sp
        tmp_html = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8")
        tmp_html.write(html)
        tmp_html.close()
        tmp_docx = tempfile.mktemp(suffix=".docx")
        
        try:
            sp.run(["pandoc", "-f", "html", "-o", tmp_docx, tmp_html.name],
                   check=True, timeout=30)
            return FileResponse(tmp_docx, filename=f"{safe_title}.docx", 
                              media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        except Exception:
            raise HTTPException(status_code=500, detail="DOCX export requires pandoc")
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown format: {fmt}")



# === Run ===

@app.get("/api/sentinel/health")
async def sentinel_health():
    """Sentinel LAW health proxy for frontend StatusIndicator"""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get("http://localhost:8102/health")
            return r.json()
    except Exception:
        return {"status": "ok", "service": "sentinel-law", "cycles": 0, "message": "sentinel not reachable, degraded mode"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
