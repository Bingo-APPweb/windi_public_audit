#!/usr/bin/env python3
"""
WINDI Serial Engine — N3: Sequential Document Numbering
"AI processes. Human decides. WINDI guarantees."

Generates unique, human-readable serial numbers for every WINDI document.
Format: WINDI-{YYYY}-{NNNN} → e.g., WINDI-2026-0001

Features:
- Atomic counter using SQLite transaction locking
- Year rollover resets sequence to 1
- Thread-safe for concurrent renders
- Persistent storage in /opt/windi/data/serial_counter.db
"""

import os
import sqlite3
import threading
import urllib.request
import urllib.error
import json
from datetime import datetime, timezone
from pathlib import Path

# ── Configuration ──
DB_PATH = Path("/opt/windi/data/serial_counter.db")
LEDGER_URL = "http://localhost:8101/api/receipts"


class SerialEngine:
    """
    Thread-safe serial number generator with SQLite persistence.

    Usage:
        engine = SerialEngine()
        serial = engine.next_serial()  # → "WINDI-2026-0001"
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern for shared counter access."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the serial engine."""
        if self._initialized:
            return
        self._db_lock = threading.Lock()
        self._init_db()
        self._initialized = True

    def _init_db(self):
        """Create database and table if not exists."""
        # Ensure data directory exists
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(str(DB_PATH), timeout=30.0) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS serial_counter (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    year INTEGER NOT NULL,
                    sequence INTEGER NOT NULL DEFAULT 0
                )
            """)
            # Seed with current year and sequence 0 if empty
            cursor = conn.execute("SELECT COUNT(*) FROM serial_counter")
            if cursor.fetchone()[0] == 0:
                current_year = datetime.now(timezone.utc).year
                conn.execute(
                    "INSERT INTO serial_counter (id, year, sequence) VALUES (1, ?, 0)",
                    (current_year,)
                )
            conn.commit()

    def next_serial(self) -> str:
        """
        Get the next serial number, atomically incrementing the counter.

        Returns:
            Serial in format WINDI-{YYYY}-{NNNN}

        Thread-safe: Uses SQLite transaction locking.
        Year rollover: Resets sequence to 1 when year changes.
        """
        with self._db_lock:
            with sqlite3.connect(str(DB_PATH), timeout=30.0) as conn:
                # Use IMMEDIATE to acquire write lock immediately
                conn.execute("BEGIN IMMEDIATE")
                try:
                    cursor = conn.execute(
                        "SELECT year, sequence FROM serial_counter WHERE id = 1"
                    )
                    row = cursor.fetchone()
                    stored_year, stored_seq = row

                    current_year = datetime.now(timezone.utc).year

                    if current_year > stored_year:
                        # Year rollover: reset sequence to 1
                        new_year = current_year
                        new_seq = 1
                    else:
                        # Same year: increment sequence
                        new_year = stored_year
                        new_seq = stored_seq + 1

                    conn.execute(
                        "UPDATE serial_counter SET year = ?, sequence = ? WHERE id = 1",
                        (new_year, new_seq)
                    )
                    conn.commit()

                    # Format: WINDI-YYYY-NNNN (expand beyond 4 digits if needed)
                    serial = f"WINDI-{new_year}-{new_seq:04d}"
                    return serial

                except Exception:
                    conn.rollback()
                    raise

    def get_current_serial(self) -> str:
        """
        Get the last assigned serial without incrementing.

        Returns:
            Last serial in format WINDI-{YYYY}-{NNNN}, or None if no serials assigned yet.
        """
        with sqlite3.connect(str(DB_PATH), timeout=30.0) as conn:
            cursor = conn.execute(
                "SELECT year, sequence FROM serial_counter WHERE id = 1"
            )
            row = cursor.fetchone()
            if row and row[1] > 0:
                return f"WINDI-{row[0]}-{row[1]:04d}"
            return None

    def get_stats(self) -> dict:
        """
        Get serial counter statistics.

        Returns:
            Dict with year, sequence, next_serial preview.
        """
        with sqlite3.connect(str(DB_PATH), timeout=30.0) as conn:
            cursor = conn.execute(
                "SELECT year, sequence FROM serial_counter WHERE id = 1"
            )
            row = cursor.fetchone()
            if row:
                return {
                    "year": row[0],
                    "sequence": row[1],
                    "current_serial": f"WINDI-{row[0]}-{row[1]:04d}" if row[1] > 0 else None,
                    "next_serial": f"WINDI-{row[0]}-{row[1]+1:04d}",
                    "db_path": str(DB_PATH),
                }
            return {"error": "no counter found"}

    def lookup_serial(self, serial: str) -> dict | None:
        """
        Query Ledger to find a receipt by serial number.

        Args:
            serial: Serial number to search for (e.g., "WINDI-2026-0001")

        Returns:
            Receipt dict if found, None otherwise.
        """
        try:
            # Query Ledger API
            req = urllib.request.Request(LEDGER_URL, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())

            receipts = data.get("receipts", data if isinstance(data, list) else [])

            # Search for matching serial
            for receipt in receipts:
                if receipt.get("serial") == serial:
                    return receipt

            return None

        except (urllib.error.URLError, json.JSONDecodeError, Exception) as e:
            return {"error": str(e)}


# ── Singleton accessor ──
_serial_engine = None


def get_serial_engine() -> SerialEngine:
    """Get or create the singleton SerialEngine instance."""
    global _serial_engine
    if _serial_engine is None:
        _serial_engine = SerialEngine()
    return _serial_engine


# ── CLI Test ──
if __name__ == "__main__":
    import sys

    print("WINDI Serial Engine - N3 Module")
    print("=" * 50)

    engine = SerialEngine()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "next":
            serial = engine.next_serial()
            print(f"Next serial: {serial}")
        elif cmd == "current":
            serial = engine.get_current_serial()
            print(f"Current serial: {serial or 'none assigned yet'}")
        elif cmd == "stats":
            stats = engine.get_stats()
            print(json.dumps(stats, indent=2))
        elif cmd == "lookup" and len(sys.argv) > 2:
            result = engine.lookup_serial(sys.argv[2])
            print(json.dumps(result, indent=2) if result else "Not found")
        else:
            print("Usage: serial_engine.py [next|current|stats|lookup <serial>]")
    else:
        # Default: show stats
        stats = engine.get_stats()
        print(f"DB Path: {stats.get('db_path')}")
        print(f"Year: {stats.get('year')}")
        print(f"Sequence: {stats.get('sequence')}")
        print(f"Current: {stats.get('current_serial') or 'none'}")
        print(f"Next: {stats.get('next_serial')}")
