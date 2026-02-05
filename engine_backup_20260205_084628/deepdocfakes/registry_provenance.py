"""
WINDI DeepDOCFakes — Registry Provenance
==========================================
Registry management for provenance records.

HIGH documents: provenance registration REQUIRED.
MEDIUM documents: provenance registration OPTIONAL.
LOW documents: provenance registration NOT AVAILABLE.

The registry provides:
1. Fast lookup by submission_id
2. Lookup by structural hash prefix
3. Statistics and audit reports
4. Batch verification support
"""

import os
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

PROV_DIR = os.environ.get("WINDI_PROVENANCE_DIR", "/opt/windi/provenance")
INDEX_FILE = os.path.join(PROV_DIR, "index.json")
RECORDS_DIR = os.path.join(PROV_DIR, "records")


def _load_index() -> Dict[str, Any]:
    if not os.path.exists(INDEX_FILE):
        return {}
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {}


def registry_stats() -> Dict[str, Any]:
    """
    Return statistics about the provenance registry.
    Useful for governance dashboards and audit reports.
    """
    idx = _load_index()
    
    if not idx:
        return {
            "total_records": 0,
            "by_level": {},
            "avg_resilience": 0,
            "last_updated": None
        }
    
    by_level = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "OTHER": 0}
    scores = []
    latest = None
    
    for sid, entry in idx.items():
        level = entry.get("governance_level", "OTHER")
        by_level[level] = by_level.get(level, 0) + 1
        
        score = entry.get("resilience_score", 0)
        scores.append(score)
        
        updated = entry.get("updated_at")
        if updated and (latest is None or updated > latest):
            latest = updated
    
    avg = sum(scores) / len(scores) if scores else 0
    
    return {
        "total_records": len(idx),
        "by_level": {k: v for k, v in by_level.items() if v > 0},
        "avg_resilience_score": round(avg, 1),
        "min_resilience_score": min(scores) if scores else 0,
        "max_resilience_score": max(scores) if scores else 0,
        "last_updated": latest,
        "protocol": "WINDI-SOF-v1"
    }


def list_records(
    governance_level: Optional[str] = None,
    min_resilience: Optional[int] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    List provenance records with optional filtering.
    
    Args:
        governance_level: Filter by level (HIGH, MEDIUM, LOW)
        min_resilience: Minimum resilience score
        limit: Maximum number of records to return
    """
    idx = _load_index()
    results = []
    
    for sid, entry in idx.items():
        # Level filter
        if governance_level and entry.get("governance_level") != governance_level.upper():
            continue
        
        # Resilience filter
        if min_resilience and entry.get("resilience_score", 0) < min_resilience:
            continue
        
        results.append({
            "submission_id": sid,
            **entry
        })
        
        if len(results) >= limit:
            break
    
    # Sort by update time (newest first)
    results.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    
    return results


def find_by_hash_prefix(hash_prefix: str) -> Optional[Dict[str, Any]]:
    """
    Find a record by structural hash prefix.
    Useful for verification from PDF metadata where only the hash is available.
    """
    idx = _load_index()
    
    for sid, entry in idx.items():
        if entry.get("structural_hash", "").startswith(hash_prefix):
            return {"submission_id": sid, **entry}
    
    return None


def registry_integrity_check() -> Dict[str, Any]:
    """
    Verify the integrity of the provenance registry itself.
    
    Checks:
    1. Index file is valid JSON
    2. All referenced record files exist
    3. No orphaned record files
    4. Hash consistency between index and records
    """
    result = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "issues": [],
        "records_checked": 0,
        "records_valid": 0,
        "orphaned_files": []
    }
    
    # Check index
    idx = _load_index()
    if not idx:
        result["issues"].append("index_empty_or_missing")
        return result
    
    # Check each indexed record
    for sid, entry in idx.items():
        result["records_checked"] += 1
        record_path = entry.get("record_path")
        
        if not record_path:
            result["issues"].append(f"missing_record_path: {sid}")
            continue
        
        if not os.path.exists(record_path):
            result["issues"].append(f"record_file_missing: {sid} → {record_path}")
            continue
        
        # Verify record is valid JSON
        try:
            with open(record_path, "r", encoding="utf-8") as f:
                record = json.load(f)
            
            # Verify hash consistency
            stored_hash = entry.get("structural_hash")
            record_hash = record.get("cryptographic_proof", {}).get("structural_hash")
            
            if stored_hash and record_hash and stored_hash != record_hash:
                result["issues"].append(f"hash_mismatch: {sid}")
                continue
            
            result["records_valid"] += 1
            
        except json.JSONDecodeError:
            result["issues"].append(f"invalid_json: {sid} → {record_path}")
    
    # Check for orphaned files
    if os.path.exists(RECORDS_DIR):
        indexed_paths = {entry.get("record_path") for entry in idx.values()}
        for fname in os.listdir(RECORDS_DIR):
            fpath = os.path.join(RECORDS_DIR, fname)
            if fpath not in indexed_paths and fname.endswith(".json"):
                result["orphaned_files"].append(fpath)
    
    result["status"] = "HEALTHY" if not result["issues"] else "ISSUES_FOUND"
    
    return result
