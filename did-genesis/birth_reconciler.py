#!/usr/bin/env python3
"""
W-DID-GENESIS Birth Reconciler
==============================
P0 Implementation — §299 PLAYGROUND-MUSTER-001

Resolves DIDs with birth_receipt_status = 'pending'
and syncs birth_failure events to Ledger.

Runs via systemd timer every 5 minutes.

Liga IA+H · Kempten, Bavaria · 2026
"""

import sqlite3
import logging
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import httpx

# Add parent dir to path for ledger_client import
sys.path.insert(0, str(Path(__file__).parent))

from ledger_client import (
    check_receipt_exists,
    post_receipt,
    build_birth_receipt,
    build_failure_receipt,
    generate_birth_receipt_id,
    generate_failure_receipt_id,
    LEDGER_URL
)

# Configuration
DB_PATH = Path(__file__).parent / "did_genesis.db"
PENDING_TTL_HOURS = 24
LOG_PATH = Path("/opt/windi/logs/birth_reconciler.log")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("birth-reconciler")


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def reconcile_pending_births():
    """
    PART 1: Reconcile DIDs with birth_receipt_status = 'pending'

    For each pending DID:
    - Check Ledger: does receipt exist?
    - If YES: UPDATE to 'sealed'
    - If NO (404) and within TTL: try to re-emit
    - If NO (404) and TTL expired: DELETE + log failure
    - If Ledger unreachable: skip, next iteration
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT did, sovereign_name, email, created_at, birth_receipt_id
        FROM identities
        WHERE birth_receipt_status = 'pending'
    """)

    pending = cursor.fetchall()
    log.info(f"Found {len(pending)} pending births to reconcile")

    for row in pending:
        did = row["did"]
        sovereign_name = row["sovereign_name"]
        email = row["email"]
        created_at = row["created_at"]
        expected_receipt_id = row["birth_receipt_id"] or generate_birth_receipt_id(did)

        # Calculate age
        try:
            created_str = created_at.replace("Z", "+00:00")
            # Handle SQLite datetime format (no timezone, space instead of T)
            if " " in created_str and "T" not in created_str:
                created_str = created_str.replace(" ", "T")
            if "+" not in created_str:
                created = datetime.fromisoformat(created_str).replace(tzinfo=timezone.utc)
            else:
                created = datetime.fromisoformat(created_str)
        except Exception as e:
            log.warning(f"Could not parse created_at '{created_at}': {e}")
            created = datetime.now(timezone.utc) - timedelta(hours=1)

        age = datetime.now(timezone.utc) - created

        try:
            # Check if receipt exists in Ledger
            exists, receipt = check_receipt_exists(expected_receipt_id)

            if exists:
                # Ledger HAS the receipt -> seal
                cursor.execute("""
                    UPDATE identities
                    SET birth_receipt_status = 'sealed'
                    WHERE did = ? AND birth_receipt_status = 'pending'
                """, (did,))
                conn.commit()
                log.info(f"SEALED: {did} (receipt found in Ledger)")

            else:
                # Ledger does NOT have the receipt (404)
                if age < timedelta(hours=PENDING_TTL_HOURS):
                    # Within TTL -> try to re-emit
                    log.info(f"RE-EMIT: {did} (age={age}, attempting to create receipt)")

                    receipt_payload = build_birth_receipt(
                        canonical_did=did,
                        sovereign_name=sovereign_name,
                        email=email,
                        birth_timestamp=created_at
                    )

                    try:
                        success, receipt_id = post_receipt(receipt_payload)
                        if success:
                            cursor.execute("""
                                UPDATE identities
                                SET birth_receipt_status = 'sealed'
                                WHERE did = ? AND birth_receipt_status = 'pending'
                            """, (did,))
                            conn.commit()
                            log.info(f"SEALED (re-emit): {did} -> {receipt_id}")
                        else:
                            log.warning(f"RE-EMIT FAILED: {did} (POST returned error)")
                    except httpx.RequestError as e:
                        log.warning(f"RE-EMIT FAILED: {did} (Ledger unreachable: {e})")

                else:
                    # TTL expired -> DELETE + log failure
                    log.warning(f"EXPIRED: {did} (age={age} > {PENDING_TTL_HOURS}h, no receipt)")

                    # Delete identity
                    cursor.execute("DELETE FROM identities WHERE did = ?", (did,))
                    cursor.execute("DELETE FROM sessions WHERE did = ?", (did,))

                    # Log failure event
                    now = datetime.now(timezone.utc).isoformat()
                    cursor.execute("""
                        INSERT INTO login_events
                        (did, event_type, timestamp, failure_cause, ledger_synced)
                        VALUES (?, 'birth_failure', ?, 'expired_after_ttl', 0)
                    """, (did, now))

                    conn.commit()
                    log.info(f"DELETED: {did} (expired, failure logged)")

        except httpx.RequestError as e:
            # Ledger unreachable -> skip, next iteration
            log.warning(f"SKIPPED: {did} (Ledger unreachable: {e})")
            continue

    conn.close()


def sync_failures_to_ledger():
    """
    PART 2: Sync birth_failure events to Ledger (idempotent)

    For each unsynced failure:
    - Check Ledger: does failure receipt exist?
    - If YES: mark synced (no rewrite)
    - If NO: POST failure receipt, mark synced
    - If Ledger unreachable: skip, next iteration
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, did, failure_cause, timestamp
        FROM login_events
        WHERE event_type = 'birth_failure' AND ledger_synced = 0
    """)

    failures = cursor.fetchall()
    log.info(f"Found {len(failures)} failures to sync to Ledger")

    for row in failures:
        event_id = row["id"]
        did = row["did"]
        cause = row["failure_cause"]
        timestamp = row["timestamp"]

        failure_receipt_id = generate_failure_receipt_id(did)

        try:
            # IDEMPOTENCY: Check if failure receipt already exists
            exists, _ = check_receipt_exists(failure_receipt_id)

            if exists:
                # Already synced -> just mark it
                cursor.execute("""
                    UPDATE login_events SET ledger_synced = 1 WHERE id = ?
                """, (event_id,))
                conn.commit()
                log.info(f"FAILURE ALREADY SYNCED: {did}")
                continue

            # Does not exist -> POST it
            now = datetime.now(timezone.utc).isoformat()
            failure_receipt = build_failure_receipt(
                canonical_did=did,
                failure_cause=cause,
                attempted_at=timestamp,
                failed_at=now
            )

            success, receipt_id = post_receipt(failure_receipt)

            if success:
                cursor.execute("""
                    UPDATE login_events SET ledger_synced = 1 WHERE id = ?
                """, (event_id,))
                conn.commit()
                log.info(f"FAILURE SYNCED: {did} (cause: {cause})")
            else:
                log.warning(f"FAILURE SYNC FAILED: {did} (POST returned error)")

        except httpx.RequestError as e:
            log.warning(f"FAILURE SYNC SKIPPED: {did} (Ledger unreachable: {e})")
            continue

    conn.close()


def main():
    log.info("=" * 60)
    log.info("Birth Reconciler starting")
    log.info(f"DB: {DB_PATH}")
    log.info(f"Ledger: {LEDGER_URL}")
    log.info(f"TTL: {PENDING_TTL_HOURS}h")
    log.info("=" * 60)

    # Part 1: Reconcile pending births
    reconcile_pending_births()

    # Part 2: Sync failures to Ledger
    sync_failures_to_ledger()

    log.info("Birth Reconciler complete")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
