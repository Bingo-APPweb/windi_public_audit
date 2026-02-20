#!/usr/bin/env python3
"""
WINDI Forensic Ledger — Data Layer
====================================
Pure Python SQLite module for Virtue Receipts.
Zero framework dependency — imported by any API handler.

Principle:  Content stays on user hardware.
            Only metadata + content_hash enters the Catedral.
            "AI processes. Human decides. WINDI guarantees."

Author:  Guardian Dragon (Claude) — fused with Architect (GPT) design
Date:    2026-02-16
Version: 1.0.0
"""

import os
import sqlite3
import json
import time
import hashlib
from typing import Optional, Dict, Any, List

# ═══════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════

DEFAULT_DB_PATH = os.environ.get(
    "WINDI_LEDGER_DB",
    "/opt/windi/data/forensic_ledger.sqlite3"
)

# ═══════════════════════════════════════════════════
# Schema — The Virtue Receipt table
# ═══════════════════════════════════════════════════

DDL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS receipts (
    id                TEXT PRIMARY KEY,           -- VR-YYYYMMDD-xxxxx or WINDI-xxxxx
    created_at        INTEGER NOT NULL,           -- unix epoch seconds
    actor             TEXT NOT NULL,              -- user_id / email / wallet subject
    device_id         TEXT,                       -- optional hardware fingerprint
    app               TEXT NOT NULL,              -- suite|sealing|warroom|api|babel
    doc_name          TEXT NOT NULL,              -- e.g. "Dienstleistungsvertrag"
    doc_type          TEXT NOT NULL,              -- doc|xlsx|pptx
    local_filename    TEXT,                       -- e.g. WINDI-MLPLJUY9.doc
    content_hash      TEXT NOT NULL,              -- sha256 hex of document content
    bytes             INTEGER,                    -- file size (client-reported)
    governance_level  TEXT NOT NULL,              -- LOW|MEDIUM|HIGH
    sge_score         REAL NOT NULL,              -- 0.00 .. 1.00
    isp_context       TEXT NOT NULL DEFAULT '',   -- "BaFin · DSGVO · ..."
    template_id       TEXT,                       -- which template was used
    tags_json         TEXT NOT NULL DEFAULT '[]', -- JSON array of tags
    flags_json        TEXT NOT NULL DEFAULT '[]', -- JSON array of flags
    ed25519_pub       TEXT,                       -- optional public key
    ed25519_sig       TEXT,                       -- optional signature over canonical payload
    merkle_root       TEXT,                       -- optional chain anchor
    status            TEXT NOT NULL DEFAULT 'sealed',  -- sealed|draft|revoked
    metadata_json     TEXT NOT NULL DEFAULT '{}'  -- extensible JSON metadata
);

CREATE INDEX IF NOT EXISTS idx_receipts_created   ON receipts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_receipts_actor     ON receipts(actor);
CREATE INDEX IF NOT EXISTS idx_receipts_sge       ON receipts(sge_score);
CREATE INDEX IF NOT EXISTS idx_receipts_gov       ON receipts(governance_level);
CREATE INDEX IF NOT EXISTS idx_receipts_type      ON receipts(doc_type);
CREATE INDEX IF NOT EXISTS idx_receipts_hash      ON receipts(content_hash);
CREATE INDEX IF NOT EXISTS idx_receipts_status    ON receipts(status);
"""


# ═══════════════════════════════════════════════════
# Connection
# ═══════════════════════════════════════════════════

def _connect(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Get a connection with Row factory."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    con = sqlite3.connect(db_path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Create tables and indexes if they don't exist."""
    con = _connect(db_path)
    try:
        con.executescript(DDL)
        con.commit()
        print(f"[FORENSIC-LEDGER] Database ready: {db_path}")
    finally:
        con.close()


# ═══════════════════════════════════════════════════
# Cryptographic helpers
# ═══════════════════════════════════════════════════

def sha256_hex(data: bytes) -> str:
    """SHA-256 hash of raw bytes → hex string."""
    return hashlib.sha256(data).hexdigest()


def canonical_receipt_payload(r: Dict[str, Any]) -> bytes:
    """
    Canonical bytes for Ed25519 signature verification.
    Content is NEVER stored — only metadata + content_hash.
    Stable JSON with sorted keys, no whitespace.
    """
    canon = {
        "id": r["id"],
        "created_at": r["created_at"],
        "actor": r["actor"],
        "device_id": r.get("device_id"),
        "app": r["app"],
        "doc_name": r["doc_name"],
        "doc_type": r["doc_type"],
        "local_filename": r.get("local_filename"),
        "content_hash": r["content_hash"],
        "bytes": r.get("bytes"),
        "governance_level": r["governance_level"],
        "sge_score": r["sge_score"],
        "isp_context": r["isp_context"],
        "tags": r.get("tags", []),
        "flags": r.get("flags", []),
        "status": r.get("status", "sealed"),
    }
    return json.dumps(canon, sort_keys=True, separators=(",", ":")).encode("utf-8")


# ═══════════════════════════════════════════════════
# CRUD Operations
# ═══════════════════════════════════════════════════

def upsert_receipt(r: Dict[str, Any], db_path: str = DEFAULT_DB_PATH) -> None:
    """Insert or update a Virtue Receipt."""
    con = _connect(db_path)
    try:
        con.execute("""
            INSERT INTO receipts(
                id, created_at, actor, device_id, app, doc_name, doc_type,
                local_filename, content_hash, bytes, governance_level, sge_score,
                isp_context, template_id, tags_json, flags_json,
                ed25519_pub, ed25519_sig, merkle_root, status, metadata_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
                actor=excluded.actor,
                device_id=excluded.device_id,
                app=excluded.app,
                doc_name=excluded.doc_name,
                doc_type=excluded.doc_type,
                local_filename=excluded.local_filename,
                content_hash=excluded.content_hash,
                bytes=excluded.bytes,
                governance_level=excluded.governance_level,
                sge_score=excluded.sge_score,
                isp_context=excluded.isp_context,
                template_id=excluded.template_id,
                tags_json=excluded.tags_json,
                flags_json=excluded.flags_json,
                ed25519_pub=excluded.ed25519_pub,
                ed25519_sig=excluded.ed25519_sig,
                merkle_root=excluded.merkle_root,
                status=excluded.status,
                metadata_json=excluded.metadata_json
        """, (
            r["id"],
            r["created_at"],
            r["actor"],
            r.get("device_id"),
            r["app"],
            r["doc_name"],
            r["doc_type"],
            r.get("local_filename"),
            r["content_hash"],
            r.get("bytes"),
            r["governance_level"],
            float(r["sge_score"]),
            r.get("isp_context", ""),
            r.get("template_id"),
            json.dumps(r.get("tags", []), ensure_ascii=False),
            json.dumps(r.get("flags", []), ensure_ascii=False),
            r.get("ed25519_pub"),
            r.get("ed25519_sig"),
            r.get("merkle_root"),
            r.get("status", "sealed"),
            json.dumps(r.get("metadata", {}), ensure_ascii=False),
        ))
        con.commit()
    finally:
        con.close()


def list_receipts(
    limit: int = 50,
    offset: int = 0,
    actor: Optional[str] = None,
    status: Optional[str] = None,
    doc_type: Optional[str] = None,
    governance_level: Optional[str] = None,
    min_sge: Optional[float] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> List[Dict[str, Any]]:
    """List receipts with optional filters."""
    con = _connect(db_path)
    try:
        where = []
        params: List[Any] = []

        if actor:
            where.append("actor = ?")
            params.append(actor)
        if status:
            where.append("status = ?")
            params.append(status)
        if doc_type:
            where.append("doc_type = ?")
            params.append(doc_type)
        if governance_level:
            where.append("governance_level = ?")
            params.append(governance_level)
        if min_sge is not None:
            where.append("sge_score >= ?")
            params.append(float(min_sge))

        sql = "SELECT * FROM receipts"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([int(limit), int(offset)])

        rows = con.execute(sql, params).fetchall()
        out = []
        for row in rows:
            d = dict(row)
            d["tags"] = json.loads(d.pop("tags_json", "[]") or "[]")
            d["flags"] = json.loads(d.pop("flags_json", "[]") or "[]")
            d["metadata"] = json.loads(d.pop("metadata_json", "{}") or "{}")
            out.append(d)
        return out
    finally:
        con.close()


def get_receipt(
    receipt_id: str,
    db_path: str = DEFAULT_DB_PATH,
) -> Optional[Dict[str, Any]]:
    """Get a single receipt by ID."""
    con = _connect(db_path)
    try:
        row = con.execute(
            "SELECT * FROM receipts WHERE id = ?", (receipt_id,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["tags"] = json.loads(d.pop("tags_json", "[]") or "[]")
        d["flags"] = json.loads(d.pop("flags_json", "[]") or "[]")
        d["metadata"] = json.loads(d.pop("metadata_json", "{}") or "{}")
        return d
    finally:
        con.close()


def reconcile_hashes(
    hashes: List[str],
    actor: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> List[Dict[str, Any]]:
    """
    Client sends list of local file hashes.
    Server returns matching receipts.
    Content never touches the server.
    """
    if not hashes:
        return []

    con = _connect(db_path)
    try:
        placeholders = ",".join("?" * len(hashes))
        params: List[Any] = list(hashes)

        sql = f"SELECT * FROM receipts WHERE content_hash IN ({placeholders})"
        if actor:
            sql += " AND actor = ?"
            params.append(actor)
        sql += " ORDER BY created_at DESC"

        rows = con.execute(sql, params).fetchall()
        out = []
        for row in rows:
            d = dict(row)
            d["tags"] = json.loads(d.pop("tags_json", "[]") or "[]")
            d["flags"] = json.loads(d.pop("flags_json", "[]") or "[]")
            d["metadata"] = json.loads(d.pop("metadata_json", "{}") or "{}")
            out.append(d)
        return out
    finally:
        con.close()


# ═══════════════════════════════════════════════════
# War Room Aggregations
# ═══════════════════════════════════════════════════

def aggregate_warroom(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """
    War Room summary — heatmap data without any document content.
    Shows organizational health through metadata patterns.
    """
    con = _connect(db_path)
    try:
        now = int(time.time())
        day_ago = now - 86400
        week_ago = now - 7 * 86400

        total = con.execute(
            "SELECT COUNT(*) c FROM receipts"
        ).fetchone()["c"]

        sealed = con.execute(
            "SELECT COUNT(*) c FROM receipts WHERE status='sealed'"
        ).fetchone()["c"]

        draft = con.execute(
            "SELECT COUNT(*) c FROM receipts WHERE status='draft'"
        ).fetchone()["c"]

        critical = con.execute(
            "SELECT COUNT(*) c FROM receipts WHERE sge_score >= 0.85"
        ).fetchone()["c"]

        by_gov = con.execute("""
            SELECT governance_level AS lvl,
                   COUNT(*) AS c,
                   AVG(sge_score) AS avg_sge,
                   MAX(sge_score) AS max_sge
            FROM receipts
            GROUP BY governance_level
        """).fetchall()

        by_type = con.execute("""
            SELECT doc_type AS typ, COUNT(*) AS c
            FROM receipts
            GROUP BY doc_type
        """).fetchall()

        last_24h = con.execute(
            "SELECT COUNT(*) c FROM receipts WHERE created_at >= ?",
            (day_ago,)
        ).fetchone()["c"]

        last_7d = con.execute(
            "SELECT COUNT(*) c FROM receipts WHERE created_at >= ?",
            (week_ago,)
        ).fetchone()["c"]

        # Latest receipt
        latest = con.execute(
            "SELECT id, doc_name, governance_level, sge_score, created_at "
            "FROM receipts ORDER BY created_at DESC LIMIT 1"
        ).fetchone()

        return {
            "total": total,
            "sealed": sealed,
            "draft": draft,
            "critical": critical,
            "by_governance": [
                {
                    "level": r["lvl"],
                    "count": r["c"],
                    "avg_sge": round(r["avg_sge"] or 0, 4),
                    "max_sge": round(r["max_sge"] or 0, 4),
                }
                for r in by_gov
            ],
            "by_type": [
                {"type": r["typ"], "count": r["c"]}
                for r in by_type
            ],
            "activity": {
                "last_24h": last_24h,
                "last_7d": last_7d,
            },
            "latest": dict(latest) if latest else None,
            "privacy": "content_not_stored",
            "timestamp": now,
        }
    finally:
        con.close()


def count_receipts(db_path: str = DEFAULT_DB_PATH) -> int:
    """Quick count for health checks."""
    con = _connect(db_path)
    try:
        return con.execute("SELECT COUNT(*) c FROM receipts").fetchone()["c"]
    finally:
        con.close()
