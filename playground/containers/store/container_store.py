"""
WINDI Container Store
Persistência SQLite para containers do Playground.

Regras:
- FREE: revisável, pode apagar micro-pensamentos
- CONSTITUTIONAL: append-only, imutável após crossing

O container nunca muda de estrutura. Muda apenas o regime.
"""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

# Database path
DB_PATH = Path("/opt/windi/playground/containers/store/containers.db")


def get_connection() -> sqlite3.Connection:
    """Get database connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS containers (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            mode TEXT DEFAULT 'free',
            constitutional INTEGER DEFAULT 0,
            crossing TEXT,
            reasoning TEXT DEFAULT '[]',
            intent_evolution TEXT DEFAULT '[]',
            graph TEXT DEFAULT '{}',
            evidence TEXT DEFAULT '[]',
            owner_did TEXT,
            receipts TEXT DEFAULT '[]',
            ledger_entries TEXT DEFAULT '[]',
            created_at TEXT,
            updated_at TEXT
        )
    """)

    # Index for session lookup
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_session_id ON containers(session_id)
    """)

    # Index for constitutional containers
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_constitutional ON containers(constitutional)
    """)

    conn.commit()
    conn.close()
    print(f"[CONTAINER-STORE] Database initialized at {DB_PATH}")


def create_container(session_id: Optional[str] = None) -> Dict:
    """
    Create a new container in FREE mode.
    Returns the full container dict.
    """
    container_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    container = {
        "id": container_id,
        "session_id": session_id,
        "mode": "free",
        "constitutional": False,
        "crossing": None,
        "reasoning": [],
        "intent_evolution": [],
        "graph": {},
        "evidence": [],
        "owner_did": None,
        "receipts": [],
        "ledger_entries": [],
        "created_at": now,
        "updated_at": now
    }

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO containers (
            id, session_id, mode, constitutional, crossing,
            reasoning, intent_evolution, graph, evidence,
            owner_did, receipts, ledger_entries,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        container["id"],
        container["session_id"],
        container["mode"],
        1 if container["constitutional"] else 0,
        json.dumps(container["crossing"]),
        json.dumps(container["reasoning"]),
        json.dumps(container["intent_evolution"]),
        json.dumps(container["graph"]),
        json.dumps(container["evidence"]),
        container["owner_did"],
        json.dumps(container["receipts"]),
        json.dumps(container["ledger_entries"]),
        container["created_at"],
        container["updated_at"]
    ))

    conn.commit()
    conn.close()

    return container


def get_container(container_id: str) -> Optional[Dict]:
    """Get a container by ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM containers WHERE id = ?", (container_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return _row_to_dict(row)


def get_containers_by_session(session_id: str) -> List[Dict]:
    """Get all containers for a session."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM containers WHERE session_id = ? ORDER BY created_at DESC",
        (session_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    return [_row_to_dict(row) for row in rows]


def add_reasoning(container_id: str, thought: str, entry_type: str = "human") -> Optional[Dict]:
    """
    Add a micro-thought to the container.
    Works in both FREE and CONSTITUTIONAL mode.

    Args:
        container_id: The container ID
        thought: The reasoning text
        entry_type: "human" (default) or "system" - I14 compliance
                    Only "human" entries count for DIFF timeline
    """
    container = get_container(container_id)
    if not container:
        return None

    container["reasoning"].append(thought)
    container["updated_at"] = datetime.utcnow().isoformat()

    # Add to intent evolution with explicit type (I14: no system entries masquerading as human)
    container["intent_evolution"].append({
        "timestamp": container["updated_at"],
        "state": thought[:100],  # Summary
        "trigger": "reasoning_added",
        "type": entry_type  # "human" or "system" - DIFF filters by this
    })

    _save_container(container)
    return container


def add_evidence(container_id: str, event_type: str, data: Dict) -> Optional[Dict]:
    """
    Add an evidence event to the container.
    Works in both modes.
    """
    container = get_container(container_id)
    if not container:
        return None

    now = datetime.utcnow().isoformat()

    container["evidence"].append({
        "timestamp": now,
        "event_type": event_type,
        "data": data
    })
    container["updated_at"] = now

    _save_container(container)
    return container


def update_graph(container_id: str, graph: Dict) -> Optional[Dict]:
    """
    Update the ProjectGraph.
    Works in both modes.
    """
    container = get_container(container_id)
    if not container:
        return None

    container["graph"] = graph
    container["updated_at"] = datetime.utcnow().isoformat()

    _save_container(container)
    return container


def delete_reasoning(container_id: str, index: int) -> Optional[Dict]:
    """
    Delete a micro-thought by index.
    ONLY works in FREE mode. Returns None if CONSTITUTIONAL.
    This is the right to forget while FREE.
    """
    container = get_container(container_id)
    if not container:
        return None

    # Constitutional containers are immutable
    if container["constitutional"]:
        return None

    if 0 <= index < len(container["reasoning"]):
        del container["reasoning"][index]
        container["updated_at"] = datetime.utcnow().isoformat()
        _save_container(container)

    return container


def record_change_of_mind(container_id: str, old_direction: str, new_direction: str) -> Optional[Dict]:
    """
    Record a change-of-mind event.
    In FREE: just evidence
    In CONSTITUTIONAL: evidence that cannot be removed
    """
    container = get_container(container_id)
    if not container:
        return None

    now = datetime.utcnow().isoformat()

    event = {
        "timestamp": now,
        "event_type": "CHANGE_OF_MIND",
        "data": {
            "old_direction": old_direction,
            "new_direction": new_direction
        }
    }

    container["evidence"].append(event)
    container["intent_evolution"].append({
        "timestamp": now,
        "state": new_direction[:100],
        "trigger": "change_of_mind",
        "type": "human"  # Change of mind is always human intent
    })
    container["updated_at"] = now

    _save_container(container)
    return container


def _row_to_dict(row: sqlite3.Row) -> Dict:
    """Convert database row to container dict."""
    return {
        "id": row["id"],
        "session_id": row["session_id"],
        "mode": row["mode"],
        "constitutional": bool(row["constitutional"]),
        "crossing": json.loads(row["crossing"]) if row["crossing"] else None,
        "reasoning": json.loads(row["reasoning"]),
        "intent_evolution": json.loads(row["intent_evolution"]),
        "graph": json.loads(row["graph"]),
        "evidence": json.loads(row["evidence"]),
        "owner_did": row["owner_did"],
        "receipts": json.loads(row["receipts"]),
        "ledger_entries": json.loads(row["ledger_entries"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }


def _save_container(container: Dict):
    """Save container to database."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE containers SET
            session_id = ?,
            mode = ?,
            constitutional = ?,
            crossing = ?,
            reasoning = ?,
            intent_evolution = ?,
            graph = ?,
            evidence = ?,
            owner_did = ?,
            receipts = ?,
            ledger_entries = ?,
            updated_at = ?
        WHERE id = ?
    """, (
        container["session_id"],
        container["mode"],
        1 if container["constitutional"] else 0,
        json.dumps(container["crossing"]),
        json.dumps(container["reasoning"]),
        json.dumps(container["intent_evolution"]),
        json.dumps(container["graph"]),
        json.dumps(container["evidence"]),
        container["owner_did"],
        json.dumps(container["receipts"]),
        json.dumps(container["ledger_entries"]),
        container["updated_at"],
        container["id"]
    ))

    conn.commit()
    conn.close()


# Initialize on import
init_db()
