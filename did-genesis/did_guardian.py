#!/usr/bin/env python3
"""
§206 DID Guardian — Auto-Healing & Protection
==============================================
Prevents DID tree fragmentation. Runs on startup and periodically.

Rules:
1. ORACLE DIDs must have sovereign_name
2. Revoked aliases of ORACLE accounts auto-reactivate
3. Duplicate DIDs for same founder → merge to canonical
4. Sessions pointing to aliases → update to canonical DID

"A árvore não fragmenta. A seiva flui para o tronco."

Liga IA+H · Kempten, Bavaria · 26 Apr 2026
"""

import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "did_genesis.db"
LOG_PATH = Path("/opt/windi/logs/did-guardian.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [DID-GUARDIAN] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("did-guardian")

# ═══════════════════════════════════════════════════════════════════════════
#  FOUNDER PROTECTION — Human Dragon canonical DID
# ═══════════════════════════════════════════════════════════════════════════

FOUNDER_CANONICAL = "did:windi:dragon-001"
FOUNDER_ALIASES = [
    "did:windi:dc110410-993d-4395-b7e9-7dca1d08af4f",
    "did:windi:JOBER-MOGELE-CORREA-001",
    "did:windi:windi-dragon",
    "Human Dragon",
    "human-dragon",
    "human_dragon",
    "jober@a4desk.de",
]


def ensure_founder_aliases():
    """
    §206 Rule 1: All founder aliases must be active and point to canonical DID.
    Auto-heals revoked or missing aliases.
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    healed = 0

    for alias in FOUNDER_ALIASES:
        # Check if alias exists
        cursor.execute(
            "SELECT status FROM did_aliases WHERE alias_actor = ?",
            (alias,)
        )
        row = cursor.fetchone()

        if row is None:
            # Create missing alias
            alias_type = "EMAIL" if "@" in alias else ("DID" if alias.startswith("did:") else "STRING")
            cursor.execute("""
                INSERT INTO did_aliases (canonical_did, alias_actor, alias_type, status, notes)
                VALUES (?, ?, ?, 'active', '§206 DID Guardian auto-created')
            """, (FOUNDER_CANONICAL, alias, alias_type))
            log.info(f"Created missing alias: {alias} → {FOUNDER_CANONICAL}")
            healed += 1

        elif row[0] != 'active':
            # Reactivate revoked alias
            cursor.execute("""
                UPDATE did_aliases SET status = 'active',
                notes = '§206 DID Guardian auto-healed ' || datetime('now')
                WHERE alias_actor = ?
            """, (alias,))
            log.info(f"Reactivated alias: {alias} → {FOUNDER_CANONICAL}")
            healed += 1

    conn.commit()
    conn.close()
    return healed


def ensure_oracle_sovereign_names():
    """
    §206 Rule 2: All ORACLE tier DIDs must have sovereign_name.
    Prevents identity fragmentation at highest tier.
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("""
        SELECT did, display_name FROM identities
        WHERE tier = 'ORACLE' AND status = 'active'
        AND (sovereign_name IS NULL OR sovereign_name = '')
    """)

    orphans = cursor.fetchall()
    if orphans:
        log.warning(f"Found {len(orphans)} ORACLE DIDs without sovereign_name:")
        for did, name in orphans:
            log.warning(f"  - {did} ({name})")

    conn.close()
    return len(orphans)


def heal_session_aliases():
    """
    §206 Rule 3: Sessions pointing to aliases should use canonical DID.
    Prevents session fragmentation.
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Find sessions pointing to alias DIDs
    cursor.execute("""
        SELECT s.token_hash, s.did, a.canonical_did
        FROM sessions s
        JOIN did_aliases a ON s.did = a.alias_actor
        WHERE a.status = 'active' AND s.expires_at > datetime('now')
    """)

    to_heal = cursor.fetchall()
    healed = 0

    for token_hash, old_did, canonical_did in to_heal:
        cursor.execute("""
            UPDATE sessions SET did = ? WHERE token_hash = ?
        """, (canonical_did, token_hash))
        log.info(f"Healed session: {old_did[:20]}... → {canonical_did}")
        healed += 1

    conn.commit()
    conn.close()
    return healed


def run_guardian():
    """Run all guardian checks."""
    log.info("=" * 60)
    log.info("§206 DID Guardian starting...")

    # Rule 1: Founder aliases
    healed_aliases = ensure_founder_aliases()
    log.info(f"Founder aliases checked: {healed_aliases} healed")

    # Rule 2: ORACLE sovereign names
    orphan_oracles = ensure_oracle_sovereign_names()
    if orphan_oracles:
        log.warning(f"ORACLE orphans detected: {orphan_oracles}")

    # Rule 3: Session aliases
    healed_sessions = heal_session_aliases()
    log.info(f"Sessions checked: {healed_sessions} healed")

    log.info("§206 DID Guardian complete")
    log.info("=" * 60)

    return {
        "healed_aliases": healed_aliases,
        "orphan_oracles": orphan_oracles,
        "healed_sessions": healed_sessions,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


if __name__ == "__main__":
    result = run_guardian()
    print(f"Guardian result: {result}")
