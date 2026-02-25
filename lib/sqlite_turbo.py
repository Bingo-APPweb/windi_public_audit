"""
WINDI SQLite Turbo Module v1.0.0
================================
Optimized SQLite connections for high-throughput operations.

Usage:
    from sqlite_turbo import turbo_connect

    conn = turbo_connect("/opt/windi/data/mydb.db")
    # ...use conn...
    conn.close()

Or with context manager:
    with turbo_connect("/opt/windi/data/mydb.db") as conn:
        cursor = conn.cursor()
        ...

Optimizations applied:
- WAL journal mode (concurrent reads/writes)
- NORMAL synchronous (safe but faster)
- 8MB cache (up from 2MB default)
- 256MB mmap (memory-mapped I/O)
- 5000ms busy_timeout (prevents lock errors)
- MEMORY temp_store (faster temp tables)

(c) 2026 WINDI Publishing House — Kempten, Bavaria
"""

import sqlite3
from pathlib import Path
from typing import Union

# Turbo PRAGMAs - applied on every new connection
TURBO_PRAGMAS = [
    "PRAGMA journal_mode=WAL",
    "PRAGMA synchronous=NORMAL",
    "PRAGMA cache_size=-8000",        # 8MB (negative = KB)
    "PRAGMA mmap_size=268435456",     # 256MB
    "PRAGMA busy_timeout=5000",       # 5 seconds
    "PRAGMA temp_store=MEMORY",       # Temp tables in RAM
]


def turbo_connect(
    db_path: Union[str, Path],
    row_factory: bool = True,
    check_same_thread: bool = True
) -> sqlite3.Connection:
    """
    Create an optimized SQLite connection with Turbo PRAGMAs.

    Args:
        db_path: Path to the SQLite database file
        row_factory: If True, use sqlite3.Row for dict-like access
        check_same_thread: If False, allows connection across threads

    Returns:
        sqlite3.Connection with turbo optimizations applied
    """
    # Ensure parent directory exists
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Create connection
    conn = sqlite3.connect(
        str(path),
        check_same_thread=check_same_thread
    )

    # Apply row factory for dict-like access
    if row_factory:
        conn.row_factory = sqlite3.Row

    # Apply turbo PRAGMAs
    for pragma in TURBO_PRAGMAS:
        try:
            conn.execute(pragma)
        except sqlite3.Error:
            pass  # Some PRAGMAs may not be supported

    return conn


def turbo_connect_readonly(db_path: Union[str, Path]) -> sqlite3.Connection:
    """
    Create a read-only turbo connection (for reporting/queries).
    Uses URI mode with immutable flag for maximum read performance.
    """
    path = Path(db_path).resolve()
    uri = f"file:{path}?mode=ro"

    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row

    # Read-only optimizations
    conn.execute("PRAGMA query_only=ON")
    conn.execute("PRAGMA cache_size=-16000")  # 16MB for reads
    conn.execute("PRAGMA mmap_size=536870912")  # 512MB for reads

    return conn


def apply_turbo_pragmas(conn: sqlite3.Connection) -> None:
    """
    Apply turbo PRAGMAs to an existing connection.
    Use this when you can't change how the connection is created.
    """
    for pragma in TURBO_PRAGMAS:
        try:
            conn.execute(pragma)
        except sqlite3.Error:
            pass


def get_turbo_status(db_path: Union[str, Path]) -> dict:
    """
    Get current PRAGMA settings for a database.
    Useful for verification.
    """
    conn = sqlite3.connect(str(db_path))

    status = {}
    for pragma_name in ["journal_mode", "synchronous", "cache_size",
                        "mmap_size", "busy_timeout", "temp_store"]:
        try:
            result = conn.execute(f"PRAGMA {pragma_name}").fetchone()
            status[pragma_name] = result[0] if result else None
        except sqlite3.Error:
            status[pragma_name] = "error"

    conn.close()
    return status


# Alias for backwards compatibility
get_db = turbo_connect


if __name__ == "__main__":
    # Test the module
    import tempfile
    import os

    print("SQLite Turbo Module Test")
    print("=" * 40)

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        test_db = f.name

    try:
        conn = turbo_connect(test_db)
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
        conn.execute("INSERT INTO test (value) VALUES ('turbo!')")
        conn.commit()

        status = get_turbo_status(test_db)
        for k, v in status.items():
            print(f"  {k}: {v}")

        conn.close()
        print("\n[OK] Turbo module working correctly")
    finally:
        os.unlink(test_db)
        # Clean up WAL files if any
        for ext in ["-wal", "-shm"]:
            try:
                os.unlink(test_db + ext)
            except FileNotFoundError:
                pass
