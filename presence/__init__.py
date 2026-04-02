"""
W-PRESENCE-001 — Presence Seal Protocol
WINDI Publishing House · Kempten, Bavaria

"Presence is not detected. It is declared and sealed."
"""

from .presence_seal import (
    # Core functions
    seal_presence,
    compose_presence_payload,
    calculate_content_hash,
    classify_presence_level,
    seal_presence_to_ledger,
    save_presence_index,

    # Query functions
    get_presence_by_did,
    get_presence_by_receipt,

    # Dataclasses
    PresencePayload,
    Location,
    Evidence,
    SealResult,
)

__version__ = "1.0.0"
__module__ = "W-PRESENCE-001"
