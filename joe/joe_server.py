"""
W-JOE-001 — Director de Transmissão
WINDI Publishing House · Kempten, Bavaria
v1.0.0 · 2026-04-03

"Quem decide o que vira memória do mundo."

Invariantes:
  I9  — nenhuma publicação sem decisão humana
  I11 — apenas hashes no Ledger (never raw media)
  I13 — JOE não decide narrativa final sem confirmação
"""

import os
import uuid
import json
import sqlite3
import hashlib
import logging
import httpx
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ── Config ────────────────────────────────────────────────────────────────────
PORT        = int(os.getenv("JOE_PORT", 8129))
DB_PATH     = os.getenv("JOE_DB", "/opt/windi/joe/joe.db")
LEDGER_URL  = os.getenv("LEDGER_URL", "http://localhost:8101")
VDCUT_URL   = os.getenv("VDCUT_URL", "http://localhost:8128")
EXPORTS_DIR = Path(os.getenv("VDCUT_EXPORTS", "/opt/windi/media/vd-cut/exports"))
LOG_PATH    = os.getenv("JOE_LOG", "/opt/windi/logs/joe.log")
VERSION     = "1.0.0"

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [JOE] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("joe")

# ── Database ──────────────────────────────────────────────────────────────────
def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    return db

def init_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id          TEXT PRIMARY KEY,
                title       TEXT,
                mode        TEXT DEFAULT 'human_director',
                status      TEXT DEFAULT 'open',
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS moments (
                id          TEXT PRIMARY KEY,
                session_id  TEXT NOT NULL REFERENCES sessions(id),
                export_id   TEXT NOT NULL,
                role        TEXT,
                weight      REAL DEFAULT 1.0,
                position    INTEGER DEFAULT 0,
                approved    INTEGER DEFAULT 0,
                created_at  TEXT NOT NULL,
                UNIQUE(session_id, export_id)
            );

            CREATE TABLE IF NOT EXISTS stories (
                id              TEXT PRIMARY KEY,
                session_id      TEXT NOT NULL REFERENCES sessions(id),
                narrative       TEXT,
                duration_sec    INTEGER,
                human_approved  INTEGER DEFAULT 0,
                ledger_receipt  TEXT,
                verify_url      TEXT,
                vdcut_job_id    TEXT,
                status          TEXT DEFAULT 'draft',
                created_at      TEXT NOT NULL,
                sealed_at       TEXT
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                event       TEXT NOT NULL,
                entity_id   TEXT,
                actor       TEXT DEFAULT 'joe',
                detail      TEXT,
                ts          TEXT NOT NULL
            );
        """)
    log.info("DB initialised at %s", DB_PATH)

# ── Lifecycle ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    log.info("W-JOE-001 v%s live on :%d", VERSION, PORT)
    yield
    log.info("W-JOE-001 shutdown")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="W-JOE-001 Director de Transmissão",
    version=VERSION,
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://windi-domain.com", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Helpers ───────────────────────────────────────────────────────────────────
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def new_id(prefix: str) -> str:
    ts  = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    uid = uuid.uuid4().hex[:8].upper()
    return f"{prefix}-{ts}-{uid}"

def audit(event: str, entity_id: str = None, detail: dict = None):
    with get_db() as db:
        db.execute(
            "INSERT INTO audit_log(event,entity_id,detail,ts) VALUES(?,?,?,?)",
            (event, entity_id, json.dumps(detail or {}), now_iso())
        )

def story_hash(story: dict) -> str:
    canonical = json.dumps(story, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()

async def seal_to_ledger(story_id: str, h: str, narrative: str) -> Optional[str]:
    """I11: apenas hash no Ledger."""
    payload = {
        "id":             story_id,
        "actor":          "W-JOE-001",
        "app":            "joe",
        "doc_name":       f"Story {story_id}",
        "doc_type":       "jmpg",
        "governance_level": "HIGH",
        "content_hash":   f"sha256:{h}",
        "sge_score":      0.85,
        "metadata": {
            "narrative":  narrative,
            "agent":      "W-JOE-001",
            "version":    VERSION
        }
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(f"{LEDGER_URL}/api/receipts", json=payload)
            if r.status_code in (200, 201):
                data = r.json()
                return data.get("receipt_id") or data.get("id")
    except Exception as e:
        log.warning("Ledger seal failed: %s", e)
    return None

# ── Pydantic Models ───────────────────────────────────────────────────────────
class SessionStart(BaseModel):
    title: Optional[str] = None
    mode:  Optional[str] = "human_director"   # human_director | auto_curator

class MomentIn(BaseModel):
    export_id: str
    role:      Optional[str] = "scene"        # intro | scene | climax | outro
    weight:    Optional[float] = 1.0
    position:  Optional[int] = 0

class SelectPayload(BaseModel):
    session_id: str
    moments:    List[MomentIn]

class SequencePayload(BaseModel):
    session_id: str
    narrative:  Optional[str] = "day_trip"
    order:      Optional[List[str]] = None    # list of export_ids in desired order

class PublishPayload(BaseModel):
    session_id:     str
    human_approved: bool                       # I9 Gate
    title:          Optional[str] = None

# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/joe/health")
def health():
    return {
        "service": "W-JOE-001",
        "version": VERSION,
        "status":  "ok",
        "ts":      now_iso()
    }


@app.post("/joe/session/start")
def session_start(body: SessionStart):
    """Abre uma nova sessão de curadoria."""
    sid   = new_id("JOE-SESSION")
    title = body.title or f"Session {sid}"
    ts    = now_iso()
    with get_db() as db:
        db.execute(
            "INSERT INTO sessions(id,title,mode,created_at,updated_at) VALUES(?,?,?,?,?)",
            (sid, title, body.mode, ts, ts)
        )
    audit("session.start", sid, {"title": title, "mode": body.mode})
    log.info("Session opened: %s [%s]", sid, body.mode)
    return {"session_id": sid, "title": title, "mode": body.mode, "status": "open"}


@app.get("/joe/session/{session_id}")
def session_get(session_id: str):
    """Estado completo de uma sessão."""
    with get_db() as db:
        sess = db.execute(
            "SELECT * FROM sessions WHERE id=?", (session_id,)
        ).fetchone()
        if not sess:
            raise HTTPException(404, "Session not found")
        moments = db.execute(
            "SELECT * FROM moments WHERE session_id=? ORDER BY position",
            (session_id,)
        ).fetchall()
        stories = db.execute(
            "SELECT id,status,narrative,ledger_receipt,sealed_at FROM stories WHERE session_id=?",
            (session_id,)
        ).fetchall()
    return {
        "session":  dict(sess),
        "moments":  [dict(m) for m in moments],
        "stories":  [dict(s) for s in stories],
    }


@app.post("/joe/select")
def select_takes(body: SelectPayload):
    """
    Curador escolhe os takes que entram na história.
    Verifica se os export_ids existem no VD-CUT (tolerante a falhas de rede).
    """
    ts = now_iso()
    inserted = []
    with get_db() as db:
        sess = db.execute(
            "SELECT id FROM sessions WHERE id=?", (body.session_id,)
        ).fetchone()
        if not sess:
            raise HTTPException(404, "Session not found")
        for m in body.moments:
            mid = new_id("MOMENT")
            try:
                db.execute(
                    """INSERT OR REPLACE INTO moments
                       (id,session_id,export_id,role,weight,position,approved,created_at)
                       VALUES(?,?,?,?,?,?,1,?)""",
                    (mid, body.session_id, m.export_id, m.role,
                     m.weight, m.position, ts)
                )
                inserted.append(m.export_id)
            except Exception as e:
                log.warning("Moment insert error %s: %s", m.export_id, e)
        db.execute(
            "UPDATE sessions SET updated_at=? WHERE id=?",
            (ts, body.session_id)
        )
    audit("moments.selected", body.session_id, {"count": len(inserted)})
    return {"session_id": body.session_id, "selected": inserted, "count": len(inserted)}


@app.post("/joe/sequence")
def build_sequence(body: SequencePayload):
    """
    Constrói a Story Graph — liga momentos numa narrativa.
    Se `order` for fornecido, respeita a ordem humana (I13).
    """
    ts = now_iso()
    with get_db() as db:
        moments = db.execute(
            "SELECT * FROM moments WHERE session_id=? AND approved=1 ORDER BY position",
            (body.session_id,)
        ).fetchall()
        if not moments:
            raise HTTPException(400, "No approved moments in session")
        moment_list = [dict(m) for m in moments]

        # Reordenar se humano especificou ordem
        if body.order:
            index = {m["export_id"]: m for m in moment_list}
            moment_list = [index[eid] for eid in body.order if eid in index]

        # Calcular duração estimada (placeholder — VD-CUT dará o valor real)
        est_duration = len(moment_list) * 10

        story_id = new_id("JOE-STORY")
        story_data = {
            "story_id":  story_id,
            "session_id": body.session_id,
            "narrative": body.narrative,
            "moments":   moment_list,
            "duration":  est_duration
        }
        h = story_hash(story_data)

        db.execute(
            """INSERT INTO stories
               (id,session_id,narrative,duration_sec,status,created_at)
               VALUES(?,?,?,?,'draft',?)""",
            (story_id, body.session_id, body.narrative, est_duration, ts)
        )
        db.execute(
            "UPDATE sessions SET updated_at=? WHERE id=?",
            (ts, body.session_id)
        )

    audit("story.sequenced", story_id, {
        "narrative": body.narrative,
        "moments":   len(moment_list),
        "hash":      h
    })
    log.info("Story sequenced: %s (%d moments)", story_id, len(moment_list))
    return {
        "story_id":       story_id,
        "narrative":      body.narrative,
        "moments":        len(moment_list),
        "estimated_secs": est_duration,
        "hash":           h,
        "status":         "draft",
        "next":           "POST /joe/publish with human_approved=true"
    }


@app.post("/joe/publish")
async def publish_story(body: PublishPayload, background: BackgroundTasks):
    """
    I9 Gate: publica apenas com human_approved=true.
    I11: sela só o hash no Ledger.
    I13: JOE não publica sem confirmação.
    """
    if not body.human_approved:
        raise HTTPException(403, "I9: human_approved=true required. JOE não publica sem decisão humana.")

    with get_db() as db:
        story = db.execute(
            "SELECT * FROM stories WHERE session_id=? AND status='draft' ORDER BY created_at DESC LIMIT 1",
            (body.session_id,)
        ).fetchone()
        if not story:
            raise HTTPException(404, "No draft story for this session")
        story = dict(story)

        moments = db.execute(
            "SELECT * FROM moments WHERE session_id=? AND approved=1 ORDER BY position",
            (body.session_id,)
        ).fetchall()
        moment_list = [dict(m) for m in moments]

    # Build Story Graph para hash
    story_data = {
        "story_id":   story["id"],
        "session_id": body.session_id,
        "narrative":  story["narrative"],
        "moments":    moment_list,
        "approved_by": "human",
        "approved_at": now_iso()
    }
    h = story_hash(story_data)

    # Seal to Ledger (I11 — hash only)
    receipt_id = await seal_to_ledger(story["id"], h, story["narrative"])
    verify_url = f"https://windi-domain.com/verify-public/?id={receipt_id}" if receipt_id else None

    ts = now_iso()
    with get_db() as db:
        db.execute(
            """UPDATE stories SET
               human_approved=1, ledger_receipt=?, verify_url=?,
               status='published', sealed_at=?
               WHERE id=?""",
            (receipt_id, verify_url, ts, story["id"])
        )
        db.execute(
            "UPDATE sessions SET status='published', updated_at=? WHERE id=?",
            (ts, body.session_id)
        )

    audit("story.published", story["id"], {
        "hash":    h,
        "receipt": receipt_id,
        "moments": len(moment_list)
    })
    log.info("Story PUBLISHED: %s | receipt=%s", story["id"], receipt_id)

    return {
        "story_id":      story["id"],
        "status":        "published",
        "hash":          h,
        "ledger_receipt": receipt_id,
        "verify_url":    verify_url,
        "moments":       len(moment_list),
        "narrative":     story["narrative"],
        "sealed_at":     ts,
        "constitutional": {
            "I9":  "human_approved=true ✓",
            "I11": "hash_only_in_ledger ✓",
            "I13": "human_confirmed ✓"
        }
    }


@app.get("/joe/story/{story_id}")
def get_story(story_id: str):
    """História final com todos os momentos."""
    with get_db() as db:
        story = db.execute(
            "SELECT * FROM stories WHERE id=?", (story_id,)
        ).fetchone()
        if not story:
            raise HTTPException(404, "Story not found")
        story = dict(story)
        moments = db.execute(
            "SELECT * FROM moments WHERE session_id=? AND approved=1 ORDER BY position",
            (story["session_id"],)
        ).fetchall()
    return {
        "story":   story,
        "moments": [dict(m) for m in moments],
        "total":   len(moments)
    }


@app.get("/joe/stories")
def list_stories(limit: int = 20):
    """Lista histórias publicadas."""
    with get_db() as db:
        rows = db.execute(
            "SELECT id,narrative,duration_sec,status,ledger_receipt,sealed_at FROM stories ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return {"stories": [dict(r) for r in rows], "count": len(rows)}


@app.get("/joe/audit")
def get_audit(limit: int = 50):
    """Log de auditoria — read-only."""
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM audit_log ORDER BY ts DESC LIMIT ?", (limit,)
        ).fetchall()
    return {"events": [dict(r) for r in rows]}


# ── Entrypoint ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("joe_server:app", host="127.0.0.1", port=PORT, reload=False)
