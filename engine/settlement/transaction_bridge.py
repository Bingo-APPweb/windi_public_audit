"""
WINDI Settlement — Transaction Bridge
======================================
Banking/Financial system integration for commitment verification.

Provides:
- Abstract adapter interface for multiple banks
- Transaction query by amount, date, parties
- Geolocation correlation
- Webhook integration for real-time settlement

"The bank confirms the action. WINDI confirms the integrity."
"""

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone, timedelta
from enum import Enum


class TransactionStatus(Enum):
    """Transaction status from banking system."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REVERSED = "reversed"


class TransactionType(Enum):
    """Types of financial transactions."""
    TRANSFER = "transfer"
    PAYMENT = "payment"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    PIX = "pix"  # Brazilian instant payment
    SEPA = "sepa"  # European transfer
    WIRE = "wire"
    UNKNOWN = "unknown"


@dataclass
class TransactionRecord:
    """Bank transaction record."""
    transaction_id: str
    bank_code: str
    account_from: Optional[str]
    account_to: Optional[str]
    amount: float
    currency: str
    transaction_type: TransactionType
    status: TransactionStatus
    timestamp: str
    description: Optional[str]
    reference: Optional[str]
    geolocation: Optional[Dict[str, float]]
    raw_data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["transaction_type"] = self.transaction_type.value
        result["status"] = self.status.value
        return result

    @property
    def is_completed(self) -> bool:
        return self.status == TransactionStatus.COMPLETED


@dataclass
class TransactionQuery:
    """Query parameters for finding transactions."""
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None
    amount_exact: Optional[float] = None
    amount_tolerance: float = 0.01  # 1% tolerance for matching

    currency: Optional[str] = None

    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

    account_from: Optional[str] = None
    account_to: Optional[str] = None

    reference_contains: Optional[str] = None
    description_contains: Optional[str] = None

    # Geolocation correlation
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geo_radius_km: float = 10.0  # Radius for location matching


@dataclass
class MatchResult:
    """Result of transaction matching."""
    transaction: TransactionRecord
    match_score: float  # 0.0 - 1.0
    match_factors: Dict[str, float]  # Breakdown of matching criteria
    correlation_proof: str  # Hash proving the match


class BankAdapter(ABC):
    """
    Abstract adapter for banking systems.

    Implementations:
    - MockBankAdapter (testing)
    - PIXBankAdapter (Brazilian banks)
    - SEPABankAdapter (European banks)
    - OpenBankingAdapter (PSD2 compliant)
    """

    @abstractmethod
    def get_name(self) -> str:
        """Get adapter name."""
        pass

    @abstractmethod
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with banking system."""
        pass

    @abstractmethod
    def query_transactions(
        self,
        query: TransactionQuery
    ) -> List[TransactionRecord]:
        """Query transactions matching criteria."""
        pass

    @abstractmethod
    def get_transaction(self, transaction_id: str) -> Optional[TransactionRecord]:
        """Get specific transaction by ID."""
        pass

    @abstractmethod
    def verify_transaction(self, transaction_id: str) -> bool:
        """Verify transaction exists and is valid."""
        pass


class MockBankAdapter(BankAdapter):
    """
    Mock bank adapter for testing and development.

    Simulates banking API responses without real bank connection.
    """

    def __init__(self):
        self.transactions: Dict[str, TransactionRecord] = {}
        self._authenticated = False

    def get_name(self) -> str:
        return "WINDI Mock Bank (Development)"

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Mock authentication always succeeds with valid structure."""
        if "api_key" in credentials or "client_id" in credentials:
            self._authenticated = True
            return True
        return False

    def add_mock_transaction(
        self,
        amount: float,
        currency: str = "EUR",
        status: TransactionStatus = TransactionStatus.COMPLETED,
        timestamp: Optional[datetime] = None,
        description: str = "",
        geolocation: Dict[str, float] = None
    ) -> TransactionRecord:
        """Add a mock transaction for testing."""
        tx_id = f"MOCK-{hashlib.sha256(str(datetime.now()).encode()).hexdigest()[:12].upper()}"

        tx = TransactionRecord(
            transaction_id=tx_id,
            bank_code="MOCK",
            account_from="DE89370400440532013000",
            account_to="DE89370400440532013001",
            amount=amount,
            currency=currency,
            transaction_type=TransactionType.TRANSFER,
            status=status,
            timestamp=(timestamp or datetime.now(timezone.utc)).isoformat(),
            description=description,
            reference=None,
            geolocation=geolocation,
            raw_data={"mock": True}
        )

        self.transactions[tx_id] = tx
        return tx

    def query_transactions(
        self,
        query: TransactionQuery
    ) -> List[TransactionRecord]:
        """Query mock transactions."""
        results = []

        for tx in self.transactions.values():
            if self._matches_query(tx, query):
                results.append(tx)

        return results

    def _matches_query(
        self,
        tx: TransactionRecord,
        query: TransactionQuery
    ) -> bool:
        """Check if transaction matches query."""
        # Amount matching
        if query.amount_exact is not None:
            tolerance = query.amount_exact * query.amount_tolerance
            if not (query.amount_exact - tolerance <= tx.amount <= query.amount_exact + tolerance):
                return False

        if query.amount_min is not None and tx.amount < query.amount_min:
            return False

        if query.amount_max is not None and tx.amount > query.amount_max:
            return False

        # Currency matching
        if query.currency and tx.currency != query.currency:
            return False

        # Date matching
        tx_date = datetime.fromisoformat(tx.timestamp.replace('Z', '+00:00'))
        if query.date_from and tx_date < query.date_from:
            return False
        if query.date_to and tx_date > query.date_to:
            return False

        # Description matching
        if query.description_contains:
            if not tx.description or query.description_contains.lower() not in tx.description.lower():
                return False

        return True

    def get_transaction(self, transaction_id: str) -> Optional[TransactionRecord]:
        return self.transactions.get(transaction_id)

    def verify_transaction(self, transaction_id: str) -> bool:
        tx = self.transactions.get(transaction_id)
        return tx is not None and tx.is_completed


class TransactionBridge:
    """
    Main bridge for connecting forensic documents to financial transactions.

    Provides:
    - Multi-bank adapter management
    - Transaction matching with commitment data
    - Geolocation correlation
    - Settlement proof generation
    """

    # Match score thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.85
    MEDIUM_CONFIDENCE_THRESHOLD = 0.65
    LOW_CONFIDENCE_THRESHOLD = 0.45

    def __init__(self):
        self.adapters: Dict[str, BankAdapter] = {}
        self.default_adapter: Optional[str] = None

    def register_adapter(
        self,
        name: str,
        adapter: BankAdapter,
        set_default: bool = False
    ):
        """Register a bank adapter."""
        self.adapters[name] = adapter
        if set_default or not self.default_adapter:
            self.default_adapter = name

    def find_matching_transactions(
        self,
        amount: float,
        currency: str,
        date_range: Tuple[datetime, datetime],
        geolocation: Optional[Dict[str, float]] = None,
        description_hint: Optional[str] = None,
        adapter_name: Optional[str] = None
    ) -> List[MatchResult]:
        """
        Find transactions matching commitment criteria.

        Args:
            amount: Expected transaction amount
            currency: Expected currency
            date_range: (from, to) datetime range
            geolocation: Optional location for correlation
            description_hint: Optional text to match in description
            adapter_name: Specific adapter to use

        Returns:
            List of MatchResult ordered by match score
        """
        adapter = self._get_adapter(adapter_name)
        if not adapter:
            return []

        # Build query
        query = TransactionQuery(
            amount_exact=amount,
            amount_tolerance=0.02,  # 2% tolerance
            currency=currency,
            date_from=date_range[0],
            date_to=date_range[1],
            description_contains=description_hint,
            latitude=geolocation.get("lat") if geolocation else None,
            longitude=geolocation.get("lon") if geolocation else None
        )

        # Query transactions
        transactions = adapter.query_transactions(query)

        # Score and rank matches
        results = []
        for tx in transactions:
            score, factors = self._calculate_match_score(
                tx, amount, currency, date_range, geolocation, description_hint
            )

            if score >= self.LOW_CONFIDENCE_THRESHOLD:
                proof = self._generate_correlation_proof(tx, factors)
                results.append(MatchResult(
                    transaction=tx,
                    match_score=score,
                    match_factors=factors,
                    correlation_proof=proof
                ))

        # Sort by score descending
        results.sort(key=lambda r: r.match_score, reverse=True)

        return results

    def verify_transaction_exists(
        self,
        transaction_id: str,
        adapter_name: Optional[str] = None
    ) -> bool:
        """Verify that a transaction exists and is valid."""
        adapter = self._get_adapter(adapter_name)
        if not adapter:
            return False

        return adapter.verify_transaction(transaction_id)

    def get_transaction_details(
        self,
        transaction_id: str,
        adapter_name: Optional[str] = None
    ) -> Optional[TransactionRecord]:
        """Get full transaction details."""
        adapter = self._get_adapter(adapter_name)
        if not adapter:
            return None

        return adapter.get_transaction(transaction_id)

    def _get_adapter(self, name: Optional[str]) -> Optional[BankAdapter]:
        """Get adapter by name or default."""
        if name:
            return self.adapters.get(name)
        return self.adapters.get(self.default_adapter) if self.default_adapter else None

    def _calculate_match_score(
        self,
        tx: TransactionRecord,
        expected_amount: float,
        expected_currency: str,
        date_range: Tuple[datetime, datetime],
        geolocation: Optional[Dict[str, float]],
        description_hint: Optional[str]
    ) -> Tuple[float, Dict[str, float]]:
        """Calculate how well a transaction matches expected criteria."""
        factors = {}

        # Amount matching (40% weight)
        amount_diff = abs(tx.amount - expected_amount) / expected_amount
        if amount_diff <= 0.001:  # Exact match
            factors["amount"] = 1.0
        elif amount_diff <= 0.01:  # 1% difference
            factors["amount"] = 0.95
        elif amount_diff <= 0.05:  # 5% difference
            factors["amount"] = 0.7
        else:
            factors["amount"] = max(0, 1.0 - amount_diff)

        # Currency matching (15% weight)
        factors["currency"] = 1.0 if tx.currency == expected_currency else 0.0

        # Date matching (25% weight)
        tx_date = datetime.fromisoformat(tx.timestamp.replace('Z', '+00:00'))
        if date_range[0] <= tx_date <= date_range[1]:
            # Closer to center of range = higher score
            range_center = date_range[0] + (date_range[1] - date_range[0]) / 2
            time_diff = abs((tx_date - range_center).total_seconds())
            range_half = (date_range[1] - date_range[0]).total_seconds() / 2

            factors["date"] = max(0.5, 1.0 - (time_diff / range_half) * 0.5)
        else:
            factors["date"] = 0.0

        # Geolocation matching (10% weight if available)
        if geolocation and tx.geolocation:
            distance = self._calculate_distance(
                geolocation.get("lat", 0),
                geolocation.get("lon", 0),
                tx.geolocation.get("lat", 0),
                tx.geolocation.get("lon", 0)
            )

            if distance <= 1:  # Within 1 km
                factors["geolocation"] = 1.0
            elif distance <= 10:  # Within 10 km
                factors["geolocation"] = 0.8
            elif distance <= 50:  # Within 50 km
                factors["geolocation"] = 0.5
            else:
                factors["geolocation"] = 0.2
        else:
            factors["geolocation"] = 0.5  # Neutral if no geo data

        # Description matching (10% weight if provided)
        if description_hint and tx.description:
            hint_lower = description_hint.lower()
            desc_lower = tx.description.lower()

            if hint_lower in desc_lower:
                factors["description"] = 1.0
            elif any(word in desc_lower for word in hint_lower.split()):
                factors["description"] = 0.6
            else:
                factors["description"] = 0.3
        else:
            factors["description"] = 0.5  # Neutral

        # Calculate weighted score
        weights = {
            "amount": 0.40,
            "currency": 0.15,
            "date": 0.25,
            "geolocation": 0.10,
            "description": 0.10
        }

        total_score = sum(
            factors.get(k, 0) * weights.get(k, 0)
            for k in weights
        )

        return total_score, factors

    def _calculate_distance(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """Calculate distance in km between two points (Haversine formula)."""
        import math

        R = 6371  # Earth's radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def _generate_correlation_proof(
        self,
        tx: TransactionRecord,
        factors: Dict[str, float]
    ) -> str:
        """Generate cryptographic proof of correlation."""
        data = {
            "transaction_id": tx.transaction_id,
            "amount": tx.amount,
            "currency": tx.currency,
            "timestamp": tx.timestamp,
            "match_factors": factors,
            "proof_generated": datetime.now(timezone.utc).isoformat()
        }

        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════════
# WEBHOOK HANDLER
# ═══════════════════════════════════════════════════════════════════════════════

class SettlementWebhook:
    """
    Webhook handler for real-time settlement notifications.

    Banks can push transaction confirmations which trigger
    automatic commitment settlement.
    """

    def __init__(self, settlement_engine=None):
        self.settlement_engine = settlement_engine
        self.pending_webhooks: Dict[str, Dict] = {}

    def handle_webhook(
        self,
        bank_code: str,
        payload: Dict[str, Any],
        signature: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle incoming webhook from bank.

        Args:
            bank_code: Bank identifier
            payload: Webhook payload
            signature: Optional HMAC signature for verification

        Returns:
            Processing result
        """
        # Validate signature if provided
        if signature and not self._verify_signature(payload, signature, bank_code):
            return {"error": "Invalid signature", "status": "rejected"}

        # Extract transaction data
        tx_data = self._extract_transaction_from_webhook(bank_code, payload)

        if not tx_data:
            return {"error": "Could not parse transaction", "status": "rejected"}

        # Check for pending commitments matching this transaction
        if self.settlement_engine:
            matched = self.settlement_engine.try_auto_settle(tx_data)
            if matched:
                return {
                    "status": "settled",
                    "commitment_id": matched.commitment_id,
                    "settlement_id": matched.settlement_id
                }

        return {"status": "received", "transaction_id": tx_data.get("transaction_id")}

    def _verify_signature(
        self,
        payload: Dict[str, Any],
        signature: str,
        bank_code: str
    ) -> bool:
        """Verify webhook signature."""
        # Implementation depends on bank's signing method
        # Typically HMAC-SHA256 with shared secret
        return True  # Placeholder

    def _extract_transaction_from_webhook(
        self,
        bank_code: str,
        payload: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Extract normalized transaction data from webhook payload."""
        # Bank-specific extraction logic
        # This would be implemented per bank integration

        if "transaction" in payload:
            return payload["transaction"]
        elif "data" in payload:
            return payload["data"]

        return payload


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def create_mock_bridge() -> TransactionBridge:
    """Create a bridge with mock adapter for testing."""
    bridge = TransactionBridge()
    mock = MockBankAdapter()
    mock.authenticate({"api_key": "test"})
    bridge.register_adapter("mock", mock, set_default=True)
    return bridge
