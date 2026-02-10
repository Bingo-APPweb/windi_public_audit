"""
WINDI Settlement — Commitment Parser
=====================================
Extracts structured commitment data from handwritten documents.

Parses:
- Monetary values (EUR, USD, BRL, etc.)
- Dates and deadlines
- Party identifiers (names, account references)
- Commitment types (payment, delivery, service)
- Conditions and contingencies

"The napkin speaks. We listen and structure."
"""

import re
import hashlib
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from enum import Enum


class CommitmentType(Enum):
    """Types of commitments that can be extracted."""
    PAYMENT = "payment"              # Money transfer commitment
    DELIVERY = "delivery"            # Goods/service delivery
    SERVICE = "service"              # Service provision
    AGREEMENT = "agreement"          # General agreement
    PROMISE = "promise"              # Non-financial promise
    CONDITIONAL = "conditional"      # Contingent on conditions
    UNKNOWN = "unknown"


class Currency(Enum):
    """Supported currencies."""
    EUR = "EUR"
    USD = "USD"
    BRL = "BRL"
    GBP = "GBP"
    CHF = "CHF"
    UNKNOWN = "UNKNOWN"


@dataclass
class MonetaryValue:
    """Extracted monetary value."""
    amount: float
    currency: Currency
    raw_text: str
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "amount": self.amount,
            "currency": self.currency.value,
            "raw_text": self.raw_text,
            "confidence": self.confidence
        }


@dataclass
class DateReference:
    """Extracted date reference."""
    date: Optional[datetime]
    raw_text: str
    is_deadline: bool
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date.isoformat() if self.date else None,
            "raw_text": self.raw_text,
            "is_deadline": self.is_deadline,
            "confidence": self.confidence
        }


@dataclass
class PartyReference:
    """Extracted party/person reference."""
    name: str
    role: str  # "payer", "payee", "provider", "recipient", "witness"
    identifier: Optional[str]  # Account number, ID, etc.
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "identifier": self.identifier,
            "confidence": self.confidence
        }


@dataclass
class ParsedCommitment:
    """Complete parsed commitment from document."""
    # Core identification
    commitment_id: str
    commitment_type: CommitmentType

    # Financial elements
    monetary_values: List[MonetaryValue]
    total_amount: Optional[float]
    currency: Currency

    # Temporal elements
    dates: List[DateReference]
    deadline: Optional[datetime]

    # Parties
    parties: List[PartyReference]
    payer: Optional[PartyReference]
    payee: Optional[PartyReference]

    # Content
    raw_text: str
    normalized_text: str
    keywords: List[str]
    conditions: List[str]

    # Metadata
    parse_confidence: float
    parse_timestamp: str
    source_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "commitment_id": self.commitment_id,
            "commitment_type": self.commitment_type.value,
            "monetary_values": [mv.to_dict() for mv in self.monetary_values],
            "total_amount": self.total_amount,
            "currency": self.currency.value,
            "dates": [d.to_dict() for d in self.dates],
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "parties": [p.to_dict() for p in self.parties],
            "payer": self.payer.to_dict() if self.payer else None,
            "payee": self.payee.to_dict() if self.payee else None,
            "raw_text": self.raw_text,
            "normalized_text": self.normalized_text,
            "keywords": self.keywords,
            "conditions": self.conditions,
            "parse_confidence": self.parse_confidence,
            "parse_timestamp": self.parse_timestamp,
            "source_hash": self.source_hash
        }


class CommitmentParser:
    """
    Parses handwritten document text to extract structured commitments.

    Supports multilingual extraction (DE, EN, PT, ES).

    Pipeline:
    1. Text normalization
    2. Monetary value extraction
    3. Date extraction
    4. Party identification
    5. Commitment type classification
    6. Condition extraction
    """

    # Currency patterns
    CURRENCY_PATTERNS = {
        Currency.EUR: [
            r'€\s*(\d+(?:[.,]\d{1,2})?)',
            r'(\d+(?:[.,]\d{1,2})?)\s*€',
            r'(\d+(?:[.,]\d{1,2})?)\s*(?:EUR|Euro|Euros)',
            r'EUR\s*(\d+(?:[.,]\d{1,2})?)',
        ],
        Currency.USD: [
            r'\$\s*(\d+(?:[.,]\d{1,2})?)',
            r'(\d+(?:[.,]\d{1,2})?)\s*\$',
            r'(\d+(?:[.,]\d{1,2})?)\s*(?:USD|Dollar|Dollars)',
            r'USD\s*(\d+(?:[.,]\d{1,2})?)',
        ],
        Currency.BRL: [
            r'R\$\s*(\d+(?:[.,]\d{1,2})?)',
            r'(\d+(?:[.,]\d{1,2})?)\s*(?:BRL|Reais|Real)',
            r'BRL\s*(\d+(?:[.,]\d{1,2})?)',
        ],
        Currency.GBP: [
            r'£\s*(\d+(?:[.,]\d{1,2})?)',
            r'(\d+(?:[.,]\d{1,2})?)\s*(?:GBP|Pound|Pounds)',
        ],
        Currency.CHF: [
            r'CHF\s*(\d+(?:[.,]\d{1,2})?)',
            r'(\d+(?:[.,]\d{1,2})?)\s*(?:CHF|Franken)',
        ],
    }

    # Date patterns (multilingual)
    DATE_PATTERNS = [
        # ISO format
        (r'(\d{4}-\d{2}-\d{2})', '%Y-%m-%d'),
        # European format
        (r'(\d{1,2}[./]\d{1,2}[./]\d{4})', '%d.%m.%Y'),
        (r'(\d{1,2}[./]\d{1,2}[./]\d{2})', '%d.%m.%y'),
        # Written dates (German)
        (r'(\d{1,2})\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*(\d{4})', None),
        # Written dates (English)
        (r'(January|February|March|April|May|June|July|August|September|October|November|December)\s*(\d{1,2}),?\s*(\d{4})', None),
        # Written dates (Portuguese)
        (r'(\d{1,2})\s*de\s*(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\s*de\s*(\d{4})', None),
    ]

    # Deadline indicators (multilingual)
    DEADLINE_INDICATORS = [
        # German
        'bis', 'spätestens', 'fällig', 'deadline', 'termin',
        # English
        'by', 'until', 'due', 'before', 'deadline',
        # Portuguese
        'até', 'prazo', 'vencimento', 'data limite',
    ]

    # Payment keywords (multilingual)
    PAYMENT_KEYWORDS = [
        # German
        'zahlung', 'bezahlung', 'überweisung', 'betrag', 'preis', 'kosten',
        'rechnung', 'honorar', 'gebühr',
        # English
        'payment', 'pay', 'transfer', 'amount', 'price', 'cost', 'fee',
        'invoice', 'bill',
        # Portuguese
        'pagamento', 'pagar', 'transferência', 'valor', 'preço', 'custo',
        'taxa', 'fatura', 'conta',
    ]

    # Role indicators
    ROLE_INDICATORS = {
        'payer': ['zahlt', 'pays', 'paga', 'überweist', 'transfers', 'transfere'],
        'payee': ['erhält', 'receives', 'recebe', 'bekommt', 'gets'],
        'provider': ['liefert', 'provides', 'fornece', 'bietet', 'offers'],
        'recipient': ['empfängt', 'receives', 'recebe'],
    }

    def __init__(self):
        """Initialize parser."""
        pass

    def parse(
        self,
        text: str,
        source_hash: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> ParsedCommitment:
        """
        Parse commitment from text.

        Args:
            text: Raw text (OCR output or transcription)
            source_hash: Hash of source document (PixWindi)
            metadata: Additional context metadata

        Returns:
            ParsedCommitment with structured data
        """
        parse_timestamp = datetime.now(timezone.utc).isoformat()

        # Normalize text
        normalized = self._normalize_text(text)

        # Extract monetary values
        monetary_values = self._extract_monetary_values(text)

        # Determine primary currency and total
        currency, total_amount = self._calculate_totals(monetary_values)

        # Extract dates
        dates = self._extract_dates(text)
        deadline = self._find_deadline(dates, text)

        # Extract parties
        parties = self._extract_parties(text)
        payer, payee = self._identify_roles(parties, text)

        # Classify commitment type
        commitment_type = self._classify_commitment(
            text, monetary_values, parties
        )

        # Extract keywords and conditions
        keywords = self._extract_keywords(text)
        conditions = self._extract_conditions(text)

        # Calculate confidence
        confidence = self._calculate_confidence(
            monetary_values, dates, parties, commitment_type
        )

        # Generate commitment ID
        commitment_id = self._generate_commitment_id(
            text, source_hash, parse_timestamp
        )

        return ParsedCommitment(
            commitment_id=commitment_id,
            commitment_type=commitment_type,
            monetary_values=monetary_values,
            total_amount=total_amount,
            currency=currency,
            dates=dates,
            deadline=deadline,
            parties=parties,
            payer=payer,
            payee=payee,
            raw_text=text,
            normalized_text=normalized,
            keywords=keywords,
            conditions=conditions,
            parse_confidence=confidence,
            parse_timestamp=parse_timestamp,
            source_hash=source_hash or hashlib.sha256(text.encode()).hexdigest()[:16]
        )

    def _normalize_text(self, text: str) -> str:
        """Normalize text for processing."""
        # Convert to lowercase for matching
        normalized = text.lower()

        # Normalize whitespace
        normalized = ' '.join(normalized.split())

        # Normalize currency symbols
        normalized = normalized.replace('eur', '€')
        normalized = normalized.replace('usd', '$')

        return normalized

    def _extract_monetary_values(self, text: str) -> List[MonetaryValue]:
        """Extract all monetary values from text."""
        values = []

        for currency, patterns in self.CURRENCY_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Extract amount
                    amount_str = match.group(1)
                    # Handle European decimal notation
                    amount_str = amount_str.replace('.', '').replace(',', '.')

                    try:
                        amount = float(amount_str)
                        values.append(MonetaryValue(
                            amount=amount,
                            currency=currency,
                            raw_text=match.group(0),
                            confidence=0.9 if '€' in match.group(0) or '$' in match.group(0) else 0.7
                        ))
                    except ValueError:
                        continue

        # Deduplicate by amount and currency
        seen = set()
        unique_values = []
        for v in values:
            key = (v.amount, v.currency)
            if key not in seen:
                seen.add(key)
                unique_values.append(v)

        return unique_values

    def _calculate_totals(
        self,
        values: List[MonetaryValue]
    ) -> Tuple[Currency, Optional[float]]:
        """Calculate total amount and determine primary currency."""
        if not values:
            return Currency.UNKNOWN, None

        # Group by currency
        by_currency: Dict[Currency, float] = {}
        for v in values:
            if v.currency not in by_currency:
                by_currency[v.currency] = 0
            by_currency[v.currency] += v.amount

        # Find dominant currency (highest total)
        primary_currency = max(by_currency, key=by_currency.get)
        total = by_currency[primary_currency]

        return primary_currency, total

    def _extract_dates(self, text: str) -> List[DateReference]:
        """Extract dates from text."""
        dates = []
        text_lower = text.lower()

        # Check for deadline context
        has_deadline_context = any(
            ind in text_lower for ind in self.DEADLINE_INDICATORS
        )

        for pattern, fmt in self.DATE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    if fmt:
                        # Simple date format
                        date_str = match.group(1).replace('/', '.')
                        parsed_date = datetime.strptime(date_str, fmt)
                    else:
                        # Complex date format (written months)
                        # Simplified: skip complex parsing for now
                        continue

                    # Check if this date is marked as deadline
                    context_start = max(0, match.start() - 20)
                    context = text[context_start:match.start()].lower()
                    is_deadline = any(ind in context for ind in self.DEADLINE_INDICATORS)

                    dates.append(DateReference(
                        date=parsed_date,
                        raw_text=match.group(0),
                        is_deadline=is_deadline,
                        confidence=0.85
                    ))

                except ValueError:
                    continue

        return dates

    def _find_deadline(
        self,
        dates: List[DateReference],
        text: str
    ) -> Optional[datetime]:
        """Find the primary deadline from extracted dates."""
        # First, look for explicitly marked deadlines
        for date in dates:
            if date.is_deadline and date.date:
                return date.date

        # If no explicit deadline, use the last date mentioned
        valid_dates = [d for d in dates if d.date]
        if valid_dates:
            return max(valid_dates, key=lambda d: d.date).date

        return None

    def _extract_parties(self, text: str) -> List[PartyReference]:
        """Extract party/person references from text."""
        parties = []

        # Look for capitalized names (simplified)
        # Pattern: Two or more capitalized words together
        name_pattern = r'\b([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+)\b'

        matches = re.finditer(name_pattern, text)
        for match in matches:
            name = match.group(1)

            # Determine role based on context
            context_start = max(0, match.start() - 30)
            context_end = min(len(text), match.end() + 30)
            context = text[context_start:context_end].lower()

            role = self._determine_role(context)

            parties.append(PartyReference(
                name=name,
                role=role,
                identifier=None,
                confidence=0.7
            ))

        return parties

    def _determine_role(self, context: str) -> str:
        """Determine party role from context."""
        for role, indicators in self.ROLE_INDICATORS.items():
            for indicator in indicators:
                if indicator in context:
                    return role
        return "party"

    def _identify_roles(
        self,
        parties: List[PartyReference],
        text: str
    ) -> Tuple[Optional[PartyReference], Optional[PartyReference]]:
        """Identify payer and payee from parties."""
        payer = None
        payee = None

        for party in parties:
            if party.role == 'payer' and not payer:
                payer = party
            elif party.role in ['payee', 'recipient'] and not payee:
                payee = party

        return payer, payee

    def _classify_commitment(
        self,
        text: str,
        monetary_values: List[MonetaryValue],
        parties: List[PartyReference]
    ) -> CommitmentType:
        """Classify the type of commitment."""
        text_lower = text.lower()

        # Check for payment indicators
        payment_score = sum(
            1 for kw in self.PAYMENT_KEYWORDS if kw in text_lower
        )

        # Has monetary values strongly suggests payment
        if monetary_values:
            payment_score += 3

        # Check for conditional language
        conditional_keywords = [
            'wenn', 'falls', 'if', 'should', 'se', 'caso',
            'unter der bedingung', 'provided that', 'desde que'
        ]
        is_conditional = any(kw in text_lower for kw in conditional_keywords)

        if is_conditional:
            return CommitmentType.CONDITIONAL
        elif payment_score >= 3:
            return CommitmentType.PAYMENT
        elif parties:
            return CommitmentType.AGREEMENT
        else:
            return CommitmentType.PROMISE

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text."""
        text_lower = text.lower()
        keywords = []

        all_keywords = self.PAYMENT_KEYWORDS + self.DEADLINE_INDICATORS

        for kw in all_keywords:
            if kw in text_lower:
                keywords.append(kw)

        return list(set(keywords))

    def _extract_conditions(self, text: str) -> List[str]:
        """Extract conditions/contingencies from text."""
        conditions = []

        # Pattern for conditional statements
        conditional_patterns = [
            r'wenn\s+(.+?)(?:\.|,|$)',
            r'falls\s+(.+?)(?:\.|,|$)',
            r'if\s+(.+?)(?:\.|,|$)',
            r'provided\s+that\s+(.+?)(?:\.|,|$)',
            r'se\s+(.+?)(?:\.|,|$)',
            r'desde\s+que\s+(.+?)(?:\.|,|$)',
        ]

        for pattern in conditional_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                condition = match.group(1).strip()
                if len(condition) > 5:  # Minimum meaningful length
                    conditions.append(condition)

        return conditions

    def _calculate_confidence(
        self,
        monetary_values: List[MonetaryValue],
        dates: List[DateReference],
        parties: List[PartyReference],
        commitment_type: CommitmentType
    ) -> float:
        """Calculate overall parse confidence."""
        confidence = 0.5  # Base confidence

        # Monetary values found
        if monetary_values:
            confidence += 0.15
            # High confidence values add more
            high_conf = sum(1 for v in monetary_values if v.confidence > 0.8)
            confidence += 0.05 * min(2, high_conf)

        # Dates found
        if dates:
            confidence += 0.1

        # Parties identified
        if parties:
            confidence += 0.1
            if len(parties) >= 2:
                confidence += 0.05

        # Known commitment type
        if commitment_type != CommitmentType.UNKNOWN:
            confidence += 0.1

        return min(0.95, confidence)

    def _generate_commitment_id(
        self,
        text: str,
        source_hash: Optional[str],
        timestamp: str
    ) -> str:
        """Generate unique commitment ID."""
        data = f"{text}:{source_hash or ''}:{timestamp}"
        hash_val = hashlib.sha256(data.encode()).hexdigest()[:12].upper()
        return f"CMT-{hash_val}"


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def parse_commitment(
    text: str,
    source_hash: Optional[str] = None
) -> ParsedCommitment:
    """
    Parse commitment from text.

    Args:
        text: Raw text from document
        source_hash: Optional PixWindi source hash

    Returns:
        ParsedCommitment
    """
    parser = CommitmentParser()
    return parser.parse(text, source_hash)
