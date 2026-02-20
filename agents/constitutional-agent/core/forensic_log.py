"""
WINDI Forensic Log — Hash-Chained Immutable Event Log
========================================================
Every Agent operation generates an append-only, hash-chained log entry.
Each entry includes the hash of the previous entry, creating a
tamper-evident chain that any auditor can verify.

"If an entry is modified, every subsequent hash breaks."
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


GENESIS_HASH = "0" * 64  # The first entry's prev_hash


@dataclass
class ForensicEntry:
    """A single entry in the hash-chained forensic log."""
    sequence: int
    prev_hash: str
    timestamp: str
    monotonic_ns: int
    operation: str
    detail: Dict[str, Any]
    agent_version: str
    config_hash: str
    entry_hash: str = ""
    
    def compute_hash(self) -> str:
        """Compute this entry's hash from all fields."""
        payload = json.dumps({
            "sequence": self.sequence,
            "prev_hash": self.prev_hash,
            "timestamp": self.timestamp,
            "monotonic_ns": self.monotonic_ns,
            "operation": self.operation,
            "detail_hash": hashlib.sha256(
                json.dumps(self.detail, sort_keys=True, default=str).encode()
            ).hexdigest(),
            "agent_version": self.agent_version,
            "config_hash": self.config_hash,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sequence": self.sequence,
            "prev_hash": self.prev_hash,
            "timestamp": self.timestamp,
            "monotonic_ns": self.monotonic_ns,
            "operation": self.operation,
            "detail": self.detail,
            "agent_version": self.agent_version,
            "config_hash": self.config_hash,
            "entry_hash": self.entry_hash,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


class ForensicLog:
    """
    Hash-chained, append-only forensic log.
    
    Properties:
    - Append-only: entries cannot be modified or deleted
    - Hash-chained: each entry includes prev_hash, forming tamper-evident chain
    - Timestamped: ISO + monotonic nanoseconds for ordering
    - Verifiable: any auditor can recompute the chain
    
    Retention: 7 years minimum (HGB §257, EU AI Act)
    """
    
    def __init__(
        self,
        log_dir: str,
        agent_version: str = "1.0.0",
        config_hash: str = "",
    ):
        self.log_dir = log_dir
        self.agent_version = agent_version
        self.config_hash = config_hash
        self.sequence = 0
        self.last_hash = GENESIS_HASH
        self.entries: List[ForensicEntry] = []
        
        os.makedirs(log_dir, exist_ok=True)
        
        # Load existing chain if present
        self._load_chain()
    
    def append(self, operation: str, detail: Dict[str, Any] = None) -> ForensicEntry:
        """
        Append a new entry to the forensic log.
        
        The entry is immediately written to disk.
        Returns the entry with computed hash.
        """
        self.sequence += 1
        
        entry = ForensicEntry(
            sequence=self.sequence,
            prev_hash=self.last_hash,
            timestamp=time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime()),
            monotonic_ns=time.monotonic_ns(),
            operation=operation,
            detail=detail or {},
            agent_version=self.agent_version,
            config_hash=self.config_hash,
        )
        
        entry.entry_hash = entry.compute_hash()
        self.last_hash = entry.entry_hash
        self.entries.append(entry)
        
        # Write to disk immediately (append mode)
        self._write_entry(entry)
        
        return entry
    
    def verify_chain(self) -> Dict[str, Any]:
        """
        Verify the integrity of the entire hash chain.
        
        Returns verification report.
        """
        if not self.entries:
            return {"valid": True, "entries_checked": 0, "detail": "Empty chain"}
        
        errors = []
        prev_hash = GENESIS_HASH
        
        for i, entry in enumerate(self.entries):
            # Check prev_hash links
            if entry.prev_hash != prev_hash:
                errors.append({
                    "sequence": entry.sequence,
                    "error": "prev_hash mismatch",
                    "expected": prev_hash,
                    "found": entry.prev_hash,
                })
            
            # Recompute and verify entry hash
            recomputed = entry.compute_hash()
            if entry.entry_hash != recomputed:
                errors.append({
                    "sequence": entry.sequence,
                    "error": "entry_hash mismatch",
                    "expected": recomputed,
                    "found": entry.entry_hash,
                })
            
            prev_hash = entry.entry_hash
        
        return {
            "valid": len(errors) == 0,
            "entries_checked": len(self.entries),
            "errors": errors,
            "chain_head": self.last_hash,
            "chain_genesis": GENESIS_HASH,
        }
    
    def get_log_path(self) -> str:
        """Get today's log file path."""
        date_str = time.strftime('%Y-%m-%d', time.gmtime())
        return os.path.join(self.log_dir, f"agent_{date_str}.jsonl")
    
    def _write_entry(self, entry: ForensicEntry):
        """Write entry to disk (append mode)."""
        log_path = self.get_log_path()
        with open(log_path, 'a') as f:
            f.write(entry.to_json() + "\n")
    
    def _load_chain(self):
        """Load existing chain from disk to restore state."""
        log_path = self.get_log_path()
        if not os.path.exists(log_path):
            return
        
        try:
            with open(log_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    entry = ForensicEntry(
                        sequence=data["sequence"],
                        prev_hash=data["prev_hash"],
                        timestamp=data["timestamp"],
                        monotonic_ns=data["monotonic_ns"],
                        operation=data["operation"],
                        detail=data["detail"],
                        agent_version=data["agent_version"],
                        config_hash=data["config_hash"],
                        entry_hash=data["entry_hash"],
                    )
                    self.entries.append(entry)
                    self.sequence = entry.sequence
                    self.last_hash = entry.entry_hash
        except (json.JSONDecodeError, KeyError, OSError):
            pass  # Start fresh if log is corrupted
