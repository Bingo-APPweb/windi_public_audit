"""
WINDI ID Genesis — Forensic Ledger (Append-Only Hash Chain)
Three Dragons Protocol v1.1 · I1-I9 Active

Immutable audit trail for governance events.
Each entry is cryptographically chained to the previous one.
NO PII is stored in the ledger — only governance metadata and hashes.

Structure per entry:
  seq         - Sequential number
  ts          - ISO timestamp
  event       - Event type (LEAD_RECEIVED, GENESIS, ACTIVATION, REVOCATION)
  entity_id   - lead_id or windi_id (not PII)
  payload     - Governance metadata (no PII)
  prev_hash   - SHA-256 of previous entry
  hash        - SHA-256 of this entry
"""
import json
import hashlib
import os
from datetime import datetime, timezone
from config import LEDGER_PATH

# ── Event Types ──
EVENT_LEAD_RECEIVED = "LEAD_RECEIVED"
EVENT_GENESIS = "WINDI_ID_GENESIS"
EVENT_ACTIVATION = "WINDI_ID_ACTIVATION"
EVENT_REVOCATION = "WINDI_ID_REVOCATION"
EVENT_SYSTEM = "SYSTEM"

def _compute_hash(entry: dict) -> str:
    """Compute SHA-256 hash of an entry (excluding the hash field itself)."""
    data = {k: v for k, v in entry.items() if k != "hash"}
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def _get_last_entry() -> dict | None:
    """Read the last entry from the ledger file."""
    if not os.path.exists(LEDGER_PATH):
        return None
    with open(LEDGER_PATH, "r") as f:
        last_line = None
        for line in f:
            line = line.strip()
            if line:
                last_line = line
        if last_line:
            return json.loads(last_line)
    return None

def _get_next_seq() -> int:
    """Get the next sequence number."""
    last = _get_last_entry()
    return (last["seq"] + 1) if last else 1

def append(event: str, entity_id: str, payload: dict = None) -> dict:
    """
    Append a new entry to the forensic ledger.
    Returns the new entry with its hash.
    
    CRITICAL: payload must NEVER contain PII (name, email, etc.)
    Only governance metadata: status, interest, key_fingerprint, etc.
    """
    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    
    last = _get_last_entry()
    prev_hash = last["hash"] if last else "0" * 64  # Genesis block

    entry = {
        "seq": _get_next_seq(),
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "entity_id": entity_id,
        "payload": payload or {},
        "prev_hash": prev_hash,
    }
    entry["hash"] = _compute_hash(entry)

    with open(LEDGER_PATH, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return entry

def verify_chain() -> dict:
    """
    Verify the integrity of the entire ledger chain.
    Returns: { valid: bool, entries: int, errors: [] }
    """
    if not os.path.exists(LEDGER_PATH):
        return {"valid": True, "entries": 0, "errors": []}

    errors = []
    prev_hash = "0" * 64
    count = 0

    with open(LEDGER_PATH, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                errors.append(f"Line {line_num}: Invalid JSON")
                continue

            count += 1

            # Verify prev_hash chain
            if entry.get("prev_hash") != prev_hash:
                errors.append(
                    f"Line {line_num}: Chain broken. Expected prev_hash={prev_hash[:16]}..., "
                    f"got {entry.get('prev_hash', 'MISSING')[:16]}..."
                )

            # Verify self-hash
            expected_hash = _compute_hash(entry)
            if entry.get("hash") != expected_hash:
                errors.append(
                    f"Line {line_num}: Hash mismatch. Expected {expected_hash[:16]}..., "
                    f"got {entry.get('hash', 'MISSING')[:16]}..."
                )

            prev_hash = entry.get("hash", "")

    return {
        "valid": len(errors) == 0,
        "entries": count,
        "last_hash": prev_hash[:16] + "..." if prev_hash else None,
        "errors": errors,
    }

def get_entries(event_type: str = None, entity_id: str = None, limit: int = 50) -> list:
    """Read ledger entries with optional filters."""
    if not os.path.exists(LEDGER_PATH):
        return []

    entries = []
    with open(LEDGER_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if event_type and entry.get("event") != event_type:
                continue
            if entity_id and entry.get("entity_id") != entity_id:
                continue
            entries.append(entry)

    return entries[-limit:]  # Return last N entries

def count_entries() -> int:
    """Count total ledger entries."""
    if not os.path.exists(LEDGER_PATH):
        return 0
    count = 0
    with open(LEDGER_PATH, "r") as f:
        for line in f:
            if line.strip():
                count += 1
    return count
