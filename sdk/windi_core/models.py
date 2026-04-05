"""
WINDI SDK v1.0 — Data Models

Canonical structures for the WINDI Core Protocol.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class SealResult:
    """Result of a seal operation (I9 Gate)."""
    ok: bool
    content_hash: Optional[str] = None
    artifact_path: Optional[str] = None
    wallet_id: Optional[str] = None
    human_approved: bool = False
    timestamp: Optional[datetime] = None
    error: Optional[str] = None

    @property
    def ready_for_ledger(self) -> bool:
        """Check if seal is ready for ledger anchoring."""
        return self.ok and self.human_approved and self.content_hash is not None


@dataclass
class LedgerReceipt:
    """Receipt from Ledger anchoring (I11)."""
    ok: bool
    receipt_id: Optional[str] = None
    content_hash: Optional[str] = None
    verify_url: Optional[str] = None
    timestamp: Optional[datetime] = None
    governance_level: str = "HIGH"
    invariants: list = field(default_factory=lambda: ["I9", "I11"])
    error: Optional[str] = None

    @property
    def short_id(self) -> str:
        """Get shortened receipt ID for display."""
        if self.receipt_id and len(self.receipt_id) > 20:
            return f"{self.receipt_id[:20]}..."
        return self.receipt_id or ""


@dataclass
class JMPGResult:
    """Result of JMPG proof card rendering."""
    ok: bool
    receipt_id: Optional[str] = None
    image_path: Optional[str] = None
    image_url: Optional[str] = None
    verify_url: Optional[str] = None
    profile: str = "telegram_square"
    error: Optional[str] = None


@dataclass
class DistributeResult:
    """Result of distribution operation."""
    ok: bool
    channel: str
    receipt_id: Optional[str] = None
    image_url: Optional[str] = None
    message_id: Optional[int] = None
    telegram_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class WindiProduct:
    """Base configuration for a WINDI product."""
    name: str
    code: str  # e.g., "VD-CUT", "LAW", "TRAVEL"
    port: int
    description: str
    artifact_types: list  # e.g., ["video/mp4", "application/pdf"]
    invariants: list = field(default_factory=lambda: ["I9", "I11"])

    def __post_init__(self):
        # Ensure code is uppercase
        self.code = self.code.upper()
