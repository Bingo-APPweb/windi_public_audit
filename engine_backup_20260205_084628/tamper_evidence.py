"""
WINDI Tamper Evidence v1.0
Heritage: PoP contentHash -> integrity_hash
AI processes. Human decides. WINDI guarantees.
"""
import hashlib, json
from datetime import datetime, timezone

def compute_integrity_hash(record):
    s = json.dumps(record, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(s).hexdigest()

def seal_record(record):
    """Add sealed_at + integrity_hash. Mutates in place."""
    record["sealed_at"] = datetime.now(timezone.utc).isoformat()
    record["integrity_hash"] = compute_integrity_hash(record)
    return record

def verify_record(record):
    """Returns (is_valid, message)."""
    if "integrity_hash" not in record:
        return False, "No integrity hash. Not sealed."
    stored = record["integrity_hash"]
    check = {k: v for k, v in record.items() if k != "integrity_hash"}
    expected = compute_integrity_hash(check)
    if stored == expected:
        return True, "Integrity verified."
    return False, f"TAMPER DETECTED. Stored: {stored[:16]}... Expected: {expected[:16]}..."
