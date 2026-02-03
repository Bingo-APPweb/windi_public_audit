# /opt/windi/brain/ledger.py
# WINDI Ledger - Append-Only com Hash Chain

import sqlite3
import hashlib
from datetime import datetime
from typing import Optional, List, Dict

DB_PATH = "/opt/windi/data/virtue_history.db"


def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _compute_hash(event_id, timestamp, actor, action, payload, prev_hash):
    data = f"{event_id}|{timestamp}|{actor}|{action}|{payload}|{prev_hash}"
    return hashlib.sha256(data.encode()).hexdigest()


def get_last_hash():
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, event_id, hash FROM ledger ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    if row:
        return {"id": row["id"], "event_id": row["event_id"], "hash": row["hash"] or "GENESIS"}
    return {"id": 0, "event_id": None, "hash": "GENESIS"}


def write_event(event):
    conn = _get_connection()
    cur = conn.cursor()
    
    last = get_last_hash()
    prev_hash = last.get("hash") or "GENESIS"
    timestamp = datetime.utcnow().isoformat()
    
    event_hash = _compute_hash(
        event.event_id,
        timestamp,
        event.actor,
        event.action,
        event.payload or "",
        prev_hash
    )
    
    cur.execute("""
        INSERT INTO ledger (event_id, timestamp, actor, action, payload, prev_hash, hash)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        event.event_id,
        timestamp,
        event.actor,
        event.action,
        event.payload,
        prev_hash,
        event_hash
    ))
    
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    
    return {"id": new_id, "hash": event_hash, "prev_hash": prev_hash}


def read_events(event_type=None, actor=None, limit=50):
    conn = _get_connection()
    cur = conn.cursor()
    
    query = "SELECT * FROM ledger WHERE 1=1"
    params = []
    
    if event_type:
        query += " AND action = ?"
        params.append(event_type)
    
    if actor:
        query += " AND actor = ?"
        params.append(actor)
    
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]
