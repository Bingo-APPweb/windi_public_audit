"""
WINDI Settlement Engine — Commitment Liquidation
=================================================
Orchestrates the binding of forensic documents to financial transactions.

Core operations:
1. CREATE: Register commitment from PixWindi document
2. LINK: Associate bank transaction with commitment
3. SETTLE: Confirm fulfillment with dual-proof
4. VERIFY: Validate settlement integrity

"The Verb (written) meets the Action (paid). WINDI guarantees both."
"""

import hashlib
import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path

from .commitment_parser import CommitmentParser, ParsedCommitment, CommitmentType
from .transaction_bridge import (
    TransactionBridge,
    TransactionRecord,
    MatchResult,
    MockBankAdapter
)


class SettlementStatus(Enum):
    """Status of commitment settlement."""
    PENDING = "pending"              # Awaiting transaction
    LINKED = "linked"                # Transaction found, not confirmed
    SETTLED = "settled"              # Fully settled with proof
    PARTIAL = "partial"              # Partially settled
    DISPUTED = "disputed"            # Settlement contested
    EXPIRED = "expired"              # Past deadline without settlement
    CANCELLED = "cancelled"          # Commitment cancelled


@dataclass
class CommitmentRecord:
    """Registered commitment from forensic document."""
    commitment_id: str
    parsed_commitment: ParsedCommitment

    # Source document
    pixwindi_submission_id: str
    pixwindi_receipt_hash: str
    document_hash: str

    # Status
    status: SettlementStatus
    created_at: str
    updated_at: str

    # Linked transactions
    linked_transactions: List[str]
    settlement_id: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "commitment_id": self.commitment_id,
            "parsed_commitment": self.parsed_commitment.to_dict(),
            "pixwindi_submission_id": self.pixwindi_submission_id,
            "pixwindi_receipt_hash": self.pixwindi_receipt_hash,
            "document_hash": self.document_hash,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "linked_transactions": self.linked_transactions,
            "settlement_id": self.settlement_id
        }


@dataclass
class SettlementReceipt:
    """
    Proof of settlement — the "Recibo de Liquidação".

    Binds:
    - The forensic document (PixWindi)
    - The parsed commitment
    - The bank transaction
    - The settlement proof
    """
    settlement_id: str

    # Commitment side (The Verb)
    commitment_id: str
    commitment_hash: str
    pixwindi_receipt: str
    document_summary: str

    # Transaction side (The Action)
    transaction_id: str
    transaction_hash: str
    amount_settled: float
    currency: str
    transaction_timestamp: str

    # Settlement proof
    match_score: float
    correlation_factors: Dict[str, float]
    dual_proof_hash: str  # Hash binding both sides

    # Metadata
    settled_at: str
    settled_by: str  # System or human verifier
    governance_level: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def verification_url(self) -> str:
        """URL for public verification."""
        return f"https://verify.windi.dev/settlement/{self.settlement_id}"


class SettlementEngine:
    """
    Main engine for commitment liquidation.

    Manages the full lifecycle:
    Commitment → Link → Settle → Verify

    Integrates with:
    - PixWindi (forensic documents)
    - TransactionBridge (banking)
    - WINDI Governance (audit trail)
    """

    VERSION = "1.0.0"

    # Storage paths
    DEFAULT_STORAGE_DIR = "/opt/windi/data/settlements"

    # Auto-settle thresholds
    AUTO_SETTLE_THRESHOLD = 0.85
    MANUAL_REVIEW_THRESHOLD = 0.65

    def __init__(
        self,
        storage_dir: str = None,
        governance_level: str = "MEDIUM"
    ):
        """
        Initialize settlement engine.

        Args:
            storage_dir: Directory for settlement records
            governance_level: WINDI governance level
        """
        self.storage_dir = Path(storage_dir or self.DEFAULT_STORAGE_DIR)
        self.governance_level = governance_level

        # Initialize components
        self.parser = CommitmentParser()
        self.bridge = TransactionBridge()

        # In-memory indices (would be DB in production)
        self.commitments: Dict[str, CommitmentRecord] = {}
        self.settlements: Dict[str, SettlementReceipt] = {}

        # Ensure storage directory exists
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def create_commitment(
        self,
        text: str,
        pixwindi_submission_id: str,
        pixwindi_receipt_hash: str,
        document_hash: str
    ) -> CommitmentRecord:
        """
        Create commitment record from parsed document.

        Args:
            text: Document text (OCR/transcription)
            pixwindi_submission_id: PixWindi submission ID
            pixwindi_receipt_hash: PixWindi receipt hash
            document_hash: Document content hash

        Returns:
            CommitmentRecord
        """
        now = datetime.now(timezone.utc).isoformat()

        # Parse commitment
        parsed = self.parser.parse(text, source_hash=document_hash)

        # Create record
        record = CommitmentRecord(
            commitment_id=parsed.commitment_id,
            parsed_commitment=parsed,
            pixwindi_submission_id=pixwindi_submission_id,
            pixwindi_receipt_hash=pixwindi_receipt_hash,
            document_hash=document_hash,
            status=SettlementStatus.PENDING,
            created_at=now,
            updated_at=now,
            linked_transactions=[],
            settlement_id=None
        )

        # Store
        self.commitments[record.commitment_id] = record
        self._persist_commitment(record)

        return record

    def find_matching_transactions(
        self,
        commitment_id: str,
        date_window_days: int = 7
    ) -> List[MatchResult]:
        """
        Find bank transactions matching a commitment.

        Args:
            commitment_id: Commitment to match
            date_window_days: Days before/after commitment to search

        Returns:
            List of matching transactions with scores
        """
        commitment = self.commitments.get(commitment_id)
        if not commitment:
            return []

        parsed = commitment.parsed_commitment

        # Build search parameters
        amount = parsed.total_amount or 0
        currency = parsed.currency.value if parsed.currency else "EUR"

        # Date range around commitment creation or deadline
        base_date = datetime.fromisoformat(commitment.created_at.replace('Z', '+00:00'))
        if parsed.deadline:
            base_date = parsed.deadline

        date_from = base_date - timedelta(days=date_window_days)
        date_to = base_date + timedelta(days=date_window_days)

        # Search transactions
        return self.bridge.find_matching_transactions(
            amount=amount,
            currency=currency,
            date_range=(date_from, date_to),
            description_hint=parsed.normalized_text[:50] if parsed.normalized_text else None
        )

    def link_transaction(
        self,
        commitment_id: str,
        transaction_id: str,
        match_result: Optional[MatchResult] = None
    ) -> bool:
        """
        Link a transaction to a commitment.

        Args:
            commitment_id: Commitment ID
            transaction_id: Transaction ID
            match_result: Optional pre-computed match result

        Returns:
            True if linked successfully
        """
        commitment = self.commitments.get(commitment_id)
        if not commitment:
            return False

        # Verify transaction exists
        if not self.bridge.verify_transaction_exists(transaction_id):
            return False

        # Add to linked transactions
        if transaction_id not in commitment.linked_transactions:
            commitment.linked_transactions.append(transaction_id)
            commitment.status = SettlementStatus.LINKED
            commitment.updated_at = datetime.now(timezone.utc).isoformat()

            self._persist_commitment(commitment)

        return True

    def settle_commitment(
        self,
        commitment_id: str,
        transaction_id: str,
        settled_by: str = "system"
    ) -> Optional[SettlementReceipt]:
        """
        Settle a commitment with a verified transaction.

        Creates the "Recibo de Liquidação" binding both sides.

        Args:
            commitment_id: Commitment ID
            transaction_id: Transaction ID
            settled_by: Who confirmed the settlement

        Returns:
            SettlementReceipt or None if settlement fails
        """
        commitment = self.commitments.get(commitment_id)
        if not commitment:
            return None

        # Get transaction details
        transaction = self.bridge.get_transaction_details(transaction_id)
        if not transaction:
            return None

        # Calculate match score
        parsed = commitment.parsed_commitment
        date_range = self._get_date_range(commitment)

        matches = self.bridge.find_matching_transactions(
            amount=parsed.total_amount or 0,
            currency=parsed.currency.value if parsed.currency else "EUR",
            date_range=date_range
        )

        # Find this transaction in matches
        match_result = None
        for m in matches:
            if m.transaction.transaction_id == transaction_id:
                match_result = m
                break

        if not match_result:
            # Transaction found but doesn't match well
            match_score = 0.5
            correlation_factors = {"manual_link": 1.0}
        else:
            match_score = match_result.match_score
            correlation_factors = match_result.match_factors

        # Generate dual-proof hash
        dual_proof = self._generate_dual_proof(commitment, transaction)

        # Create settlement receipt
        settlement_id = self._generate_settlement_id(commitment_id, transaction_id)

        receipt = SettlementReceipt(
            settlement_id=settlement_id,
            commitment_id=commitment_id,
            commitment_hash=commitment.document_hash,
            pixwindi_receipt=commitment.pixwindi_receipt_hash,
            document_summary=parsed.normalized_text[:200] if parsed.normalized_text else "",
            transaction_id=transaction_id,
            transaction_hash=hashlib.sha256(
                json.dumps(transaction.to_dict(), sort_keys=True).encode()
            ).hexdigest()[:24],
            amount_settled=transaction.amount,
            currency=transaction.currency,
            transaction_timestamp=transaction.timestamp,
            match_score=match_score,
            correlation_factors=correlation_factors,
            dual_proof_hash=dual_proof,
            settled_at=datetime.now(timezone.utc).isoformat(),
            settled_by=settled_by,
            governance_level=self.governance_level
        )

        # Update commitment status
        commitment.status = SettlementStatus.SETTLED
        commitment.settlement_id = settlement_id
        commitment.updated_at = datetime.now(timezone.utc).isoformat()

        # Store
        self.settlements[settlement_id] = receipt
        self._persist_commitment(commitment)
        self._persist_settlement(receipt)

        return receipt

    def verify_settlement(self, settlement_id: str) -> Dict[str, Any]:
        """
        Verify settlement integrity.

        Checks:
        - Commitment exists and is valid
        - Transaction exists and matches
        - Dual-proof hash is correct
        - No tampering detected

        Returns:
            Verification result with details
        """
        receipt = self.settlements.get(settlement_id)
        if not receipt:
            # Try to load from storage
            receipt = self._load_settlement(settlement_id)

        if not receipt:
            return {
                "valid": False,
                "error": "Settlement not found",
                "settlement_id": settlement_id
            }

        checks = {}

        # Check commitment
        commitment = self.commitments.get(receipt.commitment_id)
        checks["commitment_exists"] = commitment is not None
        checks["commitment_hash_valid"] = (
            commitment and commitment.document_hash == receipt.commitment_hash
        )

        # Check transaction
        tx_exists = self.bridge.verify_transaction_exists(receipt.transaction_id)
        checks["transaction_exists"] = tx_exists

        # Verify dual-proof
        if commitment:
            tx = self.bridge.get_transaction_details(receipt.transaction_id)
            if tx:
                expected_proof = self._generate_dual_proof(commitment, tx)
                checks["dual_proof_valid"] = expected_proof == receipt.dual_proof_hash
            else:
                checks["dual_proof_valid"] = False
        else:
            checks["dual_proof_valid"] = False

        # Overall validity
        all_valid = all(checks.values())

        return {
            "valid": all_valid,
            "settlement_id": settlement_id,
            "checks": checks,
            "receipt": receipt.to_dict() if all_valid else None,
            "verified_at": datetime.now(timezone.utc).isoformat()
        }

    def try_auto_settle(
        self,
        transaction_data: Dict[str, Any]
    ) -> Optional[SettlementReceipt]:
        """
        Try to auto-settle a pending commitment with new transaction.

        Called by webhook handler when bank confirms transaction.

        Args:
            transaction_data: Transaction data from bank webhook

        Returns:
            SettlementReceipt if auto-settled, None otherwise
        """
        # Build transaction record
        tx = TransactionRecord(
            transaction_id=transaction_data.get("transaction_id", ""),
            bank_code=transaction_data.get("bank_code", ""),
            account_from=transaction_data.get("account_from"),
            account_to=transaction_data.get("account_to"),
            amount=float(transaction_data.get("amount", 0)),
            currency=transaction_data.get("currency", "EUR"),
            transaction_type=transaction_data.get("type", "transfer"),
            status=transaction_data.get("status", "completed"),
            timestamp=transaction_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            description=transaction_data.get("description"),
            reference=transaction_data.get("reference"),
            geolocation=transaction_data.get("geolocation"),
            raw_data=transaction_data
        )

        # Find matching pending commitments
        for commitment in self.commitments.values():
            if commitment.status != SettlementStatus.PENDING:
                continue

            parsed = commitment.parsed_commitment

            # Quick amount check
            if parsed.total_amount:
                amount_diff = abs(tx.amount - parsed.total_amount) / parsed.total_amount
                if amount_diff > 0.05:  # More than 5% difference
                    continue

            # Check currency
            if parsed.currency and parsed.currency.value != tx.currency:
                continue

            # Potential match - calculate full score
            date_range = self._get_date_range(commitment)
            matches = self.bridge.find_matching_transactions(
                amount=parsed.total_amount or tx.amount,
                currency=tx.currency,
                date_range=date_range
            )

            # Check if this transaction would match
            for match in matches:
                if match.match_score >= self.AUTO_SETTLE_THRESHOLD:
                    # Auto-settle
                    return self.settle_commitment(
                        commitment.commitment_id,
                        tx.transaction_id,
                        settled_by="auto-webhook"
                    )

        return None

    def get_pending_commitments(self) -> List[CommitmentRecord]:
        """Get all pending commitments awaiting settlement."""
        return [
            c for c in self.commitments.values()
            if c.status == SettlementStatus.PENDING
        ]

    def get_commitment(self, commitment_id: str) -> Optional[CommitmentRecord]:
        """Get commitment by ID."""
        return self.commitments.get(commitment_id)

    def get_settlement(self, settlement_id: str) -> Optional[SettlementReceipt]:
        """Get settlement by ID."""
        return self.settlements.get(settlement_id)

    def _get_date_range(
        self,
        commitment: CommitmentRecord
    ) -> Tuple[datetime, datetime]:
        """Get date range for transaction search."""
        base = datetime.fromisoformat(commitment.created_at.replace('Z', '+00:00'))

        if commitment.parsed_commitment.deadline:
            deadline = commitment.parsed_commitment.deadline
            return (base - timedelta(days=1), deadline + timedelta(days=7))

        return (base - timedelta(days=7), base + timedelta(days=30))

    def _generate_dual_proof(
        self,
        commitment: CommitmentRecord,
        transaction: TransactionRecord
    ) -> str:
        """
        Generate dual-proof hash binding commitment and transaction.

        This is the cryptographic link between Verb and Action.
        """
        data = {
            "commitment": {
                "id": commitment.commitment_id,
                "hash": commitment.document_hash,
                "pixwindi": commitment.pixwindi_receipt_hash
            },
            "transaction": {
                "id": transaction.transaction_id,
                "amount": transaction.amount,
                "currency": transaction.currency,
                "timestamp": transaction.timestamp
            },
            "binding_timestamp": datetime.now(timezone.utc).isoformat()
        }

        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()

    def _generate_settlement_id(
        self,
        commitment_id: str,
        transaction_id: str
    ) -> str:
        """Generate unique settlement ID."""
        data = f"{commitment_id}:{transaction_id}:{datetime.now().isoformat()}"
        hash_val = hashlib.sha256(data.encode()).hexdigest()[:12].upper()
        return f"STL-{hash_val}"

    def _persist_commitment(self, commitment: CommitmentRecord):
        """Persist commitment to storage."""
        path = self.storage_dir / "commitments" / f"{commitment.commitment_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(commitment.to_dict(), f, indent=2, ensure_ascii=False)

    def _persist_settlement(self, receipt: SettlementReceipt):
        """Persist settlement to storage."""
        path = self.storage_dir / "settlements" / f"{receipt.settlement_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(receipt.to_dict(), f, indent=2, ensure_ascii=False)

    def _load_settlement(self, settlement_id: str) -> Optional[SettlementReceipt]:
        """Load settlement from storage."""
        path = self.storage_dir / "settlements" / f"{settlement_id}.json"

        if not path.exists():
            return None

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Reconstruct SettlementReceipt
                # (simplified - would need proper deserialization)
                return None  # Placeholder
        except Exception:
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

# Global engine instance
_engine: Optional[SettlementEngine] = None


def get_engine() -> SettlementEngine:
    """Get or create global settlement engine."""
    global _engine
    if _engine is None:
        _engine = SettlementEngine()
        # Register mock adapter for development
        mock = MockBankAdapter()
        mock.authenticate({"api_key": "dev"})
        _engine.bridge.register_adapter("mock", mock, set_default=True)
    return _engine


def create_commitment(
    text: str,
    pixwindi_submission_id: str,
    pixwindi_receipt_hash: str,
    document_hash: str
) -> CommitmentRecord:
    """
    Create commitment from document text.

    Example:
        commitment = create_commitment(
            text="Zahlung von €500 bis 15.02.2026",
            pixwindi_submission_id="PIX-20260210-ABC123",
            pixwindi_receipt_hash="abc123...",
            document_hash="def456..."
        )
    """
    return get_engine().create_commitment(
        text, pixwindi_submission_id, pixwindi_receipt_hash, document_hash
    )


def link_transaction(
    commitment_id: str,
    transaction_id: str
) -> bool:
    """Link a bank transaction to a commitment."""
    return get_engine().link_transaction(commitment_id, transaction_id)


def settle_commitment(
    commitment_id: str,
    transaction_id: str,
    settled_by: str = "manual"
) -> Optional[SettlementReceipt]:
    """
    Settle a commitment with a transaction.

    Returns SettlementReceipt (Recibo de Liquidação) binding both.
    """
    return get_engine().settle_commitment(
        commitment_id, transaction_id, settled_by
    )


def verify_settlement(settlement_id: str) -> Dict[str, Any]:
    """Verify settlement integrity."""
    return get_engine().verify_settlement(settlement_id)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("WINDI Settlement Engine v1.0.0")
    print("Commitment Liquidation — Verb meets Action")
    print("=" * 70)
    print()
    print("Usage:")
    print("  from engine.settlement import (")
    print("      create_commitment,")
    print("      link_transaction,")
    print("      settle_commitment,")
    print("      verify_settlement")
    print("  )")
    print()
    print("Example flow:")
    print("  # 1. Create commitment from PixWindi document")
    print("  commitment = create_commitment(")
    print("      text='Zahlung €500 bis 15.02.2026',")
    print("      pixwindi_submission_id='PIX-20260210-ABC123',")
    print("      pixwindi_receipt_hash='abc...',")
    print("      document_hash='def...'")
    print("  )")
    print()
    print("  # 2. Link bank transaction")
    print("  link_transaction(commitment.commitment_id, 'TX-123')")
    print()
    print("  # 3. Settle with dual-proof")
    print("  receipt = settle_commitment(commitment.commitment_id, 'TX-123')")
    print()
    print("  # 4. Verify settlement")
    print("  result = verify_settlement(receipt.settlement_id)")
    print()
    print("\"The Verb (written) meets the Action (paid). WINDI guarantees both.\"")
    print("=" * 70)
