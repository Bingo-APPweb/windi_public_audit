#!/usr/bin/env python3
"""
§173 DID Simplification — Orphan DID Migration Script
======================================================
Migrates DIDs from WINDI-LAW and WINDI-Travel to W-DID-GENESIS.

Usage:
    python3 migrate_orphan_dids.py --dry-run   # Preview only
    python3 migrate_orphan_dids.py             # Execute migration

Liga IA+H · 15 Abril 2026
"""

import sqlite3
import json
import hashlib
import os
from datetime import datetime
from pathlib import Path

# Configuration
GENESIS_DB = "/opt/windi/did-genesis/did_genesis.db"
LAW_DB = "/opt/windi/windi-law/identity-gate/windi_law_identity.db"
TRAVEL_DB = "/opt/windi/windi-travel/identity-gate/windi_travel_identity.db"
LOG_FILE = "/opt/windi/logs/identity-migration/orphan_migration.jsonl"

# Ensure log directory exists
Path("/opt/windi/logs/identity-migration").mkdir(parents=True, exist_ok=True)


def get_genesis_dids():
    """Get all DIDs currently in Genesis."""
    conn = sqlite3.connect(GENESIS_DB)
    cursor = conn.execute("SELECT did FROM identities")
    dids = {row[0] for row in cursor.fetchall()}
    conn.close()
    return dids


def get_orphan_dids(source_db, source_name):
    """Get DIDs from source that don't exist in Genesis."""
    genesis_dids = get_genesis_dids()

    conn = sqlite3.connect(source_db)
    cursor = conn.execute("""
        SELECT did, email, fingerprint, created_at
        FROM admins
        WHERE did IS NOT NULL
    """)

    orphans = []
    for row in cursor.fetchall():
        did, email, fingerprint, created_at = row
        if did and did not in genesis_dids:
            orphans.append({
                "did": did,
                "email": email,
                "fingerprint": fingerprint,
                "created_at": created_at,
                "source": source_name
            })

    conn.close()
    return orphans


def migrate_to_genesis(orphan, dry_run=False):
    """Insert orphan DID into Genesis database."""

    # Generate passphrase hash (dummy for migration)
    passphrase_hash = hashlib.sha256(
        f"migrated-{orphan['did']}-{orphan['created_at']}".encode()
    ).hexdigest()

    # Determine tier based on source
    tier = "NODAL"  # Default for migrated users

    if dry_run:
        return {
            "status": "dry_run",
            "did": orphan["did"],
            "tier": tier,
            "source": orphan["source"]
        }

    conn = sqlite3.connect(GENESIS_DB)
    try:
        conn.execute("""
            INSERT INTO identities (did, passphrase_hash, display_name, email, role, tier, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
        """, (
            orphan["did"],
            passphrase_hash,
            f"Migrated from {orphan['source']}",
            orphan["email"],
            "user",
            tier,
            orphan["created_at"]
        ))
        conn.commit()
        result = {
            "status": "migrated",
            "did": orphan["did"],
            "tier": tier,
            "source": orphan["source"]
        }
    except sqlite3.IntegrityError as e:
        result = {
            "status": "already_exists",
            "did": orphan["did"],
            "error": str(e)
        }
    finally:
        conn.close()

    return result


def log_migration(result):
    """Append migration result to log file."""
    result["timestamp"] = datetime.utcnow().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(result) + "\n")


def main():
    import sys
    dry_run = "--dry-run" in sys.argv

    print("=" * 60)
    print("§173 DID Simplification — Orphan Migration")
    print("=" * 60)
    print(f"Mode: {'DRY RUN (preview)' if dry_run else 'LIVE MIGRATION'}")
    print()

    # Collect orphans from both sources
    all_orphans = []

    if os.path.exists(LAW_DB):
        law_orphans = get_orphan_dids(LAW_DB, "WINDI-LAW")
        print(f"WINDI-LAW orphans: {len(law_orphans)}")
        all_orphans.extend(law_orphans)

    if os.path.exists(TRAVEL_DB):
        travel_orphans = get_orphan_dids(TRAVEL_DB, "WINDI-Travel")
        print(f"WINDI-Travel orphans: {len(travel_orphans)}")
        all_orphans.extend(travel_orphans)

    print(f"\nTotal orphans to migrate: {len(all_orphans)}")
    print("-" * 60)

    if not all_orphans:
        print("✓ No orphans found. All DIDs are in Genesis.")
        return

    # Process each orphan
    results = {"migrated": 0, "already_exists": 0, "dry_run": 0, "errors": 0}

    for orphan in all_orphans:
        result = migrate_to_genesis(orphan, dry_run)
        results[result["status"]] = results.get(result["status"], 0) + 1
        log_migration(result)

        status_icon = {
            "migrated": "✓",
            "already_exists": "○",
            "dry_run": "→",
        }.get(result["status"], "✗")

        print(f"{status_icon} {orphan['did'][:35]}... [{orphan['source']}] → {result['status']}")

    print("-" * 60)
    print(f"Results: {results}")
    print(f"Log: {LOG_FILE}")

    if dry_run:
        print("\n⚠ DRY RUN complete. Run without --dry-run to execute migration.")


if __name__ == "__main__":
    main()
