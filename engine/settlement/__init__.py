"""
WINDI Settlement Engine
========================
Commitment Liquidation API — Bridge between Forensic and Financial

Unifies:
- The VERB (what was written on the napkin)
- The ACTION (what was paid via bank transaction)

Creates cryptographic proof that a handwritten commitment
has been fulfilled through verified financial settlement.

"From intention to execution — with proof at both ends."

Version: 1.0.0
Date: 10-Feb-2026
Division: WINDI Financial Governance Division
"""

from .settlement_engine import (
    SettlementEngine,
    CommitmentRecord,
    TransactionRecord,
    SettlementReceipt,
    SettlementStatus,
    create_commitment,
    link_transaction,
    settle_commitment,
    verify_settlement
)

from .commitment_parser import (
    CommitmentParser,
    ParsedCommitment,
    CommitmentType
)

from .transaction_bridge import (
    TransactionBridge,
    BankAdapter,
    MockBankAdapter
)

__version__ = "1.0.0"
__all__ = [
    "SettlementEngine",
    "CommitmentRecord",
    "TransactionRecord",
    "SettlementReceipt",
    "SettlementStatus",
    "create_commitment",
    "link_transaction",
    "settle_commitment",
    "verify_settlement",
    "CommitmentParser",
    "ParsedCommitment",
    "CommitmentType",
    "TransactionBridge",
    "BankAdapter",
    "MockBankAdapter"
]
