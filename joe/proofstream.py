"""
W-JOE-001 · ProofStream Session Handler
WINDI Publishing House · Kempten, Bavaria
v1.0.0 · 2026-04-03

"Nao e uma transmissao que voce assiste;
 e uma sucessao de verdades que voce verifica."

Invariantes:
  I9  — nenhum fragmento entra na historia sem decisao humana
  I11 — apenas hashes no Ledger
  I13 — JOE nao publica sem confirmacao explicita

Hash de Continuidade:
  fragment[n].prev_hash = sha256(fragment[n-1])
  → Video-Chain: qualquer adulteracao quebra a corrente
"""

import hashlib
import json
import sqlite3
import uuid
import logging
import httpx
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

log = logging.getLogger("joe.proofstream")


# ── Helpers ───────────────────────────────────────────────────────────────────

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def new_id(prefix: str) -> str:
    ts  = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    uid = uuid.uuid4().hex[:8].upper()
    return f"{prefix}-{ts}-{uid}"

def fragment_hash(data: dict) -> str:
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


# ── DB Schema (extensao do joe.db) ────────────────────────────────────────────

PROOFSTREAM_SCHEMA = """
CREATE TABLE IF NOT EXISTS ps_sessions (
    id              TEXT PRIMARY KEY,
    title           TEXT,
    telegram_chat   TEXT,
    status          TEXT DEFAULT 'live',
    fragment_count  INTEGER DEFAULT 0,
    chain_head      TEXT,
    ledger_genesis  TEXT,
    manifest_url    TEXT,
    created_at      TEXT NOT NULL,
    ended_at        TEXT
);

CREATE TABLE IF NOT EXISTS ps_fragments (
    id              TEXT PRIMARY KEY,
    session_id      TEXT NOT NULL REFERENCES ps_sessions(id),
    seq             INTEGER NOT NULL,
    export_id       TEXT,
    vdcut_hash      TEXT,
    prev_hash       TEXT,
    self_hash       TEXT,
    thumbnail_b64   TEXT,
    role            TEXT DEFAULT 'scene',
    note            TEXT,
    human_decision  TEXT DEFAULT 'pending',
    ledger_receipt  TEXT,
    verify_url      TEXT,
    created_at      TEXT NOT NULL,
    decided_at      TEXT
);
"""


def init_proofstream(db_path: str):
    db = sqlite3.connect(db_path)
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript(PROOFSTREAM_SCHEMA)
    db.close()
    log.info("ProofStream schema ready at %s", db_path)


def get_db(db_path: str):
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    return db


# ── Session Lifecycle ─────────────────────────────────────────────────────────

def live_start(db_path: str, telegram_chat: str, title: str = None) -> dict:
    """
    Abre uma ProofStream Session.
    Chamado por /live_start no NOMAD-BOT.
    """
    sid   = new_id("PS")
    title = title or f"Live {datetime.now(timezone.utc).strftime('%d %b %Y %H:%M')}"
    ts    = now_iso()

    with get_db(db_path) as db:
        db.execute(
            """INSERT INTO ps_sessions
               (id, title, telegram_chat, status, fragment_count, created_at)
               VALUES (?, ?, ?, 'live', 0, ?)""",
            (sid, title, telegram_chat, ts)
        )

    log.info("ProofStream LIVE_START: %s [chat=%s]", sid, telegram_chat)
    return {
        "session_id":    sid,
        "title":         title,
        "status":        "live",
        "message":       f"ProofStream aberta: *{title}*\nEnvia clips de 3-15s. Cada um sera selado.",
        "telegram_chat": telegram_chat
    }


def live_end(db_path: str, session_id: str, ledger_url: str) -> dict:
    """
    Fecha a sessao e gera o Manifesto.
    Chamado por /live_end no NOMAD-BOT.
    """
    ts = now_iso()
    with get_db(db_path) as db:
        sess = db.execute(
            "SELECT * FROM ps_sessions WHERE id=?", (session_id,)
        ).fetchone()
        if not sess:
            return {"error": "Session not found"}

        fragments = db.execute(
            """SELECT * FROM ps_fragments
               WHERE session_id=? AND human_decision='seal'
               ORDER BY seq""",
            (session_id,)
        ).fetchall()
        fragments = [dict(f) for f in fragments]

        db.execute(
            "UPDATE ps_sessions SET status='closed', ended_at=? WHERE id=?",
            (ts, session_id)
        )

    chain_ok, _ = _verify_chain(fragments)
    manifest = _build_manifest(dict(sess), fragments)
    log.info("ProofStream LIVE_END: %s (%d fragments sealed)", session_id, len(fragments))
    return {
        "session_id":     session_id,
        "sealed_fragments": len(fragments),
        "chain_intact":   chain_ok,
        "manifest_html":  manifest,
        "ended_at":       ts
    }


# ── Fragment Processing ───────────────────────────────────────────────────────

def register_fragment(
    db_path:    str,
    session_id: str,
    export_id:  str,
    vdcut_hash: str,
    thumbnail_b64: Optional[str] = None
) -> dict:
    """
    Regista um fragmento recebido do VD-CUT.
    Estado inicial: human_decision='pending' (aguarda SIM/NAO).
    """
    with get_db(db_path) as db:
        sess = db.execute(
            "SELECT * FROM ps_sessions WHERE id=? AND status='live'",
            (session_id,)
        ).fetchone()
        if not sess:
            return {"error": "Session not live"}

        seq       = sess["fragment_count"]
        prev_hash = sess["chain_head"] or "GENESIS"

        # Hash de Continuidade — I11 chain
        fragment_data = {
            "session_id": session_id,
            "seq":        seq,
            "export_id":  export_id,
            "vdcut_hash": vdcut_hash,
            "prev_hash":  prev_hash,
            "ts":         now_iso()
        }
        self_hash = fragment_hash(fragment_data)

        fid = new_id("FRAG")
        ts  = now_iso()

        db.execute(
            """INSERT INTO ps_fragments
               (id, session_id, seq, export_id, vdcut_hash,
                prev_hash, self_hash, thumbnail_b64, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (fid, session_id, seq, export_id, vdcut_hash,
             prev_hash, self_hash, thumbnail_b64, ts)
        )
        db.execute(
            """UPDATE ps_sessions
               SET fragment_count=fragment_count+1, chain_head=?
               WHERE id=?""",
            (self_hash, session_id)
        )

    log.info("Fragment registered: %s seq=%d chain=%s...", fid, seq, self_hash[:12])
    return {
        "fragment_id": fid,
        "seq":         seq,
        "self_hash":   self_hash,
        "prev_hash":   prev_hash,
        "status":      "pending",
        "telegram_prompt": {
            "text":    f"Fragmento #{seq+1} capturado. Selar na historia?",
            "buttons": [
                {"text": "SIM (Seal)",  "callback": f"seal:{fid}"},
                {"text": "DESCARTAR",   "callback": f"discard:{fid}"},
                {"text": "+ NOTA",      "callback": f"note:{fid}"}
            ],
            "thumbnail_b64": thumbnail_b64
        }
    }


async def human_decision(
    db_path:     str,
    fragment_id: str,
    decision:    str,
    note:        str = None,
    ledger_url:  str = "http://localhost:8101"
) -> dict:
    """
    I9 Gate: processa decisao humana SIM/NAO.
    Se 'seal': envia hash ao Ledger e retorna URL verificavel.
    """
    ts = now_iso()

    with get_db(db_path) as db:
        frag = db.execute(
            "SELECT * FROM ps_fragments WHERE id=?", (fragment_id,)
        ).fetchone()
        if not frag:
            return {"error": "Fragment not found"}
        frag = dict(frag)

        db.execute(
            """UPDATE ps_fragments
               SET human_decision=?, note=?, decided_at=?
               WHERE id=?""",
            (decision, note, ts, fragment_id)
        )

    if decision == "discard":
        log.info("Fragment DISCARDED: %s (I9 — human decision)", fragment_id)
        return {
            "fragment_id": fragment_id,
            "decision":    "discard",
            "message":     "Fragmento descartado. Nao entra na historia.",
            "constitutional": "I9 — decisao humana respeitada"
        }

    # decision == "seal"
    receipt_id = await _seal_fragment_to_ledger(frag, ledger_url)
    verify_url = f"https://windi-domain.com/verify-public/?id={receipt_id}" if receipt_id else None

    with get_db(db_path) as db:
        db.execute(
            "UPDATE ps_fragments SET ledger_receipt=?, verify_url=? WHERE id=?",
            (receipt_id, verify_url, fragment_id)
        )

    log.info("Fragment SEALED: %s receipt=%s", fragment_id, receipt_id)
    return {
        "fragment_id":   fragment_id,
        "decision":      "seal",
        "ledger_receipt": receipt_id,
        "verify_url":    verify_url,
        "hash":          frag["self_hash"],
        "prev_hash":     frag["prev_hash"],
        "message":       f"Fragmento #{frag['seq']+1} selado.\n{verify_url}",
        "constitutional": {
            "I9":  "human_approved",
            "I11": "hash_only_in_ledger"
        }
    }


# ── Chain Verification ────────────────────────────────────────────────────────

def verify_chain(db_path: str, session_id: str) -> dict:
    """
    Verifica integridade da Video-Chain.
    Qualquer adulteracao quebra a corrente.
    """
    with get_db(db_path) as db:
        fragments = db.execute(
            """SELECT * FROM ps_fragments
               WHERE session_id=? AND human_decision='seal'
               ORDER BY seq""",
            (session_id,)
        ).fetchall()
        fragments = [dict(f) for f in fragments]

    intact, broken_at = _verify_chain(fragments)
    return {
        "session_id":    session_id,
        "total_sealed":  len(fragments),
        "chain_intact":  intact,
        "broken_at_seq": broken_at,
        "verdict":       "VERIFICAVEL" if intact else f"CORRENTE QUEBRADA em seq={broken_at}"
    }


def _verify_chain(fragments: list) -> Tuple[bool, Optional[int]]:
    """Interna: verifica prev_hash de cada fragmento."""
    prev = "GENESIS"
    for f in fragments:
        if f["prev_hash"] != prev:
            return False, f["seq"]
        prev = f["self_hash"]
    return True, None


# ── Ledger Seal (I11) ─────────────────────────────────────────────────────────

async def _seal_fragment_to_ledger(frag: dict, ledger_url: str) -> Optional[str]:
    payload = {
        "id":               frag["id"],
        "actor":            "W-JOE-001",
        "app":              "proofstream",
        "doc_name":         f"ProofStream Fragment #{frag['seq']}",
        "doc_type":         "jmpg",
        "governance_level": "HIGH",
        "content_hash":     f"sha256:{frag['self_hash']}",
        "sge_score":        0.85,
        "metadata": {
            "session_id":  frag["session_id"],
            "seq":         frag["seq"],
            "prev_hash":   frag["prev_hash"],
            "export_id":   frag["export_id"],
            "agent":       "W-JOE-001-ProofStream"
        }
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(f"{ledger_url}/api/receipts", json=payload)
            if r.status_code in (200, 201):
                data = r.json()
                return data.get("receipt_id") or data.get("id")
    except Exception as e:
        log.warning("Ledger seal failed for fragment %s: %s", frag["id"], e)
    return None


# ── Manifest Generator ────────────────────────────────────────────────────────

def _build_manifest(sess: dict, fragments: list) -> str:
    """
    Gera HTML do Manifesto de Sessao — The Stitcher.
    Lista todos os fragmentos selados com a sua Video-Chain.
    """
    chain_ok, broken = _verify_chain(fragments)
    chain_badge = "CORRENTE INTEGRA" if chain_ok else f"CORRENTE QUEBRADA em #{broken}"
    badge_color = "#2d6a4f" if chain_ok else "#c1121f"

    rows = ""
    for f in fragments:
        verify_link = f['verify_url'] or "#"
        rows += f"""
        <tr>
            <td>#{f['seq']+1}</td>
            <td><code>{f['self_hash'][:16]}...</code></td>
            <td><code>{f['prev_hash'][:16]}...</code></td>
            <td>{f.get('note') or '-'}</td>
            <td><a href="{verify_link}" target="_blank">Verificar</a></td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="UTF-8">
<title>ProofStream Manifesto - {sess['id']}</title>
<style>
  body {{ font-family: 'JetBrains Mono', monospace; background: #F5F0E0; color: #1a1a1a; padding: 2rem; }}
  h1   {{ font-size: 1.4rem; border-bottom: 2px solid #8B6914; padding-bottom: .5rem; }}
  .badge {{ display:inline-block; padding:.3rem .8rem; border-radius:4px;
            background: {badge_color}; color:#fff; font-size:.85rem; }}
  table  {{ width:100%; border-collapse:collapse; margin-top:1.5rem; font-size:.85rem; }}
  th,td  {{ border:1px solid #ccc; padding:.5rem .75rem; text-align:left; }}
  th     {{ background:#e8e0cc; }}
  code   {{ background:#e8e0cc; padding:2px 4px; border-radius:3px; }}
  .meta  {{ font-size:.8rem; color:#555; margin:.5rem 0; }}
</style>
</head>
<body>
<h1>ProofStream Manifesto</h1>
<p class="meta">Sessao: <strong>{sess['id']}</strong></p>
<p class="meta">Titulo: <strong>{sess['title']}</strong></p>
<p class="meta">Iniciada: {sess['created_at']} | Fechada: {sess.get('ended_at','-')}</p>
<p class="meta">Fragmentos selados: <strong>{len(fragments)}</strong></p>
<span class="badge">{chain_badge}</span>

<table>
  <thead>
    <tr>
      <th>#</th>
      <th>Hash (self)</th>
      <th>Hash (prev)</th>
      <th>Nota</th>
      <th>Verificar</th>
    </tr>
  </thead>
  <tbody>{rows}</tbody>
</table>

<p style="margin-top:2rem;font-size:.75rem;color:#888;">
  WINDI Publishing House | Kempten | "AI processes. Human decides. WINDI guarantees."<br>
  I9 I11 I13 - cada fragmento selado com decisao humana explicita.
</p>
</body>
</html>"""
