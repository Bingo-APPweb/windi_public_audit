#!/usr/bin/env python3
"""
WINDI Forensic Ledger — Bundle Hash Migration + Verify Endpoint
================================================================
Apply to: /opt/windi/suite-docs/ or wherever the Ledger (:8101) script lives

Adds:
1. bundle_hash + size_bytes columns to receipts table
2. GET /api/verify/<receipt_id> endpoint for Viewer verification
"""

import sqlite3
import json
from datetime import datetime, timezone


# ============================================================
# DATABASE MIGRATION
# ============================================================

MIGRATION_SQL = """
-- Add bundle_hash column (nullable for backwards compatibility)
ALTER TABLE receipts ADD COLUMN bundle_hash TEXT;

-- Add size_bytes column (nullable)
ALTER TABLE receipts ADD COLUMN size_bytes INTEGER;

-- Index for fast lookup by receipt_id (if not already indexed)
CREATE INDEX IF NOT EXISTS idx_receipts_doc_id ON receipts(doc_id);
"""


def run_migration(db_path: str):
    """
    Run the bundle_hash migration.
    Safe to run multiple times — ALTER TABLE will fail silently if column exists.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for stmt in MIGRATION_SQL.strip().split(";"):
        stmt = stmt.strip()
        if not stmt:
            continue
        try:
            cursor.execute(stmt)
            print(f"✅ OK: {stmt[:60]}...")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print(f"⏭️  Column already exists: {stmt[:60]}...")
            else:
                print(f"❌ Error: {e}")
    
    conn.commit()
    conn.close()
    print("\nMigration complete.")


# ============================================================
# VERIFY ENDPOINT HANDLER
# ============================================================

def handle_verify(receipt_id: str, db_path: str) -> tuple:
    """
    Handler for GET /api/verify/<receipt_id>
    
    Returns (status_code, response_dict)
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Look up by doc_id (which stores the receipt_id)
    cursor.execute("""
        SELECT doc_id, integrity_hash, bundle_hash, size_bytes, 
               created_at, action, metadata_json
        FROM receipts 
        WHERE doc_id = ? AND action != 'LAW_PROBE'
        ORDER BY created_at DESC
        LIMIT 1
    """, (receipt_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return 404, {
            "error": "Receipt not found",
            "receipt_id": receipt_id,
            "status": "NOT_FOUND",
        }
    
    # Parse metadata for additional info
    metadata = {}
    if row["metadata_json"]:
        try:
            metadata = json.loads(row["metadata_json"])
        except json.JSONDecodeError:
            pass
    
    response = {
        "receipt_id": row["doc_id"],
        "content_hash": row["integrity_hash"],            # existing field
        "bundle_hash": row["bundle_hash"],                 # NEW field (may be null for legacy)
        "size_bytes": row["size_bytes"],                   # NEW field (may be null for legacy)
        "registered_at": row["created_at"],
        "action": row["action"],
        "status": "REGISTERED",
        "algorithm": "SHA-256",
        # Include content_hash from metadata as fallback
        "metadata_content_hash": metadata.get("content_hash"),
        "metadata_bundle_hash": metadata.get("bundle_hash"),
    }
    
    return 200, response


# ============================================================
# HTTP HANDLER SNIPPET (for BaseHTTPRequestHandler)
# ============================================================

HANDLER_SNIPPET = '''
# Add this to the do_GET method of your BaseHTTPRequestHandler:

# --- VERIFY ENDPOINT ---
# GET /api/verify/<receipt_id>
elif path.startswith("/api/verify/"):
    receipt_id = path.split("/api/verify/")[1].strip("/")
    if not receipt_id:
        self.send_json(400, {"error": "receipt_id required"})
        return
    
    status_code, response = handle_verify(receipt_id, DB_PATH)
    self.send_json(status_code, response)
    return
'''


# ============================================================
# RECEIPT STORAGE SNIPPET (enhanced POST /api/receipts)
# ============================================================

STORAGE_SNIPPET = '''
# When processing POST /api/receipts, extract and store bundle_hash:

bundle_hash = data.get("bundle_hash")  # May be None for legacy clients
size_bytes = data.get("size_bytes")    # May be None for legacy clients

cursor.execute("""
    INSERT INTO receipts (doc_id, action, integrity_hash, bundle_hash, size_bytes, 
                          metadata_json, ledger_entry_id, ledger_synced, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
""", (
    doc_id,
    action,
    integrity_hash,
    bundle_hash,      # NEW
    size_bytes,        # NEW
    metadata_json,
    ledger_entry_id,
    timestamp,
))
'''


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    import tempfile
    import os
    
    print("=== WINDI Forensic Ledger — Verify Endpoint Test ===\n")
    
    # Create temp DB
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_path = tmp.name
    
    try:
        # Create table
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id TEXT,
                action TEXT,
                integrity_hash TEXT,
                bundle_hash TEXT,
                size_bytes INTEGER,
                metadata_json TEXT,
                ledger_entry_id TEXT,
                ledger_synced INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)
        
        # Insert test receipt WITH bundle_hash
        conn.execute("""
            INSERT INTO receipts (doc_id, action, integrity_hash, bundle_hash, size_bytes, 
                                  metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "JMPG-20260218-TEST01",
            "JMPG_EXPORT",
            "a6816f81a95469ddbe8b9fa8e80b058f14d34ff8137e4d328e803a9c085c9183",
            "92e8b50d888efd130cb27723172748c0c3f600dc144276242375cfbde867a22a",
            1773,
            json.dumps({"title": "Test", "template": "comunicado"}),
            datetime.now(timezone.utc).isoformat(),
        ))
        
        # Insert legacy receipt WITHOUT bundle_hash
        conn.execute("""
            INSERT INTO receipts (doc_id, action, integrity_hash, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "JMPG-20260218-LEGACY",
            "JMPG_EXPORT",
            "abc123def456",
            json.dumps({"title": "Legacy"}),
            datetime.now(timezone.utc).isoformat(),
        ))
        
        conn.commit()
        conn.close()
        
        # Test: found with bundle_hash
        status, resp = handle_verify("JMPG-20260218-TEST01", db_path)
        print(f"Test 1 (with bundle_hash): HTTP {status}")
        print(f"  content_hash: {resp['content_hash'][:16]}...")
        print(f"  bundle_hash:  {resp['bundle_hash'][:16]}...")
        print(f"  size_bytes:   {resp['size_bytes']}")
        print(f"  status:       {resp['status']}")
        assert status == 200
        assert resp["bundle_hash"] is not None
        print("  ✅ PASS\n")
        
        # Test: legacy (no bundle_hash)
        status, resp = handle_verify("JMPG-20260218-LEGACY", db_path)
        print(f"Test 2 (legacy, no bundle_hash): HTTP {status}")
        print(f"  content_hash: {resp['content_hash']}")
        print(f"  bundle_hash:  {resp['bundle_hash']}")
        print(f"  status:       {resp['status']}")
        assert status == 200
        assert resp["bundle_hash"] is None  # Legacy: no bundle_hash
        print("  ✅ PASS (graceful degradation)\n")
        
        # Test: not found
        status, resp = handle_verify("NONEXISTENT", db_path)
        print(f"Test 3 (not found): HTTP {status}")
        print(f"  status: {resp['status']}")
        assert status == 404
        print("  ✅ PASS\n")
        
    finally:
        os.unlink(db_path)
    
    print("=== All Tests Passed ===")
