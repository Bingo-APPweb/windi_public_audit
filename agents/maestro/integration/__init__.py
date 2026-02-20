# WINDI Maestro — Integration Module
"""
External system integrations for Governance Orchestrator:

- forensic_ledger_writer: Immutable case event recording
- command_center_client: Human operator notifications
- governance_api_client: WINDI platform API access

Principles:
- ALL writes are append-only
- ZERO content transmission (hashes only)
- Human notification is advisory, never blocking
"""

__all__ = [
    "write_case_event",
    "notify_operator",
    "query_isp_profile"
]
