#!/usr/bin/env python3
"""
WINDI Preview Cleaner — W-PAGE-001 Maintenance
===============================================

Cleans up expired preview pages (TTL: 60 minutes).
Designed to run via systemd.timer every 15 minutes.

Usage:
    python3 preview_cleaner.py [--dry-run]

Principle: "AI processes. Human decides. WINDI guarantees."
"""

import argparse
import os
import sqlite3
import sys
from datetime import datetime, timezone, timedelta

# Configuration
DB_PATH = "/opt/windi/agents/constitutional-agent/data/page_agent.db"
PREVIEW_TTL_MINUTES = 60
LOG_PREFIX = "[Preview Cleaner]"


def log(message: str):
    """Log with timestamp."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"{ts} {LOG_PREFIX} {message}")


def clean_expired_previews(dry_run: bool = False) -> dict:
    """
    Delete preview pages that have exceeded TTL.

    Returns:
        dict with cleanup statistics
    """
    if not os.path.exists(DB_PATH):
        log(f"Database not found: {DB_PATH}")
        return {"error": "database_not_found", "deleted": 0}

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Calculate cutoff time
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=PREVIEW_TTL_MINUTES)
    cutoff_iso = cutoff.isoformat()

    # Find expired previews
    cursor.execute("""
        SELECT id, preview_id, title, created_at
        FROM pages
        WHERE status = 'preview' AND created_at < ?
    """, (cutoff_iso,))

    expired = cursor.fetchall()

    if not expired:
        log("No expired previews found.")
        conn.close()
        return {"deleted": 0, "checked_at": datetime.now(timezone.utc).isoformat()}

    log(f"Found {len(expired)} expired preview(s).")

    deleted_ids = []
    for row in expired:
        log(f"  - {row['preview_id']}: {row['title']} (created: {row['created_at']})")
        deleted_ids.append(row['id'])

    if dry_run:
        log("DRY RUN - No changes made.")
        conn.close()
        return {
            "deleted": 0,
            "would_delete": len(expired),
            "dry_run": True,
            "checked_at": datetime.now(timezone.utc).isoformat()
        }

    # Delete expired previews
    placeholders = ",".join(["?" for _ in deleted_ids])
    cursor.execute(f"DELETE FROM pages WHERE id IN ({placeholders})", deleted_ids)
    conn.commit()

    deleted_count = cursor.rowcount
    log(f"Deleted {deleted_count} expired preview(s).")

    conn.close()

    return {
        "deleted": deleted_count,
        "checked_at": datetime.now(timezone.utc).isoformat()
    }


def main():
    parser = argparse.ArgumentParser(
        description="Clean expired WINDI page previews"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without making changes"
    )
    args = parser.parse_args()

    log("Starting preview cleanup...")
    log(f"TTL: {PREVIEW_TTL_MINUTES} minutes")
    log(f"Database: {DB_PATH}")

    result = clean_expired_previews(dry_run=args.dry_run)

    if "error" in result:
        log(f"Error: {result['error']}")
        sys.exit(1)

    log("Cleanup complete.")
    sys.exit(0)


if __name__ == "__main__":
    main()
