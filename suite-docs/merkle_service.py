#!/usr/bin/env python3
"""
WINDI Merkle Transparency Log — Data Layer
============================================
G3 Merkle implementation for the Forensic Ledger.
Binary Merkle tree with deterministic leaf ordering.

Invariants:
  - I9:  Bootstrap requires human_approved=true
  - I11: Root hash is IRREMEDIÁVEL once published
  - I14: Hash mismatch = explicit error, no silent retry

Canonical Leaf Ordering (Q3-bis):
  ORDER BY created_at ASC, rowid ASC

Leaf Formula:
  leaf_hash = sha256(receipt_id + ":" + content_hash)

Author:  Architect (CCode Opus 4.5)
Date:    2026-05-15
Sprint:  §246-IMPL-bis G3 MERKLE
"""

import os
import sqlite3
import hashlib
import time
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════

DEFAULT_DB_PATH = os.environ.get(
    "WINDI_LEDGER_DB",
    "/opt/windi/data/forensic_ledger.sqlite3"
)

# ═══════════════════════════════════════════════════════════════════
# Schema — Merkle Log Tables (append-only)
# ═══════════════════════════════════════════════════════════════════

MERKLE_DDL = """
-- Folhas do log (append-only, I11)
CREATE TABLE IF NOT EXISTS merkle_log (
    leaf_index    INTEGER PRIMARY KEY,    -- 0-based, canónico
    receipt_id    TEXT NOT NULL UNIQUE,   -- FK to receipts.id
    leaf_hash     TEXT NOT NULL,          -- sha256(receipt_id:content_hash)
    root_at_leaf  TEXT NOT NULL,          -- Raiz quando esta folha entrou
    created_at    INTEGER NOT NULL
);

-- Histórico de raízes (nunca apagar — I11)
CREATE TABLE IF NOT EXISTS merkle_roots (
    root_hash     TEXT PRIMARY KEY,
    leaf_count    INTEGER NOT NULL,
    created_at    INTEGER NOT NULL,
    status        TEXT DEFAULT 'active',  -- active|superseded
    predecessor   TEXT                    -- FK anterior (lineage)
);

CREATE INDEX IF NOT EXISTS idx_merkle_log_receipt ON merkle_log(receipt_id);
CREATE INDEX IF NOT EXISTS idx_merkle_roots_status ON merkle_roots(status);
"""

# ═══════════════════════════════════════════════════════════════════
# Connection
# ═══════════════════════════════════════════════════════════════════

def _connect(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Get a connection with Row factory."""
    con = sqlite3.connect(db_path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def init_merkle_tables(db_path: str = DEFAULT_DB_PATH) -> None:
    """Create Merkle tables if they don't exist."""
    con = _connect(db_path)
    try:
        con.executescript(MERKLE_DDL)
        con.commit()
        print(f"[MERKLE] Tables ready: {db_path}")
    finally:
        con.close()


# ═══════════════════════════════════════════════════════════════════
# Cryptographic Primitives
# ═══════════════════════════════════════════════════════════════════

def sha256_hex(data: bytes) -> str:
    """SHA-256 hash → hex string."""
    return hashlib.sha256(data).hexdigest()


def compute_leaf_hash(receipt_id: str, content_hash: str) -> str:
    """
    Compute leaf hash for a receipt.
    Formula: sha256(receipt_id + ":" + content_hash)

    The ":" separator prevents collision between:
      id="A", hash="BC" vs id="AB", hash="C"
    """
    payload = f"{receipt_id}:{content_hash}"
    return sha256_hex(payload.encode("utf-8"))


def compute_parent_hash(left: str, right: str) -> str:
    """
    Compute parent node hash from two children.
    Formula: sha256(left + right)

    Note: left and right are already hex strings.
    """
    payload = left + right
    return sha256_hex(payload.encode("utf-8"))


# ═══════════════════════════════════════════════════════════════════
# Merkle Tree Computation
# ═══════════════════════════════════════════════════════════════════

def compute_merkle_root(leaf_hashes: List[str]) -> str:
    """
    Compute Merkle root from list of leaf hashes.
    Binary tree, bottom-up construction.

    If odd number of nodes at any level, duplicate the last node.
    Empty list returns hash of empty string.

    Args:
        leaf_hashes: List of hex hash strings

    Returns:
        Root hash as hex string
    """
    if not leaf_hashes:
        return sha256_hex(b"")

    # Start with leaves
    current_level = list(leaf_hashes)

    # Build tree bottom-up
    while len(current_level) > 1:
        next_level = []

        # Process pairs
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            # If odd, duplicate last node
            right = current_level[i + 1] if i + 1 < len(current_level) else left
            parent = compute_parent_hash(left, right)
            next_level.append(parent)

        current_level = next_level

    return current_level[0]


def compute_proof(leaf_index: int, leaf_hashes: List[str]) -> List[Dict[str, Any]]:
    """
    Compute Merkle proof (sibling path) for a leaf.

    Args:
        leaf_index: 0-based index of the leaf
        leaf_hashes: Full list of leaf hashes

    Returns:
        List of {position: "left"|"right", hash: str}
    """
    if not leaf_hashes or leaf_index < 0 or leaf_index >= len(leaf_hashes):
        return []

    proof = []
    current_level = list(leaf_hashes)
    idx = leaf_index

    while len(current_level) > 1:
        next_level = []

        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i + 1] if i + 1 < len(current_level) else left
            parent = compute_parent_hash(left, right)
            next_level.append(parent)

            # If this pair contains our target node
            if i == (idx // 2) * 2:
                if idx % 2 == 0:
                    # We're on the left, sibling is on the right
                    sibling = right
                    position = "right"
                else:
                    # We're on the right, sibling is on the left
                    sibling = left
                    position = "left"

                # Only add if sibling is different (not duplicated odd case)
                if sibling != current_level[idx]:
                    proof.append({"position": position, "hash": sibling})
                elif i + 1 >= len(current_level):
                    # Odd case: sibling is duplicate of self
                    proof.append({"position": position, "hash": sibling})

        current_level = next_level
        idx = idx // 2

    return proof


def verify_proof(
    leaf_hash: str,
    proof: List[Dict[str, Any]],
    root_hash: str
) -> bool:
    """
    Verify a Merkle proof.

    Args:
        leaf_hash: The leaf hash to verify
        proof: The sibling path
        root_hash: The expected root

    Returns:
        True if proof is valid
    """
    current = leaf_hash

    for step in proof:
        sibling = step["hash"]
        if step["position"] == "left":
            current = compute_parent_hash(sibling, current)
        else:
            current = compute_parent_hash(current, sibling)

    return current == root_hash


# ═══════════════════════════════════════════════════════════════════
# Bootstrap Functions
# ═══════════════════════════════════════════════════════════════════

def get_receipts_for_bootstrap(db_path: str = DEFAULT_DB_PATH) -> List[Tuple[int, str, str]]:
    """
    Get all receipts in canonical order for bootstrap.

    Canonical order (Q3-bis): ORDER BY created_at ASC, rowid ASC

    Returns:
        List of (rowid, receipt_id, content_hash) tuples
    """
    con = _connect(db_path)
    try:
        rows = con.execute("""
            SELECT rowid, id, content_hash
            FROM receipts
            ORDER BY created_at ASC, rowid ASC
        """).fetchall()

        return [(r["rowid"], r["id"], r["content_hash"]) for r in rows]
    finally:
        con.close()


def bootstrap_dry_run(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """
    Bootstrap the Merkle tree in DRY RUN mode.
    Computes the genesis root WITHOUT persisting to database.

    This is step 3 of the implementation flow.

    Returns:
        {
            "status": "dry_run",
            "leaf_count": int,
            "root_hash": str,
            "first_leaf": {...},
            "last_leaf": {...},
            "ordering": "created_at ASC, rowid ASC"
        }
    """
    print("[MERKLE] Starting bootstrap dry run...")

    # Get receipts in canonical order
    receipts = get_receipts_for_bootstrap(db_path)
    leaf_count = len(receipts)

    if leaf_count == 0:
        return {
            "status": "dry_run",
            "error": "no_receipts",
            "leaf_count": 0
        }

    print(f"[MERKLE] Found {leaf_count} receipts in canonical order")

    # Compute all leaf hashes
    leaf_hashes = []
    first_leaf = None
    last_leaf = None

    for i, (rowid, receipt_id, content_hash) in enumerate(receipts):
        leaf_hash = compute_leaf_hash(receipt_id, content_hash)
        leaf_hashes.append(leaf_hash)

        if i == 0:
            first_leaf = {
                "index": 0,
                "rowid": rowid,
                "receipt_id": receipt_id,
                "leaf_hash": leaf_hash[:16] + "..."
            }

        if i == leaf_count - 1:
            last_leaf = {
                "index": i,
                "rowid": rowid,
                "receipt_id": receipt_id,
                "leaf_hash": leaf_hash[:16] + "..."
            }

        # Progress every 10000
        if (i + 1) % 10000 == 0:
            print(f"[MERKLE] Processed {i + 1}/{leaf_count} leaves...")

    # Compute root
    print("[MERKLE] Computing Merkle root...")
    root_hash = compute_merkle_root(leaf_hashes)

    print(f"[MERKLE] DRY RUN COMPLETE")
    print(f"[MERKLE] Genesis root: {root_hash}")

    return {
        "status": "dry_run",
        "leaf_count": leaf_count,
        "root_hash": root_hash,
        "first_leaf": first_leaf,
        "last_leaf": last_leaf,
        "ordering": "created_at ASC, rowid ASC",
        "invariant": "Q3-bis"
    }


def bootstrap_persist(
    human_approved: bool,
    db_path: str = DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """
    Bootstrap the Merkle tree and PERSIST to database.

    CONSTITUTIONAL GATE (I9):
    This function REQUIRES human_approved=True.
    The genesis root becomes IRREMEDIÁVEL (I11) once persisted.

    Args:
        human_approved: MUST be True for I9 compliance
        db_path: Database path

    Returns:
        Result dict with root_hash and leaf_count
    """
    # I9 GATE
    if not human_approved:
        return {
            "status": "blocked",
            "error": "I9_GATE_HUMAN_APPROVAL_REQUIRED",
            "message": "Bootstrap requires explicit human approval",
            "invariant": "I9"
        }

    print("[MERKLE] Starting bootstrap with persistence...")
    print("[MERKLE] I9 GATE: human_approved=True")

    # Get receipts in canonical order
    receipts = get_receipts_for_bootstrap(db_path)
    leaf_count = len(receipts)

    if leaf_count == 0:
        return {
            "status": "error",
            "error": "no_receipts",
            "leaf_count": 0
        }

    print(f"[MERKLE] Found {leaf_count} receipts")

    # Compute all leaf hashes and build tree
    leaf_hashes = []
    leaves_to_insert = []
    now = int(time.time())

    for i, (rowid, receipt_id, content_hash) in enumerate(receipts):
        leaf_hash = compute_leaf_hash(receipt_id, content_hash)
        leaf_hashes.append(leaf_hash)
        leaves_to_insert.append((i, receipt_id, leaf_hash, now))

        if (i + 1) % 10000 == 0:
            print(f"[MERKLE] Processed {i + 1}/{leaf_count} leaves...")

    # Compute root
    print("[MERKLE] Computing Merkle root...")
    root_hash = compute_merkle_root(leaf_hashes)

    print(f"[MERKLE] Genesis root: {root_hash}")
    print("[MERKLE] Persisting to database...")

    # Persist
    con = _connect(db_path)
    try:
        # Insert root first
        con.execute("""
            INSERT INTO merkle_roots (root_hash, leaf_count, created_at, status, predecessor)
            VALUES (?, ?, ?, 'active', NULL)
        """, (root_hash, leaf_count, now))

        # Insert all leaves with root_at_leaf
        con.executemany("""
            INSERT INTO merkle_log (leaf_index, receipt_id, leaf_hash, root_at_leaf, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, [(idx, rid, lh, root_hash, ts) for idx, rid, lh, ts in leaves_to_insert])

        con.commit()
        print(f"[MERKLE] Persisted {leaf_count} leaves and genesis root")

    finally:
        con.close()

    return {
        "status": "persisted",
        "leaf_count": leaf_count,
        "root_hash": root_hash,
        "invariant": "I11 — IRREMEDIÁVEL",
        "created_at": now
    }


# ═══════════════════════════════════════════════════════════════════
# Query Functions
# ═══════════════════════════════════════════════════════════════════

def get_current_root(db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Get the current active Merkle root."""
    con = _connect(db_path)
    try:
        row = con.execute("""
            SELECT root_hash, leaf_count, created_at, predecessor
            FROM merkle_roots
            WHERE status = 'active'
            ORDER BY created_at DESC
            LIMIT 1
        """).fetchone()

        if not row:
            return None

        return dict(row)
    finally:
        con.close()


def get_leaf_by_receipt(
    receipt_id: str,
    db_path: str = DEFAULT_DB_PATH
) -> Optional[Dict[str, Any]]:
    """Get leaf info for a receipt."""
    con = _connect(db_path)
    try:
        row = con.execute("""
            SELECT leaf_index, receipt_id, leaf_hash, root_at_leaf, created_at
            FROM merkle_log
            WHERE receipt_id = ?
        """, (receipt_id,)).fetchone()

        if not row:
            return None

        return dict(row)
    finally:
        con.close()


def get_all_leaf_hashes(db_path: str = DEFAULT_DB_PATH) -> List[str]:
    """Get all leaf hashes in order (for proof computation)."""
    con = _connect(db_path)
    try:
        rows = con.execute("""
            SELECT leaf_hash
            FROM merkle_log
            ORDER BY leaf_index ASC
        """).fetchall()

        return [r["leaf_hash"] for r in rows]
    finally:
        con.close()


def get_proof_for_receipt(
    receipt_id: str,
    db_path: str = DEFAULT_DB_PATH
) -> Optional[Dict[str, Any]]:
    """
    Get Merkle proof for a receipt.

    Returns:
        {
            "receipt_id": str,
            "leaf_index": int,
            "leaf_hash": str,
            "proof": [...],
            "root_hash": str
        }
    """
    leaf = get_leaf_by_receipt(receipt_id, db_path)
    if not leaf:
        return None

    root = get_current_root(db_path)
    if not root:
        return None

    # Get all leaves for proof computation
    all_hashes = get_all_leaf_hashes(db_path)

    # Compute proof
    proof = compute_proof(leaf["leaf_index"], all_hashes)

    return {
        "receipt_id": receipt_id,
        "leaf_index": leaf["leaf_index"],
        "leaf_hash": leaf["leaf_hash"],
        "proof": proof,
        "root_hash": root["root_hash"],
        "root_at_leaf": leaf["root_at_leaf"]
    }


# ═══════════════════════════════════════════════════════════════════
# CLI Interface
# ═══════════════════════════════════════════════════════════════════

def main():
    """CLI entry point."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: merkle_service.py <command>")
        print("")
        print("Commands:")
        print("  init        - Create Merkle tables")
        print("  dry-run     - Bootstrap dry run (no persistence)")
        print("  status      - Show current Merkle state")
        print("  proof <id>  - Get proof for receipt")
        print("")
        print("Invariants: I9 (human approval), I11 (irremediável), I14 (explicit)")
        return

    cmd = sys.argv[1]

    if cmd == "init":
        init_merkle_tables()

    elif cmd == "dry-run":
        result = bootstrap_dry_run()
        import json
        print(json.dumps(result, indent=2))

    elif cmd == "status":
        root = get_current_root()
        if root:
            print(f"Active root: {root['root_hash']}")
            print(f"Leaf count:  {root['leaf_count']}")
            print(f"Created:     {root['created_at']}")
        else:
            print("No active Merkle root. Run bootstrap first.")

    elif cmd == "proof" and len(sys.argv) > 2:
        receipt_id = sys.argv[2]
        result = get_proof_for_receipt(receipt_id)
        if result:
            import json
            print(json.dumps(result, indent=2))
        else:
            print(f"No proof found for receipt: {receipt_id}")

    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
