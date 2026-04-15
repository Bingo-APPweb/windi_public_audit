#!/usr/bin/env python3
"""
§173 IDENTITY MIGRATION LOG
============================
Rastreabilidade histórica da unificação ontológica.

"Não para o usuário. Para vocês."

Liga IA+H · Kempten, Bavaria · 2026
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Literal

LOG_DIR = Path("/opt/windi/logs/identity-migration")
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "migration_log.jsonl"

MigrationStatus = Literal["mapped", "orphan", "conflict", "deprecated", "migrated"]


def log_identity_transition(
    old_key: str,
    new_key: str,
    old_value: Optional[str],
    new_value: Optional[str],
    status: MigrationStatus,
    source_file: str,
    service: str,
    notes: str = ""
) -> dict:
    """
    Log an identity key transition.

    Example:
        log_identity_transition(
            old_key="windi_travel_wallet",
            new_key="windi_did",
            old_value="WALLET-20260215-0001",
            new_value="did:windi:dragon-001",
            status="mapped",
            source_file="/opt/windi/windi-travel/gate.html",
            service="WINDI-TRAVEL",
            notes="Gate template migrated"
        )
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "old_key": old_key,
        "new_key": new_key,
        "old_value": old_value[:50] + "..." if old_value and len(old_value) > 50 else old_value,
        "new_value": new_value[:50] + "..." if new_value and len(new_value) > 50 else new_value,
        "status": status,
        "source_file": source_file,
        "service": service,
        "notes": notes,
        "section": "§173"
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return entry


def log_function_deprecation(
    old_function: str,
    new_function: str,
    source_file: str,
    service: str,
    status: MigrationStatus = "deprecated"
) -> dict:
    """
    Log a function deprecation/migration.

    Example:
        log_function_deprecation(
            old_function="is_valid_windi_did()",
            new_function="shared.did_validator.validate_did()",
            source_file="/opt/windi/windi-travel/gate.py",
            service="WINDI-TRAVEL"
        )
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "function_migration",
        "old_function": old_function,
        "new_function": new_function,
        "source_file": source_file,
        "service": service,
        "status": status,
        "section": "§173"
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return entry


def get_migration_summary() -> dict:
    """Get summary of all migrations."""
    if not LOG_FILE.exists():
        return {"total": 0, "by_status": {}, "by_service": {}}

    entries = []
    with open(LOG_FILE, "r") as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))

    by_status = {}
    by_service = {}

    for e in entries:
        status = e.get("status", "unknown")
        service = e.get("service", "unknown")

        by_status[status] = by_status.get(status, 0) + 1
        by_service[service] = by_service.get(service, 0) + 1

    return {
        "total": len(entries),
        "by_status": by_status,
        "by_service": by_service,
        "last_entry": entries[-1] if entries else None
    }


# CLI usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        print(json.dumps(get_migration_summary(), indent=2))
    else:
        print(f"Migration log: {LOG_FILE}")
        print(f"Summary: python {__file__} summary")
